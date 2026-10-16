# HATA TEŞHİS KILAVUZU — Kimin Cenazesi veri hattı (site sahibi kararı 16.10.2026: "hata teşhis raporu günlerimiz olsun; 3–4 günde bir ajan bu kılavuza göre iş yapsın")

Amaç: "veri çekilmiyor / çekiliyor ama uygulamaya yüklenmiyor / yükleniyor ama görünmüyor" sorusuna her seferinde AYNI yöntemle, kanıtla cevap vermek. Üç katman ayrı ayrı ölçülür; her katman için SAYI ve KANIT yazılır. Rapor sade Türkçe, ≤40 satır, `deploy/arastirma/teshis-<tarih>.md`'ye yazılır; yeni hata YURUT.md §3'e H-maddesi olarak eklenir. Ajan: Sonnet, ~60–100k token; onarım gerekirse ayrı ajan (sahibine maliyetle sorulur, §0j).

## 0. Hazırlık
- `cd cenaze-uygulamasi`; GitHub: `python3 araclar/github_api.py --durum --n 15`; canlı veri: `https://hllerdgn80-code.github.io/cenaze-veri/veri/<il>/son7gun.json` (uygulamanın okuduğu veri.kimincenazesi.com aynı içeriği verir; X-KC-Anahtar `deploy/.kc-anahtar`, UA `KiminCenazesi/…`).
- Son başarılı `topla.yml` koşusunun `birlestir` logu ve 4 `oku` logu indirilir (github_api `/actions/jobs/<id>/logs` yönlendirmesi belirteçsiz izlenir — `araclar/ci_log.py` varsa onu kullan).
- Son `topla-tr.yml` (Mac) koşuları: hangi saatlerde çalıştı, hangileri düştü/iptal.

