#!/usr/bin/env python3
"""BOŞLUK TURU (15.10.2026, site sahibi: "önce genel tarama, boşluklar tespit edilsin; dünün bekleyen bilgisi en başta girsin [ortak.son7gun_yaz];
boşluklar 10:00'a kadar beklensin; hâlâ boşluk varsa kendi imkânlarımızla doldurulsun; belediye geç yayımlıyorsa sonraki turlar yakalar").

  --tespit [--canli] [--veri KLASOR] [--etiket ad] [--birlestir DOSYA]
        Bugün (TR tarihi) cenaze kaydı OLMAYAN illeri bulur, veri/_bosluk.json yazar.
        Kaynak: yerel veri/<il>/son7gun.json (varsayılan) ya da --canli: https://hllerdgn80-code.github.io/cenaze-veri/veri/<il>/son7gun.json
        Cenaze günü = namaz_tarihi, yoksa defin_zamani[:10], yoksa liste_tarihi, yoksa vefat_tarihi (belediye listeleri yalnız liste/vefat günü verir).
        KAYNAKSIZ il (boşluk sayılmaz) KODDAN belirlenir: okuyucu/<il>.py'nin başlığı "belediye listesi/kaynağı yok" ya da "günlük liste yok" diyor
        VE son 7 günde 0 kayıt var (elle liste yok; kaynağı sonradan gelen il kendiliğinden boşluk adayı olur).
        --birlestir: başka bir _bosluk.json'daki (ör. veri-tr/_bosluk.json) aynı güne ait tur kayıtları geçmişe katılır.
        _bosluk.json yayına GİTMEZ: yayin_suz.suz() veri/ kökünde UST_DOSYALAR dışındaki dosyayı siler (teyit: bu dosyanın başlığı).
  --oncelik     _bosluk.json'daki boş illeri e-Devlet hizmet slug'larına eşler; EDEVLET_ONCELIK için virgüllü liste yazar (boşsa boş satır).
  --il-listesi  boş illerin slug'ları, virgüllü (cenazeilanlari.py --il için).
  --rapor       Akşam raporu tek satırı.
Dosya: veri/_bosluk.json = {tarih, saat, bos_iller, kaynaksiz, dolu, onceki_turlar:[{saat, bos, bos_iller, kaynak}]}  (onceki_turlar: günün TÜM turları, sonuncusu = üstteki durum).
Python 3.9 stdlib."""
import json, os, re, sys, time, concurrent.futures as cf, urllib.request
from datetime import datetime, timedelta, timezone

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OKUYUCU = os.path.join(KOK, "okuyucu")
CANLI = "https://hllerdgn80-code.github.io/cenaze-veri/veri/"
KAYNAKSIZ_IZ = re.compile(r"belediye (?:listesi|kayna[gğ][ıi]) yok|g[uü]nl[uü]k liste yok", re.I)


def arg(ad, vars_=None):
    return sys.argv[sys.argv.index(ad) + 1] if ad in sys.argv else vars_


def simdi_tr():
    return datetime.now(timezone.utc) + timedelta(hours=3)


def kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(str.maketrans("çğıöşü", "cgiosu"))
    return re.sub(r"[^a-z0-9]+", "", s)


def iller():
    """81 il, uygulamanin ilceler.json anahtarlarindan (hepsi.ILLER sakarya'yi icermiyor)."""
    d = json.load(open(os.path.join(KOK, "uygulama", "assets", "veri", "ilceler.json"), encoding="utf-8"))
    return sorted(kat(i) for i in d)


