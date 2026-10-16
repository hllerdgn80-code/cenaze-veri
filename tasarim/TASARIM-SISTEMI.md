# Kimin Cenazesi — Tasarım Sistemi (Flutter'a aktarım için, 08.10.2026)

Kaynak: `prototip.html` (CSS değişkenleri birebir buradaki değerlerdir). Prototip yeniden üretimi: `python3 tasarim/prototip_yap.py` (`sablon.html` + `veri/` → `prototip.html`).

## 1. Renk (marka: L13 — kömür #25282D, altın #C9A45C, krem #F2EBDD)
| Belirteç | Koyu (varsayılan) | Açık | Flutter |
|---|---|---|---|
| zemin | #1F2226 | #F2EBDD | `scaffoldBackgroundColor` |
| yuzey (kart) | #2A2E34 | #FBF8F2 | `colorScheme.surface` |
| yuzey2 (rozet, sayaç) | #33383F | #EEE5D3 | `surfaceContainerHighest` |
| cizgi | krem %9 | kömür %10 | `outlineVariant` |
| metin | #F2EBDD | #25282D | `onSurface` |
| metin2 / metin3 | krem %70 / %46 | kömür %72 / %50 | `onSurfaceVariant` / özel |
| vurgu (dolgu) | #C9A45C | #C9A45C | `primary` |
| vurgu-metin | #D9B873 | #8A6A2C (kontrast için koyu altın) | özel `ThemeExtension` |
| vurgu-ust (altın üstü yazı) | #25282D | #25282D | `onPrimary` |
| vurgu-zemin | altın %13 | altın %18 | `primaryContainer` |
Kural: altından başka renk yok (kırmızı/yeşil/mavi yok). Gazete ilanı kartı her iki temada da kâğıt rengi (#FBF8F1) + siyah (#1B1C1E).

## 2. Tipografi (sistem yazı tipi: iOS SF Pro, Android Roboto; Flutter'da varsayılan, ek font yok; gazete ilanı serif: Georgia/Noto Serif)
| Rol | Boyut/satır | Ağırlık | Kullanım |
|---|---|---|---|
| Açılış başlığı | 30/36 | 700 | "Kimin Cenazesi" |
| Büyük başlık | 26/32 | 700, -0.4 | ekran başlığı (ortalı) |
| Kart adı | 22/28 | 650, -0.3 | merhumun adı |
| Adım başlığı | 20/26 | 650 | form |
| Liste satırı | 17/22 | 400 | il/ilçe |
| Gövde | 14–15/20 | 400 | alt bilgi |
| Kart sütunu | 13/18 | 400 | namaz/defin |
| Üst etiket | 11/13 | 600, büyük harf, +0.12em | altın etiket ("VEFAT · 5 EKİM 2026") |
| Sütun etiketi | 10/12 | 600, büyük harf, +0.12em | "CENAZE NAMAZI", "DEFİN" |
| Sekme etiketi | 10/12 | 600, -0.4 | alt çubuk |
Rakamlar `tabular-nums` (Flutter: `FontFeature.tabularFigures()`).

## 3. Boşluk ızgarası (4'ün katı)
4 · 8 · 12 · 16 · 20 · 24 · 32. Ekran yan boşluğu **20** (sol = sağ, ölçüldü); kart iç boşluğu **20**; kartlar arası **12**; şerit/sayaç hücreleri arası **6**; bölüm başlığı üstü **24**, altı **12**.

## 4. Köşe yarıçapı
Kart 20 · kutucuk 20 · düğme/alan 14 · tarih hücresi 14 · yuvarlak düğme 20 (40×40) · rozet 22 (44×44) · telefon çerçevesi 54.

## 5. Bileşen anatomisi
- **Başlık çubuğu** (her ekran): 3 sütun `40 | 1fr | 40`, sol = logo işareti ya da geri, sağ = ⋮ menü; ikisi aynı boy, aynı hiza; orta: altın üst etiket + büyük başlık. İlçe ekranında `76 | 1fr | 76` ("‹ İller" hapı ve ⋮ hapı eşit genişlik).
- **⋮ menü** (270 px): Adresi değiştir · Açık/Koyu tema · Hakkında · Gizlilik · Uygulamayı paylaş · Öneri ve tavsiyeleriniz · (prototipte) Seçimi sıfırla. Paylaş: metin kutusu + WhatsApp/Telegram/Diğer üç eşit düğme; Öneri: metin + isteğe bağlı e-posta, Vazgeç/Gönder iki eşit düğme.
- **İlan kartı** (ortalı): üstte altın etiket "CENAZE · gün · vakit" (tarih şeridindeki günle AYNI alan: cenaze günü; `prototip_yap.py` assert ile kilitler) → ad 22 px → küçük "Vefat: tarih · yaş" → "Anne X · Baba Y" → mahalle · ilçe (soluk) → ayraç → iki eşit sütun (Cenaze namazı: vakit / cami / gün · Defin: mezarlık / il dışıysa il-ilçe), ortada 1 px dikey çizgi → altta tam genişlik altın düğme "Sayfama kaydet"; kaydedilince "Sayfamda ✓" (pasif, soluk altın). Kayıt silinmez.
- **Sayaç satırları** (Sayfam): 5 eşit satır, her biri 56 yükseklik, `44 | 1fr | 44` → sol "−1" geri al (0'da pasif, sayaç 0'ın altına inmez), orta tam cümle düğmesi (+1), sağ altın daire içinde sayı. Cümle cinsiyete göre: "Merhuma / Merhumeye 1 Fâtiha okudum" (Yâsîn, dua, Kur'ân-ı Kerîm hatmi, Kelime-i Tevhid hatmi). Cinsiyet sırası: kayıttaki `cinsiyet` alanı → gömülü ad listesi (`adlar.json`, ~320 erkek + ~300 kadın adı) → bilinmiyorsa ilk dokunuşta "Merhum mu, merhume mi?" seçicisi, seçim cihazda saklanır. Altında "toplam N okuma". Kalıcı: cihaz deposu.
- **Tarih şeridi**: 7 eşit hücre (45×64), soldan sağa Bugün → 6 gün önce; seçili = altın dolgu; ilan olan günde 4 px nokta.
- **Kişi kartı** (Kaybettiklerimiz/Tarihte Bugün): ilan kartıyla aynı iskelet; sol rozet = vefat yılı, sağ rozet = yaş, orta ad + (cumhurbaşkanı/başbakanda görev sırası) + tanıtım. Kabir bilgisi yok.
- **Kutucuk**: 2 sütun eşit (169×132), tek kalan son kutucuk tam genişlik (350×132); 48 px altın halka içinde ikon + ad + sayı.
- **Ana düğme**: tam genişlik, 52 yükseklik, altın dolgu, kömür yazı; pasif = %32 opaklık.
- **Yasal uyarı kutusu**: 2 px altın çerçeve, altın %13 zemin, üçgen uyarı ikonu, "YASAL UYARI" büyük harf; kanun maddeleri kalın; altında 28 px onay kutusu; işaretlenmeden "Ödemeye geç" pasif; düğmenin üstünde küçük "Ödenecek: 200 ₺" satırı. Akış: "İlan ver" → fiyat kartı (200 ₺ tek seferlik) → 5 adım → taklit mağaza ödeme ekranı.
- **Boş durum**: 72 px daire içinde mihrap kemeri ikonu, 17 px başlık, 14 px açıklama, ortalı.
- **Alt sekme çubuğu**: 4 eşit sekme (97,5 px), 49 + 34 (ev çizgisi) = 83 yükseklik; ikon 24 + etiket 10; seçili = altın.

## 6. İkon kuralı
24×24 çizgi ikon, 1.6 çizgi kalınlığı, yuvarlak uç/birleşim, dolgu yok (yalnız "kaydedildi" işareti dolu). Flutter: `lucide_icons` ya da aynı SVG'ler `flutter_svg` ile. Bayrak, yıldız-hilal, renkli ikon, emoji yok.

## 7. Tema
Varsayılan KOYU (site sahibi kararı 08.10.2026). Kullanıcı ⋮ → Tema ile değiştirir, seçim saklanır. Flutter: `ThemeData(brightness: dark/light)` + `ThemeExtension<CvRenk>` (vurguMetin, vurguZemin, metin3, cizgi). Geçiş 250 ms.

## 8. Açılış davranışı
İlk açılışta il → ilçe sorulur, seçim saklanır. Sonraki açılışlarda doğrudan Cenaze İlanları, kayıtlı ilçe, **bugün** seçili. Adres ⋮ → "Adresi değiştir" ile düzeltilir.

## 9. Simetri kuralları (site sahibi kuralı: "tüm sayfa düzeni simetrik; yazılar, her şey simetrik")
Ölçü: 390 px genişlik, `getBoundingClientRect`; tolerans **≤ 1 px**. Denetim aracı: `tasarim/simetri_olc.js` (tarayıcıda `prototip.html` açıkken çalıştırılır; 124 durumu — iki tema, tüm ekran/panel/menü/modal/boş durum/uzun ad — gezer ve ihlal listesi döner). Flutter karşılıkları parantez içinde.
1. **Sol boşluk = sağ boşluk**: her kutunun ebeveyn içeriğine uzaklığı iki yanda eşit; ekran yan boşluğu 20/20 (`Padding(horizontal: 20)`, `Center`).
2. **Aynı satırdaki öğeler**: ilk öğenin sol uzaklığı = son öğenin sağ uzaklığı; öğeler arası boşluk eşit; aynı sınıftan öğelerin genişlik ve yüksekliği eşit (`Row` + `Expanded` / `GridView` eşit sütun). Üç öğeli satırlarda sol ve sağ öğe AYNA: aynı genişlik ve boy (40 | 1fr | 40 başlık, 44 | 1fr | 44 sayaç, 36 | 1fr | 36 liste satırı, 20 | 1fr | 20 durum kutusu, 28 | 1fr | 28 onay, 22 | 1fr | 22 menü, 20 | 1fr | 20 arama). Karşı tarafta içerik yoksa aynı ölçüde BOŞ yer tutucu (`SizedBox(width: n)`) konur; ikon kolonun tamamını doldurur, çizim ortada (`SizedBox` + `Center`).
3. **Metin hizası**: başlıklar, etiketler, düğme yazıları, girdi içi yazı ve yer tutucu, liste satırları, menü satırları, durum kutuları, ödeme satırları ORTALI (`TextAlign.center`; `TextField(textAlign: center)`; açılır alan yazısı ortalı, yerel ok işareti kaldırılmış). Simge + yazı birlikte duruyorsa grup ortalıdır ve karşı yana aynı genişlikte yer tutucu vardır (yazı kendi başına da ortada kalır).
4. **Çok satırlı gövde metni** (yasal onay metni, Hakkında, Gizlilik): `TextAlign.left` (iki yana yaslı YOK), ama kutunun sol iç boşluğu = sağ iç boşluğu (kart 20/20, uyarı kutusu 20/20). Satır sonundaki doğal dalgalanma (≤ 6 px) kural dışı sayılmaz.
5. **Alt sekme çubuğu**: 4 sekme eşit genişlik (97,5 px); her sekmede ikon ve etiket sekmenin yatay ortasında (±0).
6. **Sayaç satırı**: sol "−1" (44×44) ve sağ sayı (44×44) aynı boy, kenara 20 px; orta düğme 56 yüksek, iki yan 8 px boşlukla.
7. **Tarih şeridi**: 7 hücre eşit (45×64), aralık 6; **kutucuklar** 2 sütun eşit (169×132), tek kalan tam genişlik; **ikili form alanları** eşit iki sütun.
8. **Durum çubuğu**: sol (saat) ve sağ (pil) hücreleri 72 px eşit, kenarlara 32/32; çentik ortada.
9. **Menü ve modal**: ⋮ menüsü (270 px) ve Hakkında/Gizlilik kutusu telefonun yatay ortasında (sol = sağ); modal ayrıca dikeyde de ortalı.
10. **Başlıklar**: iki satıra inebilir, her zaman ortalı; "…" ile kesme YOK. Uzun kişi adı kartta iki satır ortalı.
11. **Boş durum**: daire + başlık + açıklama ortada; açıklama en çok 280 px.
Ölçüm sonucu (08.10.2026): ilk sürümde 24 farklı asimetri grubu (≈1010 örnek), düzeltmeden sonra tüm durumlarda 0 asimetri; yalnız bilinçli sola dayalı gövde metinleri (madde 4) listede kalır.

## 10. Verisi olmayan il ekranı ve metinler (08.10.2026)
- Bileşenler: **sakin kart** (72 px altın-zemin daire + 17 px başlık + açıklama + tam genişlik ana düğme "Cenaze ilanı paylaş"), **bildirim izni kartı** (52 px daire + soru + iki eşit 48 px düğme), **"Yakını paylaştı" rozeti** (kartın üstünde ortalı altın hap). Tarih şeridi bu ekranda gizlenir. Komşu il, Tarihte Bugün ve Kaybettiklerimiz şeritleri YOK (basitlik, §26).
- Kaynak var ama bugün boşsa: "Bugün {yer’de} cenaze ilanı bulunmuyor" + son 7 gün tarih başlıklarıyla kendiliğinden açılır.
- Bütün ekran metinleri: `METIN-SOZLUGU.md`. Simetri ölçümü: aşağıda §11.

## 11. Sekmeler, Dualar, şehit kartı (08.10.2026, 2. tur)
- **Alt sekmeler (4 eşit, 97,5 px; 16.10.2026'dan beri Tam Sayfa yok):** İlanlar · Sayfam · Dualar · Hatırla. 6 sekme ölçüldü: sekme 65 px, "Kaybettiklerimiz" etiketi 63 px (kenarda 1 px) → sığmıyor; Kaybettiklerimiz ve Tarihte Bugün "Hatırla" sekmesinde 2 eşit kutucuk. Bu iki ekranın sol üst düğmesi "Hatırla"ya geri döner; sekme vurgusu Hatırla'da kalır.
- **Dualar:** 4 eşit kutucuk (2×2, 156 px yükseklik — uzun ad iki-üç satır), her biri panel açar; kart: başlık 20 px · Arapça 22/40 serif sağdan sola ortalı · okunuş 14 italik · anlam 15/23 · kaynak 12 soluk.
- **Şehit kartı:** ilan kartıyla aynı iskelet + üstte 4 px al şerit (#E30A17, paletteki tek istisna; bayrak/ay-yıldız yok) + ortalı "ŞEHİT" hapı (al zemin, beyaz) + "Cenaze töreni" bloğu + "Ruhu şad olsun, mekânı cennet olsun." satırı. O günün listesinde en üstte.
- **Kaybettiklerimiz kartı:** liste numarası yok; sol rozet = vefat yılı (YIL), sağ = yaş; ad altında altın renkte görev sırası (yalnız "9. Cumhurbaşkanı", "20. Başbakan") + kısa tanıtım (meslek — sanatçılarda en çok 3, virgülle; diğerlerinde tek · neden tanınır; görev satırındaki kelimeyi tekrar etmez). Kabir bilgisi gösterilmez. Sıralama: cumhurbaşkanları, başbakanlar, bakanlar ve siyasetçiler vefat tarihine göre (yeniden eskiye); yalnız Sanat, Edebiyat ve Bilim tanınırlığa göre (Wikidata sitelink). Sıralama ölçütü kullanıcıya yazılmaz; üst etiket "Rahmetle anıyoruz". Kutucuk ikonları: cumhurbaşkanı/başbakan sade sütun, bakanlar mühür, siyasetçiler kürsü, "Sanat, Edebiyat ve Bilim" defne dalı (eğlence çağrışımı yok).
- Şehit formu doğrudan 1. adımla açılır; "ücretsiz" ifadesi şehit akışında geçmez.
- Simetri ölçümü: 180 durum, iki tema — 0 asimetri (yalnız §9.4'ün izinli sola dayalı gövde metinleri).
