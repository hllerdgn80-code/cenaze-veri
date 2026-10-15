"""Kayıt defteri okuyucusu testleri (ağ YOK: sahte indirme)."""
import json, os, sys, tempfile, unittest
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kayitli_kaynak as kk, kapi, ortak_basin as ob, ortak_ilce as oi

BUGUN = date.today()
D = BUGUN.strftime("%d.%m.%Y")


def satir(**a):
    s = {"il": "agri", "ilce": None, "ad": "Test Gazetesi", "url": "https://www.testgazete.com", "tur": "yerel_basin", "kalip": "rss",
         "rss_url": "https://www.testgazete.com/rss", "sitemap": None, "liste_url": None, "takma": [], "kesin_yerel": True,
         "siklik_dk": 60, "robots": "izin", "kanit": ["2026-10-15 a", "2026-10-13 b"]}
    s.update(a)
    return s


class Sema(unittest.TestCase):
    def test_gecerli_satir(self):
        t, n = kk.dogrula(satir())
        self.assertEqual(n, []); self.assertEqual(t["robots"], "izin")

    def test_eksik_alan(self):
        s = satir(); del s["ad"]
        t, n = kk.dogrula(s)
        self.assertIsNone(t); self.assertTrue(any("ad" in x for x in n))

    def test_kanit_az(self):
        self.assertIsNone(kk.dogrula(satir(kanit=["tek"]))[0])

    def test_facebook_yasak(self):
        self.assertIsNone(kk.dogrula(satir(url="https://www.facebook.com/x", rss_url="https://www.facebook.com/x/rss"))[0])

    def test_buyuksehir_artik_girer(self):
        self.assertIsNotNone(kk.dogrula(satir(il="istanbul"))[0])

    def test_rss_url_yok_ve_baska_alan_adi(self):
        self.assertIsNone(kk.dogrula(satir(rss_url=None))[0])
        self.assertIsNone(kk.dogrula(satir(rss_url="https://baska.com/rss"))[0])

    def test_defter_bozuk_satiri_atlar_ayni_alan_adi_tek(self):
        with tempfile.TemporaryDirectory() as d:
            yol = os.path.join(d, "bolge-x.json")
            json.dump([satir(), {"bozuk": 1}, satir(ad="Ikinci")], open(yol, "w"))
            uy = []
            out = kk.defter_oku([yol], uyar=uy.append)
            self.assertEqual(len(out), 1); self.assertEqual(len(uy), 2)
            bozuk = os.path.join(d, "bolge-y.json"); open(bozuk, "w").write("{{")
            self.assertEqual(kk.defter_oku([bozuk], uyar=uy.append), [])


class Siklik(unittest.TestCase):
    def test_robots_yasak_atlanir(self):
        self.assertIn("robots", kk.atlama_nedeni(satir(robots="yasak"), {"son": {}}))

    def test_siklik_dolmadi_ve_doldu(self):
        s = kk.dogrula(satir(siklik_dk=180))[0]
        simdi = datetime(2026, 10, 15, 12, 0)
        d = {"son": {kk.satir_anahtari(s): (simdi - timedelta(minutes=60)).isoformat()}}
        self.assertIn("siklik_dk", kk.atlama_nedeni(s, d, simdi))
        d["son"][kk.satir_anahtari(s)] = (simdi - timedelta(minutes=179)).isoformat()   # tolerans 5 dk
        self.assertIsNone(kk.atlama_nedeni(s, d, simdi))
        self.assertIsNone(kk.atlama_nedeni(s, {"son": {}}, simdi))


