#!/usr/bin/env python3
"""MAC AÇILINCA TUR (sahibi 16.10.2026: "saate bağlı değil, Mac'i açtığımda başlasın").
LaunchAgent (sunucu/mac-tetik.plist) bu betiği oturum açılışında ve sonra her 10 dakikada bir çalıştırır. Betik:
  - Mac uyanık ve ağ varsa, "Turkiye'den oku" (topla-tr.yml) için son 2 saatte koşu (kuyrukta/çalışan/bitmiş) yoksa workflow_dispatch gönderir;
  - böylece Mac açılır açılmaz tur başlar, açık kaldığı sürece en çok 2 saatte bir yenilenir (sahibi 16.10: 2 sa); sunucudaki saatli tetikleyici (06:41/10:41/14:41/18:41)
    ve bekçi aynen sürer (koşu varsa ikisi de atlar — çift tur yok).
  - Belirteç: cenaze-uygulamasi/deploy/.github-token (github_api.py ile aynı). Log: araclar/mac_tetik.log (son 200 satır tutulur). Yalnız stdlib.
Elle deneme: python3 araclar/mac_tetik.py --kuru"""
import datetime as dt, json, os, sys, urllib.request

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "araclar"))
import github_api as g  # noqa: E402

WF = "topla-tr.yml"
ARALIK_SAAT = 2
LOG = os.path.join(KOK, "araclar", "mac_tetik.log")


def yaz(satir):
    s = "%s | %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), satir)
    print(s)
    try:
        eski = open(LOG, encoding="utf-8").read().splitlines() if os.path.exists(LOG) else []
        open(LOG, "w", encoding="utf-8").write("\n".join((eski + [s])[-200:]) + "\n")
    except OSError:
        pass


def tetik():
    kuru = "--kuru" in sys.argv
    try:
        r = g.cagri("/actions/workflows/%s/runs?per_page=5" % WF)
    except SystemExit as e:
        yaz("HATA: GitHub'a ulaşılamadı (%s)" % str(e)[:80]); return
    except Exception as e:  # ağ yok (uyandı ama Wi-Fi henüz bağlanmadı) -> 10 dk sonra yeniden
        yaz("ağ yok: %s" % str(e)[:80]); return
    kosular = r.get("workflow_runs", [])
    aktif = [k for k in kosular if k.get("status") in ("queued", "in_progress", "waiting", "pending")]
    if aktif:
        yaz("ATLANDI: koşu zaten var (#%s %s)" % (aktif[0]["run_number"], aktif[0]["status"])); return
    simdi = dt.datetime.now(dt.timezone.utc)
    son = None
    for k in kosular:
        t = dt.datetime.strptime(k["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        if son is None or t > son:
            son = t
    if son and simdi - son < dt.timedelta(hours=ARALIK_SAAT):
        yaz("ATLANDI: son koşu %.0f dk önce (<%d sa)" % ((simdi - son).total_seconds() / 60, ARALIK_SAAT)); return
    if kuru:
        yaz("KURU: tetiklenirdi (son koşu: %s)" % (son.isoformat() if son else "yok")); return
    try:
        g.cagri("/actions/workflows/%s/dispatches" % WF, "POST", {"ref": "main"})
        yaz("TETİKLENDİ: %s (Mac açık; son koşu %s)" % (WF, son.isoformat() if son else "yok"))
    except SystemExit as e:
        yaz("HATA: tetikleme (%s)" % str(e)[:80])


# ---- 21.10.2026 GUVENLIK DUVARI (madde 7 + 10): Mac acikken kendiliginden guvenlik nobeti (3 saatte bir), yedek + tam tarama (gunde 1) ----
# Durum: araclar/.guvenlik-durum.json (zaman damgalari). BULGU varsa macOS bildirimi (guvenlik_nobeti.py --bildir). Ag/arac hatasi sessiz gecilir.
import subprocess  # noqa: E402
GDURUM = os.path.join(KOK, "araclar", ".guvenlik-durum.json")


def guvenlik_turu():
    simdi = dt.datetime.now(dt.timezone.utc).timestamp()
    try:
        d = json.load(open(GDURUM))
    except Exception:
        d = {}
    py = sys.executable or "python3"
    araclar = os.path.join(KOK, "araclar")

    def calistir(ad, args, zaman):
        if not os.path.exists(os.path.join(araclar, ad)):      # LaunchAgent kopyasi (~/actions-runner/mac-tetik) yalniz mac_tetik+github_api tasir: sessizce atla
            return None
        try:
            r = subprocess.run([py, os.path.join(araclar, ad)] + args, capture_output=True, text=True, timeout=zaman)
            yaz("GUVENLIK %s %s -> cikis %s%s" % (ad, " ".join(args), r.returncode, (" | " + r.stdout.strip().splitlines()[-1][:120]) if r.stdout.strip() else ""))
            return r.returncode
        except Exception as e:
            yaz("GUVENLIK %s calismadi: %s" % (ad, str(e)[:80])); return None

    if simdi - d.get("son_yedek", 0) > 24 * 3600:
        calistir("kv_yedek.py", [], 600)
        d["son_yedek"] = simdi
    if simdi - d.get("son_tam", 0) > 24 * 3600:
        calistir("guvenlik_nobeti.py", ["--tam", "--bildir", "--sessiz"], 1200)
        d["son_tam"] = d["son_nobet"] = simdi
    elif simdi - d.get("son_nobet", 0) > 3 * 3600:
        calistir("guvenlik_nobeti.py", ["--bildir", "--sessiz"], 600)
        d["son_nobet"] = simdi
    try:
        json.dump(d, open(GDURUM, "w"))
    except OSError:
        pass


def main():
    tetik()
    if "--kuru" not in sys.argv:
        try:
            guvenlik_turu()
        except Exception as e:
            yaz("GUVENLIK turu hata: %s" % str(e)[:80])


if __name__ == "__main__":
    main()
