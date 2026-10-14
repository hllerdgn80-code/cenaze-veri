#!/usr/bin/env python3
"""ULUSAL TOPLAYICI #2: cenazeilanlari.com.tr (14.10.2026, §35 sıra 2). vefatilan.py kalıbı; çıktı veri/<il>/_ulusal.json (id ile birleşir).
Site: ücretsiz ilan sitesi (aile/muhtar girişi + yönetimin kendi girdiği kayıtlar). İl sayfası /cenazeilanlari/<il> = o ilin EN YENİ 30 ilanı
(sayfa içinde tarihe göre dizili; sayfa=2.. daha eskiler). Kart: AD, Yaş, "İl / İlçe / Mahalle", sağ üstte tarih (= ilan metnindeki vefat/defin günü; 3 örnekte vefat = defin = kart tarihi).
robots.txt: Disallow yalnız /yonetim/ -> liste sayfaları serbest. Hız: >=3,6 sn; GÜNDE <=40 istek/site (durum dosyası sayar); il başına günde 1 ziyaret.
Alınan alanlar: ad soyad, yaş (0 = bilinmiyor -> boş), il, ilçe (yalnız ilin gerçek ilçesi), tarih. ALINMAYAN: ilan metni, anne-baba, mahalle, dua/taziye sayaçları, yayıncı adı.
TEST/SAHTE kayıt süzgeci: ad içinde 'test' geçen kayıt atlanır (Ağrı'da 'DİYADİN TEST' görüldü). Detay sayfası (cami/mezarlık) AÇILMAZ: istek bütçesi liste sayfalarına ayrıldı.
Öncelik: veri/kaynağı az iller (CLAUDE H41 listesi + İstanbul/Samsun/Trabzon/Gümüşhane/Rize). Hepsini her gün gezmek 81 istek ister (>40) -> kapsam dışı.
Çıktı alanları vefatilan.py ile AYNI şema; kaynak_ad = "cenazeilanlari.com.tr" (kapi.YEREL_BASIN'a eklenmeli: {"cenazeilanlari.com.tr": "cenazeilanlari.com.tr"}).
Kullanım: python3 okuyucu/cenazeilanlari.py [--kuru] [--gun 3] [--il bayburt,samsun] [--azami-tur 12]"""
import html, json, os, re, sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

DIZIN = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(DIZIN, "..", "veri")
TABAN = "https://cenazeilanlari.com.tr"
KAYNAK_AD = "cenazeilanlari.com.tr"
BEKLE = 3.6
GUNLUK_AZAMI = 40          # site başına günlük istek tavanı
TUR_AZAMI = 12             # koşu başına istek (saatlik cron'da günlük bütçe yayılsın)
KAYNAK_TURU = "yerel_basin"
ILCELER = json.load(open(os.path.join(DIZIN, "..", "uygulama", "assets", "veri", "ilceler.json"), encoding="utf-8"))

_TR = str.maketrans("çğıöşüÇĞİÖŞÜI", "cgiosucgiosuı")


def kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9]+", "", s)


IL_ADI = {kat(il): il for il in ILCELER}
ILCE_TAM = {kat(il): {kat(i): i for i in ilc} for il, ilc in ILCELER.items()}
ONCELIK = ["agri", "ardahan", "bayburt", "bingol", "bitlis", "diyarbakir", "eskisehir", "hakkari", "igdir", "kars", "kilis", "kirklareli",
           "malatya", "manisa", "mardin", "mus", "siirt", "sirnak", "tunceli", "yozgat", "istanbul", "samsun", "trabzon", "gumushane", "rize"]


def bugun_tr():
    return (datetime.now(timezone.utc) + timedelta(hours=3)).date()


def tarih_iso(s):
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", (s or "").strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None


def kartlar(s):
    """İl sayfası -> [{id, ad, yas, il, ilce, tarih}] (yalnız kart alanları)."""
    out = []
    for blok in re.split(r'(?=<a href="cenazeilani/)', s)[1:]:
        m = re.match(r'<a href="cenazeilani/([^"]+)-(\d+)"', blok)
        ad = re.search(r"<b>([^<]*)</b>", blok)
        yas = re.search(r"Yaş\s*:\s*(\d+)", blok)
        alt = re.search(r'c-showcase-box__subtitle[^>]*>([^<]*)<', blok)
        trh = re.search(r'top: 25px;">\s*([0-9.]+)\s*<', blok)
        if not (m and ad and alt and trh):
            continue
        parca = [x.strip() for x in html.unescape(alt.group(1)).split("/")]
        iso = tarih_iso(trh.group(1))
        if len(parca) < 2 or not iso:
            continue
        out.append({"id": m.group(2), "ad": html.unescape(ad.group(1)).strip(), "yas": int(yas.group(1)) if yas else 0,
                    "il": parca[0], "ilce": parca[1], "tarih": iso})
    return out


def ad_uygun(ad):
    t = kat(ad)
    if "test" in t or "deneme" in t:
        return False
    kel = ad.split()
    return 2 <= len(kel) <= 5 and not re.search(r"[\d@:/()!]", ad)


