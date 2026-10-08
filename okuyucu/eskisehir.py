#!/usr/bin/env python3
"""Eskişehir: il ve 14 ilçenin çoğunda günlük liste yok; ilçe düzeyinde Çifteler Belediyesi "izlemede".
Çifteler: `cifteler.bel.tr/HOME/INDEX/HIZMET-VE-TESISLER/VEFAT-EDENLER` serbest metin duyurular:
"VEFAT EDEN - AD SOYAD - GG.AA.YYYY" + ilan metni. 08.10.2026'da son duyuru 28.09 (pencere dışı): 0 kayıt normaldir, yeni ilan çıkınca alınır.
Metinden yalnız "X Mahallesi sakinlerinden" ve "Cenazesi ..." cümlesi alınır (yakın adları ALINMAZ). Gün = duyuru tarihi.
TLS: sunucu ara sertifikayı göndermiyor -> sertifika/ilce-zincir.pem (doğrulama AÇIK). robots.txt yok.
Kullanım: python3 okuyucu/eskisehir.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi, ortak_haber as oh

IL = "Eskişehir"

# YEREL HABER (08.10.2026): il geneli tek kişilik vefat haberleri (ortak_haber; site başına günde en çok 3 istek)
HABER_SITELERI = [
    oh.site("Sakarya Gazetesi", "eskisehir-sakaryagazetesi", "https://www.sakaryagazetesi.com.tr/rss", ek_dizin="https://www.sakaryagazetesi.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("Sonhaber", "eskisehir-sonhaber", "https://www.sonhaber.com.tr/rss", ek_dizin="https://www.sonhaber.com.tr/sitemap/sitemap-{AY}.xml"),
    oh.site("İstikbal Gazetesi", "eskisehir-istikbal", "https://www.istikbalgazetesi.com/rss", ek_dizin="https://www.istikbalgazetesi.com/sitemap/sitemap-{AY}.xml"),
]
CIFTELER = "https://www.cifteler.bel.tr/HOME/INDEX/HIZMET-VE-TESISLER/VEFAT-EDENLER"


def cifteler(ctx):
    sayfa = oi.al(CIFTELER, oi.ssl_ilce())
    duz = oi.metin(re.sub(r"<(script|style)[\s\S]*?</\1>", " ", sayfa))
    bolum = duz.split("VEFAT EDENLER", 1)[-1]
    ilanlar = re.findall(r"VEFAT EDEN\s*-\s*(.+?)\s*-\s*(\d\d\.\d\d\.\d{4})\s+(.+?)(?=VEFAT EDEN\s*-|$)", bolum)
    if not ilanlar:
        raise RuntimeError("duyuru bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for ad, tar, txt in ilanlar:
        ad = oi.ad_duzelt(ad)
        gun = oi.tarih(tar)
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        namaz, defin = oi.cenaze_ayikla(txt[:900])
        sonuc.append(oi.kayit(IL, "Çifteler", "eskisehir-cifteler", ad, gun, "Çifteler Belediyesi", CIFTELER, ctx["alindi"],
                              il_disi_metin=txt[:900], mahalle=oi.mahalle_ayikla(txt), defin_yeri=defin, namaz_tarihi=gun if namaz else None,
                              namaz_yeri_vakti=namaz, liste_tarihi=gun, ham={"ilan_tarihi": gun}))
    return sonuc


def main():
    oi.il_calistir(IL, "eskisehir", [("Çifteler", cifteler)] + oh.okuyucular(IL, HABER_SITELERI))


if __name__ == "__main__":
    main()
