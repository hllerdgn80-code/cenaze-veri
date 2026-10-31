// Ekran metinleri — tasarim/METIN-SOZLUGU.md ile birebir (anahtar adları sözlükteki gibi).
// Süzgeç: pazar dili yok, ölüm sayısı yok, ünlem yok, "ücretsiz/elle/moderatör" yok, merhum/merhume kuralı.
import 'package:flutter/foundation.dart' show defaultTargetPlatform, TargetPlatform;

import 'surum.dart';
import 'uzak_ayar.dart';
import 'yardimci.dart';

/// 0.1.4 (URUN-TASLAGI §36, site sahibi 15.10.2026): günlük cenaze bildirimi açık; ilk açılışta tek kart sorar.
/// 31.10.2026: yalnız Android'de (iOS'ta bildirim yok: menüde çalışmayan düğme kalmaz).
bool get bildirimTeklifiAcik => defaultTargetPlatform == TargetPlatform.android && UzakAyar.bayrak('bildirim_teklifi_acik', true);

class M {
  M._();

  // 1. Açılış ve adres seçimi
  static String get acilisMarka => UzakAyar.yazi('acilisMarka', 'Kimin Cenazesi');
  static String get acilisAlt => UzakAyar.yazi('acilisAlt', 'Bulunduğunuz ili seçin');
  // 0.1.7 (URUN-TASLAGI §41): açılış mesajı ve motto
  static String get acilisArapca => UzakAyar.yazi('acilisArapca', 'إِنَّا لِلَّهِ وَإِنَّا إِلَيْهِ رَاجِعُونَ');
  static String get acilisMeal => UzakAyar.yazi('acilisMeal', '“Biz şüphesiz (her şeyimizle) Allah’a aidiz ve şüphesiz O’na döneceğiz.”');
  static String get acilisSure => UzakAyar.yazi('acilisSure', 'Bakara sûresi, 2/156');
  static String get acilisKaynak => UzakAyar.yazi('acilisKaynak', 'Diyanet İşleri Başkanlığı Meâli');
  static String get motto => UzakAyar.yazi('motto', 'Şehrinizdeki cenazelerden haberdar olun');
  static String get ilAra => UzakAyar.yazi('ilAra', 'İl ara');
  static String get ilBos => UzakAyar.yazi('ilBos', 'Bu adla bir il bulunamadı');
  static String get ilceUst => UzakAyar.yazi('ilceUst', 'İlçe seçin');
  static String get ilceGeri => UzakAyar.yazi('ilceGeri', 'İller');
  static String get ilceAra => UzakAyar.yazi('ilceAra', 'İlçe ara');
  static String get ilceTumu => UzakAyar.yazi('ilceTumu', 'Tüm ilçeler');
  static String get ilceBos => UzakAyar.yazi('ilceBos', 'Bu adla bir ilçe bulunamadı');

  // 2. Cenaze İlanları
  static String get ilanlarUst => UzakAyar.yazi('ilanlarUst', 'Cenaze İlanları');
  static String get seritBugun => UzakAyar.yazi('seritBugun', 'Bugün');
  static String get seritYarin => UzakAyar.yazi('seritYarin', 'Yarın'); // 30.10.2026 §58: Yarın şeritte HER ZAMAN
  static String get bolumIlGeneli => UzakAyar.yazi('bolumIlGeneli', 'İl geneli (ilçe belirtilmemiş)');
  // §21/1: ilanları ilçe vermeyen kaynakta (ör. Gaziantep) ilanlar zaten "İl geneli"dir; parantezli açıklama gerekmez
  static String get bolumIlGenelSade => UzakAyar.yazi('bolumIlGenelSade', 'İl geneli');
  // §21/2: kullanıcının ilçesinde bugün ilan yoksa ilde bugün okunan ilçeler ("Muğla’da bugün: Bodrum, Fethiye, Milas…")
  static String digerIlcelerBaslik(String il, List<String> ilceler, {bool devami = false}) =>
      UzakAyar.kalip('digerIlcelerBaslik', '${ek(il)} bugün: ${ilceler.join(', ')}${devami ? '…' : ''}', [ek(il), '${ilceler.join(', ')}${devami ? '…' : ''}']);
  static String get kartNamaz => UzakAyar.yazi('kartNamaz', 'Cenaze namazı');
  static String get kartDefin => UzakAyar.yazi('kartDefin', 'Defin');
  static String get kartKaydet => UzakAyar.yazi('kartKaydet', 'Sayfama kaydet');
  static String get kartKaydedildi => UzakAyar.yazi('kartKaydedildi', 'Sayfamda ✓');
  // kartGorevli KALDIRILDI 16.10.2026 (sahibi: ilanın kaynağı belli edilmez)
  static String get kartBebek => UzakAyar.yazi('kartBebek', 'Bebek'); // §32: adı olan bebek kaydında rozet
  static String get kartKaldir => UzakAyar.yazi('kartKaldir', 'Sayfamdan kaldır');
  static String get kaldirSoru => UzakAyar.yazi('kaldirSoru', 'Bu kaydı sayfanızdan kaldırmak istiyor musunuz?');
  static String get kaldirVazgec => UzakAyar.yazi('kaldirVazgec', 'Vazgeç');
  static String get kaldirTamam => UzakAyar.yazi('kaldirTamam', 'Kaldır');
  static String get bildirimKaldirildi => UzakAyar.yazi('bildirimKaldirildi', 'Sayfanızdan kaldırıldı');
  static String get bildirimKaydedildi => UzakAyar.yazi('bildirimKaydedildi', 'Sayfanıza eklendi');
  static String bosBugunBaslik(String yer) => UzakAyar.kalip('bosBugunBaslik', 'Bugün ${ek(yer)} cenaze ilanı bulunmuyor', [ek(yer)]); // {0} = yer + bulunma eki ('Başiskele’de')
  static String get bosBugunAciklama => UzakAyar.yazi('bosBugunAciklama', ''); // 15.10.2026 sahibi: "son 7 günün ilanları aşağıda" ifadesi KALDIRILDI; geçmiş günler yalnız tarih şeridinden
  /// URUN §57: bugün boşken dünün ilanlarının üstündeki bölüm başlığı
  static String dunBolum(String dun) => UzakAyar.kalip('dunBolum', 'Dün (${tarih(dun, kisa: true)})', [tarih(dun, kisa: true)]);
  /// URUN §58 (sahibi 30.10.2026): Yarın (ve öbür gün) sekmesi boşken. {0} = yer ADI (ek almaz: "Bodrum için")
  static String bosYarinBaslik(String yer) => UzakAyar.kalip('bosYarinBaslik', 'Yarın $yer için henüz cenaze ilanı girilmedi', [yer]);
  static String get bosYarinAciklama => UzakAyar.yazi('bosYarinAciklama', 'Yarının ilanları gün içinde eklenir; liste kendiliğinden güncellenir.');
  static String get bosGecmisBaslik => UzakAyar.yazi('bosGecmisBaslik', 'Bu tarihte cenaze ilanı bulunmuyor');
  static String bosGecmisAciklama(String gun, String yer) => UzakAyar.kalip('bosGecmisAciklama', '${tarih(gun)} · $yer', [tarih(gun), yer]);
  // bosIlGeneli KALDIRILDI 16.10.2026 (sahibi: boş günde yalnız üstteki satır kalsın)

