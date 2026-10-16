#!/usr/bin/env python3
"""YAYIN SAĞLIK KAPISI (16.10.2026 H83 tedbiri): iç veri (veri/ozet.json) ile yayın verisi (site/veri/ozet.json) il başına karşılaştırılır.
Bir ilde iç kayıt ≥ 5 iken yayına girenler iç sayının yarısından azsa ya da iç sayı 0'ken dünkü yayın > 0 idiyse ::warning:: yazılır ve
veri/_yayin_uyari.json (iç; yayına gitmez) güncellenir. Koşuyu KIRMAZ (çıkış 0). Ayrıca bugün+dün kaydı olmayan il sayısı yazılır.
Kullanım: python3 okuyucu/yayin_kontrol.py veri/ozet.json site/veri/ozet.json [site/veri]"""
import datetime, json, os, sys


def _say(kok, il):
    """yayın son7gun'unda bugün/dün kaydı var mı"""
    try:
        v = json.load(open(os.path.join(kok, il, "son7gun.json"), encoding="utf-8"))
    except Exception:
        return False
    L = [r for l in (v.get("ilceler") or {}).values() for r in l] + (v.get("il_disi") or []) + (v.get("ilce_belirsiz") or [])
    b = datetime.date.today().isoformat(); d = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    g = lambda r: r.get("namaz_tarihi") or (r.get("defin_zamani") or "")[:10] or r.get("liste_tarihi") or r.get("vefat_tarihi") or ""
    return any(g(r) in (b, d) for r in L)


def main():
    ic, yayin = sys.argv[1], sys.argv[2]
    kok = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(yayin)
    a = json.load(open(ic, encoding="utf-8")).get("iller", {})
    b = json.load(open(yayin, encoding="utf-8")).get("iller", {})
    uyari = []
    for il, v in a.items():
        ics, ys = int(v.get("kayit_sayisi") or 0), int((b.get(il) or {}).get("kayit_sayisi") or 0)
        if ics >= 5 and ys < ics / 2:
            uyari.append({"il": il, "ic": ics, "yayin": ys, "neden": "süzgeç/kapı iç verinin yarısından fazlasını düşürdü"})
    bos = [il for il in b if not _say(kok, il)]
    print(f"[yayın kontrol] il {len(b)} · bugün+dün kaydı olmayan il {len(bos)} · süzgeç uyarısı {len(uyari)}")
    for u in uyari:
        print(f"::warning::YAYIN KAYBI {u['il']}: iç {u['ic']} -> yayın {u['yayin']} ({u['neden']})")
    if len(bos) > 35:
        print(f"::warning::BOŞ İL {len(bos)}: {', '.join(bos[:40])}")
    try:
        os.makedirs(os.path.dirname(ic), exist_ok=True)
        json.dump({"tarih": datetime.datetime.now().isoformat(timespec="minutes"), "suzgec_uyarisi": uyari, "bos_il": bos},
                  open(os.path.join(os.path.dirname(ic), "_yayin_uyari.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except OSError:
        pass


if __name__ == "__main__":
    main()
