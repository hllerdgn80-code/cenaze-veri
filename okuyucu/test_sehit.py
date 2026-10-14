"""Şehit ilanı veri hattı birim testleri (URUN-TASLAGI §27; 14.10.2026). Çalıştırma: python3 okuyucu/test_sehit.py"""
import json, os, sys, tempfile, unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_basin as ob, ortak_haber as oh, kapi, yayin_suz, sehit_ulusal, ulusal_birlestir

BUGUN = date.today().isoformat()
RFC = date.today().strftime("%a, %d %b %Y 08:00:00 +0300")


def rss(ogeler):
    x = ['<?xml version="1.0"?><rss><channel>']
    for b, u, oz in ogeler:
        x.append(f"<item><title>{b}</title><link>{u}</link><description>{oz}</description><pubDate>{RFC}</pubDate></item>")
    return "".join(x) + "</channel></rss>"


def sayfa(govde):
    return '<html><script type="application/ld+json">' + json.dumps({"@type": "NewsArticle", "articleBody": govde}, ensure_ascii=False) + "</script></html>"


class Harness(unittest.TestCase):
    def kos(self, il, ogeler, sayfalar):
        self.tmp = tempfile.mkdtemp()
        klasor = os.path.join(self.tmp, il.lower())
        os.makedirs(klasor)
        ctx = {"gunler": [(date.today() - timedelta(days=i)).isoformat() for i in range(7)], "alindi": "2026-10-14T10:00:00+03:00", "klasor": klasor, "il": il}
        eski = (oh.onbellekli_dizin, ob.al)
        oh.onbellekli_dizin = lambda c, u: rss(ogeler)
        ob.al = lambda c, u: sayfalar[u]
        try:
            sonuc = oh.haber_kaynagi(ctx, il, "test", "Test Gazetesi", "http://x/rss", kesin_yerel=False)
        finally:
            oh.onbellekli_dizin, ob.al = eski
        ik = os.path.join(klasor, "_sehit_ikinci.json")
        ikinci = json.load(open(ik, encoding="utf-8"))["kayitlar"] if os.path.exists(ik) else []
        return sonuc, ikinci


class Metin(unittest.TestCase):
    def test_isaret_kosullari(self):
        self.assertTrue(ob.sehit_metni_mi("Jandarma Uzman Çavuş Mehmet Kaya şehit oldu", ""))
        self.assertTrue(ob.sehit_metni_mi("Şehit polis memuru Ahmet Demir için cenaze töreni düzenlendi", ""))
        self.assertFalse(ob.sehit_metni_mi("Şehit Mahallesi'nde Ali Yılmaz vefat etti", "Şehit Mahallesi'nde oturan Ali Yılmaz vefat etti, cenazesi yarın."))
        self.assertFalse(ob.sehit_metni_mi("Şehit yakını Ayşe Demir vefat etti", "Cenazesi yarın kılınacak, şehit yakını idi."))
        self.assertFalse(ob.sehit_metni_mi("Şehit Ali Veli Caddesi'nde kaza", "Şehit Ali Veli Caddesi'nde asker aracı cenaze"))
        self.assertFalse(ob.sehit_metni_mi("Çanakkale şehitleri anıldı", "Şehit askerler için tören düzenlendi."))
        self.assertFalse(ob.sehit_metni_mi("Gazze'de şehit olan çocuk toprağa verildi", "Şehit çocuk cenaze"))      # güvenlik görevlisi değil
        self.assertFalse(ob.sehit_metni_mi("Şehit Ali Veli kabri başında anıldı", "Veli 1993 yılında şehit düşmüştü. Anma töreni yapıldı."))

    def test_gercek_veri_yanlis_pozitifleri(self):
        """14.10.2026 canlı valilik denemesi: Tekirdağ (şehit BABASI cenazesi) ve Niğde (şehit adına açılış töreni) şehit sayılmamalı."""
        self.assertFalse(ob.sehit_metni_mi("Şehit Babası Son Yolculuğuna Uğurlandı",
            "10.10.2026 tarihinde vefat eden Şehit Er Servet Güzelsoy’un babası Fikret Güzelsoy için Süleymanpaşa ilçemiz Süleyman Mehmet Efendi Cami’nde cenaze töreni düzenlendi. "
            "Cenaze törenine katılan Valimiz merhum Şehit Babası Fikret Güzelsoy’a Allah’tan rahmet dileyerek şehit ailesine başsağlığı diledi."))
        self.assertFalse(ob.sehit_metni_mi("Valimiz Sayın Nedim AKMEŞE Şehit Hava Uçak Bakım Astsubay Başçavuş Burak Özkan Özel Eğitim Sınıfı Açılış Töreni’ne Katıldı",
            "Valimiz Mevlana Ortaokulu'nda hayata geçirilen \"Şehit Hava Uçak Bakım Astsubay Başçavuş Burak Özkan Özel Eğitim Sınıfı\" Açılış Töreni’ne katıldı. Şehit ailemiz de katıldı."))
        self.assertFalse(ob.sehit_metni_mi("Vali Ünlüer, Şehadet Mertebesine Ulaşan Öğrencilerimizin Ailelerini Misafir Etti", "Vali şehit ailelerini ziyaret etti."))
        self.assertFalse(ob.sehit_metni_mi("Vali Çiçek’ten Şehitlerimizin Ailelerine Ziyaret", "Şehit ailelerine ziyaret."))
        self.assertNotEqual(ob.sehit_ad_rutbe("Şehit Hava Uçak Bakım Astsubay Başçavuş Ali Veli'nin cenazesi toprağa verildi", "")[0], "Hava Uçak Bakım")

    def test_vefat_haberi_sehit_yakini_normal(self):
        self.assertTrue(oh.vefat_haberi_mi("Şehit yakını Ayşe Demir vefat etti"))
        self.assertTrue(oh.vefat_haberi_mi("Şehit Mahallesi'nden Ali Yılmaz vefat etti"))
        self.assertFalse(oh.vefat_haberi_mi("Şehit Uzman Çavuş Ali Veli vefat etti"))


