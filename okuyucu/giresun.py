#!/usr/bin/env python3
"""Giresun Belediyesi vefat ilanları okuyucusu (WordPress RSS; yalnız standart kütüphane).
Kullanım: python3 okuyucu/giresun.py [--gun 7]
Kaynak: https://giresun.bel.tr/category/vefat-ilanlari/feed/ (günde 1 yazı, serbest metin).
Ayrıştırılamayan metinler veri/giresun/ayristirilamayan.json'a (kayıt dışı) yazılır.
KVKK: telefon ve yakın/taziye listesi alınmaz (ilan metnindeki akraba sıralaması yalnız
kimlik için kullanılır: kayda ad, anne-baba ve yer bilgisi girer; eş/çocuk/kardeş listesi girmez).
"""
import os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from html import unescape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak

FEED = "https://giresun.bel.tr/category/vefat-ilanlari/feed/"
KAYNAK_AD = "Giresun Belediyesi"
KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "veri", "giresun")
NS = {"c": "http://purl.org/rss/1.0/modules/content/"}
AZ = "A-ZÇĞİÖŞÜ"
ILCELER = ["ALUCRA", "BULANCAK", "ÇAMOLUK", "ÇANAKÇI", "DERELİ", "DOĞANKENT", "ESPİYE", "EYNESİL", "GÖRELE",
           "GÜCE", "KEŞAP", "PİRAZİZ", "ŞEBİNKARAHİSAR", "TİREBOLU", "YAĞLIDERE", "MERKEZ"]
REL = {"EŞİ", "ANNESİ", "ANNELERİ", "BABASI", "BABALARI", "KARDEŞİ", "KARDEŞLERİ", "ABLASI", "ABİSİ", "ABİLERİ",
       "ABLALARI", "GELİNİ", "DAMADI", "TORUNU", "TORUNLARI", "OĞLU", "KIZI", "OĞULLARI", "KIZLARI",
       "AMCASI", "DAYISI", "HALASI", "TEYZESİ", "ENİŞTESİ", "YENGESİ", "ELTİSİ", "KAYINPEDERİ", "KAYINVALİDESİ"}


def metin_yap(html):
    """İçerik HTML'i -> paragraf listesi; <strong> içi «...» ile işaretlenir, <hr> '---' paragrafı olur."""
    h = html.replace("<strong>", "«").replace("</strong>", "»")
    h = re.sub(r"<hr\s*/?>", "\n---\n", h)
    h = re.sub(r"</p>|<br\s*/?>", "\n", h)
    h = unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ")
    return [" ".join(p.split()) for p in h.split("\n") if p.strip()]


def gruplar(paragraflar):
    """Her kişi için paragraf grubu: «ad» içeren paragraf grubu başlatır, adsız paragraflar öncekine eklenir."""
    gr, cur = [], None
    for p in paragraflar:
        if p == "---":
            cur = None
            continue
        if "«" in p:
            cur = [p]
            gr.append(cur)
        elif cur is not None:
            cur.append(p)
        else:
            gr.append([p])  # adsız (öksüz) paragraf; ayrıştırma bunu reddeder
            cur = gr[-1]
    return [" ".join(g) for g in gr]


def kisilere_bol(metin):
    """Bir grup birden çok «ad» içeriyorsa 'ALLAH RAHMET EYLESİN' / 'TOPRAĞA VERİLECEKTİR' sınırlarından böl."""
    adlar = re.findall(r"«", metin)
    if len(adlar) <= 1:
        return [metin], None
    parcalar = [p.strip() for p in re.split(r"(?<=ALLAH RAHMET EYLESİN)[\s.…]*|(?<=TOPRAĞA VERİLECEKTİR)[\s.…]*", metin) if p.strip()]
    sonuc, cur = [], ""
    for p in parcalar:
        cur = (cur + " " + p).strip()
        if cur.count("«") >= 1 and ("TOPRAĞA VERİLECEKTİR" in cur or "RAHMET" in cur):
            sonuc.append(cur)
            cur = ""
    if cur:
        sonuc.append(cur)
    if len(sonuc) == len(adlar) and all(s.count("«") == 1 for s in sonuc):
        return sonuc, None
    return [metin], "bir paragrafta birden çok kişi, sınır bulunamadı"


def sade(s):
    return (s or "").replace("’", "'")


