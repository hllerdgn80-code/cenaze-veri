"""Ortak.py'ye DOKUNMADAN eklenen yardımcılar (Şanlıurfa, Tokat, Uşak, Van, Karaman, Kütahya, Karabük, Yalova, Malatya okuyucuları)."""
import html, json, os, re
from datetime import date, datetime, timedelta

import ortak

KISA_AYLAR = {"oca": 1, "şub": 2, "mar": 3, "nis": 4, "may": 5, "haz": 6, "tem": 7, "ağu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12}


def son_gunler(n=7):
    """Bugünden geriye n gün (yeni -> eski), 'YYYY-AA-GG'."""
    bugun = date.today()
    return [(bugun - timedelta(days=i)).isoformat() for i in range(n)]


def metin(s):
    """HTML parçasını düz metne çevirir (etiketler atılır, boşluklar teke iner)."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def tarih_gg_aa_yyyy(s):
    """'07.10.2026' / '7.10.2026' / '.07.10.2026' -> '2026-10-07'; olmazsa None."""
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s or "")
    if not m:
        return None
    g, a, y = map(int, m.groups())
    try:
        return datetime(y, a, g).strftime("%Y-%m-%d")
    except ValueError:
        return None


def yaz_birlestir(klasor, il, gunler, yeni_by_gun):
    """Gün dosyalarını yazar: var olan dosyadaki kayıtlar korunur, aynı id yenisiyle değişir
    (kaynak yalnız birkaç günü gösterdiğinde geçmiş kendi dosyalarımızdan tamamlanır).
    7 günden eski dosyalar silinir; son7gun.json yazılır. Dönen: {gün: kayıt sayısı}."""
    by_gun, sayac = {}, {}
    for g in gunler:
        yol = os.path.join(klasor, f"{g}.json")
        mevcut = []
        if os.path.exists(yol):
            with open(yol, encoding="utf-8") as f:
                mevcut = json.load(f).get("kayitlar", [])
        yeni = {k["id"]: k for k in yeni_by_gun.get(g, [])}
        liste = [yeni.pop(k["id"], k) for k in mevcut] + list(yeni.values())
        by_gun[g] = liste
        sayac[g] = len(liste)
        if liste or os.path.exists(yol):
            ortak.gun_yaz(klasor, il, g, liste)
    ortak.eski_gunleri_sil(klasor, set(gunler))
    ortak.son7gun_yaz(klasor, il, gunler, by_gun)
    return sayac


def bos_kayit(il, kaynak_ad, kaynak_url, alindi):
    """Şemadaki tüm alanları null olan kayıt iskeleti."""
    k = {a: None for a in ortak.ALANLAR if a not in ("il_disi_defin", "ilce_belirsiz")}   # ikisini ortak.ilce_isle ekler
    k.update(il=il, kaynak_ad=kaynak_ad, kaynak_url=kaynak_url, alindi=alindi, ham={})
    return k
