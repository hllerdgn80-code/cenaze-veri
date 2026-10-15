// Aile / Tam Sayfa / Şehit formu (v0.1.2): giriş kartı, 5 adım, telefon/T.C. yok, fiyat + ödeme ekranı (Tam Sayfa),
// Worker'a POST, e-posta kodu, sonuç ekranı, kartta Bildir.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/ortak.dart';
import 'package:kimin_cenazesi/cekirdek/aile.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/aile_formu.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

const _json = {'content-type': 'application/json; charset=utf-8'};

Widget formSayfasi(AppDurum d, AileServisi s, {bool tam = false, bool sehit = false}) => Kapsam(
      durum: d,
      child: MaterialApp(
          theme: temaYap(true), home: AileFormu(il: 'Kars', ilce: 'Merkez', tam: tam, sehit: sehit, servis: s)),
    );

/// Başlık çubuğu üst etiketi Türkçe büyük harfle yazılır
Finder ust(int n) => find.text(trBuyuk('Adım $n / 5'));

/// Gelen istekleri kaydeden sahte Worker
AileServisi sahteServis(Map<String, Map<String, dynamic>> istekler) => AileServisi(
      kok: 'https://aile.test',
      istemci: MockClient((req) async {
        istekler[req.url.path] = jsonDecode(req.body) as Map<String, dynamic>;
        if (req.url.path == '/aile/basvur') {
          return http.Response(jsonEncode({'basvuru_id': 'b1', 'dogrulama': 'eposta'}), 200, headers: _json);
        }
        if (req.url.path == '/aile/dogrula') {
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

/// Giriş kartından 5. adıma kadar doldurur. [belge]: Tam Sayfa'da zorunlu belge kodu, şehitte duyuru bağlantısı.
Future<void> besinciAdima(WidgetTester t, {bool giris = true, String? belge, String? belgeDugme, String? rutbe}) async {
  if (giris) await dokun(t, devam());
  expect(ust(1), findsOneWidget);
  if (rutbe != null) await yaz(t, 'f_rutbe', rutbe);
  await dokun(t, find.text('Erkek'));
  await yaz(t, 'f_ad', 'Ahmet Örnek');
  await dokun(t, devam());
  expect(ust(2), findsOneWidget);
  await dokun(t, devam());
  expect(ust(3), findsOneWidget);
  await yaz(t, 'f_basvuran', 'Ali Örnek');
  await yaz(t, 'f_eposta', 'ali@ornek.com');
  await dokun(t, devam());
  expect(ust(4), findsOneWidget);
  if (belge != null) {
    expect(t.widget<AnaDugme>(devam()).onTap, isNull); // doğrulanmadan ilerlenmez
    await yaz(t, 'f_belge', belge);
    await dokun(t, find.text(belgeDugme!));
  }
  await dokun(t, devam()); // aile: e-Devlet kodu atlanır
  expect(ust(5), findsOneWidget);
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
    expect(find.text('Cep telefonu'), findsNothing);
    expect(find.textContaining('T.C.'), findsNothing);
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull);
    await yaz(tester, 'f_basvuran', 'Ali Örnek');
    await yaz(tester, 'f_eposta', 'ali@');
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull); // e-posta biçimi
    await yaz(tester, 'f_eposta', 'ali@ornek.com');
    await dokun(tester, devam());

    expect(ust(4), findsOneWidget);
    expect(find.textContaining('Doğrulandı'), findsOneWidget); // rozet açıklaması
    expect(tester.widget<AnaDugme>(devam()).onTap, isNotNull); // isteğe bağlı: boş geçilebilir
    await dokun(tester, devam());

    expect(ust(5), findsOneWidget);
    expect(find.text(M.hukukMetin), findsOneWidget);
    final dugme = tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Onayla ve gönder'));
    expect(dugme.onTap, isNull); // kutu işaretlenmeden pasif
    await dokun(tester, find.byKey(const ValueKey('beyan_kutu')));
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Onayla ve gönder')).onTap, isNotNull);

    // Geri: 5 → 4
    await tester.tap(find.byType(YuvarlakDugme).first);
    await tester.pumpAndSettle();
    expect(ust(4), findsOneWidget);
  });

  testWidgets('Gönder → e-posta kodu → doğrula → "İlanınız yayımlandı"', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    final s = sahteServis(istekler);
    await tester.pumpWidget(formSayfasi(d, s));
    await tester.pumpAndSettle();
    await besinciAdima(tester);
    await onaylaVeGonder(tester);

    final b = istekler['/aile/basvur']!;
    expect(b['il'], 'Kars');
    expect(b['ilce'], 'Merkez');
    expect(b['ad_soyad'], 'Ahmet Örnek');
    expect(b['cinsiyet'], 'e');
    expect(b['beyan'], true);
    expect((b['basvuran'] as Map)['eposta'], 'ali@ornek.com');
    expect(b.containsKey('edevlet_kodu'), isFalse);
    expect(b.containsKey('telefon'), isFalse);
    expect(b.containsKey('tc'), isFalse);

    // Kod ekranı
    expect(find.text('Doğrulama kodunu ali@ornek.com adresine gönderdik.'), findsOneWidget);
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
    await besinciAdima(tester);
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
    await besinciAdima(tester);
    await onaylaVeGonder(tester);
    expect(find.text(M.aileAgHata), findsOneWidget);
    expect(ust(5), findsOneWidget);
    final tekrar = find.widgetWithText(AnaDugme, 'Yeniden deneyin');
    expect(tekrar, findsOneWidget);
    await tester.tap(tekrar);
    await tester.pump();
    await tester.pump();
    expect(find.text('Doğrulama kodunu ali@ornek.com adresine gönderdik.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox()); // geri sayım zamanlayıcısı kapansın
  });

  testWidgets('Tam Sayfa: fiyat kartı → adımlar → belge zorunlu → "Ödemeye geç" → ödeme ekranı → Worker (tam:true)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    await tester.pumpWidget(formSayfasi(d, sahteServis(istekler), tam: true));
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
    await besinciAdima(tester, belge: 'ABCD-1234-EFGH', belgeDugme: 'Belgeyi doğrula');
    expect(find.text('Belge doğrulandı'), findsNothing); // 5. adıma geçildi
    expect(find.text('Yasal beyan ve ödeme'), findsOneWidget);
    expect(find.text('Ödenecek: 200 ₺'), findsOneWidget);
    expect(find.text('Onayla ve gönder'), findsNothing);
    final odemeye = find.widgetWithText(AnaDugme, 'Ödemeye geç');
    expect(tester.widget<AnaDugme>(odemeye).onTap, isNull);
    await dokun(tester, find.byKey(const ValueKey('beyan_kutu')));
    expect(tester.widget<AnaDugme>(odemeye).onTap, isNotNull);
    expect(find.text('İlanınız ödeme ve kontrolden sonra yayımlanır.'), findsOneWidget);
    await tester.tap(odemeye);
    await tester.pumpAndSettle();

    // Prototipteki ödeme ekranı; henüz hiçbir istek gitmedi
    expect(istekler, isEmpty);
    expect(find.text(trBuyuk('Ödeme')), findsOneWidget);
    expect(find.text('Mağaza içi satın alma'), findsOneWidget);
    expect(find.text('Tam sayfa cenaze ilanı'), findsOneWidget);
    expect(find.text('200,00 ₺'), findsOneWidget);
    expect(find.text(M.odemeNot), findsOneWidget);
    await tester.tap(find.widgetWithText(AnaDugme, 'Ödemeyi onayla'));
    await tester.pump();
    await tester.pump();
    final b = istekler['/aile/basvur']!;
    expect(b['tam'], true);
    expect(b['edevlet_kodu'], 'ABCD-1234-EFGH');
    expect(b.containsKey('sehit'), isFalse);

    final kod = find.descendant(of: find.byKey(const ValueKey('f_kod')), matching: find.byType(TextField));
    await tester.enterText(kod, '123456');
    await tester.pump();
    await tester.tap(find.widgetWithText(AnaDugme, 'Doğrula'));
    await tester.pump();
    await tester.pump();
    expect(find.text('İlanınız alındı'), findsOneWidget);
    expect(find.text('İlan kontrolden sonra bulunduğunuz il veya ilçenin sayfasında yayımlanır. Başınız sağ olsun.'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Şehit formu: 1. adımla açılır, rütbe/tören/duyuru alanları, ücret yok, Worker\'a sehit:true', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    await tester.pumpWidget(formSayfasi(d, sahteServis(istekler), sehit: true));
    await tester.pumpAndSettle();

    expect(find.text('Şehit İlanı'), findsOneWidget);
    expect(ust(1), findsOneWidget); // giriş kartı yok
    expect(find.text('Şehidimizin bilgileri'), findsOneWidget);
    expect(find.text('Rütbe / unvan'), findsOneWidget);
    expect(find.textContaining('₺'), findsNothing);
    expect(find.textContaining('ücret'), findsNothing);
    await dokun(tester, find.text('Erkek'));
    await yaz(tester, 'f_ad', 'Örnekalp Yıldırımhan');
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull); // rütbe boş
    await yaz(tester, 'f_rutbe', 'Piyade Uzman Çavuş');
    await dokun(tester, devam());
    expect(find.text('Cenaze töreni yeri'), findsOneWidget);
    await yaz(tester, 'f_toren', 'Selâmet Meydanı');
    await dokun(tester, devam());
    await yaz(tester, 'f_basvuran', 'Ali Örnek');
    await yaz(tester, 'f_eposta', 'ali@ornek.com');
    await dokun(tester, devam());
    expect(ust(4), findsOneWidget);
    expect(find.text('Resmî duyuru doğrulaması'), findsOneWidget);
    expect(find.text(M.sehitDuyuruAciklama), findsOneWidget);
    expect(tester.widget<AnaDugme>(devam()).onTap, isNull);
    await yaz(tester, 'f_belge', 'https://valilik.gov.tr/duyuru');
    await dokun(tester, find.text('Duyuruyu doğrula'));
    expect(find.text('Duyuru doğrulandı'), findsOneWidget);
    await dokun(tester, devam());
    expect(ust(5), findsOneWidget);
    expect(find.text('Ödemeye geç'), findsNothing);
    expect(find.text('Yasal beyan'), findsOneWidget);
    expect(find.text('İlanınız kontrolden sonra yayımlanır.'), findsOneWidget);
    await onaylaVeGonder(tester);
    final b = istekler['/aile/basvur']!;
    expect(b['sehit'], true);
    expect(b['rutbe'], 'Piyade Uzman Çavuş');
    expect(b['toren_yeri'], 'Selâmet Meydanı');
    expect(b['duyuru_url'], 'https://valilik.gov.tr/duyuru');
    expect(b.containsKey('tam'), isFalse);
    expect(b.containsKey('edevlet_kodu'), isFalse);

    final kod = find.descendant(of: find.byKey(const ValueKey('f_kod')), matching: find.byType(TextField));
    await tester.enterText(kod, '123456');
    await tester.pump();
    await tester.tap(find.widgetWithText(AnaDugme, 'Doğrula'));
    await tester.pump();
    await tester.pump();
    expect(find.text(M.sehitBittiYazi), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Kart: "Yakını paylaştı" + "Doğrulandı" rozetleri ve Bildir', (tester) async {
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
      'dogrulandi': true,
      'namaz_tarihi': '2026-10-14',
    })!;
    expect(r.dogrulandi, isTrue);
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Yakını paylaştı'), findsOneWidget);
    expect(find.text('Doğrulandı'), findsOneWidget);

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
    expect(find.text('Yakını paylaştı'), findsNothing);
    expect(find.text('Doğrulandı'), findsNothing);
    expect(find.text('Bu ilanda bir yanlışlık mı var?'), findsNothing); // Bildir yalnız aile kartlarında
  });
}
