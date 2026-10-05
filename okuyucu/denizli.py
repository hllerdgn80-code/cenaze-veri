#!/usr/bin/env python3
"""Denizli Büyükşehir Belediyesi Mezarlık Bilgi Sistemi (Bugün Defnedilenler) okuyucusu (yalnız standart kütüphane).
Kaynak: sayfanın kendi istemci çağrısı -> POST https://mezarlik.denizli.bel.tr/bugunDefnedilenlerYeni.aspx/GetDefnedilenler
gövde {"tarih":"YYYY-AA-GG"} (ASP.NET PageMethod, JSON; "d" dizisi). Giriş/CAPTCHA yok. İl geneli (19 ilçe).
Sorgulanan gün liste_tarihi olur; aynı kayıt birkaç günün cevabında çıkabilir (id: ad + ölüm tarihi + cilt no, son7gun tekilleştirir).
Kaynakta İLÇE YOK (mezarlık adı ilçe vermez): ilce None + ilce_belirsiz. Kaynak "Nakil Giden" diyorsa defin başka yerde (hedef yok).
Ada/parsel/sıra (mezar konumu) ham'a yazılır. KVKK: telefon/ölüm nedeni yok zaten; yalnız tanımlı alanlar alınır.
Kullanım: python3 okuyucu/denizli.py [--gun 7]
"""
import json, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Denizli"
SAYFA = "https://mezarlik.denizli.bel.tr/bugunDefnedilenlerYeni.aspx"
API = SAYFA + "/GetDefnedilenler"
KAYNAK_AD = "Denizli Büyükşehir Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "denizli")


def gun_getir(gun):
    govde = json.dumps({"tarih": gun}).encode("utf-8")
    ham = ortak.indir(API, BEKLE, veri=govde, basliklar={"Content-Type": "application/json; charset=utf-8"})
    return json.loads(ham).get("d") or []


def kayda_cevir(r, gun, alindi):
    ad = " ".join(x for x in (r.get("Ad"), r.get("Soyad")) if x).strip()
    olum = ortak.tarih_iso(r.get("OlumTarihi"))
    dogum = ortak.tarih_iso(r.get("DogumTarihi"))
    nakil = str(r.get("Nakil")).lower() == "true"
    cami = None if nakil else (r.get("DefainCamii") or None)
    vakit = None if nakil else (r.get("DefinZamani") or None)
    ap = "-".join(x for x in (r.get("AnneAdi"), r.get("BabaAdi")) if x)
    mezarlik = r.get("MezarlikAdi") or None
    return {
        "id": ortak.kayit_id("denizli", ad, olum or "", f'{r.get("Cilt") or ""}|{r.get("DogumTarihi") or ""}'),
        "il": IL,
        "ilce": None,                       # kaynakta yok
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": None,                        # kaynakta yok (doğum tarihi var)
        "dogum_tarihi": dogum,
        "vefat_tarihi": olum,
        "defin_yeri": mezarlik,             # nakil ise "Nakil Giden"
        "defin_zamani": None,               # kaynak defin saatini/namaz vaktini verir, tarih vermez
        "namaz_tarihi": None,
        "namaz_yeri_vakti": " – ".join(x for x in (vakit, ortak.tr_title(cami) if cami else None) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": SAYFA,
        "alindi": alindi,
        "ham": {"dogum_yeri": r.get("DogumYeri") or None, "dogum": r.get("DogumTarihi") or None, "cilt": r.get("Cilt") or None,
                "ada": r.get("Ada") or None, "parsel": r.get("Parsel") or None, "sira": r.get("Sira") or None,
                "mezarlik_kodu": r.get("MezarlikKodu") or None, "cami": r.get("DefainCamii") or None,
                "defin_zamani": r.get("DefinZamani") or None, "olum": r.get("OlumTarihi") or None, "nakil": nakil},
    }


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(SAYFA):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun, goruldu = {}, set()
    for g in gunler:
        try:
            ham = gun_getir(g)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        alindi = ortak.simdi_iso()
        tek = []
        for r in ham:
            k = kayda_cevir(r, g, alindi)
            if k["id"] not in goruldu:
                goruldu.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        print(f"{g}: {len(tek)} kayıt (sorgu {len(ham)} satır)")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
