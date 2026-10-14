#!/usr/bin/env python3
"""ULUSAL AKIS okuyucusu (14.10.2026, site sahibi: "bu siteden bütün il ve ilçeleri doldur").
Kaynak: vefatilanlari.com.tr (Dijital Mezarlık) — ülke geneli, en yeniden eskiye; her kartta ad, vefat tarihi, İL / İLÇE ve mezarlık var.
Okuma: POST /Cenaze-İlanları sayfa=N (filtre boş = tüm iller), 22 kart/sayfa. robots.txt yok (404/HTML) → kural yok; yine de:
  - istekler arası ≥3,5 sn (ortak.indir), koşu başına ≤ AZAMI_SAYFA sayfa, ilk koşuda 3 günlük pencere, sonrakilerde yalnız yeni kartlar.
Alınan alanlar: ad soyad, vefat tarihi, il, ilçe (yalnız ilin gerçek ilçe listesinde ise), mezarlık adı. ALINMAYAN: ilan cümlesi, anma/dua sayaçları, fotoğraf, yakın adı.
Çıktı: veri/<il>/_ulusal.json (iç dosya; ulusal_birlestir.py son7gun'a katar; yayına yalnız süzülmüş hâli gider). Durum: veri/_vefatilan_durum.json.
Kullanım: python3 okuyucu/vefatilan.py [--kuru] [--gun 3]"""
import html, json, os, re, sys, urllib.parse
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

DIZIN = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(DIZIN, "..", "veri")
URL = "https://www.vefatilanlari.com.tr/Cenaze-%C4%B0lanlar%C4%B1"
REFERER = "https://www.vefatilanlari.com.tr/"
KAYNAK_AD = "ulusal liste"
AZAMI_SAYFA = 45
BEKLE = 3.5
KAYNAK_TURU = "yerel_basin"      # mevcut kapi (kapi.py K8) ve yayin suzgeci (yayin_suz.py) kilitlerinden gecer; ham.tarih_kaynagi="ilan_vefat_tarihi"
ILCELER = json.load(open(os.path.join(DIZIN, "..", "uygulama", "assets", "veri", "ilceler.json"), encoding="utf-8"))

_TR = str.maketrans("çğıöşüÇĞİÖŞÜI", "cgiosucgiosuı")


def kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9]+", "", s)


