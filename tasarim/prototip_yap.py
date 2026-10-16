#!/usr/bin/env python3
"""Kimin Cenazesi HTML prototipini üretir: veri/ JSON'larından gömülü veri + sablon.html -> prototip.html.
Kaynak adı/URL'si gömülmez (§16/§17)."""
import json, pathlib, sys
MAGAZA = "--magaza" in sys.argv
OUT = "prototip-magaza.html" if MAGAZA else "prototip.html"
K = pathlib.Path(__file__).resolve().parent.parent
T = pathlib.Path(__file__).resolve().parent

import re as _re
_ADLAR = json.load(open(pathlib.Path(__file__).resolve().parent/"adlar.json"))
_E, _K = set(_ADLAR["e"]), set(_ADLAR["k"])
def cinsiyet_coz(r):
    """TEK cinsiyet kaynağı: kayıt.cinsiyet → ad listesi (ilk ad) → None. Yanlış cinsiyet yazmaktansa None (nötr kalıp)."""
    c = {"Erkek": "e", "Kadın": "k", "e": "e", "k": "k"}.get(r.get("cinsiyet") or "")
    if c: return c
    ilk = (r.get("ad_soyad") or "").split(" ")[0]
    ilk = ilk[:1].upper() + ilk[1:].lower().replace("i̇", "i") if ilk else ""
    e, k = ilk in _E, ilk in _K
    return "e" if e and not k else "k" if k and not e else None
AY = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
def tarih_tr(t):   # "2026-10-04" -> "4 Ekim"
    y, a, g = map(int, t.split("-")); return f"{g} {AY[a-1]}"
