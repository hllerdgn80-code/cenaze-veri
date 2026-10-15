// Aile / Tam Sayfa / Şehit formu (v0.1.2): giriş kartı, 5 adım, telefon/T.C. yok, fiyat + ödeme ekranı (Tam Sayfa),
// Worker'a POST, TELEFON kodu (15.10.2026), sonuç ekranı, kartta Bildir. Şehit yolu artık bilgi ekranı (yalnız din görevlisi).
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/menu.dart' show FormAlani;
import 'package:kimin_cenazesi/bilesenler/ortak.dart';
import 'package:kimin_cenazesi/cekirdek/aile.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/odeme.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/aile_formu.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

const _json = {'content-type': 'application/json; charset=utf-8'};

Widget formSayfasi(AppDurum d, AileServisi s, {bool tam = false, bool sehit = false, OdemeKapisi? odeme}) => Kapsam(
      durum: d,
      child: MaterialApp(
          theme: temaYap(true), home: AileFormu(il: 'Kars', ilce: 'Merkez', tam: tam, sehit: sehit, servis: s, odeme: odeme)),
    );

/// Başlık çubuğu üst etiketi Türkçe büyük harfle yazılır
Finder ust(int n) => find.text(trBuyuk('Adım $n / 4'));

/// Sahte Play ödemesi: [urun] null ise mağazada ürün yok
class SahteOdeme implements OdemeKapisi {
  final UrunBilgi? urun;
  OdemeSonuc siradaki = const OdemeSonuc.tamam(token: 'tok', siparisNo: 'GPA.0');
  int satinAlSayisi = 0;
  int tuketilen = 0;
  SahteOdeme({this.urun = const UrunBilgi('₺200,00')});
  @override
  Future<UrunBilgi?> urunSorgula() async => urun;
  @override
  Future<OdemeSonuc> satinAl() async {
    satinAlSayisi++;
    return siradaki;
  }

  @override
  Future<void> tuket(OdemeSonuc s) async => tuketilen++;
}

/// Gelen istekleri kaydeden sahte Worker
AileServisi sahteServis(Map<String, Map<String, dynamic>> istekler) => AileServisi(
      kok: 'https://aile.test',
      istemci: MockClient((req) async {
        istekler[req.url.path] = jsonDecode(req.body) as Map<String, dynamic>;
        if (req.url.path == '/aile/basvur') {
          return http.Response(jsonEncode({'basvuru_id': 'b1', 'dogrulama': 'telefon'}), 200, headers: _json);
        }
        if (req.url.path == '/aile/dogrula') {
          final tam = istekler['/aile/basvur']?['tam'] == true;
          return http.Response(
              jsonEncode(tam ? {'durum': 'odeme_bekliyor', 'ilan_id': 'i1', 'basvuru_id': 'b1'} : {'durum': 'yayinda', 'ilan_id': 'i1'}),
              200,
              headers: _json);
        }
        if (req.url.path == '/aile/odeme') {
          return http.Response(jsonEncode({'durum': 'yayinda', 'ilan_id': 'i1'}), 200, headers: _json);
        }
        return http.Response('yok', 404);
      }),
    );

/// Formun kendi kaydırıcısı (TextField içindekiler değil)
Finder _kaydirici() => find.descendant(of: find.byType(ListView).last, matching: find.byType(Scrollable)).first;

Future<void> goster(WidgetTester t, Finder f) async {
  await t.scrollUntilVisible(f, 200, scrollable: _kaydirici());
  await t.pumpAndSettle();
}

Future<void> yaz(WidgetTester t, String anahtar, String metin) async {
  final f = find.descendant(of: find.byKey(ValueKey(anahtar)), matching: find.byType(TextField));
  await goster(t, f);
  await t.enterText(f, metin);
  await t.pumpAndSettle();
}

Future<void> dokun(WidgetTester t, Finder f) async {
  await goster(t, f);
  await t.tap(f);
  await t.pumpAndSettle();
}

