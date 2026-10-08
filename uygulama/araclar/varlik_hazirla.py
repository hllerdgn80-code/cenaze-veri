#!/usr/bin/env python3
"""Uygulamaya gömülen veri dosyalarını hazırlar (yerelde, bir kez; çıktı depoya girer).
Kaynaklar: okuyucu/ilceler.json, tasarim/adlar.json, tasarim/dualar.json, okuyucu/haric_tutulanlar.json
Çıktı: uygulama/assets/veri/{ilceler,adlar,dualar,haric}.json
Not: iç alanlar (katalog, doğrulama notu vb.) uygulamaya gömülmez."""
import json, pathlib
U = pathlib.Path(__file__).resolve().parent.parent      # uygulama/
K = U.parent                                              # cenaze-uygulamasi/
C = U / "assets" / "veri"
C.mkdir(parents=True, exist_ok=True)

# 1) İl -> ilçe (81 il; kaynak dosyada eksik olan iki il resmî ilçe listesiyle tamamlanır)
src = json.load(open(K / "okuyucu/ilceler.json", encoding="utf-8"))
EK = {
    "Adana": ["Aladağ", "Ceyhan", "Çukurova", "Feke", "İmamoğlu", "Karaisalı", "Karataş", "Kozan", "Pozantı",
              "Saimbeyli", "Sarıçam", "Seyhan", "Tufanbeyli", "Yumurtalık", "Yüreğir"],
    "Sakarya": ["Adapazarı", "Akyazı", "Arifiye", "Erenler", "Ferizli", "Geyve", "Hendek", "Karapürçek", "Karasu",
                "Kaynarca", "Kocaali", "Pamukova", "Sapanca", "Serdivan", "Söğütlü", "Taraklı"],
}
iller = src["_iller"]
assert len(iller) == 81, len(iller)
cikti = {}
for il in iller:
    L = src.get(il) or EK.get(il)
    assert L, f"ilçe listesi yok: {il}"
    cikti[il] = L
json.dump(cikti, open(C / "ilceler.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# 2) Ad listesi (cinsiyet çözümleme)
a = json.load(open(K / "tasarim/adlar.json", encoding="utf-8"))
json.dump({"e": a["e"], "k": a["k"]}, open(C / "adlar.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# 3) Dualar (yalnız ekranda kullanılan alanlar)
d = json.load(open(K / "tasarim/dualar.json", encoding="utf-8"))
ALAN = ("b", "ar", "ok", "an", "k", "e", "kadin", "not")
dd = {"etiketler": d["etiketler"],
      "bolumler": [{"k": b["k"], "ad": b["ad"], "ikon": b["ikon"], "kisa": b["kisa"],
                    "liste": [{f: x[f] for f in ALAN if x.get(f)} for x in b["liste"]]} for b in d["bolumler"]]}
json.dump(dd, open(C / "dualar.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# 4) Hariç tutulan kişiler (Kaybettiklerimiz / Tarihte Bugün; yalnız Wikidata kimliği — ikinci kilit)
h = json.load(open(K / "okuyucu/haric_tutulanlar.json", encoding="utf-8"))
ids = sorted({x["wikidata_id"] for x in h if not x.get("aday")} | {"Q488200"})
json.dump(ids, open(C / "haric.json", "w", encoding="utf-8"), separators=(",", ":"))
print("tamam:", len(cikti), "il ·", len(a["e"]) + len(a["k"]), "ad ·", sum(len(b["liste"]) for b in dd["bolumler"]), "dua ·", len(ids), "hariç")
