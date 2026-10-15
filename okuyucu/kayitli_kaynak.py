#!/usr/bin/env python3
"""KAYIT DEFTERİ OKUYUCUSU (15.10.2026, site sahibi kararı: ajan kod yazmaz, yalnız deftere satır ekler; düzenek işaretli yerleri gezer).
Defter: okuyucu/kaynaklar/bolge-*.json (şema: kaynaklar/SEMA.md). `_` ile başlayan dosyalar atlanır.
Kalıplar: rss / sitemap -> ortak_haber.haber_kaynagi (oh.site ile aynı parametreler); liste / tablo -> sade vefat listesi ayrıştırıcısı
(ad, cami+vakit, mezarlık, tarih; yalnız olgu, cümle yok, alanlar <= 60 karakter).
Kurallar: robots 'yasak' ya da canlı robots.txt izin vermiyorsa satır atlanır (ob.al her istekte bakar); siklik_dk uygulanır
(son okuma veri/_defter_durum.json); bozuk satır uyarıyla atlanır, tur düşmez; Facebook/Instagram/WhatsApp vb. satırlar reddedilir.
Çıktı: veri/<il>/_ulusal.json (sondakika.py ile aynı dosya/şema; ulusal_birlestir.py son7gun'a katar), kaynak_turu = defterdeki tur.
Kullanım: python3 okuyucu/kayitli_kaynak.py [--defter DOSYA] [--il agri] [--kuru] [--istek N] [--sure-sn 600]
  --kuru: dosya yazmaz (geçici klasör), varsayılan istek tavanı 5."""
import glob, json, os, re, sys, tempfile, time, urllib.parse
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh

VERI = os.path.join(DIZIN, "..", "veri")
KAYNAKLAR = os.path.join(DIZIN, "kaynaklar")
DURUM_DOSYASI = "_defter_durum.json"

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


def atlama_nedeni(s, durum, simdi=None):
    """Satır bu turda okunmayacaksa nedeni (str), okunacaksa None. robots 'yasak' -> atla; siklik_dk dolmadıysa -> atla."""
    if s.get("robots") == "yasak":
        return "robots yasak (deftere göre)"
    simdi = simdi or datetime.now()
    son = durum.get("son", {}).get(satir_anahtari(s))
    if son:
        try:
            gecen = (simdi - datetime.fromisoformat(son)).total_seconds() / 60
        except ValueError:
            return None
        if gecen < s["siklik_dk"] - ISTEK_ARALIGI_TOLERANS_DK:
            return f"siklik_dk dolmadı ({int(gecen)}/{s['siklik_dk']} dk)"
    return None


# ---------------------------------------------------------------- rss / sitemap -> oh.site
def site_tanimi(s):
    """Defter satırı -> oh.site(...) (yeni okuma kodu yok; parametreler eşlenir). sitemap kalıbında RSS yoksa dizin = sitemap (aylık {AY} açılır)."""
    slug = "defter-" + _host(s["url"]).replace(".", "-")
    if s["kalip"] == "sitemap":
        dizin = s.get("rss_url") or s["sitemap"].replace("{AY}", date.today().strftime("%Y-%m"))
    else:
        dizin = s["rss_url"]
    return oh.site(s["ad"], slug, dizin, kesin_yerel=s["kesin_yerel"], ilce=s.get("ilce"), takma=tuple(s["takma"]),
                   ek_dizin=s.get("sitemap"))


def rss_oku(ctx, il_adi, s):
    """rss / sitemap satırı: oh.haber_kaynagi ile okur."""
    t = site_tanimi(s)
    return oh.haber_kaynagi(ctx, il_adi, t["slug"], t["ad"], t["dizin"], url_suzgec=t["url_suzgec"], makale_ac=t["makale_ac"],
                            varsayilan_ilce=t["ilce"], takma=t["takma"] + ((t["ilce"],) if t["ilce"] else ()),
                            kesin_yerel=t["kesin_yerel"], ek_dizin=t["ek_dizin"])


