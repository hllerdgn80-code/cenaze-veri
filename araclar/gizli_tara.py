#!/usr/bin/env python3
"""Kimin Cenazesi GIZLI DOSYA / SIR TARAMASI (21.10.2026, guvenlik duvari madde 8). Yalniz stdlib.
Neden: GitHub deposu (hllerdgn80-code/cenaze-veri) HERKESE ACIK (github.io yayini). Oraya giren tek bir anahtar/belirtec herkesin olur.
Uc kontrol:
  1) YEREL: gizli dosya adlari (.oauth-gizli, .anahtar, .github-token, *.jks ...) diskte var mi; her biri .gitignore ile kapali mi;
            yerel dosya modu 600/700 mu (gevsekse --duzelt ile sikilastirilir).
  2) UZAK : herkese acik depo agacinda (a) yasakli dosya adi, (b) metin dosyalarinda sir desenleri (AIza, ghp_, github_pat_, PRIVATE KEY,
            GOCSPX, cfut_, re_..., JWT, "anahtar = '...'" gibi), (c) yerelde gizli olan bir yolun uzakta bulunmasi.
  3) GECMIS: yasakli dosya adlari depo gecmisinde hic commit edilmis mi (silinse bile gecmiste kalir).
Kullanim:
  python3 araclar/gizli_tara.py              # hepsi
  python3 araclar/gizli_tara.py --yerel      # yalniz disk
  python3 araclar/gizli_tara.py --uzak       # yalniz acik depo (agac + icerik; ~450 dosya, 1-2 dk)
  python3 araclar/gizli_tara.py --gecmis     # yalniz depo gecmisi
  python3 araclar/gizli_tara.py --klasor site   # bir klasoru (Pages/yukleme) tara: gizli ad ya da sir deseni
  python3 araclar/gizli_tara.py --duzelt     # yerel gizli dosyalarin modunu 600'e (klasorleri 700'e) sikilastir
Cikis kodu 0 = temiz, 1 = en az bir BULGU. Sir degerleri ASLA yazdirilmaz (yalniz dosya yolu + desen adi + satir no)."""
import fnmatch, json, os, pathlib, re, stat, sys, urllib.error, urllib.request

KOK = pathlib.Path(__file__).resolve().parent.parent
DEPO = "hllerdgn80-code/cenaze-veri"
RAW = "https://raw.githubusercontent.com/%s/main/" % DEPO
API = "https://api.github.com/repos/" + DEPO

# Depoya ASLA girmemesi gereken dosya adi desenleri (taban ad ya da yol parcasi)
YASAK_AD = [".oauth-gizli", ".parola-anahtari", ".panel-anahtari", ".resend", ".resend-domain.json", ".anahtar", ".kc-anahtar",
            ".github-token", "api-token", ".env", ".env.*", "*.jks", "*.keystore", "key.properties", "service-account*.json",
            "token-*.json", "*.pem", "*.p12", "*.key", "kc-vpn-telefon.*", "bekci-ping.txt", "id_rsa*", "credentials.json",
            "*.pfx", "google-services.json", "*-token.json", "*.secret", "*.sqlite", "*.sqlite3"]
YASAK_KLASOR = ["deploy/.play", "deploy/imza", ".wrangler", ".cf", ".google", "node_modules"]

