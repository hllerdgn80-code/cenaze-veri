"""YEREL SİTELERİN "VEFAT" KATEGORİ SAYFALARI (14.10.2026, H41). ortak_haber.py'ye DOKUNMADAN üstüne kurulur.
Kullanım (il dosyasında):  import ortak_kategori as ok;  ok.kategori("Kars Hakimiyet", "kars-karshakimiyet", "https://www.karshakimiyet.com/vefat-haberleri-24hk.htm", ilce=None)
 tip="baslik"  (varsayılan): kategori sayfası = haber başlıkları listesi (tarih yok). Başlığı vefat kalıbına uyan YENİ bağlantılar için haber
               sayfası açılır (tur başına <= makale_ac, ob bütçesi: site başına günde 40 istek, robots.txt, >=3,5 sn); yayın tarihi sayfadan
               (JSON-LD datePublished / article:published_time / <time datetime>); ad+olgu oh.olgular ile; sonuç olguları veri/<il>/_kategori_olgu.json'da
               saklanır (haber yeniden açılmaz; metin saklanmaz).
 tip="kart"    kategori sayfası = "Ad Soyad + Vefat: GG.AA.YYYY" kartları (mucadelegazetesi.com.tr/vefat): haber açılmaz, 1 istek.
Kategori sayfası 3 saat önbellekte. Ad bulunamazsa kayıt yok. Ölüm nedeni, yakın adı, sitenin cümlesi, telefon, adres SAKLANMAZ."""
import html, json, os, re, sys, time, urllib.parse
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh

ONBELLEK_SN = 3 * 3600
ADAY = re.compile(r"vefat|hayatını\s+kaybet|acı\s+günü|toprağa|defned|cenaze|son\s+yolculu|hakk['’]?a\s+yürü|rahmet|taziye|başsağlığı|yaşamını\s+yitir|ebediyete", re.I)
DEGIL = re.compile(r"anıldı|anılıyor|yıl\s*dönümü|vefatının|şehit|şehadet|ziyaret|ziyaretinde|kaymakam|vali\b|ziyaret|başkan\w*\s+(?:taziye|ziyaret)", re.I)


def _onbellek(ctx, url, sn):
    kl = os.path.join(ctx["klasor"], "_kategori_sayfa")
    os.makedirs(kl, exist_ok=True)
    import hashlib
    yol = os.path.join(kl, hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")
    if os.path.exists(yol) and time.time() - os.path.getmtime(yol) < sn:
        return open(yol, encoding="utf-8").read()
    try:
        x = ob.al(ctx, url)
    except ob.ButceDoldu as e:
        print(f"  {e}", file=sys.stderr)
        ob.durum(ctx).kaydet()
        return open(yol, encoding="utf-8").read() if os.path.exists(yol) else None
    open(yol, "w", encoding="utf-8").write(x)
    ob.durum(ctx).kaydet()
    return x


def baglantilar(sayfa, taban):
    """[(url, baslik)] — yalnız aynı alan adı, başlık metni ya da title/alt'tan; menü bağlantıları ADAY kalıbıyla elenir."""
    out, gor = [], set()
    host = ob.site_anahtari(urllib.parse.urlparse(taban).netloc)
    for m in re.finditer(r"<a\b([^>]*)>([\s\S]*?)</a>", sayfa):
        h = re.search(r'href="([^"#]+)"', m.group(1))
        if not h:
            continue
        u = urllib.parse.urljoin(taban, html.unescape(h.group(1)))
        if ob.site_anahtari(urllib.parse.urlparse(u).netloc) != host or u in gor or u.rstrip("/") == taban.rstrip("/"):
            continue
        t = oi.metin(m.group(2))
        if len(t) < 18:
            a = re.search(r'(?:title|alt)="([^"]{18,200})"', m.group(1) + m.group(2))
            t = html.unescape(a.group(1)) if a else t
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) < 18 or len(t) > 220 or not ADAY.search(t) or DEGIL.search(t):
            continue
        gor.add(u)
        out.append((u, t))
    return out