def kayit(k, alindi, il_klasor):
    il_k = kat(k["il"])
    if il_k != il_klasor or il_k not in IL_ADI:          # sayfanın ilinden başka il (kayıt kayması) alınmaz
        return None
    if not ad_uygun(k["ad"]):
        return None
    ilce = ILCE_TAM[il_k].get(kat(k["ilce"])) or ("Merkez" if kat(k["ilce"]) == "merkez" else None)
    ad = ortak.tr_title(k["ad"])
    r = {a: None for a in ortak.ALANLAR}
    r.update({"id": ortak.kayit_id("cenazeilanlari", ad, k["tarih"], k["il"] + "|" + (k["ilce"] or "") + "|" + k["id"]),
              "il": IL_ADI[il_k], "ilce": ilce, "ad_soyad": ad, "yas": k["yas"] or None,
              "vefat_tarihi": k["tarih"], "liste_tarihi": k["tarih"], "kaynak_ad": KAYNAK_AD, "kaynak_url": TABAN + "/",
              "alindi": alindi, "il_disi_defin": None, "ilce_belirsiz": ilce is None,
              "ham": {"tarih_kaynagi": "ilan_vefat_tarihi", "sayfa_tarihi": k["tarih"], "not": "kart tarihi = ilandaki Defin Tarihi (vefat gunu ya da ayni gun)"}})
    r["kaynak_turu"] = KAYNAK_TURU
    return r


def main():
    kuru = "--kuru" in sys.argv
    gun = int(sys.argv[sys.argv.index("--gun") + 1]) if "--gun" in sys.argv else 3
    tur_azami = int(sys.argv[sys.argv.index("--azami-tur") + 1]) if "--azami-tur" in sys.argv else TUR_AZAMI
    iller = sys.argv[sys.argv.index("--il") + 1].split(",") if "--il" in sys.argv else list(ONCELIK)
    bugun = bugun_tr()
    sinir = (bugun - timedelta(days=gun)).isoformat()
    ileri = (bugun + timedelta(days=1)).isoformat()      # ileri tarihli kayıt (kaynak hatası) alınmaz
    durum_yol = os.path.join(VERI, "_cenazeilanlari_durum.json")
    try:
        durum = json.load(open(durum_yol, encoding="utf-8"))
    except Exception:
        durum = {}
    if durum.get("gun") != bugun.isoformat():
        durum.update({"gun": bugun.isoformat(), "istek": 0, "ziyaret": {}})
    alindi = ortak.simdi_iso()
    sira = sorted([i for i in iller if durum["ziyaret"].get(i) is None], key=lambda i: iller.index(i))
    toplam, tur_istek, yeni = 0, 0, {}
    for slug in sira:
        if tur_istek >= tur_azami or durum["istek"] >= GUNLUK_AZAMI:
            break
        if slug not in IL_ADI:
            continue
        try:
            sayfa = ortak.indir(f"{TABAN}/cenazeilanlari/{slug}", bekle=BEKLE)
            sayfa = sayfa.decode("utf-8", "replace") if isinstance(sayfa, bytes) else sayfa
        except Exception as e:
            print(f"  {slug} okunamadı: {str(e)[:80]}", file=sys.stderr)
            durum["istek"] += 1
            tur_istek += 1
            continue
        durum["istek"] += 1
        tur_istek += 1
        durum["ziyaret"][slug] = alindi
        kl = kartlar(sayfa)
        n_test = sum(1 for k in kl if not ad_uygun(k["ad"]))
        say = 0
        for k in kl:
            if not (sinir <= k["tarih"] <= ileri):
                continue
            r = kayit(k, alindi, slug)
            if r:
                yeni.setdefault(slug, []).append(r)
                say += 1
                toplam += 1
        print(f"  {slug}: {len(kl)} kart, {say} pencerede, {n_test} elenen (test/ad)", file=sys.stderr)
    if kuru:
        print(f"[kuru] {toplam} kayıt, {len(yeni)} il, istek {tur_istek} (bugün toplam {durum['istek']})")
        return
    for slug, recs in yeni.items():
        yol = os.path.join(VERI, slug, "_ulusal.json")
        eski = []
        try:
            eski = json.load(open(yol, encoding="utf-8")).get("kayitlar", [])
        except Exception:
            pass
        kay = {x["id"]: x for x in eski}
        kay.update({x["id"]: x for x in recs})
        kay = {i: x for i, x in kay.items() if (x.get("liste_tarihi") or "") >= sinir}
        ortak.json_yaz(yol, {"il": IL_ADI.get(slug, slug), "kayitlar": list(kay.values()), "guncelleme": alindi})
    ortak.json_yaz(durum_yol, durum)
    print(f"cenazeilanlari: {toplam} kayıt, {len(yeni)} il, bu koşuda {tur_istek} istek (bugün {durum['istek']}/{GUNLUK_AZAMI})")


if __name__ == "__main__":
    main()
