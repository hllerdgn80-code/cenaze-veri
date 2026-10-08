"""YEREL BASIN kaynakları için ortak yardımcılar (site sahibi kararı 08.10.2026).

Belediye kaynağı olmayan illerde yerel haber sitelerinin GÜNLÜK vefat listelerinden yalnız OLGU alınır:
ad soyad, vefat/defin tarihi, cami + namaz vakti (kısa), mezarlık, varsa ilçe/mahalle, yaş.
ALINMAZ: sitenin cümleleri, taziye metni/yeri, telefon, adres, yakın adları, fotoğraf, ölüm nedeni.
Her kayıt: kaynak_turu "yerel_basin", kaynak_ad (site adı), kaynak_url (o günkü liste sayfası).

Okuma kuralları (ortak_ilce'ninkilere EK):
- Site başına günde en çok 3 istek (robots.txt dahil; sayaç veri/<il>/_basin.json'da, çalışmalar arasında korunur).
  robots.txt 7 gün önbellekte tutulur. Okunmuş liste sayfası yeniden okunmaz (bugünün sayfası 4 saatte bir en çok bir kez).
- robots.txt yasaklıyorsa / 401-403-429 gelirse kaynak BIRAKILIR (oi.Engel); giriş/CAPTCHA/WAF dolanılmaz.
- Önce site haritası / RSS (tek istek) ile o günün liste sayfası bulunur; sitenin derlemesinin tamamı değil pencere (7 gün) kadarı tutulur.
- TLS doğrulaması AÇIK; yalnız standart kütüphane.
"""
import http.client, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi

GUNLUK_ISTEK = 3
KAYNAK_TURU = "yerel_basin"


class ButceDoldu(Exception):
    """Bu site için bugünkü istek hakkı doldu (hata değil; kalan sayfalar yarın okunur)."""


# ---------------------------------------------------------------- durum (istek sayacı, okunan sayfalar, robots önbelleği)
class Durum:
    def __init__(self, klasor):
        self.yol = os.path.join(klasor, "_basin.json")
        try:
            with open(self.yol, encoding="utf-8") as f:
                self.d = json.load(f)
        except Exception:
            self.d = {}
        for k in ("istek", "okunan", "robots"):
            self.d.setdefault(k, {})
        for h in [h for h in self.d["istek"] if h.lower().startswith("www.")]:     # eski kayıt: www. ayrı sayılmıştı -> siteye kat
            hedef = self.d["istek"].setdefault(h[4:].lower(), {})
            for g, n in self.d["istek"].pop(h).items():
                hedef[g] = hedef.get(g, 0) + n

    def kaydet(self):
        bugun = date.today()
        sinir = (bugun - timedelta(days=10)).isoformat()
        for h in list(self.d["istek"]):
            self.d["istek"][h] = {g: n for g, n in self.d["istek"][h].items() if g >= sinir}
        self.d["okunan"] = {u: z for u, z in self.d["okunan"].items() if z[:10] >= sinir}
        ortak.json_yaz(self.yol, self.d)


_durumlar = {}


def durum(ctx):
    k = ctx["klasor"]
    if k not in _durumlar:
        _durumlar[k] = Durum(k)
    return _durumlar[k]


def _indir(url, timeout=40):
    """GET; aynı alan adına >= 3,5 sn (ortak._son_istek). Sunucu bağlantıyı erken keserse (IncompleteRead)
    ve gövdenin büyük kısmı geldiyse onu kullanır. 401/403/429 -> oi.Engel."""
    host = urllib.parse.urlparse(url).netloc
    gecen = time.time() - ortak._son_istek.get(host, 0)
    if gecen < 3.5:
        time.sleep(3.5 - gecen)
    rq = urllib.request.Request(url, headers={"User-Agent": ortak.UA})
    if os.environ.get("CENAZE_HIZLI") == "1":
        timeout = min(timeout, 20)
    for deneme in range(2):          # yanıt hiç gelmeden kopan bağlantıda (IncompleteRead 0 bayt) 5 sn sonra bir kez daha
        try:
            with urllib.request.urlopen(rq, timeout=timeout) as r:
                ctype = r.headers.get("Content-Type", "")
                try:
                    ham = r.read()
                except http.client.IncompleteRead as e:
                    ham = e.partial
                    if len(ham) < 20000:
                        raise
            break
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise oi.Engel(f"HTTP {e.code}: {url}")
            raise
        except (http.client.IncompleteRead, ConnectionError, TimeoutError):
            if deneme:
                raise
            time.sleep(5)
        finally:
            ortak._son_istek[host] = time.time()
    m = re.search(r"charset=([\w-]+)", ctype)
    return ham.decode(m.group(1) if m else "utf-8", "replace")


