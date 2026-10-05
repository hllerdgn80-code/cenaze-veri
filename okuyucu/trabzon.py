#!/usr/bin/env python3
"""Trabzon Büyükşehir Belediyesi vefat listesi okuyucusu (yalnız standart kütüphane).
Kaynak: GET /Debis/_VefatEdenleriListele?Tarih=GG.AA.YYYY (HTML parçası, akordeon).
Kullanım: python3 okuyucu/trabzon.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Trabzon"
URL = "https://www.trabzon.bel.tr/Debis/_VefatEdenleriListele?Tarih={}"
KAYNAK_AD = "Trabzon Büyükşehir Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "trabzon")


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    """-> (günlük sayı [sayfanın kendi beyanı], [ham kayıt])"""
    m = re.search(r"G\S+NL\S+K VEFAT EDEN K\S+ SAYISI\s*:\s*(\d+)", metin(sayfa), re.I)
    sayi = int(m.group(1)) if m else None
    kayitlar = []
    for blok in re.split(r'<div class="accordion-item', sayfa)[1:]:
        b = re.search(r'<div class="col-11">\s*(.*?)\s*<button', blok, re.S)
        if not b:
            continue
        baslik = metin(b.group(1))
        # alanlar: <strong>Etiket : </strong>değer
        alanlar = {}
        for et, deger in re.findall(r"<strong>\s*([^<:]+?)\s*:\s*</strong>(.*?)(?=<br|<button|</div>)", blok, re.S):
            alanlar[ortak.tr_lower(et.strip())] = metin(deger)
        kayitlar.append({"baslik": baslik, "alanlar": alanlar})
    return sayi, kayitlar


def konum_ayir(konum):
    """'TRABZON/ORTAHİSAR/UĞURLU' -> (ilce_ham, mahalle). Başka il: 'ARTVİN', 'X/Y' -> ilce_ham 'X / Y'."""
    p = [x.strip() for x in konum.split("/") if x.strip()]
    if not p:
        return None, None
    if ortak.katla(p[0]) == ortak.katla(IL):
        return (p[1] if len(p) > 1 else None), (p[2] if len(p) > 2 else None)
    return " / ".join(p[:2]), None   # il dışı: mahalle bilgisi taşınmaz


def kayda_cevir(h, gun, url, alindi):
    baslik = h["baslik"]
    ad, _, konum = baslik.rpartition(" - ")
    if not ad:                       # ' - ' yoksa tamamı addır
        ad, konum = baslik, ""
    a = h["alanlar"]
    vefat = ortak.tarih_iso(a.get("ölüm tarihi"))
    yakin = a.get("yakın bilgisi", "")   # KVKK: yalnız Anne/Baba adı alınır, kalan metin atılır
    anne = re.search(r"Anne Ad. *: *(.*?)(?: - Baba Ad.|$)", yakin)
    baba = re.search(r"Baba Ad. *: *(.*)$", yakin)
    ap = "-".join(x for x in (anne and anne.group(1).strip(), baba and baba.group(1).strip()) if x)
    ilce_ham, mahalle = konum_ayir(konum)
    yer, vakit = a.get("namaz yeri"), a.get("namaz vakti")
    return {
        "id": ortak.kayit_id("trabzon", ad, vefat or gun, yakin + (yer or "")),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,
        "mahalle": ortak.tr_title(mahalle) if mahalle else None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": None,                 # kaynakta yok
        "dogum_tarihi": None,        # kaynakta yok
        "vefat_tarihi": vefat,
        "defin_yeri": a.get("mezarlık") or None,
        "defin_zamani": None,        # kaynakta ayrı defin saati yok
        "namaz_tarihi": None,        # kaynak namaz tarihi vermiyor, yalnız vakit
        "namaz_yeri_vakti": " – ".join(x for x in (vakit, yer) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"baslik": baslik, "ölüm_tarihi": a.get("ölüm tarihi"), "namaz_vakti": vakit,
                "namaz_yeri": yer, "mezarlık": a.get("mezarlık"), "anne_baba": ap or None},
    }


def gun_oku(gun):
    d = date.fromisoformat(gun)
    url = URL.format(d.strftime("%d.%m.%Y"))
    sayi, ham = ayristir(ortak.indir(url, BEKLE))
    alindi = ortak.simdi_iso()
    return sayi, [kayda_cevir(h, gun, url, alindi) for h in ham]


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL.format("01.01.2026")):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        try:
            sayi, kayitlar = gun_oku(g)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        gor, tek = set(), []
        for k in kayitlar:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        uyari = "" if sayi in (None, len(kayitlar)) else f"  UYARI: sayfa {sayi} diyor, ayrıştırılan {len(kayitlar)}"
        print(f"{g}: {len(tek)} kayıt (sayfa beyanı: {sayi}){uyari}")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
