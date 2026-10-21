#!/usr/bin/env python3
"""Kimin Cenazesi GUVENLIK NOBETI (21.10.2026, guvenlik duvari maddeleri 9 ve 10). Yalniz stdlib; tarayici YOK.
Canli sistemi dis gozle kontrol eder, alarm uretir:
  A. Basliklar     : site, /test, /indir (HEAD), veri kapisi (gercek anahtarla), aile Worker -> guvenlik basliklari var mi
  B. Gizli uclar   : /test/{sayim,liste,uyeler,grup}, POST /test/toplu, veri kapisi (anahtarsiz), aile /aile/durum|odemeler, kopru -> anahtarsiz 403
  C. Girdi/hata    : aile'ye bozuk JSON (400) ve 5 KB govde (413) -> yanitta iz/stack yok; kotu Origin'e CORS verilmiyor
  D. Robots/DNS/TLS: robots.txt kurallari, SPF var mi, DMARC (bilgi), sertifika bitisine kalan gun
  E. Belirtec/izin : wrangler OAuth gecerli, GitHub belirteci kapsami (yalniz cenaze-veri?) + bitis tarihi, CF api-token aktif/bitis, gizli dosya modlari
  F. Istek patlamasi: Cloudflare GraphQL (zone + Workers): son tam saat, son ~3 gunun saatlik medyaninin >8 kati ve >400 ise ALARM; Worker hata orani; gunluk kota
  G. Yedek yasi    : en yeni KV yedegi <= 36 saat
Cikis: 0 = alarm yok, 1 = en az bir BULGU. Sonuc deploy/guvenlik-nobeti.json (durum.py okur).
Kullanim:
  python3 araclar/guvenlik_nobeti.py                  # hepsi (hizli: ~20 sn)
  python3 araclar/guvenlik_nobeti.py --bildir         # BULGU varsa macOS bildirimi gonderir (Mac tetikleyicisi bunu kullanir)
  python3 araclar/guvenlik_nobeti.py --tam            # + acik depo icerik/gecmis sir taramasi (~2 dk)
  python3 araclar/guvenlik_nobeti.py --sessiz         # yalniz BULGU/UYARI satirlari
  python3 araclar/guvenlik_nobeti.py --genel          # yalniz gizli/yerel dosya gerektirmeyen dis kontroller (A-D); GitHub Actions'ta (guvenlik.yml) bu calisir
  python3 araclar/guvenlik_nobeti.py --esik-test --sessiz   # alarm yolunu dener (patlama esigi 0): BULGU + cikis 1 beklenir; sonuc dosyasi yazilmaz
Kimsenin sirri yazdirilmaz."""
import datetime as dt, json, os, pathlib, socket, ssl, statistics, subprocess, sys, time, urllib.error, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import guvenlik_ortak as o  # noqa: E402

SONUC = o.KOK / "deploy" / "guvenlik-nobeti.json"      # --genel modunda YAZILMAZ (yerel tam nobet sonucunu ezmesin)
SITE = "https://kimincenazesi.com"
AILE = "https://kimincenazesi-aile.tr-kopru.workers.dev"
KOPRU = "https://kopru.whitehallminute.com"
UA = "Mozilla/5.0 KiminCenazesiGuvenlikNobeti/1.0"
sonuclar = []
ESIK_CARPAN, ESIK_MIN = 8, 400      # istek patlamasi esigi: max(CARPAN x medyan, MIN); --esik-test ile alarm yolu denenir


GENEL = False      # --genel (ya da GitHub Actions): gizli/yerel dosya gerektirmeyen dis kontroller; belirtec, analitik, yedek atlanir


def kayit(durum, grup, mesaj):
    if durum == "BULGU" and ("HTTP 0" in mesaj or "baglanti hatasi" in mesaj):
        durum = "UYARI"; mesaj += " [ag hatasi: guvenlik bulgusu sayilmadi]"
    sonuclar.append({"durum": durum, "grup": grup, "mesaj": mesaj})


def istek(url, method="GET", basliklar=None, govde=None, zaman=25):
    """(kod, basliklar{kucuk harf}, govde_bayt) — HTTP hatalari da kod olarak doner; ag hatasinda (0, {}, b'')."""
    h = {"User-Agent": UA}
    h.update(basliklar or {})
    for deneme in range(2):          # gecici ag hatasinda 1 kez daha dene
        req = urllib.request.Request(url, govde, h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=zaman) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, (r.read(200_000) if method != "HEAD" else b"")
        except urllib.error.HTTPError as e:
            try:
                g = e.read(200_000)
            except Exception:
                g = b""
            return e.code, {k.lower(): v for k, v in e.headers.items()}, g
        except Exception:
            time.sleep(3)
    return 0, {}, b""


