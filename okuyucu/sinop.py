#!/usr/bin/env python3
"""Sinop Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.sinop.bel.tr/vefat-ilanlar/?p=N (kartlar: tarih, AD SOYAD, serbest metin açıklama; en yeni üstte, sayfa başına 10).
Açıklamadan yalnız şunlar çıkarılır: namaz vakti ("ÖĞLE NAMAZI"), cami adı, mezarlık adı. Yakın listesi, meslek/kurum,
evden alınış adresi ve telefonlar ALINMAZ (ham alanda da saklanmaz). Kaynakta ilçe yok -> ilce None + ilce_belirsiz.
Kullanım: python3 okuyucu/sinop.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Sinop"
URL = "https://www.sinop.bel.tr/vefat-ilanlar/"
KAYNAK_AD = "Sinop Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "sinop")
MAKS_SAYFA = 6
U = "A-ZÇĞİÖŞÜa-zçğıöşü"


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def ayristir(sayfa):
    kayitlar = []
    for kart in re.findall(r'<div class="vef-card">(.*?)<button type="button" class="vef-btn-detay"', sayfa, re.S):
        tarih = re.search(r'class="vef-tarih">(.*?)</span>', kart, re.S)
        ad = re.search(r'class="vef-isim">(.*?)</div>', kart, re.S)
        ac = re.search(r'class="vef-aciklama">(.*?)</div>', kart, re.S)
        if ad and tarih:
            m = re.search(r"\d{2}\.\d{2}\.\d{4}", metin(tarih.group(1)))
            kayitlar.append({"ad": metin(ad.group(1)), "tarih": ortak.tarih_iso(m.group(0)) if m else None,
                             "aciklama": metin(ac.group(1)) if ac else ""})
    return kayitlar


DUR = {"CENAZESİ", "CENAZESI", "BUGÜN", "EVİNDEN", "EVINDEN", "ALINARAK", "SONRA", "TOPRAĞA", "VERİLECEKTİR", "ÖĞLE", "İKİNDİ",
       "CUMA", "NAMAZI", "NAMAZ", "VE", "İLE", "SAAT", "YAKINLARINA", "KILINACAK", "GETİRİLECEK", "DEFNEDİLECEKTİR", "DEFİN"}


def _dur(w):
    return w in DUR or re.search(r"(NDAN|NDEN|ARAK|EREK|ECEK|ACAK|ECEKTİR|ACAKTIR)$", w) is not None or bool(re.search(r"\d", w))


def _geri_topla(parca, bitis, en_cok=3):
    """parca[:bitis] metninin sonundan geriye doğru, durdurucuya kadar en çok 'en_cok' sözcük."""
    kelimeler = parca[:bitis].replace(",", " ").split()
    alinan = []
    for w in reversed(kelimeler):
        if _dur(w) or len(alinan) >= en_cok:
            break
        alinan.append(w)
    return " ".join(reversed(alinan))


def ayikla(aciklama):
    """-> (namaz vakti + cami, mezarlık) ; yalnız tanımlı kalıplar."""
    a = aciklama.replace("’", "'")
    c = re.search(r"CENAZES[İI]", a)
    parca = a[c.start():] if c else a
    parca = re.split(r"BELED[İI]YE BA[ŞS]KANLI", parca)[0]
    vakit = re.search(r"\b(SABAH|ÖĞLE|İKİNDİ|AKŞAM|YATSI|CUMA|CENAZE)\s+NAMAZ", parca)
    cami = re.search(rf"CAM[İI]İ?\b", parca)
    mezar = re.search(r"MEZARLI[ĞG]I", parca)
    cami_ad = (_geri_topla(parca, cami.start()) + " " + cami.group(0)).strip() if cami else None
    mezar_ad = _geri_topla(parca, mezar.start()) if mezar else ""
    namaz = " – ".join(x for x in (vakit and vakit.group(1) + " Namazı", cami_ad if cami_ad and cami_ad != cami.group(0) else None) if x) or None
    return namaz, (mezar_ad + " Mezarlığı") if mezar_ad else None


def kayda_cevir(h, url, alindi):
    namaz, mezarlik = ayikla(h["aciklama"])
    gun = h["tarih"]
    return {
        "id": ortak.kayit_id("sinop", h["ad"], gun, mezarlik or ""),
        "il": IL, "ilce": None, "mahalle": None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(mezarlik) if mezarlik else None,
        "defin_zamani": None, "namaz_tarihi": None,
        "namaz_yeri_vakti": ortak.tr_title(namaz) if namaz else None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"namaz": namaz, "mezarlik": mezarlik},
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
        url = URL if sayfa_no == 1 else f"{URL}?p={sayfa_no}"
        try:
            ham = ayristir(ortak.indir(url))
        except Exception as e:
            print(f"HATA sayfa {sayfa_no}: {e}", file=sys.stderr)
            break
        if not ham:
            break
        for h in ham:
            if h["tarih"] in by_gun:
                k = kayda_cevir(h, url, alindi)
                if k["id"] not in gor:
                    gor.add(k["id"])
                    by_gun[h["tarih"]].append(k)
        if all(h["tarih"] and h["tarih"] < gunler[-1] for h in ham):
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
