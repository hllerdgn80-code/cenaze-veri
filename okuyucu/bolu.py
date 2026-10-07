#!/usr/bin/env python3
"""Bolu Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: WordPress günlük yazı 'GG.AA.YYYY Vefat İlanı' -> kategori akışı https://www.bolu.bel.tr/category/vefatilanlari/feed/
(son ~10 gün). Her yazıda: <strong>AD SOYAD</strong>, yakın sayımı paragrafı (KVKK gereği ALINMAZ), 'Cenazesi ...' cümlesi.
Cümleden namaz yeri/vakti ve defin yeri çıkarılır. Defin yeri başka ilin adıyla başlıyorsa (ör. 'Çankırı Ilgaz İlçe Mezarlığı')
il_disi_defin işaretlenir. İlçe kaynakta yok -> ilce_belirsiz. Gün = yazı tarihi (ilan günü).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Bolu"
FEED = "https://www.bolu.bel.tr/category/vefatilanlari/feed/"
KAYNAK_AD = "Bolu Belediyesi"
KOK = os.path.join(ortak9.VERI, "bolu")
ATLA = {"merkez", "ilçe", "ilce", "köy", "koy", "belde", "mezarlığı", "mezarlık", "mezarlığa", "mahalle", "asri", "şehir", "sehir"}


def baska_il(defin):
    """Defin yeri 'Çorum İskilip Sorkun Köy Mezarlığı' gibi başka ilin adıyla başlıyorsa 'İl / İlçe' (ya da 'İl') döner."""
    if not defin:
        return None
    w = defin.split()
    il_adi = ortak._ad_bul(ortak.katla(w[0]), ortak.ilce_verisi()["_iller"])
    if not il_adi or ortak.katla(il_adi) == ortak.katla(IL):
        return None
    if len(w) > 1 and ortak.katla(w[1]) not in {ortak.katla(x) for x in ATLA}:
        return f"{il_adi} / {w[1]}"
    return il_adi


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(FEED):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    xml = ortak.indir(FEED, 3.5)
    alindi = ortak.simdi_iso()
    yeni = {}
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        baslik = ortak9.metin(re.search(r"<title>(.*?)</title>", it, re.S).group(1))
        gun = ortak.tarih_iso(baslik.split()[0])
        link = (re.search(r"<link>(.*?)</link>", it) or [None, FEED])[1]
        icerik = re.search(r"<content:encoded><!\[CDATA\[(.*?)\]\]></content:encoded>", it, re.S)
        if not gun or gun not in gl or not icerik:
            continue
        parcalar = re.split(r"<p><strong>(.*?)</strong></p>", icerik.group(1))
        for i in range(1, len(parcalar) - 1, 2):
            ad = ortak9.metin(parcalar[i])
            govde = [ortak9.metin(p) for p in re.findall(r"<p>(.*?)</p>", parcalar[i + 1], re.S)]
            cumle = next((p for p in govde if p.startswith("Cenazesi")), None)
            if not ad or ad.lower() in ("&nbsp;",):
                continue
            namaz, defin = ortak9.cenaze_cumlesi(cumle) if cumle else (None, None)
            ilce_ham = baska_il(defin)
            k = ortak9.kayit("bolu", IL, ortak.tr_title(ad), gun, KAYNAK_AD, link, alindi,
                             ilce=ilce_ham, defin_yeri=defin, namaz_yeri_vakti=namaz,
                             defin_zamani=gun, ham={"cenaze_cumlesi": cumle})
            yeni.setdefault(gun, []).append(k)
    print(f"pencerede {sum(len(v) for v in yeni.values())} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
