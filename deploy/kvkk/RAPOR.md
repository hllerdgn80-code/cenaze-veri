# KVKK paketi — rapor (15.10.2026)

Hukuki danışmanlık değildir. Tembih listesine ve CLAUDE.md §0k'ya uydum (haber maddeleri bu işe uymaz; ilgili ilkeler: kaynağa sadık kal, uydurma yok, beyan = fiil, kaynaksız söz yok). Kod ve Worker'a dokunulmadı, GitHub'a yüklenmedi, sır yazılmadı.

## Alternatif yol (§0k)
1. **Gerçek ihtiyaç:** kimliği ve yetkiyi bir kez doğrulamak; veriyi mümkün olduğunca hiç toplamamak.
2. **Piyasa yolu ve maliyeti:** kimlik fotoğrafını bulut yapay zekâ servisine göndermek (Cloudflare Workers AI) → yurt dışı aktarım (md.9) için standart sözleşme + Kurum bildirimi, açık rıza, saklama/silme altyapısı, hukukçu masrafı.
3. **Ucuz alternatif:** telefondaki ML Kit metin tanıma kartı ZATEN okuyor (karartma için). İbare/ad/unvan kontrolü cihazda yapılıp sunucuya fotoğraf yerine yalnız "geçti/kaldı + puan" gönderilirse fotoğraf hiç sunucuya çıkmaz: yurt dışı aktarım, açık rıza, 7 günlük saklama ve "saklanmaz" cümlesindeki istisna ORTADAN KALKAR; maliyet sıfır. Bedeli: istemci kontrolü sahtelenebilir → sahtecilik riski telefon kodu + müftülük listesi + 7 gün gözetim + "Bildir" ile karşılanır; doğrulanamayanlar için fotoğraf yalnız KULLANICI İSTERSE gönderilir (rıza onunla birlikte). Önerim bu; ürün kararı sahibinin.

## Dayanılan resmî belgeler (açılan/okunanlar)
- Aydınlatma Tebliği RG 10.03.2018/30356 (md.4 asgari içerik, md.5 usul — okundu): resmigazete.gov.tr/eskiler/2018/03/20180310-5.htm
- Veri Sorumlusuna Başvuru Tebliği (md.4–5 — okundu): …/20180310-6.htm
- KVKK Açık Rıza, Aydınlatma Yükümlülüğü, İlgili Kişinin Hakları, Silme/Yok Etme Yönetmeliği (md.5–12 — okundu), 7499 sayılı Kanun md.6/md.9 (RG 12.03.2024 — okundu), VERBİS istisna duyurusu 8577 (okundu), Kurul karar özeti 2019/273 (ölen kişi), Google Play Data safety ve hesap silme sayfaları (okundu).
- **Açılamayan/okunamayan:** Kanun md.5/2 bent metni ve md.12 doğrudan (kvkk.gov.tr'nin ilgili sayfaları PDF/eksik döndü; bent harfleri ve işleme şartları arama özetine ve genel bilgiye dayanır → sahibi/hukukçu mevzuat.gov.tr'den teyit eder); Yurt Dışına Aktarım Rehberi (yalnız başlık/arama özeti); 2026 VERBİS değişikliği (içeriği doğrulanamadı).

