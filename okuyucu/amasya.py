#!/usr/bin/env python3
"""Amasya: il belediyesinde liste yok.
MERZİFON BELEDİYESİ "Vefat İlan Sistemi" (`merbelweb.merzifon.bel.tr:8443/asp/vefat/ara.asp`) OKUNMAZ: robots.txt "User-agent: *" altında
`Disallow: /asp/vefat` ve `/asp/` der (aradaki boş satır Python ayrıştırıcısında kaydı düşürüyordu; ortak_ilce.robots_ok 13.10.2026'da
düzeltildi). `merzifon_belediye()` işlevi bu yüzden Engel verir ve çalıştırılmaz; kodu bırakıldı ki robots.txt değişirse açılabilsin.
Amasya il merkezi ve ilçeleri: YEREL BASIN (site sahibi kararı 08.10.2026), amasya YEREL_ILLER'de.
- Merzifon Bilgi Gazetesi: `merzifonbilgigazetesi.com/vefat-edenler/<gün>-aramizdan-ayrilanlar/<id>` ("D Ay YYYY Aramızdan
  Ayrılanlar", 1-3 günde bir). Sayfa "<İlçe> Vefat Edenler" başlıklarıyla bölünür (Amasya merkez -> ilçe belirsiz; Merzifon ...).
  Dizin: `sitemap_news.xml` (tek istek). Alınan: ad soyad, cami + vakit (kısa), mezarlık, köy/mahalle; tarih "Cenazesi bugün" ise
  sayfa günü namaz günüdür. Yakın adları, taziye, telefon ALINMAZ.
Kaynak türü yerel_basin; site başına günde en çok 3 istek (ortak_basin). Kullanım: python3 okuyucu/amasya.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_basin as ob, ortak_ilce as oi

IL = "Amasya"
MERZIFON_HARITA = "https://www.merzifonbilgigazetesi.com/sitemap_news.xml"


def merzifon_bilgi(ctx):
    xml = ob.dizin(ctx, MERZIFON_HARITA)
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if "/vefat-edenler/" in u and "aramizdan-ayrilanlar" in u]

    def ayristir(sayfa, url, gun):
        gun = ob.yayin_tarihi(sayfa) or gun
        return ob.serbest_kayitlar(ctx, IL, "amasya-merzifonbilgi", "Merzifon Bilgi Gazetesi", url, gun,
                                   ob.makale_govdesi(sayfa), ilce_basliklari=True)
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


MERZIFON_BEL = "https://merbelweb.merzifon.bel.tr:8443/asp/vefat/ara.asp"


def merzifon_vakit(ilan):
    """'CENAZESİ BUGÜN ... İKİNDİ NAMAZINI MÜTEAKİP ...' -> 'İkindi namazı' (hastane/cami adı atılır)."""
    m = re.search(r"(sabah|öğle|ikindi|akşam|yatsı)\s+namaz", ortak.tr_lower(ilan))
    return {"sabah": "Sabah namazı", "öğle": "Öğle namazı", "ikindi": "İkindi namazı", "akşam": "Akşam namazı", "yatsı": "Yatsı namazı"}[m.group(1)] if m else None


def merzifon_belediye(ctx):
    sayfa = oi.al(MERZIFON_BEL, oi.ssl_ilce())
    sonuc = []
    for t in re.findall(r"<table[\s\S]*?</table>", sayfa):
        alan = {oi.metin(th): oi.metin(td) for th, td in re.findall(r"<th>([\s\S]*?)</th>\s*<td>([\s\S]*?)</td>", t)}
        gun = oi.tarih(alan.get("Vefat Tarihi", ""))
        ad = oi.ad_duzelt(alan.get("Ad Soyad", ""))
        ilan = alan.get("İlan", "")
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        ilan_cenaze = ilan[ortak.tr_lower(ilan).find("cenazesi"):] if "cenazesi" in ortak.tr_lower(ilan) else ""
        _, defin = oi.cenaze_ayikla(ilan_cenaze)
        defin = ortak.tr_title(defin.replace("İlçemiz", "İlçe")) if defin else None
        mah = oi.mahalle_ayikla(ilan)
        if defin and mah and defin.startswith("Köyü"):              # "DERBENTOBRUĞU KÖYÜ AŞAĞI MAHALLESİNDE" -> köy adı mahalleden
            defin = mah.replace(" Köyü", "") + " " + defin
        elif defin == "Köy Mezarlığı" and mah:
            defin = f"{mah} Mezarlığı"
        vakit = merzifon_vakit(ilan_cenaze)
        bugun = "bugün" in ortak.tr_lower(ilan_cenaze)[:40]
        sonuc.append(oi.kayit(IL, "Merzifon", "amasya-merzifonbel", ad, gun, "Merzifon Belediyesi", MERZIFON_BEL, ctx["alindi"],
                              il_disi_metin=ilan_cenaze, mahalle=mah, vefat_tarihi=gun, defin_yeri=defin,
                              namaz_tarihi=gun if (bugun and vakit) else None, namaz_yeri_vakti=vakit, liste_tarihi=gun,
                              ham={"ilan_tarihi": gun}))
    return sonuc


def main():
    oi.il_calistir(IL, "amasya", [("Merzifon Bilgi Gazetesi", merzifon_bilgi)])    # Merzifon Belediyesi: robots.txt yasağı (üstteki not)


if __name__ == "__main__":
    main()
