# "Verimi sil" yolu — Kimin Cenazesi

Hukuki danışmanlık değildir. Kod yazılmadı; Worker için öneri aşağıdadır. Kaynak: KVKK md.11/e (silme/yok etme), Yönetmelik md.7 ve md.12 (talepte en geç **30 gün**; silme kaydı **en az 3 yıl** tutulur), Başvuru Tebliği md.5 (başvuru yöntemleri), Google Play hesap silme şartı.

## 1. Bugün mevcut olan (kod, 15.10.2026)

| Kim | Ne var | Eksik |
|---|---|---|
| Din görevlisi | Yalnız **sahibi** RED'i (`POST /gorevli/karar {id, onay:false}`) hesabı, oturumları, foto, kod, telefon dizini, tek-hesap anahtarını siler; `dondur` ilanları gizler | **Kullanıcının kendi başlatabildiği silme yok.** Onaylı hesap TTL'siz kalıyor |
| Tam Sayfa ilan veren | Başvuran ad/telefon/IP **30 günde otomatik** silinir (`temizle`, günlük cron); telefon başına sayaç 7 gün, kod anahtarları dakikalar | 30 gün dolmadan silme ve ilanı kaldırma uç noktası yok |
| Okuyucu | Sunucuda kayıt yok | — |

→ Play'in "hesap oluşturan uygulama" şartı için **uygulama içi silme + web silme bağlantısı** eksik. Eklenmeden Veri güvenliği formunda "silme isteği: Evet" işaretlenmemeli.

## 2. Uygulama içi metin

Din görevlisi paneli → ayarlar → **Hesabı sil**:

> **Hesabınızı silmek istiyor musunuz?**
> Hesabınız, telefon numaranız, oturumunuz ve yayımladığınız ilanlar silinir. Bu işlem geri alınamaz. Ödeme kaydı gibi yasal olarak saklanması gereken bilgiler dışında hiçbir veriniz tutulmaz.
> [Hesabı sil] [Vazgeç]

Başarıdan sonra: "Hesabınız silindi." + oturum belirteci cihazdan kaldırılır (`gorevli_oturum`).

Panelin altına: "Verilerinizle ilgili başka bir talebiniz için: yonetici@kimincenazesi.com".

Okuyucular için (hesap yoksa): Gizlilik sayfasında "Sunucumuzda sizinle ilgili kayıt tutmuyoruz; cihazınızdaki veriyi uygulamayı silerek kaldırabilirsiniz."

## 3. Web / e-posta yolu (uygulamayı silmiş kullanıcı için — Google şartı)

**Yayın adresi:** `https://kimincenazesi.com/hesap-silme` (Gizlilik sayfasında ve Play formundaki silme bağlantısı alanında). Sayfa: uygulama adı "Kimin Cenazesi" görünür, "Hesabımı ve verilerimi sil" başlığı, iki yol:

1. **E-posta:** yonetici@kimincenazesi.com — konu "Hesap silme". Kullanıcıdan istenen: ad-soyad, kayıtlı telefon, talep (hesap silme / ilan kaldırma / bilgi). Biz kimlik doğrulamasını yanıtla göndereceğimiz bir kodu **kayıtlı telefona** SMS atıp kullanıcıya e-postayla yazdırarak yaparız (kullanıcı kayıtta e-posta vermiyor; Tebliğ md.5 "kayıtlı e-posta" yolu uygulanamaz, bu yüzden telefon kodu şart). 30 günlük süre başvuru bize ulaştığında başlar.
2. **Form (öneri):** telefon numarası → kod gelir → "Sil" (aşağıdaki uç noktalar). Form uygulamaya dönmeyi gerektirmez.

## 4. Worker'da gereken uç noktalar (kod yazılmadı; öneri)

| Uç nokta | Kimlik | Ne yapar |
|---|---|---|
| `POST /gorevli/hesap-sil` | Oturum belirteci (`Authorization: Bearer`) | `aktifHesap/hesap()` ile hesabı bulur; siler: `gorevli:k:<id>`, `t:` (telefon özeti), `ac:`, `ot:<id>` ve içindeki her `oturum:<hash>`, `foto:`, `kod:`, `h:<id>:*` ve bunların gösterdiği `i:`/`x:`/`g:` (ilanlar). Oturumu kapatır. **Silme kaydı** (yalnız kişisel veri içermeyen: zaman, "hesap") `silme:<zaman>` anahtarına yazılır (Yönetmelik md.7/3: ≥3 yıl; TTL 3 yıl+) |
| `POST /gorevli/silme-iste {telefon}` | — | Var olan `kodIste(giris)` mantığıyla kayıtlı telefona kod yollar (varlık sızdırmaz, 60 sn sınırı korunur) |
| `POST /gorevli/silme-onay {kayit_id, kod}` | Telefon kodu | Kod doğruysa `hesap-sil` ile aynı silme. Kayıt yoksa/yanlışsa aynı genel yanıt |
| `POST /aile/ilan-kaldir {ilan_id}` | `x-gizli` (yalnız sahibi) | Tam Sayfa ilanını `gizli` yapar, dizinden siler; talep e-postayla gelince sahibi çağırır |
| `POST /aile/basvuran-sil {ilan_id}` | `x-gizli` | 30 gün dolmadan `basvuran` ve `ip` alanlarını `null` yapar |

Silinmesi **kapsam dışı** (yasal saklama / kural gereği): ödeme kaydı `od:` ve kullanılmış makbuz `pt:` (sipariş no, makbuz özeti, vefat edenin adı) — gizlilik politikasında "ödeme kayıtları yasal saklama süresince" yazılı (aydınlatma §5); süre muhasebeciden teyit edilmeli. Bu istisna Google'a da bildirilmeli (Play: saklama sebepleri politikada açık olmalı).

## 5. Cevap şablonları (30 gün içinde)

- **Silindi:** "Kimin Cenazesi hesabınız ve ilişkili verileriniz [tarih] itibarıyla silinmiştir. Yasal saklama gereği yalnız ödeme kaydı [varsa] tutulur."
- **Kayıt bulunamadı:** "Verdiğiniz bilgilerle eşleşen bir kaydımız yok; varsa süresi dolduğu için silinmiş olabilir."
- **Ret (md.13):** gerekçesi yazılır; Kurul'a şikâyet hakkı belirtilir.
- Ölen yakınının ilanının kaldırılması: ilan "Bildir" ile veya e-postayla gelirse **talep değerlendirilir ve kural olarak kaldırılır** (Kurul'a göre vefat eden ilgili kişi değildir — 2019/273 — ama yakınların hakları ve ilan gerçekten yakınının talebiyse gerekçesiz reddedilmez; ürün kararı).

---
**Dayanılan resmî belgeler:**
- Silme Yönetmeliği (md.7, md.11, md.12): https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK
- Silme/yok etme sayfası: https://www.kvkk.gov.tr/Icerik/2038/kisisel-verilerin-silinmesi-yok-edilmesi-veya-anonim-hale-getirilmesi
- Veri Sorumlusuna Başvuru Usul ve Esasları Tebliği (md.5): https://www.resmigazete.gov.tr/eskiler/2018/03/20180310-6.htm
- İlgili Kişinin Hakları: https://www.kvkk.gov.tr/Icerik/2036/Ilgili-Kisinin-Haklari
- Google Play hesap silme: https://support.google.com/googleplay/android-developer/answer/13327111
