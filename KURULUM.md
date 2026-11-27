# @runwith.mico Instagram otomasyonu: kurulum

Bu otomasyon **Arel Marin'den tamamen ayrıdır**: ayrı GitHub deposu, ayrı GitHub oturumu, ayrı Meta işletme
portföyü, ayrı Meta uygulaması. Arel Marin'in hiçbir ayarına dokunulmaz.

Gönderiler `instagram/takvim.json` dosyasında durur. Görseller `gorseller/` klasöründen GitHub Pages ile yayınlanır
(https://unicaglar.github.io/runwithmico/…). Her akşam 18:20–00:50 arası yarım saatte bir GitHub iş akışı çalışır ve
zamanı gelen gönderiyi Instagram API'si ile paylaşır.

- **taslak**: hazır ama onay bekliyor, paylaşılmaz
- **bekliyor**: onaylandı, tarihi gelince paylaşılır
- **yayinlandi**: paylaşıldı (iş akışı kendisi işaretler)

Betik paylaşmadan önce hesabın kullanıcı adının `runwith.mico` olduğunu kontrol eder; farklıysa durur.

---

## 1. Ayrı GitHub oturumu (Terminal, 2 dk)

```
~/runwithmico/.tools/ghm auth login -h github.com -p https -s workflow -w
```

Ekrandaki kodu tarayıcıda gir ve onayla. Bu oturum yalnızca `~/runwithmico/.tools/gh-config` içinde tutulur;
Arel Marin'in GitHub oturumu değişmez.

## 2. Hesabı profesyonel yap (telefon, 1 dk)

Instagram → Profil → ☰ → **Hesap türü ve araçlar** → **Profesyonel hesaba geç** → **İçerik üreticisi** → kategori: **Sporcu**.

## 3. Meta uygulaması (Facebook sayfası gerekmez)

Kurulu olan: Meta uygulaması **Run With Mico** (App ID 1765600557863847), ayrı işletme portföyü **Run With Mico**
(Arel Marin portföyü değil). Kullanım durumu: **Instagram API → API setup with Unified login**.

1. **1. Configure your app** → yapılandırma: **Instagram API (Birleşik Giriş)** (sistem kullanıcısı anahtarı, süresiz)
2. **2. Generate access tokens → Add account** → @runwith.mico'ya **Instagram Tester** rolü verilir
3. Instagram → Ayarlar → **Uygulamalar ve İnternet Siteleri → Test Kullanıcısı Davetleri** → **Kabul Et**
4. Meta'da @runwith.mico satırında **Generate token** → **Instagram ile devam et** → giriş
5. "Token generated" penceresinde **I understand** kutusunu işaretle → **Copy**
   (Kullanıcı adının altındaki 17 haneli sayı hesap kimliğidir, anahtar değil. Anahtar "EAA…" ile başlar, ~265 karakter.)
   **Bu anahtarı kimseyle (bu sohbet dahil) paylaşma.**

## 4. Anahtarı GitHub'a ekle

1. https://github.com/unicaglar/runwithmico/settings/secrets/actions
2. **New repository secret** → Name: `IG_TOKEN` → Secret: anahtar → **Add secret**

## 5. Test et

1. https://github.com/unicaglar/runwithmico/actions/workflows/instagram.yml
2. **Run workflow** → işlem: `kontrol` → **Run workflow**
3. Bir dakika sonra çalışmayı aç: `Bağlantı tamam: @runwith.mico · … · kimlik …` yazmalı.

Bundan sonra: Claude takvime gönderi ekler (taslak), sen onaylarsın (bekliyor), tarihi gelince kendiliğinden paylaşılır.

## 6. İstatistik izni (haftalık rapor için)

Haftalık rapor (`.github/workflows/rapor.yml`, her pazartesi) gönderilerin erişim, kaydetme ve paylaşım sayılarını
`instagram/rapor.md` dosyasına yazar. Bunun için anahtarın istatistik okuma izni olmalı:

1. Meta uygulaması **Run With Mico** → **Instagram API → API setup with Unified login**
2. **Permissions** bölümünde `instagram_business_manage_insights` iznini ekle
3. @runwith.mico satırında **Generate token** ile yeni anahtar al (izin ekranında istatistik iznini onayla)
4. GitHub → Settings → Secrets → `IG_TOKEN` değerini yeni anahtarla **güncelle**
5. Actions → **Instagram rapor** → **Run workflow** ile dene

İzin yoksa rapor yine oluşur ama "İstatistikler okunamadı" uyarısı gösterir.
