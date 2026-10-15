import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, edevlet

IZMIR = '''<dl class="compact"><dt>Adı Soyadı</dt><dd>HASAN YILDIRIM</dd><dt>Baba Adı</dt><dd>MEHMET</dd><dt>Ölüm Sebebi</dt><dd>-</dd>
<dt>Namaz ve Defin Yeri Bilgisi</dt><dd> Cami İl/İlçe :İZMİR / KARABAĞLAR Cami Adı: X CAMİ Vakit: ÖĞLE</dd>
<dt>Mezarlık Bilgisi</dt><dd> Mezarlık İl/İlçe :İZMİR / BUCA Mezarlık Adı: BUCA ZAFER MEZARLIĞI Ada:  Mezar No: </dd></dl>'''
IST = '<dl><dt>Adı Soyadı</dt><dd>HASAN AYTEKİN</dd><dt>Mezarlık Bilgisi</dt><dd>KOCASİNAN</dd></dl>'
IST_TIRE = '<dl><dt>Adı Soyadı</dt><dd>ALİ VELİ</dd><dt>Mezarlık Bilgisi</dt><dd>-</dd></dl>'


def kay(ad="Hasan Yıldırım"):
    return {"id": "a", "ad_soyad": ad, "ilce": None, "ilce_belirsiz": True, "il_disi_defin": None, "ham": {}}


class Detay(unittest.TestCase):
    def test_izmir_mezarlik_ilcesi_resmi_alan(self):
        d = edevlet.detay_ayikla(IZMIR)
        self.assertEqual((d["mezarlik_il"], d["mezarlik_ilce"], d["mezarlik_ad"]), ("İZMİR", "BUCA", "BUCA ZAFER MEZARLIĞI"))
        self.assertEqual(set(d), {"ad", "mezarlik_il", "mezarlik_ilce", "mezarlik_ad"})   # cami/baba adı/ölüm sebebi dönmez
        r = kay()
        self.assertTrue(edevlet.detay_uygula(r, d, "İzmir", "2026-10-15"))
        self.assertEqual((r["ilce"], r["ilce_kaynagi"], r["ilce_belirsiz"]), ("Buca", "edevlet_detay", False))   # cami ilçesi (Karabağlar) kullanılmaz

    def test_ad_uyusmazligi_yazmaz(self):
        r = kay("Baska Kisi")
        self.assertFalse(edevlet.detay_uygula(r, edevlet.detay_ayikla(IZMIR), "İzmir", "2026-10-15"))
        self.assertIsNone(r["ilce"]); self.assertNotIn("defin_yeri", r)

    def test_baska_il_mezarligi_il_disi(self):
        d = edevlet.detay_ayikla(IZMIR.replace("İZMİR / BUCA", "MANİSA / SARUHANLI"))
        r = kay()
        edevlet.detay_uygula(r, d, "İzmir", "2026-10-15")
        self.assertEqual(r["il_disi_defin"]["il"], "Manisa"); self.assertIsNone(r["ilce"])

    def test_istanbul_ad_ve_tire(self):
        self.assertEqual(edevlet.detay_ayikla(IST)["mezarlik_ad"], "KOCASİNAN")
        self.assertIsNone(edevlet.detay_ayikla(IST_TIRE)["mezarlik_ad"])

    def test_detay_gerekli_bir_kez(self):
        r = kay(); self.assertTrue(edevlet.detay_gerekli(r, "2026-10-15"))
        edevlet.detay_uygula(r, edevlet.detay_ayikla(IST_TIRE.replace("ALİ VELİ", "Hasan Yıldırım")), "İstanbul", "2026-10-15")
        self.assertFalse(edevlet.detay_gerekli(r, "2026-10-15"))      # aynı gün tekrar okunmaz
        self.assertTrue(edevlet.detay_gerekli(r, "2026-10-16"))        # ertesi gün 1 deneme daha
        r["ham"]["detay_deneme"] = 2
        self.assertFalse(edevlet.detay_gerekli(r, "2026-10-17"))

    def test_liste_satirina_detay_indeksi(self):
        g = '<table><tr><th>Adı Soyadı</th><th>Yaşı</th><th>İşlem</th></tr><tr><td>A B</td><td>70</td><td><a href="/x?islem=detay&index=7">Detay</a></td></tr></table>'
        self.assertEqual(edevlet.satirlar_idx(g), [("A B", "70", 7)]); self.assertEqual(edevlet.satirlar(g), [("A B", "70")])


class ResmiSozluk(unittest.TestCase):
    def setUp(self):
        ortak._resmi_onbellek.clear()
        ortak._resmi_onbellek["t"] = {"istanbul": {"kocasinan": {"Bahçelievler"}, "ikili": {"Pendik", "Tuzla"}, "yok ilce": {"Atlantis"}}}

    def test_birebir_ad_baglanir(self):
        k = ortak.ilce_isle({"id": "1", "ilce": None, "defin_yeri": "Kocasinan Mezarlığı"}, "İstanbul")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Bahçelievler", "mezarlik_resmi"))

    def test_benzer_ad_baglanmaz(self):
        k = ortak.ilce_isle({"id": "2", "ilce": None, "defin_yeri": "Kocasinan Eski Mezarlığı"}, "İstanbul")
        self.assertIsNone(k["ilce"])

    def test_iki_ilcede_ayni_ad_ve_gecersiz_ilce_baglanmaz(self):
        for ad in ("İkili Mezarlığı", "Yok İlçe Mezarlığı"):
            self.assertIsNone(ortak.ilce_isle({"id": "3", "ilce": None, "defin_yeri": ad}, "İstanbul")["ilce"])

    def test_baska_ilde_aranmaz_ve_kapali_katman(self):
        self.assertIsNone(ortak.ilce_isle({"id": "4", "ilce": None, "defin_yeri": "Kocasinan Mezarlığı"}, "Konya")["ilce"])
        ortak.RESMI_ETKIN = False
        try:
            self.assertIsNone(ortak.ilce_isle({"id": "5", "ilce": None, "defin_yeri": "Kocasinan Mezarlığı"}, "İstanbul")["ilce"])
        finally:
            ortak.RESMI_ETKIN = True

    def test_gercek_dosya_yuklenir(self):
        ortak._resmi_onbellek.clear()
        self.assertGreater(len(ortak.resmi_tablo().get("istanbul", {})), 400)


if __name__ == "__main__":
    unittest.main()
