#!/usr/bin/env python3
"""Yerlestirme denetimi (14.10.2026): veri/<il>/son7gun.json dosyalarinda ilce yerlestirmesini dogrular.
Kullanim: python3 okuyucu/yerlestirme_denetimi.py [veri_klasoru] [--rapor yol]
Cikis kodu: kural 1-4 ihlali varsa 1, temizse 0 (kural 5 tekrar ve kural 6 ilcesiz orani UYARIDIR, cikisi etkilemez). KVKK: rapor kisi adi tasimaz (id/il/ilce/mezarlik).
Rapor: <veri>/yerlestirme-raporu.json (ic dosya; yayin_suz veri/ kokundaki UST_DOSYALAR disindakileri siler -> yayina gitmez)."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ortak import katla, il_slug

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETIKET = "İlçe belirtilmemiş"
ESIK_ILCESIZ = 0.5


def _oku(y):
    with open(y, encoding="utf-8") as f:
        return json.load(f)


def _kayitlar(d):
    """-> [(bolum, ilce_anahtari, kayit)] bolum: ilce | il_disi | belirsiz"""
    out = []
    for i, l in (d.get("ilceler") or {}).items():
        out += [("ilce", i, k) for k in l]
    out += [("il_disi", None, k) for k in d.get("il_disi") or []]
    out += [("belirsiz", None, k) for k in d.get("ilce_belirsiz") or []]
    return out


def denetle(veri, ilce_json=None, rastgele_tohum=None):
    ilce_json = ilce_json or os.path.join(KOK, "uygulama", "assets", "veri", "ilceler.json")
    ilceler = _oku(ilce_json)
    iller_k = {katla(i): i for i in ilceler if not i.startswith("_")}
    ihlal, uyari, sayac, ilcesiz = [], [], {}, {}
    kisi_yer, ornek_havuzu = {}, []
    for klasor in sorted(os.listdir(veri)):
        yol = os.path.join(veri, klasor, "son7gun.json")
        if klasor.startswith("_") or not os.path.isfile(yol):
            continue
        d = _oku(yol)
        il_adi = d.get("il") or ""
        liste = ilceler.get(il_adi) or []
        if il_slug(il_adi) != klasor:
            ihlal.append({"kural": 1, "il": klasor, "aciklama": "son7gun.json il alani klasorle uyusmuyor", "deger": il_adi})
        top = sayi_belirsiz = 0
        sayac[klasor] = {}
        for bolum, ik, k in _kayitlar(d):
            top += 1
            kid, ilce = k.get("id"), k.get("ilce")
            if k.get("il") and il_slug(k["il"]) != klasor:
                ihlal.append({"kural": 1, "id": kid, "il": klasor, "aciklama": "kaydin il alani klasorden farkli", "deger": k["il"]})
            # 2) atanan ilce o ilin listesinde mi
            if bolum == "ilce":
                if ik != ETIKET and ik not in liste:
                    ihlal.append({"kural": 2, "id": kid, "il": klasor, "ilce": ik, "aciklama": "ilce o ilin resmi listesinde yok"})
                if ilce and ilce != ik:
                    ihlal.append({"kural": 2, "id": kid, "il": klasor, "ilce": ik, "aciklama": "kayit.ilce, bulundugu ilce basligindan farkli", "deger": ilce})
                sayac[klasor][ik] = sayac[klasor].get(ik, 0) + 1
                if ik == ETIKET:
                    sayi_belirsiz += 1
            elif bolum == "belirsiz":
                sayi_belirsiz += 1
                if ilce and ilce != ETIKET:
                    ihlal.append({"kural": 2, "id": kid, "il": klasor, "aciklama": "ilce_belirsiz listesinde ilcesi dolu kayit", "ilce": ilce})
            ik_kayit = ilce if bolum == "ilce" else None
            # 3) mezarlik tablosu tutarliligi
            kay = k.get("ilce_kaynagi") or (k.get("ham") or {}).get("ilce_kaynagi") or ""
            if kay.startswith("mezarlik_tablosu"):
                r = ortak.mezarlik_ilce_bul(il_adi, k.get("defin_yeri"))
                if r is None:
                    ihlal.append({"kural": 3, "id": kid, "il": klasor, "ilce": ik_kayit, "aciklama": "tabloda karsiligi yok", "mezarlik": k.get("defin_yeri")})
                elif r[0] == "ilce" and ik_kayit != r[1]:
                    ihlal.append({"kural": 3, "id": kid, "il": klasor, "ilce": ik_kayit, "aciklama": "tablodaki ilce farkli", "tablo": r[1], "mezarlik": k.get("defin_yeri")})
                elif r[0] == "belirsiz" and ik_kayit not in r[1]:
                    ihlal.append({"kural": 3, "id": kid, "il": klasor, "ilce": ik_kayit, "aciklama": "ilce adaylar arasinda degil", "adaylar": r[1], "mezarlik": k.get("defin_yeri")})
                ornek_havuzu.append((klasor, ik_kayit, k.get("defin_yeri"), kay))
            elif bolum == "ilce" and ik != ETIKET:
                ornek_havuzu.append((klasor, ik, k.get("defin_yeri"), kay or "kaynak"))
            # 4) defin_yeri baska ilin adiysa o ilin ilcesine/ilimize yerlestirilmemis olmali
            dy = katla(k.get("defin_yeri") or "")
            if dy in iller_k and dy != katla(il_adi):
                if bolum == "ilce" and ik != ETIKET:
                    ihlal.append({"kural": 4, "id": kid, "il": klasor, "ilce": ik, "aciklama": "defin yeri baska bir ilin adi ama kayit ilceye atanmis", "mezarlik": k.get("defin_yeri")})
            if bolum == "il_disi":
                dd = k.get("il_disi_defin") or {}
                if dd.get("il") and ik_kayit:
                    ihlal.append({"kural": 4, "id": kid, "il": klasor, "aciklama": "il_disi kaydinda ilce dolu"})
            # 5) tekrar: ayni kisi (ad+yas+vefat) iki ilde / iki ilcede
            ad = katla(k.get("ad_soyad") or "")
            if ad:
                anah = (ad, k.get("yas"), k.get("vefat_tarihi"))
                kisi_yer.setdefault(anah, []).append((klasor, ik if bolum == "ilce" else bolum, kid))
        ilcesiz[klasor] = (sayi_belirsiz, top)
    for anah, yerler in kisi_yer.items():
        if len({y[2] for y in yerler}) > 1 and (len({y[0] for y in yerler}) > 1 or len({y[1] for y in yerler}) > 1):
            uyari.append({"kural": 5, "idler": sorted({y[2] for y in yerler if y[2]}), "yerler": sorted({f"{y[0]}/{y[1]}" for y in yerler}),
                          "aciklama": "ayni kisi birden cok il/ilcede"})
    for k, (b, t) in sorted(ilcesiz.items()):
        if t and b / t > ESIK_ILCESIZ:
            uyari.append({"kural": 6, "il": k, "ilcesiz": b, "toplam": t, "oran": round(b / t, 2), "aciklama": "ilcesiz orani >%50"})
    rnd = random.Random(rastgele_tohum)
    ornek = [{"il": a, "ilce": b, "mezarlik": c, "ilce_kaynagi": d} for a, b, c, d in rnd.sample(ornek_havuzu, min(10, len(ornek_havuzu)))]
    return {"ihlal_sayisi": len(ihlal), "ihlaller": ihlal, "uyarilar": uyari,
            "ilce_kayit_sayilari": sayac, "ilcesiz_oranlari": {k: {"ilcesiz": b, "toplam": t} for k, (b, t) in ilcesiz.items()},
            "ornek10": ornek}


def main(argv):
    veri = os.path.join(KOK, "veri")
    rapor = None
    a = list(argv)
    if "--rapor" in a:
        i = a.index("--rapor"); rapor = a[i + 1]; del a[i:i + 2]
    if a:
        veri = a[0]
    r = denetle(veri)
    rapor = rapor or os.path.join(veri, "yerlestirme-raporu.json")
    with open(rapor, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    print(f"yerlestirme denetimi: {r['ihlal_sayisi']} ihlal, {len(r['uyarilar'])} uyari; rapor: {rapor}")
    for x in r["ihlaller"][:30]:
        print("  IHLAL", {k: v for k, v in x.items() if k != "aciklama"}, x["aciklama"])
    for x in r["uyarilar"]:
        print("  UYARI", x.get("il") or x.get("yerler"), f"{x['ilcesiz']}/{x['toplam']}" if "ilcesiz" in x else x["aciklama"])
    for x in r["ornek10"]:
        print("  ORNEK", x)
    return 1 if r["ihlal_sayisi"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