class Haber(Harness):
    def test_trabzonlu_sehit_ankarada_iki_il(self):
        b = "Trabzonlu şehit Piyade Uzman Onbaşı Ali Veli Ankara'da toprağa verildi"
        g = ("Trabzon'un Of ilçesine bağlı Çaykara köyü nüfusuna kayıtlı Piyade Uzman Onbaşı Ali Veli'nin cenazesi, Ankara Garnizon Komutanlığı önünde "
             "düzenlenen törenin ardından Ankara Cebeci Askerî Şehitliği'nde toprağa verildi. Cenaze namazı Kocatepe Camii'nde öğle namazının ardından kılındı. "
             "Operasyonda yaşanan çatışmada kalp krizi ve silahla yaralanma gibi ayrıntılar haberde yer aldı.")
        u = "http://x/haber/1"
        sonuc, ikinci = self.kos("Trabzon", [(b, u, "")], {u: sayfa(g)})
        self.assertEqual(len(sonuc), 1)
        k = sonuc[0]
        self.assertEqual((k["il"], k["ilce"], k["sehit"], k["rutbe"], k["ad_soyad"]), ("Trabzon", "Of", True, "Piyade Uzman Onbaşı", "Ali Veli"))
        self.assertEqual(len(ikinci), 1)
        self.assertEqual((ikinci[0]["il"], ikinci[0]["sehit"], ikinci[0]["ad_soyad"]), ("Ankara", True, "Ali Veli"))
        self.assertNotEqual(k["id"], ikinci[0]["id"])
        # yayına alan sızması yok
        for r in (k, ikinci[0]):
            s = yayin_suz.kayit_suz(r)
            self.assertTrue(set(s) <= set(yayin_suz.UYGULAMA_ALANLARI))
            self.assertTrue(s["sehit"])

    def test_polis_valilik_toreni(self):
        b = "Polis Memuru Ahmet Demir şehit oldu"
        g = ("Ordu'nun Ünye ilçesinde görev yapan Polis Memuru Ahmet Demir (28) şehit oldu. Cenaze töreni yarın Ordu Valiliği önünde yapılacak, "
             "ardından cenaze namazı Ulubey Camii'nde öğle namazından sonra kılınacak ve Ünye Şehitliği'nde defnedilecek.")
        u = "http://x/haber/2"
        sonuc, ikinci = self.kos("Ordu", [(b, u, "")], {u: sayfa(g)})
        self.assertEqual(ikinci, [])
        # yarın tören: liste_tarihi yarın (pencere dışı olabilir) ama kayıt üretildi
        self.assertEqual(len(sonuc), 1)
        k = sonuc[0]
        self.assertEqual((k["il"], k["ilce"], k["rutbe"], k["toren"], k["yas"]), ("Ordu", "Ünye", "Polis Memuru", "Ordu Valiliği önü", 28))
        self.assertLessEqual(len(k["toren"]), 60)

    def test_adi_sehit_olan_mahalle_isaretsiz(self):
        b = "Şehit Mahallesi'nden Ali Yılmaz vefat etti"
        g = "Şehit Mahallesi'nden Ali Yılmaz (70) vefat etti. Cenazesi bugün ikindi namazında Merkez Camii'nde kılınacak ve Aydın Mezarlığı'na defnedilecektir."
        u = "http://x/haber/3"
        sonuc, ikinci = self.kos("Samsun", [(b, u, g)], {u: sayfa(g)})
        self.assertTrue(all(not k.get("sehit") for k in sonuc))
        self.assertEqual(ikinci, [])
        self.assertEqual(len(sonuc), 1)

    def test_sehit_yakini_isaretsiz(self):
        b = "Şehit yakını Ayşe Demir vefat etti"
        g = "Şehit yakını Ayşe Demir (80) vefat etti. Cenazesi bugün öğle namazında Çarşı Camii'nde kılınacak ve Kalkınma Mezarlığı'na defnedilecektir."
        u = "http://x/haber/4"
        sonuc, _ = self.kos("Samsun", [(b, u, g)], {u: sayfa(g)})
        self.assertTrue(all(not k.get("sehit") for k in sonuc))


