#!/usr/bin/env python3
"""Hatay: Hatay BŞB'nin listesi yok; ilçe düzeyinde Dörtyol Belediyesi.
Dörtyol: `dortyol.bel.tr/vefat-edenler` liste + her gün için bir gün sayfası (`/GG-AA-YYYY`); günün sayfasında birden çok
"MERHUM(E): AD" bloğu var: DOĞUM TARİHİ (yalnız yaş hesaplanır), ÖLÜM TARİHİ, ANA ADI, BABA ADI, DEFİN YERİ, DEFİN TARİHİ.
TAZİYE ADRESİ, YAKINI ve TELEFON ALINMAZ. İstek sayısını küçük tutmak için son 2 gün her çalışmada, daha eski günler yalnız bir kez okunur.
Kullanım: python3 okuyucu/hatay.py [--gun 7]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Hatay"
LISTE = "https://www.dortyol.bel.tr/vefat-edenler"


def _blok_ayir(icerik):
    """Gün sayfasındaki <p> satırlarından kayıt sözlükleri: {'ad', 'dogum', 'olum', 'ana', 'baba', 'defin_yeri', 'defin'}."""
    satirlar = [oi.metin(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", icerik)]
    kayitlar, k = [], None
    for s in satirlar:
        m = re.match(r"^MERHUM[E]?\s*:\s*(.+)$", s, re.I)
        if m:
            if k:
                kayitlar.append(k)
            k = {"ad": m.group(1).strip()}
            continue
        if k is None:
            continue
        m = re.match(r"^([A-ZÇĞİÖŞÜ ]+?)\s*:\s*(.*)$", s)
        if not m:
            continue
        et = ortak.katla(m.group(1))
        v = m.group(2).strip()
        # TAZİYE ADRESİ, YAKINI ve telefon satırları BİLEREK alınmaz
        if et.startswith("dogum"): k["dogum"] = v
        elif et.startswith("olum"): k["olum"] = v
        elif et.startswith("ana"): k["ana"] = v
        elif et.startswith("baba"): k["baba"] = v
        elif et.startswith("defin yeri"): k["defin_yeri"] = v
        elif et.startswith("defin tarihi"): k["defin"] = v
    if k:
        kayitlar.append(k)
    return kayitlar


def dortyol(ctx):
    liste = oi.al(LISTE)
    gunler = {}
    for url, tar in re.findall(r'href="(https://www\.dortyol\.bel\.tr/(\d\d-\d\d-\d{4}))"', liste):
        g = oi.tarih(tar)
        if g and oi.pencerede(g, ctx["gunler"]) and g not in gunler:
            gunler[g] = url
    if not gunler:
        raise RuntimeError("pencerede gün sayfası bağlantısı bulunamadı (sayfa düzeni değişmiş olabilir)")
    okunacak = set(ctx["durum"].okunacak("Dörtyol", ctx["gunler"], her_zaman=2))
    sonuc = []
    for g, url in sorted(gunler.items(), reverse=True):
        if g not in okunacak:
            continue
        sayfa = oi.al(url)
        icerik = (re.search(r'<div class="content">([\s\S]*?)</div>\s*</div>', sayfa) or [None, sayfa])[1]
        for r in _blok_ayir(icerik):
            ad = oi.ad_duzelt(r["ad"])
            vef = oi.tarih(r.get("olum", ""))
            dogum = oi.tarih(r.get("dogum", ""))
            defin = oi.tarih(r.get("defin", "")) or g
            vakit = oi.vakit_ayikla(r.get("defin", ""))
            if not ad:
                continue
            ap = "-".join(x for x in (ortak.tr_title(r.get("ana", "")), ortak.tr_title(r.get("baba", ""))) if x)
            sonuc.append(oi.kayit(IL, "Dörtyol", "hatay-dortyol", ad, defin, "Dörtyol Belediyesi", url, ctx["alindi"],
                                  ek_id=str(vef), anne_baba=ap or None, yas=oi.yas_hesapla(dogum, vef) if dogum and vef else None,
                                  vefat_tarihi=vef, defin_yeri=oi.buyuk_ise_title(r.get("defin_yeri", ""), yer=True) or None,
                                  defin_zamani=defin, namaz_tarihi=defin if vakit else None, namaz_yeri_vakti=vakit, liste_tarihi=defin,
                                  ham={"ilan_gunu": g}))
        ctx["durum"].isaretle("Dörtyol", g)
    return sonuc


def main():
    oi.il_calistir(IL, "hatay", [("Dörtyol", dortyol)])


if __name__ == "__main__":
    main()
