#!/usr/bin/env python3
"""KAYIT DEFTERİ OKUYUCUSU (15.10.2026, site sahibi kararı: ajan kod yazmaz, yalnız deftere satır ekler; düzenek işaretli yerleri gezer).
Defter: okuyucu/kaynaklar/bolge-*.json (şema: kaynaklar/SEMA.md). `_` ile başlayan dosyalar atlanır.
Kalıplar: rss / sitemap -> ortak_haber.haber_kaynagi (oh.site ile aynı parametreler); liste / tablo -> sade vefat listesi ayrıştırıcısı
(ad, cami+vakit, mezarlık, tarih; yalnız olgu, cümle yok, alanlar <= 60 karakter).
Kurallar: robots 'yasak' ya da canlı robots.txt izin vermiyorsa satır atlanır (ob.al her istekte bakar); siklik_dk uygulanır
(son okuma veri/_defter_durum.json); bozuk satır uyarıyla atlanır, tur düşmez; Facebook/Instagram/WhatsApp vb. satırlar reddedilir.
Çıktı: veri/<il>/_ulusal.json (sondakika.py ile aynı dosya/şema; ulusal_birlestir.py son7gun'a katar), kaynak_turu = defterdeki tur.
Kullanım: python3 okuyucu/kayitli_kaynak.py [--defter DOSYA] [--il agri] [--kuru] [--istek N] [--sure-sn 600] [--yer github|mac]
  --kuru: dosya yazmaz (geçici klasör), varsayılan istek tavanı 5.
  --yer mac (16.10.2026): yalnız `calistir: mac` ya da GitHub turunda ENGEL (robots.txt 403 / HTTP 401-403-429) alıp `_mac_gerekli.json`'a
  işaretlenen satırlar okunur; sahibinin Mac runner'ı (topla-tr.yml) çalıştırır, çıktı veri/<il>/_ulusal.json -> veri-tr/. Mac'ten de engel gelirse
  satır yine bırakılır (engel dolanılmaz). GitHub turu (varsayılan) bu satırları 7 gün atlar, sonra bir kez yeniden dener.
  --ulusal-katla KLASOR: KLASOR/<il>/_ulusal.json kayıtlarını veri/<il>/_ulusal.json'a id'ye göre katar (topla.yml: veri-tr kopyası sonrası)."""
import glob, json, os, re, sys, tempfile, time, urllib.parse
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh

VERI = os.path.join(DIZIN, "..", "veri")
KAYNAKLAR = os.path.join(DIZIN, "kaynaklar")
DURUM_DOSYASI = "_defter_durum.json"
MAC_DOSYASI = os.path.join(KAYNAKLAR, "_mac_gerekli.json")   # depoda tutulur (Mac checkout'ta okur); GitHub turu yazar
MAC_GITHUB_ATLAMA_GUN = 7        # işaretli satırı GitHub bu kadar gün atlar, sonra bir kez yeniden dener (engel kalktıysa geri döner)
MAC_OKUMA_GUN = 14               # Mac işareti bu kadar gün geçerli sayar (GitHub yeniden yoklarken boşluk olmasın)
MAC_SAKLAMA_GUN = 30
YERLER = ("github", "mac")

TURLER = ("belediye", "muftuluk", "yerel_basin", "ulusal")
KALIPLAR = ("rss", "sitemap", "liste", "tablo")
YASAK_ALAN = ("facebook.com", "fb.com", "fb.watch", "instagram.com", "whatsapp.com", "wa.me", "t.me", "telegram.org",
              "twitter.com", "x.com", "tiktok.com", "youtube.com", "youtu.be")
ISTEK_ARALIGI_TOLERANS_DK = 5      # saatlik tur birkaç dk kayabilir: 60 dk'lık satır bir tur atlanmasın


def _host(url):
    h = urllib.parse.urlparse(url or "").netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


def _yasak_alan_mi(url):
    h = _host(url)
    return any(h == y or h.endswith("." + y) for y in YASAK_ALAN)


def il_adlari():
    """okuyucu/ilceler.json -> {il_slug: il adı} (Ağrı -> agri)."""
    return {ortak.il_slug(k): k for k in ortak.ilce_verisi() if not k.startswith("_")}


# ---------------------------------------------------------------- şema doğrulama
def dogrula(s, iller=None):
    """Bir defter satırını doğrular. Dönen: (temiz_satir | None, [nedenler]). Bozuk satır None döner (tur sürer)."""
    iller = iller if iller is not None else il_adlari()
    if not isinstance(s, dict):
        return None, ["satır bir nesne değil"]
    n = []
    il = s.get("il")
    if il not in iller:
        n.append(f"il tanınmıyor: {il!r}")
    for a in ("ad", "url"):
        if not str(s.get(a) or "").strip():
            n.append(f"eksik alan: {a}")
    if s.get("tur") not in TURLER:
        n.append(f"tur geçersiz: {s.get('tur')!r}")
    kalip = s.get("kalip")
    if kalip not in KALIPLAR:
        n.append(f"kalip geçersiz: {kalip!r}")
    elif kalip == "rss" and not s.get("rss_url"):
        n.append("kalip rss ama rss_url yok")
    elif kalip == "sitemap" and not s.get("sitemap"):
        n.append("kalip sitemap ama sitemap yok")
    elif kalip in ("liste", "tablo") and not s.get("liste_url"):
        n.append(f"kalip {kalip} ama liste_url yok")
    if s.get("robots", "izin") not in ("izin", "yasak"):
        n.append(f"robots geçersiz: {s.get('robots')!r}")
    if s.get("calistir", "github") not in YERLER:
        n.append(f"calistir geçersiz: {s.get('calistir')!r}")
    kanit = s.get("kanit")
    if not isinstance(kanit, list) or len([x for x in kanit if str(x).strip()]) < 2:
        n.append("kanit en az 2 tarihli başlık olmalı")
    sk = s.get("siklik_dk", 60)
    if not isinstance(sk, int) or isinstance(sk, bool) or sk < 15:
        n.append("siklik_dk >= 15 tam sayı olmalı")
    ana = _host(s.get("url"))
    for a in ("url", "rss_url", "sitemap", "liste_url"):
        v = s.get(a)
        if not v:
            continue
        p = urllib.parse.urlparse(v)
        if p.scheme not in ("http", "https") or not p.netloc:
            n.append(f"{a} geçersiz adres")
        elif _yasak_alan_mi(v):
            n.append(f"yasak alan adı ({a}): {_host(v)}")
        elif ana and _host(v) != ana:
            n.append(f"{a} farklı alan adında ({_host(v)} != {ana})")
    if n:
        return None, n
    t = dict(s)
    t.setdefault("robots", "izin")
    t.setdefault("calistir", "github")
    t["siklik_dk"] = sk
    t["takma"] = [x for x in (s.get("takma") or []) if isinstance(x, str)]
    t["kesin_yerel"] = bool(s.get("kesin_yerel"))
    return t, []


def defter_oku(dosyalar=None, iller=None, uyar=None):
    """Defter dosyalarını okur; geçerli satırlar listesi (aynı alan adı ikinci kez gelirse atlanır). Bozuk dosya/satır uyarıyla geçilir."""
    uyar = uyar or (lambda m: print("UYARI:", m, file=sys.stderr))
    if dosyalar is None:
        dosyalar = sorted(f for f in glob.glob(os.path.join(KAYNAKLAR, "bolge-*.json")) if not os.path.basename(f).startswith("_"))
    cikti, gorulen = [], set()
    for yol in dosyalar:
        try:
            with open(yol, encoding="utf-8") as f:
                veri = json.load(f)
            if not isinstance(veri, list):
                raise ValueError("kök bir dizi değil")
        except Exception as e:
            uyar(f"{os.path.basename(yol)} okunamadı: {e}")
            continue
        for i, s in enumerate(veri):
            t, neden = dogrula(s, iller)
            if t is None:
                uyar(f"{os.path.basename(yol)}[{i}] atlandı: {'; '.join(neden)}")
                continue
            h = _host(t["url"])
            if h in gorulen:
                uyar(f"{os.path.basename(yol)}[{i}] atlandı: alan adı iki satırda ({h})")
                continue
            gorulen.add(h)
            t["_dosya"] = os.path.basename(yol)
            cikti.append(t)
    return cikti


# ---------------------------------------------------------------- sıklık / durum
def satir_anahtari(s):
    return f"{s['il']}|{_host(s['url'])}"


