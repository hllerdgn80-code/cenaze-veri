#!/usr/bin/env python3
"""Kütahya Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.kutahya.bel.tr/vefat2.asp?tarih=G.A.YYYY (gün sayfası; vefatlar.asp'deki "TARİHLİ VEFAT İLANLARI" bağlantıları). Son 7 gün.
Her kart: ad (başlık), serbest ilan metni (YAKIN/AKRABA adları içerir -> ALINMAZ), seçenek satırları: saat ikonu = namaz vakti, ay ikonu = cami,
harita ikonu = mezarlık. Yalnız ad + vakit + cami + mezarlık alınır. Metinde "BUGÜN" yazar: namaz günü = sayfanın günü ("YARIN" ise +1).
İlçe kaynakta yok (köy/cami adındaki ilçe adları çıkarılmaz) -> ilce_belirsiz. robots.txt yok (404).
Kullanım: python3 okuyucu/kutahya.py
"""
import os, re, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Kütahya"
KOK_URL = "https://www.kutahya.bel.tr/"
KAYNAK_AD = "Kütahya Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kutahya")


def gun_url(gun):
    y, a, g = gun.split("-")
    return f"{KOK_URL}vefat2.asp?tarih={int(g)}.{int(a)}.{y}"


def ayristir(sayfa):
    sonuc = []
    for blok in re.split(r'<div class="pricing">', sayfa)[1:]:
        ad = re.search(r'<div class="title"><a[^>]*>(.*?)</a>', blok, re.S)
        if not ad:
            continue
        ilk = re.search(r'<div class="bottom-box">(.*?)</div>', blok, re.S)
        metin = ortak_ek.metin(ilk.group(1)) if ilk else ""
        sec = {}
        for ikon, deger in re.findall(r'<li class="active"><span><i class="fa fa-([\w-]+)"></i></span>(.*?)</li>', blok, re.S):
            sec[ikon] = ortak_ek.metin(deger)
        sonuc.append({"ad": ortak_ek.metin(ad.group(1)), "vakit": sec.get("clock-o"), "cami": sec.get("moon-o"),
                      "mezarlik": sec.get("map-marker"), "yarin": bool(re.search(r"\bYARIN\b", metin.upper().replace("İ", "I")))})
    return sonuc


def kayda_cevir(r, gun, url, alindi):
    namaz_gunu = gun
    if r["yarin"]:
        namaz_gunu = (datetime.strptime(gun, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, url, alindi)
    k.update(
        id=ortak.kayit_id("kutahya", r["ad"], gun, (r["cami"] or "") + "|" + (r["mezarlik"] or "")),
        ad_soyad=ortak.tr_title(r["ad"]),
        defin_yeri=ortak.tr_title(r["mezarlik"]) if r["mezarlik"] else None,
        defin_zamani=namaz_gunu,
        namaz_tarihi=namaz_gunu,
        namaz_yeri_vakti=" - ".join(x for x in (ortak.tr_title(r["cami"]) if r["cami"] else None, r["vakit"]) if x) or None,
        liste_tarihi=gun,
        ham={"vakit": r["vakit"], "cami": r["cami"], "mezarlik": r["mezarlik"]},
    )
    return k


def main():
    if not ortak.robots_izin(KOK_URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    alindi = ortak.simdi_iso()
    by_gun = {}
    for gun in reversed(gunler):
        url = gun_url(gun)
        sayfa = ortak.indir(url)
        if 'class="pricing"' not in sayfa and "Vefat İlanları" not in sayfa:
            raise RuntimeError(f"{gun}: beklenen sayfa düzeni yok")
        liste = [kayda_cevir(r, gun, url, alindi) for r in ayristir(sayfa)]
        by_gun[gun] = list({k["id"]: k for k in liste}.values())
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
