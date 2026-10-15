#!/usr/bin/env python3
"""okuyucu/mahalle_ilce.json uretir (15.10.2026, YURUT.md H61). Girdi: <onbellek>/<il_slug>.json (araclar/osm_yer_cek.py: p = yerlesim adlari, b = ilce sinirlari).
Kaynak: (c) OpenStreetMap katkicilari (ODbL), place=village|hamlet|suburb|neighbourhood|quarter; ilce = yerlesimin merkez noktasini iceren admin_level=6 siniri.
Kurallar: ayni ad (mahalle_norm) o ilde birden cok ilcede ya da ilce adiyla ayniysa ya da JENERIK_MAH listesindeyse TABLOYA GIRMEZ; sinir ilin 'Merkez' ilcesiyse deger 'Merkez' yazilir
(ortak.py ilceler.json'da 'Merkez' yoksa bu degeri YOK SAYAR -> kullanici karari beklenir). Kullanim: python3 araclar/mahalle_ilce_uret.py <onbellek_klasoru> [--birlestir]
--birlestir: var olan mahalle_ilce.json'daki baska illeri korur, yalnizca onbellekteki illeri yeniler."""
import json, os, sys, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okuyucu"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import katla, il_slug, mahalle_norm
from mezarlik_ilce_uret import halkalar, icinde, ilce_adi

# ulke genelinde cok tekrarlanan mahalle adlari: OSM'de tek kayit gorunse bile gercekte birden cok ilcede olabilir -> tabloya girmez
JENERIK_MAH = {"cumhuriyet", "ataturk", "yeni", "eski", "fatih", "yavuz sultan selim", "barbaros", "mimar sinan", "gazi", "yildirim beyazit", "istiklal",
               "zafer", "kurtulus", "yenimahalle", "yeni mahalle", "hurriyet", "merkez", "camii", "cami", "orta", "ortakoy", "yenikoy", "sanayi",
               "gazi mustafa kemal", "mustafa kemal", "kemalpasa", "mevlana", "fevzi cakmak", "inonu", "100 yil", "cumhuriyet mah", "bahcelievler",
               "dumlupinar", "huzur", "esentepe", "yildiz", "aksu", "camlik", "camlica", "kaynarca", "karakoy", "karaagac", "yenice", "gunes",
               "ulus", "istasyon", "demirtas", "yesilyurt", "yesil", "akpinar", "kirazlik", "cinar", "cinarlik", "selcuklu", "sehitler", "sehit"}
KOY_TURLERI = ("village", "hamlet")                      # OSM'de koy/mezra kapsami sistematik -> varsayilan tablo
KENT_TURLERI = ("suburb", "neighbourhood", "quarter")     # kent mahalleleri OSM'de eksik: ayni ad baska ilcede de olabilir (canli veride %66 uyum) -> '_kent' bolumu, VARSAYILAN KAPALI
YERLER = KOY_TURLERI + KENT_TURLERI


def uret(onbellek, turler=None):
    turler = turler or KOY_TURLERI
    iv = ortak.ilce_verisi()
    tablo, ist = {}, {}
    for f in sorted(os.listdir(onbellek)):
        if not f.endswith(".json"): continue
        d = json.load(open(os.path.join(onbellek, f), encoding="utf-8"))
        if "p" not in d: continue
        il = d["il"]; liste = iv.get(il, [])
        ilceler_k = {katla(x) for x in liste}
        poligon = []
        for r in d["b"]:
            ad = ilce_adi(r.get("tags", {}), liste)
            if not ad and katla(r.get("tags", {}).get("name", "")) in ("merkez", katla(il), katla(il) + " merkez"):
                ad = "Merkez"
            if ad: poligon.append((ad, halkalar(r)))
        say = {}
        for e in d["p"]:
            t = e.get("tags", {})
            if t.get("place") not in turler: continue
            c = e.get("center") or ({"lat": e["lat"], "lon": e["lon"]} if "lat" in e else None)
            if not c: continue
            n = mahalle_norm(t["name"])
            if not n or n in ilceler_k or n in JENERIK_MAH or len(n) < 3: continue
            bulunan = {ad for ad, hs in poligon if any(icinde((c["lat"], c["lon"]), h) for h in hs)}
            if len(bulunan) != 1: 
                say.setdefault(n, set()).add("?")      # sinir disi/belirsiz konum: ad tekrar sayilsin, ama yazilmasin
                continue
            say.setdefault(n, set()).add(next(iter(bulunan)))
        t = {a: next(iter(s)) for a, s in say.items() if len(s) == 1 and "?" not in s}
        if t: tablo[il_slug(il)] = dict(sorted(t.items()))
        ist[il_slug(il)] = (len(d["p"]), len(poligon), len(t), sum(1 for v in t.values() if v == "Merkez"))
    return tablo, ist


def canli_celiski_buda(tablo, canli):
    """Canli yayin verisinde KAYNAGIN KENDI verdigi ilce (ilce_kaynagi'siz) ile defin_yeri anahtari tabloyla celisiyorsa o anahtar tablodan atilir
    (15.10.2026: 'balcik' tabloda Gebze, kaynakta Darica x7). -> atilan [(il, ad, tablo, kaynak)]"""
    atilan = []
    for f in sorted(os.listdir(canli)):
        if not f.endswith(".json"): continue
        try: d = json.load(open(os.path.join(canli, f), encoding="utf-8"))
        except Exception: continue
        slug = il_slug(d.get("il", ""))
        t = tablo.get(slug)
        if not t: continue
        g = {}
        for ilce, l in (d.get("ilceler") or {}).items():
            if ilce == "İlçe belirtilmemiş": continue
            for k in l:
                if k.get("ilce_kaynagi") or k.get("il_disi_defin"): continue
                for a in ortak.yer_anahtarlari(k.get("defin_yeri") or "") + ortak.yer_anahtarlari(k.get("mahalle") or ""):
                    g.setdefault(a, set()).add(ilce)
        for a, s in g.items():
            if a in t and (len(s) > 1 or t[a] not in s):
                atilan.append((slug, a, t.pop(a), sorted(s)))
    return atilan


if __name__ == "__main__":
    t, ist = uret(sys.argv[1])
    kent, _ = uret(sys.argv[1], KENT_TURLERI)
    for il, d in t.items():              # ayni ad ayni ilde koyde de kentte de, FARKLI ilcelerde ise belirsizdir
        for ad in [a for a, v in d.items() if kent.get(il, {}).get(a, v) != v]:
            d.pop(ad)
    for il, d in kent.items():
        for ad in [a for a in d if a in t.get(il, {})]:
            d.pop(ad)
    canli = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--canli=")), None)
    if canli:
        print("canli celiski buda (koy):", canli_celiski_buda(t, canli))
        print("canli celiski buda (kent):", canli_celiski_buda(kent, canli))
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okuyucu", "mahalle_ilce.json")
    son = {}
    if "--birlestir" in sys.argv and os.path.isfile(out):
        son = json.load(open(out, encoding="utf-8"))
    son.update(t)
    son.setdefault("_kent", {}).update(kent)
    son["_kaynak"] = "© OpenStreetMap katkıcıları (ODbL), %s" % datetime.date.today().isoformat()
    son["_not"] = "il_slug -> {mahalle_norm: ilçe}. Ad o ilde birden çok ilçede / ilçe adıyla aynı / jenerikse tabloya girmez. 'Merkez' değeri ilceler.json'da Merkez yoksa kullanılmaz."
    json.dump(dict(sorted(son.items())), open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for k, v in ist.items(): print(k, "yerlesim/ilce_siniri/tablo/merkez:", v)
