# VERBİS ve kayıt yükümlülüğü

Hukuki danışmanlık değildir. Kaynak: KVKK duyurusu — Kurul'un 04.09.2025 tarihli ve 2025/1572 sayılı Kararı (2018/87'yi değiştirir), yayım 12.01.2026 (https://www.kvkk.gov.tr/Icerik/8577/kisisel-verileri-koruma-kurulunun-04-09-2025-tarihli-ve-2025-1572-sayili-kararinin-uygulama-esaslarina-iliskin-kamuoyu-duyurusu).

## 1. Eşik (KVKK sayfasında okunan)

- Kural: tüm veri sorumluları Veri Sorumluları Siciline (VERBİS) kayıt olur; Kurul kararla istisna getirir (https://www.kvkk.gov.tr/Icerik/2044/Veri-Sorumlulugu-Siciline-Kayit-Istisnalari).
- **İstisna 1:** gerçek ya da tüzel kişi; yıllık çalışan sayısı **50'den az VE** yıllık mali bilanço toplamı **100 milyon TL'den az**; ana faaliyet konusu özel nitelikli kişisel veri işleme **olmayan**.
- **İstisna 2:** ana faaliyeti özel nitelikli veri işlemek olan; çalışan **10'dan az VE** bilanço **10 milyon TL'den az**.
- Bilanço esasına göre defter tutanlarda iki ölçüt birlikte; **bilanço esasına göre defter tutmayanlarda yalnız çalışan sayısı** (Kurul'un 25.12.2025 tarihli 2025/2393 sayılı Kararı).
- Bir hukuk bürosu yazısı 16.06.2026 tarihli (RG 33282) yeni bir değişiklikten söz ediyor; **içeriğini doğrulayamadım** → yayından önce sahibi kvkk.gov.tr "Duyurular"dan güncel eşiği teyit eder.

## 2. Bizim durumumuz (varsayım: şirketsiz gerçek kişi veya yeni küçük Ltd.)

- Çalışan: 0. Bilanço: yok/çok küçük. Ana faaliyet: cenaze ilanı bilgilendirmesi ve ilan hizmeti (kullanıcıların md.6 türünde — din, sağlık, biyometrik — verisini işlemiyoruz; bkz. `veri-envanteri.md` not 3).
- **Sonuç: kural olarak VERBİS kaydından istisnadır.** Üç varsayım bozulursa değişir: (a) KVKK, ana faaliyeti "özel nitelikli veri" sayarsa (din görevlisi/cenaze işi bunu doğurmaz diye okuyorum ama hukukçu teyidi iyi olur); (b) çalışan/bilanço eşik üstü (bugün uzak); (c) güncel karar eşiği değiştirmişse (yukarıdaki not).
- İstisna olmak **yükümlülükten kurtarmaz**: aydınlatma (md.10), veri güvenliği tedbirleri (md.12), ilgili kişi taleplerine 30 gün, silme/yok etme yükümlülükleri geçerlidir. Saklama ve imha politikası yazma yükümlülüğü yalnız kayıtlı veri sorumlularındadır ama kayıtsız olanlar da silme sürelerine uyar: veri sorumlusu politika hazırlamıyorsa yükümlülük doğduktan sonra **3 ay** içinde silme yapılır (Yönetmelik md.11/3, md.5/3).

## 3. Sizde bekleyen (5 satır)

1. **Veri sorumlusunun adı/unvanı ve tebligat adresi**: aydınlatma metni ve gizlilik sayfasına yazılacak (Tebliğ md.4 kimliği ister; Play'de yasal ad zaten görünür — URUN-TASLAGI §18 ile uyumlu karar verin).
2. **Güncel VERBİS eşiğini** kvkk.gov.tr "Duyurular"da bir kez teyit edin (2025/1572 + 2025/2393 + olası 06.2026 değişikliği); sonucu bu dosyaya tarihle yazın.
3. **Yurt dışı aktarım**: Cloudflare (ve açılırsa Meta/WhatsApp) için Kanun md.9'a göre güvence (Kurul'un standart sözleşmesi imzalanır, **imzadan sonra 5 iş günü içinde Kurum'a bildirilir** — kvkk.gov.tr/Icerik/8170); olmuyorsa ya da hukukçuya gitmek istemezseniz RAPOR §2'deki ucuz alternatif.
4. **Ödeme kaydı saklama süresi** (Play siparişleri, vergi/muhasebe): muhasebeciden teyit; Worker'da `od:`/`pt:` için süre konur.
5. **Canlı ortam sertleştirme**: `wrangler.toml → GELISTIRME`'yi kaldırın, `PANEL_ANAHTARI`, `IP_TUZ`, `KC_ANAHTAR`, Netgsm/WA secret'larını tanımlayın (RAPOR §1/5).

---
**Dayanılan resmî belgeler:** yukarıdaki KVKK duyurusu (8577) ve sayfası (2044); Silme Yönetmeliği md.5, md.11: https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK ; Standart sözleşme duyurusu: https://www.kvkk.gov.tr/Icerik/8170/Yurt-Disina-Kisisel-Veri-Aktariminda-Kullanilacak-Standart-Sozlesmelerde-Dikkat-Edilmesi-Gereken-Hususlara-Iliskin-Kamuoyu-Duyurusu