SIR_DESENLERI = [
    ("google-api-anahtari", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("github-belirteci", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("github-ince-belirtec", re.compile(r"github_pat_[A-Za-z0-9_]{40,}")),
    ("ozel-anahtar-blogu", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY")),
    ("google-oauth-gizli", re.compile(r"GOCSPX-[A-Za-z0-9_\-]{20,}")),
    ("cloudflare-belirteci", re.compile(r"\bcf(?:ut|at|k)_[A-Za-z0-9]{30,}")),
    ("resend-anahtari", re.compile(r"\bre_[A-Za-z0-9]{20,}_?[A-Za-z0-9]*")),
    ("aws-erisim-anahtari", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-belirteci", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("stripe-canli", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}")),
    ("anthropic-openai-anahtari", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{40,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{12,}\.eyJ[A-Za-z0-9_\-]{12,}\.[A-Za-z0-9_\-]{12,}")),
    ("hizmet-hesabi-json", re.compile(r'"type"\s*:\s*"service_account"')),
    ("ozel-anahtar-alani", re.compile(r'"private_key"\s*:\s*"-----BEGIN')),
    ("atama-ile-sir", re.compile(r"""(?ix)\b(?:secret|token|passw(?:or)?d|passwd|api[_-]?key|apikey|anahtar|parola|sifre|şifre|gizli)[A-Za-z0-9_]*\s*[:=]\s*["']([A-Za-z0-9_\-+/=.]{20,})["']""")),
]
# Atama desenini yanlis pozitiften arindirma: ortam degiskeni, ornek, sablon, gizli-olmayan acik degerler
BOS_DEGER = re.compile(r"(?i)^(test|x{4,}|\*{3,}|your[_-]|example|ornek|degistir|<.+>|\$\{|env\.|process\.|secrets\.|placeholder|todo|changeme|dummy|test[_-]?key)")
METIN_UZANTI = {".py", ".js", ".mjs", ".ts", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".sh", ".html", ".css", ".dart", ".gradle",
                ".kts", ".properties", ".xml", ".plist", ".csv", ".cfg", ".ini", ""}
UZAK_ATLA_ONEK = ("veri/", "veri-tr/")          # toplu veri (kisi adlari; sir degil) — icerik taranmaz
UZAK_ATLA_UZANTI = {".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg", ".apk", ".aab", ".zip", ".gz", ".ttf", ".otf", ".woff", ".woff2", ".mp3", ".mp4"}
YEREL_ATLA = {"flutter-sdk", "node_modules", ".wrangler", ".git", "indirilen", "play-paket", "build", ".dart_tool", "veri", "veri-tr", ".gradle", "Pods"}


def gitignore_desenleri():
    p = KOK / ".gitignore"
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")] if p.exists() else []


def kapali_mi(rel, desenler):
    """Basit .gitignore eslesmesi (dizin '/' sonu, '*' joker, yol ya da taban ad)."""
    ad = rel.rsplit("/", 1)[-1]
    for d in desenler:
        d2 = d.rstrip("/")
        if fnmatch.fnmatch(rel, d2) or fnmatch.fnmatch(ad, d2) or rel == d2 or rel.startswith(d2 + "/"):
            return True
    return False


def sertifika_zinciri_mi(icerik):
    """*.pem / *.key dosyasi YALNIZ ozel anahtar iceriyorsa gizlidir; acik CA zinciri (CERTIFICATE) gizli degildir."""
    return "PRIVATE KEY" not in icerik and "BEGIN CERTIFICATE" in icerik


def yasak_ad_mi(yol, icerik=None):
    ad = yol.rsplit("/", 1)[-1]
    if ad.endswith(".pem") and icerik is not None and sertifika_zinciri_mi(icerik):
        return False
    if any(fnmatch.fnmatch(ad, d) for d in YASAK_AD):
        return True
    return any(yol == k or yol.startswith(k + "/") or ("/" + k + "/") in ("/" + yol) for k in YASAK_KLASOR)


def satir_tara(metin, yol):
    bulgu = []
    test_dosyasi = "/test/" in ("/" + yol) or yol.endswith((".test.js", ".test.py", "_test.dart"))
    for no, satir in enumerate(metin.splitlines(), 1):
        if len(satir) > 4000:
            satir = satir[:4000]
        for ad, rx in SIR_DESENLERI:
            m = rx.search(satir)
            if not m:
                continue
            if ad == "atama-ile-sir":
                if test_dosyasi:
                    continue
                v = m.group(1)
                if BOS_DEGER.match(v) or v.lower() in ("false", "true"):
                    continue
                # tamamen kucuk harf kelime/bosluksuz 'tur adi' gibi gorunenleri ele (gizli degil): rakam/buyuk harf karisimi aranir
                if not (re.search(r"\d", v) and re.search(r"[A-Za-z]", v)):
                    continue
            bulgu.append((yol, no, ad))
    return bulgu


def yerel(duzelt=False):
    sorun, tamam = [], []
    desenler = gitignore_desenleri()
    bulunan = []
    for dp, dn, fn in os.walk(KOK):
        dn[:] = [d for d in dn if d not in YEREL_ATLA]
        for f in fn:
            yol = pathlib.Path(dp) / f
            rel = str(yol.relative_to(KOK))
            ic = None
            if f.endswith(".pem"):
                try: ic = yol.read_text(errors="replace")
                except OSError: ic = None
            if yasak_ad_mi(rel, ic):
                bulunan.append((rel, yol))
        for d in list(dn):
            rel = str((pathlib.Path(dp) / d).relative_to(KOK))
            if rel in YASAK_KLASOR:
                bulunan.append((rel + "/", pathlib.Path(dp) / d))
    for rel, yol in sorted(bulunan):
        kapali = kapali_mi(rel.rstrip("/"), desenler)
        mod = stat.S_IMODE(yol.stat().st_mode)
        gevsek = bool(mod & 0o077)
        durum = "gitignore %s, mod %o" % ("KAPALI" if kapali else "ACIK", mod)
        if not kapali:
            sorun.append("yerel gizli dosya .gitignore ile KAPALI DEGIL: %s (%s)" % (rel, durum))
        elif gevsek and not rel.endswith("/"):
            if duzelt:
                os.chmod(yol, 0o600)
                tamam.append("mod 600'e sikilastirildi: %s (was %o)" % (rel, mod))
            else:
                sorun.append("gizli dosya modu gevsek (%o): %s -> --duzelt" % (mod, rel))
        elif gevsek and rel.endswith("/"):
            if duzelt:
                os.chmod(yol, 0o700)
                tamam.append("klasor modu 700'e sikilastirildi: %s (was %o)" % (rel, mod))
            else:
                sorun.append("gizli klasor modu gevsek (%o): %s -> --duzelt" % (mod, rel))
        else:
            tamam.append("%s: %s" % (rel, durum))
    return sorun, tamam, [r for r, _ in bulunan]


def http_json(url, token=None):
    h = {"User-Agent": "kimin-cenazesi-gizli-tara", "Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.load(r)


def http_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kimin-cenazesi-gizli-tara"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(2_500_000).decode("utf-8", "replace")


def token():
    for p in (KOK / ".github-token", KOK / "deploy" / ".github-token"):
        if p.exists():
            return p.read_text().strip()
    return os.environ.get("GITHUB_TOKEN")


def yerel_sir_degerleri():
    """Yerel gizli dosyalarin DEGERLERI (>=12 karakter, tek satir/kucuk dosya). Acik depoda ayni deger geciyorsa SIZINTI. Degerler ASLA yazdirilmaz."""
    degerler = {}
    for dp, dn, fn in os.walk(KOK):
        dn[:] = [d for d in dn if d not in YEREL_ATLA]
        for f in fn:
            yol = pathlib.Path(dp) / f
            rel = str(yol.relative_to(KOK))
            if not yasak_ad_mi(rel) or f.endswith((".jks", ".zip", ".png", ".keystore", ".sqlite", ".sqlite3", ".pem")):
                continue
            try:
                if yol.stat().st_size > 4096:
                    continue
                t = yol.read_text(errors="replace").strip()
            except OSError:
                continue
            if "\n" not in t and len(t) >= 12 and " " not in t:
                degerler[t] = rel
            else:   # cok satirli: yalniz 'AD = DEGER' / 'AD: DEGER' sag tarafi (karisik harf+rakam, >=12)
                for m in re.finditer(r"(?m)^[^\n=:]{2,60}[=:]\s*([A-Za-z0-9_\-+/=.]{12,})\s*$", t):
                    v = m.group(1)
                    if re.search(r"\d", v) and re.search(r"[A-Za-z]", v):
                        degerler.setdefault(v, rel)
    return degerler


def uzak(yerel_gizli):
    sorun, tamam = [], []
    canary = yerel_sir_degerleri()
    try:
        agac = http_json(API + "/git/trees/main?recursive=1", token())
    except Exception as e:
        return ["uzak depo agaci okunamadi: %s" % str(e)[:80]], []
    blob = [x for x in agac["tree"] if x["type"] == "blob"]
    tamam.append("acik depo: %d dosya, kesik=%s" % (len(blob), agac.get("truncated")))
    for x in blob:
        ic = None
        if x["path"].endswith(".pem"):
            try: ic = http_text(RAW + urllib.request.quote(x["path"]))
            except Exception: ic = None
        if yasak_ad_mi(x["path"], ic):
            sorun.append("ACIK DEPODA yasakli dosya adi: %s" % x["path"])
    for g in yerel_gizli:
        g = g.rstrip("/")
        if any(x["path"] == g or x["path"].startswith(g + "/") for x in blob):
            sorun.append("yerelde GIZLI olan yol acik depoda da var: %s" % g)
    taranan = 0
    hedef = []
    for x in blob:
        p = x["path"]
        if p.startswith(UZAK_ATLA_ONEK):
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext in UZAK_ATLA_UZANTI or (ext not in METIN_UZANTI) or x.get("size", 0) > 2_000_000:
            continue
        hedef.append(p)

    def getir(p):
        for deneme in range(3):
            try:
                return p, http_text(RAW + urllib.request.quote(p)), None
            except Exception as e:
                hata = str(e)[:40]
        return p, None, hata

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as ex:
        sonuclar = list(ex.map(getir, hedef))
    for p, metin, hata in sonuclar:
        if metin is None:
            sorun.append("okunamadi (%s): %s" % (hata, p))
            continue
        taranan += 1
        for v, kaynak in canary.items():
            if v in metin:
                sorun.append("SIZINTI: yerel gizli dosyanin degeri (%s) acik depoda geciyor: %s" % (kaynak, p))
        for yol, no, ad in satir_tara(metin, p):
            sorun.append("sir deseni '%s': %s satir %d" % (ad, yol, no))
    tamam.append("%d metin dosyasinin icerigi sir desenleri + %d yerel sir degeri icin tarandi (veri/ ve veri-tr/ haric)" % (taranan, len(canary)))
    return sorun, tamam


def gecmis():
    sorun, tamam = [], []
    t = token()
    adaylar = ["deploy/test-katil/.oauth-gizli", "deploy/aile-worker/.panel-anahtari", "deploy/aile-worker/.parola-anahtari",
               "deploy/aile-worker/.resend", "deploy/aile-worker/.resend-domain.json", "sunucu/tr-kopru/.anahtar", ".github-token",
               "deploy/.github-token", ".kc-anahtar", "deploy/.play/service-account.json", "deploy/imza/yukleme.jks",
               "deploy/imza/key.properties", "uygulama/android/key.properties"]   # anahtar.dart ATLANDI: depoda bilincli YER TUTUCU (21.10.2026 dogrulandi)
    bakildi = 0
    for p in adaylar:
        try:
            r = http_json(API + "/commits?per_page=1&path=" + urllib.request.quote(p), t)
            bakildi += 1
            if r:
                sorun.append("depo GECMISINDE bu yol commit edilmis (silinse bile gecmiste kalir): %s (ilk bulunan commit %s)" % (p, r[0]["sha"][:8]))
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                sorun.append("GitHub hiz siniri (belirtecsiz 60/saat): gecmis taramasi yarim kaldi (%d/%d yol)" % (bakildi, len(adaylar)))
                break
        except Exception as e:
            sorun.append("gecmis sorgusu basarisiz: %s" % str(e)[:60])
    if not sorun:
        tamam.append("%d gizli yol adayi icin depo gecmisi temiz" % bakildi)
    return sorun, tamam


def yukleme_kapisi(yerel_dosya, depo_yolu):
    """GitHub'a (acik depo) yuklenecek TEK dosya icin son kapi. Sorun varsa aciklama listesi doner (bos = temiz).
    github_api.py yaz/klasor/dosyalar yollarindan cagrilir: yasakli dosya adi ya da icerikte sir deseni varsa yukleme DURUR."""
    p = pathlib.Path(yerel_dosya)
    sorun = []
    ic = None
    ext = p.suffix.lower()
    if ext == ".pem" or ext in METIN_UZANTI:
        try:
            if p.stat().st_size <= 2_000_000:
                ic = p.read_text(errors="replace")
        except OSError:
            ic = None
    if yasak_ad_mi(depo_yolu, ic):
        sorun.append("yasakli dosya adi/klasoru: %s" % depo_yolu)
    if ic is not None and ext in METIN_UZANTI and not depo_yolu.startswith(UZAK_ATLA_ONEK):
        for yol, no, ad in satir_tara(ic, depo_yolu):
            sorun.append("sir deseni '%s': %s satir %d" % (ad, depo_yolu, no))
    return sorun


def klasor_tara(klasor):
    """Pages/baska yayin icin klasor taramasi: gizli ad ya da sir deseni."""
    sorun = []
    k = pathlib.Path(klasor)
    for f in sorted(x for x in k.rglob("*") if x.is_file()):
        sorun += yukleme_kapisi(f, f.relative_to(k).as_posix())
    return sorun


def main():
    a = set(sys.argv[1:])
    if "--klasor" in sys.argv:
        k = sys.argv[sys.argv.index("--klasor") + 1]
        s = klasor_tara(k)
        for x in s: print("BULGU ", x)
        print("ozet: %s klasoru, %d bulgu" % (k, len(s)))
        sys.exit(1 if s else 0)
    hepsi = not (a & {"--yerel", "--uzak", "--gecmis"})
    sorun, tamam, yerel_gizli = [], [], []
    if hepsi or "--yerel" in a or "--uzak" in a:
        s, t, yerel_gizli = yerel("--duzelt" in a)
        if hepsi or "--yerel" in a:
            sorun += s; tamam += t
    if hepsi or "--uzak" in a:
        s, t = uzak(yerel_gizli); sorun += s; tamam += t
    if hepsi or "--gecmis" in a:
        s, t = gecmis(); sorun += s; tamam += t
    for t in tamam:
        print("OK    ", t)
    for s in sorun:
        print("BULGU ", s)
    print("ozet: %d tamam, %d bulgu" % (len(tamam), len(sorun)))
    sys.exit(1 if sorun else 0)


if __name__ == "__main__":
    main()