## 1. KATMAN 1 — Veri çekiliyor mu? (kaynak → depo)
Ölçütler (her biri rapora tablo olarak):
1. **İl okuyucuları**: `oku` loglarından `[il] N kayıt, s sn[, HATA: …]` ve kaynak satırları (`[Kaynak] HATA/ENGEL/okunamadı`). Liste: HATA/ENGEL veren kaynaklar · 0 kayıt veren iller · zaman aşımı.
2. **Boş iller**: canlı `son7gun.json`'larda bugün ve dün kaydı olmayan iller (`araclar/durum.py` ya da 16.10'daki ölçüm betiği: il başına bugün/dün sayısı). 27'den fazlaysa kırmızı.
3. **e-Devlet (Mac)**: dünkü 4 yuvadan kaçı çalıştı; hizmet başına `-> N kayıt`; 3 gün üst üste 0 dönen hizmet listesi (Erzurum BŞB v3 böyle: "sonuç bulunamadı", form doğru — kaynak boş, H83). Mac uykudaysa kaçan yuvalar.
4. **Kayıt defteri (7 bölge)**: `defter: N yeni kayıt` satırı; `_mac_gerekli` ve `atlandi` nedenleri (robots/403, siklik, mac'e devredildi); Mac turunda `--yer mac` sonuçları.
5. **Sessiz kaynaklar**: `veri/_kaynak_uyari.json` (H84 bekçisi): 2 tur üst üste 0/HATA.
Kanıt örneği: "Samsun/19 Mayıs: CI zaman aşımı, Mac 0 bayt, DO 76 KB → ağ/CDN; köprüye alınmalı."

## 2. KATMAN 2 — Çekilen veri yayına giriyor mu? (depo → yayın)
1. `birlestir` logunda iç sayı vs yayın sayısı: "Yayin klasorunu hazirla" ÖNCESİ `ozet` satırları (`<İl> N`) ile yayın sonrası canlı `ozet.json` `kayit_sayisi` karşılaştırılır; fark varsa süzgeç.
2. `[süzgeç] düşen kayıt nedenleri:` satırı (H83): `yerel: tarih kaynağı yok (yayin_tarihi)` (sahibi kuralı: yalnız metinden tarih), `taze değil`, `kilit`, `isimsiz bebek`. Beklenmedik büyük sayı → `okuyucu/yayin_suz.py` kuralı gözden geçirilir.
3. `[kapı] <il>: x/y elendi {...}` satırları: K6/K10 tekrar, K2 ad biçimi, K8 uzun alan, K9 bebek; `_kapi_red.json` "yetki dışı düzeltme".
4. Yayın adımları: `upload-pages-artifact` + `deploy-pages` başarılı mı; `Cloudflare Pages'e yayimla` atlanır (secret yok; veri.kimincenazesi.com Worker'ı GitHub Pages'ten okur — normal). Canlı `guncelleme` damgası son koşudan yeni mi.
5. Görevli ilanları: `gorevli_al` → `gorevli birlestirme: N eklendi` satırı; Worker `/gorevli/<il>.json` ile canlı karşılaştırma.

## 3. KATMAN 3 — Yayındaki veri uygulamada görünüyor mu? (yayın → ekran)
1. Uygulamanın gün anahtarı `cenazeGunu` = namaz_tarihi → defin_zamani → liste_tarihi → vefat_tarihi (`lib/cekirdek/ilan.dart`). Bir ilin kayıtlarında bu alanların dağılımı (ör. Gaziantep: namaz yok, liste_tarihi dolu → "dün" sayfasında).
2. Sabah boşluğu: 08:00'de kaç ilde "bugün" kaydı var (16.10: 80 ilden 11) — kaynaklar gün içinde girer; §57 "bugün boşsa dün" kuralı çalışıyor mu.
3. Sürüm: sahibinin telefonundaki sürüm (Hakkında) ile depodaki sürüm; eski sürüm eski gün mantığı taşıyabilir.
4. Veri kapısı: `curl -H "X-KC-Anahtar: …" -A "KiminCenazesi/0.1.x" https://veri.kimincenazesi.com/veri/<il>/son7gun.json` 200 ve `guncelleme` taze mi; 403 → anahtar/UA.
5. Önbellek: uygulama 5 dk (§56/§57 sonrası); Worker `Cache-Control`.

## 4. Zaman/gecikme ölçümü
- Kaynakta görülme saati (`ilk_gorulme`, `araclar/gorulme_saati.py`) → yayın `guncelleme` → uygulama: hedef ≤ 30 dk (topla 06:17–20:47 arası 30 dk'da bir; Mac e-Devlet 06:41/10:41/14:41/18:41 + Mac açıkken 2 saatte bir; görevli ilanı anında §56).

## 5. Rapor biçimi (`deploy/arastirma/teshis-<tarih>.md`)
1. Özet (3 satır): kaç il dolu/boş, kaç kaynak bozuk, en büyük 3 sorun.
2. Katman 1/2/3 tabloları (yukarıdaki ölçütler, sayılarla).
3. Bozuk kaynak listesi: kaynak · belirti · kanıt · önerilen onarım · tahmini maliyet.
4. Kapanan kaynaklar (kalıcı: site kapalı/robots) — alternatif kaynak önerisi.
5. YURUT H-madde taslakları.
6. Sahibine tek satır: "yapılacak onarım X iş, ~Y token — onay?"

## 6. Bilinen kalıcı durumlar (tekrar raporlanmaz, yalnız değişirse)
- Erzurum: tek kaynak Uzundere (haftada ~2); e-Devlet BŞB v3 boş dönüyor (kaynak boş).
- e-Devlet yalnız Türkiye IP'si (Mac); DigitalOcean'dan açılmıyor (http 000).
- Urfanatik: Cloudflare doğrulaması (her ağdan 403) — yasak.
- Yerel basın "Son Dakika" kayıtları yayına girmez (sahibi 14.10: tarih metinden gelmeli).
- 27 ilde resmî kaynak yok (ör. Ardahan, Bayburt, Bingöl, Hakkâri, Iğdır, Kars, Tunceli, Şırnak…): din görevlisi girişi tek yol.
