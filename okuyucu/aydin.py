#!/usr/bin/env python3
"""Aydın: Aydın BŞB, Efeler, Nazilli, Kuşadası, Didim'de liste yok; ilçe düzeyinde Söke Belediyesi.
Söke: `soke.bel.tr/vefatedenler?page=N` (10 satır/sayfa): Adı Soyadı, Defin Tarihi, "Yer / Zaman" (mahalle/köy adı; saat çıkarsa namaz alanına).
Gün = defin tarihi. Kullanım: python3 okuyucu/aydin.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Aydın"
SOKE = "https://www.soke.bel.tr/vefatedenler"


def soke(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa)
        liste = []
        for s in satirlar:
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
            defin = oi.tarih(oi.kolon(baslik, s, "Defin Tarihi"))
            yer = oi.kolon(baslik, s, "Yer")
            if not ad or not defin:
                continue
            saatli = bool(re.search(r"\d|namaz|saat", yer, re.I))
            liste.append(oi.kayit(IL, "Söke", "aydin-soke", ad, defin, "Söke Belediyesi", SOKE, ctx["alindi"],
                                  mahalle=None if saatli else (oi.buyuk_ise_title(yer, yer=True) or None),
                                  defin_zamani=defin, namaz_tarihi=defin if saatli else None,
                                  namaz_yeri_vakti=yer if saatli else None, liste_tarihi=defin,
                                  ham={"yer_zaman": yer or None}))
        return liste
    return oi.sayfala(lambda n: SOKE if n == 1 else f"{SOKE}?page={n}", ayristir, ctx["gunler"], azami_sayfa=3)


def main():
    oi.il_calistir(IL, "aydin", [("Söke", soke)])


if __name__ == "__main__":
    main()
