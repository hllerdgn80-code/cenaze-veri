#!/usr/bin/env python3
"""Samsun: yalnız ilçe düzeyinde kaynak var -> 19 Mayıs Belediyesi (Samsun BŞB'nin ve diğer ilçelerin listesi yok).
19 Mayıs: `19mayis.bel.tr/cenaze-ilanlari?tarih=YYYY-AA-GG` gün parametreli tablo (Cenaze Adı, Cenaze Yakını, İrtibat Telefonu,
Defin Vakti, Mezarlık, Camii). YAKIN ADI ve TELEFON ALINMAZ. robots.txt yok (404).
İstek sayısını küçük tutmak için son 2 gün her çalışmada, daha eski günler yalnız bir kez (ilk kurulum) okunur (veri/samsun/_tarama.json).
Kullanım: python3 okuyucu/samsun.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Samsun"
URL = "https://www.19mayis.bel.tr/cenaze-ilanlari?tarih={}"


def ondokuz_mayis(ctx):
    sonuc = []
    for gun in ctx["durum"].okunacak("19 Mayıs", ctx["gunler"], her_zaman=2):
        url = URL.format(gun)
        sayfa = oi.al(url)
        govde = sayfa.split("<tbody>", 1)[-1].split("</tbody>", 1)[0]
        for tr in re.findall(r"<tr[\s\S]*?</tr>", govde):
            h = {a: oi.metin(v) for a, v in re.findall(r'data-label="([^"]+)"[^>]*>([\s\S]*?)</td>', tr)}
            ad = oi.ad_duzelt(h.get("Cenaze Adı", ""))
            if not ad:
                continue                         # "Seçilen tarihe ait cenaze ilanı bulunamadı." satırı
            vakit, camii, mezarlik = h.get("Defin Vakti", ""), h.get("Camii", ""), h.get("Mezarlık", "")
            namaz = " / ".join(x for x in (oi.buyuk_ise_title(camii), vakit) if x) or None
            sonuc.append(oi.kayit(IL, "19 Mayıs", "samsun-19mayis", ad, gun, "19 Mayıs Belediyesi", url, ctx["alindi"],
                                  defin_yeri=oi.buyuk_ise_title(mezarlik, yer=True) or None, defin_zamani=gun,
                                  namaz_tarihi=gun, namaz_yeri_vakti=namaz, liste_tarihi=gun, ham={}))
        ctx["durum"].isaretle("19 Mayıs", gun)
    return sonuc


def main():
    oi.il_calistir(IL, "samsun", [("19 Mayıs", ondokuz_mayis)])


if __name__ == "__main__":
    main()
