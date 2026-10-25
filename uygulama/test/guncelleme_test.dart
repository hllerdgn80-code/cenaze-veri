// Zorunlu güncelleme kapısı (URUN-TASLAGI §42)
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/surum.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';

Future<AppDurum> durumKur({required int build, required SurumCekici cekici}) async {
  SharedPreferences.setMockInitialValues({});
  final depo = await Depo.ac();
  return AppDurum(
      depo: depo, veri: VeriServisi(istemci: sahteAg('2026-10-15'), depo: depo), gomulu: testGomulu(), buildNo: build, surumCekici: cekici);
}

void main() {
  testWidgets('min_build büyükse güncelleme ekranı, düğme var, geri tuşu kapatmaz', (tester) async {
    final d = await durumKur(build: 10, cekici: () async => const SurumBilgi(minBuild: 16, sonBuild: 16, mesaj: 'Lütfen güncelleyin.'));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsOneWidget);
    expect(find.text('Lütfen güncelleyin.'), findsOneWidget);
    expect(find.byKey(const ValueKey('guncelle_dugme')), findsOneWidget);
    expect(find.text('Play Store\'da güncelle'), findsOneWidget);
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsOneWidget);
  });

  testWidgets('ağ hatası: kapı yok, uygulama açılır', (tester) async {
    final d = await durumKur(build: 10, cekici: () async => throw Exception('ağ yok'));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsNothing);
    expect(find.byType(Scaffold), findsWidgets); // il seçme ekranı
  });

  testWidgets('BUILD_NO == 0 (geliştirme): kapı atlanır, sürüm sorulmaz', (tester) async {
    var soruldu = false;
    final d = await durumKur(build: 0, cekici: () async {
      soruldu = true;
      return const SurumBilgi(minBuild: 999);
    });
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsNothing);
    expect(soruldu, isFalse);
  });

  testWidgets('build >= min_build: kapı yok; son_build büyükse yalnız bilgi çubuğu yok (il seçme ekranında kabuk yok)', (tester) async {
    final d = await durumKur(build: 16, cekici: () async => const SurumBilgi(minBuild: 16, sonBuild: 20));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsNothing);
    expect(d.guncellemeOnerilir, isTrue);
  });

  test('SurumBilgi.coz: bozuk gövde null, boş mesaj varsayılan', () {
    expect(SurumBilgi.coz('<html>'), isNull);
    final s = SurumBilgi.coz('{"min_build": 16, "son_build": "17", "mesaj": ""}')!;
    expect(s.minBuild, 16);
    expect(s.sonBuild, 17);
    expect(s.mesaj, varsayilanGuncellemeMesaji);
  });
}
