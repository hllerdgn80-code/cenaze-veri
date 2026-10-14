#!/usr/bin/env python3
"""KAYNAK KESIF (14.10.2026, §35 sira 3; YURUT H49). Her gun calisir.
1) Google Haberler RSS (YALNIZ kesif; baslik/icerik SAKLANMAZ, kisi adi yazilmaz): 81 il icin
   "<il>" ("vefat etti" OR "topraga verildi" OR "son yolculuguna ugurlandi" OR "cenaze namazi") when:7d
   Gunluk <= 30 istek, >= 3,5 sn aralik; sira 16 bos il once, kalani donusumlu (durum: arastirma/kesif/_kaynak_kesif_durum.json).
2) <source url> alan adlari toplanir; okuyucu/*.py + arastirma/kesif/* icindekilerle karsilastirilir; YENI olanlar il bazinda sayilir.
3) Yeni alan adi on incelemesi (en cok 10 istek/alan adi, gunde en cok 25 alan adi, sonuc 14 gun onbellek):
   robots.txt (ortak.robots_kural), ana sayfada RSS/feed baglantisi, /kategori/vefat* /vefat* /taziye /cenaze yollari 200 mu;
   403/429/CAPTCHA/Cloudflare gorulurse alan adi BIRAKILIR (dolanma yok).
4) Cikti: arastirma/kesif/gunluk/<tarih>.json + arastirma/kesif/ADAYLAR.md
Kullanim: python3 araclar/kaynak_kesif.py [--kuru] [--il agri,mus] [--sorgu-limit 30]"""
import json, os, re, sys, glob, time, urllib.error, urllib.parse, xml.etree.ElementTree as ET
from datetime import date, datetime

KOK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(KOK, "okuyucu"))
import ortak

KESIF = os.path.join(KOK, "arastirma", "kesif")
GUNLUK = os.path.join(KESIF, "gunluk")
DURUM = os.path.join(KESIF, "_kaynak_kesif_durum.json")
ADAYLAR = os.path.join(KESIF, "ADAYLAR.md")
SORGU_LIMIT = 30
ALAN_LIMIT = 25
ALAN_ISTEK = 10
ONBELLEK_GUN = 14

BOS_ILLER = "agri ardahan bayburt bingol bitlis eskisehir hakkari igdir kirklareli mardin mus siirt sirnak tunceli yozgat diyarbakir".split()
ADLAR = """Adana Adıyaman Afyonkarahisar Ağrı Aksaray Amasya Ankara Antalya Ardahan Artvin Aydın Balıkesir Bartın Batman Bayburt Bilecik Bingöl Bitlis Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli Diyarbakır Düzce Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep Giresun Gümüşhane Hakkâri Hatay Iğdır Isparta İstanbul İzmir Kahramanmaraş Karabük Karaman Kars Kastamonu Kayseri Kilis Kırıkkale Kırklareli Kırşehir Kocaeli Konya Kütahya Malatya Manisa Mardin Mersin Muğla Muş Nevşehir Niğde Ordu Osmaniye Rize Sakarya Samsun Şanlıurfa Siirt Sinop Sivas Şırnak Tekirdağ Tokat Trabzon Tunceli Uşak Van Yalova Yozgat Zonguldak""".split()
ATLA_ALAN = ("google.", "msn.com", "yahoo.", "youtube.", "facebook.", "twitter.", "x.com", "instagram.", "wikipedia.", "milliyet.", "haberler.com", "hurriyet.", "sabah.com.tr", "aa.com.tr", "ntv.com.tr", "cnnturk.", "sozcu.", "haberturk.", "mynet.", "trthaber.", "internethaber.", "ensonhaber.", "star.com.tr", "aksam.", "yenisafak.", "takvim.", "gazeteduvar.", "t24.", "bbc.", "dha.", "iha.", "ihlas", "tiktok.", "t.me")
VEFAT_YOLLAR = ["/kategori/vefat", "/kategori/vefat-haberleri", "/vefat", "/vefat-haberleri", "/vefat-edenler", "/taziye", "/cenaze", "/kategori/taziye", "/kategori/cenaze"]
ENGEL_IZ = re.compile(r"captcha|cf-chk|cloudflare|attention required|just a moment|g-recaptcha|are you a robot", re.I)