  // 3. Verisi olmayan il
  // kaynaksizBaslik/kaynaksizAciklama KALDIRILDI 16.10.2026 (sahibi)
  static String get kaynaksizDugme => UzakAyar.yazi('kaynaksizDugme', 'Cenaze ilanı paylaş');
  static String get kaynaksizBugun => UzakAyar.yazi('kaynaksizBugun', 'Bugün');
  static String get izinSoru => UzakAyar.yazi('izinSoru', 'Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?');
  static String get izinEvet => UzakAyar.yazi('izinEvet', 'Evet, haber verin');
  static String get izinHayir => UzakAyar.yazi('izinHayir', 'Şimdi değil');
  static String get izinEvetBildirim => UzakAyar.yazi('izinEvetBildirim', 'Bölgenizdeki cenazeler için sabahları haber vereceğiz');
  static String get izinHayirBildirim => UzakAyar.yazi('izinHayirBildirim', 'Bildirim gönderilmeyecek');
  static String get izinVerilmedi => UzakAyar.yazi('izinVerilmedi', 'Bildirim izni verilmedi. Telefonunuzun ayarlarından açabilirsiniz.');
  static String get menuBildirimAc => UzakAyar.yazi('menuBildirimAc', 'Cenaze bildirimini aç');
  static String get menuBildirimKapat => UzakAyar.yazi('menuBildirimKapat', 'Cenaze bildirimini kapat');
  // Bugün ilan yoksa kartın hemen altı (14.10.2026 sahibi: bağlantı en üstte)
  static String get ilanVerAciklama => UzakAyar.yazi('ilanVerAciklama', 'Aradığınız ilan burada yoksa, yakınınızın ilanını siz de paylaşabilirsiniz.');

  // 4. Aile formu
  static String get aileBittiDugme => UzakAyar.yazi('aileBittiDugme', 'Tamam');
  // Şehit akışı (METIN-SOZLUGU sehit.*): ücret ifadesi hiçbir yerde geçmez
  static String get sehitRutbe => UzakAyar.yazi('sehitRutbe', 'Rütbe / unvan');
  static String get sehitRutbeYer => UzakAyar.yazi('sehitRutbeYer', 'Ör. Piyade Uzman Çavuş');
  static String get sehitTorenYeri => UzakAyar.yazi('sehitTorenYeri', 'Cenaze töreni yeri');
  static String get sehitTorenYer => UzakAyar.yazi('sehitTorenYer', 'Tören yapılacak yer');
  static String get sehitDuyuruAlan => UzakAyar.yazi('sehitDuyuruAlan', 'Resmî duyuru bağlantısı');
  // v0.1.2: form Worker'a gönderilir (deploy/AILE-ILAN-SOZLESME.md); sonuç ekranı
  static String get aileRed => UzakAyar.yazi('aileRed', 'İlan yayımlanamadı. Bilgiler doğrulanamadı.');
  static String get aileAgHata => UzakAyar.yazi('aileAgHata', 'İşlem tamamlanamadı. Bilgileriniz silinmedi; biraz sonra yeniden deneyebilirsiniz.');
  static String get kodUst => UzakAyar.yazi('kodUst', 'Doğrulama');
  static String get kodBaslik => UzakAyar.yazi('kodBaslik', 'Doğrulama kodu');
  static String get kodAlan => UzakAyar.yazi('kodAlan', 'Kod');
  static String get kodYer => UzakAyar.yazi('kodYer', '6 haneli kod');
  static String get kodDugme => UzakAyar.yazi('kodDugme', 'Doğrula');
  static String get kodYeniden => UzakAyar.yazi('kodYeniden', 'Kodu yeniden gönder');
  /// Yeniden gönder bekleme 5 dk (sahibi 16.10): tam 300 sn iken "(5 dk)", sonra dakika:saniye geri sayım
  static String kodBekle(int sn) => sn >= 300 ? UzakAyar.yazi('kodBekle5dk', 'Kodu yeniden gönder (5 dk)') : UzakAyar.kalip('kodBekle', 'Kodu yeniden gönder (${sn ~/ 60}:${(sn % 60).toString().padLeft(2, '0')})', ['${sn ~/ 60}:${(sn % 60).toString().padLeft(2, '0')}']);
  static String get kodEksik => UzakAyar.yazi('kodEksik', 'Lütfen kodu eksiksiz yazın');
  static String get kodGitti => UzakAyar.yazi('kodGitti', 'Doğrulama kodu gönderildi');
  static String get kodHatali => UzakAyar.yazi('kodHatali', 'Kod doğru değil. Yeniden deneyebilirsiniz.');
  // Kartta bildirim (METIN-SOZLUGU §11)
  static String get bildirDugme => UzakAyar.yazi('bildirDugme', 'Bu ilanda bir yanlışlık mı var?');
  // [ekrandaki metin, Worker'a giden neden]
  static List<List<String>> get bildirSecenekler => UzakAyar.ikiliListe('bildirSecenekler', const [
    ['Kişi bilgisi yanlış', 'yanlış bilgi'],
    ['Cenaze bilgisi yanlış', 'yanlış bilgi'],
    ['Bu ilan gerçek değil', 'böyle bir kişi yok'],
    ['Diğer', 'diğer'],
  ]);
  static String get bildirGonder => UzakAyar.yazi('bildirGonder', 'Bildirin');
  static String get bildirTamam => UzakAyar.yazi('bildirTamam', 'Bildiriminiz alındı. Teşekkür ederiz.');
  // v0.1 eki (METIN-SOZLUGU §16): öneri penceresi e-posta uygulamasını açar
  static String get aileEpostaNot => UzakAyar.yazi('aileEpostaNot', 'Gönderimi e-posta uygulamanızda tamamlayabilirsiniz.');

