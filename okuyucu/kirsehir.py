#!/usr/bin/env python3
"""Kırşehir Belediyesi cenaze ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.kirsehir.bel.tr/cenaze-ilanlari?page=N (akordeon; en yeni üstte; tarih = ilanın TARİH alanı).
Alınan alanlar: Ad Soyad, Memleketi (ham), Defin Yeri, Tarih, Cenaze Namazı, (Adres alanı alınmaz: taziye/ev adresi olabilir).
KVKK: "Yakını" (ad), "Telefon" ve "Adres" ALINMAZ. Kaynakta ilçe yok -> ilce None + ilce_belirsiz (tahmin yok).
Kullanım: python3 okuyucu/kirsehir.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kırşehir"
URL = "https://www.kirsehir.bel.tr/cenaze-ilanlari"
KAYNAK_AD = "Kırşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kirsehir")
MAKS_SAYFA = 6


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def ayristir(sayfa):
    kayitlar = []
    for blok in re.split(r'<div class="accordion-item', sayfa)[1:]:
        h = {}
        for et, deger in re.findall(r'<span class="fs-4 fw-bold text-primary">\s*([^<:]+?)\s*:\s*</span>\s*<span class="text-primary">(.*?)</span>', blok, re.S):
            h[ortak.tr_lower(et)] = metin(deger)
        if h.get("ad soyad"):
            kayitlar.append(h)
    return kayitlar


def mahalle_cikar(adres):
    m = re.match(r"^(.*?)\s+MAH(?:ALLES[İI])?\b\.?", adres or "", re.I)
    return m.group(1).strip() if m and m.group(1).strip() else None


def kayda_cevir(h, gun, url, alindi):
    ad = h["ad soyad"]
    mahalle = None   # "Adres" taziye/ev adresi olabilir: ALINMAZ
    defin = h.get("defin yeri") or None
    return {
        "id": ortak.kayit_id("kirsehir", ad, gun, f"{defin or ''}|{h.get('memleketi', '')}"),
        "il": IL, "ilce": None,
        "mahalle": ortak.tr_title(mahalle) if mahalle else None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(defin) if defin else None,
        "defin_zamani": gun,
        "namaz_tarihi": gun,
        "namaz_yeri_vakti": h.get("cenaze namazı") or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"memleketi": h.get("memleketi") or None, "defin_yeri": defin,
                "cenaze_namazi": h.get("cenaze namazı") or None, },
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
            g = ortak.tarih_iso(h.get("tarih"))
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
