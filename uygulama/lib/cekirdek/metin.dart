// Ekran metinleri — tasarim/METIN-SOZLUGU.md ile birebir (anahtar adları sözlükteki gibi).
// Süzgeç: pazar dili yok, ölüm sayısı yok, ünlem yok, "ücretsiz/elle/moderatör" yok, merhum/merhume kuralı.
import 'yardimci.dart';

/// 0.1.4 (URUN-TASLAGI §36, site sahibi 15.10.2026): günlük cenaze bildirimi açık; ilk açılışta tek kart sorar.
const bool bildirimTeklifiAcik = true;

class M {
  M._();

  // 1. Açılış ve adres seçimi
  static const acilisMarka = 'Kimin Cenazesi';
  static const acilisAlt = 'Bulunduğunuz ili seçin';
  // 0.1.7 (URUN-TASLAGI §41): açılış mesajı ve motto
  static const acilisArapca = 'إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ';
  static const acilisMeal = '“Doğrusu biz Allah’a aidiz ve kuşkusuz O’na döneceğiz.”';
  static const acilisSure = 'Bakara sûresi, 2/156';
  static const acilisKaynak = 'Diyanet İşleri Başkanlığı Meâli';
  static const motto = 'Şehrinizdeki cenazelerden haberdar olun';
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
  static const seritYarin = 'Yarın'; // 15.10.2026: yarının ilanı anında yayında; yalnız o güne kayıt varsa şeritte
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
  // kartGorevli KALDIRILDI 16.10.2026 (sahibi: ilanın kaynağı belli edilmez)
  static const kartBebek = 'Bebek'; // §32: adı olan bebek kaydında rozet
  static const kartKaldir = 'Sayfamdan kaldır';
  static const kaldirSoru = 'Bu kaydı sayfanızdan kaldırmak istiyor musunuz?';
  static const kaldirVazgec = 'Vazgeç';
  static const kaldirTamam = 'Kaldır';
  static const bildirimKaldirildi = 'Sayfanızdan kaldırıldı';
  static const bildirimKaydedildi = 'Sayfanıza eklendi';
  static String bosBugunBaslik(String yer) => 'Bugün ${ek(yer)} cenaze ilanı bulunmuyor';
  static const bosBugunAciklama = ''; // 15.10.2026 sahibi: "son 7 günün ilanları aşağıda" ifadesi KALDIRILDI; geçmiş günler yalnız tarih şeridinden
  static const bosGecmisBaslik = 'Bu tarihte cenaze ilanı bulunmuyor';
  static String bosGecmisAciklama(String gun, String yer) => '${tarih(gun)} · $yer';
  // bosIlGeneli KALDIRILDI 16.10.2026 (sahibi: boş günde yalnız üstteki satır kalsın)

  // 3. Verisi olmayan il
  // kaynaksizBaslik/kaynaksizAciklama KALDIRILDI 16.10.2026 (sahibi)
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
  static const ilanVerAciklama = 'Aradığınız ilan burada yoksa, yakınınızın ilanını siz de paylaşabilirsiniz.';