def basliklar_var(grup, ad, basliklar, beklenen):
    eksik = [b for b in beklenen if b not in basliklar]
    if eksik:
        kayit("BULGU", grup, "%s: eksik guvenlik basligi: %s" % (ad, ", ".join(eksik)))
    else:
        kayit("OK", grup, "%s: %d guvenlik basligi tamam" % (ad, len(beklenen)))


GUV = ["x-content-type-options", "x-frame-options", "strict-transport-security", "content-security-policy"]


def kontrol_basliklar():
    k, b, _ = istek(SITE + "/")
    if k != 200:
        kayit("BULGU", "A", "site ana sayfa HTTP %s" % k)
    else:
        basliklar_var("A", "site /", b, GUV + ["referrer-policy", "permissions-policy"])
    k, b, g = istek(SITE + "/test")
    kayit("OK" if k == 200 and b"Kimin Cenazesi" in g else "BULGU", "A", "/test sayfasi HTTP %s" % k)
    if k == 200:
        basliklar_var("A", "/test", b, GUV + ["referrer-policy"])
    k, b, _ = istek(SITE + "/indir/kimin-cenazesi.apk", "HEAD")
    kayit("OK" if k == 200 else "BULGU", "A", "/indir APK HTTP %s" % k)
    if k == 200:
        basliklar_var("A", "/indir", b, GUV)
    anahtar = (o.KOK / "deploy" / ".kc-anahtar")
    if GENEL:
        pass
    elif anahtar.exists():
        k, b, g = istek("https://veri.kimincenazesi.com/ayarlar.json", basliklar={"X-KC-Anahtar": anahtar.read_text().strip(), "User-Agent": "KiminCenazesi/guvenlik-nobeti"})
        kayit("OK" if k == 200 else "BULGU", "A", "veri kapisi (anahtarla) /ayarlar.json HTTP %s" % k)
        if k == 200:
            basliklar_var("A", "veri kapisi", b, GUV)
    else:
        kayit("UYARI", "A", "deploy/.kc-anahtar yok: veri kapisi olumlu testi atlandi")
    k, b, g = istek(AILE + "/aile/ordu.json")
    kayit("OK" if k == 200 and b'"kayitlar"' in g else "BULGU", "A", "aile Worker /aile/ordu.json HTTP %s" % k)
    if k == 200:
        basliklar_var("A", "aile Worker", b, GUV + ["referrer-policy"])


def kontrol_gizli_uclar():
    for yol in ("/test/sayim", "/test/liste", "/test/uyeler", "/test/grup"):
        k, _, g = istek(SITE + yol)
        kayit("OK" if k in (403, 429) and b"Google" not in g else "BULGU", "B", "%s anahtarsiz -> HTTP %s" % (yol, k))
    k, _, _ = istek(SITE + "/test/toplu", "POST", {"Content-Type": "application/json"}, b'{"epostalar":["a@b.co"]}')
    kayit("OK" if k in (403, 429) else "BULGU", "B", "POST /test/toplu anahtarsiz -> HTTP %s" % k)
    k, _, g = istek("https://veri.kimincenazesi.com/veri/ordu/son7gun.json")
    kayit("OK" if k == 403 and not g else "BULGU", "B", "veri kapisi anahtarsiz -> HTTP %s, govde %d bayt" % (k, len(g)))
    for yol in ("/aile/durum", "/aile/odemeler"):
        k, _, _ = istek(AILE + yol)
        kayit("OK" if k in (403, 429) else "BULGU", "B", "aile %s anahtarsiz -> HTTP %s" % (yol, k))
    k, _, g = istek(KOPRU + "/?u=https://van.bel.tr/")
    kayit("OK" if k == 403 else "BULGU", "B", "kopru anahtarsiz -> HTTP %s" % k)
    k, _, g = istek(KOPRU + "/?u=https://van.bel.tr/", basliklar={"X-Kopru-Anahtar": "yanlis-anahtar"})
    kayit("OK" if k == 403 else "BULGU", "B", "kopru yanlis anahtar -> HTTP %s" % k)


