import json, os, tempfile, unittest, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, yerlestirme_denetimi as yd


def kay(i, il, ilce, defin, ad="Test Kisi", kaynak=None, **ek):
    k = {"id": i, "il": il, "ilce": ilce, "ad_soyad": ad, "yas": 70, "vefat_tarihi": "2026-10-13", "defin_yeri": defin}
    if kaynak: k["ilce_kaynagi"] = kaynak
    k.update(ek); return k


def yaz(kok, slug, il, ilceler=None, il_disi=None, belirsiz=None):
    os.makedirs(os.path.join(kok, slug), exist_ok=True)
    with open(os.path.join(kok, slug, "son7gun.json"), "w", encoding="utf-8") as f:
        json.dump({"il": il, "ilceler": ilceler or {}, "il_disi": il_disi or [], "ilce_belirsiz": belirsiz or []}, f, ensure_ascii=False)


class Tablo(unittest.TestCase):
    def setUp(self):
        ortak._mez_onbellek.clear()
        ortak._mez_onbellek.update({"gaziantep": {"yesilkent": "Oğuzeli", "asri": {"belirsiz": ["Şahinbey", "Şehitkamil"]}, "x": "Yanlisilce"},
                                    "_mahalle": {"gaziantep": {"ornek mah": "Şehitkamil"}}, "_cami": {"gaziantep": {"merkez camii": "Şahinbey"}}})
        ortak._OGRENILEN.clear()

    def test_tek_eslesme(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Yeşilkent Mezarlığı"}, "Gaziantep")
        self.assertEqual((k["ilce"], k["ilce_belirsiz"], k["ilce_kaynagi"]), ("Oğuzeli", False, "mezarlik_tablosu"))

    def test_baska_il_aranmaz(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Yeşilkent Mezarlığı"}, "Konya")
        self.assertIsNone(k["ilce"]); self.assertTrue(k["ilce_belirsiz"])

    def test_gecersiz_ilce_yok_sayilir(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "X Mezarlığı"}, "Gaziantep")
        self.assertIsNone(k["ilce"])

    def test_belirsiz_ipuclari(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Asri Mezarlık", "mahalle": "Örnek Mah"}, "Gaziantep")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Şehitkamil", "mezarlik_tablosu+mahalle"))
        k = ortak.ilce_isle({"id": "b", "ilce": None, "defin_yeri": "Asri Mezarlık", "namaz_yeri_vakti": "Merkez Camii"}, "Gaziantep")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Şahinbey", "mezarlik_tablosu+cami"))
        k = ortak.ilce_isle({"id": "c", "ilce": None, "defin_yeri": "Asri Mezarlık"}, "Gaziantep")
        self.assertIsNone(k["ilce"])        # hicbir ipucu yok -> tahmin yok
        ortak._OGRENILEN["gaziantep"] = {"asri": {"Şahinbey": 9, "Şehitkamil": 1}}
        k = ortak.ilce_isle({"id": "d", "ilce": None, "defin_yeri": "Asri Mezarlık"}, "Gaziantep")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Şahinbey", "mezarlik_tablosu+ogrenilen"))
        ortak._OGRENILEN["gaziantep"] = {"asri": {"Şahinbey": 5, "Şehitkamil": 4}}
        k = ortak.ilce_isle({"id": "e", "ilce": None, "defin_yeri": "Asri Mezarlık"}, "Gaziantep")
        self.assertIsNone(k["ilce"])        # %80 altinda

    def test_islenmis_kayit_yeniden_denenir_ve_idempotent(self):
        k = {"id": "a", "ilce": None, "ilce_belirsiz": True, "il_disi_defin": None, "defin_yeri": "Yeşilkent Mezarlığı"}
        ortak.ilce_isle(k, "Gaziantep"); ortak.ilce_isle(k, "Gaziantep")
        self.assertEqual(k["ilce"], "Oğuzeli")

    def test_mevcut_ilce_bozulmaz(self):
        k = ortak.ilce_isle({"id": "a", "ilce": "Nizip", "defin_yeri": "Yeşilkent Mezarlığı"}, "Gaziantep")
        self.assertEqual(k["ilce"], "Nizip"); self.assertNotIn("ilce_kaynagi", k)

    def test_tablo_yoksa_sessiz(self):
        ortak._mez_onbellek.clear(); ortak._mez_onbellek["_yok"] = True
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Yeşilkent Mezarlığı"}, "Gaziantep")
        self.assertIsNone(k["ilce"])

    def test_pafta_kesme(self):
        self.assertEqual(ortak.mezarlik_norm("Yeşilkent Mezarlığı Pafta: 52 Parsel: 13"), "yesilkent")
        self.assertEqual(ortak.mezarlik_norm("Yeşilkent Mezarlığı / S-1 Sıralı"), "yesilkent")


