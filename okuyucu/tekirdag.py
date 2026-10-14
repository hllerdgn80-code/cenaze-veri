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


BB = "https://www.tekirdag.bel.tr/merhumlar"
BB_ATLA = {"suleymanpasa", "muratli"}      # bu iki ilçe kendi sayfalarından zaten okunuyor (çift kayıt olmasın)


def buyuksehir(ctx):
    """Tekirdağ BB 'Vefat Edenler - Güncel liste' (14.10.2026 keşfi): il geneli, girişsiz/CAPTCHA'sız, yalnız güncel gün(ler).
    Sütunlar: ad, 'İLÇE / İL' (merkezde boş), vakit + tarih (defin), cami + mezarlık. Önceki günler kendi dosyalarımızdan tamamlanır."""
    sayfa = oi.al(BB)
    govde = sayfa.split('id="merhum-body"', 1)
    if len(govde) < 2:
        raise RuntimeError("liste gövdesi bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for tr in re.findall(r"<tr>([\s\S]*?)</tr>", govde[1]):
        ad = re.search(r'class="name">([^<]+)<', tr)
        yer = re.search(r'class="location">\s*([^<]*?)\s*<', tr)
        vakit = re.search(r'class="badge vakit">([^<]+)<', tr)
        gun = re.search(r'class="date">([^<]+)<', tr)
        cami = re.search(r'class="place">([^<]*)<', tr)
        mez = re.search(r'class="grave">([^<]*)<', tr)
        if not (ad and gun):
            continue
        ad = oi.ad_duzelt(oi.metin(ad.group(1)))
        gun = oi.tarih(gun.group(1))
        ilce = oi.metin(yer.group(1)).split("/")[0].strip() if yer else ""
        ilce = ortak.tr_title(ilce) if ilce else None
        if not ad or not gun or ortak.katla(ilce or "") in BB_ATLA:
            continue
        v = ortak.tr_title(oi.metin(vakit.group(1))) if vakit else None
        k = oi.kayit(IL, ilce, "tekirdag-bb", ad, gun, "Tekirdağ Büyükşehir Belediyesi", BB, ctx["alindi"],
                     ek_id=ortak.katla(ad) + gun + ortak.katla(ilce or ""), vefat_tarihi=None,
                     defin_yeri=oi.metin(mez.group(1)) if mez and mez.group(1).strip() else None, defin_zamani=gun,
                     namaz_tarihi=gun, namaz_yeri_vakti=((oi.buyuk_ise_title(oi.metin(cami.group(1)), yer=True) + (" - " + v if v else "")) if cami and cami.group(1).strip() else v),
                     liste_tarihi=gun, ham={})
        if not ilce:
            k["ilce_belirsiz"] = True
        sonuc.append(k)
    return sonuc


def main():
    oi.il_calistir(IL, "tekirdag", [("Süleymanpaşa", suleymanpasa), ("Muratlı", muratli), ("Büyükşehir", buyuksehir)])


if __name__ == "__main__":
    main()
