# Kimin Cenazesi — Kişisel Verilerin Korunması Aydınlatma Metni (KVKK md.10)

Sürüm 0.2 taslak · Hukuki danışmanlık değildir; resmî rehberlere dayanır (altta). `[…]` alanlarını sahibi doldurur.
Not: Kod ne yapıyorsa metin onu söyler (`deploy/aile-worker/src/*.js`, `uygulama/lib/**`, 15.10.2026 durumu).

---

## 1. Veri sorumlusu

- **Veri sorumlusu:** [AD SOYAD / UNVAN — sahibi doldurur]
- **Adres (tebligat):** [ADRES — sahibi doldurur]
- **İletişim:** yonetici@kimincenazesi.com
- Uygulama: Kimin Cenazesi (Android, paket `com.kimincenazesi.app`)

(Tebliğ md.4: veri sorumlusunun kimliği aydınlatmanın asgari içeriğidir. Play Console bireysel hesapta yasal ad zaten mağazada görünür — URUN-TASLAGI §18.)

## 2. Bu metin kimleri kapsar?

Metin üç ayrı gruba ayrı ayrı hitap eder (Tebliğ md.5: amaç değişince/işlem ayrıysa ayrı aydınlatma):

- **A. Uygulamayı yalnız okuyanlar** (hesap açmayanlar)
- **B. Din görevlisi olarak kaydolanlar**
- **C. "Tam Sayfa" ilan verenler** (cenaze yakını, 200 ₺)
- **D. Cenaze ilanlarında adı geçen kişiler** (vefat eden ve ilan metninde geçen yer/zaman bilgisi)

## 3. A — Yalnız okuyanlar

| Ne | Nerede | Neden |
|---|---|---|
| Seçtiğiniz il ve ilçe, tema, bildirim tercihiniz, "Sayfam" kayıtları ve sayaçlar, son indirilen liste | **Yalnız telefonunuzda.** Sunucumuza gönderilmez; uygulamayı silince silinir. | Uygulamanın çalışması |
| Cenaze ilanı listesini indirmek için ağ isteği | Cloudflare üzerindeki veri adresi. İstekte ad, telefon, cihaz kimliği, konum **gönderilmez**. İsteğin hangi il dosyasına yapıldığı ve IP adresi, barındırma hizmetinin teknik kayıtlarında kısa süre görünebilir; biz bunu kişilerle eşleştirmeyiz. | İlanları göstermek |
| Bildirim (isteğe bağlı) | Bildirim **telefonunuzda üretilir**; telefon arka planda seçtiğiniz ilin listesine bakar, o gün ilan varsa 08:00 sularında bildirim gösterir. Konum bilgisi alınmaz; "bölgeniz", sizin seçtiğiniz il/ilçedir ve cihazda durur. | Sizi bilgilendirmek |

Bildirim izni ilk açılışta size sorulur ("Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?"). "Şimdi değil" derseniz bildirim gönderilmez; izni telefon ayarlarından istediğiniz zaman kapatabilirsiniz.

Hukuki sebep: bu grupta bizde tutulan kişisel veri yoktur; ağ isteğinin teknik kaydı için KVKK md.5/2-f (meşru menfaat: hizmetin güvenli sunulması). Bildirim, yalnız sizin izin kararınıza ve cihazınızdaki tercihe dayanır.

## 4. B — Din görevlisi olarak kayıt

**Hangi veriler:** Diyanet e-posta adresiniz (kullanıcı adınız@diyanet.gov.tr), ad-soyadınız, unvanınız, görev yeriniz (il, ilçe, cami/köy adı), hesabın durumu ve doğrulama zamanı, bu aydınlatmayı okuduğunuzu belirten kabul tarihi, oturum belirteci özeti ve paylaştığınız ilanlar ile otomatik ilanlar için yaptığınız düzeltmeler. **Telefon numaranız ve personel kartı fotoğrafınız toplanmaz.**

**Nasıl toplanır:** uygulamada Diyanet kullanıcı adınızı siz yazarsınız; Diyanet'in size tahsis ettiği e-posta adresine tek kullanımlık 6 haneli kod göndeririz, kodu uygulamaya yazarsınız. Ad-soyad, görev yeri ve unvanı ilk ilanınızdan önce siz girersiniz. Diyanet e-posta kutunuza ya da şifrenize biz girmeyiz; kutuyu kendi tarayıcınızda siz açarsınız.

