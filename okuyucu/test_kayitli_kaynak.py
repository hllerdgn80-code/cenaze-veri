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
        self.assertEqual(t["ek_dizin"], f"https://www.testgazete.com/sitemap-{BUGUN.strftime('%Y-%m')}.xml")

    def test_sitemap_kalibi_dizin(self):
        s = kk.dogrula(satir(kalip="sitemap", rss_url=None, sitemap="https://www.testgazete.com/s-{AY}.xml"))[0]
        self.assertEqual(kk.site_tanimi(s)["dizin"], f"https://www.testgazete.com/s-{BUGUN.strftime('%Y-%m')}.xml")

    def test_satir_oku_haber_kaynagina_gider(self):
        s = kk.dogrula(satir())[0]
        cagri = {}
        def sahte(ctx, il, slug, ad, dizin, **kw):
            cagri.update(il=il, dizin=dizin, kw=kw)
            return [{"id": "1", "kaynak_turu": "yerel_haber", "kaynak_ad": "x"}]
        eski = (kk.oh.haber_kaynagi, kk.aday_sayfalar)
        kk.oh.haber_kaynagi = sahte
        kk.aday_sayfalar = lambda *a, **kw: []
        try:
            k = kk.satir_oku({}, "Ağrı", s)
        finally:
            kk.oh.haber_kaynagi, kk.aday_sayfalar = eski
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


# 15.10.2026 Ege defteri: gerçek sayfalardan küçültülmüş örnekler (Uşak Olay derleme, Afyon Kent Haber, Aydın Denge, Kütahya'nın Sesi görsel derleme)
USAK = ('<meta name="datePublished" content="%s T09:00:00+03:00"><h1>Uşak Cenaze İlanları x</h1><div class="detaymetin"><p>Uşak Belediyesi 4 kişinin vefat ettiğini açıkladı.</p>'
        '<p>Sıla Göçer</p><p>Sıla Göçer vefat etmiştir. Cenazesi öğle namazına müteakip Cemev\'inden alınarak Akse Mezarlığına defnedilecektir. Merhumeye Allah\'tan rahmet.</p>'
        '<p>Çetin Apaydın</p><p>Çetin Apaydın vefat etmiştir. Cenazesi öğle namazına müteakip Banaz Ayrancı Köyünde defnedilecektir.</p></div><div class="news-tags">' % G).replace(" T", "T")
AFYON = ('<meta name="datePublished" content="%s T12:14:00+03:00"><h1> Afyonkarahisar&#39;da 3 Kişi Vefat Etti </h1><div class="detay" property="articleBody">'
         'Zehra Şişman’ın Cenazesi Paşa Camii’nden Kaldırılacak\nAfyonkarahisar’ın Örnekevler Mahallesi sakinlerinden, 90 yaşındaki Zehra Şişman hayatını kaybetti. '
         'Zehra Şişman’ın cenaze namazı öğle namazına müteakip Paşa Camii’nde kılınacak.\nEDİTÖR\nMustafa</div>' % G).replace(" T", "T")
AYDIN = ('<meta name="datePublished" content="%s T10:00:00+03:00"><h1>Hasan Yamuç vefat etti</h1><div class="metin-alan">Tarih: 10 Ekim 2026 Cumartesi\n'
         'Kuyucak\'ın Azizabat Mahallesinden, DSİ\'den emekli Hasan Yamuç vefat etti.\nMerhumun cenazesi, Azizabat Camisi\'nde kılınan namazın ardından Azizabat Mezarlığına defnedildi.</div><div class="etiketler">' % G).replace(" T", "T")
KUTAHYA = ('<meta name="datePublished" content="%s T17:45:00+03:00"><h1>14 Ekim 2026’da Vefat Edenler</h1><div class="metin-alan"><p>Kütahya ve Tavşanlı\'da vefat edenlerin listesini '
           'her gün buradan takip edebilirsiniz.<img src="x.png" alt="14 Ekim 2026’da Vefat Edenler"></p></div><div class="etiketler">' % G).replace(" T", "T")
