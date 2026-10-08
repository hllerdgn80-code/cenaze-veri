#!/usr/bin/env python3
"""Kocaeli Büyükşehir Belediyesi vefat listesi okuyucusu (yalnız standart kütüphane).
Kaynak: ebelediye.kocaeli.bel.tr/sosyalhizmetler/vefatlistesi -- tarih parametresi YOK, yalnız güncel liste
(son ~2 günün defin kayıtları). Önceki günler kendi biriktirdiğimiz dosyalardan tamamlanır (ortak.liste_birikim).
Kullanım: python3 okuyucu/kocaeli.py
"""
import html, os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kocaeli"
URL = "https://ebelediye.kocaeli.bel.tr/sosyalhizmetler/vefatlistesi"
KAYNAK_AD = "Kocaeli Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kocaeli")
BASLIKLAR = ["ad", "soyad", "mezarlik", "cami", "vakit", "neden", "olum", "defin"]


def ayristir(sayfa):
    govde = sayfa[sayfa.find("<tbody>"):]
    kayitlar = []
    for tr in re.findall(r"<tr>(.*?)</tr>", govde, re.S):
        h = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in re.findall(r"<td>(.*?)</td>", tr, re.S)]
        if len(h) == len(BASLIKLAR):
            kayitlar.append(dict(zip(BASLIKLAR, h)))
    return kayitlar


def nakil_coz(cami):
    """'AKYAZI/SAKARYA NAKİL' -> 'Sakarya / Akyazı'; 'ÇANKIRI NAKİL' -> 'Çankırı'; 'THY KEŞAP/GİRESUN NAKİL' -> 'Giresun / Keşap'.
    Nakil değilse None."""
    if not re.search(r"\bNAK[İI]L\b", cami, re.I):
        return None
    v = re.sub(r"\s*\bNAK[İI]L\b", "", cami, flags=re.I).strip()
    v = re.sub(r"^THY\s+", "", v, flags=re.I)        # havayoluyla nakil öneki
    p = [x.strip() for x in v.split("/") if x.strip()]
    return " / ".join(reversed(p)) or None       # kaynakta 'ilçe/il'; ortak.ilce_coz 'il / ilçe' bekler


def cami_ilcesi(cami):
    """Cami adresinin sonundaki ilçe adı (Kocaeli ilçe listesinden, tam sözcük). Bulunamazsa None."""
    if "/" not in cami:
        return None
    adres = cami.split("/", 1)[1]
    bulunan = []
    for ilce in ortak.ilce_listesi(IL):
        if re.search(rf"(?<![a-z0-9]){ortak.katla(ilce)}(?![a-z0-9])", ortak.katla(adres)):
            bulunan.append(ilce)
    return bulunan[0] if len(bulunan) == 1 else None


def kayda_cevir(h, gun, alindi):
    ad = f'{h["ad"]} {h["soyad"]}'.strip()
    vefat, defin = ortak.tarih_iso(h["olum"]), ortak.tarih_iso(h["defin"])
    cami, vakit = h["cami"], h["vakit"]
    cami_temiz = re.sub(r"\s*/\s*null\s*$", "", cami)    # kaynakta 'CAMİİ / null' diye geliyor
    nakil = nakil_coz(cami)
    if nakil:
        ilce_ham, cami_yeri = nakil, None
        defin_yeri = "Nakil: " + ortak.tr_title(nakil).replace(" / ", " / ", 1)
    else:
        # cami alanı "CAMİ ADI / MAHALLE SOKAK NO İLÇE" biçiminde: sokak/no adresi yayımlanmaz (kapi.py K4), yalnız cami adı
        ilce_ham, cami_yeri = cami_ilcesi(cami), (cami_temiz.split("/")[0].strip() or None)
        defin_yeri = h["mezarlik"] or None
    vakit_temiz = None if re.fullmatch(r"NAK[İI]L", vakit, re.I) else (vakit or None)
    return {
        "id": ortak.kayit_id("kocaeli", ad, vefat or gun, f"{defin or ''}|{cami}|{h['mezarlik']}"),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,   # cami adresinden ya da nakil yerinden
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None,       # kaynakta yok
        "yas": None,             # kaynakta yok
        "dogum_tarihi": None,    # kaynakta yok
        "vefat_tarihi": vefat,
        "defin_yeri": defin_yeri,
        "defin_zamani": defin,   # kaynak yalnız defin TARİHİ verir
        "namaz_tarihi": None,
        "namaz_yeri_vakti": " – ".join(x for x in (ortak.tr_title(vakit_temiz) if vakit_temiz else None, cami_yeri) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": URL,
        "alindi": alindi,
        # ölüm nedeni sağlık verisi olduğundan bilerek alınmaz
        "ham": {"ad": h["ad"], "soyad": h["soyad"], "mezarlik": h["mezarlik"], "cami": cami.split("/")[0].strip(), "vakit": vakit,
                "olum_tarihi": h["olum"], "defin_tarihi": h["defin"],
                "ilce_kaynagi": "nakil_alani" if nakil else ("cami_adresi" if ilce_ham else None)},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today().isoformat()
    ham = ayristir(ortak.indir(URL))
    alindi = ortak.simdi_iso()
    yeni = [kayda_cevir(h, bugun, alindi) for h in ham]
    gunler, by_gun = ortak.liste_birikim(KOK, IL, bugun, yeni)
    for g in gunler:
        if by_gun[g] or os.path.exists(os.path.join(KOK, f"{g}.json")):
            ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt" + (f" (sayfada {len(ham)} satır)" if g == bugun else ""))
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