  // 5. Ortak form metinleri
  static String get erkek => UzakAyar.yazi('erkek', 'Erkek');
  static String get kadin => UzakAyar.yazi('kadin', 'Kadın');
  static String get alanAd => UzakAyar.yazi('alanAd', 'Ad soyad');
  static String get alanVefat => UzakAyar.yazi('alanVefat', 'Vefat tarihi');
  static List<String> get namazSecenek => UzakAyar.liste('namazSecenek', const ['Sabah namazı', 'Öğle namazı', 'İkindi namazı', 'Akşam namazı', 'Yatsı namazı', 'Cuma namazı', 'Saat belirt']); // 15.10 sahibi: sabah/akşam/yatsı eklendi
  static String get alanIl => UzakAyar.yazi('alanIl', 'İl');
  static String get alanIlce => UzakAyar.yazi('alanIlce', 'İlçe');
  static String get alanCami => UzakAyar.yazi('alanCami', 'Cami');
  static String get alanCamiAd => UzakAyar.yazi('alanCamiAd', 'Cami adı');
  static String get alanCamiDiger => UzakAyar.yazi('alanCamiDiger', 'Diğer'); // §49d: başka cami -> elle yazılır
  static String get alanVakit => UzakAyar.yazi('alanVakit', 'Vakit');
  static List<String> get vakitSecenek => UzakAyar.liste('vakitSecenek', const ['Sabah Namazını Müteakip', 'Öğle Namazını Müteakip', 'İkindi Namazını Müteakip', 'Akşam Namazını Müteakip', 'Yatsı Namazını Müteakip']); // sahibi 16.10 (§49d)
  static String get alanCamiYer => UzakAyar.yazi('alanCamiYer', 'Cenaze namazının kılınacağı cami');
  static String get alanMezarlik => UzakAyar.yazi('alanMezarlik', 'Mezarlık');
  static String get alanMezarlikYer => UzakAyar.yazi('alanMezarlikYer', 'Defin yeri');
  static String get alanYas => UzakAyar.yazi('alanYas', 'Yaş');
  static String get alanYasYer => UzakAyar.yazi('alanYasYer', 'Biliyorsanız');
  static String get alanYasYok => UzakAyar.yazi('alanYasYok', 'Belirtilmedi'); // sahibi 16.10: yaş bilinmiyorsa; ilanda yaş görünmez
  static String get alanNamazTarihi => UzakAyar.yazi('alanNamazTarihi', 'Cenaze namazı tarihi');

  static String get haritaCami => UzakAyar.yazi('haritaCami', 'Cami · haritada aç');
  static String get haritaMezarlik => UzakAyar.yazi('haritaMezarlik', 'Mezarlık · haritada aç');
  static String get haritaAcilamadi => UzakAyar.yazi('haritaAcilamadi', 'Harita açılamadı');
  static String get kartHaritadaAc => UzakAyar.yazi('kartHaritadaAc', 'Haritada aç');

  // 7. Sayfam
  static String get sayfamUst => UzakAyar.yazi('sayfamUst', 'Rahmetle anıyoruz');
  static String get sayfamBaslik => UzakAyar.yazi('sayfamBaslik', 'Sayfam');
  static String get sayfamBosBaslik => UzakAyar.yazi('sayfamBosBaslik', 'Sayfanızda henüz kimse yok');
  static String get sayfamBosAciklama => UzakAyar.yazi('sayfamBosAciklama', 'Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez.');
  static String get sayacBaslik => UzakAyar.yazi('sayacBaslik', 'Okuma sayacı — her dokunuşta bir artar'); // sahibi 16.10.2026: kutucukların sayaç olduğu üstte yazsın
  static String get sayacGeri => UzakAyar.yazi('sayacGeri', 'Geri al');
  static String get cinsSoru => UzakAyar.yazi('cinsSoru', 'Merhum mu, merhume mi?');
  static String get cinsMerhum => UzakAyar.yazi('cinsMerhum', 'Merhum');
  static String get cinsMerhume => UzakAyar.yazi('cinsMerhume', 'Merhume');
  static String sayacToplam(int n) => UzakAyar.kalip('sayacToplam', 'Okuduklarınızın toplamı: $n', ['$n']);

  // 8. Hatırla
  static String get hatirlaUst => UzakAyar.yazi('hatirlaUst', 'Rahmetle anıyoruz');
  static String get hatirlaBaslik => UzakAyar.yazi('hatirlaBaslik', 'Hatırla');
  static String get kayBaslik => UzakAyar.yazi('kayBaslik', 'Kaybettiklerimiz');
  static String get tbBaslik => UzakAyar.yazi('tbBaslik', 'Tarihte Bugün');
  static String get kayAra => UzakAyar.yazi('kayAra', 'Ad ara');
  static String get kayBos => UzakAyar.yazi('kayBos', 'Bu adla bir kayıt bulunamadı');
  static String get kayDaha => UzakAyar.yazi('kayDaha', 'Devamını gösterin');
  static String tbUst(String gun) => UzakAyar.kalip('tbUst', '${tarih(gun, kisa: true)} · hayatını kaybedenler', [tarih(gun, kisa: true)]);
  static String get tbTurkiye => UzakAyar.yazi('tbTurkiye', 'Türkiye');
  static String get tbDunya => UzakAyar.yazi('tbDunya', 'Dünya');
  // v0.1 eki (METIN-SOZLUGU §16)
  static String get tbHazirlaniyor => UzakAyar.yazi('tbHazirlaniyor', 'Bugün için liste hazırlanıyor');
  static List<List<String>> get kayKategoriler => UzakAyar.ikiliListe('kayKategoriler', const [
    ['cumhurbaskanlari', 'Cumhurbaşkanları'],
    ['basbakanlar', 'Başbakanlar'],
    ['bakanlar', 'Bakanlar'],
    ['siyasetciler', 'Siyasetçiler'],
    ['sanatcilar', 'Sanat, Edebiyat ve Bilim'],
  ]);

