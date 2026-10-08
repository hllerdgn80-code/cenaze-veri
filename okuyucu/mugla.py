#!/usr/bin/env python3
"""Muğla: Muğla BŞB'nin listesi yok; ilçe düzeyinde okunan 5 ilçe belediyesi (her biri ayrı kaynak):
- Bodrum: `bodrum.bel.tr/vefat?page=N` (20 satır/sayfa: vefat tarihi, ad, yaş, defin tarihi/zamanı/yeri, nakil yeri). Doğum yeri alınmaz.
- Milas: `milas.bel.tr/VefatEdenler?kayitSayisi=10&sayfa=N` (TLS: sertifika/ilce-zincir.pem). Kart: vefat tarihi, ad, yaş, defin tarihi/zamanı/yeri.
- Fethiye: `fethiye.bel.tr/vefatedeneler` ASP.NET GridView (20 satır/sayfa; sayfalar __doPostBack ile). Doğum tarihi GÖSTERİLMEZ (yalnız yaş hesaplanır).
- Seydikemer: `seydikemer.bel.tr/AnaSayfa/VefatEdenler` (son ~10 kayıt tablosu). Tabloda ÖLÜM NEDENİ ve taziye adresi sütunları var: ASLA alınmaz.
- Dalaman: `dalaman.bel.tr/vefat-edenler` (tablo + açılır ayrıntı metni; yalnız "Cenazesi ..." cümlesi alınır, ev adresi/yakın adı atılır).
Gün = defin tarihi (yoksa vefat tarihi). Kaynak ilçe alanı doldurulur. Kullanım: python3 okuyucu/mugla.py [--gun 7] [--ilce Bodrum,Milas]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9, ortak_ilce as oi

IL = "Muğla"


# ---------------------------------------------------------------- Bodrum
BODRUM = "https://www.bodrum.bel.tr/vefat"


def bodrum(ctx):
    def ayristir(sayfa, n):
        i = sayfa.find("Desktop Tablo")
        govde = sayfa[i:sayfa.find("</table>", i)]
        liste = []
        for tr in re.findall(r"<tr>([\s\S]*?)</tr>", govde)[1:]:
            vef = oi.tarih((re.search(r'date-badge">\s*([\d./]+)', tr) or [None, ""])[1])
            d = {oi.metin(a): oi.metin(b) for a, b in re.findall(r'info-label">([^<]*)</div>\s*<div class="info-value">([\s\S]*?)</div>', tr)}
            ad = oi.ad_duzelt(d.get("Adı:", ""))
            defin = oi.tarih(d.get("Defin Tarihi:", ""))
            nakil_t = oi.tarih(d.get("Nakil Tarihi:", ""))
            gun = defin or nakil_t or vef
            if not ad or not gun:
                continue
            nakil_yeri = d.get("Nakil Yeri:") or None
            liste.append(oi.kayit(IL, "Bodrum", "mugla-bodrum", ad, gun, "Bodrum Belediyesi", BODRUM, ctx["alindi"],
                                  ek_id=str(vef), yas=oi.say(d.get("Yaşı:", "")), vefat_tarihi=vef,
                                  defin_yeri=d.get("Defin Yeri:") or None, defin_zamani=defin, namaz_tarihi=defin,
                                  namaz_yeri_vakti=d.get("Defin Zamanı:") or None, liste_tarihi=gun,
                                  ham={"nakil_yeri": nakil_yeri, "nakil_tarihi": nakil_t}))
        return liste
    return oi.sayfala(lambda n: f"{BODRUM}?page={n}", ayristir, ctx["gunler"])


# ---------------------------------------------------------------- Milas
MILAS = "https://www.milas.bel.tr/VefatEdenler"


def milas(ctx):
    sb = oi.ssl_ilce()

    def ayristir(sayfa, n):
        liste = []
        for b in re.split(r'<div class="vefat-card">', sayfa)[1:]:
            vef = oi.tarih((re.search(r'Vefat Tarihi</div>\s*<div class="fw-semibold">\s*([\d./]+)', b) or [None, ""])[1])
            d = {oi.metin(a): oi.metin(v) for a, v in re.findall(r"<strong>([^<]*)</strong>([^<]*)</div>", b)}
            ad = oi.ad_duzelt(d.get("Adı:", ""))
            defin = oi.tarih(d.get("Defin Tarihi:", ""))
            gun = defin or vef
            if not ad or not gun:
                continue
            yer = d.get("Defin Yeri:") or None
            liste.append(oi.kayit(IL, "Milas", "mugla-milas", ad, gun, "Milas Belediyesi", MILAS, ctx["alindi"],
                                  ek_id=str(vef), yas=oi.say(d.get("Yaşı:", "")), vefat_tarihi=vef,
                                  defin_yeri=yer, defin_zamani=defin, namaz_tarihi=defin,
                                  namaz_yeri_vakti=d.get("Defin Zamanı:") or None, liste_tarihi=gun, ham={}))
        return liste
    return oi.sayfala(lambda n: f"{MILAS}?kayitSayisi=10&sayfa={n}", ayristir, ctx["gunler"], ssl_baglam=sb, azami_sayfa=4)


# ---------------------------------------------------------------- Fethiye
FETHIYE = "https://www.fethiye.bel.tr/vefatedeneler"


def _fethiye_satirlari(sayfa, ctx):
    liste = []
    i = sayfa.find('id="ContentPlaceHolder1_gvVefat"')
    if i < 0:
        raise RuntimeError("GridView bulunamadı (sayfa düzeni değişmiş olabilir)")
    govde = sayfa[i:sayfa.find("</table>", i)]
    for tr in re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", govde):
        ad = re.search(r'lblAdi_\d+">([^<]*)<', tr)
        soyad = re.search(r'lblSoyadi_\d+">([^<]*)<', tr)
        if not ad:
            continue
        tur = oi.metin((re.search(r'lblTur_\d+"[^>]*>([\s\S]*?)</span>', tr) or [None, ""])[1])
        td = re.findall(r"<td>\s*([\d.]{10})\s*</td>", tr)           # doğum, ölüm, defin/nakil tarihi
        yer = oi.metin((re.search(r'lblYerAdi_\d+">([^<]*)<', tr) or [None, ""])[1])
        adsoyad = oi.ad_duzelt(f"{ad.group(1)} {soyad.group(1) if soyad else ''}")
        dogum, vef, defin = (oi.tarih(x) for x in (td + [None] * 3)[:3])
        gun = defin or vef
        if not adsoyad or not gun:
            continue
        liste.append(oi.kayit(IL, "Fethiye", "mugla-fethiye", adsoyad, gun, "Fethiye Belediyesi", FETHIYE, ctx["alindi"],
                              ek_id=f"{vef}|{dogum}", yas=oi.yas_hesapla(dogum, vef) if dogum and vef else None,
                              vefat_tarihi=vef, defin_yeri=yer or None, defin_zamani=defin, liste_tarihi=gun,
                              ham={"tur": tur or None}))        # doğum tarihi saklanmaz (kaynak gösterdiği için değil, yaş yeter)
    return liste


def fethiye(ctx):
    sb = None
    if not oi.robots_ok(FETHIYE):
        raise oi.Engel("robots.txt yasaklıyor")
    ot = ortak9.Oturum()
    sayfa = ot.get(FETHIYE)
    sonuc = []
    for n in range(1, 4):
        liste = _fethiye_satirlari(sayfa, ctx)
        icinde = [k for k in liste if oi.pencerede(k["liste_tarihi"], ctx["gunler"])]
        sonuc.extend(icinde)
        if not liste or len(icinde) < len(liste) or n == 3:
            break
        alanlar = {a: v for a, v in re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', sayfa)}
        import html as _h
        alanlar = {a: _h.unescape(v) for a, v in alanlar.items()}
        alanlar["__EVENTTARGET"] = "ctl00$ContentPlaceHolder1$gvVefat"
        alanlar["__EVENTARGUMENT"] = f"Page${n + 1}"
        sayfa = ot.post_form(FETHIYE, alanlar)
    return sonuc


# ---------------------------------------------------------------- Seydikemer
SEYDIKEMER = "https://www.seydikemer.bel.tr/AnaSayfa/VefatEdenler"


def seydikemer(ctx):
    sayfa = oi.al(SEYDIKEMER)
    baslik, satirlar = oi.tablo(sayfa)
    sonuc = []
    for s in satirlar:
        # ÖLÜM NEDENİ ("Ö. Nedeni") ve TAZİYE ADRESİ sütunları BİLEREK okunmaz.
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Ad Soyad"))
        mah = oi.kolon(baslik, s, "Mahalle")
        vef = oi.tarih(oi.kolon(baslik, s, "Ölüm Tarihi"))
        mezar = oi.kolon(baslik, s, "Defnedildiği Yer")
        if not ad or not vef:
            continue
        sonuc.append(oi.kayit(IL, "Seydikemer", "mugla-seydikemer", ad, vef, "Seydikemer Belediyesi", SEYDIKEMER, ctx["alindi"],
                              mahalle=oi.buyuk_ise_title(mah, yer=True) or None, vefat_tarihi=vef,
                              defin_yeri=oi.buyuk_ise_title(mezar, yer=True) or None, liste_tarihi=vef, ham={}))
    return sonuc


# ---------------------------------------------------------------- Dalaman
DALAMAN = "https://dalaman.bel.tr/vefat-edenler"


def dalaman(ctx):
    sayfa = oi.al(DALAMAN)
    baslik, satirlar = oi.tablo(sayfa)
    modal = oi.modal_govdeleri(sayfa)
    sonuc = []
    for i, s in enumerate(satirlar):
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
        baba = oi.ad_duzelt(oi.kolon(baslik, s, "Baba Adı"))
        vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
        yer = oi.kolon(baslik, s, "Vefat Yeri")
        det = modal[i] if i < len(modal) else ""
        namaz, defin = oi.cenaze_ayikla(det)
        dt = re.search(r"D\.?\s?T\.?\s*:?\s*(\d{4})", det)
        if not ad or not vef:
            continue
        sonuc.append(oi.kayit(IL, "Dalaman", "mugla-dalaman", ad, vef, "Dalaman Belediyesi", DALAMAN, ctx["alindi"],
                              mahalle=oi.buyuk_ise_title(yer, yer=True) or None, anne_baba=baba or None, vefat_tarihi=vef,
                              defin_yeri=defin, namaz_yeri_vakti=namaz,
                              liste_tarihi=vef, ham={"dogum_yili": dt.group(1) if dt else None}))
    return sonuc


def main():
    oi.il_calistir(IL, "mugla", [("Bodrum", bodrum), ("Milas", milas), ("Fethiye", fethiye),
                                 ("Seydikemer", seydikemer), ("Dalaman", dalaman)])


if __name__ == "__main__":
    main()