class Esleme(unittest.TestCase):
    def test_rss_site_parametreleri(self):
        s = kk.dogrula(satir(ilce="Doğubayazıt", takma=["Doğubeyazıt"], sitemap="https://www.testgazete.com/sitemap-{AY}.xml"))[0]
        t = kk.site_tanimi(s)
        self.assertEqual((t["ad"], t["dizin"], t["ilce"], t["takma"], t["kesin_yerel"]),
                         ("Test Gazetesi", "https://www.testgazete.com/rss", "Doğubayazıt", ("Doğubeyazıt",), True))
        self.assertEqual(t["ek_dizin"], "https://www.testgazete.com/sitemap-{AY}.xml")

    def test_sitemap_kalibi_dizin(self):
        s = kk.dogrula(satir(kalip="sitemap", rss_url=None, sitemap="https://www.testgazete.com/s-{AY}.xml"))[0]
        self.assertEqual(kk.site_tanimi(s)["dizin"], f"https://www.testgazete.com/s-{BUGUN.strftime('%Y-%m')}.xml")

    def test_satir_oku_haber_kaynagina_gider(self):
        s = kk.dogrula(satir())[0]
        cagri = {}
        def sahte(ctx, il, slug, ad, dizin, **kw):
            cagri.update(il=il, dizin=dizin, kw=kw)
            return [{"id": "1", "kaynak_turu": "yerel_haber", "kaynak_ad": "x"}]
        eski = kk.oh.haber_kaynagi
        kk.oh.haber_kaynagi = sahte
        try:
            k = kk.satir_oku({}, "Ağrı", s)
        finally:
            kk.oh.haber_kaynagi = eski
        self.assertEqual(cagri["il"], "Ağrı"); self.assertEqual(k[0]["kaynak_turu"], "yerel_basin"); self.assertEqual(k[0]["kaynak_ad"], "Test Gazetesi")


TABLO = f"""<table><tr><th>Adı Soyadı</th><th>Cenaze Yeri</th><th>Saat</th><th>Mezarlık</th><th>Tarih</th></tr>
<tr><td>AHMET YILMAZ (65)</td><td>Merkez Camii</td><td>14:30</td><td>Asri Mezarlığı</td><td>{D}</td></tr>
<tr><td>Ayşe Demir</td><td>Ulu Camii</td><td>11:00</td><td>-</td><td>01.01.2020</td></tr>
<tr><td>Veli Kaya</td><td>Çarşı Camii</td><td></td><td></td><td></td></tr></table>"""
LISTE = f"<ul><li>Mehmet Can Aksoy - Hacı Bayram Camii 13:00 - {D} - Kuzey Mezarlığı</li><li>Fatma Er - Cami - 02.02.2019</li><li>Ana Sayfa</li></ul>"
CTX = {"alindi": "2026-10-15T10:00:00+03:00", "gunler": oi.gunler()}


class Liste(unittest.TestCase):
    def test_tablo(self):
        s = kk.dogrula(satir(kalip="tablo", rss_url=None, liste_url="https://www.testgazete.com/vefat", tur="belediye"))[0]
        k = kk.tablo_ayristir(TABLO, CTX, "Ağrı", s)
        self.assertEqual(len(k), 1)           # eski tarihli ve tarihsiz satır alınmaz
        k = k[0]
        self.assertEqual((k["ad_soyad"], k["yas"], k["liste_tarihi"]), ("Ahmet Yılmaz", 65, BUGUN.isoformat()))
        self.assertEqual(k["namaz_yeri_vakti"], "Merkez Camii, 14:30"); self.assertEqual(k["defin_yeri"], "Asri Mezarlığı")
        self.assertEqual(k["kaynak_turu"], "belediye"); self.assertTrue(k["ilce_belirsiz"])
        self.assertTrue(all(len(k[a]) <= 60 for a in ("namaz_yeri_vakti", "defin_yeri")))

    def test_liste(self):
        s = kk.dogrula(satir(kalip="liste", rss_url=None, liste_url="https://www.testgazete.com/vefat"))[0]
        k = kk.liste_ayristir(LISTE, CTX, "Ağrı", s)
        self.assertEqual([x["ad_soyad"] for x in k], ["Mehmet Can Aksoy"])
        self.assertEqual((k[0]["namaz_yeri_vakti"], k[0]["defin_yeri"]), ("Hacı Bayram Camii, 13:00", "Kuzey Mezarlığı"))

    def test_site_cumlesi_ve_telefon_atilir(self):
        self.assertIsNone(kk._temiz_alan("Allah rahmet eylesin"))
        self.assertIsNone(kk._temiz_alan("Aile 0532 123 45 67"))
        self.assertEqual(kk._temiz_alan("Merkez Camii"), "Merkez Camii")

    def test_ad_ayikla(self):
        self.assertEqual(kk.ad_ayikla("MEHMET ALİ ÖZ (80)"), ("Mehmet Ali Öz", 80))
        self.assertEqual(kk.ad_ayikla("Tek"), (None, None))
        self.assertEqual(kk.ad_ayikla("Ana Sayfa 2"), (None, None))


