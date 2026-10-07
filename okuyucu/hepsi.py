#!/usr/bin/env python3
"""Tüm il okuyucularını sırayla çalıştırır; biri hata verirse öbürleri devam eder.
Sonunda veri/ozet.json yazar: il -> son güncelleme, kayıt sayısı, hata.
Kullanım: python3 okuyucu/hepsi.py [il ...]     (il verilmezse hepsi)
"""
import importlib, io, json, os, sys, time, traceback
from contextlib import redirect_stdout

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak

VERI = os.path.join(DIZIN, "..", "veri")
ILLER = ["ordu", "trabzon", "kocaeli", "kahramanmaras", "batman", "giresun", "gaziantep", "bursa", "osmaniye", "kayseri", "konya", "denizli", "sivas", "kirikkale", "zonguldak", "edirne", "afyonkarahisar", "aksaray", "bartin", "bilecik", "bolu", "canakkale", "cankiri", "duzce", "elazig", "erzincan", "gumushane", "isparta", "kirsehir", "nevsehir", "nigde", "rize", "sinop", "sanliurfa", "tokat", "usak", "van", "karaman", "kutahya", "karabuk", "yalova", "malatya"]   # dosyası olmayan atlanır


def main():
    secilen = [a for a in sys.argv[1:] if not a.startswith("-")] or ILLER
    ozet_yolu = os.path.join(VERI, "ozet.json")
    try:
        with open(ozet_yolu, encoding="utf-8") as f:
            ozet = json.load(f)
    except Exception:
        ozet = {"iller": {}}
    for il in secilen:
        if not os.path.exists(os.path.join(DIZIN, f"{il}.py")):
            print(f"[{il}] okuyucu dosyası yok, atlandı")
            continue
        giris = {"son_calisma": ortak.simdi_iso(), "hata": None}
        t0 = time.time()
        tampon = io.StringIO()
        try:
            modul = importlib.import_module(il)
            sys.argv = [f"{il}.py"]
            with redirect_stdout(tampon):
                modul.main()
        except SystemExit:
            pass
        except Exception as e:
            giris["hata"] = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        son = os.path.join(VERI, il, "son7gun.json")
        try:
            with open(son, encoding="utf-8") as f:
                d = json.load(f)
            giris.update(il_adi=d.get("il"), son_guncelleme=d.get("guncelleme"), kayit_sayisi=d.get("toplam"),
                         il_disi=len(d.get("il_disi", [])), ilce_belirsiz=len(d.get("ilce_belirsiz", [])))
        except Exception as e:
            giris.update(son_guncelleme=None, kayit_sayisi=None)
            giris["hata"] = giris["hata"] or f"son7gun.json okunamadı: {e}"
        giris["sure_sn"] = round(time.time() - t0)
        ozet["iller"][il] = giris
        print(f"[{il}] {giris.get('kayit_sayisi')} kayıt, {giris['sure_sn']} sn" + (f", HATA: {giris['hata']}" if giris["hata"] else ""))
        print("   " + "\n   ".join(tampon.getvalue().strip().splitlines()[-2:]))
    ozet["guncelleme"] = ortak.simdi_iso()
    ortak.json_yaz(ozet_yolu, ozet)


if __name__ == "__main__":
    main()
