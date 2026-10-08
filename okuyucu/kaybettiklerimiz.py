#!/usr/bin/env python3
"""Kaybettiklerimiz menüsünün verisi: Wikidata (CC0) -> veri/kaybettiklerimiz/*.json

Kullanım:  python3 okuyucu/kaybettiklerimiz.py [kategori ...]
Kategoriler: cumhurbaskanlari basbakanlar bakanlar siyasetciler sanatcilar tarihte_bugun
(argümansız hepsi). Her çalışmada baştan üretir.

Yalnız Wikidata'nın yapılandırılmış alanları alınır (CC0). Wikipedia METNİ alınmaz.
Fotoğraf: Commons dosya adı + lisans (yalnız serbest lisanslılar tutulur).
Hariç tutma: (1) otomatik kurallar (Wikidata'dan), (2) elle liste haric_tutulanlar.json.
Yalnız standart kütüphane.
"""
import http.client, json, os, sys, time, re, html, urllib.request, urllib.parse, urllib.error, datetime

UA = "KiminCenazesiBot/0.1 (+kimincenazesi)"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "veri", "kaybettiklerimiz")
HARIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haric_tutulanlar.json")
SPARQL = "https://query.wikidata.org/sparql"
COMMONS = "https://commons.wikimedia.org/w/api.php"
BEKLE = 2.0

# ---- Q kimlikleri (Wikidata'da doğrulandı, 05.10.2026) ----
Q_TURKIYE, Q_OSMANLI, Q_ISRAIL = "Q43", "Q12560", "Q801"
Q_CUMHURBASKANI, Q_BASBAKAN = "Q1922067", "Q2430415"
Q_BAKAN = "Q83307"            # minister (Türkiye bakanlıkları bunun alt sınıfı + P1001/P17 Türkiye)
Q_TBMM_UYESI = "Q21030356"
Q_POLITIKACI = "Q82955"
Q_IL = "Q48336"               # province of Turkey
SAVASLAR = {"Q234738": "Kurtuluş Savaşı", "Q87138": "1919-22 Türk-Yunan Savaşı", "Q164983": "Çanakkale Seferi",
            "Q1450532": "Türk-Fransız Savaşı (Güney Cephesi)", "Q957586": "Türk-Ermeni Savaşı",
            "Q1050999": "1974 Kıbrıs Harekâtı"}
ORGUTLER = {"Q152220": "PKK", "Q1779776": "KCK", "Q864766": "PYD", "Q277036": "YPG", "Q988694": "FETÖ (Gülen hareketi)",
            "Q611202": "DHKP-C", "Q2429253": "IŞİD", "Q34490": "El Kaide", "Q720676": "ASALA",
            "Q1621312": "Hizbullah (Türkiye)", "Q1664680": "MLKP", "Q5154454": "TKP/ML", "Q5154457": "TKP/ML Hareketi",
            "Q771163": "TKP/ML", "Q2700279": "EOKA-B"}
Q_TERORIST = "Q12414919"
SUCLAR = {"Q41397": "soykırım", "Q173462": "insanlığa karşı suç", "Q135010": "savaş suçu"}
SANAT_MESLEKLERI = ("Q33999 Q10800557 Q2259451 Q10798782 Q2405480 Q177220 Q488205 Q639669 Q36834 Q36180 Q6625963 "
                    "Q49757 Q1028181 Q2526255 Q2059704 Q245068 Q214917 Q28389 Q1281618 Q158852 Q822146 Q486748 "
                    "Q3387717 Q4610556 Q1930187 Q482980 Q42973 Q1209498 Q15981151 Q2865819 Q5716684 Q33231 Q10871364").split()

_son = [0.0]
BASLA = time.time()
BUTCE = float(os.environ.get("BUTCE", "0"))   # saniye; aşılırsa önbellek kaydedilip çıkılır (yeniden çalıştırınca devam eder)
ONBELLEK = os.path.join(OUT, "_ara", "onbellek.json")
CACHE = {"dilim": {}, "FL": {}, "DET": {}, "FOTO": {}}

_log = lambda *a: print(*a, file=sys.stderr, flush=True)


class Zaman(Exception):
    pass


def kaydet_onbellek():
    os.makedirs(os.path.dirname(ONBELLEK), exist_ok=True)
    fl = {i: {k: sorted(v) for k, v in d.items()} for i, d in FL.items()}
    with open(ONBELLEK + ".tmp", "w", encoding="utf8") as f:
        json.dump({"dilim": CACHE["dilim"], "FL": fl, "DET": DET, "FOTO": FOTO}, f, ensure_ascii=False)
    os.replace(ONBELLEK + ".tmp", ONBELLEK)