class K7(unittest.TestCase):
    def test_defter_alan_adi_kayitli(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "kaynaklar"))
            json.dump([satir(ad="Defter Test Siteri", url="https://www.deftertest.com")], open(os.path.join(d, "kaynaklar", "bolge-t.json"), "w"))
            json.dump([satir(ad="Gizli", url="https://gizli.com")], open(os.path.join(d, "kaynaklar", "_ornek.json"), "w"))
            eski = kapi.DIZIN
            kapi.DIZIN = d
            try:
                a = kapi.defter_alan_adlari()
            finally:
                kapi.DIZIN = eski
        self.assertEqual(a, {"Defter Test Siteri": "www.deftertest.com"})


# Gerçek sayfalardan küçültülmüş örnekler (15.10.2026: malatyasonhaber.com/vefat kartı, malatyagazete.com günlük haber)
SON_HABER = """<div class="vef-grid"><article class="vef-card"><div class="vef-card-main"><div class="vef-card-top">
<h3 class="vef-name">MUSTAFA ACET</h3><span class="vef-age">87 yaş</span></div><div class="vef-meta"><span class="vef-meta-item">
<span data-ico="clock" data-ico-size="14"></span>
%(g)s </span><span class="vef-chip">BATTALGAZİ</span></div><p class="vef-place"><span data-ico="mapPin"></span>
<span>TANDOĞAN MH. BATTALGAZİ / MALATYA</span></p></div></article>
<article class="vef-card"><h3 class="vef-name">ESKİ KİŞİ</h3><span class="vef-age">70 yaş</span><div class="vef-meta"><span class="vef-meta-item"><span></span>
3 Ocak 2020 </span><span class="vef-chip">AKÇADAĞ</span></div><p class="vef-place"><span>AKÇADAĞ</span></p></article></div>"""
GAZETE = """<time datetime="%(iso)s T17:48:00+03:00" class="tarih">x</time><div itemprop="articleBody" class="metin-alan"><div id="rklm"><img alt="Reklam"></div>HATİCE AYDIN- YAŞ:80- ÇÖŞNÜK MH. BATTALGAZİ/MALATYA<br>NİYAZİ BAYDOĞAN- YAŞ:56- AKÇADAĞ/MALATYA<br>Allah rahmet eylesin- taziye evi</p></div><div class="etiketler">"""
KATEGORI = """<a href="/malatyada-bugun-8-kisi-vefat-etti-%(u1)s">a</a><a href="/malatyada-bugun-5-kisi-vefat-etti-18-eylul-2026">b</a><a href="/abdurrahman-yavuz-vefat-etti">c</a>"""
AYLAR = ["", "ocak", "subat", "mart", "nisan", "mayis", "haziran", "temmuz", "agustos", "eylul", "ekim", "kasim", "aralik"]
AYLAR_T = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


