#!/usr/bin/env python3
"""e-DEVLET "<Belediye> Vefat Bilgisi Sorgulama" okuyucusu (14.10.2026, site sahibi: "e-Devlette maden buldum").
Kaynak: turkiye.gov.tr/<belediye>-vefat-sorgulama (girişsiz, CAPTCHA'sız olanlar). robots.txt: "User-agent: *  Allow: /" (kural yok).
Akış (hizmet başına): 1 GET (form + token, çerez) + 3 POST (bugün, dün, evvelsi gün; site yalnız bu 3 günü tutar, eski tarih boş döner).
  Token aynı oturumda tekrar kullanılabilir (14.10 doğrulandı). İstekler arası ≥3,5 sn. Kısa kopmalarda (IncompleteRead / bağlantı kapandı) en çok 1 tekrar.
  Hizmet CAPTCHA (captcha_name alanı), giriş ya da 404 ise BIRAKILIR (dolanma yok).
Alınan alanlar: ad soyad, vefat tarihi (= sorgulanan gün), yaş (sayıysa), ilçe (hizmet tek ilçeninse). ALINMAYAN: ölüm sebebi (sağlık verisi), baba adı, doğum tarihi, "Detay" sayfaları
  (cenazeyle ilgilenen kişi vb.; hizmet başına ek istek gerektirir), T.C. kimlik, adres, telefon.
e-Devlet kullanım şartları yazılı izinsiz çoğaltmayı yasaklar; site sahibi kararıyla uygulanır (CLAUDE.md / görev 14.10.2026): alınan alan en az, istek çok düşük.
Çıktı: veri/<il>/_ulusal.json (vefatilan.py ile AYNI şema; aynı dosyaya id ile birleştirilir). kaynak_turu alanı YOK (resmî belediye verisi).
Durum: veri/_edevlet_durum.json (hizmet -> durum, kayıt sayıları). Kullanım: python3 okuyucu/edevlet.py [--kuru] [--hizmet slug,slug] [--kesif]"""
import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, http.cookiejar, http.client
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

DIZIN = os.path.dirname(os.path.abspath(__file__))
VERI = os.environ.get("EDEVLET_VERI") or os.path.join(DIZIN, "..", "veri")   # EDEVLET_VERI: deneme çıktısı için ayrı klasör
TABAN = "https://www.turkiye.gov.tr/"
BEKLE = 3.5
HIZMET_ARASI_SN = int(os.environ.get("EDEVLET_HIZMET_ARASI_SN", "600"))   # 14.10.2026 sahibi "nazik kullanim": hizmetler arasi 10 dk (--kuru/--hizmet: 0)
ISTEK_TAVANI = int(os.environ.get("EDEVLET_ISTEK_TAVANI", "60"))             # kosu basina toplam istek tavani
KOSU_SAATLERI = os.environ.get("EDEVLET_KOSU_SAATLERI", "")                  # "06,18": yalniz bu TR saatlerinde kosar (bos: her zaman)
CAPTCHA_BEKLEME_SA = 6               # hizmet CAPTCHA gösterdiyse (14.10: art arda sorguda uyarlamalı CAPTCHA çıkıyor) 6 saat hiç istek atma
GUN_SAYISI = 3                       # bugün + dün + evvelsi (site bu kadarını tutuyor)
ILCELER = json.load(open(os.path.join(DIZIN, "..", "uygulama", "assets", "veri", "ilceler.json"), encoding="utf-8"))

