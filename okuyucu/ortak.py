"""Ortak kayıt şeması ve JSON yazma yardımcıları (tüm il okuyucuları kullanır)."""
import hashlib, json, os, re, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from datetime import datetime, timedelta, timezone

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
    for g in gunler:
        for k in kayitlar_by_gun.get(g, []):
            if k["id"] in goruldu:
                continue
            goruldu.add(k["id"])
            ilce_isle(k, il)
            if k.get("il_disi_defin"):
                il_disi.append(k)
            elif k.get("ilce_belirsiz") or not k.get("ilce"):
                belirsiz.append(k)
            else:
                ilceler.setdefault(k["ilce"], []).append(k)
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


def ilce_isle(kayit, il):
    """Kaydın 'ilce' alanını ilce_coz ile işler (yerinde). Zaten işlenmişse dokunmaz.
    Ham değer kayıt['ham']['ilce_ham'] altında korunur (ham dict varsa ve anahtar yoksa)."""
    if "il_disi_defin" in kayit and "ilce_belirsiz" in kayit:
        return kayit
    ham_ilce = kayit.get("ilce")
    r = ilce_coz(il, ham_ilce)
    if isinstance(kayit.get("ham"), dict) and ham_ilce and "ilce_ham" not in kayit["ham"] and "ilce" not in kayit["ham"]:
        kayit["ham"]["ilce_ham"] = ham_ilce
    kayit["ilce"] = r["ilce"]
    kayit["ilce_belirsiz"] = r["ilce_belirsiz"]
    kayit["il_disi_defin"] = r["il_disi_defin"]
    return kayit


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
    istek = urllib.request.Request(url, data=veri, headers={"User-Agent": UA, **(basliklar or {})})
    for deneme in range(1 if hizli else 3):          # geçici kopmalarda (IncompleteRead, zaman aşımı) en çok 3 deneme, 5 sn arayla
        try:
            with urllib.request.urlopen(istek, timeout=timeout, context=ssl_baglam) as r:
                ham = r.read()
                ctype = r.headers.get("Content-Type", "")
            break
        except urllib.error.HTTPError:
            raise
        except Exception:
            if deneme == (0 if hizli else 2):
                raise
            time.sleep(5)
        finally:
            _son_istek[host] = time.time()
    m = re.search(r"charset=([\w-]+)", ctype)
    return ham.decode(m.group(1) if m else "utf-8", "replace")


def robots_izin(url, ssl_baglam=None):
    """robots.txt bu UA için url'yi yasaklıyorsa False. robots.txt yoksa/404/HTML dönerse (kural yok) True."""
    p = urllib.parse.urlparse(url)
    try:
        govde = indir(f"{p.scheme}://{p.netloc}/robots.txt", bekle=3.0, timeout=30, ssl_baglam=ssl_baglam)
    except Exception:
        return True
    if "<html" in govde[:600].lower() or "user-agent" not in govde.lower():
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(govde.splitlines())
    return rp.can_fetch(UA, url) and rp.can_fetch("*", url)


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
