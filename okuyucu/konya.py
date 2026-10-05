#!/usr/bin/env python3
"""Konya Büyükşehir Belediyesi Mezarlık Bilgi Sistemi okuyucusu (yalnız standart kütüphane).
Kaynak: https://mezarlik.konya.bel.tr/ -> açılış sayfasındaki "Bugün Vefat Edenler" tablosu (sunucuda üretilen HTML).
Tarih parametresi YOK: yalnız güncel liste (vefat/defin tarihi bugün ve dün olanlar) -> ortak.liste_birikim ile biriktirilir;
kayıt ilk görüldüğü güne yazılır, geçmiş yeni kurulumda boştur. Günde birkaç kez çalıştırılması önerilir.
Kaynakta İLÇE YOK (camii/mezarlık adı ilçe vermez): ilce None + ilce_belirsiz. KVKK: yalnız tanımlı sütunlar alınır.
Kullanım: python3 okuyucu/konya.py
"""
import html, os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Konya"
URL = "https://mezarlik.konya.bel.tr/"
KAYNAK_AD = "Konya Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "konya")
BASLIKLAR = ["vefat", "defin", "ad", "baba", "dogum_yeri", "dogum", "cami", "namaz", "mezarlik"]


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def tarih_tire(s):
    """'03-10-2026' -> '2026-10-03'"""
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{4})", (s or "").strip())
    return ortak.tarih_iso(f"{m.group(1)}.{m.group(2)}.{m.group(3)}") if m else None


def ayristir(sayfa):
    i = sayfa.find('id="tableBilgi"')
    if i < 0:
        raise RuntimeError("tableBilgi tablosu bulunamadı (sayfa düzeni değişmiş olabilir)")
    blok = sayfa[i:sayfa.find("</table>", i)]
    kayitlar = []
    for tr in re.findall(r"<tr>(.*?)</tr>", blok.split("<tbody>", 1)[-1], re.S):
        h = [metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == len(BASLIKLAR):
            kayitlar.append(dict(zip(BASLIKLAR, h)))
    return kayitlar


def kayda_cevir(h, gun, alindi):
    vefat, defin, dogum = tarih_tire(h["vefat"]), tarih_tire(h["defin"]), tarih_tire(h["dogum"])
    cami = None if ortak.katla(h["cami"]) == "mezarlikta" else (ortak.tr_title(h["cami"]) or None)
    vakit = h["namaz"] or None
    yer_vakit = " – ".join(x for x in (vakit, cami) if x) or None
    return {
        "id": ortak.kayit_id("konya", h["ad"], vefat or gun, f'{h["baba"]}|{h["dogum"]}|{defin or ""}'),
        "il": IL,
        "ilce": None,                      # kaynakta yok
        "mahalle": None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": ortak.tr_title(h["baba"]) or None,    # kaynak yalnız baba adı verir
        "yas": None,                       # kaynakta yok (doğum tarihi var)
        "dogum_tarihi": dogum,
        "vefat_tarihi": vefat,
        "defin_yeri": ortak.tr_title(h["mezarlik"]) or None,
        "defin_zamani": defin,             # yalnız defin TARİHİ
        "namaz_tarihi": defin,             # namaz defin günü kılınır (kaynak ayrı namaz tarihi vermez)
        "namaz_yeri_vakti": yer_vakit,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": URL,
        "alindi": alindi,
        "ham": {"vefat": h["vefat"], "defin": h["defin"], "baba": h["baba"] or None, "dogum_yeri": h["dogum_yeri"] or None,
                "dogum": h["dogum"] or None, "cami": h["cami"] or None, "namaz": vakit, "mezarlik": h["mezarlik"] or None},
    }


def main():
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today().isoformat()
    ham = ayristir(ortak.indir(URL))
    alindi = ortak.simdi_iso()
    yeni = [kayda_cevir(h, bugun, alindi) for h in ham]
    gunler, by_gun = ortak.liste_birikim(KOK, IL, bugun, yeni)
    for g in gunler:
        if by_gun[g] or os.path.exists(os.path.join(KOK, f"{g}.json")):
            ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt" + (f" (sayfada {len(ham)} satır)" if g == bugun else ""))
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
