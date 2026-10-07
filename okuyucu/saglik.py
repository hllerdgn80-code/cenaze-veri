#!/usr/bin/env python3
"""Sağlık denetimi: veri/ozet.json'u okur, veri/saglik.json yazar, sorun varsa ::warning:: basar.
Kullanım: python3 okuyucu/saglik.py [onceki_ozet.json]   Çıkış kodu HER ZAMAN 0 (iş başarısız olmaz).
Kontroller: (1) hata veren iller, (2) son 7 günde 0 kayıt veren iller,
(3) önceki özete göre toplam kayıt %40'tan fazla düştüyse."""
import json, os, sys

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri")


def yukle(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    ozet = yukle(os.path.join(KOK, "ozet.json")) or {"iller": {}}
    onceki = yukle(sys.argv[1]) if len(sys.argv) > 1 else None
    iller = ozet.get("iller", {})
    hatali = {k: v.get("hata") for k, v in iller.items() if v.get("hata")}
    sifir = [k for k, v in iller.items() if not v.get("hata") and (v.get("kayit_sayisi") or 0) == 0]
    toplam = sum(v.get("kayit_sayisi") or 0 for v in iller.values())
    onceki_toplam = sum((v.get("kayit_sayisi") or 0) for v in (onceki or {}).get("iller", {}).values()) if onceki else None
    dusus = None
    if onceki_toplam:
        dusus = round((onceki_toplam - toplam) / onceki_toplam * 100, 1)
    sorunlar = []
    if hatali:
        sorunlar.append(f"{len(hatali)} il hata verdi: " + ", ".join(f"{k} ({str(h)[:60]})" for k, h in hatali.items()))
    if sifir:
        sorunlar.append(f"{len(sifir)} ilde son 7 günde 0 kayıt: " + ", ".join(sifir))
    if dusus is not None and dusus > 40:
        sorunlar.append(f"toplam kayıt önceki çalışmaya göre %{dusus} düştü ({onceki_toplam} -> {toplam})")
    cikti = {"guncelleme": ozet.get("guncelleme"), "il_sayisi": len(iller), "toplam_kayit": toplam,
             "onceki_toplam": onceki_toplam, "dusus_yuzde": dusus, "hatali_iller": hatali,
             "sifir_kayitli_iller": sifir, "sorunlar": sorunlar, "saglikli": not sorunlar}
    os.makedirs(KOK, exist_ok=True)
    with open(os.path.join(KOK, "saglik.json"), "w", encoding="utf-8") as f:
        json.dump(cikti, f, ensure_ascii=False, indent=1)
    for s in sorunlar:
        print(f"::warning title=Cenaze veri sağlığı::{s}")
    print("sağlık:", "temiz" if not sorunlar else f"{len(sorunlar)} sorun", f"| toplam {toplam}")


if __name__ == "__main__":
    main()
