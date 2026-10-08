#!/usr/bin/env python3
"""YAYIN SÜZGECİ (08.10.2026): iç veri (veri/, tam) -> yayın verisi (site/veri/, süzülmüş).

Kullanım: python3 okuyucu/yayin_suz.py site/veri          # klasörü YERİNDE süzer, sonra kendini denetler
          python3 okuyucu/yayin_suz.py site/veri --denetle   # yalnız denetler (dosyaya dokunmaz)
Çıkış kodu: 0 = temiz; 1 = süzgeçten sonra hâlâ yasak bir şey var (CI yayını DURDURUR; sızdırmaktansa yayımlamamak).

Kurallar (URUN-TASLAGI §16.5, §28, KVKK):
  (a) kaynak_turu "yerel_basin" / "yerel_haber" kayıtları çıkar; yalnız bu türden okunan iller (YEREL_ILLER) klasörüyle çıkar
  (b) kaynak_ad, kaynak_url, ham, alindi, kaynak_turu soyulur
  (c) anne_baba soyulur (kartta gösterilmez; iç veride kalır)
  (d) kayıtta yalnız UYGULAMA_ALANLARI kalır; il klasöründe yalnız son7gun.json kalır (gün dosyaları, _kapi_red, _basin,
      _haber_olgu, _tarama, _haber_dizin, örnek HTML'ler silinir)
  (e) ozet.json / saglik.json / kapi.json: çıkarılan iller düşer, metinlerdeki adresler (http..., alan adları) silinir
  (g) İKİNCİ KİLİT (URUN-TASLAGI §32): isimsiz bebek kaydı ("Bebek", "Kız/Erkek Bebek", "İsimsiz", "Adsız", "Yeni Doğan", "… Bebeği",
      ya da "Bebek" atınca yalnız soyad kalan) yayına girmez; il içinde aynı ad soyad + namaz/defin/vefat tarihi ±2 gün tek kayıt olur
      (en dolu kalır, ilk ilçe korunur). Süzgeç sonrası denetim bunların kalmadığını da doğrular.
  (f) kaybettiklerimiz/ içinde "_" ile başlayan iç dosyalar silinir; _meta.json yerine yalnız tarih + sayılar: durum.json
Yeni bir yerel basın/haber ili eklenirse YEREL_ILLER'e de yazılır (yazılmasa bile kayıtları (a) ile çıkar; il klasörü boş kalır).
"""
import json, os, re, shutil, sys

BASIN_TURLERI = ("yerel_basin", "yerel_haber")
# yalnız yerel basın / yerel haber kaynağından okunan iller (resmî kaynakları yok) — §28: yayına girmez
YEREL_ILLER = {"agri", "amasya", "ardahan", "bayburt", "bingol", "bitlis", "corum", "diyarbakir", "hakkari", "igdir", "kars",
               "kastamonu", "kilis", "kirklareli", "manisa", "mardin", "mersin", "mus", "siirt", "sirnak", "tunceli"}
# uygulamanın okuyacağı alanlar (başka hiçbir alan yayına gitmez)
UYGULAMA_ALANLARI = ("id", "il", "ilce", "mahalle", "ad_soyad", "yas", "vefat_tarihi", "namaz_tarihi", "namaz_yeri_vakti",
                     "defin_yeri", "defin_zamani", "liste_tarihi", "il_disi_defin", "ilce_belirsiz",
                     "cinsiyet", "sehit", "rutbe", "toren", "aile", "bebek")
SON7_ALANLARI = ("il", "ilceler", "il_disi", "ilce_belirsiz", "toplam", "guncelleme")
YASAK_ALANLAR = ("kaynak_ad", "kaynak_url", "ham", "anne_baba", "alindi", "kaynak_turu", "kaynaklar")
UST_DOSYALAR = ("ozet.json", "saglik.json", "kapi.json")
URL = re.compile(r"https?://\S+|\b(?:[\w-]+\.)+(?:bel\.tr|gov\.tr|com\.tr|com|net|org|tv)\b(?:/\S*)?", re.I)


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return json.load(f)