def anne_baba_cikar(baslik):
    """Başlık (ad öncesi) metninin SON ilişki sözcüğü OĞLU/KIZI/OĞULLARI/KIZLARI ise ondan önceki ebeveyn adları."""
    tok = sade(baslik).split()
    son = None
    for i, t in enumerate(tok):
        if t.strip(",.") in REL:
            son = i
    if son is None or tok[son].strip(",.") not in ("OĞLU", "KIZI", "OĞULLARI", "KIZLARI"):
        return None
    j = son - 1
    parca = []
    while j >= 0:
        t = tok[j]
        tt = t.strip(",.")
        if tt in REL:
            break
        if re.search(r"(?:NDEN|NDAN|İNDEN|INDAN|OĞULLARINDAN|LARINDAN|LERİNDEN)$", tt):
            break
        parca.append(t)
        j -= 1
    parca.reverse()
    ad = " ".join(w for w in parca if w not in ("MERHUM", "MERHUME", "MERHUMUN"))
    ad = re.sub(r"'[A-ZÇĞİÖŞÜ]+\b", "", ad)  # AK'IN -> AK
    ad = re.sub(r"\s+", " ", ad).strip(" ,")
    return ortak.tr_title(ad.replace(" VE ", " ve ")).replace(" Ve ", " ve ") or None


def yer_cikar(baslik):
    """Başlıktan ilçe ve köy/mahalle/belde. Yalnız metinde yazılanlar; çıkarım yok."""
    b = sade(baslik)
    tok = b.split()
    ilce = None
    for t in tok:
        tt = t.strip(",.")
        if tt in ILCELER:
            ilce = "Merkez" if tt == "MERKEZ" else ortak.tr_title(tt)
            break
    DUR = set(ILCELER) | {"İLÇESİ", "MERKEZ", "GİRESUN"} | REL | {"MERHUM", "MERHUME", "VE"}
    birimler = []
    for i, t in enumerate(tok):
        m = re.match(r"^(KÖYÜ|MAHALLESİ|BELDESİ)(?:[0-9]?(?:N?DEN|NDEN|NIN|NİN))?$", t.strip(",.").replace("'", ""))
        if not m:
            continue
        tur = {"KÖYÜ": "Köyü", "MAHALLESİ": "Mahallesi", "BELDESİ": "Beldesi"}[m.group(1)]
        ad = []
        k = i - 1
        while k >= 0 and len(ad) < 2:
            u = tok[k].strip(",.")
            if (u in DUR or re.match(r"^(KÖYÜ|MAHALLESİ|BELDESİ)", u.replace("'", ""))
                    or re.search(r"(?:NDEN|NDAN)$", u.replace("'", "")) or "'" in u):
                break
            ad.append(u)
            k -= 1
        if ad:
            birimler.append(ortak.tr_title(" ".join(reversed(ad))) + " " + tur)
    return ilce, ", ".join(birimler) or None


def cenaze_cikar(son):
    """'CENAZESİ ... TOPRAĞA VERİLECEKTİR' bölümünden namaz yeri/vakti ve defin yeri."""
    m = re.search(r"CENAZESİ\s+(.*?)\s*(?:TOPRAĞA VERİLECEKTİR|ALLAH RAHMET|$)", son)
    if not m:
        return None, None, None
    c = m.group(1).strip(" .")
    bugun = bool(re.match(r"BUGÜN\b", c))
    c = re.sub(r"^BUGÜN\s+", "", c)
    # defin: son 'SONRA' ifadesinden sonrası; yoksa 'MÜTEAKİP/MÜTEAKİBEN'den sonrası
    s = list(re.finditer(r"\bSONRA\b", c))
    if s:
        defin, namaz = c[s[-1].end():].strip(" ."), c[:s[-1].start()].strip(" .")
        namaz = re.sub(r"\s*KILINACAK CENAZE NAMAZINDAN$|\s*NAMAZI KILINDIKTAN$|\s*KILINDIKTAN$", "", namaz).strip()
    else:
        m2 = list(re.finditer(r"MÜTEAKİ(?:P|BEN)", c))
        if m2:
            defin, namaz = c[m2[-1].end():].strip(" ."), c[:m2[-1].end()].strip(" .")
        else:
            defin, namaz = None, c
    return (ortak.tr_title(namaz) or None, ortak.tr_title(defin) if defin else None, bugun)


