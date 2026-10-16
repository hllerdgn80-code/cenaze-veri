#!/usr/bin/env python3
"""RESMÎ MAHALLE -> İLÇE TABLOSU (16.10.2026; sahibi: "bize verilen bilgileri alıp yerleştiririz" — kaynak mahalle veriyorsa ilçesi).
Kaynak: Türkçe Vikipedi "<İl> ilindeki yerleşim yerleri listesi" sayfaları (İçişleri Bakanlığı e-icisleri il bilgilerinden derlenmiş;
'== İlçe ==' başlığı altında '[[Mahalle, İlçe|Mahalle]]'). Bir il içinde birden çok ilçede geçen ad tabloya GİRMEZ (tahmin yok).
Çıktı: okuyucu/mahalle_resmi.json = {"_kaynak": ..., "<il_slug>": {"<mahalle_katla>": "İlçe"}}. Kullanım: python3 araclar/mahalle_resmi_yap.py"""
import json, os, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "okuyucu"))
import ortak

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "okuyucu")
ILCELER = json.load(open(os.path.join(KOK, "ilceler.json"), encoding="utf-8"))


def wiki(baslik):
    for deneme in range(4):
        try:
            return _wiki(baslik)
        except Exception as e:
            print("  yeniden", baslik, str(e)[:60]); time.sleep(10 * (deneme + 1))
    return ""


def _wiki(baslik):
    u = "https://tr.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "parse", "page": baslik, "prop": "wikitext", "format": "json", "formatversion": 2, "redirects": 1})
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "KiminCenazesi/1.0 (veri tablosu; hllerdgn80-code)"}), timeout=60) as r:
        d = json.loads(r.read())
    return (d.get("parse") or {}).get("wikitext") or ""


def main():
    try:
        onceki = json.load(open(os.path.join(KOK, "mahalle_resmi.json"), encoding="utf-8"))
    except Exception:
        onceki = {}
    out = {"_kaynak": "tr.wikipedia '<İl> ilindeki yerleşim yerleri listesi' (İçişleri e-icisleri); 16.10.2026", "_eksik": []}
    for il, ilceler in ILCELER.items():
        if il.startswith("_"):
            continue
        if onceki.get(ortak.il_slug(il)):
            out[ortak.il_slug(il)] = onceki[ortak.il_slug(il)]; continue
        adlar = [f"{il} ilindeki yerleşim yerleri listesi"] + {"İstanbul": ["İstanbul'un mahalleleri"], "Hakkari": ["Hakkâri ilindeki yerleşim yerleri listesi"]}.get(il, [])
        w = ""
        for b in adlar:
            try:
                w = wiki(b)
            except Exception:
                w = ""
            if w:
                break
        time.sleep(3)
        if not w:
            out["_eksik"].append(il); print("YOK", il); continue
        gecerli = {ortak.katla(x): x for x in ilceler}
        sayac = {}
        ilce = None
        for satir in w.splitlines():
            m = re.match(r"^==+\s*(.+?)\s*==+\s*$", satir)
            if m:
                ad = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", m.group(1))
                ilce = gecerli.get(ortak.katla(ad)) or ("Merkez" if ortak.katla(ad) in (ortak.katla(il), ortak.katla(il) + " merkez", "merkez") and "Merkez" in ilceler else None)
                continue
            if not ilce:
                continue
            for hedef, gor in re.findall(r"\*\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", satir):
                ad = (gor or hedef.split(",")[0]).strip()
                ad = re.sub(r"\s*\((?:köy|mahalle|[^)]*)\)\s*$", "", ad)
                k = ortak.katla(ad)
                if not k or k == ortak.katla(ilce):
                    continue
                sayac.setdefault(k, set()).add(ilce)
        tablo = {k: next(iter(v)) for k, v in sayac.items() if len(v) == 1}
        out[ortak.il_slug(il)] = tablo
        print(il, len(tablo), "tekil /", len(sayac))
    json.dump(out, open(os.path.join(KOK, "mahalle_resmi.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print("eksik:", out["_eksik"])


if __name__ == "__main__":
    main()
