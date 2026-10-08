#!/usr/bin/env python3
"""İzmir: İzmir BŞB'nin il geneli listesi e-Devlet'te (belediyeden izin gerekir) -> burada YALNIZ web sayfasında liste yayımlayan 3 ilçe (her biri ayrı kaynak):
- Bayındır: `bayindir.bel.tr/guncel/vefat-ilanlari` tek sayfa, ~2.000 satır (2,2 MB), yeniden eskiye: parça parça okunur, pencere dışına çıkınca kesilir (tek istek).
  Sütunlar: sıra, vefat eden, defin tarihi, camii, cenaze namazı vakti. Ayrıntı ("Gör") sayfaları açılmaz (yakın bilgisi içerebilir).
- Ödemiş: `odemis.bel.tr/cenaze-ilanlari?page=N` (ad, ilan tarihi, ilan metni; yalnız "Cenazesi ..." cümlesi alınır, yakın adları ALINMAZ).
- Torbalı: `torbali.bel.tr/aramizdan-ayrilanlar` tek sayfa, 6.000+ ilan (3,3 MB), yeniden eskiye: parça parça okunur (tek istek). Tarih, ad, camii/vakit, açıklama
  ("... Cenazesi X Mezarlığı'na defnedilecektir").
Gün = defin tarihi (Bayındır) / ilan tarihi (Ödemiş, Torbalı). Kullanım: python3 okuyucu/izmir.py [--gun 7] [--ilce Torbalı]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi, ortak_haber as oh

IL = "İzmir"

# YEREL HABER (08.10.2026): il geneli tek kişilik vefat haberleri (ortak_haber; site başına günde en çok 3 istek)
HABER_SITELERI = [
    oh.site("Yeni Bakış", "izmir-yenibakis", "https://www.yenibakishaber.com/rss", ek_dizin="https://www.yenibakishaber.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Ege Telgraf", "izmir-egetelgraf", "https://www.egetelgraf.com/rss", ek_dizin="https://www.egetelgraf.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Dokuz Eylül", "izmir-dokuzeylul", "https://www.dokuzeylul.com/rss", ek_dizin="https://www.dokuzeylul.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Son Mühür", "izmir-sonmuhur", "https://www.sonmuhur.com/rss", ek_dizin="https://www.sonmuhur.com/sitemap/sitemap-{AY}.xml"),
]

BAYINDIR = "https://www.bayindir.bel.tr/guncel/vefat-ilanlari"


def bayindir(ctx):
    bas = ctx["gunler"][-1]

    def yeterli(txt):
        d = [oi.tarih(x) for x in re.findall(r"<td[^>]*>\s*(\d\d-\d\d-\d{4})\s*</td>", txt)]
        d = [x for x in d if x]
        return len(d) >= 3 and all(x < bas for x in d[-3:])
    sayfa = oi.al_parca(BAYINDIR, yeterli)
    sonuc = []
    for tr in re.findall(r"<tr[\s\S]*?</tr>", sayfa):
        h = oi.hucreler(tr)
        if len(h) < 5 or not re.match(r"^\d+$", h[0]):
            continue
        sira, ad, defin, camii, vakit = h[0], oi.ad_duzelt(h[1]), oi.tarih(h[2]), h[3].strip(" ."), h[4]
        if not ad or not oi.pencerede(defin, ctx["gunler"]):
            continue
        sonuc.append(oi.kayit(IL, "Bayındır", "izmir-bayindir", ad, defin, "Bayındır Belediyesi", BAYINDIR, ctx["alindi"], ek_id=sira,
                              defin_zamani=defin, namaz_tarihi=defin,
                              namaz_yeri_vakti=" / ".join(x for x in (oi.buyuk_ise_title(camii, yer=True), vakit) if x) or None,
                              liste_tarihi=defin, ham={"sira": sira}))
    return sonuc


ODEMIS = "https://www.odemis.bel.tr/cenaze-ilanlari"


def odemis(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa)
        liste = []
        for s in satirlar:
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
            gun = oi.tarih(oi.kolon(baslik, s, "İlan Tarihi"))
            txt = oi.kolon(baslik, s, "İlan Metni")
            namaz, defin = oi.cenaze_ayikla(txt)
            if not ad or not gun:
                continue
            liste.append(oi.kayit(IL, "Ödemiş", "izmir-odemis", ad, gun, "Ödemiş Belediyesi", ODEMIS, ctx["alindi"],
                                  il_disi_metin=txt, mahalle=oi.mahalle_ayikla(txt), defin_yeri=defin,
                                  namaz_tarihi=gun if namaz else None, namaz_yeri_vakti=namaz, liste_tarihi=gun,
                                  ham={"ilan_tarihi": gun}))
        return liste
    return oi.sayfala(lambda n: ODEMIS if n == 1 else f"{ODEMIS}?page={n}", ayristir, ctx["gunler"], azami_sayfa=3)


TORBALI = "https://www.torbali.bel.tr/aramizdan-ayrilanlar"


def torbali(ctx):
    bas = ctx["gunler"][-1]

    def _doc_tarih(a):
        g, ay_yil = a
        return oi.tarih(f"{g} {ay_yil}")

    def yeterli(txt):
        d = [x for x in (_doc_tarih(a) for a in re.findall(r'doc-date-day">(\d+)</span>\s*<span class="doc-date-year">([^<]+)<', txt)) if x]
        return len(d) >= 3 and all(x < bas for x in d[-3:])
    sayfa = oi.al_parca(TORBALI, yeterli)
    sonuc = []
    for it in re.findall(r'<a class="doc-item">([\s\S]*?)</a>', sayfa):
        m = re.search(r'doc-date-day">(\d+)</span>\s*<span class="doc-date-year">([^<]+)<', it)
        gun = _doc_tarih(m.groups()) if m else None
        ad = oi.ad_duzelt((re.search(r'doc-title[^>]*>([\s\S]*?)</div>', it) or [None, ""])[1])
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        camii = oi.metin((re.search(r"<b>Camii:</b>([\s\S]*?)<b>", it) or [None, ""])[1]).strip(" /")
        acik = oi.metin((re.search(r"<b>Açıklama:</b>([\s\S]*)", it) or [None, ""])[1])
        kalan = re.sub(r"^.*?başsağlığı dileriz\.?", "", acik, flags=re.I).strip()
        _, defin = oi.cenaze_ayikla(kalan if re.search(r"cena[sz]e", kalan, re.I) else "Cenazesi " + kalan)
        camii = re.sub(r"\s*/\s*", " / ", camii)
        sonuc.append(oi.kayit(IL, "Torbalı", "izmir-torbali", ad, gun, "Torbalı Belediyesi", TORBALI, ctx["alindi"],
                              il_disi_metin=acik, defin_yeri=defin, namaz_tarihi=gun, namaz_yeri_vakti=oi.buyuk_ise_title(camii, yer=True) or None,
                              liste_tarihi=gun, ham={"ilan_tarihi": gun}))
    return sonuc


def main():
    oi.il_calistir(IL, "izmir", [("Bayındır", bayindir), ("Ödemiş", odemis), ("Torbalı", torbali)] + oh.okuyucular(IL, HABER_SITELERI))


if __name__ == "__main__":
    main()