def site_anahtari(host):
    """Bütçe SİTE başına tutulur: www.alan.com ile alan.com aynı sitedir (yönlendirmede iki ad görülür)."""
    h = (host or "").lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h


def _say(ctx, host):
    d = durum(ctx).d["istek"].setdefault(site_anahtari(host), {})
    g = date.today().isoformat()
    if d.get(g, 0) >= GUNLUK_ISTEK:
        raise ButceDoldu(f"{host}: bugünkü {GUNLUK_ISTEK} istek hakkı doldu")
    d[g] = d.get(g, 0) + 1


def robots_izin(ctx, url):
    p = urllib.parse.urlparse(url)
    host = p.netloc
    r = durum(ctx).d["robots"].get(host)
    if not r or r.get("tarih", "") < (date.today() - timedelta(days=7)).isoformat():
        _say(ctx, host)
        govde, yasak = "", False
        try:
            govde = _indir(f"{p.scheme}://{host}/robots.txt", timeout=30)
        except oi.Engel:
            yasak = True                      # robots.txt'e erişim engeli: tüm siteyi yasak say
        except Exception:
            govde = ""
        if "<html" in govde[:600].lower() or "user-agent" not in govde.lower():
            govde = ""
        r = {"tarih": date.today().isoformat(), "metin": govde[:20000], "yasak": yasak}
        durum(ctx).d["robots"][host] = r
    if r.get("yasak"):
        return False
    if not r.get("metin"):
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r["metin"].splitlines())
    return rp.can_fetch(ortak.UA, url) and rp.can_fetch("*", url)


def al(ctx, url):
    """Bütçeli + robots.txt kontrollü GET. Bütçe dolarsa ButceDoldu, robots yasaksa oi.Engel."""
    if not robots_izin(ctx, url):
        raise oi.Engel(f"robots.txt yasaklıyor: {url}")
    _say(ctx, urllib.parse.urlparse(url).netloc)
    return _indir(url)


def okunacak_mi(ctx, url, sayfa_gunu):
    """Okunmamış sayfa -> True. Okunmuş: yalnız bugünün (ya da dünün) sayfası ve son okumadan 4 saat geçtiyse True."""
    z = durum(ctx).d["okunan"].get(url)
    if not z:
        return True
    if sayfa_gunu and sayfa_gunu >= (date.today() - timedelta(days=1)).isoformat():
        try:
            return (datetime.now() - datetime.fromisoformat(z[:19])).total_seconds() > 4 * 3600
        except Exception:
            return True
    return False


def okundu(ctx, url):
    durum(ctx).d["okunan"][url] = datetime.now().isoformat(timespec="seconds")


