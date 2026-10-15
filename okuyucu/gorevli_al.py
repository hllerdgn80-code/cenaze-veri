#!/usr/bin/env python3
"""DİN GÖREVLİSİ İLANI okuyucusu (15.10.2026; URUN-TASLAGI §37). Worker: GET <AILE_WORKER_URL>/gorevli/<il_slug>.json (81 il). aile_al.py kalıbı.
AILE_WORKER_URL tanımlı değilse SESSİZCE çıkar. Çıktı: veri/<il>/_ulusal.json içindeki `gorevli: true` kayıtları YENİLENİR (öteki kayıtlara dokunulmaz).
Kayıt: ortak.ALANLAR + gorevli/gorev_yeri/cinsiyet/dogrulandi; kaynak_ad "gorevli", kaynak_url = Worker adresi (kapi.py K7 'gorevli' için yalnız https ister).
Worker çıktısında başvuran/e-posta zaten yok; burada da yalnız beyaz listedeki alanlar alınır. Kullanım: python3 okuyucu/gorevli_al.py [--kuru]
GÖZETİM ÇAPRAZ KONTROLÜ: PANEL_ANAHTARI ortamda varsa, ilk 7 gündeki (listede olmayan) hesapların ilanları veri/<il>/_ulusal.json içindeki
BAŞKA kaynaklı kayıtlarla (ad + ±3 gün) karşılaştırılır; sonuç Worker'a (/gorevli/capraz) yazılır — yalnız bilgi, sahibi kuyruğunda görünür."""
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
    r.update({"id": "gorevli-" + str(k.get("id"))[:32], "il": IL_ADI[slug], "ilce": ilce, "mahalle": temiz(k.get("mahalle")), "ad_soyad": ortak.tr_title(ad),
              "yas": k.get("yas") if isinstance(k.get("yas"), int) else None, "vefat_tarihi": vef, "namaz_tarihi": nam,
              "namaz_yeri_vakti": temiz(k.get("namaz_yeri_vakti")), "defin_yeri": temiz(k.get("defin_yeri")), "liste_tarihi": nam,
              "kaynak_ad": "gorevli", "kaynak_url": url, "alindi": alindi, "ham": {"tarih_kaynagi": "gorevli_beyan"},
              "il_disi_defin": None, "ilce_belirsiz": False})
    r["gorevli"] = True
    r["gorev_yeri"] = temiz(k.get("gorev_yeri"))
    if k.get("sehit") is True:                      # ŞEHİT ilanı yalnız din görevlisi panelinden gelir (15.10.2026); §27 alanları
        r["sehit"] = True
        r["rutbe"] = temiz(k.get("rutbe"))
        r["toren"] = temiz(k.get("toren"))
    r["cinsiyet"] = k.get("cinsiyet") if k.get("cinsiyet") in ("e", "k") else None
    r["dogrulandi"] = k.get("dogrulandi") is True
    return r


def capraz(taban, anahtar, kuru):
    """Gözetimdeki ilanları başka kaynaklı kayıtlarla karşılaştırır (bilgi amaçlı; yayını etkilemez)."""
    basl = {"x-gizli": anahtar, "Accept": "application/json"}
    try:
        bekleyen = json.loads(ortak.indir(f"{taban}/gorevli/capraz", bekle=BEKLE, basliklar=basl)).get("ilanlar") or []
    except Exception as e:
        print(f"  gorevli capraz okunamadi {str(e)[:60]}", file=sys.stderr)
        return
    sonuc = []
    for i in bekleyen:
        slug = ortak.katla(i.get("il") or "").replace(" ", "")
        try:
            veri = json.load(open(os.path.join(VERI, slug, "_ulusal.json"), encoding="utf-8")).get("kayitlar", [])
        except Exception:
            veri = []
        ad = ortak.katla(i.get("ad_soyad") or "")
        v = i.get("vefat_tarihi") or ""
        eslesti = False
        for x in veri:
            if x.get("gorevli") or x.get("aile") or ortak.katla(x.get("ad_soyad") or "") != ad:
                continue
            t = x.get("namaz_tarihi") or x.get("liste_tarihi") or x.get("vefat_tarihi") or ""
            try:
                from datetime import date
                if abs((date.fromisoformat(t) - date.fromisoformat(v)).days) <= 3:
                    eslesti = True
                    break
            except Exception:
                continue
        sonuc.append({"ilan_id": i.get("ilan_id"), "eslesti": eslesti})
    if sonuc and not kuru:
        try:
            ortak.indir(f"{taban}/gorevli/capraz", bekle=BEKLE, veri=json.dumps({"sonuclar": sonuc}).encode(), basliklar={**basl, "Content-Type": "application/json"})
        except Exception as e:
            print(f"  gorevli capraz yazilamadi {str(e)[:60]}", file=sys.stderr)
    print(f"gorevli capraz: {len(sonuc)} ilan, {sum(1 for x in sonuc if x['eslesti'])} eşleşme")


def main():
    taban = os.environ.get("AILE_WORKER_URL", "").strip().rstrip("/")
    if not taban:
        return
    kuru = "--kuru" in sys.argv
    alindi, bugun = ortak.simdi_iso(), bugun_tr()
    toplam, hatali = 0, 0
    for slug in sorted(IL_ADI):
        url = f"{taban}/gorevli/{slug}.json"
        try:
            d = json.loads(ortak.indir(url, bekle=BEKLE, basliklar={"Accept": "application/json"}))
        except Exception as e:
            hatali += 1
            print(f"  gorevli {slug}: okunamadı {str(e)[:60]}", file=sys.stderr)
            continue                                     # okunamayan ilin eski aile kayıtları KORUNUR (Worker geçici hata)
        yeni = [r for r in (kayit(k, slug, url, alindi, bugun) for k in (d.get("kayitlar") or []) if isinstance(k, dict)) if r]
        yol = os.path.join(VERI, slug, "_ulusal.json")
        try:
            mevcut = json.load(open(yol, encoding="utf-8"))
        except Exception:
            mevcut = {"il": IL_ADI[slug], "kayitlar": []}
        digerleri = [x for x in mevcut.get("kayitlar", []) if not x.get("gorevli")]
        if not yeni and len(digerleri) == len(mevcut.get("kayitlar", [])):
            continue                                     # yazacak/temizlenecek bir şey yok
        toplam += len(yeni)
        if not kuru:
            mevcut["kayitlar"] = digerleri + yeni
            mevcut["guncelleme"] = alindi
            ortak.json_yaz(yol, mevcut)
    print(f"gorevli ilanları: {toplam} kayıt" + (f", {hatali} il okunamadı" if hatali else "") + (" (kuru)" if kuru else ""))


if __name__ == "__main__":
    main()
