#!/usr/bin/env python3
"""Batman Belediyesi vefat listesi okuyucusu (yalnız standart kütüphane).
Kullanım: python3 okuyucu/batman.py [--gun 7]
Kaynak: https://www.batman.bel.tr/vefat_edenler (tarih filtreli HTML tablo; gün başına 1 istek).
KVKK: modaldaki cenaze yakını, telefon ve taziye bilgileri OKUNMAZ; yalnız ana tablo satırları alınır.
"""
import os, re, sys, time, urllib.request, urllib.robotparser
from datetime import date, timedelta
from html import unescape
from urllib.error import HTTPError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

SITE = "https://www.batman.bel.tr"
URL = SITE + "/index.php?sayfa=vefat_edenler&limit=100&baslangic={0}&bitis={0}"
UA = "KiminCenazesiBot/0.1 (+kimincenazesi)"
KAYNAK_AD = "Batman Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "batman")
SATIR = re.compile(
    r'<tr>\s*<td>(\d{2}\.\d{2}\.\d{4})</td>\s*<td class="fw-bold text-dark">(.*?)</td>\s*'
    r'<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', re.S)


def temiz(s):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", s)).split())


def robots_izin(yol):
    rp = urllib.robotparser.RobotFileParser()
    try:
        with urllib.request.urlopen(urllib.request.Request(SITE + "/robots.txt", headers={"User-Agent": UA}), timeout=30) as r:
            rp.parse(r.read().decode("utf-8", "replace").splitlines())
    except HTTPError:
        return True  # robots.txt yok (404) -> kısıt yok
    return rp.can_fetch("CenazeIlanlariBot", SITE + yol)


def indir(gun):
    url = URL.format(gun)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40) as r:
        return url, r.read().decode("utf-8", "replace")


def kayda_cevir(m, gun, url, alindi):
    vefat, ad, dt, dyeri, defin, dtar = [temiz(x) for x in m.groups()]
    vefat_iso, dogum_iso, defin_iso = ortak.tarih_iso(vefat), ortak.tarih_iso(dt), ortak.tarih_iso(dtar)
    yas = None
    if vefat_iso and dogum_iso and dogum_iso < vefat_iso:  # doğum=vefat gibi kaynak hatalarında yaş yazılmaz
        v, d = date.fromisoformat(vefat_iso), date.fromisoformat(dogum_iso)
        yas = v.year - d.year - ((v.month, v.day) < (d.month, d.day))
    return {
        "id": ortak.kayit_id("batman", ad, vefat_iso or gun, dt),
        "il": "Batman",
        "ilce": "Merkez",  # Batman Belediyesi yalnız Merkez ilçenin belediyesi; doğum yeri ilçe DEĞİL, ham'da
        "ilce_kaynak": "belediye kapsamı (Batman Belediyesi = Merkez)",
        "ilce_belirsiz": False,
        "il_disi_defin": None,
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None,  # kaynakta yok
        "yas": yas,  # doğum ve vefat tarihinden hesaplanır
        "dogum_tarihi": dogum_iso,
        "vefat_tarihi": vefat_iso,
        "defin_yeri": defin or None,
        "defin_zamani": defin_iso,  # kaynakta yalnız defin TARİHİ var (saat yok)
        "namaz_tarihi": None,
        "namaz_yeri_vakti": None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"ad": ad, "dogum_tarihi": dt, "dogum_yeri": dyeri, "defin_yeri": defin, "defin_tarihi": dtar},
    }


def gun_oku(gun):
    for deneme in range(3):  # sunucu zaman zaman zaman aşımına uğruyor
        try:
            url, html = indir(gun)
            break
        except Exception as e:
            if deneme == 2:
                raise
            time.sleep(BEKLE * 2)
    alindi = ortak.simdi_iso()
    k = [kayda_cevir(m, gun, url, alindi) for m in SATIR.finditer(html)]
    if len(k) >= 100:
        print(f"UYARI {gun}: 100 kayıt sınırına ulaşıldı, eksik olabilir", file=sys.stderr)
    return k


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not robots_izin("/vefat_edenler"):
        print("robots.txt bu yolu yasaklıyor; okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for i, g in enumerate(gunler):
        if i:
            time.sleep(BEKLE)
        try:
            by_gun[g] = gun_oku(g)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        gor, tek = set(), []
        for k in by_gun[g]:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.json_yaz(os.path.join(KOK, f"{g}.json"), {"il": "Batman", "liste_tarihi": g, "kayitlar": tek})
        print(f"{g}: {len(tek)} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, "Batman", sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
