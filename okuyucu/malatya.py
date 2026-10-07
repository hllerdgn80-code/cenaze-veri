#!/usr/bin/env python3
"""Malatya Büyükşehir Belediyesi MEBİS "Vefat Edenler" okuyucusu (yalnız standart kütüphane).
Kaynak: https://mebis.malatya.bel.tr/ (ASP.NET + DevExpress GridView). Sayfa açılışta BUGÜNÜN tarihini listeler; tarih kutusu
(ctl00$ContentPlaceHolder1$ASPxDateEdit1) + DevExpress istemci durumu (ctl00$ContentPlaceHolder1$ASPxDateEdit1$State = {"rawValue": <ms>})
ve Listele düğmesiyle POST edilince başka gün seçilir (doğrulandı: kutu seçilen tarihi gösterir). Grid sütunları: Adı Soyadı, Baba Adı, Doğum Tarihi,
Vefat Tarihi, Ada, Parsel, Parsel Kodu, Pafta, Mezarlık, Açıklama. Okuyucu bugün + önceki 6 günü sorar; gün kutusu boş dönerse o gün boş sayılır.
Gün dosyaları birikir (yaz_birlestir): kaynak geçmiş günleri vermese de bugünkü okuma kendi dosyalarımızda kalır -> günde birkaç kez çalıştır.
İlçe kaynakta yok (mezarlık sütunu mezarlık adı) -> ilce_belirsiz. robots.txt yok (hata sayfasına yönlenir, kural yok sayılır).
NOT: 08.10.2026 gece yazıldı; o saatte bütün günler "Görüntülenecek veri yok" döndü -> dolu satır şeması GERÇEK satırla sınanmadı
(sütun adlarına göre ayrıştırılır; beklenmeyen sütun sayısında hata verir).
Kullanım: python3 okuyucu/malatya.py
"""
import html, json, os, re, sys, urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Malatya"
URL = "https://mebis.malatya.bel.tr/"
KAYNAK_AD = "Malatya Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "malatya")
TARIH_ALANI = "ctl00$ContentPlaceHolder1$ASPxDateEdit1"
BASLIKLAR = ["Adı Soyadı", "Baba Adı", "Doğum Tarihi", "Vefat Tarihi", "Ada", "Parsel", "Parsel Kodu", "Pafta", "Mezarlık", "Açıklama"]


def gizli_alanlar(sayfa):
    f = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', sayfa):
        n = re.search(r'name="([^"]*)"', m.group(0))
        v = re.search(r'value="([^"]*)"', m.group(0))
        if n:
            f[n.group(1)] = html.unescape(v.group(1)) if v else ""
    return f


def gun_formu(alt, gun):
    y, a, g = map(int, gun.split("-"))
    ms = int(datetime(y, a, g, 9, 0, tzinfo=timezone.utc).timestamp() * 1000)     # öğleye yakın (TR) -> gün kayması olmaz
    f = dict(alt)
    f[TARIH_ALANI] = f"{g}.{a:02d}.{y}"
    f[TARIH_ALANI + "$State"] = json.dumps({"rawValue": str(ms), "useMinDateInsteadOfNull": False}, separators=(",", ":"))
    f["ctl00$ContentPlaceHolder1$Listele"] = "Listele"
    return urllib.parse.urlencode(f).encode()


def grid_kayitlari(sayfa):
    """Dolu satırlar -> [ {başlık: değer} ]. Grid yoksa RuntimeError, 'Görüntülenecek veri yok' ise []."""
    if "ContentPlaceHolder1_VefatGrid" not in sayfa:
        raise RuntimeError("Grid sayfada yok (sayfa düzeni değişmiş ya da hata sayfası)")
    sonuc = []
    for tr in re.findall(r'<tr[^>]*id="ContentPlaceHolder1_VefatGrid_DXDataRow\d+"[^>]*>(.*?)</tr>', sayfa, re.S):
        hucreler = [ortak_ek.metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        hucreler = hucreler[-len(BASLIKLAR):]
        if len(hucreler) != len(BASLIKLAR):
            raise RuntimeError(f"Beklenmeyen sütun sayısı: {len(hucreler)}")
        sonuc.append(dict(zip(BASLIKLAR, hucreler)))
    if len(re.findall(r'class="dxp-num', sayfa)) > 1:
        print("UYARI: grid birden çok sayfa gösteriyor, yalnız ilki okundu", file=sys.stderr)
    return sonuc


def kayda_cevir(h, gun, alindi):
    ad = h["Adı Soyadı"]
    dogum_s = h["Doğum Tarihi"]
    dogum = ortak_ek.tarih_gg_aa_yyyy(dogum_s)
    vefat = ortak_ek.tarih_gg_aa_yyyy(h["Vefat Tarihi"])
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("malatya", ad, vefat or gun, h["Baba Adı"] + "|" + h["Mezarlık"]),
        ad_soyad=ortak.tr_title(ad),
        anne_baba=ortak.tr_title(h["Baba Adı"]) or None,
        dogum_tarihi=dogum,
        vefat_tarihi=vefat,
        defin_yeri=ortak.tr_title(h["Mezarlık"]) or None,
        defin_zamani=gun,
        liste_tarihi=gun,
        ham={"dogum_ham": dogum_s or None, "ada": h["Ada"] or None, "parsel": h["Parsel"] or None, "pafta": h["Pafta"] or None,
             "aciklama": h["Açıklama"] or None},
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    alindi = ortak.simdi_iso()
    ilk = ortak.indir(URL)
    alt = gizli_alanlar(ilk)
    by_gun, gorulen = {}, set()

    def ekle(gun, satirlar):
        for h in satirlar:
            k = kayda_cevir(h, gun, alindi)
            if k["id"] not in gorulen:
                gorulen.add(k["id"])
                by_gun.setdefault(gun, []).append(k)

    ekle(gunler[0], grid_kayitlari(ilk))                       # sayfanın açılış listesi = bugün
    for gun in gunler[1:]:
        sayfa = ortak.indir(URL, veri=gun_formu(alt, gun))
        ekle(gun, grid_kayitlari(sayfa))
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
