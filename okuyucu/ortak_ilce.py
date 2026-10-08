"""Yalnız İLÇE düzeyinde kaynağı olan iller (Artvin, Samsun, Muğla, Ankara, ...) için ortak yardımcılar.
ortak.py'ye DOKUNMAZ; ortak, ortak_ek ve ortak9 üstüne kurulur. Yalnız standart kütüphane.

Bir il = tek dosya (okuyucu/<il>.py). İçinde o ilin okunabilen her ilçesi AYRI kaynak olarak bir okuyucu işlevidir;
`il_calistir()` ilçeleri sırayla çalıştırır (biri hata verirse / engel çıkarsa öbürleri sürer), kayıtları gün
dosyalarına BİRLEŞTİREREK yazar (kaynaktan düşen kayıt silinmez) ve veri/<il>/son7gun.json üretir.
Kayıtların `ilce` alanı kaynağın ilçesidir (dolu); kaynak_ad "X Belediyesi".

Okuma kuralları: robots.txt (ilçe alan adı başına bir kez okunur, yasaksa o ilçe okunmaz); aynı alan adına istekler
arası >= 3,5 sn (ortak.indir); TLS doğrulaması AÇIK (eksik ara sertifika gerekiyorsa sertifika/ilce-zincir.pem);
403/429 gelirse o ilçe BIRAKILIR (dolanılmaz). KVKK: telefon, yakınlar, taziye adresi, ölüm nedeni, meslek alınmaz.
"""
import json, os, re, ssl, sys, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ek, ortak9, ortak_kopru

VERI = os.path.join(DIZIN, "..", "veri")
SERT = os.path.join(DIZIN, "sertifika", "ilce-zincir.pem")
PENCERE = 7


class Engel(Exception):
    """robots.txt yasağı ya da 403/429: bu ilçe bırakılır (engel dolanılmaz)."""


def ssl_ilce():
    """Doğrulama AÇIK; yalnız eksik ara sertifikaları (SSL2BUY/E-Tuğra zincirleri) ekler."""
    c = ssl.create_default_context()
    c.load_verify_locations(SERT)
    return c


def gunler(n=PENCERE):
    return ortak_ek.son_gunler(n)


def metin(s):
    return ortak9.metin(s)


# ---------------------------------------------------------------- tarih / ad / metin yardımcıları
_AY = ortak.AYLAR


def tarih(s):
    """'07/10/2026' '07.10.2026' '07-10-2026' '2026-10-07' '7 Ekim 2026' '5.10.2026 00:00:00' -> 'YYYY-AA-GG'.
    Çözülemeyen ya da 2 günden ilerideki (kaynak yazım hatası: 27.06.2027) tarih None."""
    s = (s or "").strip()
    g = a = y = None
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, a, g = map(int, m.groups())
    else:
        m = re.search(r"(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4})", s)
        if m:
            g, a, y = map(int, m.groups())
        else:
            m = re.search(r"(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]+)\s+(\d{4})", s)
            if m and ortak.tr_lower(m.group(2)) in _AY:
                g, a, y = int(m.group(1)), _AY[ortak.tr_lower(m.group(2))], int(m.group(3))
    if not m:
        return None
    try:
        d = datetime(y, a, g).date()
    except ValueError:
        return None
    if d > date.today() + timedelta(days=2):
        return None
    return d.isoformat()


def ad_duzelt(s):
    """Ad-soyad: parantez içi (yaş, takma ad, yakın), yıldız, rakam atılır; Başlık Biçimi."""
    s = metin(s)
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[*\d]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -–,.:")
    return ortak.tr_title(s)


def buyuk_ise_title(s, yer=False):
    """Hepsi BÜYÜK HARF metni Başlık Biçimine çevirir; yer=True ise hepsi küçük harf yer/mezarlık adını da.
    Karışık yazılmış metne dokunmaz (cümle küçük harfle yazılmışsa olduğu gibi kalır)."""
    s = " ".join((s or "").replace("\u0307", "").split())
    harf = [c for c in s if c.isalpha()]
    if harf and all(c == c.upper() for c in harf):
        return ortak.tr_title(s)
    if yer and harf and all(c == c.lower() for c in harf):
        return ortak.tr_title(s)
    return s


