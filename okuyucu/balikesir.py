#!/usr/bin/env python3
"""Balıkesir: Balıkesir BŞB'nin listesi yok; ilçe düzeyinde 3 ilçe belediyesi (her biri ayrı kaynak):
- Bandırma: `bandirma.bel.tr/gunluk-bilgi/vefatlar?page=N` (tablo: ad, baba, anne, mezarlık, mahalle/köy, doğum, vefat, defin tarihi). Sunucuda
  üretilen HTML; doğum tarihi kaydedilmez (yalnız yaş). Gün = defin tarihi.
- Burhaniye: `burhaniye.bel.tr/Guncel/Vefat_Ilanlari.aspx` tek sayfa, 3.500+ kayıt (6,6 MB), yeniden eskiye: sayfa parça parça okunur,
  pencere dışına çıkınca bağlantı kesilir (tek istek). Doğum yeri/yılı ALINMAZ.
- Altıeylül: `altieylul.bel.tr/Hizmet/Vefat` (tablo: defin tarihi, ad, yaş, MESLEK [alınmaz], cenaze yeri, namaz, mezarlık). 08.10.2026'da son kayıt
  28.09 (pencere dışı): 0 kayıt normaldir, "izlemede".
- Balıkesir BŞB MEZARLIK BİLGİ SİSTEMİ (16.10.2026, sahibi: "mezarlık bilgi sistemi önceliğimiz"): `mbs.balikesir.bel.tr/Home/VefatListe?sayfa=N`
  (12 kayıt/sayfa, vefat tarihine göre yeniden eskiye; giriş/CAPTCHA yok). Kart: "AD SOYAD - GG.AA.YYYY" (= vefat tarihi), Ana/Baba adı, doğum,
  "Bulunduğu Mezarlık: ADI (İLÇE)". İlçe yalnız mezarlık adının parantezindeki parçadan (ilin geçerli ilçesiyse); namaz yeri/saati YOK.
  Doğum tarihi/Eş adı/adres/koordinat ALINMAZ (yalnız yaş hesaplanır). Gün = vefat tarihi (liste_tarihi; namaz_tarihi boş).
Kullanım: python3 okuyucu/balikesir.py [--gun 7] [--ilce Bandırma]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Balıkesir"


# ---------------------------------------------------------------- Bandırma
BANDIRMA = "https://www.bandirma.bel.tr/gunluk-bilgi/vefatlar"


def bandirma(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa)
        liste = []
        for s in satirlar:
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Ad Soyad"))
            baba, anne = oi.ad_duzelt(oi.kolon(baslik, s, "Baba Adı")), oi.ad_duzelt(oi.kolon(baslik, s, "Anne Adı"))
            mezar = oi.kolon(baslik, s, "Mezarlık Adı")
            mah = oi.kolon(baslik, s, "Mahalle")
            dogum = oi.tarih(oi.kolon(baslik, s, "Doğum"))
            vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
            defin = oi.tarih(oi.kolon(baslik, s, "Defin Tarihi"))
            gun = defin or vef
            if not ad or not gun:
                continue
            liste.append(oi.kayit(IL, "Bandırma", "balikesir-bandirma", ad, gun, "Bandırma Belediyesi", BANDIRMA, ctx["alindi"],
                                  ek_id=f"{vef}|{anne}|{baba}", mahalle=oi.buyuk_ise_title(mah, yer=True) or None,
                                  anne_baba="-".join(x for x in (anne, baba) if x) or None,
                                  yas=oi.yas_hesapla(dogum, vef or gun) if dogum else None, vefat_tarihi=vef,
                                  defin_yeri=oi.buyuk_ise_title(mezar, yer=True) or None, defin_zamani=defin, liste_tarihi=gun, ham={}))
        return liste
    return oi.sayfala(lambda n: f"{BANDIRMA}?page={n}", ayristir, ctx["gunler"], azami_sayfa=4)


# ---------------------------------------------------------------- Burhaniye
BURHANIYE = "https://www.burhaniye.bel.tr/Guncel/Vefat_Ilanlari.aspx"


def _burhaniye_bloklari(sayfa):
    out = []
    for li in re.findall(r"<li>\s*<div class=\"accordion-header\">([\s\S]*?)</li>", sayfa):
        d = {oi.metin(a).rstrip(" :"): oi.metin(b) for a, b in re.findall(r"<strong>([^<]*)</strong>([^<]*)</p>", li)}
        if "Adı Soyadı" in d:
            out.append(d)
    return out


def burhaniye(ctx):
    bas = ctx["gunler"][-1]

    def yeterli(txt):
        tr_ler = re.findall(r"Vefat İlan Tarihi : </strong>\s*([\d.]+)", txt)
        d = [oi.tarih(x) for x in tr_ler]
        d = [x for x in d if x]
        return len(d) >= 3 and all(x < bas for x in d[-3:])
    sayfa = oi.al_parca(BURHANIYE, yeterli)
    sonuc = []
    for d in _burhaniye_bloklari(sayfa):
        gun = oi.tarih(d.get("Vefat İlan Tarihi", ""))
        ad = oi.ad_duzelt(d.get("Adı Soyadı", ""))
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        baba, _, anne = (x.strip() for x in d.get("Baba Adı / Ana Adı", "").partition("/"))
        yer_vakit = d.get("Yer / Vakit") or None
        sonuc.append(oi.kayit(IL, "Burhaniye", "balikesir-burhaniye", ad, gun, "Burhaniye Belediyesi", BURHANIYE, ctx["alindi"],
                              ek_id=f"{anne}|{baba}", anne_baba="-".join(x for x in (ortak.tr_title(anne), ortak.tr_title(baba)) if x) or None,
                              defin_yeri=oi.buyuk_ise_title(d.get("Mezarlık", ""), yer=True) or None,
                              namaz_tarihi=gun, namaz_yeri_vakti=yer_vakit, liste_tarihi=gun, ham={"ilan_tarihi": gun}))
    return sonuc


# ---------------------------------------------------------------- Altıeylül
ALTIEYLUL = "https://www.altieylul.bel.tr/Hizmet/Vefat"


def altieylul(ctx):
    sayfa = oi.al(ALTIEYLUL)
    baslik, satirlar = oi.tablo(sayfa)
    sonuc = []
    for s in satirlar:
        # MESLEK sütunu BİLEREK okunmaz.
        defin = oi.tarih(oi.kolon(baslik, s, "Defin Tarihi"))
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Ad Soyad"))
        if not ad or not defin:
            continue
        yer, namaz = oi.kolon(baslik, s, "Cenaze Yeri"), oi.kolon(baslik, s, "Namaz")
        sonuc.append(oi.kayit(IL, "Altıeylül", "balikesir-altieylul", ad, defin, "Altıeylül Belediyesi", ALTIEYLUL, ctx["alindi"],
                              yas=oi.say(oi.kolon(baslik, s, "Yaşı")), defin_yeri=oi.buyuk_ise_title(oi.kolon(baslik, s, "Mezarlık"), yer=True) or None,
                              defin_zamani=defin, namaz_tarihi=defin,
                              namaz_yeri_vakti=" / ".join(x for x in (oi.buyuk_ise_title(yer, yer=True), oi.buyuk_ise_title(namaz, yer=True)) if x) or None,
                              liste_tarihi=defin, ham={}))
    return sonuc


# ---------------------------------------------------------------- Balıkesir BŞB Mezarlık Bilgi Sistemi
MBS = "https://mbs.balikesir.bel.tr/Home/VefatListe?sayfa={}"


def mbs(ctx):
    gecerli = {ortak.katla(x): x for x in ortak.gecerli_ilceler(IL)}

    def ayristir(sayfa, n):
        liste = []
        for t, p in re.findall(r'MeftaDetayMys/\d+"[^>]*>(.*?)</a>.*?<p class="p-2 m-0 pl-3">(.*?)</p>', sayfa, re.S):
            m = re.match(r"^(.*?)\s*-\s*(\d{1,2}\.\d{1,2}\.\d{4})\s*$", oi.metin(t))
            if not m:
                continue
            ad, gun = oi.ad_duzelt(m.group(1)), oi.tarih(m.group(2))
            h = {a.strip(): oi.metin(v) for a, v in re.findall(r"<strong>([^<:]+?)\s*:\s*</strong>\s*([^|<]*)", p)}
            if not ad or not gun:
                continue
            mez = h.get("Bulunduğu Mezarlık") or ""
            pm = re.search(r"\(([^)]+)\)\s*$", mez)
            ilce = gecerli.get(ortak.katla(pm.group(1))) if pm else None     # yalnız ilin geçerli ilçesi; yoksa None
            dg = oi.tarih(h.get("Doğum", ""))
            ana, baba = oi.ad_duzelt(h.get("Ana Ad", "")), oi.ad_duzelt(h.get("Baba Ad", ""))
            k = oi.kayit(IL, ilce, "balikesir-mbs", ad, gun, "Balıkesir Büyükşehir Belediyesi", MBS.format(1), ctx["alindi"],
                         ek_id=f"{ana}|{baba}|{mez}",
                         anne_baba="-".join(x for x in (ana, baba) if x) or None,
                         yas=oi.yas_hesapla(dg, gun) if dg else None, vefat_tarihi=gun,
                         defin_yeri=oi.buyuk_ise_title(re.sub(r"\s*\([^)]*\)\s*$", "", mez), yer=True) or None, liste_tarihi=gun,
                         ham={"ilce_kaynagi": "mezarlik_parantezi" if ilce else None})
            if not ilce:
                k["ilce_belirsiz"] = True
            liste.append(k)
        return liste

    return oi.sayfala(lambda n: MBS.format(n), ayristir, ctx["gunler"], azami_sayfa=10)


def main():
    oi.il_calistir(IL, "balikesir", [("Bandırma", bandirma), ("Burhaniye", burhaniye), ("Altıeylül", altieylul), ("Balıkesir BŞB", mbs)])


if __name__ == "__main__":
    main()
