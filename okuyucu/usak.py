#!/usr/bin/env python3
"""Uşak Belediyesi cenaze ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.usak.bel.tr/cenaze-ilanlari (sayfalama: /cenaze-ilanlari/2, /3 ...; sayfa başına 12, en yeni üstte).
Her ilan: tarih kutusu (ilan günü), ad (h5) ve serbest metin ("X vefat etmiştir. Cenazesi <vakit> namazına müteakip <cami>'nden alınarak <yer>
defnedilecektir. Merhuma Allah'tan rahmet ..."). Metinde yakın/telefon yok; yalnız cami + vakit + defin yeri alınır.
Not: robots.txt yalnız tek bir ilan sayfasını (/cenaze-ilani/beyhan-kilinc) yasaklar; liste sayfaları serbest, ilan ayrıntı sayfalarına GİRİLMEZ.
Metinde hangi gün olduğu yazmaz: ilan günü liste_tarihi'ne yazılır, vefat/defin/namaz tarihi null. İlçe kaynakta yok -> ilce_belirsiz.
Kullanım: python3 okuyucu/usak.py
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Uşak"
URL = "https://www.usak.bel.tr/cenaze-ilanlari"
KAYNAK_AD = "Uşak Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "usak")
EN_COK_SAYFA = 6

_SON_EK = [("ında", "ı"), ("inde", "i"), ("unda", "u"), ("ünde", "ü"), ("ına", "ı"), ("ine", "i"), ("una", "u"), ("üne", "ü"),
           ("nda", "ı"), ("nde", "i")]


def yalin(yer):
    """'Şekerevleri Mezarlığına' -> 'Şekerevleri Mezarlığı' (yönelme/bulunma eki atılır; ham metin ham'da kalır)."""
    kelimeler = yer.split()
    if not kelimeler:
        return yer
    son = kelimeler[-1]
    if re.search(r"[’']", son):          # "Köyü'nde" -> "Köyü" (kesme işaretinden sonrası ektir; 08.10.2026: "Köyü'i" hatası)
        kelimeler[-1] = re.split(r"[’']", son)[0]
        return " ".join(kelimeler)
    for ek, yerine in _SON_EK:
        if tr_ends(son, ek) and len(son) > len(ek) + 2:
            kelimeler[-1] = son[: -len(ek)] + yerine
            break
    return " ".join(kelimeler)


def tr_ends(s, ek):
    return ortak.tr_lower(s).endswith(ek)


def ayristir(sayfa):
    """13.10.2026: site yeniden tasarlandi. Liste sayfasi gun bloklari: <div class="fun-day"><h3><b>13 Ekim 2026 Sali</b>3 ilan</h3> ... <a class="fun" href="/cenaze-ilani/slug"> ... <b>Ad Soyad</b>.
    Namaz/defin cumlesi ILAN SAYFASINDA (robots.txt artik yalniz /manage/ ve /install'i yasaklar): ayristir_ayrinti."""
    sonuc = []
    for blok in re.split(r'<div class="fun-day">', sayfa)[1:]:
        bas = re.search(r"<h3><b>(\d{1,2}\s+\w+\s+\d{4})", blok)
        gun = ortak.tarih_iso(bas.group(1)) if bas else None
        if not gun:
            continue
        for ad, slug in [(m.group(2), m.group(1)) for m in re.finditer(r'<a class="fun" href="/cenaze-ilani/([^"]+)">.*?<b>(.*?)</b>', blok, re.S)]:
            sonuc.append({"gun": gun, "ad": ortak_ek.metin(ad), "slug": slug, "metin": None})
    return sonuc


def ayristir_ayrinti(sayfa):
    """Ilan sayfasi: <div class="prose"><p>Ad vefat etmistir. Cenazesi ... defnedilecektir. <span>...</span></p>. Yakin adi/telefon yok; yalniz cumle."""
    p = re.search(r'<div class="prose"><p>(.*?)</p>', sayfa, re.S)
    return ortak_ek.metin(re.sub(r"<span>.*?</span>", "", p.group(1), flags=re.S)) if p else ""


def cenaze_cumlesi(metin):
    """'... Cenazesi ikindi namazına müteakip Mutafa Camii'nden alınarak Şekerevleri Mezarlığına defnedilecektir. ...' ->
    (namaz_yeri_vakti, defin_yeri)."""
    m = re.search(r"Cenazesi\s+(.*?)\s+defnedilecektir", metin, re.I)
    if not m:
        return None, None
    c = m.group(1)
    defin = c
    if "alınarak" in c:
        defin = c.split("alınarak", 1)[1]
    elif "müteakip" in c:
        defin = c.split("müteakip", 1)[1]
    defin = defin.strip(" ,")
    return c, yalin(defin) or None


def kayda_cevir(r, alindi):
    namaz, defin = cenaze_cumlesi(r["metin"])
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("usak", r["ad"], r["gun"], r["slug"] or ""),
        ad_soyad=ortak.tr_title(r["ad"]),
        defin_yeri=defin,
        namaz_yeri_vakti=namaz,
        liste_tarihi=r["gun"],
        ham={"slug": r["slug"]},     # KVKK: ilan metni yakın adlarını taşıyabilir ("X, Y'nin annesi"), saklanmaz (08.10.2026)
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    alindi = ortak.simdi_iso()
    by_gun, gorulen = {}, set()
    for sayfa_no in range(1, EN_COK_SAYFA + 1):
        url = URL if sayfa_no == 1 else f"{URL}/{sayfa_no}"
        kayitlar = ayristir(ortak.indir(url))
        if not kayitlar:
            if sayfa_no == 1:
                raise RuntimeError("İlan bulunamadı (sayfa düzeni değişmiş olabilir)")
            break
        for r in kayitlar:
            if r["gun"] in gunler and not r["metin"]:                       # ayrinti sayfasi yalniz 7 gun penceresi icin
                try:
                    r["metin"] = ayristir_ayrinti(ortak.indir("https://www.usak.bel.tr/cenaze-ilani/" + r["slug"]))
                except Exception:
                    r["metin"] = ""
            r["metin"] = r["metin"] or ""
            k = kayda_cevir(r, alindi)
            if r["gun"] in gunler and k["id"] not in gorulen:
                gorulen.add(k["id"])
                by_gun.setdefault(r["gun"], []).append(k)
        if min(r["gun"] for r in kayitlar) < gunler[-1]:      # 7 günün dışına çıkıldı
            break
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
