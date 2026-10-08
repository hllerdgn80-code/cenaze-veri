"""9 il okuyucusunun (Afyonkarahisar, Aksaray, Bartın, Bilecik, Bolu, Çanakkale, Çankırı, Düzce, Elazığ)
ortak yardımcıları. ortak.py'ye dokunmadan üstüne kurulur; yalnız standart kütüphane (+ Elazığ için sistem curl yedeği)."""
import json, os, re, ssl, subprocess, sys, time, urllib.error, urllib.parse, urllib.request, http.cookiejar, uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_kopru

VERI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri")


def gun_sayisi(varsayilan=7):
    if "--gun" in sys.argv:
        return int(sys.argv[sys.argv.index("--gun") + 1])
    return varsayilan


def gunler(n):
    bugun = date.today()
    return [(bugun - timedelta(days=i)).isoformat() for i in range(n)]


def kayit(kaynak, il, ad, gun, kaynak_ad, kaynak_url, alindi, ek_id="", **alan):
    """Tüm şema alanları None başlar; verilenler yazılır. id = kaynak+ad+gün+ek."""
    k = {a: None for a in ortak.ALANLAR}
    k.update(id=ortak.kayit_id(kaynak, ad, gun, ek_id), il=il, ad_soyad=ad, liste_tarihi=gun,
             kaynak_ad=kaynak_ad, kaynak_url=kaynak_url, alindi=alindi, ham={})
    k.update(alan)
    k.pop("il_disi_defin", None)       # ilce_isle bu iki anahtarı kendisi koyar
    k.pop("ilce_belirsiz", None)
    return k


def metin(s):
    import html
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).replace("\xa0", " ").split())


def ad_duzelt(s):
    return ortak.tr_title(" ".join((s or "").split()))


