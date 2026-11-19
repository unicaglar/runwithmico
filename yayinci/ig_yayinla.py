"""@runwith.mico Instagram yayıncısı (GitHub Actions'ta çalışır, yalnızca Python standart kütüphanesi).

  python3 yayinci/ig_yayinla.py yayinla   # takvimde zamanı gelen gönderiyi paylaşır
  python3 yayinci/ig_yayinla.py kontrol   # anahtarın çalıştığını ve doğru hesaba bağlı olduğunu gösterir
  python3 yayinci/ig_yayinla.py yenile    # anahtarın süresini uzatır; yeni anahtar farklıysa yeni_anahtar dosyasına yazar

Yöntem: "Instagram girişiyle Instagram API'si" (graph.instagram.com). Facebook sayfası gerekmez.

Gerekli gizli değişkenler (GitHub > Settings > Secrets and variables > Actions):
  IG_TOKEN    @runwith.mico ile giriş yapılarak alınan uzun ömürlü erişim anahtarı
              (instagram_business_basic, instagram_business_content_publish). 60 gün geçerlidir;
              .github/workflows/anahtar-yenile.yml her hafta yeniler.

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
SURUM = os.environ.get("GRAPH_VERSION", "v23.0")
TOKEN = os.environ.get("IG_TOKEN", "").strip().strip('"').strip("'")
# "IG…" ile başlayan anahtar Instagram adresine, "EAA…" ile başlayan anahtar Facebook Graph adresine gider
HOST = "https://graph.instagram.com/" if TOKEN.startswith("IG") else "https://graph.facebook.com/"
API = HOST + SURUM + "/"
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
    me = api("me", {"fields": "user_id,username" if "instagram" in HOST else "id,username"})
    ad = me.get("username", "")
    if ad.lower() != HESAP:
        sys.exit(f"Güvenlik durdurması: anahtar @{ad} hesabına ait, @{HESAP} değil. Hiçbir şey paylaşılmadı.")
    return me.get("user_id") or me["id"]

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
    print(f"Anahtar türü: {TOKEN[:4]}… ({len(TOKEN)} karakter) → {HOST}")
    uid = ig_user()
    r = api(uid, {"fields": "username,followers_count,media_count"})
    print(f"Bağlantı tamam: @{r.get('username')} · {r.get('followers_count')} takipçi · {r.get('media_count')} gönderi · kimlik {uid}")

def yenile():
    """Uzun ömürlü anahtarın süresini 60 gün uzatır. Anahtar asla yazdırılmaz."""
    ig_user()
    url = "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode(
        {"grant_type": "ig_refresh_token", "access_token": TOKEN})
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Anahtar yenilenemedi ({e.code}): {e.read().decode(errors='ignore')[:300]}")
    gun = int(d.get("expires_in", 0)) // 86400
    yeni = d.get("access_token", "")
    if yeni and yeni != TOKEN:
        with open(os.path.join(ROOT, "yeni_anahtar"), "w") as f: f.write(yeni)
        print(f"Anahtar yenilendi (yeni değer), {gun} gün geçerli")
    else:
        print(f"Anahtar uzatıldı, {gun} gün geçerli")

if __name__ == "__main__":
    if not TOKEN:
        print("IG_TOKEN tanımlı değil; Instagram adımı atlandı."); sys.exit(0)
    {"yayinla": yayinla, "kontrol": kontrol, "yenile": yenile}[sys.argv[1] if len(sys.argv) > 1 else "kontrol"]()
