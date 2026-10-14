#!/usr/bin/env python3
"""15 kaynaksiz il: il/ilce MUFTULUKLERI (diyanet.gov.tr alt siteleri) + TUM belediye sitelerinin GENEL duyuru/haber/RSS taramasi (14.10.2026).
Kurallar: robots.txt'e uyar (en uzun eslesen kural kazanir), ayni alan adina >=3,5 sn, site basina <=40 istek, CAPTCHA/403/giris DOLANILMAZ,
kisi adi yazilmaz (yalniz sayilar). Cikti: arastirma/kesif/muftu-belediye-2026-10-14.jsonl
  python3 araclar/kesif_muftu_belediye.py [--il Mardin] [--is 10]"""
import argparse, concurrent.futures as cf, datetime as dt, html, json, os, re, socket, ssl, sys, threading, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "arastirma", "kesif", "muftu-belediye-2026-10-14.jsonl")
UA = "KiminCenazesiKesif/1.0 (+https://kimincenazesi.com; salt okuma, 3.5sn aralik)"
ARA = 3.5
LIMIT = 40
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
BUGUN = dt.date.today()
TR = str.maketrans("ığüşöçİĞÜŞÖÇâîû", "igusocIGUSOCaiu")
def asc(s): return s.translate(TR).lower().replace(" ", "")