def cenaze_gunu(r):   # TEK KAYNAK: tarih şeridi gruplaması VE kart üst etiketi bu alanı kullanır
    dz = r.get("defin_zamani") or ""
    return r.get("namaz_tarihi") or (dz if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", dz) else None) or r["liste_tarihi"]
def vakit(s):
    m = _re.search(r"(sabah|öğle|ikindi|akşam|yatsı|cuma)", (s or "").lower().replace("İ", "i").replace("I", "ı"))
    return m.group(1).capitalize() if m else ""
def etiket(gun, namaz):
    return " · ".join(x for x in ("Cenaze", tarih_tr(gun), vakit(namaz)) if x)

# --- §32: isimsiz bebek + aynı kişi iki ilçede (ikinci kilit; kapi.py ile aynı kural) ---
_YT = {"isimsiz", "adsiz", "yeni", "dogan", "kiz", "erkek", "bilinmeyen", "bilinmiyor", "bebek", "bebegi", "bebekler", "no", "nolu"}
def _kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower()
    for a, b in zip("çğıöşü", "cgiosu"): s = s.replace(a, b)
    return _re.sub(r"[^a-z0-9]+", " ", s).strip()
def isimsiz_bebek(r):
    ad = (r.get("ad_soyad") or "").strip()
    if _kat(ad).startswith("bebek"):                      # prototipte adı "Bebek…" olan ham kaynak kayıtları gösterilmez
        return True
    kel = _kat(ad).split()
    if not any(w in ("isimsiz", "adsiz", "bebek", "bebegi") for w in kel) and "yeni dogan" not in " ".join(kel):
        return False
    kalan = [w for w in kel if w not in _YT and not w.isdigit()]
    return len(kalan) < 2
def bebek_mi(r):
    try: return bool(r.get("bebek")) or (r.get("yas") is not None and int(r["yas"]) < 2)
    except (TypeError, ValueError): return bool(r.get("bebek"))
def _g(t):
    import datetime as d
    try: return d.date.fromisoformat(t)
    except Exception: return None
def _tarihler(r):
    t = [_g(r.get(a) or "") for a in ("vefat_tarihi", "namaz_tarihi")] + [_g((r.get("defin_zamani") or "")[:10])]
    return [x for x in t if x] or [x for x in [_g(r.get("liste_tarihi") or "")] if x]
def tekil_et(gruplar):
    """gruplar: [(ilçe_anahtarı, [kayıt])...] okuma sırasıyla. Aynı ad + ±2 gün (yaş farkı <= 1) -> ilk ilçedeki kayıt kalır, en dolu alanlarla."""
    kumeler = []
    for gi, (_, liste) in enumerate(gruplar):
        for k in liste:
            for km in kumeler:
                a = km[0][1]
                ok = _kat(a["ad_soyad"]) == _kat(k["ad_soyad"])
                if ok and a.get("yas") is not None and k.get("yas") is not None:
                    ok = abs(int(a["yas"]) - int(k["yas"])) <= 1
                if ok and any(abs((x - y).days) <= 2 for x in _tarihler(a) for y in _tarihler(k)):
                    km.append((gi, k)); break
            else:
                kumeler.append([(gi, k)])
    at = set()
    for km in kumeler:
        for _, o in km[1:]:
            for f, v in o.items():
                if km[0][1].get(f) in (None, "", []) and v not in (None, "", []): km[0][1][f] = v
            at.add(id(o))
    return [(a, [k for k in l if id(k) not in at]) for a, l in gruplar], len(at)

def ilan(r):
    g = cenaze_gunu(r)
    return {"bebek": bebek_mi(r), **{"id": r["id"], "ilce": r["ilce"], "mah": r["mahalle"], "ad": r["ad_soyad"],   # anne_baba GÖMÜLMEZ (§28: kartta yok)
            "yas": r["yas"], "vefat": r["vefat_tarihi"], "gun": g, "et": etiket(g, r["namaz_yeri_vakti"]),
            "defin": r["defin_yeri"], "namaz": r["namaz_yeri_vakti"],
            "disi": (r["il_disi_defin"] or None),
            "cin": cinsiyet_coz(r)}}

o = json.load(open(K/"veri/ordu/son7gun.json"))
_gr = [(k, [r for r in v if not isimsiz_bebek(r)]) for k, v in o["ilceler"].items()] + \
      [("_genel", [r for r in o["ilce_belirsiz"] + o["il_disi"] if not isimsiz_bebek(r)])]
_n_ham = sum(len(v) for _, v in _gr)
_gr, _n_tekil = tekil_et(_gr)
print(f"§32 ikinci kilit: isimsiz bebek elenen {sum(len(v) for v in o['ilceler'].values()) + len(o['ilce_belirsiz']) + len(o['il_disi']) - _n_ham}, tekilleştirilen {_n_tekil}")
ordu = {"il": "Ordu",
        "ilceler": {k: [ilan(r) for r in v] for k, v in _gr[:-1] if v},
        "genel": [ilan(r) for r in _gr[-1][1]]}

# ---- --magaza: kurgusal adlar (Play Store ekran görüntüleri; gerçek kişi/cami/mahalle adı çıkmaz) ----
_ADE = ["Selahattin","Nurettin","Cemalettin","Vehbi","Hamdi","Kemalettin","Sabri","Rüştü","Fehmi","Nuri","Zekeriya","Burhanettin","Şükrü","Remzi","Tevfik","Lütfi"]
_ADK = ["Nurhayat","Gülbeyaz","Hatice Nur","Sevgül","Naciye","Şükriye","Güllü","Rukiye","Nazlı","Hayriye","Zehra Nur","Kıymet","Sakine","Fadime Nur","Hürü","Mükerrem"]
_SOY = ["Sarıbıyık","Köseoğlu","Tunçkol","Gökçeyurt","Altınışık","Karabıçak","Demirbulut","Yalçınkaya","Aksungur","Tuzcuoğlu","Çalışkanel","Bozkurtlar","Kuşçuoğlu","Kazancıgil","Ertaşkın","Dağdelenli","Hacıoğlanlar","Sarıkaya Ünal","Torunoğlu","Gümüşçü","Yenigün","Çakırbaş","Börekçioğlu","Savaşkan"]
_SOY = [x for x in _SOY if " " not in x]
_MAH = ["Cumhuriyet","Yeni","Merkez","Bahçelievler","Çınar","Atatürk","Yeşilyurt","Fatih","Gül","Kuruçeşme"]
_CAMI = ["MERKEZ CAMİİ","YENİ CAMİİ","ÇARŞI CAMİİ","ULU CAMİİ","HACI BAYRAM CAMİİ"]
def _gercek_adlar():
    out = set()
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("ad", "ad_soyad", "isim") and isinstance(v, str): out.add(" ".join(v.split()).lower())
                else: walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for f in sorted(K.glob("veri/**/*.json")):
        if f.name == "son7gun.json" or "kaybettiklerimiz" in f.parts or "tarihte_bugun" in f.parts:
            try: walk(json.load(open(f)))
            except Exception: pass
    return out
_GERCEK = _gercek_adlar()
_GSOY = {n.split()[-1] for n in _GERCEK if n.split()}
_GAD = {n.split()[0] for n in _GERCEK if n.split()}
_SOY = [x for x in _SOY if x.lower() not in _GSOY]
_ADE = [x for x in _ADE if x.lower().split()[0] not in _GSOY]
_ADK = [x for x in _ADK if x.lower().split()[0] not in _GSOY]
_KULLANILAN = []
def _magaza_ad(i, cin):
    kadin = (cin == "k") if cin in ("k", "e") else (i % 2 == 1)
    L = _ADK if kadin else _ADE
    n = f"{L[(i*3) % len(L)]} {_SOY[(i*5+3) % len(_SOY)]}"
    assert n.lower() not in _GERCEK and n.split()[-1].lower() not in _GSOY, n
    _KULLANILAN.append(n); return n
if MAGAZA:
    _i = 0
    for _r in [x for v in ordu["ilceler"].values() for x in v] + ordu["genel"]:
        _r["ad"] = _magaza_ad(_i, _r.get("cin")); _r["mah"] = _MAH[_i % len(_MAH)]
        _r["defin"] = "MERKEZ MEZ."
        _v = _r["namaz"] or ""
        _r["namaz"] = _re.sub(r"-.*$", "-" + _CAMI[_i % len(_CAMI)], _v) if "-" in _v else _v
        _i += 1
    # tarihler kaydırılır: en yeni ilan günü = bugün (mağaza görüntülerinde "Bugün" boş çıkmasın)
    import datetime as _d0
    _tum = [x for v in ordu["ilceler"].values() for x in v] + ordu["genel"]
    _bugun = _d0.datetime.now(_d0.timezone(_d0.timedelta(hours=3))).date()
    _dl = _bugun - max(_d0.date.fromisoformat(x["gun"]) for x in _tum)
    for _r in _tum:
        _r["gun"] = (_d0.date.fromisoformat(_r["gun"]) + _dl).isoformat()
        if _r.get("vefat"): _r["vefat"] = (_d0.date.fromisoformat(_r["vefat"]) + _dl).isoformat()
        _r["et"] = etiket(_r["gun"], _r["namaz"])
ORDU_ILCE = ["Akkuş","Altınordu","Aybastı","Çamaş","Çatalpınar","Çaybaşı","Fatsa","Gölköy","Gülyalı","Gürgentepe",
             "İkizce","Kabadüz","Kabataş","Korgan","Kumru","Mesudiye","Perşembe","Ulubey","Ünye"]
assert set(ordu["ilceler"]) <= set(ORDU_ILCE)
ordu["ilce_listesi"] = ORDU_ILCE
# KİLİT: her kartın üst etiketindeki gün = bulunduğu sekmenin (gruplama) günü; değilse üretim durur
for _r in [x for v in ordu["ilceler"].values() for x in v] + ordu["genel"]:
    assert _r["et"].split(" · ")[1] == tarih_tr(_r["gun"]), ("etiket günü ≠ sekme günü", _r["id"], _r["et"], _r["gun"])

import re
# Kısa tanıtım: meslek + (varsa) neden önemli. Yöntem/kaynak izi taşıyan parçalar ("Vikipedi'de N dilde…") gösterilmez.
def tanitim(x, en_cok=1):
    # sanatçılar: en çok 3 meslek, virgülle, verideki sırayla (en bilinen önce); diğerleri: tek kimlik
    ham = x.get("meslek")
    m = [t.strip() for t in (ham.split(",") if isinstance(ham, str) else [str(t) for t in (ham or [])]) if t and t.strip()]
    m = list(dict.fromkeys(t.lower() for t in m))[:en_cok]
    ms = ", ".join(m)
    ms = ms[:1].upper() + ms[1:] if ms else ""
    parca = []
    for t in re.split(r";|(?<!\d)\.\s+(?=[A-ZÇĞİÖŞÜ])", x.get("neden_onemli") or ""):   # tek cümle: ilk anlamlı parça
        t = re.sub(r"\s*\(.*?\)", "", t).strip(" .")
        if not t or "Vikipedi" in t or re.search(r"\d+ dilde", t) or t.startswith("Ödül"): continue
        t = re.sub(r"^(Görev|Önemli eserleri?):\s*", "", t)
        if t.lower() == ms.lower() or t.lower() in m: continue
        parca.append(t)
    neden = parca[0] if parca else ""
    if not neden and x.get("aciklama_kaynak") == "wikidata_tr":
        a = re.sub(r"\s*\(.*?\)\s*", " ", x.get("aciklama") or "").strip()
        if a and not re.fullmatch(r"Türk (politikacı|siyasetçi)", a): neden = a
    # İKİNCİ KİLİT (site sahibi): "Türk ressam" gibi milliyet sıfatı yazılmaz (yabancılarda kalır; "Türk Telekom" gibi özel ad öbeğine dokunulmaz);
    # tanıtımın ikinci parçası meslek kelimesini tekrar ediyorsa gösterilmez.
    def _turk(t):
        t = t.strip()
        if t.startswith("“"): return t                                   # eser adı: dokunulmaz
        t = re.sub(r"(?<![\wçğıöşü])(?:[A-ZÇĞİÖŞÜ][\wçğıöşü]+-)?Türk[ -](?!Silahlı|Telekom|Hava|Dil|Tarih|Sinema|Giyim|müziği|Halk müziği|Sanat müziği)", "", t)
        t = t.strip(" ,")
        return t[:1].upper() + t[1:] if t else t
    ms, neden = _turk(ms), _turk(neden)
    neden = neden[:1].upper() + neden[1:] if neden else ""
    kok = lambda t: {w.lower()[:5] for w in re.findall(r"[^\W\d_]{4,}", t)}
    if neden and (neden.lower() == ms.lower() or (kok(ms) & kok(neden))): neden = ""
    return " · ".join(t for t in (ms, neden) if t)

def gorev_sirasi(x, k):
    ad = {"cumhurbaskanlari": "Cumhurbaşkanı", "basbakanlar": "Başbakan"}.get(k)
    if not ad: return None
    r = re.search(r"\d+", str(x.get("sira") or ""))
    if not r:
        r = re.search(r"(\d+)\.\s*(?:Türkiye(?: Cumhuriyeti)?'?n?i?n? )?" + ("[Cc]umhurbaşkan" if k == "cumhurbaskanlari" else "[Bb]aşbakan"),
                      (x.get("aciklama") or "") + " " + (x.get("neden_onemli") or ""))
    return f"{int(r.group(1) if r.groups() else r.group(0))}. {ad}" if r else None

def kisi(x, i, k=None):
    yer = x.get("defin_il") or x.get("defin_ulke") or x.get("defin_yeri") or ""
    return {"ad": x["ad"], "v": x["vefat_tarihi"], "y": x.get("vefat_yasi"), "yy": bool(x.get("vefat_yasi_yaklasik")),
            "m": yer, "g": gorev_sirasi(x, k), "tn": tanitim_g(x, k)}

def tanitim_g(x, k):   # görev sırası ayrı satırda gösterildiği için tanıtımda tekrarlanmaz
    t = tanitim(x, 3 if k == "sanatcilar" else 1)
    g = gorev_sirasi(x, k)
    if g:   # tanıtım, üstteki görev satırının kelimelerini tekrar etmez ("2. Cumhurbaşkanı" varsa "Cumhurbaşkanı" yazılmaz)
        gk = {w.lower() for w in re.findall(r"\w+", g) if not w.isdigit()}
        kalan = []
        for p in t.split(" · "):
            if re.match(r"\d+\. (Türkiye )?(Cumhurbaşkanı|[Bb]aşbakanı?)", p): continue
            if any(w.lower().startswith(g_) for w in re.findall(r"\w+", p) for g_ in gk): continue
            kalan.append(p)
        t = " · ".join(kalan)
    return t

# §10: hariç tutulanlar listesi (+ prototip güvencesi: terör örgütü lideri — veri ajanı haric_tutulanlar.json'a ekleyecek)
HARIC = {h["wikidata_id"] for h in json.load(open(K/"okuyucu/haric_tutulanlar.json")) if not h.get("aday")} | {"Q488200"}

def ilk_gorev(x):
    d = x.get("gorev_donemi") or []
    return min((g.get("baslangic") or "9999") for g in d) if d else "9999"

kay = {}
SIYASI = set()
for k in ["cumhurbaskanlari", "basbakanlar", "bakanlar", "siyasetciler"]:
    SIYASI |= {x["wikidata_id"] for x in json.load(open(K/f"veri/kaybettiklerimiz/{k}.json"))}
for k in ["cumhurbaskanlari","basbakanlar","bakanlar","siyasetciler","sanatcilar"]:
    L = [x for x in json.load(open(K/f"veri/kaybettiklerimiz/{k}.json")) if x["wikidata_id"] not in HARIC]
    if k == "sanatcilar":   # ikinci kilit: siyasi listelerdeki kişi sanatçılarda gösterilmez
        L = [x for x in L if x["wikidata_id"] not in SIYASI]
    if k == "sanatcilar":                         # yalnız sanatçılar tanınırlığa göre (Wikidata sitelink); kullanıcıya not gösterilmez
        L = sorted(L, key=lambda x: (-(x.get("sitelink") or x.get("sitelink_sayisi") or 0), x["ad"]))
    else:                                           # cumhurbaşkanları, başbakanlar, bakanlar, siyasetçiler: vefat tarihine göre, yeniden eskiye
        L = sorted(L, key=lambda x: x["vefat_tarihi"] or "", reverse=True)
    kay[k] = [kisi(x, i, k) for i, x in enumerate(L)]
# Üretim günü = Türkiye saatiyle bugün. "Tarihte Bugün": üretim günü + 7 gün ileri gömülür (gerçek uygulama canlı dosyadan okur)
import datetime as _dt, sys as _sys
URETIM = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=3))).date()
tbg = {}
for n in range(8):
    g = URETIM + _dt.timedelta(days=n); ag = f"{g.month:02d}-{g.day:02d}"
    tb = json.load(open(K/f"veri/kaybettiklerimiz/tarihte_bugun/{ag}.json"))
    tb = sorted(tb, key=lambda x: (not x.get("turk"), -(x.get("sitelink") or x.get("sitelink_sayisi") or 0)))
    tbg[ag] = [dict(kisi(x, 0), t=bool(x.get("turk"))) for x in tb]