def sayfalari_oku(ctx, sayfalar, ayristir, azami=2):
    """sayfalar: [(url, sayfa_gunu)] (yeni -> eski). Pencere içindeki, okunması gereken en çok `azami` sayfa okunur;
    ayristir(html, url, sayfa_gunu) -> kayıt listesi. Bütçe dolarsa kalanlar sonraki çalışmaya kalır."""
    gl = set(ctx["gunler"])
    sonuc, n = [], 0
    okunan = durum(ctx).d["okunan"]
    adaylar = [(u, g) for u, g in sayfalar if not (g and g not in gl) and okunacak_mi(ctx, u, g)]
    adaylar = [x for x in adaylar if x[0] not in okunan] + [x for x in adaylar if x[0] in okunan]   # önce hiç okunmamışlar
    try:
        for url, gun in adaylar:
            if n >= azami:
                break
            try:
                sayfa = al(ctx, url)
            except ButceDoldu as e:
                print(f"  {e}", file=sys.stderr)
                break
            n += 1
            sonuc.extend(ayristir(sayfa, url, gun))
            okundu(ctx, url)              # ayrıştırma başarılıysa okundu sayılır (hata verirse yarın yeniden denenir)
    finally:
        durum(ctx).kaydet()
    return sonuc


# ---------------------------------------------------------------- dizin (site haritası / RSS) okuma
def harita_ogeleri(xml):
    """sitemap / news-sitemap / RSS -> [(url, baslik, tarih_iso|None)]."""
    out = []
    bloklar = re.findall(r"<url>([\s\S]*?)</url>", xml) or re.findall(r"<item>([\s\S]*?)</item>", xml)
    for b in bloklar:
        def al_(desen):
            m = re.search(desen, b)
            return (m.group(1) if m else "").replace("<![CDATA[", "").replace("]]>", "").strip()
        url = al_(r"<loc>([\s\S]*?)</loc>") or al_(r"<link>([\s\S]*?)</link>")
        baslik = oi.metin(al_(r"<news:title>([\s\S]*?)</news:title>") or al_(r"<title>([\s\S]*?)</title>"))
        t = al_(r"<news:publication_date>([^<]*)") or al_(r"<lastmod>([^<]*)") or al_(r"<pubDate>([^<]*)")
        g = None
        if re.match(r"\d{4}-\d{2}-\d{2}", t):
            g = t[:10]
        elif t:
            try:
                g = datetime.strptime(t[5:16], "%d %b %Y").date().isoformat()
            except Exception:
                g = None
        if url:
            out.append((url, baslik, g))
    return out


_AY_RE = "|".join(ortak.AYLAR)


def metinden_tarih(s):
    """'7 Ekim 2026', '07/10/2026', '07.10.2026', '7-ekim-2026' (adres parçası) -> ISO; yoksa None. Gelecek (+2 gün) elenir."""
    s = s or ""
    m = re.search(r"(\d{1,2})[-\s]+(" + _AY_RE + r"|eylul|subat|agustos|kasim|aralik|mayis)[-\s]+(\d{4})", ortak.tr_lower(s))
    if m:
        ay = {"eylul": "eylül", "subat": "şubat", "agustos": "ağustos", "kasim": "kasım", "aralik": "aralık", "mayis": "mayıs"}.get(m.group(2), m.group(2))
        return oi.tarih(f"{m.group(1)} {ay} {m.group(3)}")
    return oi.tarih(s) if re.search(r"\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{4}", s) else None


# ---------------------------------------------------------------- makale gövdesi
def makale_govdesi(sayfa):
    """JSON-LD articleBody (varsa en uzunu) -> düz metin; satır sonları korunur."""
    adaylar = []
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>([\s\S]*?)</script>', sayfa):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        yigin = [d]
        while yigin:
            x = yigin.pop()
            if isinstance(x, dict):
                if isinstance(x.get("articleBody"), str):
                    adaylar.append(x["articleBody"])
                yigin.extend(x.values())
            elif isinstance(x, list):
                yigin.extend(x)
    if not adaylar:
        return ""
    return satirlara(max(adaylar, key=len))


def satirlara(h):
    import html as _h
    h = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", h or "")
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>", "\n", h)
    t = _h.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ").replace("\r", "\n")
    satir = [" ".join(s.split()) for s in t.split("\n")]
    return "\n".join(s for s in satir if s)


