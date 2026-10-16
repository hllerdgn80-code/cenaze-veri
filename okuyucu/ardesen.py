#!/usr/bin/env python3
"""Ardeşen Belediyesi (Rize) ÖLÜM İLANI duyuruları (yardımcı modül; rize.py çağırır, yalnız standart kütüphane).
16.10.2026 (sahibi: "mezarlık bilgi sistemi önceliğimiz; bize verilen bilgileri alıp yerleştiririz"): kaynak
https://vefat.ardesen.bel.tr/ (Ardeşen Belediyesi Duyuru Sistemi; tek sayfa, tablo: Duyuru Başlığı | Duyuru Tarihi GG-AA-YYYY | metin).
Metin serbest ilan: "<İlçe> <köy> sakinlerinden ... <AD SOYAD> Hakk'ın rahmetine kavuşmuştur. Cenaze namazı yarın/bugün <vakit> <cami>da kılınacaktır."
AD = "Hakk'ın rahmetine" ifadesinden hemen önceki büyük harfle başlayan 2-4 sözcük (yakın adları: virgül/ilişki sözcüğüyle ayrıldığı için ALINMAZ).
Cenaze günü: ilan tarihi + "bugün" (aynı gün) / "yarın" (+1) ya da cümlede açık GG.AA.YYYY; hiçbiri yoksa kayıt ALINMAZ (tarih uydurma yok).
İlçe: ilan "<Ardeşen|Çamlıhemşin|...> ... sakinlerinden" diye başlıyorsa o ilçe (Rize'nin geçerli ilçesiyse), aksi hâlde Ardeşen Belediyesi'nin ilçesi.
Telefon, yakın adları, taziye adresi ALINMAZ. Robots: /robots.txt 404 (kısıt yok); tek istek (sayfa ~1,7 MB).
"""
import html, os, re, sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "Rize"
URL = "https://vefat.ardesen.bel.tr/"
KAYNAK_AD = "Ardeşen Belediyesi"
_HAKK = re.compile(r"\bhakk[’'`ʼ]?(?:ı|i)?n?\s+rahmetine", re.I)
_ILISKI_DURAK = {"merhum", "merhume", "ve", "ile"}


def ad_ayikla(metin):
    """'... kuzeni, Mustafa Zaimoğlu Hakk’ın rahmetine kavuşmuştur' -> 'Mustafa Zaimoğlu' (yoksa None)."""
    m = _HAKK.search(metin)
    if not m:
        return None
    onceki = metin[:m.start()].split()
    ad = []
    for tok in reversed(onceki):
        bos = tok.rstrip(",;:.")
        if tok != bos or not bos:           # virgül/noktalı virgül: öncesi başka kişi
            break
        if "'" in bos or "’" in bos or "ʼ" in bos or not bos[0].isupper() or ortak.tr_lower(bos) in _ILISKI_DURAK:
            break
        ad.append(bos)
        if len(ad) == 4:
            break
    ad.reverse()
    if len(ad) < 2:
        return None
    return ortak.tr_title(" ".join(ad))


def cenaze_gunu(metin, ilan_gun):
    c = re.search(r"cenaze\s+namaz[^.]*", metin, re.I)
    parca = c.group(0) if c else ""
    m = re.search(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b", parca)
    if m:
        return oi.tarih(m.group(1).replace("-", "."))
    d = datetime.strptime(ilan_gun, "%Y-%m-%d").date()
    if re.search(r"\bbugün\b", parca, re.I):
        return d.isoformat()
    if re.search(r"\byarın\b", parca, re.I):
        return (d + timedelta(days=1)).isoformat()
    return None


def ayristir(sayfa):
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", sayfa, re.S):
        td = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(td) < 3:
            continue
        baslik, tarih, govde = (" ".join(html.unescape(re.sub(r"<[^>]+>", " ", x)).replace("\xa0", " ").split()) for x in td[:3])
        g = oi.tarih(tarih.replace("-", "."))
        if g:
            out.append((g, baslik, govde))
    return out


def kayitlar(gunler, alindi, sayfa=None):
    """gunler: izin verilen cenaze günleri (YYYY-AA-GG). -> {gün: [kayıt]}"""
    sayfa = sayfa if sayfa is not None else oi.al(URL, bekle=2.0)
    gecerli = {ortak.katla(x): x for x in ortak.gecerli_ilceler(IL)}
    sonuc, gor = {}, set()
    en_eski = min(gunler)
    for ilan_gun, baslik, govde in ayristir(sayfa):
        if ilan_gun < (datetime.strptime(en_eski, "%Y-%m-%d").date() - timedelta(days=1)).isoformat():
            continue
        ad = ad_ayikla(govde)
        gun = cenaze_gunu(govde, ilan_gun) if ad else None
        if not ad or not gun or gun not in gunler:
            continue
        ilk = govde.split()[0] if govde.split() else ""
        ilce = gecerli.get(ortak.katla(ilk)) or "Ardeşen"
        namaz, defin = oi.cenaze_ayikla(govde)
        if namaz:
            namaz = re.sub(r"\b(?:bugün|yarın)\b\s*", "", namaz, flags=re.I).strip() or None
        mah = oi.mahalle_ayikla(re.sub(r"^\S+\s+", "", govde)) if ilk and gecerli.get(ortak.katla(ilk)) or ilk.lower().startswith("ardeşen") else None
        k = {
            "id": ortak.kayit_id("ardesen", ad, gun, mah or ""),
            "il": IL, "ilce": ilce, "mahalle": mah,
            "ad_soyad": ad, "anne_baba": None, "yas": None, "dogum_tarihi": None, "vefat_tarihi": None,
            "defin_yeri": defin, "defin_zamani": None,
            "namaz_tarihi": gun, "namaz_yeri_vakti": namaz,
            "liste_tarihi": gun,
            "kaynak_ad": KAYNAK_AD, "kaynak_url": URL, "alindi": alindi,
            "ham": {"ilan_tarihi": ilan_gun, "ilce_kaynagi": "ilan_ilk_sozcuk" if gecerli.get(ortak.katla(ilk)) else "belediye_ilcesi"},
            "il_disi_defin": None, "ilce_belirsiz": False,
        }
        if k["id"] in gor:
            continue
        gor.add(k["id"])
        sonuc.setdefault(gun, []).append(k)
    return sonuc


if __name__ == "__main__":
    bugun = date.today()
    gl = [(bugun + timedelta(days=1) - timedelta(days=i)).isoformat() for i in range(9)]
    for g, l in sorted(kayitlar(gl, ortak.simdi_iso()).items()):
        for k in l:
            print(g, k["ilce"], "|", k["ad_soyad"], "|", k["mahalle"], "|", k["namaz_yeri_vakti"], "|", k["defin_yeri"])
