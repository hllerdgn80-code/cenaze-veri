#!/usr/bin/env python3
"""yayin_suz regresyon testi (16.10.2026 H83): kayıt defteri 'vefat edenler' listesinden gelen yerel basın kaydı (tarih_kaynagi=metin,
yalnız vefat/liste tarihi) YAYINA GİRER; 'yayin_tarihi' kaynaklı kayıt (sahibi 14.10 kuralı) GİRMEZ; eski kayıt girmez; bebek girmez.
Çalıştırma: python3 -B okuyucu/test_yayin_suz.py"""
import datetime, os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yayin_suz as ys


def _kayit(**ek):
    k = {"id": "x1", "il": "Malatya", "ilce": "Battalgazi", "ad_soyad": "Ali Veli", "yas": 70, "kaynak_turu": "yerel_basin",
         "kaynak_ad": "Deneme Gazetesi", "kaynak_url": "https://ornek.test/1", "namaz_tarihi": None, "namaz_yeri_vakti": None,
         "defin_yeri": None, "defin_zamani": None, "ham": {"sayfa_tarihi": None, "tarih_kaynagi": "metin"}}
    k.update(ek)
    return k


class YayinSuzTest(unittest.TestCase):
    def setUp(self):
        self.bugun = ys._bugun_tr()
        self.dun = (self.bugun - datetime.timedelta(days=1)).isoformat()

    def test_vefat_listesi_kaydi_yayina_girer(self):
        k = _kayit(liste_tarihi=self.dun, vefat_tarihi=self.dun, ham={"sayfa_tarihi": self.dun, "tarih_kaynagi": "metin"})
        self.assertEqual(ys.yerel_gun(k), self.dun)
        self.assertTrue(ys.yerel_kilidi(k))
        d = ys.son7_suz({"il": "Malatya", "ilceler": {"Battalgazi": [k]}, "il_disi": [], "ilce_belirsiz": []})
        self.assertEqual(len(d["ilceler"].get("Battalgazi", [])), 1)
        self.assertNotIn("kaynak_ad", d["ilceler"]["Battalgazi"][0])        # kaynak izi soyulur

    def test_defin_tarihli_kayit_yayina_girer(self):
        k = _kayit(liste_tarihi=self.dun, namaz_tarihi=self.dun, namaz_yeri_vakti="Merkez Camii, Öğle",
                   ham={"sayfa_tarihi": self.dun, "tarih_kaynagi": "metin"})
        self.assertTrue(ys.yerel_kilidi(k))

    def test_yayin_tarihi_kaydi_girmez(self):
        k = _kayit(liste_tarihi=self.dun, vefat_tarihi=self.dun, il="Samsun",
                   ham={"sayfa_tarihi": self.dun, "yayin_tarihi": self.dun, "tarih_kaynagi": "yayin_tarihi"})
        self.assertIsNone(ys.yerel_gun(k))
        self.assertFalse(ys.yerel_kilidi(k))

    def test_rahat_ilde_bilgisiz_ilan_girer(self):
        k = _kayit(il="Ağrı", ilce="Patnos", kaynak_turu="yerel_haber", ham={"sayfa_tarihi": self.dun, "tarih_kaynagi": "yayin_tarihi"})
        self.assertEqual(ys.yerel_gun(k), self.dun)
        self.assertTrue(ys.yerel_kilidi(k))

    def test_eski_kayit_girmez(self):
        eski = (self.bugun - datetime.timedelta(days=9)).isoformat()
        k = _kayit(liste_tarihi=eski, vefat_tarihi=eski, ham={"sayfa_tarihi": eski, "tarih_kaynagi": "metin"})
        self.assertFalse(ys.yerel_kilidi(k))

    def test_resmi_kayit_dokunulmaz(self):
        k = _kayit(kaynak_turu="belediye", liste_tarihi=self.dun, vefat_tarihi=self.dun)
        d = ys.son7_suz({"il": "Malatya", "ilceler": {"Battalgazi": [k]}, "il_disi": [], "ilce_belirsiz": []})
        self.assertEqual(len(d["ilceler"]["Battalgazi"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
