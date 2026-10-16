#!/usr/bin/env python3
"""HAVUZ BOŞALTMA KONTROLÜ (16.10.2026, sahibi: "belli aralıklarla veri havuzu kontrol edilsin ve havuzda ne var ne yok hepsi belirlediğimiz
kriterlere göre boşaltılsın"). bosalt.yml her 15 dakikada bir havuzu (iç veri önbelleği + Mac verisi + görevli/aile ilanları) yayına hazırlar;
bu betik iki şeyi yapar:
  1) DENETİM: havuzdaki (veri/<il>/son7gun.json + _ulusal.json) her kayıt, yayın kriterlerinden (yayin_suz.son7_suz: tarih uydurma yok,
     tazelik, isimsiz bebek, ad/metin kilidi) GEÇİYORSA yayında (site/veri/<il>/son7gun.json) olmalıdır. Eksik kalan kayıt ::warning olur
     ve veri/_havuz_kontrol.json'a yazılır (yayına gitmez). Kriterden geçmeyenler sayılır, nedenleriyle raporlanır.
  2) DEĞİŞİKLİK: hazırlanan yayın ile CANLI yayın il il karşılaştırılır (kayıt kimlik + alan imzası; 'guncelleme' damgası hariç).
     Fark yoksa GITHUB_OUTPUT'a degisti=0 yazılır, iş yayın yapmadan biter (Pages yayın sınırı boşuna harcanmaz).
Kullanım: python3 okuyucu/havuz_kontrol.py veri site/veri [canli_taban_url]"""
import collections, hashlib, json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak  # noqa: E402
import yayin_suz as ys  # noqa: E402

CANLI = "https://hllerdgn80-code.github.io/cenaze-veri/veri/"


def oku(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def liste(v):
    if not isinstance(v, dict):
        return []
    if "kayitlar" in v:
        return [r for r in v.get("kayitlar") or [] if isinstance(r, dict)]
    return [r for l in (v.get("ilceler") or {}).values() for r in l] + (v.get("il_disi") or []) + (v.get("ilce_belirsiz") or [])


def imza(v):
    L = sorted(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in liste(v))
    return hashlib.sha1("\n".join(L).encode()).hexdigest()


def canli_al(taban, il):
    try:
        rq = urllib.request.Request(taban + il + "/son7gun.json", headers={"User-Agent": "KiminCenazesiHavuz/1.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(rq, timeout=25) as r:
            return json.loads(r.read())
    except Exception:
        return None


def main():
    ic, yayin = sys.argv[1], sys.argv[2]
    taban = sys.argv[3] if len(sys.argv) > 3 else CANLI
    eksik, uygun, red = [], 0, collections.Counter()
    degisen = []
    for il in sorted(os.listdir(yayin)):
        yol = os.path.join(yayin, il, "son7gun.json")
        if not os.path.isfile(yol):
            continue
        site = oku(yol) or {}
        yayindaki = {(ortak.katla(r.get("ad_soyad") or ""), r.get("id")) for r in liste(site)}
        yayindaki_ad = {a for a, _ in yayindaki}
        havuz, gor = [], set()
        for f in ("son7gun.json", "_ulusal.json"):
            for r in liste(oku(os.path.join(ic, il, f))):
                a = ortak.katla(r.get("ad_soyad") or "")
                if a and a not in gor:
                    gor.add(a); havuz.append(r)
        for r in havuz:
            tek = {"il": il, "ilceler": {}, "il_disi": [], "ilce_belirsiz": [r]}
            ys.RAPOR_NEDEN.clear()
            gecti = liste(ys.son7_suz(tek))
            if not gecti:
                for n, s in ys.RAPOR_NEDEN.items():
                    red[n] += s
                continue
            uygun += 1
            if ortak.katla(r.get("ad_soyad") or "") not in yayindaki_ad:
                eksik.append({"il": il, "ad": r.get("ad_soyad"), "gun": r.get("liste_tarihi"), "kaynak_turu": r.get("kaynak_turu")})
        c = canli_al(taban, il)
        if c is None or imza(c) != imza(site):
            degisen.append(il)
    # kapı (K1-K10) havuzdaki bazı kayıtları bilerek eler (tekrar, ad biçimi): bunlar 'eksik' değil; kapi.json'daki elenen kimlikler düşülür
    elenen = set()
    for il in os.listdir(ic):
        d = oku(os.path.join(ic, il, "_kapi_red.json"))
        for x in (d.get("red") or []) if isinstance(d, dict) else []:
            if isinstance(x, dict):
                k = x.get("kayit") if isinstance(x.get("kayit"), dict) else x       # kapi.py: {"kural": [...], "kayit": {...}}
                elenen.add(ortak.katla(k.get("ad_soyad") or ""))
    eksik = [e for e in eksik if ortak.katla(e["ad"] or "") not in elenen]
    print(f"[havuz] kriterden geçen {uygun} · yayında olmayan {len(eksik)} · kriterden kalan {sum(red.values())} {dict(red)} · canlıdan farklı il {len(degisen)}")
    for e in eksik[:20]:
        print(f"::warning::HAVUZDA KALDI {e['il']}: {e['ad']} ({e['gun']}, {e['kaynak_turu']})")
    try:
        json.dump({"eksik": eksik, "kriter_disi": dict(red), "uygun": uygun, "degisen_il": degisen},
                  open(os.path.join(ic, "_havuz_kontrol.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except OSError:
        pass
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a") as f:
            f.write(f"degisti={1 if degisen else 0}\n")


if __name__ == "__main__":
    main()
