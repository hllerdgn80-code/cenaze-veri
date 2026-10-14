# Ulusal toplayıcı siteler ve özel cenaze firmaları (14.10.2026, URUN-TASLAGI §35 sıra 2)

Yöntem: WebSearch (zayıf; çoğunlukla yerel basın çıktı) + ~60 tahmini alan adı yoklaması (curl, ortak UA) + robots/ana sayfa/il sayfası okuma. Tüm istekler herkese açık sayfalara; CAPTCHA/giriş/403 görülmedi, dolanma yok. Kişi adı yazılmadı.

## Tablo

| Site | Tür | Kapsam / güncellik | Alanlar | Erişim (robots) | Karar |
|---|---|---|---|---|---|
| **cenazeilanlari.com.tr** | ücretsiz ilan sitesi (aile/muhtar + yönetim girişi; kısmen otomatik üretilmiş) | 81 il sayfası; taze (13.10.2026): Ankara, İzmir, Trabzon, Samsun, Gümüşhane, Rize, Bayburt (07.10), İstanbul (09.10). Günlük ulusal ~130 ilan (id farkı 3 günde ~400). Sitemap'te kişi başına URL | liste kartı: ad, yaş (çoğu 0=bilinmiyor), il, ilçe, tarih; detay: mezarlık, cami, defin tarihi (detay açılmadı) | robots: yalnız /yonetim/ yasak; CAPTCHA/giriş yok | **OKUYUCU YAZILDI** `okuyucu/cenazeilanlari.py` |
| cenazeilan.com | toplayıcı (resmî belediye verisinin aynası) | "Bugün 14 Ekim: 403 vefat"; il sayfaları: Afyon, Bursa, Konya, İzmir, Gaziantep, Kocaeli, Elazığ, Rize, Çankırı, Eskişehir (0 kayıt), Yalova (0) | ad, yaş, il/ilçe, namaz vakti, cami, mezarlık, "Resmî Kaynak" | robots: Allow, /admin /data /logs yasak | Okuyucu YAZILMADI: aynı iller zaten resmî kaynaktan okunuyor, yeni il yok; belediye kaynağı düşerse ÇAPRAZ YEDEK adayı (sayfa başı 40 kayıt) |
| etaziye.com | dijital taziye/ilan platformu (Next.js) | 96.801 ilan ama en yeni vefat tarihi 28.04.2026 (6 ay bayat); /api yasak | ad, il, ilçe, vefat tarihi, açıklama | robots: /api /admin yasak | Kullanılamaz (bayat); aylık yeniden bak |
| vefatilanlari.org | aile girişli ilan | ana sayfa "son eklenen" 2023 | ad, yaş, il/ilçe, metin | 200, robots yok | Ölü, kaynak değil |
| vefatilani.com, vefatilan.com.tr, hurriyetilan.com.tr/bugunku-vefat-ilanlari, yitik.com, postagazeteilan.net | gazete ilan ajansı | bugünkü gazete ilanları GÖRÜNTÜ (jpg/webp); en yeni sayfa Eylül 2026 | yok (resim) | açık | Okunamaz (OCR + gazete telifi); kaynak değil |
| olumhaberi.com | ölüm haberi/forum | genel içerik, günlük liste yok | - | açık | Kaynak değil |
| cenazenakil.com, ozelcenazehizmetleri.com | özel cenaze/nakil firması vitrini | statik tanıtım; günlük vefat listesi YOK | - | açık | Kaynak değil. Firma sitelerinde liste yayımlama yok; ilan verenler aileler/belediyeler |
| bassagligi.com, vefatedenler.com | başsağlığı / ünlü vefat | ünlü vefat arşivi | - | - | Kaynak değil |
| Arama motoru çıktıları: kayserihaber, gazetekale (Kırıkkale), urfadegisim (Adıyaman), habergo (Nevşehir), superkanaltv (İnegöl), urfanatik | yerel basın | günlük liste | ad, yer | - | Toplayıcı değil, yerel basın (H41 hattında zaten aranır; Adıyaman/Kırıkkale/Nevşehir için aday olarak not) |

Denenen ve yok çıkan adlar (DNS/boş): vefatlarimiz.com, cenaze.com.tr, dijitalmezar.com, olumilani.com, cenazeilani.com, vefat.com.tr ve ~40 benzeri.

