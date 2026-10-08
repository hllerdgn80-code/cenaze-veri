#!/usr/bin/env python3
"""Şırnak: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Şırnak Ajans, Şırnak Haber, Şırnak Haber 73. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/sirnak.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Şırnak"
SITELER = [
    oh.site("Şırnak Ajans", "sirnak-sirnakajans", "https://www.sirnakajans.com/rss", ek_dizin="https://www.sirnakajans.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Şırnak Haber", "sirnak-sirnakhaber", "https://www.sirnakhaber.com/rss"),
    oh.site("Şırnak Haber 73", "sirnak-sirnakhaber73", "https://www.sirnakhaber73.com/rss"),
]


def main():
    oi.il_calistir(IL, "sirnak", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
