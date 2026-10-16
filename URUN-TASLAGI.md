# Cenaze İlanları Uygulaması — Ürün Taslağı (site sahibinin fikri, 05.10.2026)

> **ANA TEMEL (site sahibi, 05.10.2026):** uygulamanın asıl işi GÜNLÜK CENAZE İLANLARINI göstermek. Listem/sayaç, ölüm bölümü, ücretli ilan, Kaybettiklerimiz YAN özelliklerdir; ana ekranı ve akışı bastırmaz. Tasarım tamamen SİMETRİK ve PREMIUM his verir.

## 1. Ana akış
- İlk açılış: il seç → ilçe seç (Ezan Pro mantığı). Seçim cihazda saklanır, sonra değiştirilebilir.
- Ana ekran: seçilen ilçenin **bugünkü** cenaze ilanları; tarih şeridiyle **son 7 gün**.
- İlan kartı alanları (Ordu Belediyesi biçimi): Ad Soyad · Anne/Baba · İl/İlçe · Mahalle · Vefat tarihi · Doğum tarihi · Defin yeri · Defin zamanı · Namaz yeri/vakti · Kaynak (ör. "Ordu Belediyesi").

## 2. Listem (kişisel)
- Her ilan kartında **⋮ menü → "Listeme ekle"**.
- Listeme eklenen ilan **hiç silinmez** (7 günlük pencere dışında da kalır; cihazda + isteğe bağlı hesapta saklanır).
- Listedeki her ilanın altında sayaçlar: **"Yâsîn okudum" (Yâsîn 1, 2, 3…)**, **"Fâtiha okudum"**, isteğe bağlı İhlâs/Kur'an hatmi vb. Her dokunuş sayacı 1 artırır.
- (Öneri) Aile paylaşımı: aynı ilanı listesine ekleyenlerin toplam sayacı ("Bu merhum için 37 Yâsîn okundu").

## 3. Ölüm bölümü (ana menü)
- Ölümle ilgili âyetler · hadisler · menkıbeler · ölüye okunması tavsiye edilen dualar (Yâsîn, Fâtiha, Mülk vb. Arapça + okunuş + meal).
- **Telif notu:** Arapça metinler serbest; **meal ve hadis tercümeleri telifli olabilir** (ör. Diyanet meali). Telif süresi dolmuş mealler (ör. yazarı 70+ yıl önce vefat etmiş) ya da kendi sade çevirimiz kullanılır; her metinde kaynak yazılır.

## 4. "Cenaze ilanı ver" (belediyesi ilan yayımlamayan yerler için)
- Form: Ad Soyad, Anne/Baba, Doğum tarihi, Vefat tarihi, İl, İlçe, Mahalle, Defin yeri (mezarlık), Defin zamanı (ör. "öğle namazından sonra"), Namaz yeri.
- **Gönder** → ilan otomatik olarak seçilen il/ilçe sayfasına düşer, kartta "Yakını tarafından eklendi" etiketiyle.
- **Kötüye kullanım önlemi (gerekli):** sahte/şaka ölüm ilanı ailelere çok büyük zarar verir. Asgari önlem: telefon numarasıyla SMS doğrulama, cihaz başına günlük sınır, her ilanda "Bildir" düğmesi, 2–3 bildirimde ilan otomatik gizlenir, aynı kişi için belediye ilanı gelince kullanıcı ilanı onunla birleşir.

## 5. Veri
- Belediye sitelerinden günlük otomatik okuma (kazıma serbest, 05.10.2026 kararı; kaynak gösterilir, düşük sıklık).
- Araştırma: `arastirma/veri-kaynaklari-2026-10-05.md` (kapsama, biçim, Ordu pilotu).

## 6. Açık sorular (sonra)
- Platform: önce Android mı, ikisi birden mi · uygulama adı · gelir modeli (reklam? bağış? ücretsiz) · hesap gerekli mi (Listem cihaz değişince kaybolmasın diye).

