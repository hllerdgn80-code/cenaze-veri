#!/usr/bin/env python3
"""Antalya: Antalya BŞB'nin listesi yok; ilçe düzeyinde Alanya Belediyesi.
Alanya: `alanya.bel.tr/Aramizdan-ayrilanlar` tek sayfa (~43 ilan): ad, tarih, büyük harfli ilan metni. Metinden yalnız
"X MAHALLESİNDEN" (mahalle) ve "CENAZESİ ..." cümlesi alınır; yakın adları ve "TAZİYE YERİ" ALINMAZ. Gün = ilan tarihi.
Kullanım: python3 okuyucu/antalya.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Antalya"
ALANYA = "https://www.alanya.bel.tr/Aramizdan-ayrilanlar"


def alanya(ctx):
    sayfa = oi.al(ALANYA)
    ogeler = re.findall(r'<span class="text">([\s\S]*?)</span>\s*<span class="date">([\s\S]*?)</span>\s*<span class="description">([\s\S]*?)</span>', sayfa)
    if not ogeler:
        raise RuntimeError("ilan bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for ad, tar, acik in ogeler:
        ad = oi.ad_duzelt(ad)
        gun = oi.tarih(oi.metin(tar))
        txt = oi.metin(acik)
        namaz, defin = oi.cenaze_ayikla(txt)
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        sonuc.append(oi.kayit(IL, "Alanya", "antalya-alanya", ad, gun, "Alanya Belediyesi", ALANYA, ctx["alindi"],
                              il_disi_metin=txt, mahalle=oi.mahalle_ayikla(txt), defin_yeri=defin, namaz_tarihi=gun if namaz else None,
                              namaz_yeri_vakti=namaz, liste_tarihi=gun, ham={"ilan_tarihi": gun}))
    return sonuc


def main():
    oi.il_calistir(IL, "antalya", [("Alanya", alanya)])


if __name__ == "__main__":
    main()
