#!/usr/bin/env python3
"""ŞEHİT İLANLARI: resmî, herkese açık duyurulardan (URUN-TASLAGI §27, 14.10.2026) + yerel haber okuyucularının ikinci-il kayıtları.

1) DAĞIT: iller gruplara bölünerek okunduğu için bir okuyucu başka ilin kaydını il klasörüne yazamaz (kaybolur). ortak_haber, memleket (sicil) ili ile
   defin ili farklı olan şehidin öbür il kaydını veri/<okuyucu ili>/_sehit_ikinci.json'a yazar; bu betik onu hedef ilin veri/<il>/_ulusal.json'ına katar.
2) RESMÎ DUYURULAR: İçişleri Bakanlığı (/haberler-yeni), Emniyet Genel Müdürlüğü (/haberler), Jandarma Genel Komutanlığı (/haberler), 81 valilik
   (<il>.gov.tr/haberler) ve Milli Savunma Bakanlığı (msb.gov.tr). Hepsi herkese açık haber listesidir; robots.txt'ye uyulur (ortak_basin.al: 7 gün önbellek),
   aynı alan adına >= 3,5 sn, site başına günde <= 40 istek (ortak_basin.GUNLUK_ISTEK), 401/403/429 -> kaynak bırakılır. MSB sayfası JavaScript
   "challenge" doğrulaması gösteriyor (div#challenge): DOLANILMAZ, o gün atlanır.
   Başlığı şehit/şehadet içeren (ya da EGM/İçişleri "Tarihli Basın Açıklaması") son 3 günün duyuruları açılır; ortak_haber.sehit_olgulari ile
   ad + rütbe + memleket/defin ili + tören yeri çıkarılır (ölüm nedeni/olay ayrıntısı ALINMAZ). Duyuru yoksa (çoğu gün) sıfır kayıt NORMALDİR.
Çıktı (vefatilan.py / ulusal_birlestir.py kalıbı): veri/<il>/_ulusal.json {"il","kayitlar","guncelleme"}; kayıt şeması ortak.ALANLAR + sehit/rutbe/toren;
kaynak_turu YOK (resmî), kaynak_ad "<Kurum> duyurusu", kaynak_url duyuru sayfası, liste_tarihi tören/defin günü. Memleket ve defin ili farklıysa iki il.
Sıra (topla.yml 'birlestir'): vefatilan.py -> sehit_ulusal.py -> ulusal_birlestir.py -> kapi.py.
Kullanım: python3 okuyucu/sehit_ulusal.py [--kuru] [--yalniz-dagit] [--yalniz-resmi] [--gun 3] [--liste N] [--duyuru N]"""
import json, os, re, sys, html as _html
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob, ortak_haber as oh

VERI = os.environ.get("SEHIT_VERI") or os.path.join(DIZIN, "..", "veri")   # SEHIT_VERI: deneme klasörü
DURUM_KLASOR = os.path.join(VERI, "_sehit_ulusal")       # ortak_basin.Durum: istek sayacı, robots önbelleği, okunan duyurular
KAYNAK_SLUG = "sehit"
ULUSAL = [  # (kurum, taban adres, liste yolu)
    ("İçişleri Bakanlığı", "https://www.icisleri.gov.tr", "/haberler-yeni"),
    ("Emniyet Genel Müdürlüğü", "https://www.egm.gov.tr", "/haberler"),
    ("Jandarma Genel Komutanlığı", "https://www.jandarma.gov.tr", "/haberler"),
    ("Milli Savunma Bakanlığı", "https://www.msb.gov.tr", "/Basin-ve-Yayin/Haberler"),
]
LISTE_ARALIK_SAAT = 2          # aynı liste en çok 2 saatte bir
KOSU_AZAMI_LISTE = 30          # koşu başına en çok bu kadar valilik listesi (en eskiden başlayarak döner; ~2 dk)
KOSU_AZAMI_DUYURU = 8          # koşu başına açılan duyuru
KOSU_AZAMI_GENEL_BASIN = 2     # "Tarihli Basın Açıklaması" gibi başlıksız duyurulardan koşu başına
ARSIV_GUN = 5                  # _ulusal.json'da tutulan gün


def bugun():
    return date.today()


def il_adlari():
    return list(ortak.ilce_verisi().get("_iller", []))