  // 4. Aile formu
  static const aileBittiDugme = 'Tamam';
  // Şehit akışı (METIN-SOZLUGU sehit.*): ücret ifadesi hiçbir yerde geçmez
  static const sehitRutbe = 'Rütbe / unvan';
  static const sehitRutbeYer = 'Ör. Piyade Uzman Çavuş';
  static const sehitTorenYeri = 'Cenaze töreni yeri';
  static const sehitTorenYer = 'Tören yapılacak yer';
  static const sehitDuyuruAlan = 'Resmî duyuru bağlantısı';
  // v0.1.2: form Worker'a gönderilir (deploy/AILE-ILAN-SOZLESME.md); sonuç ekranı
  static const aileRed = 'İlan yayımlanamadı. Bilgiler doğrulanamadı.';
  static const aileAgHata =
      'İşlem tamamlanamadı. Bilgileriniz silinmedi; biraz sonra yeniden deneyebilirsiniz.';
  static const kodUst = 'Doğrulama';
  static const kodBaslik = 'Doğrulama kodu';
  static const kodAlan = 'Kod';
  static const kodYer = '6 haneli kod';
  static const kodDugme = 'Doğrula';
  static const kodYeniden = 'Kodu yeniden gönder';
  /// Yeniden gönder bekleme 5 dk (sahibi 16.10): tam 300 sn iken "(5 dk)", sonra dakika:saniye geri sayım
  static String kodBekle(int sn) => sn >= 300 ? 'Kodu yeniden gönder (5 dk)' : 'Kodu yeniden gönder (${sn ~/ 60}:${(sn % 60).toString().padLeft(2, '0')})';
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
  static const erkek = 'Erkek';
  static const kadin = 'Kadın';
  static const alanAd = 'Ad soyad';
  static const alanVefat = 'Vefat tarihi';
  static const namazSecenek = ['Sabah namazı', 'Öğle namazı', 'İkindi namazı', 'Akşam namazı', 'Yatsı namazı', 'Cuma namazı', 'Saat belirt']; // 15.10 sahibi: sabah/akşam/yatsı eklendi
  static const alanIl = 'İl';
  static const alanIlce = 'İlçe';
  static const alanCami = 'Cami';
  static const alanCamiYer = 'Cenaze namazının kılınacağı cami';
  static const alanMezarlik = 'Mezarlık';
  static const alanMezarlikYer = 'Defin yeri';
  static const alanYas = 'Yaş';
  static const alanYasYer = 'Biliyorsanız';
  static const alanNamazTarihi = 'Cenaze namazı tarihi';

  static const haritaCami = 'Cami · haritada aç';
  static const haritaMezarlik = 'Mezarlık · haritada aç';
  static const haritaAcilamadi = 'Harita açılamadı';
  static const kartHaritadaAc = 'Haritada aç';

  // 7. Sayfam
  static const sayfamUst = 'Rahmetle anıyoruz';
  static const sayfamBaslik = 'Sayfam';
  static const sayfamBosBaslik = 'Sayfanızda henüz kimse yok';
  static const sayfamBosAciklama =
      'Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez.';
  static const sayacBaslik = 'Okuma sayacı — her dokunuşta bir artar'; // sahibi 16.10.2026: kutucukların sayaç olduğu üstte yazsın
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
  static const paylasMetin = 'Kimin Cenazesi — şehrinizdeki cenazelerden haberdar olun. Play Store: $magazaBaglanti';
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
      'Şehrinizdeki cenazelerden haberdar olun. Sayfanıza eklediğiniz bilgiler silinmez. Sürüm 0.1.9';
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
  static const sekmeler = ['İlanlar', 'Sayfam', 'Dualar', 'Hatırla'];
  // İlan kutusu (15.10.2026): her il/ilçe liste sayfasının üstünde
  static const ilanKutusuGorevli = 'Cenaze ilanınızın bu sayfada görülmesini istiyorsanız bulunduğunuz bölgedeki din görevlisinden talep edebilirsiniz.'; // tek paragraf (site sahibi 15.10.2026, birebir); başlık yok
  static const ilanKutusuKayit = 'Din görevlisi misiniz? Kayıt olun.';
  static const ilanKutusuSehit = 'Şehit cenazesi ilanı nasıl verilir?';

  // Şehit cenazesi ilanları YALNIZ din görevlisi panelinden (15.10.2026)
  static const sehitBilgiBaslik = 'Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır.';
  static const sehitBilgiGovde = 'Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur.';
  static const sehitBilgiKapanis = 'Başınız sağ olsun. Şehidimizin ruhu şad olsun.';
  static const sehitBilgiUst = 'Şehit cenazesi';
  static const gorevliSehitAnahtar = 'Şehit cenazesi';

