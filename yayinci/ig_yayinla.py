"""@runwith.mico Instagram yayıncısı (GitHub Actions'ta çalışır, yalnızca Python standart kütüphanesi).

  python3 yayinci/ig_yayinla.py yayinla   # takvimde zamanı gelen gönderiyi paylaşır
  python3 yayinci/ig_yayinla.py kontrol   # anahtarın çalıştığını ve doğru hesaba bağlı olduğunu gösterir

Gerekli gizli değişkenler (GitHub > Settings > Secrets and variables > Actions):
  IG_TOKEN    Meta sistem kullanıcısı erişim anahtarı (instagram_basic, instagram_content_publish,
              pages_show_list, pages_read_engagement, business_management)
  IG_USER_ID  (isteğe bağlı) @runwith.mico'nun Instagram kimliği; boşsa anahtardan kullanıcı adına göre bulunur

Güvenlik: Paylaşımdan önce hesabın kullanıcı adı HESAP ile karşılaştırılır; farklıysa hiçbir şey paylaşılmaz.
Takvimde yalnızca durumu "bekliyor" olan öğeler paylaşılır; "taslak" öğeler onay bekler.
"""
import sys, os, json, time, math, datetime as dt
import urllib.request, urllib.parse, urllib.error

HESAP = "runwith.mico"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAKVIM = os.path.join(ROOT, "instagram", "takvim.json")
# Görseller GitHub Pages'ten sunulur (Instagram görseli bu adresten kendisi çeker)
SITE = os.environ.get("GORSEL_ADRESI", "https://unicaglar.github.io/runwithmico").rstrip("/")
API = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0") + "/"
TOKEN = os.environ.get("IG_TOKEN", "").strip()
GEC_KALMA = dt.timedelta(hours=48)   # bundan fazla geciken takvim haftalık olarak ileri kaydırılır

def api(path, params=None, post=False):
    params = dict(params or {}, access_token=TOKEN)
    data = urllib.parse.urlencode(params).encode()
    url = API + path if post else API + path + "?" + data.decode()
    req = urllib.request.Request(url, data=data if post else None, method="POST" if post else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        sys.exit(f"Instagram API hatası ({e.code}) {path}: {body[:500]}")

def ig_user():
    """@runwith.mico hesabının kimliğini döndürür; kullanıcı adı tutmazsa durur."""
    uid = os.environ.get("IG_USER_ID", "").strip()
    if not uid:
        r = api("me/accounts", {"fields": "name,instagram_business_account{id,username}"})
        for pg in r.get("data", []):
            h = pg.get("instagram_business_account")
            if h and h.get("username", "").lower() == HESAP:
                uid = h["id"]; break
        if not uid:
            gorulen = [(pg.get("instagram_business_account") or {}).get("username") for pg in r.get("data", [])]
            sys.exit(f"@{HESAP} bu anahtarla bulunamadı. Görülen hesaplar: {gorulen}")
    ad = api(uid, {"fields": "username"}).get("username", "")
    if ad.lower() != HESAP:
        sys.exit(f"Güvenlik durdurması: kimlik {uid} @{ad} hesabına ait, @{HESAP} değil. Hiçbir şey paylaşılmadı.")
    return uid

def bekle(cid, deneme=30):
    for _ in range(deneme):
        st = api(cid, {"fields": "status_code"}).get("status_code")
        if st == "FINISHED": return
        if st in ("ERROR", "EXPIRED"): sys.exit(f"Görsel işlenemedi: {cid} {st}")
        time.sleep(5)
    sys.exit(f"Görsel işleme zaman aşımı: {cid}")

def paylas(uid, p, now):
    urls = [f"{SITE}/{g}" for g in p["gorseller"]]
    if p.get("tip") == "hikaye":
        cid = api(f"{uid}/media", {"image_url": urls[0], "media_type": "STORIES"}, post=True)["id"]
    elif p.get("tip") == "reels":
        prm = {"media_type": "REELS", "video_url": urls[0], "caption": p["metin"], "share_to_feed": "true"}
        if p.get("kapak_ms") is not None: prm["thumb_offset"] = str(p["kapak_ms"])
        cid = api(f"{uid}/media", prm, post=True)["id"]
        bekle(cid, 120)
    elif len(urls) == 1:
        cid = api(f"{uid}/media", {"image_url": urls[0], "caption": p["metin"]}, post=True)["id"]
    else:
        kids = []
        for u in urls[:10]:
            if u.endswith(".mp4"):
                k = api(f"{uid}/media", {"media_type": "VIDEO", "video_url": u, "is_carousel_item": "true"}, post=True)["id"]
                bekle(k, 72)
            else:
                k = api(f"{uid}/media", {"image_url": u, "is_carousel_item": "true"}, post=True)["id"]
                bekle(k)
            kids.append(k)
        cid = api(f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": p["metin"]}, post=True)["id"]
    bekle(cid)
    mid = api(f"{uid}/media_publish", {"creation_id": cid}, post=True)["id"]
    p.update(durum="yayinlandi", media_id=mid, yayin=now.isoformat(timespec="seconds"))
    print(f"Yayınlandı: {p['id']} → {mid}")

def yayinla():
    """Her çalışmada zamanı gelen en fazla bir gönderi ve bir hikâye paylaşılır."""
    t = json.load(open(TAKVIM, encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc)
    bekleyen = [x for x in t if x["durum"] == "bekliyor"]
    due = [x for x in bekleyen if dt.datetime.fromisoformat(x["tarih"]) <= now]
    if not due:
        print("Zamanı gelen gönderi yok"); return
    gec = now - dt.datetime.fromisoformat(min(due, key=lambda x: x["tarih"])["tarih"])
    if gec > GEC_KALMA:
        hafta = math.ceil(gec / dt.timedelta(days=7))
        for x in bekleyen:
            x["tarih"] = (dt.datetime.fromisoformat(x["tarih"]) + dt.timedelta(weeks=hafta)).isoformat()
        json.dump(t, open(TAKVIM, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Takvim {hafta} hafta ileri kaydırıldı"); return
    uid = ig_user()
    for hikaye in (False, True):
        grup = [x for x in due if (x.get("tip") == "hikaye") == hikaye]
        if not grup: continue
        paylas(uid, min(grup, key=lambda x: x["tarih"]), now)
        json.dump(t, open(TAKVIM, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def kontrol():
    uid = ig_user()
    r = api(uid, {"fields": "username,followers_count,media_count"})
    print(f"Bağlantı tamam: @{r.get('username')} · {r.get('followers_count')} takipçi · {r.get('media_count')} gönderi · kimlik {uid}")

if __name__ == "__main__":
    if not TOKEN:
        print("IG_TOKEN tanımlı değil; Instagram adımı atlandı."); sys.exit(0)
    {"yayinla": yayinla, "kontrol": kontrol}[sys.argv[1] if len(sys.argv) > 1 else "kontrol"]()
