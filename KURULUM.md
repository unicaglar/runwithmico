# @runwith.mico Instagram otomasyonu: kurulum

Gönderiler `instagram/takvim.json` dosyasında durur. Görseller `gorseller/` klasöründen GitHub Pages ile yayınlanır
(https://unicaglar.github.io/runwithmico/…). Her akşam 18:20–00:50 arası yarım saatte bir GitHub iş akışı çalışır ve
zamanı gelen gönderiyi Instagram API'si ile paylaşır.

- **taslak**: hazır ama onay bekliyor, paylaşılmaz
- **bekliyor**: onaylandı, tarihi gelince paylaşılır
- **yayinlandi**: paylaşıldı (iş akışı kendisi işaretler)

Betik paylaşmadan önce hesabın kullanıcı adının `runwith.mico` olduğunu kontrol eder; farklıysa durur.

---

## 1. Hesabı profesyonel yap (telefon, 1 dk)

Instagram → Profil → ☰ → **Hesap türü ve araçlar** → **Profesyonel hesaba geç** → **İçerik üreticisi** → kategori: **Sporcu**.
İletişim bilgisi sorarsa atlayabilirsin.

## 2. Facebook sayfası oluştur ve bağla (5 dk)

1. https://www.facebook.com/pages/create → Ad: **Run With Miço**, kategori: **Sporcu**
2. Sayfa → **Ayarlar → Bağlı hesaplar → Instagram → Hesabı bağla** → @runwith.mico ile giriş yap

## 3. İşletme portföyüne ekle ve ayrı bot kullanıcısı oluştur (10 dk)

Arel Marin'in `instagram-bot` kullanıcısına **dokunma**; iki hesabın anahtarları ayrı kalsın.

1. https://business.facebook.com/settings
2. **Hesaplar → Sayfalar → Ekle → Sayfa ekle** → Run With Miço
3. **Hesaplar → Instagram hesapları → Ekle** → @runwith.mico
4. **Kullanıcılar → Sistem kullanıcıları → Ekle**
   - Ad: `mico-bot`, rol: **Yönetici**
   - **Varlık ata**: Run With Miço sayfası (tam kontrol) + @runwith.mico (tam kontrol)
   - **Yeni anahtar oluştur** → uygulama: `Arel Marin Otomasyon` (aynı uygulama kullanılabilir) → süre: **Hiçbir zaman sona ermez**
   - İzinler: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
   - Çıkan anahtarı kopyala. **Bu anahtarı kimseyle (bu sohbet dahil) paylaşma.**

## 4. Anahtarı GitHub'a ekle

1. https://github.com/unicaglar/runwithmico/settings/secrets/actions
2. **New repository secret** → Name: `IG_TOKEN` → Secret: anahtar → **Add secret**

## 5. Test et

1. https://github.com/unicaglar/runwithmico/actions/workflows/instagram.yml
2. **Run workflow** → işlem: `kontrol` → **Run workflow**
3. Bir dakika sonra çalışmayı aç: `Bağlantı tamam: @runwith.mico · … · kimlik …` yazmalı.
4. (İsteğe bağlı) Çıktıdaki kimliği `IG_USER_ID` adlı ikinci bir secret olarak ekle.

Bundan sonra: Claude takvime gönderi ekler (taslak), sen onaylarsın (bekliyor), tarihi gelince kendiliğinden paylaşılır.