def yaz(yol, d):
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))


def kayit_suz(k):
    out = {a: k[a] for a in UYGULAMA_ALANLARI if a in k}
    # kaynakta vefat tarihi cenaze gününden SONRA yazılmışsa (kaynak hatası, ör. Bandırma 08.10.2026) kartta çelişki
    # gösterilmez: vefat tarihi yayına gitmez, cenaze günü kalır
    v = out.get("vefat_tarihi")
    c = [t for t in (out.get("namaz_tarihi"), (out.get("defin_zamani") or "")[:10]) if t and re.fullmatch(r"\d{4}-\d{2}-\d{2}", t)]
    if v and c and v > min(c):
        out["vefat_tarihi"] = None
    return out


# ---- ikinci kilit: isimsiz bebek + il içi tekilleştirme (kapi.py ile aynı kural; süzgeç tek başına çalışabilsin diye burada da var)
_TR = str.maketrans("çğıöşüÇĞİÖŞÜI", "cgiosucgiosuı")
YER_TUTUCU = {"isimsiz", "adsiz", "yeni", "dogan", "kiz", "erkek", "bilinmeyen", "bilinmiyor", "bebek", "bebegi", "bebekler", "no", "nolu"}


def _kat(s):
    s = (s or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def isimsiz_bebek(k):
    """True: yer tutucu ad ya da 'Bebek <Soyad>' (kişi adı yok)."""
    ad = (k.get("ad_soyad") or "").strip()
    kel = _kat(ad).split()
    if not kel or not (any(w in ("bebek", "bebegi", "bebekler", "isimsiz", "adsiz") for w in kel) or "yeni dogan" in " ".join(kel)):
        return False
    orj, kalan = ad.split(), 0
    for i, w in enumerate(orj):
        kw = _kat(w)
        if not kw or re.fullmatch(r"\d+", kw):
            continue
        if kw in YER_TUTUCU and not (kw == "dogan" and not (i > 0 and _kat(orj[i - 1]) == "yeni")):
            continue
        kalan += 1
    return kalan < 2


def _gun(s):
    from datetime import datetime
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _tarihler(k):
    t = [_gun(k.get(a) or "") for a in ("vefat_tarihi", "namaz_tarihi")] + [_gun((k.get("defin_zamani") or "")[:10])]
    t = [x for x in t if x]
    return t or [x for x in [_gun(k.get("liste_tarihi") or "")] if x]


def _ayni(a, b):
    if _kat(a.get("ad_soyad")) != _kat(b.get("ad_soyad")):
        return False
    try:
        if a.get("yas") is not None and b.get("yas") is not None and abs(int(a["yas"]) - int(b["yas"])) > 1:
            return False
    except (TypeError, ValueError):
        pass
    return any(abs((x - y).days) <= 2 for x in _tarihler(a) for y in _tarihler(b))


def il_ici_tekille(tum):
    """tum: okuma sırasıyla kayıt listesi -> elenecek kayıtların id()'leri; tutulan YERİNDE birleştirilir (ilk ilçe korunur)."""
    kumeler = []
    for k in tum:
        for km in kumeler:
            if _ayni(km[0], k):
                km.append(k)
                break
        else:
            kumeler.append([k])
    atilan = set()
    for km in kumeler:
        if len(km) < 2:
            continue
        ilk = km[0]
        taban = max(km, key=lambda x: sum(v not in (None, "", []) for v in x.values()))
        b = dict(taban)
        for o in km:
            for a, v in o.items():
                if b.get(a) in (None, "", []) and v not in (None, "", []):
                    b[a] = v
        b["ilce"] = ilk.get("ilce")
        ilk.clear()
        ilk.update(b)
        atilan.update(id(o) for o in km[1:])
    return atilan


def son7_suz(d):
    resmi = lambda l: [kayit_suz(k) for k in l if k.get("kaynak_turu") not in BASIN_TURLERI and not isimsiz_bebek(k)]
    ilceler = {i: resmi(l) for i, l in (d.get("ilceler") or {}).items()}
    ilceler = {i: l for i, l in ilceler.items() if l}
    out = {"il": d.get("il"), "ilceler": ilceler, "il_disi": resmi(d.get("il_disi") or []),
           "ilce_belirsiz": resmi(d.get("ilce_belirsiz") or []), "guncelleme": d.get("guncelleme")}
    tum = [k for l in ilceler.values() for k in l] + out["il_disi"] + out["ilce_belirsiz"]
    atilan = il_ici_tekille(tum)
    if atilan:
        ilceler = {i: [k for k in l if id(k) not in atilan] for i, l in ilceler.items()}
        out["ilceler"] = {i: l for i, l in ilceler.items() if l}
        out["il_disi"] = [k for k in out["il_disi"] if id(k) not in atilan]
        out["ilce_belirsiz"] = [k for k in out["ilce_belirsiz"] if id(k) not in atilan]
        ilceler = out["ilceler"]
    out["toplam"] = sum(len(l) for l in ilceler.values()) + len(out["il_disi"]) + len(out["ilce_belirsiz"])
    return out


def metin_temizle(o):
    if isinstance(o, str):
        return URL.sub("[adres]", o)
    if isinstance(o, list):
        return [metin_temizle(x) for x in o]
    if isinstance(o, dict):
        return {k: metin_temizle(v) for k, v in o.items()}
    return o


def suz(kok):
    cikan, kalan, toplamlar = [], [], {}
    for ad in sorted(os.listdir(kok)):
        yol = os.path.join(kok, ad)
        if not os.path.isdir(yol):
            if ad not in UST_DOSYALAR:          # veri/ kökünde başka dosya (ozet.N.json, notlar) yayına gitmez
                os.remove(yol)
            continue
        if ad == "kaybettiklerimiz":
            meta = os.path.join(yol, "_meta.json")
            if os.path.isfile(meta):             # yayına yalnız tarih + sayılar (_meta.json'daki eleme listeleri iç kayıttır)
                m = oku(meta)
                yaz(os.path.join(yol, "durum.json"), {"uretim_tarihi": m.get("uretim_tarihi"), "sayilar": m.get("sayilar")})
            for alt in os.listdir(yol):
                if alt.startswith("_"):
                    p = os.path.join(yol, alt)
                    shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
            continue
        son = os.path.join(yol, "son7gun.json")
        if ad.startswith("_") or ad in YEREL_ILLER or not os.path.isfile(son):
            shutil.rmtree(yol)
            cikan.append(ad)
            continue
        d = son7_suz(oku(son))
        shutil.rmtree(yol)
        os.makedirs(yol)
        yaz(son, d)
        kalan.append(ad)
        toplamlar[ad] = d["toplam"]
    # üst dosyalar: çıkan iller düşer, adresler silinir
    for ad in UST_DOSYALAR:
        yol = os.path.join(kok, ad)
        if not os.path.isfile(yol):
            continue
        d = oku(yol)
        if isinstance(d.get("iller"), dict):
            d["iller"] = {k: v for k, v in d["iller"].items() if k in kalan}
        for alan in ("hatali_iller", "ilce_sorunlari", "gun_hatasi"):
            if isinstance(d.get(alan), dict):
                d[alan] = {k: v for k, v in d[alan].items() if k in kalan}
        if isinstance(d.get("sifir_kayitli_iller"), list):
            d["sifir_kayitli_iller"] = [k for k in d["sifir_kayitli_iller"] if k in kalan]
        if ad == "kapi.json" and isinstance(d.get("iller"), dict):
            d["toplam_kayit"] = sum(v.get("kayit", 0) for v in d["iller"].values())
            d["toplam_elenen"] = sum(v.get("elenen", 0) for v in d["iller"].values())
            d.pop("nedenler", None)
        if ad == "ozet.json" and isinstance(d.get("iller"), dict):
            for k, v in d["iller"].items():
                if k in toplamlar:
                    v["kayit_sayisi"] = toplamlar[k]
        if ad == "saglik.json":                  # sorun cümleleri süzülmüş alanlardan yeniden kurulur
            s = []
            if d.get("hatali_iller"):
                s.append(f"{len(d['hatali_iller'])} il hata verdi: " + ", ".join(d["hatali_iller"]))
            if d.get("sifir_kayitli_iller"):
                s.append(f"{len(d['sifir_kayitli_iller'])} ilde son 7 günde 0 kayıt: " + ", ".join(d["sifir_kayitli_iller"]))
            if d.get("ilce_sorunlari"):
                s.append("ilçe hatası: " + ", ".join(d["ilce_sorunlari"]))
            if d.get("gun_hatasi"):
                s.append("okunamayan gün/ilçe sayfası: " + ", ".join(f"{k} ({v})" for k, v in d["gun_hatasi"].items()))
            if d.get("dusus_yuzde") is not None and d["dusus_yuzde"] > 40:
                s.append(f"toplam kayıt %{d['dusus_yuzde']} düştü")
            d["sorunlar"] = s
            d["saglikli"] = not s
            d["il_sayisi"] = len(kalan)
            d["toplam_kayit"] = sum(toplamlar.values())
            d.pop("onceki_toplam", None)
        yaz(yol, metin_temizle(d))
    return cikan, kalan


def denetle(kok):
    """Süzülmüş klasörde yasak bir şey kaldıysa listesini döndürür (boş liste = temiz)."""
    hata = []
    for ad in sorted(os.listdir(kok)):
        yol = os.path.join(kok, ad)
        if not os.path.isdir(yol) or ad == "kaybettiklerimiz":
            continue
        if ad in YEREL_ILLER:
            hata.append(f"{ad}: yerel basın ili yayında")
        for dosya in os.listdir(yol):
            if dosya != "son7gun.json":
                hata.append(f"{ad}/{dosya}: iç dosya yayında")
        son = os.path.join(yol, "son7gun.json")
        if not os.path.isfile(son):
            continue
        d = oku(son)
        tum = [k for l in (d.get("ilceler") or {}).values() for k in l] + (d.get("il_disi") or []) + (d.get("ilce_belirsiz") or [])
        for k in tum:
            fazla = set(k) - set(UYGULAMA_ALANLARI)
            if fazla:
                hata.append(f"{ad}/{k.get('id')}: yasak alan {sorted(fazla)}")
        for k in tum:
            if isimsiz_bebek(k):
                hata.append(f"{ad}/{k.get('id')}: isimsiz bebek yayında")
        for i, a in enumerate(tum):
            if any(_ayni(a, b) for b in tum[i + 1:]):
                hata.append(f"{ad}/{a.get('id')}: il içinde aynı kişi iki kez ({a.get('ad_soyad')})")
        ham = json.dumps(d, ensure_ascii=False)
        for y in YASAK_ALANLAR:
            if f'"{y}"' in ham:
                hata.append(f"{ad}: '{y}' alanı metinde")
        if URL.search(ham):
            hata.append(f"{ad}: adres/alan adı metinde ({URL.search(ham).group(0)[:40]})")
    for ad in UST_DOSYALAR:
        yol = os.path.join(kok, ad)
        if os.path.isfile(yol):
            ham = open(yol, encoding="utf-8").read()
            if URL.search(ham):
                hata.append(f"{ad}: adres metinde")
            for il in YEREL_ILLER:
                if f'"{il}"' in ham:
                    hata.append(f"{ad}: yerel basın ili '{il}' geçiyor")
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(kok)), "veri.tar.gz")):
        hata.append("veri.tar.gz yayın klasöründe (iç verinin tamamı)")
    return hata


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__)
        sys.exit(2)
    kok = args[0]
    if "--denetle" not in sys.argv:
        cikan, kalan = suz(kok)
        print(f"[süzgeç] yayına giren il: {len(kalan)} · çıkarılan: {len(cikan)} {cikan}")
    hata = denetle(kok)
    for h in hata[:50]:
        print(f"::error title=Yayin suzgeci::{h}")
    print("[süzgeç] denetim:", "TEMİZ" if not hata else f"{len(hata)} sorun — YAYIN DURDU")
    sys.exit(1 if hata else 0)


if __name__ == "__main__":
    main()
