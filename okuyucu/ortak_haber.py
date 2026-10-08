"""YEREL HABER kaynakları: TEK KİŞİLİK vefat haberleri (site sahibi kararı 08.10.2026:
"Bu vefat haberleri her gün yerel haber sitelerinde çıkıyor" -> günlük liste şart değil).

Bir yerel haber sitesinin RSS'i / site haritası okunur; başlığı vefat kalıbına uyan haber seçilir
("vefat etti", "hayatını kaybetti", "Hakk'a yürüdü", "son yolculuğuna uğurlandı", "toprağa verildi", "defnedildi" ...).
Başlık + RSS özeti (yoksa haberin ilk paragrafı) -> YALNIZ olgu: ad soyad, (varsa) yaş, ilçe/mahalle/köy, vefat/defin tarihi,
cami + namaz vakti (kısa), mezarlık. ALINMAZ: sitenin cümlesi, ölüm nedeni (kaza/hastalık ayrıntısı), fotoğraf, yakın adları,
telefon, adres. Ad bulunamazsa kayıt ÜRETİLMEZ. Kayıt: kaynak_turu "yerel_haber", kaynak_ad = site adı, kaynak_url = haber adresi
(iç veri; uygulamaya gitmez).

Okuma kuralları ortak_basin ile AYNI (sayaç ortak): site başına günde en çok 3 istek (robots.txt dahil), aynı alan adına >= 3,5 sn,
robots.txt'ye uyulur, 401/403/429 -> kaynak bırakılır (giriş/CAPTCHA/WAF dolanılmaz), TLS doğrulaması açık, yalnız standart kütüphane.
Dizin (RSS/site haritası) yanıtı veri/<il>/_haber_dizin/ altında 6 saat saklanır (aynı gün yeniden istenmez).
Haberin kendisi yalnız RSS özeti ad/olgu vermiyorsa açılır (çalışma başına en çok 2, günlük 3 istek bütçesi kalırsa).
YERELLİK: başlıkta başka il/ilçe adı geçen haber alınmaz; başlıkta ya da özette ilin/ilçesinin adı geçmelidir (ilçe gazetesinde
`kesin_yerel`). Bu, ulusal haberleri (ünlü ölümü, başka ildeki kaza) eler.
"""
import hashlib, os, re, sys, time, urllib.parse
from datetime import date, datetime, timedelta

DIZIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIZIN)
import ortak, ortak_ilce as oi, ortak_basin as ob

KAYNAK_TURU = "yerel_haber"
ONBELLEK_SN = 6 * 3600

# başlıkta vefat kalıbı (tek kişilik haber)
VEFAT_BASLIK = re.compile(
    r"(vefat\s+etti|vefat\s+etmiştir|hayatını\s+kaybetti|yaşamını\s+yitirdi|hayata\s+veda\s+etti|hakk['’]?a\s+yürüdü|"
    r"rahmet[ei]\s+kavuştu|rahmetine\s+kavuştu|son\s+yolculuğuna\s+uğurlandı|toprağa\s+verildi|defnedildi|"
    r"ebediyete\s+uğurlandı|dualarla\s+uğurlandı|gözyaşlarıyla\s+uğurlandı|kabri\s+başında|vefatı|hayatını\s+kaybeden)",
    re.I)
# toplu/olay haberleri ve tek kişilik olmayanlar (ölü sayısı, anma, yıl dönümü, başka ülke)
DISLA = re.compile(r"(\d+\s+(?:kişi|ölü|yaralı)|kişiler|anıldı|anma|yıl\s*dönümü|ölüm\s+yıl|vefatının|şehit|şehadet|"
                   r"cenazesi\s+bekleniyor|aranıyor|kayıp\s+(?:kişi|çocuk|genç|kadın)|gözaltı|tutuklandı|dava|mahkeme|sanık|"
                   r"çift|kardeşler|ailesinden\s+\d|anne\s+ve|baba\s+ve|ve\s+(?:oğlu|kızı|eşi))", re.I)
_UNVAN = set("""prof dr doç op uzm av öğr gör yrd hacı hafız şeyh seyda molla merhum merhume rahmetli emekli öğretmen imam
muhtar başkan başkanı eski usta ağa hoca hocası hemşerimiz hemşehrimiz esnaf esnafı iş insanı""".split())
_ONEK_DUR = set("""ve ile de da genç yaşlı yaşındaki yaşında acı kayıp kaybı haber haberi sevilen tanınan değerli usta eski
emekli kadın adam çocuk bebek kız oğlu kızı eşi babası annesi dedesi ninesi kardeşi ağabeyi ablası öğretmen öğretmeni imamı
iş insanı esnafı esnafından muhtarı muhtar başkanı ilçemizin ilimizin kentin şehrin ilçenin köyün tanınmış sevilen""".split())
_HARF = r"A-Za-zÇĞİÖŞÜÂÎÛçğıöşüâîû"