class IlDisi(unittest.TestCase):
    def test_baska_il_adi(self):
        for ilce_ham in (None, "Merkez"):
            k = ortak.ilce_isle({"id": "a", "ilce": ilce_ham, "defin_yeri": "Kilis"}, "Gaziantep")
            self.assertEqual(k["il_disi_defin"]["il"], "Kilis"); self.assertIsNone(k["ilce"]); self.assertFalse(k["ilce_belirsiz"])
        k = ortak.ilce_isle({"id": "b", "ilce": "Merkez", "defin_yeri": "Diyarbakır"}, "Batman")
        self.assertEqual(k["il_disi_defin"]["il"], "Diyarbakır"); self.assertIsNone(k["ilce"])

    def test_il_ilce_bicimi(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Şanlıurfa / Birecik"}, "Osmaniye")
        self.assertEqual(k["il_disi_defin"], {"il": "Şanlıurfa", "ilce": "Birecik"})

    def test_kendi_il_ve_mezarlik_etkilenmez(self):
        k = ortak.ilce_isle({"id": "a", "ilce": None, "defin_yeri": "Gaziantep"}, "Gaziantep")
        self.assertIsNone(k["il_disi_defin"]); self.assertTrue(k["ilce_belirsiz"])
        k = ortak.ilce_isle({"id": "b", "ilce": "Nizip", "defin_yeri": "Asri Mezarlık"}, "Gaziantep")
        self.assertEqual(k["ilce"], "Nizip")

    def test_islenmis_kayit(self):
        k = {"id": "a", "ilce": None, "ilce_belirsiz": True, "il_disi_defin": None, "defin_yeri": "Kilis"}
        ortak.ilce_isle(k, "Gaziantep"); self.assertEqual(k["il_disi_defin"]["il"], "Kilis")


class Denetim(unittest.TestCase):
    def setUp(self):
        TestAyar = Tablo; TestAyar.setUp(self)
        self.t = tempfile.mkdtemp()

    def test_temiz(self):
        yaz(self.t, "gaziantep", "Gaziantep", {"Oğuzeli": [kay("1", "Gaziantep", "Oğuzeli", "Yeşilkent Mezarlığı", ad="A", kaynak="mezarlik_tablosu")]})
        self.assertEqual(yd.denetle(self.t)["ihlal_sayisi"], 0)

    def test_yakalar(self):
        yaz(self.t, "gaziantep", "Gaziantep", {
            "Oğuzeli": [kay("1", "Gaziantep", "Oğuzeli", "Yeşilkent Mezarlığı", ad="Bir", kaynak="mezarlik_tablosu")],
            "Şahinbey": [kay("2", "Gaziantep", "Şahinbey", "Yeşilkent Mezarlığı", ad="Iki", kaynak="mezarlik_tablosu"),   # 3: tablo Oğuzeli diyor
                         kay("3", "Konya", "Şahinbey", "Asri", ad="Uc"),                                                   # 1: il farkli
                         kay("4", "Gaziantep", "Şahinbey", "Kilis", ad="Dort")],                                           # 4: baska il adi
            "Atlantis": [kay("5", "Gaziantep", "Atlantis", "x", ad="Bes")]})                                               # 2: listede yok
        yaz(self.t, "konya", "Konya", {"Meram": [kay("6", "Konya", "Meram", "m", ad="Bir")]})                              # 5: ayni kisi iki ilde (ad/yas/vefat ayni)
        kurallar = {x["kural"] for x in yd.denetle(self.t)["ihlaller"]}
        r = yd.denetle(self.t)
        self.assertEqual(kurallar, {1, 2, 3, 4})
        self.assertIn(5, {x["kural"] for x in r["uyarilar"]})

    def test_uyari_ve_cikis_kodu(self):
        yaz(self.t, "gaziantep", "Gaziantep", {ortak and yd.ETIKET: [kay("1", "Gaziantep", yd.ETIKET, "-", ad="A")]})
        r = yd.denetle(self.t)
        self.assertEqual((r["ihlal_sayisi"], len(r["uyarilar"])), (0, 1))
        self.assertEqual(yd.main([self.t]), 0)
        self.assertTrue(os.path.isfile(os.path.join(self.t, "yerlestirme-raporu.json")))
        yaz(self.t, "gaziantep", "Gaziantep", {"Atlantis": [kay("1", "Gaziantep", "Atlantis", "-")]})
        self.assertEqual(yd.main([self.t]), 1)


if __name__ == "__main__":
    unittest.main()
