#!/usr/bin/env python3
"""İstanbul: İBB'nin il geneli listesi e-Devlet'te (belediyeden izin gerekir) -> burada YALNIZ web sayfasında liste yayımlayan 2 ilçe okunur:
- Arnavutköy: `arnavutkoy.bel.tr/vefat-edenler` (list.js tablosu: ad, doğum, vefat, defin tarihi, defin zamanı, açıklama). 08.10.2026'da sayfada yalnız
  2020 tarihli örnek satırlar var (gerçek liste dolu görülmedi): pencerede 0 kayıt beklenir, "izlemede". Doğum tarihi kaydedilmez (yaş hesaplanır).
- Silivri: ana sayfadaki "Cenaze Duyuruları" sekmesi (son 10 duyuru; `/vefat-edenler` ana sayfaya yönleniyor). Duyuru: ad, cenaze tarihi, cenaze namazı camii,
  defnedilecek yer, "Ek Bilgi" metni (yalnız mahalle ve "Cenazesi ..." cümlesi alınır; araç/banka/yakın bilgisi ALINMAZ).
Kullanım: python3 okuyucu/istanbul.py [--gun 7] [--ilce Silivri]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ortak, ortak_ilce as oi

IL = "İstanbul"
ARNAVUTKOY = "https://www.arnavutkoy.bel.tr/vefat-edenler"
SILIVRI = "https://www.silivri.bel.tr/"


def arnavutkoy(ctx):
    sayfa = oi.al(ARNAVUTKOY)
    if 'id="table-list"' not in sayfa:
        raise RuntimeError("liste bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for cins, icerik in re.findall(r'<div class="view-table__header (man|woman)">([\s\S]*?)</div>\s*</li>', sayfa):
        h = [oi.metin(x) for x in re.findall(r"<div[^>]*>([\s\S]*?)</div>", icerik + "</div>")]
        if len(h) < 5:
            continue
        ad = oi.ad_duzelt(h[0])
        dogum, vef, defin = oi.tarih(h[1]), oi.tarih(h[2]), oi.tarih(h[3])
        gun = defin or vef
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        sonuc.append(oi.kayit(IL, "Arnavutköy", "istanbul-arnavutkoy", ad, gun, "Arnavutköy Belediyesi", ARNAVUTKOY, ctx["alindi"],
                              ek_id=str(vef), yas=oi.yas_hesapla(dogum, vef) if dogum and vef else None, vefat_tarihi=vef,
                              defin_zamani=defin, namaz_tarihi=defin, namaz_yeri_vakti=h[4] or None, liste_tarihi=gun, ham={}))
    return sonuc


def silivri(ctx):
    sayfa = oi.al(SILIVRI)
    adlar = re.findall(r'data-funeral-id="(\d+)">[\s\S]*?funeral-list-name">\s*([\s\S]*?)</span>', sayfa)
    if not adlar:
        raise RuntimeError("cenaze duyurusu bulunamadı (sayfa düzeni değişmiş olabilir)")
    sonuc = []
    for fid, ad in adlar:
        m = re.search(r'id="funeral-detail-' + fid + r'"[\s\S]*?(?=id="funeral-detail-|$)', sayfa)
        if not m:
            continue
        blok = m.group(0)
        d = {oi.metin(a): oi.metin(v) for a, v in re.findall(r'funeral-modal-label">([^<]*)</div>\s*<div class="funeral-modal-value">([\s\S]*?)</div>', blok)}
        ek = oi.metin((re.search(r'funeral-modal-extra-content">([\s\S]*?)</div>\s*</div>', blok) or [None, ""])[1])
        gun = oi.tarih(d.get("Cenaze Tarihi", ""))
        namaz, defin = oi.cenaze_ayikla(ek)
        ad = oi.ad_duzelt(ad)
        if not ad or not oi.pencerede(gun, ctx["gunler"]):
            continue
        camii = d.get("Cenaze Namazı Camii") or None
        k = (oi.kayit(IL, "Silivri", "istanbul-silivri", ad, gun, "Silivri Belediyesi", SILIVRI, ctx["alindi"], ek_id=fid,
                              mahalle=oi.mahalle_ayikla(ek), defin_yeri=defin or d.get("Defnedilecek Yer") or None,
                              defin_zamani=gun, namaz_tarihi=gun, namaz_yeri_vakti=namaz or camii, liste_tarihi=gun,
                              ham={"cenaze_namazi_camii": camii}))
        oi.il_disi_isle(k, ek)
        sonuc.append(k)
    return sonuc


def main():
    oi.il_calistir(IL, "istanbul", [("Arnavutköy", arnavutkoy), ("Silivri", silivri)])


if __name__ == "__main__":
    main()