tbl = tbg[f"{URETIM.month:02d}-{URETIM.day:02d}"]
# Tazelik denetimi: gömülü ilan verisinin en yeni günü üretim gününden 1 günden eskiyse uyar
_gunler = sorted({x["gun"] for v in ordu["ilceler"].values() for x in v} | {x["gun"] for x in ordu["genel"]})
_en_yeni = _dt.date.fromisoformat(_gunler[-1]) if _gunler else None
if not _en_yeni or (URETIM - _en_yeni).days > 1:
    print(f"UYARI: gömülü Ordu verisinin en yeni günü {_en_yeni}, üretim günü {URETIM} — önce: CENAZE_HIZLI=1 python3 okuyucu/hepsi.py ordu", file=_sys.stderr)

if MAGAZA:   # tanınmış kişi adları da kurgusal ad ile değiştirilir; tanıtım/görev satırı kaldırılır
    _j = [0]
    def _anon(L):
        for x in L:
            x["ad"] = _magaza_ad(_j[0] + 5, None); x["tn"] = ""; x["g"] = None; x["m"] = ""; _j[0] += 1
    for _L in kay.values(): _anon(_L)
    for _L in tbg.values(): _anon(_L)
    kay = {k: v[:15] for k, v in kay.items()}; tbg = {k: v[:6] for k, v in tbg.items()}; tbl = tbg[f"{URETIM.month:02d}-{URETIM.day:02d}"]
