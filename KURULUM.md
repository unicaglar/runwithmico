# @runwith.mico Instagram otomasyonu: kurulum

Bu otomasyon **Arel Marin'den tamamen ayrıdır**: ayrı GitHub deposu, ayrı GitHub oturumu, ayrı Meta işletme
portföyü, ayrı Meta uygulaması ve ayrı bot kullanıcısı. Arel Marin'in hiçbir ayarına dokunulmaz.

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

## 3. Facebook sayfası (5 dk)

1. https://www.facebook.com/pages/create → Ad: **Run With Miço**, kategori: **Sporcu**
2. Sayfa → **Ayarlar → Bağlı hesaplar → Instagram → Hesabı bağla** → @runwith.mico

## 4. Yeni işletme portföyü ve uygulama (10 dk)

1. https://business.facebook.com → sol üstteki portföy menüsü → **İşletme portföyü oluştur** → Ad: **Run With Miço**
   (Arel Marin portföyünü seçme.)
2. Yeni portföyde **Ayarlar → Hesaplar → Sayfalar → Ekle** → Run With Miço; **Instagram hesapları → Ekle** → @runwith.mico
3. https://developers.facebook.com → **Uygulamalarım → Uygulama oluştur**
   - Kullanım durumu: **Diğer** → tür: **İşletme** → Ad: `Run With Mico Otomasyon` → portföy: **Run With Miço**
   - **Ürün ekle → Instagram** (Facebook Girişi ile Instagram API)
4. Business ayarları (Run With Miço portföyü) → **Kullanıcılar → Sistem kullanıcıları → Ekle**
   - Ad: `mico-bot`, rol: **Yönetici**
   - **Varlık ata**: Run With Miço sayfası (tam kontrol) + @runwith.mico (tam kontrol)
   - **Yeni anahtar oluştur** → uygulama: `Run With Mico Otomasyon` → süre: **Hiçbir zaman sona ermez**
   - İzinler: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
   - Çıkan anahtarı kopyala. **Bu anahtarı kimseyle (bu sohbet dahil) paylaşma.**

## 5. Anahtarı GitHub'a ekle

1. https://github.com/unicaglar/runwithmico/settings/secrets/actions
2. **New repository secret** → Name: `IG_TOKEN` → Secret: anahtar → **Add secret**

## 6. Test et

1. https://github.com/unicaglar/runwithmico/actions/workflows/instagram.yml
2. **Run workflow** → işlem: `kontrol` → **Run workflow**
3. Bir dakika sonra çalışmayı aç: `Bağlantı tamam: @runwith.mico · … · kimlik …` yazmalı.
4. (İsteğe bağlı) Çıktıdaki kimliği `IG_USER_ID` adlı ikinci bir secret olarak ekle.

Bundan sonra: Claude takvime gönderi ekler (taslak), sen onaylarsın (bekliyor), tarihi gelince kendiliğinden paylaşılır.
