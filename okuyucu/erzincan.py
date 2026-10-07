#!/usr/bin/env python3
"""Erzincan Belediyesi vefat edenler listesi okuyucusu (yalnız standart kütüphane).
Kaynak: https://erzincan.bel.tr/vefatedenler?page=N (sunucuda üretilen HTML tablo, sayfa başına 10 kayıt, yeniden eskiye).
Sütunlar: AD SOYAD (+ "İlçe-DoğumYılı" = DOĞUM yeri/yılı), BABA ADI, DEFİN TARİHİ, AÇIKLAMA. Defin tarihi = listenin günü.
Kaynakta defin ilçesi YOK ("Pülümür-1931" doğum yeridir): ilce None + ilce_belirsiz. KVKK: açıklamadaki yakın listesi,
telefon, taziye bilgisi ve ses anonsu bağlantısı alınmaz; açıklamadan yalnız "Cenazesi ..." cümlesi (namaz/defin yeri-vakti) alınır.
Kullanım: python3 okuyucu/erzincan.py [--gun 7]
"""
import html, os, re, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Erzincan"
URL = "https://erzincan.bel.tr/vefatedenler"
KAYNAK_AD = "Erzincan Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "erzincan")
MAKS_SAYFA = 6


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def cenaze_cumlesi(aciklama):
    """Açıklamadan 'Cenazesi ...' kısmını alır; taziye/telefon kısmını ve numaraları atar."""
    m = re.search(r"Cenaze", aciklama)
    if not m:
        return None
    c = aciklama[m.start():]
    c = re.split(r"Taziye|TAZİYE|Tel\b|TEL\b", c)[0]
    c = re.sub(r"\(?\+?\d[\d\s()\-]{8,}\d", "", c)
    return " ".join(c.split()) or None


def ayristir(sayfa):
    """-> [{ad, dogum, baba, tarih(YYYY-AA-GG), aciklama}]"""
    kayitlar = []
    for tr in re.findall(r"<tr class=\"group.*?</tr>", sayfa, re.S):
        ad = re.search(r"<h4[^>]*>(.*?)</h4>", tr, re.S)
        if not ad:
            continue
        sp = re.findall(r"<span\s+class=\"([^\"]*)\">(.*?)</span>", tr, re.S)
        dogum = baba = tarih = aciklama = None
        for cls, ic in sp:
            t = metin(ic)
            if "tracking-widest" in cls:
                dogum = t
            elif "tabular-nums" in cls:
                tarih = t
            elif "max-w-" in cls:
                aciklama = t
            elif "text-gray-400" in cls and "tracking-tight" in cls:
                baba = t
        kayitlar.append({"ad": metin(ad.group(1)), "dogum": dogum, "baba": baba or None,
                         "tarih": tarih if tarih and re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarih) else None,
                         "aciklama": aciklama or ""})
    return kayitlar


def kayda_cevir(h, url, alindi):
    gun = h["tarih"]
    cum = cenaze_cumlesi(h["aciklama"])
    dogum_yili = None
    if h["dogum"]:
        m = re.search(r"(\d{4})\s*$", h["dogum"])
        dogum_yili = m.group(1) if m else None
    return {
        "id": ortak.kayit_id("erzincan", h["ad"], gun, f'{h["baba"] or ""}|{h["dogum"] or ""}'),
        "il": IL,
        "ilce": None,                 # kaynakta defin ilçesi yok
        "mahalle": None,
        "ad_soyad": ortak.tr_title(h["ad"]),
        "anne_baba": ortak.tr_title(h["baba"]) if h["baba"] else None,   # yalnız baba adı var
        "yas": None,
        "dogum_tarihi": None,          # yalnız doğum yılı (ham.dogum_yili)
        "vefat_tarihi": None,
        "defin_yeri": None,
        "defin_zamani": gun,           # DEFİN TARİHİ sütunu (saat yok)
        "namaz_tarihi": None,
        "namaz_yeri_vakti": cum,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": url,
        "alindi": alindi,
        "ham": {"dogum": h["dogum"], "dogum_yili": dogum_yili, "baba": h["baba"]},
    }


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {g: [] for g in gunler}
    alindi = ortak.simdi_iso()
    gor = set()
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = f"{URL}?page={sayfa_no}"
        try:
            ham = ayristir(ortak.indir(url))
        except Exception as e:
            print(f"HATA sayfa {sayfa_no}: {e}", file=sys.stderr)
            break
        if not ham:
            break
        for h in ham:
            if not h["tarih"]:
                print(f"UYARI: tarihsiz satır atlandı: {h['ad']}", file=sys.stderr)
                continue
            k = kayda_cevir(h, url, alindi)
            if h["tarih"] in by_gun and k["id"] not in gor:
                gor.add(k["id"])
                by_gun[h["tarih"]].append(k)
        if all(h["tarih"] and h["tarih"] < gunler[-1] for h in ham):
            break
    for g in gunler:
        ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