def katla(s):
    t = str.maketrans("ÇĞİIÖŞÜçğıöşüâîûÂÎÛ", "CGIIOSUcgiosuaiuAIU")
    return s.translate(t).lower().replace("i̇", "i")


SLUG = {katla(a): katla(a) for a in ADLAR}
SLUG[katla("Hakkâri")] = "hakkari"
IL = {katla(a): a for a in ADLAR}


def alan(h):
    h = (h or "").lower()
    if "//" in h:
        h = urllib.parse.urlparse(h).netloc
    h = h.split(":")[0]
    return re.sub(r"^(www|m|amp)\.", "", h)


def bilinenler():
    """(okuyucu alan adlari, liste alan adlari)"""
    ok, liste = set(), set()
    for f in glob.glob(os.path.join(KOK, "okuyucu", "*.py")):
        s = open(f, encoding="utf-8", errors="replace").read()
        for u in re.findall(r"https?://([A-Za-z0-9.-]+)", s):
            ok.add(alan(u))
        for u in re.findall(r"""["']((?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|biz|tv|com\.tr|org\.tr|net\.tr|gen\.tr)(?:\.tr)?)["']""", s):
            ok.add(alan(u))
    for f in glob.glob(os.path.join(KESIF, "*")):
        if os.path.isfile(f) and f.endswith((".json", ".jsonl", ".md", ".txt")):
            s = open(f, encoding="utf-8", errors="replace").read()
            for u in re.findall(r"(?:https?://)?((?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|biz|tv|com\.tr|org\.tr|net\.tr|gen\.tr|bel\.tr|gov\.tr))\b", s):
                liste.add(alan(u))
    return ok, liste - ok


def durum_oku():
    try:
        return json.load(open(DURUM, encoding="utf-8"))
    except Exception:
        return {"imlec": 0, "istek": {}, "alanlar": {}, "il_alan": {}}


def sorgu_url(il):
    q = f'"{il}" ("vefat etti" OR "toprağa verildi" OR "son yolculuğuna uğurlandı" OR "cenaze namazı") when:7d'
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "tr", "gl": "TR", "ceid": "TR:tr"})


def sira_sec(d, limit, istenen):
    """Once 16 bos il, kalani imlece gore donusumlu."""
    tum = [katla(a) for a in ADLAR]
    if istenen:
        return [i for i in istenen if i in tum][:limit]
    bos = [i for i in BOS_ILLER if i in tum]
    digerleri = [i for i in tum if i not in bos]
    kalan = max(0, limit - len(bos))
    im = d.get("imlec", 0) % len(digerleri)
    sec = [digerleri[(im + k) % len(digerleri)] for k in range(min(kalan, len(digerleri)))]
    d["imlec"] = (im + len(sec)) % len(digerleri)
    return (bos + sec)[:limit]


def rss_kaynaklari(il_slug):
    """Dondurur: (alan adi sayaci {alan: haber_sayisi}, belirsiz sayisi). Baslik SAKLANMAZ."""
    xml = ortak.indir(sorgu_url(IL[il_slug]), bekle=3.5, timeout=25)
    kok = ET.fromstring(xml)
    sayac, belirsiz = {}, 0
    for it in kok.iter("item"):
        t = katla(it.findtext("title") or "")
        kay = it.find("source")
        a = alan(kay.get("url")) if kay is not None else ""
        if not a or a.startswith(ATLA_ALAN):
            continue
        if il_slug not in t and IL[il_slug] and katla(kay.text or "").find(il_slug) < 0 and il_slug not in a:
            belirsiz += 1
            continue
        sayac[a] = sayac.get(a, 0) + 1
    return sayac, belirsiz


