#!/usr/bin/env python3
"""Aksaray Belediyesi e-Belediye 'Vefat Edenler' okuyucusu (yalnız standart kütüphane).
Kaynak: https://ebelediye.aksaray.bel.tr/VefatEdenler/Index -> POST /VefatEdenler/VefatEdenleriGoruntule
(multipart: __RequestVerificationToken [formdaki gizli alan + çerez], ilkTarih, sonTarih = VEFAT tarihi aralığı).
reCAPTCHA bu sitede kapalı ('recaptchaKapali = True'); açık olduğu görülürse okuma durur.
Sütunlar: ad, soyad, baba adı, doğum yeri, vefat tarihi, yaş, ölüm sebebi, cenazeyle ilgilenen, defin tarihi/saati,
namaz-defin bilgisi, mezarlık. KVKK: ÖLÜM SEBEBİ, CENAZEYLE İLGİLENEN (yakın adı) ve doğum yeri ALINMAZ.
Gün = defin tarihi (yoksa vefat tarihi). İlçe kaynakta yok -> ilce_belirsiz.
"""
import os, re, sys
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak9

IL = "Aksaray"
TABAN = "https://ebelediye.aksaray.bel.tr"
SAYFA = TABAN + "/VefatEdenler/Index"
POST = TABAN + "/VefatEdenler/VefatEdenleriGoruntule"
KAYNAK_AD = "Aksaray Belediyesi"
KOK = os.path.join(ortak9.VERI, "aksaray")


def tarih(s):
    m = re.match(r"^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", s or "")
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else None


def satirlar(html_):
    govde = html_[html_.find('id="vefatEdenlerTable"'):]
    govde = govde[:govde.find("</table>")]
    for tr in re.findall(r"<tr>\s*(<td>.*?)</tr>", govde, re.S):
        yield [ortak9.metin(c) for c in re.findall(r"<td>(.*?)</td>", tr, re.S)]


def main():
    n = ortak9.gun_sayisi()
    if not ortak.robots_izin(SAYFA):
        print("robots.txt bu adresi yasaklıyor, okunmadı", file=sys.stderr)
        return
    gl = ortak9.gunler(n)
    o = ortak9.Oturum()
    sayfa = o.get(SAYFA)
    if re.search(r"recaptchaKapali\s*=\s*'False'", sayfa, re.I):
        print("reCAPTCHA açık görünüyor, okunmadı", file=sys.stderr)
        return
    m = re.search(r'id="form1".*?name="__RequestVerificationToken" type="hidden" value="([^"]+)"', sayfa, re.S) \
        or re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"(?=.{0,200}?ilkTarih)', sayfa, re.S)
    if not m:
        print("CSRF belirteci bulunamadı", file=sys.stderr)
        return
    bas = (date.today() - timedelta(days=n + 4)).strftime("%d.%m.%Y 00:00")
    son = date.today().strftime("%d.%m.%Y 23:59")
    out = o.post_multipart(POST, {"__RequestVerificationToken": m.group(1), "ilkTarih": bas, "sonTarih": son})
    if "vefatEdenlerTable" not in out:
        print("tablo yok (yanıt beklenmedik)", file=sys.stderr)
        return
    alindi = ortak.simdi_iso()
    yeni, toplam = {}, 0
    for h in satirlar(out):
        if len(h) < 11:
            continue
        ad_, soyad, baba, _dogum_yeri, vefat, yas, _sebep, _ilgilenen, defin, namaz, mezarlik = h[:11]
        ad = ortak.tr_title(f"{ad_} {soyad}")
        v_iso, d_iso = tarih(vefat), tarih(defin)
        gun = d_iso or v_iso
        if not gun:
            continue
        toplam += 1
        saat = re.search(r"(\d{1,2}:\d{2})", defin or "")
        vakit = " – ".join(x for x in (namaz or None, f"defin saati {saat.group(1)}" if saat else None) if x) or None
        mz = " ".join((mezarlik or "").replace(" / ", " / ").split()).strip(" /")
        k = ortak9.kayit("aksaray", IL, ad, gun, KAYNAK_AD, SAYFA, alindi, ek_id=(v_iso or "") + (baba or ""),
                         anne_baba=ortak.tr_title(baba) or None, yas=int(yas) if (yas or "").isdigit() else None,
                         vefat_tarihi=v_iso, defin_yeri=ortak.tr_title(mz) if mz else None,
                         defin_zamani=d_iso, namaz_yeri_vakti=vakit,
                         ham={"baba": baba, "defin": defin, "namaz": namaz, "mezarlik": mezarlik})
        if gun in gl:
            yeni.setdefault(gun, []).append(k)
    print(f"tabloda {toplam} kayıt, pencerede {sum(len(v) for v in yeni.values())}")
    by = ortak9.birlestir(KOK, gl, yeni)
    ortak9.yaz(KOK, IL, gl, by)


if __name__ == "__main__":
    main()
