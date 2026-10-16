// Panel sekmesi (URUN-TASLAGI §53): 4 ↔ 5 sekme, 4 haneli parola (karma), 5 yanlışta bekleme, çıkış, "Parolamı unuttum".
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/gorevli.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_kayit.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_panel.dart';
import 'package:kimin_cenazesi/ekranlar/panel_sekmesi.dart';
import 'package:kimin_cenazesi/main.dart' show KiminCenazesi;

import 'ortak.dart';
import 'widget_test.dart' show telefon;

http.Response _y(Map<String, dynamic> m) =>
    http.Response(jsonEncode(m), 200, headers: {'content-type': 'application/json; charset=utf-8'});

final _istekler = <String>[];
int _hatirlatKod = 200;

GorevliServisi _servis() => GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        _istekler.add('${req.method} ${req.url.path}${req.body.isEmpty ? '' : ' ${req.body}'}');
        if (req.url.path == '/gorevli/durum') {
          return _y({'durum': 'onayli', 'ad_soyad': 'Hasan Kurguluoğlu', 'il': 'Ordu', 'ilce': 'Korgan', 'gorev_yeri': 'Korgan Merkez Camii', 'unvan': 'İmam-Hatip'});
        }
        if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
        if (req.url.path == '/gorevli/parola') return _y({'durum': 'kaydedildi'});
        if (req.url.path == '/gorevli/parola-hatirlat') {
          return http.Response(jsonEncode(_hatirlatKod == 200 ? {'durum': 'gonderildi', 'adres': 'hasan.k@diyanet.gov.tr'} : {'hata': 'x'}), _hatirlatKod,
              headers: {'content-type': 'application/json; charset=utf-8'});
        }
        return http.Response('yok', 404);
      }),
    );

GorevliServisi _sv = _servis();
Widget _sekme(AppDurum d) => Kapsam(
      durum: d,
      child: ListenableBuilder(
        listenable: d,
        builder: (_, __) => MaterialApp(theme: temaYap(true), home: Scaffold(body: SafeArea(child: PanelSekmesi(servis: _sv)))),
      ),
    );

http.Client _ag() => MockClient((req) async {
      if (req.url.path.endsWith('/gorevli/eposta-kod')) return _y({'durum': 'kod_gonderildi'});
      if (req.url.path.endsWith('/gorevli/eposta-dogrula')) return _y({'durum': 'onayli', 'oturum': 'tokYeni'});
      return http.Response('yok', 404);
    });

Future<AppDurum> _gorevli({bool pin = true}) async {
  final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'}, istemci: _ag());
  await d.depo.gorevliOturumKaydet('tok');
  await d.depo.gorevliKullaniciKaydet('hasan.k');
  await d.depo.gorevliKvkkKaydet('2026-10-16T09:00:00Z');
  await d.depo.gorevliSorumlulukKaydet('2026-10-16T09:00:00Z');
  if (pin) await d.depo.gorevliPinKur('1234');
  return d;
}

Future<void> _yaz(WidgetTester t, String anahtar, String metin) async {
  await t.enterText(find.descendant(of: find.byKey(ValueKey(anahtar)), matching: find.byType(TextField)), metin);
  await t.pumpAndSettle();
}

