// Ekran metinleri — tasarim/METIN-SOZLUGU.md ile birebir (anahtar adları sözlükteki gibi).
// Süzgeç: pazar dili yok, ölüm sayısı yok, ünlem yok, "ücretsiz/elle/moderatör" yok, merhum/merhume kuralı.
import 'yardimci.dart';

/// Site sahibi 14.10.2026: prototipteki Tam Sayfa akışı yayında olsun (fiyat kartı, "Ödemeye geç", ödeme ekranı).
/// Gerçek tahsilat (Play Billing) sonraki iş; şimdilik ödeme ekranı prototip görünümüyle gelir.
const bool odemeAcik = true;

/// 0.1.4 (URUN-TASLAGI §36, site sahibi 15.10.2026): günlük cenaze bildirimi açık; ilk açılışta tek kart sorar.
const bool bildirimTeklifiAcik = true;

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
  // §21/1: ilanları ilçe vermeyen kaynakta (ör. Gaziantep) ilanlar zaten "İl geneli"dir; parantezli açıklama gerekmez
  static const bolumIlGenelSade = 'İl geneli';
  // §21/2: kullanıcının ilçesinde bugün ilan yoksa ilde bugün okunan ilçeler ("Muğla’da bugün: Bodrum, Fethiye, Milas…")
  static String digerIlcelerBaslik(String il, List<String> ilceler, {bool devami = false}) =>
      '${ek(il)} bugün: ${ilceler.join(', ')}${devami ? '…' : ''}';
  static const kartNamaz = 'Cenaze namazı';
  static const kartDefin = 'Defin';
  static const kartKaydet = 'Sayfama kaydet';
  static const kartKaydedildi = 'Sayfamda ✓';
  static const kartYakini = 'Yakını paylaştı';
  static const kartGorevli = 'Mahallenin din görevlisi paylaştı'; // 0.1.5 (§37)
  static const kartDogrulandi = 'Doğrulandı';
  static const kartBebek = 'Bebek'; // §32: adı olan bebek kaydında rozet
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
  static const kaynaksizAciklama = 'Yakınların ya da bölgenizdeki din görevlisinin paylaştığı ilanlar burada görünür.';
  static const kaynaksizDugme = 'Cenaze ilanı paylaş';
  static const kaynaksizBugun = 'Bugün';
  static const izinSoru = 'Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?';
  static const izinEvet = 'Evet, haber verin';
  static const izinHayir = 'Şimdi değil';
  static const izinEvetBildirim = 'Bölgenizdeki cenazeler için sabahları haber vereceğiz';
  static const izinHayirBildirim = 'Bildirim gönderilmeyecek';
  static const izinVerilmedi = 'Bildirim izni verilmedi. Telefonunuzun ayarlarından açabilirsiniz.';
  static const menuBildirimAc = 'Cenaze bildirimini aç';
  static const menuBildirimKapat = 'Cenaze bildirimini kapat';
  // Bugün ilan yoksa kartın hemen altı (14.10.2026 sahibi: bağlantı en üstte)
  static const aileDavetMetin = 'Yakınınızın cenaze bilgilerini siz paylaşabilirsiniz';
  static const aileDavetDugme = 'Cenaze bilgilerini paylaş';
  static const ilanVerAciklama = 'Aradığınız ilan burada yoksa, yakınınızın ilanını siz de paylaşabilirsiniz.';

  // 4. Aile formu
  static const aileBaslik = 'Cenaze İlanı';
  static const aileUstGiris = 'Cenaze bilgisi paylaşımı';
  static const aileGirisBaslik = 'Cenaze ilanı paylaşın';
  static String aileGirisAciklama(String il) =>
      'Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra bulunduğunuz il veya ilçenin sayfasında görünür.';
  static const aileGirisEtiket = 'Yakınlar için';
  static const aileGirisNot = 'Yalnız vefat edenin yakınları paylaşabilir';
  static const aileMadde1 = 'e-Devlet belge kodu isteğe bağlıdır';
  static const aileMadde3 = 'Bilgiler kurallardan geçince ilan il ve ilçe sayfasında görünür.';
  static const aileMadde4 = 'Belge dosyası saklanmaz';
  static const aileNot = 'İlanınız kurallardan geçtiğinde yayımlanır.';
  static const aileBittiUst = 'Gönderildi';
  static const aileBittiDugme = 'Tamam';
  static const aileBittiBaslik = 'İlanınız alındı';
  static String aileBittiAciklama(String il) => 'İlan kontrolden sonra bulunduğunuz il veya ilçenin sayfasında yayımlanır. Başınız sağ olsun.';
  // Şehit akışı (METIN-SOZLUGU sehit.*): ücret ifadesi hiçbir yerde geçmez
  static const sehitFormBaslik = 'Şehit İlanı';
  static const sehitAdim1 = 'Şehidimizin bilgileri';
  static const sehitAdimDuyuru = 'Resmî duyuru doğrulaması';
  static const sehitRutbe = 'Rütbe / unvan';
  static const sehitRutbeYer = 'Ör. Piyade Uzman Çavuş';
  static const sehitAdYer = 'Şehidimizin adı ve soyadı';
  static const sehitTorenYeri = 'Cenaze töreni yeri';
  static const sehitTorenYer = 'Tören yapılacak yer';
  static const sehitMezarlikYer = 'Şehitlik';
  static const sehitDuyuruAciklama =
      'Valilik, Emniyet, Jandarma ya da Türk Silahlı Kuvvetleri duyurusunun bağlantısını girin. İlan bu duyuruyla karşılaştırılır.';
  static const sehitDuyuruAlan = 'Resmî duyuru bağlantısı';
  static const sehitDuyuruYer = 'Duyurunun internet adresi';
  static const sehitDuyuruDugme = 'Duyuruyu doğrula';
  static const sehitDuyuruTamam = 'Duyuru doğrulandı';
  static const sehitBittiYazi = 'İlan kontrolden sonra Tam Sayfa’da yayımlanır. Şehidimizin ruhu şad olsun.';
  static const sehitNot = 'İlanınız kontrolden sonra yayımlanır.';
  static const belgeDugme = 'Belgeyi doğrula';
  static const belgeTamam = 'Belge doğrulandı';
  // v0.1.2: form Worker'a gönderilir (deploy/AILE-ILAN-SOZLESME.md); sonuç ekranı
  static const aileYayinda = 'İlanınız yayımlandı. Allah rahmet eylesin.';
  static const aileRed = 'İlan yayımlanamadı. Bilgiler doğrulanamadı.';
  static const aileAgHata =
      'İşlem tamamlanamadı. Bilgileriniz silinmedi; biraz sonra yeniden deneyebilirsiniz.';
  static const kodUst = 'Doğrulama';
  static const kodBaslik = 'Doğrulama kodu';
  static const kodAciklamaTel = 'Telefonunuza gönderilen 6 haneli kodu girin.'; // aile / din görevlisi (15.10.2026: e-posta yerine telefon)
  static String kodAciklama(String eposta) => 'Doğrulama kodunu $eposta adresine gönderdik.';
  static const kodAlan = 'Kod';
  static const kodYer = '6 haneli kod';
  static const kodDugme = 'Doğrula';
  static const kodYeniden = 'Kodu yeniden gönder';
  static String kodBekle(int sn) => 'Kodu yeniden gönder ($sn sn)';
  static const kodEksik = 'Lütfen kodu eksiksiz yazın';
  static const kodGitti = 'Doğrulama kodu gönderildi';
  static const kodHatali = 'Kod doğru değil. Yeniden deneyebilirsiniz.';
  // Kartta bildirim (METIN-SOZLUGU §11)
  static const bildirDugme = 'Bu ilanda bir yanlışlık mı var?';
  // [ekrandaki metin, Worker'a giden neden]
  static const bildirSecenekler = [
    ['Kişi bilgisi yanlış', 'yanlış bilgi'],
    ['Cenaze bilgisi yanlış', 'yanlış bilgi'],
    ['Bu ilan gerçek değil', 'böyle bir kişi yok'],
    ['Diğer', 'diğer'],
  ];
  static const bildirGonder = 'Bildirin';
  static const bildirTamam = 'Bildiriminiz alındı. Teşekkür ederiz.';
  // v0.1 eki (METIN-SOZLUGU §16): öneri penceresi e-posta uygulamasını açar
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
  static const namazSecenek = ['Sabah namazı', 'Öğle namazı', 'İkindi namazı', 'Akşam namazı', 'Yatsı namazı', 'Cuma namazı', 'Saat belirt']; // 15.10 sahibi: sabah/akşam/yatsı eklendi
  static const alanIl = 'İl';
  static const alanIlce = 'İlçe';
  static const alanMahalle = 'Mahalle';
  static const alanMahalleYer = 'Mahallesi';
  static const alanCami = 'Cami';
  static const alanCamiYer = 'Cenaze namazının kılınacağı cami';
  static const alanMezarlik = 'Mezarlık';
  static const alanMezarlikYer = 'Defin yeri';
  static const alanYas = 'Yaş';
  static const alanYasYer = 'Biliyorsanız';
  static const alanNamazTarihi = 'Cenaze namazı tarihi';
  static const adimCenazeBaslik = 'Cenaze bilgileri';
  static const adimCenazeAciklama = 'Bildiğiniz kadarını yazabilirsiniz.';
  static const adim2Baslik = 'Ölüm belgesi doğrulama';
  static const adim2Aciklama =
      'İsteğe bağlı. e-Devlet’ten aldığınız Ölüm Belgesi’nin doğrulama kodunu girerseniz ilanda “Doğrulandı” işareti görünür. Belge dosyası saklanmaz.';
  static const adim2Alan = 'Belge doğrulama kodu';
  static const adim2AlanYer = 'Örn. ABCD-1234-EFGH';
  static const adim3Baslik = 'Başvuran bilgileri';
  static const adim3Aciklama = 'Doğrulama kodu telefonunuza gönderilir.';
  static const adim3Eposta = 'Cep telefonu';
  static const adim3EpostaYer = '5xx xxx xx xx';
  static const adim3TelefonNot = 'Telefon numaranız yalnız doğrulama için kullanılır; ilanda görünmez.';
  static const adim3Ad = 'Ad soyad';
  static const adim3AdYer = 'Adınız ve soyadınız';
  static const adim3Yakinlik = 'Yakınlık';
  static const yakinlikSecenek = ['Oğlu / kızı', 'Eşi', 'Kardeşi', 'Torunu', 'Gelini / damadı', 'Diğer'];
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
  static String formUst(int n) => 'Adım $n / 5';

  // 6. Tam Sayfa
  static const tamUst = 'Türkiye geneli';
  static const tamBaslik = 'Tam Sayfa';
  static const tamOrnek = 'ÖRNEK';
  // v0.1 eki (METIN-SOZLUGU §16): ücretli ilan ilk sürümde kapalı (URUN-TASLAGI §28)
  static const tamBolum = 'Yayımlanan vefat ilanları';
  static const sehitTamDugme = 'Şehidimiz için ilan hazırlayın';
  static const tamIlanUst = 'Tam sayfa ilan';
  static const tamHaritaCami = 'Cami · haritada aç';
  static const tamHaritaMezarlik = 'Mezarlık · haritada aç';
  static String tamHaritaBildirim(String yer) => '$yer · haritada açılır';
  static const fiyatAciklama = 'Gazetedeki vefat ilanının uygulamadaki karşılığı.';
  static const tamDugme = 'Vefat ilanı hazırlayın';
  static const formTamUst = 'Tam sayfa';
  static const formTamBaslik = 'Vefat İlanı';
  static const fiyatBaslik = 'Tam sayfa vefat ilanı';
  static const fiyatEtiket = 'Tek seferlik';
  static const fiyatTutar = '200 ₺';
  static const fiyatNot = 'Abonelik değildir, bir kez ödenir';
  static const fiyatMadde1 = 'Türkiye genelinde görünür';
  static const fiyatMadde2 = 'Metni sizinle birlikte hazırlanır';
  static const fiyatMadde3 = 'Cami ve mezarlık haritada gösterilir';
  static const fiyatMadde4 = 'Yayından önce doğrulanır ve kontrol edilir';
  static const adim5TamBaslik = 'Yasal beyan ve ödeme';
  static const adim5TamTutar = 'Ödenecek: 200 ₺';
  static const adim5TamDugme = 'Ödemeye geç';
  static const adim5TamNot = 'İlanınız ödeme ve kontrolden sonra yayımlanır.';
  static const odemeUst = 'Ödeme';
  static const odemeAlt = 'Mağaza içi satın alma';
  static const odemeUrunAd = 'Tam sayfa cenaze ilanı';
  static const odemeUrunAlt = 'Kimin Cenazesi · tek seferlik satın alma';
  static const odemeTutarEt = 'Tutar';
  static const odemeTutar = '200,00 ₺';
  static const odemeHesapEt = 'Hesap';
  static const odemeHesap = '••••@••••';
  static const odemeYayinEt = 'Yayın';
  static const odemeYayin = 'Kontrolden sonra';
  static const odemeNot = 'Gerçek uygulamada bu ekranı App Store / Google Play açar; ödeme bilgisi uygulamaya gelmez.';
  static const odemeDugme = 'Ödemeyi onayla';
  static const odemeGeri = 'Forma dönün';

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
      'İl ve ilçenizdeki cenaze ilanlarını her gün bir arada gösterir. Sayfanıza eklediğiniz bilgiler silinmez. Sürüm 0.1.4';
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
  // İlan kutusu (15.10.2026): her il/ilçe liste sayfasının üstünde
  static const ilanKutusuBaslik = 'Cenaze ilanınızın burada görülmesini istiyorsanız:';
  static const ilanKutusuYakin = 'Cenaze yakını olarak ilanı paylaş';
  static const ilanKutusuVeya = 'veya';
  static const ilanKutusuGorevli = 'Bulunduğunuz bölgedeki cami din görevlisinden bunu talep edin.';
  static const ilanKutusuKayit = 'Din görevlisi misiniz? Kayıt olun.';

  // Şehit cenazesi ilanları YALNIZ din görevlisi panelinden (15.10.2026)
  static const sehitBilgiBaslik = 'Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır.';
  static const sehitBilgiGovde = 'Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur.';
  static const sehitBilgiKapanis = 'Başınız sağ olsun. Şehidimizin ruhu şad olsun.';
  static const sehitBilgiUst = 'Şehit cenazesi';
  static const gorevliSehitAnahtar = 'Şehit cenazesi';

  // 12. Din görevlisi (0.1.5, URUN-TASLAGI §37). §22: sade dil, ünlem yok, pazar dili yok.
  static const gorevliDugme = 'Din görevlisiyim';
  static const gorevliUst = 'Din görevlisi';
  static const gorevliBaslik = 'Din Görevlisi İlanı';
  static const gorevliGirisEtiket = 'Din görevlileri için';
  static const gorevliGirisNot = 'Hesabınız Diyanet personel kartınızla doğrulanır.';
  static const gorevliMadde1 = 'Cami ve köy cenazelerini ilk siz duyurabilirsiniz';
  static const gorevliMadde2 = 'İl ve ilçe görev yerinize göre sabittir';
  static const gorevliMadde3 = 'İlanlarınızı panelden düzenler ya da kaldırırsınız';
  static const gorevliAd = 'Ad soyad';
  static const gorevliAdYer = 'Kartınızdaki gibi';
  static const gorevliYer = 'Görev yeri';
  static const gorevliYerYer = 'Cami ya da köy adı';
  static const gorevliUnvan = 'Unvan';
  static const gorevliTelefon = 'Cep telefonu';
  static const gorevliTelefonYer = '5xx xxx xx xx';
  static const gorevliTelefonNot = 'Telefon numaranız yalnız doğrulama ve bilgilendirme için kullanılır; ilanlarda görünmez.';
  static const gorevliKodAciklama = 'Telefonunuza gönderilen 6 haneli kodu girin.';
  // [ekrandaki, Worker değeri]
  static const gorevliUnvanlar = [
    ['İmam-Hatip', 'İmam-Hatip'],
    ['Müezzin-Kayyım', 'Müezzin-Kayyım'],
    ['Kur\'an Kursu Öğreticisi', 'Kur\'an Kursu Öğreticisi'],
    ['Vaiz', 'Vaiz'],
    ['Din Hizmetleri Uzmanı', 'Din Hizmetleri Uzmanı'],
    ['Müftü Yardımcısı', 'Müftü Yardımcısı'],
  ];
  static const gorevliDevam = 'Devam';
  static const gorevliListedeBulundu = 'Adınız müftülük listesinde bulundu. Şimdi kartınızı doğrulayalım.';
  static const gorevliListedeYok = 'Adınız müftülük listesinde bulunamadı. Kartınızın fotoğrafıyla devam edebilirsiniz; başvurunuz ayrıca kontrol edilir.';
  static const gorevliFotoUst = 'Diyanet personel kartı';
  static const gorevliFotoYonerge = 'Diyanet İşleri Başkanlığı\'nın size verdiği personel kimlik kartınızın ön yüzünü çekin.';
  static const gorevliFotoAciklama =
      'KVKK uyarınca personel kartınızın fotoğrafı saklanmaz ve veri tabanında tutulmaz; doğrulama tamamlandığında otomatik olarak silinir. TC kimlik numaranız sistemimizde görünmez.';
  static const gorevliKartIslenemedi = 'Fotoğraf işlenemedi. Lütfen kartı yeniden çekin.';
  static const gorevliKamera = 'Personel kartımı çek'; // yalnız uygulama içi kamera; galeri seçeneği yok
  static const gorevliDeneme2 = 'Kart doğrulanamadı. Işığı kontrol edip bir kez daha çekin.';
  static const gorevliBeyan = 'Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum.';
  static const gorevliBasvuruGonder = 'Başvuruyu gönder';
  static const gorevliKuyrukUyari = 'Doğrulama yapılamadı; fotoğrafınız en çok 7 gün kontrol için saklanır, sonra silinir.';
  static const gorevliFotoSaklama = 'Doğrulama için kartınızın fotoğrafı en çok 7 gün kontrol amacıyla saklanır, sonra silinir.';
  static const gorevliKontrolMetin =
      'Başvurunuz kontrol ediliyor. Onaylanınca tarafınıza bilgi verilecek ve din görevlisi paneliniz açılacaktır.';
  // Panel açıkken, onay beklerken (kontrolde)
  static const gorevliKontrolBilgi =
      'Başvurunuz kontrol ediliyor. Hesabınız onaylanınca paneldeki "İlan paylaş" düğmesi etkin hale gelir. Onay verilmezse panel ve hesap silinir.';
  static const gorevliSilindi = 'Başvurunuz onaylanmadı; hesap silindi.';
  static const gorevliOnayBildirimi = 'Başvurunuz onaylandı; din görevlisi paneliniz açıldı.';
  static const gorevliOturumDoldu = 'Oturumunuz sona erdi. Telefon numaranızla yeniden giriş yapabilirsiniz.';
  static const gorevliOnaylandi = 'Hesabınız onaylandı';
  static const gorevliPaneleGit = 'Panele git';
  static const gorevliCiftKayit = 'Hesap kontrol bekliyor';
  static const gorevliCiftKayitNot = 'Bu ad ve görev yeri için başka bir başvuru var. İkisi de kontrol edilecek.';
  static const gorevliGirisYap = 'Hesabım var';
  static const gorevliGirisBaslik = 'Telefon ile giriş';
  static const gorevliGirisAciklama = 'Kayıt olduğunuz telefon numarasına doğrulama kodu göndeririz.';
  static const gorevliKodGonder = 'Kodu gönder';
  static const gorevliBittiUst = 'Başvuru';
  // Panel
  static const gorevliPanelUst = 'Din görevlisi paneli';
  static const gorevliIlanPaylas = 'İlan paylaş';
  static String gorevliIlanlarim(int n) => 'İlanlarım ($n)';
  static const gorevliIlanlarimBaslik = 'İlanlarım';
  static const gorevliSonIlanlar = 'Son ilanlar';
  static const gorevliIlanYok = 'Henüz ilan paylaşmadınız.';
  static const gorevliYerKilit = 'İl ve ilçe görev yerinize göre sabittir.';
  static const gorevliIlanFormBaslik = 'Cenaze ilanı';
  static const gorevliMahalleKoy = 'Mahalle ya da köy';
  static const gorevliGonder = 'İlanı yayımla';
  static const gorevliKaydet = 'Değişikliği kaydet';
  static const gorevliDuzenle = 'Düzenle';
  static const gorevliKaldir = 'İlanı kaldır';
  static const gorevliIlanTamam = 'İlanınız yayımlandı. Allah rahmet eylesin.';
  static const gorevliIlanGuncel = 'İlanınız güncellendi.';
  static const gorevliIlanKalkti = 'İlan kaldırıldı.';
  static const gorevliDonduruldu = 'Hesabınız şu an kullanıma kapalı.';
  static const gorevliYukleniyor = 'Yükleniyor';
  static String gorevliBaslikKart(String yer, String? unvan) {
    final u = unvan ?? '';
    const tamlama = {
      'İmam-Hatip': 'İmam Hatibi',
      'Müezzin-Kayyım': 'Müezzin-Kayyımı',
      'Kur\'an Kursu Öğreticisi': 'Kur\'an Kursu Öğreticisi',
      'Vaiz': 'Vaizi',
      'Din Hizmetleri Uzmanı': 'Din Hizmetleri Uzmanı',
      'Müftü Yardımcısı': 'Müftü Yardımcısı',
    };
    final t = tamlama[u];
    if (t != null) return '$yer $t';
    return u.isEmpty ? yer : '$yer · $u';
  }

  static const gorevliDurumEtiket = {
    'yayinda': 'Yayında',
    'gizli': 'Gizlendi',
    'iptal': 'Kaldırıldı',
    'bekliyor': 'Kontrolde',
    'red': 'Yayımlanmadı',
  };

}
