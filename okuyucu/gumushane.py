#!/usr/bin/env python3
"""Gümüşhane Belediyesi vefat duyuruları okuyucusu (yalnız standart kütüphane).
Kaynak: https://gumushane.bel.tr/vefat-edenler?page=N (21.10.2026'da eski /2/duyuru/ adresi 404 oldu; kartta metin de var, ayrıntı sayfası gerekmez) (liste: başlık "AD hakkın rahmetine kavuşmuştur" + tarih)
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
ANA = "https://gumushane.bel.tr"
LISTE = ANA + "/vefat-edenler?page={}"
KAYNAK_AD = "Gümüşhane Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "gumushane")
MAKS_SAYFA = 4


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def liste_ayristir(sayfa):
    """21.10.2026: site yeniden tasarlandi (gumushane.bel.tr/vefat-edenler?page=N). Her kart: ad (h3), tarih (rozet), serbest metin (govde).
    -> [{href, baslik, tarih, govde}]"""
    sonuc = []
    for kart in re.split(r'<div class="nh-vefat-card', sayfa)[1:]:
        h = re.search(r'<h3 class="nh-vefat-name[^>]*>(.*?)</h3>', kart, re.S)
        t = re.search(r'bi-calendar-event[^>]*></i>\s*([^<]+)<', kart)
        d = re.search(r'<div class="nh-vefat-desc">(.*?)</div>', kart, re.S)
        if not h:
            continue
        tarih = ortak.tarih_iso(" ".join(metin(t.group(1)).split()[:3])) if t else None
        sonuc.append({"href": None, "baslik": metin(h.group(1)), "tarih": tarih, "govde": metin(d.group(1)) if d else ""})
    return sonuc


def ad_cikar(baslik):
    ad = re.split(r"[,\s]+hak+[ıi]n\s+rahmetine", baslik, flags=re.I)[0].strip(" ,.")
    return ad


def ayrinti_ayristir(govde):
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
    if not ortak.robots_izin(ANA + "/vefat-edenler"):
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
            url = LISTE.format(1).split("?")[0]
            ad = ad_cikar(o["baslik"])
            mahalle, cum = ayrinti_ayristir(o["govde"])
            k = {
                "id": ortak.kayit_id("gumushane", ad, o["tarih"], o["baslik"]),
                "il": IL, "ilce": None,
                "mahalle": ortak.tr_title(mahalle) if mahalle else None,
                "ad_soyad": ortak.tr_title(ad),
                "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
                "defin_yeri": None, "defin_zamani": None,
                # 'Cenazesi bugün ...' = duyurunun yayımlandığı gün (giresun.py ile aynı kural; kapi.py K1)
                "namaz_tarihi": o["tarih"] if cum and re.search(r"\bbugün\b", ortak.tr_lower(cum)) else None,
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