# ---------------------------------------------------------------- serbest metinden olgu ayıklama
OLUM = re.compile(r"(hak+['’]?k?[ıi]n\s+rahmetine\s+kavuş\w*|rahmeti\s+rahmana\s+kavuş\w*|vefat\s+et(?:miştir|mistir|ti|miş)\b)", re.I)
_YAKIN = set("""oğlu oğulları kızı kızları eşi eşleri hanımı kocası babası babaları annesi anneleri kardeşi kardeşleri
ağabeyi ağabeyleri abisi abileri ablası ablaları yeğeni yeğenleri dedesi dedeleri ninesi nineleri amcası amcaları
dayısı dayıları teyzesi teyzeleri halası halaları torunu torunları gelini gelinleri damadı damatları kayınpederi
kayınvalidesi kayınbiraderi kayınbabası eniştesi yengesi dünürü bacanağı amcaoğlu amcakızı anneannesi babaannesi
torunları muhtarı muhtarımız""".split())
_DUR = set("""vefat edenler edenler merhum merhume rahmetli muhterem sayın ve ile de da köyü köyünden mahallesi mahallesinden
mah. beldesi beldesinden ilçesi ilçemiz sakinlerinden halkından ailesinden aşireti kolundan emekli emeklisi öğretmen
esnaflarından kurucusu""".split())
_KELIME = r"[A-Za-zÇĞİÖŞÜÂÎÛçğıöşüâîûêÊ]"


def _buyuk_basli(w):
    return bool(re.fullmatch(r"[A-ZÇĞİÖŞÜÂÎÛ]" + _KELIME + r"*\.?", w)) or bool(re.fullmatch(r"[A-ZÇĞİÖŞÜ]\.", w))


def ad_bul(parca):
    """Ölüm ifadesinden HEMEN ÖNCEKİ metinden ad soyadı çıkarır: geriye doğru büyük harfle başlayan sözcükler toplanır;
    yakınlık sözcüğü (babası, eşi ...), kesme işaretli sözcük (Ali'nin), rakam, virgül görülünce durulur.
    Dönen: (ad|None, yas|None)."""
    s = " ".join((parca or "").split())
    yas = None
    for _ in range(2):
        s = re.sub(r"[,\s]+\d{1,2}[./]\d{1,2}[./]\d{4}\s*(?:tarihinde)?\s*$", "", s)              # ', 7.10.2026 tarihinde'
        s = re.sub(r"[,\s]+\d{1,2}\s+(?:" + _AY_RE + r")\s+\d{4}\s*(?:tarihinde)?\s*$", "", s, flags=re.I)
        s = re.sub(r"[,\s]+" + _KELIME + r"+['’](?:da|de|ta|te|nda|nde)\s*$", "", s)             # ', Aydın'da'
        m = re.search(r"\((\d{1,3})\)\s*[,.]?\s*$", s) or re.search(r"\b(\d{1,3})\s+yaşında\s*[,.]?\s*$", s, re.I)
        if m:
            yas = int(m.group(1))
            s = s[:m.start()].rstrip(" ,")
        s = re.sub(r"\([^)]*\)\s*[,.]?\s*$", "", s).rstrip(" ,")                             # (takma ad)
    if s.endswith((";", ":")):
        return None, yas
    toplanan = []
    for w in reversed(s.split()):
        w2 = w.strip(".;:")
        lw = ortak.tr_lower(w2)
        if w != w.rstrip(",;:") or "'" in w2 or "’" in w2 or re.search(r"[\d()/@]", w2):
            break
        if lw in _YAKIN or lw in _DUR or not _buyuk_basli(w2):
            break
        toplanan.append(w2)
        if len(toplanan) > 8:
            break
    toplanan.reverse()
    for i, w in enumerate(toplanan):                 # 'Hüseyin Gülçiçek Min Beyt X': 'Min ...' aile/hane adıdır, ad değildir
        if ortak.tr_lower(w) in ("min", "mın"):
            toplanan = toplanan[:i]
            break
    while toplanan and ortak.tr_lower(toplanan[0]) in ("hacı", "h.", "hafız", "melle", "molla", "şeyh", "seyda", "sofi") and len(toplanan) > 3:
        toplanan = toplanan[1:]
    if not (2 <= len(toplanan) <= 5):
        return None, yas
    return oi.ad_duzelt(" ".join(toplanan)), (yas if yas and 0 < yas < 125 else None)