ILLER = ["Ağrı", "Ardahan", "Bayburt", "Bingöl", "Bitlis", "Eskişehir", "Hakkari", "Iğdır", "Kırklareli", "Mardin", "Muş", "Siirt", "Şırnak", "Tunceli", "Yozgat"]
# ilceler.json merkez ilceyi icermez; il merkezi belediyesi il adiyla aranir. Ek: belde/ilce adlari
EK_ILCE = {"Mardin": ["Kızıltepe"], "Hakkari": ["Hakkari"], "Eskişehir": ["Eskişehir"]}
KALIP = re.compile(r"vefat|ba[sş]sa[gğ]l[ıi][gğ][ıi]|ba[sş] sa[gğ]l[ıi][gğ][ıi]|cenaze|hakk.{0,3}a y[uü]r[uü]|son yolculu[gğ]|topra[gğ]a verildi|rahmetli|ebediyete|taziye|defnedil|ahirete|vefat[ıi]", re.I)
ANAHTAR_LINK = re.compile(r"vefat|cenaze|taziye|sa[gğ]l[ıi][gğ][ıi]|hakk.?a.?y[uü]r|defin|duyuru|haber|ilan|gundem|g[uü]ndem|basin|bas[ıi]n|etkinlik|mezarl|kaybettik", re.I)
ONCELIK = re.compile(r"vefat|cenaze|taziye|sa[gğ]l[ıi][gğ][ıi]|defin|kaybettik|mezarl", re.I)
TARIH = re.compile(r"(\d{1,2})[./-](\d{1,2})[./-](20\d{2})|(20\d{2})-(\d{2})-(\d{2})")
AYADI = {"ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12}
TARIH2 = re.compile(r"(\d{1,2})\s+(Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)\s+(20\d{2})", re.I)
ENGEL = re.compile(r"captcha|recaptcha|g-recaptcha|cf-chrome|attention required|access denied|erişim engel|just a moment", re.I)

_kilit = {}; _son = {}; _g = threading.Lock()
def bekle(host):
    with _g:
        k = _kilit.setdefault(host, threading.Lock())
    with k:
        gec = time.time() - _son.get(host, 0)
        if gec < ARA: time.sleep(ARA - gec)
        _son[host] = time.time()

def ac(url, host=None, boyut=700000, zs=20):
    host = host or urllib.parse.urlparse(url).netloc
    bekle(host)
    rq = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml,*/*", "Accept-Language": "tr"})
    try:
        r = urllib.request.urlopen(rq, timeout=zs, context=CTX)
        b = r.read(boyut)
        ct = r.headers.get("Content-Type", "")
        m = re.search(r"charset=([\w-]+)", ct)
        enc = m.group(1) if m else "utf-8"
        try: t = b.decode(enc, "replace")
        except Exception: t = b.decode("utf-8", "replace")
        return r.status, r.geturl(), t
    except urllib.error.HTTPError as e:
        return e.code, url, ""
    except Exception as e:
        return 0, url, str(e)[:80]

def cozulur(h):
    return True

class Robots:
    def __init__(self, txt): self.k = []; self._oku(txt or "")
    def _oku(self, txt):
        ua = False; onceki_ua = False
        for s in txt.splitlines():
            s = s.split("#")[0].strip()
            if ":" not in s: continue
            x, v = [y.strip() for y in s.split(":", 1)]
            x = x.lower()
            if x == "user-agent":
                ua = (ua or v == "*") if onceki_ua else (v == "*"); onceki_ua = True
            else:
                onceki_ua = False
                if ua and x in ("allow", "disallow") and v: self.k.append((x, v))
    def izin(self, path):
        en = None
        for a, v in self.k:
            p = re.escape(v).replace(r"\*", ".*").replace(r"\$", "$")
            if re.match(p, path):
                if en is None or len(v) > len(en[1]) or (len(v) == len(en[1]) and a == "allow"): en = (a, v)
        return not (en and en[0] == "disallow")

def metin(h):
    h = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", h, flags=re.S | re.I)
    h = re.sub(r"<(br|/p|/div|/li|/tr|/h\d|/a|/td)[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"[ \t\r\xa0]+", " ", html.unescape(h))

def tarihler(s):
    out = []
    for m in TARIH.finditer(s):
        try:
            if m.group(1): d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            else: d = dt.date(int(m.group(4)), int(m.group(5)), int(m.group(6)))
            out.append(d)
        except Exception: pass
    for m in TARIH2.finditer(s):
        try: out.append(dt.date(int(m.group(3)), AYADI[m.group(2).lower()], int(m.group(1))))
        except Exception: pass
    return out

def say(t):
    """(kalip penceresi sayisi, son 14 gun icinde tarihli pencere sayisi, en yeni tarih) - kisi adi tutulmaz."""
    n = r = 0; en = None; son_bit = -999
    for m in KALIP.finditer(t):
        if m.start() < son_bit: continue
        pen = t[max(0, m.start() - 200): m.end() + 250]; son_bit = m.end() + 250; n += 1
        ds = tarihler(pen)
        for d in ds:
            if d <= BUGUN and (en is None or d > en): en = d
        if any(0 <= (BUGUN - d).days <= 14 for d in ds): r += 1
    return n, r, en

def rss_say(x):
    n = r = 0; en = None
    for it in re.findall(r"<item.*?</item>|<entry.*?</entry>", x, flags=re.S | re.I):
        tt = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<!\[CDATA\[|\]\]>", "", it)))
        tarih = None
        m = re.search(r"<(?:pubDate|published|updated|dc:date)[^>]*>([^<]+)<", it, re.I)
        if m:
            s = m.group(1)
            mm = re.search(r"(\d{1,2}) (\w{3}) (20\d{2})", s)
            ay = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
            try:
                if mm: tarih = dt.date(int(mm.group(3)), ay[mm.group(2)], int(mm.group(1)))
                else:
                    d2 = tarihler(s); tarih = d2[0] if d2 else None
            except Exception: tarih = None
        if KALIP.search(tt):
            n += 1
            if tarih:
                if en is None or tarih > en: en = tarih
                if 0 <= (BUGUN - tarih).days <= 14: r += 1
    return n, r, en

def tara(ad, tur, il, ilce, kok_url, yol_onek, host, ek_yollar=()):
    """Tek site: robots, ana sayfa, ilgili <=6 menu baglantisi, RSS adaylari. <=LIMIT istek."""
    k = {"ad": ad, "tur": tur, "il": il, "ilce": ilce, "url": kok_url, "sinif": None, "istek": 0, "kalip": 0, "son14": 0, "en_yeni": None, "rss": None, "yollar": [], "not": ""}
    sayac = [0]
    def get(u):
        if sayac[0] >= LIMIT: return 0, u, ""
        sayac[0] += 1; return ac(u, host)
    st, son, rtxt = get(f"https://{host}/robots.txt")
    rb = Robots(rtxt if st == 200 and "<html" not in rtxt[:200].lower() else "")
    def izin(u): return rb.izin(urllib.parse.urlparse(u).path or "/")
    st, son, h = get(kok_url)
    if st == 0 and kok_url.startswith("https://") and not yol_onek:
        st, son, h = get(kok_url.replace("https://", "http://", 1))
    if st in (401, 403, 429) or (st == 200 and ENGEL.search(h[:6000]) and len(h) < 15000):
        k.update(sinif="ENGEL", **{"not": f"HTTP {st}/engel"}); k["istek"] = sayac[0]; return k
    if st != 200:
        k.update(sinif="ACILMADI", **{"not": f"HTTP {st} {h[:40] if st == 0 else ''}"}); k["istek"] = sayac[0]; return k
    if not izin(kok_url):
        k.update(sinif="ROBOTS"); k["istek"] = sayac[0]; return k
    k["url"] = son
    toplam_n = toplam_r = 0; en = None; sayfalar = [(kok_url, h)]
    # baglantilar
    base = son
    adaylar = []
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', h, flags=re.S | re.I):
        href = html.unescape(m.group(1)).strip(); lab = re.sub(r"<[^>]+>", " ", m.group(2))
        if re.match(r"(mailto|tel|javascript):", href, re.I) or re.search(r"\.(css|js|jpe?g|png|gif|pdf|docx?|xlsx?|zip|ico|svg)(\?|$)", href, re.I): continue
        u = urllib.parse.urljoin(base, href)
        pu = urllib.parse.urlparse(u)
        if pu.netloc.lower().replace("www.", "") != host.lower().replace("www.", ""): continue
        if yol_onek and not pu.path.lower().startswith(yol_onek.lower()): continue
        if ANAHTAR_LINK.search(href + " " + lab):
            pr = 0 if ONCELIK.search(href + " " + lab) else 1
            adaylar.append((pr, u))
    gor = set(); secili = []
    for pr, u in sorted(adaylar, key=lambda x: x[0]):
        key = u.split("?")[0].rstrip("/").lower() + ("?" + u.split("?")[1].lower() if "?" in u and pr == 0 else "")
        if key in gor: continue
        gor.add(key); secili.append(u)
        if len(secili) >= 6: break
    for u in list(ek_yollar) + secili:
        if sayac[0] >= LIMIT - 4: break
        if not izin(u): k["yollar"].append(["ROBOTS", u[:120]]); continue
        s2, u2, t2 = get(u)
        if s2 == 200 and not (ENGEL.search(t2[:5000]) and len(t2) < 15000):
            sayfalar.append((u2, t2)); k["yollar"].append([s2, u2[:120]])
        else: k["yollar"].append([s2, u2[:120]])
    # RSS
    rs = re.findall(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)', h, flags=re.I) + re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/(?:rss|atom)\+xml', h, flags=re.I)
    aday_rss = [urllib.parse.urljoin(base, x) for x in rs][:2]
    if not aday_rss and not yol_onek:
        aday_rss = [f"https://{host}{p}" for p in ("/rss", "/feed", "/rss.xml")]
    for u in aday_rss:
        if sayac[0] >= LIMIT or not izin(u): continue
        s2, u2, x = get(u)
        if s2 == 200 and re.search(r"<(rss|feed|rdf)", x[:2000], re.I):
            n, r, e = rss_say(x); k["rss"] = {"url": u2[:120], "kalip": n, "son14": r}
            toplam_n += n; toplam_r += r
            if e and (en is None or e > en): en = e
            break
    for u, t in sayfalar:
        n, r, e = say(metin(t)); toplam_n += n; toplam_r += r
        if e and (en is None or e > en): en = e
    k.update(kalip=toplam_n, son14=toplam_r, en_yeni=str(en) if en else None)
    k["sinif"] = "VAR14" if toplam_r else ("KALIP_ESKI" if toplam_n else "ICERIK_YOK")
    k["istek"] = sayac[0]
    return k

def belediye_adaylari(ilce):
    a = asc(ilce)
    return [f"{a}.bel.tr", f"www.{a}.bel.tr", f"{a}belediyesi.bel.tr", f"{a}-bld.gov.tr", f"{a}bld.gov.tr", f"{a}belediyesi.com", f"{a}belediyesi.com.tr", f"{a}belediye.com"]

def isler(iller):
    ilc = json.load(open(os.path.join(ROOT, "okuyucu", "ilceler.json"), encoding="utf-8"))
    out = []
    for il in iller:
        a = asc(il); ilcs = list(dict.fromkeys([il] + ilc.get(il, []) + EK_ILCE.get(il, [])))
        out.append(("muftu_il", il, il, a))
        for i in ilcs:
            if i != il: out.append(("muftu_ilce", il, i, a))
            out.append(("bel", il, i, None))
    return out

def is_yap(j):
    tur, il, ilce, a = j
    ad = ilce if tur != "muftu_il" else il
    try:
        if tur == "bel":
            for h in belediye_adaylari(ilce):
                if not cozulur(h): continue
                # sitenin gercekten bu ilce oldugunu ana sayfada ara
                st, son, t = ac(f"https://{h}/", h, zs=10)
                if st == 0: continue
                if st in (200, 403, 401, 429):
                    gerekli = asc(ilce)
                    if st == 200 and gerekli not in asc(metin(t)[:200000]) :
                        continue
                    k = tara(f"{ilce} Belediyesi", "belediye", il, ilce, f"https://{h}/", "", h)
                    k["alan"] = h; return k
            return {"ad": f"{ilce} Belediyesi", "tur": "belediye", "il": il, "ilce": ilce, "sinif": "SITE_YOK", "alan": None}
        host = f"{a}.diyanet.gov.tr"
        if not cozulur(host): return {"ad": f"{ad} Müftülüğü", "tur": "muftuluk", "il": il, "ilce": ilce, "sinif": "SITE_YOK", "alan": host}
        if tur == "muftu_il":
            k = tara(f"{il} İl Müftülüğü", "muftuluk", il, None, f"https://{host}/Sayfalar/home.aspx", "", host,
                     ek_yollar=[f"https://{host}/sayfalar/ContentsWithoutImage.aspx?MenuCategory=Kurumsal&ContentCategory=ilan&ContentType=true", f"https://{host}/sayfalar/ContentsWithImage.aspx?ContentType=True&MenuCategory=Kurumsal&ContentCategory=haber"])
        else:
            sl = asc(ilce)
            k = tara(f"{ilce} İlçe Müftülüğü", "muftuluk", il, ilce, f"https://{host}/{sl}/Sayfalar/home.aspx", f"/{sl}/", host,
                     ek_yollar=[f"https://{host}/{sl}/sayfalar/ContentsWithoutImage.aspx?MenuCategory=Kurumsal&ContentCategory=ilan&ContentType=true", f"https://{host}/{sl}/sayfalar/ContentsWithImage.aspx?ContentType=True&MenuCategory=Kurumsal&ContentCategory=haber"])
        k["alan"] = host; return k
    except Exception as e:
        return {"ad": ad, "tur": tur, "il": il, "ilce": ilce, "sinif": "HATA", "not": str(e)[:100], "alan": None}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--derin", action="store_true"); ap.add_argument("--il"); ap.add_argument("--is", type=int, default=10, dest="n"); a = ap.parse_args()
    iller = [a.il] if a.il else ILLER
    js = isler(iller); print(len(js), "is", file=sys.stderr)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f, cf.ThreadPoolExecutor(a.n) as ex:
        for k in ex.map(is_yap, js):
            f.write(json.dumps(k, ensure_ascii=False) + "\n"); f.flush()
            print(k.get("il"), k.get("ad"), k.get("sinif"), k.get("kalip"), k.get("son14"), file=sys.stderr)

if __name__ == "__main__" and "--derin" not in sys.argv:
    main()


# ---------------- DERIN: vefat listesi sayfalarini yol sondajiyla bul, tarih istatistigi cikar ----------------
STANDART = ["/vefat-edenler", "/vefat", "/vefatlar", "/vefat-ilanlari", "/cenaze-ilanlari", "/cenaze-duyurulari", "/taziye-ilanlari", "/vefat-edenler/", "/vefat-duyurulari", "/vefat-listesi", "/cenaze", "/basin-sagligi"]
OUT2 = os.path.join(ROOT, "arastirma", "kesif", "muftu-belediye-derin-2026-10-14.jsonl")

def derin(k):
    import difflib
    host = k.get("alan"); res = {"ad": k["ad"], "il": k["il"], "ilce": k["ilce"], "alan": host, "sayfalar": []}
    if not host or k["tur"] != "belediye" or k["sinif"] in ("ENGEL", "ROBOTS", "SITE_YOK", "ACILMADI"): return None
    st, _, rtxt = ac(f"https://{host}/robots.txt", host)
    rb = Robots(rtxt if st == 200 and "<html" not in rtxt[:200].lower() else "")
    st, son, ana = ac(f"https://{host}/", host)
    if st != 200: return None
    ana_t = re.sub(r"\s+", " ", metin(ana))[:3000]
    adaylar = []
    for y in k.get("yollar", []):
        if y[0] == 200 and re.search(r"vefat|cenaze-?ilan|taziye-?ilan|kaybettik|vefatedenler", y[1], re.I): adaylar.append(y[1])
    for p in STANDART:
        u = f"https://{host}{p}"
        if u not in adaylar and not any(u.rstrip("/") == a.rstrip("/") for a in adaylar): adaylar.append(u)
    n_istek = 3
    bak = set()
    for u in adaylar:
        if n_istek >= LIMIT - 2: break
        path = urllib.parse.urlparse(u).path
        if path.rstrip("/") in bak: continue
        bak.add(path.rstrip("/"))
        if not rb.izin(path or "/"): res["sayfalar"].append({"url": u, "durum": "ROBOTS"}); continue
        s2, u2, t2 = ac(u, host); n_istek += 1
        if s2 != 200: continue
        txt = metin(t2); yo = len(KALIP.findall(txt)); tt = re.sub(r"\s+", " ", txt)[:3000]
        benz = difflib.SequenceMatcher(None, ana_t, tt).quick_ratio()
        ds = tarihler(txt); ds = [d for d in ds if d <= BUGUN]
        d14 = len([d for d in ds if (BUGUN - d).days <= 14]); d30 = len([d for d in ds if (BUGUN - d).days <= 30])
        res["sayfalar"].append({"url": u2[:140], "vefat_soz": yo, "ana_benzerlik": round(benz, 2), "tarih_say": len(ds), "en_yeni": str(max(ds)) if ds else None, "son14": d14, "son30": d30, "uzunluk": len(t2)})
    res["istek"] = n_istek
    return res

def derin_main():
    R = [json.loads(l) for l in open(OUT, encoding="utf-8")]
    with open(OUT2, "w", encoding="utf-8") as f, cf.ThreadPoolExecutor(14) as ex:
        for r in ex.map(lambda k: (derin(k) if k["tur"] == "belediye" else None), R):
            if r:
                f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
                print(r["il"], r["ad"], len(r["sayfalar"]), file=sys.stderr)

if __name__ == "__main__" and "--derin" in sys.argv:
    derin_main()
