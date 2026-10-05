#!/usr/bin/env python3
"""Kahramanmaraş Büyükşehir Belediyesi cenaze ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: GET /cenaze-ilanlari?tarih=YYYY-AA-GG&sayfa=N (HTML kartlar, sayfa başına 25 kayıt).
Kullanım: python3 okuyucu/kahramanmaras.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kahramanmaraş"
URL = "https://www.kahramanmaras.bel.tr/cenaze-ilanlari?tarih={}&sayfa={}"
KAYNAK_AD = "Kahramanmaraş Büyükşehir Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kahramanmaras")
# KVKK: 'Cenaze yakını', 'Taziye adresi', 'Anons metni' bilerek alınmaz
ETIKET = {"ana adı": "ana", "baba adı": "baba", "doğum tarihi": "dogum", "vefat tarihi": "vefat",
          "defin tarihi": "defin_tarihi", "defin yeri": "defin_yeri", "cenaze kaldırma saati": "saat",
          "cenaze kaldırma yeri": "yer"}


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    """-> (en büyük sayfa no, [ham kayıt])"""
    sayfalar = [int(x) for x in re.findall(r"sayfa=(\d+)", sayfa)] or [1]
    kayitlar = []
    parcalar = re.split(r'<div class="clearfix cenaze-row-wrapper cenaze-row-wrapper-id-(\d+)">', sayfa)
    for i in range(1, len(parcalar), 2):
        site_id, blok = parcalar[i], parcalar[i + 1]
        ad = re.search(r'<h3 class="cenaze-baslik">(.*?)</h3>', blok, re.S)
        yas = re.search(r'cenaze-yas">\s*Yaş:\s*<strong>(.*?)</strong>', blok, re.S)
        ilce = re.search(r'<span class="cenaze-ilce">(.*?)</span>', blok, re.S)
        alanlar = {}
        for et, deger in re.findall(r'<span class="cenaze-th">(.*?)</span>\s*<span class="cenaze-td">(.*?)</span>', blok.split("cenaze-details")[-1], re.S):
            k = ETIKET.get(ortak.tr_lower(metin(et)).rstrip(":").strip())
            if k:
                alanlar[k] = metin(deger)
        kayitlar.append({"site_id": site_id, "ad": metin(ad.group(1)) if ad else "",
                         "yas": metin(yas.group(1)) if yas else "", "ilce_mahalle": metin(ilce.group(1)) if ilce else "",
                         "alanlar": alanlar})
    return max(sayfalar), kayitlar


def ilce_mahalle(s):
    """'ONİKİŞUBAT / YEŞİLYURT MAH.' -> ('ONİKİŞUBAT', 'YEŞİLYURT MAH.'); 'GAZİANTEP/MERKEZ /' -> ('GAZİANTEP/MERKEZ', None)."""
    p = re.split(r"(?:^|\s)/(?:\s+|$)", s.strip(), maxsplit=1)
    ilce = p[0].strip() or None
    mahalle = p[1].strip() if len(p) > 1 and p[1].strip() else None
    return ilce, mahalle


def kayda_cevir(h, gun, url, alindi):
    a = h["alanlar"]
    ilce_ham, mahalle = ilce_mahalle(h["ilce_mahalle"])
    vefat = ortak.tarih_iso(a.get("vefat"))
    defin = ortak.tarih_iso(a.get("defin_tarihi"))
    dogum = a.get("dogum", "")
    dogum_iso = ortak.tarih_iso(dogum)            # kaynak çoğu kez yalnız yıl veriyor -> null, yıl ham'da
    ap = "-".join(x for x in (a.get("ana"), a.get("baba")) if x)
    vakit, yer = a.get("saat"), a.get("yer")
    return {
        "id": ortak.kayit_id("kahramanmaras", h["ad"], vefat or gun, f'{h["site_id"]}'),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,
        "mahalle": ortak.tr_title(mahalle) if mahalle else None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": int(h["yas"]) if h["yas"].isdigit() else None,
        "dogum_tarihi": dogum_iso,
        "vefat_tarihi": vefat,
        "defin_yeri": a.get("defin_yeri") or None,
        "defin_zamani": defin,        # kaynak defin TARİHİ verir
        "namaz_tarihi": None,
        "namaz_yeri_vakti": " – ".join(x for x in (vakit, yer) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"site_id": h["site_id"], "ad": h["ad"], "ilce_mahalle": h["ilce_mahalle"], "yas": h["yas"],
                "dogum": dogum or None, "vefat": a.get("vefat"), "defin_tarihi": a.get("defin_tarihi"),
                "anne_baba": ap or None},
    }


def gun_oku(gun):
    """Bir günün tüm sayfalarını okur; kayıtlar (liste tarihi gun) döner."""
    kayitlar, sayfa, son = [], 1, 1
    while sayfa <= son and sayfa <= 10:
        url = URL.format(gun, sayfa)
        son, ham = ayristir(ortak.indir(url, BEKLE))
        alindi = ortak.simdi_iso()
        kayitlar += [kayda_cevir(h, gun, url, alindi) for h in ham]
        sayfa += 1
    return kayitlar


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL.format(date.today().isoformat(), 1)):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        try:
            kayitlar = gun_oku(g)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        # Kaynakta ?tarih=D, vefat <= D <= defin olan (o gün yürürlükteki) ilanları verir; aynı ilan birkaç günün
        # listesinde çıkar. Gün dosyası o günün listesidir (gün içi tekrar elenir); son7gun.json id'ye göre tekilleştirir.
        tek, gor = [], set()
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