def yukle_onbellek():
    if os.environ.get("TEMIZ") or not os.path.exists(ONBELLEK):
        return
    d = json.load(open(ONBELLEK, encoding="utf8"))
    CACHE["dilim"] = d["dilim"]
    FL.update({i: {k: set(v) for k, v in x.items()} for i, x in d["FL"].items()})
    DET.update(d["DET"])
    FOTO.update(d["FOTO"])


def sparql(q, deneme=5):
    if BUTCE and time.time() - BASLA > BUTCE:
        kaydet_onbellek()
        _log("BÜTÇE doldu; yeniden çalıştırın (kaldığı yerden devam eder)")
        sys.exit(75)
    for d in range(deneme):
        gec = BEKLE - (time.time() - _son[0])
        if gec > 0:
            time.sleep(gec)
        _son[0] = time.time()
        req = urllib.request.Request(SPARQL, data=urllib.parse.urlencode({"query": q, "format": "json"}).encode(),
                                     headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        try:
            raw = urllib.request.urlopen(req, timeout=100).read()
            return json.loads(raw)["results"]["bindings"]
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf8", "replace")
            if e.code == 500 and "Timeout" in body:
                raise Zaman()
            _log("HTTP", e.code, body[:100])
            time.sleep(int(e.headers.get("Retry-After", "10")) if e.code == 429 else 10 * (d + 1))
        except (json.JSONDecodeError, TimeoutError, urllib.error.URLError, OSError, http.client.HTTPException) as e:
            _log("hata", type(e).__name__, str(e)[:80])
            if isinstance(e, (json.JSONDecodeError, http.client.IncompleteRead)) and d >= 1:
                raise Zaman()
            time.sleep(10 * (d + 1))
    raise RuntimeError("SPARQL başarısız")


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def val(b, k):
    return b[k]["value"] if k in b else None


def partiler(liste, n):
    for i in range(0, len(liste), n):
        yield liste[i:i + n]


def values(ids):
    return "VALUES ?p { " + " ".join("wd:" + i for i in ids) + " }"


def toplu(ids, sorgu_fn, n=150):
    """Kimlik gruplarında sorgu çalıştırır, zaman aşımında grubu böler."""
    sonuc = []
    for g in partiler(ids, n):
        sonuc += _toplu_grup(g, sorgu_fn)
    return sonuc


def _toplu_grup(g, sorgu_fn):
    try:
        return sparql(sorgu_fn(g))
    except Zaman:
        if len(g) == 1:
            return []
        h = len(g) // 2
        return _toplu_grup(g[:h], sorgu_fn) + _toplu_grup(g[h:], sorgu_fn)


# ----------------------------------------------------------------- tarih
def tarih_biçim(v, kesinlik):
    """timeValue + precision -> 'YYYY-MM-DD' / 'YYYY-MM' / 'YYYY'."""
    m = re.match(r"(-?\d+)-(\d\d)-(\d\d)", v or "")
    if not m:
        return None
    y, mo, d = m.groups()
    k = int(kesinlik)
    if k >= 11:
        return f"{y}-{mo}-{d}"
    if k == 10:
        return f"{y}-{mo}"
    if k == 9:
        return y
    return None


def yas_hesapla(dg, ve):
    if not dg or not ve:
        return None, False
    try:
        if len(dg) == 10 and len(ve) == 10:
            a = datetime.date.fromisoformat(dg)
            b = datetime.date.fromisoformat(ve)
            return b.year - a.year - ((b.month, b.day) < (a.month, a.day)), False
        return int(ve[:4]) - int(dg[:4]), True
    except (ValueError, TypeError):
        return None, False


# ----------------------------------------------------------------- aday sorguları
def aday_pozisyon(q_poz):
    q = f"""SELECT DISTINCT ?p ?d WHERE {{ ?p wdt:P31 wd:Q5 ; wdt:P570 ?d ; wdt:P39 wd:{q_poz} .
      FILTER(?d >= "1923-01-01T00:00:00Z"^^xsd:dateTime) }}"""
    return {qid(val(b, "p")): {"sl": 0} for b in sparql(q)}


def aday_bakan():
    q = f"""SELECT DISTINCT ?p WHERE {{ ?p wdt:P31 wd:Q5 ; wdt:P570 ?d ; wdt:P39 ?pos .
      ?pos wdt:P279* wd:{Q_BAKAN} . ?pos (wdt:P1001|wdt:P17) wd:{Q_TURKIYE} .
      FILTER(?d >= "1923-01-01T00:00:00Z"^^xsd:dateTime) }}"""
    return {qid(val(b, "p")): {"sl": 0} for b in sparql(q)}


def aday_siyasetci(limit):
    q = f"""SELECT DISTINCT ?p ?sl WHERE {{
      ?art schema:about ?p ; schema:isPartOf <https://tr.wikipedia.org/> .
      ?p wdt:P31 wd:Q5 ; wdt:P570 ?d ; wikibase:sitelinks ?sl .
      {{ ?p wdt:P27 wd:{Q_TURKIYE} ; wdt:P106 wd:{Q_POLITIKACI} }} UNION {{ ?p wdt:P39 wd:{Q_TBMM_UYESI} }}
      FILTER(?d >= "1923-01-01T00:00:00Z"^^xsd:dateTime) }} ORDER BY DESC(?sl) LIMIT {limit}"""
    return {qid(val(b, "p")): {"sl": int(val(b, "sl"))} for b in sparql(q)}


def aday_sanatci(limit):
    occ = " ".join("wd:" + o for o in SANAT_MESLEKLERI)
    q = f"""SELECT DISTINCT ?p ?sl WHERE {{
      ?art schema:about ?p ; schema:isPartOf <https://tr.wikipedia.org/> .
      ?p wdt:P31 wd:Q5 ; wdt:P27 wd:{Q_TURKIYE} ; wdt:P570 ?d ; wikibase:sitelinks ?sl ; wdt:P106 ?occ .
      VALUES ?occ {{ {occ} }}
      FILTER(?d >= "1923-01-01T00:00:00Z"^^xsd:dateTime) }} ORDER BY DESC(?sl) LIMIT {limit}"""
    return {qid(val(b, "p")): {"sl": int(val(b, "sl"))} for b in sparql(q)}


def dilim_sorgu(a, b, ek, esik):
    f = []
    if a:
        f.append(f'?d >= "{a:04d}-01-01T00:00:00Z"^^xsd:dateTime')
    if b:
        f.append(f'?d < "{b:04d}-01-01T00:00:00Z"^^xsd:dateTime')
    f = " && ".join(f) or "true"
    return f"""SELECT ?p ?sl ?d WHERE {{
      ?p wdt:P31 wd:Q5 ; p:P570 ?s . ?s psv:P570 ?n . ?n wikibase:timeValue ?d ; wikibase:timePrecision 11 .
      FILTER({f})
      ?p wikibase:sitelinks ?sl . FILTER(?sl >= {esik})
      ?art schema:about ?p ; schema:isPartOf <https://tr.wikipedia.org/> .
      {ek} }}"""


def dilim_cek(a, b, ek, esik, sonuc, ad=""):
    anahtar = f"{ad}|{a}|{b}"
    if CACHE["dilim"].get(anahtar) == "bolundu":
        o = (a + b) // 2
        dilim_cek(a, o, ek, esik, sonuc, ad)
        dilim_cek(o, b, ek, esik, sonuc, ad)
        return
    if anahtar in CACHE["dilim"]:
        sonuc.update({i: tuple(v) for i, v in CACHE["dilim"][anahtar].items()})
        return
    try:
        rows = sparql(dilim_sorgu(a, b, ek, esik))
    except Zaman:
        if a is not None and b is not None and b - a > 1:
            o = (a + b) // 2
            dilim_cek(a, o, ek, esik, sonuc, ad)
            dilim_cek(o, b, ek, esik, sonuc, ad)
            CACHE["dilim"][anahtar] = "bolundu"
            return
        _log("dilim atlandı", a, b)
        return
    parca = {qid(val(r, "p")): (int(val(r, "sl")), val(r, "d")[:10]) for r in rows}
    sonuc.update(parca)
    CACHE["dilim"][anahtar] = parca
    kaydet_onbellek()
    _log("dilim", ad, a, b, len(rows))


def aday_tarihte_bugun():
    """{ay-gün: {'tr': [(sl,id,yıl)], 'yab': [...]}}; Türkler eşik 6, yabancılar eşik 20."""
    dilimler = [(None, 1500), (1500, 1700), (1700, 1800), (1800, 1850), (1850, 1880), (1880, 1900)] + \
               [(y, y + 3) for y in range(1900, 2027, 3)]
    yab, turk = {}, {}
    for a, b in dilimler:
        dilim_cek(a, b, f"FILTER NOT EXISTS {{ ?p wdt:P27 wd:{Q_TURKIYE} }}", 20, yab, "yab")
        dilim_cek(a, b, f"?p wdt:P27 wd:{Q_TURKIYE} .", 6, turk, "tr")
    gunler = {}
    for kind, src in (("tr", turk), ("yab", yab)):
        for i, (sl, d) in src.items():
            if d.startswith("-") or len(d) < 10:
                continue
            gunler.setdefault(d[5:], {"tr": [], "yab": []})[kind].append((sl, i))
    return gunler


# ----------------------------------------------------------------- bayraklar (hariç tutma kuralları)
def bayraklar(ids):
    war = " ".join("wd:" + x for x in SAVASLAR)
    org = " ".join("wd:" + x for x in ORGUTLER)
    suc = " ".join("wd:" + x for x in SUCLAR)

    def sg(g):
        return f"""SELECT ?p ?k ?v WHERE {{ {values(g)}
          {{ ?p wdt:P27 ?v . BIND("c" AS ?k) }}
          UNION {{ ?p wdt:P607 ?v . VALUES ?v {{ {war} }} BIND("w" AS ?k) }}
          UNION {{ ?p (wdt:P463|wdt:P102|wdt:P1416) ?v . VALUES ?v {{ {org} }} BIND("o" AS ?k) }}
          UNION {{ ?p wdt:P106 ?v . VALUES ?v {{ wd:{Q_TERORIST} }} BIND("t" AS ?k) }}
          UNION {{ ?p wdt:P1399 ?c . ?c wdt:P279* ?v . VALUES ?v {{ {suc} }} BIND("s" AS ?k) }} }}"""

    f = {i: {"c": set(), "w": set(), "o": set(), "t": set(), "s": set()} for i in ids}
    for b in toplu(ids, sg):
        f[qid(val(b, "p"))][val(b, "k")].add(qid(val(b, "v")))
    return f


def kural_degerlendir(fl, manuel):
    """Tetiklenen kuralların listesi (boşsa kalır)."""
    k = []
    if Q_ISRAIL in fl["c"]:
        k.append("a_israil_vatandasi")
    if fl["w"] and fl["c"] and not (fl["c"] & {Q_TURKIYE, Q_OSMANLI}) and not fl.get("m"):
        k.append("b_turkiyeye_karsi_savas")
    if fl["o"] or fl["t"]:
        k.append("c_teror_orgutu")
    if fl["s"]:
        k.append("d_soykirim_savas_sucu")
    return k, manuel


GERI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geri_alinanlar.json")


def geri_yukle():
    try:
        return {x["wikidata_id"] for x in json.load(open(GERI, encoding="utf8"))}
    except FileNotFoundError:
        return set()


def osmanli_safi(ids):
    """Savaşa katılanlardan P241 (askerî birlik) ya da P463 (üyelik) Osmanlı/Türkiye'ye bağlı olanlar."""
    def sg(g):
        return f"""SELECT DISTINCT ?p WHERE {{ {values(g)} ?p (wdt:P241|wdt:P463) ?b .
          {{ FILTER(?b IN (wd:{Q_OSMANLI}, wd:{Q_TURKIYE})) }} UNION {{ ?b (wdt:P17|wdt:P1001|wdt:P361|wdt:P749) wd:{Q_OSMANLI} }}
          UNION {{ ?b (wdt:P17|wdt:P1001) wd:{Q_TURKIYE} }} }}"""
    return {qid(val(b, "p")) for b in toplu(ids, sg)}


def haric_yukle():
    try:
        return {x["wikidata_id"]: x for x in json.load(open(HARIC, encoding="utf8"))}
    except FileNotFoundError:
        return {}


ELENENLER = {}   # id -> {kategori:set, kurallar:set}


def filtrele(adaylar, kategori, manuel, fl_cache):
    """adaylar: id listesi. Dönen: kalanlar listesi. Elenenleri ELENENLER'e yazar."""
    yeni = [i for i in adaylar if i not in fl_cache]
    fl_cache.update(bayraklar(yeni))
    gerekli = [i for i in adaylar if fl_cache[i]["w"] and "m" not in fl_cache[i]]
    if gerekli:
        osm = osmanli_safi(gerekli)
        for i in gerekli:
            fl_cache[i]["m"] = {"Q12560"} if i in osm else set()
    kaydet_onbellek()
    geri = geri_yukle()
    kalan = []
    for i in adaylar:
        k, _ = kural_degerlendir(fl_cache[i], None)
        if i in geri:
            k = [x for x in k if x == "e_elle_liste"] and []
        if i in manuel and i not in geri:
            k.append("e_elle_liste")
        if k:
            e = ELENENLER.setdefault(i, {"kategoriler": set(), "kurallar": set()})
            e["kategoriler"].add(kategori)
            e["kurallar"].update(k)
        else:
            kalan.append(i)
    return kalan


# ----------------------------------------------------------------- ayrıntılar
DET = {}


def etiket(b, tr, en):
    return val(b, tr) or val(b, en)


def ayrinti_cek(ids):
    ids = [i for i in dict.fromkeys(ids) if i not in DET]
    for g in partiler(ids, 150):
        loc = _ayrinti_grup(g)
        DET.update(loc)
        kaydet_onbellek()


def _ayrinti_grup(ids):
    loc = {}
    for i in ids:
        loc[i] = {"ad": None, "ad_dil": None, "sl": 0, "dogum": None, "vefat": None, "dogum_yeri": None,
                  "vefat_yeri": None, "defin_yeri": None, "defin_il": None, "defin_ulke": None, "foto": []}
    # çekirdek
    def s1(g):
        return f"""SELECT ?p ?sl ?tr ?en WHERE {{ {values(g)} ?p wikibase:sitelinks ?sl .
          OPTIONAL {{ ?p rdfs:label ?tr FILTER(lang(?tr)="tr") }} OPTIONAL {{ ?p rdfs:label ?en FILTER(lang(?en)="en") }} }}"""
    for b in toplu(ids, s1, 200):
        d = loc[qid(val(b, "p"))]
        d["sl"] = int(val(b, "sl"))
        d["ad"], d["ad_dil"] = (val(b, "tr"), "tr") if val(b, "tr") else (val(b, "en"), "en")

    # tarihler
    def s2(g):
        return f"""SELECT ?p ?k ?v ?pr ?rk WHERE {{ {values(g)}
          {{ ?p p:P569 ?s . ?s ps:P569 ?v ; psv:P569/wikibase:timePrecision ?pr ; wikibase:rank ?rk . BIND("dogum" AS ?k) }}
          UNION {{ ?p p:P570 ?s . ?s ps:P570 ?v ; psv:P570/wikibase:timePrecision ?pr ; wikibase:rank ?rk . BIND("vefat" AS ?k) }}
          FILTER(?rk != wikibase:DeprecatedRank) }}"""
    gor = {}
    for b in toplu(ids, s2, 200):
        i = qid(val(b, "p"))
        t = tarih_biçim(val(b, "v"), val(b, "pr"))
        if not t:
            continue
        # tercih: Preferred rank, sonra kesinliği yüksek olan
        skor = (val(b, "rk").endswith("PreferredRank"), len(t))
        key = (i, val(b, "k"))
        if key not in gor or skor > gor[key][0]:
            gor[key] = (skor, t)
    for (i, k), (_, t) in gor.items():
        loc[i][k] = t

    # doğum/vefat yeri
    def s3(g):
        return f"""SELECT ?p ?k ?tr ?en WHERE {{ {values(g)}
          {{ ?p wdt:P19 ?y . BIND("dogum_yeri" AS ?k) }} UNION {{ ?p wdt:P20 ?y . BIND("vefat_yeri" AS ?k) }}
          OPTIONAL {{ ?y rdfs:label ?tr FILTER(lang(?tr)="tr") }} OPTIONAL {{ ?y rdfs:label ?en FILTER(lang(?en)="en") }} }}"""
    for b in toplu(ids, s3, 200):
        d = loc[qid(val(b, "p"))]
        if not d[val(b, "k")]:
            d[val(b, "k")] = etiket(b, "tr", "en")

    # defin yeri + il + ülke
    def s4(g):
        return f"""SELECT ?p ?btr ?ben ?itr ?ien ?ctr ?cen WHERE {{ {values(g)} ?p wdt:P119 ?b .
          OPTIONAL {{ ?b rdfs:label ?btr FILTER(lang(?btr)="tr") }} OPTIONAL {{ ?b rdfs:label ?ben FILTER(lang(?ben)="en") }}
          OPTIONAL {{ ?b wdt:P131* ?il . ?il wdt:P31 wd:{Q_IL} .
             OPTIONAL {{ ?il rdfs:label ?itr FILTER(lang(?itr)="tr") }} OPTIONAL {{ ?il rdfs:label ?ien FILTER(lang(?ien)="en") }} }}
          OPTIONAL {{ ?b wdt:P17 ?c . OPTIONAL {{ ?c rdfs:label ?ctr FILTER(lang(?ctr)="tr") }} OPTIONAL {{ ?c rdfs:label ?cen FILTER(lang(?cen)="en") }} }} }}"""
    for b in toplu(ids, s4, 150):
        d = loc[qid(val(b, "p"))]
        yer = etiket(b, "btr", "ben")
        il = etiket(b, "itr", "ien")
        if yer and not d["defin_yeri"]:
            d["defin_yeri"] = yer
        if il:
            d["defin_il"] = il
        if etiket(b, "ctr", "cen") and not d["defin_ulke"]:
            d["defin_ulke"] = etiket(b, "ctr", "cen")

    # fotoğraf dosya adları
    def s5(g):
        return f"SELECT ?p ?img WHERE {{ {values(g)} ?p wdt:P18 ?img }}"
    for b in toplu(ids, s5, 200):
        u = val(b, "img")
        ad = urllib.parse.unquote(u.rsplit("/", 1)[-1]).replace("_", " ")
        if ad not in loc[qid(val(b, "p"))]["foto"]:
            loc[qid(val(b, "p"))]["foto"].append(ad)
    return loc


# ----------------------------------------------------------------- Commons lisans
FOTO = {}   # dosya adı -> dict | None


def serbest_mi(lisans, nonfree):
    if str(nonfree).lower() == "true":
        return False
    l = (lisans or "").lower().replace("-", " ")
    if not l:
        return False
    if re.search(r"\b(nc|nd)\b", l) or "non commercial" in l or "noderiv" in l:
        return False
    return (l.startswith("public domain") or l.startswith("pd") or l.startswith("cc0") or l.startswith("cc by")
            or l.startswith("cc zero") or "public domain" in l)


def temiz(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def commons_lisans(dosyalar):
    dosyalar = [d for d in dict.fromkeys(dosyalar) if d not in FOTO]
    for g in partiler(dosyalar, 50):
        params = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "extmetadata",
                  "iiextmetadatafilter": "LicenseShortName|NonFree|Artist|Copyrighted",
                  "titles": "|".join("File:" + x for x in g)}
        time.sleep(1.0)
        veri = None
        for d in range(4):
            try:
                req = urllib.request.Request(COMMONS + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
                veri = json.load(urllib.request.urlopen(req, timeout=60))
                break
            except Exception as e:
                _log("commons hata", e)
                time.sleep(5 * (d + 1))
        if veri is None:
            for x in g:
                FOTO[x] = None
            continue
        norm = {n["from"]: n["to"] for n in veri.get("query", {}).get("normalized", [])}
        sayfalar = {p["title"]: p for p in veri.get("query", {}).get("pages", {}).values()}
        for x in g:
            t = norm.get("File:" + x, "File:" + x)
            p = sayfalar.get(t)
            em = (p or {}).get("imageinfo", [{}])[0].get("extmetadata", {}) if p else {}
            lis = (em.get("LicenseShortName") or {}).get("value")
            if p and serbest_mi(lis, (em.get("NonFree") or {}).get("value")):
                FOTO[x] = {"dosya": x, "lisans": lis, "yazar": temiz((em.get("Artist") or {}).get("value"))[:200] or None,
                           "url": "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(x.replace(" ", "_")),
                           "sayfa": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(x.replace(" ", "_"))}
            else:
                FOTO[x] = None


def foto_sec(ids):
    commons_lisans([f for i in ids for f in DET[i]["foto"]])
    for i in ids:
        DET[i]["fotograf"] = next((FOTO[f] for f in DET[i]["foto"] if FOTO.get(f)), None)


# ----------------------------------------------------------------- kayıt kurma
def kayit(i, ek=None):
    d = DET[i]
    yas, yak = yas_hesapla(d["dogum"], d["vefat"])
    r = {"ad": d["ad"] or i, "dogum_tarihi": d["dogum"], "vefat_tarihi": d["vefat"], "vefat_yasi": yas}
    if yak:
        r["vefat_yasi_yaklasik"] = True
    r.update({"dogum_yeri": d["dogum_yeri"], "vefat_yeri": d["vefat_yeri"], "defin_yeri": d["defin_yeri"],
              "defin_il": d["defin_il"], "defin_ulke": None if d["defin_il"] else d["defin_ulke"],
              "wikidata_id": i, "sitelink_sayisi": d["sl"], "fotograf": d.get("fotograf")})
    if ek:
        r.update(ek)
    return r


def sirala(kayitlar):
    return sorted(kayitlar, key=lambda r: ((r["vefat_tarihi"] or "").ljust(10, "0"), r["sitelink_sayisi"]), reverse=True)


def yaz(ad, veri):
    os.makedirs(os.path.dirname(os.path.join(OUT, ad)), exist_ok=True)
    with open(os.path.join(OUT, ad), "w", encoding="utf8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
        f.write("\n")


def gorevler(ids, q_filtre, ordinal=True):
    """Pozisyon dönemleri: {id: [ {gorev, sira, baslangic, bitis} ]}"""
    def sg(g):
        return f"""SELECT ?p ?pos ?posl ?ord ?s ?e WHERE {{ {values(g)} ?p p:P39 ?st . ?st ps:P39 ?pos . {q_filtre}
          OPTIONAL {{ ?pos rdfs:label ?posl FILTER(lang(?posl)="tr") }}
          OPTIONAL {{ ?st pq:P1545 ?ord }} OPTIONAL {{ ?st pq:P580 ?s }} OPTIONAL {{ ?st pq:P582 ?e }} }}"""
    out = {}
    for b in toplu(ids, sg, 100):
        out.setdefault(qid(val(b, "p")), []).append(
            {"gorev": val(b, "posl") or qid(val(b, "pos")), "sira": int(val(b, "ord")) if val(b, "ord") and val(b, "ord").isdigit() else None,
             "baslangic": (val(b, "s") or "")[:10] or None, "bitis": (val(b, "e") or "")[:10] or None})
    for i in out:
        out[i].sort(key=lambda x: x["baslangic"] or "")
    return out


# ----------------------------------------------------------------- kategoriler
FL = {}   # bayrak önbelleği


def kategori_pozisyon(ad, q_poz, manuel):
    adaylar = list(aday_pozisyon(q_poz))
    g = gorevler(adaylar, f"FILTER(?pos = wd:{q_poz})")
    # Vekâlet/geçici ve Cumhuriyet öncesi kayıtlar ayıklanır: cumhurbaşkanında sıra numarası (P1545) şart,
    # başbakanda dönem başlangıcı 29.10.1923 sonrası şart.
    for i in list(g):
        if q_poz == Q_CUMHURBASKANI:
            g[i] = [x for x in g[i] if x["sira"]]
        else:
            g[i] = [x for x in g[i] if (x["baslangic"] or "") >= "1923-10-29"]
        if not g[i]:
            del g[i]
    adaylar = [i for i in adaylar if i in g]
    kalan = filtrele(adaylar, ad, manuel, FL)
    ayrinti_cek(kalan)
    foto_sec(kalan)
    out = []
    for i in kalan:
        dn = g.get(i, [])
        siralar = [x["sira"] for x in dn if x["sira"]]
        out.append(kayit(i, {"sira": siralar[0] if siralar else None, "gorev_donemi": [{"baslangic": x["baslangic"], "bitis": x["bitis"]} for x in dn]}))
    yaz(ad + ".json", sirala(out))
    return len(out)


def kategori_bakan(manuel):
    adaylar = list(aday_bakan())
    kalan = filtrele(adaylar, "bakanlar", manuel, FL)
    ayrinti_cek(kalan)
    foto_sec(kalan)
    g = gorevler(kalan, f"?pos wdt:P279* wd:{Q_BAKAN} . ?pos (wdt:P1001|wdt:P17) wd:{Q_TURKIYE} .")
    out = []
    for i in kalan:
        out.append(kayit(i, {"gorevler": [{"gorev": x["gorev"], "baslangic": x["baslangic"], "bitis": x["bitis"]} for x in g.get(i, [])]}))
    yaz("bakanlar.json", sirala(out))
    return len(out)


def kategori_ilk_n(ad, adaylar_fn, n, limit, manuel):
    ad_ = adaylar_fn(limit)
    sirali = sorted(ad_, key=lambda i: -ad_[i]["sl"])
    kalan = filtrele(sirali, ad, manuel, FL)[:n]
    ayrinti_cek(kalan)
    foto_sec(kalan)
    yaz(ad + ".json", sirala([kayit(i) for i in kalan]))
    return len(kalan)


def kategori_tarihte_bugun(manuel):
    gunler = aday_tarihte_bugun()
    secim = {}
    for gun, v in sorted(gunler.items()):
        t = sorted(v["tr"], reverse=True)[:10]
        y = sorted(v["yab"], reverse=True)[:24]
        secim[gun] = (t, y)
    havuz = [i for t, y in secim.values() for _, i in t + y]
    filtrele(havuz, "tarihte_bugun", manuel, FL)
    final = {}
    for gun, (t, y) in secim.items():
        t = [i for _, i in t if not _elendi(i)][:8]
        y = [i for _, i in y if not _elendi(i)]
        yer = 15 - len(t)
        final[gun] = (t, y[:max(yer, 0)])
        # Türk sayısı 8'in altındaysa yabancılar zaten doldurur
    tum = [i for t, y in final.values() for i in t + y]
    ayrinti_cek(tum)
    foto_sec(tum)
    os.makedirs(os.path.join(OUT, "tarihte_bugun"), exist_ok=True)
    adet = 0
    for ay in range(1, 13):
        for gun in range(1, 32):
            try:
                datetime.date(2024, ay, gun)
            except ValueError:
                continue
            k = f"{ay:02d}-{gun:02d}"
            t, y = final.get(k, ([], []))
            kay = [kayit(i, {"turk": True}) for i in t] + [kayit(i, {"turk": False}) for i in y]
            # Türkler önce, kendi içinde ve yabancılar kendi içinde sitelink sayısına göre
            kay.sort(key=lambda r: (not r["turk"], -r["sitelink_sayisi"]))
            yaz(f"tarihte_bugun/{k}.json", kay)
            adet += len(kay)
    return adet


def _elendi(i):
    return i in ELENENLER


# ----------------------------------------------------------------- ana
def main():
    yukle_onbellek()
    kats = sys.argv[1:] or ["cumhurbaskanlari", "basbakanlar", "bakanlar", "siyasetciler", "sanatcilar", "tarihte_bugun"]
    manuel = haric_yukle()
    sayilar = {}
    for k in kats:
        _log("=== kategori:", k)
        if k == "cumhurbaskanlari":
            sayilar[k] = kategori_pozisyon(k, Q_CUMHURBASKANI, manuel)
        elif k == "basbakanlar":
            sayilar[k] = kategori_pozisyon(k, Q_BASBAKAN, manuel)
        elif k == "bakanlar":
            sayilar[k] = kategori_bakan(manuel)
        elif k == "siyasetciler":
            sayilar[k] = kategori_ilk_n(k, aday_siyasetci, 500, 800, manuel)
        elif k == "sanatcilar":
            sayilar[k] = kategori_ilk_n(k, aday_sanatci, 1000, 1700, manuel)
        elif k == "tarihte_bugun":
            sayilar[k] = kategori_tarihte_bugun(manuel)
        else:
            _log("bilinmeyen kategori", k)
    # elenenler raporu
    if ELENENLER:
        ayrinti_cek(list(ELENENLER))
    elen = [{"wikidata_id": i, "ad": DET[i]["ad"], "kategoriler": sorted(v["kategoriler"]), "kurallar": sorted(v["kurallar"])}
            for i, v in ELENENLER.items()]
    yaz("_elenenler.json", sorted(elen, key=lambda x: x["ad"] or ""))
    kural_say = {}
    for e in elen:
        for r in e["kurallar"]:
            kural_say.setdefault(r, []).append(e["ad"])
    eski = {}
    try:
        eski = json.load(open(os.path.join(OUT, "_meta.json"), encoding="utf8")).get("sayilar", {})
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    eski.update(sayilar)
    yaz("_meta.json", {"uretim_tarihi": datetime.datetime.now().isoformat(timespec="seconds"), "kaynak": "Wikidata (CC0)",
                       "sayilar": eski,
                       "elenen_kural_basina": {k: {"adet": len(v), "ornek": v[:3]} for k, v in sorted(kural_say.items())},
                       "elenen_toplam": len(elen)})
    print(json.dumps(sayilar, ensure_ascii=False))


if __name__ == "__main__":
    main()
