#!/usr/bin/env python3
"""Nevşehir Belediyesi vefat edenler okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.nevsehir.bel.tr/vefat-edenler?page=N — her "kutu" bir günün ilanı; içinde serbest <p> satırları:
  [tarih+gün] [N.]AD SOYAD / yaş / ÖLÜM NEDENİ / adres / namaz / mezarlık (kişiler boş <p> ile ayrılır, bazen numaralı).
Ayrıştırma sezgiseldir: kişi, ardından yalnız rakamdan oluşan YAŞ satırı gelen ad satırıdır. ÖLÜM NEDENİ (…ÖLÜM) ATILIR;
adresten yalnız "… MAH." mahalle adı alınır (sokak/no atılır). Tek başına ilçe adı olan satır (ör. KOZAKLI) ilçedir.
Kutunun başlık tarihi, kutu zaman damgasıyla (>3 gün fark) çelişirse zaman damgası kullanılır (kaynakta "06.09.2026" yazım hatası vardı).
Tarih = ilan tarihi (liste_tarihi). Ayrıştırılamayan kutular veri/nevsehir/ayristirilamayan.json'a yazılır.
Kullanım: python3 okuyucu/nevsehir.py [--gun 7]
"""
import html, json, os, re, sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Nevşehir"
URL = "https://www.nevsehir.bel.tr/vefat-edenler"
KAYNAK_AD = "Nevşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "nevsehir")
MAKS_SAYFA = 5


def temiz(p):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", p)).replace("\xa0", " ").split())


def kutular(sayfa):
    """-> [(paragraflar, zaman_damgasi_tarihi)]"""
    sonuc = []
    for b, ts in re.findall(r'<div class="news-box-download">(.*?)<span style="width:20%">\s*([^<]*?)\s*</span>', sayfa, re.S):
        ps = [temiz(p) for p in re.findall(r"<p>(.*?)</p>", b, re.S)]
        m = re.match(r"(\d{2})-(\d{2})-(\d{4})", ts)
        sonuc.append((ps, f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None))
    return sonuc


def kutu_tarihi(ps, ts):
    """Başlık tarihi ile zaman damgasını uzlaştırır -> (tarih, başlık_ham)"""
    ilk = ps[0] if ps else ""
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", ilk)
    baslik = None
    if m:
        try:
            baslik = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date().isoformat()
        except ValueError:
            baslik = None
    if ts and baslik:
        fark = abs((date.fromisoformat(ts) - date.fromisoformat(baslik)).days)
        return (baslik if fark <= 3 else ts), ilk
    return (baslik or ts), ilk


def kisileri_ayir(ps):
    """Başlık satırından sonraki paragrafları kişilere böler: yaş satırından geriye doğru ad bulunur."""
    govde = [p for p in ps[1:] if p]
    govde = [p for p in govde if not re.fullmatch(r"\d+\s*[-.]?", p) or re.fullmatch(r"\d{1,3}", p)]   # '1-' numara satırlarını at, yaşı koru
    idx = [i for i, p in enumerate(govde) if re.fullmatch(r"\d{1,3}", p) and i > 0]
    kisiler = []
    for n, i in enumerate(idx):
        son = idx[n + 1] - 1 if n + 1 < len(idx) else len(govde)
        kisiler.append({"ad": govde[i - 1], "yas": int(govde[i]), "satirlar": govde[i + 1:son]})
    return kisiler


def kisi_coz(k):
    ad = re.sub(r"^\s*\d+\s*[-.)]?\s*", "", k["ad"]).strip()
    mahalle = namaz = mezarlik = ilce_ham = None
    diger = []
    for s in k["satirlar"]:
        u = ortak.tr_lower(s)
        if re.search(r"ölüm|olum", u):                 # ölüm nedeni: ALINMAZ
            continue
        if re.search(r"mezar|mezrl|kabirstan|kabristan", u):
            mezarlik = s
        elif re.search(r"namaz|cami", u):
            namaz = s
        elif re.search(r"\bmah\b|mah\.|mahalle", u):
            m = re.match(r"^(.*?)\s+MAH(?:ALLES[İI])?\b\.?", s, re.I)
            if m and m.group(1).strip():
                mahalle = m.group(1).strip()
        elif any(ortak.katla(s) == ortak.katla(x) for x in ortak.ilce_listesi(IL)) and not ilce_ham:
            ilce_ham = s
        elif re.search(r"\bno\s*:|\bapt\b|\bkat\b|\bsk\b|\bsok\b|\bcd\b|\bcad\b|\bst\b|\d+/\d+", u):
            continue                                    # sokak/bina adresi artığı: ATILIR
        else:
            diger.append(s)
    return {"ad": ad, "yas": k["yas"], "mahalle": mahalle, "namaz": namaz, "mezarlik": mezarlik,
            "ilce_ham": ilce_ham, "diger": diger}


def kayda_cevir(c, gun, baslik_ham, url, alindi):
    return {
        "id": ortak.kayit_id("nevsehir", c["ad"], gun, f'{c["yas"]}|{c["mezarlik"] or ""}'),
        "il": IL,
        "ilce": ortak.tr_title(c["ilce_ham"]) if c["ilce_ham"] else None,
        "mahalle": ortak.tr_title(c["mahalle"]) if c["mahalle"] else None,
        "ad_soyad": ortak.tr_title(c["ad"]),
        "anne_baba": None, "yas": c["yas"], "dogum_tarihi": None, "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(c["mezarlik"]) if c["mezarlik"] else None,
        "defin_zamani": None, "namaz_tarihi": None,
        "namaz_yeri_vakti": ortak.tr_title(c["namaz"]) if c["namaz"] else None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"baslik_tarihi": baslik_ham, "diger_satirlar": c["diger"] or None},
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
    gor, bozuk = set(), []
    for sayfa_no in range(1, MAKS_SAYFA + 1):
        url = f"{URL}?page={sayfa_no}"
        try:
            kt = kutular(ortak.indir(url))
        except Exception as e:
            print(f"HATA sayfa {sayfa_no}: {e}", file=sys.stderr)
            break
        if not kt:
            break
        tarihler = []
        for ps, ts in kt:
            g, baslik_ham = kutu_tarihi(ps, ts)
            tarihler.append(g)
            if g not in by_gun:
                continue
            kisiler = kisileri_ayir(ps)
            if not kisiler:
                bozuk.append({"tarih": g, "paragraflar": ps})
                continue
            for k in kisiler:
                kayit = kayda_cevir(kisi_coz(k), g, baslik_ham, url, alindi)
                if kayit["id"] not in gor:
                    gor.add(kayit["id"])
                    by_gun[g].append(kayit)
        if all(t and t < gunler[-1] for t in tarihler):
            break
    for g in gunler:
        ortak.gun_yaz(KOK, IL, g, by_gun[g])
        print(f"{g}: {len(by_gun[g])} kayıt")
    if bozuk:
        ortak.json_yaz(os.path.join(KOK, "ayristirilamayan.json"), bozuk)
        print(f"UYARI: {len(bozuk)} kutu ayrıştırılamadı (ayristirilamayan.json)", file=sys.stderr)
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, gunler, by_gun)


if __name__ == "__main__":
    main()
