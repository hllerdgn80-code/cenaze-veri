#!/usr/bin/env python3
"""H66 ölçüm: resmî mezarlık sözlüğü (okuyucu/veri/mezarlik_resmi.json) katmanı öncesi/sonrası ilçeli kayıt sayısı.
Kullanım: python3 araclar/ilce_resmi_olc.py <canli_klasor> [--ornek N]   (canli_klasor: <il_slug>.json = canlı son7gun kopyaları; salt okur)
Önce = depodaki TÜM katmanlar, resmî katman kapalı (ortak.RESMI_ETKIN=False); Sonra = resmî katman açık. Aynı kayıt kopyaları üzerinde."""
import collections, copy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okuyucu"))
import ilce_anatomi as A
import ortak


def coz(k, il, etkin):
    ortak.RESMI_ETKIN = etkin
    k2 = copy.deepcopy(k)
    if k2.get("ilce") == "İlçe belirtilmemiş":
        k2["ilce"] = None
    ham = k2.get("ham") if isinstance(k2.get("ham"), dict) else {}
    ham.pop("ilce_kaynagi", None)
    k2["ham"] = ham
    k2.pop("ilce_kaynagi", None)
    if not k2.get("ilce"):
        k2["ilce_belirsiz"] = True
        k2["il_disi_defin"] = k2.get("il_disi_defin")
    return ortak.ilce_isle(k2, il)


def main():
    hepsi = A.yukle(sys.argv[1])
    toplam = len(hepsi)
    bel = [(il, k) for il, ilce, k in hepsi if ilce.startswith("İlçe belirt")]
    once = sonra = 0
    il_say = collections.Counter()
    ornek = []
    for il, k in bel:
        a, b = coz(k, il, False), coz(k, il, True)
        if a.get("ilce") or a.get("il_disi_defin"):
            once += 1
        if b.get("ilce") or b.get("il_disi_defin"):
            sonra += 1
            if not (a.get("ilce") or a.get("il_disi_defin")):
                il_say[il] += 1
                ornek.append((il, k.get("defin_yeri"), b.get("ilce")))
    ortak.RESMI_ETKIN = True
    ilceli_once = toplam - len(bel)
    print(f"toplam kayıt {toplam}; canlıda ilçesiz {len(bel)}")
    print(f"depo kodu (resmî katman KAPALI) ilçesiz kalandan çözer: {once}  -> ilçeli {ilceli_once + once}")
    print(f"resmî katman AÇIK çözer: {sonra}  (katmanın ek kazancı: {sonra - once})  -> ilçeli {ilceli_once + sonra}")
    print("ek kazanç il bazında:", dict(il_say))
    for o in ornek[: (int(sys.argv[sys.argv.index('--ornek') + 1]) if '--ornek' in sys.argv else 10)]:
        print("  ", o)
    t = ortak.resmi_tablo()
    print("sözlük kapsamı:", {il: len(v) for il, v in t.items()}, "toplam ad:", sum(len(v) for v in t.values()))


if __name__ == "__main__":
    main()