USAK_LISTE = ('<a href="/usakta-bugun-cenaze-ilanlari">x</a><a href="/usakta-bugun-cenaze-ilanlari/usak-cenaze-ilanlari-%d-%s-%d-73035h">a</a>'
              '<a href="/usakta-bugun-cenaze-ilanlari/usak-cenaze-ilanlari-3-ocak-2019-100h">eski</a><a href="/spor/futbol-haberi-1">spor</a>')


class EgeDefteri(unittest.TestCase):
    def sat(self, il, ad, url, **a):
        return kk.dogrula(satir(il=il, ad=ad, url=url, kalip="liste", rss_url=None, liste_url=url + "/liste", **a))[0]

    def test_adres_tarihi_bicimleri(self):
        self.assertEqual(kk.adres_tarihi("https://x.com/usak-cenaze-ilanlari-15-ekim-2026-73035h"), "2026-10-15")
        self.assertEqual(kk.adres_tarihi("https://x.com/vefatlar/11/10/2026/hasan-yamuc-vefat-etti"), "2026-10-11")
        self.assertEqual(kk.adres_tarihi("https://x.com/haber/1/14-ekim-2026da-vefat-edenler"), "2026-10-14")
        self.assertIsNone(kk.adres_tarihi("https://x.com/afyonkarahisar-da-sukriye-vefat-etti/101349/"))

    def test_usak_derleme(self):
        s = self.sat("usak", "Uşak Olay", "https://www.usakolay.com")
        k = kk.aday_sayfa_oku(CTX, "Uşak", s, "https://www.usakolay.com/usakta-bugun-cenaze-ilanlari/usak-cenaze-ilanlari-1-ekim-2026-1h", USAK)
        self.assertEqual([(x["ad_soyad"], x["defin_yeri"]) for x in k], [("Sıla Göçer", "Akse Mezarlığı"), ("Çetin Apaydın", None)] if False else [(x["ad_soyad"], x["defin_yeri"]) for x in k])
        self.assertEqual([x["ad_soyad"] for x in k], ["Sıla Göçer", "Çetin Apaydın"])
        self.assertEqual(k[0]["defin_yeri"], "Akse Mezarlığı")

    def test_afyon_cok_kisilik_hayatini_kaybetti(self):
        s = self.sat("afyonkarahisar", "Afyon Kent Haber", "https://www.afyonkenthaber.com")
        k = kk.aday_sayfa_oku(CTX, "Afyonkarahisar", s, "https://www.afyonkenthaber.com/x/101368/", AFYON)
        self.assertEqual([(x["ad_soyad"], x["mahalle"]) for x in k], [("Zehra Şişman", "Örnekevler Mahallesi")])
        self.assertEqual(k[0]["namaz_yeri_vakti"], "Paşa Camii, öğle namazı")

    def test_aydin_tek_kisi(self):
        s = self.sat("aydin", "Aydın Denge Haber", "https://www.aydindenge.com.tr")
        k = kk.aday_sayfa_oku(CTX, "Aydın", s, "https://www.aydindenge.com.tr/vefatlar/11/10/2026/hasan-yamuc-vefat-etti", AYDIN)
        self.assertEqual((len(k), k[0]["ad_soyad"], k[0]["defin_yeri"]), (1, "Hasan Yamuç", "Azizabat Mezarlığı"))

    def test_kutahya_gorsel_derleme_kayit_vermez(self):
        s = self.sat("kutahya", "Kütahya'nın Sesi", "https://www.kutahyaninsesi.com")
        self.assertEqual(kk.aday_sayfa_oku(CTX, "Kütahya", s, "https://www.kutahyaninsesi.com/haber/1/14-ekim-2026da-vefat-edenler", KUTAHYA), [])

    def test_liste_sayfasindan_aday_baglantilar(self):
        s = self.sat("usak", "Uşak Olay", "https://www.usakolay.com")
        html = USAK_LISTE % (BUGUN.day, AYLAR[BUGUN.month], BUGUN.year)
        a = kk.aday_baglantilar(html, "https://www.usakolay.com/usakta-bugun-cenaze-ilanlari", s, oi.gunler())
        self.assertEqual(len(a), 1); self.assertEqual(list(a.values()), [(BUGUN.isoformat(), 0)])   # ana liste, eski ve spor bağlantısı elenir

    def test_sitemap_aday_baglantilari_gunsuz_tek_haber(self):
        s = kk.dogrula(satir(il="kutahya", ad="K", url="https://www.kutahyaninsesi.com", kalip="sitemap", rss_url=None, sitemap="https://www.kutahyaninsesi.com/s.xml"))[0]
        xml = (f"<urlset><url><loc>https://www.kutahyaninsesi.com/haber/9/ali-veli-vefat-etti</loc><lastmod>{G}T10:00:00+03:00</lastmod></url>"
               f"<url><loc>https://www.kutahyaninsesi.com/haber/8/trafik-kazasi</loc><lastmod>{G}T10:00:00+03:00</lastmod></url></urlset>")
        self.assertEqual(list(kk.aday_baglantilar(xml, "https://www.kutahyaninsesi.com/s.xml", s, oi.gunler())), ["https://www.kutahyaninsesi.com/haber/9/ali-veli-vefat-etti"])


