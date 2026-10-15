#!/usr/bin/env python3
"""Hangi il/ilçe cenaze listesini günün kaçında giriyor? (15.10.2026) veri/<il>/son7gun.json'daki ilk_gorulme damgalarından,
cenaze günü = ilk görülme günü olan kayıtlar için il bazında ilk/medyan/son görülme saati. Bildirim saati ve sabah tur sıklığı buna göre.
Kullanım: python3 araclar/gorulme_saati.py [veri_klasoru] [--il ordu]"""
import json, os, sys, statistics
from collections import defaultdict

def main():
    kok = next((a for a in sys.argv[1:] if not a.startswith("--") and os.path.isdir(a)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri"))
    il_f = sys.argv[sys.argv.index("--il") + 1] if "--il" in sys.argv else None
    sonuc = {}
    for il in sorted(os.listdir(kok)):
        if il_f and il != il_f:
            continue
        yol = os.path.join(kok, il, "son7gun.json")
        if not os.path.isfile(yol):
            continue
        try:
            d = json.load(open(yol, encoding="utf-8"))
        except Exception:
            continue
        saatler = defaultdict(list)
        for l in list((d.get("ilceler") or {}).values()) + [d.get("il_disi") or [], d.get("ilce_belirsiz") or []]:
            for k in l:
                g = k.get("ilk_gorulme") or ""
                cg = k.get("namaz_tarihi") or (k.get("defin_zamani") or "")[:10]
                if len(g) >= 16 and cg and g[:10] == cg:          # ayni gun girilmis (onceki gun girilenler bekleme deposundan gelir)
                    saatler[k.get("ilce") or "?"].append(int(g[11:13]) * 60 + int(g[14:16]))
        tum = [x for v in saatler.values() for x in v]
        if tum:
            f = lambda m: "%02d:%02d" % (m // 60, m % 60)
            sonuc[il] = {"kayit": len(tum), "ilk": f(min(tum)), "medyan": f(int(statistics.median(tum))), "son": f(max(tum)),
                         "ilceler": {i: f(int(statistics.median(v))) for i, v in sorted(saatler.items())}}
    for il, s in sorted(sonuc.items(), key=lambda x: x[1]["medyan"]):
        print("%-16s %3d kayıt  ilk %s  medyan %s  son %s" % (il, s["kayit"], s["ilk"], s["medyan"], s["son"]))
        if il_f:
            for i, m in s["ilceler"].items():
                print("    %-20s medyan %s" % (i, m))
    if not sonuc:
        print("henüz ilk_gorulme damgalı kayıt yok (damga 15.10.2026'dan itibaren).")

if __name__ == "__main__":
    main()
