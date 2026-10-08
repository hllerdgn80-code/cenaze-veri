#!/usr/bin/env python3
"""Artvin: yalnız ilçe düzeyinde kaynak var -> Şavşat Belediyesi (il belediyesinde liste yok).
Şavşat: `savsat.bel.tr/cenaze-ilanlari` kart listesi (son 10 ilan). Kart: ilan tarihi, köy/mahalle, ad, "Vefat: GG.AA.YYYY",
metin ("Cenazesi GG.AA.YYYY tarihinde X Köyü bölgesinde defnedilecektir"). Yalnız ad, köy, tarihler, defin yeri alınır.
TLS: sunucu ara sertifikayı göndermiyor -> sertifika/ilce-zincir.pem (doğrulama AÇIK). robots.txt: /arama kapalı, liste serbest.
Sayfa yalnız son ilanları gösterir: gün dosyaları birleştirilerek (kayıt silinmez) biriktirilir.
Kullanım: python3 okuyucu/artvin.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Artvin"
SAVSAT_URL = "https://www.savsat.bel.tr/cenaze-ilanlari"


def savsat(ctx):
    sb = oi.ssl_ilce()
    sayfa = oi.al(SAVSAT_URL, sb)
    bloklar = re.split(r'<div class="death-list-card">', sayfa)[1:]
    if not bloklar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for b in bloklar:
        spans = [oi.metin(x) for x in re.findall(r"<span>\s*<i[^>]*></i>([\s\S]*?)</span>", b)]
        ad = oi.ad_duzelt((re.search(r"<h2>([\s\S]*?)</h2>", b) or [None, ""])[1])
        p = oi.metin((re.search(r"<p>([\s\S]*?)</p>", b) or [None, ""])[1])
        vef = oi.tarih((re.search(r"Vefat:\s*([\d./-]+)", b) or [None, ""])[1])
        ilan = oi.tarih(spans[0]) if spans else None
        koy = spans[1] if len(spans) > 1 else None
        m = re.search(r"Cenazesi\s+([\d./]+)\s+tarihinde", p)
        defin = oi.tarih(m.group(1)) if m else None
        gun = defin or vef or ilan
        if not ad or not gun:
            continue
        k = oi.kayit(IL, "Şavşat", "artvin-savsat", ad, gun, "Şavşat Belediyesi", SAVSAT_URL, ctx["alindi"],
                     ek_id=f"{vef}|{koy}",
                     mahalle=ortak.tr_title(koy) if koy else None,
                     vefat_tarihi=vef, defin_yeri=ortak.tr_title(koy) if koy else None, defin_zamani=defin,
                     liste_tarihi=gun, ham={"ilan_tarihi": ilan, "bolge": koy})
        sonuc.append(k)
    return sonuc


def main():
    oi.il_calistir(IL, "artvin", [("Şavşat", savsat)])


if __name__ == "__main__":
    main()
