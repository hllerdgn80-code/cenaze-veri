#!/usr/bin/env python3
"""Rize Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.rize.bel.tr/vefat-edenler?page=N (HTML tablo kartları, en yeni üstte; sayfa başına 6 kayıt).
Alanlar: ad (h3), Cenaze Tarihi, Mahalle / Köy, Namaz Yeri ve Saati, Defin Yeri. Tarih = cenaze tarihi (liste_tarihi).
KVKK: "Yakınları" (yakın listesi, taziye telefonu/adı) ALINMAZ. Kaynakta ilçe yok -> ilce None + ilce_belirsiz.
Kullanım: python3 okuyucu/rize.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Rize"
URL = "https://www.rize.bel.tr/vefat-edenler"
KAYNAK_AD = "Rize Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "rize")
MAKS_SAYFA = 8


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def ayristir(sayfa):
    kayitlar = []
    for tablo in re.findall(r"<table>(.*?)</table>", sayfa, re.S):
        ad = re.search(r"<h3>(.*?)</h3>", tablo, re.S)
        if not ad:
            continue
        h = {"ad": metin(ad.group(1))}
        for et, deger in re.findall(r"<th>\s*([^<:]+?)\s*:\s*</th>\s*<td>(.*?)</td>", tablo, re.S):
            h[ortak.tr_lower(et)] = metin(deger)      # 'yakınları' okunur ama kayda GİRMEZ
        kayitlar.append(h)
    return kayitlar


def kayda_cevir(h, gun, url, alindi):
    mah = h.get("mahalle / köy") or None
    namaz, defin = h.get("namaz yeri ve saati") or None, h.get("defin yeri") or None
    return {
        "id": ortak.kayit_id("rize", h["ad"], gun, f"{mah or ''}|{defin or ''}"),
        "il": IL, "ilce": None,
        "mahalle": ortak.tr_title(mah) if mah else None,   # 'Mahalle / Köy' alanı olduğu gibi (ör. 'Hamzabey Mahallesi', 'Veliköy Köyü')
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(defin) if defin else None,
        "defin_zamani": gun, "namaz_tarihi": gun,
        "namaz_yeri_vakti": ortak.tr_title(namaz) if namaz else None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"mahalle_koy": mah, "namaz": namaz, "defin": defin},
    }


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {g: [] for g in gunler}
    alindi = ortak.simdi_iso()
    gor = set()
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = f"{URL}?page={sayfa_no}"
        try:
            ham = ayristir(ortak.indir(url))
        except Exception as e:
            print(f"HATA sayfa {sayfa_no}: {e}", file=sys.stderr)
            break
        if not ham:
            break
        tarihler = []
        for h in ham:
            g = ortak.tarih_iso(h.get("cenaze tarihi"))
            tarihler.append(g)
            if g in by_gun:
                k = kayda_cevir(h, g, url, alindi)
                if k["id"] not in gor:
                    gor.add(k["id"])
                    by_gun[g].append(k)
        if all(t and t < gunler[-1] for t in tarihler):
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