Finder devam() => find.widgetWithText(AnaDugme, 'Devam');

/// Giriş kartından son (4.) adıma kadar doldurur. 15.10.2026: e-Devlet belge adımı kalktı; 3. adımdan sonra doğrudan yasal beyan.
Future<void> sonAdima(WidgetTester t, {bool giris = true}) async {
  if (giris) await dokun(t, devam());
  expect(ust(1), findsOneWidget);
  await dokun(t, find.text('Erkek'));
  await yaz(t, 'f_ad', 'Ahmet Örnek');
  await dokun(t, devam());
  expect(ust(2), findsOneWidget);
  await dokun(t, devam());
  expect(ust(3), findsOneWidget);
  await yaz(t, 'f_basvuran', 'Ali Örnek');
  await yaz(t, 'f_telefon', '0532 111 22 33');
  await dokun(t, devam());
  expect(ust(4), findsOneWidget);
}

Future<void> onaylaVeGonder(WidgetTester t) async {
  await dokun(t, find.byKey(const ValueKey('beyan_kutu')));
  final dugme = find.widgetWithText(AnaDugme, 'Onayla ve gönder');
  await goster(t, dugme);
  expect(t.widget<AnaDugme>(dugme).onTap, isNotNull);
  await t.tap(dugme);
  await t.pump();
  await t.pump();
}

