// Ekran metinleri — tasarim/METIN-SOZLUGU.md ile birebir (anahtar adları sözlükteki gibi).
// Süzgeç: pazar dili yok, ölüm sayısı yok, ünlem yok, "ücretsiz/elle/moderatör" yok, merhum/merhume kuralı.
import 'yardimci.dart';

class M {
  M._();

  // 1. Açılış ve adres seçimi
  static const acilisMarka = 'Kimin Cenazesi';
  static const acilisAlt = 'Bulunduğunuz ili seçin';
  static const ilAra = 'İl ara';
  static const ilBos = 'Bu adla bir il bulunamadı';
  static const ilceUst = 'İlçe seçin';
  static const ilceGeri = 'İller';
  static const ilceAra = 'İlçe ara';
  static const ilceTumu = 'Tüm ilçeler';
  static const ilceBos = 'Bu adla bir ilçe bulunamadı';

  // 2. Cenaze İlanları
  static const ilanlarUst = 'Cenaze İlanları';
  static const seritBugun = 'Bugün';
  static const bolumIlGeneli = 'İl geneli (ilçe belirtilmemiş)';
  static const kartNamaz = 'Cenaze namazı';
  static const kartDefin = 'Defin';
  static const kartKaydet = 'Sayfama kaydet';
  static const kartKaydedildi = 'Sayfamda ✓';
  static const kartYakini = 'Yakını paylaştı';
  static const kartKaldir = 'Sayfamdan kaldır';
  static const kaldirSoru = 'Bu kaydı sayfanızdan kaldırmak istiyor musunuz?';
  static const kaldirVazgec = 'Vazgeç';
  static const kaldirTamam = 'Kaldır';
  static const bildirimKaldirildi = 'Sayfanızdan kaldırıldı';
  static const bildirimKaydedildi = 'Sayfanıza eklendi';
  static String bosBugunBaslik(String yer) => 'Bugün ${ek(yer)} cenaze ilanı bulunmuyor';
  static const bosBugunAciklama = 'Son yedi günün cenaze ilanları aşağıda.';
  static const bosGecmisBaslik = 'Bu tarihte cenaze ilanı bulunmuyor';
  static String bosGecmisAciklama(String gun, String yer) => '${tarih(gun)} · $yer';
  static const bosIlGeneli = 'Bu tarihte ilçesi belirtilmemiş cenaze ilanı bulunmuyor.';

  // 3. Verisi olmayan il
  static String kaynaksizBaslik(String il) => '${ek(il)} cenaze ilanları şu an yakınları tarafından paylaşılıyor.';
  static const kaynaksizAciklama = 'Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra burada görünür.';
  static const kaynaksizDugme = 'Cenaze ilanı paylaş';

  // 4. Aile formu
  static const aileBaslik = 'Cenaze İlanı';
  static const aileUstGiris = 'Cenaze bilgisi paylaşımı';
  static const aileGirisBaslik = 'Cenaze ilanı paylaşın';
  static String aileGirisAciklama(String il) =>
      'Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra $il sayfasında görünür.';
  static const aileGirisEtiket = 'Yakınlar için';
  static const aileGirisNot = 'Yalnız vefat edenin yakınları paylaşabilir';
  static const aileMadde1 = 'Ölüm belgesi e-Devlet koduyla doğrulanır';
  static const aileMadde3 = 'Kontrolden sonra il ve ilçe sayfasında görünür';
  static const aileMadde4 = 'Belge dosyası saklanmaz';
  static const aileNot = 'İlanınız kontrolden sonra yayımlanır.';
  static const aileBittiUst = 'Gönderildi';
  static const aileBittiDugme = 'Tamam';
  // v0.1 eki (METIN-SOZLUGU §16): gönderim kullanıcının e-posta uygulamasında tamamlanır
  static const aileEpostaNot = 'Gönderimi e-posta uygulamanızda tamamlayabilirsiniz.';

