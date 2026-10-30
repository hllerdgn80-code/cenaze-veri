// 30.10.2026 uçtan uca ekran (Play önerisi, Android 15 / SDK 35+): çubuklar şeffaf, içerik ek (inset) alanlarına SafeArea ile uyar.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/ekranlar/acilis_mesaji.dart';
import 'package:kimin_cenazesi/ekranlar/guncelleme.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';

void main() {
  test('sistem çubukları şeffaf; ikon rengi temaya göre', () {
    final k = sistemCubuklari(false), d = sistemCubuklari(true);
    expect(k.statusBarColor, Colors.transparent);
    expect(k.systemNavigationBarColor, Colors.transparent);
    expect(k.systemNavigationBarContrastEnforced, false);
    expect(k.statusBarIconBrightness, Brightness.dark);
    expect(k.systemNavigationBarIconBrightness, Brightness.dark);
    expect(d.statusBarIconBrightness, Brightness.light);
    expect(d.systemNavigationBarIconBrightness, Brightness.light);
  });

  testWidgets('uygulama kökü şeffaf çubuk stilini taşır (tema değişince ikon rengi değişir)', (tester) async {
    final d = await testDurumu();
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pump();
    final bolge = tester.widget<AnnotatedRegion<SystemUiOverlayStyle>>(find.byWidgetPredicate((w) => w is AnnotatedRegion<SystemUiOverlayStyle> && w.value.statusBarColor == Colors.transparent).first);
    expect(bolge.value.systemNavigationBarColor, Colors.transparent);
  });

  testWidgets('açılış ve zorunlu güncelleme ekranları çentik/çubuk altına taşmaz (SafeArea)', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(size: Size(400, 800), padding: EdgeInsets.only(top: 48, bottom: 34)),
        child: AcilisMesaji(sure: Duration(seconds: 5), sonra: SizedBox()),
      ),
    ));
    expect(find.descendant(of: find.byType(AcilisMesaji), matching: find.byType(SafeArea)), findsOneWidget);
    final ust = tester.getTopLeft(find.byType(SingleChildScrollView)).dy;
    expect(ust, greaterThanOrEqualTo(0));
    await tester.pumpWidget(const MaterialApp(home: GuncellemeGerekli(mesaj: 'x')));
    expect(find.descendant(of: find.byType(GuncellemeGerekli), matching: find.byType(SafeArea)), findsOneWidget);
  });
}
