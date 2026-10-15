"""Ortak kayıt şeması ve JSON yazma yardımcıları (tüm il okuyucuları kullanır)."""
import hashlib, http.client, json, os, re, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from datetime import datetime, timedelta, timezone
import ortak_kopru

ALANLAR = ["id", "il", "ilce", "mahalle", "ad_soyad", "anne_baba", "yas", "dogum_tarihi",
           "vefat_tarihi", "defin_yeri", "defin_zamani", "namaz_tarihi", "namaz_yeri_vakti",
           "liste_tarihi", "kaynak_ad", "kaynak_url", "alindi", "ham",
           "il_disi_defin", "ilce_belirsiz"]

AYLAR = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6, "temmuz": 7,
         "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}


def tr_lower(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def tr_title(s):
    """'ÇAMAŞ' -> 'Çamaş', 'ESME-ŞÜKRÜ' -> 'Esme-Şükrü', 'SAMSUN / TERME' -> 'Samsun / Terme'."""
    def kelime(w):
        w = tr_lower(w)
        if not w:
            return w
        return {"i": "İ", "ı": "I"}.get(w[0], w[0].upper()) + w[1:]
    return " ".join("-".join(kelime(p) for p in w.split("-")) for w in (s or "").split())


def tarih_iso(s):
    """'4 Ekim 2026' veya '4.10.2026' -> '2026-10-04'; çözülemezse None."""
    if not s:
        return None
    s = s.strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        g, a, y = map(int, m.groups())
    else:
        m = re.match(r"^(\d{1,2})\s+(\S+)\s+(\d{4})$", s)
        if not m or tr_lower(m.group(2)) not in AYLAR:
            return None
        g, a, y = int(m.group(1)), AYLAR[tr_lower(m.group(2))], int(m.group(3))
    try:
        return datetime(y, a, g).strftime("%Y-%m-%d")
    except ValueError:
        return None


def kayit_id(kaynak, ad, tarih, ek=""):
    ham = "|".join([kaynak, tr_lower(ad), tarih, tr_lower(ek)])
    return hashlib.sha1(ham.encode("utf-8")).hexdigest()[:12]


def simdi_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def json_yaz(yol, nesne):
    os.makedirs(os.path.dirname(yol), exist_ok=True)
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(nesne, f, ensure_ascii=False, indent=1)


def eski_gunleri_sil(klasor, tutulacak_gunler):
    """klasördeki YYYY-AA-GG.json dosyalarından tutulacak listede olmayanları siler."""
    silinen = []
    if not os.path.isdir(klasor):
        return silinen
    for ad in os.listdir(klasor):
        m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", ad)
        if m and m.group(1) not in tutulacak_gunler:
            os.remove(os.path.join(klasor, ad))
            silinen.append(ad)
    return silinen


def son7gun_yaz(klasor, il, gunler, kayitlar_by_gun):
    """Özet yazar. Aynı id tekrarlarını eler. Çıktı anahtarları:
    ilceler (ilçe -> kayıtlar), il_disi (il dışı defin), ilce_belirsiz, toplam, guncelleme.
    İlçe alanı henüz işlenmemiş kayıtlar burada ilce_isle() ile işlenir (yerinde)."""
    ilceler, il_disi, belirsiz, goruldu = {}, [], [], set()
    # O gün okunamadıysa (ağ hatası -> okuyucu günü atlar) eski gün dosyası korunur ve son7gun'a girer
    # (08.10.2026 denetimi: Gaziantep'te 5 günün kaydı tek IncompleteRead ile son7gun'dan düşüyordu).
    kayitlar_by_gun = dict(kayitlar_by_gun)
    bugun_ = datetime.now(timezone.utc).astimezone().date()
    pencere = {(bugun_ - timedelta(days=i)).isoformat() for i in range(7)}
    dosya_gunleri = set()
    if os.path.isdir(klasor):
        dosya_gunleri = {m.group(1) for m in (re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.json", a) for a in os.listdir(klasor)) if m}
    gunler = sorted(set(gunler) | (dosya_gunleri & pencere), reverse=True)
    for g in gunler:
        if g not in kayitlar_by_gun and g in dosya_gunleri:
            try:
                with open(os.path.join(klasor, f"{g}.json"), encoding="utf-8") as f:
                    kayitlar_by_gun[g] = json.load(f).get("kayitlar", [])
            except Exception:
                pass
    # BEKLEME DEPOSU (14.10.2026 sahibi: "bilgi depoda beklesin, yarin sabah tarama yapinca bekleyenlerle birlikte listeye girsin"):
    # cenaze gunu BUGUNDEN SONRA olan kayit son7gun'a (yayina) GIRMEZ; <klasor>/_bekleyen.json'da bekler, gunu gelince listeye eklenir.
    # Kaynak sayfa kaydi ertesi gun listeden dusurse bile depodaki kopya korunur. _bekleyen.json yayina gitmez (yayin_suz yalniz son7gun.json birakir).
    bek_yol = os.path.join(klasor, "_bekleyen.json")
    def _cenaze_gunu(k):
        for t in (k.get("namaz_tarihi"), (k.get("defin_zamani") or "")[:10]):
            if t and re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
                return t
        return None
    bugun_s = bugun_.isoformat()
    bekleyen = {}
    try:
        with open(bek_yol, encoding="utf-8") as f:
            for k in json.load(f).get("kayitlar", []):
                bekleyen[k["id"]] = k
    except Exception:
        pass
    # 15.10.2026 (sahibi: "saat 7 oldu Ordu güncellenmedi" — kaynak listeyi henüz girmemişti): her kayda ILK GORULME damgasi;
    # onceki son7gun.json'daki damga korunur. Yayina gitmez (yayin_suz UYGULAMA_ALANLARI'na gore siler); depodaki veri/<il>/son7gun.json'da
    # durur -> hangi il/ilce listeyi gunun kacinda giriyor olculur (bildirim saati ve sabah tur sikligi buna gore ayarlanir; araclar/gorulme_saati.py).
    onceki_gorulme = {}
    try:
        with open(os.path.join(klasor, "son7gun.json"), encoding="utf-8") as f:
            _e = json.load(f)
        for _l in list((_e.get("ilceler") or {}).values()) + [_e.get("il_disi") or [], _e.get("ilce_belirsiz") or []]:
            for _k in _l:
                if _k.get("ilk_gorulme"):
                    onceki_gorulme[_k["id"]] = _k["ilk_gorulme"]
    except Exception:
        pass
    _simdi = simdi_iso()
    def yerlestir(k):
        if k["id"] in goruldu:
            return
        goruldu.add(k["id"])
        k["ilk_gorulme"] = onceki_gorulme.get(k["id"]) or k.get("ilk_gorulme") or _simdi
        ilce_isle(k, il)
        if k.get("il_disi_defin"):
            il_disi.append(k)
        elif k.get("ilce_belirsiz") or not k.get("ilce"):
            belirsiz.append(k)
        else:
            ilceler.setdefault(k["ilce"], []).append(k)
    try:   # ipucu 3: bu turun kayitlarindan mezarlik->ilce orani (tablo disi, ilcesi bilinen kayitlar)
        _tum = [ilce_isle_ham(k, il) for g in gunler for k in kayitlar_by_gun.get(g, [])]
        ogrenilen_hazirla(il, _tum)
    except Exception:
        pass
    for g in gunler:
        for k in kayitlar_by_gun.get(g, []):
            cg = _cenaze_gunu(k)
            if cg and cg > bugun_s:
                bekleyen[k["id"]] = k                   # gelecek tarihli: depoda beklet (yeni okuma eskisinin yerine gecer)
                continue
            bekleyen.pop(k["id"], None)                 # artik bugun/gecmis: depodaki kopya gereksiz
            yerlestir(k)
    kalan_bek = []
    for k in bekleyen.values():
        cg = _cenaze_gunu(k)
        if cg and cg > bugun_s:
            if (datetime.strptime(cg, "%Y-%m-%d").date() - bugun_).days <= 4:
                kalan_bek.append(k)                     # beklemeye devam
        else:
            yerlestir(k)                                # gunu geldi: bugunun listesine, yeni bilgilerle birlikte
    if kalan_bek or os.path.isfile(bek_yol):
        json_yaz(bek_yol, {"il": il, "kayitlar": kalan_bek, "guncelleme": simdi_iso()})
    ilceler = dict(sorted(ilceler.items(), key=lambda x: katla(x[0])))
    json_yaz(os.path.join(klasor, "son7gun.json"),
             {"il": il, "ilceler": ilceler, "il_disi": il_disi, "ilce_belirsiz": belirsiz,
              "toplam": len(goruldu), "guncelleme": simdi_iso()})


# ---------------------------------------------------------------- ilçe / il dışı defin
_ILCELER_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ilceler.json")
_ilce_onbellek = {}
YAZIM_DUZELT = {"tarabzon": "Trabzon", "trabzom": "Trabzon", "samsum": "Samsun"}  # bilinen yazım hataları


def katla(s):
    """Karşılaştırma anahtarı: küçük harf, Türkçe harfler sadeleşmiş, boşluk/noktalama tek."""
    s = tr_lower(s or "").strip()
    for a, b in zip("çğıöşü", "cgiosu"):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def ilce_verisi():
    if not _ilce_onbellek:
        with open(_ILCELER_YOLU, encoding="utf-8") as f:
            _ilce_onbellek.update(json.load(f))
    return _ilce_onbellek


def ilce_listesi(il):
    return ilce_verisi().get(il, [])


def _ad_bul(katli, liste):
    for x in liste:
        if katla(x) == katli:
            return x
    return None


def ilce_coz(il, ham):
    """Kaynağın ilçe değerini çözer. Dönen sözlük:
    {"ilce": str|None, "ilce_belirsiz": bool, "il_disi_defin": {"il","ilce"}|None}
    Kurallar: '<il> / <ilçe>' ve başka il -> il_disi; il adı tek başına (kendi ili) -> belirsiz;
    başka ilin bilinen ilçesi tek başına -> o ilin il_disi'si; kendi il listesinde yoksa -> belirsiz."""
    v = ilce_verisi()
    ham = " ".join((ham or "").split())
    sonuc = {"ilce": None, "ilce_belirsiz": True, "il_disi_defin": None}
    if not ham:
        return sonuc
    iller = v["_iller"]
    kendi = ilce_listesi(il)
    bilinen_dis = {katla(a): b for a, b in v["_il_disi_bilinen"].items()}
    if "/" in ham:
        parcalar = [p.strip() for p in ham.split("/") if p.strip()]
        if not parcalar:
            return sonuc
        ilk = parcalar[0]
        ilk_k = katla(ilk)
        ilk_duz = YAZIM_DUZELT.get(ilk_k.replace(" ", ""), None) or YAZIM_DUZELT.get(ilk_k)
        il_adi = ilk_duz or _ad_bul(ilk_k, iller)
        if il_adi and katla(il_adi) != katla(il):
            ikinci = tr_title(parcalar[1]) if len(parcalar) > 1 else None
            sonuc["il_disi_defin"] = {"il": il_adi, "ilce": ikinci or None}
            sonuc["ilce_belirsiz"] = False
            return sonuc
        son_il = None
        if not il_adi and len(parcalar) > 1:   # ters sıra: '<ilçe> / <il>' (ör. 'Nurdağı/gaziantep')
            sk = katla(parcalar[-1])
            son_il = YAZIM_DUZELT.get(sk.replace(" ", "")) or _ad_bul(sk, iller)
        if son_il:
            if katla(son_il) != katla(il):
                a = tr_title(parcalar[0])
                sonuc["il_disi_defin"] = {"il": son_il, "ilce": None if "mezarl" in katla(a) else a}
                sonuc["ilce_belirsiz"] = False
                return sonuc
            ham = parcalar[0]
        elif il_adi and len(parcalar) > 1:      # '<kendi il> / <ilçe>'
            ham = parcalar[1]
        else:
            ham = parcalar[0]                  # '<ilçe> / <mahalle>' gibi
    k = katla(ham)
    ad = _ad_bul(k, kendi)
    if ad:
        sonuc.update(ilce=ad, ilce_belirsiz=False)
        return sonuc
    if k in bilinen_dis:
        sonuc.update(ilce_belirsiz=False, il_disi_defin={"il": bilinen_dis[k], "ilce": tr_title(ham)})
        return sonuc
    il_adi = YAZIM_DUZELT.get(k.replace(" ", "")) or _ad_bul(k, iller)
    if il_adi and katla(il_adi) != katla(il):
        sonuc.update(ilce_belirsiz=False, il_disi_defin={"il": il_adi, "ilce": None})
        return sonuc
    return sonuc   # kendi il adı ya da listede olmayan değer -> ilce None, belirsiz


# ---- MEZARLIK -> ILCE TABLOSU (14.10.2026 sahibi: "ilce en basit bilgi, verilmeli"; YURUT.md H37)
# Kaynak: OpenStreetMap (ODbL) + resmi acik listeler; mezarlik_ilce.json = {"il_slug": {"normalize_ad": "Ilce" | {"belirsiz": [ilceler]}},
# "_mahalle": {il_slug: {ad: ilce}}, "_cami": {il_slug: {ad: ilce}}}. Ad YALNIZ kaydin kendi ilinin altinda aranir. Tablo yok/bozuksa sessizce atlanir.
_MEZ_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mezarlik_ilce.json")
_mez_onbellek = {}
_OGRENILEN = {}     # il_slug -> {mezarlik_norm: {ilce: sayi}} (son7gun_yaz her turda doldurur)
_MEZ_EK = {"mezarligi", "mezarlik", "mezarliginda", "mezarlikta", "mezarlari", "kabristanligi", "kabristani", "kabristanliginda",
           "mezari", "mez", "mzl", "kabristan"}
_MEZ_KES = {"pafta", "parsel", "ada", "kapisi", "kapi", "sira", "sistem", "sistemi", "bolum", "kisim", "blok", "no", "sokak", "cadde", "yol"}


def il_slug(il):
    return katla(il).replace(" ", "")


def mezarlik_tablosu():
    if not _mez_onbellek:
        try:
            with open(_MEZ_YOLU, encoding="utf-8") as f:
                _mez_onbellek.update(json.load(f))
        except Exception:
            _mez_onbellek["_yok"] = True
    return _mez_onbellek


def mezarlik_norm(ad):
    """Mezarlik adi anahtari: katla + 'mezarligi/kabristanligi' gibi ekleri at; 'pafta/ada/kapi', '/' ya da rakamdan sonrasini kes."""
    s = (ad or "").split("/")[0]
    toks = []
    for t in katla(s).split():
        if t in _MEZ_KES or any(c.isdigit() for c in t):
            break
        toks.append(t)
    return " ".join(t for t in toks if t not in _MEZ_EK)


def _tablo_ara(bolum, il, ad):
    """bolum: {il_slug: {norm: ilce|{'belirsiz': [...]}}} icinden il icinde arar -> str | list | None."""
    if not ad:
        return None
    t = mezarlik_tablosu()
    d = (t.get(bolum, {}) if bolum.startswith("_") else t).get(il_slug(il)) or {}
    n = mezarlik_norm(ad) if bolum == "mezarlik" else katla(ad)
    v = d.get(n)
    if isinstance(v, dict):
        return list(v.get("belirsiz") or []) or None
    return v


def mezarlik_ilce_bul(il, defin_yeri):
    """-> ('ilce', ad) | ('belirsiz', [adaylar]) | None. Yalniz o ilin ilcelerine esleme; ad listede degilse yok sayilir."""
    n = mezarlik_norm(defin_yeri)
    if not n:
        return None
    d = mezarlik_tablosu().get(il_slug(il)) or {}
    v = d.get(n)
    if v is None:
        return None
    gecerli = gecerli_ilceler(il)
    if isinstance(v, str):
        return ("ilce", v) if v in gecerli else None
    if any(x not in gecerli for x in (v.get("belirsiz") or [])):
        return None            # H61: adaylardan biri gecerli ilce degil (orn. 'Merkez' listede yok) -> kalani secmek tahmin olur
    adaylar = [x for x in (v.get("belirsiz") or []) if x in gecerli]
    return ("belirsiz", adaylar) if len(adaylar) > 1 else (("ilce", adaylar[0]) if adaylar else None)


def _ipucu_isle(kayit, il):
    """ilce yok + il disi degil + defin_yeri tabloda -> ilce ata (tek eslesme) ya da siralı ipuclariyla coz:
    (1) mahalle (2) cami/namaz yeri (3) ayni ilde ogrenilen oran (baskin >=%80, en az 3 kayit). Hicbiri cozmezse ilcesiz kalir (tahmin yok)."""
    if kayit.get("ilce") or kayit.get("il_disi_defin") or not kayit.get("ilce_belirsiz", True):
        return kayit
    try:
        r = mezarlik_ilce_bul(il, kayit.get("defin_yeri"))
        if not r:
            return kayit
        ilce, kaynak = None, "mezarlik_tablosu"
        if r[0] == "ilce":
            ilce = r[1]
        else:
            adaylar = r[1]
            m = _tablo_ara("_mahalle", il, kayit.get("mahalle"))
            if isinstance(m, str) and m in adaylar:
                ilce, kaynak = m, "mezarlik_tablosu+mahalle"
            if not ilce:
                c = _tablo_ara("_cami", il, kayit.get("namaz_yeri_vakti"))
                if isinstance(c, str) and c in adaylar:
                    ilce, kaynak = c, "mezarlik_tablosu+cami"
            if not ilce:
                o = (_OGRENILEN.get(il_slug(il)) or {}).get(mezarlik_norm(kayit.get("defin_yeri"))) or {}
                o = {i: n for i, n in o.items() if i in adaylar}
                top = sum(o.values())
                if top >= 3:
                    i, n = max(o.items(), key=lambda x: x[1])
                    if n / top >= 0.8:
                        ilce, kaynak = i, "mezarlik_tablosu+ogrenilen"
        if ilce:
            kayit["ilce"] = ilce
            kayit["ilce_belirsiz"] = False
            kayit["ilce_kaynagi"] = kaynak
            if isinstance(kayit.get("ham"), dict):
                kayit["ham"]["ilce_kaynagi"] = kaynak
    except Exception:
        pass            # tablo/ipucu hatasi mevcut davranisi bozmaz
    return kayit


# ---- H61 (15.10.2026) EK KATMANLAR: ilce adi metinde / mahalle-koy tablosu / ad sifati. Hepsi YALNIZ kesin eslesmede ilce yazar,
# yalniz kaydin KENDI ilinin ilceleri icinde; tahmin yok. Etiketler ham.ilce_kaynagi: ilce_adi_metinde | mahalle_tablo | ad_sifati.
_MAH_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mahalle_ilce.json")
_mah_onbellek = {}
_MAH_EK = {"mah", "mahallesi", "mahalle", "mh", "mahalles", "koy", "koyu", "koyunde", "koyunun", "koyundeki", "mevkii", "mevki", "beldesi", "belde"}
_STOP = {"mezarligi", "mezarlik", "mez", "mzl", "kabristan", "kabristanligi", "cami", "camii", "camisi", "camiinde", "mescidi", "mescit",
         "mah", "mahallesi", "mh", "koy", "koyu", "koyunde", "merkez", "yeni", "eski", "asri", "aile", "sehir", "sehitligi"}
# ilce adi gunluk sozcukle ayni (ya da kisi/tarihi adla ortak) -> yalniz ilce adi + (ilcesi|belediyesi|mezarligi|cami eki) disinda baska sozcuk yoksa
_GENEL_ILCE = {"guney", "kale", "bozkurt", "cardak", "merkez", "maden", "bahce", "gonen", "sultan", "kemer", "cay", "ova", "yildirim",
               "orhangazi", "osmangazi", "gazi", "ulas", "yenice"}
_STOP_MEZ = {"mezarligi", "mezarlik", "mez", "mzl", "kabristan", "kabristanligi"}   # cami sozcugu BILEREK yok: 'Orhangazi Camii' Bursa'da Osmangazi'dedir
_IZINLI_REST = _STOP_MEZ | {"merkez", "yeni", "eski", "kent", "belediyesi", "ilcesi", "ilce", "cem", "evi", "cemevi", "cami", "camii", "camisi", "sehir", "sehitlik", "sehitligi", "asri"}
_ILCE_DEMIR = {"ilcesinden", "ilcesine", "ilcesindeki", "nakil", "otobus", "kilitlenmis"}


# Ad sifati ("Keskinli Enver ...") kaynakta KISININ MEMLEKETIDIR, cenaze yeri degil: Kirikkale'de "Keskinli X" ilanlarinin camileri
# Kirikkale merkezindedir (Yunus Emre, Etiler Ulu, Nokta Camii...). Bu yuzden varsayilan KAPALI (kesin eslesme ilkesi); yalniz sahibi acarsa True.
AD_SIFATI_ACIK = False
_GENEL_DEFIN = {"koy", "koyu", "mezarlik", "mezarligi", "mez", "mzl", "koy mezarligi", "mahalle", "mah", "belde", "yeni", "eski", "asri"}


# Tablolar (OSM) 'Merkez' ilcesini de biliyor; ama ilceler.json'da Merkez yok (yalniz Batman, Giresun) ve kaynaklar 'Merkez'i kendileri
# yazmadikca uygulama Merkez gostermez. True yapilirsa tablolardan gelen 'Merkez' de yazilir (H61: ~110 kayit daha). SAHIBI KARARI bekliyor.
MERKEZ_ETKIN = False


def gecerli_ilceler(il):
    g = set(ilce_listesi(il))
    if MERKEZ_ETKIN:
        g.add("Merkez")
    return g


def mahalle_tablosu():
    if not _mah_onbellek:
        try:
            with open(_MAH_YOLU, encoding="utf-8") as f:
                _mah_onbellek.update(json.load(f))
        except Exception:
            _mah_onbellek["_yok"] = True
    return _mah_onbellek


def mahalle_norm(ad):
    """Mahalle/koy anahtari: katla, 'mah/mahallesi/koy/koyu' eklerini at; '(', '-', ',' sonrasini at."""
    s = re.split(r"[(,\-]", ad or "")[0]
    return " ".join(t for t in katla(s).split() if t not in _MAH_EK)


def _alt_dizi(tk, it):
    n = len(it)
    return [i for i in range(len(tk) - n + 1) if tk[i:i + n] == it]


def ilce_adi_metinde(il, metin):
    """metin (mezarlik/cami/defin yeri) o ilin TEK bir ilce adini tam sozcuk olarak iceriyorsa onu doner, aksi hâlde None.
    Atlanir: baska il adi gecen metin, 'nakil/otobus/ilcesinden'; genel sozcuk olan ilce adlari (Merkez, Maden, Kale...) yalniz
    baska anlamli sozcuk eslik etmiyorsa ('Maden Mezarligi', 'Maden Ilcesi')."""
    tk = katla(metin).split()
    if not tk or _ILCE_DEMIR & set(tk):
        return None
    liste = ilce_listesi(il)
    bulunan = {}
    for x in liste:
        it = katla(x).split()
        if it == ["merkez"]:
            continue                      # 'Merkez Mezarligi' baska ilcenin merkez mezarligi de olabilir: metinden Merkez cikarilmaz
        for i in _alt_dizi(tk, it):
            bulunan.setdefault(x, []).append((i, i + len(it)))
    if len(bulunan) != 1:
        return None
    ad, yerler = next(iter(bulunan.items()))
    # baska ilin adi (ilce adinin parcasi degilse) -> metin baska yeri anlatiyor olabilir
    kapsanan = {j for (a, b) in yerler for j in range(a, b)}
    for ilk in ilce_verisi()["_iller"]:
        if katla(ilk) == katla(il):
            continue
        for i in _alt_dizi(tk, katla(ilk).split()):
            if i not in kapsanan:
                return None
    il_tk = set(katla(il).split())
    if katla(ad) in _GENEL_ILCE:
        kalan = [t for j, t in enumerate(tk) if j not in kapsanan and t not in _STOP_MEZ and t not in il_tk and t not in ("ilcesi", "belediyesi", "ilce", "merkez")]
        if kalan:
            return None
    # KABUL BICIMLERI (15.10.2026 'Harran Aile Mezarligi' dersi: Sanliurfa SEHIR mezarligi, Harran ilcesinde degil; ilce adi yon/yol adi olabilir):
    # (a) ilce adindan baska yalniz mezarlik/cami/merkez/belediye/ilce/il adi sozcukleri ('Gebze Mezarligi', 'Usak Ulubey Ilcesi')
    # (b) ilce adi, 'Koyu/Koyunde/Mah./Belde' isaretcisinden ONCE ('Banaz Alaba Koyu', 'Kibriscik Kizilcaoren Koyunde')
    # (c) ilce adinin hemen ardindan mezarlik sozcugu ('Uzumlu Mezarligina')
    rest = [t for j, t in enumerate(tk) if j not in kapsanan]
    ilk, son = min(a for a, b in yerler), max(b for a, b in yerler)
    a_ok = all(t in _IZINLI_REST or t in il_tk for t in rest)
    b_ok = any(t in _KOY_ISARET for t in tk[son:]) or "belde" in tk[son:]
    c_ok = son < len(tk) and (tk[son] in _STOP_MEZ or tk[son] in ("mezarligina", "mezarliginda", "mezarligindan"))
    if not (a_ok or b_ok or c_ok):
        return None
    return ad


_YER_EK = {"mezarligi", "mezarlik", "mez", "mzl", "kabristan", "kabristanligi", "cami", "camii", "camisi", "camiinde", "mescidi", "mescit", "cemevi"}
_YER_SIFAT = {"merkez", "yeni", "eski", "asri", "istasyon", "aile", "park", "sehir", "belediye"}   # 'Halidere Merkez Mezarligi' -> halidere


def yer_anahtarlari(ad):
    """Mezarlik/cami/mahalle metninden yerlesim adi adaylari: tam ad ve (sonda yalniz 'merkez/yeni/kent...' sifati varsa) bas kisim."""
    tk = [t for t in mahalle_norm(ad).split() if t not in _YER_EK]
    out = []
    if tk:
        out.append(" ".join(tk))
        h = list(tk)
        while len(h) > 1 and h[-1] in _YER_SIFAT:
            h.pop()
            out.append(" ".join(h))
    return out


_KOY_ISARET = {"koyu", "koyunde", "koyunun", "koyundeki", "koyune", "koyunden", "koy", "mah", "mahallesi", "mahallesinde", "mahallesindeki", "mh", "mahalle"}


def koy_adaylari(metin):
    """Serbest metinden ('Kibriscik Kizilcaoren Koyunde kilinacak...', 'Akbelen Koyu - Ikindi') 'X Koyu/Mahallesi' oncesindeki 1-3 sozcuk:
    en uzundan kisaya anahtar listesi. Tek tek sozcuk degil, YER ISARETCISIYLE biten kume aranir."""
    tk = katla(metin).split()
    out = []
    for i, t in enumerate(tk):
        if t in _KOY_ISARET and i > 0:
            for n in (3, 2, 1):
                if i - n >= 0:
                    a = [x for x in tk[i - n:i] if x not in _KOY_ISARET]
                    if len(a) == n:
                        out.append(" ".join(a))
    return out


# Kent mahalleleri (OSM suburb/neighbourhood) icin '_kent' bolumu: OSM'de eksik -> canli veride yalniz ~%66 uyum (15.10.2026) -> VARSAYILAN KAPALI.
KENT_MAHALLE_ETKIN = False


def _mahalle_ilce(il, ad):
    """-> ilce | None. mahalle_ilce.json = {il_slug: {mahalle_norm: ilce}} (koy/mezra); '_kent' yalniz KENT_MAHALLE_ETKIN iken.
    Ayni ad birden cok ilcedeyse tabloya hic girmez."""
    t = dict(mahalle_tablosu().get(il_slug(il)) or {})
    if KENT_MAHALLE_ETKIN:
        for k, v in ((mahalle_tablosu().get("_kent") or {}).get(il_slug(il)) or {}).items():
            t.setdefault(k, v)
    gecerli = gecerli_ilceler(il)
    for n in yer_anahtarlari(ad) + koy_adaylari(ad):
        v = t.get(n)
        if isinstance(v, str) and v in gecerli:
            return v
    return None


def _ad_sifati_ilce(il, ad_soyad):
    """'Keskinli Enver Yildizli' -> Keskin (ilce adi + li/lu eki, ad_soyad'in ILK sozcugu, ilcenin kendi ilinin listesinde). Ad DEGISTIRILMEZ."""
    tk = katla(ad_soyad).split()
    if len(tk) < 2:
        return None
    ilk, adaylar = tk[0], []
    for x in ilce_listesi(il):
        k = katla(x)
        if " " in k or katla(x) in _GENEL_ILCE:
            continue
        for ek in ("li", "lu"):
            if ilk == k + ek:
                adaylar.append(x)
    # unlu uyumu: son unlu e/i -> li, a/ı -> li degil lı ... katla() ı->i yaptigindan 'li' ve 'lu' (u/ü->u) kapsar
    return adaylar[0] if len(adaylar) == 1 else None


def namaz_parcalari(ny):
    """'Ogle - Halidere Merkez Cami' / 'Karsiyaka Merkez Camii - Ikindi Namazi' -> parcalar (en cok 3)."""
    return [p.strip() for p in re.split(r"\s[-\u2013]\s|\sMüteakiben\s", ny or "") if p.strip()][:3]


def _ek_katmanlar(kayit, il):
    """ilce yok + il disi degil -> sirayla: ilce adi metinde (defin_yeri, namaz_yeri_vakti) -> mahalle/koy tablosu (mahalle, defin_yeri, namaz yeri)
    -> ad sifati. Ilk KESIN sonuc yazilir; hicbiri yoksa dokunmaz."""
    if kayit.get("ilce") or kayit.get("il_disi_defin") or not kayit.get("ilce_belirsiz", True):
        return kayit
    try:
        ilce, kaynak = None, None
        dy = kayit.get("defin_yeri")
        ilce = ilce_adi_metinde(il, dy)
        if not ilce:
            # mahalle alani 'Beycuma Saraycik Koyu' gibi '<ilce> <yerlesim> <Koyu|Mah.>' biciminde ise (ilce adi BASTA, arada en az bir sozcuk)
            mh = katla(kayit.get("mahalle")).split()
            if len(mh) >= 3 and (set(mh) & _KOY_ISARET) and mh[-1] in _KOY_ISARET:
                ilce = ilce_adi_metinde(il, kayit.get("mahalle"))
                if ilce and katla(kayit.get("mahalle")).split()[:len(katla(ilce).split())] != katla(ilce).split():
                    ilce = None
        namaz_serbest = not dy or all(t in _GENEL_DEFIN for t in katla(dy).split()) or "koy" in katla(dy).split()
        if not ilce and namaz_serbest:
            # namaz yeri metni: defin yeri bos/genel (Koy Mezarligi) ise guvenilir; belirli ama tabloda olmayan bir mezarlik varsa
            # ('Yukari Tekke - 90. Ada' + 'Ulas Merkez Cami') namaz ilcesi gomme ilcesi OLMAYABILIR -> baglanmaz
            ilce = ilce_adi_metinde(il, kayit.get("namaz_yeri_vakti"))
        if ilce:
            kaynak = "ilce_adi_metinde"
        if not ilce:
            adaylar = [kayit.get("mahalle"), dy]
            if namaz_serbest:        # cami: defin yeri bos/genel ise (ayni kapi: belirli bir mezarlik varsa cami ilcesi gomme ilcesi olmayabilir)
                adaylar += namaz_parcalari(kayit.get("namaz_yeri_vakti"))
            for a in adaylar:
                ilce = _mahalle_ilce(il, a)
                if ilce:
                    kaynak = "mahalle_tablo"
                    break
        if not ilce and AD_SIFATI_ACIK:
            ilce = _ad_sifati_ilce(il, kayit.get("ad_soyad"))
            kaynak = "ad_sifati" if ilce else None
        if ilce:
            kayit["ilce"], kayit["ilce_belirsiz"], kayit["ilce_kaynagi"] = ilce, False, kaynak
            if isinstance(kayit.get("ham"), dict):
                kayit["ham"]["ilce_kaynagi"] = kaynak
    except Exception:
        pass
    return kayit


def _defin_il_disi(kayit, il):
    """defin_yeri BASKA bir ilin adiysa (Kilis, Diyarbakir...) ya da '<Il> / <ilce>' bicimindeyse kayit il disina alinir
    (mevcut kural: 'baska il -> il_disi'; okuyucunun ilce_belirsiz on dolduruşu ya da kaynagin 'Merkez'i bunu bastirmaz). 14.10.2026."""
    if kayit.get("il_disi_defin"):
        return kayit
    y = " ".join((kayit.get("defin_yeri") or "").split())
    if not y:
        return kayit
    try:
        iller = ilce_verisi()["_iller"]
        if "/" in y:
            ilk = katla(y.split("/")[0])
            adaylar = [_ad_bul(ilk, iller), _ad_bul(katla(y.split("/")[-1]), iller)]
        else:
            adaylar = [_ad_bul(katla(y), iller)]
        if not any(a and katla(a) != katla(il) for a in adaylar):
            return kayit
        r = ilce_coz(il, y)
        if r.get("il_disi_defin"):
            kayit["il_disi_defin"] = r["il_disi_defin"]
            kayit["ilce"] = None
            kayit["ilce_belirsiz"] = False
            if isinstance(kayit.get("ham"), dict):
                kayit["ham"]["il_disi_kaynagi"] = "defin_yeri"
    except Exception:
        pass
    return kayit


def ilce_isle(kayit, il):
    """Kaydın 'ilce' alanını ilce_coz ile işler (yerinde). Zaten işlenmişse dokunmaz (yalnız ilçesiz kayıt için mezarlık tablosu yeniden denenir).
    Ham değer kayıt['ham']['ilce_ham'] altında korunur (ham dict varsa ve anahtar yoksa)."""
    if "il_disi_defin" in kayit and "ilce_belirsiz" in kayit:
        return _ek_katmanlar(_ipucu_isle(_defin_il_disi(kayit, il), il), il)
    ham_ilce = kayit.get("ilce")
    r = ilce_coz(il, ham_ilce)
    if isinstance(kayit.get("ham"), dict) and ham_ilce and "ilce_ham" not in kayit["ham"] and "ilce" not in kayit["ham"]:
        kayit["ham"]["ilce_ham"] = ham_ilce
    kayit["ilce"] = r["ilce"]
    kayit["ilce_belirsiz"] = r["ilce_belirsiz"]
    kayit["il_disi_defin"] = r["il_disi_defin"]
    return _ek_katmanlar(_ipucu_isle(_defin_il_disi(kayit, il), il), il)


def ilce_isle_ham(kayit, il):
    """Yalniz ogrenme icin: ilce_coz sonucunu (tablo ipucusuz) kayda yazmadan okur; ilcesi bilinen kayit ise kendisini doner."""
    if "il_disi_defin" in kayit and "ilce_belirsiz" in kayit:
        return kayit
    r = ilce_coz(il, kayit.get("ilce"))
    return {"ilce": r["ilce"], "il_disi_defin": r["il_disi_defin"], "defin_yeri": kayit.get("defin_yeri")}


def ogrenilen_hazirla(il, kayitlar):
    """Ayni ilde ilcesi ZATEN bilinen kayitlardan (tablo disi kaynaklar) mezarlik -> ilce sayimi (ipucu 3)."""
    d = {}
    for k in kayitlar:
        if k.get("ilce") and not k.get("il_disi_defin") and not k.get("ilce_kaynagi") and k.get("defin_yeri"):
            n = mezarlik_norm(k["defin_yeri"])
            if n:
                d.setdefault(n, {}).setdefault(k["ilce"], 0)
                d[n][k["ilce"]] += 1
    _OGRENILEN[il_slug(il)] = d


def gun_yaz(klasor, il, gun, kayitlar):
    """Gün dosyasını yazar (kayıtlara ilce_isle uygulanır)."""
    for k in kayitlar:
        ilce_isle(k, il)
    json_yaz(os.path.join(klasor, f"{gun}.json"), {"il": il, "liste_tarihi": gun, "kayitlar": kayitlar})


# ---------------------------------------------------------------- ağ: User-Agent, robots.txt, bekleme
UA = "KiminCenazesiBot/0.1 (+kimincenazesi)"
_son_istek = {}


def indir(url, bekle=3.5, veri=None, timeout=40, ssl_baglam=None, basliklar=None):
    """GET (veri verilirse POST). Aynı alan adına yapılan istekler arasında en az 'bekle' sn.
    ssl_baglam: isteğe bağlı ssl.SSLContext (doğrulama AÇIK kalır; yalnız eksik ara sertifikayı eklemek için).
    basliklar: isteğe bağlı ek HTTP başlıkları (ör. JSON POST için Content-Type)."""
    hizli = os.environ.get("CENAZE_HIZLI") == "1"   # CI: yanıtsız sitede uzun beklemeyi kes
    if hizli:
        timeout = min(timeout, 15)
    host = urllib.parse.urlparse(url).netloc
    gecen = time.time() - _son_istek.get(host, 0)
    if gecen < bekle:
        time.sleep(bekle - gecen)
    hedef, ek = ortak_kopru.kopru_url(url)           # yalnız CENAZE_KOPRU tanımlıysa (GitHub) ve izinli alan adıysa köprü
    istek = urllib.request.Request(hedef, data=veri, headers={"User-Agent": UA, **(basliklar or {}), **ek})
    # geçici kopmalarda en çok 3 deneme, 5 sn arayla. CI (hızlı): zaman aşımında tekrar YOK (bekleme uzamasın), ama
    # yarım gelen yanıtta (IncompleteRead / bağlantı sıfırlandı) bir kez daha denenir (08.10.2026 denetimi: 7 il/ilçe bundan düştü)
    son_deneme = 2
    for deneme in range(3):
        try:
            with urllib.request.urlopen(istek, timeout=timeout, context=ssl_baglam) as r:
                ham = r.read()
                ctype = r.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError:
            raise
        except Exception as e:
            if hizli:
                son_deneme = 1 if isinstance(e, (http.client.IncompleteRead, ConnectionResetError)) else 0
            if deneme >= son_deneme:
                raise
            time.sleep(2 if hizli else 5)
        finally:
            _son_istek[host] = time.time()
    m = re.search(r"charset=([\w-]+)", ctype)
    return ham.decode(m.group(1) if m else "utf-8", "replace")


def robots_kural(govde, ua, yol):
    """RFC 9309 / Google biçimi: boş satırlar yok sayılır, UA grupları birleşir, en UZUN eşleşen kural kazanır (eşitlikte Allow).
    Python RobotFileParser iki durumda yanılıyor: 'User-agent: *' sonrası boş satır (kayıt düşer -> her şey serbest) ve 'Allow: /'
    satırının 'Disallow: /api/'dan önce gelmesi (ilk eşleşme kazanır -> her şey serbest). 13.10.2026: Merzifon ve Erenler bu yüzden yanlış serbest çıkıyordu."""
    ua = (ua or "").split("/")[0].lower()
    gruplar, simdiki, kurallar_basladi = [], None, False
    for ham in govde.splitlines():
        satir = ham.split("#", 1)[0].strip()
        if ":" not in satir:
            continue
        ad, deger = [x.strip() for x in satir.split(":", 1)]
        ad = ad.lower()
        if ad == "user-agent":
            if simdiki is None or kurallar_basladi:
                simdiki, kurallar_basladi = ([], []), False
                gruplar.append(simdiki)
            simdiki[0].append(deger.lower())
        elif ad in ("allow", "disallow") and simdiki is not None:
            kurallar_basladi = True
            if deger:
                simdiki[1].append((ad == "allow", deger))
    ozel = [g for g in gruplar if any(u != "*" and u in ua for u in g[0])]
    secili = ozel or [g for g in gruplar if "*" in g[0]]
    en_iyi = (-1, True)
    for _, kurallar in secili:
        for izin, desen in kurallar:
            rx = re.escape(desen).replace(r"\*", ".*")
            if rx.endswith(r"\$"):
                rx = rx[:-2] + "$"
            if re.match(rx, yol) and (len(desen), izin) > (en_iyi[0], en_iyi[1] if len(desen) == en_iyi[0] else False):
                en_iyi = (len(desen), izin)
    return en_iyi[1]


def robots_izin(url, ssl_baglam=None):
    """robots.txt bu UA için url'yi yasaklıyorsa False. robots.txt yoksa/404/HTML dönerse (kural yok) True."""
    p = urllib.parse.urlparse(url)
    try:
        govde = indir(f"{p.scheme}://{p.netloc}/robots.txt", bekle=3.0, timeout=30, ssl_baglam=ssl_baglam)
    except Exception:
        return True
    if "<html" in govde[:600].lower() or "user-agent" not in govde.lower():
        return True
    return robots_kural(govde, UA, p.path or "/" + (("?" + p.query) if p.query else ""))


# ---------------------------------------------------------------- yalnız güncel liste veren siteler
def liste_birikim(klasor, il, bugun, yeni_kayitlar, gun_sayisi=7):
    """Tarih parametresi olmayan (yalnız o günkü listeyi veren) kaynaklar için.
    Bugünkü kayıtlar, önceki günlerin dosyalarındaki id'lerde yoksa bugün dosyasına eklenir
    (liste_tarihi = ilk görüldüğü gün). Önceki gün dosyaları okunup son 'gun_sayisi' gün döndürülür.
    Dönen: (gunler [yeni->eski], {gun: [kayıt]}). Çağıran sonra gun_yaz / son7gun_yaz yapar."""
    bugun_d = datetime.strptime(bugun, "%Y-%m-%d").date()
    gunler = [(bugun_d - timedelta(days=i)).isoformat() for i in range(gun_sayisi)]
    by_gun, gorulen = {}, set()
    for g in reversed(gunler):                       # eskiden yeniye
        yol = os.path.join(klasor, f"{g}.json")
        liste = []
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                liste = json.load(f).get("kayitlar", [])
        by_gun[g] = [k for k in liste if k["id"] not in gorulen]
        gorulen.update(k["id"] for k in by_gun[g])
    mevcut = {k["id"] for k in by_gun[bugun]}
    for k in yeni_kayitlar:
        if k["id"] not in gorulen and k["id"] not in mevcut:
            k["liste_tarihi"] = bugun
            by_gun[bugun].append(k)
            mevcut.add(k["id"])
    return gunler, by_gun
