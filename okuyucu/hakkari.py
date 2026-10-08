#!/usr/bin/env python3
"""Hakkari: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Hakkari İl Sesi, Gazete Pano, Yüksekova Halkın Sesi. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/hakkari.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Hakkari"
SITELER = [
    oh.site("Hakkari İl Sesi", "hakkari-hakkariilsesi", "https://www.hakkariilsesigazetesi.com/rss", ek_dizin="https://www.hakkariilsesigazetesi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Gazete Pano", "hakkari-gazetepano", "https://www.gazetepano.com/feed/"),
    oh.site("Yüksekova Halkın Sesi", "hakkari-yuksekovahalkinsesi", "https://www.yuksekovahalkinsesigazetesi.com/rss", ek_dizin="https://www.yuksekovahalkinsesigazetesi.com/sitemap/sitemap-{AY}.xml"),
]


def main():
    oi.il_calistir(IL, "hakkari", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
