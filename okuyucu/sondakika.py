#!/usr/bin/env python3
"""SONDAKIKA.COM YEREL AKIŞI (14.10.2026, H41). Tüm Türkiye; haber başlığında/etiketinde il adı geçer.
Kaynak: https://rss.sondakika.com/rss.asp?kategori=yerel (sitenin kendi RSS'i; sondakika.com sayfasındaki RSS bağlantısı; robots: Allow /),
~140 haber / 2 gün. Sayfalama (/yerel/2/ ...) yönlendirmeli, bu yüzden yalnız RSS. Gerekirse haber gövdesi (www.sondakika.com/yerel/haber-*; robots izinli).
Bütçe: host başına günde <= 40 istek (ortak_basin.GUNLUK_ISTEK), RSS en çok 2,5 saatte bir, tur başına <= 3 haber gövdesi, istekler arası >= 3,5 sn.
Alınan: yalnız olgu (ad soyad, yaş, il, ilçe, mahalle/köy, cami+vakit, defin yeri, cenaze günü) — ortak_haber ayrıştırıcıları; haber cümlesi/ölüm nedeni/yakın adı SAKLANMAZ.
Çıktı: veri/<il>/_ulusal.json (vefatilan.py ile AYNI dosya/şema; birleştirmede kayıt id'sine göre güncellenir; ulusal_birlestir.py son7gun'a katar).
kaynak_turu "yerel_basin", kaynak_ad "Son Dakika Yerel" (kapi.YEREL_BASIN: "Son Dakika Yerel": "www.sondakika.com").
Tarih: cenaze günü haber metninde açık/göreli ise ham.tarih_kaynagi="metin", yoksa yayın günü ("yayin_tarihi").
Kullanım: python3 okuyucu/sondakika.py [--kuru] [--gun 3] [--rss dosya.xml]  (--rss: yerel dosyadan, ağ yok)"""
import html, json, os, re, sys, time, urllib.error
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh

VERI = os.path.join(DIZIN, "..", "veri")
RSS = "https://rss.sondakika.com/rssnew.aspx?kategori=yerel"  # rss.asp 301 ile buraya yonlenir
KAYNAK_AD = "Son Dakika Yerel"
HOSTLAR = ("rss.sondakika.com", "www.sondakika.com")
ILCELER = json.load(open(os.path.join(DIZIN, "..", "uygulama", "assets", "veri", "ilceler.json"), encoding="utf-8"))
IL_KAT = {ortak.katla(il): il for il in ILCELER}
DURUM = os.path.join(VERI, "_sondakika_durum.json")
OLGU = os.path.join(VERI, "_sondakika_olgu.json")
RSS_ARALIK = 2.5 * 3600
GOVDE_TUR = 3


class Butce(Exception):
    pass


class Durum:
    def __init__(self):
        try:
            self.d = json.load(open(DURUM, encoding="utf-8"))
        except Exception:
            self.d = {}
        self.d.setdefault("istek", {})
        self.d.setdefault("robots", {})

    def say(self, host):
        a = self.d["istek"].setdefault(host, {})
        g = date.today().isoformat()
        if a.get(g, 0) >= ob.GUNLUK_ISTEK:
            raise Butce(f"{host}: günlük {ob.GUNLUK_ISTEK} istek doldu")
        a[g] = a.get(g, 0) + 1
        for k in [k for k in a if k < (date.today() - timedelta(days=5)).isoformat()]:
            del a[k]

    def kaydet(self):
        ortak.json_yaz(DURUM, self.d)