def onbellekli_dizin(ctx, url):
    """RSS/site haritası: 6 saatten taze önbellek varsa onu verir; yoksa bütçeli GET (ob.al). Bütçe doluysa eski önbellek
    (varsa) ya da None. Dönen: metin|None."""
    kl = os.path.join(ctx["klasor"], "_haber_dizin")
    os.makedirs(kl, exist_ok=True)
    yol = os.path.join(kl, hashlib.sha1(url.encode()).hexdigest()[:16] + ".xml")
    if os.path.exists(yol) and time.time() - os.path.getmtime(yol) < ONBELLEK_SN:
        with open(yol, encoding="utf-8") as f:
            return f.read()
    try:
        x = ob.al(ctx, url)
    except ob.ButceDoldu as e:
        print(f"  {e}", file=sys.stderr)
        ob.durum(ctx).kaydet()
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                return f.read()
        return None
    with open(yol, "w", encoding="utf-8") as f:
        f.write(x)
    # eski önbellek dosyalarını temizle (2 gün)
    for a in os.listdir(kl):
        p = os.path.join(kl, a)
        if time.time() - os.path.getmtime(p) > 2 * 86400:
            os.remove(p)
    ob.durum(ctx).kaydet()
    return x


def rss_ogeleri(xml):
    """RSS/Atom/sitemap -> [{url, baslik, ozet, tarih}] (tarih ISO gün|None)."""
    out = []
    bloklar = re.findall(r"<item[\s>]([\s\S]*?)</item>", xml) or re.findall(r"<entry[\s>]([\s\S]*?)</entry>", xml) \
        or re.findall(r"<url>([\s\S]*?)</url>", xml)
    for b in bloklar:
        def al_(desen):
            m = re.search(desen, b)
            return (m.group(1) if m else "").replace("<![CDATA[", "").replace("]]>", "").strip()
        url = al_(r"<link>([\s\S]*?)</link>") or al_(r'<link[^>]+href="([^"]+)"') or al_(r"<loc>([\s\S]*?)</loc>")
        baslik = oi.metin(al_(r"<title[^>]*>([\s\S]*?)</title>") or al_(r"<news:title>([\s\S]*?)</news:title>"))
        ozet = al_(r"<description>([\s\S]*?)</description>") or al_(r"<summary[^>]*>([\s\S]*?)</summary>") \
            or al_(r"<content:encoded>([\s\S]*?)</content:encoded>")
        import html as _h
        ozet = ob.satirlara(_h.unescape(ozet))
        t = al_(r"<pubDate>([^<]*)") or al_(r"<published>([^<]*)") or al_(r"<updated>([^<]*)") \
            or al_(r"<news:publication_date>([^<]*)") or al_(r"<lastmod>([^<]*)") or al_(r"<dc:date>([^<]*)")
        g = None
        if re.match(r"\d{4}-\d{2}-\d{2}", t):
            g = t[:10]
        elif t:
            m = re.search(r"(\d{1,2}) (\w{3}) (\d{4})", t)
            if m:
                try:
                    g = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %b %Y").date().isoformat()
                except Exception:
                    g = None
        slug = False
        if not baslik and url:      # sitemap: başlık adres parçasından (Türkçe harfsiz; ad için KULLANILMAZ)
            slug = True
            baslik = re.sub(r"[-_]+", " ", re.sub(r"(?:-|/)\d+(?:\.html?)?/?$|\.html?$", "", url.rstrip("/").rsplit("/", 1)[-1]))
        if url:
            out.append({"url": url.strip(), "baslik": baslik, "ozet": ozet, "tarih": g, "slug": slug})
    return out


def vefat_haberi_mi(baslik):
    b = baslik or ""
    if not VEFAT_BASLIK.search(b):
        return False
    if DISLA.search(b):
        return False
    return True


