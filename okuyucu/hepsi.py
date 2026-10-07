#!/usr/bin/env python3
"""Tüm il okuyucularını sırayla çalıştırır; biri hata verirse öbürleri devam eder.
Sonunda veri/ozet.json yazar: il -> son güncelleme, kayıt sayısı, hata.
Kullanım: python3 okuyucu/hepsi.py [il ...]     (il verilmezse hepsi)
          python3 okuyucu/hepsi.py --grup N/M    (ILLER'in M parçadan N.sü; özet veri/ozet.N.json)
          python3 okuyucu/hepsi.py --ozet-birlestir   (veri/ozet.*.json -> veri/ozet.json)
Her il en çok IL_SINIRI_SN sürer; aşarsa "zaman aşımı" ile atlanır.
"""
import importlib, io, json, os, shutil, sys, threading, time, traceback
from contextlib import redirect_stdout

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak

VERI = os.path.join(DIZIN, "..", "veri")
ILLER = ["ordu", "trabzon", "kocaeli", "kahramanmaras", "batman", "giresun", "gaziantep", "bursa", "osmaniye", "kayseri", "konya", "denizli", "sivas", "kirikkale", "zonguldak", "edirne", "afyonkarahisar", "aksaray", "bartin", "bilecik", "bolu", "canakkale", "cankiri", "duzce", "elazig", "erzincan", "gumushane", "isparta", "kirsehir", "nevsehir", "nigde", "rize", "sinop", "sanliurfa", "tokat", "usak", "van", "karaman", "kutahya", "karabuk", "yalova", "malatya"]   # dosyası olmayan atlanır


IL_SINIRI_SN = 150


def birlestir():
    ozet_yolu = os.path.join(VERI, "ozet.json")
    try:
        with open(ozet_yolu, encoding="utf-8") as f:
            ozet = json.load(f)
    except Exception:
        ozet = {"iller": {}}
    n = 0
    for ad in sorted(os.listdir(VERI)):
        if ad.startswith("ozet.") and ad.endswith(".json") and ad != "ozet.json":
            with open(os.path.join(VERI, ad), encoding="utf-8") as f:
                ozet["iller"].update(json.load(f).get("iller", {}))
            n += 1
    ozet["guncelleme"] = ortak.simdi_iso()
    ortak.json_yaz(ozet_yolu, ozet)
    print(f"{n} grup özeti birleştirildi, {len(ozet['iller'])} il")


def sinirli_calistir(modul, il):
    """modul.main()'i ayrı iş parçacığında çalıştırır; IL_SINIRI_SN'yi aşarsa TimeoutError."""
    sonuc = {}

    def is_():
        try:
            sys.argv = [f"{il}.py"]
            modul.main()
        except SystemExit:
            pass
        except BaseException as e:
            sonuc["hata"] = e
    t = threading.Thread(target=is_, daemon=True)
    t.start()
    t.join(IL_SINIRI_SN)
    if t.is_alive():
        raise TimeoutError(f"zaman aşımı ({IL_SINIRI_SN} sn)")
    if "hata" in sonuc:
        raise sonuc["hata"]


def main():
    args = sys.argv[1:]
    if "--ozet-birlestir" in args:
        return birlestir()
    grup = None
    if "--grup" in args:
        i = args.index("--grup")
        n, m = map(int, args[i + 1].split("/"))
        args = args[:i] + args[i + 2:]
        grup = n
        parca = [ILLER[k] for k in range(len(ILLER)) if k % m == n - 1]   # dağıtık: yavaş iller gruplara yayılır
        if "--sadece-grubu-birak" in args:   # CI: artifact'a yalnız bu grubun illeri girsin (eski veri öbür grubu ezmesin)
            for ad in os.listdir(VERI):
                yol = os.path.join(VERI, ad)
                if os.path.isdir(yol) and ad not in parca and ad != "kaybettiklerimiz":
                    shutil.rmtree(yol, ignore_errors=True)
            for ad in os.listdir(VERI):
                if ad.startswith("ozet") and ad != f"ozet.{grup}.json":
                    os.remove(os.path.join(VERI, ad))
            print(f"grup {grup}/{m}: yalnız {parca} bırakıldı")
            return
    secilen = [a for a in args if not a.startswith("-")] or (parca if grup else ILLER)
    ozet_yolu = os.path.join(VERI, f"ozet.{grup}.json" if grup else "ozet.json")
    try:
        with open(ozet_yolu, encoding="utf-8") as f:
            ozet = json.load(f)
    except Exception:
        ozet = {"iller": {}}
    if grup:
        ozet = {"iller": {}}
    for il in secilen:
        if not os.path.exists(os.path.join(DIZIN, f"{il}.py")):
            print(f"[{il}] okuyucu dosyası yok, atlandı")
            continue
        giris = {"son_calisma": ortak.simdi_iso(), "hata": None}
        t0 = time.time()
        tampon = io.StringIO()
        il_dizin = os.path.join(VERI, il)
        yedek = os.path.join(VERI, f"_yedek_{il}")
        shutil.rmtree(yedek, ignore_errors=True)
        if os.path.isdir(il_dizin):
            shutil.copytree(il_dizin, yedek)          # hata/boş sonuçta eski veri korunur
        try:
            modul = importlib.import_module(il)
            with redirect_stdout(tampon):
                sinirli_calistir(modul, il)
        except Exception as e:
            giris["hata"] = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        son = os.path.join(VERI, il, "son7gun.json")
        if os.path.isdir(yedek):
            yeni_toplam = None
            try:
                with open(son, encoding="utf-8") as f:
                    yeni_toplam = json.load(f).get("toplam")
            except Exception:
                pass
            eski_toplam = None
            try:
                with open(os.path.join(yedek, "son7gun.json"), encoding="utf-8") as f:
                    eski_toplam = json.load(f).get("toplam")
            except Exception:
                pass
            if giris["hata"] or (not yeni_toplam and eski_toplam):
                shutil.rmtree(il_dizin, ignore_errors=True)
                shutil.copytree(yedek, il_dizin)      # geri al: hatalı/boş okuma eskiyi silmesin
                giris["geri_alindi"] = True
            shutil.rmtree(yedek, ignore_errors=True)
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
    sys.stdout.flush()
    os._exit(0)   # zaman aşımına uğrayan arka plan iş parçacıkları süreci tutmasın


if __name__ == "__main__":
    main()
