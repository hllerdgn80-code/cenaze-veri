#!/usr/bin/env python3
"""16 bos il: YEREL RADYO/TV, MUHTARLIK ve KOY/HEMSEHRI DERNEGI siteleri kesfi + on inceleme (14.10.2026, H51).
Aday = (a) Google Haberler RSS sorgularindan (YALNIZ kesif; baslik saklanmaz) alan adlari, (b) tahmini alan adlari (DNS cozulenler).
Her aday: robots.txt, 403/CAPTCHA/giris DOLANILMAZ, <=40 istek, >=3,5 sn/alan adi, kisi adi YAZILMAZ (kesif_muftu_belediye.tara).
Cikti: arastirma/kesif/radyo-tv-muhtar-dernek-2026-10-14.jsonl.   python3 araclar/kesif_radyo_tv_muhtar_dernek.py [--il agri] [--is 10] [--kesif-yalniz]"""
import argparse, concurrent.futures as cf, json, os, re, socket, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kesif_muftu_belediye as K

ROOT = K.ROOT
OUT = os.path.join(ROOT, "arastirma", "kesif", "radyo-tv-muhtar-dernek-2026-10-14.jsonl")
ADAY_JSON = os.path.join(ROOT, "arastirma", "kesif", "radyo-tv-muhtar-dernek-adaylar.json")
# il adi -> (slug, "demonym" ascii)
ILLER = {"Ağrı": ("agri", "agrili"), "Ardahan": ("ardahan", "ardahanli"), "Bayburt": ("bayburt", "bayburtlu"), "Bingöl": ("bingol", "bingollu"),
         "Bitlis": ("bitlis", "bitlisli"), "Diyarbakır": ("diyarbakir", "diyarbakirli"), "Eskişehir": ("eskisehir", "eskisehirli"),
         "Hakkâri": ("hakkari", "hakkarili"), "Iğdır": ("igdir", "igdirli"), "Kırklareli": ("kirklareli", "kirklarelili"), "Mardin": ("mardin", "mardinli"),
         "Muş": ("mus", "muslu"), "Siirt": ("siirt", "siirtli"), "Şırnak": ("sirnak", "sirnakli"), "Tunceli": ("tunceli", "tuncelili"), "Yozgat": ("yozgat", "yozgatli")}
ILCE = {"agri": ["dogubayazit", "patnos"], "ardahan": ["gole", "cildir"], "bayburt": [], "bingol": ["genc", "solhan"], "bitlis": ["tatvan", "ahlat"],
        "diyarbakir": ["bismil", "silvan"], "eskisehir": ["sivrihisar", "inonu"], "hakkari": ["yuksekova"], "igdir": ["tuzluca"], "kirklareli": ["luleburgaz", "babaeski"],
        "mardin": ["kiziltepe", "midyat"], "mus": ["malazgirt", "varto"], "siirt": ["kurtalan", "baykan"], "sirnak": ["cizre", "silopi"], "tunceli": ["ovacik", "pertek"], "yozgat": ["sorgun", "yerkoy"]}
TLD = [".com", ".com.tr", ".net", ".org"]
TLD_D = [".org", ".com", ".org.tr"]
TR = str.maketrans("ığüşöçİĞÜŞÖÇâîû", "igusocIGUSOCaiu")
KESIF_SORGU = ["{il} radyo", "{il} tv haber", "{il} hemşehri derneği", "{il} muhtarlar derneği", "{il} köyü derneği vefat"]

def tahmin(slug, dem):
    out = []
    for t in TLD:
        for p in (f"{slug}radyo", f"{slug}tv", f"{slug}fm", f"radyo{slug}", f"tv{slug}", f"{slug}radyotv"):
            out.append((p + t, "RADYO/TV"))
    for t in TLD_D:
        for p in (f"{slug}muhtarlar", f"{slug}muhtarlardernegi", f"{slug}muhtarlarfederasyonu", f"muhtar{slug}"):
            out.append((p + t, "MUHTARLIK"))
        for p in (f"{dem}ler", f"{dem}lerdernegi", f"{dem}lardernegi", f"{slug}lilar", f"{slug}hemsehridernegi", f"{slug}dernegi", f"{slug}lilardernegi"):
            out.append((p + t, "DERNEK"))
    for ic in ILCE.get(slug, []):
        for t in (".com", ".org", ".net"):
            out.append((f"{ic}radyo{t}", "RADYO/TV")); out.append((f"{ic}tv{t}", "RADYO/TV")); out.append((f"{ic}dernegi{t}", "DERNEK"))
    return out

def cozulur(h):
    try: socket.setdefaulttimeout(4); socket.getaddrinfo(h, 443); return True
    except Exception: return False

def tur_tahmin(h):
    if re.search(r"radyo|fm\b|fm\.|tv|televizyon", h): return "RADYO/TV"
    if re.search(r"muhtar", h): return "MUHTARLIK"
    if re.search(r"dernek|vakf|lilar|liler|lular|luler|hemsehri", h): return "DERNEK"
    return "YEREL HABER"