  // 8b. Dualar
  static String get duaSekme => UzakAyar.yazi('duaSekme', 'Dualar');
  static String get duaUst => UzakAyar.yazi('duaUst', 'Rahmetle anıyoruz');
  static String get duaBaslik => UzakAyar.yazi('duaBaslik', 'Dualar ve Âyetler');
  static String get duaTumu => UzakAyar.yazi('duaTumu', 'Tümü');
  static String get duaMerhumIcin => UzakAyar.yazi('duaMerhumIcin', 'Merhum için');
  static String get duaMerhumeIcin => UzakAyar.yazi('duaMerhumeIcin', 'Merhume için');
  static String get sureBaslik => UzakAyar.yazi('sureBaslik', 'Sûreler');
  static String get sureOkunusDugme => UzakAyar.yazi('sureOkunusDugme', 'Türkçe yazılışını oku');
  static String get sureArapcaDugme => UzakAyar.yazi('sureArapcaDugme', 'Arapçasını oku');

  // 8c. Şehit
  static String get sehitEtiket => UzakAyar.yazi('sehitEtiket', 'ŞEHİT');
  static String get sehitToren => UzakAyar.yazi('sehitToren', 'Cenaze töreni');
  static String get sehitKapanis => UzakAyar.yazi('sehitKapanis', 'Ruhu şad olsun, mekânı cennet olsun.');
  static String get sehitBolum => UzakAyar.yazi('sehitBolum', 'Şehidimiz');

  // 9. Menü, Hakkında, Gizlilik
  static String get menuAdres => UzakAyar.yazi('menuAdres', 'Adresi değiştir');
  static String get menuAcikTema => UzakAyar.yazi('menuAcikTema', 'Açık tema');
  static String get menuKoyuTema => UzakAyar.yazi('menuKoyuTema', 'Koyu tema');
  static String get menuHakkinda => UzakAyar.yazi('menuHakkinda', 'Hakkında');
  static String get menuGizlilik => UzakAyar.yazi('menuGizlilik', 'Gizlilik');
  static String get menuPaylas => UzakAyar.yazi('menuPaylas', 'Uygulamayı paylaş');
  static String get menuOneri => UzakAyar.yazi('menuOneri', 'Öneri ve tavsiyeleriniz');
  // Mağaza bağlantısı/paylaşma metni platforma göre: Android = Play Store (uzak ayar anahtarları aynen); iOS = App Store (surum.json ios_magaza_url)
  static String get magazaBaglanti => iosMu
      ? UzakAyar.yazi('magazaBaglantiIos', sonIosMagazaUrl ?? varsayilanIosMagazaUrl)
      : UzakAyar.yazi('magazaBaglanti', 'https://play.google.com/store/apps/details?id=com.kimincenazesi.app');
  static String get paylasMetin => iosMu
      ? UzakAyar.yazi('paylasMetinIos', 'Kimin Cenazesi — şehrinizdeki cenazelerden haberdar olun. App Store: $magazaBaglanti')
      : UzakAyar.yazi('paylasMetin', 'Kimin Cenazesi — şehrinizdeki cenazelerden haberdar olun. Play Store: $magazaBaglanti');
  static String get oneriBaslik => UzakAyar.yazi('oneriBaslik', 'Öneri ve tavsiyeleriniz');
  static String get oneriMesaj => UzakAyar.yazi('oneriMesaj', 'Mesajınız');
  static String get oneriMesajYer => UzakAyar.yazi('oneriMesajYer', 'Görüşünüzü yazın');
  static String get oneriEposta => UzakAyar.yazi('oneriEposta', 'E-posta (isteğe bağlı)');
  static String get oneriEpostaYer => UzakAyar.yazi('oneriEpostaYer', 'ornek@eposta.com');
  static String get oneriVazgec => UzakAyar.yazi('oneriVazgec', 'Vazgeç');
  static String get oneriGonder => UzakAyar.yazi('oneriGonder', 'Gönder');
  static String get oneriTamamBaslik => UzakAyar.yazi('oneriTamamBaslik', 'Teşekkür ederiz');
  static String get oneriTamamDugme => UzakAyar.yazi('oneriTamamDugme', 'Tamam');
  static String get hakkindaBaslik => UzakAyar.yazi('hakkindaBaslik', 'Kimin Cenazesi');
  static String get hakkindaMetin => UzakAyar.yazi('hakkindaMetin', 'Şehrinizdeki cenazelerden haberdar olun. Sayfanıza eklediğiniz bilgiler silinmez. Sürüm 0.1.19');
  static String get gizlilikBaslik => UzakAyar.yazi('gizlilikBaslik', 'Gizlilik');
  // 21.10.2026 Play denetimi: metin KODA eşit olmalı (tam metin: kimincenazesi.com/gizlilik)
  static String get gizlilikMetin => UzakAyar.yazi('gizlilikMetin', 'Okumak için hesap gerekmez; seçtiğiniz adres ve Sayfanıza eklediğiniz bilgiler yalnız bu cihazda tutulur. Din görevlisi olarak kayıt olursanız Diyanet e-posta adresiniz, adınız, görev yeriniz ve panel parolanız sunucuda saklanır; hesabınızı panel menüsünden silebilirsiniz. Bildirim izni isteğe bağlıdır. Konum izni istenmez, uygulamada reklam yoktur.');
  static String get gizlilikBaglantiYazi => UzakAyar.yazi('gizlilikBaglantiYazi', 'Gizlilik politikasının tam metni');
  static String get gizlilikUrl => UzakAyar.yazi('gizlilikUrl', 'https://kimincenazesi.com/gizlilik');
  static String get modalKapat => UzakAyar.yazi('modalKapat', 'Tamam');
  static String get iletisimEposta => UzakAyar.yazi('iletisimEposta', 'iletisim@kimincenazesi.com');

