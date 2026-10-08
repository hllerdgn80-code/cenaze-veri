#!/usr/bin/env python3
"""Siirt: belediye kaynağı yok -> YEREL BASIN (site sahibi kararı 08.10.2026). Her site ayrı kaynak:
- Artı Siirt: "Siirt'te Vefat ve Taziyeler - D Ay YYYY" (günlük; sayfa BİRİKEN listedir, en yeni sayfa yeterli). Yalnız açık tarihi
  olan ilanlar alınır (tarih_zorunlu). Dizin `sitemap_google_news.xml`.
- Siirt Haberci (siirthaberci.com): "Siirt'te Vefat ve Taziye Duyuruları – D Ay YYYY". Dizin `sitemap-news.xml`.
- Kurtalan Gazetesi: "Kurtalan'da Bugün Vefat Edenler – D Ay YYYY" (ilçe Kurtalan). Dizin `xml/sitemap_0.xml`.
İlanlarda telefon, taziye evi ve yakın adları var: ALINMAZ; yalnız ad soyad, tarih, ilçe (metnin başında resmî ilçe adı), köy,
cami + vakit, mezarlık. Kadınların adı çoğu ilanda yazılmaz ("... annesi Hakk'ın rahmetine kavuştu"): adı olmayan ilan alınmaz.
Site başına günde en çok 3 istek (ortak_basin). Kullanım: python3 okuyucu/siirt.py [--gun 7] [--ilce "Artı Siirt"]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_basin as ob, ortak_ilce as oi

IL = "Siirt"


def arti_siirt(ctx):
    xml = ob.dizin(ctx, "https://www.artisiirt.com/sitemap_google_news.xml")
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if re.search(r"vefat-ve-taziye", u)]

    def ayristir(sayfa, url, gun):
        return ob.serbest_kayitlar(ctx, IL, "siirt-artisiirt", "Artı Siirt", url, ob.yayin_tarihi(sayfa) or gun,
                                   ob.makale_govdesi(sayfa), tarih_zorunlu=True)
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=1)


def siirt_haberci(ctx):
    xml = ob.dizin(ctx, "https://www.siirthaberci.com/sitemap-news.xml")
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if re.search(r"vefat-ve-taziye|vefat-edenler", u)]

    def ayristir(sayfa, url, gun):
        return ob.serbest_kayitlar(ctx, IL, "siirt-siirthaberci", "Siirt Haberci", url, ob.yayin_tarihi(sayfa) or gun,
                                   ob.makale_govdesi(sayfa))
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def kurtalan_gazetesi(ctx):
    xml = ob.dizin(ctx, "https://www.kurtalangazetesi.com/xml/sitemap_0.xml")
    if xml is None:
        return []
    sayfalar = [(u, ob.metinden_tarih(u.replace("-", " "))) for u, t, g in ob.harita_ogeleri(xml) if "bugun-vefat-edenler" in u]

    def ayristir(sayfa, url, gun):
        return ob.serbest_kayitlar(ctx, IL, "siirt-kurtalan", "Kurtalan Gazetesi", url, gun or ob.yayin_tarihi(sayfa),
                                   ob.makale_govdesi(sayfa), varsayilan_ilce="Kurtalan")
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def main():
    oi.il_calistir(IL, "siirt", [("Artı Siirt", arti_siirt), ("Siirt Haberci", siirt_haberci), ("Kurtalan Gazetesi", kurtalan_gazetesi)])


if __name__ == "__main__":
    main()
