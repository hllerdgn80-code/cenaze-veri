#!/usr/bin/env python3
"""Bingöl: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Bingöl Kent Haber, Bingöl Online. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/bingol.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Bingöl"
SITELER = [
    oh.site("Bingöl Kent Haber", "bingol-bingolkenthaber", "https://www.bingolkenthaber.com/rss", ek_dizin="https://www.bingolkenthaber.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Bingöl Online", "bingol-bingolonline", "https://www.bingolonline.com/rss"),
]


def main():
    oi.il_calistir(IL, "bingol", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
