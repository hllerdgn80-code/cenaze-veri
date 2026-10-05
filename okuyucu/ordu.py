#!/usr/bin/env python3
"""Ordu Büyükşehir Belediyesi vefat listesi okuyucusu (yalnız standart kütüphane).
Kullanım: python3 okuyucu/ordu.py [--gun 7]
"""
import os, sys, time, urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

URL = "https://www.ordu.bel.tr/vefat-edenler?date={}"
UA = "CenazeIlanlariBot/0.1 (+https://github.com/hllerdgn80-code/cenaze-veri)"
KAYNAK_AD = "Ordu Büyükşehir Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "ordu")
ETIKET = {"adı soyadı": "ad", "vefat tarihi": "vefat", "vefat yaşı": "yas", "anne-baba adı": "anne_baba",
          "i̇lçe": "ilce", "ilçe": "ilce", "mahalle": "mahalle", "defin yeri": "defin",
          "namazın kılınacağı tarih": "namaz_tarih", "namazın kılınacağı yer": "namaz_yer"}


class Ayrac(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.kayitlar, self.cur = [], None
        self.li_derin = 0
        self.alan = None      # 'title' | 'name' | 'js-name' | 'datetext' | 'older'
        self.alan_div = 0
        self.buf = []
        self.etiket = None

    def handle_starttag(self, tag, attrs):
        cls = (dict(attrs).get("class") or "").split()
        if tag == "li" and "list-column" in cls:
            self.cur = {"_baslik": {}, "alanlar": {}}
            self.li_derin = 1
            return
        if self.cur is None:
            return
        if tag == "li":
            self.li_derin += 1
        if self.alan:
            if tag == "div":
                self.alan_div += 1
            return
        if tag == "div":
            for c in ("js-name", "datetext", "older", "row-title", "row-name"):
                if c in cls:
                    self.alan, self.alan_div, self.buf = c, 1, []
                    return

    def handle_endtag(self, tag):
        if self.cur is None:
            return
        if tag == "div" and self.alan:
            self.alan_div -= 1
            if self.alan_div == 0:
                t = " ".join("".join(self.buf).split())
                if self.alan == "row-title":
                    self.etiket = t.rstrip(":").strip().lower()
                elif self.alan == "row-name":
                    if self.etiket:
                        self.cur["alanlar"][self.etiket] = t
                    self.etiket = None
                else:
                    self.cur["_baslik"][self.alan] = t
                self.alan = None
        elif tag == "li":
            self.li_derin -= 1
            if self.li_derin == 0:
                self.kayitlar.append(self.cur)
                self.cur = None

    def handle_data(self, data):
        if self.alan:
            self.buf.append(data)


def indir(gun):
    url = URL.format(gun)
    istek = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(istek, timeout=40) as r:
        return url, r.read().decode("utf-8", "replace")


def kayda_cevir(ham, gun, url, alindi):
    a = {}
    for etiket, deger in ham["alanlar"].items():
        k = ETIKET.get(etiket)
        if k:
            a[k] = deger  # KVKK: telefon / yakınları gibi bilinmeyen etiketler bilerek alınmaz
    ad = a.get("ad") or ham["_baslik"].get("js-name", "")
    vefat = ortak.tarih_iso(a.get("vefat") or ham["_baslik"].get("datetext"))
    namaz = ortak.tarih_iso(a.get("namaz_tarih"))
    yas = a.get("yas") or ham["_baslik"].get("older")
    return {
        "id": ortak.kayit_id("ordu", ad, vefat or gun, a.get("anne_baba", "") + (namaz or "")),
        "il": "Ordu",
        "ilce": ortak.tr_title(a.get("ilce", "")) or None,
        "mahalle": ortak.tr_title(a.get("mahalle", "")) or None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(a.get("anne_baba", "")) or None,
        "yas": int(yas) if yas and yas.isdigit() else None,
        "dogum_tarihi": None,  # Ordu listesi doğum tarihi vermiyor
        "vefat_tarihi": vefat,
        "defin_yeri": a.get("defin") or None,
        "defin_zamani": None,  # kaynakta ayrı defin saati yok; namaz alanları kullanılır
        "namaz_tarihi": namaz,
        "namaz_yeri_vakti": a.get("namaz_yer") or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"ad": ad, "ilce": a.get("ilce"), "mahalle": a.get("mahalle"), "vefat_tarihi": a.get("vefat"),
                "namaz_tarihi": a.get("namaz_tarih"), "anne_baba": a.get("anne_baba")},
    }


def gun_oku(gun):
    url, html = indir(gun)
    p = Ayrac()
    p.feed(html)
    alindi = ortak.simdi_iso()
    return [kayda_cevir(h, gun, url, alindi) for h in p.kayitlar]


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL.format(date.today().isoformat())):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
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
        # aynı gün içinde tekrar eden id'leri ele
        gor, tek = set(), []
        for k in by_gun[g]:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, "Ordu", g, tek)   # ilçe / il dışı defin ayrımı burada işlenir
        print(f"{g}: {len(tek)} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, "Ordu", sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
