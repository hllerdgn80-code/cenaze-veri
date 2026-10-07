#!/usr/bin/env python3
"""Çanakkale Belediyesi cenaze ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.canakkale.bel.tr/tr/sayfa/1214-cenaze-ilanlari (liste: 'GG.AA.YYYY Tarihli Cenaze İlanı', her biri ayrı sayfa).
Pencerede kalan ilan sayfaları tek tek açılır (aynı alan adına ≥3,5 sn arayla; pencere başına birkaç sayfa). İlan metni:
'Çanakkale eşrafından; AD SOYAD vefat etmiştir. Cenazesi bugün <vakit> ... Camii'nden kaldırılarak <mezarlık>'a defnedilecektir.'
Gün = ilan tarihi. İlçe kaynakta yok -> ilce_belirsiz. Sayfa kimliği (11945) id'ye girer (aynı gün birden çok ilan).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Çanakkale"
TABAN = "https://www.canakkale.bel.tr/"
LISTE = TABAN + "tr/sayfa/1214-cenaze-ilanlari"
KAYNAK_AD = "Çanakkale Belediyesi"
KOK = os.path.join(ortak9.VERI, "canakkale")


def ilan_metni(sayfa):
    """Sayfadaki ilan gövdesi: 'Tarihli Cenaze İlanı' başlığından 'Dost, akraba' satırına kadar."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", sayfa, flags=re.S)
    satir = [ortak9.metin(x) for x in re.split(r"<[^>]+>", t)]
    satir = [x for x in satir if x]
    for i in range(len(satir) - 1, -1, -1):
        if re.match(r"^\d{2}\.\d{2}\.\d{4} Tarihli Cenaze İlanı", satir[i]):
            govde = []
            for x in satir[i + 1:]:
                if x.startswith("Dost, akraba") or x == "Başkan":
                    break
                govde.append(x)
            return " ".join(govde)
    return None


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(LISTE):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    liste = ortak.indir(LISTE, 3.5)
    alindi = ortak.simdi_iso()
    yeni, goruldu = {}, set()
    for yol, kimlik, gg, aa, yyyy in re.findall(r"href=['\"](tr/sayfa/1214-cenaze-ilanlari/(\d+)-(\d{2})(\d{2})(\d{4})-tarihli-cenaze-ilani)['\"]", liste):
        gun = f"{yyyy}-{aa}-{gg}"
        if gun not in gl or kimlik in goruldu:
            continue
        goruldu.add(kimlik)
        url = TABAN + yol
        try:
            metin = ilan_metni(ortak.indir(url, 3.5))
        except Exception as e:
            print(f"HATA {kimlik}: {e}", file=sys.stderr)
            continue
        m = re.search(r"(?:^|;)\s*([^;]*?)\s*;?\s*([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ' .-]{3,}?)\s+vefat etmiştir", metin or "")
        if not m:
            print(f"UYARI {kimlik}: ad ayrıştırılamadı: {metin!r}", file=sys.stderr)
            continue
        ad = " ".join(m.group(2).split())
        cumle = re.search(r"Cenazesi\b.*", metin)
        namaz, defin = ortak9.cenaze_cumlesi(cumle.group(0)) if cumle else (None, None)
        k = ortak9.kayit("canakkale", IL, ortak.tr_title(ad), gun, KAYNAK_AD, url, alindi, ek_id=kimlik,
                         defin_yeri=defin, namaz_yeri_vakti=namaz, defin_zamani=gun,
                         ham={"sayfa_kimligi": kimlik, "cenaze_cumlesi": cumle.group(0) if cumle else None})
        yeni.setdefault(gun, []).append(k)
    print(f"pencerede {sum(len(v) for v in yeni.values())} kayıt")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