  // 5. Ortak form metinleri
  static const adim1Baslik = 'Vefat eden yakınınızın bilgileri';
  static const adim1Aciklama = 'Bilgiler ilanda göründüğü biçimde yayımlanır.';
  static const alanCinsiyet = 'Vefat eden';
  static const erkek = 'Erkek';
  static const kadin = 'Kadın';
  static const alanAd = 'Ad soyad';
  static String alanAdYer(String? c) =>
      c == 'e' ? 'Merhumun adı ve soyadı' : (c == 'k' ? 'Merhumenin adı ve soyadı' : 'Adı ve soyadı');
  static const alanVefat = 'Vefat tarihi';
  static const alanNamaz = 'Namaz vakti';
  static const namazSecenek = ['Öğle namazı', 'İkindi namazı', 'Cuma namazı', 'Saat belirt'];
  static const alanIl = 'İl';
  static const alanIlce = 'İlçe';
  static const alanMahalle = 'Mahalle';
  static const alanMahalleYer = 'Mahallesi';
  static const alanCami = 'Cami';
  static const alanCamiYer = 'Cenaze namazının kılınacağı cami';
  static const alanMezarlik = 'Mezarlık';
  static const alanMezarlikYer = 'Defin yeri';
  static const adim2Baslik = 'Ölüm belgesi doğrulama';
  static const adim2Aciklama = 'e-Devlet’ten aldığınız Ölüm Belgesi’nin doğrulama kodunu girin. Belge dosyası saklanmaz.';
  static const adim2Alan = 'Belge doğrulama kodu';
  static const adim2AlanYer = 'Örn. ABCD-1234-EFGH';
  static const adim3Baslik = 'Telefon doğrulama';
  static const adim3Ad = 'Ad soyad';
  static const adim3AdYer = 'Adınız ve soyadınız';
  static const adim3Tc = 'T.C. son 4 hane';
  static const adim3Yakinlik = 'Yakınlık';
  static const yakinlikSecenek = ['Oğlu / kızı', 'Eşi', 'Kardeşi', 'Torunu', 'Gelini / damadı', 'Diğer'];
  static const adim3Tel = 'Cep telefonu';
  static const adim3TelYer = '05xx xxx xx xx';
  static const adim5Baslik = 'Yasal beyan';
  static const adim5Aciklama = 'Lütfen aşağıdaki metni okuyun.';
  static const hukukBaslik = 'YASAL UYARI — Yanlış beyanın cezai sorumluluğu vardır';
  static const hukukMetin =
      'Verdiğim bilgilerin doğru ve eksiksiz olduğunu, ilanı vermeye yetkili yakın olduğumu kabul ve beyan ederim. '
      'Yanıltıcı, gerçek dışı veya başkasının hakkını ihlal eden bilgi vermem hâlinde 5237 sayılı Türk Ceza Kanunu’nun '
      'ilgili hükümleri (m. 206 resmî belgenin düzenlenmesinde yalan beyan, m. 267 iftira, m. 136 kişisel verileri '
      'hukuka aykırı olarak verme) uyarınca hakkımda hukuki ve cezai işlem başlatılmasını, ilanın derhal kaldırılmasını '
      've hesabımın kalıcı olarak kapatılmasını kabul ediyorum.';
  static const hukukKutu = 'Okudum, kabul ediyorum.';
  static const sonDugme = 'Onayla ve gönder';
  static const formDevam = 'Devam';

  // 6. Tam Sayfa
  static const tamUst = 'Türkiye geneli';
  static const tamBaslik = 'Tam Sayfa';
  static const tamOrnek = 'ÖRNEK';
  // v0.1 eki (METIN-SOZLUGU §16): ücretli ilan ilk sürümde kapalı (URUN-TASLAGI §28)
  static const tamYakinda = 'Tam sayfa vefat ilanları yakında';
  static const fiyatAciklama = 'Gazetedeki vefat ilanının uygulamadaki karşılığı.';

  // 7. Sayfam
  static const sayfamUst = 'Rahmetle anıyoruz';
  static const sayfamBaslik = 'Sayfam';
  static const sayfamBosBaslik = 'Sayfanızda henüz kimse yok';
  static const sayfamBosAciklama =
      'Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez.';
  static const sayacGeri = 'Geri al';
  static const cinsSoru = 'Merhum mu, merhume mi?';
  static const cinsMerhum = 'Merhum';
  static const cinsMerhume = 'Merhume';
  static String sayacToplam(int n) => 'Okuduklarınızın toplamı: $n';