## 1. Ürün gerçeğiyle çelişen / eksik bulduğum noktalar
1. **Gizlilik sayfası ve Play formu eskimiş:** `gizlilik.html` "ad, telefon yok; kamera/bildirim izni yok; hiçbir veri sunucuya gitmez" diyor; `PLAY-STORE-PAKETI.md §C2` "toplanan veri yok". 0.1.5/0.1.6'da: telefon, ad, kart fotoğrafı, ödeme kaydı sunucuya gidiyor; POST_NOTIFICATIONS + BILLING izinleri var. Yeni `gizlilik.html` ve `play-veri-guvenligi-cevaplari.md` bunu düzeltir. Mağaza uzun açıklamasındaki "hesap açmanız gerekmez / konum izni istenmez" cümlesi de güncellenmeli.
2. **"Fotoğraf saklanmaz" cümlesi koşulsuz, kod koşullu:** kamera ekranı (`metin.dart:356-357`) mutlak söylüyor; Worker iki başarısız denemede fotoğrafı 7 gün KV'de tutuyor. Önerilen cümle `acik-riza-din-gorevlisi.md §3`'te.
3. **Sahibi uç noktaları kimliksiz açık olabilir:** `wrangler.toml [vars] GELISTIRME="1"` → `PANEL_ANAHTARI` yoksa `/gorevli/kuyruk` (kart fotoğrafı dahil), `/aile/odemeler` korumasız; kod yanıtta döner. Canlıya çıkmadan kaldırılmalı (md.12 veri güvenliği).
4. **IP özeti tuzu sabit:** `IP_TUZ` tanımlı değilse "aile" → özet kolay geri çözülür. Din görevlisi hesabındaki `ip` alanı hiç silinmiyor (Tam Sayfa'da 30 gün var). Telefon düz metin ve `sha256(telefon)` anahtarları anonim değil.
5. **Silme yolu yok:** kullanıcı kendi hesabını silemiyor; onaylı hesap TTL'siz. Play "hesap oluşturan uygulama" şartı (uygulama içi + web silme bağlantısı) karşılanmıyor. Öneri: `silme-talebi.md`.
6. **Ödeme kayıtları süresiz** (`od:`, `pt:`): süre teyidi gerekli.
7. **Üçüncü kişi verisi:** müftülük personel listesi (`gorevli:liste:*`, ad+cami) başvuranlar dışındaki kişilerin verisi; aydınlatma yükümlülüğü ayrıca değerlendirilmeli. (§37 ek-12 listelerin kaldırıldığını söylüyor; yüklü değilse sorun yok.)
8. **Yurt dışı aktarım (md.9, 01.06.2024'ten beri):** düzenli aktarım için açık rıza yetmez; uygun güvence (ör. Kurul standart sözleşmesi, imzadan sonra 5 iş günü içinde Kurum'a bildirim) gerekir. Cloudflare/Meta bunu şimdilik kapsamıyor → yukarıdaki cihaz-içi alternatif ya da sözleşme.
9. **Açık rıza ilkesi:** Kurum, rıza dışı hukuki sebep varken rızaya dayanmayı "aldatıcı" sayıyor; bu yüzden rızayı yalnız kart fotoğrafının yurt dışı bulutta işlenmesine bağladım, kaydı 5/2-c ve 5/2-f'ye oturttum. Rıza kaydı için hesap kaydında alan yok (`riza_kart_tarih`, `riza_surum` önerisi).
10. **Veri sorumlusu kimliği:** Tebliğ md.4 kimliği ister; URUN-TASLAGI §18 "adım hiçbir yerde geçmesin" diyor. Play bireysel hesapta yasal adı zaten gösterir. Şirket (Ltd.) kurulmadan metne ad yazmak gerekir; bu sahibinin kararı.
11. **İletişim e-postası tutarsız:** uygulamada `iletisim@kimincenazesi.com` (`metin.dart:303`, mağaza paketi), yeni metinlerde `yonetici@kimincenazesi.com`. Biri seçilip her yerde aynı yapılmalı.
12. **TC "görünmez" vaadi** cihaz-içi örtmenin başarısına bağlı (başarısızsa fotoğraf gitmez → vaat doğru kalır); kuyruk yolunda sahibine giden fotoğraf da örtülü. Örtülmemiş sicil/doğum tarihi vb. kartta kalabilir; kartta başka alan varsa görüntü işlenmeden gönderilir.
13. **Vefat edenin verisi:** Kurul'a göre (2019/273) ölen kişi "ilgili kişi" değil; ama yakınların verisi doğabilir → metinde ilan kaldırma talebi her zaman değerlendirilir denildi. Bu, ürün kararıdır; Worker'da sahibi için "ilan kaldır" uç noktası yok (öneri `silme-talebi.md §4`).

## 2. Ana oturumun uygulamaya koyacağı satırlar
- `uygulama/web/gizlilik.html` ← `deploy/kvkk/gizlilik.html` (yer tutucuları doldurduktan sonra); `kimincenazesi.com/gizlilik` ve github.io yedeği; Play'deki gizlilik URL'si aynı kalır.
- `metin.dart`: `izinAydinlatma` satırı (bildirim-izni-metni.md); kart ekranı cümlesi + ikinci onay kutusu (rıza metni) + kutu işaretlenmeden kamera düğmesi pasif; `gizlilikMetin` (satır 300) yeni özetle değiştirilmeli.
- Worker: `GELISTIRME` kaldır, `PANEL_ANAHTARI`/`IP_TUZ` secret; din görevlisi `ip` alanı için süre; `hesap-sil` + `silme-iste/onay` + `ilan-kaldir` + `basvuran-sil`; `od:`/`pt:` süresi; `riza_*` alanı.
- Play Console: Veri güvenliği formu (`play-veri-guvenligi-cevaplari.md`), hesap silme bağlantısı, IARC "dijital satın alma: evet", mağaza metni (hesap/konum cümlesi).
- Aydınlatma metnindeki "Hesabı sil" ve web silme cümlesi, uç noktalar yayına girene dek METİNDEN ÇIKARILIR (beyan = fiil); `gizlilik.html`'de köşeli parantezle işaretlendi.

## 3. Sahibine kalan (tek satır)
Veri sorumlusu adı/adresi · Cloudflare/Meta güvence kararı (cihaz-içi alternatif mi, sözleşme mi) · ödeme kaydı saklama süresi · güncel VERBİS eşiği teyidi · e-posta adresinin tekleştirilmesi · hukukçuya 1 saatlik göz (özellikle md.9 ve vefat eden verisi).
