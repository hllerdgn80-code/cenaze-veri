#!/usr/bin/env python3
"""Osmaniye Belediyesi vefat listesi okuyucusu (WordPress RSS; yalnız standart kütüphane).
Kaynak: https://osmaniye-bld.gov.tr/kategori/vefaat/feed/ (günde 1 yazı "04 EKİM 2026 PAZAR"; yazıda numaralı
"Cenaze Bilgi Sistemi" blokları: Adı & Soyadı, Taziye Adresi, Defin Yeri). Feed son 10 yazıyı taşır.
Bir yazıdan birden çok kayıt çıkar. KVKK: TAZİYE ADRESİ ALINMAZ (kişisel konum). İlçe kaynakta yok:
defin yeri ("KADİRLİ / KÜMBET", "ASRİ MEZARLIK", "KARACALAR") olduğu gibi defin_yeri'ne yazılır, ondan ilçe ÇIKARILMAZ.
Kullanım: python3 okuyucu/osmaniye.py [--gun 7]
"""
import html, os, re, sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Osmaniye"
FEED = "https://osmaniye-bld.gov.tr/kategori/vefaat/feed/"
KAYNAK_AD = "Osmaniye Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "osmaniye")
NS = {"c": "http://purl.org/rss/1.0/modules/content/"}


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def tarih_coz(s):
    """'04 EKİM 2026 PAZAR' / '03.10.2026 CUMARTESİ' -> 'YYYY-AA-GG'."""
    s = metin(s)
    m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", s)
    if m:
        return ortak.tarih_iso(m.group(1))
    m = re.search(r"(\d{1,2}\s+\S+\s+\d{4})", s)
    return ortak.tarih_iso(m.group(1)) if m else None


def bloklar(icerik):
    """İçerik HTML'i -> [(tarih_iso|None, ad, defin_yeri)]. Taziye adresi bilerek okunmaz."""
    sonuc = []
    for parca in re.split(r"Cenaze Bilgi Sistemi\s*TAR[İI]H\s*:", icerik)[1:]:
        tarih = tarih_coz(re.split(r"</tr>", parca, 1)[0])
        ad = re.search(r"Ad[ıi]\s*&(?:amp;)?\s*Soyad[ıi]\s*</strong></td>\s*<td[^>]*>(.*?)</td>", parca, re.S)
        defin = re.search(r"Defin Yeri\s*</strong></td>\s*<td[^>]*>(.*?)</td>", parca, re.S)
        if not ad or not metin(ad.group(1)):
            continue
        sonuc.append((tarih, metin(ad.group(1)), metin(defin.group(1)) if defin else None))
    return sonuc


def kayda_cevir(ad, defin, gun, url, alindi):
    return {
        "id": ortak.kayit_id("osmaniye", ad, gun, defin or ""),
        "il": IL,
        "ilce": None,                # kaynakta yok; defin yerinden çıkarılmaz
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None,
        "yas": None,
        "dogum_tarihi": None,
        "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(defin) if defin else None,
        "defin_zamani": None,
        "namaz_tarihi": None,
        "namaz_yeri_vakti": None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"defin_yeri": defin},
        "il_disi_defin": None,
        "ilce_belirsiz": True,
    }


def feed_oku():
    ham = ortak.indir(FEED)
    kok = ET.fromstring(ham.lstrip("﻿").encode("utf-8"))
    yazilar = []
    for it in kok.findall(".//item"):
        link = it.find("link").text
        baslik_gun = tarih_coz(it.find("title").text or "")
        yazilar.append((baslik_gun, link, it.find("c:encoded", NS).text or ""))
    return yazilar


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(FEED):
        print("robots.txt bu yolu yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    alindi = ortak.simdi_iso()
    by_gun = {g: [] for g in gunler}
    for baslik_gun, link, icerik in feed_oku():
        for tarih, ad, defin in bloklar(icerik):
            gun = tarih or baslik_gun
            if gun in by_gun:
                by_gun[gun].append(kayda_cevir(ad, defin, gun, link, alindi))
    for g in gunler:
        gor, tek = set(), []
        for k in by_gun[g]:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        print(f"{g}: {len(tek)} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
