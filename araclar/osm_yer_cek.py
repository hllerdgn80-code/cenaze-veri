#!/usr/bin/env python3
"""H61 (15.10.2026): Overpass (ODbL) -> il il {c: mezarlik merkezleri, b: ilce sinirlari (out geom), p: yerlesim adlari (mahalle/koy/belde noktalari)}.
Kullanim: python3 araclar/osm_yer_cek.py <onbellek_klasoru> <il_slug> [<il_slug> ...]
Nazik: il basina 3 sorgu, aralarinda >=10 sn; 429/504'te 60 sn bekleyip yeniden dener; var olan onbellek dosyasi atlanir.
Sonra: araclar/mezarlik_ilce_uret.py <onbellek> (c+b) ve araclar/mahalle_ilce_uret.py <onbellek> (p+b)."""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
UA = "KiminCenazesi/arastirma (iletisim@kimincenazesi.com)"
PL = "Adana Adıyaman Afyonkarahisar Ağrı Amasya Ankara Antalya Artvin Aydın Balıkesir Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli Diyarbakır Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane Hakkari Hatay Isparta Mersin İstanbul İzmir Kars Kastamonu Kayseri Kırklareli Kırşehir Kocaeli Konya Kütahya Malatya Manisa Kahramanmaraş Mardin Muğla Muş Nevşehir Niğde Ordu Rize Sakarya Samsun Siirt Sinop Sivas Tekirdağ Tokat Trabzon Tunceli Şanlıurfa Uşak Van Yozgat Zonguldak Aksaray Bayburt Karaman Kırıkkale Batman Şırnak Bartın Ardahan Iğdır Yalova Karabük Kilis Osmaniye Düzce".split()
HOSTLAR = ["https://overpass-api.de/api/interpreter", "https://overpass.openstreetmap.fr/api/interpreter"]   # fr yansisi alan (area) sorgusunda BOS donebilir -> bos sonuc basarisizdir


def slug(a):
    for x, y in zip("çğıöşüÇĞİÖŞÜI", "cgiosucgiosui"):
        a = a.replace(x, y)
    return a.lower()


def ov(q):
    """curl ile (Python 3.9/LibreSSL Overpass'a TLS el sikismasinda dusuyor: 15.10.2026)."""
    import subprocess
    for t in range(6):
        h = HOSTLAR[t % 2]
        try:
            r = subprocess.run(["curl", "-s", "-m", "300", "-A", UA, "--data-urlencode", "data=" + q, h], capture_output=True, timeout=320)
            if r.returncode == 0 and r.stdout.lstrip().startswith(b"{"):
                return json.loads(r.stdout)
            print("curl", r.returncode, r.stdout[:120], flush=True)
        except Exception as e:
            print("ERR", e, flush=True)
        time.sleep(60)


if __name__ == "__main__":
    cikti = sys.argv[1]; os.makedirs(cikti, exist_ok=True)
    for s in sys.argv[2:]:
        i = next(j for j, p in enumerate(PL) if slug(p) == s)
        f = os.path.join(cikti, f"{s}.json")
        if os.path.exists(f):
            continue
        A = f'area["ISO3166-2"="TR-{i + 1:02d}"]->.il;'
        c = ov(f'[out:json][timeout:200];{A}(nwr["landuse"="cemetery"]["name"](area.il);nwr["amenity"="grave_yard"]["name"](area.il););out tags center;'); time.sleep(10)
        b = ov(f'[out:json][timeout:250];{A}rel(area.il)["boundary"="administrative"]["admin_level"="6"];out geom;'); time.sleep(10)
        p = ov(f'[out:json][timeout:250];{A}(nwr["place"~"^(village|hamlet|suburb|neighbourhood|quarter|town|locality|isolated_dwelling)$"]["name"](area.il););out tags center;'); time.sleep(10)
        if c is None or b is None or p is None or not (b["elements"] and p["elements"]):   # ilce siniri ya da yerlesim yoksa bos yansi cevabi
            if b is not None and not b["elements"]:
                print("BOS CEVAP (yansi?)", s, flush=True)
            print("FAIL", s, flush=True); continue
        json.dump({"il": PL[i], "c": c["elements"], "b": b["elements"], "p": p["elements"]}, open(f, "w"), ensure_ascii=False)
        print("OK", s, len(c["elements"]), len(b["elements"]), len(p["elements"]), flush=True)
