# Kaynak kayıt defteri — şema (15.10.2026, site sahibi kararı)

Sahibi: "ajan araştırsın dediğimde ajan görevlendirmeyecek, yalnız İŞARETLEYECEK: 'şu sayfada güncel içerik var ve vefat haberlerine sık yer veriyor'. GitHub'daki düzenek verilen işaretli yerleri gezecek." Yani: ajan kod yazmaz, bu deftere satır ekler; `okuyucu/kayitli_kaynak.py` (genel okuyucu) her turda defteri okur.

Dosya: `okuyucu/kaynaklar/bolge-<bolge>.json` (bolge: marmara, ege, akdeniz, ic-anadolu, karadeniz, dogu-anadolu, guneydogu-anadolu). JSON dizisi; her öğe:

```json
{
  "il": "erzurum",                      // okuyucu/ilceler.json anahtarı (küçük harf, ASCII: agri, mus, igdir)
  "ilce": "Merkez",                     // ilceler.json'daki yazım; il geneli kaynaksa null
  "ad": "Erzurum Pusula Gazetesi",      // kaynağın adı, sitede yazdığı gibi
  "url": "https://www.erzurumpusula.com",   // ana adres (alan adı K7 kaydına girer)
  "tur": "yerel_basin",                 // belediye | muftuluk | yerel_basin | ulusal
  "kalip": "rss",                       // rss | sitemap | liste | tablo   (genel okuyucunun hangi yolla okuyacağı)
  "rss_url": "https://www.erzurumpusula.com/rss",            // kalip rss ise
  "sitemap": "https://www.erzurumpusula.com/sitemap/sitemap-{AY}.xml",  // varsa (oh.site ek_dizin)
  "liste_url": null,                    // kalip liste/tablo ise: vefat listesinin sayfası
  "takma": ["Erzurum"],                 // ilçe/il için sitedeki başka yazımlar (isteğe bağlı)
  "kesin_yerel": false,                 // site yalnız bu ilçeyi/ili yazıyorsa true
  "siklik_dk": 60,                      // en az kaç dakikada bir okunsun (60 = her saatlik tur)
  "robots": "izin",                     // robots.txt kontrolü: izin | yasak (yasak ise okunmaz, satır kanıt olarak kalır)
  "kanit": ["2026-10-15 Hayatını kaybeden X toprağa verildi", "2026-10-13 …", "2026-10-11 …"],  // son 3 vefat haberi: tarih + başlık (ajanın gözle gördüğü)
  "guncel": "2026-10-15",               // sitedeki en yeni içeriğin tarihi
  "isaretleyen": "ajan-dogu-anadolu",
  "tarih": "2026-10-15",
  "not": ""                             // ör. "vefat haberleri 'Yaşam' kategorisinde", "belediye duyuru sayfası PDF"
}
```

Kurallar:
- Defter yalnız HERKESE AÇIK, girişsiz, CAPTCHA'sız sayfaları içerir; Facebook/Instagram/WhatsApp satırı YAZILMAZ.
- `robots` alanı ajan tarafından gerçekten kontrol edilir (`<url>/robots.txt`); "yasak" ise genel okuyucu o satırı atlar.
- Kanıt olmadan satır yok: `kanit` en az 2 tarihli başlık; son 30 günde vefat haberi yoksa satır eklenmez (defteri kirletmez).
- Aynı alan adı iki satırda olmaz (il geneli bir satır; ilçe gazeteleri ayrı satır).
- Büyükşehirler de deftere GİRER (sahibi kararı 15.10.2026 17:20: "İstanbul vefat haberleri diye günlük paylaşım yapan platformlar vardır, onları da dahil et"): büyükşehirde ilçe gazeteleri yerine önce İL GENELİ günlük vefat/cenaze listesi yayımlayan toplu sayfalar aranır (ör. "istanbul vefat haberleri", "ankara bugün vefat edenler"); e-Devlet ve belediye listeleri ayrıca sürer, K10 tekilleştirme kopyayı eler.
- Genel okuyucu, her satırı `ortak_basin.oh.site(ad, anahtar, rss_url, kesin_yerel=…, ilce=…, takma=…, ek_dizin=sitemap)` ile ya da liste/tablo kalıbıyla okur; kayıtlar `kapi.py` K1–K10'dan geçer; `kaynak_turu` = tur. Alan adı K7 için defterden otomatik kayıtlıdır.