def kisi_ayristir(metin, gun, url, alindi):
    """Tek kişilik metin -> kayıt ya da (None, neden)."""
    m = re.search(r"«\s*([^»]+?)\s*»", metin)
    if not m or "VEFAT" not in metin:
        return None, "kalın yazılmış ad ya da 'VEFAT ETMİŞTİR' yok"
    ad_govde = m.group(1)
    bas, son = metin[:m.start()], metin[m.end():]
    mv = re.search(r"VEFAT ET", son)
    # ad/soyad karşılaştırması: 'VEFAT ETMİŞTİR'den hemen önceki büyük harfli sözcükler de aynı adı vermeli
    if not mv:
        return None, "'VEFAT ETMİŞTİR' adın ardında değil"
    ad = ortak.tr_title(ad_govde.replace("«", "").replace("»", ""))
    if len(ad.split()) < 2:
        return None, f"ad tek sözcük: {ad_govde}"
    ilce, yer = yer_cikar(bas)
    anne_baba = anne_baba_cikar(bas)
    namaz, defin, bugun = cenaze_cikar(son)
    yas = re.search(r"(\d{1,3})\s*YAŞINDA", metin)
    liste = gun
    kayit = {
        "id": ortak.kayit_id("giresun", ad, gun, anne_baba or ""),
        "il": "Giresun", "ilce": ilce, "mahalle": yer, "ad_soyad": ad, "anne_baba": anne_baba,
        "yas": int(yas.group(1)) if yas else None,
        "dogum_tarihi": None,
        "vefat_tarihi": None,  # ilan vefat tarihini yazmıyor (liste tarihi = ilan günü)
        "defin_yeri": defin,
        "defin_zamani": None,
        "namaz_tarihi": gun if bugun else None,  # 'CENAZESİ BUGÜN' = ilanın yayımlandığı gün
        "namaz_yeri_vakti": namaz,
        "liste_tarihi": liste, "kaynak_ad": KAYNAK_AD, "kaynak_url": url, "alindi": alindi,
        "ham": {"metin": re.sub(r"[«»]", "", metin)},
    }
    return kayit, None


def feed_oku():
    ham = ortak.indir(FEED)
    kok = ET.fromstring(ham.lstrip("﻿").encode("utf-8"))
    yazilar = []
    for it in kok.findall(".//item"):
        link = it.find("link").text
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", link)
        if not m:
            continue
        yazilar.append(("-".join(m.groups()), link, it.find("c:encoded", NS).text or ""))
    return yazilar


def main():
    n = 7
    if "--gun" in sys.argv:
        n = int(sys.argv[sys.argv.index("--gun") + 1])
    if not ortak.robots_izin(FEED):
        print("robots.txt bu yolu yasaklıyor; okunmadı", file=sys.stderr)
        return
    bugun = date.today()
    gunler = [(bugun - timedelta(days=i)).isoformat() for i in range(n)]
    alindi = ortak.simdi_iso()
    by_gun = {g: [] for g in gunler}
    ayrisamayan = []
    for gun, link, html in feed_oku():
        if gun not in by_gun:
            continue
        for grup in gruplar(metin_yap(html)):
            parcalar, neden = kisilere_bol(grup)
            if neden:
                ayrisamayan.append({"liste_tarihi": gun, "kaynak_url": link, "neden": neden, "ham_metin": grup.replace("«", "").replace("»", "")})
                continue
            for p in parcalar:
                k, neden = kisi_ayristir(p, gun, link, alindi)
                if k:
                    by_gun[gun].append(k)
                else:
                    ayrisamayan.append({"liste_tarihi": gun, "kaynak_url": link, "neden": neden, "ham_metin": p.replace("«", "").replace("»", "")})
    for g in gunler:
        gor, tek = set(), []
        for k in by_gun[g]:
            if k["id"] not in gor:
                gor.add(k["id"]); tek.append(k)
        by_gun[g] = tek
        ortak.gun_yaz(KOK, "Giresun", g, tek)
        print(f"{g}: {len(tek)} kayıt")
    ortak.json_yaz(os.path.join(KOK, "ayristirilamayan.json"), {"il": "Giresun", "guncelleme": ortak.simdi_iso(), "sayi": len(ayrisamayan), "metinler": ayrisamayan})
    print("ayrıştırılamayan:", len(ayrisamayan))
    silinen = ortak.eski_gunleri_sil(KOK, set(gunler))
    if silinen:
        print("silinen eski dosyalar:", silinen)
    ortak.son7gun_yaz(KOK, "Giresun", gunler, by_gun)


if __name__ == "__main__":
    main()
