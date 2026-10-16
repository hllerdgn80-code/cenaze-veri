# Veri envanteri — Kimin Cenazesi (kodla birebir; 15.10.2026 durumu)

Kaynak: `deploy/aile-worker/src/{index,gorevli,dogrulama,odeme,kurallar}.js`, `uygulama/lib/cekirdek/*.dart`. KV = Cloudflare KV (`AILE` ad alanı). Hukuki dayanak kısaltmaları: **5/2-c** sözleşme, **5/2-ç** hukuki yükümlülük, **5/2-f** meşru menfaat, **AR** açık rıza (md.5/1), md.6 = özel nitelikli (bu envanterdeki hiçbir veri md.6 listesindeki türden değil; bkz. not 3). Dayanak kolonu bir öneridir; sahibi/hukukçu teyit eder.

## 1. Telefonda (bizde değil)

| Veri | Kimden | Yer | Amaç | Dayanak | Saklama | Silme yolu |
|---|---|---|---|---|---|---|
| İl, ilçe | Kullanıcı seçer | Telefon (SharedPreferences) | Liste ve bildirim bölgesi | Cihazda kalır, bizim işlememiz değil | Uygulama silinene kadar | Uygulama verisini sil |
| Tema, bildirim izni, ertele tarihi, bildirimde görülen ilan kimlikleri | Kullanıcı/uygulama | Telefon | Çalışma | aynı | aynı | aynı |
| Sayfam kayıtları (vefat eden kişi bilgisi), okuma sayaçları, cinsiyet seçimi | Kullanıcı | Telefon | Kişisel kullanım | aynı | aynı | aynı |
| Son indirilen liste (çevrimdışı önbellek) | Sunucu | Telefon | Çevrimdışı gösterim | aynı | aynı | aynı |
| Din görevlisi oturum belirteci, son durum | Sunucu | Telefon | Oturum | aynı | Çıkışa/silmeye kadar | Çıkış / uygulamayı sil |
| Kart fotoğrafı (örtülmüş, 1600 px) | Kamera | **Diskte yok**; yalnız bellek (kod: "diske YAZILMAZ") | Doğrulama | — | Gönderim süresi | Kendiliğinden |

## 2. Cloudflare KV / Worker (bizim sunucu tarafı)

