#!/usr/bin/env python3
"""Adıyaman: il belediyesinin listesi yok; ilçe düzeyinde 2 ilçe (her biri ayrı kaynak):
- Besni: `besni.bel.tr/sayfa/VefatEdenler` kartlar: ad, ilan tarihi ("07 Ekim 2026"), yaş, "Defin Yeri" (aslında cenaze cümlesi). YAKINI, YAKINLIĞI,
  TELEFON, TAZİYE ADRESİ ve "Yakınları" ALINMAZ. Gün = ilan tarihi.
- Kâhta: `taziye.kahta.bel.tr` taziye ilanı kartları: ad (parantez içi yakınlık bilgisi atılır), yaş, vefat tarihi. YAKINI GSM ve TAZİYE EVİ
  (adres) ALINMAZ. Kaynakta yazım hatalı tarih olabilir (ör. 27.06.2027): gelecekteki tarihli kayıt atlanır. Gün = vefat tarihi.
Kullanım: python3 okuyucu/adiyaman.py [--gun 7] [--ilce Besni]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Adıyaman"
BESNI = "https://www.besni.bel.tr/sayfa/VefatEdenler"
KAHTA = "https://taziye.kahta.bel.tr/"


def besni(ctx):
    sayfa = oi.al(BESNI)
    bloklar = re.findall(r'<div class="vefattitlesol">([\s\S]*?)</div>\s*<div class="vefattitlesag">([\s\S]*?)</div>'
                         r'([\s\S]*?)<div class="vefatcontent">([\s\S]*?)</div>', sayfa)
    if not bloklar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for ad, tar, _, icerik in bloklar:
        d = {oi.metin(a).strip(" :"): oi.metin(b) for a, b in re.findall(r"<b>([^<]*)</b>([^<]*(?:<br\s*/?>)?)", icerik)}
        ad = oi.ad_duzelt(ad)
        gun = oi.tarih(tar)
        namaz, defin = oi.cenaze_ayikla(d.get("Defin Yeri", ""))
        if not ad or not gun:
            continue
        sonuc.append(oi.kayit(IL, "Besni", "adiyaman-besni", ad, gun, "Besni Belediyesi", BESNI, ctx["alindi"],
                              il_disi_metin=d.get("Defin Yeri", ""), yas=oi.say(d.get("Yaş", "")), defin_yeri=defin, namaz_tarihi=gun if namaz else None,
                              namaz_yeri_vakti=namaz, liste_tarihi=gun, ham={"ilan_tarihi": gun}))
    return sonuc


def kahta(ctx):
    sayfa = oi.al(KAHTA)
    kartlar = re.split(r'<div class="card w-100"', sayfa)[1:]
    if not kartlar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc, atlanan = [], 0
    for b in kartlar:
        ad = oi.ad_duzelt((re.search(r'<p class="adsoyad">([\s\S]*?)</p>', b) or [None, ""])[1])
        d = {oi.metin(a): oi.metin(v) for a, v in re.findall(r"<th>([^<]*)</th>\s*<td>([\s\S]*?)</td>", b)}
        vef = oi.tarih(d.get("Vefat Tarihi", ""))
        if not ad:
            continue
        if not vef:
            atlanan += 1
            continue
        sonuc.append(oi.kayit(IL, "Kâhta", "adiyaman-kahta", ad, vef, "Kâhta Belediyesi", KAHTA, ctx["alindi"],
                              yas=oi.say(d.get("Yaş", "")), vefat_tarihi=vef, liste_tarihi=vef, ham={}))
    if atlanan:
        print(f"[Kâhta] tarihi geçersiz/gelecekte {atlanan} kayıt atlandı", file=sys.stderr)
    return sonuc


def main():
    oi.il_calistir(IL, "adiyaman", [("Besni", besni), ("Kâhta", kahta)])


if __name__ == "__main__":
    main()
