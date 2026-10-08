#!/usr/bin/env python3
"""KAPI: yayından önce çalışan makine denetçisi (08.10.2026).

Girdi: veri/<il>/son7gun.json. Kuralı geçmeyen kayıt son7gun.json'dan ÇIKARILIR ve veri/<il>/_kapi_red.json'a yazılır;
özet veri/kapi.json. veri/ozet.json varsa il başına kayıt sayısı güncellenir. Gün dosyalarına dokunulmaz (bir sonraki
okuma son7gun'u yeniden kurar, kapı yine çalışır).

Kurallar (her kayıt):
  K1 zorunlu alan: ad_soyad, kaynak_url ve tarih (resmî: vefat|namaz|defin|liste_tarihi; yerel basın: vefat|namaz|defin
     ya da ham.tarih_kaynagi işaretli ilan günü)
  K2 ad: 2-5 sözcük; rakam, URL, @, ünlem, parantez yok (karşılaştırma büyük harfe normalize edilmiş adla yapılır)
  K3 tarih: geçerli YYYY-AA-GG; liste_tarihi pencerede (son 8 gün .. +2 gün); hiçbir tarih bugünden 2 günden ileri değil
  K4 kişisel veri: metin alanlarında telefon / TC kimlik no / e-posta / açık adres kalıbı yok (cami/mezarlık alanlarında
     "sokak/cadde" yer adıdır; orada yalnız kapı no / daire / kat / apartman elenir)
  K5 ölüm nedeni / hastalık sözcüğü yok
  K6 aynı kişi aynı gün tekrar yok (resmî kaynak önce tutulur, yerel basın kopyası elenir); yerel_haber kaydı aynı adla ±3 gün
     içinde daha önce tutulmuş bir kayıt varsa elenir (vefat ve defin haberi, iki site)
  K7 kaynak_url http(s) ve aynı kaynak_ad'ın kayıtlarıyla AYNI alan adından; yerel basında kayıtlı alan adı
  K8 (kaynak_turu "yerel_basin" ya da "yerel_haber") sitenin cümlesi yok: alan değerleri <= 60 karakter; "vefat etmiştir/etti",
     "başsağlığı", "Allah rahmet", "rahmetine kavuş", "taziye" gibi cümle parçaları yok
Kullanım: python3 okuyucu/kapi.py [il ...] [--kuru]     (--kuru: yalnız rapor, dosyalar değişmez)
          python3 okuyucu/hepsi.py --kapi           (aynısı, tüm iller)
"""
import json, os, re, sys, urllib.parse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak

VERI = os.path.join(DIZIN, "..", "veri")