## 16 boş il ve İstanbul/İzmir kapsamı (cenazeilanlari.com.tr il sayfaları, 14.10)
| İl | Sitedeki durum |
|---|---|
| Bayburt | canlı: 06.10, 07.10 (haftada ~1); 3 günlük pencerede 0 |
| Ağrı | yalnız TEST kaydı ("... TEST", metin "test amaçlı") + eski 2022-2023; elenir |
| Ardahan, Bingöl, Bitlis, Eskişehir, Hakkâri, Kırklareli, Mardin, Muş, Siirt, Diyarbakır, Yozgat | son güncelleme 2022-2025, taze kayıt yok |
| Iğdır (son 07.2026), Şırnak (03.2026), Tunceli (06.2026) | seyrek, bayat |
| İzmir | taze (13.10) ama resmî kaynağımız var |
| İstanbul | son kayıt 09.10, 3 günlük pencerede 0 |
| Samsun, Gümüşhane | 1 ve 2 kayıt/3 gün (Gümüşhane'de mevcut veri 0 -> yeni kazanç) |
| Trabzon | 30 kayıt/3 gün (ilk sayfa); mevcut veri 08.10'dan beri bayat -> asıl kazanç |
| Rize | 3 kayıt/3 gün |
Sonuç: 16 boş ilden yalnız Bayburt'ta (haftalık ~1) taze veri; Gümüşhane/Samsun/Trabzon/Rize'de küçük artış. Beklenen etki: ~35 kayıt/3 gün (öncelik listesindeki 25 ilde). Ulusal çözüm değil.

## Okuyucu (cenazeilanlari.py) — teknik özet
- Kalıp vefatilan.py'nin aynısı: `veri/<il>/_ulusal.json`, kayıt şeması `ortak.ALANLAR`, `kaynak_turu="yerel_basin"`, `ham.tarih_kaynagi="ilan_vefat_tarihi"`, `kaynak_ad="cenazeilanlari.com.tr"`.
- İstek: `GET /cenazeilanlari/<il>` (o ilin en yeni 30 ilanı); hız 3,6 sn; günlük tavan 40, koşu başına 12, il başına günde 1 ziyaret (durum `veri/_cenazeilanlari_durum.json`); öncelik 25 il (H41 listesi + İstanbul, Samsun, Trabzon, Gümüşhane, Rize). 81 ili her gün gezmek 81 istek eder (>40), kapsam dışı.
- Alınan: ad, yaş (0 ise boş), il, ilçe (yalnız ilin gerçek ilçesi). Alınmayan: ilan metni, anne-baba, mahalle, yayıncı, dua sayaçları. Detay sayfası açılmaz (istek bütçesi).
- Süzgeçler: ad içinde "test"/"deneme" -> atla (Ağrı'da 2 test kaydı yakalandı); 2-5 sözcük; kartın ili sayfanın iliyle uyuşmalı; ileri tarihli kayıt (yarından sonrası) alınmaz.
- Testler (--kuru, canlı sayfa): Bayburt 30 kart/0 pencere, Ağrı 30/0 (2 test elendi), Samsun 1, Gümüşhane 2, Hakkâri 14/0, Trabzon 30, İstanbul 0, Rize 3. Trabzon'da 30 kaydın 30'u mevcut veride yok; Samsun 1/1, Gümüşhane 2/2 yeni. 10 örnek gözle: ad biçimi (2-3 sözcük), ilçe gerçek ilçe listesinde, tarih 11-13.10; yaş 0 (bilinmiyor) hâlinde boş.
- **kapi kaydı (sahibi ekler):** `YEREL_BASIN` içine `"cenazeilanlari.com.tr": "cenazeilanlari.com.tr"`. topla.yml'e `python3 okuyucu/cenazeilanlari.py` (ulusal_birlestir'den ÖNCE). Ortak dosyalara dokunulmadı. Yerel basın yayın kilidi: kayıt `ilan_vefat_tarihi` penceresinden (bugün-6..bugün) geçer; ad+il+ilçe+tarih yeterli, mezarlık/cami yok.

## Riskler / dürüst notlar
1. Kaynak güvenilirliği orta: ilan metni şablonlu ve hatalı ("Trabzon İli İlkadım İlçesi" - Samsun kaydında; Bayburt kaydında "Trabzon İli Bayburt İlçesi"). İl bilgisi ayrı alandan alınıyor ama doğruluğu bağımsız doğrulanamadı. Ağrı'da canlı sitede test kaydı var -> aile-girişli kayıtlar denetimsiz. Önerim: bu kaynağı yalnız bu 25 ilde ve yalnız resmî kaynağı olmayan illerde kullanmak (kod zaten öncelik listesiyle sınırlı).
2. Kart tarihi = ilandaki "Defin Tarihi" (3 detay sayfasında vefat günüyle aynı). Vefat günü ayrıca doğrulanamaz; yayın penceresi 7 günlük kaldığı için etkisi küçük.
3. 8 Ekim kararı (Play hesabı riski, `yayin_suz.YEREL_ILLER`): bu kaynak "yerel basın" sınıfındadır, o koruma aynen işler; kararı sahibi verir.
4. Site istek yükü: bugünkü araştırma (~70 istek) tek seferlik; okuyucu günde ≤25 istek.

## Sonraki aday (bu turda bakılmadı)
Yerel basın aday listesi: Adıyaman (urfadegisim günlük defin listesi), Kırıkkale (gazetekale + belediye), Nevşehir (habergo), İnegöl (superkanaltv). Bunlar toplayıcı değil, H41 hattına eklenecek yerel basın.