class Kapi(unittest.TestCase):
    def kayit(self, **ek):
        k = {a: None for a in ortak.ALANLAR}
        k.update(id="a1", il="Trabzon", ilce="Of", ad_soyad="Ali Veli", liste_tarihi=BUGUN, namaz_tarihi=BUGUN, kaynak_ad="Test Gazetesi",
               kaynak_url="http://x/haber/1", alindi="x", ham={}, il_disi_defin=None, ilce_belirsiz=False, kaynak_turu="yerel_haber")
        k.update(ek)
        return k

    def test_k5_k8_sehit_alanlari_elenmez(self):
        kapi.YEREL_BASIN.setdefault("Test Gazetesi", "x")
        k = self.kayit(sehit=True, rutbe="Jandarma Uzman Çavuş", toren="Trabzon Valiliği önü")
        self.assertEqual(kapi.denetle(k, date.today(), {}), [])
        # sehit metni olan ama NEDEN sözcüğü içermeyen kayıt: "şehit" sözcüğü K5'e takılmaz
        k2 = self.kayit(sehit=True, rutbe="Şehit Polis Memuru")
        self.assertEqual([x for x in kapi.denetle(k2, date.today(), {}) if x.startswith("K5")], [])

    def test_uzunluk_sinirlari(self):
        kapi.YEREL_BASIN.setdefault("Test Gazetesi", "x")
        self.assertTrue(any("rutbe" in x for x in kapi.denetle(self.kayit(sehit=True, rutbe="x" * 41), date.today(), {})))
        self.assertTrue(any("toren" in x for x in kapi.denetle(self.kayit(sehit=True, toren="y" * 61), date.today(), {})))


class Resmi(unittest.TestCase):
    LISTE = ('<a class="card news-card-horizontal" href="//www.trabzon.gov.tr/sehit-uzman-cavus-ali-veli-icin-tören"><div class="card-body">'
             '<h6 class="card-subtitle"><span class="cardDate">14.10.2026</span></h6><h5 class="card-title">Şehit Uzman Çavuş Ali Veli İçin Tören Düzenlendi</h5></div></a>')
    DUYURU = ('<html><h2 class="page-title"><span>Şehit Uzman Çavuş Ali Veli İçin Tören Düzenlendi</span></h2><div class="icerik" id="x"><div>'
              'Trabzon Valiliği önünde düzenlenen törenin ardından Jandarma Uzman Çavuş Ali Veli Of ilçesinde toprağa verildi.</div></div></html>')

    def test_kart_ve_duyuru(self):
        k = sehit_ulusal.kartlar(self.LISTE, "https://www.trabzon.gov.tr")
        self.assertEqual(k[0][0], "2026-10-14")
        self.assertTrue(ob.sehit_baslik_adayi(k[0][1]))
        b, g, _ = sehit_ulusal.duyuru_metni(self.DUYURU)
        f = oh.sehit_olgulari("Trabzon", b, g, "2026-10-14")
        self.assertEqual((f["ad"], f["rutbe"], f["d_il"]), ("Ali Veli", "Uzman Çavuş", "Trabzon"))
        kayit = oh.sehit_kayitlari("Trabzon", "sehit", "Trabzon Valiliği duyurusu", "https://www.trabzon.gov.tr/x", f, "2026-10-14", "n", resmi=True)
        self.assertEqual(len(kayit), 1)
        self.assertNotIn("kaynak_turu", kayit[0][1])

    MSB = ('<section class="haber"><h1 class="haber-title"> Bir Kahraman Silah Arkadaşımız Şehit Oldu </h1><small class="date"><strong>Tarih: </strong>14.10.2026</small>'
           '<div class="haber-content"><p><span>Pençe-Kilit operasyon bölgesinde görevli P.Uzm.Çvş. Mustafa Aslan, 14 Ekim 2026 tarihinde meydana gelen silah kazasında yaralanmış, '
           'kurtarılamayarak şehit olmuştur.<br /> Aziz şehidimize Allah’tan rahmet dileriz.</span></p></div><small class="views">Okunma Sayısı</small></section>')

    def test_msb(self):
        liste = '<a href="/SlaytHaber/02a38ce6b01c4951ae75354ca74dc2e6"><img/> Bir Kahraman Silah Arkadaşımız Şehit Oldu </a><a href="/SlaytHaber/52aa2ba38b174941be4e5047585419bb">Bakan ziyaret etti</a>'
        k = sehit_ulusal.kartlar(liste, "https://www.msb.gov.tr")
        self.assertEqual(len(k), 2)
        b, g, t = sehit_ulusal.duyuru_metni(self.MSB)
        self.assertEqual(t, "2026-10-14")
        f = oh.sehit_olgulari(None, b, g, t)
        self.assertEqual((f["ad"], f["rutbe"]), ("Mustafa Aslan", "Piyade Uzman Çavuş"))
        self.assertEqual(oh.sehit_kayitlari(None, "sehit", "MSB duyurusu", "u", f, t, "n", resmi=True), [])      # yer yok: kayıt açılmaz
        self.assertNotIn("silah", json.dumps(f, ensure_ascii=False).lower())                                    # ölüm nedeni olguya girmez

    def test_bot_sayfasi(self):
        self.assertTrue(sehit_ulusal.bot_sayfasi_mi('<html><meta http-equiv="refresh" content="1"><div id="challenge" ></div></html>'))
        self.assertFalse(sehit_ulusal.bot_sayfasi_mi(self.LISTE))


