#!/usr/bin/env python3
"""Elazığ Belediyesi 'Vefat Edenler' okuyucusu (yalnız standart kütüphane; TLS için sistem curl yedeği).
Kaynak: https://www.elazig.bel.tr/vefat-edenler/ ve /vefat-edenler/sayfa/N/ (sayfa başına 24 kayıt, en yeni üstte; kart başlığında tarih + ad).
Kart tablosu: Adı Soyadı, Vefat Tarihi, Cenaze Sahibi (yakın adı: KVKK gereği ALINMAZ), Defin Yeri, Taziye Bilgisi (taziye yeri: ALINMAZ).
Gün = vefat tarihi. Sayfalar pencere bitene kadar (en çok 6) okunur. İlçe kaynakta yok -> ilce_belirsiz.
TLS: bu site yalnız TLS 1.3 konuşuyor; Python'un LibreSSL 2.8'i konuşamazsa sistem curl'ü kullanılır (sertifika doğrulaması AÇIK).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Elazığ"
TABAN = "https://www.elazig.bel.tr/vefat-edenler/"
KAYNAK_AD = "Elazığ Belediyesi"
KOK = os.path.join(ortak9.VERI, "elazig")
EN_COK_SAYFA = 6


def indir(url):
    return ortak9.indir_yedekli(url, bekle=3.5)


def kartlar(sayfa):
    for b in re.split(r'<div class="card-header deceased', sayfa)[1:]:
        etiket = {ortak9.metin(a).rstrip(":"): ortak9.metin(d)
                  for a, d in re.findall(r'<td class="width-160 font-bold">(.*?)</td>\s*<td>(.*?)</td>', b, re.S)}
        bas = re.search(r'<i class="mdi[^>]*></i>\s*([^<]*)</div>', b)
        if etiket.get("Adı Soyadı"):
            yield (ortak.tarih_iso(bas.group(1).strip()) if bas else None), etiket


def main():
    n = ortak9.gun_sayisi()
    if not ortak9.robots_ok(TABAN, indir):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    alindi = ortak.simdi_iso()
    yeni, toplam = {}, 0
    for s in range(1, EN_COK_SAYFA + 1):
        url = TABAN if s == 1 else f"{TABAN}sayfa/{s}/"
        k_say = 0
        en_eski = None
        for baslik_gun, e in kartlar(indir(url)):
            k_say += 1
            vefat = ortak.tarih_iso(e.get("Vefat Tarihi")) or baslik_gun
            en_eski = min(en_eski, vefat) if en_eski and vefat else (vefat or en_eski)
            if not vefat or vefat not in gl:
                continue
            toplam += 1
            ad = ortak.tr_title(e["Adı Soyadı"])
            defin = e.get("Defin Yeri")
            k = ortak9.kayit("elazig", IL, ad, vefat, KAYNAK_AD, TABAN, alindi, ek_id=defin or "",
                             vefat_tarihi=vefat, defin_yeri=defin or None, ham={"defin_yeri": defin})
            yeni.setdefault(vefat, []).append(k)
        if not k_say or (en_eski and en_eski < gl[-1]):
            break
    print(f"pencerede {toplam} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
