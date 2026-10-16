#!/usr/bin/env python3
"""TOPLAYICI -> BOŞALTICI DEVRİ (16.10.2026 H89). topla.yml havuzu (onbellek) kaydettikten sonra çalışır:
  - bosalt.yml son 60 dk içinde BAŞARIYLA bittiyse: yayını ona bırakır (kendin=0) ve onu hemen tetikler (havuz beklemeden boşalsın);
  - bitmediyse ya da API okunamazsa: kendin=1 -> topla.yml yayını kendisi yapar (YEDEK; boşaltıcı bozulsa da uygulama beslenir).
GITHUB_TOKEN ile (GH_TOKEN env; actions: write). Yalnız stdlib; hata kosuyu kirmaz."""
import datetime as dt, json, os, sys, urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "hllerdgn80-code/cenaze-veri")
TOK = os.environ.get("GH_TOKEN", "")


def api(yol, method="GET", govde=None):
    rq = urllib.request.Request(f"https://api.github.com/repos/{REPO}{yol}", method=method,
                                data=json.dumps(govde).encode() if govde is not None else None,
                                headers={"Authorization": "Bearer " + TOK, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(rq, timeout=20) as r:
        b = r.read()
        return json.loads(b) if b else {}


def yaz(k):
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        open(go, "a").write(f"kendin={k}\n")
    print(f"kendin={k}")


def main():
    try:
        son = api("/actions/workflows/bosalt.yml/runs?status=success&per_page=1").get("workflow_runs", [])
        t = dt.datetime.fromisoformat(son[0]["updated_at"].replace("Z", "+00:00")) if son else None
        yas = (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 60 if t else 9999
        print(f"bosalt.yml son basarili: {yas:.0f} dk once")
    except Exception as e:
        print("::warning::bosalt durumu okunamadi, yayini topla yapar:", str(e)[:100]); yaz(1); return
    if yas > 60:
        print("::warning::BOSALTICI 60 dk'dir basarili degil - yayini toplayici yapiyor (yedek)"); yaz(1); return
    try:
        api("/actions/workflows/bosalt.yml/dispatches", "POST", {"ref": os.environ.get("GITHUB_REF_NAME", "main")})
        print("bosalt.yml tetiklendi")
        yaz(0)
    except Exception as e:
        print("::warning::bosalt tetiklenemedi, yayini topla yapar:", str(e)[:100]); yaz(1)


if __name__ == "__main__":
    main()