def kaynaklar():
    """[(kurum, taban, yol, il|None, ulusal_mi)]"""
    out = [(k, t, y, None, True) for k, t, y in ULUSAL]
    seen = set()
    for il in il_adlari():
        if il in seen:
            continue
        seen.add(il)
        out.append((f"{il} Valiliği", f"https://www.{oh.il_slug(il)}.gov.tr", "/haberler", il, False))
    return out


# ---------------------------------------------------------------- liste / duyuru ayrıştırma (devlet sitelerinin ortak içerik sistemi)
_KART = re.compile(r'<a class="card news-card[^"]*" href="([^"]+)"[\s\S]*?cardDate">([^<]*)<[\s\S]*?card-title">([\s\S]*?)</h5>')


def kartlar(sayfa, taban):
    """Haber listesi -> [(tarih_iso, baslik, url)]."""
    if "msb.gov.tr" in taban:
        return msb_kartlari(sayfa)
    out = []
    for m in _KART.finditer(sayfa or ""):
        href, t, b = m.group(1), m.group(2).strip(), m.group(3)
        mt = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", t)
        if not mt:
            continue
        baslik = _html.unescape(" ".join(re.sub(r"<[^>]+>", " ", b).split())).replace("\xa0", " ").strip(" “”\"")
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = taban + href
        out.append((f"{mt.group(3)}-{mt.group(2)}-{mt.group(1)}", baslik, href))
    return out


def msb_kartlari(sayfa):
    """MSB haber listesi (/Basin-ve-Yayin/Haberler): /SlaytHaber/<id> bağlantıları; tarih listede yok (duyuru sayfasından okunur) -> None."""
    out, goruldu = [], set()
    for m in re.finditer(r'<a[^>]+href="(/SlaytHaber/[0-9a-f]+)"[^>]*>([\s\S]{0,400}?)</a>', sayfa or ""):
        baslik = _html.unescape(" ".join(re.sub(r"<[^>]+>", " ", m.group(2)).split())).strip()
        url = "https://www.msb.gov.tr" + m.group(1)
        if baslik and url not in goruldu:
            goruldu.add(url)
            out.append((None, baslik, url))
    return out


def duyuru_metni(sayfa):
    """Duyuru sayfası -> (baslik, govde, tarih_iso|None). Önce MSB düzeni (haber-title/haber-content), JSON-LD, ortak devlet içerik sistemi (div.icerik), <p>'ler."""
    tarih = None
    mt = re.search(r"(?:Tarih|card-date)[^0-9]{0,40}(\d{2})\.(\d{2})\.(\d{4})", sayfa or "")
    if mt:
        tarih = f"{mt.group(3)}-{mt.group(2)}-{mt.group(1)}"
    mh = re.search(r'<h1 class="haber-title">([\s\S]*?)</h1>', sayfa or "")
    mc = re.search(r'<div class="haber-content">([\s\S]*?)<small class="views"', sayfa or "")
    if mh and mc:
        return _html.unescape(" ".join(re.sub(r"<[^>]+>", " ", mh.group(1)).split())), ob.satirlara(mc.group(1)), tarih
    govde = ob.makale_govdesi(sayfa)
    if not govde:
        i = sayfa.find('class="icerik"')
        if i < 0:
            i = sayfa.find("detail-content-container")
        if i >= 0:
            seg = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", sayfa[i:i + 20000])
            seg = seg[seg.find(">") + 1:]                 # açılış etiketinin kendisi metne girmesin
            govde = ob.satirlara(seg)
    if not govde:
        govde = oh._ilk_paragraflar(sayfa, 40)
    m = re.search(r'<h2 class="page-title">\s*<span>([\s\S]*?)</span>', sayfa)
    baslik = _html.unescape(" ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())).strip(" “”\"") if m else oh.sayfa_basligi(sayfa)
    return baslik, govde, tarih


def bot_sayfasi_mi(sayfa):
    """JavaScript 'challenge' ara sayfası (MSB): içerik yok -> DOLANILMAZ."""
    s = sayfa or ""
    return "cardDate" not in s and ('id="challenge"' in s[:60000] or "http-equiv=\"refresh\"" in s[:60000])