def yas_hesapla(dogum_iso, vefat_iso):
    try:
        d = datetime.strptime(dogum_iso, "%Y-%m-%d").date()
        v = datetime.strptime(vefat_iso, "%Y-%m-%d").date()
    except Exception:
        return None
    y = v.year - d.year - ((v.month, v.day) < (d.month, d.day))
    return y if 0 <= y <= 125 else None


def say(s):
    try:
        return int(re.search(r"\d+", s or "").group(0))
    except Exception:
        return None


_VAKIT = r"(sabah|öğle|öğlen|ikindi|ikindi|akşam|yatsı|cuma|teravih|cenaze)\s*(?:namaz\w*)?"
_ADRES = re.compile(r"(evinden|evinde|ev adresi|sokak|sk\.|cadde|cd\.|apartman|\bno\s*:|\bdaire\b|taziye|\bgsm\b|\btel\b)", re.I)
_TEL = re.compile(r"(?:\+?90\s?)?0?\s?5\d{2}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")


_FIIL = (r"(?:defnedilecektir|defnedilecek|defnedilmiştir|defnedilmistir|toprağa verilecektir|toprağa verildi|"
         r"kaldırılacaktır|kılınacaktır|kılınacak|gömülecektir)")
_DURAK = {"ardından", "sonra", "müteakip", "müteakiben", "kaldırılarak", "kaldırılıp", "alınarak", "kılınacak", "namazının",
          "namazından", "namazına", "namazını", "bugün", "yarın", "ve", "olarak", "da", "de", "ile",
          "tarihinde", "alınıp", "alınarak", "namazı", "saat"}


_DEFIN_FIIL = r"(?:defnedilecektir|defnedilecek|defnedilmiştir|defnedilmistir|toprağa verilecektir|toprağa verildi|gömülecektir)"


def _yer_sonek(s):
    """'Kızılalan Mezarlığına' -> 'Kızılalan Mezarlığı'; 'asri mezarlıkta' -> 'asri mezarlık'."""
    s = s.strip(" ,.;")
    w = s.split(" ")
    son = w[-1]
    lw = ortak.tr_lower(son).replace("’", "'")
    if re.match(r"mezarl[ıi]ğ", lw):
        w[-1] = son[:8] + ("ı" if son[:8].isupper() is False else "I")
    elif re.match(r"mezarl[ıi]k", lw):
        w[-1] = son[:8]
    else:
        w[-1] = ortak9._dativ(son)
    return " ".join(w).strip(" ,.;")


