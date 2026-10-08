#!/usr/bin/env python3
"""Zonguldak Belediyesi "Vefat İlanları" okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.zonguldak.bel.tr/vefat (gün listesi; /vefat/YYYY-AA-GG gün sayfaları, bir günde birkaç ilan, serbest metin).
Gün sayfasındaki ilan blokları: TAM BÜYÜK HARF AD satırı, ardından "<konum> sakinlerinden,", akraba satırları, "Cenazesi, ..." cümlesi.
KVKK: akraba/yakın satırları ("... eşi", "... dedeleri", "... annesi/kızı") ve aracın kalkacağı yere dair satır ALINMAZ. Yaş kaynakta yok.
Konum satırı (köy/mahalle) `mahalle`ye yazılır; İLÇE kaynakta ayrı verilmez -> ilce None + ilce_belirsiz (konumdan çıkarılmaz).
"bugün"/"yarın" sözcükleri ilan tarihine göre namaz_tarihi'ne çevrilir. Son 7 günün sayfaları okunur.
Kullanım: python3 okuyucu/zonguldak.py
"""
import html, os, re, sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Zonguldak"
URL = "https://www.zonguldak.bel.tr/vefat"
GUN_URL = "https://www.zonguldak.bel.tr/vefat/{}"
KAYNAK_AD = "Zonguldak Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "zonguldak")


def gun_listesi(sayfa):
    return sorted(set(re.findall(r'href="/vefat/(\d{4}-\d{2}-\d{2})"', sayfa)), reverse=True)


def satirlar(sayfa):
    """İlan gövdesi (prose bloğu) -> satır listesi; boş satır '' olarak korunur (isim ayracı)."""
    m = re.search(r'<div class="prose[^"]*">(.*?)</div>', sayfa, re.S)
    if not m:
        return []
    parcalar = re.split(r"<br\s*/?>", m.group(1))
    return [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", p)).split()) for p in parcalar]


def bloklar(satir_listesi):
    """[(ad, [satırlar])]"""
    sonuc, simdiki = [], None
    for i, s in enumerate(satir_listesi):
        sonraki_bos = i + 1 < len(satir_listesi) and satir_listesi[i + 1] == ""
        if s and sonraki_bos and not re.search(r"[a-zçğıöşü]", s) and 2 <= len(s.split()) <= 5 and not re.search(r"\d", s):
            simdiki = (s, [])
            sonuc.append(simdiki)
        elif simdiki and s:
            simdiki[1].append(s)
    return sonuc


def blok_coz(ad, ls, gun):
    konum = None
    cenaze = []
    for s in ls:
        if re.search(r"sakinlerinden\s*,?\s*$", s, re.I):
            konum = re.sub(r"\s*sakinlerinden\s*,?\s*$", "", s, flags=re.I).strip() or None
        elif re.match(r"Cenaze(si|nin)\b", s) and "araç kaldırılacak" not in s.lower():
            cenaze.append(s)
    metin = " ".join(cenaze)
    metin = re.sub(r"^Cenazesi,?\s*", "", metin)
    metin = re.sub(r"\s*Akraba, dost ve tanıdıklarına üzüntüyle duyurulur\.?\s*", " ", metin).strip(" .") 
    namaz_tarihi = None
    t0 = datetime.strptime(gun, "%Y-%m-%d").date()
    if re.search(r"\bbugün\b", metin, re.I):
        namaz_tarihi = gun
    elif re.search(r"\byarın\b", metin, re.I):
        namaz_tarihi = (t0 + timedelta(days=1)).isoformat()
    defin_yeri = None
    dm = re.search(r"((?:[A-ZÇĞİÖŞÜ][^\s,’']*\s+){1,3}(?:[Aa]ile\s+)?)[Mm]ezarlığ", metin)
    if dm:      # yalnız özel adlı mezarlık ("Kandilli Aile Mezarlığı"); "aynı köyde aile mezarlığı" gibi belirsiz ifade alınmaz
        defin_yeri = ortak.tr_title(dm.group(1).strip() + " Mezarlığı")
    return konum, metin or None, namaz_tarihi, defin_yeri


_ADRES = re.compile(r"\b(?:sokak\w*|sk\.|cadde\w*|cd\.|bulvar\w*|apartman\w*|apt\.|no\s*:\s*\d+|daire\s*\d)", re.I)


def kayda_cevir(ad, ls, gun, url, alindi):
    konum, metin, namaz_tarihi, defin_yeri = blok_coz(ad, ls, gun)
    if metin and _ADRES.search(metin):
        # cümlede ev adresi var ("... Köşk Sokak'ta helallik ..."): KVKK, cümle yayımlanmaz, yalnız namaz vakti (kapi.py K4)
        v = re.search(r"\b(sabah|öğle|ikindi|akşam|yatsı|cuma)\s+namaz", ortak.tr_lower(metin))
        metin = (v.group(1) + " namazı") if v else None
    return {
        "id": ortak.kayit_id("zonguldak", ad, gun, (konum or "") + "|" + (metin or "")),
        "il": IL,
        "ilce": None,                        # kaynakta ayrı ilçe alanı yok
        "mahalle": ortak.tr_title(konum) if konum else None,   # "<köy/mahalle> sakinlerinden" satırı
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None,                   # KVKK: akraba satırları alınmaz
        "yas": None,
        "dogum_tarihi": None,
        "vefat_tarihi": None,
        "defin_yeri": defin_yeri,
        "defin_zamani": None,
        "namaz_tarihi": namaz_tarihi,
        "namaz_yeri_vakti": metin,           # "Cenazesi, ..." cümlesi (namaz vakti/yeri ve defin yeri), aynen
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"konum": konum, "cenaze_cumlesi": metin},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(7)]
    liste = gun_listesi(ortak.indir(URL, BEKLE))
    by_gun = {g: [] for g in gunler}
    goruldu = set()
    for g in [x for x in liste if x in by_gun]:
        url = GUN_URL.format(g)
        try:
            sayfa = ortak.indir(url, BEKLE)
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        alindi = ortak.simdi_iso()
        for ad, ls in bloklar(satirlar(sayfa)):
            k = kayda_cevir(ad, ls, g, url, alindi)
            if k["id"] not in goruldu:
                goruldu.add(k["id"]); by_gun[g].append(k)
    for g in gunler:
        ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt" + ("" if g in liste else " (günde ilan yok)"))
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
