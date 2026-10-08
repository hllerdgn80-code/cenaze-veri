#!/usr/bin/env python3
"""Mardin: belediye kaynağı yok -> YEREL BASIN (site sahibi kararı 08.10.2026).
- Mardin Haber Gazetesi: gün sayfası `mardinhaber.com.tr/mardin-vefatlar/GG-AA-YYYY` ("<gün> tarihinde vefat eden hemşehrilerimiz";
  günde ~1-6 ilan). Her ilan kartının özet metninden yalnız ad soyad, ilçe (metnin başındaki resmî ilçe adı), yaş, mezarlık,
  cami + vakit alınır. Telefon, yakın adları, taziye evi ALINMAZ. Gün = sayfa günü (vefat günü).
  Önce hiç okunmamış gün sayfaları, sonra bugün/dün (4 saatte bir) yeniden; günde en çok 3 sayfa, site başına günde en çok 3 istek (ortak_basin).
Kullanım: python3 okuyucu/mardin.py [--gun 7]
"""
import os, re, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_basin as ob, ortak_ilce as oi

IL = "Mardin"
GUN_URL = "https://mardinhaber.com.tr/mardin-vefatlar/{:%d-%m-%Y}"


def mardin_haber(ctx):
    sayfalar = [(GUN_URL.format(datetime.strptime(g, "%Y-%m-%d")), g) for g in ctx["gunler"]]

    def ayristir(sayfa, url, gun):
        h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", sayfa)
        if not h1 and re.search(r"<title>\s*Vefat eden hemşehrilerimiz", sayfa):
            return []                     # o gün için ilan yok (sayfa başlıksız boş liste döner)
        if not h1 or "vefat eden" not in oi.metin(h1.group(1)).lower():
            raise RuntimeError("Mardin Haber gün sayfası tanınmadı (düzen değişmiş olabilir)")
        liste = []
        for a in re.findall(r"<article>([\s\S]*?)</article>", sayfa):
            s = re.search(r'class="sum[^"]*">([\s\S]*?)</div>', a)
            if s:
                liste += ob.serbest_kayitlar(ctx, IL, "mardin-mardinhaber", "Mardin Haber Gazetesi", url, gun, ob.satirlara(s.group(1)))
        return liste
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=3)


def main():
    oi.il_calistir(IL, "mardin", [("Mardin Haber Gazetesi", mardin_haber)])


if __name__ == "__main__":
    main()
