#!/usr/bin/env python3
"""16.10.2026 ilçe kuralları: mezarlık ön eki, ilçe adı başta, merkez belediyesi. Çalıştırma: python3 -B okuyucu/test_ilce_kural.py"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak


def isle(il, **k):
    r = {"il": il, "ilce": None, "mahalle": None, "ad_soyad": "Ali Veli", "defin_yeri": None, "namaz_yeri_vakti": None,
         "kaynak_ad": None, "ham": {}}
    r.update(k)
    return ortak.ilce_isle(r, il)


class IlceKural(unittest.TestCase):
    def test_mezarlik_on_ek(self):
        self.assertEqual(isle("Kayseri", defin_yeri="Erkilet Bülbülpınar Mez.")["ilce"], "Kocasinan")

    def test_ilce_adi_basta(self):
        self.assertEqual(isle("Uşak", defin_yeri="Sivaslı Tatar Kasabası")["ilce"], "Sivaslı")

    def test_mezarlik_adi_ilce_basta_baglanmaz(self):
        self.assertIsNone(isle("Şanlıurfa", defin_yeri="Harran Aile Mezarlığı")["ilce"])

    def test_merkez_belediyesi(self):
        self.assertEqual(isle("Edirne", defin_yeri="Yenişehir Mezarlığı", kaynak_ad="Edirne Belediyesi")["ilce"], "Merkez")

    def test_merkez_belediyesi_koy_baglanmaz(self):
        self.assertIsNone(isle("Karabük", defin_yeri="Bulak Köyü Mezarlığı", namaz_yeri_vakti="Bulak Köyü Cami - Öğle",
                               kaynak_ad="Karabük Belediyesi")["ilce"])

    def test_buyuksehir_merkez_yok(self):
        self.assertIsNone(isle("Konya", defin_yeri="Yediler Mezarlığı", kaynak_ad="Konya Belediyesi")["ilce"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
