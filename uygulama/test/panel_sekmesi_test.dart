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

GorevliServisi _servis() => GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        if (req.url.path == '/gorevli/durum') {
          return _y({'durum': 'onayli', 'ad_soyad': 'Hasan Kurguluoğlu', 'il': 'Ordu', 'ilce': 'Korgan', 'gorev_yeri': 'Korgan Merkez Camii', 'unvan': 'İmam-Hatip'});
        }
        if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
        return http.Response('yok', 404);
      }),
    );

Widget _sekme(AppDurum d) => Kapsam(
      durum: d,
      child: ListenableBuilder(
        listenable: d,
        builder: (_, __) => MaterialApp(theme: temaYap(true), home: Scaffold(body: SafeArea(child: PanelSekmesi(servis: _servis())))),
      ),
    );

Future<AppDurum> _gorevli({bool pin = true}) async {
  final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
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
  testWidgets('Doğrulanmamışta 4 sekme; oturum olunca 5. sekme "Panel"', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(d.sekmeSayisi, 4);
    expect(find.byKey(const ValueKey('sekme_4')), findsNothing);
    d.sekmeSec(4); // sınır: 4 sekmede 5. seçilemez
    expect(d.sekme, 0);
    await d.depo.gorevliOturumKaydet('tok');
    d.oturumDegisti();
    await tester.pumpAndSettle();
    expect(d.sekmeSayisi, 5);
    expect(find.byKey(const ValueKey('sekme_4')), findsOneWidget);
    expect(find.text(M.sekmePanel), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('sekme_4')));
    await tester.pumpAndSettle();
    expect(d.sekme, 4);
    expect(find.text(M.pinBelirleBaslik), findsOneWidget); // parolası olmayan oturum: önce belirle
    // çıkış -> 4 sekme
    await d.gorevliCikis();
    await tester.pumpAndSettle();
    expect(d.sekmeSayisi, 4);
    expect(d.sekme, 0);
    expect(find.byKey(const ValueKey('sekme_4')), findsNothing);
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

  testWidgets('"Parolamı unuttum": çıkış yapar ve e-posta kodu kayıt ekranını açar', (tester) async {
    telefon(tester);
    final d = await _gorevli();
    await tester.pumpWidget(_sekme(d));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('pin_unuttum')));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliOturum, isNull);
    expect(d.depo.gorevliPinVar, isFalse);
    expect(find.byType(GorevliKayit), findsOneWidget);
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
