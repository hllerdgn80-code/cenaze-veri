#!/usr/bin/env python3
"""veri/<il>/_ulusal.json (vefatilan.py çıktısı) kayıtlarını veri/<il>/son7gun.json'a katar (14.10.2026).
Sıra: gruplar birleştirildikten SONRA, kapi.py'den ÖNCE (topla.yml 'birlestir'). Yinelenen kişiyi eklemez (aynı il, aynı ad, ±2 gün);
kaynakta ilçe varsa o ilçenin altına, yoksa ilce_belirsiz'e. Yalnız eksik kişiler eklenir: mevcut resmî/yerel kayıt zenginse (mahalle, namaz yeri...) korunur.
Kullanım: python3 okuyucu/ulusal_birlestir.py [veri_klasoru]"""
import json, os, re, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

_TR = str.maketrans("çğıöşüÇĞİÖŞÜI", "cgiosucgiosuı")


def kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def gun(s):
    try:
        return datetime.strptime((s or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def tarihler(k):
    t = [gun(k.get(a)) for a in ("vefat_tarihi", "namaz_tarihi", "liste_tarihi")] + [gun((k.get("defin_zamani") or "")[:10])]
    return [x for x in t if x]


def ayni(a, b):
    if kat(a.get("ad_soyad")) != kat(b.get("ad_soyad")):
        return False
    try:
        if a.get("yas") is not None and b.get("yas") is not None and abs(int(a["yas"]) - int(b["yas"])) > 1:
            return False
    except (TypeError, ValueError):
        pass
    return any(abs((x - y).days) <= 2 for x in tarihler(a) for y in tarihler(b))


def main():
    kok = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri")
    eklenen = {}
    for il in sorted(os.listdir(kok)):
        yol = os.path.join(kok, il)
        ul = os.path.join(yol, "_ulusal.json")
        if not os.path.isfile(ul):
            continue
        try:
            yeni = json.load(open(ul, encoding="utf-8")).get("kayitlar", [])
        except Exception:
            continue
        son = os.path.join(yol, "son7gun.json")
        try:
            d = json.load(open(son, encoding="utf-8"))
        except Exception:
            d = {"il": yeni[0].get("il") if yeni else il, "ilceler": {}, "il_disi": [], "ilce_belirsiz": [], "toplam": 0}
        mevcut = [k for l in (d.get("ilceler") or {}).values() for k in l] + (d.get("il_disi") or []) + (d.get("ilce_belirsiz") or [])
        n = 0
        for r in yeni:
            if any(ayni(r, m) for m in mevcut):
                continue
            mevcut.append(r)
            if r.get("ilce") and not r.get("ilce_belirsiz"):
                d.setdefault("ilceler", {}).setdefault(r["ilce"], []).append(r)
            else:
                d.setdefault("ilce_belirsiz", []).append(r)
            n += 1
        if n:
            d["toplam"] = len(mevcut)
            d["guncelleme"] = ortak.simdi_iso()
            ortak.json_yaz(son, d)
            eklenen[il] = n
    print(f"ulusal birleştirme: {sum(eklenen.values())} kayıt, {len(eklenen)} il", dict(sorted(eklenen.items(), key=lambda x: -x[1])[:10]))


if __name__ == "__main__":
    main()
