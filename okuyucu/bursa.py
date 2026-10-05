#!/usr/bin/env python3
"""Bursa Büyükşehir Belediyesi Mezarlık Bilgi Sistemi okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.bursa.bel.tr/mezarlik-bilgi-sistemi -> "Bugün Defnedilenler" sekmesi (sunucuda üretilen HTML tablo).
Yalnız BUGÜNÜN listesi var (tarih parametresi yok): önceki günler kendi dosyalarımızdan tamamlanır (ortak.liste_birikim);
sayfa günde birkaç kez okunduğunda gün içinde eklenen kayıtlar yakalanır. Kayıt ilk görüldüğü güne yazılır.
İlçe: yalnız kaynak mezarlık sütununda "İLÇE / Mezarlık adı" biçiminde yazıyorsa o ilçe alınır (ham.ilce_kaynagi:
mezarlik_oneki); yazmıyorsa ilçe belirsiz kalır. İlçe mahalleden ÇIKARILMAZ. Haritaya bağlantı/koordinat alınmaz.
Kullanım: python3 okuyucu/bursa.py
"""
import html, os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Bursa"
URL = "https://www.bursa.bel.tr/mezarlik-bilgi-sistemi"
KAYNAK_AD = "Bursa Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "bursa")
BASLIKLAR = ["mezarlik", "ad", "mahalle", "dogum", "ana", "baba"]


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def ayristir(sayfa):
    i = sayfa.find('id="bugundefnedilenler"')
    if i < 0:
        raise RuntimeError('"Bugün Defnedilenler" sekmesi sayfada bulunamadı (sayfa düzeni değişmiş olabilir)')
    blok = sayfa[i:]
    blok = blok[:blok.find("</table>")]
    kayitlar = []
    for tr in re.findall(r"<tr>(.*?)</tr>", blok.split("<tbody>", 1)[-1], re.S):
        h = [metin(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(h) == len(BASLIKLAR):
            kayitlar.append(dict(zip(BASLIKLAR, h)))
    return kayitlar


def mezarlik_ayir(m):
    """'OSMANGAZİ / Bursa Hamitler Mezarlığı' -> (ilçe_ham, 'Bursa Hamitler Mezarlığı'); önek ilçe değilse (None, tamamı)."""
    if " / " in m:
        on, _, son = m.partition(" / ")
        if on.strip() and any(ortak.katla(on) == ortak.katla(x) for x in ortak.ilce_listesi(IL)):
            return on.strip(), son.strip() or None
    return None, m or None


def kayda_cevir(h, gun, alindi):
    ad = h["ad"]
    ilce_ham, mezarlik = mezarlik_ayir(h["mezarlik"])
    ap = "-".join(x for x in (h["ana"], h["baba"]) if x)
    return {
        "id": ortak.kayit_id("bursa", ad, gun, f'{h["mahalle"]}|{h["dogum"]}|{h["ana"]}|{h["baba"]}'),
        "il": IL,
        "ilce": ortak.tr_title(ilce_ham) if ilce_ham else None,   # kaynak ilçe yazıyorsa; mahalleden çıkarılmaz
        "mahalle": ortak.tr_title(h["mahalle"]) or None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": None,                 # kaynakta yok
        "dogum_tarihi": None,        # kaynak yalnız doğum YILI veriyor (ham.dogum)
        "vefat_tarihi": None,        # kaynakta yok
        "defin_yeri": mezarlik,
        "defin_zamani": gun,         # sekme "Bugün Defnedilenler": defin tarihi = listenin ilk görüldüğü gün (saat yok)
        "namaz_tarihi": None,
        "namaz_yeri_vakti": None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": URL,
        "alindi": alindi,
        "ham": {"mezarlik": h["mezarlik"] or None, "mahalle": h["mahalle"] or None, "dogum": h["dogum"] or None,
                "ana": h["ana"] or None, "baba": h["baba"] or None,
                "ilce_kaynagi": "mezarlik_oneki" if ilce_ham else None},
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
