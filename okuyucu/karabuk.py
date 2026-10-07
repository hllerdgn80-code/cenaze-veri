#!/usr/bin/env python3
"""Karabük Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.karabuk.bel.tr/vefat-edenler.asp (klasik ASP, UTF-8; tarih/sayfa parametresi yok -> yalnız o an yayında olan kayıtlar).
Sayfa kayıt yokken yalnız başlığı ("Vefat Edenler") gösterir. 07.10.2026'da bir kayıt görülmüş (cami, namaz vakti, defin yeri, defin tarihi);
08.10.2026 gece okumada liste BOŞTU, bu yüzden dolu satırın HTML'i görülemedi: ayrıştırıcı sütun/etiket adlarına göre tablo satırlarını okur
(ad, cami, vakit/saat, defin yeri/mezarlık, defin tarihi). Boş sayfa = 0 kayıt (hata değil); içerik var ama tanınmayan düzendeyse RuntimeError verir
(sessizce boş yazılmaz). Gün dosyaları birikir (yaz_birlestir): günde birkaç kez çalıştır. İlçe kaynakta ayrı alan değil -> ilce_belirsiz.
mebis.karabuk.bel.tr 08.10.2026'da HTTP 500 verdi (kullanılmadı). robots.txt yok (404).
Kullanım: python3 okuyucu/karabuk.py
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Karabük"
URL = "https://www.karabuk.bel.tr/vefat-edenler.asp"
KAYNAK_AD = "Karabük Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "karabuk")


def icerik_blogu(sayfa):
    i = sayfa.find('<h1 class="page_title">')
    if i < 0:
        raise RuntimeError("Sayfa başlığı bulunamadı (sayfa düzeni değişmiş olabilir)")
    j = sayfa.find("</section>", i)
    return sayfa[sayfa.find("</h1>", i) + 5: j if j > 0 else len(sayfa)]


def sutun(baslik):
    b = ortak.katla(baslik)
    if "cami" in b:
        return "cami"
    if "vakit" in b or "saat" in b or "namaz" in b:
        return "vakit"
    if "mezarl" in b or "defin yeri" in b:
        return "defin_yeri"
    if "tarih" in b:
        return "tarih"
    if "ad" in b.split() or "vefat" in b or "soyad" in b:
        return "ad"
    return None


def ayristir(blok):
    if not ortak_ek.metin(blok):
        return []                                        # kayıt yok
    tablolar = re.findall(r"<table[^>]*>(.*?)</table>", blok, re.S)
    sonuc = []
    for t in tablolar:
        satirlar = [[ortak_ek.metin(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)] for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]
        if len(satirlar) < 2:
            continue
        esle = [sutun(b) for b in satirlar[0]]
        if "ad" not in esle:
            continue
        for s in satirlar[1:]:
            d = {e: v for e, v in zip(esle, s) if e}
            if d.get("ad"):
                sonuc.append(d)
    if not sonuc:
        raise RuntimeError("Sayfada içerik var ama tanınan tablo yok: " + ortak_ek.metin(blok)[:200])
    return sonuc


def kayda_cevir(d, bugun, alindi):
    gun = ortak_ek.tarih_gg_aa_yyyy(d.get("tarih")) or bugun
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, URL, alindi)
    k.update(
        id=ortak.kayit_id("karabuk", d["ad"], gun, d.get("cami", "")),
        ad_soyad=ortak.tr_title(d["ad"]),
        defin_yeri=ortak.tr_title(d.get("defin_yeri", "")) or None,
        defin_zamani=gun,
        namaz_tarihi=gun,
        namaz_yeri_vakti=" - ".join(x for x in (d.get("cami"), d.get("vakit")) if x) or None,
        liste_tarihi=gun,
        ham={k2: v for k2, v in d.items()},
    )
    return k


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    bugun = gunler[0]
    alindi = ortak.simdi_iso()
    liste = ayristir(icerik_blogu(ortak.indir(URL)))
    by_gun = {}
    for d in liste:
        k = kayda_cevir(d, bugun, alindi)
        if k["liste_tarihi"] in gunler:
            by_gun.setdefault(k["liste_tarihi"], []).append(k)
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    print(f"sayfada {len(liste)} satır")
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
