#!/usr/bin/env python3
"""e-DEVLET "<Belediye> Vefat Bilgisi Sorgulama" okuyucusu (14.10.2026, site sahibi: "e-Devlette maden buldum").
Kaynak: turkiye.gov.tr/<belediye>-vefat-sorgulama (girişsiz, CAPTCHA'sız olanlar). robots.txt: "User-agent: *  Allow: /" (kural yok).
Akış (hizmet başına): 1 GET (form + token, çerez) + 3 POST (bugün, dün, evvelsi gün; site yalnız bu 3 günü tutar, eski tarih boş döner).
  Token aynı oturumda tekrar kullanılabilir (14.10 doğrulandı). İstekler arası ≥3,5 sn. Kısa kopmalarda (IncompleteRead / bağlantı kapandı) en çok 1 tekrar.
  Hizmet CAPTCHA (captcha_name alanı), giriş ya da 404 ise BIRAKILIR (dolanma yok).
Alınan alanlar: ad soyad, vefat tarihi (= sorgulanan gün), yaş (sayıysa), ilçe (hizmet tek ilçeninse).
  H66 (15.10.2026, site sahibi: "doğru ve tahminsiz olanı uygula"): il geneli İZMİR ve İSTANBUL hizmetlerinde ("Detay" sayfası) YALNIZ "Mezarlık Bilgisi" okunur: İzmir'de
  "Mezarlık İl/İlçe + Mezarlık Adı" (resmî alan -> ilçe), İstanbul'da mezarlık adı (ilçe okuyucu/veri/mezarlik_resmi.json'daki İBB listesiyle ortak.py'de bağlanır).
  ALINMAYAN: ölüm sebebi (sağlık verisi), baba adı, doğum tarihi, cenazeyle ilgilenen kişi, cami (cami ilçesi gömü ilçesi olmayabilir), T.C. kimlik, adres, telefon.
  Detay istekleri ISTEK_TAVANI'na SAYILIR (DETAY_TAVANI / DETAY_HIZMET_TAVANI ile ayrıca sınırlı; bugünün kayıtları önce; çözülmüş kayıt bir daha okunmaz).
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
ISTEK_TAVANI = int(os.environ.get("EDEVLET_ISTEK_TAVANI", "120"))   # 16.10.2026: 25 ilce hizmetine hic sira gelmiyordu (80 doluyordu)             # kosu basina toplam istek tavani
KOSU_SAATLERI = os.environ.get("EDEVLET_KOSU_SAATLERI", "")                  # "06,18": yalniz bu TR saatlerinde kosar (bos: her zaman)
SURE_DK = int(os.environ.get("EDEVLET_SURE_DK", "70"))   # 16.10.2026: e-Devlet adimi en cok 70 dk; kalan hizmetler sonraki tura (donusumlu)
BASLANGIC = time.time()
DETAY_TAVANI = int(os.environ.get("EDEVLET_DETAY_TAVANI", "45"))              # H66: koşu başına toplam "Detay" isteği
DETAY_HIZMET_TAVANI = int(os.environ.get("EDEVLET_DETAY_HIZMET_TAVANI", "30"))  # H66: hizmet başına "Detay" isteği
DETAY_HIZMETLERI = {"izmir-buyuksehir-belediyesi-vefat-sorgulama", "istanbul-buyuksehir-belediyesi-vefat-sorgulama"}
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
    r = satirlar_idx(g)
    return None if r is None else [(a, y) for a, y, _ in r]


def satirlar_idx(g):
    """Sonuç tablosu -> [(ad, yas_metni, detay_indeksi | None)] (H66: 'İşlem' sütunundaki '?islem=detay&index=N' bağlantısı)."""
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
            m_i = re.search(r"islem=detay(?:&amp;|&)index=(\d+)", tr)
            cikti.append((hucre[i_ad], hucre[i_yas], int(m_i.group(1)) if m_i else None))
    return cikti


def detay_ayikla(g):
    """'Vefat Detay Bilgileri' sayfası -> {'ad': Adı Soyadı, 'mezarlik_il', 'mezarlik_ilce', 'mezarlik_ad'} (yalnız bu alanlar; yoksa None).
    İzmir: 'Mezarlık İl/İlçe :İZMİR / BUCA Mezarlık Adı: BUCA ZAFER MEZARLIĞI Ada: Mezar No:'; İstanbul: düz ad ('KOCASİNAN') ya da '-'.
    Cami bilgisi, baba adı, ölüm sebebi, cenazeyle ilgilenen kişi OKUNMAZ (ayrıştırıcı bunları hiç döndürmez)."""
    cift = {}
    for dt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", g, re.S):
        k = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", dt))).strip()
        if k in ("Adı Soyadı", "Mezarlık Bilgisi"):
            cift[k] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", dd))).strip()
    if "Mezarlık Bilgisi" not in cift:
        return None
    mb, out = cift["Mezarlık Bilgisi"], {"ad": cift.get("Adı Soyadı"), "mezarlik_il": None, "mezarlik_ilce": None, "mezarlik_ad": None}
    m = re.search(r"Mezarlık\s+İl/İlçe\s*:\s*(.*?)\s*Mezarlık\s+Adı\s*:\s*(.*?)\s*(?:Ada\s*:|Mezar\s+No\s*:|$)", mb)
    if m:
        il_ilce = [x.strip() for x in m.group(1).split("/")]
        out["mezarlik_il"] = il_ilce[0] or None
        out["mezarlik_ilce"] = il_ilce[1] if len(il_ilce) > 1 and il_ilce[1] else None
        out["mezarlik_ad"] = m.group(2).strip() or None
    elif mb and mb != "-" and "İl/İlçe" not in mb:
        out["mezarlik_ad"] = mb
    return out


def detay_uygula(r, d, hizmet_il, bugun):
    """Detay sonucunu (detay_ayikla çıktısı) kayda işler -> ilçe bulundu mu. Kayıt adı ile detay adı birebir (normalize) uyuşmuyorsa HİÇBİR ŞEY yazılmaz.
    İlçe yalnız 'Mezarlık İl/İlçe' resmî alanından: aynı ilin geçerli ilçesi ise ilce, başka ilin adıysa il_disi_defin; aksi halde yazılmaz (tahmin yok)."""
    ham = r.setdefault("ham", {})
    ham["detay_tarih"] = bugun
    ham["detay_deneme"] = ham.get("detay_deneme", 0) + 1
    if not d or kat(d.get("ad")) != kat(r.get("ad_soyad")):
        return False
    if d.get("mezarlik_ad"):
        r["defin_yeri"] = ortak.tr_title(d["mezarlik_ad"])
    il_k, m_il, m_ilce = kat(hizmet_il), kat(d.get("mezarlik_il")), d.get("mezarlik_ilce")
    if m_il and m_ilce and m_il != il_k and m_il in IL_ADI:
        r["il_disi_defin"] = {"il": IL_ADI[m_il], "ilce": ortak.tr_title(m_ilce)}
        r["ilce_belirsiz"] = False
        ham["detay_mezarlik_ilce"] = m_ilce
        return True
    if (m_il in ("", il_k)) and m_ilce:
        ilce_adi = ILCE_ADI[il_k].get(kat(m_ilce))
        if ilce_adi:
            r["ilce"], r["ilce_belirsiz"], r["ilce_kaynagi"] = ilce_adi, False, "edevlet_detay"
            ham["ilce_kaynagi"] = "edevlet_detay"
            ham["detay_mezarlik_ilce"] = m_ilce
            return True
    return False


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


def detay_gerekli(r, bugun):
    """Çözülmemiş (ilçe/il dışı yok) ve bugün okunmamış, en çok 2 kez denenmiş kayıt."""
    ham = r.get("ham") or {}
    return not r.get("ilce") and not r.get("il_disi_defin") and ham.get("detay_tarih") != bugun and ham.get("detay_deneme", 0) < 2


def hizmet_oku(slug, il, ilce, gunler, alindi, durum, onceki=None, detay_butce=0):
    """-> ([kayıt..], not). Her hizmet: 1 GET + len(gunler) POST (+ H66: il geneli İzmir/İstanbul için en çok detay_butce 'Detay' GET).
    onceki: {kayıt id: kayıt} (_ulusal.json'dan; çözülmüş detay bilgisi taşınır, tekrar okunmaz)."""
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
    onceki = onceki or {}
    detay_kalan = detay_butce if slug in DETAY_HIZMETLERI else 0
    detay_oku = detay_cozulen = 0
    detay_yenile = False
    bugun_s = bugun_tr().isoformat()
    for gun in gunler:
        if detay_yenile:                                               # detay okumalarından sonra form belirteci yenilenir (1 GET)
            try:
                _, sf = al_tekrarli(o, url)
                tk = re.search(r'name="token" value="([^"]*)"', govde_blok(sf))
                if tk:
                    tok = tk
            except Exception:
                pass
            detay_yenile = False
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
        satir = satirlar_idx(g2)
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
        for ad_ham, yas_s, d_idx in satir:
            ad = temiz_ad(ad_ham)
            if not ad:
                continue
            sira[ad] = sira.get(ad, 0) + 1
            r, slug_il = kayit(slug, il, ilce, kurum, ad, yas_s, gun.isoformat(), alindi, sira[ad])
            eski = onceki.get(r["id"])
            if eski:                                                    # önceki koşuda okunan detay bilgisi korunur
                for a in ("ilce", "ilce_belirsiz", "ilce_kaynagi", "defin_yeri", "il_disi_defin"):
                    if eski.get(a) not in (None, "") and not r.get(a):
                        r[a] = eski[a]
                r["ham"].update({a: v for a, v in (eski.get("ham") or {}).items() if a.startswith("detay") or a == "ilce_kaynagi"})
                if r.get("ilce") or r.get("il_disi_defin"):
                    r["ilce_belirsiz"] = False
            if d_idx is not None and detay_kalan > 0 and detay_gerekli(r, bugun_s):
                detay_kalan -= 1
                detay_oku += 1
                detay_yenile = True
                try:
                    _, sd = al_tekrarli(o, f"{url}?islem=detay&index={d_idx}", None, post)
                    gd = govde_blok(sd)
                    if "captcha_name" in gd:
                        detay_kalan = 0                                # CAPTCHA: detay okuma durur (dolanma yok); liste kayıtları yine de döner
                        gd = ""
                    detay_uygula(r, detay_ayikla(gd) if gd else None, il, bugun_s)
                    if r.get("defin_yeri") and not r.get("ilce") and not r.get("il_disi_defin"):
                        ortak.ilce_isle(r, IL_ADI[kat(il)])             # İstanbul: mezarlık adı -> İBB resmî listesi (birebir ad)
                    if r.get("ilce") or r.get("il_disi_defin"):
                        detay_cozulen += 1
                except Exception:
                    pass
            out.append((r, slug_il))
            n += 1
        sayilar[t_tr] = n
    durum["son_istek"] = o.istek_sayisi
    durum["detay"] = {"okunan": detay_oku, "ilce_bulunan": detay_cozulen}
    return out, sayilar


def il_yaz(slug_il, recs, bugun, alindi):
    """veri/<il>/_ulusal.json'a e-Devlet kayitlarini birlestirir (7 gun). Dosya yolunu dondurur."""
    sinir = (bugun - timedelta(days=7)).isoformat()
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
    return yol


def anlik_yayin(slug_il, yol):
    """16.10.2026 (sahibi: "topladigi verileri direkt uygulamaya aktar"): hizmet okunur okunmaz il dosyasini depoya (veri-tr/<il>/_ulusal.json)
    yazar ve bosalt.yml'yi tetikler -> ~3 dk icinde uygulamada. Yalniz GH_TOKEN + GITHUB_REPOSITORY varsa (Mac runner); hata turu durdurmaz."""
    tok, repo = os.environ.get("GH_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not tok or not repo or os.environ.get("EDEVLET_ANLIK", "1") != "1":
        return
    import base64
    api = f"https://api.github.com/repos/{repo}"
    h = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json", "User-Agent": "kc-edevlet"}
    def cagri(url, method="GET", govde=None):
        rq = urllib.request.Request(url, method=method, headers=h, data=json.dumps(govde).encode() if govde is not None else None)
        with urllib.request.urlopen(rq, timeout=30) as r:
            b = r.read()
            return json.loads(b) if b else {}
    hedef = f"veri-tr/{slug_il}/_ulusal.json"
    for deneme in range(3):
        try:
            sha = None
            try:
                sha = cagri(f"{api}/contents/{hedef}?ref=main").get("sha")
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise
            govde = {"message": f"e-Devlet anlik: {slug_il}", "branch": "main",
                     "content": base64.b64encode(open(yol, "rb").read()).decode()}
            if sha:
                govde["sha"] = sha
            cagri(f"{api}/contents/{hedef}", "PUT", govde)
            cagri(f"{api}/actions/workflows/bosalt.yml/dispatches", "POST", {"ref": "main"})
            print(f"  anlik yayin: {hedef} yazildi, bosalt tetiklendi", file=sys.stderr)
            return
        except Exception as e:
            print(f"  anlik yayin denemesi {deneme + 1}: {str(e)[:80]}", file=sys.stderr)
            time.sleep(5)


def main():
    kuru = "--kuru" in sys.argv
    secili = sys.argv[sys.argv.index("--hizmet") + 1].split(",") if "--hizmet" in sys.argv else None
    if not ortak.robots_izin(TABAN + "x"):
        print("robots.txt turkiye.gov.tr'yi yasaklıyor: durdu", file=sys.stderr)
        return
    bugun = bugun_tr()
    gun_n = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else GUN_SAYISI      # --gun N: yalnız bugün..(N-1) gün önce (doğrulama komutu için --gun 1)
    gunler = [bugun - timedelta(days=i) for i in range(gun_n)]
    alindi = ortak.simdi_iso()
    durum_yol = os.path.join(VERI, "_edevlet_durum.json")
    durum = {}
    try:
        onceki = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        onceki = {}
    # ilçe hizmetleri önce, il geneli sonra
    # 14.10.2026 #13 dersi: alfabetik sira 60 istegi 0 donen ilce hizmetlerine harcadi (Istanbul/Izmir/Trabzon'a sira gelmedi).
    # ONCELIK: bilinen verimli hizmetler once; son 3 kosuda 0/captcha donen hizmet 7 gunde bir denenir (haftalik yeniden kontrol).
    # 16.10.2026 (sahibi: "bize verilen bilgiyi al, yerlestir"): ILCEYI HAZIR VEREN ilce belediyesi hizmetleri ONCE (Istanbul 13, Ankara Mamak,
    # Kocaeli/Bursa/Tekirdag/Samsun/Corum/Kayseri ilceleri); IBB/Izmir il geneli sonra (ayni kisi ilceli kayitla zaten varsa il geneli kopyasi eklenmez).
    # 16.10.2026 aksam DUZELTME: ilce hizmetleri ONE alininca (10 dk aralikla 25 hizmet = 4+ saat) IBB/Izmir sona kaldi ve tur 200 dk
    # sinirina dayandi. Yeni sira: IBB + Izmir BSB (en buyuk hacim) ONCE; sonra ILCE hizmetleri EN UZUN SURE OKUNMAMIS olan once
    # (donusumlu: her tur farkli ilceler; gunde 8 tur); sonra diger il geneli hizmetleri. Tur suresi EDEVLET_SURE_DK (70) ile sinirli.
    def _son_okuma(s_):
        return (onceki.get(s_) or {}).get("zaman") or ""
    ONCELIK = ["istanbul-buyuksehir-belediyesi-vefat-sorgulama", "izmir-buyuksehir-belediyesi-vefat-sorgulama"] + \
        sorted([s_ for s_, (il_, ic_) in HIZMETLER.items() if ic_], key=_son_okuma) + ["izmir-buyuksehir-belediyesi-vefat-sorgulama", "istanbul-buyuksehir-belediyesi-vefat-sorgulama", "trabzon-buyuksehir-belediyesi-vefat-sorgulama",
               "denizli-buyuksehir-belediyesi-vefat-sorgulama", "kocaeli-buyuksehir-belediyesi-vefat-sorgulama", "konya-buyuksehir-belediyesi-vefat-sorgulama",
               "kahramanmaras-buyuksehir-belediyesi-vefat-sorgulama", "tekirdag-buyuksehir-belediyesi-vefat-sorgulama", "diyarbakir-buyuksehir-belediyesi-vefat-sorgulama-v3",
               "erzurum-buyuksehir-belediyesi-vefat-sorgulama-v3", "pendik-belediyesi-vefat-sorgulama", "gebze-belediyesi-vefat-sorgulama", "bagcilar-belediyesi-vefat-sorgulama",
               "inegol-belediyesi-vefat-sorgulama", "mamak-belediyesi-vefat-sorgulama-v3", "korfez-belediyesi-vefat-sorgulama", "bafra-belediyesi-vefat-sorgulama"]
    # 15.10.2026 BOSLUK TURU: EDEVLET_ONCELIK (virgullu slug) verilirse yukaridaki ONCELIK yerine o kullanilir;
    # EDEVLET_YALNIZ=1 ise yalniz o liste gezilir (liste bos ise hic istek atilmaz). Nazik kullanim kurallari (aralik, tavan, captcha, haftalik atlama) AYNEN.
    yalniz_liste = None
    if "EDEVLET_ONCELIK" in os.environ:
        ONCELIK = [x.strip() for x in os.environ["EDEVLET_ONCELIK"].split(",") if x.strip()]
        if os.environ.get("EDEVLET_YALNIZ") == "1":
            yalniz_liste = set(ONCELIK)
            if not yalniz_liste:
                print("e-Devlet: EDEVLET_YALNIZ=1 ve oncelik listesi bos, istek yok", file=sys.stderr)
                return
    def _oncelik(kv):
        return (ONCELIK.index(kv[0]) if kv[0] in ONCELIK else 100 + (kv[1][1] is None), kv[0])
    sira = sorted(HIZMETLER.items(), key=_oncelik)
    def _haftalik_atla(slug):
        o = onceki.get(slug) or {}
        bos = o.get("bos_kosu", 0)
        z = o.get("zaman")
        if bos >= 3 and z:
            try:
                return (datetime.now(timezone.utc) - datetime.fromisoformat(z)).total_seconds() < 7 * 86400
            except Exception:
                return False
        return False
    toplam = {}
    # 15.10.2026 H64: saat kapisi yalniz EDEVLET_ZORLA=1 ile gecilir (bosluk turu, elle 'zorla' girdisi). GITHUB_EVENT_NAME'e bakilmaz:
    # sunucu zamanlayicisi (kc_tetikleyici) her kosuyu workflow_dispatch ile actigindan eski kosul kapiyi her kosuda kaldiriyordu (12:41 kosusu 200 dk zaman asimi).
    if KOSU_SAATLERI and not secili and not kuru and os.environ.get("EDEVLET_ZORLA") != "1":
        saat = (datetime.now(timezone.utc) + timedelta(hours=3)).strftime("%H")
        if saat not in [x.strip() for x in KOSU_SAATLERI.split(",")]:
            print(f"e-Devlet: kosu saati degil (TR {saat}; izinli {KOSU_SAATLERI}), istek yok", file=sys.stderr)
            return
    ara = 0 if (kuru or secili) else HIZMET_ARASI_SN
    toplam_istek = 0
    detay_toplam = 0
    gorulen_kisi = set()                                               # (il, ad_norm, tarih): ilçeli kayıt varken il geneli kopyasını ekleme
    yeni = {}
    for slug, (il, ilce) in sira:
        if secili and slug not in secili:
            continue
        if yalniz_liste is not None and slug not in yalniz_liste:
            continue
        o = onceki.get(slug) or {}
        if o.get("durum") == "captcha" and o.get("zaman") and (datetime.now(timezone.utc) - datetime.fromisoformat(o["zaman"])).total_seconds() < CAPTCHA_BEKLEME_SA * 3600:
            print(f"  {slug}: captcha beklemesi ({CAPTCHA_BEKLEME_SA} sa), istek yok", file=sys.stderr)
            continue
        if _haftalik_atla(slug):
            durum[slug] = dict(onceki.get(slug) or {}, **{"not": "haftalik atlama (3 bos kosu)"})
            continue
        if SURE_DK and time.time() - BASLANGIC > SURE_DK * 60:
            print(f"  {slug}: tur suresi ({SURE_DK} dk) doldu, sonraki tura", file=sys.stderr)
            continue
        if toplam_istek >= ISTEK_TAVANI:
            print(f"  {slug}: kosu istek tavani ({ISTEK_TAVANI}) doldu, sonraki kosuya", file=sys.stderr)
            continue
        if ara and toplam_istek:
            time.sleep(ara)                                                # nazik kullanim: hizmetler arasi bekleme
        onceki_kayit = {}
        if slug in DETAY_HIZMETLERI:
            try:
                for x in json.load(open(os.path.join(VERI, IL_SLUG[kat(il)], "_ulusal.json"), encoding="utf-8")).get("kayitlar", []):
                    onceki_kayit[x["id"]] = x
            except Exception:
                pass
        # H66: detay bütçesi = koşu/hizmet tavanı ile ISTEK_TAVANI'nda kalan (sonraki en çok 8 hizmetin 4'er isteği ayrılır) arasındaki en küçük
        kalan_hizmet = [s2 for s2, _ in sira[sira.index((slug, (il, ilce))) + 1:] if not secili or s2 in secili][:8]
        detay_butce = max(0, min(DETAY_HIZMET_TAVANI, DETAY_TAVANI - detay_toplam, ISTEK_TAVANI - toplam_istek - 4 - 4 * len(kalan_hizmet)))
        dd = {}
        sonuc, sayilar = hizmet_oku(slug, il, ilce, gunler, alindi, dd, onceki_kayit, detay_butce)
        toplam_istek += max(4, dd.get("son_istek", 4))
        detay_toplam += (dd.get("detay") or {}).get("okunan", 0)
        if dd.get("detay", {}).get("okunan"):
            print(f"  {slug}: detay {dd['detay']['okunan']} okundu, {dd['detay']['ilce_bulunan']} ilçe bulundu, istek {dd.get('son_istek')}", file=sys.stderr)
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
        calisir = any(isinstance(v, int) and v > 0 for v in sayilar.values())
        durum[slug] = {"durum": "calisir" if calisir else "bos", "gunler": sayilar, "eklenen": eklenen, "zaman": alindi,
                       "bos_kosu": 0 if calisir else (onceki.get(slug) or {}).get("bos_kosu", 0) + 1}
        toplam[slug] = eklenen
        if eklenen and not kuru:
            for slug_il_ in {si for _, si in sonuc}:
                anlik_yayin(slug_il_, il_yaz(slug_il_, yeni.get(slug_il_, []), bugun, alindi))
        print(f"  {slug}: {sayilar} -> {eklenen} kayıt", file=sys.stderr)
    if kuru:
        print(f"[kuru] {sum(toplam.values())} kayıt, {len(yeni)} il")
        return
    for slug_il, recs in yeni.items():
        il_yaz(slug_il, recs, bugun, alindi)
    try:
        eski_d = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        eski_d = {}
    eski_d.update(durum)
    ortak.json_yaz(durum_yol, eski_d)
    print(f"e-Devlet: {sum(toplam.values())} kayıt, {len(yeni)} il, hizmet durumu: " + ", ".join(f"{k.split('-belediyesi')[0]}={v}" for k, v in sorted(toplam.items())))


if __name__ == "__main__":
    main()
