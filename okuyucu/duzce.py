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
    if not bos:
        os.makedirs(KOK, exist_ok=True)
        with open(os.path.join(KOK, "_dolu_ornek.html"), "w", encoding="utf-8") as f:
            f.write(sayfa[sayfa.find('class="Vefat-Edenler-wrapper"'):][:20000])
        print("UYARI: liste dolu görünüyor ama kart işaretlemesi doğrulanmadı; kayıt atlandı (_dolu_ornek.html'e bakın)", file=sys.stderr)
    print("bugün: liste boş" if bos else "bugün: liste dolu, ayrıştırılamadı")
    gunler, by = ortak.liste_birikim(KOK, IL, bugun, yeni, len(gl))
    ortak9.yaz(KOK, IL, gunler, by)


if __name__ == "__main__":
    main()
