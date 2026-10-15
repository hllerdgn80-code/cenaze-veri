#!/usr/bin/env python3
"""okuyucu/mezarlik_ilce.json uretir (14.10.2026, YURUT.md H37). Girdi: <on_bellek>/<il_slug>.json (Overpass: c=mezarlik merkezleri, b=ilce sinirlari out geom).
Kaynak: (c) OpenStreetMap katkicilari (ODbL). Kullanim: python3 araclar/mezarlik_ilce_uret.py <on_bellek_klasoru>"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okuyucu"))
import ortak
from ortak import katla, il_slug, mezarlik_norm


def halkalar(rel):
    """Iliski uyelerinden kapali dis halkalar (nokta listeleri) kurar."""
    parcalar = [[(p["lat"], p["lon"]) for p in m["geometry"]] for m in rel.get("members", []) if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry")]
    halkalar_, acik = [], [list(p) for p in parcalar if len(p) > 1]
    while acik:
        h = acik.pop()
        degisti = True
        while h[0] != h[-1] and degisti:
            degisti = False
            for i, p in enumerate(acik):
                if p[0] == h[-1]: h += p[1:]
                elif p[-1] == h[-1]: h += p[::-1][1:]
                elif p[-1] == h[0]: h = p[:-1] + h
                elif p[0] == h[0]: h = p[::-1][:-1] + h
                else: continue
                acik.pop(i); degisti = True; break
        if h[0] == h[-1] and len(h) > 3:
            halkalar_.append(h)
    return halkalar_


def icinde(nokta, halka):
    y, x = nokta; ic = False
    for i in range(len(halka) - 1):
        y1, x1 = halka[i]; y2, x2 = halka[i + 1]
        if (x1 > x) != (x2 > x) and y < (y2 - y1) * (x - x1) / (x2 - x1) + y1:
            ic = not ic
    return ic


def ilce_adi(tags, liste):
    for ad in (tags.get("name"), (tags.get("name") or "").replace(" İlçesi", "").replace(" Belediyesi", "")):
        for x in liste:
            if ad and katla(x) == katla(ad):
                return x
    return None


def uret(onbellek):
    ilcelerj = ortak.ilce_verisi()
    tablo = {"_kaynak": "© OpenStreetMap katkıcıları (ODbL)", "_not": "il_slug -> {mezarlik_norm: ilçe | {belirsiz:[ilçeler]}}; _mahalle/_cami: il_slug -> {ad: ilçe}"}
    ist = {}
    for f in sorted(os.listdir(onbellek)):
        if not f.endswith(".json"): continue
        d = json.load(open(os.path.join(onbellek, f), encoding="utf-8"))
        il = d["il"]; liste = ilcelerj.get(il, [])
        poligon = []
        for r in d["b"]:
            ad = ilce_adi(r.get("tags", {}), liste)
            if not ad and katla(r.get("tags", {}).get("name", "")) in ("merkez", katla(il), katla(il) + " merkez"):
                ad = "Merkez"      # H61: ilceler.json'da Merkez YOKSA runtime (ortak.mezarlik_ilce_bul) bu degeri kullanmaz; olmasi 'Merkez ile X' belirsizligini yakalar
            if ad: poligon.append((ad, halkalar(r)))
        say = {}
        for e in d["c"]:
            c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
            if not c: continue
            n = mezarlik_norm(e["tags"]["name"])
            n2 = mezarlik_norm(e["tags"]["name"].replace(il, "", 1)) if katla(e["tags"]["name"]).startswith(katla(il)) else None
            bulunan = {ad for ad, hs in poligon if any(icinde((c["lat"], c["lon"]), h) for h in hs)}
            if len(bulunan) != 1: continue
            for anah in {a for a in (n, n2) if a}:
                say.setdefault(anah, set()).add(next(iter(bulunan)))
        t = {}
        for anah, s in say.items():
            if anah in ("", "yeni", "eski", "koy", "sehir", "merkez", "asri", "aile", "kent", "sehitlik", "sehitligi"): continue   # H61: jenerik ad (her ilde birden cok) tabloya girmez
            t[anah] = next(iter(s)) if len(s) == 1 else {"belirsiz": sorted(s)}
        if t: tablo[il_slug(il)] = dict(sorted(t.items()))
        ist[il_slug(il)] = (len(d["c"]), len(poligon), len(t))
    return tablo, ist


GENEL_KELIME = {"guney", "kale", "bozkurt", "cardak", "merkez"}   # ilce adi gunluk sozcukle ayni: mezarlik adi tek basina ipucu sayilmaz


def ad_icinde_ilce(tablo, canli):
    """Ikinci kaynak: kaynagin defin_yeri metni dogrudan ilce adiyla basliyor ('Mengen Babahizir Koy Mezarligi', 'Kadirli').
    canli: son7gun.json kopyalari klasoru. OSM girdisiyle celisen ad EKLENMEZ. -> eklenen sayisi {il_slug: n}"""
    eklenen = {}
    for f in sorted(os.listdir(canli)):
        if not f.endswith(".json"): continue
        d = json.load(open(os.path.join(canli, f), encoding="utf-8"))
        il = d.get("il"); liste = ortak.ilce_listesi(il)
        kayitlar = list((d.get("ilceler") or {}).get("İlçe belirtilmemiş", [])) + (d.get("ilce_belirsiz") or [])   # yalniz ilcesizler
        for y in {k.get("defin_yeri") for k in kayitlar if k.get("defin_yeri")}:
            # H61: eski 'ilce adiyla basliyor' kurali 'Harran Aile Mezarligi'ni Harran ilcesine bagliyordu (sehir mezarligi); ortak.ilce_adi_metinde kabul bicimleri kullanilir
            ad = ortak.ilce_adi_metinde(il, y)
            if not ad or katla(ad) in GENEL_KELIME: continue
            n = mezarlik_norm(y)
            if not n: continue
            t = tablo.setdefault(il_slug(il), {})
            if n in t and t[n] != ad: continue
            if n not in t:
                t[n] = ad; eklenen[il_slug(il)] = eklenen.get(il_slug(il), 0) + 1
    return eklenen


def canli_buda(tablo, canli):
    """H61: canli yayin verisinde kaynagin KENDI verdigi ilce ile celisen mezarlik anahtarlarini atar (ornek: Kocaeli 'asri' Izmit, kaynak Derince)."""
    atilan = []
    for f in sorted(os.listdir(canli)):
        if not f.endswith(".json"): continue
        try: d = json.load(open(os.path.join(canli, f), encoding="utf-8"))
        except Exception: continue
        t = tablo.get(il_slug(d.get("il", "")))
        if not t: continue
        for ilce, l in (d.get("ilceler") or {}).items():
            if ilce == "İlçe belirtilmemiş": continue
            for k in l:
                if k.get("ilce_kaynagi") or k.get("il_disi_defin") or not k.get("defin_yeri"): continue
                n = mezarlik_norm(k["defin_yeri"])
                v = t.get(n)
                if isinstance(v, str) and v != ilce:
                    atilan.append((il_slug(d["il"]), n, t.pop(n), ilce))
    return atilan


def birlestir(eski, yeni):
    """H61: --birlestir. Eski tablodaki ADLAR korunur; yeni gelenle celisen (farkli ilce) ad 'belirsiz' olur; yeni ad eklenir."""
    for il, d in yeni.items():
        if il.startswith("_"): continue
        e = eski.setdefault(il, {})
        for ad, v in d.items():
            if ad not in e: e[ad] = v; continue
            ov = e[ad]
            a = set(ov["belirsiz"]) if isinstance(ov, dict) else {ov}
            b = set(v["belirsiz"]) if isinstance(v, dict) else {v}
            if a == b: continue
            u = sorted(a | b)
            e[ad] = {"belirsiz": u} if len(u) > 1 else u[0]
        eski[il] = dict(sorted(e.items()))
    return eski


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    t, ist = uret(args[0])
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okuyucu", "mezarlik_ilce.json")
    if len(args) > 1:
        print("ad icinde ilce adi:", ad_icinde_ilce(t, args[1]))
    if "--birlestir" in sys.argv and os.path.isfile(out):
        t = birlestir(json.load(open(out, encoding="utf-8")), t)
        import datetime
        t["_kaynak"] = "© OpenStreetMap katkıcıları (ODbL); son yenileme (H61) %s" % datetime.date.today().isoformat()
    elif len(args) > 1:
        t["_not"] += " Ek kaynak: kaynak defin_yeri metni dogrudan o ilin ilce adiyla basliyorsa (ornek 'Mengen Babahizir Koy Mezarligi')."
    if len(args) > 1:
        print("canli celiski buda:", canli_buda(t, args[1]))
    for k in list(t):
        if not k.startswith("_"): t[k] = dict(sorted(t[k].items()))
    json.dump(t, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for k, v in ist.items(): print(k, "mezarlik/ilce_siniri/tablo:", v)
