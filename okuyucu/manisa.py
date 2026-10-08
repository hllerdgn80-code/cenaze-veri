#!/usr/bin/env python3
"""Manisa: il ve ilçe belediyelerinde liste yok (MBS API robots ile kapalı) -> YEREL BASIN (site sahibi kararı 08.10.2026).
- Akhisar Haber (akhisarhaber.net): "Vefat Edenler" bölümü; kişi başına bir ilan sayfası `/vefat/<ad-soyad>/<no>` (günde ~1-2).
  Bölümün liste sayfası yok (410): dizin aylık site haritası `sitemap-YYYY-AA.xml` (tek istek), günde en çok 2 ilan sayfası.
  Alınan: ad soyad (ilan başlığı), mahalle ("X MAHALLESİNDEN"), cami + vakit (kısa), mezarlık; ev adresi, yakın adları ALINMAZ.
  İlanda tarih yoksa yayın günü namaz günü sayılır (ham.tarih_kaynagi = yayin_tarihi). İlçe yazılmıyorsa belirsiz.
Site başına günde en çok 3 istek (ortak_basin). Kullanım: python3 okuyucu/manisa.py [--gun 7]
"""
import os, re, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak_basin as ob, ortak_ilce as oi

IL = "Manisa"


def akhisar_haber(ctx):
    xml = ob.dizin(ctx, f"https://www.akhisarhaber.net/sitemap-{date.today():%Y-%m}.xml")
    if xml is None:
        return []
    sayfalar = sorted([(u, g) for u, t, g in ob.harita_ogeleri(xml) if "/vefat/" in u], key=lambda x: x[1] or "", reverse=True)

    def ayristir(sayfa, url, gun):
        gun = ob.yayin_tarihi(sayfa) or gun
        ad, _ = ob.ad_bul(ob.baslik_ad(sayfa, "Akhisar Haber"))
        if not ad:
            return []
        govde = ob.makale_govdesi(sayfa)
        cumle = ob.cenaze_cumlesi(govde)
        namaz, defin = oi.cenaze_ayikla(cumle) if cumle else (None, None)
        defin_t = ob.metinden_tarih(cumle) if cumle else None
        k = ob.kayit(ctx, IL, "manisa-akhisarhaber", "Akhisar Haber", url, ad, defin_t or gun,
                     ilce=ob.ilce_bul(IL, govde, 3), ek_id=gun or "",
                     namaz_tarihi=None if defin_t else gun, defin_zamani=defin_t,
                     namaz_yeri_vakti=ob.namaz_kisa(cumle), defin_yeri=ob.kisa(defin), mahalle=ob.kisa(ob.mahalle_temiz(govde)),
                     ham={"sayfa_tarihi": gun, "tarih_kaynagi": "metin" if defin_t else "yayin_tarihi"})
        dis = ob.il_disi_bul(IL, cumle)
        if dis:
            k["il_disi_defin"] = {"il": dis, "ilce": None}
            k["ilce_belirsiz"] = False
        return [k]
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def main():
    oi.il_calistir(IL, "manisa", [("Akhisar Haber", akhisar_haber)])


if __name__ == "__main__":
    main()
