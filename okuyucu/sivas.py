#!/usr/bin/env python3
"""Sivas Belediyesi "Aramızdan Ayrılanlar" listesi okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.sivas.bel.tr/vefat-edenler[?page=N] (sunucuda üretilen HTML, sayfa başına 10 kayıt, en yeni üstte).
Kayıt: ad, vefat yaşı, defin tarihi (+gün adı), yer-vakit (cami + saat) ya da nakil yeri, defin yeri (mezarlık / nakil yeri), taziye adresi.
TAZİYE ADRESİ alınmaz (KVKK). Nakil kayıtlarında yer-vakit = defin yeri = nakil yeri ("DİVRİĞİ  BAŞÖREN" = ilçe + köy,
"SİNOP  DURAĞAN" = il + ilçe, "İSTANBUL" = il): ortak.ilce_coz ile çözülür (Sivas ilçesi -> ilce, başka il -> il_disi_defin).
Sivas kent merkezindeki (Ay Yıldız Cami / Yukarı Tekke vb.) kayıtlarda kaynakta ilçe yok -> ilce None + ilce_belirsiz.
TLS: sitenin ara sertifikası (Sectigo DV R36) eksik; doğrulama AÇIK, sertifika/zincir-eksik-ara.pem eklenir (gaziantep.py ile aynı yöntem).
Kullanım: python3 okuyucu/sivas.py
"""
import html, os, re, ssl, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Sivas"
URL = "https://www.sivas.bel.tr/vefat-edenler"
KAYNAK_AD = "Sivas Belediyesi"
BEKLE = 3.5
MAKS_SAYFA = 5
DIZIN = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.join(DIZIN, "..", "veri", "sivas")
ARA_SERTIFIKA = os.path.join(DIZIN, "sertifika", "zincir-eksik-ara.pem")
ETIKETLER = {"adı soyadı": "ad", "vefat yaşı": "yas", "defin tarihi": "defin", "yer - vakit": "yer_vakit",
             "defin yeri": "defin_yeri", "taziye adresi": "taziye"}


def baglam():
    c = ssl.create_default_context()          # doğrulama ve ana makine adı denetimi açık
    c.load_verify_locations(ARA_SERTIFIKA)
    return c


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    a = sayfa.find('<div class="funeral-list">')
    if a < 0:
        raise RuntimeError("funeral-list bulunamadı (sayfa düzeni değişmiş olabilir)")
    blok = sayfa[a:sayfa.find("</ul>", a)]
    kayitlar = []
    for li in re.split(r"<li\b", blok)[1:]:
        li = re.sub(r"<!--.*?-->", "", li, flags=re.S)
        r = {}
        for et, deger in re.findall(r'<div class="label">\s*(.*?)\s*</div>(.*?)(?=<div class="label">|$)', li, re.S):
            anahtar = ETIKETLER.get(ortak.tr_lower(metin(et)).rstrip(" :").strip() )
            if anahtar in ("yer_vakit", "defin_yeri"):   # iç boşluk korunur: nakil yerinde çift boşluk ayraçtır
                r[anahtar] = re.sub(r"\s*[\r\n\t]+\s*", " ", html.unescape(re.sub(r"<[^>]+>", "", deger))).strip()
            elif anahtar:
                r[anahtar] = metin(deger)
        if r.get("ad"):
            kayitlar.append(r)
    return kayitlar


def kayda_cevir(r, url, alindi):
    ad = r["ad"]
    m = re.match(r"(\d{1,2}\.\d{1,2}\.\d{4})", r.get("defin", ""))
    defin = ortak.tarih_iso(m.group(1)) if m else None
    yer_vakit, defin_yeri = r.get("yer_vakit", ""), r.get("defin_yeri", "")
    nakil = bool(yer_vakit) and ortak.katla(yer_vakit) == ortak.katla(defin_yeri)   # yer-vakit = defin yeri: nakil/başka yer
    cami = vakit = None
    if not nakil:
        mm = re.match(r"(.*?)\s*-\s*SAAT\s*:\s*(\d{1,2}:\d{2})\s*$", yer_vakit)
        cami, vakit = (mm.group(1), mm.group(2)) if mm else (yer_vakit or None, None)
    ilce_ham = " / ".join(p for p in re.split(r"\s{2,}", defin_yeri.strip()) if p) if nakil else None
    yas = r.get("yas", "")
    return {
        "id": ortak.kayit_id("sivas", ad, defin or "", f"{yas}|{yer_vakit}|{defin_yeri}"),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,   # yalnız nakil yerinden (kaynak yazar); ortak.ilce_coz çözer
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None,                  # kaynakta yok
        "yas": int(yas) if yas.isdigit() else None,
        "dogum_tarihi": None,
        "vefat_tarihi": None,               # kaynakta yok
        "defin_yeri": ortak.tr_title(defin_yeri) if (defin_yeri and not nakil) else (("Nakil: " + ortak.tr_title(ilce_ham)) if ilce_ham else None),
        "defin_zamani": defin,              # kaynak defin TARİHİ verir; saat namaz vaktinde
        "namaz_tarihi": defin if not nakil else None,
        "namaz_yeri_vakti": " – ".join(x for x in (vakit, ortak.tr_title(cami) if cami else None) if x) or None,
        "liste_tarihi": defin,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"yer_vakit": yer_vakit or None, "defin_yeri": defin_yeri or None, "defin": r.get("defin"), "nakil": nakil,
                "ilce_kaynagi": "nakil_yeri" if ilce_ham else None},
    }


def main():
    ctx = baglam()
    if not ortak.robots_izin(URL, ctx):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(7)]
    by_gun = {g: [] for g in gunler}
    goruldu = set()
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = URL if sayfa_no == 1 else f"{URL}?page={sayfa_no}"
        ham = ayristir(ortak.indir(url, BEKLE, ssl_baglam=ctx))
        alindi = ortak.simdi_iso()
        en_eski = None
        for r in ham:
            k = kayda_cevir(r, url, alindi)
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
