#!/usr/bin/env python3
"""Kimin Cenazesi: tek ekranda veri, derleme, site, APK, yerel ve Cloudflare durumu (--veri: yalnız veri)."""
import sys, json, os, re, subprocess, urllib.request, urllib.error
from datetime import datetime, timezone

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(KOK, ".."))
VERI = "https://hllerdgn80-code.github.io/cenaze-veri/veri/"
GH = "https://api.github.com/repos/hllerdgn80-code/cenaze-veri/actions"
HESAP = "ba872dc9ccbc4853f9f06378bc456ab7"
sonuc = {"ok": 0, "hata": 0, "uyari": 0}
bayrak = {}

def yaz(i, m, anahtar=None):
    print(f"{i} {m}")
    sonuc[{"✅": "ok", "❌": "hata", "⚠️": "uyari"}[i]] += 1
    if anahtar:
        bayrak[anahtar] = (i == "✅")

def al(url, yontem="GET", baslik=None, zaman=25):
    r = urllib.request.Request(url, method=yontem, headers={"User-Agent": "durum.py", **(baslik or {})})
    try:
        with urllib.request.urlopen(r, timeout=zaman) as x:
            return x.status, x.read() if yontem == "GET" else b"", dict(x.headers)
    except urllib.error.HTTPError as e:
        return e.code, b"", dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}

def js(url, baslik=None):
    k, g, _ = al(url, baslik=baslik)
    if k != 200:
        return None, k
    try:
        return json.loads(g), k
    except Exception:
        return None, k