# slug -> (il, ilçe | None [büyükşehir/il geneli]). Önce ilçe hizmetleri okunur; il geneli listede aynı kişi varsa ilçeli kayıt kalır.
HIZMETLER = {
    "bagcilar-belediyesi-vefat-sorgulama": ("İstanbul", "Bağcılar"),
    "pendik-belediyesi-vefat-sorgulama": ("İstanbul", "Pendik"),
    "kucukcekmece-belediyesi-vefat-sorgulama": ("İstanbul", "Küçükçekmece"),
    "silivri-belediyesi-vefat-sorgulama": ("İstanbul", "Silivri"),
    "sultangazi-belediyesi-vefat-sorgulama": ("İstanbul", "Sultangazi"),
    "uskudar-belediyesi-vefat-sorgulama": ("İstanbul", "Üsküdar"),
    "arnavutkoy-belediyesi-vefat-sorgulama": ("İstanbul", "Arnavutköy"),
    "bahcelievler-belediyesi-vefat-sorgulama": ("İstanbul", "Bahçelievler"),
    "beylikduzu-belediyesi-vefat-sorgulama": ("İstanbul", "Beylikdüzü"),
    "buyukcekmece-belediyesi-vefat-sorgulama": ("İstanbul", "Büyükçekmece"),
    "gaziosmanpasa-belediyesi-vefat-sorgulama": ("İstanbul", "Gaziosmanpaşa"),
    "kagithane-belediyesi-vefat-sorgulama": ("İstanbul", "Kâğıthane"),
    "tuzla-belediyesi-vefat-sorgulama": ("İstanbul", "Tuzla"),
    "bafra-belediyesi-vefat-sorgulama": ("Samsun", "Bafra"),
    "inegol-belediyesi-vefat-sorgulama": ("Bursa", "İnegöl"),
    "korfez-belediyesi-vefat-sorgulama": ("Kocaeli", "Körfez"),
    "gebze-belediyesi-vefat-sorgulama": ("Kocaeli", "Gebze"),
    "mamak-belediyesi-vefat-sorgulama-v3": ("Ankara", "Mamak"),
    "cerkezkoy-belediyesi-vefat-sorgulama": ("Tekirdağ", "Çerkezköy"),
    "develi-belediyesi-vefat-sorgulama": ("Kayseri", "Develi"),
    "osmancik-belediyesi-vefat-sorgulama": ("Çorum", "Osmancık"),
    "istanbul-buyuksehir-belediyesi-vefat-sorgulama": ("İstanbul", None),
    "izmir-buyuksehir-belediyesi-vefat-sorgulama": ("İzmir", None),
    "kocaeli-buyuksehir-belediyesi-vefat-sorgulama": ("Kocaeli", None),
    "konya-buyuksehir-belediyesi-vefat-sorgulama": ("Konya", None),
    "denizli-buyuksehir-belediyesi-vefat-sorgulama": ("Denizli", None),
    "kahramanmaras-buyuksehir-belediyesi-vefat-sorgulama": ("Kahramanmaraş", None),
    "trabzon-buyuksehir-belediyesi-vefat-sorgulama": ("Trabzon", None),
    "tekirdag-buyuksehir-belediyesi-vefat-sorgulama": ("Tekirdağ", None),
    "erzurum-buyuksehir-belediyesi-vefat-sorgulama-v3": ("Erzurum", None),
    "diyarbakir-buyuksehir-belediyesi-vefat-sorgulama-v3": ("Diyarbakır", None),
}
# BİLİNEN HARİÇ (14.10.2026 keşfi): CAPTCHA -> bursa-buyuksehir-, sakarya-buyuksehir-belediyesi-vefat-sorgulama;
# 404 -> antalya-buyuksehir-, beyoglu-, derince-, eyup-, malatya-buyuksehir-, uzundere-belediyesi-vefat-sorgulama, diyarbakir/erzurum (v3'süz), pendik-belediyesi-vefat;
# belirsiz il -> zonguldak-karapinar-belediyesi-vefat-sorgulama (kuruma bakılıp eklenir).

_TR = str.maketrans("çğıöşüÇĞİÖŞÜI", "cgiosucgiosuı")


def kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9]+", "", s)


IL_SLUG = {kat(il): kat(il) for il in ILCELER}
IL_ADI = {kat(il): il for il in ILCELER}
ILCE_ADI = {kat(il): {kat(i): i for i in ilc} for il, ilc in ILCELER.items()}


