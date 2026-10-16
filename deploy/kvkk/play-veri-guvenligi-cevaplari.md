# Google Play "Veri güvenliği" ve "Hesap silme" — işaretlenecek cevaplar (v0.1.5+)

Sahibi Play Console → Uygulama içeriği'nde işaretler. `PLAY-STORE-PAKETI.md §C2` ("toplanan veri yok") **0.1.5 ile geçersizdir**; aşağıdaki cevaplarla değiştirilir. Kural (Google): form, Play'de dağıtılan TÜM sürümleri kapsar; doğruluğu geliştiricinin sorumluluğudur; uyuşmazlık güncelleme engeli/kaldırma sebebidir.
Kaynak tanımlar: "toplama" = verinin cihazdan çıkması; "ephemeral" = yalnız bellekte, gerçek zamanlı istek için; hizmet sağlayıcıya (bizim adımıza işleyen) aktarım "paylaşma" sayılmaz; yalnız cihazda işlenen veri "toplama" sayılmaz.

## 1. Üst düzey sorular
| Soru | Cevap | Gerekçe |
|---|---|---|
| Uygulama gerekli kullanıcı verisi toplar veya paylaşır mı? | **Evet** | Din görevlisi kaydı ve Tam Sayfa: ad, telefon, kart fotoğrafı, sipariş kaydı sunucuya gider |
| Tüm kullanıcı verisi aktarım sırasında şifreleniyor mu? | **Evet** | Tüm uç noktalar https (`veriKok`, `aileKok`; Netgsm/Meta/Google https) |
| Kullanıcılar verilerinin silinmesini isteyebilir mi? | **Evet** — ancak **önce** `silme-talebi.md` uygulanmalı (şimdilik yalnız e-posta ve sahibi RED var). Uygulanmadan "Evet" işaretlenmez | Google: silme yolu yoksa "Hayır" |

## 2. Veri türleri (her biri: toplanıyor mu / paylaşılıyor mu / ephemeral mi / zorunlu mu / amaç)