# ---------------------------------------------------------------- liste / tablo ayrıştırıcısı
_CUMLE = re.compile(r"vefat\s+et|başsağlığı|rahmet|taziye|cennet|fatiha|hakk['’]?[ıi]n", re.I)
_ADRES = re.compile(r"\b(?:apartman\w*|apt\.|daire\s*\d|kat\s*:\s*\d|no\s*[:.]?\s*\d+\s*/\s*\d+|no\s*:\s*\d+|kapı\s+no|posta\s+kodu)\b", re.I)
_TEL = re.compile(r"\d{3}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")
_CAMI = re.compile(r"cami|camii|cemevi|musalla", re.I)
_MEZAR = re.compile(r"mezarl|kabristan|şehitli", re.I)
_YAS = re.compile(r"(\d{1,3})\s+yaşında(?:ki)?|\((\d{1,3})\)")
_SAAT = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b")

AD_KOLON = ("ad soyad", "adi soyadi", "vefat eden", "merhum", "isim", "ad")
CAMI_KOLON = ("cenaze yeri", "namaz yeri", "cami", "namaz")
MEZAR_KOLON = ("mezarlik", "defin yeri", "kabristan", "defin")
SAAT_KOLON = ("namaz vakti", "saat", "vakit")
TARIH_KOLON = ("defin tarihi", "cenaze tarihi", "namaz tarihi", "tarih")


def _temiz_alan(v, kisa=60):
    """Tek alan değeri -> <= 60 karakter olgu; site cümlesi, telefon, adres içeren değer atılır (None)."""
    v = oi.metin(v or "")
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
    """Gün son 7 gün ya da yarın mı? (bekleme deposu yarını karşılar; eski arşiv satırları alınmaz)"""
    if not gun:
        return False
    bugun = date.today()
    return (bugun - timedelta(days=6)).isoformat() <= gun <= (bugun + timedelta(days=1)).isoformat()


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
            h = oi.hucreler(tr)
            ad_ham = oi.kolon(baslik, h, *AD_KOLON)
            ad, yas = ad_ayikla(ad_ham)
            if not ad:
                continue
            yas = yas or next((int(x) for x in [oi.kolon(baslik, h, "yas", "yasi")] if x.isdigit() and 0 < int(x) < 125), None)
            tarih_hucre = oi.kolon(baslik, h, *TARIH_KOLON)
            tarih_turu = "defin"
            if not oi.tarih(tarih_hucre):
                tarih_hucre, tarih_turu = oi.kolon(baslik, h, "vefat tarihi"), "vefat"
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


def adres_tarihi(url):
    """Adres sonundaki '14-ekim-2026' -> '2026-10-14' (Türkçe harfsiz ay adı katlanır); bulunamazsa None. oi.tarih hata verirse None."""
    m = re.search(r"(\d{1,2})-([a-z]+)-(20\d\d)/?$", ortak.katla(url.split("?")[0]).replace(" ", "-")) or \
        re.search(r"(\d{1,2})-([a-z]+)-(20\d\d)/?$", url.lower().split("?")[0])
    if not m:
        return None
    ay = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5, "haziran": 6, "temmuz": 7, "agustos": 8, "eylul": 9, "ekim": 10, "kasim": 11, "aralik": 12}.get(m.group(2))
    try:
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
    if not kayitlar:
        kayitlar = tablo_ayristir(sayfa, ctx, il_adi, s) if s["kalip"] == "tablo" else liste_ayristir(sayfa, ctx, il_adi, s)
    if not kayitlar:
        kayitlar = gunluk_haberler(sayfa, ctx, il_adi, s)
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


def calistir(defter, veri_kok=VERI, kuru=False, sure_sn=600, simdi=None, il_suzgec=None):
    """Defterdeki satırları okur. Dönen: özet sözlüğü. Hiçbir satır hatası turu düşürmez."""
    iller = il_adlari()
    durum = durum_yukle(veri_kok)
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
        neden = atlama_nedeni(s, durum, simdi)
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
            ozet["atlandi"][ad] = f"ENGEL (bırakıldı): {e}"
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
        durum_kaydet(veri_kok, durum)
    ozet["ornek"] = [{a: k.get(a) for a in ("il", "ilce", "ad_soyad", "yas", "liste_tarihi", "namaz_yeri_vakti", "defin_yeri", "kaynak_turu")}
                     for v in toplanan.values() for k in v][:5]
    return ozet


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    def arg(ad, varsayilan=None):
        return argv[argv.index(ad) + 1] if ad in argv and argv.index(ad) + 1 < len(argv) else varsayilan

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
    ozet = calistir(defter, kuru=kuru, sure_sn=int(arg("--sure-sn", "600")), il_suzgec=arg("--il"))
    ozet["istek_sayisi"] = sayac["istek"] if tavan else None
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
