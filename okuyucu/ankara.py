#!/usr/bin/env python3
"""Ankara: Ankara BŞB'nin web listesi yok; ilçe düzeyinde 5 ilçe belediyesi (her biri ayrı kaynak):
- Ayaş: `ayas.bel.tr/vefat-edenler?page=N` (tablo: vefat tarihi, defin tarihi, defin yeri, açıklama). Gün = defin tarihi.
- Beypazarı: `beypazari.bel.tr/cenaze-ilanlari?page=N` (liste + sayfadaki ayrıntı tabloları). robots.txt sayfalamayı kapatıyorsa yalnız ilk sayfa okunur.
  Ayrıntıdan yalnız doğum yılı/yaş ve "defin edileceği yer" alınır; ÖLÜM YERİ-HEKİM ve "bilgiyi bildiren" (yakın) ALINMAZ.
- Çubuk: `cubuk.bel.tr/category/anons/feed/` WordPress yayını; cenaze yazıları "İLÇEMİZ X MAH. HALKINDAN AD VEFAT ETMİŞTİR". 08.10.2026'da
  kategorideki son yazı Aralık 2020: pencerede 0 kayıt beklenir ("izlemede").
- Kalecik: `kalecik.bel.tr/vefat-edenler` (tablo: ad, baba adı, vefat tarihi, vefat yeri). Gün = vefat tarihi.
- Polatlı: `polatli.bel.tr/vefat-edenler?page=N` (tarih, ad, şehir/mahalle, yaş, cenaze namazı yeri, vakit, mezarlık). 403 gelirse bu ilçe BIRAKILIR.
- YEREL BASIN (site sahibi kararı 08.10.2026) Ankara Net Haber: günlük "D Ay <gün> Ankara vefat sorgulama: Ankara'da bugün
  defnedilecekler" yazısı (ABB mezarlıkları: Karşıyaka, Sincan, Cebeci, Ortaköy, Gölbaşı; günde ~50 ad). Yalnız ad soyad + mezarlık
  alınır (ada/parsel ALINMAZ); defin günü = yazı günü; ilçe yazılmadığı için belirsiz (mezarlıktan ilçe çıkarılmaz).
  Dizin `sitemap-news.xml`; site başına günde en çok 3 istek (ortak_basin). kaynak_turu yerel_basin.
Kullanım: python3 okuyucu/ankara.py [--gun 7] [--ilce Ayaş,Polatlı]
"""
import html as _html, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Ankara"


def _aciklama(txt):
    """Serbest 'Açıklama' alanından yalnız cenaze cümlesi ya da namaz vakti."""
    if not txt:
        return None
    namaz, _ = oi.cenaze_ayikla(txt)
    return namaz or oi.vakit_ayikla(txt)


# ---------------------------------------------------------------- Ayaş
AYAS = "https://ayas.bel.tr/vefat-edenler"


def ayas(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa)
        liste = []
        for s in satirlar:
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Ad Soyad"))
            vef, defin = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi")), oi.tarih(oi.kolon(baslik, s, "Defin Tarihi"))
            yer = oi.kolon(baslik, s, "Defin Yeri")
            gun = defin or vef
            if not ad or not gun:
                continue
            liste.append(oi.kayit(IL, "Ayaş", "ankara-ayas", ad, gun, "Ayaş Belediyesi", AYAS, ctx["alindi"], ek_id=str(vef),
                                  vefat_tarihi=vef, defin_yeri=oi.buyuk_ise_title(yer, yer=True) or None, defin_zamani=defin,
                                  namaz_yeri_vakti=_aciklama(oi.kolon(baslik, s, "Açıklama")), liste_tarihi=gun, ham={}))
        return liste
    return oi.sayfala(lambda n: AYAS if n == 1 else f"{AYAS}?page={n}", ayristir, ctx["gunler"], azami_sayfa=3)