adlar = json.load(open(T/"adlar.json"))
veri = {"adlar": adlar, "ordu": ordu, "kay": kay, "tb": tbg, "uretim": URETIM.isoformat()}
s = (T/"sablon.html").read_text()
s = s.replace("/*__VERI__*/null", json.dumps(veri, ensure_ascii=False, separators=(",", ":")))
# 15.10.2026 AÇILIŞ EKRANI (sahibi): görsel + âyet + Diyanet meali + motto, 6 sn sonra uygulamaya girer.
# Görsel: tasarim/acilis/secim.txt içindeki dosya adı (varsayılan simge1.png); sahibi adayı seçince o ad yazılır. data: URL olarak gömülür.
import base64 as _b64
_secim = (T/"acilis/secim.txt").read_text().strip() if (T/"acilis/secim.txt").exists() else "simge2.png"
def _veri_url(p):
    return "data:image/png;base64," + _b64.b64encode(p.read_bytes()).decode()
_gorsel = T/"acilis"/_secim
s = s.replace("__ACILIS_GORSEL__", _veri_url(_gorsel) if _gorsel.exists() else "")
# adaylar: ?aday=1|2|3 ile prototipte karşılaştırma (sahibi seçer; seçim acilis/secim.txt'ye yazılır)
_adaylar = {p.stem: _veri_url(p) for p in sorted((T/"acilis").glob("simge*.png"))}
s = s.replace("/*__ACILIS_ADAYLAR__*/null", json.dumps(_adaylar))
(T/OUT).write_text(s)
print("üretim günü", URETIM, "· ilan günleri", _gunler[0], "…", _gunler[-1], "· bugün dolu:", URETIM.isoformat() in _gunler)
print("prototip.html", len(s.encode()), "bayt;", sum(len(v) for v in kay.values()), "kişi;", len(tbl), "tarihte bugün")