def durum_yukle(veri_kok):
    try:
        with open(os.path.join(veri_kok, DURUM_DOSYASI), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("son", {})
    return d


def durum_kaydet(veri_kok, d):
    sinir = (datetime.now() - timedelta(days=30)).isoformat(timespec="seconds")
    d["son"] = {k: v for k, v in d["son"].items() if v >= sinir}     # bir ay okunmayan satırın izi silinir
    ortak.json_yaz(os.path.join(veri_kok, DURUM_DOSYASI), d)


def _gun_farki(tarih, simdi):
    try:
        return (simdi.date() - date.fromisoformat(str(tarih)[:10])).days
    except ValueError:
        return 9999


def mac_gerekli_yukle(durum, dosya=None):
    """Mac'e devredilen satırlar: depodaki _mac_gerekli.json + veri/_defter_durum.json['mac_gerekli'] birleşimi ({satır_anahtarı: {tarih, neden, ad}}).
    Aynı anahtarda daha yeni tarih kazanır. Dosya yoksa/bozuksa yalnız durum kullanılır."""
    out = {}
    kaynaklar = [durum.get("mac_gerekli") or {}]
    try:
        with open(dosya or MAC_DOSYASI, encoding="utf-8") as f:
            kaynaklar.append(json.load(f).get("satirlar") or {})
    except Exception:
        pass
    for k_ in kaynaklar:
        for k, v in k_.items():
            if isinstance(v, dict) and v.get("tarih") and v["tarih"] >= (out.get(k, {}).get("tarih") or ""):
                out[k] = v
    return out


def mac_dosyasi_yaz(mac, dosya=None, simdi=None):
    """GitHub turu: işaretleri depo dosyasına yazar (üst düzey zaman damgası YOK: içerik değişmedikçe commit çıkmaz). 30 günden eski işaret silinir."""
    simdi = simdi or datetime.now()
    mac = {k: v for k, v in mac.items() if _gun_farki(v.get("tarih"), simdi) <= MAC_SAKLAMA_GUN}
    yol = dosya or MAC_DOSYASI
    yeni = json.dumps({"aciklama": "GitHub veri merkezi IP'sine engel veren (robots.txt 403 / HTTP 401-403-429) kayıt defteri satırları; Mac runner okur "
                                   "(kayitli_kaynak.py --yer mac). Otomatik yazılır, elle düzenlenmez.", "satirlar": dict(sorted(mac.items()))},
                      ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    try:
        if open(yol, encoding="utf-8").read() == yeni:
            return mac
    except OSError:
        pass
    with open(yol, "w", encoding="utf-8") as f:
        f.write(yeni)
    return mac


def atlama_nedeni(s, durum, simdi=None, yer="github", mac=None):
    """Satır bu turda okunmayacaksa nedeni (str), okunacaksa None. robots 'yasak' -> atla; siklik_dk dolmadıysa -> atla.
    yer='github': `calistir: mac` ya da 7 günden yeni Mac işareti -> 'mac'e devredildi'. yer='mac': yalnız `calistir: mac` ∪ 14 günden yeni işaretliler okunur."""
    if s.get("robots") == "yasak":
        return "robots yasak (deftere göre)"
    simdi = simdi or datetime.now()
    anahtar = satir_anahtari(s)
    isaret = (mac or {}).get(anahtar)
    if yer == "mac":
        if s.get("calistir") != "mac" and not (isaret and _gun_farki(isaret.get("tarih"), simdi) <= MAC_OKUMA_GUN):
            return "mac turunda değil (GitHub okur)"
    else:
        if s.get("calistir") == "mac":
            return "mac'e devredildi (deftere göre calistir=mac)"
        if isaret and _gun_farki(isaret.get("tarih"), simdi) <= MAC_GITHUB_ATLAMA_GUN:
            return f"mac'e devredildi ({isaret.get('neden', 'engel')}, {isaret.get('tarih')})"
    son = durum.get("son", {}).get(anahtar)
    if son:
        try:
            gecen = (simdi - datetime.fromisoformat(son)).total_seconds() / 60
        except ValueError:
            return None
        if gecen < s["siklik_dk"] - ISTEK_ARALIGI_TOLERANS_DK:
            return f"siklik_dk dolmadı ({int(gecen)}/{s['siklik_dk']} dk)"
    return None


def engel_sinifi(ctx, s, e):
    """oi.Engel hangi türden? 'robots-403' (robots.txt'e erişim engeli) | 'http-403' (401/403/429 sayfa) -> Mac'e devredilebilir (veri merkezi IP'si engeli).
    None -> robots.txt gerçekten yasaklıyor (200 + Disallow): site kendi kuralıyla yasakladı, Mac'e de devredilmez."""
    host = _host(s["url"])
    for h, r in (ob.durum(ctx).d.get("robots") or {}).items():
        if ob.site_anahtari(h) == host and r.get("yasak"):
            return "robots-403"
    m = re.search(r"HTTP (40[13]|429)", str(e))
    return f"http-{m.group(1)}" if m else None


# ---------------------------------------------------------------- rss / sitemap -> oh.site
def ay_ac(url, simdi=None):
    """Defter adresindeki aylık yer tutucuları açar: {AY} -> YYYY-MM, {YYYY} -> yıl, {MM} -> ay (iki hane). Yer tutucu yoksa aynen döner."""
    d = simdi or date.today()
    return (url or "").replace("{AY}", d.strftime("%Y-%m")).replace("{YYYY}", d.strftime("%Y")).replace("{MM}", d.strftime("%m"))


def site_tanimi(s):
    """Defter satırı -> oh.site(...) (yeni okuma kodu yok; parametreler eşlenir). sitemap kalıbında RSS yoksa dizin = sitemap (aylık {AY} açılır)."""
    slug = "defter-" + _host(s["url"]).replace(".", "-")
    if s["kalip"] == "sitemap":
        dizin = s.get("rss_url") or ay_ac(s["sitemap"])
    else:
        dizin = s["rss_url"]
    ek = ay_ac(s.get("sitemap"))
    if ek and ek == dizin:
        ek = None                              # dizin zaten bu sitemap: ek_dizin aynı adresi ikinci kez 'RSS'te var' sayıp adayları eler
    return oh.site(s["ad"], slug, dizin, kesin_yerel=s["kesin_yerel"], ilce=s.get("ilce"), takma=tuple(s["takma"]), ek_dizin=ek or None, makale_ac=1)


def rss_oku(ctx, il_adi, s):
    """rss / sitemap satırı: oh.haber_kaynagi ile okur; sitemap kalıbında ayrıca vefat bölümü / derleme sayfaları açılır (aday_sayfalar)."""
    t = site_tanimi(s)
    kayitlar = oh.haber_kaynagi(ctx, il_adi, t["slug"], t["ad"], t["dizin"], url_suzgec=t["url_suzgec"], makale_ac=t["makale_ac"],
                                varsayilan_ilce=t["ilce"], takma=t["takma"] + ((t["ilce"],) if t["ilce"] else ()),
                                kesin_yerel=t["kesin_yerel"], ek_dizin=t["ek_dizin"])
    # günlük derleme / vefat bölümü sayfaları: sitemap kalıbında 3, RSS kalıbında 2 sayfa (kaynak başına istek disiplini ~5)
    kayitlar = list(kayitlar) + aday_sayfalar(ctx, il_adi, s, t["dizin"], azami=3 if s["kalip"] == "sitemap" and not s.get("rss_url") else 2)
    return kayitlar


# ---------------------------------------------------------------- sitemap/RSS'teki vefat bölümü ve günlük derleme sayfaları
# Tek kişilik: '/vefat/<id>/<ad>' (başlık yalnız ad olabilir). Derleme: 'Çanakkale Vefat İlanları: 15 Ekim 2026' (gövdede 'AD vefat etmiştir' blokları).
TEKIL_YOL = re.compile(r"/vefat/\d+", re.I)
DERLEME_YOL = re.compile(r"vefat-ilanlari|vefat-ilani|cenaze-ilanlari|cenaze-ilani|vefatlar|vefat-edenler|hemsehrilerimiz", re.I)
TARIHLI_VEFAT_YOL = re.compile(r"/vefatlar?/\d{1,2}/\d{1,2}/20\d\d/", re.I)      # Aydın Denge: /vefatlar/11/10/2026/<ad>-vefat-etti
GOVDE_KAPLARI = (r'id="makale"[^>]*>', r'(?:itemprop|property)="articleBody"[^>]*>', r'class="[^"]*detaymetin[^"]*"[^>]*>', r'class="[^"]*metin-alan[^"]*"[^>]*>',
                 r'class="[^"]*news-content[^"]*"[^>]*>', r'class="[^"]*entry-content[^"]*"[^>]*>', r'class="[^"]*liste-cart[^"]*"[^>]*>')
GOVDE_SONU = re.compile(r"news-tags|</article>|etiketler|paylas-alan|EDİTÖR|YORUMLAR|İlginizi Çekebilir")


EK_SLUG = re.compile(r"vefat-olum|olum-defin|vefat-listesi|cenaze-listesi|kimler-vefat|aci-gunu|aci-kayip|aci-haber|son-yolculuga|son-yolculuk|aramizdan-ayrildi|vefat-haberi|rahmetine-kavustu|hakkin-rahmetine|cenaze-programi")


def aday_mi(url):
    """Adres vefat bölümü, günlük derleme ya da tek kişilik vefat haberi gibi mi? (oh.SLUG_VEFAT: 'vefat-etti', 'topraga-verildi'...)"""
    return bool(TEKIL_YOL.search(url) or DERLEME_YOL.search(url) or TARIHLI_VEFAT_YOL.search(url) or oh.SLUG_VEFAT.search(url) or EK_SLUG.search(url))


GOVDE_ISARET = re.compile(r"vefat\s+et|hayatını\s+kayb|toprağa|defn|doğumlu|mezarl|cenaze|ölüm tarihi|defin yeri|rahmet", re.I)


def govde_metni(sayfa):
    """Sayfa gövdesi düz metin. Adaylar: galeri alt yazıları (Haber Dairesi), bilinen gövde kapları (satır yapısı korunur), <article>, JSON-LD articleBody
    (yapısı düz). Sitelerin işaretlemesi farklı olduğundan (kap bazen bir meta etiketi ya da menü çıkar) en çok cenaze/vefat ipucu içeren aday seçilir;
    eşitlikte sıradaki ilk aday. Kaplarda bölümün sonu 'EDİTÖR / YORUMLAR / etiketler' ile kesilir."""
    adaylar = []
    parcalar = re.findall(r'<div class="text-content">([\s\S]*?)</div>', sayfa)
    if len(parcalar) >= 3:
        adaylar.append(ob.satirlara("\n".join(parcalar)))
    ld = ob.makale_govdesi(sayfa)
    if ld:
        adaylar.append(ld)
    for kap in GOVDE_KAPLARI + (r"<article[^>]*>",):
        for m in list(re.finditer(kap, sayfa))[:3]:
            parca = GOVDE_SONU.split(sayfa[m.end():m.end() + 14000])[0]
            t = re.sub(r"<[^>]*$", "", ob.satirlara(re.sub(r"<(?:img|source|meta|link)[^>]*>", " ", parca)))
            if len(t) > 40:
                adaylar.append(t)
    if not adaylar:
        return ""
    return max(adaylar, key=lambda t: (len(GOVDE_ISARET.findall(t)), -len(t)))      # en çok ipucu; eşitlikte en kısa (menü/yan haber başlıkları şişirmez)


def sayfa_gunu(sayfa, url):
    """datePublished (JSON-LD ya da meta) -> gün; yoksa adres sonundaki tarih."""
    m = re.search(r'datePublished"?\s*(?::|content=)\s*"(\d{4}-\d{2}-\d{2})', sayfa)
    return m.group(1) if m else adres_tarihi(url)


ETIKET = re.compile(r"^(Doğum Tarihi|Ölüm Tarihi|Mezarlık|Cami|Vakit|Cenaze Yeri|Defin Yeri|Yer\s*[–-]\s*Vakit|Doğum Yeri\s*/\s*Yılı|Baba\s*/\s*Ana Adı|Taziye Adresi)\s*:\s*(.*)$", re.I)
ETIKETLI_BLOK = re.compile(r"(?m)^(?:Ölüm Tarihi|Defin Yeri|Cenaze Yeri|Yer\s*[–-]\s*Vakit)\s*:", re.I)
# Baba/Ana adı, taziye adresi ve doğum yeri okunur ama HİÇBİR alana yazılmaz (kişisel veri; K filtreleri)


AD_DESENI = r"(?<![\wçğıöşü’'])((?:[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşüâîû’']+ ){1,3}[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşüâîû’']+)"
CUMLE_BASLANGIC = re.compile(
    AD_DESENI + r"(?:,\s*(?P<d1>\d{1,2} [A-Za-zçğıöşüÇĞİÖŞÜ]+ \d{4})(?: [A-ZÇĞİÖŞÜ][\wçğıöşü]+)? doğumlu\.\s*"
    r"|\s*\.\s*(?P<d2>\d{4})(?: [A-ZÇĞİÖŞÜ][\wçğıöşü]+)* doğumlu\.\s*"
    r"|\s*\((?P<y>\d{1,3})\):\s*"
    r"|:\s+(?=[A-ZÇĞİÖŞÜ][^.]*?(?:namaz|defn|toprağa)))")
CAMI_DESENI = re.compile(r"((?:\(?[A-ZÇĞİÖŞÜ][\wçğıöşü’']*\)? ){1,4}Cami[i]?)\b")
MEZAR_DESENI = re.compile(r"((?:[A-ZÇĞİÖŞÜ][\wçğıöşü’']+ ){0,3}Mezarlı[ğk]ı)")
VAKIT_DESENI = re.compile(r"(sabah|öğle|ikindi|akşam|yatsı|cuma)\s+namaz", re.I)


def tail_alanlari(tail):
    """Cenaze cümlesi -> (namaz_yeri_vakti, defin_yeri): 'Hacı Veyis Camii, öğle namazı' / 'Karaaslan Mezarlığı'. Yalnız olgu; cümle taşınmaz."""
    c = CAMI_DESENI.search(tail)
    v = VAKIT_DESENI.search(tail)
    mz = MEZAR_DESENI.search(tail)
    cami = c.group(1).strip() if c else None
    cami = re.sub(r"^(?:Öğle|İkindi|Sabah|Akşam|Yatsı|Cuma|Namazı|Sonrası)\s+", "", cami) if cami else None
    vakit = f"{ortak.tr_lower(v.group(1))} namazı" if v else None
    namaz = f"{cami}, {vakit}" if cami and vakit else (cami or vakit)
    return _temiz_alan(namaz), _temiz_alan(mz.group(1)) if mz else None


def cumle_listesi_ayristir(govde, ctx, il_adi, s, url, gun):
    """Adı cümle başında olan derlemeler: 'Ad, 21 Kasım 1937 doğumlu. …toprağa verildi.' (Konya Hakimiyet), 'Ad. 1944 Karabayır doğumlu. …'
    (Haber Dairesi), 'Ad: …Mezarlığı'nda defnedildi.' (Konya'nın Sesi), 'Ad (34): …Camii'nden kaldırılacaktır.' (İl Gazetesi). Yaş doğumdan; yoksa parantezden."""
    g = re.sub(r"\.(?=[A-ZÇĞİÖŞÜ])", ". ", govde.replace("\n", " "))
    ms = list(CUMLE_BASLANGIC.finditer(g))
    if len(ms) < 1:
        return []
    sonuc, gorulen = [], set()
    for i, m in enumerate(ms):
        ad, _ = ad_ayikla(m.group(1))
        if not ad or ortak.katla(ad) in gorulen:
            continue
        tail = g[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(g)][:400]
        namaz, mezar = tail_alanlari(tail)
        if not (namaz or mezar):
            continue                                       # cenaze bilgisi olmayan eşleşme (cümle içi büyük harfli sözcükler)
        gorulen.add(ortak.katla(ad))
        yas = None
        if m.group("d1"):
            yas = oi.yas_hesapla(oi.tarih(m.group("d1")) or "", gun)
        elif m.group("d2"):
            yas = int(gun[:4]) - int(m.group("d2"))
        elif m.group("y"):
            yas = int(m.group("y"))
        k = _kayit_yap(ctx, il_adi, s, ad, yas if yas and 0 < yas < 125 else None, gun, "defin", None, None, mezar, s.get("ilce"), url)
        k["namaz_yeri_vakti"] = namaz
        sonuc.append(k)
    return sonuc


ILCE_BASLIK = re.compile(r"^(.+?)['’](?:da|de|ta|te)\s+(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+([A-Za-zçğıöşüÇĞİÖŞÜ]+)\s+(\d{4})\s+Vefat Edenler", re.I)
KISI_BASLIK = re.compile(r"^(.+?)\s+[–-]\s+(.+)$")


def baslikli_ilan_ayristir(govde, ctx, il_adi, s, url, gun):
    """İlçe ilçe derleme (NNC Haber): "Kızılcahamam'da 13 Ekim 2026 Vefat Edenler" başlığı ilçe ve günü verir; "Ad Soyad – Mahalle" satırı kişiyi başlatır;
    altındaki paragrafın akraba/yakınlık cümleleri ATILIR, yalnız cami/vakit, mezarlık ve (varsa) yaş alınır."""
    sat = [x.strip() for x in govde.split("\n") if x.strip()]
    ilce, bgun, kisi, sonuc = None, gun, None, []

    def bitir():
        if kisi is None:
            return
        namaz, mezar = tail_alanlari(" ".join(kisi["metin"]))
        if not (namaz or mezar) or not _tarih_penceresi_icinde(bgun):
            return
        ym = re.search(r"\((\d{1,3})\)|(\d{1,3}) yaşında", " ".join(kisi["metin"]))
        yas = int(ym.group(1) or ym.group(2)) if ym else None
        mah = kisi["mahalle"] if re.search(r"(?i)mahalle|mah\.|köy", kisi["mahalle"]) else None
        k = _kayit_yap(ctx, il_adi, s, kisi["ad"], yas if yas and 0 < yas < 125 else None, bgun, "defin", None, None, mezar, ilce or s.get("ilce"), url)
        k["namaz_yeri_vakti"] = namaz
        k["mahalle"] = _temiz_alan(ortak.tr_title(mah)) if mah else None
        sonuc.append(k)

    for x in sat:
        m = ILCE_BASLIK.match(x)
        if m:
            bitir()
            kisi = None
            ilce = _resmi_ilce(il_adi, m.group(1).split()[-1]) or _resmi_ilce(il_adi, m.group(1))
            bgun = oi.tarih(f"{m.group(2)} {m.group(3)} {m.group(4)}") or gun
            continue
        km = KISI_BASLIK.match(x)
        if km and len(x) < 90:
            ad, _ = ad_ayikla(km.group(1))
            if ad:
                bitir()
                kisi = {"ad": ad, "mahalle": km.group(2), "metin": []}
                continue
        if kisi is not None:
            kisi["metin"].append(x)
    bitir()
    return sonuc


def ayracli_satir_ayristir(govde, ctx, il_adi, s, url, gun):
    """'Ad Soyad - Mezarlık - Cami' satırları (Hunat TV: 'Fati Fakir - Anbar Mez. - Org.Hulusi Akar Camii'); parça sırası serbest, anahtar sözcüğe bakılır."""
    sonuc = []
    for satir_ in re.split(r"\n|şu şekilde:", govde):
        parcalar = [p_.strip() for p_ in re.split(r"\s+[-–]\s+", satir_) if p_.strip()]
        if len(parcalar) < 3:
            continue
        ad, yas = ad_ayikla(parcalar[0])
        cami = next((p_ for p_ in parcalar[1:] if re.search(r"cami|camii|camisi|cemevi|musalla", p_, re.I)), None)
        mezar = next((p_ for p_ in parcalar[1:] if re.search(r"mez\b|mezar|kabristan", p_, re.I)), None)
        if not ad or not (cami or mezar):
            continue
        k = _kayit_yap(ctx, il_adi, s, ad, yas, gun, "defin", None, None, _temiz_alan(mezar), s.get("ilce"), url)
        k["namaz_yeri_vakti"] = _temiz_alan(cami)
        sonuc.append(k)
    return sonuc


def isimli_paragraf_ayristir(govde, ctx, il_adi, s, url, gun):
    """Ad satırı + 'NN yaşında hayatını kaybeden …' paragrafı + 'Cenaze yeri (ve vakti) …' / 'Defin yeri|işlemi …' cümleleri (Gündem Sivas)."""
    sat = [x.strip() for x in govde.split("\n") if x.strip()]
    sonuc = []
    for i, x in enumerate(sat[:-1]):
        ad, _ = ad_ayikla(x)
        ym = re.match(r"(\d{1,3}) yaşında hayatını kaybeden", sat[i + 1])
        if not (ad and ym):
            continue
        blok = " ".join(sat[i + 2:i + 6])
        cm = re.search(r"Cenaze yeri(?: ve vakti)?\s+(.+?)(?:,\s*saat\s*([\d.:]+))?\s+olarak", blok)
        mz = re.search(r"Defin (?:yeri|işlemi)\s+([^.]*?Mezarlığı)", blok)
        namaz = None
        if cm:
            saat = cm.group(2).replace(".", ":") if cm.group(2) else None
            namaz = _temiz_alan(f"{cm.group(1)}, {saat}" if saat else cm.group(1))
        k = _kayit_yap(ctx, il_adi, s, ad, int(ym.group(1)), gun, "defin", None, None, _temiz_alan(mz.group(1)) if mz else None, s.get("ilce"), url)
        k["namaz_yeri_vakti"] = namaz
        sonuc.append(k)
    return sonuc


ETIKET_ADLARI = r"Baba\s*/\s*Ana Adı|Doğum Yeri\s*/\s*Yılı|Doğum Tarihi|Ölüm Tarihi|Cenaze Yeri|Defin Yeri|Taziye Adresi|Yer\s*[–-]\s*Vakit|Mezarlık|Cami|Vakit"


def etiket_ayir(govde):
    """JSON-LD gövdesinde satır sonları düşmüşse ('…diliyoruz.FATİ FAKİRBaba / Ana Adı: …Cenaze Yeri: …Vakit: ÖĞLE…') BİTİŞİK duran etiketlerin önüne
    satır sonu koyar ve etiketten hemen önce yapışık BÜYÜK HARFLİ adı kendi satırına alır. Etiketler zaten ayrıysa (boşluk/satır sonu) metin değişmez."""
    glued = r"(?<=\S)(?=(?:" + ETIKET_ADLARI + r")\s*:)"
    if not re.search(glued, govde):
        return govde
    t = re.sub(glued, "\n", govde)
    return re.sub(r"([.!?])([A-ZÇĞİÖŞÜ]{2,}(?: [A-ZÇĞİÖŞÜ]{2,}){1,3})\n(?=Baba|Doğum|Ölüm|Cenaze|Defin|Yer )", r"\1\n\2\n", t)


def _dolu(blok):
    """Blokta ad dışında en az bir etiketli değer var mı?"""
    return any(k not in ("ad", "_yas", "yer") for k in blok)


def etiketli_blok_ayristir(govde, ctx, il_adi, s, url, gun):
    """Etiketli vefat blokları (Sakarya Yenihaber 'Sakarya'da vefatlar'): 'AD' satırı, [İLÇE - MAHALLE], Doğum/Ölüm Tarihi, Mezarlık, Cami, Vakit.
    Gün = sayfanın günü (cenaze günü). İlçe: 'İLÇE - MAHALLE' satırı, yoksa cami adının ilk sözcüğü resmî ilçeyse; tahmin yok."""
    bloklar, cur = [], None
    for satir_ in govde.split("\n"):
        satir_ = satir_.strip()
        m = ETIKET.match(satir_)
        if m:
            if cur is not None:
                cur[ortak.katla(m.group(1))] = m.group(2).strip()
            continue
        if cur is not None and _dolu(cur):
            bloklar.append(cur)
            cur = None
        if cur is not None and not _dolu(cur) and "yer" not in cur and " - " in satir_:      # 'ARİFİYE - NEVİYE' (ilçe - mahalle) ad satırından hemen sonra
            cur["yer"] = satir_
            continue
        ad, yas = ad_ayikla(satir_)
        if ad:
            cur = {"ad": ad, "_yas": yas}
        elif cur is not None and not _dolu(cur) and len(satir_) > 40:
            cur = None
    if cur is not None and _dolu(cur):
        bloklar.append(cur)
    sonuc = []
    for b in bloklar:
        olum = oi.tarih(b.get("olum tarihi", ""))
        dogum = oi.tarih(b.get("dogum tarihi", ""))
        yas = oi.yas_hesapla(dogum, olum) if dogum and olum else b.get("_yas")
        yer_vakit = b.get("yer vakit", "")
        saat = (_SAAT.search(yer_vakit) or _SAAT.search(b.get("vakit", "")))
        cami_ham = b.get("cami") or b.get("cenaze yeri") or re.split(r"\s*[–-]\s*Saat\s*:", yer_vakit)[0]
        cami = re.split(r"(?i)\bmah\.?\s*", cami_ham)[-1].strip() or cami_ham
        cami = okunur_yap(cami)
        ilce = None
        if b.get("yer"):
            ilce = _resmi_ilce(il_adi, b["yer"].split(" - ")[0])
        ilce = ilce or _resmi_ilce(il_adi, cami_ham.split()[0] if cami_ham else "") or s.get("ilce")
        vakit = (b.get("vakit") or "").strip()
        if saat and not (vakit and not _SAAT.search(vakit)):
            zaman = f"{int(saat.group(1)):02d}:{saat.group(2)}"
        else:
            zaman = f"{ortak.tr_lower(vakit)} namazı" if vakit else ""
        namaz = _temiz_alan(f"{cami}, {zaman}" if cami and zaman else cami)
        mezar = re.sub(r"\s*\([^)]*\)", "", b.get("mezarlik") or b.get("defin yeri") or "").strip()
        k = _kayit_yap(ctx, il_adi, s, b["ad"], yas if yas and 0 < yas < 125 else None, gun, "defin", None, None,
                       _temiz_alan(mezar), ilce, url)
        k["namaz_yeri_vakti"] = namaz
        k["vefat_tarihi"] = olum
        sonuc.append(k)
    return sonuc


def aday_sayfa_oku(ctx, il_adi, s, url, sayfa):
    """Açılmış tek sayfa -> kayıtlar. Önce tek kişilik (başlık vefat kalıbında ya da /vefat/<id>) olgular; olmazsa derleme gibi okunur:
    etiketli bloklar, yoksa ob.serbest_kayitlar (Mardin/Siirt biçimi: 'AD vefat etmiştir. Cenazesi ...')."""
    gun = sayfa_gunu(sayfa, url)
    if not _tarih_penceresi_icinde(gun):
        return []
    slug = "defter-" + _host(s["url"]).replace(".", "-")
    govde = govde_metni(sayfa)
    h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", sayfa)
    baslik = oi.metin(h1.group(1)) if h1 else ""
    tekil = bool(TEKIL_YOL.search(url))
    govde = etiket_ayir(govde)
    if ETIKETLI_BLOK.search(govde):
        return etiketli_blok_ayristir(govde, ctx, il_adi, s, url, gun)
    if tekil or (oh.vefat_haberi_mi(baslik) and not DERLEME_YOL.search(url)):
        if tekil and not oh.vefat_haberi_mi(baslik):
            baslik = (baslik + " vefat etti").strip()
        f = oh.olgular(il_adi, baslik, govde[:900], gun)
        if f:
            if not f["ilce"] and s.get("ilce"):
                f["ilce"] = s["ilce"]
            return [oh.kayit_yap(ctx, il_adi, slug, s["ad"], url, f, gun)]
        if tekil:
            return []
    for ayristir in (baslikli_ilan_ayristir, cumle_listesi_ayristir, isimli_paragraf_ayristir, ayracli_satir_ayristir):
        k = ayristir(govde, ctx, il_adi, s, url, gun)
        if k:
            return k
    govde = re.sub(r"(?i)\n(?=(?:vefat|hakk|rahmet))", " ", re.sub(r"<[^>]*$", "", govde))     # 'AD' ve 'vefat etmiştir.' ayrı satırdaysa birleşsin
    govde = re.sub(r"(?i)hayatını\s+kaybet(?:ti|miştir)|yaşamını\s+yitir\w*", "vefat etti", govde)    # ayrıştırıcı yalnız 'vefat' kalıbını tanır (yalnız ayrıştırma metni; olgular değişmez)
    return ob.serbest_kayitlar(ctx, il_adi, slug, s["ad"], url, gun, govde, varsayilan_ilce=s.get("ilce"))


DERLEME_BASLIK = re.compile(r"vefat\s+eden|kimler\s+vefat|aramızdan\s+ayrılan|cenaze\s+ilan|defin\s+bilgi|vefat\s+haberleri|vefat\s+ilan|vefat\s+etti\?|cenaze\s+bilgi", re.I)


def aday_baglantilar(metin_, taban, s, gl=None, il_adi=None):
    """RSS/sitemap XML'inden ya da liste sayfası HTML'inden aday adresler: {url: (gün|'', bölüm)}. Aynı site; adresi aday_mi() ya da (RSS'te)
    başlığı günlük derleme kalıbında olanlar (DERLEME_BASLIK: 'Konya'da bugün vefat edenler', 'Aramızdan Ayrılanlar'). Çok-illi sitede başlıkta
    başka il/ilçe adı geçenler elenir (oh.yerel_mi). Adres/RSS tarihi biliniyorsa pencere içinde olmalı (bilinmiyorsa sayfa açılınca datePublished'a bakılır).
    bölüm 0 = vefat bölümü/derleme, 1 = tek haber."""
    gl = set(gl or oi.gunler())
    ham = {}
    if "<loc>" in metin_ or "<item" in metin_ or "<entry" in metin_:
        for o in oh.rss_ogeleri(metin_):
            baslik_derleme = (not o["slug"]) and bool(DERLEME_BASLIK.search(o["baslik"] or ""))
            if baslik_derleme and il_adi and oh.yerel_mi(il_adi, o["baslik"], "", tuple(s.get("takma") or ()), bool(s.get("kesin_yerel"))) is False:
                continue
            ham[o["url"]] = (o["tarih"] or adres_tarihi(o["url"]) or "", baslik_derleme or bool(TEKIL_YOL.search(o["url"]) or DERLEME_YOL.search(o["url"]) or TARIHLI_VEFAT_YOL.search(o["url"])), baslik_derleme or aday_mi(o["url"]))
    else:
        kendi, baska = oh._yer_sozleri(il_adi, tuple(s.get("takma") or ())) if il_adi else (set(), set())
        for h in re.findall(r'href="([^"#]+)"', metin_):
            u = urllib.parse.urljoin(taban, h.strip())
            ilk = ortak.katla(urllib.parse.urlparse(u).path.strip("/").split("/")[0].split("-")[0])      # çok-illi sitede adres 'afyonkarahisar-…', 'bucak-vefat-…'
            if ilk in baska and ilk not in kendi:
                continue
            ham.setdefault(u, (adres_tarihi(u) or "", bool(TEKIL_YOL.search(u) or DERLEME_YOL.search(u) or TARIHLI_VEFAT_YOL.search(u)), aday_mi(u)))
    return {u: (g, 0 if b else 1) for u, (g, b, ok) in ham.items()
            if ok and _host(u) == _host(s["url"]) and u.rstrip("/") != taban.rstrip("/") and urllib.parse.urlparse(u).path.rstrip("/") != urllib.parse.urlparse(taban).path.rstrip("/")
            and not (urllib.parse.urlparse(u).path.strip("/").count("/") == 0 and u.rstrip("/").endswith(("vefatlar", "vefatlarimiz")))
            and (not g or g in gl)}


def _kimlik(u):
    m = re.findall(r"\d{4,}", u)
    return int(m[-1]) if m else 0


def adaylari_ac(ctx, il_adi, s, adaylar, azami=3):
    """Aday sayfaların pencere içindeki en yenilerini açar (okunmamış önce; okunmuş sayfa 4 saat dolmadan yeniden açılmaz)."""
    okunan = ob.durum(ctx).d["okunan"]
    # aynı günde vefat bölümü sayfaları genel haberlerden önce; tarihsizlerde yenilik için kimlik sırası
    sira = sorted(adaylar.items(), key=lambda x: (x[0] in okunan, [-ord(c) for c in x[1][0]] or [0], x[1][1] if x[1][0] else 0, -_kimlik(x[0])))
    sonuc, n = [], 0
    for u, (g, _b) in sira:
        if n >= azami:
            break
        if not ob.okunacak_mi(ctx, u, g):
            continue
        try:
            sayfa = ob.al(ctx, u)
        except (ob.ButceDoldu, oi.Engel):
            break
        except Exception as e:
            print(f"  sayfa açılamadı: {u}: {e}", file=sys.stderr)
            continue
        n += 1
        sonuc.extend(aday_sayfa_oku(ctx, il_adi, s, u, sayfa))
        ob.okundu(ctx, u)
    ob.durum(ctx).kaydet()
    return sonuc


def aday_sayfalar(ctx, il_adi, s, dizin_url, azami=3):
    """sitemap/RSS dizininden (6 saat önbellek, haber_kaynagi ile aynı adres) vefat adaylarını açar."""
    xml = oh.onbellekli_dizin(ctx, dizin_url)
    return adaylari_ac(ctx, il_adi, s, aday_baglantilar(xml, dizin_url, s, ctx["gunler"], il_adi), azami) if xml else []


# ---------------------------------------------------------------- liste / tablo ayrıştırıcısı
_CUMLE = re.compile(r"vefat\s+et|başsağlığı|rahmet|taziye|cennet|fatiha|hakk['’]?[ıi]n", re.I)
_ADRES = re.compile(r"\b(?:apartman\w*|apt\.|daire\s*\d|kat\s*:\s*\d|no\s*[:.]?\s*\d+\s*/\s*\d+|no\s*:\s*\d+|kapı\s+no|posta\s+kodu)\b", re.I)
_TEL = re.compile(r"\d{3}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")
_CAMI = re.compile(r"cami|camii|cemevi|musalla", re.I)
_MEZAR = re.compile(r"mezarl|kabristan|şehitli", re.I)
_YAS = re.compile(r"(\d{1,3})\s+yaşında(?:ki)?|\((\d{1,3})\)")
_SAAT = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b")

AD_KOLON = ("ad soyad", "adi soyadi", "vefat eden", "merhum", "isim", "ad")
CAMI_KOLON = ("cenaze yeri", "namaz yeri", "yer vakit", "cami", "namaz")
MEZAR_KOLON = ("mezarlik", "defin yeri", "kabristan", "defin")
SAAT_KOLON = ("namaz vakti", "saat")
TARIH_KOLON = ("defin tarihi", "cenaze tarihi", "namaz tarihi", "tarih")


def okunur_yap(v):
    """BÜYÜK HARFLİ değeri okunur biçime çevirir ('ORG.HULUSİ AKAR CAMİİ' -> 'Org.Hulusi Akar Camii'); karışık harfli değere dokunmaz."""
    return re.sub(r"[^\s.]+", lambda m: ortak.tr_title(m.group(0)), v) if v and v.isupper() else v


def _temiz_alan(v, kisa=60):
    """Tek alan değeri -> <= 60 karakter olgu; site cümlesi, telefon, adres içeren değer atılır (None)."""
    v = oi.metin(v or "")
    v = okunur_yap(v)                          # BÜYÜK HARFLİ kaynak değeri ('ANBAR MEZ.') okunur biçime
    if not v or _CUMLE.search(v) or _TEL.search(v) or _ADRES.search(v):
        return None
    return ob.kisa(v, kisa)


def ad_ayikla(ham):
    """'AHMET YILMAZ (65)' -> ('Ahmet Yılmaz', 65). 2-4 sözcük, rakam/bağlantı yok; aksi halde (None, None)."""
    ham = oi.metin(ham or "")
    ym = _YAS.search(ham)
    yas = int(ym.group(1) or ym.group(2)) if ym else None
    ad = _YAS.sub(" ", ham)
    ad = re.sub(r"\s+", " ", ad).strip(" ,;:-–")
    if not ad or re.search(r"[\d!@()\[\]]|https?:|www\.|\.com|\.tr\b", ad, re.I):
        return None, None
    sozler = ad.split()
    if not 2 <= len(sozler) <= 4 or any(not re.fullmatch(r"[A-Za-zÇĞİÖŞÜÂÎÛçğıöşüâîû.'’-]+", w) for w in sozler):
        return None, None
    return ortak.tr_title(" ".join(sozler)), (yas if yas and 0 < yas < 125 else None)


def _kayit_yap(ctx, il_adi, s, ad, yas, gun, tarih_turu, cami, saat, mezar, ilce, url):
    slug = "defter-" + _host(s["url"]).replace(".", "-")
    namaz = None
    if cami:
        namaz = ob.kisa(f"{cami}, {saat}" if saat else cami, 60)
    k = oi.kayit(il_adi, ilce, slug, ad, gun, s["ad"], url, ctx["alindi"], ek_id="", liste_tarihi=gun, yas=yas,
                 namaz_tarihi=gun if tarih_turu == "defin" else None, namaz_yeri_vakti=namaz, defin_yeri=mezar,
                 vefat_tarihi=gun if tarih_turu == "vefat" else None,
                 ham={"sayfa_tarihi": gun, "tarih_kaynagi": "metin"})
    k["kaynak_turu"] = s["tur"]
    if not ilce:
        k["ilce"], k["ilce_belirsiz"] = None, True
    return k


def _tarih_penceresi_icinde(gun):
    """Gün son 7 gün, yarın ya da öbür gün mü? (yarının ilanı anında yayında, 15.10.2026; eski arşiv satırları alınmaz)"""
    if not gun:
        return False
    bugun = date.today()
    return (bugun - timedelta(days=6)).isoformat() <= gun <= (bugun + timedelta(days=2)).isoformat()


def tablo_ayristir(sayfa, ctx, il_adi, s):
    """HTML tablolarından vefat kayıtları: başlık satırında ad sütunu bulunan her tablo okunur. Tarihsiz satır alınmaz."""
    sonuc, tarihsiz = [], 0
    for ham in re.findall(r"<table[\s\S]*?</table>", sayfa):
        satirlar = re.findall(r"<tr[\s\S]*?</tr>", ham)
        if len(satirlar) < 2:
            continue
        baslik = [ortak.katla(x) for x in oi.hucreler(satirlar[0])]
        if not any(any(a == b or a in b for a in AD_KOLON[:-1]) or b == "ad" for b in baslik):
            continue
        for tr in satirlar[1:]:
            h = oi.hucreler(re.sub(r'<span[^>]*hidden[^>]*>[\s\S]*?</span>', "", tr))     # mobil görünüm etiketleri ('Adı Soyadı :') hücre metnine karışmasın
            ad_ham = oi.kolon(baslik, h, *AD_KOLON)
            ad, yas = ad_ayikla(ad_ham)
            if not ad:
                continue
            yas = yas or next((int(x) for x in [oi.kolon(baslik, h, "yas", "yasi")] if x.isdigit() and 0 < int(x) < 125), None)
            tarih_hucre = oi.kolon(baslik, h, "defin tarihi", "cenaze tarihi", "namaz tarihi")
            tarih_turu = "defin"
            if not oi.tarih(tarih_hucre):
                tarih_hucre, tarih_turu = oi.kolon(baslik, h, "vefat tarihi", "tarih"), "vefat"
            gun = oi.tarih(tarih_hucre)
            if not _tarih_penceresi_icinde(gun):
                tarihsiz += 0 if gun else 1
                continue
            saat_h = oi.kolon(baslik, h, *SAAT_KOLON)
            sm = _SAAT.search(saat_h or "") or _SAAT.search(oi.kolon(baslik, h, *CAMI_KOLON) or "")
            saat = f"{int(sm.group(1)):02d}:{sm.group(2)}" if sm else None
            cami = _temiz_alan(_SAAT.sub("", oi.kolon(baslik, h, *CAMI_KOLON)).strip(" ,-–"))
            mezar = _temiz_alan(oi.kolon(baslik, h, *MEZAR_KOLON))
            ilce = ortak.ilce_coz(il_adi, oi.kolon(baslik, h, "ilce")) if oi.kolon(baslik, h, "ilce") else None
            ilce = ilce if isinstance(ilce, str) else None
            sonuc.append(_kayit_yap(ctx, il_adi, s, ad, yas, gun, tarih_turu, cami, saat, mezar, ilce or s.get("ilce"), s["liste_url"]))
    if tarihsiz:
        print(f"  {s['ad']}: {tarihsiz} tablo satırı tarihsiz olduğu için alınmadı", file=sys.stderr)
    return sonuc


def liste_ayristir(sayfa, ctx, il_adi, s):
    """<li> öğelerinden vefat kayıtları: 'Ad Soyad - Cami - 15.10.2026 - Mezarlık' gibi ayraçlı satırlar. Tarihsiz öğe alınmaz."""
    sonuc, tarihsiz = [], 0
    for li in re.findall(r"<li[\s>][\s\S]*?</li>", sayfa):
        t = oi.metin(li)
        if not 8 <= len(t) <= 240:
            continue
        parcalar = [p.strip() for p in re.split(r"\s[-–—|]\s|\|", t) if p.strip()]
        ad, yas = ad_ayikla(parcalar[0]) if parcalar else (None, None)
        if not ad:
            continue
        gun = oi.tarih(t)
        if not _tarih_penceresi_icinde(gun):
            tarihsiz += 0 if gun else 1
            continue
        cami = next((p for p in parcalar[1:] if _CAMI.search(p)), None)
        mezar = next((p for p in parcalar[1:] if _MEZAR.search(p)), None)
        sm = _SAAT.search(cami or "") or _SAAT.search(t)
        saat = f"{int(sm.group(1)):02d}:{sm.group(2)}" if sm else None
        cami = _temiz_alan(_SAAT.sub("", cami).strip(" ,-–")) if cami else None
        sonuc.append(_kayit_yap(ctx, il_adi, s, ad, yas, gun, "defin", cami, saat, _temiz_alan(mezar), s.get("ilce"), s["liste_url"]))
    if tarihsiz:
        print(f"  {s['ad']}: {tarihsiz} liste öğesi tarihsiz olduğu için alınmadı", file=sys.stderr)
    return sonuc


def _resmi_ilce(il_adi, ad):
    """Metindeki ilçe adı ilin resmî ilçe listesindeyse resmî yazımı, değilse None."""
    k = ortak.katla(ad)
    return next((x for x in ortak.ilce_listesi(il_adi) if ortak.katla(x) == k), None)


def yer_ayir(il_adi, metin_):
    """'ÇÖŞNÜK MH. BATTALGAZİ / MALATYA' -> ('Çöşnük Mahallesi', 'Battalgazi'). Sondaki '/ İL' atılır; kalanın son 1-2 sözcüğü
    resmî ilçe ise ilçe olur, önceki kısım mahalle/köy (rakam içeriyorsa atılır). Tanınmazsa (None, None)."""
    sol = re.split(r"\s*/\s*", oi.metin(metin_ or ""))[0].strip()
    sozler = sol.split()
    for n in (2, 1):
        if len(sozler) >= n:
            ilce = _resmi_ilce(il_adi, " ".join(sozler[-n:]))
            if ilce:
                on = " ".join(sozler[:-n]).strip(" ,-")
                on = re.sub(r"(?i)\b(?:mh|mah)\.?$", "Mahallesi", ortak.tr_title(on)) if on else ""
                on = re.sub(r"\bMh\.?$|\bMah\.?$", "Mahallesi", on)
                return (_temiz_alan(on) if on and not re.search(r"\d", on) else None), ilce
    return None, None


def kart_ayristir(sayfa, ctx, il_adi, s):
    """'vef-card' kartları (Malatya Son Haber /vefat): ad, 'NN yaş', tarih ('14 Ekim 2026'), ilçe rozeti, yer satırı."""
    sonuc = []
    for kart in re.findall(r"<article[^>]*vef-card[\s\S]*?</article>", sayfa):
        ad, yas = ad_ayikla((re.search(r'class="vef-name"[^>]*>([\s\S]*?)<', kart) or [None, ""])[1])
        if not ad:
            continue
        ym = re.search(r"(\d{1,3})\s*yaş", kart)
        yas = yas or (int(ym.group(1)) if ym and 0 < int(ym.group(1)) < 125 else None)
        gun = oi.tarih((re.search(r'class="vef-meta-item"[\s\S]*?</span>\s*([^<]+)', kart) or [None, ""])[1])
        if not _tarih_penceresi_icinde(gun):
            continue
        chip = (re.search(r'class="vef-chip"[^>]*>([^<]+)', kart) or [None, ""])[1]
        yer = (re.search(r'class="vef-place"[\s\S]*?<span>([^<]+)</span>\s*</p>', kart) or [None, ""])[1]
        mahalle, ilce = yer_ayir(il_adi, yer)
        ilce = _resmi_ilce(il_adi, chip.strip()) or ilce or s.get("ilce")
        k = _kayit_yap(ctx, il_adi, s, ad, yas, gun, "vefat", None, None, None, ilce, s["liste_url"])
        k["mahalle"] = mahalle
        sonuc.append(k)
    return sonuc


AYLAR_ASCII = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}


def adres_tarihi(url):
    """Adresteki tarih -> 'YYYY-AA-GG': '/vefatlar/11/10/2026/..' ya da '...-14-ekim-2026..' (sonda kimlik/ek olabilir); yoksa None."""
    yol = ortak.katla(url.split("?")[0]).replace(" ", "-")
    ham = url.split("?")[0].lower()
    try:
        m = re.search(r"/(\d{1,2})/(\d{1,2})/(20\d\d)(?:/|$)", ham)
        if m:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
        m = re.search(r"(?<!\d)(\d{1,2})-([a-z]+)-(20\d\d)", yol) or re.search(r"(?<!\d)(\d{1,2})-([a-z]+)-(20\d\d)", ham)
        ay = AYLAR_ASCII.get(m.group(2)) if m else None
        return date(int(m.group(3)), ay, int(m.group(1))).isoformat() if ay else None
    except ValueError:
        return None


GUNLUK_LINK = re.compile(r'href="([^"]*\d+-kisi-[^"]*vefat[^"]*)"', re.I)
GUNLUK_SATIR = re.compile(r"^(.+?)\s*-\s*YAŞ\s*:?\s*(\d{1,3})\s*-\s*(.+)$", re.I)


def gunluk_haber_ayristir(sayfa, url, ctx, il_adi, s):
    """'Malatya'da bugün N kişi vefat etti' haberinin gövdesi: 'AD- YAŞ:80- MAH. İLÇE/İL' satırları. Gün <time datetime>, yoksa adres/başlık tarihi."""
    gm = re.search(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})', sayfa)
    gun = gm.group(1) if gm else adres_tarihi(url)
    if not _tarih_penceresi_icinde(gun):
        return []
    govde = re.search(r'articleBody[^>]*>([\s\S]*?)</p></div>|articleBody[^>]*>([\s\S]*?)</div>', sayfa)
    govde = (govde.group(1) or govde.group(2)) if govde else ""
    sonuc = []
    for satir_ in re.split(r"<br\s*/?>|</p>|\n", govde):
        m = GUNLUK_SATIR.match(oi.metin(satir_))
        if not m:
            continue
        ad, _ = ad_ayikla(m.group(1))
        if not ad:
            continue
        yas = int(m.group(2))
        mahalle, ilce = yer_ayir(il_adi, m.group(3))
        k = _kayit_yap(ctx, il_adi, s, ad, yas if 0 < yas < 125 else None, gun, "vefat", None, None, None, ilce or s.get("ilce"), url)
        k["mahalle"] = mahalle
        sonuc.append(k)
    return sonuc


