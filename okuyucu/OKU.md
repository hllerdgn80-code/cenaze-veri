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