def cenaze_ayikla(txt):
    """Serbest ilan metninden yalnız 'Cenazesi ...' cümlesini alır -> (namaz_yeri_vakti, defin_yeri).
    Yakın adları, telefon, taziye/ev adresi KVKK gereği atılır. Bulunamazsa (None, None)."""
    t = " ".join((txt or "").replace("\xa0", " ").split())
    low = ortak.tr_lower(t)
    m = re.search(r"cena[sz]e(?:z[iı]|si|miz|nin)\b", low) or re.search(r"cenaze\s+namaz", low)
    if not m:
        return None, None
    ek = low[m.start():]
    son = re.search(_DEFIN_FIIL, ek) or re.search(_FIIL, ek)
    c = t[m.start():m.start() + (son.end() if son else min(len(ek), 260))]
    c = _TEL.split(c)[0].strip(" ,.;-")
    gov = re.sub(r"^cena[sz]e\w*\s+", "", c, flags=re.I)
    gov = re.sub(r"^namaz\w*\s+(?=\S)", "", gov, flags=re.I)          # "Cenaze namazı öğle namazına ..." -> "öğle namazına ..."
    gov = re.sub(r"\s*" + _FIIL + r"\.?$", "", gov, flags=re.I).strip(" ,.;")
    # defin yeri: sondaki "...mezarlığ-" sözcüğü ve önündeki en çok 3 sözcük
    defin = None
    sozler = gov.split()
    for i in range(len(sozler) - 1, -1, -1):
        if "mezarl" in ortak.tr_lower(sozler[i]) or "mezar" == ortak.tr_lower(sozler[i])[:5] or ortak.tr_lower(sozler[i]).startswith("asri"):
            bas = i
            while bas > 0 and i - bas < 3:
                onceki = sozler[bas - 1]
                onceki_t = onceki.strip(" ,;:")
                ol = ortak.tr_lower(onceki_t)
                if onceki != onceki_t and onceki.endswith((",", ";", ":")):
                    break
                if ol in _DURAK or re.search(r"(den|dan|ten|tan|ıp|ip|up|üp)$", ol.strip("’'")) or re.search(r"[\d.(]", onceki) or ol.endswith("namaz"):
                    break
                bas -= 1
            defin = _yer_sonek(" ".join(sozler[bas:i + 1]))
            break
    if not defin and re.search(_DEFIN_FIIL, ek):
        for i in range(len(sozler) - 1, -1, -1):
            lw = ortak.tr_lower(sozler[i]).strip(",.;")
            mm = re.match(r"^(köy|mezra|belde|mahalle)\w*$", lw)
            if mm and i > 0:
                ekk = {"köy": "Köyü", "mezra": "Mezrası", "belde": "Beldesi", "mahalle": "Mahallesi"}[mm.group(1)]
                bas = i
                while bas > 0 and i - bas < 2 and ortak.tr_lower(sozler[bas - 1]).strip(",;") not in _DURAK \
                        and not re.search(r"[\d.(,]", sozler[bas - 1]) and not re.search(r"(den|dan|ten|tan|ıp|ip|up|üp)$", ortak.tr_lower(sozler[bas - 1])):
                    bas -= 1
                if bas < i:
                    defin = " ".join(sozler[bas:i]) + " " + ekk
                break
    namaz = gov
    if namaz and _ADRES.search(ortak.tr_lower(namaz)):
        v = re.search(_VAKIT, ortak.tr_lower(namaz))
        namaz = v.group(0) if v else None
    if defin and _ADRES.search(ortak.tr_lower(defin)):
        defin = None
    return (buyuk_ise_title(namaz) if namaz else None), (buyuk_ise_title(defin, yer=True) if defin else None)


_NAKIL = re.compile(r"(kaldırılarak|kaldırılıp|alınarak|alınıp|nakledilerek|nakledilip|götürülerek|götürülüp)", re.I)


def il_disi_isle(k, txt):
    """Cenaze cümlesi 'X Camii'nden kaldırılarak <başka İL> ... Mezarlığı'na defnedilecektir' ise kaydın il_disi_defin alanını
    {"il": başka il, "ilce": None} yapar (kaydın `ilce` alanı kaynağın ilçesi olarak KALIR). Yalnız nakil fiilinden SONRAKİ parçaya bakılır
    (hastane/cami adlarındaki il adları yanlış alarm vermesin). Bulunursa il adını döndürür."""
    t = " ".join((txt or "").split())
    ms = list(_NAKIL.finditer(t))
    if not ms:
        return None
    parca = t[ms[-1].end():]
    kendi = ortak.katla(k.get("il"))
    iller = {ortak.katla(x): x for x in ortak.ilce_verisi().get("_iller", [])}
    for sozcuk in re.findall(r"[^\s,.;()]+", parca)[:6]:
        a = iller.get(ortak.katla(sozcuk.split("'")[0].split("’")[0]))
        if a and ortak.katla(a) != kendi:
            k["il_disi_defin"] = {"il": a, "ilce": None}
            return a
    return None


_MAH = re.compile(r"^\s*(?:ilçemiz\s+)?([a-zçğıöşü0-9.' -]{2,40}?)\s+"
                  r"(mahallesi(?:nden|\s+sakinlerinden|\s+halkından)?|mah\.?\s?(?:den|’den|'den)|mhallesinden|mah\.\s+halkından|"
                  r"köyü(?:nden|\s+sakinlerinden)?|köyünden|beldesi(?:nden)?|mezrasından|mah\.)", re.I)


