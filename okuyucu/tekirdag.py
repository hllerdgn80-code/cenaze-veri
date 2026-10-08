#!/usr/bin/env python3
"""Tekirdağ: Tekirdağ BŞB'nin listesi yok; ilçe düzeyinde 2 ilçe belediyesi (her biri ayrı kaynak):
- Süleymanpaşa: `suleymanpasa.bel.tr/vefat-edenler` tek sayfa, 1.900+ satır (1,5 MB), yeniden eskiye: parça parça okunur, pencere dışına
  çıkınca bağlantı kesilir (tek istek). Sütunlar: ad, vefat tarihi, "VAKİT GG.AA.YYYY" (defin), defin yeri (cami + mezarlık). Gün = defin tarihi.
- Muratlı: `muratli.bel.tr/vefat-edenler` kartlar: ad, "Vefat Tarihi : GG/AA/YYYY", serbest ilan metni. Yakın adları ALINMAZ;
  yalnız "X mahallesi sakinlerinden" ve "Cenazesi ..." cümlesi. Gün = vefat tarihi (ilanda "bugün").
Kullanım: python3 okuyucu/tekirdag.py [--gun 7] [--ilce Muratlı]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Tekirdağ"

SULEYMANPASA = "https://suleymanpasa.bel.tr/vefat-edenler"


def _sp_satirlari(sayfa):
    govde = sayfa.split("<tbody>", 1)[-1]
    out = []
    for tr in re.findall(r"<tr>([\s\S]*?)</tr>", govde):
        td = [oi.metin(x) for x in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr)]
        if len(td) >= 4:
            out.append(td)
    return out


def suleymanpasa(ctx):
    bas = ctx["gunler"][-1]

    def yeterli(txt):
        d = [oi.tarih(x) for x in re.findall(r"<td\s+data-order=\"\d+\"\s*>\s*(\d\d/\d\d/\d{4})", txt)]
        d = [x for x in d if x]
        return len(d) >= 3 and all(x < bas for x in d[-3:])
    sayfa = oi.al_parca(SULEYMANPASA, yeterli)
    sonuc = []
    for ad, vef, defin_s, yer in _sp_satirlari(sayfa):
        vef = oi.tarih(vef)
        m = re.match(r"(\S+)\s+([\d./]+)", defin_s)
        vakit, defin = (m.group(1), oi.tarih(m.group(2))) if m else (None, oi.tarih(defin_s))
        gun = defin or vef
        ad = oi.ad_duzelt(ad)
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        sonuc.append(oi.kayit(IL, "Süleymanpaşa", "tekirdag-suleymanpasa", ad, gun, "Süleymanpaşa Belediyesi", SULEYMANPASA,
                              ctx["alindi"], ek_id=str(vef), vefat_tarihi=vef,
                              defin_yeri=ortak.tr_title(yer.replace("̇", "")) or None, defin_zamani=defin,
                              namaz_tarihi=defin, namaz_yeri_vakti=ortak.tr_title(vakit) if vakit else None, liste_tarihi=gun, ham={}))
    return sonuc


MURATLI = "https://www.muratli.bel.tr/vefat-edenler"


def muratli(ctx):
    sayfa = oi.al(MURATLI)
    kartlar = re.findall(r"<h3>([^<]+)</h3></div>\s*<div[^>]*><h3>\s*Vefat Tarihi\s*:\s*([\d/.]+)\s*</h3></div>\s*<div class='clear'></div>\s*"
                         r"<p>([\s\S]*?)</p>", sayfa)
    if not kartlar:
        raise RuntimeError("kart bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for ad, vef, p in kartlar:
        ad = oi.ad_duzelt(ad)
        vef = oi.tarih(vef)
        txt = oi.metin(p)
        namaz, defin = oi.cenaze_ayikla(txt)
        if not ad or not vef:
            continue
        sonuc.append(oi.kayit(IL, "Muratlı", "tekirdag-muratli", ad, vef, "Muratlı Belediyesi", MURATLI, ctx["alindi"],
                              il_disi_metin=txt, mahalle=oi.mahalle_ayikla(txt), vefat_tarihi=vef, defin_yeri=defin,
                              namaz_tarihi=vef if namaz else None, namaz_yeri_vakti=namaz, liste_tarihi=vef, ham={}))
    return sonuc


def main():
    oi.il_calistir(IL, "tekirdag", [("Süleymanpaşa", suleymanpasa), ("Muratlı", muratli)])


if __name__ == "__main__":
    main()