def kontrol_girdi():
    k, b, g = istek(AILE + "/aile/basvur", "POST", {"Content-Type": "application/json"}, b"{bozuk-json")
    izsiz = all(x not in g.lower() for x in (b"stack", b"error:", b"    at ", b"exception"))
    kayit("OK" if k in (400, 429) and izsiz else "BULGU", "C", "aile bozuk JSON -> HTTP %s, ic bilgi yok=%s" % (k, izsiz))
    k, b, g = istek(AILE + "/aile/basvur", "POST", {"Content-Type": "application/json"}, b'{"x":"' + b"a" * 5000 + b'"}')
    kayit("OK" if k in (413, 429) else "BULGU", "C", "aile 5 KB govde -> HTTP %s (413 beklenir)" % k)
    k, b, _ = istek(AILE + "/aile/ordu.json", basliklar={"Origin": "https://kotu-site.example"})
    kayit("OK" if "access-control-allow-origin" not in b else "BULGU", "C", "kotu Origin'e CORS izni verilmiyor (aile)")
    k, b, g = istek(AILE + "/aile/%00%2e%2e/etc")
    kayit("OK" if k in (400, 404, 429) and b"stack" not in g.lower() else "BULGU", "C", "aile garip yol -> HTTP %s" % k)


def kontrol_robots_dns_tls():
    k, _, g = istek(SITE + "/robots.txt")
    t = g.decode("utf-8", "replace")
    kayit("OK" if k == 200 and "Disallow: /test" in t and "Disallow: /aile/" in t else "BULGU", "D", "robots.txt: /test ve /aile/ kapali=%s" % ("Disallow: /test" in t and "Disallow: /aile/" in t))
    def txt(ad):
        k2, _, g2 = istek("https://cloudflare-dns.com/dns-query?name=%s&type=TXT" % ad, basliklar={"Accept": "application/dns-json"})
        try:
            return [a["data"] for a in json.loads(g2).get("Answer", [])]
        except Exception:
            return None
    spf = txt("kimincenazesi.com")
    if spf is None:
        kayit("UYARI", "D", "DNS TXT sorgusu basarisiz")
    else:
        kayit("OK" if any("v=spf1" in x for x in spf) else "BULGU", "D", "SPF kaydi var=%s" % any("v=spf1" in x for x in spf))
    dm = txt("_dmarc.kimincenazesi.com")
    if dm is not None and not any("v=DMARC1" in x for x in dm):
        kayit("UYARI", "D", "DMARC kaydi yok (bilgi): Workspace iptalinden (29.10.2026) sonra p=quarantine eklenecek; simdi Workspace gonderimi hizalanmadigi icin ATLANDI")
    elif dm:
        kayit("OK", "D", "DMARC kaydi var")
    for ad in ("kimincenazesi.com", "veri.kimincenazesi.com"):
        try:
            c = ssl.create_default_context()
            with socket.create_connection((ad, 443), timeout=15) as s, c.wrap_socket(s, server_hostname=ad) as ss:
                bitis = ssl.cert_time_to_seconds(ss.getpeercert()["notAfter"])
            gun = (bitis - time.time()) / 86400
            kayit("OK" if gun > 14 else ("UYARI" if gun > 5 else "BULGU"), "D", "TLS %s: %.0f gun kaldi" % (ad, gun))
        except Exception as e:
            kayit("BULGU", "D", "TLS %s baglanti hatasi: %s" % (ad, str(e)[:60]))


def kontrol_belirtec():
    t = o.cf_belirtec()
    kayit("OK" if t else "BULGU", "E", "wrangler OAuth belirteci gecerli=%s (yoksa sahibi: bash haber-motoru/deploy/login.sh)" % bool(t))
    gt = o.github_belirteci()
    if not gt:
        kayit("UYARI", "E", "GitHub belirteci yok")
    else:
        h = {"Authorization": "Bearer " + gt, "Accept": "application/vnd.github+json", "User-Agent": "kc-nobet"}
        k, b, g = istek("https://api.github.com/repos/hllerdgn80-code/cenaze-veri", basliklar=h)
        if k != 200:
            kayit("BULGU", "E", "GitHub belirteci repo erisimi HTTP %s (suresi dolmus olabilir)" % k)
        else:
            bit = b.get("github-authentication-token-expiration")
            if bit:
                try:
                    gun = (dt.datetime.strptime(bit[:19], "%Y-%m-%d %H:%M:%S") - dt.datetime.utcnow()).days
                    kayit("OK" if gun > 14 else ("UYARI" if gun > 3 else "BULGU"), "E", "GitHub belirteci bitisine %d gun" % gun)
                except Exception:
                    kayit("UYARI", "E", "GitHub belirteci bitis tarihi okunamadi: " + bit[:30])
            else:
                kayit("UYARI", "E", "GitHub belirteci bitis basligi yok (suresiz belirtec?)")
            k2, _, g2 = istek("https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator,organization_member", basliklar=h)
            try:
                depolar = [r["full_name"] for r in json.loads(g2)]
            except Exception:
                depolar = None
            if depolar is None:
                kayit("UYARI", "E", "GitHub belirteci depo listesi okunamadi (HTTP %s; ince taneli belirteclerde olagan)" % k2)
            else:
                kayit("OK" if depolar == ["hllerdgn80-code/cenaze-veri"] else "UYARI", "E", "GitHub belirteci %d depoya erisiyor (en az yetki: yalniz cenaze-veri)" % len(depolar))
    api = o.HABER / ".cf" / "api-token"
    if api.exists():
        k, _, g = istek(o.CF + "/user/tokens/verify", basliklar={"Authorization": "Bearer " + api.read_text().strip()})
        try:
            r = json.loads(g)["result"]
            kayit("OK" if r.get("status") == "active" else "BULGU", "E", "Cloudflare api-token durumu: %s (yalniz DNS/zone okuma kapsami; WAF/Workers yazamaz)" % r.get("status"))
        except Exception:
            kayit("BULGU", "E", "Cloudflare api-token dogrulanamadi HTTP %s" % k)
    try:
        import gizli_tara
        s, tamam, _ = gizli_tara.yerel(False)
        kayit("OK" if not s else "BULGU", "E", "gizli dosyalar: %d tamam, %d sorun%s" % (len(tamam), len(s), (" -> " + s[0][:90]) if s else ""))
    except Exception as e:
        kayit("UYARI", "E", "gizli_tara calismadi: %s" % str(e)[:60])