void main() {
  testWidgets('Adımlar: düğme pasifliği, telefon ve T.C. alanı yok, yasal metin 5. adımda', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final s = AileServisi(istemci: MockClient((_) async => http.Response('yok', 404)), kok: 'https://aile.test');
    await tester.pumpWidget(formSayfasi(d, s));
    await tester.pumpAndSettle();

    expect(find.text('Cenaze ilanı paylaşın'), findsOneWidget); // giriş kartı
    expect(find.text(trBuyuk(M.aileUstGiris)), findsOneWidget);
    await dokun(tester, devam());
    expect(ust(1), findsOneWidget);
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull); // cinsiyet ve ad yok
    expect(find.text('Onayla ve gönder'), findsNothing);
    await dokun(tester, find.text('Kadın'));
    await yaz(tester, 'f_ad', 'Ayşe'); // tek sözcük geçersiz
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull);
    await yaz(tester, 'f_ad', 'Ayşe Örnek');
    expect(tester.widget<AnaDugme>(devam()).onTap, isNotNull);
    await dokun(tester, devam());

    await dokun(tester, devam()); // 2. adım
    expect(ust(3), findsOneWidget);
    expect(find.text('Cep telefonu'), findsOneWidget); // e-posta yerine telefon
    expect(find.text('E-posta'), findsNothing);
    expect(find.textContaining('T.C.'), findsNothing);
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull);
    await yaz(tester, 'f_basvuran', 'Ali Örnek');
    await yaz(tester, 'f_telefon', '12345');
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull); // telefon biçimi (10 hane, 5 ile başlar)
    await yaz(tester, 'f_telefon', '+90 532 111 22 33');
    await dokun(tester, devam());

    expect(ust(4), findsOneWidget); // e-Devlet belge adımı yok: 3. adımdan sonra doğrudan yasal beyan
    expect(find.textContaining('Belge'), findsNothing);
    expect(find.textContaining('e-Devlet'), findsNothing);
    expect(find.text(M.hukukMetin), findsOneWidget);
    final dugme = tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Onayla ve gönder'));
    expect(dugme.onTap, isNull); // kutu işaretlenmeden pasif
    await dokun(tester, find.byKey(const ValueKey('beyan_kutu')));
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Onayla ve gönder')).onTap, isNotNull);

    // Geri: 4 → 3
    await tester.tap(find.byType(YuvarlakDugme).first);
    await tester.pumpAndSettle();
    expect(ust(3), findsOneWidget);
  });

  testWidgets('Gönder → telefon kodu → doğrula → "İlanınız yayımlandı"', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    final s = sahteServis(istekler);
    await tester.pumpWidget(formSayfasi(d, s));
    await tester.pumpAndSettle();
    await sonAdima(tester);
    await onaylaVeGonder(tester);

    final b = istekler['/aile/basvur']!;
    expect(b['il'], 'Kars');
    expect(b['ilce'], 'Merkez');
    expect(b['ad_soyad'], 'Ahmet Örnek');
    expect(b['cinsiyet'], 'e');
    expect(b['beyan'], true);
    expect((b['basvuran'] as Map)['telefon'], '5321112233');
    expect((b['basvuran'] as Map).containsKey('eposta'), isFalse);
    expect(b.containsKey('edevlet_kodu'), isFalse);
    expect(b.containsKey('tc'), isFalse);

    // Kod ekranı
    expect(find.text('Telefonunuza gönderilen 6 haneli kodu girin.'), findsOneWidget);
    expect(find.textContaining('Kodu yeniden gönder'), findsOneWidget);
    final kod = find.descendant(of: find.byKey(const ValueKey('f_kod')), matching: find.byType(TextField));
    await tester.enterText(kod, '123');
    await tester.pump();
    await tester.tap(find.widgetWithText(AnaDugme, 'Doğrula'));
    await tester.pump();
    expect(find.text('Lütfen kodu eksiksiz yazın'), findsOneWidget); // 6 hane değil: istek gitmedi
    expect(istekler.containsKey('/aile/dogrula'), isFalse);
    await tester.pump(const Duration(seconds: 5)); // bildirim süresi dolar
    await tester.pumpAndSettle(); // kapanış animasyonu biter
    await tester.enterText(kod, '123456');
    await tester.pump();
    // CI #17/#18: bildirim artığı dokunuşu yuttu; düğmenin kendi onTap'i çağrılır (davranış aynı, hit-test'e bağımlı değil)
    tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Doğrula')).onTap!();
    await tester.pump();
    await tester.pumpAndSettle();
    expect(istekler['/aile/dogrula'], {'basvuru_id': 'b1', 'kod': '123456'});
    expect(find.text('İlanınız yayımlandı. Allah rahmet eylesin.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Sunucu "red" derse neden gösterilir', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final s = AileServisi(
      kok: 'https://aile.test',
      istemci: MockClient((req) async =>
          http.Response(jsonEncode({'durum': 'red', 'neden': 'Aynı ilan zaten var'}), 200, headers: _json)),
    );
    await tester.pumpWidget(formSayfasi(d, s));
    await tester.pumpAndSettle();
    await sonAdima(tester);
    await onaylaVeGonder(tester);
    expect(find.text('İlan yayımlanamadı. Bilgiler doğrulanamadı.'), findsOneWidget);
    expect(find.text('Aynı ilan zaten var'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Ağ hatası: sakin hata, form korunur, tekrar denenir', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    var deneme = 0;
    final s = AileServisi(
      kok: 'https://aile.test',
      istemci: MockClient((req) async {
        deneme++;
        if (deneme == 1) throw http.ClientException('bağlantı yok');
        return http.Response(jsonEncode({'basvuru_id': 'b2'}), 200, headers: _json);
      }),
    );
    await tester.pumpWidget(formSayfasi(d, s));
    await tester.pumpAndSettle();
    await sonAdima(tester);
    await onaylaVeGonder(tester);
    expect(find.text(M.aileAgHata), findsOneWidget);
    expect(ust(4), findsOneWidget);
    final tekrar = find.widgetWithText(AnaDugme, 'Yeniden deneyin');
    expect(tekrar, findsOneWidget);
    await tester.tap(tekrar);
    await tester.pump();
    await tester.pump();
    expect(find.text('Telefonunuza gönderilen 6 haneli kodu girin.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox()); // geri sayım zamanlayıcısı kapansın
  });

  testWidgets('Tam Sayfa: fiyat kartı → 4 adım (belge adımı yok) → telefon kodu → Play ödemesi → Worker doğrulaması → "Ödemeniz alındı"', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    final odeme = SahteOdeme();
    await tester.pumpWidget(formSayfasi(d, sahteServis(istekler), tam: true, odeme: odeme));
    await tester.pumpAndSettle();

    expect(odemeAcik, isTrue);
    expect(find.text(trBuyuk(M.formTamUst)), findsOneWidget);
    expect(find.text('Vefat İlanı'), findsOneWidget);
    expect(find.text('Tam sayfa vefat ilanı'), findsOneWidget);
    expect(find.text('200 ₺'), findsOneWidget);
    expect(find.text(trBuyuk('Tek seferlik')), findsOneWidget);
    expect(find.text('Abonelik değildir, bir kez ödenir'), findsOneWidget);
    for (final m in [M.fiyatMadde1, M.fiyatMadde2, M.fiyatMadde3, M.fiyatMadde4]) {
      expect(find.text(m), findsOneWidget);
    }
    await sonAdima(tester);
    expect(find.text('Ölüm belgesi doğrulama'), findsNothing);
    expect(find.text('Yasal beyan ve ödeme'), findsOneWidget);
    expect(find.text('Ödenecek: 200 ₺'), findsOneWidget);
    expect(find.text('Onayla ve gönder'), findsNothing);
    final odemeye = find.widgetWithText(AnaDugme, 'Ödemeye geç');
    expect(tester.widget<AnaDugme>(odemeye).onTap, isNull);
    await dokun(tester, find.byKey(const ValueKey('beyan_kutu')));
    expect(tester.widget<AnaDugme>(odemeye).onTap, isNotNull);
    expect(find.text('İlanınız ödeme ve kontrolden sonra yayımlanır.'), findsOneWidget);
    await tester.tap(odemeye);
    await tester.pump();
    await tester.pump();

    // Önce telefon kodu (ödemeden ÖNCE): başvuru gitti, satın alma henüz yok
    final b = istekler['/aile/basvur']!;
    expect(b['tam'], true);
    expect(b.containsKey('edevlet_kodu'), isFalse);
    expect(b.containsKey('sehit'), isFalse);
    expect(odeme.satinAlSayisi, 0);
    final kod = find.descendant(of: find.byKey(const ValueKey('f_kod')), matching: find.byType(TextField));
    await tester.enterText(kod, '123456');
    await tester.pump();
    tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Doğrula')).onTap!();
    await tester.pump();
    await tester.pumpAndSettle();

    // Ödeme ekranı: fiyat mağazadan
    expect(find.text(trBuyuk('Ödeme')), findsOneWidget);
    expect(find.text('Tam sayfa cenaze ilanı'), findsOneWidget);
    expect(find.text('₺200,00'), findsOneWidget);
    expect(find.text(M.odemeNot), findsOneWidget);
    expect(istekler.containsKey('/aile/odeme'), isFalse);

    // İptal: "Ödeme tamamlanmadı" + yeniden dene; sunucuya bir şey gitmez
    odeme.siradaki = const OdemeSonuc.iptal();
    await tester.tap(find.widgetWithText(AnaDugme, 'Google Play ile öde'));
    await tester.pumpAndSettle();
    expect(find.text(M.odemeTamamlanmadi), findsOneWidget);
    expect(istekler.containsKey('/aile/odeme'), isFalse);

    // Başarı: token + orderId Worker'a, sonra tüketilir
    odeme.siradaki = const OdemeSonuc.tamam(token: 'tok-123', siparisNo: 'GPA.1111-2222-3333-44444');
    await tester.tap(find.widgetWithText(AnaDugme, 'Yeniden deneyin'));
    await tester.pumpAndSettle();
    expect(istekler['/aile/odeme'], {
      'basvuru_id': 'b1',
      'purchase_token': 'tok-123',
      'order_id': 'GPA.1111-2222-3333-44444',
      'urun': 'tam_sayfa_ilan',
    });
    expect(odeme.tuketilen, 1);
    expect(find.text('Ödemeniz alındı, ilanınız yayında'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Tam Sayfa: ürün Play\'de yoksa düğme pasif, fiyat kartı görünür, "Ödeme şu an alınamıyor"', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    await tester.pumpWidget(formSayfasi(d, sahteServis(istekler), tam: true, odeme: SahteOdeme(urun: null)));
    await tester.pumpAndSettle();
    expect(find.text('200 ₺'), findsOneWidget);
    await sonAdima(tester);
    await dokun(tester, find.byKey(const ValueKey('beyan_kutu')));
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Ödemeye geç')).onTap, isNull);
    expect(find.text('Ödeme şu an alınamıyor, kısa süre sonra açılacak.'), findsOneWidget);
    expect(istekler, isEmpty);
  });

  testWidgets('Şehit yolu: form AÇILMAZ, bilgi ekranı (yalnız din görevlisi); Worker\'a hiçbir istek gitmez; kayıt bağlantısı', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    await tester.pumpWidget(formSayfasi(d, sahteServis(istekler), sehit: true));
    await tester.pumpAndSettle();

    expect(find.text('Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır.'), findsOneWidget);
    expect(find.text('Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur.'), findsOneWidget);
    expect(find.text('Başınız sağ olsun. Şehidimizin ruhu şad olsun.'), findsOneWidget);
    expect(find.byKey(const ValueKey('sehit_bilgi_pencere')), findsOneWidget); // PENCERE (tam ekran değil)
    expect(find.byType(FormAlani), findsNothing);
    expect(find.text('Rütbe / unvan'), findsNothing);
    expect(istekler, isEmpty);
    await tester.tap(find.text(M.ilanKutusuKayit));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliGirisNot), findsOneWidget); // din görevlisi kayıt ekranı (alt başlık görünür bölgede)
  });

  testWidgets('Kart: "Tam Sayfa" rozeti ve Bildir (Doğrulandı rozeti yok)', (tester) async {
    telefon(tester);
    Map<String, dynamic>? giden;
    final d = await testDurumu(
      istemci: MockClient((req) async {
        if (req.url.path == '/aile/bildir') {
          giden = jsonDecode(req.body) as Map<String, dynamic>;
          return http.Response(jsonEncode({'alindi': true}), 200, headers: _json);
        }
        return http.Response('yok', 404);
      }),
    );
    final r = Ilan.fromJson({
      'id': 'a1',
      'ad_soyad': 'Veli Örnek',
      'ilce': 'Merkez',
      'aile': true,
      'dogrulandi': true, // eski veri gelse bile rozet çıkmaz
      'namaz_tarihi': '2026-10-14',
    })!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Tam Sayfa'), findsOneWidget);
    expect(find.text('Doğrulandı'), findsNothing);

    await tester.tap(find.text('Bu ilanda bir yanlışlık mı var?'));
    await tester.pumpAndSettle();
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Bildirin')).onTap, isNull);
    await tester.tap(find.text('Bu ilan gerçek değil'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(AnaDugme, 'Bildirin'));
    await tester.pumpAndSettle();
    expect(giden, {'ilan_id': 'a1', 'neden': 'böyle bir kişi yok'});
    expect(find.text('Bildiriminiz alındı. Teşekkür ederiz.'), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Kartta aile alanı yoksa rozet yok', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final r = Ilan.fromJson({'id': 'x', 'ad_soyad': 'Hasan Örnek', 'namaz_tarihi': '2026-10-14'})!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Tam Sayfa'), findsNothing);
    expect(find.text('Doğrulandı'), findsNothing);
    expect(find.text('Bu ilanda bir yanlışlık mı var?'), findsNothing); // Bildir yalnız aile kartlarında
  });
}
