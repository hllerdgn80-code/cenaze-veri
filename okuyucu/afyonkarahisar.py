#!/usr/bin/env python3
"""Afyonkarahisar Belediyesi cenaze ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.afyon.bel.tr/cenaze-ilanlari (tek sayfa, ~330 ilan, en yeni üstte; kartlar HTML'de hazır).
Alanlar: ilan tarihi/saati, ad, yaş, defin yeri, mahalle, cenaze namazı cümlesi. İlan metnindeki yakın/akraba
sayımı KVKK gereği ALINMAZ. İlçe kaynakta yok -> ilce_belirsiz. Kullanım: python3 okuyucu/afyonkarahisar.py [--gun 7]
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Afyonkarahisar"
URL = "https://www.afyon.bel.tr/cenaze-ilanlari"
KAYNAK_AD = "Afyonkarahisar Belediyesi"
KOK = os.path.join(ortak9.VERI, "afyonkarahisar")
AYRAC = "bg-white border border-slate-200/90 rounded-2xl overflow-hidden flex flex-col md:flex-row"


def kartlar(sayfa):
    for blok in sayfa.split(AYRAC)[1:]:
        blok = blok.split("<script")[0]
        t = re.sub(r"<svg.*?</svg>", "", blok, flags=re.S).replace("<!-- -->", "")
        j = [x.strip() for x in re.split(r"<[^>]+>", t) if x.strip()]
        yield [ortak9.metin(x) for x in j]


def alan(j, etiket):
    for i, x in enumerate(j):
        if x.rstrip(" :") == etiket and i + 1 < len(j):
            return j[i + 1]
    return None


def ayristir(j, alindi):
    if "İlan Tarihi" not in j or "İlan Saati" not in j:
        return None
    i = j.index("İlan Tarihi")
    gun = ortak.tarih_iso(f"{j[i+1]} {j[i+2]}")
    saat = j[j.index("İlan Saati") + 1]
    ad = j[j.index("İlan Saati") + 2]
    yas = None
    for x in j[j.index("İlan Saati") + 3:j.index("İlan Saati") + 5]:
        m = re.match(r"^(\d+)\s*Ya", x)
        if m:
            yas = int(m.group(1))
    defin = alan(j, "Defin Yeri")
    mah = alan(j, "Mahalle")
    if mah:
        mah = re.sub(r"\s+(Mahallesinden|Mahallesi|Mah\.?)$", "", mah)
    namaz = alan(j, "Cenaze Namazı Bilgisi")
    if not (gun and ad):
        return None
    return ortak9.kayit("afyonkarahisar", IL, ortak.tr_title(ad), gun, KAYNAK_AD, URL, alindi,
                        ek_id=saat, ilce=None, mahalle=ortak.tr_title(mahalle_temiz(mah)) if mah else None,
                        yas=yas, defin_yeri=defin, namaz_yeri_vakti=namaz,
                        ham={"ilan_saati": saat, "mahalle_ham": alan(j, "Mahalle")})


def mahalle_temiz(m):
    return m


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    sayfa = ortak.indir(URL, 3.5, timeout=90)
    alindi = ortak.simdi_iso()
    yeni, toplam = {}, 0
    for j in kartlar(sayfa):
        k = ayristir(j, alindi)
        if not k:
            continue
        toplam += 1
        if k["liste_tarihi"] in gl:
            yeni.setdefault(k["liste_tarihi"], []).append(k)
    print(f"sayfada {toplam} ilan, pencerede {sum(len(v) for v in yeni.values())}")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
