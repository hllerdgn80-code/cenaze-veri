import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kaynak_sayac as ks


class T(unittest.TestCase):
    def test_iki_tur_sifir_uyari(self):
        with tempfile.TemporaryDirectory() as d:
            ks.VERI = d
            os.makedirs(os.path.join(d, "x"))
            ks.kaydet("x", {"A": 3, "B": 0, "C": 5})
            ks.kaydet("x", {"A": 0, "B": "HATA: zaman aşımı", "C": 0})
            ks.kaydet("x", {"A": 0, "B": 0, "C": 2})
            u = {w["kaynak"]: w for w in ks.birlestir()}
            self.assertEqual(set(u), {"x/A", "x/B"})        # A: 2 tur 0; B: 3 tur 0/HATA; C kurtuldu
            self.assertEqual(u["x/B"]["ardisik_tur"], 3)
            self.assertTrue(os.path.exists(os.path.join(d, "_kaynak_uyari.json")))

    def test_tek_tur_uyarmaz_ve_14_sinir(self):
        with tempfile.TemporaryDirectory() as d:
            ks.VERI = d
            os.makedirs(os.path.join(d, "y"))
            ks.kaydet("y", {}, toplam=0, hata=None)
            self.assertEqual(ks.birlestir(), [])
            for i in range(20):
                ks.kaydet("y", {"K": i})
            self.assertEqual(len(json.load(open(os.path.join(d, "y", "_sayac.json")))["K"]), 14)


if __name__ == "__main__":
    unittest.main()
