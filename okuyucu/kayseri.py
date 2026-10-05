#!/usr/bin/env python3
"""Kayseri Büyükşehir Belediyesi vefat ilanları okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.kayseri.bel.tr/vefat-ilanlari (ASP.NET WebForms). Sayfadan __VIEWSTATE / __VIEWSTATEGENERATOR /
__EVENTVALIDATION alınır, tarih alanı (ctl00$contentHolder$vefatDate, GG.AA.YYYY) ile "Listele" düğmesinin
postback'i POST edilir. Giriş/CAPTCHA yok; sayfada CAPTCHA ya da giriş formu çıkarsa okuma DURUR.
KVKK: TAZİYE ADRESİ ALINMAZ (kişisel konum; ilçe çıkarmak için de kullanılmaz), koordinatlar alınmaz.
İlçe kaynakta yok -> ilce None + ilce_belirsiz. Hacim düşüktür (liste yalnız Mezarlık Bilgi Sistemi'ne girilenleri verir).
Kullanım: python3 okuyucu/kayseri.py [--gun 7]
"""
import html, os, re, sys, urllib.parse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

IL = "Kayseri"
URL = "https://www.kayseri.bel.tr/vefat-ilanlari"
KAYNAK_AD = "Kayseri Büyükşehir Belediyesi"
BEKLE = 3.5
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "kayseri")
TARIH_ALANI = "ctl00$contentHolder$vefatDate"
DUGME = "ctl00$contentHolder$btnSorgula"
GIZLI = ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION")


def metin(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def gizli_alanlar(sayfa):
    f = {}
    for n in GIZLI:
        m = re.search(rf'name="{n}"[^>]*value="([^"]*)"', sayfa)
        if not m:
            raise RuntimeError(f"{n} sayfada yok (form düzeni değişmiş ya da erişim engeli)")
        f[n] = html.unescape(m.group(1))
    return f


def engel_var(sayfa):
    """Giriş formu ya da CAPTCHA belirtisi."""
    return bool(re.search(r"(?i)captcha|g-recaptcha|type=\"password\"", sayfa))


def ayristir(sayfa):
    """-> [ham sözlük]. Taziye adresi hücresi bilerek okunmaz."""
    if "contentHolder_container" not in sayfa:
        raise RuntimeError("liste kapsayıcısı yok")
    kayitlar = []
    for tr in re.findall(r'<tr class="ng-scope">(.*?)</tr>', sayfa, re.S):
        h = {}
        for et, deger in re.findall(r'<td data-th="([^"]*)">(.*?)</td>', tr, re.S):
            if ortak.tr_lower(et).startswith("taziye"):
                continue
            h[et] = metin(deger)
        if h.get("Adı Soyadı"):
            kayitlar.append(h)
    return kayitlar


def kayda_cevir(h, gun, alindi):
    ad = h["Adı Soyadı"]
    bab = h.get("Baba Adı / Ana Adı", "")
    baba, _, ana = (x.strip() for x in bab.partition("/"))
    dy, _, dyil = (x.strip() for x in h.get("Doğum Yeri / Yılı", "").partition("/"))
    cami, vakit = h.get("Yer") or None, h.get("Vakit") or None
    mez_ham = h.get("Mezarlık") or ""
    ada = re.search(r"\(([^)]*)\)\s*$", mez_ham)
    mezarlik = re.sub(r"\s*\([^)]*\)\s*$", "", mez_ham).strip() or None
    ap = "-".join(x for x in (ana, baba) if x)
    return {
        "id": ortak.kayit_id("kayseri", ad, gun, f"{bab}|{dyil}|{cami or ''}|{mez_ham}"),
        "il": IL,
        "ilce": None,                # kaynakta yok; taziye adresinden çıkarılmaz (KVKK)
        "mahalle": None,
        "ad_soyad": ortak.tr_title(ad),
        "anne_baba": ortak.tr_title(ap) or None,
        "yas": None,
        "dogum_tarihi": None,        # kaynak yalnız yıl veriyor (ham.dogum_yili)
        "vefat_tarihi": None,
        "defin_yeri": ortak.tr_title(mezarlik) if mezarlik else None,
        "defin_zamani": None,
        "namaz_tarihi": gun,         # liste, tarih seçilerek o güne sorgulanıyor (cenaze günü)
        "namaz_yeri_vakti": " – ".join(x for x in (ortak.tr_title(vakit) if vakit else None,
                                                    ortak.tr_title(cami) if cami else None) if x) or None,
        "liste_tarihi": gun,
        "kaynak_ad": KAYNAK_AD,
        "kaynak_url": URL,
        "alindi": alindi,
        "ham": {"baba_ana": bab or None, "dogum_yeri": dy or None, "dogum_yili": dyil or None,
                "yer": cami, "vakit": vakit, "mezarlik": mez_ham or None,
                "mezar_ada_parsel": ada.group(1) if ada else None},
        "il_disi_defin": None,
        "ilce_belirsiz": True,
    }


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(URL):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    sayfa = ortak.indir(URL, BEKLE)
    if engel_var(sayfa):
        print("DUR: sayfada giriş/CAPTCHA belirtisi var, okunmadı", file=sys.stderr)
        return
    alanlar = gizli_alanlar(sayfa)
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    by_gun = {}
    for g in gunler:
        d = date.fromisoformat(g)
        form = dict(alanlar, __EVENTTARGET=DUGME, __EVENTARGUMENT="")
        form[TARIH_ALANI] = d.strftime("%d.%m.%Y")
        try:
            sayfa = ortak.indir(URL, BEKLE, veri=urllib.parse.urlencode(form).encode())
            if engel_var(sayfa):
                print(f"DUR: {g} yanıtında giriş/CAPTCHA belirtisi, okuma bırakıldı", file=sys.stderr)
                break
            ham = ayristir(sayfa)
            try:
                alanlar = gizli_alanlar(sayfa)       # yeni durum belirteçleri varsa onları kullan
            except RuntimeError:
                pass
        except Exception as e:
            print(f"HATA {g}: {e}", file=sys.stderr)
            continue
        alindi = ortak.simdi_iso()
        gor, tek = set(), []
        for h in ham:
            k = kayda_cevir(h, g, alindi)
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, IL, g, tek)
        print(f"{g}: {len(tek)} kayıt")
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, IL, sorted(by_gun, reverse=True), by_gun)


if __name__ == "__main__":
    main()
