#!/usr/bin/env python3
"""gorevli_birlestir birim testi:  python3 -I okuyucu/gorevli_birlestir_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gorevli_birlestir import birlestir

def kayit(id_, ad, ilce, nam, **ek):
    r = {"id": id_, "ad_soyad": ad, "ilce": ilce, "namaz_tarihi": nam, "vefat_tarihi": None, "liste_tarihi": nam}
    r.update(ek); return r

# 1) aynı kişi iki kaynakta -> TEK kart, gorevli:true; boş alanlar otomatik kayıttan dolar
otomatik = kayit("b1", "Fatma Örnek", "Korgan", "2026-10-15", defin_yeri="Korgan Mezarlığı", mahalle="Tepe", yas=80, kaynak_ad="Belediye")
d = {"il": "Ordu", "ilceler": {"Korgan": [otomatik]}, "il_disi": [], "ilce_belirsiz": []}
g = kayit("gorevli-1", "FATMA ÖRNEK", "Korgan", "2026-10-16", gorevli=True, gorev_yeri="Korgan Merkez Camii", kaynak_ad="gorevli", yas=None, defin_yeri=None)
e, s = birlestir(d, [g])
liste = d["ilceler"]["Korgan"]
assert len(liste) == 1 and liste[0]["id"] == "gorevli-1" and liste[0]["gorevli"] is True, liste
assert liste[0]["defin_yeri"] == "Korgan Mezarlığı" and liste[0]["mahalle"] == "Tepe" and liste[0]["yas"] == 80
assert (e, s) == (0 + 1, 1)
# 2) görevli kaydı ulusal_birlestir ile zaten eklenmişse çift kart olmaz
d = {"il": "Ordu", "ilceler": {"Korgan": [otomatik, kayit("gorevli-1", "Fatma Örnek", "Korgan", "2026-10-16", gorevli=True)]}, "il_disi": [], "ilce_belirsiz": []}
birlestir(d, [d["ilceler"]["Korgan"][1]])
assert [x["id"] for x in d["ilceler"]["Korgan"]] == ["gorevli-1"], d
# 3) farklı kişi dokunulmaz; ilçesiz otomatik kayıt da (ilce_belirsiz) kalkar
d = {"il": "Ordu", "ilceler": {"Korgan": [kayit("b2", "Ali Kaya", "Korgan", "2026-10-15")]}, "il_disi": [], "ilce_belirsiz": [kayit("b3", "Fatma Örnek", None, "2026-10-14")]}
birlestir(d, [kayit("gorevli-2", "Fatma Örnek", "Korgan", "2026-10-15", gorevli=True)])
assert len(d["ilceler"]["Korgan"]) == 2 and d["ilce_belirsiz"] == [], d
# 4) şehit kaydı korunur, görevli kaydı eklenmez
sehit = kayit("s1", "Mehmet Er", "Korgan", "2026-10-15", sehit=True)
d = {"il": "Ordu", "ilceler": {"Korgan": [sehit]}, "il_disi": [], "ilce_belirsiz": []}
birlestir(d, [kayit("gorevli-3", "Mehmet Er", "Korgan", "2026-10-15", gorevli=True)])
assert d["ilceler"]["Korgan"] == [sehit]
# 5) yaş çelişirse aynı kişi sayılmaz
d = {"il": "Ordu", "ilceler": {"Korgan": [kayit("b4", "Hasan Öz", "Korgan", "2026-10-15", yas=40)]}, "il_disi": [], "ilce_belirsiz": []}
birlestir(d, [kayit("gorevli-4", "Hasan Öz", "Korgan", "2026-10-15", yas=80, gorevli=True)])
assert len(d["ilceler"]["Korgan"]) == 2
print("gorevli_birlestir: 5 test tamam")