class Hat(Harness):
    """Uçtan uca: okuyucu -> son7gun -> sehit_ulusal.dagit -> ulusal_birlestir -> kapi -> yayin_suz (iki ilde de şehit kartı, alan sızıntısı yok)."""
    def test_uctan_uca_iki_il(self):
        b = "Trabzonlu şehit Piyade Uzman Onbaşı Ali Veli Ankara'da toprağa verildi"
        g = ("Trabzon'un Of ilçesine bağlı Çaykara köyü nüfusuna kayıtlı Piyade Uzman Onbaşı Ali Veli'nin cenazesi, Ankara Garnizon Komutanlığı önünde "
             "düzenlenen törenin ardından Ankara Cebeci Askerî Şehitliği'nde toprağa verildi. Cenaze namazı Kocatepe Camii'nde öğle namazının ardından kılındı.")
        u = "http://x/haber/1"
        sonuc, ikinci = self.kos("Trabzon", [(b, u, "")], {u: sayfa(g)})
        kok = os.path.join(self.tmp, "veri")
        os.makedirs(os.path.join(kok, "trabzon")); os.makedirs(os.path.join(kok, "ankara"))
        os.replace(os.path.join(self.tmp, "trabzon", "_sehit_ikinci.json"), os.path.join(kok, "trabzon", "_sehit_ikinci.json"))
        gunler = [BUGUN]
        for il, slug in (("Trabzon", "trabzon"), ("Ankara", "ankara")):
            ortak.son7gun_yaz(os.path.join(kok, slug), il, gunler, {BUGUN: [dict(k) for k in sonuc] if slug == "trabzon" else []})
        sehit_ulusal.VERI = kok
        sehit_ulusal.dagit()
        ulusal_birlestir.sys.argv = ["x", kok]
        ulusal_birlestir.main()
        kapi.VERI = kok
        kapi.YEREL_BASIN["Test Gazetesi"] = "x"
        for slug in ("trabzon", "ankara"):
            r = kapi.il_denetle(slug, date.today())
            self.assertEqual(r["elenen"], 0, r)
        site = os.path.join(self.tmp, "site")
        import shutil
        shutil.copytree(kok, site)
        yayin_suz.suz(site)
        self.assertEqual(yayin_suz.denetle(site), [])
        for slug, ilce in (("trabzon", "Of"), ("ankara", None)):
            d = json.load(open(os.path.join(site, slug, "son7gun.json"), encoding="utf-8"))
            tum = [k for l in d["ilceler"].values() for k in l] + d["il_disi"] + d["ilce_belirsiz"]
            self.assertEqual(len(tum), 1, (slug, d))
            k = tum[0]
            self.assertTrue(k["sehit"])
            self.assertEqual(k["rutbe"], "Piyade Uzman Onbaşı")
            self.assertTrue(set(k) <= set(yayin_suz.UYGULAMA_ALANLARI), set(k))
        d = json.load(open(os.path.join(site, "trabzon", "son7gun.json"), encoding="utf-8"))
        self.assertIn("Of", d["ilceler"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