| Veri (KV anahtarı) | Kimden | Yer | Amaç | Dayanak | Saklama (kod) | Silme yolu |
|---|---|---|---|---|---|---|
| Din görevlisi hesabı `gorevli:k:<id>`: **Diyanet e-posta adresi (kullanıcı adı@diyanet.gov.tr)**, ad-soyad, unvan, il/ilçe, görev yeri, durum, doğrulama zamanı (`dogrulama: diyanet_eposta`), KVKK kabul tarihi (`kvkk_kabul`). **Telefon yok, kart fotoğrafı yok** | Din görevlisi | KV | Kimlik teyidi (e-posta kodu), panel, kötüye kullanım denetimi | 5/2-c, 5/2-f | Onaylı: süresiz (TTL yok) | Sahibi `dondur`/RED; kullanıcı için uç nokta yok (öneri: `silme-talebi.md`) |
| Bekleyen e-posta kodu `gorevli:ek:<kullanıcı>` (kod özeti, deneme sayısı) ve günlük kod sayacı `gorevli:eks:<kullanıcı>:<gün>` | Din görevlisi | KV | Kod doğrulama, kötüye kullanım sınırı | 5/2-f | Kod 10 dk (TTL); sayaç ~25 saat | Kendiliğinden |
| Oturum `gorevli:oturum:<sha256(belirteç)>` ve `gorevli:ot:<id>` | Sistem | KV | Giriş durumu | 5/2-c | 180 gün; RED'de "RED" işareti 30 gün | Süre dolar / RED |
| Doğrulama kodu özeti (kod_ozeti) | Sistem | Hesap kaydı içinde | Telefon doğrulama | 5/2-c | 15 dk geçerli, 3 yanlış denemede iptal | Doğrulamada `null` |
| Doğrulama kodu (gönderim) | Sistem | Netgsm (TR) / WhatsApp Cloud API (Meta) | Telefona kod | 5/2-c | Tutulmaz (bizde) | — |
| Onay SMS'i (ONAY_SMS) | — | Netgsm | Onay haberi (yedek) | 5/2-c | Tutulmaz (bizde) | — |
| Müftülük personel listesi `gorevli:liste:<il>:<ilçe>` [ad-soyad, cami] — **üçüncü kişilerin** verisi | Kamuya açık müftülük sayfaları (CI ile yüklenir) | KV | Başvuru adını listede aramak (puan) | 5/2-d (alenileştirme) / 5/2-f — aydınlatma yükümlülüğü ayrıca değerlendirilmeli (RAPOR §3) | Süresiz, günlük yenilenir | CI ile üzerine yazılır |
| Din görevlisi ilanı `gorevli:i:<id>`: vefat edenin adı, cinsiyet, yaş, vefat/namaz tarihi, yer, defin yeri, mahalle/köy, şehitse rütbe/tören yeri/resmî duyuru bağlantısı, görev yeri, hesap kimliği | Din görevlisi | KV | Yayın | 5/2-f; vefat eden Kurul'a göre ilgili kişi değil (2019/273) | 120 gün, sonra kendiliğinden; liste ekranı yalnız son 7 gün | İptal / TTL / gizleme |
| İlan dizini `gorevli:x:…`, hesap-ilan `gorevli:h:…`, gözetim `gorevli:g:…` | Sistem | KV | Mükerrer kontrol, listeleme, çapraz kontrol | 5/2-f | 120 gün / 8 gün | TTL |
| Bildirim yapan IP özetleri `gorevli:n:<ilan>` / `n:<ilan>` | Bildirimi yapan | KV | "2 bildirimde gizle" | 5/2-f | İlan ömrü (120 gün) | TTL |
| Günlük ilan sayacı `gorevli:gs:…` | — | KV | Günlük 10 ilan sınırı | 5/2-f | ~25 saat | TTL |
| Hız sınırı `r:<IP özeti>:<saat>` (IP+tuz sha256) | İstek | KV | Kötüye kullanım sınırı (10/saat) | 5/2-f | ~1 saat | TTL |
| Tam Sayfa başvurusu `b:<id>`: ilan alanları + başvuran **ad-soyad, telefon, yakınlık**, kod özeti, IP özeti | Cenaze yakını | KV | Telefon doğrulama | 5/2-c | 15 dk | TTL |
| Tekrar-gönderim anahtarı `bk:<sha256(telefon|ad|tarih)>` | — | KV | 60 sn sınırı | 5/2-f | 15 dk | TTL |
| Tam Sayfa ilanı `i:<id>`: ilan + **başvuran ad-soyad, telefon, yakınlık, IP özeti**, ödeme durumu, sipariş no | Cenaze yakını | KV | Yayın, ödeme eşleştirme | 5/2-c (ilan), 5/2-ç (ödeme kaydı) | Ödeme bekleyen: 2 gün; yayında: 120 gün. **Başvuran + IP 30 gün sonra silinir** (günlük cron `temizle`, 03:17) | Cron / TTL |
| Telefon başına ilan sayacı `e:<sha256(telefon)>` | Sistem | KV | Telefon başına 7 günde 2 ilan | 5/2-f | 7 gün | TTL |
| Ödeme bekleyen `bo:<basvuru>` | Sistem | KV | Ödeme-ilan eşleştirme | 5/2-c | 2 gün | TTL |
| Kullanılmış makbuz `pt:<sha256(token)>` → ilan | Google Play | KV | Aynı makbuz iki kez kullanılmasın | 5/2-ç / 5/2-f | **Süresiz (TTL yok)** | — (kural: hukuki saklama süresi teyit edilip bağlanmalı) |
| Ödeme kaydı `od:<zaman>:<özet>`: ilan kimliği, **vefat edenin adı**, il/ilçe, sipariş no, token özeti, doğrulandı mı | Google Play / sistem | KV | Muhasebe/mutabakat | 5/2-ç | **Süresiz (TTL yok)** | — (aynı not) |
| Panel sayaçları `st:<il>` (yayında/gizli/red sayıları) | Sistem | KV | Panel istatistiği | — (kişisel veri değil) | Süresiz | — |

