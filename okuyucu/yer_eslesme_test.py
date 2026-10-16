#!/usr/bin/env python3
"""ortak.yer_eslesir testi (12 örnek; Dart ve JS testleriyle AYNI liste):  python3 -B okuyucu/yer_eslesme_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortak import yer_eslesir, yer_sade, namaz_cami

ORNEK = [
    ("Korgan Merkez Camii", "MERKEZ CAMİİ", None, None, True),
    ("Çitlice Camii", None, "Çitlice", None, True),
    ("Çitlice Camii", "Merkez Camii", None, None, False),
    ("Çitlice Camii", "Merkez Camii", "Çitlice Mahallesi", None, True),
    ("", "Merkez Camii", "Merkez", None, False),
    ("Çitlice Camii", None, None, None, False),
    ("Merkez Camii", "Korgan Merkez Camii", None, None, True),
    ("Ordu Merkez Camii", "Korgan Merkez Camii", None, None, False),
    ("Ulu Camii", "Yeni Camii", None, None, False),
    ("Tepe Köyü", "", "TEPE KÖYÜ", None, True),
    ("Çitlice Camii", "Çitlik Camii", None, None, False),
    ("Korgan Çitlice Camii", "Korgan Merkez Camii", None, "Korgan", False),
]
for g, c, m, h, bek in ORNEK:
    assert yer_eslesir(g, c, m, h) == bek, (g, c, m, h, bek)
assert yer_eslesir("Korgan Çitlice Camii", "Korgan Merkez Camii", None) is True   # haric verilmezse ortak 'korgan' eşleştirir
assert yer_sade("ÇİTLİCE MAHALLESİ") == "citlice" and yer_sade("Mah. Ortaköy Camisi") == "ortakoy"
assert namaz_cami("ÖĞLE NAMAZINDAN SONRA - MERKEZ CAMİİ") == "MERKEZ CAMİİ" and namaz_cami("İkindi-ORTAKÖY CAMİİ") == "ORTAKÖY CAMİİ" and namaz_cami("Öğle") == ""
print("yer_eslesme: 12 örnek + 3 ek tamam")