def yas(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600

def veri():
    o, k = js(VERI + "ozet.json")
    if o is None:
        yaz("❌", f"ozet.json okunamadı (HTTP {k})", "A"); return
    zam = None
    for a in ("guncelleme", "guncellendi", "updated", "tarih", "uretim"):
        if isinstance(o, dict) and isinstance(o.get(a), str):
            zam = o[a]; break
    iller = o.get("iller") if isinstance(o, dict) else None
    n = len(iller) if isinstance(iller, (list, dict)) else (o.get("il_sayisi") if isinstance(o, dict) else None)
    hatali = []
    if isinstance(iller, dict):
        hatali = [i for i, v in iller.items() if isinstance(v, dict) and (v.get("hata") or v.get("ok") is False)]
    elif isinstance(iller, list):
        hatali = [str(v.get("il", v)) for v in iller if isinstance(v, dict) and (v.get("hata") or v.get("ok") is False)]
    ok = True
    if zam:
        s = yas(zam)
        i = "✅" if s <= 30 else "❌"; ok &= s <= 30
        yaz(i, f"veri güncelleme yaşı: {s:.1f} saat")
    else:
        yaz("⚠️", "ozet.json'da güncelleme zamanı alanı bulunamadı")
    if n is not None:
        i = "✅" if n >= 50 else "❌"; ok &= n >= 50
        yaz(i, f"il sayısı: {n}")
    else:
        yaz("⚠️", "il sayısı okunamadı")
    if hatali:
        yaz("❌", f"hata veren iller ({len(hatali)}): {', '.join(hatali[:15])}")
    s, k = js(VERI + "saglik.json")
    sor = None
    if isinstance(s, dict):
        sor = s.get("sorunlar") or s.get("sorun") or []
    elif isinstance(s, list):
        sor = s
    if sor is None:
        yaz("⚠️", f"saglik.json okunamadı (HTTP {k})")
    else:
        i = "✅" if len(sor) <= 3 else "❌"; ok &= len(sor) <= 3
        yaz(i, f"saglik sorunları: {len(sor)}" + (" — " + "; ".join(str(x)[:60] for x in sor[:3]) if sor else ""))
    d, k = js(VERI + "durum.json")
    if isinstance(d, dict):
        t = next((d[a] for a in ("tarih", "guncelleme", "updated", "son") if a in d), None)
        yaz("✅", f"kaybettiklerimiz durumu tarihi: {t}")
    else:
        yaz("⚠️", "durum.json yok (kaybettiklerimiz tarihi bilinmiyor)")
    bayrak["A"] = ok and hatali == []
    sessiz_kaynaklar()


def sessiz_kaynaklar():
    """Sıfır kaynak bekçisi (okuyucu/kaynak_sayac.py): yerel veri/_kaynak_uyari.json — 2+ tur üst üste 0/HATA veren kaynaklar.
    Dosya '_' ile başlar, yayına gitmez: yalnız toplama yapılan makinede/yerel klasörde bulunur."""
    yol = os.path.join(KOK, "veri", "_kaynak_uyari.json")
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        yaz("⚠️", "sessiz kaynaklar: veri/_kaynak_uyari.json yok (bekçi henüz çalışmadı / veri bu makinede değil)"); return
    s = d.get("sessiz") or []
    if not s:
        yaz("✅", f"sessiz kaynak yok ({d.get('guncelleme')})")
    else:
        yaz("⚠️", f"sessiz kaynaklar ({len(s)}): " + "; ".join(f"{x['kaynak']} ({x['ardisik_tur']} tur: {x['son']})" for x in s[:12]))

def calisma(ad):
    o, k = js(f"{GH}/workflows/{ad}/runs?per_page=1", {"Accept": "application/vnd.github+json"})
    if not o or not o.get("workflow_runs"):
        yaz("⚠️", f"{ad}: çalışma okunamadı (HTTP {k})"); return None
    r = o["workflow_runs"][0]
    return r

def github():
    r = calisma("android.yml")
    if r:
        s = r.get("conclusion") or r.get("status")
        i = "✅" if s == "success" else ("⚠️" if s in ("in_progress", "queued") else "❌")
        yaz(i, f"android.yml: #{r['run_number']} {s} ({yas(r['created_at']):.1f} saat önce, id {r['id']})")
        a, _ = js(f"{GH}/runs/{r['id']}/artifacts", {"Accept": "application/vnd.github+json"})
        adlar = [x["name"] for x in (a or {}).get("artifacts", [])]
        gerek = ["aab", "apk-arm64", "apk-"]
        tam = any("aab" in x for x in adlar) and any("arm64" in x for x in adlar)
        yaz("✅" if tam else "❌", "artifact: " + (", ".join(adlar) if adlar else "yok"))
        bayrak["B"] = (s == "success") and tam
    for ad, sinir in (("topla.yml", 36), ("topla-tr.yml", 36)):
        r = calisma(ad)
        if r:
            s = r.get("conclusion") or r.get("status"); h = yas(r["created_at"])
            ok = s == "success" and h <= sinir
            yaz("✅" if ok else "❌", f"{ad}: {s}, {h:.1f} saat önce" + ("" if h <= sinir else " (36 saatten eski)"))

def site():
    ok = True
    for u, ad in (("https://kimincenazesi.com/", "ana sayfa"), ("https://kimincenazesi.com/gizlilik/", "gizlilik"), ("https://www.kimincenazesi.com/", "www")):
        k, g, _ = al(u)
        yaz("✅" if k == 200 else "❌", f"{ad} {u} → HTTP {k}"); ok &= k == 200
        if u == "https://kimincenazesi.com/" and k == 200:
            m = re.search(r'<[^>]*id="apk"[^>]*>', g.decode("utf8", "replace"))
            if not m:
                yaz("❌", 'ana sayfada id="apk" yok')
            elif re.search(r"\bhidden\b", m.group(0)):
                yaz("✅", 'id="apk" gizli (sahibi kararı 17.10.2026: APK düğmesi açılmayacak)')
            else:
                yaz("✅", 'id="apk" görünür')
    k, _, h = al("https://kimincenazesi.com/indir/kimin-cenazesi.apk", "HEAD")
    cl = h.get("Content-Length") or h.get("content-length")
    yer = os.path.join(KOK, "deploy/play-paket/app-arm64-v8a-release.apk")
    if k != 200:
        yaz("❌", f"APK HEAD → HTTP {k}"); ok = False
    else:
        msg = f"APK 200, content-length {cl}"
        if os.path.exists(yer):
            b = os.path.getsize(yer)
            if str(b) == str(cl):
                yaz("✅", msg + " (yerel arm64 ile eşit)")
            else:
                yaz("❌", msg + f" ≠ yerel {b} (apk_yayinla.sh çalıştır)"); ok = False
        else:
            yaz("✅", msg + " (yerel APK yok, karşılaştırılmadı)")
    bayrak["C"] = ok

def yerel():
    if os.path.exists(os.path.join(KOK, "deploy/imza/yukleme-anahtari.jks")):
        yaz("✅", "imza anahtarı yerelde var")
    else:
        yaz("❌", "imza anahtarı yerelde yok — yedekten geri koy (~/Downloads/yukleme-anahtari.zip)")
    a, b = os.path.join(KOK, "yuklenecek/uygulama"), os.path.join(KOK, "uygulama")
    if not (os.path.isdir(a) and os.path.isdir(b)):
        yaz("⚠️", "yuklenecek/uygulama ya da uygulama klasörü yok"); return
    p = subprocess.run(["diff", "-rq", "-x", ".claude", "-x", ".dart_tool", "-x", "build", a, b], capture_output=True, text=True)   # 17.10: yerel araç klasörleri karşılaştırılmaz
    if p.returncode == 0:
        yaz("✅", "yuklenecek/uygulama = uygulama")
    else:
        yaz("❌", "yuklenecek/uygulama ≠ uygulama: " + "; ".join(p.stdout.strip().splitlines()[:3]))

def cloudflare():
    t = os.path.join(REPO, "haber-motoru/.cf/.wrangler/config/default.toml")
    jeton = None
    if os.path.exists(t):
        m = re.search(r'oauth_token\s*=\s*"([^"]+)"', open(t).read())
        jeton = m and m.group(1)
    if not jeton:
        yaz("⚠️", "Cloudflare belirteci yok, atlandı"); return
    o, k = js(f"https://api.cloudflare.com/client/v4/accounts/{HESAP}/pages/projects/kimincenazesi/domains", {"Authorization": "Bearer " + jeton})
    if not o or not o.get("success"):
        yaz("⚠️", f"Cloudflare alan adı sorgusu başarısız (HTTP {k}; belirteç süresi dolmuş olabilir)"); return
    for d in o.get("result", []):
        yaz("✅" if d.get("status") == "active" else "❌", f"Pages alan adı {d.get('name')}: {d.get('status')}")

def play():
    """Google Play Developer API (10.10.2026): kimlik varsa track durumunu yazar; yoksa kurulumu hatırlatır."""
    sa = os.path.join(KOK, "deploy/.play/service-account.json"); tk = os.path.join(REPO, "haber-motoru/.google/token-play.json")
    if not (os.path.exists(sa) or os.path.exists(tk)):
        yaz("⚠️", "Play API kurulmadı → deploy/PLAY-API-KURULUM.md (sahibinin tek seferlik adımı); o zamana dek Play durumu sahibinden"); return
    p = subprocess.run([sys.executable, os.path.join(KOK, "araclar/play_api.py"), "--durum"], capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        yaz("⚠️", "Play API: " + (p.stderr or p.stdout).strip().splitlines()[0][:150]); return
    for l in p.stdout.splitlines():
        if l.startswith("  ") and ("alpha" in l or "production" in l or "internal" in l):
            yaz("✅", "Play " + l.strip()[:150])

def guvenlik():
    """21.10.2026 guvenlik duvari (madde 10): guvenlik_nobeti.py son sonucunu ve yedek yasini okur; nobet 12 saatten eskiyse yeniden calistirmayi soyler."""
    f = os.path.join(KOK, "deploy/guvenlik-nobeti.json")
    if not os.path.exists(f):
        yaz("⚠️", "güvenlik nöbeti hiç çalışmadı → python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py"); return
    d = json.load(open(f))
    yas_sa = (datetime.now() - datetime.fromisoformat(d["zaman"])).total_seconds() / 3600
    if d.get("bulgu", 0) > 0:
        yaz("❌", f"güvenlik nöbeti: {d['bulgu']} BULGU ({yas_sa:.1f} sa önce): " + "; ".join(d.get("bulgular", [])[:2])[:200])
    elif yas_sa > 12:
        yaz("⚠️", f"güvenlik nöbeti {yas_sa:.0f} saattir çalışmadı (Mac kapalı olabilir) → python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py")
    else:
        yaz("✅", f"güvenlik nöbeti: {d['ok']} OK, 0 bulgu, {d.get('uyari', 0)} uyarı ({yas_sa:.1f} sa önce)")

def main():
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__.strip()); print("Kullanım: durum.py [--veri]"); return
    if "--veri" in sys.argv[1:]:
        veri(); print(f"özet: {sonuc['ok']} ✅ {sonuc['hata']} ❌ {sonuc['uyari']} ⚠️"); return
    for f in (veri, github, site, yerel, cloudflare, play, guvenlik):
        try:
            f()
        except Exception as e:
            yaz("⚠️", f"{f.__name__} bölümü çöktü: {e}")
    asama = "A"
    if bayrak.get("A"):
        asama = "B" if bayrak.get("B") else "A"
        if bayrak.get("B") and bayrak.get("C"):
            asama = "C"
    print(f"özet: {sonuc['ok']} ✅ {sonuc['hata']} ❌ {sonuc['uyari']} ⚠️")
    if asama == "C":
        print("asama: D? (Console'dan bak)")
    else:
        print(f"asama: {asama}")

main()
