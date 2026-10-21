"""Guvenlik duvari araclari icin ortak yardimcilar (21.10.2026). Yalniz stdlib.
Cloudflare: wrangler OAuth belirteci (haber-motoru/.cf/.wrangler/config/default.toml). Kapsami: Workers script/KV/route okuma-yazma + GraphQL analitik
(zone + workers). DNS/WAF/zone ayarlari YOK (haber-motoru/.cf/api-token yalniz DNS duzenler). Sure dolmussa `wrangler whoami` yeniler (YURUT H18)."""
import json, os, pathlib, re, subprocess, sys, time, urllib.error, urllib.request

KOK = pathlib.Path(__file__).resolve().parent.parent            # cenaze-uygulamasi
HABER = KOK.parent / "haber-motoru"
CFD = HABER / ".cf"
TOML = CFD / ".wrangler" / "config" / "default.toml"
HESAP = "ba872dc9ccbc4853f9f06378bc456ab7"
ZONE = "93ffd173d3c7b591d521e1d6f59a70e3"                      # kimincenazesi.com
KV_AILE = "3cc1bbb1855648208fa5c40ddaf8368f"
WORKERLAR = ["kimincenazesi-aile", "kimincenazesi-indir", "kimincenazesi-test-katil", "kimincenazesi-veri-kapisi", "tr-kopru"]
CF = "https://api.cloudflare.com/client/v4"
YEDEK = KOK / "deploy" / "yedek"


def _oauth():
    if not TOML.exists():
        return None, 0
    s = TOML.read_text()
    m = re.search(r'oauth_token\s*=\s*"([^"]+)"', s)
    e = re.search(r'expiration_time\s*=\s*"([^"]+)"', s)
    bitis = (time.mktime(time.strptime(e.group(1)[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone) if e else 0
    return (m.group(1) if m else None), bitis


def cf_belirtec():
    """Gecerli wrangler OAuth belirteci; suresi dolmussa wrangler whoami ile yeniler. Yoksa None."""
    t, bitis = _oauth()
    if t and bitis > time.time() + 60:
        return t
    w = HABER / "tools" / "deploy" / "node_modules" / ".bin" / "wrangler"
    env = dict(os.environ, PATH=str(HABER / "tools" / "node" / "bin") + ":" + os.environ.get("PATH", ""), XDG_CONFIG_HOME=str(CFD), WRANGLER_SEND_METRICS="false", CI="1")
    try:
        subprocess.run([str(w), "whoami"], cwd=str(HABER / "tools" / "deploy"), env=env, capture_output=True, timeout=120)
    except Exception:
        return None
    t, bitis = _oauth()
    return t if t and bitis > time.time() + 30 else None


def cf_istek(yol, method="GET", govde=None, ham=False, belirtec=None):
    t = belirtec or cf_belirtec()
    if not t:
        raise RuntimeError("Cloudflare OAuth belirteci yok/yenilenemedi (sahibi: bash haber-motoru/deploy/login.sh)")
    h = {"Authorization": "Bearer " + t}
    if govde is not None:
        govde = json.dumps(govde).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(CF + yol, govde, h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = r.read()
            return d if ham else json.loads(d)
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"success": False, "errors": [{"code": e.code, "message": "HTTP %s" % e.code}]}


def graphql(sorgu):
    r = cf_istek("/graphql", "POST", {"query": sorgu})
    if r.get("errors"):
        raise RuntimeError("GraphQL: " + str(r["errors"])[:200])
    return r["data"]


def github_belirteci():
    for p in (KOK / ".github-token", KOK / "deploy" / ".github-token"):
        if p.exists():
            return p.read_text().strip()
    return os.environ.get("GITHUB_TOKEN")
