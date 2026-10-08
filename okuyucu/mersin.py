#!/usr/bin/env python3
"""Mersin: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Çukurova Gazetesi, Mersin Haber Merkezi, İmece Gazetesi, İste Mersin. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/mersin.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Mersin"
SITELER = [
    oh.site("Çukurova Gazetesi", "mersin-cukurovagazetesi", "https://www.cukurovagazetesi.com/rss", ek_dizin="https://www.cukurovagazetesi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Mersin Haber Merkezi", "mersin-mersinhabermerkezi", "https://www.mersinhabermerkezi.com/rss", ek_dizin="https://www.mersinhabermerkezi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("İmece Gazetesi", "mersin-imecegazetesi", "https://www.imecegazetesi.com/rss"),
    oh.site("İste Mersin", "mersin-istemersin", "https://www.istemersin.com/rss"),
]


def main():
    oi.il_calistir(IL, "mersin", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