def oku_il(il, canli, veri):
    for deneme in range(3):
        try:
            if canli:
                req = urllib.request.Request(CANLI + il + "/son7gun.json", headers={"User-Agent": "bosluk.py"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode("utf-8"))
            with open(os.path.join(veri, il, "son7gun.json"), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            if not canli:
                return None
            time.sleep(2)
    return None


def kayitlar(d):
    out = []
    for l in (d.get("ilceler") or {}).values():
        out += l
    out += d.get("il_disi") or []
    out += d.get("ilce_belirsiz") or []
    return out


def cenaze_gunu(k):
    return k.get("namaz_tarihi") or (k.get("defin_zamani") or "")[:10] or k.get("liste_tarihi") or k.get("vefat_tarihi") or ""


def kaynaksiz_basligi(il):
    try:
        bas = open(os.path.join(OKUYUCU, il + ".py"), encoding="utf-8").read(1500)
    except Exception:
        return False
    return bool(KAYNAKSIZ_IZ.search(bas))


def yukle(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def yaz(yol, d):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def tespit():
    canli = "--canli" in sys.argv
    veri = arg("--veri", os.path.join(KOK, "veri"))
    etiket = arg("--etiket", "saatlik")
    simdi = simdi_tr()
    bugun = simdi.date().isoformat()
    tum = iller()
    with cf.ThreadPoolExecutor(8) as ex:
        veriler = dict(zip(tum, ex.map(lambda i: oku_il(i, canli, veri), tum)))
    bos, kaynaksiz, okunamayan, dolu = [], [], [], 0
    for il in tum:
        d = veriler[il]
        if d is None:
            okunamayan.append(il)
            continue
        ks = kayitlar(d)
        if any(cenaze_gunu(k) == bugun for k in ks):
            dolu += 1
        elif not ks and kaynaksiz_basligi(il):
            kaynaksiz.append(il)
        else:
            bos.append(il)
    if len(okunamayan) > len(tum) // 2:
        print(f"HATA: {len(okunamayan)}/{len(tum)} il okunamadi ({'canli' if canli else veri}); _bosluk.json yazilmadi", file=sys.stderr)
        return 1
    yol = os.path.join(veri, "_bosluk.json")
    onceki = yukle(yol)
    turlar = onceki.get("onceki_turlar", []) if onceki.get("tarih") == bugun else []
    if "--birlestir" in sys.argv:
        diger = yukle(arg("--birlestir"))
        if diger.get("tarih") == bugun:
            var = {(t["saat"], t.get("kaynak")) for t in turlar}
            turlar += [t for t in diger.get("onceki_turlar", []) if (t["saat"], t.get("kaynak")) not in var]
    saat = simdi.strftime("%H:%M")
    turlar = [t for t in turlar if not (t["saat"] == saat and t.get("kaynak") == etiket)]
    turlar.append({"saat": saat, "bos": len(bos), "bos_iller": bos, "kaynak": etiket})
    turlar.sort(key=lambda t: t["saat"])
    cikti = {"tarih": bugun, "saat": saat, "bos_iller": bos, "kaynaksiz": kaynaksiz, "dolu": dolu, "onceki_turlar": turlar}
    if okunamayan:
        cikti["okunamayan"] = okunamayan
    os.makedirs(veri, exist_ok=True)
    yaz(yol, cikti)
    print(f"bosluk {bugun} {saat} ({etiket}): bos {len(bos)}, dolu {dolu}, kaynaksiz {len(kaynaksiz)}, okunamayan {len(okunamayan)}")
    print("  bos:", ", ".join(bos) or "-")
    print("  kaynaksiz:", ", ".join(kaynaksiz) or "-")
    if okunamayan:
        print("  okunamayan:", ", ".join(okunamayan))
    return 0


def durum_oku():
    return yukle(os.path.join(arg("--veri", os.path.join(KOK, "veri")), "_bosluk.json"))


def oncelik():
    sys.path.insert(0, OKUYUCU)
    import edevlet
    bos = {edevlet.kat(i) for i in durum_oku().get("bos_iller", [])}
    secilen = [(slug, ilce) for slug, (il, ilce) in edevlet.HIZMETLER.items() if edevlet.kat(il) in bos]
    secilen.sort(key=lambda x: (x[1] is not None, x[0]))      # il geneli (büyükşehir) önce: tek hizmet bütün ili kapsar
    print(",".join(s for s, _ in secilen))
    return 0


def il_listesi():
    print(",".join(durum_oku().get("bos_iller", [])))
    return 0


def rapor():
    d = durum_oku()
    turlar = d.get("onceki_turlar", [])
    if not turlar:
        print("Bosluk raporu: bugun tur kaydi yok")
        return 0
    baz = next((t for t in turlar if t.get("kaynak") == "tr-bosluk"), None) or next((t for t in turlar if t["saat"] >= "10:00"), turlar[0])
    sonra = [t for t in turlar if t["saat"] > baz["saat"]]
    b0 = set(baz.get("bos_iller", []))
    parca = [f"{baz['saat']}'da bos {len(b0)} il"]
    if sonra:
        ilk, son = sonra[0], sonra[-1]
        parca.append(f"{ilk['saat']} turu {len(b0 - set(ilk.get('bos_iller', [])))} doldurdu")
        parca.append(f"aksam ({son['saat']}) {len(b0 - set(son.get('bos_iller', [])))}")
        kalan = sorted(b0 & set(son.get("bos_iller", [])))
    else:
        parca.append("sonraki tur henuz yok")
        kalan = sorted(b0)
    parca.append(f"hic dolmayan {len(kalan)} ({', '.join(kalan) or '-'})")
    print("; ".join(parca))
    return 0


def main():
    for bayrak, f in (("--tespit", tespit), ("--oncelik", oncelik), ("--il-listesi", il_listesi), ("--rapor", rapor)):
        if bayrak in sys.argv:
            return f()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