def on_inceleme(host):
    """Dondurur sozluk. En cok ALAN_ISTEK istek; engel gorunce BIRAKIR."""
    r = {"tarih": date.today().isoformat(), "robots_izinli": None, "feed": False, "vefat_sayfasi": [], "durum": "?", "istek": 0}
    base = "https://" + host

    def al(yol):
        if r["istek"] >= ALAN_ISTEK:
            raise RuntimeError("butce")
        r["istek"] += 1
        return ortak.indir(base + yol, bekle=3.5, timeout=20)

    def engel(e):
        return isinstance(e, urllib.error.HTTPError) and e.code in (401, 403, 429, 503)

    try:
        rb = ""
        try:
            rb = al("/robots.txt")
            if "<html" in rb[:600].lower() or "user-agent" not in rb.lower():
                rb = ""
        except urllib.error.HTTPError as e:
            if engel(e):
                r["durum"] = f"ENGEL robots {e.code}"; r["robots_izinli"] = False
                return r
        izin = lambda y: (not rb) or ortak.robots_kural(rb, ortak.UA, y)
        r["robots_izinli"] = izin("/")
        if not r["robots_izinli"]:
            r["durum"] = "ROBOTS KAPALI"
            return r
        try:
            ana = al("/")
        except urllib.error.HTTPError as e:
            r["durum"] = f"ENGEL ana {e.code}" if engel(e) else f"HTTP {e.code}"
            return r
        if ENGEL_IZ.search(ana[:4000]) and len(ana) < 20000:
            r["durum"] = "CAPTCHA/Cloudflare"
            return r
        r["feed"] = bool(re.search(r'<link[^>]+type="application/(?:rss|atom)\+xml"', ana, re.I)) or bool(re.search(r'href="[^"]*(?:/feed|/rss)[^"]*"', ana, re.I))
        # menuden vefat/taziye/cenaze baglantisi
        yollar = []
        for h in set(re.findall(r'href="([^"#]+)"', ana)):
            p = urllib.parse.urlparse(urllib.parse.urljoin(base + "/", h))
            if alan(p.netloc) == host and re.search(r"vefat|taziye|cenaze|olum-ilan", p.path, re.I) and len(p.path) < 70 and not re.search(r"\d{5,}|\.(jpg|png)", p.path):
                yollar.append(p.path)
        r["menu_yollar"] = sorted(set(yollar))[:6]
        adaylar = (r["menu_yollar"][:3]) + [y for y in VEFAT_YOLLAR if y not in yollar]
        for y in adaylar:
            if r["istek"] >= ALAN_ISTEK:
                break
            if not izin(y):
                continue
            try:
                s = al(y)
                if len(s) > 2000 and re.search(r"<article|<item|<h2|<h3", s):
                    r["vefat_sayfasi"].append(y)
                    if len(r["vefat_sayfasi"]) >= 2:
                        break
            except urllib.error.HTTPError as e:
                if engel(e):
                    r["durum"] = f"ENGEL {e.code}"
                    return r
            except Exception:
                pass
        r["durum"] = "VAR" if r["vefat_sayfasi"] else "VEFAT SAYFASI YOK"
    except RuntimeError:
        r["durum"] = "butce"
    except Exception as e:
        r["durum"] = f"HATA {type(e).__name__}: {str(e)[:60]}"
    return r


def puan(haber, r):
    p = haber
    if r:
        if r.get("vefat_sayfasi"):
            p += 3
        if r.get("robots_izinli"):
            p += 2
        if r.get("feed"):
            p += 1
        if str(r.get("durum", "")).startswith(("ENGEL", "ROBOTS", "CAPTCHA")):
            p = 0
    return p