def gunluk_haberler(sayfa, ctx, il_adi, s, azami=2):
    """Liste sayfasındaki günlük vefat haberi bağlantılarından pencere içindeki en yeni `azami` tanesini açar (sayfa başına 1-2 istek)."""
    adaylar = {}
    for h in GUNLUK_LINK.findall(sayfa):
        u = urllib.parse.urljoin(s["liste_url"], h)
        gun = adres_tarihi(u)
        if _host(u) == _host(s["url"]) and _tarih_penceresi_icinde(gun):
            adaylar[u] = gun
    sonuc = []
    for u, gun in sorted(adaylar.items(), key=lambda x: x[1], reverse=True)[:azami]:
        if not ob.okunacak_mi(ctx, u, gun):
            continue
        try:
            sonuc.extend(gunluk_haber_ayristir(ob.al(ctx, u), u, ctx, il_adi, s))
        except ob.ButceDoldu:
            break
        ob.okundu(ctx, u)
    return sonuc


def liste_oku(ctx, il_adi, s):
    """liste / tablo satırı: sayfa bütçeli + robots kontrollü açılır (ob.al). Sırayla: kartlar, tablo/li, günlük vefat haberi bağlantıları."""
    sayfa = ob.al(ctx, s["liste_url"])
    kayitlar = kart_ayristir(sayfa, ctx, il_adi, s)
    if not kayitlar and "<table" in sayfa:
        kayitlar = tablo_ayristir(sayfa, ctx, il_adi, s)        # belediye listeleri: kalıp 'liste' yazılsa da tablo varsa önce o (Talas, Melikgazi)
    if not kayitlar and s["kalip"] != "tablo":
        kayitlar = liste_ayristir(sayfa, ctx, il_adi, s)
    if not kayitlar:
        kayitlar = gunluk_haberler(sayfa, ctx, il_adi, s)
    if not kayitlar:      # genel yol: liste/kategori sayfasındaki vefat bağlantıları (Uşak, Afyon, Aydın, '<il>-vefatlar' yazılım ailesi)
        kayitlar = adaylari_ac(ctx, il_adi, s, aday_baglantilar(sayfa, s["liste_url"], s, ctx["gunler"], il_adi))
    ob.durum(ctx).kaydet()
    tek = {}
    for k in kayitlar:                           # aynı sayfada aynı kişi-gün bir kez
        tek.setdefault((ortak.katla(k["ad_soyad"]), k["liste_tarihi"]), k)
    return list(tek.values())


