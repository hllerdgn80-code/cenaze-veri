#!/usr/bin/env python3
"""GÜNLÜK DENETİM KAYDI (16.10.2026 H86; sahibi: "bir önceki günün performansını değerlendirip bozuk kısımları düzeltecek düzenek").
Her topla.yml turunun sonunda (birlestir işi) iç verilerden tek bir JSON üretir: deploy/denetim/<YYYY-MM-DD>.json (gün içinde üstüne yazılır,
akşam turu depoya commit eder). Bulut onarım rutini (claude.ai/code routines, 21:30 TR) bu dosyayı ve HATA-TESHIS-KILAVUZU.md'yi okuyup
bozuk okuyucuları onarır. İçerik: il başına iç/yayın kayıt, bugün/dün sayıları, boş iller, süzgeç nedenleri (_yayin_uyari), sessiz kaynaklar
(_kaynak_uyari / _kaynak_sayac varsa), defter durumu (yeni_kayit), kapı elemeleri (ozet.kapi_elenen), hata veren iller (ozet.hata).
Kullanım: python3 okuyucu/gunluk_denetim.py veri site/veri deploy/denetim"""
import datetime, json, os, sys


def oku(yol, varsayilan=None):
    try:
        return json.load(open(yol, encoding="utf-8"))
    except Exception:
        return varsayilan


def gun(r):
    return r.get("namaz_tarihi") or (r.get("defin_zamani") or "")[:10] or r.get("liste_tarihi") or r.get("vefat_tarihi") or ""


def main():
    ic, yayin, hedef = sys.argv[1], sys.argv[2], sys.argv[3]
    tr = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    bugun, dun = tr.date().isoformat(), (tr.date() - datetime.timedelta(days=1)).isoformat()
    oz_ic = oku(os.path.join(ic, "ozet.json"), {}).get("iller", {})
    oz_y = oku(os.path.join(yayin, "ozet.json"), {}).get("iller", {})
    iller = {}
    for il in sorted(set(oz_ic) | set(oz_y)):
        v = oku(os.path.join(yayin, il, "son7gun.json"), {}) or {}
        L = [r for l in (v.get("ilceler") or {}).values() for r in l] + (v.get("il_disi") or []) + (v.get("ilce_belirsiz") or [])
        iller[il] = {"ic": int((oz_ic.get(il) or {}).get("kayit_sayisi") or 0), "yayin": int((oz_y.get(il) or {}).get("kayit_sayisi") or 0),
                     "bugun": sum(1 for r in L if gun(r) == bugun), "dun": sum(1 for r in L if gun(r) == dun),
                     "hata": (oz_ic.get(il) or {}).get("hata"), "kapi_elenen": (oz_ic.get(il) or {}).get("kapi_elenen"),
                     "son_calisma": (oz_ic.get(il) or {}).get("son_calisma")}
    bos = [il for il, x in iller.items() if x["bugun"] == 0 and x["dun"] == 0]
    kayip = [il for il, x in iller.items() if x["ic"] >= 5 and x["yayin"] < x["ic"] / 2]
    defter = oku(os.path.join(ic, "_defter_durum.json"), {}) or {}
    out = {
        "tarih": tr.isoformat(timespec="minutes"), "il_sayisi": len(iller),
        "bugun_kaydi_olan_il": sum(1 for x in iller.values() if x["bugun"] > 0), "bugun_toplam": sum(x["bugun"] for x in iller.values()),
        "dun_toplam": sum(x["dun"] for x in iller.values()), "bos_iller": bos, "yayin_kaybi_iller": kayip,
        "hata_veren_iller": {il: x["hata"] for il, x in iller.items() if x.get("hata")},
        "suzgec": oku(os.path.join(ic, "_yayin_uyari.json"), {}),
        "sessiz_kaynaklar": oku(os.path.join(ic, "_kaynak_uyari.json"), None),
        "kaynak_sayac": oku(os.path.join(ic, "_kaynak_sayac.json"), None),
        "defter_yeni_kayit": (defter.get("yeni_kayit") or {}) if isinstance(defter, dict) else {},
        "defter_mac_gerekli": (defter.get("mac_gerekli") or {}) if isinstance(defter, dict) else {},
        "iller": iller,
    }
    os.makedirs(hedef, exist_ok=True)
    yol = os.path.join(hedef, bugun + ".json")
    json.dump(out, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[denetim] {yol}: bugün kaydı olan il {out['bugun_kaydi_olan_il']}/{len(iller)} · bugün {out['bugun_toplam']} · dün {out['dun_toplam']} · boş il {len(bos)} · yayın kaybı {kayip}")


if __name__ == "__main__":
    main()
