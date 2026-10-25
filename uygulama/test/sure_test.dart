// Sûre ekranı: Arapça kipinde her âyetin numarası, düğmeye basınca yalnız Türkçe okunuş (Arapça yok), geri dönüş.
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/ekranlar/dualar.dart';
import 'package:kimin_cenazesi/ekranlar/sure.dart';

import 'ortak.dart';

Map<String, dynamic> sureVerisi() =>
    Map<String, dynamic>.from(jsonDecode(File('assets/veri/sureler.json').readAsStringSync()) as Map);

void telefon(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 2340);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

Future<AppDurum> durumSure() async {
  final d = await testDurumu();
  return AppDurum(
    depo: d.depo,
    veri: d.veri,
    gomulu: Gomulu(
      ilceler: d.gomulu.ilceler,
      cinsiyet: d.gomulu.cinsiyet,
      dualar: const {'bolumler': []},
      sureler: sureVerisi(),
    ),
  );
}

void main() {
  test('arapcaRakam', () {
    expect(arapcaRakam(1), '١');
    expect(arapcaRakam(83), '٨٣');
    expect(arapcaRakam(40), '٤٠');
  });

  test('sureler.json: 3 sûre, âyet sayıları 83/30/40, her âyette Arapça ve okunuş', () {
    final v = sureVerisi();
    final l = (v['sureler'] as List).cast<Map>();
    expect(l.map((s) => s['kisa']).toList(), ['Yâsîn', 'Mülk', 'Nebe’']);
    expect(l.map((s) => (s['ayetler'] as List).length).toList(), [83, 30, 40]);
    for (final s in l) {
      for (final a in (s['ayetler'] as List).cast<Map>()) {
        expect((a['ar'] as String).trim(), isNotEmpty);
        expect((a['ok'] as String).trim(), isNotEmpty);
      }
    }
  });

  for (final koyu in [true, false]) {
    testWidgets('Yâsîn: Arapça kipte 83 âyet numarası; düğme okunuşa çevirir ve geri alır (${koyu ? 'koyu' : 'açık'} tema)',
        (tester) async {
      telefon(tester);
      final d = await durumSure();
      final v = sureVerisi();
      final yasin = Map<String, dynamic>.from((v['sureler'] as List).first as Map);
      await tester.pumpWidget(Kapsam(
        durum: d,
        child: MaterialApp(
          theme: temaYap(koyu),
          home: SureEkrani(sure: yasin, besmeleAr: v['besmele_ar'] as String, besmeleOk: v['besmele_ok'] as String),
        ),
      ));
      await tester.pumpAndSettle();

      // Arapça kip: düğme "Türkçe yazılışını oku", 83 numara rozeti (Arapça-Hint rakam)
      expect(find.text('Türkçe yazılışını oku'), findsOneWidget);
      expect(find.text('Arapçasını oku'), findsNothing);
      final numaralar = [for (int i = 1; i <= 83; i++) arapcaRakam(i)];
      for (final n in numaralar) {
        expect(find.text(n, skipOffstage: false), findsOneWidget, reason: 'âyet no $n');
      }
      expect(find.textContaining('Bismillâhirrahmânirrahîm', skipOffstage: false), findsNothing);
      final dugme = tester.getSize(find.ancestor(of: find.text('Türkçe yazılışını oku'), matching: find.byType(InkWell)).first);
      expect(dugme.height, greaterThanOrEqualTo(44));

      // Okunuşa geç
      await tester.tap(find.text('Türkçe yazılışını oku'));
      await tester.pumpAndSettle();
      expect(find.text('Arapçasını oku'), findsOneWidget);
      expect(find.textContaining('Bismillâhirrahmânirrahîm'), findsOneWidget);
      expect(find.textContaining('Yâsîn.', skipOffstage: false), findsWidgets);
      final arapca = RegExp(r'[؀-ۿ]');
      final metinler = tester.widgetList<RichText>(find.byType(RichText, skipOffstage: false)).map((w) => w.text.toPlainText());
      expect(metinler.where(arapca.hasMatch), isEmpty, reason: 'okunuş kipinde Arapça harf olmamalı');
      for (final n in numaralar) {
        expect(find.text(n, skipOffstage: false), findsNothing);
      }

      // Geri dön
      await tester.tap(find.text('Arapçasını oku'));
      await tester.pumpAndSettle();
      expect(find.text('Türkçe yazılışını oku'), findsOneWidget);
      expect(find.text('٨٣', skipOffstage: false), findsOneWidget);
    });
  }

  testWidgets('Dualar ekranı: Sûreler başlığı + üç eşit döşeme, dokununca sûre açılır', (tester) async {
    telefon(tester);
    final d = await durumSure();
    await tester.pumpWidget(Kapsam(
      durum: d,
      child: MaterialApp(theme: temaYap(true), home: const Scaffold(body: SafeArea(child: DualarEkrani()))),
    ));
    await tester.pumpAndSettle();
    expect(find.text('SÛRELER'), findsOneWidget);
    final kutular = ['Yâsîn', 'Mülk', 'Nebe’'];
    final genislik = <double>[];
    for (final k in kutular) {
      final f = find.text(k);
      expect(f, findsOneWidget);
      genislik.add(tester.getSize(find.ancestor(of: f, matching: find.byType(InkWell)).first).width);
    }
    expect(genislik[0], closeTo(genislik[1], 0.5));
    expect(genislik[1], closeTo(genislik[2], 0.5));
    await tester.tap(find.text('Mülk'));
    await tester.pumpAndSettle();
    expect(find.text('Mülk Sûresi'), findsOneWidget);
    expect(find.text('Türkçe yazılışını oku'), findsOneWidget);
  });
}
