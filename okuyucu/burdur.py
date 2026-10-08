#!/usr/bin/env python3
"""Burdur: il belediyesinin listesi yok; ilçe düzeyinde Bucak Belediyesi.
Bucak: `bucak.bel.tr/vefat-edenler` kartlar (sayfa başına ~18, JavaScript sayfalama): ad, kısa ilan metni ("X köyünden ... *AD(73)* vefat etmiştir.
Cenaze namazı ... defnedilecektir."), Tarih. YAKINI, TELEFON ve TAZİYE ADRESİ ALINMAZ. Gün = ilan tarihi. İlk sayfa pencereyi (7 gün) kapsar.
Kullanım: python3 okuyucu/burdur.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Burdur"
BUCAK = "https://bucak.bel.tr/vefat-edenler"


def bucak(ctx):
    sayfa = oi.al(BUCAK)
    kartlar = re.split(r'<div class="card h-100 shadow-sm vefat-card">', sayfa)[1:]
    if not kartlar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for b in kartlar:
        ad = oi.ad_duzelt((re.search(r'card-title[^>]*>\s*<a[^>]*>([\s\S]*?)</a>', b) or [None, ""])[1])
        p = oi.metin((re.search(r'<p class="card-text[^>]*>([\s\S]*?)</p>', b) or [None, ""])[1])
        gun = oi.tarih((re.search(r"<strong>Tarih:</strong>\s*([\d./-]+)", b) or [None, ""])[1])
        yas = re.search(r"\((\d{1,3})\)", p)
        namaz, defin = oi.cenaze_ayikla(p)
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        sonuc.append(oi.kayit(IL, "Bucak", "burdur-bucak", ad, gun, "Bucak Belediyesi", BUCAK, ctx["alindi"],
                              il_disi_metin=p, mahalle=oi.mahalle_ayikla(p), yas=int(yas.group(1)) if yas else None, defin_yeri=defin,
                              namaz_tarihi=gun if namaz else None, namaz_yeri_vakti=namaz, liste_tarihi=gun,
                              ham={"ilan_tarihi": gun}))
    return sonuc


def main():
    oi.il_calistir(IL, "burdur", [("Bucak", bucak)])


if __name__ == "__main__":
    main()