def gnews(il, slug):
    out = {}
    for q in KESIF_SORGU:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q.format(il=il) + " when:30d", "hl": "tr", "gl": "TR", "ceid": "TR:tr"})
        st, _, x = K.ac(url, "news.google.com")
        if st != 200: continue
        for m in re.finditer(r'<source url="([^"]+)"', x):
            h = urllib.parse.urlparse(m.group(1)).netloc.lower().replace("www.", "")
            if h and not h.startswith(K.__dict__.get("_x", "@@")): out[h] = out.get(h, 0) + 1
    return out

ATLA = ("google.", "msn.com", "yahoo.", "youtube.", "facebook.", "twitter.", "x.com", "instagram.", "wikipedia.", "milliyet.", "haberler.com", "hurriyet.", "sabah.com.tr", "aa.com.tr", "ntv.com.tr", "cnnturk.", "sozcu.", "haberturk.", "mynet.", "trthaber.", "internethaber.", "ensonhaber.", "star.com.tr", "aksam.", "yenisafak.", "takvim.", "gazeteduvar.", "t24.", "bbc.", "dha.", "iha.", "ihlas", "tiktok.", "t.me", "bianet", "birgun", "cumhuriyet", "dunya", "ahaber", "haber7", "yeniakit", "turkiyegazetesi", "milligazete", "indyturk", "tgrt", "haberglobal", "sondakika.com", "onedio", "ajansspor", "gazetevatan", "yenicag", "karar.com", "tv100", "halktv", "ntvspor", "fanatik", "hurriyet", "aydinlik", "rudaw", "kurdistan24", "dw.com", "euronews", "sputnik", "en.", "gazeteoksijen", "sabah", "posta.com", "gazetem", "odatv", "medyascope", "evrensel", "ilkha", "yeniozgur", "mesaj", "diken", "arti", "cumhuriyet", "turkiye.", "turkishminute", "dogruhaber")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--il"); ap.add_argument("--is", dest="isn", type=int, default=10); ap.add_argument("--kesif-yalniz", action="store_true")
    a = ap.parse_args()
    bilinen = set(l.strip() for l in open(os.environ.get("BILINEN", "/dev/null")) if l.strip()) if os.environ.get("BILINEN") else set()
    adaylar = json.load(open(ADAY_JSON, encoding="utf-8")) if os.path.exists(ADAY_JSON) else {}
    for il, (slug, dem) in ILLER.items():
        if a.il and a.il != slug: continue
        if slug in adaylar: continue
        g = gnews(il, slug)
        liste = {}
        for h, n in g.items():
            if h.startswith(ATLA) or any(x in h for x in ATLA if len(x) > 6): continue
            liste[h] = {"tur": tur_tahmin(h), "kaynak": f"gnews:{n}"}
        for h, t in tahmin(slug, dem):
            if h not in liste: liste[h] = {"tur": t, "kaynak": "tahmin-dns"}
        adaylar[slug] = liste
        json.dump(adaylar, open(ADAY_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(slug, len(liste), flush=True)
    sayac = {}
    for sl, lst in adaylar.items():
        for h, d in lst.items():
            if d['kaynak'].startswith('gnews'): sayac[h] = sayac.get(h, 0) + 1
    for sl, lst in adaylar.items():
        for h in [h for h, d in lst.items() if d['kaynak'].startswith('gnews') and sayac[h] >= 4]: del lst[h]
    json.dump(adaylar, open(ADAY_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.kesif_yalniz: return
    gorev = []
    for il, (slug, dem) in ILLER.items():
        if a.il and a.il != slug: continue
        for h, d in adaylar.get(slug, {}).items():
            if d["tur"] == "YEREL HABER" and slug in ("yozgat", "bayburt"): continue
            gorev.append((il, slug, h, d))
    yapilan = set()
    if os.path.exists(OUT):
        for l in open(OUT, encoding="utf-8"):
            try: j = json.loads(l); yapilan.add((j["il"], j["host"]))
            except Exception: pass
    gorev = [g for g in gorev if (g[0], g[2]) not in yapilan]
    print("gorev", len(gorev), flush=True)
    def is_(g):
        il, slug, h, d = g
        k = K.tara(h, d["tur"], il, None, f"https://{h}/", "", h)
        k["host"] = h; k["aday_kaynak"] = d["kaynak"]; return k
    with cf.ThreadPoolExecutor(a.isn) as ex, open(OUT, "a", encoding="utf-8") as f:
        for k in ex.map(is_, gorev):
            f.write(json.dumps(k, ensure_ascii=False) + "\n"); f.flush()
            print(k["il"], k["host"], k["sinif"], k["son14"], flush=True)

if __name__ == "__main__":
    main()