## 7. Ücretli "Ülke Geneli İlanlar" penceresi (site sahibinin fikri, 05.10.2026)
- Ana menüde ayrı pencere: il/ilçe fark etmeksizin herkesin gördüğü, özel tasarımlı ücretli vefat/anma ilanları (gazetelerdeki büyük aile ilanları örnek alınır).
- En üstte "Bu sayfaya ilan ver" bağlantısı → hizmet listesi: ülke geneli görünürlük · ilan metni hazırlanır (gazete kalıbı: "Değerli eşimiz, babamız…", âyet/dua seçeneği) · isteğe bağlı fotoğraf, köşesine otomatik siyah kurdele · cami ve mezarlık konumu (haritada aç / yol tarifi) · tek seferlik **200 TL**.
- **Ödeme:** ilan uygulama içinde tüketilen dijital hizmet → Apple kuralı 3.1.1 gereği uygulama içi satın alma (IAP) zorunlu (developer.apple.com/app-store/review/guidelines, 05.10.2026'da okundu); Google Play'de de aynı. Mağaza payı küçük geliştiricide %15 → ilan başına net ~170 TL.
- **Sahte ilan önlemi (ücretli ilanda daha kritik):** yayından önce kontrol — belediye kaydıyla eşleşme ya da veren kişiden kısa doğrulama (ör. defin belgesi fotoğrafı, yalnız bizde kalır, ilan yayımlanınca silinir). İlk aşamada her ilan kontrol edilir.
- Konum: cami/mezarlık koordinatı OpenStreetMap'ten (ücretsiz, kaynak gösterilir) ya da ilan verenin haritada işaretlediği nokta.
- Site sahibine düşen: Google Play geliştirici hesabı (tek sefer 25 $), Apple Developer (yıllık 99 $), ödeme alabilmek için vergi kaydı (şahıs şirketi) — hepsi sahibin düğmesi.

## 8. Yayın planı (site sahibi kararı 05.10.2026)
1. Uygulama yalnız okunabilen ~30 il ile kurulur, Play Store ve App Store'da yayımlanır.
2. Sonra verisi olmayan illerin belediyelerine e-posta: "Böyle bir uygulama yaptık, ilinizin verisi yok; paylaşırsanız ilinizi ekleyelim." (Taslakları asistan hazırlar, gönderen site sahibi.)
3. O zamana kadar bu illerde "Cenaze ilanı ver" formu açık kalır.

## 9. İlçesi belli olmayan ilanlar (karar 05.10.2026)
Gaziantep, Osmaniye ve Kayseri kaynakları ilçe yazmıyor. Uygulamada ilçe sayfasının altında "İl geneli (ilçe belirtilmemiş)" bölümü gösterilir; ilçe seçen kişi bu ilanları da görür. Sonraki adım: mezarlık → ilçe eşleme tablosu (mezarlığın konumu bir yer bilgisidir, kişi hakkında çıkarım değildir; OpenStreetMap'ten). Taziye adresinden ilçe ÇIKARILMAZ (KVKK).

## 10. "Kaybettiklerimiz" menüsü (site sahibinin fikri, 05.10.2026)
- Kutucuklar: Vefat eden cumhurbaşkanlarımız · başbakanlarımız · bakanlarımız · siyasetçilerimiz · sanatçılarımız (Kemal Sunal, Adile Naşit…). Liste en yeni vefattan geriye doğru kayar.
- Kart: ad soyad, doğum tarihi, vefat tarihi, vefat yaşı, mezarın bulunduğu şehir, (cumhurbaşkanı/başbakanda) kaçıncı olduğu, görev dönemi, serbest lisanslı fotoğraf.
- "Tarihte bugün vefat edenler": her gün o güne ait yerli ve yabancı önemli kişiler.
- Veri: Wikidata (CC0, telif yok; Wikipedia metni alınmaz). Haftalık yenileme, böylece liste güncel kalır.
- İçerik kuralı (site sahibi): infial yaratacak figürler yazılmaz; İsrail vatandaşları hariç tutulur. Türkiye'ye karşı savaşmış ya da katliamla anılan yabancı liderler ve terör örgütü liderleri OTOMATİK hariç tutulur (site sahibi 05.10.2026: onay beklenmez). Wikidata kuralları + elle liste okuyucu/haric_tutulanlar.json. Türk vatandaşı Yahudi sanatçılar bu kurala girmez.

## 11. Tasarım kuralı (site sahibi 05.10.2026)
Yalnız logo değil, uygulamanın İÇİ de tamamen simetrik ve premium: ortalı başlıklar, eşit kenar boşlukları, kategori kutucukları eşit boy ve ızgarada simetrik, sınırlı renk (marka paletinden), sade ikonlar, cömert boşluk.

## 12. "Merhum adına bağış yap" (fikir, 05.10.2026 — sakıncalar değerlendirildi)
- Para BİZDEN GEÇMEZ: 2860 sayılı Yardım Toplama Kanunu izinsiz bağış toplamayı yasaklıyor; Apple kuralı 3.2.2(iv) (05.10.2026 okundu): onaylı kuruluş olmayan uygulama bağışı yalnız uygulama DIŞINDA (Safari/SMS) toplatabilir.
- Uygulama, kuruluşların kendi "çelenk yerine bağış / anma bağışı" sayfalarına bağlantı verir; bağış orada yapılır.
- Aday kuruluşlar (resmî sayfaları yayından önce açılıp doğrulanacak): Türkiye Diyanet Vakfı, Türk Eğitim Vakfı (çelenk yerine bağış), TEMA (hatıra fidanı), Türk Kızılay, LÖSEV, Darüşşafaka, Mehmetçik Vakfı.

## 13. Marka (site sahibi seçimi 05.10.2026)
- Logo: **L13** — mihrap kemeri + musalla taşı, altın-krem / kömür (marka/svg/L13.svg). Uygulama paleti buradan: kömür #25282D, altın #C9A45C, krem #F2EBDD.
- İsim adayı: **"Cenaze İlanı"** (site sahibinin önerisi). Mağaza kontrolü 05.10: Play'de aynı ad yok; App Store'da "Cenaze İlanları" (2018'den beri güncellenmeyen, 2 puanlı uygulama) var. Öneri: mağaza başlığı "Cenaze İlanı — Bugünün Cenazeleri", ayırt edici alt başlık "İl İlçe Vefat ve Cenaze İlanları".
- **KARAR (site sahibi 05.10.2026): marka adı "Cenaze Vakti"** (tescil edilebilirlik için; "Cenaze İlanı" genel/tanımlayıcı kaldı). Mağaza kontrolü 05.10: Play ve App Store'da çakışma yok. Mağaza başlığı önerisi: "Cenaze Vakti: Cenaze İlanları" (aranan kelime başlıkta kalır). Logo L13.
- Site sahibine düşen: TÜRKPATENT'te marka araştırması + başvuru (öneri sınıflar: 9 mobil uygulama, 35 ilan, 38 bilgi iletimi, 45 cenaze hizmetleri — son seçim marka vekiliyle; ücretli), alan adı satın alma (cenazevakti.com / .com.tr — kayıt firmasında teyit).

## 14. Yerel basın verisi + KAPI (site sahibi kararı 08.10.2026)
- Belediye kaynağı olmayan illerde yerel haber sitelerinin günlük listelerinden YALNIZ OLGU (ad, tarih, cami/vakit, mezarlık, ilçe) alınır; `kaynak_turu: yerel_basin` iç veride kalır, kartta kaynak gösterilmez (§16.5). Sitenin cümlesi, taziye metni, telefon, adres, yakın adı, fotoğraf, ölüm nedeni alınmaz. Risk (FSEK ek m.8 veri tabanı hakkı) site sahibince kabul edildi.
- **KAPI:** yayından önce `okuyucu/kapi.py` (makine denetçisi: zorunlu alan, ad biçimi, tarih penceresi, telefon/TC/adres/ölüm nedeni yok, kopyalanmış cümle yok, tekrar yok) her çalışmada CI'da; kuralı geçmeyen kayıt yayına girmez (`_kapi_red.json`). Ek olarak ana oturum günde bir kez `yerel_basin` örneklerini Sonnet denetçiye okutur (CI içinde LLM yok: ücretli API yasağı).

*(16.10.2026: Tam Sayfa KALDIRILDI, §44 — bu bölümün Tam Sayfa/ödeme/aile formu hükümleri geçersiz)*
## 15. Aile ilan formu — EN AGRESİF kabul ölçütleri (kaynaksız iller için; site sahibi isteği 08.10.2026)
Sıra ile, hepsi ZORUNLU; biri eksikse ilan yayına girmez:
1. **e-Devlet "Ölüm Belgesi" doğrulaması:** başvuran e-Devlet'ten aldığı ölüm belgesinin (ya da "Vefat Bilgisi") BARKOD/doğrulama kodunu girer; moderatör turkiye.gov.tr "Belge Doğrulama" sayfasında kodu doğrular (bu sayfa üçüncü kişilerin belge doğrulaması için açık). Belgedeki ad soyad = ilandaki ad soyad. Belge dosyası bizde saklanmaz, yalnız "doğrulandı" damgası + kod özeti (hash).
2. **Başvuranın kimliği:** telefon numarasına SMS kodu + ad soyad + TC'nin SON 4 hanesi (tam TC saklanmaz). Başvuranın soyadı ile merhumun soyadı ya da anne/baba adı eşleşmeli; eşleşmiyorsa (gelin, damat, komşu) yakınlık derecesi + ikinci bir doğrulama (cami imamı/muhtar telefonu) istenir.
3. **Kimlik fotoğrafı İSTENMEZ.** Gerekçe: kimlik kopyası toplamak KVKK'da ağır yükümlülük (veri sorumlusu kaydı, saklama, sızıntı riski) ve sahteciliğe açık; e-Devlet belge doğrulaması hem daha güçlü hem veri tutmaz.
4. **Tutarlılık denetimi:** cami ve mezarlık o il/ilçede var mı (OSM listesi); defin tarihi vefat tarihinden ≤3 gün sonra; aynı kişi için ikinci ilan yok; kapi.py kuralları.
5. **Kontrol:** ilk 6 ay her aile ilanı yayından önce moderatör (site sahibi/asistan) onayından geçer; onay süresi hedefi 30 dk (cenaze aynı gün olduğu için bildirim ile).
6. **Yayın sonrası:** her ilanda "Bildir" düğmesi; 2 bildirimde otomatik gizleme + inceleme; belediye kaydı sonradan gelirse birleştirme. Sahte ilan tespitinde başvuranın numarası kalıcı engel.
7. **Hukuki metin:** başvuran "bilgilerin doğruluğunu beyan ederim, yanlış beyanın sorumluluğu bana aittir" kutusunu işaretler (TCK 267 iftira / 206 yalan beyan uyarısı metinde).

## 16. Kaynakların ve kodun gizliliği (site sahibi isteği 08.10.2026)
Gerçek: uygulamanın gösterdiği veri her zaman kopyalanabilir; gizlenebilecek olan KOD, KAYNAK HARİTASI ve YÖNTEMdir.
1. **Depo PRIVATE'a alınır** (GitHub'da tek tık). Sonuç: kod, okuyucular, kaynak listesi, raporlar görünmez. Bedel: GitHub Pages ücretsiz planda private depoda çalışmaz; Actions dakikaları private depoda ayda 2000 ile sınırlı (bizim kullanım ~8.000/ay).
2. **Çözüm: self-hosted runner (Mac) tüm işi çalıştırır** — self-hosted dakikalar SAYILMAZ, sınırsız ve ücretsiz; Türkiye'den okuduğu için Kocaeli/Aksaray/Van/Malatya/Milas/Arnavutköy sorunu da biter. Bedel: Mac günde 8 kez uyanık olmalı; ileride 3–4 €/ay Türkiye VPS'ine taşınır.
3. **Veri yayını GitHub Pages yerine Cloudflare Pages/R2** (ücretsiz; Whitehall'da kullanılan hesap): yayımlanan şey yalnız uygulamanın okuduğu JSON. `ozet.json`, `saglik.json`, `kapi.json`, raporlar, kaynak URL'leri YAYIMLANMAZ (yalnız özel panelde).
4. **Uygulama ↔ veri hattı:** JSON'lar tahmin edilemez yolda + uygulamaya gömülü anahtarla (Cloudflare Worker önünde başlık denetimi + hız sınırı + yalnız uygulama User-Agent'ı). Kararlı bir rakip yine çekebilir; amaç kolayca kopyalanmayı engellemek.
5. **KARAR (site sahibi 08.10.2026): kartta kaynak adı YAZILMAZ.** "Doğru bilgiyi verdikten sonra nereden verdiğimiz kimseyi ilgilendirmez." Uygulamaya giden JSON'da `kaynak_ad`/`kaynak_url` alanları BULUNMAZ (yayın adımında soyulur); iç veride (private depo) denetim için kalır. Asistanın tek itirazı kayda geçti: kaynak göstermek hukuken zorunlu değil ama bir yerel site şikâyet ederse iyi niyet savunmasını zayıflatır; karar site sahibinin.
6. **Mağaza listesi** (açıklama, ekran görüntüleri) kaynak sayısı/yöntem anlatmaz; "81 ilde cenaze ilanları" der, "belediye sitelerinden otomatik" demez.
7. Bu klasördeki araştırma raporları ve kod yalnız bu Mac'te ve private depoda durur; hiçbir yere yüklenmez.

*(16.10.2026: Tam Sayfa KALDIRILDI, §44 — bu bölümün Tam Sayfa/ödeme/aile formu hükümleri geçersiz)*
## 17. UYGULAMA KURGUSU — NİHAİ (site sahibi 08.10.2026; §1–§13'ün üstüne geçer)
**İlke:** bu alanda İLK ve EN İYİ olacağız; milyon dolar kazandıran uygulamaların tasarım dilini örnek al (iç tasarım, şekil, renk, şablon, kart düzeni); kaynak ve yöntem GİZLİ; ilk etapta REKLAM YOK (kullanıcıyı bezdirmemek için); tasarım simetrik ve premium (L13 paleti).
**Ana sekmeler (soldan sağa, eşit kutucuklar):**
1. **Cenaze İlanları** (ana ekran): il → ilçe; bugün + son 7 gün; ilan kartı (ad soyad, anne-baba, mahalle, vefat tarihi, yaş, defin yeri/zamanı, namaz yeri/vakti). Kaynak gösterilmez.
   - Kartta **"Kendi sayfama kaydet"** düğmesi → **Sayfam**'a gider; kayıt hiç silinmez.
   - Sayfam'daki her ilanın altında sayaçlar (her dokunuş +1): **1 Fâtiha okudum · 1 Yâsîn okudum · 1 dua okudum · 1 Kur'ân-ı Kerîm hatmi okudum · 1 Kelime-i Tevhid hatmi okudum.**
2. **Tam Sayfa Cenaze İlanı** (gazetedeki ücretli ilanın karşılığı; ana ilanların hemen yanında): ülke geneli görünür ücretli ilanlar. **İlan ver** → §15'teki agresif ölçütler (e-Devlet ölüm belgesi doğrulama kodu, SMS, soyad/anne-baba eşleşmesi, tutarlılık, kontrol) → en sonda **göz korkutucu hukuki onay kutusu** (metin aşağıda) → ödeme (mağaza içi satın alma, 200 TL) → yayın.
3. **Kaybettiklerimiz**: cumhurbaşkanları · başbakanlar · bakanlar · siyasetçiler · sanatçılar (Wikidata; haftalık).
4. **Tarihte Bugün Hayatını Kaybedenler**: günün listesi (Türkler önce).
(Ölüm bölümü — âyet/hadis/dua — ve bağış bağlantıları ikincil menüde kalır.)
**Son onay kutusu metni (taslak, hukuki üslup):**
> "Verdiğim bilgilerin doğru ve eksiksiz olduğunu, ilanı vermeye yetkili yakın olduğumu kabul ve beyan ederim. Yanıltıcı, gerçek dışı veya başkasının hakkını ihlal eden bilgi vermem hâlinde 5237 sayılı Türk Ceza Kanunu'nun ilgili hükümleri (m. 206 resmî belgenin düzenlenmesinde yalan beyan, m. 267 iftira, m. 136 kişisel verileri hukuka aykırı olarak verme) uyarınca hakkımda hukuki ve cezai işlem başlatılmasını, ilanın derhal kaldırılmasını ve hesabımın kalıcı olarak kapatılmasını kabul ediyorum."
> [ ] Okudum, kabul ediyorum.   (Kutucuk işaretlenmeden "Onayla ve öde" düğmesi pasif.)
**Sıradaki üretim adımı:** ekran tasarımı (Figma yerine HTML prototip: 6 ekran, telefon çerçevesinde, L13 paleti, simetrik) → site sahibi onayı → uygulama kodu (Flutter: tek kodla Android + iOS).
- **Açılış davranışı (site sahibi 08.10.2026):** il/ilçe yalnız ilk açılışta sorulur ve kaydedilir; sonraki her açılış doğrudan İlanlar ekranı + kayıtlı ilçe + bugünün ilanları. Sağ üst ⋮ menü: "Adresi değiştir" (yanlış seçimi düzeltme), tema, hakkında, gizlilik. İlçe listesindeyken sol üstte "‹ İller" geri düğmesi. Geri (sol) ve ⋮ (sağ) aynı boy/hizada, başlık ortada.

## 18. Yayıncı kimliği (site sahibi 08.10.2026: "kendi adım, soyadım, hllerdgn80 maili hiçbir yerde geçmesin; kurumsal firma havası veren isim")
- **Mağaza gerçeği (08.10.2026'da okundu):** Google Play, kişisel geliştirici hesabında geliştirici adını serbest bırakır ama **yasal adı, ülkeyi ve e-postayı mağazada gösterir**; satış yapılırsa adresi de (support.google.com/googleplay/android-developer/answer/13628312). Apple, bireysel hesapta **satıcı adı olarak kişinin yasal adını** gösterir; şirket adı için "Organization" hesabı = tüzel kişilik + D-U-N-S numarası + şirket alan adlı e-posta + web sitesi (developer.apple.com/programs/enroll).
- **Sonuç:** adın hiçbir yerde görünmemesi için **şirket (şahıs şirketi yetmez — tüzel kişilik: limited) kurulması** gerekir; zaten ücretli ilan için vergi kaydı şarttı. Bu, yayından önce site sahibinin kararı ve masrafı (limited kuruluş + D-U-N-S ücretsiz, 1–2 hafta).
- **Ara çözüm (şirket kurulana kadar):** uygulama yalnız Google Play'de, geliştirici adı marka adıyla; yasal ad mağaza sayfasında "hakkında" kısmında yine görünür — bu kaçınılmaz.
- **Teknik taraf (hemen):** GitHub kullanıcı adı (hllerdgn80-code) depo adresinde ve Pages adresinde geçiyor → depo private'a alınınca ve veri Cloudflare'e taşınınca görünmez; okuyucu User-Agent'ındaki depo adresi marka adıyla değiştirilir; yeni GitHub hesabı gerekmez. Uygulama içi "hakkında/gizlilik" sayfalarında yalnız şirket adı + kurumsal e-posta (ör. destek@cenazevakti.com; alan adı alınınca).
- **Kurumsal yayıncı adı adayları (marka vekiliyle teyit; "Cenaze Vakti" ürün adı kalır):** Vakit Dijital Yazılım · Rahmet Teknoloji · Hüve'l-Bâkî Bilişim · Musalla Yazılım · Sükûn Dijital · Vefa Bilişim · Andaç Teknoloji · Niyaz Yazılım · Ebedî Dijital · Selâ Bilişim. Önerim: **Vakit Dijital Yazılım Ltd. Şti.** (ürün adıyla uyumlu, nötr, kurumsal; "Vakit" dinî uygulama kitlesine tanıdık).
- **Tema (site sahibi 08.10.2026, son karar): uygulama KOYU temayla açılır** (kömür zemin, altın vurgu); açık tema ⋮ menüden seçilir.

## 19. Ödeme — şirket KURMADAN yol (08.10.2026, kaynaklar okundu)
- **GVK mükerrer 20/B "mobil uygulama geliştiriciliği kazanç istisnası":** gerçek kişi (şirket yok) Play/App Store gibi platformlardan uygulama geliri elde ederse, yıllık ~5,3 milyon TL'ye (2026 tahmini, 4. gelir dilimi) kadar GELİR VERGİSİNDEN MUAF; tek yükümlülük: (1) ikametgâh vergi dairesinden **istisna belgesi** (ücretsiz, e-Devlet/İnteraktif Vergi Dairesi'nden başvuru), (2) tüm hasılat Türkiye'de bu iş için açılan BANKA HESABINA gelir, (3) banka %15 stopaj keser (beyanname yok, defter yok, KDV mükellefiyeti yok — Play/App Store KDV'yi kendileri topluyor). Kaynak: GVK 318 ve 325 seri no.lu Genel Tebliğler (ismmmo.org.tr/dosya/5033), kpmgvergi.com bülteni.
- **Sonuç:** vergi ve şirkete bulaşmadan: bireysel Google Play (25 $) + bireysel Apple (99 $/yıl) hesabı + istisna belgesi + ayrı banka hesabı. Ücretli ilan mağaza içi satın alma ile alınır (Apple 3.1.1 zorunlu), mağaza payı %15–30, kalan banka hesabına.
- **Bedel:** bireysel hesapta mağazada yasal ad görünür (§18). Yani "adım hiçbir yerde geçmesin" ile "şirket kurmayayım" AYNI ANDA olmuyor: ya şirket (ad gizli) ya bireysel + istisna (vergi yok, ad görünür). Site sahibinin seçimi.
- Bağış/ücretli ilan parası uygulama dışından (IBAN) alınırsa istisna da IAP kuralı da bozulur; yapılmaz.

## 20. KARARLAR (site sahibi 08.10.2026)
- **Uygulama adı: "Kimin Cenazesi"** ("Cenaze Vakti" bırakıldı). Play/App Store'da çakışma yok; kimincenazesi.com ve .com.tr DNS'te boş görünüyor (kayıt firmasında teyit). Mağaza başlığı önerisi: "Kimin Cenazesi: Cenaze İlanı". Logo L13 kalır; marka yazısı prototipte güncellendi. TÜRKPATENT araması site sahibinin.
- **Yayın/ödeme yolu: bireysel Play + bireysel Apple hesabı + GVK mük. 20/B istisna belgesi + ayrı banka hesabı** (şirket yok); uygulama tutunca limited kurulup hesaplar şirkete devredilir. Bedel: bireysel hesapta yasal ad mağazada görünür (kabul edildi).

## 21. Verisi olmayan il/ilçe ekranı (site sahibi sorusu 08.10.2026 — karar)
Boş ekran ASLA gösterilmez. Üç durum:
1. **İl var, ilçe yok (ilçesiz kaynak, ör. Gaziantep):** ilçe sayfasının altında "İl geneli" ilanları gösterilir (mezarlık→ilçe eşlemesi yapıldıkça ilçeye düşer).
2. **İlde yalnız bazı ilçeler var (ör. Muğla):** kullanıcının ilçesi yoksa önce o ilde okunan ilçelerin ilanları ("Muğla'da bugün: Bodrum, Fethiye, Milas…") + ilçesi için aile formu daveti.
3. **İlde hiç kaynak yok (17 il + İstanbul/İzmir merkez):** ekran dolu gelir:
   - Üstte sakin bir kart: "Kars'ta ilanlar şu an yakınları tarafından paylaşılıyor." + büyük düğme **"Cenaze ilanı paylaş"** (ücretsiz aile formu; §15 doğrulama, kontrol).
   - (Komşu il gösterimi YOK — site sahibi kararı 08.10.2026.)
   - Altında **"Tarihte bugün"** ve **"Kaybettiklerimiz"** kısa şeritleri (uygulama boş hissettirmez).
   - Bildirim izni teklifi: "İlçenizde ilan paylaşıldığında haber verelim" (push).
   - Aile formuyla gelen ilanlar il/ilçe sayfasında "Yakını paylaştı" rozetiyle (kaynak yazılmaz) normal kart gibi görünür; kapıdan geçer.
4. **Günün boş olması (kaynak var, bugün ilan yok):** "Bugün [ilçe]de ilan yok" + dünden geriye son 7 gün otomatik açılır.

## 22. Bildirim kuralı (site sahibi 08.10.2026)
- Bildirim metni ilanın içeriğini VERMEZ (ad, cami, saat yazılmaz). **Dil kuralı (site sahibi 08.10.2026): cenaze konusunda her kelime hassas; "yeni ilan var", "3 ilan" gibi pazar dili YASAK.** Onaylı kalıp: **"Ünye'de bugünkü cenaze ilanlarını göster"**. Alternatif sakin kalıplar: "Bugün Ünye'de uğurlananlar", "Ünye'de bugün Hakk'a yürüyenler", "Ünye'de bugünkü vefat ilanları". Sayı yazılmaz. Dokununca uygulama o ilçenin bugünkü listesinde açılır.
- **Genel dil ilkesi (uygulamanın her metni için):** satış/pazar kelimeleri yok ("yeni", "fırsat", "kaçırma", "hemen", ünlem), rakamla ölüm sayısı yok, "ilan" kelimesi yerine mümkün olan yerde "vefat", "cenaze", "uğurlama", "Hakk'a yürüdü", "rahmetli", "merhum/merhume"; emir kipi yerine davet ("gösterelim", "bakabilirsiniz"); başsağlığı dili ölçülü, abartısız. Yazılacak her metin bu süzgeçten geçer; ekran metinleri sözlüğü `tasarim/METIN-SOZLUGU.md`'de tutulur.
- Zamanlama: günün ilk okuması sonrası (sabah ~07:00) tek bildirim + gün içinde yeni ilan düşerse en çok 1 bildirim daha (bezdirmemek için günde en çok 2). Gece bildirimi yok (21:00–07:00 sessiz).
- Sayfam'daki merhumlar için isteğe bağlı: "Merhum X için bugün bir Fâtiha" hatırlatması (kullanıcı açarsa; içerik vermez, yalnız ad).
- **Kaynaksız il/ilçe bilgi metni (site sahibi 08.10.2026, yumuşatılmış):** "Seçtiğiniz il ve ilçe için şu an cenaze bilgisi bulunmuyor. Cenaze sahibiyseniz aşağıdaki bağlantıdan cenaze bilgilerini paylaşabilirsiniz; paylaşımınız Ordu – Çamaş sayfasında görünecektir." + düğme "Cenaze bilgilerini paylaş". Site sahibi bunu yine de "can sıkıcı" buldu → asıl çözüm: bu illerde TEK KİŞİLİK yerel vefat haberlerinden (RSS) olgu verisi (yeni ajan turu, `kaynak_turu: yerel_haber`); bilgi metni yalnız gerçekten hiçbir şey yoksa.

## 23. Hastane/morg kayıtları (site sahibi sorusu 08.10.2026) — KAPALI YOL
- Hastane ve morg kayıtları sağlık verisidir: KVKK m.6 "özel nitelikli kişisel veri", hastane bilgi sistemleri (HBYS) ve Sağlık Bakanlığı ÖBS (Ölüm Bildirim Sistemi) yalnız yetkili sağlık personeline açıktır; üçüncü kişi erişimi yasak, izinle bile verilmez. Nüfus (MERNİS) ölüm kaydı da kamuya açık değildir (yalnız e-Devlet'te kişinin yakınına, kişi bazlı). Bu yola GİRİLMEZ.
- Ayrıca bu kayıtlarda defin yeri/vakti zaten YOKTUR: cenaze namazının vakti ve mezarlık, belediye mezarlık müdürlüğünün "defin ruhsatı/mezar yeri tahsisi" işlemiyle belirlenir; yani kaynak yine belediye (okuduğumuz listeler) ya da ailedir. Bu yüzden belediye listesi + aile formu + yerel haber zaten doğru üçlü.

## 24. İlan sahibinin düzeltmesi (site sahibi 08.10.2026)
- (Netleştirme, site sahibi 08.10.2026) İlanı veren kişi uygulamada KENDİ İLANININ üstüne dokununca **"İlanı düzelt"** seçeneğini görür (yalnız ilanı veren doğrulanmış telefonda görünür) ve **düzeltebilir** (ör. namaz vakti öğle → ikindi, cami/mezarlık değişikliği).
- Düzeltme de kapıdan geçer: aynı telefon (SMS kodu yeniden), aynı kişi (önceki doğrulama kaydı), değişen alan için tutarlılık denetimi; **vefat tarihi ve ad soyad değiştirilemez** (yeni kişi = yeni ilan); yalnız namaz vakti, cami, mezarlık, defin tarihi (±2 gün), mahalle düzeltilebilir.
- Düzeltme yayına girmeden önce kontrol (ilk 6 ay) ; onaylanınca kartta küçük "Güncellendi · 14:20" ibaresi; Sayfam'ında bu ilanı kaydetmiş kullanıcılara içeriksiz bildirim: "Kaydettiğiniz bir cenaze ilanında güncelleme var".
- Belediye kaynaklı ilanlar kullanıcı tarafından düzeltilemez; yalnız "Düzeltme bildir" (serbest metin, moderatöre gider).

## 25. Kaynaksız belediyelere kurumsal yazı + "tek tık" veri yolu (site sahibi kararı 08.10.2026)
- Veri olmayan il/ilçe belediyeleri tek listede toplanır; her birine kurumsal dille yazı: uygulamanın amacı (vatandaşın kendi ilçesindeki cenazeleri görmesi), belediyeden istenen şey (günlük cenaze bilgilerini paylaşmak), ve bilgisayardan anlamayan görevliye bile kolay gelecek **üç yol, kolaydan zora**:
  1. **E-posta CC yolu (tek tık, hiç program yok):** belediye zaten defin bilgisini cami/anons/ilçe birimlerine e-postayla gönderiyorsa, o e-postaya bizim adresimizi CC eklemesi yeter; biz e-postadaki şablonu otomatik okuruz. Yazıya hazır tablo şablonu (ad soyad, baba/anne adı, mahalle, vefat tarihi, namaz vakti, cami, mezarlık) eklenir.
  2. **Paylaşımlı çizelge yolu:** bizim açtığımız, yalnız o belediyeye özel bağlantıyla açılan bir çizelge (Google E-Tablo); görevli satır ekler, biz otomatik okuruz. Program bilgisi gerekmez; telefonla da girilir.
  3. **Mevcut mezarlık yazılımında "Vefat Edenler" sayfasını açtırma (bir kez, bilgi işlem):** MEBİS/e-Belediye/MezarlikApp gibi yazılımlarda modül zaten var, çoğu belediyede kapalı; bilgi işlem bir kutucuğu işaretler, sayfa herkese açılır, biz otomatik okuruz (en kalıcı yol).
- Gönderen kimliği: kurumsal e-posta (iletisim@kimincenazesi.com; alan adı alınınca) ve yayıncı adı; kişisel ad/e-posta yok (§18). Yazı ve ekler asistan hazırlar, GÖNDEREN site sahibidir (dış yazışma = sahibin düğmesi).
- Bu, §16'daki "kaynak gizliliği" ile çelişmez: belediye zaten verinin sahibidir; rakibin öğreneceği yeni bir şey yok.
- **Takip (site sahibi 08.10.2026):** belediye yazı listesi canlı bir takip dosyasıdır (`deploy/belediye-takip.md`: belediye · gönderim tarihi · yanıt · seçilen yol · veri akmaya başladığı gün). Olumlu dönen belediye listeden düşer, okuyucusu/kanalı kurulur; 81 ile ulaşana kadar döngü sürer (2 haftada bir hatırlatma yazısı, en çok 3 tur).

## 26. Basitlik ilkesi + Dualar sekmesi (site sahibi 08.10.2026)
- Kullanıcı kitlesi çoğunlukla yaşlı: uygulama mantığı olabildiğince BASİT, kafa karıştırıcı ayrıntı yok, ekranda az öğe.
- Verisi olmayan il ekranında Tarihte Bugün / Kaybettiklerimiz şeritleri GÖSTERİLMEZ (o il'e ait ölenler sanılıyor). Yalnız bilgi kartı + "Cenaze ilanı paylaş" + varsa aile ilanları + bildirim izni.
- Yeni sekme (Sayfam'dan sonra): **Dualar** — 4 kutucuk: ölümle ilgili âyetler · hadisler · menkıbeler · vefat eden yakınlarımız için dualar. Her madde: Arapça + okunuş + sade anlam + kaynak. Telifli meal/çeviri kopyalanmaz.
- Sekme sırası: İlanlar · Tam Sayfa · Sayfam · Dualar · (Kaybettiklerimiz · Tarihte Bugün — sığmazsa tek "Hatırla" sekmesi altında).

## 27. Şehit ilanları (site sahibi 08.10.2026) — uygulama mantığının tamamında
- **Veri:** kayıtta `sehit: true` alanı. Kaynak belirleme: belediye/yerel haber metninde "şehit", "şehidimiz", "şehit düştü", "şehadet" geçiyorsa ve kişi asker/polis/jandarma/güvenlik korucusu/bekçi/itfaiye/sağlık personeli (görev başında) ise işaretlenir; kapi.py bu kayıtta ÖLÜM NEDENİ ayrıntısını yine almaz (yalnız "şehit" işareti), rütbe/unvan alınır ("Jandarma Uzman Çavuş", "Polis Memuru"). Belirsizse işaret konmaz; aile formunda "Şehit" seçeneği yalnız resmî tören bilgisiyle (Valilik/TSK/EGM duyurusu kaynaklı) onaylanır — sahte şehit ilanı en ağır itibar riskidir, kontrol zorunlu.
- **Kart:** şehit kartı farklı ve saygın: üstte ince al şerit (bayrak kırmızısı, paletteki tek istisna) ve "ŞEHİT" etiketi; ad başında rütbe/unvan; "Hakk'a yürüdü" yerine **"şehit oldu"**; cenaze bilgisi: tören yeri (valilik/garnizon/il müftülüğü), cenaze namazı camisi ve vakti, defin (şehitlik). Fotoğraf yok (kural), siyah kurdele yerine ay-yıldız YOK (bayrak kullanılmaz kuralı korunur; yalnız al şerit).
- **Sıralama:** şehit ilanı o gün il/ilçe listesinin EN ÜSTÜNDE; ayrıca şehidin memleketi (sicil ili/ilçesi) ile defin yeri farklıysa her iki yerde de gösterilir (haber "Trabzonlu şehit X Ankara'da toprağa verildi" → Trabzon ilçe sayfası + Ankara).
- **Dil:** METIN-SOZLUGU'na "şehit" kalıpları: "Şehidimiz [Rütbe Ad Soyad]", "Cenaze töreni", "Ruhu şad olsun", "Mekânı cennet olsun"; "vefat etti" yazılmaz. Bildirim: "İlçenizde bir şehit cenazesi var" (içerik yok).
- **Sayfam:** sayaç cümlesi şehit için "Şehidimize 1 Fâtiha okudum" (cinsiyet kalıbı yerine).
- **Tam Sayfa:** şehit ilanında ücret söz konusu edilmez (200 TL alınmaz; ekranda "ücretsiz" ifadesi de GEÇMEZ — sahip 08.10; fiyat kartı yok, doğrudan form; doğrulama resmî duyuruyla; sert kriterler aynen geçerli).
- **Kaybettiklerimiz:** ayrı kutucuk YOK (basitlik); Tarihte Bugün listesinde şehit işareti varsa rütbe gösterilir.
- **Ulusal şehit haberleri:** TSK/İçişleri duyuruları günlük okuyucuya kaynak olarak eklenir (resmî, herkese açık); kayıt il/ilçeye memleket bilgisiyle düşer.

## 28. ÖN OTOPSİ KARARLARI — hepsi kabul (site sahibi 08.10.2026)
- iOS'ta ve genel olarak kartta anne/baba adı GÖSTERİLMEZ (iç veride kalır).
- Yerel basın/yerel haber verisi yayındaki uygulamaya KONMAZ (Play hesabı kalıcı kapanma riski); o illerde aile formu. (Okuyucular iç veride kalır, kullanılmaz.)
- Yâsîn/Fâtiha sayaçları yalnız cihazda; hesaba bağlanmaz.
- Ücretli ilan ilk sürümde KAPALI (adres görünmesi + moderasyon); aile formunda otomatik kapı + "inceleniyor" rozeti; ücretli açılınca "en geç 12 saat, onaylanmazsa iade".
- Ücretli ilan metnini aile yazar, uygulama kalıp önerir (5651 içerik sağlayıcı olmamak için).
- SMS/Firebase açılmadan KVKK danışmanına tek soru (yurt dışı aktarım bildirimi).
- Apple'a Android'den 1–2 ay sonra, bulutta derleme (Codemagic ücretsiz kota).
- Harcama sırası: alan adı → Play (12 test kullanıcısı listesiyle) → istisna belgesi/banka/%15 kaydı → Firebase (bütçe tavanı) → Apple → ertelenen: marka tescili, limited, TR sunucu.
- Sıralama (son): cumhurbaşkanı/başbakan/bakan/siyasetçi vefat tarihine göre 2026'dan geriye; Sanat, Edebiyat ve Bilim tanınırlığa göre. Görev satırı varken meslek satırında aynı kelime tekrar edilmez.
- **Dil kuralı (sahip 08.10.2026): erkek için "merhum", kadın için "merhume"** — kişiye bağlı her metinde (kart, sayaç, dua, bildirim, form) cinsiyete göre doğru biçim; cinsiyet bilinmiyorsa ad listesi → bilinmiyorsa nötr ("vefat eden yakınınız"); asla yanlış cinsiyet yazılmaz. Arapça dualarda zamir farkı (-hu/-hâ) için iki sürüm.
- **İlan formlarında cinsiyet seçimi zorunlu (sahip 08.10.2026):** aile/Tam Sayfa/şehit formunun 1. adımında 'Erkek · Kadın' (Cihan, Deniz gibi iki cinsiyetli adlar için); kayda cinsiyet yazılır, merhum/merhume buna göre.

## 29. Güncelleme saatleri ve "sonradan gelen ilan" bildirimi (site sahibi sorusu 08.10.2026)
- **Okuma turları (TR saati):** 06:47 · 08:47 · 09:47 · 10:47 · 11:47 · 12:47 · 15:47 · 21:47 (8 tur; her tur ~7–10 dk; yani veri en geç ~07:00, 09:00, 10:00, 11:00, 12:00, 13:00, 16:00, 22:00'de yenilenmiş olur). Sabah yoğunluğu bilerek: belediyeler ilanları çoğunlukla 08:00–11:00 arasında giriyor (cenazeler öğle/ikindi).
- **Uygulama her açılışta canlı dosyayı çeker** (son yenileme saati ekranda küçük yazıyla: "Son güncelleme 09:02"); kullanıcı aşağı çekerek de yeniler.
- **Bildirim (cevap: EVET, haber gelir):** sabah ilk turda ilçede ilan yoksa, gün içindeki turlarda o ilçeye İLK ilan düştüğünde bir bildirim: "Ünye'de bugünkü cenaze ilanlarını göster". Sonraki turlarda yeni ilan eklenirse ikinci (ve son) bildirim; günde en çok 2 (§22). Bildirim, kullanıcının seçtiği ilçeye göre; sunucu tarafında her turda "bu ilçede bugün yeni kayıt var mı" farkı alınır (`veri/<il>/son7gun.json` önceki sürümle karşılaştırılır → `veri/yeni-ilanlar.json`), uygulama push ile iletir (Firebase; §28 KVKK notu).
- Tur sıklığı ileride veriyle ayarlanır: hangi saatlerde yeni kayıt düşüyor (ozet'teki `son_guncelleme` ve kayıt sayısı farkları) → turlar oraya kaydırılır. Hedef: bir ilan belediyede göründükten en geç 60 dk sonra uygulamada.

## 30. Görünürlük kararları (08.10.2026, arastirma/gorunurluk-plani-2026-10-08.md)
- Mağaza başlığı "Kimin Cenazesi: Cenaze İlanı" (28 karakter; Play sınırı 30). Kategori **Yaşam Tarzı** ("Haber ve Dergi" kaynak gösterme şartı istiyor → §16.5 ile çelişir); mağaza metninde "haber" kelimesi yok.
- Web: verisiz il/ilçe yönlendirme sayfaları YAPILMAZ (Google "doorway" spam). İl başına bilgi sayfası (namaz vakitleri, mezarlıklar, belediye cenaze hizmeti, uygulama bağlantısı; kişi verisi yok) ile başlanır; 90. günde veriyle yeniden karar.
- Ücretsiz ilk hamleler: uygulama içi paylaş düğmesi (WhatsApp, "Kimin Cenazesi uygulamasından" imzası), pilot ilçelerde QR afiş (imam/muhtar izniyle), ASO, sahibin kendi hesabıyla yerel Facebook grupları + yerel basına tek yönlü e-posta, Türkçe YouTube kanalında bilgi Shorts'ları ("bugün kimin cenazesi var" formatı YOK).
- Ücretli (90. günden sonra): Google App kampanyası 14 gün × 75 TL + Meta il hedefli 14 gün × 50 TL ≈ 1.750 TL ilk test.

## 31. Görünürlük ekleri + belediye toplu gönderim (site sahibi 08.10.2026)
- **"Uygulamayı paylaş" düğmesi** (⋮ menü + Hakkında): WhatsApp / Telegram / diğer; metin hassas dille ("Kimin Cenazesi — il ve ilçenizdeki cenaze ilanları. Play Store: <bağlantı>"); bağlantı doğrudan mağaza sayfasına (UTM ile izlenir). Ayrıca ilan kartında "Cenaze bilgisini paylaş" (ilan + mağaza bağlantısı imzası, §30).
- **"Öneri ve tavsiyeleriniz" düğmesi** (⋮ menü): kısa form (metin + isteğe bağlı e-posta) → iletisim@kimincenazesi.com'a gider (ya da mağaza yorumu değil, kendi kutumuz); teşekkür mesajı; bu metinler haftalık okunur.
- **Belediyelere TOPLU gönderim:** tek tek elle değil; Gmail'den "şu adres olarak gönder" (iletisim@…) + **Gmail'in kendi "Mail Merge" (çoklu gönderim) özelliği** ya da Google E-Tablo + Apps Script ile kişiselleştirilmiş toplu e-posta (her belediyeye [İL/İLÇE] yer tutucusu dolu, aynı anda 50–100). Gönderme düğmesi sahibin; hazırlık (tablo + şablon + ekler) asistanın. Ekler: (1) Ordu örneği ekran görüntüsü (prototipten, hayali/anonim kartlarla değil GERÇEK Ordu listesi görüntüsü; KVKK: ad soyad görünür — belediyenin kendi yayımladığı veri, yine de görüntüde 1 kart + bulanık devamı), (2) Ek-1 kılavuz PDF. Üslup: sıcak ve ikna edici ("Ordu'da böyle çalışıyor; Iğdır'da da olsun ister misiniz?"), vatandaşa hizmet vurgusu, paylaşmanın 2 dakikalık kolaylığı adım adım.
- Sayfam: kayıt kendiliğinden silinmez; kullanıcı ⋮ → 'Sayfamdan kaldır' (onaylı) ile kendisi kaldırabilir (sahip 08.10.2026).
- Sayfam sayaçları (sahip 08.10.2026): Fâtiha · 3 İhlâs ve 1 Fâtiha · Yâsîn · dua · Kur'ân hatmi · Kelime-i Tevhid hatmi (6 satır).

## 32. Kararlar (sahip 08.10.2026)
- **İsimsiz bebek kayıtları gösterilmez** (kapı + yayın süzgeci: "Bebek", "İsimsiz", "Kız/Erkek Bebek" yer tutucuları elenir; adı olan bebek kalır, `bebek: true`).
- **İlan formunda "Vefat eden" seçimi 4 seçenek: Erkek · Kadın · Şehit · Bebek** (Şehit → şehit akışı + cinsiyet; Bebek → ad zorunlu, cinsiyet, yaş gün/ay, kartta "Bebek" rozeti, sayaç "Bebeğimize 1 Fâtiha okudum").
- **Aynı kişi iki kaynakta (Muğla: Fethiye + Seydikemer) → TEK KART** (il içinde ad + ±2 gün eşleşmesi; alanları en dolu kayıt tutulur).

## 33. Play 12 testçi şartı — çözüm (08.10.2026, arastirma/play-testci-cozumleri-2026-10-08.md)
- Şart doğrulandı: 13.11.2023 sonrası bireysel hesaplar → kapalı testte ≥12 testçi, kesintisiz ≥14 gün; kuruluş hesapları muaf (D-U-N-S; sahibe uymaz).
- Yol: (1) karşılıklı test toplulukları (r/AndroidClosedTesting bağlantı takası, Testers Community uygulaması: 3 uygulama test et → kredi; 0 TL) + hedef kitleden 3–5 gerçek kullanıcı; 20–25 kişi toplanır (bırakanlara pay), 3. ve 7. gün hatırlatma, 14 gün içinde bir güncelleme. (2) Ücretli testçi (15–30 $, iade garantili) yalnız eksik tamamlamak için; Google'ın teşvikli manipülasyon kuralı nedeniyle orta–yüksek risk. (3) Beklerken Huawei AppGallery (bireysel, ücretsiz) + kendi sitesinden APK; testçi sayısına sayılmaz ama kullanıcı toplar. Samsung Galaxy Store bireysel kabul etmiyor.

## §34. Başka ülkeler / gurbetçi kitlesi (sahibin sorusu, 08.10.2026 — asistan değerlendirmesi, veri yok, doğrulanacak)
- Türkiye zemini nadir: açık belediye vefat listeleri + aynı gün defin + yerleşik rakip yok. ABD/İngiltere/Almanya/İspanya/İtalya'da yerleşik devler ve ücretli veri → girilmez. Bosna/Kosova/Arnavutluk/K. Makedonya, Azerbaycan, KKTC: olabilir, veri emek ister. Ürdün/Körfez: mevcut uygulamalar + kapalı veri.
- **Önce aynı veriyle yeni kitle:** Avrupa'daki Türkiye kökenliler (DE/NL/FR/AT/BE) — Play'de ülke açmak + mağaza metni + (sonra) Almanca arayüz; ek veri işi yok. Sıra: TR üretim → 4 hafta veri → Avrupa ülkelerini aç → tutarsa Balkan/KKTC araştırması (ajan: veri kaynakları + rakipler).


## §35. Kaynak genişletme sırası ve "ortaklık en son" kuralı (site sahibi 14.10.2026)
"2'yi (belediye/müftülük veri ortaklığı yazısı) hazırda beklet; gidebildiğimiz yere kadar gidelim; 2. seçenek bütün yollar tükendikten sonra." Sıra: (1) il/ilçe müftülükleri + ilçe belediyesi genel duyuru/RSS; (2) özel cenaze hizmeti/nakil firmaları ve diğer ulusal toplayıcı siteler; (3) günlük otomatik kaynak keşfi (Google Haberler RSS "vefat etti/toprağa verildi + il" → aday site listesi); (4) e-Devlet ölçülü koşu (Mac runner, günde 2); (5) yerel radyo/TV, muhtarlık, köy derneği siteleri. Ortaklık yazıları (§25) hazır tutulur, gönderilmez.

## 36. Bildirim — 0.1.4 kararı (site sahibi 15.10.2026: "onaylıyorum… saat 08.00'de bildirim gitsin… kullanıcının onayından sonra, ona sorulsun: bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?")
- Firebase/sunucu YOK: uygulama telefonda arka planda (WorkManager) seçili il/ilçenin listesini çeker; **08:00**'de (günün ilk veri yayınından sonra) o gün ilan varsa YEREL bildirim; yoksa sessiz. Gün içinde en çok 1 bildirim daha (§22); 21:00–07:00 sessiz.
- İzin akışı (site sahibi düzeltmesi 15.10: "en başta, uygulamayı açar açmaz sorulsun"): uygulama İLK AÇILIŞTA, daha hiçbir şey göstermeden tek kart: **"Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?"** → "Evet, haber verin" / "Şimdi değil". Evet → Android bildirim izni (13+) → ardından il/ilçe seçimi (bildirimin "bölgesi" bu seçimdir; sonradan değişirse bildirim de değişir). "Evet" diyenlere her sabah 08:00. Ayarlardan kapatılabilir; bir kez "Şimdi değil" diyene 7 gün yeniden sorulmaz.
- Metin §22 kalıbı: "Ünye'de bugünkü cenaze ilanlarını göster" (sayı/ad/cami/saat yok). Dokununca o ilçenin bugünkü listesi.
- Uygulama: `bildirimTeklifiAcik = true`; paketler `workmanager` + `flutter_local_notifications`; veri kapısı başlıkları (anahtar.dart) arka plan isteğinde de gönderilir. Ajan: Sonnet, ~150k token; derleme CI.

## 37. Din görevlisi ilanı — karar (site sahibi 15.10.2026)
"İlan ver" üç kapı: **Cenaze yakını · Şehit yakını · Din görevlisi.** Din görevlisi kaydı: ad-soyad, görev yeri (il → ilçe → cami/köy adı), Diyanet personel kartı fotoğrafı. **Doğrulama anlık ve fotoğraf SAKLANMAZ** (sahibi: "doğrulamadan hemen sonra silsek"): fotoğraf yalnız bellekte OCR ile okunur; kartta "Diyanet İşleri Başkanlığı" ibaresi + kayıttaki ad-soyad eşleşirse hesap onaylı, fotoğraf anında yok edilir (diske/KV'ye yazılmaz); kayıtta yalnız `dogrulama: "kart", tarih`. Eşleşmezse 2. deneme; o da tutmazsa sahibinin haftalık onay kuyruğu (yalnız bu durumda fotoğraf ≤7 gün, karar sonrası silinir). Uyarı metni: "TC numaranızı parmağınızla kapatarak çekin". OCR: Cloudflare Workers AI (ücretsiz kota) ya da DO sunucusunda Tesseract — Türkçe karakter testi sonucu seçilir. Diyanet kurumsal e-posta YOK (sahibi düzeltti), bu yol kullanılmaz.
Panel: "İlanlarım" + "İlan oluştur" (aile formuyla aynı alanlar + mahalle/köy); il/ilçe görev yeriyle KİLİTLİ; ilan anında yayına girer, kartta "Din görevlisi paylaştı" rozeti; kendi ilanını düzenler/iptal eder. Kötüye kullanım: ilan kartında Bildir (2 bildirimde gizle), sahibinin panelinde hesabı dondurma tek tık; ilerleyen günlerde belediye listesiyle çapraz kontrol. Veri hattı: aile Worker genişler (`/gorevli/kayit, /gorevli/dogrula, /gorevli/ilan…`), `okuyucu/gorevli_al.py` her turda çeker, kapı/denetim normal. Sürüm: 0.1.5. Alternatif yol gerekçesi: köy/mahalle cenazeleri için tek dijital kaynak imamdır; belediye ortaklığına (§35) göre sıfır maliyetli ve anında.
- **§37 ek (site sahibi 15.10.2026): MÜFTÜLÜK LİSTESİ EŞLEŞMESİ önce.** "Ordu Korgan Merkez Camii görevlisiyim" → Korgan müftülüğünün personel/camiler listesinde ad + cami eşleşirse hesap anında onaylı (`dogrulama: "muftuluk_listesi"`), fotoğraf istenmez; eşleşmezse kart fotoğrafı yolu. Liste günlük toplanır (`okuyucu/muftuluk_personel.py` → `veri/_muftuluk_personel.json`, yayına girmez → Worker KV). Kapsam ölçümü ilk 5 il ile.
- **§37 ek-2 (site sahibi 15.10.2026, taklit riski: "biri mevcut din görevlisini takip ederek bilgi girebilir"):** liste eşleşmesi tek başına onay DEĞİL. Anında onay = liste eşleşmesi + kart fotoğrafı OCR (ad kart=kayıt=liste, cami uyumlu; fotoğraf saklanmaz). Liste var/fotoğraf yok → "sınırlı" (ilanlar sahibinin onayıyla). Liste yok/fotoğraf var → onaylı + 7 gün gözetim. TEK HESAP: aynı ad+cami için ikinci kayıt → iki hesap da dondurulur, kuyruk. İlk 7 gün belediye listesiyle çapraz kontrol; 2 Bildir → dondur.
- **§37 ek-3 (site sahibi 15.10.2026) kart fotoğrafı ekranı açıklaması:** "Kartınızın fotoğrafı veri tabanımızda tutulmaz; yalnızca verdiğiniz bilgileri doğrulamak için o anda kullanılır ve hemen silinir. TC kimlik numaranızı parmağınızla kapatarak çekebilirsiniz." (Sahibi "tutuyoruz" yazdı; düzenek saklamadığı için "tutulmaz" olarak işlendi; sahibi aksini söylerse KVKK aydınlatma metni de değişir.) Kuyruk istisnası: "Doğrulama yapılamadı; fotoğrafınız en çok 7 gün kontrol için saklanır, sonra silinir."
- **§37 ek-4 (15.10.2026) kart doğrulama somut kontrolleri:** (1) "T.C. DİYANET İŞLERİ BAŞKANLIĞI" + "PERSONEL/GÖREV KİMLİK KARTI" ibaresi; (2) ad-soyad birebir; (3) Diyanet unvanı (İmam-Hatip, Müezzin-Kayyım, Kur'an Kursu Öğreticisi, Vaiz, Müftü, Müftü Yrd., Din Hizmetleri Uzmanı); (4) il/kurum uyumu (varsa); (5) sicil no alanı var mı (değer kaydedilmez); (6) fiziksel kart mı (logo+vesikalık, ekran görüntüsü değil); (7) ELDE OLMA KANITI: uygulama 4 haneli kod gösterir, kâğıda yazılıp kartın yanında çekilir, OCR'da kod aranır. 1,2,3,6,7 zorunlu. Kalibrasyon için gerçek kart örneği (bilgiler kapalı) sahibinden beklenir; eşikler tek dosyada.
- **§37 ek-5 (site sahibi 15.10.2026, NİHAİ KABUL — ek-2'nin yerine):** ONAYLI = karttaki ad-soyad = başvurudaki ad-soyad = ilçe müftülük personel listesindeki ad-soyad. Cami adı eşleşmek zorunda değil (tayin gecikmesi; `cami_eslesti` notu). Kartın diğer kontrolleri (başlık, unvan, fiziksel kart, elde olma kodu) zorunlu. Ad listede yoksa / ilçenin listesi yoksa → "sınırlı" (ilanlar sahibinin onayıyla). Tek hesap + 7 gün gözetim sürer.
- **§37 ek-6 (site sahibi 15.10.2026):** Kart geçti ama ad müftülük listesinde yoksa/liste yoksa → hesap "kontrolde": panel AÇILMAZ, ilan verilemez; metin: "Başvurunuz kontrol ediliyor. Onaylanınca tarafınıza bilgi verilecek ve din görevlisi paneliniz açılacaktır." Sahibi kuyruktan karar verir (kart fotoğrafı bu durumda ≤7 gün saklanır, karar sonrası silinir — kullanıcıya söylenir); onayda e-posta + panel açılır. "Sınırlı" durumu kaldırıldı.
- **§37 ek-7 (site sahibi 15.10.2026) PANEL TASARIMI:** en üstte sabit başlık kartı: "Korgan Merkez Camii İmam Hatibi" / "Hasan Kurguluoğlu" (görev yeri + unvan, altında ad-soyad; küçük yazıyla "Ordu · Korgan"); altında iki büyük düğme "İlan paylaş" ve "İlanlarım (n)"; altta son ilanlar. "Kontrolde" hesapta aynı başlık + kontrol metni, düğme yok. Prototipte aynı kart.
- **§37 ek-8 (site sahibi 15.10.2026) İLETİŞİM:** kayıtta e-posta yerine TELEFON (din görevlileri e-postaya yabancı); doğrulama SMS kodu (Netgsm, mesaj başına kuruş düzeyi; İYS gerekmez — bilgilendirme/doğrulama). Onay haberi ASIL yol: uygulamanın günlük arka plan işi hesap durumuna bakar, onaylanınca yerel bildirim "Başvurunuz onaylandı; din görevlisi paneliniz açıldı" (sıfır maliyet); SMS yedek. Telefon ilanlarda/JSON'da asla görünmez. SAHİBİNE DÜŞEN: Netgsm hesabı (bireysel; API kullanıcı/şifre/başlık → Worker secret). Hesap gelene dek GELISTIRME=1 (kod ekranda, yalnız test).
- **§37 ek-9 (site sahibi 15.10.2026; ek-6'nın yerine):** "kontrolde" hesapta PANEL AÇILIR, "İlan paylaş" düğmesi PASİF, metin: "Başvurunuz kontrol ediliyor. Hesabınız onaylanınca paneldeki 'İlan paylaş' düğmesi etkin hale gelir. Onay verilmezse panel ve hesap silinir." Onay → düğme etkin (uygulama durum sorgusu + arka plan bildirimi); RED → hesap, oturum ve kart fotoğrafı silinir, uygulama giriş kartına döner. Kontrolde en çok 14 gün (KV TTL).
- **§37 ek-10 (site sahibi 15.10.2026) İLAN KUTUSU:** her il/ilçe sayfasında listenin üstünde sabit kutu: "Cenaze ilanınızın burada görülmesini istiyorsanız:" A) düğme "Cenaze yakını olarak ilanı paylaş" (aile formu); B) "Bulunduğunuz bölgedeki cami din görevlisinden bunu talep edin." + küçük bağlantı "Din görevlisi misiniz? Kayıt olun". Kaynaksız il ekranında aynı kutu (davetle birleşik).
- **§37 ek-11 (site sahibi 15.10.2026) YİNELENEN İLAN:** din görevlisinin ilanı ile otomatik çekilen kayıt aynı kişiyse (ad + ±2 gün) din görevlisininki kalır, otomatik olan yayına girmez; boş alanları otomatik kayıttan doldurulur. Kartın köşesinde rozet: "Mahallenin din görevlisi paylaştı". Aynı ilan iki kez görünmez. (Aile ilanı için de aynı öncelik.)
- **§37 ek-12 (site sahibi 15.10.2026) DOĞRULAMA SON HÂLİ:** kâğıttaki anlık kod KALDIRILDI (kullanıcıya yük). Kart: yalnız uygulama içi kamera (galeri yok); kontroller ibare + ad + unvan + fiziksel kart zorunlu; geçerse ONAYLI (liste şartı yok — müftülükler listeleri KVKK gerekçesiyle kaldırmış; liste eşleşirse puan). Telefon: KODU BİZ GÖNDERİRİZ (WhatsApp Cloud API doğrulama şablonu — ücretli, Meta işletme doğrulaması gerekir — ya da Netgsm SMS; hangisi hazırsa), kullanıcı başvuru ekranına girer. BEYAN KUTUSU (zorunlu, en altta): "Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum." (beyan_tarihi kayıtta). Unvanlar: İmam-Hatip, Müezzin-Kayyım, Vaiz, Müftü, Müftü Yrd., Kur'an Kursu Öğreticisi, Din Hizmetleri Uzmanı — panel başlığı unvana göre.
- **§37 ek-13 / §15 değişikliği (site sahibi 15.10.2026):** cenaze yakını ve şehit yakını ilanlarında da doğrulama e-posta yerine TELEFON KODU (WhatsApp şablonu / Netgsm); K6 sınırı telefon başına 7 günde 2; telefon hiçbir çıktıda görünmez. `AILE-ILAN-SOZLESME.md` buna göre güncellenir.
- **§27/§37 ek-14 (site sahibi 15.10.2026, hassas):** şehit ilanı YALNIZ din görevlisi panelinden; "Şehit yakını" kapısı forma değil bilgi ekranına gider: "Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır. Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur. Başınız sağ olsun. Şehidimizin ruhu şad olsun." + "Din görevlisi misiniz? Kayıt olun." Worker aile uçlarında sehit:true reddedilir.
- **§37 ek-15 (site sahibi 15.10.2026):** "TC numaranızı parmağınızla kapatın" cümlesi KALDIRILDI (kuşku). Yerine cihaz içi OTOMATİK KARARTMA: uygulama göndermeden önce karttaki 11 haneli kimlik numarasını cihazda bulup siyah bantla kapatır (ML Kit metin tanıma, internetsiz). Metin (sahibi, resmî dil, 15.10): "KVKK uyarınca personel kartınızın fotoğrafı saklanmaz ve veri tabanında tutulmaz; doğrulama tamamlandığında otomatik olarak silinir. TC kimlik numaranız sistemimizde görünmez." (teknik örtme cihazda sürer, metinde anılmaz) İlan kutusu: üç satır da okunur (2. satır ana metin rengi, 3. satır altın bağlantı). Prototipe yeni altın logo. Kural: prototipin aynısı yayına girer.

*(16.10.2026: Tam Sayfa KALDIRILDI, §44 — bu bölümün Tam Sayfa/ödeme/aile formu hükümleri geçersiz)*
## 38. Tam Sayfa ödemesi — karar (site sahibi 15.10.2026: "oranın bir değeri olmalı; o yolu her hâlükârda açacağız")
Fiyat (200 ₺) her zaman görünür; ücretsiz yapılmaz. Ödeme YALNIZ Google Play Faturalandırma (uygulama içi dijital hizmet için Google kuralı; kart bilgisi bize gelmez). Vergi: GVK 20/B "mobil uygulama geliştiriciliği kazanç istisnası" — vergi dairesinden istisna belgesi + Türkiye'de ayrı banka hesabı + banka %15 stopaj; şirket/fatura/muhasebeci yok (güncel koşul ve tavan muhasebeciye teyit ettirilir). Play ödeme profili + 20/B belgesi sahibinin; hazır olana dek düğme "Ödeme şu an alınamıyor, kısa süre sonra açılacak" (fiyat ekranda kalır). Uygulama: `in_app_purchase` ile tek seferlik ürün `tam_sayfa_ilan` (200 ₺); satın alma doğrulaması Worker'da (Play Developer API purchases.products.get — sahibinin Play API servis hesabı gelene dek istemci makbuzu + sunucu kaydı, ilan "ödeme bekliyor"→"yayında"). Sürüm 0.1.6.
- **§15/§38 ek (site sahibi 15.10.2026):** Tam Sayfa akışındaki "Ölüm belgesi doğrulama (e-Devlet kodu)" adımı KALDIRILDI; doğrulama telefon koduyla. e-Devlet kodu yalnız aile formunda isteğe bağlı alan olarak kalır (rozet).

## 39. DOĞRULAMA YOLLARI — MUTABAKAT ÖZETİ (site sahibi 15.10.2026; e-Devlet kodu HER YERDEN kaldırıldı)
- **Cenaze yakını ilanı:** telefona kod (WhatsApp doğrulama şablonu → Netgsm SMS yedek) + beyan kutusu + makine kuralları (il/ilçe gerçek, ad biçimi, tarih tutarlılığı, mezarlık–ilçe uyumu, yinelenen ilan, telefon başına 7 günde 2, IP sınırı) + "Bildir" (2 bildirimde gizle) + sahibinin haftalık bakışı. Rozet: "Yakını paylaştı". e-Devlet rozeti YOK.
- **Şehit ilanı:** yalnız din görevlisi panelinden; yakını bilgi ekranıyla imama yönlendirilir.
- **Din görevlisi:** telefona kod + Diyanet personel kartı fotoğrafı (yalnız kamera; cihazda TC örtülür; OCR bellekte: Diyanet ibaresi + ad + unvan + fiziksel kart; fotoğraf saklanmaz) + müftülük listesi eşleşmesi (varsa puan) + tek hesap + ilk 7 gün çapraz kontrol + beyan kutusu. Kart tutmazsa: panel açık, "İlan paylaş" pasif, sahibinin kuyruğu (foto ≤7 gün), onayda uygulama içi bildirim (+SMS yedek), redde hesap silinir.
- **Tam Sayfa (200 ₺):** telefona kod + beyan + Google Play Faturalandırma; ölüm belgesi/e-Devlet adımı yok.
- **Her yerde:** kart fotoğrafı veri tabanında tutulmaz (KVKK metni), telefon hiçbir çıktıda görünmez, kâğıt kodu yok, galeri yok.

## 40. ÜCRETSİZ AİLE İLANI KALDIRILDI (site sahibi 15.10.2026: "cenaze yakını ilanını kaldıralım, hepsini cami hocalarına yönlendirelim")
Normal cenaze ilanları yalnız din görevlisi panelinden; Tam Sayfa (200 ₺, yakının ücretli ilanı) kalır. İlan kutusu (sahibi metni, birebir): "Cenaze ilanınızın bu sayfada görülmesini istiyorsanız bulunduğunuz bölgedeki din görevlisinden talep edebilirsiniz." + "Din görevlisi misiniz? Kayıt olun." "İlan ver" kapıları: Tam Sayfa · Din görevlisi (şehit → bilgi penceresi). Worker /aile/basvur yalnız tam:true. §39'daki "cenaze yakını ilanı" maddesi geçersiz.


## 41. AÇILIŞ MESAJI VE MOTTO (site sahibi 15.10.2026; meal metni sahibi 16.10.2026: “Biz şüphesiz (her şeyimizle) Allah’a aidiz ve şüphesiz O’na döneceğiz.”)
- Her açılışta tam ekran açılış mesajı **11 sn** (sahibi 16.10.2026: 6 → 9 → 11 sn) görünür, sonra sönerek uygulamaya girer: ortada daire simge (altın çift halka, kubbe + hilal + tek minare, önünde ÖRTÜLÜ TABUT ve musalla taşı; `uygulama/assets/acilis/acilis.png`, kaynak `tasarim/acilis/simge22.png`, Higgsfield nano_banana_pro, sahibi seçti: "örtülü tabut olsun"), altında Arapça âyet **إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ**, altında SIRAYLA: küçük altın başlık **BAKARA SÛRESİ, 2/156** → meal **“Doğrusu biz Allah’a aidiz ve kuşkusuz O’na döneceğiz.”** → kaynak satırı **Diyanet İşleri Başkanlığı Meâli** (sahibi 15.10 18:40: sûre/âyet üstte, kaynak altta) (kuran.diyanet.gov.tr, sayfa 23, 15.10.2026'da doğrulandı). Yazı görsele çizdirilmez, uygulama yazıyla bindirir (yapay zekâ Arapça harfleri bozar).
- Motto **“Şehrinizdeki cenazelerden haberdar olun”**: açılış görselinde DEĞİL; il seçme ekranında başlığın altında ve Play mağaza kısa açıklamasında (PLAY-STORE-PAKETI.md).
- Prototip: `tasarim/sablon.html` `#acilis` + `prototip_yap.py` (secim.txt; `#aday=N` ile aday karşılaştırma; `#acilis=0` atlama). Uygulama (0.1.7): `AcilisMesaji` ekranı `home`'dan önce, 6 sn Timer, bildirim sorusu ondan sonra.

## 42. ZORUNLU GÜNCELLEME KAPISI (site sahibi 15.10.2026: "kullanıcı girer girmez güncelleme var desin, Play Store'a gitmeden giremesin")
- Dosya: depoda `site/surum.json` (`min_build`, `son_build`, `son_surum`, `mesaj`) → `https://veri.kimincenazesi.com/surum.json`. Uygulama build numarasını `--dart-define=BUILD_NO=${{ github.run_number }}` ile alır (android.yml); 0 = geliştirme, kapı atlanır.
- Kural: açılış mesajı (11 sn) sürerken sürüm çekilir (3 sn zaman aşımı); `BUILD_NO < min_build` ise tam ekran "Güncelleme gerekli" + "Play Store'da güncelle" (market:// → https yedek), geri tuşu kapatmaz; uygulama öne dönünce yeniden kontrol. `BUILD_NO < son_build` ama `>= min_build`: ana ekranda tek satır "Yeni sürüm var" çubuğu.
- Yayın: Play yeni sürümü gösterdikten SONRA `python3 araclar/surum_yayinla.py --min N --son N --surum 0.1.7` (N = yeni sürümün build numarası = Actions run_number). Kapıyı kaldırmak: `--min 0 --son 0`.
- Ağ hatası/bozuk dosya = kapı AÇIK (fail-open): sunucu düşünce kullanıcı kilitlenmez. Bu kapıyı koyan sürüm (0.1.7+16) öncesi kurulumlar kapıyı bilmez; yalnız 0.1.7+ sonrası sürümler zorlanır. Play In-App Update API ileride.

## 43. YARININ İLANLARI ANINDA YAYINDA (site sahibi 15.10.2026 20:30; 14.10 "bilgi depoda beklesin, yarın sabah taramada listeye girsin" kararını DEĞİŞTİRİR)
- Cenaze günü bugünden sonra olan kayıt (yarın ve öbür gün, en çok +2; kapı K3 ile uyumlu) toplandığı turda kendi tarihiyle `son7gun.json`'a ve yayına girer; ertesi günün koşusu beklenmez.
- `_bekleyen.json` artık "ileri tarihli kayıt deposu": kaynak sayfa kaydı düşürse bile cenaze günü +1 gün geçene kadar kayıt yayında kalır; +2'den ileri tarih depoda bekler.
- Tekilleştirme: aynı `id` tek kayıt; ertesi gün kaynak aynı kişiyi farklı id ile verirse (K10 mantığı: ad + tarih ±2 gün, yaş ±1) TAZE KAYNAK KAYDI kalır, depodaki eski kopya düşer ve `_kapi_red.json`'a "yarın kopyası" yazılır.
- Uygulama/prototip: tarih şeridinde Bugün'ün soluna "Yarın" (öbür gün için gün adı) YALNIZ o güne kayıt varsa eklenir; Bugün varsayılan seçili kalır, 7 geçmiş gün aynen durur; boş günde başka içerik açılmaz.

## 44. Tam Sayfa kategorisi KALDIRILDI (site sahibi 16.10.2026 05:00: "uygulamadan Tam Sayfa ilan kategorisini tamamen çıkar")
(Not: istenen numara §43 başka karar tarafından kullanılıyordu; bu madde §44.) Sürüm 0.1.8+17.
- Sekme çubuğu 5 → 4: İlanlar · Sayfam · Dualar · Hatırla. Tam Sayfa ekranı (örnek önizlemeler, gazete ilanı), "Vefat ilanı hazırlayın", fiyat kartı (200 ₺), Google Play Faturalandırma (`in_app_purchase`, BILLING izni, `odeme.dart`), ürün `tam_sayfa_ilan` ve kartın "Tam Sayfa" rozeti uygulamadan silindi.
- Aile formu (`aile_formu.dart`) tek giriş noktası Tam Sayfa olduğundan bütünüyle silindi (ücretsiz aile ilanı zaten §40'ta kapalıydı). `AileServisi` yalnız Bildir ve din görevlisi yanıt tipi için kalır.
- Din görevlisi kapısı ve şehit bilgi penceresi İlanlar ekranındaki ilan kutusuna taşındı: "Din görevlisi misiniz? Kayıt olun." + yeni "Şehit cenazesi ilanı nasıl verilir?" bağlantısı. Din görevlisi onay bildirimi İlanlar sekmesinde paneli açar.
- Worker (`deploy/aile-worker/`) değişmedi: `/aile/odeme` ve `tam` uç noktaları uyur durumda kalır. Play Console'daki `tam_sayfa_ilan` ürünü hiç açılmadıysa yapılacak bir şey yok.
- Mağaza metni (`PLAY-STORE-PAKETI.md`) ve veri güvenliği/gizlilik metinlerindeki ödeme satırları ayrı iş (KVKK dosyaları 16.10.2026'da yalnız listelendi).

## 45. DİN GÖREVLİSİ DOĞRULAMA = DİYANET E-POSTA KODU (site sahibi 16.10.2026 05:30; §37'deki yolu ve YURUT'taki "DİBBYS fikri" tartışmasını KAPATIR)
Sahibinin sözü: "din görevlisi misiniz butonunu tıklayan kişinin karşısına önce bir kılavuz çıkaracağız… Diyanet İşleri Başkanlığının size tahsis ettiği mail adresinize bir kod göndereceğiz, bu kodu buraya yazın… ikinci adımda ona verilen mail adresinin nasıl oluştuğunu tarif edeceğiz… bu kodu yazınca paneli açılsın."
- **Akış (3 ekran):** (1) KILAVUZ: "Din görevlisi olduğunuzu teyit etmek için Diyanet İşleri Başkanlığının size tahsis ettiği e-posta adresinize bir kod göndereceğiz; kodu buraya yazın." + kullanıcı adı alanı (yalnız @ öncesi; alan adı sabit `@diyanet.gov.tr`, kullanıcı değiştiremez) + "Kodu gönder". (2) TARİF (aynı ekranda, kod gönderildikten sonra ya da "E-posta adresim mi var?" bağlantısıyla): "E-posta adresiniz DİBBYS'de girdiğiniz kullanıcı adınızla başlar: kullanıcıadınız@diyanet.gov.tr. Daha sonra Google tarayıcısına girerek posta.diyanet.gov.tr yazın. Bu sayfada karşınıza çıkan kullanıcı adı boşluğuna DİBBYSkullanıcıadınız@diyanet.gov.tr şeklinde yazın. Şifre boşluğuna ise DİBBYS'de girdiğiniz şifreyi girin. Giriş yapın. Gelen kutusunda size gönderdiğimiz kodu uygulamaya girin." (sahibi 16.10 07:40: "çok uzun, adımlara böl" → 6 kısa madde: 1 Diyanet her personeline e-posta verir · 2 Adresiniz: DİBBYS kullanıcı adınız@diyanet.gov.tr · 3 Tarayıcıya posta.diyanet.gov.tr yazın · 4 Kullanıcı adı: DİBBYSkullanıcıadınız@diyanet.gov.tr · 5 Şifre: DİBBYS şifreniz, giriş yapın · 6 Gelen kutusundaki kodu uygulamaya girin) + 6 haneli kod alanı + "Yeniden gönder" (5 dk; sahibi 16.10 08:05: "60 saniye olmasın 5 dakika olsun"). (3) Kod doğru → **PANEL HEMEN AÇILIR** (oturum depoya yazılır; "kontrol ediliyor" bekleme yok). Paneldeki "Hesabınız Diyanet e-postanızla doğrulandı." notu yalnız doğrulamadan sonraki İLK panel açılışında görünür, sonra kalkar (sahibi 16.10 10:40).
- **Kural:** kod YALNIZ `@diyanet.gov.tr` adresine gider (Worker başka alan adını reddeder); kod 6 hane, 10 dk geçerli, 5 yanlış denemede yeni kod; aynı kullanıcı adına günde en çok 5 kod; e-posta gövdesi tek cümle + kod, bağlantı yok. Doğrulanan hesap kaydı: kullanıcı adı (@diyanet.gov.tr), il/ilçe, görev yeri, ad-soyad (panelde ilan yazarken gerekir), doğrulama zamanı.
- **Eski adımlar:** personel kartı fotoğrafı ve telefon kodu bu kapının YERİNE geçmez; sahibi "kodu yazınca paneli açılsın" dediği için kart + telefon adımları KALDIRILIR (asistan yorumu 16.10; sahibi aksini derse geri konur). Diyanet sayfalarına uygulama ya da biz GİRMEYİZ; kullanıcı kendi tarayıcısında kendi postasını açar.
- **Gönderim:** Worker → Resend (ücretsiz katman 3.000/ay; `deploy/aile-worker/.resend` anahtarı + kimincenazesi.com DNS kayıtları sahibinde); gönderen `dogrulama@kimincenazesi.com`. §0k: ihtiyaç tek bir kod e-postası; alışılmış yol SMS/WhatsApp sağlayıcı (ücretli, numara kaydı); ucuz yol Diyanet'in zaten verdiği kurumsal posta + ücretsiz Resend katmanı — kimlik teyidi kurumsal posta sahipliğine dayanır, SMS'ten güçlüdür.
- **Uygulama:** `gorevli_kayit.dart` fazları → kılavuz · kod · panel; `kart_kamera.dart` ve telefon kodu kullanılmıyorsa kaldırılır; Worker `/gorevli/eposta-kod` + `/gorevli/eposta-dogrula`. Kayıt: YURUT H76 (uygulandığında).

## 46. GÖREV YERİ DEĞİŞİKLİĞİ (site sahibi 16.10.2026 08:05)
"Din görevlisi yer değişikliği yaptı (Korgan Merkez Camii → Samsun Kavak Camii): kendi panelinde **'Görev yerim değişti'** düğmesi; oraya yeni görev yerini ya da unvanını yazsın; panelin en üstünde artık yeni cami yazsın." UYGULAMA (sahibi 16.10 08:30: "düğme sağ üstteki üç noktaya; tıklayınca ayrı sayfa gelsin"): panel başlığının sağ üstünde ⋮ menüsü → 'Görev yerim değişti' (ve 'Çıkış yap') → AYRI SAYFA (görev yeri, il/ilçe, unvan, Kaydet) (yeni görev yeri, il/ilçe, unvan) → Kaydet → Worker hesap kaydı güncellenir (`POST /gorevli/gorev-yeri`), panel başlık kartı hemen yeni değeri gösterir; sonraki ilanlar yeni görev yeri/il-ilçeyle paylaşılır, eski ilanlar değişmez. Prototip: p-gpanel "Görev yerim değişti". Ayrıca kod ekranında "Kodu yeniden gönder" beklemesi 60 sn → **5 dk** (kod geçerliliği 10 dk aynı).

## 47. SAYFAM — SAYAÇ BAŞLIĞI (site sahibi 16.10.2026 08:20)
"Sayfam'daki kutucukların sayaç olduğunu sayacın üst tarafına yazalım; tıkladığında sayacın arttığını görsün." → Her kartta sayaç bloğunun üstünde tek satır: **"Okuma sayacı — her dokunuşta bir artar"** (`M.sayacBaslik`; prototip `.sayac-baslik`). Dokunuşta sağdaki sayı artar ve kısa vurgu animasyonu zaten var.

## 48. MOTTO HER YERDE + ESKİ SİMGE SİLİNDİ (site sahibi 16.10.2026 08:45)
- "İl ve ilçenizdeki cenaze ilanları" ifadesi her yerde **"Şehrinizdeki cenazelerden haberdar olun"** ile değiştirildi (paylaş metni, Hakkında, mağaza kısa/uzun açıklama, özellik grafiği).
- Eski kavisli (kemer / L13) simge her yerden kaldırıldı: uygulama simgesi, Play simgesi (512), özellik grafiği, prototip logosu, boş durum daireleri → sahibinin seçtiği **tabutlu daire amblem** (`tasarim/acilis/simge22.png` → `uygulama/assets/ikon/ikon.png`, `ikon_on.png`, `deploy/magaza/ikon-512.png`, `ozellik-grafigi-1024x500.png`; uyarlanır simge zemini #0F1F2E). `marka/` klasörü arşiv olarak kalır, hiçbir yerde kullanılmaz.

## 49. DİN GÖREVLİSİ OTOMATİK İLANI DÜZELTİR (site sahibi 16.10.2026 08:50)
"Veri olarak çektiğimiz ilanda bir bilgi hatalıysa, o bölgedeki din görevlisi fark edince düzeltebilsin." UYGULAMA: din görevlisi oturumu açıkken, kendi il/ilçesindeki OTOMATİK (kaynaktan okunmuş) ilan kartının ⋮ menüsünde **"Düzelt"**; form o ilanın bilgileriyle dolu açılır (ad-soyad, yaş, ilçe/mahalle, cenaze namazı yeri-vakti, defin yeri); kaydedince Worker'a görevli ilanı olarak gider (`duzeltme_id` = düzeltilen kaydın id'si). Veri hattı: `gorevli_birlestir` görevli kaydını zaten otomatik kaydın yerine koyar (aynı kişi); `duzeltme_id` eşleşmesi doğrudan o kaydı değiştirir. Panelde "İlanlarım"da düzeltme "Düzeltildi" etiketiyle görünür. Kartta kaynak gösterilmez (H75). Düzeltme yalnız kendi il/ilçesi için; başka il/ilçe için düğme çıkmaz.

## 50a. ÇIKIŞ SONRASI YENİDEN GİRİŞ = YENİDEN E-POSTA KODU (site sahibi 16.10.2026 09:15)
"Bir din görevlisi çıkış yaptığında bir daha giriş yapmak istediğinde tekrar e-posta doğrulaması istesin." Çıkışta oturum cihazdan ve Worker'dan silinir; yeniden giriş yalnız kılavuz → kod akışıyla olur, "hesabım var" kestirmesi YOK. KVKK penceresi her GİRİŞ sonrası panelin ilk açılışında bir kez gösterilir (sahibi 16.10 10:00: çıkış yapıp yeniden girince KVKK yeniden çıkar); aynı oturumda tekrar sorulmaz.

## 50. PANEL İLK AÇILIŞTA KVKK UYARISI (site sahibi 16.10.2026 08:50; "sadece ilk açılışta"; 09:35: "Cloudflare sunucuları / yurt dışı" satırı kısa uyarıda OLMAZ — korkutur; yurt dışı aktarım bilgisi yalnız tam metinde/Gizlilik'te)
Din görevlisi paneli İLK kez açılırken tam ekran KVKK aydınlatma penceresi: kısa metin (hangi veriler: Diyanet e-posta adresi, ad-soyad, görev yeri/unvan, il-ilçe, paylaştığınız ilanlar; amaç; saklama; haklar) + "Tam metin" bağlantısı (Gizlilik sayfası) + **"Okudum, anladım"** düğmesi; kabul tarihi cihazda ve Worker hesap kaydında (`kvkk_kabul`) tutulur; bir daha gösterilmez (hesap değişirse yeniden). Aydınlatma metninin B bölümü (telefon/kart fotoğrafı) §45'e göre YENİDEN YAZILACAK (KVKK işiyle birlikte).

## 51. EKRANDA TEK İLAN + VEFAT TARİHİ YOK (site sahibi 16.10.2026 09:05)
- "Bir sayfada birden fazla ilan varsa ekranı sadece bir ilan görülecek şekilde ayarla": İlanlar listesinde her kart ekranı doldurur, kaydırınca sıradaki karta geçilir (kaydırma kilidi/snap). Sayfam listesi aynı kuralla (kartlar sayaçlı, zaten uzun).
- "Vefat tarihini sil, sadece cenaze günü kalsın; yaş kalabilir — iki tarih kafa karıştırıyor": kartta "Vefat: 13 Ekim · 77 yaş" satırı → yalnız **"77 yaş"**; şehit kartında "Şehit oldu: tarih" satırı da kalkar (yalnız yaş). Cenaze günü ve vakti "Cenaze namazı" kutusunda kalır. Veri alanı (`vefat_tarihi`) silinmez; yalnız gösterilmez.

## 52. BOŞ GÜN SIRASI: ÖNCE "BULUNMUYOR", ALTINDA İLAN KUTUSU (site sahibi 16.10.2026 09:25)
Verisi olmayan il/ilçede eski "… yakınları tarafından paylaşılıyor / din görevlisinin paylaştığı ilanlar burada görünür" kartı KALDIRILDI; yerine her yerde aynı satır: **"Bugün Ovacık'ta cenaze ilanı bulunmuyor"** (ilçe seçiliyse ilçe, yoksa il). Sıra her ekranda: üstte "bulunmuyor" satırı (ya da ilanlar), ALTTA "Cenaze ilanınızın bu sayfada görülmesini istiyorsanız…" ilan kutusu + "Din görevlisi misiniz?" bağlantısı. (15.10'daki "kutu listenin üstünde" kararı değişti.)

## 53. "PANEL" SEKMESİ + 4 HANELİ PAROLA (site sahibi 16.10.2026 09:55)
"Din görevlileri için kategorilerde Hatırla'dan sonra Panel kategorisi aç; doğrulamadan sonra açık halde tutulsun; kötü niyetle biri girip paylaşmasın diye 4 haneli parola belirleyerek girebilsin." UYGULAMA (sahibi düzeltmesi 16.10 10:50: "Panel sekmesi sürekli orada dursun"): alt sekme çubuğu HER ZAMAN 5 sekme (İlanlar · Sayfam · Dualar · Hatırla · **Panel**). Doğrulanmamış kullanıcı Panel'e dokununca: "Bu paneli din görevlileri kullanabilir. Din görevlisi misiniz? Kayıt olun." + "Kayıt olun" düğmesi → kılavuz/kod akışı. Giriş yaptıktan sonra gerisi aynı (parola → KVKK → sorumluluk → panel). Kod doğrulanır doğrulanmaz **parola belirleme** ekranı (4 rakam, iki kez); parola cihazda (karma) saklanır. Panel sekmesine her girişte (uygulama açılışı başına bir kez) parola sorulur — **uygulama kapatılıp yeniden açılınca parola YENİDEN sorulur** (sahibi 16.10 10:30; parola kaydı yalnız bellekte, diske yazılmaz); 5 yanlışta 1 dk bekleme; "Parolamı unuttum" (sahibi 16.10 11:00, kesin: "kendisinin başta verdiği Diyanet mailine parolası gitsin") → parolanın KENDİSİ hesabın Diyanet adresine e-postayla gönderilir ("Kimin Cenazesi panel parolanız: 1234"). Bunun için parola belirlenirken Worker'a da gönderilir ve hesap kaydında sunucu anahtarıyla ŞİFRELİ (AES-GCM, secret `PAROLA_ANAHTARI`) tutulur; cihazda karma kalır. Hatırlatma günde en çok 3 kez; oturum/hesap/KVKK/sorumluluk kayıtları korunur; kişi e-postadaki parolayla panele girer (isterse ⋮ menüden "Parolamı değiştir" ile yeniler). Düğmeye basınca AYRI SAYFA (sahibi 16.10 11:15): başlık "Parolanız gönderildi", metin "Parolanızı <adres> adresine gönderdik. Gelen kutunuza bakın, parolanız gönderilmiştir.", "Tamam" → parola ekranına döner. Çıkışta sekme gizlenir, parola silinir. İlan kutusundaki "Din görevlisi misiniz?" bağlantısı oturum varken Panel sekmesine götürür. KVKK penceresi (§50) parola belirlendikten sonra, panel ilk açılışında.

## 54. PAROLA AÇIKLAMASI + SORUMLULUK UYARISI (site sahibi 16.10.2026 10:15)
- Parola belirleme ekranındaki açıklama birebir: **"Birilerinin sizin hesabınıza girip kötü niyetli/yanıltıcı paylaşımlar yapmasını önlemek için 4 haneli parola belirleyin."**
- Din görevlisi panele ilk girişinde (KVKK penceresinden sonra, giriş başına bir kez) SORUMLULUK uyarısı, metin birebir: **"Bu panelden yapılacak ilanlardaki bilgilerin doğru olma sorumluluğu din görevlisine aittir. Yanıltıcı veya yanlış bilgi paylaşımından hesabın sahibi olan din görevlisi sorumludur."** Düğme "Anladım, kabul ediyorum"; kabul tarihi cihazda ve Worker hesap kaydında (`sorumluluk_kabul`); geri tuşu kapatmaz; çıkışta sıfırlanır.

## 49a. DÜZELTME YETKİSİ: CAMİ / MAHALLE EŞLEŞMESİ (site sahibi 16.10.2026 12:40)
"Hiçbir din görevlisi kendi mahallesi dışındaki ilanlara müdahale edemesin. Çitlice'de görevli hoca, ilanda Çitlice Mahallesi yazıyorsa düzeltebilsin; cenaze merkezdeyse yalnız merkezdeki hocalar. Düzeltme hakkı için ilandaki cami adı ile görevlinin panelindeki cami adı eşleşmeli. Eşleşiyorsa, yalnız onun göreceği 'Düzelt' düğmesi ilanın altında kendiliğinden görünsün."
KURAL (il/ilçe eşleşmesine EK, §49'un yerine geçer):
- Görevlinin hesabındaki **görev yeri** (cami ya da köy/mahalle adı; §46 ile güncellenebilir) ile ilanın **cenaze namazı yeri (cami)** ya da **mahalle/köy** alanı eşleşmeli. Eşleşme sadeleştirilmiş adla yapılır (büyük/küçük harf, "camii/camisi/cami", "mahallesi/mah./köyü" ekleri, Türkçe karakter farkları atılır; "Merkez Camii" = "Korgan Merkez Camii").
- İlanda cami ya da mahalle bilgisi yoksa kimse düzeltemez (yanlış kişiye yetki vermektense düzeltmesiz kalır; ilan din görevlisi paneline bildirilir: "Bildir").
- "Düzelt" düğmesi ilanın ALTINDA, yalnız eşleşen görevli oturumunda görünür; başkası için düğme yoktur.
- Sunucu ve veri hattı aynı kuralı yeniden denetler: Worker, düzeltmeyi hesabın görev yeriyle birlikte kaydeder; `gorevli_birlestir` düzeltmeyi yalnız orijinal kayıttaki cami/mahalle görevlinin görev yeriyle eşleşiyorsa uygular, eşleşmiyorsa düzeltme reddedilir ve `_kapi_red.json`'a "yetki dışı düzeltme" yazılır.
- Örnek: Korgan Çitlice Camii görevlisi → yalnız "Çitlice" geçen (cami ya da mahalle) ilanları düzeltir; Korgan Merkez Camii görevlisi → "Merkez Camii"/"Merkez Mahallesi" ilanları.

## 49b. KARTTA "DÜZELT" YOK; (sahibi 16.10 13:20, kesin akış: Çitlice camisinde görevli hoca → mahallesindeki cenaze bizim veriden İlanlar'da yayımlandı → aynı ilan görev yeri Çitlice olan hocaların İLANLARIM sayfasında da görünür → altında 'İlanı düzelt' → soyadındaki harf hatasını düzeltir → düzeltme İlanlar sayfasındaki ilana otomatik uygulanır [gerçek uygulamada en geç bir sonraki saatlik turda]) — EŞLEŞEN İLAN GÖREVLİNİN "İLANLARIM" SAYFASINA OTOMATİK DÜŞER (site sahibi 16.10.2026 13:00; §49a'nın "ilanın altında düğme" kısmının YERİNE geçer)
"Altında düzeltme düğmesi çıkmasından ziyade, paylaştığımız ilan o hocanın mahallesindeyse direkt onun İlanlarım sayfasına otomatik düşsün."
- Halka açık ilan kartında hiçbir düzeltme düğmesi YOK (kaynak da görünmez, H75).
- Din görevlisi panelindeki **İlanlarım** listesi iki bölüm gösterir: (a) kendi paylaştıkları; (b) **"Bölgenizdeki ilanlar"**: bizim çektiğimiz, il/ilçe + cami/mahalle eşleşen (§49a `yer_eslesir`) OTOMATİK ilanlar, "Otomatik" etiketiyle. Görevli bunlara dokunup **İlanı düzelt** der (sahibi 16.10 13:10: düğme ilanın altında, adı "İlanı düzelt"); kaydedince kayıt onun düzeltmesi olur (`duzeltme_id` = orijinal id) ve veri hattı orijinalin yerine koyar (§49). Düzenlemediği ilanlara dokunulmaz.
- Uygulama her panel açılışında canlı veriden (`veri/<il>/son7gun.json`) eşleşen kayıtları süzer (cihazda; sunucuya ek istek yok).
- Yetki denetimi sunucuda ve veri hattında aynen §49a (eşleşmeyen düzeltme reddedilir).

## 49c. İLANLARIM SAYFASI METİNLERİ (site sahibi 16.10.2026 13:40)
- İlan paylaş formunda yaş alanı KALIR; altında **"Belirtilmedi"** kutucuğu (sahibi 16.10 13:50): işaretlenince yaş alanı kapanır, kayıtta yaş boş gider ve ilan kartındaki yaş satırı görünmez. Düzeltme formunda da aynı kutucuk (orijinalde yaş yoksa işaretli gelir).
- İlanlarım sayfasının üstünde görünür (soluk değil) açıklama, birebir: **"Bu sayfada sizin eklediğiniz ve sistem tarafından yüklenen ilanlar görüntülenir. Sistemin yüklediği ilanlarda bir hata görürseniz düzeltebilirsiniz, düzeltme ilanlar sayfasında otomatik olarak uygulanır."**
- Bölüm başlıkları: "Sizin eklediğiniz ilanlar" · "Sistemin yüklediği ilanlar".
- Kayıt satırı etiketi: sistem kaydında "Yenipınar · Korgan · **Sistem**" (düzeltilmişse "Sistem · Düzeltildi"); hocanın kendi ilanında "Yenipınar · Korgan · **Din görevlisi**" ("Otomatik"/"Yayında" sözcükleri kullanılmaz).

## 49d. İLAN FORMU: VAKİT KUTUCUKLARI + CAMİ SEÇİMİ (site sahibi 16.10.2026 14:00)
- "Vakit" başlığı altında 5 kutucuk: Sabah / Öğle / İkindi / Akşam / Yatsı **Namazını Müteakip**; biri seçilir (serbest yazı yok).
- "Cami" başlığı altında önce **görevlinin kendi camisi** (hesabındaki görev yeri) kutucuk olarak seçili gelir; altında **"Diğer"**; Diğer seçilince "Cami adı" alanı açılır ve elle yazılır. Düzeltme formunda cami farklıysa "Diğer" seçili ve alan dolu gelir.
- Kayıt biçimi değişmez: `namaz_yeri_vakti = "<Vakit>-<CAMİ>"`.

## 49e. GÖREVLİ İLANI YALNIZ KENDİ İLÇESİNDE YAYIMLANIR (site sahibi 16.10.2026 14:10)
"Hocanın bulunduğu ilçede yayınlanmasına dikkat et; başka ilçede veya ilde yayınlanmasın." Üç katman: (1) formda il/ilçe değiştirilemez (hesabın görev yerinden gelir, kilitli; not: "İlanınız yalnız görev yaptığınız ilçede yayımlanır"); (2) Worker, ilanın il/ilçesini gövdeden DEĞİL hesap kaydından yazar; (3) veri hattı (`gorevli_al.py`) görevli kaydını yalnız Worker'ın verdiği il'in dosyasına, ilçe hesabın ilçesi olarak koyar; il/ilçe hesapla uyuşmayan kayıt alınmaz. Görev yeri değişince (§46) sonraki ilanlar yeni ilçeye gider, eskileri yerinde kalır.

## 56. VERİDEN EKRANA EN KISA YOL: GÖREVLİ İLANI ANINDA + YENİLEME (site sahibi 16.10.2026: "veri çekme ile uygulamada gösterme arasındaki süreyi en hızlıya çevir")
(A) Uygulama `son7gun.json`'u indirirken aynı ilin `GET <Worker>/gorevli/<il>.json`'unu da PARALEL çeker (5 sn zaman aşımı; hata/bozuk yanıt = sessizce atlanır) ve cihazda birleştirir (`lib/cekirdek/gorevli_birlestir.dart`): aynı id (`gorevli-<id>`) ya da aynı kişi (ad + cenaze günü ±2 gün + yaş ±1, `kapi.ayni_kisi` ile aynı) listedeyse listedeki kalır; `duzeltme_id` varsa o id'li otomatik kayıt çıkar, görevli kaydı yerine konur; yoksa kaydın ilçesinin listesine eklenir (`gorevli:true`). Cenaze günü bugün−7…bugün+2 dışındakiler alınmaz; yalnız `Ilan` beyaz liste alanları saklanır (telefon/başvuran yok). Kaynaksız ilde (404) görevli kaydı varsa il kaynaklı sayılır. Hoca paylaşınca/düzeltince saatlik tur beklenmez. (B) Her açılışta, İlanlar sekmesine dönüşte ve uygulamaya dönüşte (veri 5 dk'dan eskiyse) yeniden çekilir; listeyi aşağı çekince her zaman (görevli verisi dahil). Veri kapısı önbelleği 60 sn / `max-age=120` (≤5 dk, değişmedi); Worker liste `max-age=60`.

## 57. SABAH BOŞLUĞU: BUGÜN BOŞSA DÜN KENDİLİĞİNDEN AÇILIR (site sahibi 16.10.2026: "uygulama bomboş görünüyor")
Seçili gün BUGÜN ve bugün hiç kayıt yoksa "Bugün …'da cenaze ilanı bulunmuyor" satırının ALTINDA "Dün (15 Ekim)" bölüm başlığıyla yalnız DÜNÜN ilanları listelenir (şehit önce; ilçe bölümleri aynı); dün de boşsa yalnız "bulunmuyor" satırı. Daha eski günler tarih şeridinden. 15.10'daki "boş günde son 7 gün açılmaz" kuralı yalnız bu kadar gevşedi (diğer ilçeler hâlâ açılmaz). İlan kutusu yine en altta (§52).



**§57 DEĞİŞTİ (sahibi 16.10.2026 öğleden sonra):** "dünü de göstermesin; o gün cenaze yoksa sadece yok desin, altında ilan linkleri olsun, bu kadar." Bugün boşsa "Dün (…)" bölümü AÇILMAZ; yalnız "Bugün <yer>’de cenaze ilanı bulunmuyor" + ilan kutusu. Kural uzak ayarda: `bugun_bossa_dunu_goster` (varsayılan false; site/ayarlar.json, araclar/uzak_ayar.py). İlçe sayfasında "İl geneli" bölümü de yok (`ilce_sayfasinda_il_geneli` false; YURUT H91).
