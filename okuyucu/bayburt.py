#!/usr/bin/env python3
"""Bayburt: belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Bayburt Haber, Bayburt Haber Ajansı, Bayburt Gündem. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/bayburt.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_haber as oh, ortak_ilce as oi, ortak_kategori as ok

IL = "Bayburt"
SITELER = [
    oh.site("Bayburt Haber", "bayburt-bayburthaber", "https://www.bayburthaber.com/rss"),
    oh.site("Bayburt Haber Ajansı", "bayburt-bayburthaberajansi", "https://www.bayburthaberajansi.com.tr/rss"),
    oh.site("Bayburt Gündem", "bayburt-bayburtgundem", "https://www.bayburtgundem.com/rss", ek_dizin="https://www.bayburtgundem.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Bayburt Postası", "bayburt-bayburtpostasi", "https://www.bayburtpostasi.com.tr/rss", ek_dizin="https://www.bayburtpostasi.com.tr/sitemap/sitemap-{AY}.xml"),   # 14.10.2026 H50: RSS 20 haber; vefat haberi ayda ~2-4 -> aylık site haritası da taranır
]
# vefat KATEGORİ sayfası (H50): /taziye-ve-duyurular haber başlıkları (tarih sayfadan); /vefat 410, /vefat-edenler 404 -> yok
KATEGORI = [(("Bayburt Postası", "bayburt-bayburtpostasi", "https://www.bayburtpostasi.com.tr/taziye-ve-duyurular"), {})]


def main():
    oi.il_calistir(IL, "bayburt", oh.okuyucular(IL, SITELER) + [ok.kategori(*a, **k) for a, k in KATEGORI])


if __name__ == "__main__":
    main()