  // 12. Din görevlisi (0.1.5, URUN-TASLAGI §37). §22: sade dil, ünlem yok, pazar dili yok.
  static const gorevliUst = 'Din görevlisi';
  static const gorevliBaslik = 'Din Görevlisi İlanı';
  static const gorevliGirisEtiket = 'Din görevlileri için';
  static const gorevliMadde1 = 'Cami ve köy cenazelerini ilk siz duyurabilirsiniz';
  static const gorevliMadde2 = 'İl ve ilçe görev yerinize göre sabittir';
  static const gorevliMadde3 = 'İlanlarınızı panelden düzenler ya da kaldırırsınız';
  // ---- Diyanet e-posta doğrulaması (URUN §45, 16.10.2026) ----
  static const gorevliEpostaBaslik = 'Din görevlisi olduğunuzu teyit edelim';
  static const gorevliEpostaAciklama = 'Diyanet İşleri Başkanlığının size tahsis ettiği e-posta adresinize bir kod göndereceğiz. Gelen kodu bir sonraki ekrana yazın.';
  static const gorevliKullanici = 'Diyanet kullanıcı adınız';
  static const gorevliKullaniciYer = 'kullaniciadi';
  static const gorevliAlanAdi = '@diyanet.gov.tr';
  static const gorevliKodGonderDugme = 'Kodu gönder';
  static const gorevliNasilGiris = 'Diyanet e-posta adresime nasıl giriş yapabilirim?';
  static const gorevliNasilBaslik = 'Diyanet e-posta adresiniz';
  /// Kılavuz penceresi: 6 kısa madde
  static const gorevliNasil6 = [
    'Diyanet her personeline bir e-posta adresi verir.',
    'Adresiniz: DİBBYS kullanıcı adınız@diyanet.gov.tr',
    'Tarayıcıya posta.diyanet.gov.tr yazın.',
    'Kullanıcı adı: kullanıcıadınız@diyanet.gov.tr',
    'Şifre: DİBBYS şifreniz. Giriş yapın.',
    'Gelen kutusundaki kodu uygulamaya girin.',
  ];
  /// Kod ekranındaki 5 madde (kişinin adı dolu)
  static List<String> gorevliTarif5(String adres) => [
        'Adresiniz: $adres',
        'Tarayıcıya posta.diyanet.gov.tr yazın.',
        'Kullanıcı adı: $adres',
        'Şifre: DİBBYS şifreniz. Giriş yapın.',
        'Gelen kutusundaki kodu aşağıya yazın.',
      ];
  static String gorevliKodGitti(String adres) => 'Kod gönderildi: $adres';
  static const gorevliKodGecerli = 'Kod 10 dakika geçerlidir.';
  static const gorevliKodDogrulaDugme = 'Doğrula ve paneli aç';
  static const gorevliKodYanlis = 'Kod yanlış ya da süresi dolmuş. Yeniden deneyin ya da yeni kod isteyin.';
  static const gorevliKodGecersiz = 'Kod 5 kez yanlış girildi; yeni kod isteyin.';
  static const gorevliKullaniciHata = 'Kullanıcı adı geçersiz. Yalnız harf, rakam, nokta, tire ve alt çizgi kullanın.';
  static const gorevliGunlukSinir = 'Bugün için kod sınırına ulaştınız. Yarın yeniden deneyin.';
  static const gorevliDondurulmus = 'Hesabınız şu an kullanıma kapalı.';
  static const gorevliProfilYok = 'Görev bilgilerinizi ilk ilanınızda bir kez yazacaksınız.';
  static const gorevliProfilBaslik = 'Görev bilgileriniz';
  static const gorevliProfilAciklama = 'İlanlarınız bu görev yeriyle yayımlanır. Bilgiler hesabınızda saklanır.';
  static const gorevliKaydetDugme = 'Kaydet ve devam et';
  static const gorevliYerDegisti = 'Görev yerim değişti';
  static const gorevliYerDegistiAciklama = 'Yeni ilanlarınız bu görev yeriyle paylaşılır; önceki ilanlar değişmez.';
  static const gorevliYerGuncellendi = 'Görev yeriniz güncellendi.';
  static const gorevliTamam = 'Tamam';
  static const gorevliCikisYap = 'Çıkış yap';
  static const gorevliCikisYapildi = 'Çıkış yaptınız.';
  static const gorevliAd = 'Ad soyad';
  static const gorevliAdYer = 'Kartınızdaki gibi';
  static const gorevliYer = 'Görev yeri';
  static const gorevliYerYer = 'Cami ya da köy adı';
  static const gorevliUnvan = 'Unvan';
  // [ekrandaki, Worker değeri]
  static const gorevliUnvanlar = [
    ['İmam-Hatip', 'İmam-Hatip'],
    ['Müezzin-Kayyım', 'Müezzin-Kayyım'],
    ['Kur\'an Kursu Öğreticisi', 'Kur\'an Kursu Öğreticisi'],
    ['Vaiz', 'Vaiz'],
    ['Din Hizmetleri Uzmanı', 'Din Hizmetleri Uzmanı'],
    ['Müftü Yardımcısı', 'Müftü Yardımcısı'],
  ];
  static const gorevliKontrolMetin =
      'Başvurunuz kontrol ediliyor. Onaylanınca tarafınıza bilgi verilecek ve din görevlisi paneliniz açılacaktır.';
  // Panel açıkken, onay beklerken (kontrolde)
  static const gorevliKontrolBilgi =
      'Başvurunuz kontrol ediliyor. Hesabınız onaylanınca paneldeki "İlan paylaş" düğmesi etkin hale gelir. Onay verilmezse panel ve hesap silinir.';
  static const gorevliSilindi = 'Başvurunuz onaylanmadı; hesap silindi.';
  static const gorevliOnayBildirimi = 'Başvurunuz onaylandı; din görevlisi paneliniz açıldı.';
  static const gorevliOturumDoldu = 'Oturumunuz sona erdi. Diyanet e-posta kodunuzla yeniden giriş yapabilirsiniz.';
  static const gorevliPaneleGit = 'Panele git';
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
  static const gorevliYerKaydet = 'Kaydet';
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

