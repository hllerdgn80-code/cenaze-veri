#!/usr/bin/env python3
"""Kimin Cenazesi YEDEK (21.10.2026, guvenlik duvari madde 7). Yalniz stdlib; Cloudflare wrangler OAuth + (varsa) GitHub belirteci.
Ne yedekler:
  1) KV 'AILE' (3cc1bbb1...): tum anahtar + deger + metadata -> deploy/yedek/kv-AILE-<tarih>.json.gz   (test uyeleri, gorevli hesaplari, ilanlar)
     'test:yonetici' (Google yenileme belirteci) DEGERI yedege YAZILMAZ (yalnizca anahtar adi); gerekirse /test/yonetici ile yeniden yetkilenir.
  2) Canli Worker kodlari (5 script) -> deploy/yedek/worker-<ad>-<tarih>.txt   (geri donus: bozuk surum yayinlanirsa eski paket)
  3) Acik GitHub deposu (main) tarball -> deploy/yedek/depo-<tarih>.tar.gz   (veri + kod; gecmis GitHub'da zaten durur)
Saklama: KV ve Worker 14 adet, depo 4 adet. Klasor 700, dosyalar 600; .gitignore'da (deploy/yedek/) — HICBIR ZAMAN depoya yuklenmez.
Kullanim:
  python3 araclar/kv_yedek.py                 # hepsi
  python3 araclar/kv_yedek.py --kv            # yalniz KV     (--worker, --depo da ayri ayri)
  python3 araclar/kv_yedek.py --dogrula       # en yeni yedekleri acip anahtar sayisini canli KV ile karsilastirir (yazmaz)
  python3 araclar/kv_yedek.py --yas           # en yeni KV yedeginin yasi (saat); 36 saati asarsa cikis kodu 1
Geri yukleme (KV): yedek JSON'daki her kayit icin `wrangler kv key put --namespace-id <id> <anahtar> <deger>` (kilavuz madde 7)."""
import base64, datetime as dt, gzip, json, os, pathlib, stat, sys, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import guvenlik_ortak as o  # noqa: E402

HARIC_DEGER = {"test:yonetici"}


def klasor():
    o.YEDEK.mkdir(parents=True, exist_ok=True)
    os.chmod(o.YEDEK, 0o700)


def yaz(yol, veri):
    yol.write_bytes(veri)
    os.chmod(yol, 0o600)


def damga():
    return dt.datetime.now().strftime("%Y%m%d-%H%M")


def temizle(onek, uzanti, tut):
    dosyalar = sorted(o.YEDEK.glob(onek + "*" + uzanti))
    for f in dosyalar[:-tut] if len(dosyalar) > tut else []:
        f.unlink()


def kv_anahtarlari(belirtec):
    anahtarlar, imlec = [], ""
    while True:
        r = o.cf_istek("/accounts/%s/storage/kv/namespaces/%s/keys?limit=1000%s" % (o.HESAP, o.KV_AILE, ("&cursor=" + imlec) if imlec else ""), belirtec=belirtec)
        if not r.get("success"):
            raise RuntimeError("KV anahtar listesi: " + str(r.get("errors"))[:150])
        anahtarlar += r["result"]
        imlec = (r.get("result_info") or {}).get("cursor") or ""
        if not imlec:
            return anahtarlar


def kv_yedekle():
    t = o.cf_belirtec()
    anahtarlar = kv_anahtarlari(t)
    kayitlar = {}
    for k in anahtarlar:
        ad = k["name"]
        if ad in HARIC_DEGER:
            kayitlar[ad] = {"deger": None, "not": "deger yedege yazilmaz (gizli)"}
            continue
        d = o.cf_istek("/accounts/%s/storage/kv/namespaces/%s/values/%s" % (o.HESAP, o.KV_AILE, urllib.parse.quote(ad, safe="")), ham=True, belirtec=t)
        try:
            deger = d.decode("utf-8")
            kayit = {"deger": deger}
        except UnicodeDecodeError:
            kayit = {"deger_b64": base64.b64encode(d).decode()}
        if k.get("metadata") is not None:
            kayit["metadata"] = k["metadata"]
        if k.get("expiration"):
            kayit["expiration"] = k["expiration"]
        kayitlar[ad] = kayit
    govde = {"namespace": "AILE", "namespace_id": o.KV_AILE, "alinma": dt.datetime.now().isoformat(timespec="seconds"), "sayi": len(kayitlar), "kayitlar": kayitlar}
    f = o.YEDEK / ("kv-AILE-%s.json.gz" % damga())
    yaz(f, gzip.compress(json.dumps(govde, ensure_ascii=False).encode("utf-8")))
    temizle("kv-AILE-", ".json.gz", 14)
    print("OK    KV AILE: %d anahtar -> %s (%d bayt)" % (len(kayitlar), f.relative_to(o.KOK), f.stat().st_size))
    return len(kayitlar)


