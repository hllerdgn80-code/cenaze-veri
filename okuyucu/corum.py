#!/usr/bin/env python3
"""Çorum: il belediyesinde liste yok. RESMÎ ilçe kaynağı (13.10.2026): Alaca Belediyesi `alaca.bel.tr/vefat-ve-defin-hizmetleri/` (WordPress/Formidable
tablosu: Ad Soyad, Vefat Tarihi, Defin Tarihi, Camii, Vakit, Açıklama). "Açıklama" yakın adlarıdır: ALINMAZ. Son kayıt 25.09.2026 (seyrek, haftalar arası boşluk):
pencerede 0 kayıt normaldir, yeni ilan çıkınca alınır. Diğer ilçeler ve il merkezi: -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Osmancık Haber, Çorum Hakimiyet, Leblebi TV, Yayla Haber, Çorum Haber. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/corum.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_haber as oh, ortak_ilce as oi

IL = "Çorum"
SITELER = [
    oh.site("Osmancık Haber", "corum-osmancikhaber", "https://www.osmancik.com.tr/feed/", kesin_yerel=True, ilce="Osmancık"),
    oh.site("Çorum Hakimiyet", "corum-corumhakimiyet", "https://www.corumhakimiyet.net/rss", ek_dizin="https://www.corumhakimiyet.net/sitemap/sitemap-{AY}.xml"),
    oh.site("Leblebi TV", "corum-leblebitv", "https://www.leblebi.tv/rss", ek_dizin="https://www.leblebi.tv/sitemap/sitemap-{AY}.xml"),
    oh.site("Yayla Haber", "corum-yaylahaber", "https://www.yaylahaber.com.tr/rss", ek_dizin="https://www.yaylahaber.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("Çorum Haber", "corum-corumhaber", "https://www.corumhaber.net/rss", ek_dizin="https://www.corumhaber.net/sitemap/sitemap-{AY}.xml"),
]


ALACA = "https://www.alaca.bel.tr/vefat-ve-defin-hizmetleri/"


def baslik_biciminde(s):
    """Kaynak bazı satırları ASCII BÜYÜK yazar ('IBRAHIMKOY KOYU CAMII', 'AZIME DEMIR'): tr_lower I'yı 'ı' yapıp 'Azıme Demır' üretirdi.
    Yalnız-ASCII büyük harf metinde I -> i (diakritik kaynakta zaten yok), sözcük başı I -> İ; karışık yazılmış metin tr_title ile kalır."""
    s = " ".join((s or "").split())
    if s and s.isascii() and s.isupper():
        return " ".join(("İ" + w[1:].lower() if w[0] == "I" else w[0] + w[1:].lower()) for w in s.split())
    return ortak.tr_title(s)


def alaca(ctx):
    baslik, satirlar = oi.tablo(oi.al(ALACA))
    sonuc = []
    for s in satirlar:
        ad = baslik_biciminde(oi.metin(oi.kolon(baslik, s, "Ad Soyad")))
        vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
        defin = oi.tarih(oi.kolon(baslik, s, "Defin Tarihi")) or vef
        cami = oi.kolon(baslik, s, "Camii").strip(" –-")
        vakit = oi.kolon(baslik, s, "Vakit").strip(" –-")
        if not ad or not vef:
            continue
        gun = defin or vef
        yer = baslik_biciminde(cami) if cami else None
        namaz = ", ".join(x for x in (baslik_biciminde(vakit) if vakit else None, yer) if x) or None
        sonuc.append(oi.kayit(IL, "Alaca", "corum-alaca", ad, gun, "Alaca Belediyesi", ALACA, ctx["alindi"], vefat_tarihi=vef,
                              namaz_tarihi=defin if namaz else None, namaz_yeri_vakti=namaz, liste_tarihi=gun))
    return [k for k in sonuc if oi.pencerede(k["liste_tarihi"], ctx["gunler"])]


def main():
    oi.il_calistir(IL, "corum", [("Alaca", alaca)] + oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