# yerel basın kaynakları: kaynak_ad -> izinli alan adı (yeni site eklenince buraya da yazılır)
YEREL_BASIN = {
    "Ankara Net Haber": "www.ankaranethaber.com",
    "Merzifon Bilgi Gazetesi": "www.merzifonbilgigazetesi.com",
    "Mardin Haber Gazetesi": "mardinhaber.com.tr",
    "Artı Siirt": "www.artisiirt.com",
    "Siirt Haberci": "www.siirthaberci.com",
    "Kurtalan Gazetesi": "www.kurtalangazetesi.com",
    "Bitlis Haber": "www.bitlishaber13.net",
    "Akhisar Haber": "www.akhisarhaber.net",
    # YEREL HABER (tek kişilik vefat haberleri, ortak_haber.py; 08.10.2026). Karşılaştırmada baştaki "www." yok sayılır.
    "Doğubayazıt Gazetesi": "dogubayazitgazetesi.com", "Ağrı Hürses": "agrihurses.net", "Patnos Haber Gazetesi": "patnoshabergazetesi.com",
    "Ardahan Haber": "ardahanhaber.com.tr",
    "Bayburt Haber": "bayburthaber.com", "Bayburt Haber Ajansı": "bayburthaberajansi.com.tr", "Bayburt Gündem": "bayburtgundem.com",
    "Bingöl Kent Haber": "bingolkenthaber.com", "Bingöl Online": "bingolonline.com",
    "Osmancık Haber": "osmancik.com.tr", "Çorum Hakimiyet": "corumhakimiyet.net", "Leblebi TV": "leblebi.tv",
    "Yayla Haber": "yaylahaber.com.tr", "Çorum Haber": "corumhaber.net",
    "Bismil Haber": "bismilhaber.com.tr", "Mücadele Gazetesi": "mucadelegazetesi.com.tr", "Diyarbakır Söz": "diyarbakirsoz.com",
    "Sakarya Gazetesi": "sakaryagazetesi.com.tr", "Sonhaber": "sonhaber.com.tr", "İstikbal Gazetesi": "istikbalgazetesi.com",
    "Hakkari İl Sesi": "hakkariilsesigazetesi.com", "Gazete Pano": "gazetepano.com", "Yüksekova Halkın Sesi": "yuksekovahalkinsesigazetesi.com",
    "Yeşil Iğdır": "yesiligdir.com", "Iğdır Haber": "igdirhaber.net",
    "Kars Manşet": "karsmanset.com", "Haber Sarıkamış": "habersarikamis.com", "Kars Hakimiyet": "karshakimiyet.com",
    "Taşköprü Postası": "taskoprupostasi.com", "Kastamonu İstiklal": "kastamonuistiklal.com", "Kastamonu Haber": "kastamonuhaber.com",
    "Açıksöz": "aciksoz.com.tr",
    "Kilis Kent Haber": "kiliskenthaber.com", "Kilis Olay": "kilisolay.com",
    "Alternatif Gazetesi": "alternatifgazetesi.com", "Kırklareli Gazetesi": "kirklareligazetesi.com.tr",
    "Çukurova Gazetesi": "cukurovagazetesi.com", "Mersin Haber Merkezi": "mersinhabermerkezi.com", "İmece Gazetesi": "imecegazetesi.com",
    "İste Mersin": "istemersin.com",
    "Haber49": "haber49.net",
    "Şırnak Ajans": "sirnakajans.com", "Şırnak Haber": "sirnakhaber.com", "Şırnak Haber 73": "sirnakhaber73.com",
    "Tunceli Emek": "tunceliemek.com.tr",
    "Yeni Bakış": "yenibakishaber.com", "Ege Telgraf": "egetelgraf.com", "Dokuz Eylül": "dokuzeylul.com", "Son Mühür": "sonmuhur.com",
}
BASIN_TURLERI = ("yerel_basin", "yerel_haber")


def _www(h):
    h = (h or "").lower()
    return h[4:] if h.startswith("www.") else h

TARIH_ALANLARI = ("vefat_tarihi", "namaz_tarihi", "defin_zamani", "liste_tarihi", "dogum_tarihi")
TARAMA_DISI = {"id", "kaynak_url", "alindi", "il", "kaynak_turu"} | set(TARIH_ALANLARI)

TEL = re.compile(r"(?<!\d)(?:\+?90[\s.-]?)?\(?0?\s?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)"
                 r"|(?<!\d)\(?0[2-4]\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)")
TC = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")
EPOSTA = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
ADRES = re.compile(r"\b(?:sokak|sokağı|sokağında|sk\.|cadde|caddesi|cd\.|bulvarı|apartmanı|apartman|apt\.|daire\s*\d|"
                   r"kat\s*:\s*\d|no\s*[:.]?\s*\d+\s*/\s*\d+|no\s*:\s*\d+|kapı\s+no|posta\s+kodu)\b", re.I)
