#!/usr/bin/env python3
"""Kars: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Kars Manşet, Haber Sarıkamış, Kars Hakimiyet. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/kars.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Kars"
SITELER = [
    oh.site("Kars Manşet", "kars-karsmanset", "https://www.karsmanset.com/rss"),
    oh.site("Haber Sarıkamış", "kars-habersarikamis", "https://www.habersarikamis.com/rss", kesin_yerel=True, ilce="Sarıkamış"),
    oh.site("Kars Hakimiyet", "kars-karshakimiyet", "https://www.karshakimiyet.com/rss"),
]


def main():
    oi.il_calistir(IL, "kars", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