# 15.10.2026 İç Anadolu defteri: gerçek sayfalardan küçültülmüş örnekler
def _iso(h): return h.replace(" T", "T")
KONYA_HAK = "Yakup Yılmaz, 21 Kasım 1937 doğumlu. İkindi namazı sonrası mezarlıkta kılınan cenaze namazının ardından Tekke Mezarlığı’nda toprağa verildi. Hasan Çorapcıoğlu, 20 Mart 1936 Konya doğumlu. Öğle namazı sonrası Hacı Veyis Camii’nde (Üçler Mezarlığı yanı) kılınan cenaze namazının ardından Üçler Mezarlığı’nda toprağa verildi."
KONYA_SES = "Yakup Yılmaz: İkindi namazını müteakiben Tekke Mezarlığı'nda dualarla defnedildi.Hasan Çorapcıoğlu: Öğle namazını müteakiben Üçler Mezarlığı'nda dualarla defnedildi."
HABER_DAIRESI = ('<h1>Konya\'da bugün vefat edenler</h1><figure><figcaption><div class="text-content"><p>Konya Mezarlık Bilgi sisteminde yer alan bilgiye göre Konya’da bugün 2 kişi hayatını kaybetti.</p></div></figcaption></figure>'
                 '<div class="text-content"><p><strong>Mithat Gedik</strong>. 1944 Karabayır doğumlu. İkindi namazı sonrası Musalla (Halkabiköşk) Camii’nde kılınan namazın ardından Musalla Mezarlığı’nda toprağa verildi.</p></div>'
                 '<div class="text-content"><p><strong>Mahiye Atçeken</strong>. 1954 Ölmez doğumlu. İkindi namazı sonrası Yediler Mezarlığı’nda kılınan namazın ardından toprağa verildi.</p></div>')
