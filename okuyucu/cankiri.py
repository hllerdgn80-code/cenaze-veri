#!/usr/bin/env python3
"""Çankırı Belediyesi 'Vefat Edenler' okuyucusu (yalnız standart kütüphane).
Kaynak: https://cankiri.bel.tr/vefat-edenler (tablo: AD SOYAD | DEFİN TARİHİ GG-AA-YYYY | AÇIKLAMA). Sayfa YALNIZ en son 10 kaydı verir
(tarih süzgeci formu sonucu değiştirmiyor, denendi) -> kayıtlar defin tarihine göre gün dosyalarına BİRİKTİRİLİR; günde birkaç kez çalıştırılmalı.
Açıklama: 'AD vefat etmiştir. Cenazesi <vakit> namazını müteakip <yer> toprağa verilecektir.' Yer 'X ilinde' ise (X != Çankırı) il_disi_defin;
'X köyünde / ilçesinde / aile mezarlığında' ilçe ya da mahalle OLARAK alınmaz (defin yeri; ilce_belirsiz).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Çankırı"
URL = "https://cankiri.bel.tr/vefat-edenler"
KAYNAK_AD = "Çankırı Belediyesi"
KOK = os.path.join(ortak9.VERI, "cankiri")


def ayristir(aciklama):
    m = re.search(r"Cenazesi\s+(?:(\S+)\s+namaz\w*\s+müteakip\s+)?(.*?)\s+(?:toprağa|defnedil)", aciklama or "", re.I)
    if not m:
        return None, None, None
    vakit, yer = m.group(1), m.group(2).strip()
    ilce_ham = None
    mi = re.match(r"^(.+?)\s+ilinde$", yer, re.I)
    if mi:
        ilce_ham = ortak.tr_title(mi.group(1))      # başka il -> ortak.ilce_coz il_disi'ye çevirir
    return vakit, yer, ilce_ham


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    sayfa = ortak.indir(URL, 3.5)
    alindi = ortak.simdi_iso()
    yeni = {}
    for ad, tarih, acik in re.findall(r"<tr>\s*<td>(?!<strong>)(.*?)</td>\s*<td>(\d{2}-\d{2}-\d{4})</td>\s*<td>(.*?)</td>\s*</tr>", sayfa, re.S):
        ad = ortak9.metin(ad)
        gg, aa, yyyy = tarih.split("-")
        gun = f"{yyyy}-{aa}-{gg}"
        if gun not in gl:
            continue
        acik = ortak9.metin(acik)
        vakit, yer, ilce_ham = ayristir(acik)
        k = ortak9.kayit("cankiri", IL, ortak.tr_title(ad), gun, KAYNAK_AD, URL, alindi,
                         ilce=ilce_ham if ilce_ham and ilce_ham else None,
                         defin_yeri=ortak.tr_title(yer) if yer else None, defin_zamani=gun, namaz_tarihi=gun if vakit else None,
                         namaz_yeri_vakti=f"{vakit} namazını müteakip" if vakit else None,
                         ham={"aciklama": re.sub(r"^.*?vefat etmiştir\.\s*", "", acik)})
        yeni.setdefault(gun, []).append(k)
    print(f"pencerede {sum(len(v) for v in yeni.values())} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
