#!/usr/bin/env python3
"""Bitlis: belediye kaynağı yok -> YEREL BASIN (site sahibi kararı 08.10.2026).
- Bitlis Haber (bitlishaber13.net): "Bitlis merkez ve ilçelerde vefat edenler" / "Bitlis'te vefat edenler (N vefat)" derleme
  yazıları (2-5 günde bir; 08.10.2026'da son derleme 30.09 -> İZLEMEDE, pencerede 0 kayıt normaldir). Dizin: kategori RSS'i
  `/rss/vefat-edenler` (tek istek); RSS'teki tekil "X vefat etti" haberleri ALINMAZ, yalnız derleme yazıları.
  Alınan: ad soyad, cami, mezarlık; yakın adı/telefon/taziye ALINMAZ. Gün = yazı günü.
Site başına günde en çok 3 istek (ortak_basin). Kullanım: python3 okuyucu/bitlis.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_basin as ob, ortak_ilce as oi

IL = "Bitlis"


def bitlis_haber(ctx):
    xml = ob.dizin(ctx, "https://www.bitlishaber13.net/rss/vefat-edenler")
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if re.search(r"vefat edenler", ortak.tr_lower(t))]

    def ayristir(sayfa, url, gun):
        return ob.serbest_kayitlar(ctx, IL, "bitlis-bitlishaber", "Bitlis Haber", url, ob.yayin_tarihi(sayfa) or gun,
                                   ob.makale_govdesi(sayfa))
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def main():
    oi.il_calistir(IL, "bitlis", [("Bitlis Haber", bitlis_haber)])


if __name__ == "__main__":
    main()