KAYSERI = "Kayseri Büyükşehir Belediyesi vefat edenleri yayınlıyor.FATİ FAKİRBaba / Ana Adı: SALMAN / MERYEMDoğum Yeri / Yılı: PINARBAŞI / 1946Cenaze Yeri: ORG.HULUSİ AKAR CAMİİVakit: ÖĞLEDefin Yeri: ANBAR MEZ. (Ada:4, Parsel:32)Taziye Adresi: KOCATEPE Mah. DEDEGÜL Sokak/Cadde No:26 MELİKGAZİ/KAYSERİ"
SIVAS346 = "Sivas’ta 15 Ekim 2026 tarihinde 2 kişi vefat etti.\nŞEFİK YANCI (71)\nYer – Vakit: Ay Yıldız Camii – Saat: 13:00\nDefin Yeri: Yukarı Tekke 91. Ada Sıra Mezarlığı\nTaziye Adresi: Mehmet Akif Ersoy Mah. 49-73 Sok. No: 4\nMUSTAFA YILMAZ (82)\nYer – Vakit: Gürün\nDefin Yeri: Gürün\nTaziye Adresi: Gürün"
GUNDEM_SIVAS = "Hubuyar Akgül\n68 yaşında hayatını kaybeden Hubuyar Akgül'ün defin tarihi 14 Ekim 2026 Çarşamba olarak açıklandı.\nCenaze yeri ve vakti Ay Yıldız Camii, saat 13.00 olarak belirtildi.\nDefin işlemi Yukarı Tekke Mezarlığı'nın 91. ada sıra mezarlığında gerçekleştirilecek.\nTaziye adresi Yüceyurt Mahallesi, 15-Karabağ Caddesi, No: 42 olarak kaydedildi."
IL_GAZETESI = "15 EKİM 2026 PERŞEMBE GÜNCEL VEFAT LİSTESİ\nİsmail Ay: Kırşehir Akçakentli (Yaş 34)\nİsmail Ay (34): Kırşehir Akçakent nüfusuna kayıtlı 34 yaşındaki merhumun cenazesi, öğle namazına müteakiben Sanayi Mahallesi Yeşiltepe Camii'nden kaldırılacaktır.\nAhmet Çapraz (61): Kayserili merhumun cenazesi, öğle namazına müteakiben Fabrikalar Mahallesi Atatepe Camii'nden kaldırılacaktır."
HUNAT = "Vefat eden vatandaşımızın bilgileri şu şekilde:Fati Fakir - Anbar Mez. - Org.Hulusi Akar Camii"
NNC = ("Ankara'da 13-14 Ekim 2026 Vefat Edenler: Kızılcahamam ve Bala\nÖnemli bilgi: Aşağıdaki tarihler cenaze tarihleridir.\nKızılcahamam'da 13 Ekim 2026 Vefat Edenler\n"
       "Şerife Algül – Eğerlidereköy Mahallesi\nKızılcahamam ilçesine bağlı Eğerlidereköy Mahallesi sakinlerinden Hasan Algül'ün eşi Şerife Algül'ün cenazesi öğle namazının ardından Eğerlidereköy Mahallesi Camii'nde kılınacaktır.\n"
       "Bala'da 14 Ekim 2026 Vefat Edenler\nRamazan Kılıç – Büyükbayat Mahallesi\nCenaze namazı öğle namazına müteakip kılınacak ve Büyükbayat Mahallesi Mezarlığı'na defnedilecek.")
TALAS = ('<table><thead><tr><th>Vefat Tarihi</th><th>Adı Soyadı</th><th>Baba / Anne Adı</th><th>Doğum Yeri / Yılı</th><th>Yer / Vakit</th><th>Mezarlık</th></tr></thead><tbody>'
         '<tr><th>%s</th><th>HAKKI ÇOLAK</th><th>FAZLI / HÜSNE</th><th>KAYALTI / 1964</th><th>DEDEOĞLU CAMİ</th><th>TALAS MEZARLIĞI </th></tr></tbody></table>')
MELIK = ('<table><thead><tr><th>Vefat Tarihi</th><th>Adı Soyadı</th><th>Anne Adı</th><th>Baba Adı</th><th>Mezarlık</th></tr></thead><tbody><tr>'
         '<td><span class="uk-hidden@m">Vefat Tarihi :</span> %s </td><td><span class="uk-hidden@m">Adı Soyadı :</span>Lutfu Abdüsselamoğlu </td><td><span class="uk-hidden@m">Anne Adı :</span>Asiye </td>'
         '<td><span class="uk-hidden@m">Baba Adı :</span>Halil </td><td><span class="uk-hidden@m">Mezarlık :</span>Mimarsinan Güneyler Dere Mezarlığı</td></tr></tbody></table>')


