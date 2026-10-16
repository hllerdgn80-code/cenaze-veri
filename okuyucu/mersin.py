#!/usr/bin/env python3
"""Mersin: RESMÎ kaynak = Anamur Belediyesi (13.10.2026: `anamur.bel.tr` WordPress REST, kategori "Vefat Edenler" id 122, günlük yazı
"GG.AA.YYYY Vefat Edenler"; robots.txt yalnız /wp-admin kapalı). Yazı satırları: "<Mahalle/Köy>" / "Ad Soyad (yakın) [vefat etmiştir.]" /
"<yer> mezarlığına [vakit namazına müteakip] defnedilecek." ; telefon ve parantez içi yakın adı ALINMAZ. Mersin merkez/diğer ilçelerde
belediye listesi yok -> YEREL HABER siteleri, TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026).
Kaynaklar: Çukurova Gazetesi, Mersin Haber Merkezi, İmece Gazetesi, İste Mersin. Ayrıntı ve hacim: arastirma/yerel-haber-2026-10-08.md.
Her site ayrı kaynak; dizin = sitenin RSS'i (6 saat önbellek), site başına günde en çok 3 istek (robots.txt dahil).
Yalnız olgu (ad, yaş, ilçe/köy, tarih, cami + vakit, mezarlık); sitenin cümlesi, ölüm nedeni, yakın adı, fotoğraf ALINMAZ (ortak_haber).
Kullanım: python3 okuyucu/mersin.py [--gun 7] [--ilce "Kaynak Adı"]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, re, time
import ortak, ortak_haber as oh, ortak_ilce as oi

IL = "Mersin"
SITELER = [
    oh.site("Çukurova Gazetesi", "mersin-cukurovagazetesi", "https://www.cukurovagazetesi.com/rss", ek_dizin="https://www.cukurovagazetesi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("Mersin Haber Merkezi", "mersin-mersinhabermerkezi", "https://www.mersinhabermerkezi.com/rss", ek_dizin="https://www.mersinhabermerkezi.com/sitemap/sitemap-{AY}.xml"),
    oh.site("İmece Gazetesi", "mersin-imecegazetesi", "https://www.imecegazetesi.com/rss"),
    oh.site("İste Mersin", "mersin-istemersin", "https://www.istemersin.com/rss"),
]


ANAMUR_API = "https://anamur.bel.tr/wp-json/wp/v2/posts?categories=122&per_page=15&_fields=date,title,content,link"
_MAH_SATIR = re.compile(r"^[^.:]{2,60}?\s(mahallesi|köyü|mah\.?|mahalle|beldesi)\s*$", re.I)
_TEL_SATIR = re.compile(r"\d{3}\s?\d{3}\s?\d{2}\s?\d{2}|:\s*0?\d{3}")


def anamur_satirlari(html_):
    x = re.sub(r"<br\s*/?>|</p>|</div>", "\n", html_ or "")
    return [l for l in (oi.metin(l) for l in x.split("\n")) if l]


def anamur_ayristir(satirlar):
    """-> [(mahalle|None, ad, defin_satiri)]. Satır akışı: mahalle satırı (isteğe bağlı), ad satırı, 'defnedilecek' satırı."""
    sonuc, mah, ad = [], None, None
    for l in satirlar:
        if _TEL_SATIR.search(l):
            continue
        if "defnedilecek" in ortak.tr_lower(l):
            if ad:
                sonuc.append((mah, ad, l))
            ad, mah = None, None
        elif _MAH_SATIR.match(l):
            mah = l
        else:
            ad = re.sub(r"\s*vefat\s+etmiştir\.?\s*$", "", l, flags=re.I)
    return sonuc


ANAMUR_YOLLAR = [ANAMUR_API,
                 ANAMUR_API.replace("/wp-json/wp/v2/posts?", "/?rest_route=/wp/v2/posts&"),
                 ANAMUR_API.replace("https://anamur.bel.tr", "https://www.anamur.bel.tr")]


def anamur_json():
    """WordPress REST bazı ağlardan HTML (koruma/yönlendirme) döner (CI, 16.10.2026: JSONDecodeError): sırayla üç eşdeğer yol denenir."""
    ipucu = []
    for i, u in enumerate(ANAMUR_YOLLAR):
        govde = oi.al(u)
        try:
            d = json.loads(govde)
            if isinstance(d, list):
                return d
        except ValueError:
            pass
        ipucu.append(f"{len(govde)} bayt: {oi.metin(govde)[:60]!r}")
        time.sleep(5)
    raise RuntimeError("Anamur REST JSON vermedi (3 yol): " + " | ".join(ipucu))


def anamur(ctx):
    d = anamur_json()
    sonuc = []
    for p in d:
        m = re.match(r"\s*(\d{2}\.\d{2}\.\d{4})", oi.metin(p["title"]["rendered"]))
        gun = oi.tarih(m.group(1)) if m else None
        if not gun:
            continue
        for mah, ad_ham, defin_satir in anamur_ayristir(anamur_satirlari(p["content"]["rendered"])):
            ad = oi.ad_duzelt(ad_ham)
            if not ad or len(ad.split()) < 2:
                continue
            _, defin = oi.cenaze_ayikla("Cenazesi " + defin_satir)
            defin = ortak.tr_title(defin) if defin else None
            v, sa = oi.vakit_ayikla(defin_satir), re.search(r"saat\s*[–-]?\s*(\d{1,2}[:.]\d{2})", defin_satir, re.I)
            namaz = ortak.tr_title(v) if v else (("Saat " + sa.group(1).replace(".", ":")) if sa else None)
            mah_t = oi.buyuk_ise_title(re.sub(r"\s*\([^)]*\)", "", mah), yer=True) if mah else None
            sonuc.append(oi.kayit(IL, "Anamur", "mersin-anamur", ad, gun, "Anamur Belediyesi", p["link"], ctx["alindi"],
                                  mahalle=mah_t, defin_yeri=defin, defin_zamani=gun, namaz_tarihi=gun, namaz_yeri_vakti=namaz,
                                  liste_tarihi=gun, il_disi_metin=defin_satir))
    return sonuc


def main():
    oi.il_calistir(IL, "mersin", [("Anamur", anamur)] + oh.okuyucular(IL, SITELER))


if __name__ == "__main__":
    main()
