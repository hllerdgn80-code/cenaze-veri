#!/usr/bin/env python3
"""DİN GÖREVLİSİ ÖNCELİĞİ (15.10.2026; URUN-TASLAGI §37 ek): din görevlisinin paylaştığı ilan ile otomatik çekilen (belediye/ulusal/yerel) kayıt
AYNI KİŞİYSE (ulusal_birlestir.ayni(): ad + ±2 gün [+ yaş]) görevlinin kaydı KALIR, otomatik olan yayına girmez; görevli kaydındaki
BOŞ alanlar (mezarlık, mahalle, namaz yeri, yaş...) otomatik kayıttan doldurulur (ulusal_birlestir zenginleştirmesinin tersi).
Sıra (topla.yml): gorevli_al -> ulusal_birlestir -> gorevli_birlestir -> yerlestirme_denetimi -> kapi.
Şehit kaydı (sehit:true) asla silinmez (§27). ortak.py / yayin_suz.py'ye dokunmaz.
Kullanım: python3 okuyucu/gorevli_birlestir.py [veri_klasoru]"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from ulusal_birlestir import ayni

ZENGINLES = ("defin_yeri", "mahalle", "namaz_yeri_vakti", "namaz_tarihi", "defin_zamani", "yas", "vefat_tarihi", "cinsiyet")


def birlestir(d, gorevliler):
    """d: son7gun sözlüğü (yerinde değişir); gorevliler: _ulusal.json'daki görevli kayıtları. Döner: (eklenen, silinen)."""
    ilceler = d.setdefault("ilceler", {})
    listeler = [(None, d.setdefault("il_disi", [])), (None, d.setdefault("ilce_belirsiz", []))] + list(ilceler.items())
    eklenen = silinen = 0
    for g in gorevliler:
        eslesen = []
        for _, l in listeler:
            for m in l:
                if m is g or m.get("gorevli") or m.get("id") == g.get("id"):
                    continue
                if ayni(g, m):
                    eslesen.append((l, m))
        if any(m.get("sehit") for _, m in eslesen):
            continue                                              # şehit kaydı korunur; görevli kaydı eklenmez
        for l, m in eslesen:
            for a in ZENGINLES:
                if g.get(a) in (None, "", []) and m.get(a) not in (None, "", []):
                    g[a] = m[a]
            l.remove(m)
            silinen += 1
        var = any(x.get("id") == g.get("id") for _, l in listeler for x in l)
        if var:                                                   # ulusal_birlestir zaten eklemiş: kayıtlı olanı güncelle
            for _, l in listeler:
                for i, x in enumerate(l):
                    if x.get("id") == g.get("id"):
                        for a in ZENGINLES:
                            if x.get(a) in (None, "", []) and g.get(a) not in (None, "", []):
                                x[a] = g[a]
        else:
            if g.get("ilce") and not g.get("ilce_belirsiz"):
                ilceler.setdefault(g["ilce"], []).append(g)
            else:
                d["ilce_belirsiz"].append(g)
            eklenen += 1
    return eklenen, silinen


def main():
    kok = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri")
    toplam_e = toplam_s = 0
    for il in sorted(os.listdir(kok)):
        yol = os.path.join(kok, il)
        ul, son = os.path.join(yol, "_ulusal.json"), os.path.join(yol, "son7gun.json")
        if not (os.path.isfile(ul) and os.path.isfile(son)):
            continue
        try:
            g = [k for k in json.load(open(ul, encoding="utf-8")).get("kayitlar", []) if k.get("gorevli")]
            d = json.load(open(son, encoding="utf-8"))
        except Exception:
            continue
        if not g:
            continue
        e, s = birlestir(d, g)
        if e or s:
            d["toplam"] = sum(len(l) for l in (d.get("ilceler") or {}).values()) + len(d.get("il_disi") or []) + len(d.get("ilce_belirsiz") or [])
            d["guncelleme"] = ortak.simdi_iso()
            ortak.json_yaz(son, d)
        toplam_e += e
        toplam_s += s
    print(f"gorevli birlestirme: {toplam_e} eklendi, {toplam_s} otomatik kayit yerine gorevli kaydi kaldi")


if __name__ == "__main__":
    main()