_CAMI = re.compile(r"(?i:cami(?:i|si)?\b|camii\w*|camisi\w*|camisin\w*|cem\s*evi\w*|cemevi\w*|musalla\w*)")
_CAMI_DUR = re.compile(r"^(?:cena[sz]e\w*|merhum\w*|bugün|yarın|saat|namaz\w*|müteakip|müteakiben|ardından|sonra|kılınacak|kılınan|"
                       r"olarak|ve|ile|ilçemiz|ilimiz|\d.*)$", re.I)


def namaz_kisa(cumle):
    """Cenaze cümlesinden yalnız '<Cami adı> Camii, <vakit> namazı' (kısa; sitenin cümlesi değil). Yoksa yalnız vakit."""
    if not cumle:
        return None
    vm = re.search(r"\b(sabah|öğle|öğlen|ikindi|akşam|yatsı|cuma)\b", ortak.tr_lower(cumle))
    vakit = {"öğlen": "öğle"}.get(vm.group(1), vm.group(1)) if vm else None
    cami = None
    sozler = cumle.split()
    for i, w in enumerate(sozler):
        if not _CAMI.match(w.strip(",.;:'’")):
            continue
        on = []
        for x in reversed(sozler[max(0, i - 4):i]):
            x2 = x.strip(",.;:")
            if _CAMI_DUR.match(ortak.tr_lower(x2)) or not re.match(r"[A-ZÇĞİÖŞÜ0-9]", x2) or "'" in x2 or "’" in x2 or x != x.rstrip(",;:"):
                break
            on.append(x2)
        if on:
            on.reverse()
            tur = "Cemevi" if re.search(r"cem", ortak.tr_lower(w)) else ("Musalla" if "musalla" in ortak.tr_lower(w) else "Camii")
            cami = oi.buyuk_ise_title(" ".join(on), yer=True) + " " + tur
            break
    v = f"{vakit} namazı" if vakit and vakit != "cenaze" else None
    s = ", ".join(x for x in (cami, v) if x)
    return s[:60].rstrip(", ") if s else None


def mahalle_temiz(on):
    """Girişin başındaki 'X Köyünden / X Mahallesinden' -> 'X Köyü' (yalnız 1-3 sözcüklük temiz ad)."""
    on = re.sub(r"^[A-ZÇĞİÖŞÜ][\wçğıöşü]*['’](?:n?[ıiuü]n)\s+", "", (on or "").strip())   # "Kurtalan'ın ..."
    on = re.sub(r"^(?:merhum|merhume|rahmetli|merhumun|ilçemiz)\s+", "", on, flags=re.I)
    m = oi.mahalle_ayikla(on)
    if m and re.fullmatch(r"(?:[A-ZÇĞİÖŞÜ][\wçğıöşü()-]*\s){1,3}(?:Köyü|Mahallesi|Beldesi|Mezrası)", m) and not re.search(r"(?i)taziye|cami", m):
        return m
    return None


def kisa(s, n=60):
    s = " ".join((s or "").split())
    return s if s and len(s) <= n else None


def il_disi_bul(il, metin_):
    """Cenaze cümlesinde başka bir il adı geçiyorsa (ör. 'Aydın Ovaeymir Mezarlığı'nda', 'Batman'a götürülecektir') o il."""
    if not metin_:
        return None
    kendi = ortak.katla(il)
    iller = {ortak.katla(x): x for x in ortak.ilce_verisi().get("_iller", [])}
    for w in re.findall(r"[A-ZÇĞİÖŞÜ][^\s,.;()]*", metin_):
        a = iller.get(ortak.katla(re.split(r"['’]", w)[0]))
        if a and ortak.katla(a) != kendi:
            return a
    return None


