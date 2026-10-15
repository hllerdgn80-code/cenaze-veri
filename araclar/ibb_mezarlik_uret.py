#!/usr/bin/env python3
"""H66 (15.10.2026) okuyucu/veri/mezarlik_resmi.json'a İBB "Mezarlık Adres Bilgileri" (İBB Açık Veri Lisansı) satırlarını yazar.
Kaynak: https://data.ibb.gov.tr/dataset/mezarlik-adres-bilgileri (ilce-bazli-mezarliklar.xlsx: İLÇE, MAHALLE, MEZARLIK ADI). Tahmin yok:
ad aynen alınır, ilçe ilceler.json yazımına çevrilir (listede yoksa satır ATILIR). Başka il için eklenen kayıtlar korunur (yalnız İstanbul/İBB satırları yenilenir).
Kullanım: python3 araclar/ibb_mezarlik_uret.py [--xlsx yerel.xlsx]   (python3 -I DEĞİL; okuyucu/ yolu eklenir)"""
import json, os, re, subprocess, sys, zipfile, io
from datetime import datetime, timezone, timedelta
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "okuyucu"))
import ortak
URL = "https://data.ibb.gov.tr/dataset/73b8b262-0d0f-46f4-9fa5-f55f9dfdeccd/resource/c2e9fc32-6e83-4b77-ba01-e943132867b4/download/ilce-bazli-mezarliklar.xlsx"
SAYFA = "https://data.ibb.gov.tr/dataset/mezarlik-adres-bilgileri"
CIKTI = os.path.join(KOK, "okuyucu", "veri", "mezarlik_resmi.json")
KAYNAK_AD = "İBB Açık Veri – Mezarlık Adres Bilgileri (İBB Açık Veri Lisansı)"


def xlsx_satirlari(veri):
    z = zipfile.ZipFile(io.BytesIO(veri))
    paylasilan = []
    if "xl/sharedStrings.xml" in z.namelist():
        x = z.read("xl/sharedStrings.xml").decode("utf-8")
        for si in re.findall(r"<si>(.*?)</si>", x, re.S):
            paylasilan.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
    import html
    sayfa = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    satirlar = []
    for r in re.findall(r"<row[^>]*>(.*?)</row>", sayfa, re.S):
        d = {}
        for ref, t, v in re.findall(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', r, re.S):
            m = re.search(r"<v>(.*?)</v>", v or "", re.S)
            if not m:
                continue
            val = paylasilan[int(m.group(1))] if 't="s"' in t else m.group(1)
            d[ref] = html.unescape(val).strip()
        satirlar.append(d)
    return satirlar


# İBB sütunundaki yazımların ilceler.json karşılığı (resmî ad değişikliği / yazım / İBB kısaltması; ikinci bir yorum yok):
ILCE_ESLEME = {"eyup": "Eyüpsultan", "kagithane": "Kâğıthane", "gop": "Gaziosmanpaşa"}


# tek başına jenerik ad (her ilçede bulunabilir): resmî listede tek satır olsa da bağlanmaz (mezarlik_ilce_uret.py ile aynı ilke)
JENERIK = {"yeni", "eski", "koy", "sehir", "merkez", "asri", "aile", "kent", "sehitlik", "sehitligi", "cumhuriyet", "ortak", "genel", "musalla"}


def uret(veri):
    sat = xlsx_satirlari(veri)
    baslik = sat[0]
    assert (baslik.get("A", "").upper().startswith("İLÇE") or baslik.get("A", "").upper().startswith("ILCE")) and "MEZARLIK" in baslik.get("C", "").upper(), baslik
    liste = ortak.ilce_listesi("İstanbul")
    tarih = (datetime.now(timezone.utc) + timedelta(hours=3)).date().isoformat()
    cikti, atilan, goruldu = [], 0, set()
    for r in sat[1:]:
        ilce = ortak._ad_bul(ortak.katla(r.get("A")), liste) or ILCE_ESLEME.get(ortak.katla(r.get("A")))
        if ilce and ilce not in liste:
            ilce = None
        ad = (r.get("C") or "").strip()
        if not ilce or not ortak.mezarlik_norm(ad) or ortak.mezarlik_norm(ad) in JENERIK:
            atilan += 1
            continue
        if (ortak.mezarlik_norm(ad), ilce) in goruldu:
            continue
        goruldu.add((ortak.mezarlik_norm(ad), ilce))
        cikti.append({"ad": ad, "il": "İstanbul", "ilce": ilce, "kaynak_url": SAYFA, "kaynak_ad": KAYNAK_AD, "tarih": tarih})
    return cikti, atilan


def main():
    if "--xlsx" in sys.argv:
        veri = open(sys.argv[sys.argv.index("--xlsx") + 1], "rb").read()
    else:
        if not ortak.robots_izin(URL):
            sys.exit("robots.txt yasakliyor")
        # İBB sitesi özel User-Agent'a 403 veriyor (curl varsayılanı 200): osm_yer_cek.py gibi curl ile alınır (tek dosya, robots Crawl-Delay 10 sn'ye uygun)
        veri = subprocess.run(["curl", "-s", "-f", "-m", "60", URL], capture_output=True, check=True).stdout
    yeni, atilan = uret(veri)
    eski = []
    try:
        eski = [r for r in json.load(open(CIKTI, encoding="utf-8")) if not (r.get("il") == "İstanbul" and r.get("kaynak_url") == SAYFA)]
    except Exception:
        pass
    ortak.json_yaz(CIKTI, eski + yeni)
    farkli = len({ortak.mezarlik_norm(r["ad"]) for r in yeni})
    cakisan = sum(1 for n in {ortak.mezarlik_norm(r["ad"]) for r in yeni} if len({r["ilce"] for r in yeni if ortak.mezarlik_norm(r["ad"]) == n}) > 1)
    print(f"mezarlik_resmi.json: {len(yeni)} satir (İBB), {farkli} farkli ad, {cakisan} ad birden cok ilcede (baglanmaz), {atilan} satir atildi; toplam {len(eski) + len(yeni)}")


if __name__ == "__main__":
    main()
