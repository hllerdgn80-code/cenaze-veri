#!/usr/bin/env python3
"""Erzurum: yalnız ilçe düzeyinde kaynak var -> Uzundere Belediyesi (seyrek: haftada ~2 ilan; il belediyesinde liste yok).
Uzundere: `uzundere.bel.tr/?p=vefat` "VEFAT & TAZİYE İLANI" kartları: "Vefat Tarihi: YYYY-AA-GG", ad, açılır detay metni
(serbest: mahalle, cami, vakit). Detay metnindeki oğulları/yakın adları ve TELEFONLAR ALINMAZ; yalnız "X mahallesinden"
ve "Cenazesi ..." cümlesi. robots.txt yok. Sayfa tek (15 kayıt): gün dosyaları birleştirilerek biriktirilir.
Kullanım: python3 okuyucu/erzurum.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Erzurum"
URL = "https://www.uzundere.bel.tr/?p=vefat"


def uzundere(ctx):
    sayfa = oi.al(URL)
    eslesme = re.findall(r"Vefat Tarihi:\s*(\d{4}-\d\d-\d\d)</span>[\s\S]*?<h3[^>]*>([^<]+)</h3>"
                         r"[\s\S]*?<div class=\"vefat-detay-panel\"[^>]*>([\s\S]*?)</div>", sayfa)
    if not eslesme:
        raise RuntimeError("ilan bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for vef, ad, panel in eslesme:
        ad = oi.ad_duzelt(ad)
        txt = re.sub(r"\\+'", "'", oi.metin(panel))
        txt = re.sub(r"\\+", "", txt)
        vef = oi.tarih(vef)
        namaz, defin = oi.cenaze_ayikla(txt)
        defin_gun = oi.tarih(namaz or "")
        gun = defin_gun or vef
        if not ad or not gun:
            continue
        sonuc.append(oi.kayit(IL, "Uzundere", "erzurum-uzundere", ad, gun, "Uzundere Belediyesi", URL, ctx["alindi"],
                              ek_id=vef or "", il_disi_metin=txt, mahalle=oi.mahalle_ayikla(txt), vefat_tarihi=vef, defin_yeri=defin,
                              defin_zamani=defin_gun, namaz_tarihi=defin_gun, namaz_yeri_vakti=namaz,
                              liste_tarihi=gun, ham={}))
    return sonuc


def main():
    oi.il_calistir(IL, "erzurum", [("Uzundere", uzundere)])


if __name__ == "__main__":
    main()