def ilce_bul(il, metin_, ilk_sozcuk=6):
    """Metnin ilk sözcüklerinde ilin resmî ilçe adı geçiyorsa onu döndürür."""
    liste = {ortak.katla(x): x for x in ortak.ilce_listesi(il)}
    for w in (metin_ or "").split()[:ilk_sozcuk]:
        a = liste.get(ortak.katla(re.split(r"['’]", w)[0]))
        if a:
            return a
    return None


def cenaze_cumlesi(metin_):
    m = re.search(r"(cena[sz]e\w*[\s\S]*?(?:defnedil\w*|toprağa veril\w*|götürül\w*|kaldırıl\w*|kılın\w*)[^.]*\.?)", metin_ or "", re.I)
    return m.group(1) if m else None


_KISALTMA = {"mah", "sk", "cad", "no", "hz", "dr", "av", "prof", "doç", "h", "m", "s", "öğr", "gör", "yrd", "uzm", "op"}


def girisleri_ayir(metin_):
    """Serbest metin -> [(önceki parça, ölüm ifadesi, sonraki parça)]. Önceki parça bir önceki girişin sonundan başlar."""
    t = re.sub(r"\.(?=[A-ZÇĞİÖŞÜ])", ". ", metin_ or "")
    t = re.sub(r"(\d{4})(?=[A-ZÇĞİÖŞÜ])", r"\1 ", t)
    ms = list(OLUM.finditer(t))
    out = []
    for i, m in enumerate(ms):
        bas = ms[i - 1].end() if i else 0
        on = t[bas:m.start()]
        # önceki girişin cenaze/taziye/telefon kuyruğunu at: son cümle sonundan (". " ya da satır sonu) sonrası alınır
        noktalar = [m2.start() for m2 in re.finditer(r"(\S+)\.\s", on)
                    if ortak.tr_lower(m2.group(1)) not in _KISALTMA]
        kes = max([on.rfind("\n"), on.rfind(": ")] + [p_ + len(re.match(r"\S+", on[p_:]).group(0)) for p_ in noktalar])
        on_kisa = on[kes + 1:] if kes >= 0 else on
        son = t[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(t)]
        out.append((on_kisa.strip(), m.group(0), son, on))
    return out


def kayit(ctx, il, slug, kaynak_ad, url, ad, gun, ilce=None, ek_id="", **alan):
    """Yerel basın kaydı. ilce None -> ilce_belirsiz. ham'a yalnız sayfa tarihi / tarih kaynağı yazılır."""
    k = oi.kayit(il, ilce, slug, ad, gun, kaynak_ad, url, ctx["alindi"], ek_id=ek_id, liste_tarihi=gun, **alan)
    k["kaynak_turu"] = KAYNAK_TURU
    if not ilce:
        k["ilce"] = None
        k["ilce_belirsiz"] = True
    return k


