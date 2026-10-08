#!/usr/bin/env python3
"""Bayburt: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Bayburt Haber, Bayburt Haber Ajansı, Bayburt Gündem. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/bayburt.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Bayburt"
SITELER = [
    oh.site("Bayburt Haber", "bayburt-bayburthaber", "https://www.bayburthaber.com/rss"),
    oh.site("Bayburt Haber Ajansı", "bayburt-bayburthaberajansi", "https://www.bayburthaberajansi.com.tr/rss"),
    oh.site("Bayburt Gündem", "bayburt-bayburtgundem", "https://www.bayburtgundem.com/rss", ek_dizin="https://www.bayburtgundem.com/sitemap/sitemap-{AY}.xml"),
]


def main():
    oi.il_calistir(IL, "bayburt", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
