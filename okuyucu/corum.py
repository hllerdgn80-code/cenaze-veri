#!/usr/bin/env python3
"""Çorum: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Osmancık Haber, Çorum Hakimiyet, Leblebi TV, Yayla Haber, Çorum Haber. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/corum.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Çorum"
SITELER = [
    oh.site("Osmancık Haber", "corum-osmancikhaber", "https://www.osmancik.com.tr/feed/", kesin_yerel=True, ilce="Osmancık"),
    oh.site("Çorum Hakimiyet", "corum-corumhakimiyet", "https://www.corumhakimiyet.net/rss", ek_dizin="https://www.corumhakimiyet.net/sitemap/sitemap-{AY}.xml"),
    oh.site("Leblebi TV", "corum-leblebitv", "https://www.leblebi.tv/rss", ek_dizin="https://www.leblebi.tv/sitemap/sitemap-{AY}.xml"),
    oh.site("Yayla Haber", "corum-yaylahaber", "https://www.yaylahaber.com.tr/rss", ek_dizin="https://www.yaylahaber.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("Çorum Haber", "corum-corumhaber", "https://www.corumhaber.net/rss", ek_dizin="https://www.corumhaber.net/sitemap/sitemap-{AY}.xml"),
]


def main():
    oi.il_calistir(IL, "corum", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
