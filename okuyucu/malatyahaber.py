#!/usr/bin/env python3
"""Malatya: Malatya Haber (malatyahaber.com) GÜNLÜK "Vefat Edenler" listesi (14.10.2026, H41; MEBİS boş olduğu için tek kaynak).
Kategori: /vefat-edenler -> günlük yazılar "13 EKİM 2026- Vefat Edenler"; yazı gövdesi satırları: "AD SOYAD- YAŞ:77- MAHALLE MH. İLÇE / MALATYA".
Alınan: ad soyad, yaş, mahalle, ilçe (yalnız Malatya'nın gerçek ilçesi), gün = başlıktaki tarih (ilan_vefat_tarihi). Başka ilde olan (… / İSTANBUL ya da il yok) satır ALINMAZ.
Bütçe/kural: ortak_basin.al (robots.txt, site başına günde 40 istek, >=3,5 sn); kategori sayfası 3 saat önbellek, tur başına <= 2 yeni günlük yazı (okunanlar önbellekte).
Çıktı: veri/malatya/_ulusal.json (vefatilan/sondakika ile aynı dosya, id'ye göre birleşir; ulusal_birlestir.py son7gun'a katar). kaynak_turu "yerel_basin", kaynak_ad "Malatya Haber".
Kullanım: python3 okuyucu/malatyahaber.py [--gun 7] [--kuru]"""
import json, os, re, sys, urllib.parse
from datetime import date, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh, ortak_kategori as ok

IL = "Malatya"
KAYNAK_AD = "Malatya Haber"
KATEGORI = "https://www.malatyahaber.com/vefat-edenler"
AYLAR = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}
SATIR = re.compile(r"^(?P<ad>[^\d:]{4,60}?)\s*-\s*YAŞ\s*:?\s*(?P<yas>\d{1,3})\s*-\s*(?P<yer>.+)$", re.I)


def baslik_gunu(t):
    m = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(20\d\d)", t or "")
    if not m:
        return None
    ay = AYLAR.get(ortak.tr_lower(m.group(2)))
    try:
        return date(int(m.group(3)), ay, int(m.group(1))).isoformat() if ay else None
    except ValueError:
        return None


def satirlar(govde, gun, ctx, ilceler):
    out = []
    for s in govde.splitlines():
        m = SATIR.match(s.strip())
        if not m:
            continue
        yer = re.sub(r"\s+", " ", m.group("yer")).strip()
        if "/" not in yer or ortak.katla(yer.rsplit("/", 1)[1]) != ortak.katla(IL):
            continue                                   # başka il / il yok: bu ilin kaydı değil
        on = yer.rsplit("/", 1)[0].strip()
        ilce = next((i for i in ilceler if ortak.katla(on).endswith(ortak.katla(i))), None)
        mah = on[: len(on) - len(ilce)].strip() if ilce and on.lower().endswith(ilce.lower()) else on
        if ilce:
            mah = re.sub(r"\s*(?:mh\.?|mahallesi)\s*$", "", on[: max(0, len(on) - len(ilce))].strip(), flags=re.I).strip() or None
        else:
            mah = None
        yas = int(m.group("yas"))
        if not (0 <= yas <= 120):
            continue
        ad = ortak.tr_title(m.group("ad").strip())
        if len(ad.split()) < 2:
            continue
        k = oi.kayit(IL, ilce, "malatya-malatyahaber", ad, gun, KAYNAK_AD, ctx["url"], ctx["alindi"], ek_id="", liste_tarihi=gun, vefat_tarihi=gun,
                     yas=yas, mahalle=ob.kisa(ortak.tr_title(mah)) if mah else None, ham={"yayin_tarihi": gun, "sayfa_tarihi": gun, "tarih_kaynagi": "ilan_vefat_tarihi"})
        k["kaynak_turu"] = oh.KAYNAK_TURU
        if not ilce:
            k["ilce"] = None
            k["ilce_belirsiz"] = True
        out.append(k)
    return out


def main():
    kuru = "--kuru" in sys.argv
    n_gun = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else 7
    klasor = os.path.join(DIZIN, "..", "veri", "malatya")
    os.makedirs(klasor, exist_ok=True)
    gl = oi.gunler(n_gun)
    ctx = {"gunler": gl, "alindi": ortak.simdi_iso(), "klasor": klasor, "durum": oi.Durum(klasor), "il": IL}
    sayfa = ok._onbellek(ctx, KATEGORI, ok.ONBELLEK_SN)
    if sayfa is None:
        return
    ilceler = ortak.ilce_listesi(IL)
    yol = os.path.join(klasor, "_gunluk_liste.json")
    try:
        sakli = json.load(open(yol, encoding="utf-8"))
    except Exception:
        sakli = {}
    aday = []
    for m in re.finditer(r"<a\b[^>]*href=\"([^\"#]+)\"[^>]*>([\s\S]*?)</a>", sayfa):
        t = oi.metin(m.group(2))
        g = baslik_gunu(t)
        if g and re.search(r"vefat\s+edenler", t, re.I) and g in gl:
            aday.append((urllib.parse.urljoin(KATEGORI, m.group(1)), g))
    aday = sorted(set(aday), key=lambda x: x[1], reverse=True)
    kayitlar, n = [], 0
    for u, g in aday:
        if u in sakli and sakli[u].get("tarih") != date.today().isoformat():   # bugünkü yazı gün içinde güncellenebilir; eskiler yeniden açılmaz
            kayitlar += sakli[u]["kayitlar"]
            continue
        if n >= 2:
            continue
        try:
            s = ob.al(ctx, u)
        except (ob.ButceDoldu, oi.Engel) as e:
            print(f"  {e}", file=sys.stderr)
            break
        n += 1
        govde = ob.makale_govdesi(s) or "\n".join(oi.metin(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", s))
        ctx["url"] = u
        ks = satirlar(govde, g, ctx, ilceler)
        sakli[u] = {"tarih": date.today().isoformat(), "gun": g, "kayitlar": ks}
        kayitlar += ks
        print(f"  {g}: {len(ks)} kayıt")
    ob.durum(ctx).kaydet()
    if kuru:
        print(f"[kuru] {len(kayitlar)} kayıt")
        for k in kayitlar[:5]:
            print({a: k.get(a) for a in ("yas", "ilce", "mahalle", "liste_tarihi")})
        return
    sakli = {u: v for u, v in sakli.items() if v.get("gun", "") >= (date.today() - timedelta(days=10)).isoformat()}
    ortak.json_yaz(yol, sakli)
    ul = os.path.join(klasor, "_ulusal.json")
    try:
        eski = json.load(open(ul, encoding="utf-8")).get("kayitlar", [])
    except Exception:
        eski = []
    kay = {x["id"]: x for x in eski}
    kay.update({x["id"]: x for x in kayitlar})
    sinir = gl[-1]
    kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
    ortak.json_yaz(ul, {"il": IL, "kayitlar": list(kay.values()), "guncelleme": ctx["alindi"]})
    print(f"Malatya Haber: {len(kayitlar)} kayıt")


if __name__ == "__main__":
    main()