| Veri türü | Toplanıyor | Paylaşılıyor | Ephemeral | Zorunlu/isteğe bağlı | Amaç | Gerekçe |
|---|---|---|---|---|---|---|
| Kişisel bilgi → **Ad** | Evet | Hayır | Hayır | İsteğe bağlı* | Uygulama işlevselliği; Hesap yönetimi; Dolandırıcılık önleme, güvenlik | Din görevlisi ad-soyadı; Tam Sayfa başvuran adı |
| Kişisel bilgi → **Telefon numarası** | Evet | Hayır | Hayır | İsteğe bağlı* | Uygulama işlevselliği; Hesap yönetimi; Dolandırıcılık önleme, güvenlik | Doğrulama kodu, giriş |
| Kişisel bilgi → **Kullanıcı kimlikleri** | Evet | Hayır | Hayır | İsteğe bağlı* | Hesap yönetimi; Güvenlik | Hesap/oturum kimliği (rastgele belirteç) |
| Kişisel bilgi → **Diğer bilgiler** (unvan, görev yeri) | Evet | Hayır | Hayır | İsteğe bağlı* | Uygulama işlevselliği | Panel başlığı, ilan bölgesi |
| **Fotoğraflar ve videolar → Fotoğraflar** | Evet | Hayır (hizmet sağlayıcı Cloudflare) | **Hayır** | İsteğe bağlı* | Dolandırıcılık önleme, güvenlik ve uyumluluk | Kart fotoğrafı normalde bellekte işlenir ama doğrulanamazsa 7 güne kadar KV'de durur → "ephemeral" işaretlenmez |
| Finansal bilgiler → **Satın alma geçmişi** | Evet | Hayır | Hayır | İsteğe bağlı* | Uygulama işlevselliği; Uyumluluk | Sipariş numarası + makbuz özeti (Tam Sayfa) |
| Finansal bilgiler → Kullanıcı ödeme bilgileri | **Hayır** | — | — | — | — | Ödeme Google Play Faturalandırma'da; uygulama/Worker kart verisine erişmez |
| Cihaz veya diğer kimlikler | Hayır (öneri) | — | — | — | — | IP adresi istek anında kullanılır, hesaba yalnız tuzlu özet olarak yazılır (din görevlisi hesabında kalıcı). Tutucu okuma: bu özet "diğer kimlik" sayılabilir → Console incelemesi sorarsa **Evet / Dolandırıcılık önleme** olarak ekleyin |
| Konum (yaklaşık/kesin) | **Hayır** | — | — | — | — | Cihaz konumu hiçbir yerde okunmaz; il/ilçeyi kullanıcı seçer ve cihazda durur. (Not: IP'den konum çıkarımı yapılmıyor) |
| Kişi, mesaj, takvim, ses, dosya, sağlık, web geçmişi | Hayır | — | — | — | — | — |
| Uygulama etkinliği, uygulama bilgileri/performans (çökme, analiz) | Hayır | — | — | — | — | Analitik/çökme SDK'sı yok (`pubspec.yaml`) |

\* "İsteğe bağlı" gerekçesi: bu veriler yalnız "Din görevlisiyim" / "Tam Sayfa ilan" özelliklerinde istenir; uygulamanın okuma işlevi hesapsız tam çalışır ve kullanıcı bu özellikleri hiç kullanmayabilir. Google "kullanıcı atlayabiliyorsa isteğe bağlı" der; Play incelemesi aksini isterse "Gerekli" işaretleyin (sonuç: ne bir şey bozulur ne değişir, yalnız etiket).

## 3. Paylaşım
**Hiçbir veri türü "paylaşılıyor" işaretlenmez.** Cloudflare, Netgsm, Meta (WhatsApp) ve Google bizim adımıza işleyen hizmet sağlayıcılardır; Google tanımına göre bu aktarım "paylaşma" değildir. (Meta WhatsApp kullanıma açılırsa Meta'nın kendi kullanım koşullarını ayrıca okuyun; Meta veriyi kendi amacıyla kullanıyorsa bu işaret değişir.)

## 4. Güvenlik uygulamaları
- Şifreleme (aktarım): **Evet**
- Silme isteği mekanizması: **Evet** (uygulandıktan sonra) → bağlantı alanına web silme sayfası URL'si (`silme-talebi.md §3`)
- Bağımsız güvenlik incelemesi, Aileler politikası, UPI rozetleri: **Hayır**

## 5. Hesap silme bölümü (Play, "hesap oluşturan uygulamalar")
Din görevlisi kaydı uygulama içinde hesap oluşturduğu için Google şunları şart koşar: (1) uygulama içi, belirgin silme yolu; (2) **web üzerinde** silme isteği bağlantısı (uygulamayı silmiş kullanıcı için); sayfada uygulama/geliştirici adı görünür olmalı ve istek uygulamaya dönmeden verilebilmeli; (3) Veri güvenliği formundaki "silme" sorularının cevaplanması. Kapsam: Veri güvenliği formunda "toplanan" yazan her şey; saklama istisnaları (dolandırıcılık, düzenleme) gizlilik politikasında açıkça yazılmalı → `aydinlatma-metni.md §5` (ödeme kayıtları) bunu yapar.
**Şu anki eksik:** uygulama içi silme düğmesi ve web silme sayfası YOK → Play incelemesinde ret riski. `silme-talebi.md` öneri.

## 6. Diğer içerik formları (bu sürümle değişenler)
- IARC: "Dijital ürün satın alma" → **Evet** (Tam Sayfa 200 ₺).
- İzinler (Mağaza paketi §E): INTERNET + **POST_NOTIFICATIONS** + **BILLING**; kamera erişimi `image_picker` ile sistem kamera uygulamasından yapılır (manifestte CAMERA izni eklenmiyor); birleşik manifestte WorkManager'ın RECEIVE_BOOT_COMPLETED/WAKE_LOCK gibi izinleri olabilir → AAB'den `aapt dump permissions` ile teyit edin.
- Mağaza uzun açıklamasındaki "Hesap açmanız gerekmez… konum izni istenmez" cümlesi 0.1.5'te şu hâle gelmeli: "Okumak için hesap gerekmez. Din görevlileri ve Tam Sayfa ilan verenler için telefon doğrulaması gerekir." ("Uygulamada reklam yoktur" doğru kalır.)
- Gizlilik politikası URL'si: `gizlilik.html` yeni sürümü (bu klasör).

---
**Dayanılan belgeler:**
- Google Play Data safety form rehberi: https://support.google.com/googleplay/android-developer/answer/10787469
- Google Play hesap silme şartı: https://support.google.com/googleplay/android-developer/answer/13327111
- Kod: `index.js`, `gorevli.js`, `odeme.js`, `pubspec.yaml`, `araclar/android_ayarla.py`
