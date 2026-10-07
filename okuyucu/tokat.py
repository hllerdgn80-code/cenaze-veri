#!/usr/bin/env python3
"""Tokat Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: sitenin kendi herkese açık API'si https://client-api.tokat.bel.tr/api/public/obituaries?page=1&limit=60
(tokat.bel.tr/robots.txt bu yolu açıkça 'Allow: /api/public/obituaries' ile serbest bırakır; client-api alan adında robots.txt yok).
Sayfa (www.tokat.bel.tr/vefat-edenler) Nuxt tabanlı, liste bu API'den gelir. Alanlar: ad, deathDate (ilan/vefat günü), cami (funeralLocation),
mezarlık (cemetery; çoğu kayıtta köy/ilçe adı içerir), namaz vakti (prayerTime).
ALINMAZ (KVKK): relatives (yakınları), phone, address, description. İlçe kaynakta ayrı alan değil: cami/mezarlık adından ÇIKARILMAZ -> ilce_belirsiz.
Kullanım: python3 okuyucu/tokat.py
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Tokat"
SAYFA_URL = "https://www.tokat.bel.tr/vefat-edenler"
API = "https://client-api.tokat.bel.tr/api/public/obituaries?page=1&limit=60"
KAYNAK_AD = "Tokat Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "tokat")


def kayda_cevir(o, alindi):
    gun = (o.get("deathDate") or "")[:10]
    ad = " ".join((o.get("fullName") or "").split())
    if not ad or len(gun) != 10:
        return None
    cami = o.get("funeralLocation") or None
    mezarlik = o.get("cemetery") or None
    vakit = o.get("prayerTime") or None
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, SAYFA_URL, alindi)
    k.update(
        id=ortak.kayit_id("tokat", ad, gun, o.get("id") or ""),
        ad_soyad=ortak.tr_title(ad),
        vefat_tarihi=gun,
        defin_yeri=mezarlik,
        defin_zamani=gun,
        namaz_tarihi=gun,
        namaz_yeri_vakti=" - ".join(x for x in (cami, vakit) if x) or None,
        liste_tarihi=gun,
        ham={"cami": cami, "mezarlik": mezarlik, "namaz_vakti": vakit, "kaynak_id": o.get("id"),
             "olusturma": o.get("createdAt")},
    )
    return k


def main():
    if not ortak.robots_izin(SAYFA_URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    d = json.loads(ortak.indir(API))
    if not d.get("success") or "data" not in d:
        raise RuntimeError("API beklenen yapıda değil: " + str(list(d)[:5]))
    alindi = ortak.simdi_iso()
    gunler = ortak_ek.son_gunler(7)
    by_gun = {}
    for o in d["data"]:
        k = kayda_cevir(o, alindi)
        if k and k["liste_tarihi"] in gunler:
            by_gun.setdefault(k["liste_tarihi"], []).append(k)
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
