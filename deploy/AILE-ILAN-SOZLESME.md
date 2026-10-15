# Aile ilanı hattı — sözleşme (Fable, 14.10.2026; site sahibi kararı: §15 önerisi 1–4 onaylandı)

Amaç: kaynağı olmayan il/ilçede cenaze sahibi ilanı KENDİ verir; makine kuralları geçerse ilan HEMEN yayına girer ("Yakını paylaştı" rozeti), 2 bildirimde kendiliğinden gizlenir; sahibi haftalık gününde bakar. e-Devlet barkodu İSTEĞE BAĞLI (verilirse "doğrulandı" rozeti). TC istenmez. Doğrulama TELEFON koduyla (15.10.2026; e-posta alanı kalktı): kod WhatsApp doğrulama şablonuyla, olmazsa Netgsm SMS ile gider (`src/dogrulama.js`).

## Parçalar
1. **Sunucu:** Cloudflare Worker + KV (`deploy/aile-worker/`): başvuru alır, telefona kod gönderir (WhatsApp şablonu → Netgsm; ikisi de yoksa `GELISTIRME=1` modunda kodu yanıtta döner — üretimde ASLA), kuralları çalıştırır, yayındaki ilanları il bazında JSON verir, bildirim alır.
2. **Veri hattı:** `okuyucu/aile_al.py` her turda 81 ilin `GET /aile/<il_slug>.json` çıktısını `veri/<il>/_ulusal.json` biçiminde yazar (kayıt şeması `ortak.ALANLAR` + `aile: true`, `kaynak_ad: "aile"`, `kaynak_url: <worker>`); `ulusal_birlestir.py` katar; `kapi.py` K7 için `aile` kaynak adı/alan adı kaydı; `yayin_suz.py` `aile` alanını zaten yayına açık tutuyor.
3. **Uygulama:** form Worker'a POST eder (e-posta taslağı yolu kalkar); kod ekranı; sonuç ekranı; boş gün/kaynaksız ekranında bağlantı EN ÜSTTE; kartlarda "Bildir".

## Uç noktalar (JSON, UTF-8, CORS: yalnız uygulama; hız sınırı IP başına 10/saat)
- `POST /aile/basvur` → `{il, ilce, mahalle?, ad_soyad, cinsiyet("e"|"k"), yas?, vefat_tarihi(YYYY-AA-GG), namaz_tarihi, namaz_yeri_vakti?, defin_yeri?, basvuran:{ad_soyad, telefon(+90 / 10 hane), yakinlik}, beyan:true, edevlet_kodu?}` → `{basvuru_id, dogrulama:"eposta"}` (6 haneli kod telefona, 15 dk geçerli, 3 deneme).
- `POST /aile/dogrula` → `{basvuru_id, kod}` → `{durum:"yayinda"|"red", neden?, ilan_id}`.
- `GET /aile/<il_slug>.json` → `{il, kayitlar:[{id, il, ilce, mahalle, ad_soyad, cinsiyet, yas, vefat_tarihi, namaz_tarihi, namaz_yeri_vakti, defin_yeri, liste_tarihi, aile:true, dogrulandi:bool}], guncelleme}` — yalnız `yayinda`, son 7 gün; başvuran bilgisi ve e-posta ASLA çıkmaz.
- `POST /aile/bildir` → `{ilan_id, neden}` → `{alindi:true}`; 2 farklı IP'den bildirimde ilan `gizli`.
- `GET /aile/durum` → sayılar (il başına yayında/gizli/red) — yalnız panel.

## Kurallar (makine; biri tutmazsa `red` + neden)
K1 il `uygulama/assets/veri/ilceler.json`'da; ilçe o ilin listesinde ("Merkez" kabul). K2 ad 2–5 sözcük, rakam/URL/@ yok; başvuran adı da aynı. K3 vefat_tarihi ≤ namaz_tarihi ≤ vefat+3 gün; namaz_tarihi ≥ bugün−1 ve ≤ bugün+3. K4 `okuyucu/mezarlik_ilce.json`'da mezarlık varsa ve ilçesi tekse ilan ilçesiyle aynı olmalı (farklıysa red: "mezarlık başka ilçede"). K5 aynı il + aynı ad (normalize) + ±3 gün → ikinci ilan red ("zaten var"). K6 telefon başına 7 günde en çok 2 ilan; IP başına saatte 10 istek. K7 beyan:true şart (metin §17). K8 ölüm nedeni, telefon, adres, TC alanı YOK; serbest metin alanı YOK (yalnız sabit alanlar, ≤60 karakter). K9 e-Devlet kodu verildiyse biçim denetimi + `dogrulandi:true` (sahibi haftalık turda turkiye.gov.tr "Belge Doğrulama"da bakar; yanlışsa gizler).

## Saklama (KVKK)
KV'de: ilan alanları, başvuran ad + telefon (yalnız doğrulama/K6 için; JSON çıktısında ASLA yok), yakınlık, IP özeti (sha256), zaman. 30 gün sonra başvuran bilgisi silinir, ilan kalır. Hiçbir yerde ölüm nedeni/TC/telefon yok.

## Sahibine düşenler (tek sefer)
Resend hesabı (ücretsiz) + `kimincenazesi.com` için DNS doğrulama kayıtları; Cloudflare belirtecinde Workers+KV izni (yoksa yeni belirteç). Bunlar gelene dek Worker `GELISTIRME=1` ile çalışır (kod yanıtta döner; yalnız test).


## Değişiklikler (15.10.2026)
- **Telefon doğrulaması:** `POST /aile/basvur` gövdesinde `basvuran.telefon` (e-posta kalktı); kod telefona gider; `POST /aile/dogrula` aynı. K6 telefon başına 7 günde 2 ilan. Yanıt: `{basvuru_id, dogrulama:"telefon", kanal:"whatsapp"|"sms"}` (GELISTIRME=1 ve kanal yokken `gelistirme_kodu`). Üretimde en az bir kanal yoksa 503 `dogrulama_servisi_yok`. Telefon halka açık JSON'da, panel çıktılarında ve kuyrukta ASLA görünmez.
- **Şehit ilanı:** `POST /aile/basvur` gövdesinde `sehit:true` REDDEDİLİR (400 "şehit ilanı yalnız din görevlisi"). Şehit ilanı yalnız `POST /gorevli/ilan` ile (`sehit:true`, `rutbe` zorunlu, `toren_yeri` ve `duyuru_url` (https) isteğe bağlı); halka açık kayıtta `sehit, rutbe, toren` çıkar, duyuru bağlantısı çıkmaz. Din görevlisi uç noktaları: `src/gorevli.js` (başlığındaki KV haritası).