IL_SLUG = {kat(il): kat(il) for il in ILCELER}                  # 'Şanlıurfa' -> 'sanliurfa' (klasör adı)
ILCE_TAM = {kat(il): {kat(i): i for i in ilc} for il, ilc in ILCELER.items()}
IL_ADI = {kat(il): il for il in ILCELER}
AYLAR = {"oca": 1, "şub": 2, "sub": 2, "mar": 3, "nis": 4, "may": 5, "haz": 6, "tem": 7, "ağu": 8, "agu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12}


def tarih(s):
    m = re.match(r"^(\d{1,2})\s+(\w{3})\w*\s+(\d{4})$", (s or "").strip())
    if not m:
        return None
    ay = AYLAR.get(m.group(2).lower().replace("ş", "ş"))
    if not ay:
        return None
    try:
        return date(int(m.group(3)), ay, int(m.group(1))).isoformat()
    except ValueError:
        return None


def bugun_tr():
    return (datetime.now(timezone.utc) + timedelta(hours=3)).date()


def sayfa_al(n):
    veri = urllib.parse.urlencode({"sayfa": n, "ad": "", "soyad": "", "v_tarih": "", "d_tarih": "", "cins": "", "yas": "", "v_sebep": "", "mezarlik": ""}).encode()
    s = ortak.indir(URL, bekle=BEKLE, veri=veri, basliklar={"Referer": REFERER, "Content-Type": "application/x-www-form-urlencoded"})
    return s.decode("utf-8", "replace") if isinstance(s, bytes) else s


def kartlar(s):
    """Sayfadan kart listesi -> [{ad, tarih, il, ilce, mezarlik, durum}] (ilan cümlesi saklanmaz)."""
    out = []
    for c in re.findall(r'<div class="ilan mb-0.*?(?=<div class="ilan mb-0|$)', s, flags=re.S):
        t = html.unescape(re.sub(r"<script.*?</script>", "", c, flags=re.S))
        satirlar = [x.strip() for x in re.sub(r"<[^>]+>", "\n", t).split("\n") if x.strip()]
        ad = satirlar[0] if satirlar else ""
        trh = next((tarih(x) for x in satirlar[1:4] if tarih(x)), None)
        yer = next((x for x in satirlar[1:8] if "/" in x and len(x) < 60), "")
        i = satirlar.index(yer) if yer in satirlar else -1
        mez = satirlar[i + 1] if i >= 0 and i + 1 < len(satirlar) else ""
        metin = " ".join(satirlar[i + 2:i + 4]) if i >= 0 else ""
        il, _, ilce = yer.partition("/")
        durum = "defnedildi" if re.search(r"defnedildi|toprağa verildi", metin, re.I) else ("defnedilecek" if re.search(r"defnedilecek|toprağa verilecek", metin, re.I) else None)
        if ad and trh and il:
            out.append({"ad": ad, "tarih": trh, "il": il.strip(), "ilce": ilce.strip(), "mezarlik": mez.strip(), "durum": durum})
    return out


def ad_duzelt(ad):
    """'Elif DOST' / 'ELİF DOST' -> 'Elif Dost'."""
    return ortak.tr_title(ad)


def kayit(k, alindi):
    il_k = kat(k["il"])
    if il_k not in IL_SLUG:
        return None
    ilce = ILCE_TAM[il_k].get(kat(k["ilce"])) or ("Merkez" if kat(k["ilce"]) == "merkez" else None)   # ilin gerçek ilçesi ya da kaynağın 'Merkez'i; aksi hâlde ilçesiz
    ad = ad_duzelt(k["ad"])
    mez = k["mezarlik"]
    if not mez or kat(mez) in (kat(k["il"]), "") or len(mez) > 60:
        mez = None
    r = {a: None for a in ortak.ALANLAR}
    r.update({"id": ortak.kayit_id("ulusal", ad, k["tarih"], k["il"] + "|" + (k["ilce"] or "")), "il": IL_ADI[il_k], "ilce": ilce, "ad_soyad": ad,
              "vefat_tarihi": k["tarih"], "defin_yeri": mez, "liste_tarihi": k["tarih"], "kaynak_ad": KAYNAK_AD, "kaynak_url": "https://www.vefatilanlari.com.tr/", "alindi": alindi,
              "ham": {"tarih_kaynagi": "ilan_vefat_tarihi", "sayfa_tarihi": k["tarih"], "durum": k["durum"]},
              "il_disi_defin": None, "ilce_belirsiz": ilce is None})
    r["kaynak_turu"] = KAYNAK_TURU
    return r, IL_SLUG[il_k]


def main():
    kuru = "--kuru" in sys.argv
    gun = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else 3
    sinir = (bugun_tr() - timedelta(days=gun)).isoformat()
    durum_yol = os.path.join(VERI, "_vefatilan_durum.json")
    try:
        durum = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        durum = {"gorulen": []}
    gorulen = set(durum.get("gorulen", []))
    alindi = ortak.simdi_iso()
    yeni, toplam, atlanan = {}, 0, 0
    for n in range(1, AZAMI_SAYFA + 1):
        try:
            sayfa = sayfa_al(n)
        except Exception as e:
            print(f"  sayfa {n} okunamadı: {str(e)[:80]}", file=sys.stderr)
            break
        kl = kartlar(sayfa)
        if not kl:
            break
        yeni_say, eski_say = 0, 0
        for k in kl:
            if k["tarih"] < sinir:
                eski_say += 1
                continue
            sonuc = kayit(k, alindi)
            if not sonuc:
                atlanan += 1
                continue
            r, slug = sonuc
            if r["id"] in gorulen:
                continue
            gorulen.add(r["id"])
            yeni.setdefault(slug, []).append(r)
            yeni_say += 1
            toplam += 1
        print(f"  sayfa {n}: {len(kl)} kart, {yeni_say} yeni, {eski_say} pencere dışı", file=sys.stderr)
        if eski_say == len(kl):
            break                                                    # sayfa tümüyle pencere dışı: dur
        if yeni_say == 0 and durum.get("gorulen"):
            break                                                    # artımlı koşu: bilinen kartlara ulaşıldı
    if kuru:
        print(f"[kuru] {toplam} yeni kayıt, {len(yeni)} il")
        return
    for slug, recs in yeni.items():
        yol = os.path.join(VERI, slug, "_ulusal.json")
        eski = []
        try:
            eski = json.load(open(yol, encoding="utf-8")).get("kayitlar", [])
        except Exception:
            pass
        kay = {x["id"]: x for x in eski}
        kay.update({x["id"]: x for x in recs})
        kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
        ortak.json_yaz(yol, {"il": IL_ADI.get(slug, slug), "kayitlar": list(kay.values()), "guncelleme": alindi})
    # bilinenler listesini pencereyle sınırla (dosya şişmesin)
    durum["gorulen"] = sorted(gorulen)[-12000:]
    ortak.json_yaz(durum_yol, durum)
    print(f"ulusal akış: {toplam} yeni kayıt, {len(yeni)} il, ilçesi doğrulanamayan/il dışı atlanan {atlanan}")


if __name__ == "__main__":
    main()
