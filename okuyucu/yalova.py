#!/usr/bin/env python3
"""Yalova Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.yalova.bel.tr/vefatedenler (HTML tablo; sayfa başına 20, ?page=N; en yeni üstte). robots.txt: Allow /.
Sütunlar: Adı Soyadı, Baba Adı, Vefat Tarihi ("7 Eki 2026"), Defin Yeri ("YALOVA MERKEZ", "PAŞAKENT", "ELMALIK KÖYÜ", "ÇİFTLİKKÖY"...),
Açıklama ("MERKEZ CAMİ İKİNDİ" = cami + vakit). Sayfada aynı kayıtlar mobil kart olarak da tekrarlanır: yalnız <tbody> satırları alınır.
Defin yeri bir mezarlık/semt/köy adıdır: değer YALNIZ resmî ilçe adıyla birebir eşleşirse (Çiftlikköy, Altınova...) ilçe olur; "YALOVA MERKEZ",
semt ve köyler ilce_belirsiz kalır (tahmin yok). Namaz günü ilan günü (vefat tarihi alanı) varsayılmaz: namaz_tarihi null.
Kullanım: python3 okuyucu/yalova.py
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Yalova"
URL = "https://www.yalova.bel.tr/vefatedenler"
KAYNAK_AD = "Yalova Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "yalova")
EN_COK_SAYFA = 5


def kisa_tarih(s):
    """'7 Eki 2026' -> '2026-10-07'."""
    m = re.match(r"^(\d{1,2})\s+(\S+)\s+(\d{4})$", s.strip())
    if not m:
        return None
    ay = ortak_ek.KISA_AYLAR.get(ortak.tr_lower(m.group(2))[:3])
    if not ay:
        return None
    return f"{int(m.group(3)):04d}-{ay:02d}-{int(m.group(1)):02d}"


def ayristir(sayfa):
    govde = sayfa.split("<tbody", 1)[-1].split("</tbody>", 1)[0]
    sonuc = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", govde, re.S):
        h = [ortak_ek.metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == 5 and kisa_tarih(h[2]):
            sonuc.append({"ad": h[0], "baba": h[1], "gun": kisa_tarih(h[2]), "defin": h[3], "aciklama": h[4]})
    return sonuc


def kayda_cevir(r, alindi):
    ilce = None
    for x in ortak.ilce_listesi(IL):
        if ortak.katla(x) == ortak.katla(r["defin"]):
            ilce = x
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("yalova", r["ad"], r["gun"], r["baba"] + "|" + r["defin"]),
        ilce=ilce,
        ad_soyad=ortak.tr_title(r["ad"]),
        anne_baba=ortak.tr_title(r["baba"]) or None,
        vefat_tarihi=r["gun"],
        defin_yeri=ortak.tr_title(r["defin"]) or None,
        namaz_yeri_vakti=r["aciklama"] or None,
        liste_tarihi=r["gun"],
        ham={"defin_yeri": r["defin"], "aciklama": r["aciklama"], "ilce_kaynagi": "defin_yeri_birebir" if ilce else None},
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    alindi = ortak.simdi_iso()
    by_gun, gorulen = {}, set()
    for no in range(1, EN_COK_SAYFA + 1):
        liste = ayristir(ortak.indir(URL if no == 1 else f"{URL}?page={no}"))
        if not liste:
            if no == 1:
                raise RuntimeError("Tabloda kayıt bulunamadı (sayfa düzeni değişmiş olabilir)")
            break
        for r in liste:
            k = kayda_cevir(r, alindi)
            if r["gun"] in gunler and k["id"] not in gorulen:
                gorulen.add(k["id"])
                by_gun.setdefault(r["gun"], []).append(k)
        if min(r["gun"] for r in liste) < gunler[-1]:
            break
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
