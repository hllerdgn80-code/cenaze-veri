# Play Store paketi — Kimin Cenazesi v0.1 kapalı test (08.10.2026)

Amaç: bireysel geliştirici hesabında üretime çıkabilmek için Google'ın şartı olan **kapalı test: en az 12 testçi × kesintisiz 14 gün** süresini bir an önce başlatmak. Bütün düğmeler (ödeme, kimlik, yükleme, gönderim) **sahibindir**; asistan metinleri, dosyaları ve derlemeyi hazırlar.

Paket adı: `com.kimincenazesi.app` · Uygulama adı: **Kimin Cenazesi** · Sürüm: 0.1.0 (sürüm kodu = GitHub derleme numarası)

---

## A. Sıra (sahibin adımları)

1. **Geliştirici hesabı** — play.google.com/console → "Kendim için (bireysel)" → kayıt ücreti **25 $** (tek sefer, kartla). Hesap türü: Kişisel.
   - Not (URUN-TASLAGI §18–§20): bireysel hesapta **yasal ad, ülke ve geliştirici e-postası mağazada görünür**; kabul edilmişti. Geliştirici adı alanına "Kimin Cenazesi" yazılabilir.
2. **Kimlik doğrulama** — Play Console'un istediği resmî kimlik (nüfus cüzdanı) + adres; telefon ve e-posta doğrulaması; çoğu yeni hesapta ayrıca **"gerçek bir Android cihaza erişim"** doğrulaması (telefona Play Console uygulamasını kurup giriş). Onay birkaç saat–birkaç gün sürebilir.
3. **Uygulama oluştur** — "Uygulama oluştur": ad *Kimin Cenazesi* · varsayılan dil *Türkçe – tr-TR* · *Uygulama* · *Ücretsiz* · beyan kutuları (Geliştirici Program Politikaları, ABD ihracat yasaları).
4. **Mağaza girişi ve uygulama içeriği** — aşağıdaki §B–§E cevaplarıyla doldurulur (her bölümde "Kaydet").
5. **AAB üret** — `deploy/ANDROID-IMZA.md` (anahtar secret'ları) → GitHub Actions → "Android derleme (Kimin Cenazesi)" → Artifacts → `kimin-cenazesi-aab-N` indir, zip'ten `app-release.aab` çıkar.
6. **Kapalı test kanalı** — Test ve yayınla → Test → **Kapalı test** → "Kanal oluştur" (ad: *Kapalı test – v0.1*) → **Ülkeler/bölgeler: Türkiye** → **Testçiler: e-posta listesi** oluştur ("Kimin Cenazesi testçileri"), §F'deki 12+ Gmail adresini ekle → "Geri bildirim URL'si / e-posta": iletisim@… (alan adı yoksa hesap e-postası).
7. **Sürüm oluştur** — Kapalı test → "Yeni sürüm oluştur" → **Play Uygulama İmzalama: Devam / Kabul** (Google asıl anahtarı saklar) → `app-release.aab` yükle → sürüm adı `0.1.0 (N)` → sürüm notu (§D) → "Sonraki" → "Kapalı teste sun / İncelemeye gönder". İlk inceleme birkaç saat–birkaç gün.
8. **Katılım bağlantısı** — Kapalı test → Testçiler sekmesi → **"Web'de katıl" bağlantısını** kopyala; §F'deki mesajla testçilere gönder (gönderen sahip). Her testçi: bağlantıyı **kendi Gmail hesabıyla** aç → "Test kullanıcısı ol" → aynı sayfadaki Play bağlantısından uygulamayı kur.
9. **14 gün** — en az **12 testçi**, kesintisiz **14 gün** testte kalmalı (katılımdan çıkmamalı, uygulamayı silmemeli). Sayaç Kontrol Paneli'nde görünür. Güvence için 15–20 kişi davet edin; ara sürümler (yeni AAB) süreyi bozmaz.
10. **Üretim erişimi başvurusu** — 14 gün dolunca Kontrol Paneli → "Üretime erişim için başvur": test nasıl yapıldı, testçiler nasıl bulundu, geri bildirimler, uygulamada ne değişti, üretime neden hazır — sorularına kısa cevap (asistan taslak hazırlar). Onay genelde ≤7 gün.

---

## B. Mağaza girişi (Ana mağaza girişi)
Kaynak: `tasarim/METIN-SOZLUGU.md §13` (kaynak/yöntem anlatılmaz; "haber", "ücretsiz", "yeni", ünlem, rakamla ilan sayısı YOK).

| Alan | Değer | Sınır |
|---|---|---|
| Uygulama adı | **Kimin Cenazesi: Cenaze İlanı** | 28 / 30 |
| Kısa açıklama | **Şehrinizdeki cenazelerden haberdar olun.** | 79 / 80 (sahibi mottosu 15.10.2026: "Şehrinizdeki cenazelerden haberdar olun" — Play tanıtım yazısında ve uygulama giriş ekranında; açılış görselinde DEĞİL) |

**Uzun açıklama** (≤ 4000):
```
Kimin Cenazesi — şehrinizdeki cenazelerden haberdar olun. Uygulama, cenaze ilanlarını her sabah bir arada gösterir: vefat edenin adı, cenaze namazının kılınacağı cami ve vakit, defin yeri. Rahmetle andığınız kişileri Sayfanıza ekleyebilir, onlar için okuduğunuz Fâtiha ve Yâsîn’leri sayabilirsiniz.

İlinizi ve ilçenizi bir kez seçersiniz; uygulama her açılışta o günün cenaze ilanlarıyla açılır. Tarih şeridinden son yedi güne bakabilirsiniz.

Uygulamada neler var:
• Cenaze İlanları: il ve ilçenize göre, cenaze günüyle birlikte
• Sayfam: eklediğiniz bilgiler silinmez; Fâtiha, Yâsîn, dua, Kur’ân-ı Kerîm hatmi ve Kelime-i Tevhid hatmi için kendi sayaçlarınız
• Dualar ve Âyetler: ölümle ilgili âyetler, hadisler, menkıbeler ve vefat eden yakınlarımız için dualar; Arapça metni, okunuşu ve sade anlamıyla
• Hatırla: Kaybettiklerimiz ve Tarihte Bugün hayatını kaybedenler
• Açık ve koyu tema

Cenaze bilgisi henüz bulunmayan illerde yakınlar cenaze ilanını paylaşabilir; ilan kontrolden sonra yayımlanır.

Hesap açmanız gerekmez. Seçtiğiniz adres ve Sayfanıza eklediğiniz bilgiler yalnız telefonunuzda tutulur. Uygulamada reklam yoktur, konum izni istenmez.

Allah rahmet eylesin.
```

**Görseller**
| Öğe | Dosya | Şart |
|---|---|---|
| Uygulama simgesi | `deploy/magaza/ikon-512.png` (16.10.2026: sahibinin seçtiği tabutlu daire simge, lacivert zemin; kaynak `tasarim/acilis/simge22.png`; eski L13 kaldırıldı) | 512×512 PNG, ≤1 MB |
| Özellik grafiği | GitHub Actions → "Android derleme" → Artifacts → `magaza-gorselleri` → `ozellik-grafigi-1024x500.png` (kaynak `uygulama/magaza/ozellik-grafigi.svg`: L13 + "Kimin Cenazesi" + "İL VE İLÇENİZDEKİ CENAZE İLANLARI", ortalı) | 1024×500 PNG/JPEG |
| Telefon ekran görüntüleri | aşağıdaki 8 ekran | 2–8 adet, 9:16, kenar 320–3840 px (öneri 1080×1920) |

**Ekran görüntüleri (8)** — **HAYALİ adlarla** (gerçek kişi adı mağazada yer almaz). Kaynak: `tasarim/prototip.html` örnek verisi hayali adlarla değiştirilmiş bir kopyasından (asistanın sıradaki işi: `prototip_yap.py`'ye "mağaza" kipi — Ordu kayıtlarının adları/mahalleleri kurgusal adlarla değiştirilir) 390×844 telefon çerçevesi olmadan, 1080×1920'ye ölçeklenerek alınır. Üstüne kısa, ortalı başlık (kömür zemin, altın yazı) eklenir.
1. Açılış — il seçimi ("Bulunduğunuz ili seçin") · başlık: *İlinizi bir kez seçin*
2. İlçe seçimi ("‹ İller", "Tüm ilçeler") · *İlçenizin cenaze ilanları*
3. Cenaze İlanları — bugün, bir ilan kartı (CENAZE · gün · vakit, cami, defin) · *Bugünün cenaze ilanları*
4. Tarih şeridi başka gün seçili + "İl geneli" bölümü · *Son yedi gün*
5. Sayfam — sayaçlar (Merhuma 1 Fâtiha okudum …) · *Rahmetle andıklarınız*
6. Dualar — dört kutucuk ya da bir dua kartı (Arapça + okunuş + anlam) · *Dualar ve Âyetler*
7. Hatırla — Kaybettiklerimiz kutucukları · *Kaybettiklerimiz*
8. Açık tema — Cenaze İlanları ekranı · *Açık ve koyu tema*

**Kategori ve iletişim**
- Uygulama türü: Uygulama · **Kategori: Yaşam Tarzı** (URUN-TASLAGI §30; "Haber ve Dergi" seçilmez)
- Etiketler (en çok 5, Play listesinden): Yaşam tarzı · Din (varsa) · Referans
- E-posta: iletisim@kimincenazesi.com (alan adı + e-posta yönlendirmesi kurulana dek geliştirici hesabının e-postası) · Web sitesi: boş · Telefon: boş
- **Gizlilik politikası URL'si (geçici):** `https://hllerdgn80-code.github.io/cenaze-veri/kimincenazesi-gizlilik.html` — kaynak `uygulama/web/gizlilik.html`; `topla.yml` her turda site/'ye kopyalar (depoya yükledikten sonraki ilk turda canlı olur, yayından önce tarayıcıda açılıp bakılır). Alan adı gelince `kimincenazesi.com/gizlilik`'e taşınır ve URL güncellenir.

---

## C. Uygulama içeriği (Politika → Uygulama içeriği)

| Bölüm | Cevap |
|---|---|
| Gizlilik politikası | §B'deki URL |
| Uygulama erişimi | **Tüm işlevler özel erişim gerektirmeden kullanılabilir** (giriş yok) |
| Reklamlar | **Hayır, uygulamamda reklam yok** |
| İçerik derecelendirmesi | §C1 |
| Hedef kitle ve içerik | Hedef yaş grubu: **yalnız 18 ve üzeri** · Çocuklara hitap ediyor mu: Hayır |
| Haber uygulaması | **Hayır** |
| COVID-19 izleme / durum | Hayır |
| Veri güvenliği | §C2 |
| Devlet uygulaması | Hayır |
| Finansal özellikler | Uygulamam finansal özellik sunmuyor |
| Sağlık | Sağlık özelliği yok |

### C1. İçerik derecelendirme anketi (IARC)
- E-posta: geliştirici e-postası · Kategori: **"Tüm diğer uygulama türleri"** (Referans, Haber veya Eğitim değil)
- Şiddet: Hayır · Korku/ürkütücü içerik: Hayır · Cinsellik/çıplaklık: Hayır · Küfür/kaba dil: Hayır · Uyuşturucu/alkol/tütün: Hayır · Kumar ya da kumar benzeri: Hayır
- Kullanıcıların birbiriyle iletişim kurması ya da içerik paylaşması (uygulama içinde): **Hayır** (aile formu yalnız kullanıcının kendi e-posta uygulamasını açar; uygulama içinde kullanıcılar arası iletişim yok)
- Konum paylaşımı: Hayır · Dijital ürün satın alma: Hayır (uygulamada hiçbir ücretli ürün/ödeme yok; Tam Sayfa 16.10.2026'da kaldırıldı) · Web tarayıcısı/arama motoru: Hayır
- Beklenen sonuç: Herkes / 3+ (IARC).

### C2. Veri güvenliği formu
- **Uygulamanız gerekli kullanıcı verisi türlerinden herhangi birini topluyor ya da paylaşıyor mu? → Hayır.**
  - Gerekçe (Play tanımı): yalnız cihazda işlenip cihazdan çıkmayan veri "toplanan" sayılmaz. Cihazda tutulanlar: seçilen il/ilçe, tema, Sayfam kayıtları ve sayaçlar, son indirilen ilan listesi (önbellek). Hiçbiri sunucumuza gitmez.
  - Ağ isteği yalnız herkese açık JSON indirir (kimlik, cihaz kimliği, konum gönderilmez).
  - "Cenaze ilanı paylaş" ve "Öneri" kullanıcının KENDİ e-posta uygulamasını açar; gönderimi kullanıcı yapar, uygulama veriyi iletmez.
- Hesap silme bağlantısı: uygulamada hesap yok → gerekmez.
- **Değişince güncellenir:** SMS doğrulama, Firebase, bildirim ya da sunucuya form gönderimi eklendiğinde (v0.2+) bu form yeniden doldurulur (URUN-TASLAGI §28: önce KVKK sorusu).

---

## D. Sürüm notu (kapalı test, tr-TR)
```
<tr-TR>
İlk deneme sürümü: il ve ilçe seçimi, cenaze ilanları ve son yedi gün, Sayfam ve okuma sayaçları, Dualar ve Âyetler, Hatırla. Görüşlerinizi menüdeki "Öneri ve tavsiyeleriniz" ile iletebilirsiniz.
</tr-TR>
```

---

## E. İzinler ve teknik beyan
- İzin: yalnız `INTERNET` (çalışma anında kullanıcıdan izin istenmez). Konum, kişiler, kamera, bildirim YOK.
- Bildirim, analitik, SMS, Firebase, reklam SDK'sı YOK (v0.1).
- Hedef API: Flutter'ın güncel kararlı şablonu (Play'in güncel hedef API şartını karşılar); minimum Android 5.0 (API 21) ve üzeri (Flutter şablonuna göre).

---

## F. Testçiler (12+, sahip toplar ve gönderir)
- Şart: her biri **Gmail/Google hesabı** olan ve **Android telefon** kullanan kişi. iPhone kullanıcısı sayılmaz.
- Öneri: 15–20 kişi (aile, akrabalar, cami cemaati, arkadaşlar); bazıları kurmayı unutur.
- Liste biçimi (Play Console'a yapıştırılır, virgülle ya da her satıra bir adres):
```
ad1@gmail.com
ad2@gmail.com
…
```
- Testçilere mesaj (WhatsApp; gönderen sahip):
```
Selamün aleyküm. "Kimin Cenazesi" adında, il ve ilçedeki cenaze ilanlarını gösteren bir uygulama hazırladık; Google Play'de yayımlanmadan önce 14 gün denenmesi gerekiyor. Yardımcı olursanız çok memnun oluruz:
1) Bu bağlantıyı telefonunuzda, Play Store'daki Gmail hesabınızla açın: <KATILIM BAĞLANTISI>
2) "Test kullanıcısı ol" düğmesine basın.
3) Aynı sayfadaki "Google Play'den indirin" bağlantısından uygulamayı kurun.
Lütfen 14 gün boyunca uygulamayı silmeyin. Görüşünüzü uygulamadaki menüden yazabilirsiniz. Teşekkür ederiz.
```

---

## G. Bilinen v0.1 sınırları (testçilere ve üretim başvurusuna yazılabilir)
- Uygulamada ücretli ilan / uygulama içi satın alma yok (Tam Sayfa kategorisi 16.10.2026'da kaldırıldı); sekmeler: İlanlar · Sayfam · Dualar · Hatırla.
- Aile formu: gönderim e-posta taslağıyla; SMS ve e-Devlet kodu uygulamada otomatik doğrulanmaz — gelen e-posta kontrol edilir, ilan kontrolden sonra veri dosyasına eklenir. Formdaki "Telefonunuz SMS ile doğrulanır" maddesi bu yüzden v0.1'de gösterilmez.
- iletisim@kimincenazesi.com adresi **alan adı alınıp e-posta yönlendirmesi kurulana dek çalışmaz** — testçiler davet edilmeden önce kurulmalı (sahibin düğmesi: alan adı satın alma + Cloudflare Email Routing).
- Kaybettiklerimiz / Tarihte Bugün verisi canlıya çıkana dek ekranda "Bugün için liste hazırlanıyor" görünür.
