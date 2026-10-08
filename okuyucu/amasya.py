#!/usr/bin/env python3
"""Amasya: belediye kaynağı yok (il ve ilçe belediyelerinde liste yok) -> YEREL BASIN (site sahibi kararı 08.10.2026).
- Merzifon Bilgi Gazetesi: `merzifonbilgigazetesi.com/vefat-edenler/<gün>-aramizdan-ayrilanlar/<id>` ("D Ay YYYY Aramızdan
  Ayrılanlar", 1-3 günde bir). Sayfa "<İlçe> Vefat Edenler" başlıklarıyla bölünür (Amasya merkez -> ilçe belirsiz; Merzifon ...).
  Dizin: `sitemap_news.xml` (tek istek). Alınan: ad soyad, cami + vakit (kısa), mezarlık, köy/mahalle; tarih "Cenazesi bugün" ise
  sayfa günü namaz günüdür. Yakın adları, taziye, telefon ALINMAZ.
Kaynak türü yerel_basin; site başına günde en çok 3 istek (ortak_basin). Kullanım: python3 okuyucu/amasya.py [--gun 7]
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_basin as ob, ortak_ilce as oi

IL = "Amasya"
MERZIFON_HARITA = "https://www.merzifonbilgigazetesi.com/sitemap_news.xml"


def merzifon_bilgi(ctx):
    xml = ob.dizin(ctx, MERZIFON_HARITA)
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if "/vefat-edenler/" in u and "aramizdan-ayrilanlar" in u]

    def ayristir(sayfa, url, gun):
        gun = ob.yayin_tarihi(sayfa) or gun
        return ob.serbest_kayitlar(ctx, IL, "amasya-merzifonbilgi", "Merzifon Bilgi Gazetesi", url, gun,
                                   ob.makale_govdesi(sayfa), ilce_basliklari=True)
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def main():
    oi.il_calistir(IL, "amasya", [("Merzifon Bilgi Gazetesi", merzifon_bilgi)])


if __name__ == "__main__":
    main()