## 3. Üçüncü taraflar (veri işleyen)

| Taraf | Görev | Konum |
|---|---|---|
| Cloudflare (Workers, KV, Workers AI, Pages/veri adresi) | Barındırma, depolama, OCR | Küresel/yurt dışı (KV ve AI'nın hangi bölgede çalıştığını sahibi Cloudflare ayarlarından teyit etmeli) |
| Netgsm | SMS | Türkiye |
| Meta WhatsApp Cloud API | Doğrulama kodu (`WA_TOKEN` tanımlıysa) | Yurt dışı |
| Google Play Faturalandırma / Play Developer API | Ödeme ve makbuz doğrulama | Yurt dışı |

## 4. Notlar

1. **Telefon düz metin saklanıyor** (`k.telefon`) — SMS/WhatsApp kodu ve onay SMS'i için gerekli. `t:`/`tk:`/`e:` anahtarlarındaki sha256 **anonimleştirme değildir**: 10 haneli Türkiye cep numarası alanı küçüktür, özet geri çözülebilir; bu veriler de kişisel veri sayılır.
2. IP özeti `sha256(IP|IP_TUZ)`; `IP_TUZ` tanımlı değilse tuz sabit "aile" (`index.js`) — tanımlanmalı. Din görevlisi hesabındaki `ip` alanı **silinmiyor** (Tam Sayfa ilanındaki 30 günlük temizliğin karşılığı din görevlisi hesabında yok).
3. Özel nitelikli veri (md.6) yok: din/mezhep, sağlık, biyometrik veri bu sistemde işlenmiyor. Kart fotoğrafında vesikalık yüz görüntüsü bulunur; Workers AI isteminde yüz tanıma/karşılaştırma yoktur (yalnız "logo ve vesikalık fotoğraf var mı" sorulur) → biyometrik işleme yapılmıyor. Din görevlisi olmak (Diyanet personeli) din inancı açıklamak sayılmaz ama bu değerlendirme hukukçuya sorulmalı.
4. Cihazdaki "Sayfam" (dua sayaçları, vefat edenin adı) yalnız telefonda; bizim erişimimiz yok → veri sorumlusu faaliyeti sayılmaz.
5. `wrangler.toml → [vars] GELISTIRME = "1"` yayında **kapatılmazsa**: kod yanıtta döner; `PANEL_ANAHTARI` yoksa sahibi uç noktaları (kuyruk = kart fotoğrafı dahil) kimlik denetimsiz açılır. Bkz. RAPOR.

## 5. Silme yolları özeti (Yönetmelik md.7, md.12)

Sahibi tarafı: RED → hesap + oturum + foto + kod + telefon dizini + tek-hesap anahtarı silinir (kod: `karar()`). TTL ile otomatik silinenler yukarıda. Kullanıcı tarafı: bkz. `silme-talebi.md`.

---
**Dayanılan resmî belgeler:**
- Kişisel Verilerin Silinmesi, Yok Edilmesi veya Anonim Hale Getirilmesi Hakkında Yönetmelik: https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK
- Kişisel Verilerin İşlenme Şartları: https://www.kvkk.gov.tr/Icerik/4190/Kisisel-Verilerin-Islenme-Sartlari
- 7499 sayılı Kanun md.6/md.9 (RG 12.03.2024): https://www.resmigazete.gov.tr/eskiler/2024/03/20240312-1.htm
- Kurul Karar Özeti 2019/273 (ölen kişi): https://www.kvkk.gov.tr/Icerik/6710/2019-273