def worker_yedekle():
    t = o.cf_belirtec()
    n = 0
    for w in o.WORKERLAR:
        d = o.cf_istek("/accounts/%s/workers/scripts/%s/content/v2" % (o.HESAP, w), ham=True, belirtec=t)
        if not isinstance(d, (bytes, bytearray)) or len(d) < 200:
            print("BULGU %s kodu indirilemedi" % w)
            continue
        f = o.YEDEK / ("worker-%s-%s.txt" % (w, damga()))
        yaz(f, d)
        temizle("worker-%s-" % w, ".txt", 14)
        n += 1
    print("OK    Worker kodlari: %d/%d -> deploy/yedek/worker-*.txt" % (n, len(o.WORKERLAR)))
    return n


def depo_yedekle():
    tok = o.github_belirteci()
    h = {"User-Agent": "kimin-cenazesi-yedek", "Accept": "application/vnd.github+json"}
    if tok:
        h["Authorization"] = "Bearer " + tok

    class _Yonlendirme(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):   # codeload'a Authorization tasinmaz
            yeni = urllib.request.Request(newurl, headers={"User-Agent": "kimin-cenazesi-yedek"})
            return yeni
    acici = urllib.request.build_opener(_Yonlendirme)
    d = acici.open(urllib.request.Request("https://api.github.com/repos/hllerdgn80-code/cenaze-veri/tarball/main", headers=h), timeout=300).read()
    f = o.YEDEK / ("depo-%s.tar.gz" % damga())
    yaz(f, d)
    temizle("depo-", ".tar.gz", 4)
    print("OK    Acik depo tarball -> %s (%.1f MB)" % (f.relative_to(o.KOK), len(d) / 1e6))
    return len(d)


def en_yeni(onek, uzanti):
    d = sorted(o.YEDEK.glob(onek + "*" + uzanti)) if o.YEDEK.exists() else []
    return d[-1] if d else None


def yas_saat():
    f = en_yeni("kv-AILE-", ".json.gz")
    if not f:
        return None
    return (dt.datetime.now().timestamp() - f.stat().st_mtime) / 3600


def dogrula():
    f = en_yeni("kv-AILE-", ".json.gz")
    if not f:
        print("BULGU KV yedegi yok"); return 1
    y = json.loads(gzip.decompress(f.read_bytes()))
    canli = len(kv_anahtarlari(o.cf_belirtec()))
    fark = abs(canli - y["sayi"])
    print("%s KV yedegi %s: yedekte %d, canlida %d anahtar (fark %d; TTL'li kayitlar suresi dolunca azalir)" % ("OK   " if fark <= max(3, canli // 5) else "BULGU", f.name, y["sayi"], canli, fark))
    for onek, uz in (("worker-kimincenazesi-aile-", ".txt"), ("depo-", ".tar.gz")):
        x = en_yeni(onek, uz)
        print("%s %s: %s" % ("OK   " if x else "BULGU", onek, x.name if x else "yok"))
    return 0 if fark <= max(3, canli // 5) else 1


def main():
    a = set(sys.argv[1:])
    if "--yas" in a:
        y = yas_saat()
        if y is None:
            print("BULGU KV yedegi hic yok"); sys.exit(1)
        print("%s en yeni KV yedegi %.1f saatlik" % ("OK   " if y <= 36 else "BULGU", y)); sys.exit(0 if y <= 36 else 1)
    klasor()
    if "--dogrula" in a:
        sys.exit(dogrula())
    hepsi = not (a & {"--kv", "--worker", "--depo"})
    hata = 0
    for secim, fn in (("--kv", kv_yedekle), ("--worker", worker_yedekle), ("--depo", depo_yedekle)):
        if hepsi or secim in a:
            try:
                fn()
            except Exception as e:
                print("BULGU %s basarisiz: %s" % (secim, str(e)[:160])); hata += 1
    sys.exit(1 if hata else 0)


if __name__ == "__main__":
    main()