# ---- Dualar sekmesi verisi dosyadan (dualar.json; kaynak/doğrulama: DUALAR-KAYNAKLAR.md) — 08.10.2026 eki ----
# Şablondaki örnek DUALAR dizisi dualar.json ile değiştirilir; kartlara konu etiketi süzgeci, merhume sürümü ve not eklenir.
_dj = json.load(open(T/"dualar.json"))
_DUA = [[b["k"], b["ad"], b["ikon"], [{f: x[f] for f in ("b", "ar", "ok", "an", "h", "k", "e", "kadin", "not") if x.get(f)} for x in b["liste"]]]
        for b in _dj["bolumler"]]
_p = (T/OUT).read_text()
_p, _n = re.subn(r"const DUALAR=\[.*?\}\]\]\];", lambda m: "const DUALAR=" + json.dumps(_DUA, ensure_ascii=False, separators=(",", ":")) + ";", _p, count=1, flags=re.S)
assert _n == 1, "sablon.html içinde DUALAR dizisi bulunamadı"
_ETK = json.dumps(_dj["etiketler"], ensure_ascii=False)
_DUA_JS = """<style>
.dua-suz{display:grid;gap:6px;margin:0 0 var(--s3)}
.dua-suz button.tumu{grid-column:1/-1}
.dua-suz button{font:inherit;font-size:13px;line-height:18px;padding:7px 4px;min-width:0;border-radius:999px;border:1px solid var(--cizgi);background:var(--yuzey);color:var(--metin2);cursor:pointer}
.dua-suz button.secili{background:var(--vurgu-zemin);color:var(--vurgu-metin);border-color:var(--vurgu)}
.dua .surum{font-size:13px;line-height:18px;color:var(--metin3);margin-top:var(--s3)}
.dua .hisse{margin-top:var(--s4);padding-top:var(--s3);border-top:1px solid var(--cizgi);text-align:center}
.dua .hisse-et{font-size:11px;line-height:13px;font-weight:600;letter-spacing:.12em;color:var(--metin2)}
.dua .hisse-c{font-size:16px;line-height:24px;font-style:italic;color:var(--vurgu-metin);margin-top:var(--s2)}
.dua .not{font-size:14px;line-height:21px;color:var(--metin2);margin-top:var(--s2)}
</style>
<script>
(()=>{const ETK=__ETK__;let SEC=null,BOL=null;
function kart(x){const cift=!!(x.kadin&&x.kadin.ar);
 return `<article class="kart dua"><h2 class="ad">${esc(x.b)}</h2>`+
  (cift?'<div class="surum">Merhum için</div>':'')+(x.ar?`<div class="arapca">${x.ar}</div>`:'')+(x.ok?`<div class="okunus">${esc(x.ok)}</div>`:'')+
  (cift?`<div class="surum">Merhume için</div><div class="arapca">${x.kadin.ar}</div>${x.kadin.ok?`<div class="okunus">${esc(x.kadin.ok)}</div>`:''}`:'')+
  `<p class="anlam">${esc(x.h?x.an.replace(/\s*Kıssadan hisse:[\s\S]*$/,''):x.an)}</p>`+(x.h?`<div class="hisse"><div class="hisse-et">KISSADAN HİSSE</div><div class="hisse-c">${esc(x.h)}</div></div>`:'')+(x.not?`<p class="not">${esc(x.not)}</p>`:'')+`<div class="kaynak">${esc(x.k)}</div></article>`}
function ciz(){const L=DUALAR.find(x=>x[0]===BOL)[3];
 // basitlik: bölümde en sık geçen en çok 4 konu + Tümü; kalanlar yalnız "Tümü" içinde
 const say={};L.forEach(x=>(x.e||[]).forEach(t=>{if(ETK[t])say[t]=(say[t]||0)+1}));
 const var_=Object.keys(say).sort((a,b)=>say[b]-say[a]||ETK[a].localeCompare(ETK[b],'tr')).slice(0,4);
 // simetri: üstte tam genişlik "Tümü", altında konular eşit sütunlarda (sütun sayısı = konu sayısı)
 const suz=`<div class="dua-suz" style="grid-template-columns:repeat(${Math.max(1,var_.length)},minmax(0,1fr))">`+[['','Tümü'],...var_.map(t=>[t,ETK[t]])].map(([t,a])=>`<button data-etk="${t}" class="${t?'':'tumu '}${(SEC||'')===t?'secili':''}">${esc(a)}</button>`).join('')+`</div>`;
 $('#dua-akis').innerHTML=suz+L.filter(x=>!SEC||(x.e||[]).includes(SEC)).map(kart).join('');}
duaCiz=function(k){BOL=k;SEC=null;$('#dua-ust').textContent=DUA_KISA[k][0];$('#dua-baslik').textContent=DUA_KISA[k][1];ciz();$('#dua-akis').scrollTop=0;};
$('#dua-akis').addEventListener('click',e=>{const b=e.target.closest('[data-etk]');if(!b)return;SEC=b.dataset.etk||null;ciz();});
})();
</script>
""".replace("__ETK__", _ETK)
_p = _p.replace("</body>", _DUA_JS + "</body>", 1)
(T/OUT).write_text(_p)
print("dualar:", " · ".join(f"{b['k']} {len(b['liste'])}" for b in _dj["bolumler"]))

if MAGAZA:   # çerçevesiz tam ekran görünüm (Play ekran görüntüsü için)
    _m = (T/OUT).read_text()
    _m = _m.replace("</body>", "<style>body{background:#25282D!important}.telefon{border-radius:0!important;box-shadow:none!important;transform:none!important}.durum .ada{display:none}</style></body>", 1)
    (T/OUT).write_text(_m)
    print("magaza kipi:", OUT, len(_m.encode()), "bayt")

if MAGAZA:
    _c = [n for n in set(_KULLANILAN) if n.lower() in _GERCEK or n.split()[-1].lower() in _GSOY]
    print(f"çakışma: {len(_c)} / {len(_GERCEK)} gerçek ad (soyad düzeyinde {len(_GSOY)}) · kurgusal ad {len(set(_KULLANILAN))}")
    assert not _c
