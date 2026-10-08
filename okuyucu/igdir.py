#!/usr/bin/env python3
"""Iğdır: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Yeşil Iğdır, Iğdır Haber. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/igdir.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Iğdır"
SITELER = [
    oh.site("Yeşil Iğdır", "igdir-yesiligdir", "https://www.yesiligdir.com/rss", ek_dizin="https://www.yesiligdir.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Iğdır Haber", "igdir-igdirhaber", "https://www.igdirhaber.net/rss"),
]


def main():
    oi.il_calistir(IL, "igdir", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