class GercekSayfa(unittest.TestCase):
    def setUp(self):
        self.s = kk.dogrula(satir(il="malatya", ad="Malatya Gazete", url="https://malatyagazete.com", rss_url="https://malatyagazete.com/rss",
                                  kalip="liste", liste_url="https://malatyagazete.com/kategori/vefat-edenler"))[0]

    def test_yer_ayir(self):
        self.assertEqual(kk.yer_ayir("Malatya", "TANDOĞAN MH. BATTALGAZİ / MALATYA"), ("Tandoğan Mahallesi", "Battalgazi"))
        self.assertEqual(kk.yer_ayir("Malatya", "AKÇADAĞ"), (None, "Akçadağ"))
        self.assertEqual(kk.yer_ayir("Malatya", "Bilinmeyen Yer"), (None, None))

    def test_kart_son_haber(self):
        dun = BUGUN - timedelta(days=1)
        html = SON_HABER % {"g": f"{dun.day} {AYLAR_T[dun.month]} {dun.year}"}
        k = kk.kart_ayristir(html, CTX, "Malatya", self.s)
        self.assertEqual(len(k), 1)           # 2020 tarihli kart pencere dışı
        self.assertEqual((k[0]["ad_soyad"], k[0]["yas"], k[0]["ilce"], k[0]["mahalle"], k[0]["liste_tarihi"]),
                         ("Mustafa Acet", 87, "Battalgazi", "Tandoğan Mahallesi", dun.isoformat()))
        self.assertFalse(k[0]["ilce_belirsiz"] if "ilce_belirsiz" in k[0] and k[0]["ilce"] else False)

    def test_gunluk_haber_govdesi(self):
        html = GAZETE % {"iso": BUGUN.isoformat()}.copy() if False else GAZETE.replace("%(iso)s T", BUGUN.isoformat() + "T")
        k = kk.gunluk_haber_ayristir(html, "https://malatyagazete.com/malatyada-bugun-2-kisi-vefat-etti", CTX, "Malatya", self.s)
        self.assertEqual([(x["ad_soyad"], x["yas"], x["ilce"]) for x in k], [("Hatice Aydın", 80, "Battalgazi"), ("Niyazi Baydoğan", 56, "Akçadağ")])
        self.assertEqual(k[0]["mahalle"], "Çöşnük Mahallesi"); self.assertEqual(k[0]["liste_tarihi"], BUGUN.isoformat())

    def test_gunluk_tarih_adresten(self):
        html = GAZETE.replace("<time datetime=\"%(iso)s T17:48:00+03:00\" class=\"tarih\">x</time>", "")
        u = f"https://malatyagazete.com/malatyada-bugun-2-kisi-vefat-etti-{BUGUN.day}-{AYLAR[BUGUN.month]}-{BUGUN.year}"
        self.assertEqual(kk.adres_tarihi(u), BUGUN.isoformat())
        self.assertEqual(len(kk.gunluk_haber_ayristir(html, u, CTX, "Malatya", self.s)), 2)

    def test_kategori_baglantilari_yalniz_pencere_ici(self):
        u1 = f"{BUGUN.day}-{AYLAR[BUGUN.month]}-{BUGUN.year}"
        acilan = []
        eski = (kk.ob.al, kk.ob.okunacak_mi, kk.ob.okundu)
        kk.ob.al = lambda ctx, u: acilan.append(u) or GAZETE.replace("%(iso)s T", BUGUN.isoformat() + "T")
        kk.ob.okunacak_mi = lambda *a: True
        kk.ob.okundu = lambda *a: None
        try:
            k = kk.gunluk_haberler(KATEGORI % {"u1": u1}, CTX, "Malatya", self.s)
        finally:
            kk.ob.al, kk.ob.okunacak_mi, kk.ob.okundu = eski
        self.assertEqual(len(acilan), 1); self.assertEqual(len(k), 2)     # eylül haberi ve ad-vefat haberi açılmaz


# 15.10.2026 gerçek sayfalardan küçültülmüş örnekler: Çanakkale Olay derleme, Sakarya Yenihaber etiketli bloklar, Kocaeli Gazetesi /vefat/ sayfası
G = BUGUN.isoformat()
CANAKKALE = ('<meta property="datePublished" content="%s T09:45:00+03:00"><h1>Çanakkale Vefat İlanları: x</h1><div class="detaymetin">'
             '<p>Çanakkale eşrafından;</p><h2>Müzeyyen GÜDEREL</h2><p>vefat etmiştir.</p><p>Cenazesi bugün öğle namazından sonra Yalı Camii\'nden '
             'kaldırılarak Şehrimiz Eski Mezarlığı\'na defnedilecektir.</p><p>Dost, akraba ve din kardeşlerine duyurulur.</p></div><div class="news-tags">' % G).replace(" T", "T")
SAKARYA = ('<script type="application/ld+json">{"datePublished": "%s"}</script><div class="detaymetin"><p>15 Ekim Sakarya\'da vefatlar</p>'
           '<p>ALİYE EKİNER<br>Doğum Tarihi: 12.07.1932<br>Ölüm Tarihi: 14.10.2026<br>Mezarlık: Serdivan Merkez Mezarlığı-2<br>'
           'Cami: Adapazarı Semerciler Mah. Şerefiye Cami<br>Vakit: Öğle<br>ŞABAN ŞAVLIK<br>ARİFİYE - NEVİYE<br>Doğum Tarihi: 1.03.1957<br>'
           'Ölüm Tarihi: 14.10.2026<br>Mezarlık: Arifiye Merkez Mezarlığı<br>Cami: Arifiye Neviye Mah. Büyükdere Cami<br>Vakit: İkindi</p></div><div class="news-tags">' % G)
