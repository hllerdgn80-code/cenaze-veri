#!/usr/bin/env python3
"""Kırıkkale Belediyesi "Kaybettiklerimiz" duyuru listesi okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.kirikkale.bel.tr/?sayfa=kaybettiklerimiz[&page=N] (sunucuda üretilen HTML, sayfa başına 25 duyuru).
Duyurular serbest metindir: "<AD SOYAD> (YAŞ 83) VEFAT ETMİŞTİR. CENAZESİ ÖĞLE NAMAZINA MÜTEAKİBEN <YER> KALDIRILACAKTIR. - Tarih : 4.10.2026".
Ad alanının başında memleket/köy öneki olabilir ("KALECİKLİ ...", "ORDU FATSALI ..."): ayrıştırılamaz, tam metin ad_soyad'a yazılır,
ham.ad_ham'da korunur ve ham.ad_notu ile işaretlenir. Kaynakta İLÇE YOK: ilce None + ilce_belirsiz (cami/köy adından çıkarılmaz).
Ad içermeyen duyurular (ör. "personelimizin abisi vefat etmiştir") KVKK gereği alınmaz. Son 7 günün duyuruları sayfalardan okunur.
Kullanım: python3 okuyucu/kirikkale.py
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kırıkkale"
URL = "https://www.kirikkale.bel.tr/?sayfa=kaybettiklerimiz"
KAYNAK_AD = "Kırıkkale Belediyesi"
BEKLE = 3.5
MAKS_SAYFA = 4
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kirikkale")
VAKIT = r"(?:SABAH|ÖĞLE|İKİNDİ|AKŞAM|YATSI|CUMA|BAYRAM)\s+NAMAZ\w*(?:\s+M[ÜU]TEAK[İI]BEN)?"


def duyurular(sayfa):
    ps = re.findall(r'<p Style[^>]*>(.*?)</p>', sayfa, re.S | re.I)
    return [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", p)).split()) for p in ps]


def yer_temizle(y):
    """'HASANDEDE KÖYÜNDEN' -> 'HASANDEDE KÖYÜ' (yalnız ad-çıkma eki); öbürleri aynen."""
    y = y.strip(" .")
    return re.sub(r"(CAM[İI][İI]|KÖYÜ|MAH\.?|MESC[İI]D[İI])N(DEN|DAN)\b", r"\1", y) if y else y


def ayristir(satir):
    """-> sözlük ya da None (ad içermiyorsa / biçim tanınmıyorsa)."""
    m = re.match(r"^(?P<ad>.+?)\s*\(\s*(?P<yas>[^)]*?)\s*\)\s*VEFAT ET[MN][İI][ŞS]T[İI]R\.?\s*(?P<cenaze>.*?)\s*-\s*Tarih\s*:\s*(?P<tarih>\d{1,2}\.\d{1,2}\.\d{4})\s*$", satir)
    if not m:
        return None
    ym = re.search(r"YA[ŞS]\s*(\d{1,3})", m.group("yas"))
    cenaze = m.group("cenaze")
    vm = re.search(VAKIT, cenaze)
    yer = None
    cm = re.search(r"CENAZES[İI]\s+(?:" + VAKIT + r"\s+)?(?P<yer>.*?)\s*KALDIRILACAKTIR", cenaze)
    if cm:
        yer = yer_temizle(cm.group("yer"))
    return {"ad": m.group("ad"), "yas": int(ym.group(1)) if ym else None, "yas_ham": m.group("yas"),
            "vakit": vm.group(0) if vm else None, "yer": yer or None, "tarih": ortak.tarih_iso(m.group("tarih")), "tarih_ham": m.group("tarih"), "satir": satir}


def _koy_on(ad):
    """Metinde açıkça yazılmış '<YER> KÖYÜNDEN / MAHALLESİNDEN' önekini addan ayırır (08.10.2026 denetimi); yoksa (None, ad)."""
    m = re.match(r"^(?P<yer>.+?)\s+(?P<tur>KÖYÜNDEN|KÖYÜ'NDEN|MAHALLESİNDEN|MAH\.?DEN)\s+(?P<ad>.+)$", ad.strip())
    if not m or not (2 <= len(m.group("ad").split()) <= 5):
        return None, ad
    tur = "Köyü" if "KÖY" in m.group("tur") else "Mahallesi"
    return ortak.tr_title(m.group("yer")) + " " + tur, m.group("ad")


def kayda_cevir(h, url, alindi):
    g = h["tarih"]
    yer_vakit = " – ".join(x for x in (ortak.tr_title(h["vakit"]) if h["vakit"] else None, ortak.tr_title(h["yer"]) if h["yer"] else None) if x) or None
    return {
        "id": ortak.kayit_id("kirikkale", h["ad"], g, h["yas_ham"] + "|" + (h["yer"] or "")),
        "il": IL,
        "ilce": None,                       # kaynakta yok
        "mahalle": _koy_on(h["ad"])[0],     # "KARACALI KÖYÜNDEN HACI ÖMER ÖCAL" -> mahalle "Karacalı Köyü", ad "Hacı Ömer Öcal"
        "ad_soyad": ortak.tr_title(_koy_on(h["ad"])[1]),
        "anne_baba": None,                  # kaynakta yok
        "yas": h["yas"],
        "dogum_tarihi": None,
        "vefat_tarihi": None,               # kaynakta yok; duyuru tarihi liste_tarihi
        "defin_yeri": None,                 # kaynak mezarlık vermez; cenazenin kalkacağı yer namaz_yeri_vakti'nde
        "defin_zamani": None,
        "namaz_tarihi": None,
        "namaz_yeri_vakti": yer_vakit,
        "liste_tarihi": g,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"ad_ham": h["ad"], "ad_notu": "ilk sözcük(ler) memleket/köy öneki olabilir", "yas_ham": h["yas_ham"],
                "vakit": h["vakit"], "cenaze_yeri": h["yer"], "tarih": h["tarih_ham"], "duyuru": h["satir"]},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(7)]
    by_gun = {g: [] for g in gunler}
    goruldu, atlanan = set(), 0
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = URL if sayfa_no == 1 else f"{URL}&page={sayfa_no}"
        satirlar = duyurular(ortak.indir(url, BEKLE))
        alindi = ortak.simdi_iso()
        en_eski = None
        for s in satirlar:
            h = ayristir(s)
            if not h or not h["tarih"]:
                atlanan += 1 if "VEFAT" in s else 0
                continue
            en_eski = h["tarih"] if en_eski is None else min(en_eski, h["tarih"])
            if h["tarih"] in by_gun:
                k = kayda_cevir(h, url, alindi)
                if k["id"] not in goruldu:
                    goruldu.add(k["id"]); by_gun[h["tarih"]].append(k)
        if not satirlar or en_eski is None or en_eski < gunler[-1]:
            break
    for g in gunler:
        ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt")
    if atlanan:
        print(f"ad içermeyen/tanınmayan duyuru atlandı: {atlanan}")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
