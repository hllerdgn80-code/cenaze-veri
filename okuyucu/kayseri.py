#!/usr/bin/env python3
"""Kayseri Büyükşehir Belediyesi MEZARLIK BİLGİ SİSTEMİ vefat ilanları okuyucusu (yalnız standart kütüphane).
16.10.2026 (sahibi: "mezarlık bilgi sistemi önceliğimiz"; "bize verilen bilgileri alıp yerleştiririz"): kaynak
https://mezarlik.kayseri.bel.tr/Vefat/Ilanlar?tarih=YYYY-AA-GG (GET; giriş/CAPTCHA yok). Kart: AD SOYAD, ANNE / BABA,
Cenaze Vakti, Mezarlık, Cami / Yer, Ada / Parsel, Taziye Adresi ("... KOCASİNAN/KAYSERİ").
İLÇE: taziye satırının SONUNDAKİ "<İLÇE>/KAYSERİ" parçasından yalnız ilçe adı alınır (ilin geçerli ilçesiyse); adresin kendisi
(mahalle, sokak, kapı no) ve koordinatlar ALINMAZ, saklanmaz. Mezarlık adından ilçe tablosu ikinci yol (ortak.ilce_isle).
Liste tarih seçilerek o güne sorgulanır -> namaz_tarihi = o gün (cenaze günü).
Eski kaynak (www.kayseri.bel.tr/vefat-ilanlari, ASP.NET) yedektir: MBS okunamazsa o denenir.
Kullanım: python3 okuyucu/kayseri.py [--gun 7]"""
import html, os, re, sys, urllib.parse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kayseri"
URL = "https://mezarlik.kayseri.bel.tr/Vefat/Ilanlar"
KAYNAK_AD = "Kayseri Büyükşehir Belediyesi"
BEKLE = 2.0
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kayseri")


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def engel_var(sayfa):
    return bool(re.search(r"(?i)captcha|g-recaptcha|type=\"password\"", sayfa))


def ilce_al(taziye):
    """'... No:18 KOCASİNAN/KAYSERİ' -> 'Kocasinan' (yalnız geçerli ilçe; değilse None). Adres döndürülmez."""
    m = re.search(r"([A-Za-zÇĞİÖŞÜçğıöşü.\- ]+?)\s*/\s*KAYSER[İI]\s*$", taziye or "", re.I)
    if not m:
        return None
    aday = m.group(1).split()[-1] if m.group(1).split() else ""
    gecerli = {ortak.katla(x): x for x in ortak.gecerli_ilceler(IL)}
    return gecerli.get(ortak.katla(aday))


def ayristir(sayfa):
    """-> [ham sözlük]."""
    out = []
    for kart in re.split(r'class="ilan-card', sayfa)[1:]:
        ad = re.search(r"<h3>(.*?)</h3>", kart, re.S)
        if not ad:
            continue
        h = {"ad": metin(ad.group(1))}
        ab = re.search(r'class="parent-names">(.*?)</span>', kart, re.S)
        h["anne_baba"] = metin(ab.group(1)) if ab else ""
        for et, deger in re.findall(r'<span class="label">(.*?)</span>\s*<span class="value">(.*?)</span>', kart, re.S):
            h[metin(et)] = metin(deger)
        tz = re.search(r"Taziye Adresi:</strong>\s*<p>(.*?)</p>", kart, re.S)
        h["_ilce"] = ilce_al(metin(tz.group(1))) if tz else None      # adres saklanmaz, yalnız ilçe
        if h["ad"]:
            out.append(h)
    return out


def kayda_cevir(h, gun, alindi):
    ad = h["ad"]
    ana, _, baba = (x.strip() for x in (h.get("anne_baba") or "").partition("/"))
    vakit = h.get("Cenaze Vakti") or None
    cami = h.get("Cami / Yer") or None
    mez = h.get("Mezarlık") or None
    ilce = h.get("_ilce")
    k = {
        "id": ortak.kayit_id("kayseri", ad, gun, f"{h.get('anne_baba','')}|{cami or ''}|{mez or ''}"),
        "il": IL, "ilce": ilce, "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title("-".join(x for x in (ana, baba) if x)) or None,
        "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(mez) if mez else None,
        "defin_zamani": None,
        "namaz_tarihi": gun,
        "namaz_yeri_vakti": " – ".join(x for x in (ortak.tr_title(vakit) if vakit else None, ortak.tr_title(cami) if cami else None) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": URL, "alindi": alindi,
        "ham": {"vakit": vakit, "cami": cami, "mezarlik": mez, "ada_parsel": h.get("Ada / Parsel"),
                "ilce_kaynagi": "taziye_ilce" if ilce else None},
        "il_disi_defin": None,
        "ilce_belirsiz": not bool(ilce),
    }
    return k


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        try:
            sayfa = ortak.indir(URL + "?" + urllib.parse.urlencode({"tarih": g}), BEKLE)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        if engel_var(sayfa):
            print(f"DUR: {g} yanıtında giriş/CAPTCHA belirtisi", file=sys.stderr)
            break
        alindi = ortak.simdi_iso()
        gor, tek = set(), []
        for h in ayristir(sayfa):
            k = kayda_cevir(h, g, alindi)
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        print(f"{g}: {len(tek)} kayıt, ilçeli {sum(1 for k in tek if k['ilce'])}")
    if not by_gun:
        print("UYARI: mezarlık sistemi okunamadı", file=sys.stderr)
        return
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