NEDEN = re.compile(r"\b(?:kanser\w*|tümör\w*|lösemi\w*|kalp\s+kriz\w*|kalp\s+yetmezli\w*|beyin\s+kanama\w*|felç\w*|"
                   r"covid\w*|korona\w*|zatürre\w*|böbrek\s+yetmezli\w*|siroz\w*|şeker\s+hastalı\w*|alzheimer\w*|demans\w*|"
                   r"intihar\w*|cinayet\w*|öldürül\w*|bıçakla\w*|silahla\w*|vurularak|vuruldu\w*|kaza|kazası|kazasında|kazada|"
                   r"boğularak|boğuldu\w*|zehirlen\w*|yanarak|hastalığ\w*|hastalık\w*|rahatsızlı\w*|yoğun\s+bakım\w*|"
                   r"ameliyat\w*|tedavi\s+gör\w*|ölüm\s+nedeni|ölüm\s+sebebi)\b", re.I)
BASIN_CUMLE = re.compile(r"(?:vefat\s+et(?:miştir|ti|mişti)|başsağlığı|allah['’]?\s*(?:tan)?\s*rahmet|rahmetine\s+kavuş|taziye|"
                         r"mekan[ıi]\s+cennet|ruhu\s+için|el\s+fatiha|hakk?['’]?[ıi]n\s+rahmeti)", re.I)
AD_YASAK = re.compile(r"[\d!@()\[\]]|https?:|www\.|\.com|\.tr\b", re.I)   # parantez: takma ad/ayrıştırma artığı ("Aydın) Sedat Aygün")
# cami / mezarlık alanlarında "sokak/cadde" bir YER ADIDIR ("Aşağı Sokak Camii", Ordu Tekkeköy; 08.10.2026 denetimi: yanlış eleme);
# bu alanlarda yalnız kişiye ait açık adres işaretleri (kapı no, daire, kat, apartman) elenir
YER_ALANLARI = {"defin_yeri", "namaz_yeri_vakti", "ham.cami", "ham.mezarlik", "ham.namaz", "ham.namaz_yeri", "ham.defin_yeri"}
ADRES_GUCLU = re.compile(r"\b(?:apartmanı|apartman|apt\.|daire\s*\d|kat\s*:\s*\d|no\s*[:.]?\s*\d+\s*/\s*\d+|no\s*:\s*\d+|kapı\s+no|posta\s+kodu)\b", re.I)


def _metinler(k):
    """Kaydın taranacak metin değerleri: (alan, değer)."""
    for a, v in k.items():
        if a in TARAMA_DISI or v is None:
            continue
        if isinstance(v, str):
            yield a, v
        elif isinstance(v, dict):
            for a2, v2 in v.items():
                if isinstance(v2, str) and a2 not in TARIH_ALANLARI and not re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", v2) \
                        and not re.fullmatch(r"[0-9a-fA-F-]{16,}", v2):          # kaynak kimliği (UUID/hex) telefon sanılmasın
                    yield f"{a}.{a2}", v2