# ---------------------------------------------------------------- tur
def satir_oku(ctx, il_adi, s):
    """Tek defter satırı -> kayıt listesi (kaynak_turu = defterdeki tur)."""
    kayitlar = rss_oku(ctx, il_adi, s) if s["kalip"] in ("rss", "sitemap") else liste_oku(ctx, il_adi, s)
    for k in kayitlar:
        k["kaynak_turu"] = s["tur"]
        k["kaynak_ad"] = s["ad"]
    return kayitlar


def _ulusal_yaz(veri_kok, slug, il_adi, kayitlar, alindi):
    """veri/<il>/_ulusal.json'a id'ye göre birleştirir (sondakika.py ile aynı biçim; 7 günden eski atılır)."""
    yol = os.path.join(veri_kok, slug, "_ulusal.json")
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    try:
        with open(yol, encoding="utf-8") as f:
            eski = json.load(f).get("kayitlar", [])
    except Exception:
        eski = []
    kay = {x["id"]: x for x in eski}
    kay.update({x["id"]: x for x in kayitlar})
    sinir = (date.today() - timedelta(days=7)).isoformat()
    kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
    ortak.json_yaz(yol, {"il": il_adi, "kayitlar": list(kay.values()), "guncelleme": alindi})


def calistir(defter, veri_kok=VERI, kuru=False, sure_sn=600, simdi=None, il_suzgec=None, yer="github", mac_dosya=None):
    """Defterdeki satırları okur. Dönen: özet sözlüğü. Hiçbir satır hatası turu düşürmez.
    yer='github': ENGEL (robots-403/http-403) alan satır Mac'e işaretlenir; yer='mac': yalnız Mac'e devredilenler okunur, işaret yazılmaz."""
    iller = il_adlari()
    durum = durum_yukle(veri_kok)
    mac = mac_gerekli_yukle(durum, mac_dosya)
    mac_degisti = False
    alindi = ortak.simdi_iso()
    bitis = time.time() + sure_sn
    ozet = {"satir": len(defter), "okundu": 0, "atlandi": {}, "hata": {}, "kayit": 0, "il": {}}
    # önce en uzun süredir okunmayan satır (adil dağılım; süre dolarsa sondakiler sonraki tura kalır)
    sirali = sorted(defter, key=lambda s: durum["son"].get(satir_anahtari(s), ""))
    toplanan = {}
    for s in sirali:
        ad = f"{s['il']}/{s['ad']}"
        if il_suzgec and s["il"] != il_suzgec:
            continue
        neden = atlama_nedeni(s, durum, simdi, yer=yer, mac=mac)
        if neden:
            ozet["atlandi"][ad] = neden
            continue
        if time.time() > bitis:
            ozet["atlandi"][ad] = "tur süresi doldu (sonraki tura kalır)"
            continue
        il_adi = iller[s["il"]]
        klasor = tempfile.mkdtemp(prefix="defter-") if kuru else os.path.join(veri_kok, s["il"])
        os.makedirs(klasor, exist_ok=True)
        ctx = {"gunler": oi.gunler(), "alindi": alindi, "klasor": klasor, "il": il_adi}
        try:
            kayitlar = satir_oku(ctx, il_adi, s)
        except oi.Engel as e:
            sinif = engel_sinifi(ctx, s, e) if yer == "github" else None
            if sinif:                           # veri merkezi IP'sine engel: Mac (ev interneti) sitenin kendi kurallarıyla dener; engel DOLANILMAZ
                mac[satir_anahtari(s)] = {"tarih": (simdi or datetime.now()).date().isoformat(), "neden": sinif, "ad": s["ad"]}
                mac_degisti = True
                ozet["atlandi"][ad] = f"ENGEL ({sinif}) -> mac'e devredildi: {e}"
                ozet.setdefault("mac_isaret", []).append(ad)
            else:
                ozet["atlandi"][ad] = f"ENGEL (bırakıldı{', mac de' if yer == 'mac' else ''}): {e}"
            continue
        except ob.ButceDoldu as e:
            ozet["atlandi"][ad] = f"bütçe/istek tavanı: {e}"
            continue
        except Exception as e:
            ozet["hata"][ad] = f"{type(e).__name__}: {e}"
            print(f"UYARI: {ad} okunamadı: {ozet['hata'][ad]}", file=sys.stderr)
            continue
        ozet["okundu"] += 1
        durum["son"][satir_anahtari(s)] = datetime.now().isoformat(timespec="seconds")
        toplanan.setdefault(s["il"], []).extend(kayitlar)
        ozet["il"][s["il"]] = ozet["il"].get(s["il"], 0) + len(kayitlar)
        ozet["kayit"] += len(kayitlar)
        print(f"[{ad}] {len(kayitlar)} kayıt ({s['kalip']})")
    if not kuru:
        for slug, kayitlar in toplanan.items():
            if kayitlar:
                _ulusal_yaz(veri_kok, slug, iller[slug], kayitlar, alindi)
        if yer == "github":
            durum["mac_gerekli"] = mac_dosyasi_yaz(mac, mac_dosya, simdi) if mac_degisti or mac else {}
        durum_kaydet(veri_kok, durum)
    ozet["ornek"] = [{a: k.get(a) for a in ("il", "ilce", "ad_soyad", "yas", "liste_tarihi", "namaz_yeri_vakti", "defin_yeri", "kaynak_turu")}
                     for v in toplanan.values() for k in v][:5]
    return ozet