def mahalle_ayikla(txt):
    """Metin 'X mahallesinden / X Mahallesi sakinlerinden / X köyünden ...' diye başlıyorsa 'X Mahallesi' / 'X Köyü'."""
    orj = " ".join((txt or "").split())
    m = _MAH.match(ortak.tr_lower(orj))
    if not m:
        return None
    yer = orj[m.start(1):m.end(1)].strip()          # tr_lower uzunluğu korur
    tur = ortak.tr_lower(m.group(2))
    ek = "Köyü" if tur.startswith("köy") else ("Beldesi" if tur.startswith("belde") else ("Mezrası" if tur.startswith("mezra") else "Mahallesi"))
    yer = re.sub(r"\s*\b(?:mah\.?|mahallesi)$", "", yer, flags=re.I).strip()
    return ortak.tr_title(yer) + " " + ek if yer else None


def vakit_ayikla(txt):
    m = re.search(_VAKIT, ortak.tr_lower(txt or ""))
    if not m:
        return None
    return {"öğlen": "öğle"}.get(m.group(1), m.group(1))


# ---------------------------------------------------------------- ağ
_robots = {}


def robots_ok(url, ssl_baglam=None):
    p = urllib.parse.urlparse(url)
    k = p.scheme + "://" + p.netloc
    if k not in _robots:
        rp = None
        try:
            govde = ortak.indir(k + "/robots.txt", bekle=3.5, timeout=30, ssl_baglam=ssl_baglam)
            if "<html" not in govde[:600].lower() and "user-agent" in govde.lower():
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(govde.splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                rp = "yasak"            # robots.txt'e erişim engeli: tüm siteyi yasak say
        except Exception:
            rp = None
        _robots[k] = rp
    rp = _robots[k]
    if rp == "yasak":
        return False
    return True if rp is None else (rp.can_fetch(ortak.UA, url) and rp.can_fetch("*", url))


def al(url, ssl_baglam=None, veri=None, basliklar=None, bekle=3.5):
    """robots.txt kontrollü GET/POST. 403/429 -> Engel (dolanılmaz)."""
    if not robots_ok(url, ssl_baglam):
        raise Engel(f"robots.txt yasaklıyor: {url}")
    try:
        return ortak.indir(url, bekle=bekle, veri=veri, ssl_baglam=ssl_baglam, basliklar=basliklar)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            raise Engel(f"HTTP {e.code}: {url}")
        if e.code in (301, 302, 303, 307, 308) and not e.headers.get("Location"):
            # Muratlı gibi bazı sunucular sayfayı "301" kodu ve Location başlığı OLMADAN, gövdesiyle birlikte döndürür
            try:
                gov = e.read()
            except Exception:
                gov = b""
            if len(gov) > 2000:
                m = re.search(r"charset=([\w-]+)", e.headers.get("Content-Type", ""))
                return gov.decode(m.group(1) if m else "utf-8", "replace")
        raise


def al_parca(url, yeterli, ssl_baglam=None, azami=7_000_000, parca=262144):
    """Çok büyük, yeniden eskiye sıralı listeler (Torbalı 3 MB, Burhaniye 6,6 MB) için: sayfa parça parça okunur,
    `yeterli(metin)` True olunca (pencere dışı kayda ulaşılınca) bağlantı kapatılır. Tek istektir."""
    if not robots_ok(url, ssl_baglam):
        raise Engel(f"robots.txt yasaklıyor: {url}")
    host = urllib.parse.urlparse(url).netloc
    gecen = time.time() - ortak._son_istek.get(host, 0)
    if gecen < 3.5:
        time.sleep(3.5 - gecen)
    hedef, ek = ortak_kopru.kopru_url(url)
    rq = urllib.request.Request(hedef, headers={"User-Agent": ortak.UA, **ek})
    ham = b""
    try:
        with urllib.request.urlopen(rq, timeout=60, context=ssl_baglam) as r:
            ctype = r.headers.get("Content-Type", "")
            while len(ham) < azami:
                b = r.read(parca)
                if not b:
                    break
                ham += b
                if yeterli(ham.decode("utf-8", "replace")):
                    break
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            raise Engel(f"HTTP {e.code}: {url}")
        raise
    finally:
        ortak._son_istek[host] = time.time()
    m = re.search(r"charset=([\w-]+)", ctype)
    cs = m.group(1) if m and m.group(1).lower() not in ("big5",) else "utf-8"
    return ham.decode(cs, "replace")


# ---------------------------------------------------------------- kayıt
def kayit(il, ilce, slug, ad, gun, kaynak_ad, url, alindi, ek_id="", il_disi_metin=None, **alan):
    """Şemanın tüm alanları None başlar. ilce = kaynağın ilçesi (dolu); il_disi_defin/ilce_belirsiz önceden
    doldurulur, böylece ortak.ilce_isle ilçeyi yeniden çözmeye çalışmaz."""
    k = ortak9.kayit(slug, il, ad, gun, kaynak_ad, url, alindi, ek_id, **alan)
    k["ilce"] = ilce
    k["il_disi_defin"] = None
    k["ilce_belirsiz"] = False
    if il_disi_metin:
        il_disi_isle(k, il_disi_metin)       # başka ilde defin varsa il_disi_defin dolar (ilce kaynağın ilçesi olarak kalır)
    return k


def pencerede(gun, gun_listesi):
    return bool(gun) and gun in set(gun_listesi)


def sayfala(url_fn, ayristir, gun_listesi, ssl_baglam=None, azami_sayfa=4, baslangic=1, gun_alani="liste_tarihi"):
    """?page=N türü sayfalama: ayristir(html, sayfa_no) -> kayıt listesi (liste_tarihi dolu). Sayfada pencere içinde
    kayıt kalmayınca (ya da sayfa boşsa) durur. Dönen: pencere içi kayıtlar."""
    sonuc = []
    for n in range(baslangic, baslangic + azami_sayfa):
        try:
            sayfa = al(url_fn(n), ssl_baglam)
        except Engel:
            if n == baslangic:
                raise
            print(f"  sayfa {n} robots.txt/engel nedeniyle okunmadı (ilk sayfalar yeterli sayıldı)", file=sys.stderr)
            break
        liste = ayristir(sayfa, n)
        if not liste:
            break
        icinde = [k for k in liste if pencerede(k.get(gun_alani), gun_listesi)]
        sonuc.extend(icinde)
        if not icinde:
            break
    return sonuc


# ---------------------------------------------------------------- tablo yardımcıları
def hucreler(tr):
    return [metin(c) for c in re.findall(r"<t[hd](?:\s[^>]*)?>([\s\S]*?)</t[hd]>", tr)]


def tablo(sayfa, indeks=0, tr_sinifi=None):
    """HTML'deki indeks'inci <table>: (başlıklar [katla'lanmış], satırlar [[hücre]]). İlk satır başlıktır."""
    t = re.findall(r"<table[\s\S]*?</table>", sayfa)
    if len(t) <= indeks:
        raise RuntimeError("tablo bulunamadı (sayfa düzeni değişmiş olabilir)")
    rows = re.findall(r"<tr[\s\S]*?</tr>", t[indeks])
    if not rows:
        raise RuntimeError("tabloda satır yok")
    baslik = [ortak.katla(x) for x in hucreler(rows[0])]
    return baslik, [hucreler(r) for r in rows[1:]]


def kolon(baslik, satir, *adlar):
    """Başlık adına (katla'lanmış, kısmi eşleşme) göre hücre değeri; yoksa ''."""
    for a in adlar:
        a = ortak.katla(a)
        for i, b in enumerate(baslik):
            if a == b or a in b:
                return satir[i] if i < len(satir) else ""
    return ""


def modal_govdeleri(sayfa):
    return [metin(m) for m in re.findall(r'<div class="modal-body">([\s\S]*?)</div>', sayfa)]


# ---------------------------------------------------------------- "taranan gün" durumu (gün parametreli kaynaklar)
class Durum:
    """veri/<il>/_tarama.json: {ilçe: {gün: tarama zamanı}}. Gün parametreli kaynaklarda (19 Mayıs, Dörtyol) son
    `her_zaman` gün her çalışmada okunur; daha eski günler yalnız bir kez (ilk kurulum) okunur -> istek sayısı küçük kalır."""
    def __init__(self, klasor):
        self.yol = os.path.join(klasor, "_tarama.json")
        try:
            with open(self.yol, encoding="utf-8") as f:
                self.d = json.load(f)
        except Exception:
            self.d = {}

    def okunacak(self, ilce, gun_listesi, her_zaman=2):
        taranan = self.d.get(ilce, {})
        return [g for i, g in enumerate(gun_listesi) if i < her_zaman or g not in taranan]

    def isaretle(self, ilce, gun):
        self.d.setdefault(ilce, {})[gun] = ortak.simdi_iso()

    def kaydet(self, gun_listesi):
        for ilce in self.d:
            self.d[ilce] = {g: z for g, z in self.d[ilce].items() if g in set(gun_listesi)}
        ortak.json_yaz(self.yol, self.d)


# ---------------------------------------------------------------- il yürütücüsü
def il_calistir(il, klasor_adi, okuyucular, argv=None):
    """okuyucular: [(ilce_adi, islev)], islev(ctx) -> kayıt listesi (liste_tarihi dolu). ctx: dict(gunler, alindi, klasor, durum).
    Dönen: {ilçe: durum}. Kaynaktan düşen/önceden alınan kayıtlar korunur."""
    argv = sys.argv if argv is None else argv
    n = PENCERE
    if "--gun" in argv:
        n = int(argv[argv.index("--gun") + 1])
    secili = None
    if "--ilce" in argv:
        secili = {ortak.katla(x) for x in argv[argv.index("--ilce") + 1].split(",")}
    klasor = os.path.join(VERI, klasor_adi)
    os.makedirs(klasor, exist_ok=True)
    gl = gunler(n)
    ctx = {"gunler": gl, "alindi": ortak.simdi_iso(), "klasor": klasor, "durum": Durum(klasor), "il": il}
    by_gun = {g: [] for g in gl}
    ozet = {}
    for ilce, islev in okuyucular:
        if secili and ortak.katla(ilce) not in secili:
            continue
        try:
            kayitlar = islev(ctx)
        except Engel as e:
            ozet[ilce] = f"ENGEL (bırakıldı): {e}"
            print(f"[{ilce}] {ozet[ilce]}", file=sys.stderr)
            continue
        except Exception as e:
            ozet[ilce] = f"HATA: {type(e).__name__}: {e}"
            print(f"[{ilce}] {ozet[ilce]}", file=sys.stderr)
            continue
        goruldu, sayac = set(), 0
        for k in kayitlar:
            g = k.get("liste_tarihi")
            if g in by_gun and k["id"] not in goruldu:
                goruldu.add(k["id"])
                by_gun[g].append(k)
                sayac += 1
        ozet[ilce] = sayac
        print(f"[{ilce}] pencerede {sayac} kayıt")
    ctx["durum"].kaydet(gl)
    sayac = ortak_ek.yaz_birlestir(klasor, il, gl, by_gun)
    print(f"{il}: gün başına {sayac}")
    # ilçe başına sonuç son7gun.json'a yazılır (saglik.py HATA/ENGEL satırlarını uyarı olarak gösterir)
    try:
        son = os.path.join(klasor, "son7gun.json")
        with open(son, encoding="utf-8") as f:
            d = json.load(f)
        d["ilce_durum"] = {k: (v if isinstance(v, int) else str(v)) for k, v in ozet.items()}
        ortak.json_yaz(son, d)
    except Exception as e:
        print(f"ilce_durum yazılamadı: {e}", file=sys.stderr)
    return ozet