_AD_DEGIL = set("""trafik kaza kazası kazasında kazada feci acı genç yaşlı öğrenci bebek çocuk usta anne baba kadın adam işçi şoför
sürücü yaya kız oğlu kızı eşi vatandaş kişi hayatını kaybetti vefat etti son yolculuğuna uğurlandı haber haberi kayıp ölüm
emekli öğretmen esnaf imam muhtar başkan polis asker uzman çavuş er şehit doktor hemşire hayat veda toprağa verildi
defnedildi yürüdü hakk'a ailesinin ailesi günü acı kara gün yas köy köyü mahalle sevilen tanınan değerli eski ünlü ilk
okul hastane hastanede kalp krizi yangın yangında motosiklet otomobil tır kamyon traktör""".split())
_EK_SONU = re.compile(r"(?:[ıiuü]nda|[ıiuü]nde|s[ıiuü]nda|s[ıiuü]nde|lar[ıi]|ler[ıi]|[ıiuü]n[ıiuü]n|s[ıiuü]n[ıiuü]n|daki|deki|taki|teki)$")


def _kelime_ad_mi(w):
    if not re.fullmatch(r"[A-ZÇĞİÖŞÜÂÎÛ][" + _HARF + r"]*\.?", w):
        return False
    lw = ortak.tr_lower(w.rstrip("."))
    return lw not in _AD_DEGIL and not (len(lw) > 6 and _EK_SONU.search(lw))


def baslik_ad(baslik):
    """Başlıktan ad soyad: vefat kalıbından ÖNCEKİ son büyük harfli 2-4 sözcük (iyelik/unvan sonrası).
    'Bismil'de esnaf Ahmet Yılmaz vefat etti' -> 'Ahmet Yılmaz'. Yaş '(65)' / '65 yaşındaki' yakalanır."""
    b = " ".join((baslik or "").replace("’", "'").split())
    m = VEFAT_BASLIK.search(b)
    if not m:
        return None, None
    on = b[:m.start()].strip(" ,:-–")
    # 'Ahmet Yılmaz, ... vefat etti' / 'Ahmet Yılmaz hayatını kaybetti'
    yas = None
    ym = re.search(r"\((\d{1,3})\)|(\d{1,3})\s+yaşında(?:ki)?", on)
    if ym:
        yas = int(ym.group(1) or ym.group(2))
    on = re.sub(r"\(\d{1,3}\)", " ", on)
    on = re.split(r"[,:;!?]|\s[-–]\s", on)
    # 'Ahmet Yılmaz vefat etti' -> son parça; 'Usta gazeteci Ahmet Yılmaz' -> sondan geriye büyük harfli sözcükler
    for parca in reversed(on):
        sozler = parca.split()
        n_kucuk = 0                                   # 'Hacı Ali Çelik dualarla son ...': sondaki 1-3 küçük harfli sözcük atlanır
        atlanan = []
        while sozler and n_kucuk < 3 and re.fullmatch(r"[a-zçğıöşü]+", sozler[-1]):
            atlanan.append(sozler[-1])
            sozler = sozler[:-1]
            n_kucuk += 1
        if set(atlanan) & {"bebek", "çocuk", "kız", "öğrenci", "genç", "minik", "küçük"}:
            return None, None                         # 'Hafsa Nur bebek ...': yalnız ön ad yazılmış, soyadı yok
        top = []
        for w in reversed(sozler):
            w2 = w.strip(".'\"“”")
            if "'" in w2 or re.search(r"\d", w2):
                break
            lw = ortak.tr_lower(w2)
            if lw in _ONEK_DUR or lw.rstrip(".") in _UNVAN or not _kelime_ad_mi(w2):
                break
            top.append(w2)
        top.reverse()
        if 2 <= len(top) <= 4 and not all(w.isupper() and len(w) <= 3 for w in top):
            return oi.ad_duzelt(" ".join(top)), (yas if yas and 0 < yas < 125 else None)
        break
    return None, (yas if yas and 0 < yas < 125 else None)


_YAS = re.compile(r"(\d{1,3})\s+yaşında(?:ki)?|\((\d{1,3})\)")


def _yas_bul(metin_, ad):
    """Yaş: adın hemen yanında '(65)' ya da '65 yaşındaki/yaşında' (ad ile aynı cümlede, 80 karakter içinde)."""
    if not metin_:
        return None
    i = ortak.katla(metin_).find(ortak.katla(ad)) if ad else -1
    alan = metin_[max(0, i - 80): i + len(ad) + 80] if i >= 0 else metin_[:200]
    m = _YAS.search(alan)
    if m:
        y = int(m.group(1) or m.group(2))
        return y if 0 < y < 125 else None
    return None


