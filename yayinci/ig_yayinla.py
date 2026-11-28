"""@runwith.mico Instagram yayıncısı (GitHub Actions'ta çalışır, yalnızca Python standart kütüphanesi).

  python3 yayinci/ig_yayinla.py yayinla   # takvimde zamanı gelen gönderiyi paylaşır
  python3 yayinci/ig_yayinla.py kontrol   # anahtarın çalıştığını ve doğru hesaba bağlı olduğunu gösterir
  python3 yayinci/ig_yayinla.py yenile    # anahtarın süresini uzatır; yeni anahtar farklıysa yeni_anahtar dosyasına yazar
  python3 yayinci/ig_yayinla.py rapor     # paylaşılan gönderilerin istatistiklerini instagram/rapor.md dosyasına yazar
                                          # (anahtarda instagram_business_manage_insights izni gerekir)

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
IG_ID = os.environ.get("IG_USER_ID", "").strip() or "17841431899987553"   # @runwith.mico
GEC_KALMA = dt.timedelta(hours=48)   # bundan fazla geciken takvim haftalık olarak ileri kaydırılır
ERKEN_BEKLE = dt.timedelta(hours=5, minutes=30)   # bu kadar yakındaki gönderi için çalıştırma bekleyip tam saatinde paylaşır

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
    if "instagram" in HOST:
        me = api("me", {"fields": "user_id,username"})
    else:
        # Facebook Graph (sistem kullanıcısı anahtarı, süresiz): hesap kimliğiyle sorgulanır
        me = api(IG_ID, {"fields": "id,username"})
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
    if not p.get("gorseller"):
        print(f"Atlandı: {p['id']} için görsel/video yok. Önce dosyayı ekleyin."); return False
    urls = [f"{SITE}/{g}" for g in p["gorseller"]]
    if p.get("tip") == "hikaye":
        cid = api(f"{uid}/media", {"image_url": urls[0], "media_type": "STORIES"}, post=True)["id"]
    elif p.get("tip") == "reels":
        prm = {"media_type": "REELS", "video_url": urls[0], "caption": p["metin"], "share_to_feed": "true"}
        if p.get("kapak"): prm["cover_url"] = f"{SITE}/{p['kapak']}"   # özel kapak görseli
        elif p.get("kapak_ms") is not None: prm["thumb_offset"] = str(p["kapak_ms"])
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
    return True

def yayinla():
    """Her çalışmada zamanı gelen en fazla bir gönderi ve bir hikâye paylaşılır."""
    t = json.load(open(TAKVIM, encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc)
    bekleyen = [x for x in t if x["durum"] == "bekliyor"]
    due = [x for x in bekleyen if dt.datetime.fromisoformat(x["tarih"]) <= now]
    if not due:
        # GitHub'ın zamanlanmış çalıştırmaları saatlerce gecikebilir; yaklaşan gönderi varsa
        # bu çalıştırma saatine kadar bekler ve tam zamanında paylaşır.
        yakin = [x for x in bekleyen if dt.datetime.fromisoformat(x["tarih"]) - now <= ERKEN_BEKLE]
        if not yakin:
            print("Zamanı gelen gönderi yok"); return
        hedef = min(dt.datetime.fromisoformat(x["tarih"]) for x in yakin)
        sure = (hedef - now).total_seconds()
        print(f"Sıradaki gönderi {hedef.isoformat()}; {int(sure // 60)} dk bekleniyor", flush=True)
        time.sleep(max(0, sure) + 5)
        now = dt.datetime.now(dt.timezone.utc)
        due = [x for x in bekleyen if dt.datetime.fromisoformat(x["tarih"]) <= now]
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
        if paylas(uid, min(grup, key=lambda x: x["tarih"]), now):
            json.dump(t, open(TAKVIM, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def kontrol():
    print(f"Anahtar türü: {TOKEN[:4]}… ({len(TOKEN)} karakter) → {HOST}")
    uid = ig_user()
    r = api(uid, {"fields": "username,followers_count,media_count"})
    print(f"Bağlantı tamam: @{r.get('username')} · {r.get('followers_count')} takipçi · {r.get('media_count')} gönderi · kimlik {uid}")

def api_dene(path, params):
    """api() gibi, ama hata olursa durmak yerine (None, hata metni) döndürür."""
    params = dict(params, access_token=TOKEN)
    try:
        with urllib.request.urlopen(API + path + "?" + urllib.parse.urlencode(params), timeout=60) as r:
            return json.load(r), None
    except urllib.error.HTTPError as e:
        try: msg = json.loads(e.read().decode(errors="ignore")).get("error", {}).get("message", "")
        except Exception: msg = ""
        return None, f"{e.code} {msg}".strip()

METRIKLER = {
    "reels":    [["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time"],
                 ["views", "reach", "likes", "comments", "shares", "saved"], ["reach", "likes", "comments", "saved"]],
    "hikaye":   [["views", "reach", "replies", "shares"], ["reach", "replies"]],
    "diger":    [["views", "reach", "likes", "comments", "shares", "saved", "total_interactions"],
                 ["reach", "likes", "comments", "shares", "saved"], ["reach", "likes", "comments", "saved"]],
}
BASLIK = [("views", "Görüntülenme"), ("reach", "Erişim"), ("likes", "Beğeni"), ("comments", "Yorum"),
          ("shares", "Paylaşım"), ("saved", "Kaydetme"), ("replies", "Yanıt"), ("ig_reels_avg_watch_time", "Ort. izlenme (sn)")]

def rapor():
    """Paylaşılan her gönderinin istatistiklerini toplar ve instagram/rapor.md dosyasına yazar."""
    uid = ig_user()
    hesap, _ = api_dene(uid, {"fields": "username,followers_count,media_count"})
    t = json.load(open(TAKVIM, encoding="utf-8"))
    satirlar, izin_yok = [], False
    for p in sorted((x for x in t if x.get("media_id")), key=lambda x: x.get("yayin", ""), reverse=True):
        tur = p.get("tip") if p.get("tip") in ("reels", "hikaye") else "diger"
        veri, hata = None, None
        for liste in METRIKLER[tur]:
            veri, hata = api_dene(f"{p['media_id']}/insights", {"metric": ",".join(liste)})
            if veri is not None: break
        degerler = {}
        if veri:
            for m in veri.get("data", []):
                v = (m.get("values") or [{}])[0].get("value", m.get("total_value", {}).get("value"))
                degerler[m.get("name")] = v
        elif hata and ("permission" in hata.lower() or hata.startswith("403") or "(#10)" in hata):
            izin_yok = True
        satirlar.append((p, degerler, hata if not veri else None))
    simdi = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).strftime("%d.%m.%Y %H:%M")
    out = [f"# @{HESAP} performans raporu", "", f"Güncelleme: {simdi} (TSİ)", ""]
    if hesap:
        out += [f"**Takipçi:** {hesap.get('followers_count', '?')} · **Gönderi:** {hesap.get('media_count', '?')}", ""]
    if izin_yok:
        out += ["> İstatistikler okunamadı: anahtarda `instagram_business_manage_insights` izni yok. KURULUM.md → 6. adım.", ""]
    kolonlar = [k for k, _ in BASLIK if any(k in d for _, d, _ in satirlar)]
    out += ["| " + " | ".join(["Gönderi", "Tür", "Tarih"] + [dict(BASLIK)[k] for k in kolonlar] + ["Kaydetme / erişim"]) + " |",
            "|" + "---|" * (4 + len(kolonlar))]
    for p, d, hata in satirlar:
        tarih = (p.get("yayin") or p.get("tarih", ""))[:10]
        oran = f"%{100 * d['saved'] / d['reach']:.1f}" if d.get("reach") and d.get("saved") is not None else "–"
        hucre = [str(d.get(k, "–")) for k in kolonlar] if not hata else ["–"] * len(kolonlar)
        out.append("| " + " | ".join([p["id"], p.get("tip", ""), tarih] + hucre + [oran if not hata else "hata: " + hata[:60]]) + " |")
    out += ["", "Hikâye istatistikleri Instagram'da yalnızca 24 saat tutulur; sonrasında boş görünür."]
    open(os.path.join(ROOT, "instagram", "rapor.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))

def yenile():
    """Uzun ömürlü anahtarın süresini 60 gün uzatır. Anahtar asla yazdırılmaz."""
    ig_user()
    if "instagram" not in HOST:
        print("Sistem kullanıcısı anahtarı süresiz; yenileme gerekmiyor"); return
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
    {"yayinla": yayinla, "kontrol": kontrol, "yenile": yenile, "rapor": rapor}[sys.argv[1] if len(sys.argv) > 1 else "kontrol"]()
