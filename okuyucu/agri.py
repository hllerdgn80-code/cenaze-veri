#!/usr/bin/env python3
"""Ağrı: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Doğubayazıt Gazetesi, Ağrı Hürses, Patnos Haber Gazetesi. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/agri.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi

IL = "Ağrı"
SITELER = [
    oh.site("Doğubayazıt Gazetesi", "agri-dogubayazitgazetesi", "https://www.dogubayazitgazetesi.com/rss", kesin_yerel=True, ilce="Doğubayazıt", takma=("Doğubeyazıt",), ek_dizin="https://www.dogubayazitgazetesi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Ağrı Hürses", "agri-agrihurses", "https://www.agrihurses.net/rss", ek_dizin="https://www.agrihurses.net/sitemap/sitemap-{AY}.xml"),
    oh.site("Patnos Haber Gazetesi", "agri-patnoshabergazetesi", "https://www.patnoshabergazetesi.com/rss"),
    # H52 (14.10.2026): ilçe bazlı keşifle bulunan yerel siteler (Ağrı/Iğdır; ajans04 Iğdır haberini de verir)
    oh.site("Ajans 04", "agri-ajans04", "https://www.ajans04.net/rss.php"),
    oh.site("Diyadin Net", "agri-diyadinnet", "https://www.diyadinnet.com/rss", ilce="Diyadin"),
    oh.site("Ağrı 04 Haber", "agri-agri04haber", "https://www.agri04haber.com/rss"),
    oh.site("TV04", "agri-tv04", "https://www.tv04.net/rss/"),
    oh.site("Ağrıda Haber", "agri-agridahaber", "https://www.agridahaber.com/rss/"),
    oh.site("Karaköse Haber", "agri-karakosehaber", "https://www.karakosehaber.com/rss/"),
]


def main():
    oi.il_calistir(IL, "agri", oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
