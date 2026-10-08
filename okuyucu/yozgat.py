#!/usr/bin/env python3
"""Yozgat: il belediyesinin robots.txt'i `Disallow: /` -> okunmaz. Yalnız ilçe düzeyinde 2 ilçe (her biri ayrı kaynak):
- Sorgun: `sorgun.bel.tr/vefat-edenler` tablo (ad, baba adı, vefat tarihi, vefat yeri). Seyrek (08.10'da son kayıt 30.09).
- Çekerek: `cekerek.bel.tr/vefat-edenler?page=N` aynı şablon (+ açılır ayrıntı). Seyrek (son kayıt 03.10).
"Vefat Yeri" sütunu kaynakta ayrım yapmıyor (mezarlık adı, köy ya da ilçe adı): "mezarlık" geçiyorsa defin_yeri, geçmiyorsa ham'a yazılır.
Gün = vefat tarihi. Kullanım: python3 okuyucu/yozgat.py [--gun 7] [--ilce Sorgun]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Yozgat"


def _macroturk(ctx, ilce, slug, kaynak_ad, url, sayfa, modal=None):
    baslik, satirlar = oi.tablo(sayfa)
    sonuc = []
    for i, s in enumerate(satirlar):
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
        baba = oi.ad_duzelt(oi.kolon(baslik, s, "Baba Adı"))
        vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
        yer = oi.kolon(baslik, s, "Vefat Yeri")
        det = modal[i] if modal and i < len(modal) else ""
        namaz, defin = oi.cenaze_ayikla(det)
        if not ad or not vef:
            continue
        mezarlik = "mezarl" in ortak.tr_lower(yer)
        sonuc.append(oi.kayit(IL, ilce, slug, ad, vef, kaynak_ad, url, ctx["alindi"], anne_baba=baba or None, vefat_tarihi=vef,
                              defin_yeri=defin or (oi.buyuk_ise_title(yer, yer=True) if mezarlik else None),
                              namaz_yeri_vakti=namaz, liste_tarihi=vef,
                              ham={"vefat_yeri": (yer or None) if not mezarlik else None}))
    return sonuc


SORGUN = "https://sorgun.bel.tr/vefat-edenler"
CEKEREK = "https://cekerek.bel.tr/vefat-edenler"


def sorgun(ctx):
    sayfa = oi.al(SORGUN)
    return _macroturk(ctx, "Sorgun", "yozgat-sorgun", "Sorgun Belediyesi", SORGUN, sayfa, oi.modal_govdeleri(sayfa))


def cekerek(ctx):
    sonuc = []
    for n in range(1, 4):
        url = CEKEREK if n == 1 else f"{CEKEREK}?page={n}"
        sayfa = oi.al(url)
        liste = _macroturk(ctx, "Çekerek", "yozgat-cekerek", "Çekerek Belediyesi", CEKEREK, sayfa, oi.modal_govdeleri(sayfa))
        icinde = [k for k in liste if oi.pencerede(k["liste_tarihi"], ctx["gunler"])]
        sonuc.extend(icinde)
        if not icinde:
            break
    return sonuc


def main():
    oi.il_calistir(IL, "yozgat", [("Sorgun", sorgun), ("Çekerek", cekerek)])


if __name__ == "__main__":
    main()
