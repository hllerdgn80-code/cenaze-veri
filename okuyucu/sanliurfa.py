#!/usr/bin/env python3
"""Şanlıurfa Büyükşehir Belediyesi taziye defteri okuyucusu (yalnız standart kütüphane).
Kaynak: https://www.sanliurfa.bel.tr/kategori/80/0/taziye-defteri?page=N (Başlık = ad, Açıklama = ilanın eklenme zamanı "07.10.2026 16:29";
sayfa başına ~10 satır, en yenisi üstte) + her ilanın ayrıntı sayfası (/icerik/<id>/106/<slug>): Adı Soyadı, Baba adı, Doğum Tarihi (yıl),
Ölüm tarihi, Defin Tarihi, Defin yeri. ALINMAZ (KVKK): İrtibat (telefon), Taziye Yeri (adres). robots.txt yalnız /uploads/ yasaklar.
Ayrıntı sayfası yalnız son 7 gün için açılır (~25 istek, 3,5 sn arayla -> ~2 dk). Kayıt kaynak_id'si (icerik no) zaten kayıtlı günlerin ayrıntısı
tekrar çekilmez. İlçe kaynakta yok (defin yeri mezarlık adı) -> ilce_belirsiz.
Kullanım: python3 okuyucu/sanliurfa.py
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ek

IL = "Şanlıurfa"
LISTE = "https://www.sanliurfa.bel.tr/kategori/80/0/taziye-defteri"
KAYNAK_AD = "Şanlıurfa Büyükşehir Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "sanliurfa")
EN_COK_SAYFA = 8


def liste_ayristir(sayfa):
    """[(icerik_no, url, ad, 'YYYY-AA-GG', 'SS:DD')]"""
    govde = sayfa.split('id="table"', 1)[-1]
    sonuc = []
    for tr in re.findall(r"<tr>(.*?)</tr>", govde, re.S):
        a = re.search(r'<a href="(https://www\.sanliurfa\.bel\.tr/icerik/(\d+)/[^"]*)">(.*?)</a>', tr, re.S)
        z = re.search(r"(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})", tr)
        if a and z:
            sonuc.append((a.group(2), a.group(1), ortak_ek.metin(a.group(3)), ortak_ek.tarih_gg_aa_yyyy(z.group(1)), z.group(2)))
    return sonuc


def etiketler(sayfa):
    """Ayrıntı sayfasından 'Adı Soyadı : X' benzeri etiketleri sözlüğe çevirir (İrtibat ve Taziye Yeri döndürülmez)."""
    m = re.search(r"Ad[ıi]\s+Soyad[ıi]\s*:.*?Eklenme Tarihi:", ortak_ek.metin(sayfa), re.S)
    if not m:
        return None
    parca = m.group(0)
    anahtarlar = ["Adı Soyadı", "Baba adı", "Doğum Tarihi", "Ölüm tarihi", "Defin Tarihi", "İrtibat", "Defin yeri", "Taziye Yeri", "Eklenme Tarihi"]
    d, konumlar = {}, []
    for a in anahtarlar:
        i = parca.find(a + " :")
        if i < 0:
            i = parca.find(a + ":")
        if i >= 0:
            konumlar.append((i, a))
    konumlar.sort()
    for n, (i, a) in enumerate(konumlar):
        son = konumlar[n + 1][0] if n + 1 < len(konumlar) else len(parca)
        d[a] = parca[i + len(a):son].lstrip(" :").strip()
    return d


def kayda_cevir(no, url, ad_liste, eklenme_gun, saat, d, alindi):
    ad = (d or {}).get("Adı Soyadı") or ad_liste
    olum = ortak_ek.tarih_gg_aa_yyyy((d or {}).get("Ölüm tarihi"))
    defin = ortak_ek.tarih_gg_aa_yyyy((d or {}).get("Defin Tarihi")) or eklenme_gun
    dogum = ((d or {}).get("Doğum Tarihi") or "").strip()
    k = ortak_ek.bos_kayit(IL, KAYNAK_AD, url, alindi)
    k.update(
        id=ortak.kayit_id("sanliurfa", ad, eklenme_gun, no),
        ad_soyad=ortak.tr_title(ad),
        anne_baba=ortak.tr_title((d or {}).get("Baba adı", "")) or None,
        vefat_tarihi=olum,
        defin_yeri=((d or {}).get("Defin yeri") or "").strip() or None,
        defin_zamani=defin,
        liste_tarihi=eklenme_gun,
        ham={"icerik_no": no, "eklenme": f"{eklenme_gun} {saat}", "dogum_yili": dogum if re.fullmatch(r"\d{4}", dogum) else (dogum or None),
             "ayrinti_okundu": d is not None},
    )
    return k


def main():
    if not ortak.robots_izin(LISTE):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gunler = ortak_ek.son_gunler(7)
    alindi = ortak.simdi_iso()
    # daha önce kaydedilmiş içerik no'ları (ayrıntıyı yeniden çekmemek için)
    onceki = {}
    for g in gunler:
        yol = os.path.join(KOK, f"{g}.json")
        if os.path.exists(yol):
            for k in json.load(open(yol, encoding="utf-8")).get("kayitlar", []):
                if k.get("ham", {}).get("ayrinti_okundu"):
                    onceki[k["ham"].get("icerik_no")] = k
    by_gun = {}
    for no_sayfa in range(1, EN_COK_SAYFA + 1):
        satirlar = liste_ayristir(ortak.indir(LISTE if no_sayfa == 1 else f"{LISTE}?page={no_sayfa}"))
        if not satirlar:
            if no_sayfa == 1:
                raise RuntimeError("Liste bulunamadı (sayfa düzeni değişmiş olabilir)")
            break
        for no, url, ad, gun, saat in satirlar:
            if gun not in gunler:
                continue
            if no in onceki:
                k = onceki[no]
            else:
                d = etiketler(ortak.indir(url))
                k = kayda_cevir(no, url, ad, gun, saat, d, alindi)
            by_gun.setdefault(gun, []).append(k)
        if min(s[3] for s in satirlar) < gunler[-1]:
            break
    sayac = ortak_ek.yaz_birlestir(KOK, IL, gunler, by_gun)
    for g in gunler:
        print(f"{g}: {sayac[g]} kayıt")


if __name__ == "__main__":
    main()
