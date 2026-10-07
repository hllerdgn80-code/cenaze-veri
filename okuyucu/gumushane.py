#!/usr/bin/env python3
"""Gümüşhane Belediyesi vefat duyuruları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.gumushane.bel.tr/2/duyuru/?type=1&page=N (liste: başlık "AD hakkın rahmetine kavuşmuştur" + tarih)
ve her duyurunun ayrıntı sayfası (serbest metin). Tarih = duyuru tarihi (liste_tarihi).
Ayrıntıdan yalnız: mahalle/köy ("... mahallesi sakinlerinden") ve "Cenazesi ..." cümlesi (namaz/defin yeri-vakti) alınır.
KVKK: yakın listesi ("... eşi, ... annesi"), taziye telefonu ve taziye adı alınmaz. Kaynakta ilçe yok -> ilce None + ilce_belirsiz.
Kullanım: python3 okuyucu/gumushane.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Gümüşhane"
ANA = "https://www.gumushane.bel.tr"
LISTE = ANA + "/2/duyuru/?type=1&page={}"
KAYNAK_AD = "Gümüşhane Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "gumushane")
MAKS_SAYFA = 4


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def liste_ayristir(sayfa):
    """-> [{href, baslik, tarih}] (yalnız 'links fresh' listesi)"""
    i = sayfa.find('class="links fresh"')
    blok = sayfa[i:sayfa.find("</ul>", i)] if i >= 0 else ""
    sonuc = []
    for a, ic in re.findall(r'<a href="([^"]+)">(.*?)</a>', blok, re.S):
        t = re.search(r"<time[^>]*>(.*?)</time>", ic, re.S)
        baslik = metin(re.sub(r"<time.*?</time>", "", ic, flags=re.S))
        tarih = None
        if t:
            parca = metin(t.group(1)).replace(",", " ").split()[:3]
            tarih = ortak.tarih_iso(" ".join(parca))
        sonuc.append({"href": a, "baslik": baslik, "tarih": tarih})
    return sonuc


def ad_cikar(baslik):
    ad = re.split(r"[,\s]+hak+[ıi]n\s+rahmetine", baslik, flags=re.I)[0].strip(" ,.")
    return ad


def ayrinti_ayristir(sayfa):
    m = re.search(r"<h1>.*?</h1>\s*<p>(.*?)</p>", sayfa, re.S)
    govde = metin(m.group(1)) if m else ""
    mah = re.search(r"(?:İlimiz\s+|Gümüşhane\s+)?([\wÇĞİÖŞÜçğıöşü.' -]+?)\s+(mahallesi|mahalle|köyü|beldesi|kasabası)\s+sakinlerinden", govde, re.I)
    mahalle = None
    if mahalle_ham := (mah.group(1).strip() if mah else None):
        mahalle = re.sub(r"^(?:İlimiz|Gümüşhane)\s+", "", mahalle_ham, flags=re.I)
    cum = None
    c = re.search(r"Cenaze", govde)
    if c:
        cum = govde[c.start():]
        cum = re.split(r"Merhum\w*\s+[Cc]enab|[Cc]enab|Taziye|TAZ[İI]YE|Tel\b|TEL\b", cum)[0]
        cum = re.sub(r"\(?\+?\d[\d\s()\-]{8,}\d", "", cum)
        cum = " ".join(cum.split()).strip() or None
    return mahalle, cum


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(ANA + "/2/duyuru/"):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {g: [] for g in gunler}
    alindi = ortak.simdi_iso()
    gor = set()
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        try:
            ogeler = liste_ayristir(ortak.indir(LISTE.format(sayfa_no)))
        except Exception as e:
            print(f"HATA liste sayfa {sayfa_no}: {e}", file=sys.stderr)
            break
        if not ogeler:
            break
        for o in ogeler:
            if not o["tarih"] or o["tarih"] not in by_gun:
                continue
            url = ANA + o["href"] if o["href"].startswith("/") else o["href"]
            ad = ad_cikar(o["baslik"])
            try:
                mahalle, cum = ayrinti_ayristir(ortak.indir(url))
            except Exception as e:
                print(f"HATA ayrıntı {url}: {e}", file=sys.stderr)
                mahalle = cum = None
            k = {
                "id": ortak.kayit_id("gumushane", ad, o["tarih"], o["href"]),
                "il": IL, "ilce": None,
                "mahalle": ortak.tr_title(mahalle) if mahalle else None,
                "ad_soyad": ortak.tr_title(ad),
                "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
                "defin_yeri": None, "defin_zamani": None, "namaz_tarihi": None,
                "namaz_yeri_vakti": cum,
                "liste_tarihi": o["tarih"],
                "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
                "ham": {"baslik": o["baslik"], "mahalle_ham": mahalle},
            }
            if k["id"] not in gor:
                gor.add(k["id"])
                by_gun[o["tarih"]].append(k)
        if all(o["tarih"] and o["tarih"] < gunler[-1] for o in ogeler):
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