def bugun_tr():
    return (datetime.now(timezone.utc) + timedelta(hours=3)).date()


class Oturum:
    """Çerezli tek istemci; turkiye.gov.tr'ye istekler arası ≥ BEKLE sn."""
    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.son = 0.0
        self.istek_sayisi = 0

    def al(self, url, veri=None, ref=None):
        gecen = time.time() - Oturum._son_genel
        if gecen < BEKLE:
            time.sleep(BEKLE - gecen)
        h = {"User-Agent": ortak.UA}
        if ref:
            h["Referer"] = ref
        if veri is not None:
            h["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            with self.op.open(urllib.request.Request(url, data=veri, headers=h), timeout=40) as r:
                govde = r.read().decode("utf-8", "replace")
                son_url = r.geturl()
        finally:
            Oturum._son_genel = time.time()
            self.istek_sayisi += 1
        return son_url, govde


Oturum._son_genel = 0.0


def al_tekrarli(oturum, url, veri=None, ref=None):
    """Kısa kopmada (bağlantı kapandı / yarım yanıt) en çok 1 tekrar."""
    try:
        return oturum.al(url, veri, ref)
    except (http.client.IncompleteRead, http.client.RemoteDisconnected, ConnectionResetError, urllib.error.URLError, TimeoutError):
        time.sleep(6)
        return oturum.al(url, veri, ref)


def govde_blok(s):
    i = s.find('id="pageContentBlock"')
    return s[i:] if i >= 0 else s


def satirlar(g):
    """Sonuç tablosu -> [(ad, yas_metni)]. Yalnız ad ve yaş sütunu okunur; baba adı, doğum tarihi, ölüm sebebi atılır."""
    cikti = []
    m = re.search(r"<table[^>]*>.*?</table>", g, re.S)
    if not m:
        return None
    basliklar = [re.sub(r"<[^>]+>", "", t).strip() for t in re.findall(r"<th[^>]*>(.*?)</th>", m.group(0), re.S)]
    try:
        i_ad, i_yas = basliklar.index("Adı Soyadı"), basliklar.index("Yaşı")
    except ValueError:
        return None
    for tr in re.findall(r"<tr>(.*?)</tr>", m.group(0), re.S):
        hucre = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(hucre) > max(i_ad, i_yas):
            cikti.append((hucre[i_ad], hucre[i_yas]))
    return cikti


ADSIZ = re.compile(r"^(bebek|kimliksiz|bilinmeyen|bilinmiyor|erkek|kad[ıi]n|ceset|[şs]ahıs|sahis)\b", re.I)


def temiz_ad(ad):
    ad = re.sub(r"\s+", " ", ad or "").strip()
    if len(ad.split()) < 2 or re.search(r"[\d*]", ad) or ADSIZ.match(ortak.tr_lower(ad)):
        return None
    return ortak.tr_title(ad)


def kayit(slug, il, ilce, kurum, ad, yas_s, tarih, alindi, sira):
    il_k = kat(il)
    r = {a: None for a in ortak.ALANLAR}
    yas = int(yas_s) if re.fullmatch(r"\d{1,3}", yas_s or "") and 0 < int(yas_s) < 125 else None
    ilce_adi = ILCE_ADI[il_k].get(kat(ilce)) if ilce else None
    r.update({"id": ortak.kayit_id("edevlet", ad, tarih, f"{slug}|{yas}|{sira}"), "il": IL_ADI[il_k], "ilce": ilce_adi, "ad_soyad": ad, "yas": yas,
              "vefat_tarihi": tarih, "liste_tarihi": tarih, "kaynak_ad": f"{kurum} (e-Devlet)", "kaynak_url": TABAN + slug, "alindi": alindi,
              "ham": {"sayfa_tarihi": tarih, "hizmet": slug},
              "il_disi_defin": None, "ilce_belirsiz": ilce_adi is None})
    return r, IL_SLUG[il_k]


def kurum_adi(s, il, ilce):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    t = html.unescape(m.group(1)).strip() if m else ""
    t = re.sub(r"\s*-\s*Vefat Bilgisi Sorgulama.*$", "", t)
    return t or f"{ilce or il} Belediyesi"


def hizmet_oku(slug, il, ilce, gunler, alindi, durum):
    """-> ([kayıt..], not). Her hizmet: 1 GET + len(gunler) POST."""
    o = Oturum()
    url = TABAN + slug
    try:
        son_url, s = al_tekrarli(o, url)
    except urllib.error.HTTPError as e:
        return [], f"http{e.code}"
    except Exception as e:
        return [], f"hata:{str(e)[:60]}"
    g = govde_blok(s)
    if "giris.turkiye.gov.tr" in son_url:
        return [], "giris"
    if "captcha_name" in g:
        return [], "captcha"
    tok = re.search(r'name="token" value="([^"]*)"', g)
    if 'name="tarih"' not in g or not tok:
        return [], "form_yok"
    act = re.search(r'<form[^>]*id="mainForm"[^>]*action="([^"]+)"', g, re.S)
    post = (TABAN.rstrip("/") + html.unescape(act.group(1))) if act else url + "?submit"
    kurum = kurum_adi(s, il, ilce)
    out, sayilar = [], {}
    for gun in gunler:
        t_tr = gun.strftime("%d/%m/%Y")
        veri = urllib.parse.urlencode({"tarih": t_tr, "token": tok.group(1), "btn": "Sorgula"}).encode()
        try:
            _, s2 = al_tekrarli(o, post, veri, url)
        except Exception as e:
            sayilar[t_tr] = f"hata:{str(e)[:40]}"
            continue
        g2 = govde_blok(s2)
        if "captcha_name" in g2:
            return out, "captcha"
        if "<table" in g2 and "</table>" not in g2:                     # yarım gelen sayfa: bir kez daha
            try:
                _, s2 = al_tekrarli(o, post, veri, url)
                g2 = govde_blok(s2)
            except Exception:
                pass
        satir = satirlar(g2)
        if satir is None:
            sayilar[t_tr] = 0 if ("warningContainer" in g2 or 'name="tarih"' in g2) else "belirsiz"
            nt = re.search(r'name="token" value="([^"]*)"', g2)
            if nt:
                tok = nt
            continue
        echo = re.search(r"Vefat Tarihi\s*</?[^>]*>\s*(?:<[^>]+>\s*)*(\d{2}/\d{2}/\d{4})", g2) or re.search(r"Vefat Tarihi[^0-9]{0,60}(\d{2}/\d{2}/\d{4})", g2)
        if echo and echo.group(1) != t_tr:
            sayilar[t_tr] = "tarih_uyusmuyor"
            continue
        n, sira = 0, {}
        for ad_ham, yas_s in satir:
            ad = temiz_ad(ad_ham)
            if not ad:
                continue
            sira[ad] = sira.get(ad, 0) + 1
            r, slug_il = kayit(slug, il, ilce, kurum, ad, yas_s, gun.isoformat(), alindi, sira[ad])
            out.append((r, slug_il))
            n += 1
        sayilar[t_tr] = n
    durum["son_istek"] = o.istek_sayisi
    return out, sayilar


def main():
    kuru = "--kuru" in sys.argv
    secili = sys.argv[sys.argv.index("--hizmet") + 1].split(",") if "--hizmet" in sys.argv else None
    if not ortak.robots_izin(TABAN + "x"):
        print("robots.txt turkiye.gov.tr'yi yasaklıyor: durdu", file=sys.stderr)
        return
    bugun = bugun_tr()
    gunler = [bugun - timedelta(days=i) for i in range(GUN_SAYISI)]
    alindi = ortak.simdi_iso()
    durum_yol = os.path.join(VERI, "_edevlet_durum.json")
    durum = {}
    try:
        onceki = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        onceki = {}
    # ilçe hizmetleri önce, il geneli sonra
    sira = sorted(HIZMETLER.items(), key=lambda kv: (kv[1][1] is None, kv[0]))
    toplam = {}
    if KOSU_SAATLERI and not secili and not kuru and os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":   # elle tetiklenen kosu saat kapisini gecer
        saat = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%H")
        if saat not in [x.strip() for x in KOSU_SAATLERI.split(",")]:
            print(f"e-Devlet: kosu saati degil (TR {saat}; izinli {KOSU_SAATLERI}), istek yok", file=sys.stderr)
            return
    ara = 0 if (kuru or secili) else HIZMET_ARASI_SN
    toplam_istek = 0
    gorulen_kisi = set()                                               # (il, ad_norm, tarih): ilçeli kayıt varken il geneli kopyasını ekleme
    yeni = {}
    for slug, (il, ilce) in sira:
        if secili and slug not in secili:
            continue
        o = onceki.get(slug) or {}
        if o.get("durum") == "captcha" and o.get("zaman") and (datetime.now(timezone.utc) - datetime.fromisoformat(o["zaman"])).total_seconds() < CAPTCHA_BEKLEME_SA * 3600:
            print(f"  {slug}: captcha beklemesi ({CAPTCHA_BEKLEME_SA} sa), istek yok", file=sys.stderr)
            continue
        if toplam_istek >= ISTEK_TAVANI:
            print(f"  {slug}: kosu istek tavani ({ISTEK_TAVANI}) doldu, sonraki kosuya", file=sys.stderr)
            continue
        if ara and toplam_istek:
            time.sleep(ara)                                                # nazik kullanim: hizmetler arasi bekleme
        sonuc, sayilar = hizmet_oku(slug, il, ilce, gunler, alindi, {})
        toplam_istek += 4
        if isinstance(sayilar, str):
            durum[slug] = {"durum": sayilar, "zaman": alindi}
            print(f"  {slug}: {sayilar}", file=sys.stderr)
            continue
        eklenen = 0
        for r, slug_il in sonuc:
            anahtar = (slug_il, kat(r["ad_soyad"]), r["vefat_tarihi"])
            if anahtar in gorulen_kisi and ilce is None:
                continue
            gorulen_kisi.add(anahtar)
            yeni.setdefault(slug_il, []).append(r)
            eklenen += 1
        durum[slug] = {"durum": "calisir" if any(isinstance(v, int) and v > 0 for v in sayilar.values()) else "bos", "gunler": sayilar, "eklenen": eklenen, "zaman": alindi}
        toplam[slug] = eklenen
        print(f"  {slug}: {sayilar} -> {eklenen} kayıt", file=sys.stderr)
    if kuru:
        print(f"[kuru] {sum(toplam.values())} kayıt, {len(yeni)} il")
        return
    sinir = (bugun - timedelta(days=7)).isoformat()
    for slug_il, recs in yeni.items():
        yol = os.path.join(VERI, slug_il, "_ulusal.json")
        eski = []
        try:
            eski = json.load(open(yol, encoding="utf-8")).get("kayitlar", [])
        except Exception:
            pass
        kay = {x["id"]: x for x in eski}
        kay.update({x["id"]: x for x in recs})
        kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
        ortak.json_yaz(yol, {"il": IL_ADI.get(slug_il, slug_il), "kayitlar": list(kay.values()), "guncelleme": alindi})
    try:
        eski_d = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        eski_d = {}
    eski_d.update(durum)
    ortak.json_yaz(durum_yol, eski_d)
    print(f"e-Devlet: {sum(toplam.values())} kayıt, {len(yeni)} il, hizmet durumu: " + ", ".join(f"{k.split('-belediyesi')[0]}={v}" for k, v in sorted(toplam.items())))


if __name__ == "__main__":
    main()
