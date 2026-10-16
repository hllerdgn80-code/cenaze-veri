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


def defter_adlari():
    """Kayıt defterindeki kaynak adları (kayitli_kaynak 'kaynak_ad' olarak yazar). Defter okunamazsa boş küme (sayaç çalışmaz, birleştirme etkilenmez)."""
    try:
        import kayitli_kaynak as kk
        return {s["ad"] for s in kk.defter_oku(uyar=lambda m: None)}
    except Exception:
        return set()


def sayac_yaz(kok, yeni_il, yeni_kaynak):
    """16.10.2026: veri/_defter_durum.json['yeni_kayit'][gün] = {toplam, il, kaynak} (saatlik turlar toplanır, 14 gün tutulur). 'Yeni' = bu turda
    son7gun'a İLK KEZ giren ve kaynağı defterdeki bir satır olan kayıt (zenginleştirme/yinelenen sayılmaz)."""
    try:
        import kayitli_kaynak as kk
        d = kk.durum_yukle(kok)
        g = datetime.now().date().isoformat()
        e = d.setdefault("yeni_kayit", {}).setdefault(g, {"toplam": 0, "il": {}, "kaynak": {}})
        e["toplam"] += sum(yeni_il.values())
        for a, b in ((e["il"], yeni_il), (e["kaynak"], yeni_kaynak)):
            for k, v in b.items():
                a[k] = a.get(k, 0) + v
        sinir = (datetime.now().date() - timedelta(days=14)).isoformat()
        d["yeni_kayit"] = {k: v for k, v in d["yeni_kayit"].items() if k >= sinir}
        ortak.json_yaz(os.path.join(kok, kk.DURUM_DOSYASI), d)
    except Exception as ex:
        print("UYARI: defter sayacı yazılamadı:", ex, file=sys.stderr)


def main():
    kok = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri")
    eklenen = {}
    adlar = defter_adlari()
    yeni_il, yeni_kaynak = {}, {}
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
            es = next((m for m in mevcut if ayni(r, m)), None)
            if es is not None:
                # 14.10.2026 (Fable): ayni kisi zaten varsa EKLEME ama ZENGINLESTIR — mevcut kayitta bos olan alanlari (ilce, mezarlik, yas,
                # mahalle, namaz) ulusal/e-Devlet kaydindan doldur; ilce yalniz ilin gercek ilcesi ise (kaynak zaten dogruladi) ve kayit
                # ilcesizse: ilce_belirsiz listesinden o ilcenin listesine tasinir. Boylece belediye listesinin ilcesiz kaydi ilceye kavusur.
                for a in ("defin_yeri", "yas", "mahalle", "namaz_yeri_vakti", "namaz_tarihi", "defin_zamani", "vefat_tarihi"):
                    if es.get(a) in (None, "", []) and r.get(a) not in (None, "", []):
                        es[a] = r[a]
                if r.get("sehit") and not es.get("sehit"):                   # sehit isareti (ve rutbe/toren) kaybolmasin (§27)
                    es["sehit"] = True
                    for a in ("rutbe", "toren"):
                        if r.get(a) and not es.get(a):
                            es[a] = r[a]
                if not es.get("ilce") and r.get("ilce") and not r.get("ilce_belirsiz") and r["ilce"] != "Merkez":
                    if es in (d.get("ilce_belirsiz") or []):
                        d["ilce_belirsiz"].remove(es)
                        es["ilce"] = r["ilce"]; es["ilce_belirsiz"] = False
                        es.setdefault("ham", {})["ilce_kaynagi"] = "capraz_eslesme"
                        d.setdefault("ilceler", {}).setdefault(r["ilce"], []).append(es)
                        n += 1
                # H60 (15.10.2026): zenginlesme sonrasi hala ilcesiz ise mezarlik/mahalle/ilce-adi katmanlari bir kez de burada denenir
                if es in (d.get("ilce_belirsiz") or []) and not es.get("ilce") and not es.get("il_disi_defin"):
                    ortak.ilce_isle(es, d.get("il") or il)
                    if es.get("ilce"):
                        d["ilce_belirsiz"].remove(es)
                        d.setdefault("ilceler", {}).setdefault(es["ilce"], []).append(es)
                        n += 1
                continue
            if not r.get("ilce") and not r.get("il_disi_defin"):
                ortak.ilce_isle(r, d.get("il") or il)          # H60: ulusal kayit da mezarlik/mahalle/ilce-adi katmanlarindan gecer (tahmin yok)
            mevcut.append(r)
            if r.get("kaynak_ad") in adlar:                    # defter satırından gelen, son7gun'da ilk kez görülen kayıt
                yeni_il[il] = yeni_il.get(il, 0) + 1
                yeni_kaynak[r["kaynak_ad"]] = yeni_kaynak.get(r["kaynak_ad"], 0) + 1
            if r.get("ilce") and not r.get("ilce_belirsiz"):
                d.setdefault("ilceler", {}).setdefault(r["ilce"], []).append(r)
            else:
                d.setdefault("ilce_belirsiz", []).append(r)
            n += 1
        if n:
            d["toplam"] = sum(len(l) for l in (d.get("ilceler") or {}).values()) + len(d.get("il_disi") or []) + len(d.get("ilce_belirsiz") or [])
            d["guncelleme"] = ortak.simdi_iso()
            ortak.json_yaz(son, d)
            eklenen[il] = n
    if adlar:
        sayac_yaz(kok, yeni_il, yeni_kaynak)
        print(f"defter: {sum(yeni_il.values())} yeni kayıt (bugün ilk görülen), il başına {dict(sorted(yeni_il.items(), key=lambda x: -x[1]))}, "
              f"kaynak başına {dict(sorted(yeni_kaynak.items(), key=lambda x: -x[1]))}")
    print(f"ulusal birleştirme: {sum(eklenen.values())} kayıt, {len(eklenen)} il", dict(sorted(eklenen.items(), key=lambda x: -x[1])[:10]))


if __name__ == "__main__":
    main()
