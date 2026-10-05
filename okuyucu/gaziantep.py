#!/usr/bin/env python3
"""Gaziantep Büyükşehir Belediyesi defin listesi okuyucusu (yalnız standart kütüphane).
Kaynak: GET https://www.gaziantep.bel.tr/tr/defin-listesi?date=GG.AA.YYYY (sunucuda üretilen HTML tablo, tek sayfa).
Kullanım: python3 okuyucu/gaziantep.py [--gun 7]

TLS: sitenin sunucusu ara sertifikayı (Sectigo DV R36 + R46 çapraz imzası) göndermiyor. Doğrulama AÇIK kalır;
eksik ara sertifikalar sertifika/zincir-eksik-ara.pem içinde (sertifikadaki AIA adreslerinden indirildi) ve ssl
bağlamına eklenir. Sistemin güvenilen kök listesi (USERTrust) yine kullanılır.
Kaynakta İLÇE YOK (yalnız mezarlık adı): ilce None + ilce_belirsiz True; mezarlık adı defin_yeri'ne yazılır,
mezarlık adından ilçe ÇIKARILMAZ. Kaynakta namaz yeri/saati yok.
"""
import html, os, re, ssl, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Gaziantep"
URL = "https://www.gaziantep.bel.tr/tr/defin-listesi?date={}"
KAYNAK_AD = "Gaziantep Büyükşehir Belediyesi"
BEKLE = 3.5
DIZIN = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.join(DIZIN, "..", "veri", "gaziantep")
ARA_SERTIFIKA = os.path.join(DIZIN, "sertifika", "zincir-eksik-ara.pem")


def baglam():
    c = ssl.create_default_context()          # doğrulama ve ana makine adı denetimi açık
    c.load_verify_locations(ARA_SERTIFIKA)
    return c


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    """Masaüstü tablosunu (<table> ... <tbody>) ayrıştırır -> [sözlük]. Satır yoksa []."""
    t = re.search(r"<table.*?</table>", sayfa, re.S)
    if not t:
        return []
    basliklar = [metin(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", t.group(0), re.S)]
    kayitlar = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t.group(0).split("<tbody>", 1)[-1], re.S):
        h = [metin(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == len(basliklar) and h and h[0]:
            kayitlar.append(dict(zip(basliklar, h)))
    return kayitlar


def kayda_cevir(h, gun, url, alindi):
    ad = h.get("Adı Soyadı", "")
    bab = h.get("Baba / Ana Adı", "")
    baba, _, ana = (x.strip() for x in bab.partition("/"))
    vefat_ham = h.get("Vefat Tarihi / Yaşı", "")
    vt, _, yas = (x.strip() for x in vefat_ham.partition("/"))
    vefat = ortak.tarih_iso(vt)
    mezarlik = h.get("Defin Yeri") or None
    ap = "-".join(x for x in (ana, baba) if x)    # diğer okuyucularda sıra: anne-baba
    return {
        "id": ortak.kayit_id("gaziantep", ad, vefat or gun, bab + "|" + (mezarlik or "") + "|" + h.get("Doğum Yılı", "")),
        "il": IL,
        "ilce": None,                 # kaynakta yok; mezarlık adından çıkarılmaz
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": int(yas) if yas.isdigit() else None,
        "dogum_tarihi": None,         # kaynak yalnız doğum YILI veriyor (ham.dogum_yili)
        "vefat_tarihi": vefat,
        "defin_yeri": mezarlik,       # mezarlık adı
        "defin_zamani": None,         # "defin listesi" tarihe göre ama saat yok; tarih beyanı doğrulanmadı
        "namaz_tarihi": None,
        "namaz_yeri_vakti": None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"cinsiyet": h.get("Cinsiyet") or None, "dogum_yili": h.get("Doğum Yılı") or None,
                "baba_ana": bab or None, "vefat_yas": vefat_ham or None},
        "il_disi_defin": None,
        "ilce_belirsiz": True,
    }


def gun_oku(gun, ctx):
    d = date.fromisoformat(gun)
    url = URL.format(d.strftime("%d.%m.%Y"))
    ham = ayristir(ortak.indir(url, BEKLE, ssl_baglam=ctx))
    alindi = ortak.simdi_iso()
    return [kayda_cevir(h, gun, url, alindi) for h in ham]


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    ctx = baglam()
    if not ortak.robots_izin(URL.format("01.01.2026"), ctx):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        try:
            kayitlar = gun_oku(g, ctx)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        gor, tek = set(), []
        for k in kayitlar:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        print(f"{g}: {len(tek)} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
