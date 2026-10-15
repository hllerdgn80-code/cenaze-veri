#!/usr/bin/env python3
"""MÜFTÜLÜK PERSONEL LİSTESİ toplayıcı (15.10.2026; URUN-TASLAGI §37 ek-1). Yayına GİRMEZ: çıktı veri/_muftuluk_personel.json (`_` önekli).
Kaynak: <il>.diyanet.gov.tr/<ilce>/Sayfalar/personlist.aspx?...ContentCategory=personelimiz -> "Personelimiz" içerik sayfası.
robots.txt'ye uyar (urllib.robotparser), alan başına ≥3 sn bekler, User-Agent "KiminCenazesi/arastirma". Günde bir kez (sunucu/muftuluk.yml).
ÖLÇÜM (15.10.2026, Ordu/Trabzon/Samsun/Giresun/Rize ≈ 75 ilçe): "Personelimiz" sayfaları ya boş ya "Kişisel Verileri Koruma Kanunu kapsamında personel listesi yayından kaldırılmıştır"; gerçek ad+cami listesi bulunamadı.
Bu yüzden betik her ilçe için DURUMU kaydeder: liste | kaldirildi | bos | erisilemedi; yalnız 'ad + cami' satırı çıkarabildiği ilçelerin listesi Worker'a gider.
Kullanım:  python3 okuyucu/muftuluk_personel.py [--iller ordu,trabzon,...] [--olc] [--yukle]   (--olc: yalnız ölçüm raporu; --yukle: PANEL_ANAHTARI + AILE_WORKER_URL ile Worker'a POST /gorevli/liste)"""
import json, os, re, sys, time, html, urllib.request, urllib.robotparser, urllib.parse
from datetime import datetime, timezone

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
from vefatilan import ILCELER, IL_ADI, kat

UA = "KiminCenazesi/arastirma"
BEKLE = 3.0
CIKTI = os.path.join(DIZIN, "..", "veri", "_muftuluk_personel.json")
PILOT = ["ordu", "trabzon", "samsun", "giresun", "rize"]
UNVAN = re.compile(r"\b(imam|hatip|müezzin|muezzin|kayyım|kayyim|vaiz|müftü|muftu|öğretici|ogretici|din hizmetleri)\b", re.I)
CAMI = re.compile(r"\b[\wçğıöşüÇĞİÖŞÜ' .-]{2,40}?\s(cami|camii|camisi|mescidi)\b", re.I)
_son = {}
_robot = {}


def _bekle(host):
    g = time.time() - _son.get(host, 0)
    if g < BEKLE:
        time.sleep(BEKLE - g)
    _son[host] = time.time()


def izinli(host, yol):
    if host not in _robot:
        rp = urllib.robotparser.RobotFileParser()
        try:
            _bekle(host)
            ham = urllib.request.urlopen(urllib.request.Request(f"https://{host}/robots.txt", headers={"User-Agent": UA}), timeout=20).read().decode("utf-8", "ignore")
            rp.parse(ham.splitlines())
        except Exception:
            rp.parse(["User-agent: *", "Disallow: /_layouts/"])
        _robot[host] = rp
    return _robot[host].can_fetch(UA, f"https://{host}{yol}")


def al(host, yol):
    if not izinli(host, yol.split("?")[0]):
        return None
    _bekle(host)
    try:
        return urllib.request.urlopen(urllib.request.Request(f"https://{host}{yol}", headers={"User-Agent": UA}), timeout=30).read().decode("utf-8", "ignore")
    except Exception:
        return None


def metin(h):
    h = re.sub(r"(?s)<(script|style).*?</\1>", "", h)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", h))
    return [x.strip() for x in t.split("\n") if x.strip()]


def ilce_oku(il_slug, ilce_slug):
    """-> (durum, kayitlar[{ad_soyad, cami}])"""
    host = f"{il_slug}.diyanet.gov.tr"
    kok = f"/{ilce_slug}/Sayfalar/"
    h = al(host, kok + "personlist.aspx?MenuCategory=Kurumsal2&ContentCategory=personelimiz")
    if h is None:
        return "erisilemedi", []
    m = re.search(r'persons".*?href="([^"]*contentdetail\.aspx\?ContentId=\d+[^"]*)"', h, re.S | re.I)
    if not m:
        return "bos", []
    yol = urllib.parse.urlparse(html.unescape(m.group(1)))
    c = al(host, f"{yol.path}?{yol.query}")
    if c is None:
        return "erisilemedi", []
    l = metin(c)
    if any("yayından kaldırılmıştır" in x.lower() or "yayindan kaldirilmistir" in x.lower() for x in l):
        return "kaldirildi", []
    # içerik: menüden sonra, "Müftülüğümüz" yan menüsüne kadar
    try:
        i = next(k for k, x in enumerate(l) if re.match(r"\d{2}\.\d{2}\.\d{4}$", x))
        j = next(k for k in range(i, len(l)) if l[k] == "Müftülüğümüz")
        govde = l[i + 1:j]
    except StopIteration:
        return "bos", []
    kayitlar = []
    for satir in govde:
        if UNVAN.search(satir) and CAMI.search(satir):
            ad = re.sub(r"\b(imam[- ]hatip|müezzin[- ]kayyım|vaiz|öğretici)\b", "", satir.split("-")[0].split(",")[0], flags=re.I).strip(" :-–")
            cm = CAMI.search(satir).group(0).strip()
            if 2 <= len(ad.split()) <= 5 and not re.search(r"(mescid|cami|lise|okul|kurs|müftülü|muftulu)", ad, re.I):
                kayitlar.append({"ad_soyad": ad, "cami": cm})
    return ("liste" if kayitlar else "bos"), kayitlar


def main():
    arg = sys.argv[1:]
    iller = PILOT
    if "--iller" in arg:
        iller = arg[arg.index("--iller") + 1].split(",")
    elif "--hepsi" in arg:
        iller = sorted(IL_ADI)
    liste, durumlar = {}, {}
    for il in iller:
        if il not in IL_ADI:
            continue
        durumlar[il] = {}
        for ilce in ILCELER[IL_ADI[il]]:
            s = kat(ilce)
            d, k = ilce_oku(il, s)
            durumlar[il][s] = d
            if k:
                liste.setdefault(il, {})[s] = k
        sayim = {}
        for d in durumlar[il].values():
            sayim[d] = sayim.get(d, 0) + 1
        print(f"{il}: {sayim}", flush=True)
    cikti = {"guncelleme": datetime.now(timezone.utc).isoformat(timespec="seconds"), "durumlar": durumlar, "liste": liste}
    if "--olc" not in arg:
        os.makedirs(os.path.dirname(CIKTI), exist_ok=True)
        json.dump(cikti, open(CIKTI, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if "--yukle" in arg and liste:
        taban, anahtar = os.environ.get("AILE_WORKER_URL", "").rstrip("/"), os.environ.get("PANEL_ANAHTARI", "")
        if taban and anahtar:
            r = urllib.request.Request(f"{taban}/gorevli/liste", data=json.dumps({"liste": liste}).encode(), method="POST",
                                       headers={"x-gizli": anahtar, "Content-Type": "application/json", "User-Agent": UA})
            print(urllib.request.urlopen(r, timeout=60).read().decode()[:200])


if __name__ == "__main__":
    main()