def yayin_tarihi(sayfa):
    for d in (r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', r'article:published_time"?\s+content="(\d{4}-\d{2}-\d{2})',
              r'content="(\d{4}-\d{2}-\d{2})[^"]*"\s+property="article:published_time', r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})'):
        m = re.search(d, sayfa)
        if m:
            return m.group(1)
    return None


def kategori(ad, slug, url, ilce=None, takma=(), tip="baslik", makale_ac=4):
    """(kaynak adı, işlev) — oi.il_calistir listesine eklenir; il ctx['il']'den."""
    def islev(ctx):
        il = ctx["il"]
        sayfa = _onbellek(ctx, url, ONBELLEK_SN)
        if sayfa is None:
            return []
        gl = set(ctx["gunler"])
        if tip == "kart":
            return _kartlar(ctx, il, slug, ad, url, sayfa, gl, ilce)
        olgu_yol = os.path.join(ctx["klasor"], "_kategori_olgu.json")
        try:
            sakli = json.load(open(olgu_yol, encoding="utf-8"))
        except Exception:
            sakli = {}
        sonuc, acilacak = {}, []
        for u, t in baglantilar(sayfa, url):
            if u in sakli:
                v = sakli[u]
                if (v.get("tarih") or "") in gl:
                    for f in oh._sakli_olgular(v):
                        sonuc[(u, f["ad"])] = oh.kayit_yap(ctx, il, slug, ad, u, f, v["tarih"])
            else:
                acilacak.append((u, t))
        n = 0
        for u, t in acilacak:                                     # sayfadaki sıra = en yeni önce
            if n >= makale_ac:
                break
            try:
                s = ob.al(ctx, u)
            except (ob.ButceDoldu, oi.Engel):
                break
            except Exception as e:
                print(f"  haber açılamadı: {u}: {e}", file=sys.stderr)
                continue
            n += 1
            g = yayin_tarihi(s) or ob.metinden_tarih(oi.metin(s)[:400])
            bulunan = []
            if g and g in gl:
                govde = ob.makale_govdesi(s) or oh._ilk_paragraflar(s, 40)
                h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", s)
                bas = oi.metin(h1.group(1)) if h1 else t
                f = oh.olgular(il, bas, govde[:900], g)
                if f:
                    if not f["ilce"] and ilce:
                        f["ilce"] = ilce
                    bulunan.append(f)
                    sonuc[(u, f["ad"])] = oh.kayit_yap(ctx, il, slug, ad, u, f, g)
            sakli[u] = {"olgular": bulunan, "tarih": g}
        ob.durum(ctx).kaydet()
        sinir = (date.today() - timedelta(days=10)).isoformat()
        sakli = {u: v for u, v in sakli.items() if (v.get("tarih") or "9") >= sinir}
        ortak.json_yaz(olgu_yol, sakli)
        birlesen, _ = ob.gunleri_birlestir(ctx, list(sonuc.values()))
        return birlesen
    return (ad + " (vefat sayfası)", islev)


def _kartlar(ctx, il, slug, ad, url, sayfa, gl, ilce):
    out = []
    for m in re.finditer(r'<a[^>]+href="(/[^"]+)"[^>]*>([\s\S]*?)</a>', sayfa):
        t = oi.metin(m.group(2))
        d = re.search(r"Vefat:?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", t)
        if not d:
            continue
        isim = re.sub(r"\s*Vefat:.*$", "", t).strip()
        try:
            g = date(int(d.group(3)), int(d.group(2)), int(d.group(1))).isoformat()
        except ValueError:
            continue
        if g not in gl or len(isim.split()) < 2 or len(isim) > 40 or re.search(r"\d", isim):
            continue
        u = urllib.parse.urljoin(url, m.group(1))
        k = oi.kayit(il, ilce, slug, ortak.tr_title(isim), g, ad, u, ctx["alindi"], ek_id="", liste_tarihi=g, vefat_tarihi=g,
                     ham={"yayin_tarihi": g, "sayfa_tarihi": g, "tarih_kaynagi": "ilan_vefat_tarihi"})
        k["kaynak_turu"] = oh.KAYNAK_TURU
        if not ilce:
            k["ilce"] = None
            k["ilce_belirsiz"] = True
        out.append(k)
    return out