  // 11. Hata ve uyarı
  static String get hataBaglanti => UzakAyar.yazi('hataBaglanti', 'Bağlantı kurulamadı. İlanlar bağlantı gelince yenilenir.');
  static String get hataDogrulama => UzakAyar.yazi('hataDogrulama', 'Veri doğrulanamadı. Güvenliğiniz için ilanlar gösterilmiyor. Biraz sonra yeniden deneyin; sorun sürerse uygulamayı güncelleyin.');
  static String get hataVeri => UzakAyar.yazi('hataVeri', 'Cenaze ilanları şu an yüklenemedi. Biraz sonra yeniden deneyin.');
  static String get hataTekrar => UzakAyar.yazi('hataTekrar', 'Yeniden deneyin');
  static String bilgiGuncelleme(String saat) => UzakAyar.kalip('bilgiGuncelleme', 'Son güncelleme $saat', [saat]);

  // 12. Alt sekmeler
  static List<String> get sekmeler => UzakAyar.liste('sekmeler', const ['İlanlar', 'Sayfam', 'Dualar', 'Hatırla']);
  static String get sekmePanel => UzakAyar.yazi('sekmePanel', 'Panel'); // 5. sekme: yalnız din görevlisi oturumu varken (URUN §53)
  // Panel parolası (URUN §53; ölçü: tasarim/sablon.html panelEkraniCiz)
  static String get panelGorevliBaslik => UzakAyar.yazi('panelGorevliBaslik', 'Bu paneli din görevlileri kullanabilir.');
  static String get panelGorevliAciklama => UzakAyar.yazi('panelGorevliAciklama', 'Din görevlisi misiniz? Kayıt olun.');
  static String get panelKayitDugme => UzakAyar.yazi('panelKayitDugme', 'Kayıt olun');
  static String get pinBelirleBaslik => UzakAyar.yazi('pinBelirleBaslik', 'Panel parolası belirleyin');
  static String get pinBelirleAciklama => UzakAyar.yazi('pinBelirleAciklama', 'Birilerinin sizin hesabınıza girip kötü niyetli/yanıltıcı paylaşımlar yapmasını önlemek için 4 haneli parola belirleyin.');
  static String get pinAlan1 => UzakAyar.yazi('pinAlan1', '4 haneli parola');
  static String get pinAlan2 => UzakAyar.yazi('pinAlan2', 'Yeniden yazın');
  static String get pinKaydet => UzakAyar.yazi('pinKaydet', 'Kaydet');
  static String get pinRakam => UzakAyar.yazi('pinRakam', '4 rakam yazın.');
  static String get pinFarkli => UzakAyar.yazi('pinFarkli', 'İki parola aynı değil.');
  static String get pinKaydedildi => UzakAyar.yazi('pinKaydedildi', 'Parola kaydedildi.');
  static String get pinGirBaslik => UzakAyar.yazi('pinGirBaslik', 'Panel parolanız');
  static String get pinGirAciklama => UzakAyar.yazi('pinGirAciklama', 'Panele girmek için 4 haneli parolanızı yazın.');
  static String get pinGirAlan => UzakAyar.yazi('pinGirAlan', 'Parola');
  static String get pinGir => UzakAyar.yazi('pinGir', 'Panele gir');
  static String get pinUnuttum => UzakAyar.yazi('pinUnuttum', 'Parolamı unuttum');
  static String get pinYanlis => UzakAyar.yazi('pinYanlis', 'Parola yanlış.');
  static String pinYanlisKalan(int n) => UzakAyar.kalip('pinYanlisKalan', 'Parola yanlış. Kalan hak: $n', ['$n']);
  static String pinBekle(int sn) => UzakAyar.kalip('pinBekle', 'Çok fazla yanlış deneme. $sn saniye sonra yeniden deneyin.', ['$sn']);
  static String get pinSunucuyaYok => UzakAyar.yazi('pinSunucuyaYok', 'Parola sunucuya kaydedilemedi; hatırlatma çalışmayabilir.');
  static String pinGonderildi(String adres) => UzakAyar.kalip('pinGonderildi', 'Parolanız $adres adresine gönderildi.', [adres]);
  static String get pinGonderilemedi => UzakAyar.yazi('pinGonderilemedi', 'Parola şu an gönderilemedi. Daha sonra yeniden deneyin.');
  static String get pinSunucudaYok => UzakAyar.yazi('pinSunucudaYok', 'Parolanız sunucuda kayıtlı değil; hatırlatma gönderilemez.');
  static String get pinGunlukSinir => UzakAyar.yazi('pinGunlukSinir', 'Bugün en çok 3 kez gönderilebilir. Yarın yeniden deneyin.');
  static String get pinGonderildiBaslik => UzakAyar.yazi('pinGonderildiBaslik', 'Parolanız gönderildi');
  static String get pinGonderildiBir => UzakAyar.yazi('pinGonderildiBir', 'Parolanız e-postanıza gönderildi.');
  static String pinGonderildiIki(String adres) => UzakAyar.kalip('pinGonderildiIki', 'Parolanızı $adres adresine gönderdik. Gelen kutunuza bakın, parolanız gönderilmiştir.', [adres]);
  static String get pinGonderilemediSayfa => UzakAyar.yazi('pinGonderilemediSayfa', 'Gönderilemedi; biraz sonra yeniden deneyin.');
  static String get pinTamam => UzakAyar.yazi('pinTamam', 'Tamam');
  static String get pinDegistir => UzakAyar.yazi('pinDegistir', 'Parolamı değiştir');
  static String get pinDegistirBaslik => UzakAyar.yazi('pinDegistirBaslik', 'Parolanızı değiştirin');
  static String get pinEski => UzakAyar.yazi('pinEski', 'Eski parola');
  static String get pinYeni => UzakAyar.yazi('pinYeni', 'Yeni parola');
  static String get pinEskiYanlis => UzakAyar.yazi('pinEskiYanlis', 'Eski parola yanlış.');
  static String get pinDegisti => UzakAyar.yazi('pinDegisti', 'Parolanız değişti.');
  static String get panelKilitle => UzakAyar.yazi('panelKilitle', 'Paneli kilitle');
  static String get panelKilitlendi => UzakAyar.yazi('panelKilitlendi', 'Panel kilitlendi.');
  // İlan kutusu (15.10.2026): her il/ilçe liste sayfasının üstünde
  static String get ilanKutusuGorevli => UzakAyar.yazi('ilanKutusuGorevli', 'Cenaze ilanınızın bu sayfada görülmesini istiyorsanız bulunduğunuz bölgedeki din görevlisinden cenaze ilanınızı paylaşmasını talep edebilirsiniz.'); // tek paragraf (site sahibi 15.10.2026, birebir); başlık yok
  static String get ilanKutusuKayit => UzakAyar.yazi('ilanKutusuKayit', 'Din görevlisi misiniz? Kayıt olun.');
  static String get ilanKutusuSehit => UzakAyar.yazi('ilanKutusuSehit', 'Şehit cenazesi ilanı nasıl verilir?');

