#!/usr/bin/env python3
"""[PRO HESABI] GitHub REST API — Kimin Cenazesi deposu (hllerdgn80-code/cenaze-veri), yalnız stdlib; `gh` ve TARAYICI GEREKMEZ.
Belirteç: GITHUB_TOKEN ortam değişkeni ya da cenaze-uygulamasi/.github-token (tek satır). Okuma (--durum) belirteçsiz de çalışır (saatte 60 istek).
Kurulum (sahibi, bir kez): github.com → Settings → Developer settings → Fine-grained tokens → Generate new token →
  Repository access: Only select → cenaze-veri · Permissions: Actions RW, Contents RW, Secrets RW, Workflows RW, Metadata R · süre 1 yıl →
  belirteci kopyala → terminalde:  pbpaste > ~/Desktop/model-arastirmasi/cenaze-uygulamasi/.github-token && chmod 600 ~/Desktop/model-arastirmasi/cenaze-uygulamasi/.github-token
Kullanım:
  python3 araclar/github_api.py --durum [--n 8]                       # iş akışlarının son çalışmaları (ad, durum, sonuç, tarih)
  python3 araclar/github_api.py --calistir kaybettiklerimiz.yml [--ref main] [--girdi ad=deger ...] [--bekle]
                                                                     # workflow_dispatch (YURUT R1 yerine); --bekle: derleme_bekle.py ile izler
  python3 araclar/github_api.py --indir [RUN_ID|son] [--ad aab,apk-arm64]   # artifact zip'leri deploy/indirilen/ içine (YURUT R3 yerine)
        sonra: PAKET_DIZIN=cenaze-uygulamasi/deploy/indirilen bash cenaze-uygulamasi/araclar/paket_ac.sh N
  python3 araclar/github_api.py --yaz YEREL DEPO_YOLU [-m "mesaj"]   # tek dosya commit (contents API)
  python3 araclar/github_api.py --klasor-yukle YEREL_KLASOR DEPO_KLASORU [-m "mesaj"]   # klasörün tamamı TEK commit (git trees API; YURUT R2/H1 yerine)
  python3 araclar/github_api.py --secret AD < deger.txt              # Actions secret yaz: PyNaCl gerekir; yoksa 'sahibi web'den' der.
        İMZA SECRET'LARI (ANDROID_*) DEĞİŞTİRİLMEZ (YURUT §2.2/§7) — araç bu adları reddeder.
  --kuru : belirteç durumu + hedef depo; ağ yok.
Ağ: api.github.com (indirme yönlendirmesi: *.blob.core.windows.net / pipelines.actions.githubusercontent.com)."""
import argparse, base64, http.client, json, os, pathlib, subprocess, sys, time, urllib.error, urllib.request

KOK = pathlib.Path(__file__).resolve().parent.parent
DEPO = "hllerdgn80-code/cenaze-veri"
API = "https://api.github.com/repos/" + DEPO
TOKF = KOK / ".github-token"
TOKF2 = KOK / "deploy" / ".github-token"   # 14.10.2026: sahibine bu yol söylendi; ikisi de kabul
INDIR = KOK / "deploy" / "indirilen"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gizli_tara  # noqa: E402  21.10.2026 guvenlik duvari madde 8: acik depoya sir girmesin


def yukleme_kapisi(cift):
    """cift = [(yerel_dosya, depo_yolu)...]. Yasakli dosya adi ya da icerikte sir deseni varsa HICBIR sey yuklenmeden durur."""
    sorun = []
    for yerel, yol in cift:
        sorun += gizli_tara.yukleme_kapisi(yerel, yol)
    if sorun:
        sys.exit("GIZLI DOSYA KAPISI: depo HERKESE ACIK; yukleme DURDURULDU (%d bulgu):\n  %s\n(Dosya gizli degilse araclar/gizli_tara.py desenini/atlama listesini guncelle; deger yazdirilmaz.)" % (len(sorun), "\n  ".join(sorun[:12])))


KORUNAN = {"ANDROID_KEYSTORE_PASSWORD", "ANDROID_KEY_PASSWORD", "ANDROID_KEY_ALIAS", "ANDROID_KEYSTORE_BASE64"}


