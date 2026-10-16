# Açık rıza — Din görevlisi kaydı (kart fotoğrafı)

Hukuki danışmanlık değildir. Kurum ilkeleri uygulanmıştır (altta). `[…]` sahibi doldurur.

## 0. ÖNCE OKU — Kurum ilkesiyle ilgili uyarı

Kurum'un "Açık Rıza Alırken Dikkat Edilecek Hususlar" sayfasına ve işleme şartları açıklamasına göre: açık rıza (a) belirli bir konuya ilişkin, (b) bilgilendirmeye dayalı, (c) özgür iradeyle verilmiş olmalı; aydınlatma ve rıza iki ayrı adımdır (Tebliğ md.5/f); rıza ispatı veri sorumlusuna aittir; geri alınabilir. Ayrıca Kurum, **açık rıza dışında bir hukuki sebep varken işlemeyi açık rızaya dayandırmanın "aldatıcı ve hakkın kötüye kullanımı" olacağını** söyler.

Bu yüzden iki katmanlı kurulum önerilir:
- Kayıt (ad, görev yeri, telefon) ve kart kontrolü: hukuki sebep md.5/2-c ve 5/2-f; rıza **dayanağı değildir**, aydınlatma yapılır.
- **Açık rıza** yalnız şuna alınır: kart fotoğrafının, yurt dışında bulunan bulut hizmetinde (Cloudflare Workers AI) geçici işlenmesi ve (doğrulanamazsa) en çok 7 gün saklanması. Rıza verilmezse kart yolu kapanır; kişi başvurusunu başka yoldan (sahibinin elle kontrolü; kod tarafında yoktur, öneri) sürdürebilir. NOT: md.9'a göre (7499 sayılı Kanun, 01.06.2024) açık rıza yalnız **arızi** yurt dışı aktarımda dayanaktır; düzenli aktarım için uygun güvence (standart sözleşme vb.) gerekir — bkz. RAPOR §2. Rızayı güvence yerine koymayın.

## 1. Kayıt ekranındaki onay kutuları

Mevcut kutu (kodda var, **değişmez**): doğruluk beyanı — "Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum." (Rıza değil, beyandır.)

**Eklenecek ikinci kutu (kart ekranında, fotoğraf çekilmeden önce; işaretlenmeden kamera düğmesi pasif):**

> ☐ Personel kartımın fotoğrafının, doğrulama amacıyla yurt dışındaki bir bulut hizmetinde geçici olarak işlenmesine açık rıza veriyorum. [Ayrıntı]

(*Ayrıntı* bağlantısı aşağıdaki tam metni açar; aydınlatma metni ayrıca "Gizlilik" sayfasındadır.)

## 2. Tam açık rıza metni

**Açık Rıza Beyanı — Personel Kartı Fotoğrafı**

Veri sorumlusu [AD SOYAD / UNVAN — sahibi doldurur], din görevlisi hesabınızı doğrulamak amacıyla çektiğiniz personel kartı fotoğrafını işleyecektir. Bu işlemle ilgili aydınlatma metnini okudum/okumam için bana sunuldu.

1. **Hangi veri:** Uygulama içi kamerayla çektiğim personel kartı fotoğrafı. Fotoğrafı göndermeden önce kimlik numaram (11 haneli sayı) telefonumda siyah bantla örtülür; örtme yapılamazsa fotoğraf gönderilmez.
2. **Amaç:** Yalnızca kartta "Diyanet İşleri Başkanlığı" ibaresi, adım-soyadım, unvanım olup olmadığını ve kartın gerçek bir kart olup olmadığını denetlemek. Başka hiçbir amaçla kullanılmaz.
3. **Nasıl işlenir ve kime aktarılır:** Fotoğraf, Cloudflare'in yurt dışında bulunabilen "Workers AI" metin okuma hizmetine, bizim adımıza ve talimatımızla **geçici olarak** gönderilir; bellekte okunur.
4. **Saklama:** "KVKK uyarınca personel kartınızın fotoğrafı saklanmaz ve veri tabanında tutulmaz; doğrulama tamamlandığında otomatik olarak silinir. TC kimlik numaranız sistemimizde görünmez." — **Tek istisna:** kart iki denemede doğrulanamazsa fotoğraf, sahibinin elle bakması için **en çok 7 gün** saklanır; karar verilince ya da 7. günün sonunda silinir. Sicil numarasının değeri hiçbir durumda saklanmaz.
5. **Rıza vermek zorunda değilim.** Vermezsem kart fotoğrafı yoluyla doğrulama yapılmaz; uygulamanın okuma işlevleri etkilenmez.
6. **Geri alma:** Rızamı istediğim an, ilerisi için geri alabilirim (yonetici@kimincenazesi.com ya da uygulamadaki *Hesabı sil*). Geri alma, öncesindeki işlemin hukuka uygunluğunu etkilemez.

[Rıza tarihi ve sürümü hesap kaydına yazılır: `riza_kart_tarih`, `riza_surum` — Worker'da henüz alan YOK (öneri, RAPOR §3).]

## 3. Kodla tutarlılık notu (beyan = fiil)

Uygulamadaki mevcut cümle ("fotoğraf saklanmaz… otomatik silinir") kamera ekranında **koşulsuz** yazıyor (`metin.dart:356-357`), ama Worker iki başarısız denemeden sonra fotoğrafı 7 gün KV'de tutuyor (`gorevli.js: fotoSakla = true`, `FOTO_TTL = 7 gün`). Uygulama bu istisnayı sonuçta ayrı bir satırla söylüyor (`gorevliKuyrukUyari`), ama çekimden **önce** koşulsuz söz veriliyor. Önerilen tutarlı cümle (kamera ekranı):

> KVKK uyarınca personel kartınızın fotoğrafı veri tabanında tutulmaz ve doğrulama tamamlandığında otomatik olarak silinir. Yalnızca kart iki kez doğrulanamazsa, en çok 7 gün kontrol için saklanır, sonra silinir. TC kimlik numaranız cihazınızda örtülür ve sistemimizde görünmez.

("sistemimizde görünmez": cihazdaki otomatik örtme tanıyıcı yalnız 11 haneli diziyi/etiket yanındaki sayıyı bulabilir; kart düzeni beklenmedikse örtme başarısız olur ve fotoğraf GİTMEZ — yani vaat doğrudur; yalnız örtülemeyen kartta kullanıcı yeniden çeker.)

---
**Dayanılan resmî belgeler:**
- Açık Rıza Alırken Dikkat Edilecek Hususlar: https://www.kvkk.gov.tr/Icerik/2037/Acik-Riza-Alirken-Dikkat-Edilecek-Hususlar
- Aydınlatma Tebliği md.5 (aydınlatma ile rıza ayrı adım; amaç belirli, anlaşılır): https://www.resmigazete.gov.tr/eskiler/2018/03/20180310-5.htm
- Kişisel Verilerin İşlenme Şartları (açık rıza dışı şart varken rızaya dayanmak): https://www.kvkk.gov.tr/Icerik/4190/Kisisel-Verilerin-Islenme-Sartlari
- 7499 sayılı Kanun, md.9 (arızi aktarımda açık rıza; düzenli aktarımda güvence), RG 12.03.2024: https://www.resmigazete.gov.tr/eskiler/2024/03/20240312-1.htm
