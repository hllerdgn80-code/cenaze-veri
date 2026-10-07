#!/usr/bin/env python3
"""Isparta Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane; İSAY "custom-table" şablonu).
Kaynak: https://www.isparta.bel.tr/vefat-ilanlari (tek sayfa, yalnız GÜNCEL ilanlar, tarih parametresi yok).
Önceki günler kendi dosyalarımızdan tamamlanır (ortak.liste_birikim; kayıt ilk görüldüğü güne yazılır, geçmiş yeni kurulumda boştur).
Sütunlar: AD SOYAD, ADRES, NAMAZ YERİ, DEFİN YERİ, "TARİH / VAKİT" (namaz tarihi / vakti).
KVKK: ADRES alanından yalnız mahalle adı alınır (sokak, kapı no atılır). İlçe: defin yeri "İLÇE / ... MEZARLIĞI" ise ya da adres/mezarlık
adı tek başına bir ilçe/il ise; Merkez mezarlıklarında ilçe yazmaz -> ilce None + ilce_belirsiz (tahmin yok).
Kullanım: python3 okuyucu/isparta.py
"""
import html, os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Isparta"
URL = "https://www.isparta.bel.tr/vefat-ilanlari"
KAYNAK_AD = "Isparta Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "isparta")
KISALTMA = {"Ş.KARAAĞAÇ": "Şarkikaraağaç"}   # kaynaktaki kısaltma


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").split())


def ayristir(sayfa):
    kayitlar = []
    for satir in re.findall(r'<div class="custom-table-row">(.*?)(?=<div class="custom-table-row">|</div>\s*</div>\s*</div>)', sayfa, re.S):
        h = {ortak.tr_lower(a): metin(v) for a, v in re.findall(r'data-header="([^"]+)">(.*?)</div>', satir, re.S)}
        if h.get("ad soyad"):
            kayitlar.append(h)
    return kayitlar


def baslik(s):
    """tr_title + kısaltma sonrası harf büyütme: 'H.sultan' -> 'H.Sultan'."""
    t = ortak.tr_title(s)
    return re.sub(r"\.([a-zçğıöşüi])", lambda m: "." + {"i": "İ", "ı": "I"}.get(m.group(1), m.group(1).upper()), t)


def mahalle_cikar(adres):
    m = re.match(r"^(.*?)\s*MAH(?:ALLES[İI])?\.?(?=\s|\d|$|\.)", adres or "", re.I)
    return m.group(1).strip() if m and m.group(1).strip() else None


def ilce_ham_bul(adres, defin):
    """Kayda yazılacak ham ilçe değeri (ilce_isle çözer) ya da None."""
    d = (defin or "").strip()
    if "/" in d:
        p = [x.strip() for x in d.split("/") if x.strip()]
        ilk = KISALTMA.get(p[0], p[0])
        return " / ".join([ilk] + p[1:2]) if p else None
    ad = re.sub(r"\s*MEZARLI[ĞG]I\s*$", "", d, flags=re.I).strip()
    for aday in (ad, (adres or "").strip()):
        k = ortak.katla(aday)
        if k and (any(ortak.katla(x) == k for x in ortak.ilce_listesi(IL))
                  or any(ortak.katla(x) == k for x in ortak.ilce_verisi()["_iller"])):
            return aday
    return None


def kayda_cevir(h, gun, alindi):
    ad = h["ad soyad"]
    adres, namaz, defin = h.get("adres"), h.get("namaz yeri"), h.get("defin yeri")
    for kisa, uzun in KISALTMA.items():
        if defin and kisa in defin:
            defin = defin.replace(kisa, uzun.upper().replace("I", "İ") if False else uzun)
    tv = h.get("tarih / vakit", "")
    tar_ham, _, vakit = (x.strip() for x in tv.partition("/"))
    mt = re.match(r"^(\d{2}\.\d{2}\.\d{4})", tar_ham)
    namaz_tarihi = ortak.tarih_iso(mt.group(1)) if mt else None
    ilce_ham = ilce_ham_bul(adres, defin)
    mahalle = mahalle_cikar(adres)
    return {
        "id": ortak.kayit_id("isparta", ad, namaz_tarihi or gun, f"{defin or ''}|{namaz or ''}"),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,
        "mahalle": baslik(mahalle) if mahalle else None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": baslik(defin) if defin else None,
        "defin_zamani": namaz_tarihi,
        "namaz_tarihi": namaz_tarihi,
        "namaz_yeri_vakti": " – ".join(x for x in (vakit, namaz) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": URL, "alindi": alindi,
        "ham": {"adres_mahalle": mahalle, "adres_ilce_ya_da_yer": adres if not mahalle else None,
                "namaz_yeri": namaz, "defin_yeri": defin, "tarih_vakit": tv or None},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today().isoformat()
    ham = ayristir(ortak.indir(URL))
    alindi = ortak.simdi_iso()
    yeni = [kayda_cevir(h, bugun, alindi) for h in ham]
    gunler, by_gun = ortak.liste_birikim(KOK, IL, bugun, yeni)
    for g in gunler:
        if by_gun[g] or os.path.exists(os.path.join(KOK, f"{g}.json")):
            ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt" + (f" (sayfada {len(ham)} satır)" if g == bugun else ""))
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