# ---------------------------------------------------------------- Beypazarı
BEYPAZARI = "https://beypazari.bel.tr/cenaze-ilanlari"


def beypazari(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa, 0)
        ayr = []
        for t in re.findall(r"<table[\s\S]*?</table>", sayfa)[1:]:
            d = {}
            for tr in re.findall(r"<tr[\s\S]*?</tr>", t):
                h = oi.hucreler(tr)
                if len(h) >= 2:
                    d[ortak.katla(h[0])] = h[1]
            ayr.append(d)
        liste = []
        for i, s in enumerate(satirlar):
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Vefat Eden"))
            vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
            d = ayr[i] if i < len(ayr) else {}
            dogum = (re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", d.get("dogum tarihi ve yasi", "")) or [None, None])[1]
            yas = oi.say(re.sub(r"\b(1[89]\d\d|20[0-2]\d)\b", "", d.get("dogum tarihi ve yasi", ""))) if d.get("dogum tarihi ve yasi") else None
            if not ad or not vef:
                continue
            liste.append(oi.kayit(IL, "Beypazarı", "ankara-beypazari", ad, vef, "Beypazarı Belediyesi", BEYPAZARI, ctx["alindi"],
                                  yas=yas if yas and yas < 125 else (int(vef[:4]) - int(dogum) if dogum else None),
                                  vefat_tarihi=vef, defin_yeri=oi.buyuk_ise_title(d.get("defin edilecegi yer", ""), yer=True) or None,
                                  liste_tarihi=vef, ham={"dogum_yili": dogum, "yas_kaynagi": "dogum_yili_farki" if dogum else None}))
        return liste
    return oi.sayfala(lambda n: BEYPAZARI if n == 1 else f"{BEYPAZARI}?page={n}", ayristir, ctx["gunler"], azami_sayfa=3)


# ---------------------------------------------------------------- Çubuk
CUBUK = "https://www.cubuk.bel.tr/category/anons/feed/"


def cubuk(ctx):
    from email.utils import parsedate_to_datetime
    xml = oi.al(CUBUK)
    sonuc = []
    for it in re.findall(r"<item>[\s\S]*?</item>", xml):
        baslik = _html.unescape((re.search(r"<title>([\s\S]*?)</title>", it) or [None, ""])[1]).strip()
        yayin = (re.search(r"<pubDate>([\s\S]*?)</pubDate>", it) or [None, ""])[1]
        try:
            gun = parsedate_to_datetime(yayin).date().isoformat()
        except Exception:
            continue
        m = re.search(r"halkından\s+(.+?)\s+vefat\s+etmi", baslik, re.I)
        if not m or not oi.pencerede(gun, ctx["gunler"]):
            continue
        mah = re.search(r"(?:ilçemiz\s+)?(.+?)\s+halkından", baslik, re.I)
        sonuc.append(oi.kayit(IL, "Çubuk", "ankara-cubuk", oi.ad_duzelt(m.group(1)), gun, "Çubuk Belediyesi", CUBUK, ctx["alindi"],
                              mahalle=oi.buyuk_ise_title(re.sub(r"^ilçemiz\s+", "", mah.group(1), flags=re.I), yer=True) if mah else None,
                              liste_tarihi=gun, ham={"baslik": baslik[:160]}))
    return sonuc


# ---------------------------------------------------------------- Kalecik
KALECIK = "https://www.kalecik.bel.tr/vefat-edenler"


def kalecik(ctx):
    sayfa = oi.al(KALECIK)
    baslik, satirlar = oi.tablo(sayfa)
    sonuc = []
    for s in satirlar:
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
        baba = oi.ad_duzelt(oi.kolon(baslik, s, "Baba Adı"))
        vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
        yer = oi.kolon(baslik, s, "Vefat Yeri")
        if not ad or not vef:
            continue
        sonuc.append(oi.kayit(IL, "Kalecik", "ankara-kalecik", ad, vef, "Kalecik Belediyesi", KALECIK, ctx["alindi"],
                              anne_baba=baba or None, vefat_tarihi=vef, namaz_yeri_vakti=_aciklama(oi.kolon(baslik, s, "Açıklama")),
                              liste_tarihi=vef, ham={"vefat_yeri": yer or None}))
    return sonuc


# ---------------------------------------------------------------- Polatlı
POLATLI = "https://www.polatli.bel.tr/vefat-edenler"


def polatli(ctx):
    def ayristir(sayfa, n):
        baslik, satirlar = oi.tablo(sayfa)
        liste = []
        for s in satirlar:
            gun = oi.tarih(oi.kolon(baslik, s, "Tarih"))
            ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
            mah = oi.kolon(baslik, s, "Mahalle")
            cami, vakit = oi.kolon(baslik, s, "Cenaze Namazı"), oi.kolon(baslik, s, "Vakit")
            if not ad or not gun:
                continue
            liste.append(oi.kayit(IL, "Polatlı", "ankara-polatli", ad, gun, "Polatlı Belediyesi", POLATLI, ctx["alindi"],
                                  mahalle=oi.buyuk_ise_title(mah, yer=True) or None, yas=oi.say(oi.kolon(baslik, s, "Yaş")),
                                  defin_yeri=oi.buyuk_ise_title(oi.kolon(baslik, s, "Mezarlık"), yer=True) or None,
                                  defin_zamani=gun, namaz_tarihi=gun,
                                  namaz_yeri_vakti=" / ".join(x for x in (oi.buyuk_ise_title(cami.rstrip("."), yer=True), oi.buyuk_ise_title(vakit, yer=True)) if x) or None,
                                  liste_tarihi=gun, ham={}))
        return liste
    return oi.sayfala(lambda n: POLATLI if n == 1 else f"{POLATLI}?page={n}", ayristir, ctx["gunler"], azami_sayfa=3)


# ---------------------------------------------------------------- Ankara Net Haber (yerel basın)
def ankara_net_haber(ctx):
    import ortak_basin as ob
    xml = ob.dizin(ctx, "https://www.ankaranethaber.com/sitemap-news.xml")
    if xml is None:
        return []
    sayfalar = [(u, g) for u, t, g in ob.harita_ogeleri(xml) if "vefat-sorgulama" in u]

    def ayristir(sayfa, url, gun):
        gun = ob.yayin_tarihi(sayfa) or gun
        govde = ob.makale_govdesi(sayfa)
        if not govde:
            raise RuntimeError("Ankara Net Haber: makale gövdesi bulunamadı (düzen değişmiş olabilir)")
        liste, mezarlik = [], None
        for satir in govde.split("\n"):
            if re.fullmatch(r"[A-ZÇĞİÖŞÜ ]+MEZARLI[GĞ]I", satir.strip()):
                mezarlik = ortak.tr_title(satir.strip())
                continue
            m = re.match(r"^([^—–\-:]{3,60}?)\s+[—–-]\s+Ada\b", satir.strip())
            if not m or not mezarlik:
                continue
            ad = oi.ad_duzelt(m.group(1))
            if not (2 <= len(ad.split()) <= 5):
                continue
            liste.append(ob.kayit(ctx, IL, "ankara-ankaranethaber", "Ankara Net Haber", url, ad, gun, ilce=None, ek_id=mezarlik,
                                  defin_zamani=gun, defin_yeri=mezarlik, ham={"sayfa_tarihi": gun, "tarih_kaynagi": "yayin_tarihi"}))
        return liste
    return ob.sayfalari_oku(ctx, sayfalar, ayristir, azami=2)


def main():
    oi.il_calistir(IL, "ankara", [("Ayaş", ayas), ("Beypazarı", beypazari), ("Çubuk", cubuk), ("Kalecik", kalecik), ("Polatlı", polatli),
                                  ("Ankara Net Haber", ankara_net_haber)])


if __name__ == "__main__":
    main()