def _gun(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def ad_anahtar(ad):
    """Büyük harfe normalize edilmiş karşılaştırma anahtarı (Türkçe harfler sadeleşmiş)."""
    return ortak.katla(ad).upper()


def denetle(k, bugun, alan_adi_cogunluk):
    nedenler = []
    ad = (k.get("ad_soyad") or "").strip()
    # K1
    # tarih: resmî kaynakta liste_tarihi (kaynağın ilan/liste günü) yeterli; yerel basında vefat/namaz/defin tarihi ya da
    # ham.tarih_kaynagi ile işaretlenmiş ilan günü (site sahibi kararı 08.10.2026)
    basin_ = k.get("kaynak_turu") in BASIN_TURLERI
    tarih_var = k.get("vefat_tarihi") or k.get("namaz_tarihi") or k.get("defin_zamani")
    if not tarih_var:
        if basin_:
            tarih_var = k.get("liste_tarihi") and (k.get("ham") or {}).get("tarih_kaynagi")
        else:
            tarih_var = k.get("liste_tarihi")
    if not ad or not k.get("kaynak_url") or not tarih_var:
        nedenler.append("K1 zorunlu alan eksik")
    # K2
    if ad and (not (2 <= len(ad.split()) <= 5) or AD_YASAK.search(ad)):
        nedenler.append("K2 ad biçimi")
    # K3
    ileri = bugun + timedelta(days=2)
    for a in TARIH_ALANLARI:
        v = k.get(a)
        if v is None:
            continue
        d = _gun(v)
        if a == "dogum_tarihi":
            if d is None or d > bugun:
                nedenler.append(f"K3 tarih geçersiz ({a})")
            continue
        if d is None:
            nedenler.append(f"K3 tarih geçersiz ({a})")
        elif d > ileri:
            nedenler.append(f"K3 tarih gelecekte ({a})")
    lt = _gun(k.get("liste_tarihi") or "")
    if lt is None or lt < bugun - timedelta(days=8) or lt > ileri:
        nedenler.append("K3 pencere dışı")
    # K4 / K5 / K8
    basin = k.get("kaynak_turu") in BASIN_TURLERI
    for a, v in _metinler(k):
        if a in ("kaynak_ad",):
            continue
        if TEL.search(v) or TC.search(v) or EPOSTA.search(v):
            nedenler.append(f"K4 telefon/TC/e-posta ({a})")
        if (ADRES_GUCLU if a in YER_ALANLARI else ADRES).search(v):
            nedenler.append(f"K4 adres ({a})")
        if NEDEN.search(v):
            nedenler.append(f"K5 ölüm nedeni ({a})")
        if basin:
            if len(v) > 60:
                nedenler.append(f"K8 uzun alan ({a})")
            if BASIN_CUMLE.search(v):
                nedenler.append(f"K8 site cümlesi ({a})")
    # K7
    u = urllib.parse.urlparse(k.get("kaynak_url") or "")
    if u.scheme not in ("http", "https") or not u.netloc:
        nedenler.append("K7 kaynak_url geçersiz")
    else:
        beklenen = YEREL_BASIN.get(k.get("kaynak_ad")) if basin else alan_adi_cogunluk.get(k.get("kaynak_ad"))
        if basin and not beklenen:
            nedenler.append("K7 yerel basın kaynağı kayıtlı değil")
        elif beklenen and (_www(u.netloc) != _www(beklenen) if basin else u.netloc.lower() != beklenen.lower()):
            nedenler.append("K7 alan adı farklı")
    return sorted(set(nedenler))


def il_denetle(il_klasor, bugun, kuru=False):
    yol = os.path.join(VERI, il_klasor, "son7gun.json")
    with open(yol, encoding="utf-8") as f:
        d = json.load(f)
    gruplar = [("ilceler", ilce, liste) for ilce, liste in d.get("ilceler", {}).items()] + \
              [("il_disi", None, d.get("il_disi", [])), ("ilce_belirsiz", None, d.get("ilce_belirsiz", []))]
    tum = [k for _, _, l in gruplar for k in l]
    alanlar = defaultdict(Counter)
    for k in tum:
        alanlar[k.get("kaynak_ad")][urllib.parse.urlparse(k.get("kaynak_url") or "").netloc.lower()] += 1
    cogunluk = {ka: c.most_common(1)[0][0] for ka, c in alanlar.items() if c}
    # K6 için sıra: resmî kaynaklar önce, yerel basın sonra
    # yerel haber kayıtlarında en çok alanı dolu olan önce (aynı kişinin iki sitedeki haberi: zengin olan kalır)
    sira = sorted(range(len(tum)), key=lambda i: (tum[i].get("kaynak_turu") in BASIN_TURLERI, tum[i].get("kaynak_turu") == "yerel_haber",
                                                  -sum(v is not None for v in tum[i].values()) if tum[i].get("kaynak_turu") == "yerel_haber" else 0, i))
    gorulen, red, elenen_id = set(), [], set()
    ad_gunleri = defaultdict(list)          # yerel haber: aynı ad ±3 gün içinde (vefat haberi ile defin haberi farklı günlerde çıkar)
    neden_say = Counter()
    for i in sira:
        k = tum[i]
        n = denetle(k, bugun, cogunluk)
        gun_ = k.get("liste_tarihi") or k.get("defin_zamani") or k.get("vefat_tarihi")
        anahtar = (ad_anahtar(k.get("ad_soyad")), gun_)
        if not n:
            yakin = False
            if k.get("kaynak_turu") == "yerel_haber" and _gun(gun_ or ""):
                yakin = any(abs((_gun(gun_) - g2).days) <= 3 for g2 in ad_gunleri[anahtar[0]])
            if anahtar in gorulen or yakin:
                n = ["K6 aynı kişi aynı gün tekrar"]
            else:
                gorulen.add(anahtar)
                if _gun(gun_ or ""):
                    ad_gunleri[anahtar[0]].append(_gun(gun_))
        if n:
            red.append({"kural": n, "kayit": k})
            elenen_id.add(id(k))
            for x in n:
                neden_say[x.split(" (")[0]] += 1
    if not kuru:
        d["ilceler"] = {ilce: [k for k in l if id(k) not in elenen_id] for _, ilce, l in gruplar if ilce}
        d["ilceler"] = {a: l for a, l in d["ilceler"].items() if l}
        d["il_disi"] = [k for k in d.get("il_disi", []) if id(k) not in elenen_id]
        d["ilce_belirsiz"] = [k for k in d.get("ilce_belirsiz", []) if id(k) not in elenen_id]
        d["toplam"] = len(tum) - len(red)
        d["kapi"] = {"denetim": ortak.simdi_iso(), "elenen": len(red)}
        ortak.json_yaz(yol, d)
        ortak.json_yaz(os.path.join(VERI, il_klasor, "_kapi_red.json"),
                       {"il": d.get("il"), "guncelleme": ortak.simdi_iso(), "elenen": len(red), "red": red})
    return {"il": d.get("il"), "kayit": len(tum), "gecen": len(tum) - len(red), "elenen": len(red),
            "nedenler": dict(neden_say.most_common())}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    kuru = "--kuru" in argv
    secili = [a for a in argv if not a.startswith("-")]
    bugun = date.today()
    iller = secili or sorted(a for a in os.listdir(VERI)
                             if os.path.isfile(os.path.join(VERI, a, "son7gun.json")) and not a.startswith("_"))
    ozet = {"guncelleme": ortak.simdi_iso(), "kuru": kuru, "iller": {}}
    toplam, toplam_red, genel = 0, 0, Counter()
    for il in iller:
        try:
            r = il_denetle(il, bugun, kuru)
        except Exception as e:
            ozet["iller"][il] = {"hata": f"{type(e).__name__}: {e}"}
            print(f"[kapı] {il}: HATA {e}", file=sys.stderr)
            continue
        ozet["iller"][il] = r
        toplam += r["kayit"]
        toplam_red += r["elenen"]
        genel.update(r["nedenler"])
        if r["elenen"]:
            print(f"[kapı] {il}: {r['elenen']}/{r['kayit']} elendi {r['nedenler']}")
    ozet.update(toplam_kayit=toplam, toplam_elenen=toplam_red, nedenler=dict(genel.most_common()))
    if not kuru:
        ortak.json_yaz(os.path.join(VERI, "kapi.json"), ozet)
        oy = os.path.join(VERI, "ozet.json")
        if os.path.exists(oy):
            try:
                with open(oy, encoding="utf-8") as f:
                    o = json.load(f)
                for il, r in ozet["iller"].items():
                    if il in o.get("iller", {}) and "gecen" in r:
                        o["iller"][il]["kayit_sayisi"] = r["gecen"]
                        o["iller"][il]["kapi_elenen"] = r["elenen"]
                ortak.json_yaz(oy, o)
            except Exception as e:
                print(f"[kapı] ozet.json güncellenemedi: {e}", file=sys.stderr)
    print(f"[kapı] {len(iller)} il, {toplam} kayıt, {toplam_red} elendi" + (" (kuru)" if kuru else ""))
    return ozet


if __name__ == "__main__":
    main()