def adaylar_yaz(d, ok, liste):
    il_alan = d["il_alan"]  # {il: {alan: haber}}
    satirlar = []
    for il, m in il_alan.items():
        for a, n in m.items():
            if a in ok or a.startswith(ATLA_ALAN) or any(x in a for x in ATLA_ALAN):
                continue
            r = d["alanlar"].get(a)
            satirlar.append((puan(n, r), il, a, n, r, a in liste))
    satirlar.sort(key=lambda x: (-x[0], x[1], x[2]))
    bos = set(BOS_ILLER)
    L = ["# KAYNAK ADAYLARI (araclar/kaynak_kesif.py; otomatik, elle duzenleme)", "",
         f"Guncelleme: {datetime.now():%d.%m.%Y %H:%M}. Puan = haber sayisi (7 gun, toplam) + vefat sayfasi var (+3) + robots izinli (+2) + feed (+1); ENGEL/ROBOTS KAPALI/CAPTCHA = 0.",
         "Yalniz keşif: Google Haberler baslik/icerigi saklanmaz. 'liste' = arastirma/kesif/* dosyalarinda zaten gecen ama okuyucusu olmayan alan adi.", "",
         "| Puan | Il | Alan adi | Haber | Vefat sayfasi | Robots | Feed | Durum | Not |", "|---|---|---|---|---|---|---|---|---|"]
    for p, il, a, n, r, lis in satirlar[:150]:
        rr = r or {}
        L.append(f"| {p} | {il}{' (BOS IL)' if SLUG.get(il) in bos or il in bos else ''} | {a} | {n} | {', '.join(rr.get('vefat_sayfasi') or []) or ('-' if r else '?')} | "
                 f"{'evet' if rr.get('robots_izinli') else ('hayir' if r else '?')} | {'evet' if rr.get('feed') else ('-' if r else '?')} | {rr.get('durum', 'on inceleme bekliyor')} | {'liste' if lis else 'YENI'} |")
    open(ADAYLAR, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return satirlar


def main():
    args = sys.argv[1:]
    kuru = "--kuru" in args
    limit = SORGU_LIMIT
    istenen = []
    if "--sorgu-limit" in args:
        limit = min(SORGU_LIMIT, int(args[args.index("--sorgu-limit") + 1]))
    if "--il" in args:
        istenen = [katla(x) for x in args[args.index("--il") + 1].split(",")]
    os.makedirs(GUNLUK, exist_ok=True)
    d = durum_oku()
    bugun = date.today().isoformat()
    kullanilan = d["istek"].get(bugun, 0)
    ok, liste = bilinenler()
    print(f"bilinen alan adi: okuyucu {len(ok)}, liste {len(liste)}; bugun kullanilan sorgu {kullanilan}/{SORGU_LIMIT}")
    sira = sira_sec(d, max(0, min(limit, SORGU_LIMIT - kullanilan)), istenen)
    gun = {"tarih": bugun, "sorgulanan_iller": [], "il_alan_yeni": {}, "belirsiz": 0, "hata": {}}
    for il in sira:
        try:
            sayac, bel = rss_kaynaklari(il)
        except urllib.error.HTTPError as e:
            gun["hata"][il] = f"HTTP {e.code}"
            if e.code in (429, 503, 403):
                print("Google Haberler", e.code, "-> durduruldu"); break
            continue
        except Exception as e:
            gun["hata"][il] = f"{type(e).__name__}"
            continue
        kullanilan += 1
        d["istek"][bugun] = kullanilan
        gun["sorgulanan_iller"].append(il)
        gun["belirsiz"] += bel
        yeni = {a: n for a, n in sayac.items() if a not in ok}
        if yeni:
            gun["il_alan_yeni"][IL[il]] = yeni
            tut = d["il_alan"].setdefault(IL[il], {})
            for a, n in yeni.items():
                tut[a] = max(tut.get(a, 0), n)
        print(f"{IL[il]:14s} kaynak {len(sayac):2d}  yeni {len(yeni):2d}")
    # on inceleme
    gunluk_alan = set()
    for m in d["il_alan"].values():
        gunluk_alan.update(m)
    toplam = {}
    for m in d["il_alan"].values():
        for a, n in m.items():
            toplam[a] = toplam.get(a, 0) + n
    sirali = sorted(gunluk_alan, key=lambda a: -toplam[a])
    yapilan = 0
    bugun_dt = date.today()
    for a in sirali:
        if kuru or yapilan >= ALAN_LIMIT:
            break
        r = d["alanlar"].get(a)
        if r and (bugun_dt - date.fromisoformat(r["tarih"])).days < ONBELLEK_GUN:
            continue
        d["alanlar"][a] = on_inceleme(a)
        yapilan += 1
        rr = d["alanlar"][a]
        print(f"  on inceleme {a}: {rr['durum']} vefat={rr['vefat_sayfasi']} feed={rr['feed']}")
        ortak.json_yaz(DURUM, d)
    gun["on_inceleme_yapilan"] = yapilan
    gun["alan_sonuc"] = {a: d["alanlar"][a] for a in gunluk_alan if a in d["alanlar"] and d["alanlar"][a]["tarih"] == bugun}
    ortak.json_yaz(os.path.join(GUNLUK, bugun + ".json"), gun)
    ortak.json_yaz(DURUM, d)
    s = adaylar_yaz(d, ok, liste)
    print(f"ADAYLAR.md: {len(s)} satir; sorgu bugun {kullanilan}/{SORGU_LIMIT}; on inceleme {yapilan}")


if __name__ == "__main__":
    main()
