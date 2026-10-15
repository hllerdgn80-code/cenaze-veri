"""Yarının ilanları anında yayında (15.10.2026): yarın/öbür gün son7gun'a girer, depo geri katar, kopyalar tek kalır."""
import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

BUGUN = datetime.now(timezone.utc).astimezone().date()


def g(n):
    return (BUGUN + timedelta(days=n)).isoformat()


def kay(i, ad, gun, yas=70, **ek):
    k = {"id": i, "il": "Gaziantep", "ilce": "Şahinbey", "ilce_belirsiz": False, "ad_soyad": ad, "yas": yas,
         "namaz_tarihi": gun, "vefat_tarihi": gun, "liste_tarihi": gun, "kaynak_ad": "t", "kaynak_url": "http://x/" + i}
    k.update(ek)
    return k


def calis(kok, kayitlar):
    by = {}
    for k in kayitlar:
        by.setdefault(k["liste_tarihi"], []).append(k)
    ortak.son7gun_yaz(kok, "Gaziantep", sorted(by, reverse=True), by)
    with open(os.path.join(kok, "son7gun.json"), encoding="utf-8") as f:
        d = json.load(f)
    tum = [k for l in d["ilceler"].values() for k in l] + d["il_disi"] + d["ilce_belirsiz"]
    return {k["id"]: k for k in tum}, tum


class Yarin(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); self.kok = self.t.name
    def tearDown(self):
        self.t.cleanup()

    def test_yarin_yayina_girer(self):
        s, _ = calis(self.kok, [kay("a", "Ali Veli", g(1))])
        self.assertIn("a", s); self.assertEqual(s["a"]["namaz_tarihi"], g(1))

    def test_obur_gun_girer(self):
        s, _ = calis(self.kok, [kay("a", "Ali Veli", g(2))])
        self.assertIn("a", s)

    def test_uc_gun_sonrasi_girmez(self):
        s, _ = calis(self.kok, [kay("a", "Ali Veli", g(3))])
        self.assertNotIn("a", s)
        with open(os.path.join(self.kok, "_bekleyen.json"), encoding="utf-8") as f:
            self.assertEqual([k["id"] for k in json.load(f)["kayitlar"]], ["a"])

    def test_depodan_geri_katilir(self):
        calis(self.kok, [kay("a", "Ali Veli", g(1))])
        s, _ = calis(self.kok, [kay("b", "Baska Kisi", g(0))])   # kaynak "a"yı düşürdü
        self.assertIn("a", s); self.assertIn("b", s)

    def test_gun_gecince_depodan_cikar(self):
        k = kay("a", "Ali Veli", g(-2))
        with open(os.path.join(self.kok, "_bekleyen.json"), "w", encoding="utf-8") as f:
            json.dump({"il": "Gaziantep", "kayitlar": [k]}, f)
        s, _ = calis(self.kok, [kay("b", "Baska Kisi", g(0))])
        self.assertNotIn("a", s)

    def test_ayni_id_tek_kayit(self):
        calis(self.kok, [kay("a", "Ali Veli", g(1))])
        s, tum = calis(self.kok, [kay("a", "Ali Veli", g(1), yas=71)])
        self.assertEqual(len(tum), 1); self.assertEqual(s["a"]["yas"], 71)

    def test_farkli_id_ayni_kisi_taze_kalir(self):
        calis(self.kok, [kay("eski", "Ali Veli", g(1), yas=None)])
        s, tum = calis(self.kok, [kay("yeni", "ALİ VELİ", g(1), yas=70, mahalle="Merkez")])
        self.assertEqual([k["id"] for k in tum], ["yeni"])
        with open(os.path.join(self.kok, "_kapi_red.json"), encoding="utf-8") as f:
            red = json.load(f)["red"]
        self.assertEqual(red[0]["kural"], ["yarın kopyası"]); self.assertEqual(red[0]["tutulan_id"], "yeni")
        with open(os.path.join(self.kok, "_bekleyen.json"), encoding="utf-8") as f:
            self.assertEqual([k["id"] for k in json.load(f)["kayitlar"]], ["yeni"])

    def test_ilk_gorulme_korunur(self):
        calis(self.kok, [kay("a", "Ali Veli", g(1), ilk_gorulme="2026-10-14T20:00:00+03:00")])
        # ilk tur damgayi son7gun'a yazdi mi? Sonraki turda kaynak dusurse depodan gelen kayit ayni damgayi tasir.
        with open(os.path.join(self.kok, "son7gun.json"), encoding="utf-8") as f:
            d = json.load(f)
        ilk = d["ilceler"]["Şahinbey"][0]["ilk_gorulme"]
        s, _ = calis(self.kok, [kay("b", "Baska Kisi", g(0))])
        self.assertEqual(s["a"]["ilk_gorulme"], ilk)


if __name__ == "__main__":
    unittest.main()