  // 8. Hatırla
  static const hatirlaUst = 'Rahmetle anıyoruz';
  static const hatirlaBaslik = 'Hatırla';
  static const kayBaslik = 'Kaybettiklerimiz';
  static const tbBaslik = 'Tarihte Bugün';
  static const kayAra = 'Ad ara';
  static const kayBos = 'Bu adla bir kayıt bulunamadı';
  static const kayDaha = 'Devamını gösterin';
  static String tbUst(String gun) => '${tarih(gun, kisa: true)} · hayatını kaybedenler';
  static const tbTurkiye = 'Türkiye';
  static const tbDunya = 'Dünya';
  // v0.1 eki (METIN-SOZLUGU §16)
  static const tbHazirlaniyor = 'Bugün için liste hazırlanıyor';
  static const kayKategoriler = [
    ['cumhurbaskanlari', 'Cumhurbaşkanları'],
    ['basbakanlar', 'Başbakanlar'],
    ['bakanlar', 'Bakanlar'],
    ['siyasetciler', 'Siyasetçiler'],
    ['sanatcilar', 'Sanat, Edebiyat ve Bilim'],
  ];

  // 8b. Dualar
  static const duaSekme = 'Dualar';
  static const duaUst = 'Rahmetle anıyoruz';
  static const duaBaslik = 'Dualar ve Âyetler';
  static const duaTumu = 'Tümü';
  static const duaMerhumIcin = 'Merhum için';
  static const duaMerhumeIcin = 'Merhume için';

  // 8c. Şehit
  static const sehitEtiket = 'ŞEHİT';
  static const sehitToren = 'Cenaze töreni';
  static const sehitKapanis = 'Ruhu şad olsun, mekânı cennet olsun.';
  static const sehitBolum = 'Şehidimiz';

  // 9. Menü, Hakkında, Gizlilik
  static const menuAdres = 'Adresi değiştir';
  static const menuAcikTema = 'Açık tema';
  static const menuKoyuTema = 'Koyu tema';
  static const menuHakkinda = 'Hakkında';
  static const menuGizlilik = 'Gizlilik';
  static const menuPaylas = 'Uygulamayı paylaş';
  static const menuOneri = 'Öneri ve tavsiyeleriniz';
  static const magazaBaglanti = 'https://play.google.com/store/apps/details?id=com.kimincenazesi.app';
  static const paylasMetin = 'Kimin Cenazesi — il ve ilçenizdeki cenaze ilanları. Play Store: $magazaBaglanti';
  static const oneriBaslik = 'Öneri ve tavsiyeleriniz';
  static const oneriMesaj = 'Mesajınız';
  static const oneriMesajYer = 'Görüşünüzü yazın';
  static const oneriEposta = 'E-posta (isteğe bağlı)';
  static const oneriEpostaYer = 'ornek@eposta.com';
  static const oneriVazgec = 'Vazgeç';
  static const oneriGonder = 'Gönder';
  static const oneriTamamBaslik = 'Teşekkür ederiz';
  static const oneriTamamDugme = 'Tamam';
  static const hakkindaBaslik = 'Kimin Cenazesi';
  static const hakkindaMetin =
      'İl ve ilçenizdeki cenaze ilanlarını her gün bir arada gösterir. Sayfanıza eklediğiniz bilgiler silinmez. Sürüm 0.1';
  static const gizlilikBaslik = 'Gizlilik';
  static const gizlilikMetin =
      'Seçtiğiniz adres ve Sayfanıza eklediğiniz bilgiler yalnız bu cihazda tutulur. Konum izni istenmez, uygulamada reklam yoktur.';
  static const modalKapat = 'Tamam';
  static const iletisimEposta = 'iletisim@kimincenazesi.com';

  // 11. Hata ve uyarı
  static const hataBaglanti = 'Bağlantı kurulamadı. İlanlar bağlantı gelince yenilenir.';
  static const hataVeri = 'Cenaze ilanları şu an yüklenemedi. Biraz sonra yeniden deneyin.';
  static const hataTekrar = 'Yeniden deneyin';
  static String bilgiGuncelleme(String saat) => 'Son güncelleme $saat';

  // 12. Alt sekmeler
  static const sekmeler = ['İlanlar', 'Tam Sayfa', 'Sayfam', 'Dualar', 'Hatırla'];
}
