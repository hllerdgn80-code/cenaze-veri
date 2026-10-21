# KİMİN CENAZESİ — GÜVENLİK DUVARI KILAVUZU (sahibi kararı 21.10.2026: "onay/müdahale gerektirmeyen 10 somut adım yaz, hepsini kendin uygula")

Amaç: canlı sistemin (Cloudflare Worker'lar, kimincenazesi.com, herkese açık GitHub deposu `cenaze-veri`, Play uygulaması) önüne, sahibinin parolası/paneli/2FA'sı gerekmeden kurulabilen katmanlar örmek. Her madde: **NE · NEDEN · NASIL (komut) · NASIL DOĞRULANIR**. Hepsi geri alınabilir (her Worker için `.bak-2110` dosyası + `deploy/yedek/worker-*.txt` canlı kod yedeği). Veri silme yok; Play/track değişikliği yok.

Canlı sistem haritası (21.10.2026):
| Parça | Adres | Kaynak | Not |
|---|---|---|---|
| Site (Pages) | kimincenazesi.com, www | `site/` | statik; `_headers` ile başlıklar |
| `kimincenazesi-test-katil` | kimincenazesi.com/test* | `deploy/test-katil/` | testçi katılım sayfası + bakım uçları (x-gizli) |
| `kimincenazesi-indir` | kimincenazesi.com/indir/* | `sunucu/indir/` | APK (KV `DOSYA`) |
| `kimincenazesi-veri-kapisi` | veri.kimincenazesi.com/* | `deploy/veri-kapisi/` | uygulamanın veri kapısı (anahtar + UA + hız sınırı + yol listesi) |
| `kimincenazesi-aile` | kimincenazesi-aile.tr-kopru.workers.dev | `deploy/aile-worker/` | aile ilanı, din görevlisi paneli, ödeme (KV `AILE`) |
| `tr-kopru` | kopru.whitehallminute.com | `sunucu/tr-kopru/` | TR belediye siteleri için ağ köprüsü (CI kullanır) |
| `arapca-test-sayfa` | kimincenazesi.com/arapca*, /islamkadini* | (başka proje) | **dokunulmadı** |

Ortak komutlar (hepsi `/Users/halil/Desktop/model-arastirmasi` altından):
```bash
R=/Users/halil/Desktop/model-arastirmasi
# Worker dağıtımı (örnek: test-katil)
cd $R/haber-motoru/tools/deploy && PATH=$R/haber-motoru/tools/node/bin:$PATH XDG_CONFIG_HOME=$R/haber-motoru/.cf WRANGLER_SEND_METRICS=false CI=1 \
  ./node_modules/.bin/wrangler deploy --config $R/cenaze-uygulamasi/deploy/test-katil/wrangler.toml
# Birim testleri
cd $R/cenaze-uygulamasi/deploy/aile-worker && PATH=$R/haber-motoru/tools/node/bin:$PATH node --test test/*.test.js     # 72
cd $R/cenaze-uygulamasi/deploy/test-katil  && PATH=$R/haber-motoru/tools/node/bin:$PATH node --test test/*.test.js     # 10
cd $R/cenaze-uygulamasi/deploy/veri-kapisi && PATH=$R/haber-motoru/tools/node/bin:$PATH node --test test/*.test.js     # 13
# Tek bakışta canlı güvenlik kontrolü
python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py
```
Geri alma (bir Worker bozulursa): `cp <worker>/src/index.js.bak-2110 <worker>/src/index.js` (aile: `gorevli.js.bak-2110` de; `guvenlik.js` kalsa zararsız) → yukarıdaki `wrangler deploy` → `guvenlik_nobeti.py`.

---

## 1. Worker yanıtlarına güvenlik başlıkları
**NE:** 5 Worker'ın yanıtlarına `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Content-Security-Policy` (API'lerde `default-src 'none'; frame-ancestors 'none'`; `/test` sayfasında satır içi stil/betik izinli ama ağ bağlantısı, harici betik, form, çerçeve yok), `Strict-Transport-Security: max-age=31536000`, `Permissions-Policy`.
**NEDEN:** tıklama-hırsızlığı (sayfayı çerçeveye gömüp tıklatma), MIME karıştırma ve HTTPS düşürme saldırılarını tarayıcı katmanında keser; hata yanıtları dahil her yanıt aynı korumayı taşır. (Veri kapısının hata yanıtları kasıtlı olarak boş ve başlıksız kalır; yalnız başarılı JSON başlık alır.)
**NASIL:** `aile-worker/src/guvenlik.js` (`GUVENLIK_BASLIK`) + `index.js` `yanit()`; `test-katil/src/index.js` (`GUVENLIK`, `CSP_SAYFA`, `CSP_API`, `html()`, `json()`, `yonlendir()`); `veri-kapisi/src/index.js` başarılı yanıt; `sunucu/indir/src/index.js`; `sunucu/tr-kopru/src/index.js` (`nosniff`). Dağıtım: ortak komut.
**DOĞRULA:** `python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py --sessiz` → grup `[A]` satırlarında BULGU yok. Elle: `curl -sI https://kimincenazesi.com/indir/kimin-cenazesi.apk` (nosniff, x-frame-options, CSP, HSTS görünür); `curl -s https://kimincenazesi.com/test` hâlâ sayfayı döndürür.

## 2. Site (Pages) başlıkları, robots.txt, security.txt
**NE:** `site/_headers`: aynı başlıklar + `Permissions-Policy` + site CSP'si (`default-src 'self'`, yalnız Cloudflare Web Analytics betiği ve bağlantısı ek izinli, `frame-ancestors 'none'`); `ayarlar.json`, `surum.json`, `ezan/*` için `X-Robots-Tag: noindex`. `site/robots.txt`: `/test`, `/indir/`, `/aile/`, `/gorevli/`, `/ezan/`, `/ayarlar.json`, `/surum.json` kapalı; toplayıcı/SEO botları (Semrush, Ahrefs, MJ12, DotBot, BLEXBot, DataForSEO, PetalBot, Bytespider) tümüyle kapalı. `site/.well-known/security.txt` (RFC 9116; iletişim: iletisim@kimincenazesi.com).
**NEDEN:** siteyi çerçeveye gömme/yanlış içerik yükleme saldırısını keser; uygulama yapılandırma dosyaları aramada çıkmaz; güvenlik araştırmacısı bulgu bildireceği adresi bulur. robots.txt yalnız nazik botları durdurur; gerçek engelleme için bkz. madde 6.
**NASIL:** dosyaları düzenle → `bash cenaze-uygulamasi/araclar/site_yayinla.sh` (yayın öncesi yedek dosyalarını siteden çıkarır ve `gizli_tara.py --klasor site` çalıştırır; sır varsa yayın durur). `*.bak-*` dosyaları `deploy/yedek/site-bak/` içine taşınır.
**DOĞRULA:** `curl -sI https://kimincenazesi.com/ | grep -i -E "x-frame|content-security|strict"`; `curl -s https://kimincenazesi.com/robots.txt | head`; tarayıcıda ana sayfa açılır, konsolda CSP ihlali yok; `/gizlilik/`, `/logo.svg`, `/stil.css` 200.

## 3. Gizli uçlar: sabit-zaman karşılaştırma + hatalı-deneme kilidi
**NE:** `x-gizli` ile korunan bakım uçlarında (`/test/{sayim,liste,uyeler,grup}`, `POST /test/toplu`; aile `/aile/durum`, `/aile/odemeler`, `/gorevli/{karar,liste,capraz}`) ve köprüde (`X-Kopru-Anahtar`) anahtar karşılaştırması **sabit zamanlı** (bayt bayt `XOR`, uzunluk farkı da sabit sürede). Aynı IP'den 10 dakikada 10 yanlış anahtar → IP 10 dakika kilitlenir (429; doğru anahtar da o IP'den reddedilir).
**NEDEN:** `!==` karşılaştırması zamanlama farkıyla anahtarı sızdırabilir; kilit kaba kuvveti ve Worker kotasını yakmayı durdurur. Anahtarlar zaten uzun rastgele değerlerdir; bu katman ikinci duvardır.
**NASIL:** `test-katil`: `esit()`, `gizliMi()`, `hataliGizli()`, `kilitliMi()`; `aile-worker`: `guvenlik.js` (`kilitliMi`, `basarisizKaydet`) + `index.js` `GIZLI_YOLLAR`; `tr-kopru`: `esit()`. Sayaç Worker bellekte tutulur (KV yazma kotasını harcamaz; en iyi çaba).
**DOĞRULA:** birim testleri (aile 72, test-katil 10); canlı: `curl -s -o /dev/null -w "%{http_code}\n" https://kimincenazesi.com/test/sayim` → 403; `guvenlik_nobeti.py` `[B]` satırları OK.

## 4. Girdi doğrulama ve gövde boyutu sınırı
**NE:** İstek gövdesi **`Content-Length` ön kontrolü + akış sınırlı okuma** (sınır aşılırsa gövde belleğe alınmaz, 413): aile 4 KB (liste yükleme 8 MB, görevli kodu 2 KB — mevcut sınırlar korunur), test-katil `/test/katil` 4 KB (kimlik jetonu ≤ 3500 karakter), `/test/toplu` 16 KB; köprü POST 1 MB. `/test/toplu` e-posta listesi: yalnız `kullanici@alan.uzanti` biçimi, ≤ 254 karakter; geçersiz adres Directory API yoluna **hiç girmez** (yol enjeksiyonu yok). Aile'de mevcut sıkı doğrulamalar (`girdiTemizle`, `^[0-9a-f]{16}$` kimlikleri, `purchase_token` deseni) korunur.
**NEDEN:** büyük/bozuk gövdeyle bellek ve CPU yakmayı, e-posta alanıyla API yolu manipülasyonunu önler.
**NASIL:** `aile-worker/src/guvenlik.js` `sinirliMetin()` (index.js `govdeOku`, gorevli.js `govde`); `test-katil` `govdeJson()`, `EPOSTA`; `tr-kopru` içerik uzunluğu kontrolü.
**DOĞRULA:** `curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" --data "{\"x\":\"$(head -c 5000 /dev/zero | tr '\0' a)\"}" https://kimincenazesi-aile.tr-kopru.workers.dev/aile/basvur` → 413; bozuk JSON → 400; `guvenlik_nobeti.py` `[C]` OK.

## 5. Hata gövdelerinde iç bilgi sızdırmama (genel yakalayıcı)
**NE:** Her Worker'da en dışta `try/catch`: beklenmeyen hata → yanıtta yalnız `{"hata":"sunucu_hatasi"}` (500) / köprüde "kopru hatasi" (502) / indirmede "Geçici hata" (503); ayrıntı yalnız Cloudflare günlüğüne (`console.error`). `test-katil` Google'ın hata metnini (`ayrinti`) artık dışarı vermez; `/test/geri` sayfasındaki yansıyan değerler HTML-kaçışlı (XSS yok).
**NEDEN:** yığın izi, kütüphane/Google hata metni, KV anahtar adı gibi iç bilgi saldırgana yol gösterir.
**NASIL:** `aile index.js default.fetch`; `test-katil default.fetch → isle()`; `indir`, `tr-kopru` try/catch.
**DOĞRULA:** `curl -s -X POST -d '{bozuk' https://kimincenazesi-aile.tr-kopru.workers.dev/aile/basvur` → `{"hata":"geçersiz JSON"}` (iz yok); birim testleri "beklenmeyen hata" senaryosu; `guvenlik_nobeti.py` `[C]` OK.

## 6. Oran sınırı (Worker içi) — Cloudflare WAF kuralı yerine
**NE:** Mevcut katmanlar korunur ve eksikler tamamlanır: veri kapısı IP başına 60/dk (Durable Object sayacı — kesin); aile POST uçları IP başına 10/saat (KV) + yeniden gönderme 60 sn; **yeni:** `test-katil` `/test/katil`, `/test/yonetici`, `/test/geri` IP başına 20/dk (429), bakım uçlarında hatalı-deneme kilidi (madde 3).
**NEDEN:** SMS/Google çağrısı yapan ve KV yazan uçları tek IP'nin kötüye kullanmasını (maliyet ve kota) sınırlar. Sayaçlar Worker belleğindedir: aynı konumdaki istekler için etkili, küresel kesin değil.
**NASIL:** `test-katil` `sinirAsildi(anahtar, limit, pencereMs)`.
**DOĞRULA:** birim testi (`/test/katil` 22. istek 429); `guvenlik_nobeti.py` `[F]` istek patlaması izleme (madde 10).
**NOT (uygulanamayan kısım):** bölge düzeyinde Cloudflare WAF/oran sınırlama kuralı `cf_api.py` ile **kurulamaz**: elimizdeki belirteçlerin kapsamı yok (API belirteci yalnız DNS düzenler; wrangler OAuth zone ayarı/WAF kapsamı vermez — 21.10.2026 canlı denendi: `rulesets` ve `settings` uçları 403). Sahibinin ileride isteyeceği tek seferlik adım: Cloudflare → API Tokens → "Zone · WAF · Edit" (+ "Zone Settings · Edit") ekli yeni belirteç → `haber-motoru/.cf/api-token`. Bu kılavuzun kapsamı DIŞINDADIR; onsuz da Worker içi sınırlar yukarıdaki gibi çalışır.

## 7. Yedek: KV + Worker kodu + açık depo
**NE:** `araclar/kv_yedek.py`: (1) KV `AILE` (test üyeleri, görevli hesapları, ilanlar; `test:yonetici` DEĞERİ yazılmaz) → `deploy/yedek/kv-AILE-<tarih>.json.gz`; (2) 5 canlı Worker'ın dağıtılmış kodu → `worker-<ad>-<tarih>.txt`; (3) açık depo `main` tarball → `depo-<tarih>.tar.gz`. Saklama: KV ve Worker 14, depo 4 adet. Klasör 700, dosyalar 600, `.gitignore`'da (depoya GİRMEZ). Mac açıkken günde 1 kez kendiliğinden (madde 10, `mac_tetik.py`).
**NEDEN:** KV'deki aile/görevli kayıtları Cloudflare'in dışında hiçbir yerde durmaz; Worker'a yanlış kod yayımlanırsa eski paket elde olsun.
**NASIL:** `python3 cenaze-uygulamasi/araclar/kv_yedek.py` (`--kv`, `--worker`, `--depo`, `--dogrula`, `--yas`). **Geri yükleme (KV):** yedek JSON'u aç; her anahtar için `wrangler kv key put --namespace-id 3cc1bbb1855648208fa5c40ddaf8368f "<anahtar>" "<deger>" [--expiration <unix>]` (komut `haber-motoru/tools/deploy` içinden; yukarıdaki ortak ortamla). **Worker geri alma:** `worker-*.txt` çok parçalı pakettir; kolay yol `*.bak-2110` + `wrangler deploy`.
**DOĞRULA:** `python3 cenaze-uygulamasi/araclar/kv_yedek.py --dogrula` (yedekteki anahtar sayısı canlıyla uyuşur) ve `--yas` (≤ 36 saat); `ls -l cenaze-uygulamasi/deploy/yedek` (modlar `-rw-------`).

## 8. Gizli dosya / sır taraması + yükleme kapısı + .gitignore
**NE:** GitHub deposu **herkese açıktır** (github.io yayını): oraya giren tek sır herkesin olur. (a) `araclar/gizli_tara.py`: yerel gizli dosyalar (`.oauth-gizli`, `.anahtar`, `.github-token`, `*.jks` …) `.gitignore` ile kapalı mı ve modu 600/700 mü (`--duzelt` sıkılaştırır); açık depo ağacında yasaklı dosya adı; **383 metin dosyasının içinde** sır desenleri (AIza, ghp_, github_pat_, PRIVATE KEY, GOCSPX, cfut_, re_…, JWT, `anahtar = '…'`) ve **yerel sır değerlerinin açık depoda geçip geçmediği** (değer yazdırılmaz); depo geçmişinde yasaklı dosya adı. (b) **Yükleme kapısı:** `github_api.py` (`--klasor-yukle`, `--yaz`, `--dosyalar`) her dosyayı göndermeden önce aynı kuralları uygular; sır ya da yasaklı ad varsa **hiçbir şey yüklenmeden durur**. `site_yayinla.sh` de Pages'e göndermeden önce `--klasor site` tarar. (c) `.gitignore` tamamlandı (`.parola-anahtari`, `.resend*`, `.anahtar`, `*.jks`, `deploy/yedek/` …).
**NEDEN:** `deploy/aile-worker/` klasörünü yükleyen bir komut `.panel-anahtari`, `.parola-anahtari`, `.resend` dosyalarını açık depoya koyabilirdi; artık kapı bunu engeller.
**NASIL:** `python3 cenaze-uygulamasi/araclar/gizli_tara.py` (hepsi; `--yerel`, `--uzak` ~90 sn, `--gecmis`, `--klasor <dizin>`).
**DOĞRULA:** çıkış kodu 0 ve "0 bulgu"; kapı testi: sahte `.oauth-gizli` içeren klasörü `github_api.py --klasor-yukle` ile göndermeyi dene → "GIZLI DOSYA KAPISI … DURDURULDU" (ağa hiç gidilmez).

## 9. Belirteç/izin denetimi (en az yetki)
**NE:** Her turda: wrangler OAuth geçerli mi; GitHub belirteci erişebildiği depo sayısı + bitiş tarihi; Cloudflare `api-token` aktif mi ve kapsamı dar mı (yalnız DNS + zone okuma; Worker/KV/WAF yazamaz); gizli dosya ve klasör modları (`deploy/imza/` 700, anahtar dosyaları 600 — bu turda 9 dosya/klasör sıkılaştırıldı). Kapsam tablosu:
| Belirteç | Yapabildiği | Gerekçe / not |
|---|---|---|
| `haber-motoru/.cf/api-token` | DNS düzenle, zone/hesap okuma | Worker/KV/WAF/ayar **yazamaz** (21.10 doğrulandı) |
| wrangler OAuth | Worker, KV, Pages, rota, analitik GraphQL | DNS/WAF yok; süresi doldukça kendini yeniler (H18) |
| `deploy/.github-token` | `cenaze-veri` Actions/Contents/Secrets/Workflows RW | **UYARI:** belirteç 5 depoya erişiyor (içinde özel `arapca-uygulama`); en az yetki için sahibi tek seferde yalnız `cenaze-veri` seçili yeni ince taneli belirteç üretebilir (zorunlu değil; bitiş 2027-01-12) |
| `deploy/.play/service-account.json` | Play yayın API'si | yerel, modu 600/700 |
| Worker sırları | `OAUTH_GIZLI`, `PANEL_ANAHTARI`, `IP_TUZ`, `PAROLA_ANAHTARI`, `RESEND_ANAHTARI`, `KC_ANAHTAR`, `ANAHTAR` | Worker ortamında; yerel kopya yalnız ilgili `.gizli`/`.anahtar` dosyasında (600) |
**NEDEN:** sızan belirteç ne kadar çok şey yapabiliyorsa zarar o kadar büyük; kapsamı bilmek ve izlemek ilk adımdır.
**NASIL:** `python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py` `[E]` grubu; `python3 cenaze-uygulamasi/araclar/gizli_tara.py --yerel --duzelt`.
**DOĞRULA:** `[E]` satırlarında BULGU yok; `stat -f "%Sp %N" cenaze-uygulamasi/deploy/imza cenaze-uygulamasi/deploy/imza/*` → `drwx------` / `-rw-------`.

## 10. Güvenlik nöbeti + istek patlaması alarmı
**NE:** `araclar/guvenlik_nobeti.py` canlı sistemi dışarıdan sınar (≈ 40 kontrol, 2-3 dk): başlıklar (madde 1–2), gizli uçlar anahtarsız 403 (madde 3), bozuk/büyük gövde ve kötü Origin (madde 4–5), robots/SPF/TLS bitişi, belirteç (madde 9), yedek yaşı (madde 7), ve **istek patlaması**: Cloudflare GraphQL'den site ve her Worker için son tam saatin isteği, son ~3 günün saatlik medyanının 8 katını ve 400'ü aşarsa ALARM; Worker hata oranı > %5, günlük istek > 50.000 (ücretsiz plan 100.000) uyarısı. Sonuç `deploy/guvenlik-nobeti.json`; `durum.py` aynı dosyayı okur. **Kendiliğinden:** `mac_tetik.py` (LaunchAgent, 10 dk) Mac açıkken 3 saatte bir nöbeti, günde bir `--tam` (açık depo sır taraması + geçmiş) ve KV yedeğini çalıştırır; BULGU olursa **macOS bildirimi** gelir ("Kimin Cenazesi GUVENLIK ALARMI").
**NEDEN:** sonradan eklenen bir kod ya da yanlış dağıtım başlığı/sırrı sessizce bozabilir; bir bot ya da saldırı fark edilmeden kota bitirebilir.
**NASIL:** `python3 cenaze-uygulamasi/araclar/guvenlik_nobeti.py [--tam] [--bildir] [--sessiz]`; `python3 cenaze-uygulamasi/araclar/durum.py` ("güvenlik nöbeti" satırı). Sunucudaki bekçiye (DigitalOcean) eklemek için sahibinin SSH adımı gerekir; bu yüzden alarm kanalı olarak Mac bildirimi + `durum.py` ❌ satırı seçildi.
**DOĞRULA:** çıktıda `ozet: N OK, 0 BULGU`; `cat cenaze-uygulamasi/araclar/mac_tetik.log | tail` içinde "GUVENLIK" satırları; kasıtlı deneme: `guvenlik_nobeti.py` içinde eşik değeri geçici düşürülürse BULGU + bildirim gelir.

---

## YAPILMAYAN / SINIR (dürüst liste)
- Bölge düzeyinde Cloudflare WAF/oran sınırlama kuralı ve bölge ayarları (HSTS preload, TLS minimum sürümü): belirteç kapsamı yok → madde 6 notu.
- GitHub belirtecinin tek depoya daraltılması ve Workspace hesabı/DMARC sıkılaştırması (`p=quarantine`): sahibinin paneli/hesabı gerekir; Workspace 29.10.2026'da iptal edilince DMARC eklenecek (bugün Workspace gönderimi DKIM-hizalı olmadığından `p=none` bile yarar sağlamıyor, eklenmedi).
- Sunucudaki (DigitalOcean) bekçiye güvenlik betiği: SSH gerekir; Mac bildirimi seçildi.
