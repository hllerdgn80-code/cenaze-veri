// 0.1.7 açılış mesajı (URUN-TASLAGI §41)
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/ekranlar/acilis_mesaji.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';

void main() {
  testWidgets('açılışta âyet, meal ve kaynak görünür; süre dolunca sonraki ekran gelir', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: AcilisMesaji(sure: Duration(milliseconds: 100), sonra: Scaffold(body: Text('SONRAKI'))),
    ));
    expect(find.text(M.acilisArapca), findsOneWidget);
    expect(find.text(M.acilisMeal), findsOneWidget);
    expect(find.text(M.acilisKaynak), findsOneWidget);
    expect(find.text('SONRAKI'), findsNothing);
    await tester.pump(const Duration(milliseconds: 150));
    await tester.pumpAndSettle();
    expect(find.text('SONRAKI'), findsOneWidget);
    expect(find.text(M.acilisArapca), findsNothing);
  });

  testWidgets('motto il seçme ekranında görünür', (tester) async {
    final d = await testDurumu();
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text(M.motto), findsOneWidget);
    expect(find.text(M.acilisAlt), findsOneWidget);
  });
}