def ulusal_katla(veri_kok, eski_kok):
    """eski_kok/<il>/_ulusal.json kayıtlarını veri_kok/<il>/_ulusal.json'a id'ye göre katar (aynı id'de veri_kok'taki KAZANIR; 7 günden eskisi atılır).
    topla.yml: veri-tr/ (Mac) kopyası veri/<il>/_ulusal.json'un üstüne yazar; kopyadan önce saklanan GitHub kayıtları buradan geri katılır."""
    n = 0
    if not os.path.isdir(eski_kok):
        return 0
    sinir = (date.today() - timedelta(days=7)).isoformat()
    for il in sorted(os.listdir(eski_kok)):
        try:
            with open(os.path.join(eski_kok, il, "_ulusal.json"), encoding="utf-8") as f:
                eski = json.load(f)
        except Exception:
            continue
        yol = os.path.join(veri_kok, il, "_ulusal.json")
        try:
            with open(yol, encoding="utf-8") as f:
                simdiki = json.load(f)
        except Exception:
            simdiki = {"il": eski.get("il"), "kayitlar": [], "guncelleme": eski.get("guncelleme")}
        kay = {x["id"]: x for x in eski.get("kayitlar", []) if x.get("id")}
        onceki = len(kay)
        kay.update({x["id"]: x for x in simdiki.get("kayitlar", []) if x.get("id")})
        kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
        if len(kay) != len(simdiki.get("kayitlar", [])):
            n += len(kay) - len(simdiki.get("kayitlar", []))
            os.makedirs(os.path.dirname(yol), exist_ok=True)
            ortak.json_yaz(yol, {"il": simdiki.get("il") or eski.get("il"), "kayitlar": list(kay.values()),
                                 "guncelleme": simdiki.get("guncelleme") or eski.get("guncelleme")})
    return n


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    def arg(ad, varsayilan=None):
        return argv[argv.index(ad) + 1] if ad in argv and argv.index(ad) + 1 < len(argv) else varsayilan

    if "--ulusal-katla" in argv:
        n = ulusal_katla(VERI, arg("--ulusal-katla"))
        print(f"ulusal katla: {n} kayıt geri katıldı")
        return 0
    yer = arg("--yer", "github")
    if yer not in YERLER:
        print(f"HATA: --yer {yer!r} geçersiz ({'|'.join(YERLER)})", file=sys.stderr)
        return 2
    kuru = "--kuru" in argv
    dosya = arg("--defter")
    defter = defter_oku([dosya] if dosya else None)
    sayac = {"istek": 0}
    tavan = arg("--istek", "5" if kuru else None)
    if tavan:                                   # istek tavanı: ağ katmanını sayaçla sarar (kuru denemede 5)
        tavan = int(tavan)
        gercek = ob._indir

        def sinirli(url, timeout=40):
            if sayac["istek"] >= tavan:
                raise ob.ButceDoldu(f"--istek {tavan} tavanı doldu")
            sayac["istek"] += 1
            print(f"  GET {url}", file=sys.stderr)
            return gercek(url, timeout)
        ob._indir = sinirli
    ozet = calistir(defter, kuru=kuru, sure_sn=int(arg("--sure-sn", "600")), il_suzgec=arg("--il"), yer=yer)
    ozet["yer"] = yer
    ozet["istek_sayisi"] = sayac["istek"] if tavan else None
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