def belirtec(zorunlu=True):
    t = os.environ.get("GITHUB_TOKEN") or (TOKF.read_text().strip() if TOKF.exists() else "") or (TOKF2.read_text().strip() if TOKF2.exists() else "")
    if not t and zorunlu:
        sys.exit("HATA: GitHub belirteci yok (%s ya da GITHUB_TOKEN). Kurulum satırı: python3 araclar/github_api.py --help" % TOKF)
    return t


def cagri(url, method="GET", body=None, zorunlu=True, ham=False):
    h = {"User-Agent": "kimin-cenazesi-araclar", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    t = belirtec(zorunlu)
    if t: h["Authorization"] = "Bearer " + t
    if body is not None: body = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(url if url.startswith("http") else API + url, body, h, method=method)
    try:
        for deneme in range(4):          # sandbox proxy'si büyük parçalı yanıtı yarıda kesebiliyor (IncompleteRead) → yeniden dene
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    d = r.read(); return d if ham else (json.loads(d) if d else {})
            except http.client.IncompleteRead:
                if deneme == 3: raise
                time.sleep(2 * (deneme + 1))
    except urllib.error.HTTPError as e:
        s = e.read().decode("utf-8", "replace")[:300]
        ip = {401: " → belirteç geçersiz/süresi dolmuş", 403: " → belirteç izni eksik (Actions/Contents/Secrets RW) ya da hız sınırı",
              404: " → depo/iş akışı adı yanlış ya da belirteç bu depoya erişemiyor"}.get(e.code, "")
        sys.exit("HATA HTTP %s %s%s\n%s" % (e.code, url[-90:], ip, s))


def durum(n):
    r = cagri("/actions/runs?per_page=%d&exclude_pull_requests=true" % n, zorunlu=False)
    for x in r.get("workflow_runs", []):
        print("%-24s #%-5s %-11s %-10s %s  id %s" % (x["name"][:24], x["run_number"], x["status"], x.get("conclusion") or "-", x["created_at"][:16], x["id"]))


def calistir(wf, ref, girdiler, bekle):
    once = time.time()
    cagri("/actions/workflows/%s/dispatches" % wf, "POST", {"ref": ref, "inputs": dict(g.split("=", 1) for g in girdiler)})
    print("Tetiklendi: %s (%s)" % (wf, ref))
    rid = None
    for _ in range(12):
        time.sleep(5)
        r = cagri("/actions/workflows/%s/runs?per_page=3&event=workflow_dispatch" % wf)
        for x in r.get("workflow_runs", []):
            if time.mktime(time.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone >= once - 30:
                rid = x["id"]; break
        if rid: break
    if not rid: print("Çalışma kimliği henüz görünmedi; --durum ile bak."); return
    print("Çalışma: https://github.com/%s/actions/runs/%s" % (DEPO, rid))
    if bekle: izle(rid)


def izle(rid):
    r = cagri("/actions/runs/%s" % rid, zorunlu=False)
    if "android" in (r.get("path") or ""):
        sys.exit(subprocess.call([sys.executable, str(KOK / "araclar" / "derleme_bekle.py"), str(rid)]))
    bas = time.time()
    while r.get("status") != "completed" and time.time() - bas < 1800:
        print("… %s (%d sn)" % (r.get("status"), time.time() - bas), flush=True); time.sleep(20)
        r = cagri("/actions/runs/%s" % rid, zorunlu=False)
    print("%s %s: %s" % ("✅" if r.get("conclusion") == "success" else "❌", r.get("name"), r.get("conclusion")))
    for job in cagri("/actions/runs/%s/jobs" % rid, zorunlu=False).get("jobs", []):
        for s in job.get("steps", []):
            if s.get("conclusion") == "failure": print("❌ başarısız adım: %s → %s" % (job["name"], s["name"]))


def indir(rid, adlar):
    if rid in (None, "son"):
        rid = cagri("/actions/workflows/android.yml/runs?per_page=1&status=success", zorunlu=False)["workflow_runs"][0]["id"]
    ar = cagri("/actions/runs/%s/artifacts" % rid, zorunlu=False).get("artifacts", [])
    INDIR.mkdir(parents=True, exist_ok=True)
    for x in ar:
        if adlar and not any(a in x["name"] for a in adlar): continue
        if x.get("expired"): print("⚠️ süresi dolmuş: %s" % x["name"]); continue
        # 14.10.2026: yönlendirme (Azure blob) Authorization başlığını reddeder → konumu al, başlıksız indir
        class _NoRedir(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        try:
            urllib.request.build_opener(_NoRedir).open(urllib.request.Request(x["archive_download_url"], headers={"Authorization": "Bearer " + belirtec(), "User-Agent": "kc", "Accept": "application/vnd.github+json"}), timeout=60)
            d = cagri(x["archive_download_url"], ham=True)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307):
                d = urllib.request.urlopen(e.headers.get("Location"), timeout=300).read()
            else: raise
        f = INDIR / (x["name"] + ".zip"); f.write_bytes(d)
        print("✅ %s (%.1f MB)" % (f, len(d) / 1e6))
    print("Sonra: PAKET_DIZIN=%s bash %s/araclar/paket_ac.sh <N>" % (INDIR, KOK))


def yaz(yerel, yol, msg):
    yukleme_kapisi([(yerel, yol)])
    p = pathlib.Path(yerel); icerik = base64.b64encode(p.read_bytes()).decode()
    sha = None
    try: sha = cagri("/contents/%s?ref=main" % yol).get("sha")
    except SystemExit as e:
        if "404" not in str(e): raise
    gov = {"message": msg or ("güncelle " + yol), "content": icerik, "branch": "main"}
    if sha: gov["sha"] = sha
    r = cagri("/contents/%s" % yol, "PUT", gov)
    print("✅ commit %s → %s" % (r["commit"]["sha"][:7], yol))


def klasor(yerel, hedef, msg):
    k = pathlib.Path(yerel)
    if not k.is_dir(): sys.exit("HATA: klasör yok: %s" % yerel)
    ref = cagri("/git/ref/heads/main"); taban = ref["object"]["sha"]
    agac_taban = cagri("/git/commits/%s" % taban)["tree"]["sha"]
    ogeler = []
    dosyalar_ = sorted(x for x in k.rglob("*") if x.is_file() and ".DS_Store" not in x.name)
    yukleme_kapisi([(f, (hedef.strip("/") + "/" if hedef.strip("/") else "") + f.relative_to(k).as_posix()) for f in dosyalar_])
    for f in dosyalar_:
        b = cagri("/git/blobs", "POST", {"content": base64.b64encode(f.read_bytes()).decode(), "encoding": "base64"})
        yol = (hedef.strip("/") + "/" if hedef.strip("/") else "") + f.relative_to(k).as_posix()
        ogeler.append({"path": yol, "mode": "100755" if os.access(f, os.X_OK) else "100644", "type": "blob", "sha": b["sha"]})
    agac = cagri("/git/trees", "POST", {"base_tree": agac_taban, "tree": ogeler})
    c = cagri("/git/commits", "POST", {"message": msg or ("yükle " + hedef), "tree": agac["sha"], "parents": [taban]})
    cagri("/git/refs/heads/main", "PATCH", {"sha": c["sha"]})
    print("✅ %d dosya tek commit'te: %s (%s)" % (len(ogeler), c["sha"][:7], hedef))
    print("Not: .github/workflows/ dosyası değiştiyse belirteçte 'Workflows: RW' izni de gerekir.")


def dosyalar(ciftler, msg):
    """YEREL:DEPO_YOLU ... → hepsi TEK commit (git trees). 14.10.2026: web yüklemesinde klasör başına commit gerekiyordu."""
    ref = cagri("/git/ref/heads/main"); taban = ref["object"]["sha"]
    agac_taban = cagri("/git/commits/%s" % taban)["tree"]["sha"]
    ogeler = []
    yukleme_kapisi([(c.split(":", 1)[0], c.split(":", 1)[1].strip("/")) for c in ciftler if ":" in c])
    for c in ciftler:
        yerel, yol = c.split(":", 1); f = pathlib.Path(yerel)
        if not f.is_file(): sys.exit("HATA: dosya yok: %s" % yerel)
        # H74: zsh $ARGS bölünmeyince tüm liste tek depo yoluna dönüşüyordu (Mac runner ENAMETOOLONG)
        if any(ch in yol for ch in "\n\r\t :") or len(yol) > 200:
            sys.exit("HATA: bozuk depo yolu (boşluk/satır/':' ya da çok uzun) — argümanlar bölünmemiş olabilir: %r" % yol[:120])
        b = cagri("/git/blobs", "POST", {"content": base64.b64encode(f.read_bytes()).decode(), "encoding": "base64"})
        ogeler.append({"path": yol.strip("/"), "mode": "100644", "type": "blob", "sha": b["sha"]})
    agac = cagri("/git/trees", "POST", {"base_tree": agac_taban, "tree": ogeler})
    c = cagri("/git/commits", "POST", {"message": msg or "güncelle", "tree": agac["sha"], "parents": [taban]})
    cagri("/git/refs/heads/main", "PATCH", {"sha": c["sha"]})
    print("✅ %d dosya tek commit'te: %s" % (len(ogeler), c["sha"][:7]))
    for o in ogeler: print("   ", o["path"])


def secret(ad):
    if ad in KORUNAN: sys.exit("REDDEDİLDİ: %s imza secret'ı — değiştirilmez (YURUT §2.2/§7)." % ad)
    try:
        from nacl import encoding, public
    except ImportError:
        sys.exit("PyNaCl yok (libsodium şifrelemesi gerekir) → secret'ı sahibi web'den girer: github.com/%s/settings/secrets/actions" % DEPO)
    deger = sys.stdin.read().rstrip("\n")
    pk = cagri("/actions/secrets/public-key")
    kutu = public.SealedBox(public.PublicKey(pk["key"].encode(), encoding.Base64Encoder()))
    sif = base64.b64encode(kutu.encrypt(deger.encode())).decode()
    cagri("/actions/secrets/%s" % ad, "PUT", {"encrypted_value": sif, "key_id": pk["key_id"]})
    print("✅ secret yazıldı: %s" % ad)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="GitHub API — cenaze-veri", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--durum", action="store_true"); ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--calistir", metavar="WF.yml"); ap.add_argument("--ref", default="main"); ap.add_argument("--girdi", nargs="*", default=[])
    ap.add_argument("--bekle", action="store_true"); ap.add_argument("--izle", metavar="RUN_ID")
    ap.add_argument("--indir", nargs="?", const="son", metavar="RUN_ID"); ap.add_argument("--ad", help="virgüllü artifact adı parçaları")
    ap.add_argument("--yaz", nargs=2, metavar=("YEREL", "DEPO_YOLU")); ap.add_argument("--klasor-yukle", nargs=2, metavar=("YEREL", "DEPO_KLASORU"))
    ap.add_argument("-m", dest="msg"); ap.add_argument("--secret", metavar="AD"); ap.add_argument("--kuru", action="store_true")
    ap.add_argument("--dosyalar", nargs="+", metavar="YEREL:DEPO_YOLU", help="birden çok dosya TEK commit")
    a = ap.parse_args()
    if a.kuru:
        print("Depo: %s\nBelirteç: %s" % (DEPO, "VAR" if belirtec(False) else "YOK (%s) — okuma çalışır, yazma/indirme/tetikleme çalışmaz" % TOKF)); sys.exit()
    if a.durum: durum(a.n)
    elif a.calistir: calistir(a.calistir, a.ref, a.girdi, a.bekle)
    elif a.izle: izle(a.izle)
    elif a.indir: indir(a.indir, [x for x in (a.ad or "").split(",") if x])
    elif a.yaz: yaz(a.yaz[0], a.yaz[1], a.msg)
    elif a.klasor_yukle: klasor(a.klasor_yukle[0], a.klasor_yukle[1], a.msg)
    elif a.dosyalar: dosyalar(a.dosyalar, a.msg)
    elif a.secret: secret(a.secret)
    else: ap.print_help()
