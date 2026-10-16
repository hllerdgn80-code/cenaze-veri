#!/usr/bin/env python3
"""EZAN VAKİTLERİ — Diyanet İşleri Başkanlığı (namazvakitleri.diyanet.gov.tr; herkese açık sayfalar, kayıt gerekmez).
Sahibi 16.10.2026: "ezan vakitlerini koyalım; tümüyle Diyanet'in verileri olsun".
Akış (haftada bir, ezan.yml):
  1) /tr-TR/home/GetRegList?ChangeType=country&CountryId=2  -> Türkiye illeri (StateList)
  2) /tr-TR/home/GetRegList?ChangeType=state&CountryId=2&StateId=<il> -> il başına ilçeler (StateRegionList: IlceID, IlceAdi, IlceUrl)
  3) her ilçe sayfası (IlceUrl): "aylık" (bugünden 30 gün) + "yıllık" tablolar -> gün -> [imsak, güneş, öğle, ikindi, akşam, yatsı]
Çıktı: site/ezan/<il_slug>.json = {"il","kaynak","guncelleme","ilceler":{"<İlçe adı (bizim yazım)>": {"YYYY-AA-GG": "05:30 06:53 12:39 15:44 18:16 19:34", ...}},
       "_merkez": "<il merkezi ilçenin anahtarı>"}; yalnız bugünden itibaren GUN_SAYISI gün yazılır.
Nazik okuma: istekler arası BEKLE sn; hata veren ilçe atlanır (önceki dosyadaki değeri korunur).
Kullanım: python3 okuyucu/ezan.py [--il ordu] [--kuru]"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak  # noqa: E402

KOK = "https://namazvakitleri.diyanet.gov.tr"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
BEKLE = float(os.environ.get("EZAN_BEKLE", "1.5"))
GUN_SAYISI = 60
CIKTI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site", "ezan")
AYLAR = {"ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12}
ILCELER = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ilceler.json"), encoding="utf-8"))


def al(yol, json_mu=False):
    rq = urllib.request.Request(KOK + yol, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9",
                                                    "Accept": "application/json" if json_mu else "text/html,application/xhtml+xml",
                                                    **({"X-Requested-With": "XMLHttpRequest"} if json_mu else {})})
    with urllib.request.urlopen(rq, timeout=40) as r:
        b = r.read().decode("utf-8", "replace")
    time.sleep(BEKLE)
    if "güvenlik kurallarına" in b:
        raise RuntimeError("Diyanet güvenlik engeli")
    return json.loads(b) if json_mu else b


def gun_coz(metin):
    p = metin.strip().split()
    if len(p) < 3:
        return None
    ay = AYLAR.get(p[1].lower().replace("i̇", "i"))
    try:
        return date(int(p[2]), ay, int(p[0])).isoformat() if ay else None
    except ValueError:
        return None


def tablo_oku(sayfa):
    """Sayfadaki bütün vakit tabloları -> {gün: "hh:mm x6"}"""
    out = {}
    for t in re.findall(r"<table[\s\S]*?</table>", sayfa):
        for tr in re.findall(r"<tr[\s\S]*?</tr>", t):
            hucre = [html.unescape(re.sub(r"<[^>]+>", " ", h)).strip() for h in re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr)]
            if len(hucre) < 8:
                continue
            g = gun_coz(hucre[0])
            saat = [re.sub(r"\s+", "", x) for x in hucre[2:8]]
            if g and all(re.fullmatch(r"\d{2}:\d{2}", x) for x in saat):
                out[g] = " ".join(saat)
    return out


def bizim_il(diyanet_adi):
    k = ortak.katla(diyanet_adi)
    return next((il for il in ILCELER if not il.startswith("_") and ortak.katla(il) == k), None)


def main():
    kuru = "--kuru" in sys.argv
    tek = sys.argv[sys.argv.index("--il") + 1] if "--il" in sys.argv else None
    bugun = (datetime.now(timezone.utc) + timedelta(hours=3)).date()
    son = (bugun + timedelta(days=GUN_SAYISI)).isoformat()
    iller = al("/tr-TR/home/GetRegList?" + urllib.parse.urlencode({"ChangeType": "country", "CountryId": 2, "Culture": "tr-TR"}), True).get("StateList") or []
    print(f"Diyanet: {len(iller)} il", file=sys.stderr)
    os.makedirs(CIKTI, exist_ok=True)
    toplam_ilce = 0
    for st in iller:
        il = bizim_il(st.get("SehirAdi") or "")
        if not il or (tek and ortak.il_slug(il) != tek):
            continue
        slug = ortak.il_slug(il)
        yol = os.path.join(CIKTI, slug + ".json")
        try:
            eski = json.load(open(yol, encoding="utf-8"))
        except Exception:
            eski = {"ilceler": {}}
        try:
            ilceler = al("/tr-TR/home/GetRegList?" + urllib.parse.urlencode(
                {"ChangeType": "state", "CountryId": 2, "Culture": "tr-TR", "StateId": st["SehirID"]}), True).get("StateRegionList") or []
        except Exception as e:
            print(f"  {il}: ilçe listesi alınamadı ({e})", file=sys.stderr)
            continue
        bizim = {ortak.katla(x): x for x in (ILCELER.get(il) or [])}
        veri, merkez = {}, None
        for ic in ilceler:
            ad_d = ic.get("IlceAdi") or ""
            k = ortak.katla(ad_d)
            # Diyanet il merkezini il adıyla verir ("ANKARA", "ORDU"): bizde Merkez ya da büyükşehirde merkez ilçeler
            if k == ortak.katla(il):
                ad = "_merkez"
                merkez = "_merkez"
            else:
                ad = bizim.get(k) or ortak.tr_title(ad_d)
            try:
                vak = tablo_oku(al(ic["IlceUrl"]))
            except Exception as e:
                print(f"  {il}/{ad_d}: {e}", file=sys.stderr)
                vak = {}
            vak = {g: v for g, v in vak.items() if bugun.isoformat() <= g <= son}
            if not vak and ad in (eski.get("ilceler") or {}):
                vak = {g: v for g, v in eski["ilceler"][ad].items() if g >= bugun.isoformat()}   # hata: önceki değer korunur
            if vak:
                veri[ad] = dict(sorted(vak.items()))
        toplam_ilce += len(veri)
        out = {"il": il, "kaynak": "Diyanet İşleri Başkanlığı", "guncelleme": datetime.now(timezone(timedelta(hours=3))).isoformat(timespec="minutes"),
               "_merkez": merkez, "ilceler": veri}
        print(f"  {il}: {len(veri)}/{len(ilceler)} ilçe, {sum(len(v) for v in veri.values())} gün-satırı", file=sys.stderr)
        if not kuru and veri:
            json.dump(out, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"ezan: {toplam_ilce} ilçe yazıldı", file=sys.stderr)


if __name__ == "__main__":
    main()