class IcAnadolu(unittest.TestCase):
    def sat(self, il, ad="Test", url="https://www.test.com", **a):
        return kk.dogrula(satir(il=il, ad=ad, url=url, rss_url=url + "/rss", **a))[0]

    def test_yer_tutucular(self):
        d = date(2026, 10, 5)
        self.assertEqual(kk.ay_ac("https://x.com/sitemap_posts-{YYYY}-{MM}.xml", d), "https://x.com/sitemap_posts-2026-10.xml")
        self.assertEqual(kk.ay_ac("https://x.com/s-{AY}.xml", d), "https://x.com/s-2026-10.xml")
        self.assertEqual(kk.ay_ac("https://x.com/s.xml", d), "https://x.com/s.xml")

    def test_konya_iki_bicim_ve_galeri(self):
        s = self.sat("konya")
        for g in (KONYA_HAK, KONYA_SES):
            k = kk.cumle_listesi_ayristir(g, CTX, "Konya", s, "https://x/1", G)
            self.assertEqual([(x["ad_soyad"], x["defin_yeri"]) for x in k], [("Yakup Yılmaz", "Tekke Mezarlığı"), ("Hasan Çorapcıoğlu", "Üçler Mezarlığı")])
        k = kk.cumle_listesi_ayristir(KONYA_HAK, CTX, "Konya", s, "https://x/1", "2026-10-15")
        self.assertEqual((k[0]["yas"], k[1]["namaz_yeri_vakti"]), (88, "Hacı Veyis Camii, öğle namazı"))
        g = kk.govde_metni(HABER_DAIRESI)
        k = kk.cumle_listesi_ayristir(g, CTX, "Konya", s, "https://x/2", G)
        self.assertEqual([x["ad_soyad"] for x in k], ["Mithat Gedik", "Mahiye Atçeken"])
        self.assertEqual(k[0]["namaz_yeri_vakti"], "Musalla (Halkabiköşk) Camii, ikindi namazı")

    def test_kayseri_yapisik_etiketler_anne_baba_alinmaz(self):
        s = self.sat("kayseri")
        g = kk.etiket_ayir(KAYSERI)
        k = kk.etiketli_blok_ayristir(g, CTX, "Kayseri", s, "https://x/3", G)
        self.assertEqual((len(k), k[0]["ad_soyad"], k[0]["defin_yeri"], k[0]["namaz_yeri_vakti"]), (1, "Fati Fakir", "Anbar Mez.", "Org.Hulusi Akar Camii, öğle namazı"))
        self.assertNotIn("SALMAN", json.dumps(k, ensure_ascii=False)); self.assertNotIn("KOCATEPE", json.dumps(k, ensure_ascii=False))
        self.assertIsNone(k[0]["anne_baba"])

    def test_sivas346_ve_gundem_sivas(self):
        s = self.sat("sivas")
        k = kk.etiketli_blok_ayristir(SIVAS346, CTX, "Sivas", s, "https://x/4", G)
        self.assertEqual([(x["ad_soyad"], x["yas"], x["namaz_yeri_vakti"]) for x in k], [("Şefik Yancı", 71, "Ay Yıldız Camii, 13:00"), ("Mustafa Yılmaz", 82, "Gürün")])
        k = kk.isimli_paragraf_ayristir(GUNDEM_SIVAS, CTX, "Sivas", s, "https://x/5", G)
        self.assertEqual((k[0]["ad_soyad"], k[0]["yas"], k[0]["namaz_yeri_vakti"], k[0]["defin_yeri"]), ("Hubuyar Akgül", 68, "Ay Yıldız Camii, 13:00", "Yukarı Tekke Mezarlığı"))

    def test_il_gazetesi_ve_hunat(self):
        s = self.sat("kirikkale")
        k = kk.cumle_listesi_ayristir(IL_GAZETESI, CTX, "Kırıkkale", s, "https://x/6", G)
        self.assertEqual([(x["ad_soyad"], x["yas"]) for x in k], [("İsmail Ay", 34), ("Ahmet Çapraz", 61)])
        k = kk.ayracli_satir_ayristir(HUNAT, CTX, "Kayseri", s, "https://x/7", G)
        self.assertEqual((k[0]["ad_soyad"], k[0]["defin_yeri"], k[0]["namaz_yeri_vakti"]), ("Fati Fakir", "Anbar Mez.", "Org.Hulusi Akar Camii"))

    def test_nnc_ilce_ilce(self):
        s = self.sat("ankara")
        k = kk.baslikli_ilan_ayristir(NNC, CTX, "Ankara", s, "https://x/8", "2026-10-14")
        self.assertEqual([(x["ad_soyad"], x["ilce"], x["mahalle"]) for x in k], [("Şerife Algül", "Kızılcahamam", "Eğerlidereköy Mahallesi"), ("Ramazan Kılıç", "Bala", "Büyükbayat Mahallesi")])
        self.assertNotIn("Hasan Algül", json.dumps(k, ensure_ascii=False))     # akraba adı alınmaz

    def test_belediye_tablolari_anne_baba_alinmaz(self):
        for ham, ad in ((TALAS, "Hakkı Çolak"), (MELIK, "Lutfu Abdüsselamoğlu")):
            s = self.sat("kayseri", ilce="Talas", kalip="liste", liste_url="https://www.test.com/v")
            k = kk.tablo_ayristir(ham % D, CTX, "Kayseri", s)
            self.assertEqual((len(k), k[0]["ad_soyad"], k[0]["ilce"]), (1, ad, "Talas"))
            txt = json.dumps(k, ensure_ascii=False)
            for yasak in ("FAZLI", "HÜSNE", "Asiye", "Halil", "KAYALTI"):
                self.assertNotIn(yasak, txt)

    def test_rss_derleme_basligi_ve_baska_il_elenir(self):
        s = self.sat("konya")
        rss = ("<rss><channel><item><title>Konya'da bugün vefat edenler | 15 Ekim 2026</title><link>https://www.test.com/konya/a-1</link><pubDate>%s</pubDate></item>"
               "<item><title>İstanbul'da bugün vefat edenler | 15 Ekim 2026</title><link>https://www.test.com/istanbul/b-2</link><pubDate>%s</pubDate></item>"
               "<item><title>Belediye yeni hizmet binasını açtı</title><link>https://www.test.com/c-3</link><pubDate>%s</pubDate></item></channel></rss>") % ((BUGUN.isoformat(),) * 3)
        a = kk.aday_baglantilar(rss, "https://www.test.com/rss", s, oi.gunler(), "Konya")
        self.assertEqual(list(a), ["https://www.test.com/konya/a-1"])

    def test_html_adaylarinda_baska_il_adresi_elenir(self):
        s = self.sat("ankara", kalip="liste", liste_url="https://www.test.com/vefatlar")
        html = ('<a href="/ankara-ve-ilceleri-13-ekim-14-ekim-2026-bugun-vefat-olum-defin">a</a><a href="/afyonkarahisar-ve-ilcelerinde-kimler-vefat-etti-13-14-ekim-2026-cenaze-listesi">b</a>'
                '<a href="/vefatlar?sayfa=2">c</a>')
        a = kk.aday_baglantilar(html, "https://www.test.com/vefatlar", s, ["2026-10-14", "2026-10-13"], "Ankara")
        self.assertEqual(len(a), 1)

    def test_308_yonlendirmesi(self):
        import urllib.request
        h = kk.ob._Yonlendir308()
        r = urllib.request.Request("https://a.com/rss", headers={"User-Agent": "x"})
        yeni = h.redirect_request(r, None, 308, "Permanent Redirect", {}, "https://b.com/rss")
        self.assertEqual(yeni.full_url, "https://b.com/rss")
        self.assertTrue(hasattr(h, "http_error_308"))


if __name__ == "__main__":
    unittest.main()