KOCAELI = ('<meta itemprop="datePublished" content="%s">'.replace('itemprop="datePublished" content', 'name="datePublished" content') % G +
           '<h1>Seher Aydoğdu vefat etti</h1><section class="liste-cart"><article><h3>Seher Aydoğdu vefat etti</h3><p>İzmit Mehmet Ali Paşa Mahallesi’nde ikamet eden '
           'Seher Aydoğdu (86) vefat etti. Cenazesi ikindi namazına müteakip Mehmet Ali Paşa Camii’nde kılınan cenaze namazının ardından Kent Mezarlığı’nda toprağa verildi. </p></article></section>')


class Aday(unittest.TestCase):
    def setUp(self):
        self.s = kk.dogrula(satir(il="canakkale", ad="Çanakkale Olay", url="https://www.canakkaleolay.com", kalip="sitemap", rss_url=None,
                                  sitemap="https://www.canakkaleolay.com/sitemap.xml"))[0]

    def test_derleme_ilan(self):
        k = kk.aday_sayfa_oku(CTX, "Çanakkale", self.s, "https://www.canakkaleolay.com/haber/canakkale-vefat-ilanlari-1", CANAKKALE)
        self.assertEqual([(x["ad_soyad"], x["namaz_yeri_vakti"], x["defin_yeri"], x["liste_tarihi"]) for x in k],
                         [("Müzeyyen Güderel", "Yalı Camii, öğle namazı", "Eski Mezarlığı", G)])

    def test_etiketli_bloklar(self):
        s = kk.dogrula(satir(il="malatya", ad="Sakarya Test", url="https://www.sakaryayenihaber.com", kalip="sitemap", rss_url=None,
                             sitemap="https://www.sakaryayenihaber.com/s.xml"))[0]
        g = kk.govde_metni(SAKARYA.replace("<br>", "</p><p>"))
        k = kk.etiketli_blok_ayristir(g, CTX, "Sakarya", s, "https://www.sakaryayenihaber.com/haber/x-vefatlar", G)
        self.assertEqual([(x["ad_soyad"], x["yas"], x["defin_yeri"]) for x in k],
                         [("Aliye Ekiner", 94, "Serdivan Merkez Mezarlığı-2"), ("Şaban Şavlık", 69, "Arifiye Merkez Mezarlığı")])
        self.assertEqual(k[1]["namaz_yeri_vakti"], "Büyükdere Cami, ikindi namazı"); self.assertEqual(k[0]["vefat_tarihi"], "2026-10-14")

    def test_tekil_vefat_sayfasi(self):
        s = kk.dogrula(satir(il="kocaeli", ad="Kocaeli Gazetesi", url="https://www.kocaeligazetesi.com.tr", kalip="sitemap", rss_url=None,
                             sitemap="https://www.kocaeligazetesi.com.tr/s-{AY}.xml"))[0]
        k = kk.aday_sayfa_oku(CTX, "Kocaeli", s, "https://www.kocaeligazetesi.com.tr/vefat/28983321/seher-aydogdu-vefat-etti", KOCAELI)
        self.assertEqual((len(k), k[0]["ad_soyad"], k[0]["yas"], k[0]["defin_yeri"]), (1, "Seher Aydoğdu", 86, "Kent Mezarlığı"))

    def test_sitemap_kalibinda_ek_dizin_dizinle_ayni_olmaz(self):
        s = kk.dogrula(satir(kalip="sitemap", rss_url=None, sitemap="https://www.testgazete.com/s-{AY}.xml"))[0]
        self.assertIsNone(kk.site_tanimi(s)["ek_dizin"])

    def test_aday_adres_suzgeci(self):
        self.assertTrue(kk.TEKIL_YOL.search("https://x.com/vefat/28986594/halit"))
        self.assertTrue(kk.DERLEME_YOL.search("https://x.com/haber/canakkale-vefat-ilanlari-15-ekim-2026-1"))
        self.assertFalse(kk.DERLEME_YOL.search("https://x.com/haber/biga-da-yol-coktu-126973"))


if __name__ == "__main__":
    unittest.main()