def serbest_kayitlar(ctx, il, slug, kaynak_ad, url, sayfa_gunu, metin_, varsayilan_ilce=None, ilce_basliklari=False,
                     tarih_zorunlu=False):
    """Serbest metin listesinden kayıtlar (Mardin, Siirt, Merzifon, Kurtalan, Bitlis biçimleri).
    ilce_basliklari: '<İlçe> Vefat Edenler' başlıkları ilçe olarak kullanılır (Merzifon Bilgi; sonraki girişlere de geçer).
    tarih_zorunlu: girişte açık tarih yoksa kayıt ALINMAZ (biriken/arşiv sayfaları: Artı Siirt)."""
    girisler, aktif = [], None
    for on, ifade, son, on_tam in girisleri_ayir(metin_):
        if ilce_basliklari:
            hs = re.findall(r"([A-ZÇĞİÖŞÜ][\wçğıöşü]+)\s+Vefat\s+Edenler", on_tam)
            if hs:
                aktif = hs[-1]
            on = re.sub(r"^.*Vefat\s+Edenler\s*", "", on)
        ad, yas = ad_bul(on)
        if not ad:
            if girisler and not ad:                   # aynı kişinin ikinci cümlesi olabilir: kuyruğu öncekine ekle
                girisler[-1]["son"] += " " + son
            continue
        if girisler and ortak.katla(girisler[-1]["ad"]) == ortak.katla(ad):
            girisler[-1]["son"] += " " + son          # 'AD Hakk'ın rahmetine kavuşmuştur. <yakınlar> AD Hakk'ın ...' tekrarı
            girisler[-1]["yas"] = girisler[-1]["yas"] or yas
            continue
        girisler.append({"ad": ad, "yas": yas, "on": on, "son": son, "baslik": aktif})
    sonuc, gorulen = [], set()
    for g in girisler:
        ad, on, son = g["ad"], g["on"], g["son"]
        if ortak.katla(ad) in gorulen:
            continue
        gorulen.add(ortak.katla(ad))
        vef = metinden_tarih(son[:40]) or metinden_tarih(on[-40:])
        cumle = cenaze_cumlesi(son[:700])
        defin_t = metinden_tarih(cumle) if cumle else None
        namaz_t = None
        if cumle and re.search(r"\bbugün\b", ortak.tr_lower(cumle)):
            namaz_t = sayfa_gunu
        elif cumle and re.search(r"\byarın\b", ortak.tr_lower(cumle)) and sayfa_gunu:
            namaz_t = (datetime.strptime(sayfa_gunu, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        if not (vef or defin_t or namaz_t):
            if tarih_zorunlu:
                continue
            vef = sayfa_gunu          # günlük "bugün vefat edenler" listesi: sayfa günü vefat günüdür
            tarih_kaynagi = "yayin_tarihi"
        else:
            tarih_kaynagi = "metin"
        namaz, defin = (oi.cenaze_ayikla(cumle) if cumle else (None, None))
        if defin:
            defin = re.sub(r"^(?:İlçemiz|ilçemiz|İLÇEMİZ|Şehrimiz|şehrimiz)\s+", "", defin)
            if len(defin.split()) < 2:
                defin = None              # yalnız "Mezarlığı" kaldıysa yer adı yok
        ilce = ilce_bul(il, g["baslik"], 1) if g["baslik"] else None
        ilce = ilce or ilce_bul(il, on) or varsayilan_ilce
        gun = defin_t or namaz_t or vef or sayfa_gunu
        k = kayit(ctx, il, slug, kaynak_ad, url, ad, gun, ilce=ilce, ek_id=str(vef or ""),
                  yas=g["yas"], vefat_tarihi=vef, defin_zamani=defin_t, namaz_tarihi=namaz_t,
                  namaz_yeri_vakti=namaz_kisa(cumle), defin_yeri=kisa(defin), mahalle=kisa(mahalle_temiz(on)),
                  ham={"sayfa_tarihi": sayfa_gunu, "tarih_kaynagi": tarih_kaynagi})
        dis = il_disi_bul(il, cumle)
        if dis:
            k["il_disi_defin"] = {"il": dis, "ilce": None}
            k["ilce_belirsiz"] = False
        sonuc.append(k)
    return sonuc


# ---------------------------------------------------------------- okuyucu kalıbı
def dizin(ctx, url):
    """Site haritası / RSS'i okur (1 istek). Bugünkü bütçe dolmuşsa None (kaynak bu çalışmada atlanır, hata değil)."""
    try:
        return al(ctx, url)
    except ButceDoldu as e:
        print(f"  {e}", file=sys.stderr)
        durum(ctx).kaydet()
        return None


def baslik_ad(sayfa, site_eki):
    """<title>AD - Site</title> / og:title -> ad."""
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', sayfa) or re.search(r"<title>([\s\S]*?)</title>", sayfa)
    t = oi.metin(m.group(1)) if m else ""
    return t.split(" - " + site_eki)[0].strip() if t else ""


def yayin_tarihi(sayfa):
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', sayfa) or re.search(r'name="datePublished" content="(\d{4}-\d{2}-\d{2})', sayfa)
    return m.group(1) if m else None
