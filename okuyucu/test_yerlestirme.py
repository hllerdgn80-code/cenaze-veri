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


class H61Katmanlar(unittest.TestCase):
    """H61 (15.10.2026): ilce adi metinde / mahalle-koy tablosu / ad sifati. Yalniz KESIN eslesme, yalniz kendi il."""
    def setUp(self):
        ortak._mez_onbellek.clear(); ortak._mez_onbellek["_yok"] = True
        ortak._mah_onbellek.clear()
        ortak._mah_onbellek.update({"bursa": {"kogukcinar": "Osmangazi", "kuplupinar": "Osmangazi"}, "isparta": {"batikent": "Merkez"},
                                    "sivas": {"yukari tekke": "Merkez"}})
        ortak._OGRENILEN.clear()

    def isle(self, il, **alan):
        k = {"id": "t", "ilce": None, "ilce_belirsiz": True, "il_disi_defin": None}
        k.update(alan)
        return ortak.ilce_isle(k, il)

    def test_ilce_adi_metinde(self):
        k = self.isle("Kocaeli", defin_yeri="GEBZE MEZARLIĞI", namaz_yeri_vakti="Vakitsiz – MERKEZ MEZ")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"], k["ilce_belirsiz"]), ("Gebze", "ilce_adi_metinde", False))
        k = self.isle("Kocaeli", defin_yeri="KÖSEKÖY İSTASYON MEZARLIĞI", namaz_yeri_vakti="Öğlen – KÖSEKÖY İSTASYON PARK CAMİ")
        self.assertIsNone(k["ilce"])                      # mahalle adi, ilce adi degil
        k = self.isle("Bolu", defin_yeri="Köy Mezarlığı", namaz_yeri_vakti="Kıbrıscık Kızılcaören Köyünde kılınacak ikindi")
        self.assertEqual(k["ilce"], "Kıbrıscık")

    def test_yon_adi_mezarlik_baglanmaz(self):
        # 15.10.2026: 'Harran Aile Mezarligi' Sanliurfa sehir mezarligi; ilce adi mezarlik adinin onunde 'Aile' gibi sozcukle gelirse baglanmaz
        self.assertIsNone(self.isle("Şanlıurfa", defin_yeri="Harran Aile Mezarlığı")["ilce"])
        self.assertEqual(self.isle("Şanlıurfa", defin_yeri="Harran Mezarlığı")["ilce"], "Harran")
        self.assertEqual(self.isle("Erzincan", namaz_yeri_vakti="Cenazesi Öğlen Namazını Müteakip Üzümlü Çarşı Camii'nden Alınarak Üzümlü Mezarlığına Defnedilecektir.")["ilce"], "Üzümlü")
        self.assertEqual(self.isle("Uşak", defin_yeri="Uşak Ulubey İlçesi")["ilce"], "Ulubey")

    def test_baska_il_ve_nakil_atlanir(self):
        self.assertIsNone(self.isle("Kocaeli", defin_yeri="Nakil: Samsun Otobüs / Gebze")["ilce"])
        self.assertIsNone(self.isle("Kocaeli", defin_yeri="Ankara Gebze Mezarlığı")["ilce"])
        self.assertIsNone(self.isle("Kırıkkale", namaz_yeri_vakti="Bayat İlçesinden")["ilce"])

    def test_cok_ilce_adi_belirsiz(self):
        self.assertIsNone(self.isle("Kocaeli", defin_yeri="Gebze Gölcük Yolu Mezarlığı")["ilce"])

    def test_genel_ilce_adi_siki(self):
        self.assertEqual(self.isle("Elazığ", defin_yeri="Maden Mezarlığı")["ilce"], "Maden")
        self.assertIsNone(self.isle("Elazığ", defin_yeri="Bakır Maden Ocağı Mezarlığı")["ilce"])
        self.assertIsNone(self.isle("Bursa", defin_yeri="Yıldırım Beyazıt Mezarlığı")["ilce"])
        self.assertIsNone(self.isle("Bursa", defin_yeri="Köy", namaz_yeri_vakti="Orhangazi Camii")["ilce"])   # tarihi cami Osmangazi'de

    def test_namaz_yeri_belirli_mezarlik_varsa_baglanmaz(self):
        k = self.isle("Sivas", defin_yeri="Yukarı Tekke - 90. Ada Mezarlığı", namaz_yeri_vakti="Ulaş Merkez")
        self.assertEqual(k["ilce"], "Merkez")              # gomme Sivas merkezde (sehir mezarligi); namaz yeri ilce secimini belirlemez (15.10 MERKEZ_ETKIN)
        k = self.isle("Sivas", defin_yeri="Köy Mezarlığı", namaz_yeri_vakti="Ulaş Merkez")
        self.assertEqual(k["ilce"], "Ulaş")

    def test_mahalle_tablosu(self):
        k = self.isle("Bursa", mahalle="Koğukçınar Mah.")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Osmangazi", "mahalle_tablo"))
        k = self.isle("Bursa", mahalle="Küplüpınar Mahallesi")
        self.assertEqual(k["ilce"], "Osmangazi")
        self.assertIsNone(self.isle("Konya", mahalle="Koğukçınar Mah.")["ilce"])      # baska ilin tablosu aranmaz
        self.assertIsNone(self.isle("Bursa", mahalle="Bilinmeyen Mah.")["ilce"])

    def test_merkez_degeri_listede_varsa_yazilir(self):
        k = self.isle("Isparta", mahalle="Batıkent")                                   # 15.10: buyuksehir olmayan illerde Merkez ilceler.json'da
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Merkez", "mahalle_tablo"))

    def test_merkez_etkin_bayragi(self):
        # 15.10: Merkez artik ilceler.json'da oldugu icin bayrak yalniz listede OLMAYAN Merkez'i acar; listedeki Merkez her durumda gecerli
        self.assertEqual(self.isle("Isparta", mahalle="Batıkent")["ilce"], "Merkez")
        # 'Merkez' + baska ilce ortak mezarlik adi: Merkez gecerli degilken kalani secmek tahmin olur -> None
        ortak._mez_onbellek.clear(); ortak._mez_onbellek.update({"isparta": {"asri": {"belirsiz": ["Merkez", "Atabey"]}}})
        self.assertIsNone(self.isle("Isparta", defin_yeri="Asri Mezarlık")["ilce"])

    def test_koy_adayi_ve_tablo_yoksa_sessiz(self):
        ortak._mah_onbellek.clear(); ortak._mah_onbellek["bolu"] = {"doganci": "Mudurnu"}
        k = self.isle("Bolu", defin_yeri="Köy Mezarlığı", namaz_yeri_vakti="Doğancı Köyü Yeni Camiide kılınacak öğle ve cenaze namazından sonra")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Mudurnu", "mahalle_tablo"))
        ortak._mah_onbellek.clear(); ortak._mah_onbellek["_yok"] = True
        self.assertIsNone(self.isle("Bolu", defin_yeri="Köy Mezarlığı", namaz_yeri_vakti="Doğancı Köyü")["ilce"])

    def test_belirli_mezarlik_varken_cami_mahallesi_baglanmaz(self):
        ortak._mah_onbellek.clear(); ortak._mah_onbellek["bursa"] = {"zyxhamit": "Yıldırım"}   # 16.10: resmi tabloda OLMAYAN uydurma ad (resmi liste once gelir)
        k = self.isle("Bursa", defin_yeri="Bilinmeyen Sehir Mezarlığı", namaz_yeri_vakti="Öğle – Zyxhamit Camii")
        self.assertIsNone(k["ilce"])
        k = self.isle("Bursa", defin_yeri=None, namaz_yeri_vakti="Öğle – Zyxhamit Camii")
        self.assertEqual(k["ilce"], "Yıldırım")

    def test_ad_sifati_varsayilan_kapali_ve_ad_degismez(self):
        k = self.isle("Kırıkkale", ad_soyad="Keskinli Enver Yıldızlı")
        self.assertIsNone(k["ilce"]); self.assertEqual(k["ad_soyad"], "Keskinli Enver Yıldızlı")
        ortak.AD_SIFATI_ACIK = True
        try:
            k = self.isle("Kırıkkale", ad_soyad="Keskinli Enver Yıldızlı")
            self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Keskin", "ad_sifati"))
            self.assertEqual(k["ad_soyad"], "Keskinli Enver Yıldızlı")
            self.assertEqual(self.isle("Kırıkkale", ad_soyad="Balışeyhli Zekeriye Doğan")["ilce"], "Balışeyh")
            self.assertIsNone(self.isle("Kırıkkale", ad_soyad="Çorumlu Emine Memişoğlu")["ilce"])   # Corum Kirikkale ilcesi degil
            self.assertIsNone(self.isle("Kırıkkale", ad_soyad="Keskinli")["ilce"])                  # tek sozcuk = ad degil
        finally:
            ortak.AD_SIFATI_ACIK = False

    def test_il_disi_ve_mevcut_ilce_bozulmaz(self):
        k = self.isle("Bursa", mahalle="Koğukçınar Mah.", defin_yeri="Kilis")
        self.assertEqual(k["il_disi_defin"]["il"], "Kilis"); self.assertIsNone(k["ilce"])
        k = ortak.ilce_isle({"id": "a", "ilce": "Nilüfer", "mahalle": "Koğukçınar Mah."}, "Bursa")
        self.assertEqual(k["ilce"], "Nilüfer"); self.assertNotIn("ilce_kaynagi", k)

    def test_mezarlik_tablosu_oncelikli(self):
        ortak._mez_onbellek.clear(); ortak._mez_onbellek.update({"bursa": {"sayfiye": "Mudanya"}})
        k = self.isle("Bursa", defin_yeri="Sayfiye Mezarlığı", mahalle="Koğukçınar Mah.")
        self.assertEqual((k["ilce"], k["ilce_kaynagi"]), ("Mudanya", "mezarlik_tablosu"))

    def test_mahalle_norm(self):
        self.assertEqual(ortak.mahalle_norm("Koğukçınar Mah."), "kogukcinar")
        self.assertEqual(ortak.mahalle_norm("İçmesu Köyü"), "icmesu")
        self.assertEqual(ortak.mahalle_norm("Demirtaş Dumlupınar Mahallesi (Yeni)"), "demirtas dumlupinar")


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