def govde_ad(metin_):
    """Gövdeden ad: ob.ad_bul ile ölüm ifadesinden önceki büyük harfli sözcükler (gövdede 'vefat etti' cümlesi)."""
    for on, ifade, son, on_tam in ob.girisleri_ayir(metin_ or ""):
        ad, yas = ob.ad_bul(on)
        if ad:
            return ad, yas
    m = re.search(r"((?:[A-ZÇĞİÖŞÜ][" + _HARF + r"]+\s){1,3}[A-ZÇĞİÖŞÜ][" + _HARF + r"]+)\s*(?:\((\d{1,3})\))?,?\s+"
                  r"(?:\d{1,3}\s+yaşında\s+)?(?:hayatını\s+kaybetti|yaşamını\s+yitirdi|hayata\s+veda|toprağa\s+verildi|"
                  r"son\s+yolculuğuna|defnedildi|vefat)", metin_ or "")
    if m:
        ad = m.group(1).split()
        while ad and (ortak.tr_lower(ad[0]) in _ONEK_DUR or ortak.tr_lower(ad[0]).rstrip(".") in _UNVAN):
            ad = ad[1:]
        if 2 <= len(ad) <= 4:
            y = int(m.group(2)) if m.group(2) else None
            return oi.ad_duzelt(" ".join(ad)), y
    return None, None


def _ilce_metinde(il, metin_):
    """'Bismil'de', 'Bismil ilçesinde', 'Bismil ilçesine bağlı' -> resmî ilçe adı (ilk 300 karakter)."""
    liste = {ortak.katla(x): x for x in ortak.ilce_listesi(il)}
    for w in re.findall(r"[A-ZÇĞİÖŞÜ][" + _HARF + r"]+(?:['’][a-zçğıöşü]+)?", (metin_ or "")[:300]):
        a = liste.get(ortak.katla(re.split(r"['’]", w)[0]))
        if a:
            return a
    return None


def _koy_mahalle(metin_):
    m = re.search(r"([A-ZÇĞİÖŞÜ][" + _HARF + r"]+(?:\s[A-ZÇĞİÖŞÜ][" + _HARF + r"]+)?)\s+(köyü|Köyü|mahallesi|Mahallesi|beldesi|Beldesi)"
                  r"(?:nde|nden|nde|ne|nin)?\b", (metin_ or "")[:600])
    if not m:
        return None
    ad = m.group(1)
    if ortak.tr_lower(ad.split()[0]) in _ONEK_DUR:
        return None
    yerler = {ortak.katla(x) for x in ortak.ilce_verisi().get("_iller", [])}
    for liste in ortak.ilce_verisi().values():
        if isinstance(liste, list):
            yerler |= {ortak.katla(x) for x in liste}
    sozler = ad.split()
    while len(sozler) > 1 and ortak.katla(sozler[0]) in yerler:      # "Kargı Çobankaya Köyü" -> "Çobankaya Köyü"
        sozler = sozler[1:]
    ad = " ".join(sozler)
    return f"{ad} {ortak.tr_title(m.group(2))}"


def _mezarlik(metin_):
    m = re.search(r"((?:[A-ZÇĞİÖŞÜ][" + _HARF + r"]+\s){0,3}(?:[A-ZÇĞİÖŞÜ][" + _HARF + r"]+\s)?)(?:Köy\s+)?(Mezarlığı|mezarlığı|Mezarlık|"
                  r"Asri Mezarlığı|Şehitliği)(?=['’]|\s|\.|,)", metin_ or "")
    if not m:
        return None
    on = m.group(1).strip()
    sozler = []
    for w in reversed(on.split()):                    # sağdan sola: ekli/sıradan sözcükte durulur ('Gözyaşları Arasında')
        lw = ortak.tr_lower(w)
        if lw in _ONEK_DUR or _EK_SONU.search(lw) or lw in {"arasında", "gözyaşları", "eşliğinde", "dualarla", "aile", "ailesinin"}:
            break
        sozler.insert(0, w)
    while sozler and re.search(r"(?i)^(cenaze|naaşı|naaş|cenazesi|merhum|aile|ailesinin|ilçe|köy)", sozler[0]):
        sozler = sozler[1:]
    if not sozler or all(ortak.tr_lower(w) in {"mahalle", "köy", "ilçe", "şehir", "kent", "aile"} for w in sozler):
        return None                                   # 'Mahalle Mezarlığı' gibi adsız yer
    return ob.kisa(" ".join(sozler) + " " + ortak.tr_title(m.group(2)), 60)


def _cami_vakit(metin_):
    """'<Ad> Camii'nde kılınan ikindi namazının ardından' -> 'Ad Camii, ikindi namazı'."""
    m = re.search(r"[^.]*\b(?:cami|camii|camisi|cemevi)\w*[^.]*", metin_ or "", re.I)
    return ob.namaz_kisa(m.group(0)) if m else None


