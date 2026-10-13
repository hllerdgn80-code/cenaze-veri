#!/usr/bin/env python3
"""Düzce Belediyesi Mezarlıklar Müdürlüğü (MEBİS) 'Vefat Edenler' okuyucusu (yalnız standart kütüphane).
Kaynak: https://mebis.duzce.bel.tr/vefat-edenler (Blazor Server; sayfa ilk yüklemede 'Bugün' listesini sunucuda hazır basıyor,
başka güne geçmek Blazor/SignalR bağlantısı ister -> yapılamaz). Yalnız BUGÜNÜN defin listesi okunur; geçmiş günler günlük çalıştıkça birikir.

DURUM (08.10.2026): sayfa 'tarihinde defin kaydı bulunmamaktadır' diyor (boş-liste durumu doğrulandı). Kayıt içeren kart işaretlemesi
henüz GÖRÜLMEDİ; bu yüzden dolu liste ayrıştırılmıyor — dolu durum görülünce okuyucu uyarı basar ve kaydı ATLAR, ham HTML
'veri/duzce/_dolu_ornek.html' olarak saklanır (KVKK: telefon/yakın bilgisi olabilir; ayrıştırıcı yazılırken bu dosya silinir, git'e girmez).
"""
import os, re, sys
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Düzce"
URL = "https://mebis.duzce.bel.tr/vefat-edenler"
KAYNAK_AD = "Düzce Belediyesi"
KOK = os.path.join(ortak9.VERI, "duzce")


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(ortak9.gun_sayisi())
    sayfa = ortak.indir(URL, 3.5)
    alindi = ortak.simdi_iso()
    bugun = date.today().isoformat()
    m = re.search(r'class="tarih-input" value="(\d{4}-\d{2}-\d{2})"', sayfa)
    if m and m.group(1) != bugun:
        print(f"UYARI: sayfa {m.group(1)} gösteriyor, bugün {bugun}", file=sys.stderr)
    bos = "defin kaydı bulunmamaktadır" in sayfa
    yeni = []
    # 13.10.2026: site yeniden tasarlandı; kayıtlar <div class="vefat-card"> kartları. Kartın "Cenaze Adresi" satırı (açık adres) KVKK gereği ATILIR.
    for kart in sayfa.split('<div class="vefat-card">')[1:]:
        kart = kart.split('<div class="card-footer">')[0]
        ad = re.search(r'<h3 class="card-title">(.*?)</h3>', kart, re.S)
        if not ad:
            continue
        alan = {ortak9.metin(e).rstrip(":"): ortak9.metin(v) for e, v in
                re.findall(r'<span class="info-label">(.*?)</span>\s*<span class="info-value">(.*?)</span>', kart, re.S)}
        ad = ortak9.ad_duzelt(ortak9.metin(ad.group(1)))
        defin_t = ortak.tarih_iso(alan.get("Defin Tarihi", "")) or bugun
        mez = re.search(r'<div class="mezarlik-banner">.*?<span>(.*?)</span></div>', kart, re.S)
        mezarlik = ortak9.metin(mez.group(1)) if mez else None
        duy = alan.get("Cenaze Duyurusu", "")
        nm = re.match(r"(.+?)\s+kılınacak\b", duy)
        namaz, defin = (ortak9.metin(nm.group(1)).strip(" ,") if nm else None), None
        baba, anne = alan.get("Baba Adı"), alan.get("Anne Adı")
        k = ortak9.kayit("duzce", IL, ad, defin_t, KAYNAK_AD, URL, alindi,
                         anne_baba="-".join(x for x in (ortak9.ad_duzelt(anne) if anne else "", ortak9.ad_duzelt(baba) if baba else "") if x) or None,
                         vefat_tarihi=ortak.tarih_iso(alan.get("Ölüm Tarihi", "")), defin_yeri=ortak9.ad_duzelt(mezarlik) if mezarlik else defin,
                         namaz_yeri_vakti=namaz,
                         ham={"cenaze_duyurusu": alan.get("Cenaze Duyurusu")})
        yeni.append(k)
    if not bos and not yeni:
        print("UYARI: liste dolu görünüyor ama kart bulunamadı (sayfa düzeni değişmiş olabilir)", file=sys.stderr)
    print(f"bugün: {len(yeni)} kayıt" if yeni else "bugün: liste boş")
    gunler, by = ortak.liste_birikim(KOK, IL, bugun, yeni, len(gl))
    ortak9.yaz(KOK, IL, gunler, by)


if __name__ == "__main__":
    main()