# ---------------------------------------------------------------- kayıt dosyaları
def ulusal_yaz(il, kayitlar, kuru=False):
    """veri/<il slug>/_ulusal.json'a id'ye göre katar (daha dolu kayıt kalır), ARSIV_GUN'den eskileri atar. Dönen: yeni eklenen id sayısı."""
    slug = oh.il_slug(il)
    yol = os.path.join(VERI, slug, "_ulusal.json")
    try:
        with open(yol, encoding="utf-8") as fh:
            eski = json.load(fh).get("kayitlar", [])
    except Exception:
        eski = []
    kay = {k["id"]: k for k in eski}
    yeni = 0
    for r in kayitlar:
        o = kay.get(r["id"])
        if o is None:
            yeni += 1
            kay[r["id"]] = r
        elif sum(v not in (None, "", []) for v in r.values()) > sum(v not in (None, "", []) for v in o.values()):
            kay[r["id"]] = r
    sinir = (bugun() - timedelta(days=ARSIV_GUN)).isoformat()
    kay = {i: k for i, k in kay.items() if (k.get("liste_tarihi") or "") >= sinir}
    if not kuru and (yeni or kay or os.path.exists(yol)):
        ortak.json_yaz(yol, {"il": kayitlar[0]["il"] if kayitlar else il, "kayitlar": list(kay.values()), "guncelleme": ortak.simdi_iso()})
    return yeni


def dagit(kuru=False):
    """veri/<il>/_sehit_ikinci.json (yerel haber okuyucularının öbür-il kayıtları) -> hedef ilin _ulusal.json'ı."""
    gruplar, say = {}, 0
    if not os.path.isdir(VERI):
        return 0
    for ad in sorted(os.listdir(VERI)):
        yol = os.path.join(VERI, ad, "_sehit_ikinci.json")
        if not os.path.isfile(yol):
            continue
        try:
            with open(yol, encoding="utf-8") as fh:
                for k in json.load(fh).get("kayitlar", []):
                    if k.get("il") and k.get("sehit"):
                        gruplar.setdefault(k["il"], []).append(k)
        except Exception as e:
            print(f"  {yol} okunamadı: {e}", file=sys.stderr)
    for il, l in gruplar.items():
        say += ulusal_yaz(il, l, kuru)
    print(f"şehit ikinci-il dağıtımı: {sum(len(l) for l in gruplar.values())} kayıt, {len(gruplar)} il, {say} yeni")
    return say