**Amaç:** (1) din görevlisi olduğunuzu e-posta koduyla teyit etmek; (2) size ilan paylaşma ve düzeltme panelini açmak; (3) kötüye kullanımı (bildirilen ilanlar, aşırı kod isteği) önlemek.

**Hukuki sebep (md.5/2):** sözleşmenin kurulması/ifası (c) — panel hizmetini vermek; meşru menfaat (f) — kimlik teyidi ve kötüye kullanımın önlenmesi. Verileriniz Cloudflare sunucularında tutulduğundan yurt dışına aktarılır (bkz. bölüm 7).

**Saklama:**
| Veri | Süre |
|---|---|
| E-posta doğrulama kodu | 10 dk geçerli, tek kullanımlık; 5 yanlış denemede iptal; günde en çok 5 kod istenir |
| Oturum | 180 gün |
| Hesap (e-posta kullanıcı adı, ad-soyad, görev yeri, unvan, il-ilçe, kabul tarihi) | Siz silinmesini isteyene ya da sahibi hesabı kapatana kadar |
| Paylaştığınız ilanlar ve düzeltmeler | 120 gün sonra kendiliğinden silinir |
| Kod isteği sayacı | Aynı gün içinde |

## 5. C — "Tam Sayfa" ilan verenler

**Veriler:** başvuran ad-soyadı, telefon, vefat edenle yakınlığınız; ilan metni (vefat edenin adı vb., bkz. D); ödeme makbuzu bilgileri (sipariş numarası, satın alma belirtecinin özeti). Kart/ödeme bilgileriniz **bize gelmez**; ödeme Google Play Faturalandırma üzerinden yapılır.

**Amaç:** telefonunuzu doğrulamak, ilanı yayımlamak, ödemeyi doğrulamak ve mükerrer/hileli kullanımı önlemek.

**Hukuki sebep:** sözleşmenin kurulması/ifası (md.5/2-c); ödeme kayıtları için hukuki yükümlülük (md.5/2-ç) [kayıt süresi için muhasebeci teyidi — sahibi]; kötüye kullanımı önleme için meşru menfaat (md.5/2-f).

**Saklama:** başvuran adı, telefonu ve IP özeti **30 gün sonra silinir**; ilan 120 gün yayında kalır. Telefon numarasının tek yönlü özeti en çok 7 gün (telefon başına ilan sınırı için) tutulur. Ödeme kaydı (sipariş no, belirteç özeti, vefat edenin adı) şimdilik süre sınırı konmadan tutulur [sahibi: yasal saklama süresini muhasebeciden teyit edip kayda bağlayacak].

## 6. D — Vefat edenin ve cenaze ilanında geçen bilgiler

Uygulamada, belediye ve müftülük gibi kamuya açık kaynaklarda yayımlanan ve din görevlisi ya da cenaze yakınlarınca bize bildirilen cenaze ilanları gösterilir: vefat edenin adı, yaşı, cenaze namazı yeri-vakti, defin yeri, mahalle/köy.

- Kişisel Verileri Koruma Kurulu, kişisel veri sahibinin "gerçek kişi" olduğunu ve ölümle kişiliğin sona erdiğini belirterek ölen kişiye ilişkin başvuruyu Kanun md.11 kapsamında ilgili kişi başvurusu saymamıştır (Kurul, 18.09.2019, 2019/273). Ancak ilandaki bilgiler (aile adı, yer) hayatta olan yakınlarla ilişkilendirilebildiği ölçüde onların da verisi olabilir; bu yüzden ilan kaldırma talepleri her zaman değerlendirilir: yonetici@kimincenazesi.com.
- Hukuki sebep: ilanlar kamuya duyurulmuş bilgilere ve ilan sahibinin bildirimine dayanır; meşru menfaat (md.5/2-f). Din görevlisinin bildirdiği ilan, hesabı kapatılınca kaldırılır.
- İlan kaldırma: ilanın üzerindeki "Bildir" düğmesi (iki ayrı cihazdan bildirimde ilan gizlenir) ya da e-posta.
- Şehit ilanları yalnız din görevlisi panelinden girilir.

## 7. Verilerinizin aktarıldığı taraflar ve yurt dışı

Aşağıdakiler bizim adımıza ve talimatımızla veri işleyen hizmet sağlayıcılardır; verinizi kendi amaçlarıyla satmaz/paylaşmaz:

