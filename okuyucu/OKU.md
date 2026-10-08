# Okuyucular

## Çalıştırma
    python3 okuyucu/hepsi.py                 # tüm iller sırayla (biri hata verirse öbürleri sürer) + veri/ozet.json
    python3 okuyucu/hepsi.py trabzon ordu    # seçili iller
    python3 okuyucu/<il>.py [--gun 7]        # tek il (ordu, trabzon, kocaeli, kahramanmaras, batman, giresun, gaziantep, bursa, osmaniye, kayseri, konya, denizli, sivas, kirikkale, zonguldak, edirne)

Çıktı: `veri/<il>/YYYY-AA-GG.json` (gün başına) ve `veri/<il>/son7gun.json`:
`{"il", "ilceler": {ilçe: [kayıt]}, "il_disi": [kayıt], "ilce_belirsiz": [kayıt], "toplam", "guncelleme"}`.
7 günden eski gün dosyaları her çalıştırmada silinir. Yalnız standart kütüphane. `veri/ozet.json`: il -> son güncelleme, kayıt sayısı, il_disi/ilce_belirsiz sayısı, hata, süre.

## Okuma kuralları (ortak.indir / ortak.robots_izin)
User-Agent `CenazeIlanlariBot/0.1 (+iletisim: …)`; aynı alan adına istekler arası ≥3,5 sn; her okuyucu başlamadan robots.txt'ye bakar (yasaklıysa okumaz, stderr'e yazar; robots.txt yoksa/404/HTML dönüyorsa kural yok sayılır); geçici kopmada 3 deneme.

## Şema (ortak.ALANLAR)
id, il, ilce, mahalle, ad_soyad, anne_baba, yas, dogum_tarihi, vefat_tarihi, defin_yeri, defin_zamani, namaz_tarihi, namaz_yeri_vakti, liste_tarihi, kaynak_ad, kaynak_url, alindi, ham, il_disi_defin, ilce_belirsiz.
Tarihler YYYY-AA-GG; kaynakta olmayan alan `null`. KVKK: telefon, yakın/cenaze yakını, taziye adresi, ölüm nedeni alınmaz; yalnız tanımlı etiketler eşlenir (anne-baba adı alınır).

## İlçe / il dışı defin (ortak.ilce_isle, `ilceler.json`)
- `ilceler.json`: il -> resmî ilçe listesi (+ `_iller` 81 il, `_il_disi_bilinen` tek başına gelen komşu il ilçeleri, ör. Terme -> Samsun). Yeni il eklerken buraya ilçe listesini koy.
- Kaynak ilçe değeri `<il> / <ilçe>` (ya da ters `<ilçe>/<il>`) ve il, okunan il değilse: `il_disi_defin: {"il","ilce"}`, `ilce: null`; kayıt son7gun'da `il_disi` listesine gider. Bilinen yazım hataları düzeltilir (Tarabzon -> Trabzon, `ortak.YAZIM_DUZELT`); ham değer `ham.ilce_ham`/`ham.ilce`'de korunur.
- İlçe yerine il adı (ör. "Ordu") ya da il listesinde olmayan değer (Refaiye, Merkez): `ilce: null`, `ilce_belirsiz: true`, son7gun'da `ilce_belirsiz` listesi.
- Okuyucu kaydı yazarken `ilce` alanına kaynağın ham ilçesini koyar; `ortak.gun_yaz()` ve `son7gun_yaz()` bunu çözer (yerinde, bir kez).

## İl notları
- **ordu**: `ordu.bel.tr/vefat-edenler?date=YYYY-AA-GG`. İlçe alanı il dışı defini "Samsun / Terme" biçiminde verebilir.
- **trabzon**: `/Debis/_VefatEdenleriListele?Tarih=GG.AA.YYYY`; başlık "AD - TRABZON/İLÇE/MAHALLE" (başka il: "ARTVİN"). Sayfanın "günlük vefat sayısı" beyanı ile ayrıştırılan sayı karşılaştırılıp uyarı basılır. Yaş ve doğum tarihi kaynakta yok.
- **kocaeli**: yalnız güncel liste (tarih parametresi yok, ~son 2 günün defin kayıtları). Önceki günler `ortak.liste_birikim()` ile kendi dosyalarımızdan tamamlanır (kayıt ilk görüldüğü güne yazılır; yeni kurulumda geçmiş boştur, günlük çalıştıkça dolar). İlçe kaynakta yoktur: cami adresinin sonundan çıkarılır (`ham.ilce_kaynagi: cami_adresi`) ya da "XXX/SAKARYA NAKİL" alanından (il dışı defin). Ölüm nedeni alınmaz.
- **kahramanmaras**: `/cenaze-ilanlari?tarih=YYYY-AA-GG&sayfa=N` (sayfa başına 25; sayfalar sırayla okunur). `tarih=D`, o gün yürürlükte olan (vefat <= D <= defin) ilanları verir; aynı ilan birkaç günün dosyasında çıkar, son7gun id'ye göre tekilleştirir. Doğum tarihi çoğunlukla yalnız yıl (`ham.dogum`). "MERKEZ" resmî ilçe değildir (Dulkadiroğlu/Onikişubat) -> ilce_belirsiz.
- **batman, giresun**: ayrı ajan yazdı; aynı ortak yardımcıları kullanır.

