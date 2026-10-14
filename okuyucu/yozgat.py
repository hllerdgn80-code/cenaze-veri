#!/usr/bin/env python3
"""Yozgat: il belediyesinin robots.txt'i `Disallow: /` -> okunmaz. Kaynaklar (her biri ayrı):
- Yozgat Hakimiyet (14.10.2026, H50): `yozgathakimiyet.com.tr/vefat` ilan kartları (Ad + "Vefat: GG.AA.YYYY", ilk sayfa 12 kart ≈ 3 gün; "Daha fazla" /service/json/ robots'ta
  kapalı -> kullanılmaz). Her yeni kart için ilan sayfası açılır: tablo (Vefat Tarihi, Memleket "Yozgat <İlçe|Merkez>", Defin Yeri, Defin Tarihi) + cenaze cümlesinden
  yalnız cami/vakit. Olgular veri/yozgat/_hakimiyet_olgu.json'da saklanır (metin saklanmaz; yeniden açılmaz). tarih_kaynagi = ilan_vefat_tarihi.
- İlçe belediyeleri (belediye listesi yok, yalnız 2 ilçe):
- Sorgun: `sorgun.bel.tr/vefat-edenler` tablo (ad, baba adı, vefat tarihi, vefat yeri). Seyrek (08.10'da son kayıt 30.09).
- Çekerek: `cekerek.bel.tr/vefat-edenler?page=N` aynı şablon (+ açılır ayrıntı). Seyrek (son kayıt 03.10).
"Vefat Yeri" sütunu kaynakta ayrım yapmıyor (mezarlık adı, köy ya da ilçe adı): "mezarlık" geçiyorsa defin_yeri, geçmiyorsa ham'a yazılır.
Gün = vefat tarihi. Kullanım: python3 okuyucu/yozgat.py [--gun 7] [--ilce Sorgun]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, urllib.parse
from datetime import date, timedelta
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh, ortak_kategori as ok

IL = "Yozgat"


def _macroturk(ctx, ilce, slug, kaynak_ad, url, sayfa, modal=None):
    baslik, satirlar = oi.tablo(sayfa)
    sonuc = []
    for i, s in enumerate(satirlar):
        ad = oi.ad_duzelt(oi.kolon(baslik, s, "Adı Soyadı"))
        baba = oi.ad_duzelt(oi.kolon(baslik, s, "Baba Adı"))
        vef = oi.tarih(oi.kolon(baslik, s, "Vefat Tarihi"))
        yer = oi.kolon(baslik, s, "Vefat Yeri")
        det = modal[i] if modal and i < len(modal) else ""
        namaz, defin = oi.cenaze_ayikla(det)
        if not ad or not vef:
            continue
        mezarlik = "mezarl" in ortak.tr_lower(yer)
        sonuc.append(oi.kayit(IL, ilce, slug, ad, vef, kaynak_ad, url, ctx["alindi"], anne_baba=baba or None, vefat_tarihi=vef,
                              defin_yeri=defin or (oi.buyuk_ise_title(yer, yer=True) if mezarlik else None),
                              namaz_yeri_vakti=namaz, liste_tarihi=vef,
                              ham={"vefat_yeri": (yer or None) if not mezarlik else None}))
    return sonuc


SORGUN = "https://sorgun.bel.tr/vefat-edenler"
CEKEREK = "https://cekerek.bel.tr/vefat-edenler"


def sorgun(ctx):
    sayfa = oi.al(SORGUN)
    return _macroturk(ctx, "Sorgun", "yozgat-sorgun", "Sorgun Belediyesi", SORGUN, sayfa, oi.modal_govdeleri(sayfa))


def cekerek(ctx):
    sonuc = []
    for n in range(1, 4):
        url = CEKEREK if n == 1 else f"{CEKEREK}?page={n}"
        sayfa = oi.al(url)
        liste = _macroturk(ctx, "Çekerek", "yozgat-cekerek", "Çekerek Belediyesi", CEKEREK, sayfa, oi.modal_govdeleri(sayfa))
        icinde = [k for k in liste if oi.pencerede(k["liste_tarihi"], ctx["gunler"])]
        sonuc.extend(icinde)
        if not icinde:
            break
    return sonuc


HK_LISTE = "https://www.yozgathakimiyet.com.tr/vefat"
HK_AD = "Yozgat Hakimiyet"
HK_ISTEK_TUR = 8            # tur başına en çok 8 yeni ilan sayfası (site başına günde 40 istek bütçesi ob'da)
_KART = re.compile(r'<a\s+href="(/vefat/[^"#?]+)"[^>]*>([\s\S]*?)</a>')


def _gun(s):
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(20\d\d)", s or "")
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat() if m else None
    except (ValueError, AttributeError):
        return None


def hk_kartlar(sayfa):
    """[(url, vefat_gunu)] — kart: <a href="/vefat/slug"> ... <strong>Vefat:</strong> GG.AA.YYYY."""
    out, gor = [], set()
    for m in _KART.finditer(sayfa):
        g = _gun(oi.metin(m.group(2)).split("Vefat:")[-1]) if "Vefat:" in oi.metin(m.group(2)) else None
        u = urllib.parse.urljoin(HK_LISTE, m.group(1))
        if g and u not in gor:
            gor.add(u)
            out.append((u, g))
    return out


def hk_ilan(sayfa):
    """İlan sayfasından yalnız olgular: ad, vefat, ilçe, defin yeri/tarihi, doğum, cami+vakit. Başlık '<Ad> Vefat Etti' değilse None."""
    h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", sayfa)
    bas = oi.metin(h1.group(1)) if h1 else ""
    m = re.match(r"^(.{4,60}?)\s+Vefat\s+Etti\s*\d*$", bas, re.I)
    if not m:
        return None
    ad = oi.ad_duzelt(m.group(1))
    if not (2 <= len(ad.split()) <= 5) or re.search(r"[\d@:/()!]", ad):
        return None
    alan = {}
    for th, td in re.findall(r"<th[^>]*>([\s\S]*?)</th>\s*<td[^>]*>([\s\S]*?)</td>", sayfa):
        alan[ortak.tr_lower(oi.metin(th))] = oi.metin(td)
    vef = _gun(alan.get("doğum tarihi - vefat tarihi", "").split("-")[-1])
    dog = None
    d0 = alan.get("doğum tarihi - vefat tarihi", "").split(" - ")[0]
    if _gun(d0):
        dog = _gun(d0)
    govde = sayfa[h1.end():] if h1 else sayfa
    govde = oi.metin(govde.split("<table")[0])
    cumle = ob.cenaze_cumlesi(govde[:900])
    mem = (alan.get("memleket") or "").strip()
    defin = (alan.get("defin yeri") or "").strip()
    if not defin and cumle:                       # tabloda boşsa yalnız cenaze cümlesindeki mezarlık adı (cümle saklanmaz)
        d2 = oi.cenaze_ayikla(cumle)[1]
        defin = d2 if d2 and len(d2.split()) >= 2 else ""
    return {"ad": ad, "vefat": vef, "dogum": dog, "memleket": mem, "defin_yeri": defin,
            "defin_tarihi": _gun(alan.get("defin tarihi")), "namaz": ob.namaz_kisa(cumle) if cumle else None}


def hk_ilce(il, memleket):
    """'Yozgat Sorgun' -> Sorgun; 'Yozgat Merkez' / boş -> None (merkez TAHMİNİ yok). Başka ilin memleketi -> False (kayıt alınmaz)."""
    w = memleket.split()
    if not w:
        return None
    if ortak.katla(w[0]) != ortak.katla(il):
        return False
    for i in ortak.ilce_listesi(il):
        if ortak.katla(i) == ortak.katla(" ".join(w[1:])):
            return i
    return None


def hakimiyet(ctx):
    il = ctx["il"]
    sayfa = ok._onbellek(ctx, HK_LISTE, ok.ONBELLEK_SN)
    if sayfa is None:
        return []
    gl = set(ctx["gunler"])
    yol = os.path.join(ctx["klasor"], "_hakimiyet_olgu.json")
    try:
        sakli = json.load(open(yol, encoding="utf-8"))
    except Exception:
        sakli = {}
    n = 0
    for u, g in hk_kartlar(sayfa):
        if g not in gl or u in sakli:
            continue
        if n >= HK_ISTEK_TUR:
            break
        try:
            s = ob.al(ctx, u)
        except (ob.ButceDoldu, oi.Engel):
            break
        except Exception as e:
            print(f"  ilan açılamadı: {u}: {e}", file=sys.stderr)
            continue
        n += 1
        sakli[u] = {"olgu": hk_ilan(s), "vefat": g}
    ob.durum(ctx).kaydet()
    sinir = (date.today() - timedelta(days=10)).isoformat()
    sakli = {u: v for u, v in sakli.items() if v.get("vefat", "9") >= sinir}
    ortak.json_yaz(yol, sakli)
    sonuc = []
    for u, v in sakli.items():
        f = v.get("olgu")
        if not f:
            continue
        g = f["vefat"] or v["vefat"]
        ilce = hk_ilce(il, f["memleket"])
        if g not in gl or ilce is False:
            continue
        defin = ob.kisa(oi.buyuk_ise_title(f["defin_yeri"], yer=True)) if f["defin_yeri"] else None
        yas = None
        if f["dogum"]:
            y = int(g[:4]) - int(f["dogum"][:4])
            yas = y if 0 <= y <= 120 else None
        k = oi.kayit(il, ilce, "yozgat-yozgathakimiyet", f["ad"], g, HK_AD, u, ctx["alindi"], ek_id="", liste_tarihi=g, vefat_tarihi=g,
                     defin_yeri=defin, defin_zamani=f["defin_tarihi"], namaz_yeri_vakti=f["namaz"], yas=yas,
                     dogum_tarihi=f["dogum"], ham={"yayin_tarihi": g, "sayfa_tarihi": g, "tarih_kaynagi": "ilan_vefat_tarihi"})
        k["kaynak_turu"] = oh.KAYNAK_TURU
        if not ilce:
            k["ilce"] = None
            k["ilce_belirsiz"] = True
        dis = ob.il_disi_bul(il, defin) if defin else None
        if dis:
            k["il_disi_defin"] = {"il": dis, "ilce": None}
        sonuc.append(k)
    return sonuc


def main():
    oi.il_calistir(IL, "yozgat", [("Yozgat Hakimiyet (vefat sayfası)", hakimiyet), ("Sorgun", sorgun), ("Çekerek", cekerek)])


if __name__ == "__main__":
    main()
