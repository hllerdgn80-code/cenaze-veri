#!/usr/bin/env python3
"""Bilecik Belediyesi 'Vefat Edenler' okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.bilecik.bel.tr/VefatEdenler; sayfanın kendi çağrısı POST /VefatEdenlerAjax (ay=&yıl=) kart HTML'i döner.
Pencerenin kapsadığı ay(lar) sorgulanır. Kart: ad, ilan tarihi, serbest ilan metni. Metindeki yakın/akraba sayımı KVKK gereği ALINMAZ;
yalnız 'Cenazesi ...' cümlesinden namaz yeri/vakti ve defin yeri çıkarılır. Gün = ilan tarihi. İlçe/mahalle kaynakta ayrı yok -> ilce_belirsiz.
"""
import os, re, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Bilecik"
SAYFA = "https://www.bilecik.bel.tr/VefatEdenler"
AJAX = "https://www.bilecik.bel.tr/VefatEdenlerAjax"
KAYNAK_AD = "Bilecik Belediyesi"
KOK = os.path.join(ortak9.VERI, "bilecik")


def kartlar(html_):
    for b in re.split(r'<div class="card h-100 bg-light mb-3">', html_)[1:]:
        ad = re.search(r'<h5 class="card-title">(.*?)</h5>', b, re.S)
        tarih = re.search(r'<p class="card-text">\s*(\d{1,2}\s+\S+\s+\d{4})\s*</p>', b)
        govde = re.search(r"<small>(.*?)</small>", b, re.S)
        if ad and tarih:
            yield ortak9.metin(ad.group(1)), ortak.tarih_iso(tarih.group(1)), ortak9.metin(govde.group(1)) if govde else ""


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(SAYFA):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    aylar = sorted({(int(g[:4]), int(g[5:7])) for g in gl}, reverse=True)
    o = ortak9.Oturum()
    o.get(SAYFA)
    alindi = ortak.simdi_iso()
    yeni = {}
    for yil, ay in aylar:
        html_ = o.post_form(AJAX, {"ay": ay, "yil": yil}, {"X-Requested-With": "XMLHttpRequest", "Referer": SAYFA})
        for ad, gun, metin in kartlar(html_):
            if not gun or gun not in gl:
                continue
            m = re.search(r"Cenazesi\b.*", metin)
            namaz, defin = ortak9.cenaze_cumlesi(m.group(0)) if m else (None, None)
            k = ortak9.kayit("bilecik", IL, ortak.tr_title(ad), gun, KAYNAK_AD, SAYFA, alindi,
                             defin_yeri=defin, namaz_yeri_vakti=namaz,
                             namaz_tarihi=gun if m and re.search(r"\bbugün\b", ortak.tr_lower(m.group(0))) else None,   # 'Cenazesi bugün' = ilan günü (kapi.py K1)
                             ham={"cenaze_cumlesi": re.sub(r"\s*Belediye Başkanlığı olarak.*$", "", m.group(0)) if m else None})
            yeni.setdefault(gun, []).append(k)
    print(f"pencerede {sum(len(v) for v in yeni.values())} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
