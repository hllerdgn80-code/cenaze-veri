#!/usr/bin/env python3
"""Van Büyükşehir Belediyesi "Vefat & Taziyeler" okuyucusu (yalnız standart kütüphane).
Kaynak: https://van.bel.tr/Taziyeler.html (tek sayfa HTML; son ~5-7 günün defin kayıtları, sayfalama yok).
Alanlar: ad (yaş), ilçe (küçük harf ASCII: tusba, ipekyolu...; "ildisi" = il dışı defin), defin tarihi, mezarlık, mezar no.
Taziye sahibi / tel no / yakınlık / taziye adresi kaynakta yorum satırında, ALINMAZ (KVKK).
Sayfa yalnız son günleri gösterdiği için geçmiş günler kendi dosyalarımızdan korunur (ortak_ek.yaz_birlestir).
Kullanım: python3 okuyucu/van.py
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Van"
URL = "https://van.bel.tr/Taziyeler.html"
KAYNAK_AD = "Van Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "van")


def ayristir(sayfa):
    kutular = re.findall(r'<div class="qa-box">(.*?)(?=<div class="qa-box">|<!-- Döngü|</body>)', sayfa, re.S)
    sonuc = []
    for b in kutular:
        m = re.search(r'<div class="qa-title">(.*?)</div>', b, re.S)
        if not m:
            continue
        baslik = ortak_ek.metin(m.group(1))
        # yorum satırlarını at, kalan <li><span>Etiket</span>: değer</li>
        temiz = re.sub(r"<!--.*?-->", "", b, flags=re.S)
        alan = {k.strip(): ortak_ek.metin(v) for k, v in re.findall(r"<li><span>([^<]*)</span>:\s*(.*?)</li>", temiz, re.S)}
        sonuc.append((baslik, alan))
    return sonuc


def kayda_cevir(baslik, alan, alindi):
    m = re.match(r"^(.*?)\s*\((\d{1,3})\)\s*$", baslik)
    ad, yas = (m.group(1), int(m.group(2))) if m else (baslik, None)
    defin = alan.get("Defin Tarihi")
    if not defin or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", defin):
        return None
    ilce_ham = alan.get("İlçe") or None
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    ilce_dis = ilce_ham and ortak.katla(ilce_ham) == "ildisi"      # "il dışı" = defin başka ilde (hangi il belli değil)
    k.update(
        id=ortak.kayit_id("van", ad, defin, f'{alan.get("Mezarlık","")}|{alan.get("Mezar No","")}'),
        ilce=None if ilce_dis else ilce_ham,
        ad_soyad=ortak.tr_title(ad),
        yas=yas,
        defin_yeri=ortak.tr_title(alan.get("Mezarlık", "")) or None,
        defin_zamani=defin,
        liste_tarihi=defin,
        ham={"ilce": ilce_ham, "mezar_no": alan.get("Mezar No") or None,
             "il_disi_notu": "kaynak 'ildisi' yazıyor (başka ilde defin; hangi il belli değil)" if ilce_dis else None},
    )
    if ilce_dis:
        k["ilce_belirsiz"] = True      # ilce_isle'a "işlendi" işareti: il_disi_defin None kalır (il bilinmiyor)
        k["il_disi_defin"] = None
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    ham = ayristir(ortak.indir(URL))
    if not ham:
        raise RuntimeError("Sayfada qa-box bulunamadı (sayfa düzeni değişmiş olabilir)")
    alindi = ortak.simdi_iso()
    gunler = ortak_ek.son_gunler(7)
    by_gun = {}
    for baslik, alan in ham:
        k = kayda_cevir(baslik, alan, alindi)
        if k and k["liste_tarihi"] in gunler:
            by_gun.setdefault(k["liste_tarihi"], []).append(k)
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
