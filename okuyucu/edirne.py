#!/usr/bin/env python3
"""Edirne Belediyesi "Kaybettiklerimiz" listesi okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.edirne.bel.tr/hizmet/vefat[?sayfa=N] (sunucuda üretilen HTML tablo, sayfa başına 10 kayıt, en yeni üstte).
Sütunlar: Defin Tarihi, Ad Soyad, Yaşı, Meslek, Cenaze Yeri (cami), Namaz (vakit), Mezarlık.
MESLEK alınmaz (kaynakta "ENGELLİ" gibi sağlık durumu bildiren değerler var, KVKK). Kaynakta İLÇE YOK (cami/mezarlık adında köy/ilçe adı geçse de
çıkarılmaz): ilce None + ilce_belirsiz. Kaynak yalnız Edirne Belediyesi (merkez) kayıtlarını içerir.
Kullanım: python3 okuyucu/edirne.py
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Edirne"
URL = "https://www.edirne.bel.tr/hizmet/vefat"
KAYNAK_AD = "Edirne Belediyesi"
BEKLE = 3.5
MAKS_SAYFA = 5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "edirne")
BASLIKLAR = ["defin", "ad", "yas", "meslek", "cami", "namaz", "mezarlik"]


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    i = sayfa.find("<table")
    if i < 0:
        raise RuntimeError("tablo bulunamadı (sayfa düzeni değişmiş olabilir)")
    blok = sayfa[i:sayfa.find("</table>", i)]
    kayitlar = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", blok.split("<tbody>", 1)[-1], re.S):
        h = [metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == len(BASLIKLAR):
            kayitlar.append(dict(zip(BASLIKLAR, h)))
    return kayitlar


def kayda_cevir(h, url, alindi):
    defin = ortak.tarih_iso(h["defin"])
    yer_vakit = " – ".join(x for x in (ortak.tr_title(h["namaz"]) or None, ortak.tr_title(h["cami"]) or None) if x) or None
    return {
        "id": ortak.kayit_id("edirne", h["ad"], defin or "", f'{h["yas"]}|{h["cami"]}|{h["mezarlik"]}'),
        "il": IL,
        "ilce": None,                       # kaynakta yok
        "mahalle": None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": None,                  # kaynakta yok
        "yas": int(h["yas"]) if h["yas"].isdigit() else None,
        "dogum_tarihi": None,
        "vefat_tarihi": None,               # kaynakta yok
        "defin_yeri": ortak.tr_title(h["mezarlik"]) or None,
        "defin_zamani": defin,              # kaynak defin TARİHİ verir; saat yok (namaz vakti ayrı)
        "namaz_tarihi": defin,              # namaz defin günü kılınır (kaynak ayrı namaz tarihi vermez)
        "namaz_yeri_vakti": yer_vakit,
        "liste_tarihi": defin,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"defin": h["defin"], "yas": h["yas"] or None, "cami": h["cami"] or None, "namaz": h["namaz"] or None,
                "mezarlik": h["mezarlik"] or None},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(7)]
    by_gun = {g: [] for g in gunler}
    goruldu = set()
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = URL if sayfa_no == 1 else f"{URL}?sayfa={sayfa_no}"
        ham = ayristir(ortak.indir(url, BEKLE))
        alindi = ortak.simdi_iso()
        en_eski = None
        for h in ham:
            k = kayda_cevir(h, url, alindi)
            g = k["liste_tarihi"]
            if not g:
                continue
            en_eski = g if en_eski is None else min(en_eski, g)
            if g in by_gun and k["id"] not in goruldu:
                goruldu.add(k["id"]); by_gun[g].append(k)
        if not ham or en_eski is None or en_eski < gunler[-1]:
            break
    for g in gunler:
        ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