void main() {
  testWidgets('Oturumsuz da 5 sekme; Panel sekmesinde görevli mesajı + "Kayıt olun" -> kayıt ekranı; oturum olunca parola belirleme; çıkışta sekme kalır', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(d.sekmeSayisi, 5);
    expect(find.byKey(const ValueKey('sekme_4')), findsOneWidget);
    expect(find.text(M.sekmePanel), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('sekme_4')));
    await tester.pumpAndSettle();
    expect(d.sekme, 4);
    expect(find.text(M.panelGorevliBaslik), findsOneWidget);
    expect(find.text(M.panelGorevliAciklama), findsOneWidget);
    expect(find.byKey(const ValueKey('sekme_4')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('panel_kayit')));
    await tester.pumpAndSettle();
    expect(find.byType(GorevliKayit), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.byType(GorevliKayit), findsNothing);
    // oturum olunca (parolasız): önce parola belirleme
    await d.depo.gorevliOturumKaydet('tok');
    d.oturumDegisti();
    await tester.pumpAndSettle();
    expect(find.text(M.pinBelirleBaslik), findsOneWidget);
    // çıkış: sekme kalır, yine görevli mesajı
    await d.gorevliCikis();
    d.sekmeSec(4);
    await tester.pumpAndSettle();
    expect(d.sekmeSayisi, 5);
    expect(find.byKey(const ValueKey('sekme_4')), findsOneWidget);
    expect(find.text(M.panelGorevliBaslik), findsOneWidget);
  });

  testWidgets('Parola belirleme: 4 rakam, iki kez; karma saklanır (düz parola yok); sonra panel', (tester) async {
    telefon(tester);
    final d = await _gorevli(pin: false);
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    expect(find.text(M.pinBelirleBaslik), findsOneWidget);
    expect(find.text('Birilerinin sizin hesabınıza girip kötü niyetli/yanıltıcı paylaşımlar yapmasını önlemek için 4 haneli parola belirleyin.'), findsOneWidget);
    await _yaz(tester, 'pin_1', '123');
    await _yaz(tester, 'pin_2', '123');
    await tester.tap(find.text(M.pinKaydet));
    await tester.pumpAndSettle();
    expect(find.text(M.pinRakam), findsOneWidget);
    await _yaz(tester, 'pin_1', '1234');
    await _yaz(tester, 'pin_2', '4321');
    await tester.tap(find.text(M.pinKaydet));
    await tester.pumpAndSettle();
    expect(find.text(M.pinFarkli), findsOneWidget);
    expect(d.depo.gorevliPinVar, isFalse);
    await _yaz(tester, 'pin_2', '1234');
    await tester.tap(find.text(M.pinKaydet));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliPinVar, isTrue);
    expect(d.depo.gorevliPinDogru('1234'), isTrue);
    expect(d.depo.gorevliPinDogru('0000'), isFalse);
    expect(d.panelAcik, isTrue);
    expect(find.byType(GorevliPanel), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Parola ekranı: yanlış parola uyarısı + kalan hak; doğru parola -> panel; ⋮ "Paneli kilitle" -> yeniden parola', (tester) async {
    telefon(tester);
    final d = await _gorevli();
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    expect(find.text(M.pinGirBaslik), findsOneWidget);
    expect(find.byType(GorevliPanel), findsNothing);
    await _yaz(tester, 'pin_gir', '0000');
    await tester.tap(find.text(M.pinGir));
    await tester.pumpAndSettle();
    expect(find.text(M.pinYanlisKalan(4)), findsOneWidget);
    await _yaz(tester, 'pin_gir', '1234');
    await tester.tap(find.text(M.pinGir));
    await tester.pumpAndSettle();
    expect(d.panelAcik, isTrue);
    expect(find.byType(GorevliPanel), findsOneWidget);
    expect(find.byKey(const ValueKey('g_baslik_karti')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('g_menu')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.panelKilitle));
    await tester.pumpAndSettle();
    expect(d.panelAcik, isFalse);
    expect(find.text(M.pinGirBaslik), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('5 yanlış parola: 1 dk bekleme metni, düğme pasif; doğru parola da bekleme bitene dek geçmez', (tester) async {
    telefon(tester);
    final d = await _gorevli();
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    for (int i = 0; i < 5; i++) {
      await _yaz(tester, 'pin_gir', '0000');
      await tester.tap(find.byKey(const ValueKey('pin_ac')));
      await tester.pump();
      await tester.pump();
    }
    expect(find.textContaining('saniye sonra yeniden deneyin'), findsOneWidget);
    expect(d.depo.gorevliPinKilitKalanSn(), greaterThan(0));
    expect(d.depo.gorevliPinKilitKalanSn(), lessThanOrEqualTo(60));
    expect(d.panelAcik, isFalse);
    await _yaz(tester, 'pin_gir', '1234');
    await tester.tap(find.byKey(const ValueKey('pin_ac')), warnIfMissed: false);
    await tester.pump();
    expect(d.panelAcik, isFalse);
    await tester.pumpWidget(const SizedBox()); // sayaç Timer'ı kapanır
    await tester.pump();
  });

  testWidgets('Çıkış: oturum + parola + görev bilgisi + KVKK silinir', (tester) async {
    telefon(tester);
    final d = await _gorevli();
    await d.depo.gorevliYerKaydet('Ordu', 'Korgan');
    await d.gorevliCikis();
    expect(d.depo.gorevliOturum, isNull);
    expect(d.depo.gorevliPinVar, isFalse);
    expect(d.depo.gorevliPinDogru('1234'), isFalse);
    expect(d.depo.gorevliYer, isNull);
    expect(d.depo.gorevliKvkkKabul, isNull);
    expect(d.depo.gorevliSorumlulukKabul, isNull);
    expect(d.panelAcik, isFalse);
  });

  testWidgets('"Parolamı unuttum": çıkış YOK, parola silinmez; ayrı "Parolanız gönderildi" sayfası; Tamam -> parola ekranı; hata (429/503) sade uyarı', (tester) async {
    telefon(tester);
    _istekler.clear();
    _hatirlatKod = 200;
    _sv = _servis();
    final d = await _gorevli();
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('pin_unuttum')));
    await tester.pumpAndSettle();
    expect(_istekler.where((x) => x == 'POST /gorevli/parola-hatirlat'), hasLength(1));
    expect(find.text(M.pinGonderildiBaslik), findsOneWidget);
    expect(find.text(M.pinGonderildiBir), findsOneWidget);
    expect(find.text(M.pinGonderildiIki('hasan.k@diyanet.gov.tr')), findsOneWidget);
    expect(d.depo.gorevliOturum, 'tok'); // çıkış yok
    expect(d.depo.gorevliPinDogru('1234'), isTrue); // parola silinmedi
    await tester.tap(find.byKey(const ValueKey('pin_tamam')));
    await tester.pumpAndSettle();
    expect(find.text(M.pinGirBaslik), findsOneWidget); // parola giriş ekranına dönüldü
    for (final kod in [429, 503]) {
      _hatirlatKod = kod;
      await tester.tap(find.byKey(const ValueKey('pin_unuttum')));
      await tester.pumpAndSettle();
      expect(find.text(M.pinGonderilemediSayfa), findsOneWidget);
      expect(find.text(M.pinGonderildiBir), findsNothing);
      await tester.tap(find.byKey(const ValueKey('pin_tamam')));
      await tester.pumpAndSettle();
    }
    _hatirlatKod = 200;
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Parola belirlenince Worker\'a /parola gider (gövde parola); ağ yoksa uyarı metni', (tester) async {
    telefon(tester);
    _istekler.clear();
    final d = await _gorevli(pin: false);
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    await _yaz(tester, 'pin_1', '4821');
    await _yaz(tester, 'pin_2', '4821');
    await tester.tap(find.text(M.pinKaydet));
    await tester.pump();
    await tester.pump();
    expect(_istekler, contains('POST /gorevli/parola {"parola":"4821"}'));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliPinDogru('4821'), isTrue);
    // ağ yok: kayıt başarısız -> uyarı, ama cihaz parolası geçerli
    final d2 = await _gorevli(pin: false);
    _sv = GorevliServisi(kok: 'https://g.test', istemci: MockClient((_) async => throw http.ClientException('ağ yok')));
    await tester.pumpWidget(_sekme(d2));
    await tester.pumpAndSettle();
    await _yaz(tester, 'pin_1', '1111');
    await _yaz(tester, 'pin_2', '1111');
    await tester.tap(find.text(M.pinKaydet));
    await tester.pump();
    await tester.pump();
    expect(find.text(M.pinSunucuyaYok), findsOneWidget);
    expect(d2.depo.gorevliPinDogru('1111'), isTrue);
    _sv = _servis();
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('⋮ "Parolamı değiştir": eski parola yanlışsa uyarı; doğruysa yeni parola cihaza ve Worker\'a yazılır', (tester) async {
    telefon(tester);
    _istekler.clear();
    _sv = _servis();
    final d = await _gorevli();
    d.panelAcik = true;
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('g_menu')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.pinDegistir));
    await tester.pumpAndSettle();
    await _yaz(tester, 'pin_eski', '0000');
    await _yaz(tester, 'pin_1', '9999');
    await _yaz(tester, 'pin_2', '9999');
    await tester.tap(find.byKey(const ValueKey('pin_kaydet')));
    await tester.pumpAndSettle();
    expect(find.text(M.pinEskiYanlis), findsOneWidget);
    expect(d.depo.gorevliPinDogru('1234'), isTrue);
    await _yaz(tester, 'pin_eski', '1234');
    await tester.tap(find.byKey(const ValueKey('pin_kaydet')));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliPinDogru('9999'), isTrue);
    expect(d.depo.gorevliPinDogru('1234'), isFalse);
    expect(_istekler, contains('POST /gorevli/parola {"parola":"9999"}'));
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Bildirim/ilan kutusu yolu: oturum varken panelSekmesiAc Panel sekmesini seçer, yokken seçmez', (tester) async {
    final d = await _gorevli();
    expect(d.panelSekmesiAc(), isTrue);
    expect(d.sekme, 4);
    await d.gorevliCikis();
    expect(d.panelSekmesiAc(), isFalse);
    expect(d.sekme, 0);
  });
}