def indir(dr, url):
    p = url.split("/")[2]
    r = dr.d["robots"].get(p)
    if not r or r["tarih"] < (date.today() - timedelta(days=7)).isoformat():
        dr.say(p)
        try:
            g = ortak.indir(f"https://{p}/robots.txt", bekle=3.5, timeout=30)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise oi.Engel(f"{p} robots {e.code}")
            g = ""
        except Exception:
            g = ""
        if "<html" in g[:600].lower() or "user-agent" not in g.lower():
            g = ""
        r = dr.d["robots"][p] = {"tarih": date.today().isoformat(), "metin": g[:20000]}
    yol = "/" + url.split("/", 3)[3]
    if r["metin"] and not ortak.robots_kural(r["metin"], ortak.UA, yol):
        raise oi.Engel(f"robots yasak: {yol}")
    dr.say(p)
    try:
        return ortak.indir(url, bekle=3.5, timeout=40)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            raise oi.Engel(f"{p} {e.code} (dolanılmaz)")
        raise


def ogeler(xml):
    out = []
    for b in re.findall(r"<item>([\s\S]*?)</item>", xml):
        o = (oh.rss_ogeleri("<item>" + b + "</item>") or [None])[0]
        if not o:
            continue
        kw = re.search(r"<news:keywords>([\s\S]*?)</news:keywords>", b)
        o["etiket"] = [x.strip() for x in html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", kw.group(1) if kw else "")).split(",") if x.strip()]
        pd = re.search(r"<news:publication_date>([^<]*)", b)
        o["tarih"] = o["tarih"]                       # pubDate günü (+03:00 yerel gün)
        out.append(o)
    return out


def il_bul(o):
    """Etiketlerden il (81 il adı); yoksa başlıktan ilk yer-ekli il adı. Birden çok il etiketi varsa belirsiz -> başlıktaki."""
    et = {IL_KAT[ortak.katla(x)] for x in o["etiket"] if ortak.katla(x) in IL_KAT}
    ba = [IL_KAT[ortak.katla(re.split(r"['’]", w)[0])] for w in re.findall(r"[A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü]+(?:['’][a-zçğıöşü]+)?", o["baslik"]) if ortak.katla(re.split(r"['’]", w)[0]) in IL_KAT]
    if len(et) == 1:
        return next(iter(et))
    if ba and (not et or ba[0] in et):
        return ba[0]
    return None


def main():
    kuru = "--kuru" in sys.argv
    gun_n = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else 3
    dosya = sys.argv[sys.argv.index("--rss") + 1] if "--rss" in sys.argv else None
    bugun = date.today()
    sinir = (bugun - timedelta(days=gun_n)).isoformat()
    dr = Durum()
    try:
        olgu = json.load(open(OLGU, encoding="utf-8"))
    except Exception:
        olgu = {}
    ctx = {"alindi": ortak.simdi_iso()}
    xml = None
    if dosya:
        xml = open(dosya, encoding="utf-8").read()
    else:
        son = dr.d.get("rss_zaman", 0)
        yol_on = os.path.join(VERI, "_sondakika_rss.xml")
        if time.time() - son < RSS_ARALIK and os.path.exists(yol_on):
            xml = open(yol_on, encoding="utf-8").read()
        else:
            try:
                xml = indir(dr, RSS)
                if "<item>" not in xml:
                    raise RuntimeError("RSS tanınmadı")
                open(yol_on, "w", encoding="utf-8").write(xml)
                dr.d["rss_zaman"] = time.time()
            except (Butce, oi.Engel) as e:
                print(f"  RSS okunamadı: {e}", file=sys.stderr)
                if os.path.exists(yol_on):
                    xml = open(yol_on, encoding="utf-8").read()
    if not xml:
        dr.kaydet(); return
    sonuc, acilacak, say = {}, [], {"oge": 0, "vefat_basligi": 0, "il_yok": 0, "yerel_degil": 0}
    for o in ogeler(xml):
        say["oge"] += 1
        g = o["tarih"]
        if not g or g < sinir:
            continue
        vefat, olay = oh.vefat_haberi_mi(o["baslik"]), oh.olay_baslik_mi(o["baslik"])
        if not (vefat or olay):
            continue
        say["vefat_basligi"] += 1
        il = il_bul(o)
        if not il:
            say["il_yok"] += 1
            continue
        if o["url"] in olgu:
            for f in oh._sakli_olgular(olgu[o["url"]]):
                sonuc[(o["url"], f["ad"])] = (il, f, g, o["url"])
            continue
        y = oh.yerel_mi(il, o["baslik"], o["ozet"])
        if y is False:
            say["yerel_degil"] += 1
            continue
        f = oh.olgular(il, o["baslik"], o["ozet"], g) if vefat else None
        if f and (f["namaz"] or f["defin"] or f["namaz_t"] or f["defin_t"]):
            sonuc[(o["url"], f["ad"])] = (il, f, g, o["url"])
        elif f is None or not oh._ozet_yeterli(o["ozet"], o["baslik"]) or olay:
            acilacak.append((o, il, g, f))
        else:
            sonuc[(o["url"], f["ad"])] = (il, f, g, o["url"])
    n = 0
    for o, il, g, f0 in sorted(acilacak, key=lambda x: x[2], reverse=True):
        if kuru or n >= GOVDE_TUR or not o["url"].startswith("https://www.sondakika.com/"):
            continue
        try:
            sayfa = indir(dr, o["url"])
        except (Butce, oi.Engel) as e:
            print(f"  haber açılamadı: {e}", file=sys.stderr)
            break
        except Exception as e:
            print(f"  haber açılamadı: {o['url']}: {e}", file=sys.stderr)
            continue
        n += 1
        govde = ob.makale_govdesi(sayfa) or oh._ilk_paragraflar(sayfa, 40)
        bulunan = []
        if oh.vefat_haberi_mi(o["baslik"]):
            f = oh.olgular(il, o["baslik"], govde[:900], g)
            if f:
                bulunan.append(f)
        if oh.olay_baslik_mi(o["baslik"]):
            for f2 in oh.olay_olgulari(il, govde, g):
                bulunan = [x for x in bulunan if ortak.katla(x["ad"]) != ortak.katla(f2["ad"])] + [f2]
        olgu[o["url"]] = {"olgular": bulunan, "tarih": g, "il": il}
        for f in bulunan:
            sonuc[(o["url"], f["ad"])] = (il, f, g, o["url"])
    olgu = {u: v for u, v in olgu.items() if (v.get("tarih") or "") >= (bugun - timedelta(days=10)).isoformat()}
    kayitlar = {}
    for (u, _), (il, f, g, url) in sonuc.items():
        if f.get("defin") and re.fullmatch(r"(?:Mahalle|Köy|Aile|İlçe|Şehir|Kent)\s+Mezarl\w*", f["defin"]):
            f["defin"] = None
        k = oh.kayit_yap(ctx, il, "sondakika", KAYNAK_AD, url, f, g)
        k["id"] = ortak.kayit_id("sondakika", f["ad"], k["liste_tarihi"], il)
        kayitlar.setdefault(ortak.katla(il), []).append(k)
    say["kayit"] = sum(len(v) for v in kayitlar.values())
    say["il"] = {il: len(v) for il, v in sorted(kayitlar.items())}
    say["govde_acildi"] = n
    print(json.dumps(say, ensure_ascii=False))
    if kuru:
        ornek = [k for v in kayitlar.values() for k in v][:12]
        for k in ornek:
            print({a: k.get(a) for a in ("il", "ilce", "yas", "liste_tarihi", "namaz_yeri_vakti", "defin_yeri", "mahalle")}, k["ham"]["tarih_kaynagi"])
        return
    for slug, recs in kayitlar.items():
        yol = os.path.join(VERI, slug, "_ulusal.json")
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        try:
            eski = json.load(open(yol, encoding="utf-8")).get("kayitlar", [])
        except Exception:
            eski = []
        kay = {x["id"]: x for x in eski}
        kay.update({x["id"]: x for x in recs})
        kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
        ortak.json_yaz(yol, {"il": recs[0]["il"], "kayitlar": list(kay.values()), "guncelleme": ctx["alindi"]})
    ortak.json_yaz(OLGU, olgu)
    dr.kaydet()


if __name__ == "__main__":
    main()