def saatlik(satirlar):
    return [x["sum"]["requests"] for x in satirlar]


def kontrol_patlama():
    simdi = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    bas = (simdi - dt.timedelta(hours=70)).strftime("%Y-%m-%dT%H:%M:%SZ")   # ucretsiz plan: 1 saatlik gruplar en cok 72 saat
    son = (simdi + dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        d = o.graphql('{ viewer { zones(filter:{zoneTag:"%s"}) { httpRequests1hGroups(limit:300, filter:{datetime_geq:"%s", datetime_leq:"%s"}, orderBy:[datetime_ASC]) { dimensions{datetime} sum{requests threats} } } } }' % (o.ZONE, bas, son))
        g = d["viewer"]["zones"][0]["httpRequests1hGroups"]
        # son TAM saat = simdi - 1 saat
        tam = simdi - dt.timedelta(hours=1)
        key = tam.strftime("%Y-%m-%dT%H:00:00Z")
        deger = {x["dimensions"]["datetime"]: x["sum"] for x in g}
        onceki = [v["requests"] for k, v in deger.items() if k < (simdi - dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:00:00Z")]
        med = statistics.median(onceki) if onceki else 0
        son_saat = deger.get(key, {"requests": 0, "threats": 0})
        esik = max(ESIK_CARPAN * med, ESIK_MIN)
        kayit("OK" if son_saat["requests"] <= esik else "BULGU", "F", "site istek: son tam saat %d (~3 gun saatlik medyan %.0f, esik %.0f)" % (son_saat["requests"], med, esik))
        tehdit = sum(v["threats"] for k, v in deger.items() if k >= (simdi - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:00:00Z"))
        kayit("OK" if tehdit < 100 else "UYARI", "F", "Cloudflare 'tehdit' sayisi (24 sa): %d" % tehdit)
    except Exception as e:
        kayit("UYARI", "F", "zone analitigi okunamadi: %s" % str(e)[:100])
    try:
        d = o.graphql('{ viewer { accounts(filter:{accountTag:"%s"}) { workersInvocationsAdaptive(limit:1000, filter:{datetime_geq:"%s", datetime_leq:"%s"}) { dimensions{scriptName datetimeHour} sum{requests errors} } } } }' % (o.HESAP, bas, son))
        satirlar = d["viewer"]["accounts"][0]["workersInvocationsAdaptive"]
        tam = (simdi - dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:00:00Z")
        esik_k = (simdi - dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:00:00Z")
        gun24 = (simdi - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:00:00Z")
        toplam24 = 0
        for ad in o.WORKERLAR:
            kendi = [x for x in satirlar if x["dimensions"]["scriptName"] == ad]
            by_hour = {}
            for x in kendi:
                h = x["dimensions"]["datetimeHour"]
                by_hour.setdefault(h, [0, 0])
                by_hour[h][0] += x["sum"]["requests"]; by_hour[h][1] += x["sum"]["errors"]
            onc = [v[0] for k, v in by_hour.items() if k < esik_k]
            med = statistics.median(onc) if onc else 0
            sonh = by_hour.get(tam, [0, 0])[0]
            esik = max(ESIK_CARPAN * med, ESIK_MIN)
            kayit("OK" if sonh <= esik else "BULGU", "F", "%s: son tam saat %d istek (medyan %.0f, esik %.0f)" % (ad, sonh, med, esik))
            r24 = sum(v[0] for k, v in by_hour.items() if k >= gun24); e24 = sum(v[1] for k, v in by_hour.items() if k >= gun24)
            toplam24 += r24
            if r24 >= 50 and e24 / r24 > 0.05:
                kayit("BULGU", "F", "%s: 24 saatte hata orani %.1f%% (%d/%d)" % (ad, 100 * e24 / r24, e24, r24))
        kayit("OK" if toplam24 < 50_000 else "UYARI", "F", "Worker toplam istek (24 sa): %d (ucretsiz plan sinirina 100.000 kala)" % toplam24)
    except Exception as e:
        kayit("UYARI", "F", "Worker analitigi okunamadi: %s" % str(e)[:100])


def kontrol_yedek():
    try:
        import kv_yedek
        y = kv_yedek.yas_saat()
        if y is None:
            kayit("BULGU", "G", "KV yedegi hic yok (python3 araclar/kv_yedek.py)")
        else:
            kayit("OK" if y <= 36 else "BULGU", "G", "en yeni KV yedegi %.1f saatlik (<=36 sa)" % y)
    except Exception as e:
        kayit("UYARI", "G", "yedek yasi okunamadi: %s" % str(e)[:60])


def kontrol_tam():
    import gizli_tara
    s, t = gizli_tara.uzak(gizli_tara.yerel(False)[2])
    kayit("OK" if not s else "BULGU", "H", "acik depo sir taramasi: %d bulgu%s" % (len(s), (" -> " + s[0][:100]) if s else ""))
    s, t = gizli_tara.gecmis()
    kayit("OK" if not s else "BULGU", "H", "depo gecmisi gizli dosya taramasi: %d bulgu%s" % (len(s), (" -> " + s[0][:100]) if s else ""))


def main():
    global ESIK_CARPAN, ESIK_MIN, GENEL
    a = set(sys.argv[1:])
    GENEL = "--genel" in a or bool(os.environ.get("GITHUB_ACTIONS"))
    if "--esik-test" in a:      # alarm yolunu dene: esik 0 -> her saat 'patlama' sayilir (sonuc dosyasi YAZILMAZ)
        ESIK_CARPAN, ESIK_MIN = 0, 0
    liste = (kontrol_basliklar, kontrol_gizli_uclar, kontrol_girdi, kontrol_robots_dns_tls) if GENEL else \
            (kontrol_basliklar, kontrol_gizli_uclar, kontrol_girdi, kontrol_robots_dns_tls, kontrol_belirtec, kontrol_patlama, kontrol_yedek)
    for fn in liste + ((kontrol_tam,) if "--tam" in a and not GENEL else ()):
        try:
            fn()
        except Exception as e:
            kayit("UYARI", fn.__name__, "kontrol calismadi: %s" % str(e)[:100])
    bulgu = [s for s in sonuclar if s["durum"] == "BULGU"]
    for s in sonuclar:
        if "--sessiz" in a and s["durum"] == "OK":
            continue
        print("%-6s [%s] %s" % (s["durum"], s["grup"], s["mesaj"]))
    ok = sum(1 for s in sonuclar if s["durum"] == "OK")
    print("ozet: %d OK, %d BULGU, %d UYARI" % (ok, len(bulgu), len(sonuclar) - ok - len(bulgu)))
    try:
        if "--esik-test" in a or GENEL:
            raise OSError("sonuc dosyasi yazilmaz (deneme ya da --genel)")
        SONUC.write_text(json.dumps({"zaman": dt.datetime.now().isoformat(timespec="seconds"), "ok": ok, "bulgu": len(bulgu), "uyari": len(sonuclar) - ok - len(bulgu),
                                     "bulgular": [s["mesaj"] for s in bulgu], "sonuclar": sonuclar}, ensure_ascii=False, indent=1))
        os.chmod(SONUC, 0o600)
    except OSError:
        pass
    if bulgu and "--bildir" in a:
        try:
            subprocess.run(["osascript", "-e", 'display notification "%s" with title "Kimin Cenazesi GUVENLIK ALARMI"' % (str(len(bulgu)) + " bulgu: " + bulgu[0]["mesaj"][:90].replace('"', "'"))], timeout=10)
        except Exception:
            pass
    sys.exit(1 if bulgu else 0)


if __name__ == "__main__":
    main()