def _tarih_metinde(metin_):
    return ob.metinden_tarih(metin_[:400]) if metin_ else None


# ---------------------------------------------------------------- yerellik (haber o ilin mi?)
_YER_EK = re.compile(r"['’]?(?:n?[dt][ae]|n?[dt][ae]n|[ıiuü]n|n[ıiuü]n|l[ıiuü]|l[ıiuü]lar|l[ıiuü]n[ıiuü]n|[ae]|y[ae]|n[ae])?$")
_baska_onbellek = {}


def _yer_sozleri(il, takma=()):
    """(kendi, başka): katlanmış yer adı kümeleri. kendi = il + ilçeleri + takma adlar; başka = öbür 80 il + öbür illerin
    ilçeleri (kendi ilin ilçesiyle aynı adı taşıyanlar hariç)."""
    k = (il, tuple(takma))
    if k in _baska_onbellek:
        return _baska_onbellek[k]
    v = ortak.ilce_verisi()
    kendi = {ortak.katla(il)} | {ortak.katla(x) for x in ortak.ilce_listesi(il)} | {ortak.katla(x) for x in takma}
    baska = {ortak.katla(x) for x in v.get("_iller", [])} - kendi
    for il2, liste in v.items():
        if il2.startswith("_") or il2 == il or not isinstance(liste, list):
            continue
        baska |= {ortak.katla(x) for x in liste if len(x) > 3} - kendi
    for x, il2 in (v.get("_il_disi_bilinen") or {}).items():
        if il2 != il:
            baska.add(ortak.katla(x))
    baska -= {"merkez", "yenice", "yenisehir", "akdeniz", "sur", "han", "bayat", "selim", "hani"} - kendi   # sıradan sözcük de olan adlar
    _baska_onbellek[k] = (kendi, baska)
    return kendi, baska


_YER_EKI = re.compile(r"^(?:n?[dt][ae]n?|y?[ae]|n[ae])$")          # 'da/'de/'ta/'te/'dan/'den/'nda/'ndan/'a/'e/'ya/'ye/'na/'ne
_GUNLER = {"pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar"}


def _yer_sirasi(metin_):
    """Metindeki büyük harfli sözcükler sırayla: (katlanmış kök, yer_eki_var_mi). "Gaziantep’te" -> ("gaziantep", True),
    "Çorumlu" -> ("corum", False). Gün adları (Perşembe, Pazar: aynı zamanda ilçe adı) atlanır."""
    out = []
    for w in re.findall(r"[A-ZÇĞİÖŞÜ][" + _HARF + r"]+(?:['’][a-zçğıöşü]+)?", metin_ or ""):
        parca = re.split(r"['’]", w)
        kok = ortak.katla(parca[0])
        if kok in _GUNLER:
            continue
        ekli = len(parca) > 1 and bool(_YER_EKI.match(parca[1]))
        out.append((kok, ekli))
        m = re.match(r"(.+?)(?:l[ıiuü]|l[ıiuü]lar)$", parca[0])          # Çorumlu, Kastamonulu
        if m:
            out.append((ortak.katla(m.group(1)), False))
    return out


def yerel_mi(il, baslik, ozet, takma=(), kesin_yerel=False):
    """Haber bu ilin mi? (True / False / None = kanıt yok)
    Başka il/ilçe yalnız YER EKİYLE yazılmışsa sayılır ("Gaziantep’te", "Bartın’a"); kişi adı olan ilçe adları (Yıldırım, Demirci)
    ve gün adları (Perşembe, Pazar) böylece yer sanılmaz. Kendi ilin/ilçenin adı her biçimde sayılır (Çorum’un, Çorumlu).
    - Başlıkta ekli başka yer var, kendi yer yok: HAYIR.
    - Başlık + özette ilk anılan yer başka bir yerse: HAYIR; kendi yer geçiyorsa: EVET.
    - kesin_yerel (ilçe gazetesi): başlıkta kesmeli yabancı özel ad yoksa EVET.
    - il gazetesi: özette cenaze cümlesi/cami/mezarlık varsa EVET; yoksa None (haber açılıp yeniden bakılır)."""
    kendi, baska = _yer_sozleri(il, takma)
    bs = _yer_sirasi(baslik)
    if any(x in baska and e for x, e in bs) and not any(x in kendi for x, _ in bs):
        return False
    oz = (ozet or "")[:600]
    tum = bs + _yer_sirasi(oz)
    ilk = next(((x, e) for x, e in tum if x in kendi or (e and x in baska)), None)
    if ilk and ilk[0] not in kendi:
        return False
    if ilk:
        return True
    if kesin_yerel:
        # başlıkta kesmeli özel ad (Fenerbahçe'nin, Yeşilçam'ın) kendi yer adı değilse ulusal haber sayılır
        ekli_ad = [ortak.katla(re.split(r"['’]", w)[0]) for w in re.findall(r"[A-ZÇĞİÖŞÜ][" + _HARF + r"]+['’][a-zçğıöşü]+", baslik or "")]
        return not [x for x in ekli_ad if x not in kendi]
    if ob.cenaze_cumlesi(oz) or re.search(r"(?i)cami|mezarl", oz):
        return True
    return None          # kanıt yok: haberin kendisi açılırsa yeniden bakılır