| Taraf | Ne için | Hangi veri |
|---|---|---|
| Cloudflare (barındırma, veri depolama, Workers AI) — yurt dışı | Sunucu, kayıt, kart yazılarının okunması | B ve C'deki tüm veriler; kart fotoğrafı (bellekte) |
| Netgsm — Türkiye | SMS ile doğrulama kodu / onay haberi | Telefon numarası, kod |
| WhatsApp (Meta) Cloud API — yurt dışı [kullanıma açıldığında] | Doğrulama kodunu WhatsApp'tan göndermek | Telefon numarası, kod |
| Google Play (Faturalandırma) — yurt dışı | Tam Sayfa ödemesi | Ödeme verisi doğrudan Google'a verilir; bize sipariş numarası ve makbuz özeti gelir |

Yurt dışına aktarım Kanun md.9'a uygun güvencelerle yapılır [sahibi: Cloudflare/Meta için Kurul'un standart sözleşmesinin imzalanıp Kurum'a bildirildiğini burada belirtin — bkz. RAPOR]. Veriler hiçbir zaman reklam/pazarlama amacıyla kullanılmaz ve satılmaz. Yasal talep olmadıkça kamu kurumlarına aktarılmaz.

## 8. Haklarınız (KVKK md.11)

Bize başvurarak şunları isteyebilirsiniz: verinizin işlenip işlenmediğini öğrenme; işlenmişse bilgi isteme; işlenme amacını ve amaca uygun kullanılıp kullanılmadığını öğrenme; yurt içi/yurt dışı aktarıldığı kişileri öğrenme; eksik/yanlış işlenmişse düzeltme; silme veya yok edilme; bu işlemlerin aktarılan kişilere bildirilmesi; yalnızca otomatik sistemle analiz sonucu aleyhinize bir sonuca itiraz; kanuna aykırı işleme nedeniyle zararın giderilmesi.

**Nasıl:** uygulamada *Din görevlisi paneli → Hesabı sil* (ya da bilgi talebi için e-posta) veya yonetici@kimincenazesi.com. Başvuruda ad-soyad, kayıtlı telefon, talep konusu belirtilir; kimliğinizi kayıtlı telefonunuza gönderilecek kodla doğrularız. En geç **30 gün** içinde yanıtlarız. Başvurunuz reddedilir veya yanıtsız kalırsa Kişisel Verileri Koruma Kurulu'na şikâyet hakkınız saklıdır.

Rızanızı istediğiniz an geri alabilirsiniz; geri alma ileriye dönük sonuç doğurur.

## 9. Veri güvenliği

Tüm iletişim HTTPS ile yapılır; doğrulama kodları ve oturum belirteçleri yalnız özet (hash) hâliyle saklanır; kart fotoğrafı veri tabanına yazılmaz; kimlik numarası cihazda örtülür; yönetim ve onay uç noktaları gizli anahtarla korunur; IP adresleri yalnız tuzlanmış özet olarak ve hız sınırı için kullanılır.

---
**Dayanılan resmî belgeler:**
- Aydınlatma Yükümlülüğünün Yerine Getirilmesinde Uyulacak Usul ve Esaslar Hakkında Tebliğ, RG 10.03.2018 sayı 30356 (md.4 asgari içerik, md.5 usul): https://www.resmigazete.gov.tr/eskiler/2018/03/20180310-5.htm ; KVKK duyurusu/rehber: https://www.kvkk.gov.tr/Icerik/5395/Aydinlatma-Yukumlulugunun-Yerine-Getirilmesi-Rehberi-Kurum-Internet-Sayfasinda-Yayinlanmistir-
- Aydınlatma Yükümlülüğü sayfası: https://www.kvkk.gov.tr/Icerik/2033/Aydinlatma-Yukumlulugu-
- İlgili Kişinin Hakları: https://www.kvkk.gov.tr/Icerik/2036/Ilgili-Kisinin-Haklari
- Veri Sorumlusuna Başvuru Usul ve Esasları Hakkında Tebliğ, RG 10.03.2018: https://www.resmigazete.gov.tr/eskiler/2018/03/20180310-6.htm
- Kişisel Verilerin İşlenme Şartları: https://www.kvkk.gov.tr/Icerik/4190/Kisisel-Verilerin-Islenme-Sartlari
- Ölü kişi verisi: Kurul Karar Özeti 2019/273: https://www.kvkk.gov.tr/Icerik/6710/2019-273
- 7499 sayılı Kanun (md.6 ve md.9 değişikliği), RG 12.03.2024: https://www.resmigazete.gov.tr/eskiler/2024/03/20240312-1.htm