- **gaziantep**: `gaziantep.bel.tr/tr/defin-listesi?date=GG.AA.YYYY` (tek sayfa HTML tablo, günde ~20-30 kayıt). Sitenin TLS ara sertifikası eksik: doğrulama AÇIK, eksik ara sertifikalar `okuyucu/sertifika/zincir-eksik-ara.pem` (Sectigo DV R36 + R46 çapraz imzası; sertifikadaki AIA adreslerinden indirildi; sertifika 2027'de yenilenirse aynı yoldan tazele) ssl bağlamına eklenir (`ortak.indir(..., ssl_baglam=)` (JSON POST gibi ek başlık için `basliklar={...}`), `ortak.robots_izin(url, ssl_baglam)`). Kaynakta ilçe yok: ilce null + ilce_belirsiz (hepsi); mezarlık adı `defin_yeri`; ilçe mezarlıktan çıkarılmaz. Yaş/vefat tarihi var; doğum yalnız yıl (`ham.dogum_yili`), cinsiyet `ham`'da.
- **bursa**: `bursa.bel.tr/mezarlik-bilgi-sistemi` "Bugün Defnedilenler" sekmesi; yalnız bugün -> `liste_birikim` (günde birkaç kez çalıştır; gün içinde eklenen kayıtlar yakalanır, geçmiş yeni kurulumda boş). Mezarlık sütunu "İLÇE / Mezarlık" ise ilçe alınır (`ham.ilce_kaynagi: mezarlik_oneki`), değilse ilçe belirsiz; ilçe mahalleden ÇIKARILMAZ. Mahalle var. defin_zamani = listenin günü (saat yok). Vefat tarihi/yaş yok.
- **osmaniye**: `osmaniye-bld.gov.tr/kategori/vefaat/feed/` (son 10 yazı); yazıdaki her "Cenaze Bilgi Sistemi" bloğu bir kayıt. Yalnız ad + defin yeri (ilçe yok, defin yerinden çıkarılmaz). TAZİYE ADRESİ alınmaz.
- **kayseri**: `kayseri.bel.tr/vefat-ilanlari` ASP.NET formu: ViewState/EventValidation sayfadan alınır, `ctl00$contentHolder$vefatDate` + `__EVENTTARGET=ctl00$contentHolder$btnSorgula` POST; 7 gün. Giriş/CAPTCHA belirtisi çıkarsa okuma durur. TAZİYE ADRESİ ve koordinatlar alınmaz (ilçe de ondan çıkarılmaz -> hepsi ilce_belirsiz). Hacim düşük (günde 1-7): liste yalnız sisteme girilenleri gösteriyor. Namaz yeri/vakti var (namaz_tarihi = sorgulanan gün).

- **konya** (05.10.2026): `mezarlik.konya.bel.tr/` açılış sayfası "Bugün Vefat Edenler" HTML tablosu (robots: kısıt yok). Tarih parametresi yok -> `liste_birikim` (günde birkaç kez çalıştır; geçmiş yeni kurulumda boş). Ad, baba adı (anne_baba), doğum tarihi (tam), vefat ve defin tarihi, cami + namaz vakti, defin yeri (mezarlık). Kaynakta ilçe ve yaş yok -> ilce_belirsiz (hepsi).
- **denizli**: sayfanın kendi çağrısı `POST mezarlik.denizli.bel.tr/bugunDefnedilenlerYeni.aspx/GetDefnedilenler` gövde `{"tarih":"YYYY-AA-GG"}` (ASP.NET PageMethod, JSON `d` dizisi; `ortak.indir(..., basliklar=)` ile Content-Type verilir). robots.txt yok (404). Günde ~12-27 kayıt, il geneli. Aynı kayıt komşu günlerin cevabında çıkabilir (id: ad + ölüm tarihi + cilt no). Alanlar: ad, anne/baba, doğum tarihi, ölüm tarihi, defin camii + vakit, mezarlık; ada/parsel/sıra ham'da. "Nakil Giden" -> defin başka yerde (hedef yok). İlçe kaynakta yok -> ilce_belirsiz (hepsi).
- **sivas**: `sivas.bel.tr/vefat-edenler?page=N` (sayfa başına 10, en yeni üstte; en çok 5 sayfa okunur). Sitenin ara sertifikası eksik (Sectigo DV R36): gaziantep ile aynı `sertifika/zincir-eksik-ara.pem` yöntemi, doğrulama AÇIK. Yaş, defin tarihi, cami + saat, mezarlık. TAZİYE ADRESİ alınmaz. Nakil kayıtlarında yer-vakit = defin yeri = "DİVRİĞİ  BAŞÖREN" (ilçe + köy) / "SİNOP  DURAĞAN" (il + ilçe) / "İSTANBUL": ilce_coz ile çözülür (Sivas ilçesi -> ilce, başka il -> il_disi). Kent merkezi kayıtlarında ilçe yok -> ilce_belirsiz.
- **kirikkale**: `kirikkale.bel.tr/?sayfa=kaybettiklerimiz[&page=N]` serbest metin duyurular ("AD (YAŞ 83) VEFAT ETMİŞTİR. CENAZESİ <vakit> <yer> KALDIRILACAKTIR - Tarih : G.AA.YYYY"); regex ile ayrıştırılır. Ad başında memleket/köy öneki olabilir ("KALECİKLİ ...") ve ayrıştırılamaz: tam metin ad_soyad'da, ham.ad_notu ile işaretli. Ad içermeyen duyurular (personelin yakını) alınmaz. İlçe/mezarlık/vefat tarihi kaynakta yok.
- **zonguldak**: `zonguldak.bel.tr/vefat` gün listesi -> `/vefat/YYYY-AA-GG` gün sayfaları (ilanlar her gün yok; bir günde 1-4 ilan, serbest metin). Blok: BÜYÜK HARF ad, "<köy/mahalle> sakinlerinden,", akraba satırları (ALINMAZ, KVKK), "Cenazesi, ..." cümlesi (namaz_yeri_vakti'ne aynen; "bugün/yarın" ilan tarihine göre namaz_tarihi'ne çevrilir; defin_yeri yalnız özel adlı mezarlıkta). Köy/mahalle satırı `mahalle`ye gider, ilçe kaynakta ayrı verilmez -> ilce_belirsiz. robots.txt yok (404; Next.js 404 sayfası döner, kural sayılmaz).
- **edirne**: `edirne.bel.tr/hizmet/vefat?sayfa=N` (HTML tablo, sayfa başına 10, en çok 5 sayfa): defin tarihi, ad, yaş, cenaze yeri (cami), namaz vakti, mezarlık. MESLEK alınmaz (kaynakta "ENGELLİ" gibi sağlık durumu değerleri var). Yalnız Edirne Belediyesi (merkez) kayıtları; ilçe kaynakta yok (cami/mezarlık adındaki köy/ilçe adı çıkarılmaz) -> ilce_belirsiz.

## Yeni il ekleme kalıbı
1. `okuyucu/<il>.py` aç; `ortak`'ı içe aktar (`indir`, `robots_izin`, `tr_title`, `tarih_iso`, `kayit_id`, `gun_yaz`, `eski_gunleri_sil`, `son7gun_yaz`; yalnız güncel liste veren siteler için `liste_birikim`).
2. `ilceler.json`'a ilin resmî ilçelerini ekle. Kaydın `ilce` alanına kaynağın ham değerini yaz.
3. Her kaydı şemaya çevir; karşılığı olmayan alana `null`, ham değerleri `ham`'a yaz. `main()` için trabzon.py örnek.
4. `hepsi.py` içindeki `ILLER` listesine il adını ekle.

## 9 il paketi (08.10.2026): afyonkarahisar, aksaray, bartin, bilecik, bolu, canakkale, cankiri, duzce, elazig
Ortak yardımcılar `okuyucu/ortak9.py` (ortak.py'ye dokunmaz): `Oturum` (çerezli GET/POST, multipart), `birlestir`/`yaz` (mevcut gün dosyalarıyla birleştirip yazar; kaynak sayfadan düşen kayıt silinmez), `cenaze_cumlesi` ("Cenazesi ... namazından sonra X'ten kaldırılarak Y'ye defnedilecektir" -> namaz yeri/vakti + defin yeri), `curl_indir`/`indir_yedekli`.
- **afyonkarahisar**: `afyon.bel.tr/cenaze-ilanlari` tek sayfa (6,6 MB, ~330 ilan, en yeni üstte). Ilan tarihi/saati, ad, yaş, defin yeri, mahalle, namaz cümlesi. İlan metnindeki akraba sayımı ALINMAZ. Gün = ilan tarihi; ilçe yok.
- **aksaray**: `ebelediye.aksaray.bel.tr` POST `/VefatEdenler/VefatEdenleriGoruntule` (multipart; `__RequestVerificationToken` formdan + çerez; ilkTarih/sonTarih = VEFAT tarihi aralığı). reCAPTCHA kapalı (`recaptchaKapali = True`), açılırsa okuma durur. ÖLÜM SEBEBİ, CENAZEYLE İLGİLENEN, doğum yeri ALINMAZ. Gün = defin tarihi; saat `namaz_yeri_vakti`'ne.
- **bartin**: `bartin.bel.tr/vefat-ilanlari` akordeon (en yeni ~15 ilan; "Daha fazla göster" JS). Vefat/doğum tarihi, baba adı, mahalle, namaz yeri-vakti, defin yeri. Gün = vefat tarihi; günlük çalıştıkça birikir.
- **bilecik**: sayfanın kendi çağrısı `POST /VefatEdenlerAjax` (ay=&yil=); kart = ad + ilan tarihi + serbest metin (akraba sayımı ALINMAZ, yalnız "Cenazesi ..." cümlesi). Mahalle/ilçe yok.
- **bolu**: WordPress günlük yazı; `/category/vefatilanlari/feed/` (~10 gün). Yazıda `<strong>AD</strong>` + akraba paragrafı (ALINMAZ) + "Cenazesi ..." cümlesi. Defin yeri başka ilin adıyla başlıyorsa ("Çankırı Ilgaz İlçe Mezarlığı") il_disi_defin.
- **canakkale**: liste sayfası + her ilan ayrı sayfa (`/tr/sayfa/1214-cenaze-ilanlari/<id>-GGAAYYYY-tarihli-cenaze-ilani`); yalnız pencere içindeki ilan sayfaları açılır. Hepsi merkez ("Çanakkale eşrafından"), ilçe yok.
- **cankiri**: `cankiri.bel.tr/vefat-edenler` tablo, YALNIZ son 10 kayıt (formdaki tarih süzgeci sonucu değiştirmiyor, denendi) -> defin tarihine göre BİRİKTİRİLİR; günde birkaç kez çalıştır. "X ilinde" -> il_disi_defin; köy/ilçe adı ilçe sayılmaz (defin yeri).
- **duzce**: `mebis.duzce.bel.tr/vefat-edenler` Blazor Server; ilk yüklemedeki "Bugün" listesi sunucuda hazır geliyor, başka güne geçmek SignalR ister (yapılamaz, `?tarih=` işe yaramıyor). 08.10'da liste BOŞ: kayıt içeren kart işaretlemesi hiç görülmedi -> dolu liste ayrıştırılmıyor, uyarı basılıp `veri/duzce/_dolu_ornek.html`'e örnek yazılır. Dolu gün görülünce ayrıştırıcı bu örneğe göre tamamlanmalı.
- **elazig**: `www.elazig.bel.tr/vefat-edenler/` + `/sayfa/N/` (24 kayıt/sayfa, pencere bitene dek en çok 6 sayfa). Cenaze sahibi (yakın) ve taziye bilgisi ALINMAZ. Site yalnız TLS 1.3 konuşur; Python 3.9/LibreSSL 2.8 (bu Mac) bağlanamaz -> `ortak9.indir_yedekli` sistem curl'üne düşer (doğrulama AÇIK). OpenSSL 1.1.1+ olan ortamda (GitHub Actions) urllib doğrudan çalışır.

### 08.10.2026 ekleme: erzincan, gumushane, isparta, kirsehir, nevsehir, nigde, rize, sinop (sakarya YOK)
Hepsinde ilçe kaynakta yazmıyorsa `ilce: null` + `ilce_belirsiz` (tahmin yok); yakın listesi, telefon, taziye, ölüm nedeni ALINMAZ; robots.txt kapalı değil.
- **erzincan**: `erzincan.bel.tr/vefatedenler?page=N` (10 kayıt/sayfa, yeniden eskiye). "Pülümür-1931" = DOĞUM yeri/yılı (ilçe DEĞİL, `ham.dogum`). Gün = DEFİN TARİHİ. Açıklamadan yalnız "Cenazesi ..." cümlesi. Ayrıntı modalındaki (`/vefatedenler/<id>`) iletişim/telefon hiç çekilmez.
- **gumushane**: `gumushane.bel.tr/2/duyuru/?type=1&page=N` liste + her duyurunun ayrıntı sayfası (≈ haftada 4-5 ilan). Ad başlıktan ("... hakkın rahmetine kavuşmuştur"), mahalle "... mahallesi sakinlerinden"den, namaz/defin "Cenazesi ..." cümlesinden. Gün = duyuru tarihi.
- **isparta**: `isparta.bel.tr/vefat-ilanlari` İSAY `custom-table` (yalnız güncel liste -> `liste_birikim`, geçmiş günlük çalıştıkça dolar). ADRES'ten yalnız mahalle. İlçe: defin yeri "İLÇE / ... Mezarlığı" ya da adres/mezarlık adı tek başına ilçe/il ise ("Ş.KARAAĞAÇ" -> Şarkikaraağaç); Merkez mezarlıkları ilçe yazmaz. `namaz_tarihi` = "TARİH / VAKİT" sütunu.
- **kirsehir**: `kirsehir.bel.tr/cenaze-ilanlari?page=N` akordeon. **Telefon, Yakını ve Adres alınmaz** (Adres taziye/ev adresi olabilir). Memleketi/Defin yeri köy adıdır (ilçe değil).
- **nevsehir**: `nevsehir.bel.tr/vefat-edenler?page=N` serbest `<p>` kutuları, SEZGİSEL ayrıştırma (yaş satırından geriye ad bulunur; ölüm nedeni atılır; tek başına ilçe adı satırı = ilçe; "... MAH." = mahalle). Kutu başlık tarihi zaman damgasıyla >3 gün çelişirse damga kullanılır (kaynakta "06.09" yazım hatası vardı). Bozuk kutular `veri/nevsehir/ayristirilamayan.json`.
- **nigde**: `vefatedenler.nigde.bel.tr/vefatedenler.php?araTarih=YYYY-AA-GG` (günlük sorgu, sayfa başına 3 satır, "Sonraki"). TLS: sunucu ara sertifikayı göndermiyor VE yerel depoda GlobalSign Root R46 yok -> `sertifika/nigde-zincir.pem` (GlobalSign GCC R46 AlphaSSL CA 2025 + Root R46, parmak izi okuyucu başlığında) yalnız bu bağlamda; doğrulama AÇIK. Uç sertifika Nisan 2027'de biter.
- **rize**: `rize.bel.tr/vefat-edenler?page=N` (6 kart/sayfa). "Mahalle / Köy" alanı `mahalle`'ye olduğu gibi gider ("Veliköy Köyü" dahil). Gün = cenaze tarihi.
- **sinop**: `sinop.bel.tr/vefat-ilanlar/?p=N` (10 kart/sayfa) serbest metin; yalnız namaz vakti + cami + mezarlık adı kalıpla çıkarılır (yakın listesi, kurum, evden alınış adresi ham alanda da saklanmaz).
- **sakarya**: OKUYUCU YAZILMADI. `sakarya.bel.tr/vefat-edenler` bir liste değil, ana sayfanın kendisini döndürüyor (site her `/vefat-edenler/...` yoluna ana sayfayı veriyor; sitemap da yok); tek gerçek liste `mebis.sakarya.bel.tr/BugunVefatEdenler` CAPTCHA'lı -> kullanılmaz.

## Şanlıurfa, Tokat, Uşak, Van, Karaman, Kütahya, Karabük, Yalova, Malatya (08.10.2026)
Ortak yeni yardımcı: `ortak_ek.py` (ortak.py'ye dokunulmadı): `son_gunler`, `metin`, `tarih_gg_aa_yyyy`, `yaz_birlestir` (gün dosyalarını yazarken var olan kayıtları KORUR; kaynak yalnız birkaç günü gösterdiği için geçmiş kendi dosyalarımızdan tamamlanır) ve `bos_kayit` (ilce_isle'ın işleyebilmesi için `il_disi_defin`/`ilce_belirsiz` anahtarı eklemez).
- **sanliurfa**: `sanliurfa.bel.tr/kategori/80/0/taziye-defteri` (tek sayfada ~150 satır: ad + eklenme zamanı) + her ilanın `/icerik/<no>/106/<slug>` ayrıntısı (baba adı, doğum YILI, ölüm tarihi, defin tarihi, defin yeri). İrtibat (telefon) ve Taziye Yeri (adres) AYRIŞTIRILIR ama KAYDEDİLMEZ. Ayrıntı yalnız son 7 gün için çekilir; daha önce okunmuş ilan yeniden çekilmez (ilk koşu ~100 sn). İlçe yok -> belirsiz. Yaş türetilmez (doğum yalnız yıl, `ham.dogum_yili`). Kaynakta hafta sonu girişi seyrek (3-4 Ekim boş).
- **tokat**: Nuxt sitesinin kendi API'si `client-api.tokat.bel.tr/api/public/obituaries?page=1&limit=60` (www robots.txt `Allow: /api/public/obituaries`). Ad, `deathDate`, cami, mezarlık/köy, namaz vakti. `relatives`/`phone`/`address` ALINMAZ. İlçe ayrı alan değil (cami/mezarlık adından çıkarılmaz) -> belirsiz. Sunucu HTTP/2'de kopuyor (curl), urllib (HTTP/1.1) sorunsuz.
- **usak**: `usak.bel.tr/cenaze-ilanlari[/N]` (sayfa başına 12, en çok 6 sayfa). Serbest metin: "Cenazesi <vakit> namazına müteakip <cami>'nden alınarak <yer> defnedilecektir" -> `namaz_yeri_vakti` cümlenin bu kısmı, `defin_yeri` ek atılmış yer adı; ham metin `ham.ilan_metni`. Hangi gün olduğu yazmadığı için yalnız `liste_tarihi` (ilan günü) dolu. robots.txt yalnız tek bir ayrıntı sayfasını yasaklar; ayrıntı sayfalarına girilmez.
- **van**: `van.bel.tr/Taziyeler.html` (tek sayfa, ~5 günlük ~39 kayıt, sayfalama yok). İlçe küçük harf ASCII ("tusba", "ipekyolu") -> `ilceler.json` ile eşlenir; `ildisi` = başka ilde defin (hangi il bilinmiyor) -> ilce null, ilce_belirsiz, `il_disi_defin` null. Taziye sahibi/tel/yakınlık/adres kaynakta yorum satırında, alınmaz.
- **karaman**: `http://web.karaman.bel.tr:571/Mebis/VefatListesi.aspx` (http, iso-8859-9, TLS yok). Liste (~40 satır) + her satır için `__doPostBack` ayrıntısı (ikamet mahallesi, namaz günü/vakti/çıkış yeri, mezarlık adı, ada no). Aslen (memleket) yalnız ham'da. Son 7 gün ~12 ayrıntı isteği (~50 sn). İlçe yok ("Merkez Mezarlığı") -> belirsiz.
- **kutahya**: gün sayfası `kutahya.bel.tr/vefat2.asp?tarih=G.A.YYYY` (7 gün = 7 istek). İlan metni (akraba adları) ALINMAZ; kartın seçenek satırlarından (ikon: saat/ay/harita) vakit, cami, mezarlık. Namaz günü sayfa günü ("YARIN" yazıyorsa +1). İlçe yok -> belirsiz. robots.txt yok.
- **karabuk**: `karabuk.bel.tr/vefat-edenler.asp` yalnız o an yayındaki kayıtları gösterir. 08.10 gece liste BOŞTU; dolu satır HTML'i görülemedi -> ayrıştırıcı tablo başlıklarına göre yazıldı, SINANMADI. Sayfada tanınmayan içerik varsa RuntimeError verir (sessiz boş yazmaz). Günde birkaç kez çalıştırılıp ilk dolu kayıtta doğrulanmalı. `mebis.karabuk.bel.tr` HTTP 500 verdi.
- **yalova**: `yalova.bel.tr/vefatedenler[?page=N]` (HTML tablo, 20 satır/sayfa; mobil kart kopyaları atlanır). Defin Yeri sütunu yalnız resmî ilçe adıyla birebir eşleşirse ilçe olur (Çiftlikköy); "Yalova Merkez", semt ve köyler belirsiz kalır. Açıklama ("MERKEZ CAMİ İKİNDİ") `namaz_yeri_vakti`'ne aynen.
- **malatya**: `mebis.malatya.bel.tr` DevExpress GridView; açılış = bugün; geçmiş gün için POST: `ctl00$ContentPlaceHolder1$ASPxDateEdit1` + `...$State={"rawValue":<ms>}` + `Listele` (tarih kutusunun değiştiği doğrulandı). 08.10 gece her gün "Görüntülenecek veri yok" döndü -> dolu satır şeması SINANMADI (sütun adlarıyla ayrıştırılır). Sabah/öğlen yeniden dene.

## 16 il, yalnız İLÇE düzeyinde kaynak (08.10.2026): artvin, samsun, erzurum, mugla, balikesir, tekirdag, yozgat, adiyaman, antalya, burdur, hatay, aydin, ankara, istanbul, izmir, eskisehir
Bu illerde il belediyesinin listesi yok (ya da robots/e-Devlet engeli var); bir il = TEK dosya `okuyucu/<il>.py`, içinde okunabilen her ilçe AYRI kaynak (işlev) ve ayrı `kaynak_ad` ("X Belediyesi"). Çıktı yine `veri/<il>/son7gun.json`; kayıtların `ilce` alanı kaynağın ilçesidir (dolu; `ilce_belirsiz` false). Başka ilde defin cümlesi varsa (`il_disi_defin` dolu) kayıt `il_disi` listesine gider, `ilce` yine kaynağın ilçesidir.
Ortak yardımcı `ortak_ilce.py` (ortak.py'ye dokunulmaz): robots.txt (host başına bir kez; 401/403 = yasak), 403/429 gelirse o ilçe BIRAKILIR (`Engel`), bir ilçe hata verirse öbürleri sürer, gün dosyaları `ortak_ek.yaz_birlestir` ile BİRLEŞTİRİLİR (kaynaktan düşen kayıt silinmez), büyük listeler (`al_parca`) parça parça okunup pencere dışına çıkınca kesilir (tek istek), gün parametreli kaynaklarda (`Durum`, `veri/<il>/_tarama.json`) son 2 gün her çalışmada, eski günler bir kez okunur. Serbest metinden yalnız `cenaze_ayikla()` ("Cenazesi ..." cümlesi: namaz yeri/vakti + defin yeri) ve `mahalle_ayikla()` alınır; telefon, yakın adları, taziye/ev adresi, ölüm nedeni, meslek ALINMAZ. Doğum tarihi saklanmaz (yalnız yaş).
Seçenekler: `--gun N`, `--ilce Ad[,Ad]` (örn. `python3 okuyucu/mugla.py --ilce Bodrum`). TLS: Şavşat, Milas, Çifteler sunucuları ara sertifikayı göndermiyor -> `sertifika/ilce-zincir.pem` (SSL2BUY + SSL.com 2022 kökü + zincir-eksik-ara.pem; doğrulama AÇIK; sertifikalar 01.11.2026 (Çifteler), 14.01.2027 (Milas), 01.04.2027 (Şavşat)'ta yenilenir, zincir değişirse AIA'dan tazele).
- **artvin**: Şavşat `savsat.bel.tr/cenaze-ilanlari` (son 10 kart). · **samsun**: 19 Mayıs `19mayis.bel.tr/cenaze-ilanlari?tarih=` (yakın+telefon yok sayılır).
- **erzurum**: Uzundere `uzundere.bel.tr/?p=vefat` (seyrek, serbest metin). · **mugla**: Bodrum, Milas, Fethiye (ASP.NET sayfalama), Seydikemer (ölüm nedeni sütunu OKUNMAZ), Dalaman.
- **balikesir**: Bandırma, Burhaniye (6,6 MB, parça parça), Altıeylül (izlemede: son kayıt 28.09). · **tekirdag**: Süleymanpaşa (1,5 MB), Muratlı (sunucu sayfayı Location'sız "301" ile döndürür; gövde alınır).
- **yozgat**: Sorgun, Çekerek (il belediyesi robots ile kapalı). · **adiyaman**: Besni, Kâhta (kaynak tarih yazım hatalarını `tarih()` eler). · **antalya**: Alanya. · **burdur**: Bucak. · **hatay**: Dörtyol (gün sayfaları). · **aydin**: Söke.
- **ankara**: Ayaş, Beypazarı, Çubuk (WordPress yayını; son cenaze yazısı 2020: izlemede), Kalecik, Polatlı (403 görülmedi). · **istanbul**: Arnavutköy (liste yalnız 2020 örnek satırı: izlemede), Silivri. · **izmir**: Bayındır (2,2 MB), Ödemiş, Torbalı (3,3 MB). · **eskisehir**: Çifteler (izlemede: son ilan 28.09).
İzlemede = ayrıştırıcı örnek günle sınandı (`--gun 14`), pencerede 0 kayıt normaldir; yeni ilan çıkınca alınır.

## YEREL BASIN kaynakları (site sahibi kararı 08.10.2026): amasya, mardin, siirt, bitlis, manisa + ankara'da "Ankara Net Haber"
Belediye kaynağı olmayan illerde yerel haber sitelerinin GÜNLÜK vefat listelerinden yalnız OLGU alınır (ad soyad, vefat/namaz/defin tarihi,
cami + vakit kısa biçimde "X Camii, öğle namazı", mezarlık, varsa ilçe/köy, yaş). Sitenin cümlesi, taziye metni/yeri, telefon, adres,
yakın adları, fotoğraf, ölüm nedeni ALINMAZ. Kayıtta `kaynak_turu: "yerel_basin"`, `kaynak_ad` = site adı, `kaynak_url` = o günkü liste
sayfası; `ham` yalnız `sayfa_tarihi` + `tarih_kaynagi` ("metin" | "yayin_tarihi": ilanda tarih yoksa yayın günü kullanıldı).
Ortak yardımcı `ortak_basin.py` (ortak.py'ye dokunmaz): site başına günde EN ÇOK 3 istek (robots.txt dahil; sayaç + okunan sayfalar +
7 günlük robots önbelleği `veri/<il>/_basin.json`), dizin = site haritası/RSS (tek istek), okunmuş sayfa yeniden okunmaz (bugün/dünün
sayfası 4 saatte bir), önce hiç okunmamış sayfalar; 401/403/429 ya da robots yasağı -> kaynak bırakılır (Engel). Serbest metin
ayrıştırıcı `serbest_kayitlar()`: ölüm ifadesinden ("Hakk'ın rahmetine kavuştu", "vefat etmiştir") hemen önceki büyük harfli 2-5 sözcük
ad sayılır; adı yazılmayan ilan (ör. "... annesi Hakk'ın rahmetine kavuştu") ALINMAZ. Siteler ve biçimleri:
`arastirma/yerel-basin-2026-10-08.md`.

## KAPI (yayın öncesi makine denetçisi): `python3 okuyucu/kapi.py [il ...] [--kuru]` ya da `python3 okuyucu/hepsi.py --kapi`
veri/<il>/son7gun.json'daki her kayıt K1-K8 kurallarından geçer (zorunlu alan, ad biçimi, tarih penceresi/gelecek, telefon-TC-e-posta-adres,
ölüm nedeni, aynı kişi aynı gün, alan adı tutarlılığı, yerel basında site cümlesi/60 karakter). Geçmeyen kayıt son7gun'dan çıkarılır,
`veri/<il>/_kapi_red.json`'a yazılır; özet `veri/kapi.json`; `veri/ozet.json` kayıt sayısı güncellenir. Yeni yerel basın sitesi eklenince
`kapi.YEREL_BASIN`'a (kaynak_ad -> alan adı) da yazılır, yoksa K7 eler.

## YEREL HABER: tek kişilik vefat haberleri (site sahibi kararı 08.10.2026)
Yeni iller: agri, ardahan, bayburt, bingol, corum, diyarbakir, hakkari, igdir, kars, kastamonu, kilis, kirklareli, mersin, mus,
sirnak ve tunceli. Ayrıca eskisehir.py ile izmir.py'ye `HABER_SITELERI` eklendi.
Ortak kod `ortak_haber.py` dosyasında. Her il dosyası `SITELER = [oh.site(ad, slug, rss, kesin_yerel=, ilce=, takma=, ek_dizin=)]`
listesini taşır ve `oi.il_calistir(IL, klasör, oh.okuyucular(IL, SITELER))` ile çalışır.
- Dizin sitenin RSS'idir ve 6 saat önbellekte tutulur (`veri/<il>/_haber_dizin/`). `ek_dizin` sitenin aylık haritasıdır; RSS'e
  girmeyen vefat haberlerinin adresini verir ve bu haberler bütçe kaldıkça açılır.
- Seçim ve yerellik kuralları için `ortak_haber.yerel_mi` ile `vefat_haberi_mi` işlevlerine bakılır. Ad yalnız Türkçe başlıktan ya da
  özetten alınır; site haritasındaki adres parçasından alınmaz.
- Kayıtta `kaynak_turu` "yerel_haber" olur, `kaynak_url` haberin adresidir. `ham` alanında yalnız `yayin_tarihi` ve `tarih_kaynagi` durur.
- Açılan haberden yalnız OLGULAR saklanır (`_haber_olgu.json`, 10 gün). Metin saklanmaz.
- İstek bütçesi `ortak_basin` ile ortaktır: site başına günde 3 istek. `www.` ile `www.`siz adres aynı site sayılır (`site_anahtari`).
- Yeni bir site eklenince `kapi.YEREL_BASIN` listesine site adı ve alan adı yazılır. Yazılmazsa K7 kaydı eler.
- Siteler, hacim ve sıfır çıkan iller: `arastirma/yerel-haber-2026-10-08.md`.
