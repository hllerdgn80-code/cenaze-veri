#!/usr/bin/env python3
"""Adana: il belediyesinde liste yok -> Kozan Belediyesi (13.10.2026 keşfi: JS_FORM değil, düz HTML liste).
`kozan.bel.tr/cenaze-hizmetleri`: kart listesi, her kart "Ad Soyad" + tarih (YYYY-AA-GG); 60 kart tek sayfada. Kartın "Detaylar" sayfası
aynı tarihi "Vefaat Tarihi" diye verir (3 örnekte kart tarihi = vefat tarihi doğrulandı) ve yakın adlarıyla taziye adresini içerir: KVKK gereği
detay sayfaları AÇILMAZ; yalnız ad + vefat tarihi alınır (defin yeri/ilçe içi yer kaynakta yok). robots.txt yok (404).
Kullanım: python3 okuyucu/adana.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Adana"
KOZAN_URL = "http://www.kozan.bel.tr/cenaze-hizmetleri"


def kozan(ctx):
    sayfa = oi.al(KOZAN_URL)
    kartlar = re.findall(r'<h3 class="box-title"><a href="[^"]+">([^<]+)</a></h3>\s*<div class="blog-meta">\s*<a[^>]*>(?:<i[^>]*></i>)?\s*([\d.\-/]+)', sayfa)
    if not kartlar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for ad_ham, t in kartlar:
        ad, gun = oi.ad_duzelt(ad_ham), oi.tarih(t)
        if not ad or not gun:
            continue
        sonuc.append(oi.kayit(IL, "Kozan", "adana-kozan", ad, gun, "Kozan Belediyesi", KOZAN_URL, ctx["alindi"],
                              vefat_tarihi=gun, liste_tarihi=gun, ham={}))
    return sonuc


def main():
    oi.il_calistir(IL, "adana", [("Kozan", kozan)])


if __name__ == "__main__":
    main()
