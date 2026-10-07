#!/usr/bin/env python3
"""Niğde Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: https://vefatedenler.nigde.bel.tr/vefatedenler.php?araTarih=YYYY-AA-GG (günlük sorgu; sayfa başına 3 satır, "Sonraki" bağlantısı).
Sütunlar: Adı Soyad, Vefat Tarihi, Vakit (namaz vakti), Defin Yeri, Açıklama (serbest metin).
Açıklamadan yalnız: mahalle/köy/kasaba ("X Mahallesi Sakinlerinden") ve "Cenazesi ..." cümlesi (namaz yeri + defin) alınır; yakın listesi/meslek atılır.
TLS: sunucu ara sertifikayı (GlobalSign GCC R46 AlphaSSL CA 2025) göndermiyor ve yerel güven deposunda GlobalSign Root R46 yok.
Doğrulama AÇIK kalır; sertifika/nigde-zincir.pem = ara sertifika (secure.globalsign.com AIA adresinden) + GlobalSign Root R46 kökü
(SHA-256 4F:A3:12:6D:8D:3A:11:D1:C4:85:5A:4F:80:7C:BA:D6:CF:91:9D:3A:5A:88:B0:3B:EA:2C:63:72:D9:3C:40:C9, GlobalSign'ın yayımladığı değer)
ve yalnız bu bağlama eklenir. Ara sertifika 2029, uç sertifika Nisan 2027'de biter; yenilenirse aynı yoldan tazele.
Kaynakta ilçe yok -> ilce None + ilce_belirsiz.
Kullanım: python3 okuyucu/nigde.py [--gun 7]
"""
import html, os, re, ssl, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Niğde"
URL = "https://vefatedenler.nigde.bel.tr/vefatedenler.php"
KAYNAK_AD = "Niğde Belediyesi"
DIZIN = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.join(DIZIN, "..", "veri", "nigde")
ZINCIR = os.path.join(DIZIN, "sertifika", "nigde-zincir.pem")
MAKS_SAYFA = 8


def baglam():
    c = ssl.create_default_context()      # doğrulama ve ana makine adı denetimi açık
    c.load_verify_locations(ZINCIR)
    return c


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def ayristir(sayfa):
    kayitlar = []
    for tr in re.findall(r"<tr>(.*?)</tr>", sayfa, re.S):
        h = [metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == 5:
            kayitlar.append(dict(zip(["ad", "tarih", "vakit", "defin", "aciklama"], h)))
    return kayitlar, ("Sonraki" in sayfa and "prevnext" in sayfa and re.search(r'href="\?page=\d+[^"]*">\s*Sonraki', sayfa) is not None)


def aciklama_coz(a):
    mah = re.search(r"([\wÇĞİÖŞÜçğıöşü.' -]+?)\s+(Mahallesi|Köyü|Kasabası|Beldesi)\s*(?:Sakinlerinden|’ndan|'ndan|ndan)", a, re.I)
    mahalle = mah.group(1).strip() if mah else None
    if not mah:
        k = re.search(r"([\wÇĞİÖŞÜçğıöşü.' -]+?)\s+(Kasabasından|Köyünden|Beldesinden|Mahallesinden)", a, re.I)
        mahalle = k.group(1).strip() if k else None
    if mahalle and len(mahalle.split()) > 3:      # meslek/yakınlık cümlesi yakalandıysa kabul etme
        mahalle = None
    cum = None
    c = re.search(r"Cenaze", a)
    if c:
        cum = re.split(r"Allah\s+Rahmet|Taziye|TAZİYE|Tel\b", a[c.start():], flags=re.I)[0]
        cum = re.sub(r"\(?\+?\d[\d\s()\-]{8,}\d", "", cum)
        cum = " ".join(cum.split()).strip() or None
    return mahalle, cum


def kayda_cevir(h, gun, url, alindi):
    mahalle, cum = aciklama_coz(h["aciklama"])
    vefat = None
    mt = re.match(r"^(\d{1,2})\s+(\S+)\s+(\d{4})$", h["tarih"])
    if mt:
        vefat = ortak.tarih_iso(h["tarih"])
    return {
        "id": ortak.kayit_id("nigde", h["ad"], vefat or gun, h["defin"]),
        "il": IL, "ilce": None,
        "mahalle": ortak.tr_title(mahalle) if mahalle else None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": None, "yas": None, "dogum_tarihi": None,
        "vefat_tarihi": vefat,
        "defin_yeri": ortak.tr_title(h["defin"]) if h["defin"] else None,
        "defin_zamani": None, "namaz_tarihi": None,
        "namaz_yeri_vakti": cum if cum else (h["vakit"] or None),
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"vakit": h["vakit"] or None, "defin": h["defin"] or None, "mahalle_ham": mahalle},
    }


def gun_oku(gun, ssl_b):
    sonuc = []
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = f"{URL}?araTarih={gun}" + (f"&page={sayfa_no}" if sayfa_no > 1 else "")
        ham, sonraki = ayristir(ortak.indir(url, ssl_baglam=ssl_b))
        alindi = ortak.simdi_iso()
        sonuc += [kayda_cevir(h, gun, url, alindi) for h in ham]
        if not sonraki:
            break
    return sonuc


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    ssl_b = baglam()
    if not ortak.robots_izin(URL, ssl_b):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        try:
            kayitlar = gun_oku(g, ssl_b)
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
