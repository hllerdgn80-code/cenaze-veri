#!/usr/bin/env python3
"""PASİF (13.10.2026): kaynak bot istemcilerine CAPTCHA gösteriyor (/Auth/Captcha) -> dolanılmaz; hepsi.py ILLER'de DEĞİL. Sakarya için ilçe belediyeleri (Erenler, Arifiye, Hendek) araştırılıyor.
Sakarya Büyükşehir Belediyesi MEBİS "Bugün Vefat Edenler" okuyucusu (yalnız standart kütüphane). 13.10.2026.
Kaynak: https://mebis.sakarya.bel.tr/BugunVefatEdenler — il geneli RESMÎ liste (akordeon; sayfa başına ~27 kayıt, son 1-2 gün).
Her kayıt: ad (info-name), "İLÇE - MAHALLE" (info-place), Doğum/Ölüm Tarihi, Mezarlık, Cami, Vakit (öğle/ikindi...). Telefon/yakın/ölüm nedeni yok.
Liste yalnız son günleri tuttuğu için her turda kayıtlar gün dosyalarına BİRLEŞTİRİLİR (kaynaktan düşen kayıt silinmez). robots.txt yok (404).
Kullanım: python3 okuyucu/sakarya.py
"""
import html, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Sakarya"
URL = "https://mebis.sakarya.bel.tr/BugunVefatEdenler"
KAYNAK_AD = "Sakarya Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "sakarya")


def alan(blok, etiket):
    m = re.search(re.escape(etiket) + r':\s*<span class="info">(.*?)</span>', blok, re.S)
    return ortak_ek.metin(m.group(1)) if m else None


def ayristir(sayfa):
    sayfa = html.unescape(sayfa)
    sonuc = []
    for blok in re.split(r'<div class="accordion-item"', sayfa)[1:]:
        ad = re.search(r'<span class="info-name">(.*?)</span>', blok, re.S)
        yer = re.search(r'<span class="info-place">(.*?)</span>', blok, re.S)
        vefat = ortak_ek.tarih_gg_aa_yyyy(alan(blok, "Ölüm Tarihi"))
        if not (ad and vefat):
            continue
        yer = ortak_ek.metin(yer.group(1)) if yer else ""
        ilce, _, mah = yer.partition(" - ")
        sonuc.append({"ad": ortak_ek.metin(ad.group(1)), "ilce": ilce.strip() or None, "mahalle": mah.strip() or None,
                      "dogum": ortak_ek.tarih_gg_aa_yyyy(alan(blok, "Doğum Tarihi")), "vefat": vefat,
                      "mezarlik": alan(blok, "Mezarlık"), "cami": alan(blok, "Cami"), "vakit": alan(blok, "Vakit")})
    return sonuc


def yas(dogum, vefat):
    if not dogum:
        return None
    d, v = [tuple(map(int, x.split("-"))) for x in (dogum, vefat)]
    a = v[0] - d[0] - ((v[1], v[2]) < (d[1], d[2]))
    return a if 0 <= a <= 125 else None


def kayda_cevir(r, alindi):
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("sakarya", r["ad"], r["vefat"], r["dogum"] or ""),
        ilce=ortak.tr_title(r["ilce"]) if r["ilce"] else None,
        mahalle=ortak.tr_title(r["mahalle"]) if r["mahalle"] else None,
        ad_soyad=ortak.tr_title(r["ad"]), yas=yas(r["dogum"], r["vefat"]), dogum_tarihi=r["dogum"], vefat_tarihi=r["vefat"],
        defin_yeri=r["mezarlik"],
        namaz_yeri_vakti=" - ".join(x for x in (r["vakit"], r["cami"]) if x) or None,
        liste_tarihi=r["vefat"],
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    liste = ayristir(ortak.indir(URL))
    if not liste:
        raise RuntimeError("Liste bulunamadı (sayfa düzeni değişmiş olabilir)")
    alindi = ortak.simdi_iso()
    by_gun, gorulen = {}, set()
    for r in liste:
        k = kayda_cevir(r, alindi)
        if r["vefat"] in gunler and k["id"] not in gorulen:
            gorulen.add(k["id"])
            by_gun.setdefault(r["vefat"], []).append(k)
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
