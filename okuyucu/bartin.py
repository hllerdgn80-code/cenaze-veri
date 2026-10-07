#!/usr/bin/env python3
"""Bartın Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.bartin.bel.tr/vefat-ilanlari (akordeon; sayfada en yeni ~15 ilan, kalanı 'Daha fazla göster').
Alanlar: vefat tarihi, ad, baba adı, mahalle, doğum tarihi, namaz yeri/vakti, defin yeri. İlçe kaynakta yok -> ilce_belirsiz.
Sayfa yalnız son ilanları verdiği için gün dosyaları günlük çalıştıkça birikir. Gün = vefat tarihi.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Bartın"
URL = "https://www.bartin.bel.tr/vefat-ilanlari"
KAYNAK_AD = "Bartın Belediyesi"
KOK = os.path.join(ortak9.VERI, "bartin")


def alanlar(blok):
    b = re.sub(r"<(?:p|br|div|h5)[^>]*>", "\n", blok)
    b = ortak9.metin(b.replace("\n", " | "))
    d = {}
    for et, deger in re.findall(r"(Vefat Tarihi|Vefat Edenin Adı Soyadı|Baba Adı|Mahalle|Doğum Tarihi|"
                                r"Namazın kılınacağı yer|Namazın kılınacağı vakit|Defin yeri)\s*:\s*(.*?)(?=\s*\|)", b):
        d[et] = deger.strip()
    return d


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    sayfa = ortak.indir(URL, 3.5)
    alindi = ortak.simdi_iso()
    yeni = {}
    for blok in re.split(r'<span class="card" id="faqitem-top-', sayfa)[1:]:
        blok = blok.split("Daha fazla göster")[0]
        d = alanlar(blok)
        ad = d.get("Vefat Edenin Adı Soyadı")
        gun = ortak.tarih_iso(d.get("Vefat Tarihi"))
        if not (ad and gun):
            continue
        yer, vakit = d.get("Namazın kılınacağı yer"), d.get("Namazın kılınacağı vakit")
        k = ortak9.kayit("bartin", IL, ortak.tr_title(ad), gun, KAYNAK_AD, URL, alindi,
                         ek_id=d.get("Baba Adı", ""), mahalle=ortak.tr_title(d["Mahalle"]) if d.get("Mahalle") else None,
                         anne_baba=ortak.tr_title(d["Baba Adı"]) if d.get("Baba Adı") else None,
                         dogum_tarihi=ortak.tarih_iso(d.get("Doğum Tarihi")), vefat_tarihi=gun,
                         defin_yeri=ortak.tr_title(d["Defin yeri"]) if d.get("Defin yeri") else None,
                         namaz_yeri_vakti=" – ".join(ortak.tr_title(x) for x in (vakit, yer) if x) or None,
                         ham={"baba": d.get("Baba Adı"), "namaz_yeri": yer, "namaz_vakti": vakit})
        if gun in gl:
            yeni.setdefault(gun, []).append(k)
    print(f"pencerede {sum(len(v) for v in yeni.values())} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