# ---------------------------------------------------------------- resmî duyurular
def resmi_oku(kuru=False, gun=3, azami_liste=KOSU_AZAMI_LISTE, azami_duyuru=KOSU_AZAMI_DUYURU):
    os.makedirs(DURUM_KLASOR, exist_ok=True)
    ctx = {"klasor": DURUM_KLASOR, "alindi": ortak.simdi_iso(), "gunler": [(bugun() - timedelta(days=i)).isoformat() for i in range(gun + 1)]}
    d = ob.durum(ctx).d
    liste_son = d.setdefault("liste", {})
    engel = d.setdefault("engel", {})
    su_an = datetime.now()
    bugun_s = bugun().isoformat()
    sinir = (bugun() - timedelta(days=gun)).isoformat()
    hepsi = kaynaklar()
    # ulusal kaynaklar her koşuda (2 saat kuralı geçerli); valilikler en eski kontrolden başlayarak, koşu başına azami_liste
    def yas(k):
        s = liste_son.get(k[1] + k[2])
        return datetime.fromisoformat(s) if s else datetime.min
    uygun = [k for k in hepsi if (su_an - yas(k)).total_seconds() >= LISTE_ARALIK_SAAT * 3600 and engel.get(k[1]) != bugun_s]
    sec = [k for k in uygun if k[4]] + sorted([k for k in uygun if not k[4]], key=yas)[:azami_liste]
    adaylar, genel_basin, ozet = [], 0, {"liste": 0, "kart": 0, "engel": [], "hata": []}
    okunan = d["okunan"]
    for kurum, taban, yol, il, ulusal in sec:
        url = taban + yol
        try:
            sayfa = ob.al(ctx, url)
        except ob.ButceDoldu as e:
            print(f"  {e}", file=sys.stderr)
            continue
        except oi.Engel as e:
            engel[taban] = bugun_s
            ozet["engel"].append(f"{kurum}: {str(e)[:80]}")
            print(f"  {kurum}: ENGEL (bırakıldı): {e}", file=sys.stderr)
            continue
        except Exception as e:
            ozet["hata"].append(f"{kurum}: {type(e).__name__}")
            print(f"  {kurum}: liste okunamadı: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
            continue
        liste_son[url] = datetime.now().isoformat(timespec="seconds")
        if bot_sayfasi_mi(sayfa):
            engel[taban] = bugun_s
            ozet["engel"].append(f"{kurum}: bot doğrulama sayfası (JavaScript challenge) - dolanılmıyor")
            print(f"  {kurum}: bot doğrulama sayfası - atlandı (dolanılmaz)", file=sys.stderr)
            continue
        ozet["liste"] += 1
        for tarih, baslik, href in kartlar(sayfa, taban):
            if (tarih and tarih < sinir) or href in okunan:
                continue
            tarih = tarih or bugun_s                  # MSB: liste tarihsiz; gerçek tarih duyuru sayfasından okunur
            ozet["kart"] += 1
            if ob.sehit_baslik_adayi(baslik):
                adaylar.append((3, tarih, kurum, il, baslik, href))
            elif ulusal and re.search(r"(?i)tarihli\s+bas[ıi]n\s+a[çc][ıi]klamas", baslik) and tarih >= (bugun() - timedelta(days=1)).isoformat() and genel_basin < KOSU_AZAMI_GENEL_BASIN:
                genel_basin += 1
                adaylar.append((1, tarih, kurum, il, baslik, href))
    kayitlar_il = {}
    acilan = 0
    for _, tarih, kurum, il, baslik, href in sorted(adaylar, key=lambda x: (x[0], x[1]), reverse=True):
        if acilan >= azami_duyuru:
            break
        try:
            sayfa = ob.al(ctx, href)
        except ob.ButceDoldu as e:
            print(f"  {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"  duyuru açılamadı: {href}: {type(e).__name__}", file=sys.stderr)
            continue
        acilan += 1
        ob.okundu(ctx, href)
        b2, govde, t2 = duyuru_metni(sayfa)
        if t2:
            tarih = t2
        if tarih < sinir:
            print(f"  duyuru: {kurum} | {(b2 or baslik)[:60]} -> pencere dışı ({tarih})")
            continue
        f = oh.sehit_olgulari(il, b2 or baslik, govde, tarih)
        print(f"  duyuru: {kurum} | {(b2 or baslik)[:70]} -> " + ("şehit olgusu (ad gizli)" if f else "şehit değil/belirsiz"))
        if not f:
            continue
        yerli = oh.sehit_kayitlari(il, KAYNAK_SLUG, f"{kurum} duyurusu", href, f, tarih, ctx["alindi"], resmi=True)
        if not yerli:
            print("    yer (memleket/defin ili) duyuruda yok: kayıt açılmaz; cenaze duyurusu (valilik/İçişleri) gelince düşer")
        for il_k, k in yerli:
            kayitlar_il.setdefault(il_k, []).append(k)
    yeni = 0
    for il_k, l in kayitlar_il.items():
        yeni += ulusal_yaz(il_k, l, kuru)
    if not kuru:
        ob.durum(ctx).kaydet()
    ozet.update(acilan=acilan, yeni=yeni, guncelleme=ortak.simdi_iso())
    if not kuru:
        ortak.json_yaz(os.path.join(VERI, "_sehit_ulusal_son.json"), ozet)
    print(f"şehit resmî duyurular: {ozet['liste']} liste, {ozet['kart']} yeni kart, {acilan} duyuru açıldı, {yeni} yeni kayıt"
          + (f", engel/hata: {len(ozet['engel'])}/{len(ozet['hata'])}" if ozet["engel"] or ozet["hata"] else ""))
    return ozet


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    kuru = "--kuru" in a
    gun = int(a[a.index("--gun") + 1]) if "--gun" in a else 3
    liste = int(a[a.index("--liste") + 1]) if "--liste" in a else KOSU_AZAMI_LISTE
    duyuru = int(a[a.index("--duyuru") + 1]) if "--duyuru" in a else KOSU_AZAMI_DUYURU
    if "--yalniz-resmi" not in a:
        dagit(kuru)
    if "--yalniz-dagit" not in a:
        resmi_oku(kuru, gun, liste, duyuru)


if __name__ == "__main__":
    main()
