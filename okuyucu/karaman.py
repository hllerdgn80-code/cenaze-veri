#!/usr/bin/env python3
"""Karaman Belediyesi Mezarlık Bilgi Sistemi (MEBİS) vefat listesi okuyucusu (yalnız standart kütüphane).
Kaynak: http://web.karaman.bel.tr:571/Mebis/VefatListesi.aspx (http, port 571, ASP.NET WebForms, karakter kodu iso-8859-9/windows-1254).
Liste: Defin Tarihi | Vefat Eden "AD SOYAD (yaş)" | Namaz Vakti; satırlar en yenisi üstte (~40 satır). Her satır __doPostBack ile ayrıntı açar
(ViewState + EventValidation + __EVENTTARGET=...DlKayitlar$ctlNN$LnkBtnSec): ikamet mahallesi, namaz günü/vakti/çıkış yeri, defin yeri (mezarlık adı), ada no.
Yalnız son 7 günün satırları için ayrıntı istenir (~10-15 istek, 3,5 sn arayla). "Aslen ... köyünde" (memleket) yalnız ham'a yazılır.
İlçe kaynakta yok ("MERKEZ MEZARLIĞI" resmî ilçe adı sayılmaz) -> ilce_belirsiz. Vefat tarihi kaynakta yok; robots.txt yok (404 hata sayfası).
Kullanım: python3 okuyucu/karaman.py
"""
import html, os, re, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Karaman"
URL = "http://web.karaman.bel.tr:571/Mebis/VefatListesi.aspx"
KAYNAK_AD = "Karaman Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "karaman")


def gizli_alanlar(sayfa):
    f = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', sayfa):
        n = re.search(r'name="([^"]*)"', m.group(0))
        v = re.search(r'value="([^"]*)"', m.group(0))
        if n:
            f[n.group(1)] = html.unescape(v.group(1)) if v else ""
    return f


def liste_ayristir(sayfa):
    """[(indeks, 'YYYY-AA-GG', 'AD SOYAD', yas|None, vakit)]"""
    sonuc = []
    for i, blok in enumerate(re.findall(r'id="ctl00_MainContent_DlKayitlar_ctl\d+_LnkBtnSec"(.*?)</a>', sayfa, re.S)):
        h = [ortak_ek.metin(x) for x in re.findall(r"<div[^>]*>(.*?)</div>", blok, re.S)]
        if len(h) < 3:
            continue
        gun = ortak_ek.tarih_gg_aa_yyyy(h[0])
        m = re.match(r"^(.*?)\s*\((\d{1,3})\)\s*$", h[1])
        ad, yas = (m.group(1), int(m.group(2))) if m else (h[1], None)
        if gun:
            sonuc.append((i, gun, ad, yas, h[2]))
    return sonuc


def span(sayfa, ad):
    m = re.search(rf'id="ctl00_MainContent_{ad}">(.*?)</span>', sayfa, re.S)
    return ortak_ek.metin(m.group(1)) if m else None


def ayrinti(sayfa):
    mezarlik = span(sayfa, "LblMezarlik")
    return {
        "aslen": span(sayfa, "LblAslen"), "ikamet": span(sayfa, "LblIkamet"), "tarih": span(sayfa, "LblTarih"),
        "vakit": span(sayfa, "LblVakit"), "cikis": span(sayfa, "LblDefinYeri"), "mezarlik": mezarlik,
        "ada": span(sayfa, "LblAdaNo"),
    }


def yalin_mahalle(s):
    s = ortak.tr_title(s or "")
    for ek, yerine in (("Mahallesinde", "Mahallesi"), ("Köyünde", "Köyü"), ("Mahallesinden", "Mahallesi")):
        if s.endswith(ek):
            return s[: -len(ek)] + yerine
    return s or None


def namaz_gunu(tarih_metni, defin_gunu):
    """'7 Ekim Çarşamba GÜNÜ' + liste yılı -> 'YYYY-AA-GG' (çözülemezse None)."""
    m = re.match(r"^(\d{1,2})\s+(\S+)", tarih_metni or "")
    if not m:
        return None
    return ortak.tarih_iso(f"{m.group(1)} {m.group(2)} {defin_gunu[:4]}")


def kayda_cevir(satir, d, alindi):
    _, gun, ad, yas, vakit = satir
    mez = d.get("mezarlik")
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("karaman", ad, gun, f"{yas}"),
        mahalle=yalin_mahalle(d.get("ikamet")) if d.get("ikamet") else None,
        ad_soyad=ortak.tr_title(ad),
        yas=yas,
        defin_yeri=(ortak.tr_title(mez) + " Mezarlığı") if mez else None,
        defin_zamani=gun,
        namaz_tarihi=namaz_gunu(d.get("tarih"), gun) or gun,
        namaz_yeri_vakti=" - ".join(x for x in (ortak.tr_title(d["cikis"]) if d.get("cikis") else None, ortak.tr_title(d.get("vakit") or vakit)) if x) or None,
        liste_tarihi=gun,
        ham={"vakit": vakit, "aslen": d.get("aslen"), "ikamet": d.get("ikamet"), "namaz_gunu_metni": d.get("tarih"),
             "cikis_yeri": d.get("cikis"), "mezarlik_adi": mez, "ada_no": d.get("ada")},
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler7 = ortak_ek.son_gunler(7)
    sayfa = ortak.indir(URL)
    liste = liste_ayristir(sayfa)
    if not liste:
        raise RuntimeError("Liste bulunamadı (sayfa düzeni değişmiş olabilir)")
    alt = gizli_alanlar(sayfa)
    alindi = ortak.simdi_iso()
    by_gun, gorulen = {}, set()
    for satir in liste:
        i, gun, ad, yas, vakit = satir
        if gun not in gunler7:
            continue
        veri = dict(alt)
        veri["__EVENTTARGET"] = f"ctl00$MainContent$DlKayitlar$ctl{i:02d}$LnkBtnSec"
        veri["__EVENTARGUMENT"] = ""
        d = ayrinti(ortak.indir(URL, veri=urllib.parse.urlencode(veri).encode()))
        k = kayda_cevir(satir, d, alindi)
        if k["id"] not in gorulen:
            gorulen.add(k["id"])
            by_gun.setdefault(gun, []).append(k)
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler7, by_gun)
    for g in gunler7:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