def olgular(il, baslik, ozet, yayin_gunu):
    """Başlık + özet/ilk paragraf -> olgu sözlüğü (ad yoksa None). Ölüm nedeni, yakın adı, sitenin cümlesi ALINMAZ."""
    ad, yas = baslik_ad(baslik)
    if not ad:
        ad, yas2 = govde_ad(ozet)
        yas = yas or yas2
    if not ad or len(ad.split()) < 2 or re.search(r"\b[A-ZÇĞİÖŞÜ]\.", ad):
        return None
    yas = yas or _yas_bul(ozet, ad) or _yas_bul(baslik, ad)
    ilce = _ilce_metinde(il, baslik) or _ilce_metinde(il, ozet)
    cumle = ob.cenaze_cumlesi(ozet or "")
    namaz_t = defin_t = None
    namaz = defin = None
    if cumle:
        lc = ortak.tr_lower(cumle)
        t = ob.metinden_tarih(cumle)
        if t:
            namaz_t = t
        elif re.search(r"\bbugün\b", lc):
            namaz_t = yayin_gunu
        elif re.search(r"\byarın\b", lc) and yayin_gunu:
            namaz_t = (datetime.strptime(yayin_gunu, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
        _, defin = oi.cenaze_ayikla(cumle)
        namaz = ob.namaz_kisa(cumle)
        if defin:
            defin = re.sub(r"^(?:İlçemiz|ilçemiz|Şehrimiz|şehrimiz|Köyündeki|köyündeki)\s+", "", defin)
            if len(defin.split()) < 2 or re.search(r"(?i)cami|namaz", defin):
                defin = None
    if not namaz_t and ozet:
        m = re.search(r"(?i)cenaze[^.]{0,220}", ozet)
        t = ob.metinden_tarih(m.group(0)) if m else None
        if t:
            namaz_t = t
    defin = ob.kisa(defin) or _mezarlik(ozet)
    if not namaz:
        namaz = _cami_vakit(ozet)
    gecti = re.search(r"(?i)toprağa\s+verildi|defnedildi|son\s+yolculuğuna\s+uğurlandı|dualarla\s+uğurlandı|gözyaşlarıyla\s+uğurlandı",
                      f"{baslik} {ozet or ''}")
    if gecti and not namaz_t:
        defin_t = yayin_gunu                     # 'toprağa verildi' haberi: defin, yayın günü (ya da bir gün önce) yapılmış
    return {"ad": ad, "yas": yas, "ilce": ilce, "mahalle": ob.kisa(_koy_mahalle(ozet)), "namaz": ob.kisa(namaz), "defin": ob.kisa(defin),
            "namaz_t": namaz_t, "defin_t": defin_t, "il_disi": ob.il_disi_bul(il, defin) if defin else None}


def kayit_yap(ctx, il, slug, kaynak_ad, url, f, yayin_gunu):
    """olgular() sözlüğünden şema kaydı. Gün = cenaze cümlesindeki tarih, yoksa haberin yayın günü (ham.tarih_kaynagi)."""
    gun = f["namaz_t"] or yayin_gunu
    tk = "metin" if f["namaz_t"] else "yayin_tarihi"
    k = oi.kayit(il, f["ilce"], slug, f["ad"], gun, kaynak_ad, url, ctx["alindi"], ek_id="", liste_tarihi=gun,
                 yas=f["yas"], vefat_tarihi=None, defin_zamani=f["defin_t"], namaz_tarihi=f["namaz_t"],
                 namaz_yeri_vakti=f["namaz"], defin_yeri=f["defin"], mahalle=f["mahalle"],
                 ham={"yayin_tarihi": yayin_gunu, "tarih_kaynagi": tk})
    k["kaynak_turu"] = KAYNAK_TURU
    if not f["ilce"]:
        k["ilce"] = None
        k["ilce_belirsiz"] = True
    if f["il_disi"]:
        k["il_disi_defin"] = {"il": f["il_disi"], "ilce": None}
        k["ilce_belirsiz"] = False
    return k


def _ozet_yeterli(oz, baslik):
    return bool(oz) and len(oz) > 80 and not ortak.katla(oz).startswith(ortak.katla(baslik)[:40])


SLUG_VEFAT = re.compile(r"vefat-etti|vefat-etmistir|hayatini-kaybetti|yasamini-yitirdi|hakka-yurudu|son-yolculuguna-ugurlandi|"
                        r"topraga-verildi|defnedildi|dualarla-ugurlandi|gozyaslariyla-ugurlandi|hayata-veda|rahmetine-kavustu")


def _ayni_site(u1, u2):
    return ob.site_anahtari(urllib.parse.urlparse(u1).netloc) == ob.site_anahtari(urllib.parse.urlparse(u2).netloc)


def sayfa_basligi(sayfa):
    m = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', sayfa) or re.search(r"<title>([\s\S]*?)</title>", sayfa)
    t = oi.metin(m.group(1)) if m else ""
    return re.split(r"\s[-|–]\s", t)[0].strip()


def haber_kaynagi(ctx, il, slug, kaynak_ad, dizin_url, url_suzgec=None, makale_ac=2, varsayilan_ilce=None, takma=(),
                  kesin_yerel=False, ek_dizin=None):
    """Tek site: dizini (RSS) okur, pencere içindeki VEFAT haberlerinden (yerel olanlar) kayıt üretir.
    Başlık ve özet adı/olguyu vermiyorsa ve bütçe kalmışsa en çok `makale_ac` haber açılır (en yeni önce).
    Açılan haberden çıkarılan OLGULAR (metin değil) veri/<il>/_haber_olgu.json'da saklanır; haber yeniden açılmaz."""
    xml = onbellekli_dizin(ctx, dizin_url)
    if xml is None:
        return []
    gl = set(ctx["gunler"])
    olgu_yol = os.path.join(ctx["klasor"], "_haber_olgu.json")
    try:
        import json
        with open(olgu_yol, encoding="utf-8") as fh:
            sakli = json.load(fh)
    except Exception:
        sakli = {}
    sonuc, acilacak = {}, []
    for o in rss_ogeleri(xml):
        if url_suzgec and not re.search(url_suzgec, o["url"]):
            continue
        if o["slug"] or not vefat_haberi_mi(o["baslik"]):
            continue
        g = o["tarih"] or ob.metinden_tarih(o["url"].replace("-", " "))
        if not g or g not in gl:
            continue
        if o["url"] in sakli:
            f = sakli[o["url"]].get("olgu")
            if f and f.get("defin") and re.fullmatch(r"(?:Mahalle|Köy|Aile|İlçe|Şehir|Kent)\s+Mezarl\w*", f["defin"]):
                f["defin"] = None
            if f:
                sonuc[o["url"]] = kayit_yap(ctx, il, slug, kaynak_ad, o["url"], f, g)
            continue
        y = yerel_mi(il, o["baslik"], o["ozet"], takma, kesin_yerel)
        if y is False:
            continue
        if y is None:                                  # yerellik belirsiz: özet yetersizse haber açılır
            if not _ozet_yeterli(o["ozet"], o["baslik"]):
                acilacak.append((o, g))
            continue
        f = olgular(il, o["baslik"], o["ozet"], g)
        if f and not f["ilce"] and varsayilan_ilce:
            f["ilce"] = varsayilan_ilce
        if f:
            sonuc[o["url"]] = kayit_yap(ctx, il, slug, kaynak_ad, o["url"], f, g)
        if (f is None or not (f["namaz"] or f["defin"])) and not _ozet_yeterli(o["ozet"], o["baslik"]):
            acilacak.append((o, g))
    # daha önce açılmış (site haritasından gelen) haberlerin saklı olguları: RSS'te artık görünmeseler de pencere içindeyse kayıt
    for u, v in sakli.items():
        f = v.get("olgu")
        if f and u not in sonuc and (v.get("tarih") or "") in gl and (not url_suzgec or re.search(url_suzgec, u)) \
                and _ayni_site(u, dizin_url):
            if f.get("defin") and re.fullmatch(r"(?:Mahalle|Köy|Aile|İlçe|Şehir|Kent)\s+Mezarl\w*", f["defin"]):
                f["defin"] = None
            sonuc[u] = kayit_yap(ctx, il, slug, kaynak_ad, u, f, v["tarih"])
    if ek_dizin:
        rss_url = {o["url"] for o in rss_ogeleri(xml)}
        try:
            x2 = onbellekli_dizin(ctx, ek_dizin.replace("{AY}", date.today().strftime("%Y-%m")))
        except Exception as e:
            x2 = None
            print(f"  ek dizin okunamadı: {e}", file=sys.stderr)
        for o in rss_ogeleri(x2 or ""):
            g = o["tarih"]
            if g in gl and o["url"] not in rss_url and o["url"] not in sakli and SLUG_VEFAT.search(o["url"]):
                acilacak.append(({"url": o["url"], "baslik": "", "ozet": ""}, g))
    n = 0
    for o, g in sorted(acilacak, key=lambda x: x[1], reverse=True):
        if n >= makale_ac:
            break
        try:
            sayfa = ob.al(ctx, o["url"])
        except (ob.ButceDoldu, oi.Engel):
            break
        except Exception as e:
            print(f"  haber açılamadı: {o['url']}: {e}", file=sys.stderr)
            continue
        n += 1
        ilk = (ob.makale_govdesi(sayfa) or _ilk_paragraflar(sayfa))[:900]
        ob.okundu(ctx, o["url"])
        f = None
        if not o["baslik"]:                            # site haritasından gelen aday: başlık sayfadan
            o["baslik"] = sayfa_basligi(sayfa)
        if o["baslik"] and vefat_haberi_mi(o["baslik"]) and yerel_mi(il, o["baslik"], ilk, takma, kesin_yerel):
            f = olgular(il, o["baslik"], ilk, g)
            if f and not f["ilce"] and varsayilan_ilce:
                f["ilce"] = varsayilan_ilce
        sakli[o["url"]] = {"olgu": f, "tarih": g}          # yalnız olgular saklanır (sitenin metni değil)
        if f:
            sonuc[o["url"]] = kayit_yap(ctx, il, slug, kaynak_ad, o["url"], f, g)
        else:
            sonuc.pop(o["url"], None)
    ob.durum(ctx).kaydet()
    sinir = (date.today() - timedelta(days=10)).isoformat()
    sakli = {u: v for u, v in sakli.items() if (v.get("tarih") or "") >= sinir}
    ortak.json_yaz(olgu_yol, sakli)
    # aynı kişi aynı sitede iki haber (vefat + defin): tek kayıt (en çok alanı dolu olan)
    tek = {}
    for k in sonuc.values():
        a = ortak.katla(k["ad_soyad"])
        eski = tek.get(a)
        if not eski or sum(v is not None for v in k.values()) > sum(v is not None for v in eski.values()):
            tek[a] = k
    return list(tek.values())


def _ilk_paragraflar(sayfa):
    """JSON-LD yoksa: <article> ya da sayfadaki ilk uzun <p>'ler (yalnız bellekte işlenir; saklanmaz)."""
    m = re.search(r"<article[\s\S]*?</article>", sayfa)
    alan = m.group(0) if m else sayfa
    ps = [oi.metin(p) for p in re.findall(r"<p[^>]*>([\s\S]*?)</p>", alan)]
    ps = [p for p in ps if len(p) > 60]
    return "\n".join(ps[:4])


# ---------------------------------------------------------------- il okuyucusu kalıbı
def site(ad, slug, dizin, kesin_yerel=False, ilce=None, takma=(), makale_ac=2, url_suzgec=None, ek_dizin=None):
    """Bir yerel haber sitesi tanımı (il dosyalarında kullanılır). ek_dizin: aylık site haritası ("{AY}" -> YYYY-AA);
    RSS'e girmeyen vefat haberlerinin adresini verir (Türkçe harfsiz adres parçası ad için KULLANILMAZ; haber açılınca okunur)."""
    return {"ad": ad, "slug": slug, "dizin": dizin, "kesin_yerel": kesin_yerel, "ilce": ilce, "takma": tuple(takma),
            "makale_ac": makale_ac, "url_suzgec": url_suzgec, "ek_dizin": ek_dizin}


def okuyucular(il, siteler):
    """[site(...)] -> oi.il_calistir için [(kaynak adı, işlev)]."""
    out = []
    for s in siteler:
        def islev(ctx, s=s):
            return haber_kaynagi(ctx, il, s["slug"], s["ad"], s["dizin"], url_suzgec=s["url_suzgec"], makale_ac=s["makale_ac"],
                                 varsayilan_ilce=s["ilce"], takma=s["takma"] + ((s["ilce"],) if s["ilce"] else ()),
                                 kesin_yerel=s["kesin_yerel"], ek_dizin=s["ek_dizin"])
        out.append((s["ad"], islev))
    return out
