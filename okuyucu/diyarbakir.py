#!/usr/bin/env python3
"""Diyarbakır: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Bismil Haber, Mücadele Gazetesi, Diyarbakır Söz. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/diyarbakir.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi, ortak_kategori as ok

IL = "Diyarbakır"
SITELER = [
    oh.site("Bismil Haber", "diyarbakir-bismilhaber", "https://www.bismilhaber.com.tr/rss", kesin_yerel=True, ilce="Bismil", ek_dizin="https://www.bismilhaber.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("Mücadele Gazetesi", "diyarbakir-mucadelegazetesi", "https://www.mucadelegazetesi.com.tr/rss", ek_dizin="https://www.mucadelegazetesi.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("Diyarbakır Söz", "diyarbakir-diyarbakirsoz", "https://www.diyarbakirsoz.com/rss"),
]
# vefat KATEGORİ sayfaları (14.10.2026, H41; ortak_kategori.py)
KATEGORI = [
    (("Bismil Haber", "diyarbakir-bismilhaber", "https://www.bismilhaber.com.tr/vefat-edenler"), {"ilce": "Bismil"}),
    (("Mücadele Gazetesi", "diyarbakir-mucadelegazetesi", "https://www.mucadelegazetesi.com.tr/vefat"), {"tip": "kart"}),
]


def main():
    oi.il_calistir(IL, "diyarbakir", oh.okuyucular(IL, SITELER) + [ok.kategori(*a, **k) for a, k in KATEGORI])


if __name__ == "__main__":
    main()