  // Şehit cenazesi ilanları YALNIZ din görevlisi panelinden (15.10.2026)
  static String get sehitBilgiBaslik => UzakAyar.yazi('sehitBilgiBaslik', 'Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır.');
  static String get sehitBilgiGovde => UzakAyar.yazi('sehitBilgiGovde', 'Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur.');
  static String get sehitBilgiKapanis => UzakAyar.yazi('sehitBilgiKapanis', 'Başınız sağ olsun. Şehidimizin ruhu şad olsun.');
  static String get sehitBilgiUst => UzakAyar.yazi('sehitBilgiUst', 'Şehit cenazesi');
  static String get gorevliSehitAnahtar => UzakAyar.yazi('gorevliSehitAnahtar', 'Şehit cenazesi');

  // 12. Din görevlisi (0.1.5, URUN-TASLAGI §37). §22: sade dil, ünlem yok, pazar dili yok.
  static String get gorevliUst => UzakAyar.yazi('gorevliUst', 'Din görevlisi');
  static String get gorevliBaslik => UzakAyar.yazi('gorevliBaslik', 'Din Görevlisi İlanı');
  static String get gorevliGirisEtiket => UzakAyar.yazi('gorevliGirisEtiket', 'Din görevlileri için');
  static String get gorevliMadde1 => UzakAyar.yazi('gorevliMadde1', 'Cami ve köy cenazelerini ilk siz duyurabilirsiniz');
  static String get gorevliMadde2 => UzakAyar.yazi('gorevliMadde2', 'İl ve ilçe görev yerinize göre sabittir');
  static String get gorevliMadde3 => UzakAyar.yazi('gorevliMadde3', 'İlanlarınızı panelden düzenler ya da kaldırırsınız');
  // ---- Diyanet e-posta doğrulaması (URUN §45, 16.10.2026) ----
  static String get gorevliEpostaBaslik => UzakAyar.yazi('gorevliEpostaBaslik', 'Din görevlisi olduğunuzu teyit edelim');
  static String get gorevliEpostaAciklama => UzakAyar.yazi('gorevliEpostaAciklama', 'Diyanet İşleri Başkanlığının size tahsis ettiği e-posta adresinize bir kod göndereceğiz. Gelen kodu bir sonraki ekrana yazın.');
  static String get gorevliKullanici => UzakAyar.yazi('gorevliKullanici', 'Diyanet kullanıcı adınız');
  static String get gorevliKullaniciYer => UzakAyar.yazi('gorevliKullaniciYer', 'kullaniciadi');
  static String get gorevliAlanAdi => UzakAyar.yazi('gorevliAlanAdi', '@diyanet.gov.tr');
  static String get gorevliKodGonderDugme => UzakAyar.yazi('gorevliKodGonderDugme', 'Kodu gönder');
  static String get gorevliNasilGiris => UzakAyar.yazi('gorevliNasilGiris', 'Diyanet e-posta adresime nasıl giriş yapabilirim?');
  static String get gorevliNasilBaslik => UzakAyar.yazi('gorevliNasilBaslik', 'Diyanet e-posta adresiniz');
  /// Kılavuz penceresi: 6 kısa madde
  static List<String> get gorevliNasil6 => UzakAyar.liste('gorevliNasil6', const [
    'Diyanet her personeline bir e-posta adresi verir.',
    'Adresiniz: DİBBYS kullanıcı adınız@diyanet.gov.tr',
    'Tarayıcıya posta.diyanet.gov.tr yazın.',
    'Kullanıcı adı: DİBBYSkullanıcıadınız@diyanet.gov.tr',
    'Şifre: DİBBYS şifreniz. Giriş yapın.',
    'Gelen kutusundaki kodu uygulamaya girin.',
  ]);
  /// Kod ekranındaki 5 madde (kişinin adı dolu)
  static List<String> gorevliTarif5(String adres) => [
        'Adresiniz: $adres',
        'Tarayıcıya posta.diyanet.gov.tr yazın.',
        'Kullanıcı adı: $adres',
        'Şifre: DİBBYS şifreniz. Giriş yapın.',
        'Gelen kutusundaki kodu aşağıya yazın.',
      ];
  static String gorevliKodGitti(String adres) => UzakAyar.kalip('gorevliKodGitti', 'Kod gönderildi: $adres', [adres]);
  static String get gorevliKodGecerli => UzakAyar.yazi('gorevliKodGecerli', 'Kod 10 dakika geçerlidir.');
  static String get gorevliKodDogrulaDugme => UzakAyar.yazi('gorevliKodDogrulaDugme', 'Doğrula ve paneli aç');
  static String get gorevliKodYanlis => UzakAyar.yazi('gorevliKodYanlis', 'Kod yanlış ya da süresi dolmuş. Yeniden deneyin ya da yeni kod isteyin.');
  static String get gorevliKodGecersiz => UzakAyar.yazi('gorevliKodGecersiz', 'Kod 5 kez yanlış girildi; yeni kod isteyin.');
  static String get gorevliKullaniciHata => UzakAyar.yazi('gorevliKullaniciHata', 'Kullanıcı adı geçersiz. Yalnız harf, rakam, nokta, tire ve alt çizgi kullanın.');
  static String get gorevliGunlukSinir => UzakAyar.yazi('gorevliGunlukSinir', 'Bugün için kod sınırına ulaştınız. Yarın yeniden deneyin.');
  static String get gorevliDondurulmus => UzakAyar.yazi('gorevliDondurulmus', 'Hesabınız şu an kullanıma kapalı.');
  static String get gorevliProfilYok => UzakAyar.yazi('gorevliProfilYok', 'Görev bilgilerinizi ilk ilanınızda bir kez yazacaksınız.');
  static String get gorevliProfilBaslik => UzakAyar.yazi('gorevliProfilBaslik', 'Görev bilgileriniz');
  static String get gorevliProfilAciklama => UzakAyar.yazi('gorevliProfilAciklama', 'İlanlarınız bu görev yeriyle yayımlanır. Bilgiler hesabınızda saklanır.');
  static String get gorevliKaydetDugme => UzakAyar.yazi('gorevliKaydetDugme', 'Kaydet ve devam et');
  static String get gorevliYerDegisti => UzakAyar.yazi('gorevliYerDegisti', 'Görev yerim değişti');
  static String get gorevliYerDegistiAciklama => UzakAyar.yazi('gorevliYerDegistiAciklama', 'Yeni ilanlarınız bu görev yeriyle paylaşılır; önceki ilanlar değişmez.');
  static String get gorevliYerGuncellendi => UzakAyar.yazi('gorevliYerGuncellendi', 'Görev yeriniz güncellendi.');
  static String get gorevliTamam => UzakAyar.yazi('gorevliTamam', 'Tamam');
  static String get gorevliCikisYap => UzakAyar.yazi('gorevliCikisYap', 'Çıkış yap');
  static String get gorevliCikisYapildi => UzakAyar.yazi('gorevliCikisYapildi', 'Çıkış yaptınız.');
  // 21.10.2026 Play: uygulama içi hesap silme (⋮ menüsü); web yolu kimincenazesi.com/hesap-silme
  static String get gorevliHesapSil => UzakAyar.yazi('gorevliHesapSil', 'Hesabımı sil');
  static String get gorevliHesapSilBaslik => UzakAyar.yazi('gorevliHesapSilBaslik', 'Hesabınızı silmek istiyor musunuz?');
  static String get gorevliHesapSilMetin => UzakAyar.yazi('gorevliHesapSilMetin', 'Hesabınız, oturumunuz ve yayımladığınız bütün ilanlar sunucudan silinir. Bu işlem geri alınamaz.');
  static String get gorevliHesapSilVazgec => UzakAyar.yazi('gorevliHesapSilVazgec', 'Vazgeç');
  static String get gorevliHesapSilindi => UzakAyar.yazi('gorevliHesapSilindi', 'Hesabınız silindi.');
  static String get gorevliHesapSilHata => UzakAyar.yazi('gorevliHesapSilHata', 'Hesap silinemedi. İnternet bağlantınızı kontrol edip yeniden deneyin.');
  static String get gorevliAd => UzakAyar.yazi('gorevliAd', 'Ad soyad');
  static String get gorevliAdYer => UzakAyar.yazi('gorevliAdYer', 'Kartınızdaki gibi');
  // 16.10.2026 sahibi: "soyadımı yanlış yazdım, düzeltemedim" -> panel menüsünde ad-soyad düzeltme
  static String get gorevliBilgiDuzenle => UzakAyar.yazi('gorevliBilgiDuzenle', 'Bilgilerimi düzenle');
  static String get gorevliBilgiDuzenleAciklama => UzakAyar.yazi('gorevliBilgiDuzenleAciklama', 'Ad soyad, il, ilçe, görev yeri ve unvan bilgilerinizi düzeltebilirsiniz. Daha önce paylaştığınız ilanlar değişmez.');
  static String get gorevliAdKaydet => UzakAyar.yazi('gorevliAdKaydet', 'Kaydet');
  static String get gorevliBilgiGuncellendi => UzakAyar.yazi('gorevliBilgiGuncellendi', 'Bilgileriniz güncellendi.');
  static String get gorevliAdHakDoldu => UzakAyar.yazi('gorevliAdHakDoldu', 'Ad soyad düzeltme hakkınız doldu. Destek için iletisim@kimincenazesi.com adresine yazın.');
  static String get gorevliYer => UzakAyar.yazi('gorevliYer', 'Görev yeri');
  static String get gorevliYerYer => UzakAyar.yazi('gorevliYerYer', 'Cami ya da köy adı');
  static String get gorevliUnvan => UzakAyar.yazi('gorevliUnvan', 'Unvan');
  // [ekrandaki, Worker değeri]
  static List<List<String>> get gorevliUnvanlar => UzakAyar.ikiliListe('gorevliUnvanlar', const [
    ['İmam-Hatip', 'İmam-Hatip'],
    ['Müezzin-Kayyım', 'Müezzin-Kayyım'],
    ['Kur\'an Kursu Öğreticisi', 'Kur\'an Kursu Öğreticisi'],
    ['Vaiz', 'Vaiz'],
    ['Din Hizmetleri Uzmanı', 'Din Hizmetleri Uzmanı'],
    ['Müftü Yardımcısı', 'Müftü Yardımcısı'],
  ]);
  static String get gorevliKontrolMetin => UzakAyar.yazi('gorevliKontrolMetin', 'Başvurunuz kontrol ediliyor. Onaylanınca tarafınıza bilgi verilecek ve din görevlisi paneliniz açılacaktır.');
  // Panel açıkken, onay beklerken (kontrolde)
  static String get gorevliKontrolBilgi => UzakAyar.yazi('gorevliKontrolBilgi', 'Başvurunuz kontrol ediliyor. Hesabınız onaylanınca paneldeki "İlan paylaş" düğmesi etkin hale gelir. Onay verilmezse panel ve hesap silinir.');
  static String get gorevliSilindi => UzakAyar.yazi('gorevliSilindi', 'Başvurunuz onaylanmadı; hesap silindi.');
  static String get gorevliOnayBildirimi => UzakAyar.yazi('gorevliOnayBildirimi', 'Başvurunuz onaylandı; din görevlisi paneliniz açıldı.');
  static String get gorevliOturumDoldu => UzakAyar.yazi('gorevliOturumDoldu', 'Oturumunuz sona erdi. Diyanet e-posta kodunuzla yeniden giriş yapabilirsiniz.');
  static String get gorevliPaneleGit => UzakAyar.yazi('gorevliPaneleGit', 'Panele git');
  static String get gorevliBittiUst => UzakAyar.yazi('gorevliBittiUst', 'Başvuru');
  // Panel
  static String get gorevliPanelUst => UzakAyar.yazi('gorevliPanelUst', 'Din görevlisi paneli');
  static String get gorevliIlanPaylas => UzakAyar.yazi('gorevliIlanPaylas', 'İlan paylaş');
  static String gorevliIlanlarim(int n) => UzakAyar.kalip('gorevliIlanlarim', 'İlanlarım ($n)', ['$n']);
  static String get gorevliIlanlarimBaslik => UzakAyar.yazi('gorevliIlanlarimBaslik', 'İlanlarım');
  static String get gorevliKendiBaslik => UzakAyar.yazi('gorevliKendiBaslik', 'Sizin eklediğiniz ilanlar');
  static String get gorevliIlanlarimAciklama => UzakAyar.yazi('gorevliIlanlarimAciklama', 'Bu sayfada sizin eklediğiniz ve sistem tarafından yüklenen ilanlar görüntülenir. Sistemin yüklediği ilanlarda bir hata görürseniz düzeltebilirsiniz, düzeltme ilanlar sayfasında otomatik olarak uygulanır.'); // sahibi 16.10 (birebir)
  static String get gorevliBolgeBaslik => UzakAyar.yazi('gorevliBolgeBaslik', 'Sistemin yüklediği ilanlar');
  static String get gorevliBolgeDuzelt => UzakAyar.yazi('gorevliBolgeDuzelt', 'İlanı düzelt'); // sahibi 16.10: bölge ilanında düğme adı
  static String get gorevliOtomatik => UzakAyar.yazi('gorevliOtomatik', 'Sistem'); // sahibi 16.10: 'Otomatik' değil 'Sistem'
  static String get gorevliSonIlanlar => UzakAyar.yazi('gorevliSonIlanlar', 'Son ilanlar');
  static String get gorevliIlanYok => UzakAyar.yazi('gorevliIlanYok', 'Henüz ilan paylaşmadınız.');
  static String get gorevliYerKilit => UzakAyar.yazi('gorevliYerKilit', 'İl ve ilçe görev yerinize göre sabittir.');
  static String get gorevliIlanFormBaslik => UzakAyar.yazi('gorevliIlanFormBaslik', 'Cenaze ilanı');
  static String get gorevliMahalleKoy => UzakAyar.yazi('gorevliMahalleKoy', 'Mahalle ya da köy');
  static String get gorevliGonder => UzakAyar.yazi('gorevliGonder', 'İlanı yayımla');
  static String get gorevliKaydet => UzakAyar.yazi('gorevliKaydet', 'Değişikliği kaydet');
  static String get gorevliYerKaydet => UzakAyar.yazi('gorevliYerKaydet', 'Kaydet');
  static String get gorevliDuzenle => UzakAyar.yazi('gorevliDuzenle', 'Düzenle');
  static String get gorevliKaldir => UzakAyar.yazi('gorevliKaldir', 'İlanı kaldır');
  static String get gorevliIlanTamam => UzakAyar.yazi('gorevliIlanTamam', 'İlanınız yayımlandı. Allah rahmet eylesin.');
  static String get gorevliIlanGuncel => UzakAyar.yazi('gorevliIlanGuncel', 'İlanınız güncellendi.');
  static String get gorevliIlanKalkti => UzakAyar.yazi('gorevliIlanKalkti', 'İlan kaldırıldı.');
  static String get gorevliDonduruldu => UzakAyar.yazi('gorevliDonduruldu', 'Hesabınız şu an kullanıma kapalı.');
  static String get gorevliYukleniyor => UzakAyar.yazi('gorevliYukleniyor', 'Yükleniyor');
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
  static String get gorevliDuzelt => UzakAyar.yazi('gorevliDuzelt', 'Düzelt');
  static String get gorevliDuzeltmeAlindi => UzakAyar.yazi('gorevliDuzeltmeAlindi', 'Düzeltmeniz alındı; bir sonraki güncellemede yayına girer.');
  static String get gorevliDuzeltildi => UzakAyar.yazi('gorevliDuzeltildi', 'Düzeltildi');
  // Sorumluluk uyarısı (URUN §54, birebir)
  static String get gorevliSorumlulukBaslik => UzakAyar.yazi('gorevliSorumlulukBaslik', 'Paylaşımlarınızın sorumluluğu');
  static String get gorevliSorumlulukMetin => UzakAyar.yazi('gorevliSorumlulukMetin', 'Bu panelden yapılacak ilanlardaki bilgilerin doğru olma sorumluluğu din görevlisine aittir. Yanıltıcı veya yanlış bilgi paylaşımından hesabın sahibi olan din görevlisi sorumludur.');
  static String get gorevliSorumlulukKabul => UzakAyar.yazi('gorevliSorumlulukKabul', 'Anladım, kabul ediyorum');
  static String get gorevliKvkkBaslik => UzakAyar.yazi('gorevliKvkkBaslik', 'Kişisel verileriniz');
  static String get gorevliKvkkOku => UzakAyar.yazi('gorevliKvkkOku', 'Okudum, anladım');
  static String get gorevliKvkkTam => UzakAyar.yazi('gorevliKvkkTam', 'Tam metin');
  // 16.10.2026 sahibi: "Cloudflare / yurt dışı" satırı kısa uyarıda YOK (korkutur); yurt dışı aktarımı tam metinde (Gizlilik) kalır
  static List<String> get gorevliKvkkMetin => UzakAyar.liste('gorevliKvkkMetin', const [
    'Tuttuğumuz veriler: Diyanet e-posta adresiniz, ad-soyadınız, görev yeriniz ve unvanınız, il-ilçeniz, panel parolanız (şifreli), paylaştığınız ilanlar.',
    'Amaç: din görevlisi olduğunuzu teyit etmek ve ilan paylaşmanızı sağlamak.',
    'Süre: hesabınız açık kaldıkça; ilanlar 120 gün; e-posta kodu 10 dakika.',
    'Telefon numarası, kimlik ya da personel kartı fotoğrafı toplanmaz.',
    'Verileriniz üçüncü kişilerle paylaşılmaz.',
    'Haklarınız (KVKK md. 11): verilerinize erişme, düzeltme ve silme isteğinde bulunabilirsiniz. Hesabınızı panel menüsündeki "Hesabımı sil" ile istediğiniz an silebilirsiniz; ayrıntı için Tam metin.',
  ]);

  static Map<String, String> get gorevliDurumEtiket => UzakAyar.harita('gorevliDurumEtiket', const {
    'yayinda': 'Din görevlisi', // sahibi 16.10: hocanın kendi ilanında etiket 'Din görevlisi'
    'gizli': 'Gizlendi',
    'iptal': 'Kaldırıldı',
    'bekliyor': 'Kontrolde',
    'red': 'Yayımlanmadı',
  });

}
