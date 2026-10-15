#!/usr/bin/env python3
"""Zorunlu güncelleme kapısı: site/surum.json'u yazar ve depoya yükler (URUN-TASLAGI §42).
  python3 araclar/surum_yayinla.py --min 16 --son 16 --surum 0.1.7 [--mesaj "..."] [--kuru]
min: bu build'den KÜÇÜK her kurulum kapıya takılır (Play'e yeni sürüm yayında göründükten SONRA verin).
son: bundan küçük kurulumlar ana ekranda 'Yeni sürüm var' çubuğu görür (kapı değil). Sıfırlamak için --min 0.
Build numarası = android.yml'deki github.run_number (Play'deki sürüm kodu)."""
import argparse, datetime, json, pathlib, subprocess, sys

KOK = pathlib.Path(__file__).resolve().parent.parent
DOSYA = KOK / "site" / "surum.json"
VARSAYILAN = "Yeni bir sürüm yayımlandı. Devam etmek için güncelleyin."

a = argparse.ArgumentParser()
a.add_argument("--min", type=int, required=True)
a.add_argument("--son", type=int, required=True)
a.add_argument("--surum", required=True)
a.add_argument("--mesaj", default=VARSAYILAN)
a.add_argument("--kuru", action="store_true", help="yalnız dosyayı yaz, yükleme")
g = a.parse_args()
if g.min > g.son:
    sys.exit("HATA: --min, --son'dan büyük olamaz")
d = {"min_build": g.min, "son_build": g.son, "son_surum": g.surum, "mesaj": g.mesaj,
     "guncelleme": datetime.date.today().isoformat()}
DOSYA.write_text(json.dumps(d, ensure_ascii=False) + "\n", encoding="utf-8")
print("yazıldı:", DOSYA, d)
if not g.kuru:
    subprocess.check_call([sys.executable, str(KOK / "araclar" / "github_api.py"), "--yaz", str(DOSYA), "site/surum.json",
                           "-m", "surum.json: min %d son %d (%s)" % (g.min, g.son, g.surum)])