# ---------------------------------------------------------------- ağ
class Oturum:
    """Çerez saklayan GET/POST (CSRF'li formlar için). Aynı alan adına istekler arası ≥ bekle sn."""
    def __init__(self, bekle=3.5, ssl_baglam=None):
        self.bekle = bekle
        self.cj = http.cookiejar.CookieJar()
        h = [urllib.request.HTTPCookieProcessor(self.cj)]
        if ssl_baglam:
            h.append(urllib.request.HTTPSHandler(context=ssl_baglam))
        self.op = urllib.request.build_opener(*h)

    def _git(self, url, veri=None, basliklar=None):
        host = urllib.parse.urlparse(url).netloc
        gecen = time.time() - ortak._son_istek.get(host, 0)
        if gecen < self.bekle:
            time.sleep(self.bekle - gecen)
        hedef, ek = ortak_kopru.kopru_url(url)
        rq = urllib.request.Request(hedef, data=veri, headers={"User-Agent": ortak.UA, **(basliklar or {}), **ek})
        for deneme in range(3):
            try:
                with self.op.open(rq, timeout=40) as r:
                    ham = r.read()
                    ct = r.headers.get("Content-Type", "")
                break
            except urllib.error.HTTPError:
                raise
            except Exception:
                if deneme == 2:
                    raise
                time.sleep(5)
            finally:
                ortak._son_istek[host] = time.time()
        m = re.search(r"charset=([\w-]+)", ct)
        return ham.decode(m.group(1) if m else "utf-8", "replace")

    def get(self, url, basliklar=None):
        return self._git(url, None, basliklar)

    def post_form(self, url, alanlar, basliklar=None):
        return self._git(url, urllib.parse.urlencode(alanlar).encode(),
                         {"Content-Type": "application/x-www-form-urlencoded", **(basliklar or {})})

    def post_multipart(self, url, alanlar, basliklar=None):
        b = uuid.uuid4().hex
        govde = "".join(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n' for n, v in alanlar.items())
        govde = (govde + f"--{b}--\r\n").encode()
        return self._git(url, govde, {"Content-Type": "multipart/form-data; boundary=" + b, **(basliklar or {})})


def curl_indir(url, bekle=3.5, timeout=40):
    """Python'un TLS yığını (LibreSSL 2.8) sitenin TLS 1.3'ünü konuşamıyorsa sistem curl'ü (doğrulama AÇIK)."""
    host = urllib.parse.urlparse(url).netloc
    gecen = time.time() - ortak._son_istek.get(host, 0)
    if gecen < bekle:
        time.sleep(bekle - gecen)
    try:
        r = subprocess.run(["curl", "-sS", "-f", "--max-time", str(timeout), "-A", ortak.UA, url],
                           capture_output=True, timeout=timeout + 10)
    finally:
        ortak._son_istek[host] = time.time()
    if r.returncode != 0:
        raise RuntimeError("curl " + r.stderr.decode("utf-8", "replace").strip()[:200])
    return r.stdout.decode("utf-8", "replace")


def indir_yedekli(url, **kw):
    """Önce ortak.indir; TLS sürüm uyuşmazlığında curl yedeği."""
    try:
        return ortak.indir(url, **kw)
    except (ssl.SSLError, urllib.error.URLError) as e:
        if isinstance(e, urllib.error.HTTPError):
            raise
        return curl_indir(url, kw.get("bekle", 3.5))


def robots_ok(url, indirici=None):
    """robots.txt kontrolü; indirici verilirse (ör. curl yedekli) onunla. robots yok/HTML ise kural yok sayılır."""
    if indirici is None:
        return ortak.robots_izin(url)
    import urllib.robotparser
    p = urllib.parse.urlparse(url)
    try:
        govde = indirici(f"{p.scheme}://{p.netloc}/robots.txt")
    except Exception:
        return True
    if "<html" in govde[:600].lower() or "user-agent" not in govde.lower():
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(govde.splitlines())
    return rp.can_fetch(ortak.UA, url) and rp.can_fetch("*", url)


# ---------------------------------------------------------------- kayıt biriktirme / yazma
def birlestir(klasor, gun_listesi, yeni_by_gun):
    """Mevcut gün dosyaları + yeni okunanlar (aynı id'de yeni sürüm kazanır). Aynı id başka güne de düşmez."""
    by, gor = {}, set()
    for g in gun_listesi:
        yol = os.path.join(klasor, f"{g}.json")
        d = {}
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                for k in json.load(f).get("kayitlar", []):
                    d[k["id"]] = k
        for k in yeni_by_gun.get(g, []):
            d[k["id"]] = k
        by[g] = [k for i, k in d.items() if i not in gor]
        gor.update(k["id"] for k in by[g])
    return by


def yaz(klasor, il, gun_listesi, by):
    for g in gun_listesi:
        if by.get(g) or os.path.exists(os.path.join(klasor, f"{g}.json")):
            ortak.gun_yaz(klasor, il, g, by.get(g, []))
            print(f"{g}: {len(by.get(g, []))} kayıt")
    silinen = ortak.eski_gunleri_sil(klasor, set(gun_listesi))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(klasor, il, gun_listesi, by)


def pencere_icinde(gun, gun_listesi):
    return gun in set(gun_listesi)


# ---------------------------------------------------------------- serbest metin: "Cenazesi ..." cümlesi
_FIIL = r"(?:defnedilecektir|defnedilecek|toprağa|savunulacaktır|gömülecektir|defin)"


def _dativ(s):
    s = s.strip(" ,.;")
    s = re.sub(r"[’']\s*(?:y?[aeı]|n[aeı])$", "", s)
    s = re.sub(r"(?<=[ıiuü])n[ae]$", "", s)          # mezarlığına -> mezarlığı
    s = re.sub(r"ığa$", "ık", s)
    return s.strip()


def _ablativ(s):
    return re.sub(r"[’']?\s*(?:n?[dt][ae]n)$", "", s.strip(" ,.;")).strip()


def cenaze_cumlesi(s):
    """'Cenazesi bugün X namazından sonra Y Camii'nden kaldırılarak Z Mezarlığı'na defnedilecektir.'
    -> (namaz_yeri_vakti, defin_yeri) ; bulunamayan None."""
    s = " ".join((s or "").split())
    s = re.sub(r"^.*?\bCenazesi\s+", "", s, flags=re.I)
    s = re.sub(r"^(?:bugün|yarın|dün)\s+", "", s, flags=re.I)
    m = re.search(r"\bkaldırılarak,?\s+(.+?)\s+" + _FIIL, s)
    if m:
        defin = _dativ(m.group(1))
        namaz = s[:m.start()].strip(" ,")
        yer = re.search(r"(?:sonra|müteakip)\s+(.+)$", namaz)
        vakit = namaz[:yer.start() + (len("sonra") if yer.group(0).startswith("sonra") else len("müteakip"))] if yer else ""
        namaz = (vakit + " " + _ablativ(yer.group(1))).strip() if yer else _ablativ(namaz)
        return namaz or None, defin or None
    m = re.search(r"\b(?:sonra|müteakip)\s+(.+?)\s+" + _FIIL, s)
    if m:
        namaz = s[:m.start() + len(m.group(0).split()[0])].strip()
        return namaz or None, _dativ(m.group(1)) or None
    m = re.search(r"(.+?)\s+" + _FIIL, s)
    if m:
        return None, _dativ(re.sub(r"^.*?olarak\s+", "", m.group(1))) or None
    return None, None
