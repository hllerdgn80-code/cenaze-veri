#!/usr/bin/env python3
"""SIFIR KAYNAK BEKÇİSİ (16.10.2026). Her tur, her kaynağın (il/ilçe-kaynak) pencere içi kayıt sayısı kaydedilir; bir kaynak
ART ARDA 2 tur 0 ya da HATA/ENGEL verirse uyarı çıkar. Yayına GİTMEZ (dosyalar '_' ile başlar).
- veri/<il>/_sayac.json : o ilin kaynakları -> son 14 tur [{t, d}]  (hepsi.py her il koşusundan sonra yazar; grup işleri çakışmasın diye il başına)
- veri/_kaynak_sayac.json : tüm iller birleşik  | veri/_kaynak_uyari.json : sessiz kaynaklar
Kullanım: hepsi.py içinden; elle: python3 okuyucu/kaynak_sayac.py   (birleştir + uyarı bas)"""
import json, os, sys

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak

VERI = os.path.join(DIZIN, "..", "veri")
SON = 14
ESIK = 2


def _oku(yol, varsayilan):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return varsayilan


def sifir_mu(d):
    return isinstance(d, str) or not d          # metin = HATA/ENGEL; 0/None = kayıt yok


def kaydet(il, ilce_durum, toplam=None, hata=None):
    """ilce_durum: {kaynak: sayı | 'HATA…' | 'ENGEL…'} (son7gun.json). Boşsa ilin toplamı tek kaynak sayılır."""
    klasor = os.path.join(VERI, il)
    if not os.path.isdir(klasor):
        return
    d = dict(ilce_durum or {})
    if not d:
        d = {"(il)": (f"HATA: {hata}"[:80] if hata else (toplam or 0))}
    yol = os.path.join(klasor, "_sayac.json")
    kayit = _oku(yol, {})
    zaman = ortak.simdi_iso()
    for k, v in d.items():
        kayit.setdefault(k, []).append({"t": zaman, "d": v if isinstance(v, int) else str(v)[:80]})
        kayit[k] = kayit[k][-SON:]
    for k in list(kayit):                          # artık okuyucuda olmayan kaynak
        if k not in d:
            del kayit[k]
    ortak.json_yaz(yol, kayit)


def birlestir(yaz=True):
    """Tüm il dosyalarını birleştirir; sessiz kaynakları döndürür ve ::warning:: basar."""
    toplu, uyari = {}, []
    if not os.path.isdir(VERI):
        return uyari
    for il in sorted(os.listdir(VERI)):
        kayit = _oku(os.path.join(VERI, il, "_sayac.json"), None)
        if not isinstance(kayit, dict):
            continue
        for k, tur in kayit.items():
            toplu[f"{il}/{k}"] = tur
            son = tur[-ESIK:]
            if len(son) >= ESIK and all(sifir_mu(x["d"]) for x in son):
                ardisik = 0
                for x in reversed(tur):
                    if not sifir_mu(x["d"]):
                        break
                    ardisik += 1
                uyari.append({"kaynak": f"{il}/{k}", "ardisik_tur": ardisik, "son": son[-1]["d"], "son_zaman": son[-1]["t"]})
    if yaz:
        ortak.json_yaz(os.path.join(VERI, "_kaynak_sayac.json"), {"guncelleme": ortak.simdi_iso(), "kaynaklar": toplu})
        ortak.json_yaz(os.path.join(VERI, "_kaynak_uyari.json"), {"guncelleme": ortak.simdi_iso(), "sessiz": uyari})
    if uyari:
        print("::warning title=Sessiz kaynaklar::" + "; ".join(f"{u['kaynak']} ({u['ardisik_tur']} tur: {u['son']})" for u in uyari[:25]))
    return uyari


if __name__ == "__main__":
    u = birlestir()
    print(f"{len(u)} sessiz kaynak")