  // URUN §49 / §50
  static const gorevliDuzelt = 'Düzelt';
  static const gorevliDuzeltmeAlindi = 'Düzeltmeniz alındı; bir sonraki güncellemede yayına girer.';
  static const gorevliDuzeltildi = 'Düzeltildi';
  static const gorevliKvkkBaslik = 'Kişisel verileriniz';
  static const gorevliKvkkOku = 'Okudum, anladım';
  static const gorevliKvkkTam = 'Tam metin';
  // 16.10.2026 sahibi: "Cloudflare / yurt dışı" satırı kısa uyarıda YOK (korkutur); yurt dışı aktarımı tam metinde (Gizlilik) kalır
  static const gorevliKvkkMetin = [
    'Tuttuğumuz veriler: Diyanet e-posta adresiniz, ad-soyadınız, görev yeriniz ve unvanınız, il-ilçeniz, paylaştığınız ilanlar.',
    'Amaç: din görevlisi olduğunuzu teyit etmek ve ilan paylaşmanızı sağlamak.',
    'Süre: hesabınız açık kaldıkça; ilanlar 120 gün; e-posta kodu 10 dakika.',
    'Telefon numarası, kimlik ya da personel kartı fotoğrafı toplanmaz.',
    'Verileriniz üçüncü kişilerle paylaşılmaz.',
    'Haklarınız (KVKK md. 11): verilerinize erişme, düzeltme ve silme isteğinde bulunabilirsiniz; Gizlilik sayfasından ulaşın.',
  ];

  static const gorevliDurumEtiket = {
    'yayinda': 'Yayında',
    'gizli': 'Gizlendi',
    'iptal': 'Kaldırıldı',
    'bekliyor': 'Kontrolde',
    'red': 'Yayımlanmadı',
  };

}
