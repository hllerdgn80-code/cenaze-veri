#!/usr/bin/env python3
"""AILE İLANI okuyucusu (14.10.2026; deploy/AILE-ILAN-SOZLESME.md). Worker: GET <AILE_WORKER_URL>/aile/<il_slug>.json (81 il).
AILE_WORKER_URL tanımlı değilse SESSİZCE çıkar. Çıktı: veri/<il>/_ulusal.json içindeki `aile: true` kayıtları YENİLENİR (öteki kayıtlara dokunulmaz).
Kayıt: ortak.ALANLAR + aile/cinsiyet/dogrulandi; kaynak_ad "aile", kaynak_url = Worker adresi (kapi.py K7 'aile' için yalnız https ister).
Worker çıktısında başvuran/e-posta zaten yok; burada da yalnız beyaz listedeki alanlar alınır. Kullanım: python3 okuyucu/aile_al.py [--kuru]"""
import json, os, re, sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak
from vefatilan import ILCELER, IL_ADI, IL_SLUG, bugun_tr, kat

DIZIN = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(DIZIN, "..", "veri")
BEKLE = 0.4
TARIH = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def temiz(s, azami=60):
    s = re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else None
    return s if s and len(s) <= azami else None


def kayit(k, slug, url, alindi, bugun):
    """Worker kaydı -> iç kayıt; geçersizse None. namaz_tarihi bugün+2'den ileri ise bekletilir (kapı K3 penceresi)."""
    ad = temiz(k.get("ad_soyad"))
    vef, nam = k.get("vefat_tarihi"), k.get("namaz_tarihi")
    if not ad or not isinstance(vef, str) or not isinstance(nam, str) or not TARIH.match(vef) or not TARIH.match(nam):
        return None
    if nam > (bugun + timedelta(days=2)).isoformat() or nam < (bugun - timedelta(days=7)).isoformat():
        return None
    ilce = temiz(k.get("ilce"))
    if ilce != "Merkez" and ilce not in ILCELER[IL_ADI[slug]]:
        return None
    r = {a: None for a in ortak.ALANLAR}
    r.update({"id": "aile-" + str(k.get("id"))[:32], "il": IL_ADI[slug], "ilce": ilce, "mahalle": temiz(k.get("mahalle")), "ad_soyad": ortak.tr_title(ad),
              "yas": k.get("yas") if isinstance(k.get("yas"), int) else None, "vefat_tarihi": vef, "namaz_tarihi": nam,
              "namaz_yeri_vakti": temiz(k.get("namaz_yeri_vakti")), "defin_yeri": temiz(k.get("defin_yeri")), "liste_tarihi": nam,
              "kaynak_ad": "aile", "kaynak_url": url, "alindi": alindi, "ham": {"tarih_kaynagi": "aile_beyan"},
              "il_disi_defin": None, "ilce_belirsiz": False})
    r["aile"] = True
    r["cinsiyet"] = k.get("cinsiyet") if k.get("cinsiyet") in ("e", "k") else None
    r["dogrulandi"] = k.get("dogrulandi") is True
    return r


def main():
    taban = os.environ.get("AILE_WORKER_URL", "").strip().rstrip("/")
    if not taban:
        return
    kuru = "--kuru" in sys.argv
    alindi, bugun = ortak.simdi_iso(), bugun_tr()
    toplam, hatali = 0, 0
    for slug in sorted(IL_ADI):
        url = f"{taban}/aile/{slug}.json"
        try:
            d = json.loads(ortak.indir(url, bekle=BEKLE, basliklar={"Accept": "application/json"}))
        except Exception as e:
            hatali += 1
            print(f"  aile {slug}: okunamadı {str(e)[:60]}", file=sys.stderr)
            continue                                     # okunamayan ilin eski aile kayıtları KORUNUR (Worker geçici hata)
        yeni = [r for r in (kayit(k, slug, url, alindi, bugun) for k in (d.get("kayitlar") or []) if isinstance(k, dict)) if r]
        yol = os.path.join(VERI, slug, "_ulusal.json")
        try:
            mevcut = json.load(open(yol, encoding="utf-8"))
        except Exception:
            mevcut = {"il": IL_ADI[slug], "kayitlar": []}
        digerleri = [x for x in mevcut.get("kayitlar", []) if not x.get("aile")]
        if not yeni and len(digerleri) == len(mevcut.get("kayitlar", [])):
            continue                                     # yazacak/temizlenecek bir şey yok
        toplam += len(yeni)
        if not kuru:
            mevcut["kayitlar"] = digerleri + yeni
            mevcut["guncelleme"] = alindi
            ortak.json_yaz(yol, mevcut)
    print(f"aile ilanları: {toplam} kayıt" + (f", {hatali} il okunamadı" if hatali else "") + (" (kuru)" if kuru else ""))


if __name__ == "__main__":
    main()
