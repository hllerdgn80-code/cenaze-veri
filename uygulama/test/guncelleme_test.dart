// Zorunlu güncelleme kapısı (URUN-TASLAGI §42)
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/surum.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';

Future<AppDurum> durumKur({required int build, required SurumCekici cekici, bool? ios}) async {
  SharedPreferences.setMockInitialValues({});
  final depo = await Depo.ac();
  return AppDurum(
      depo: depo, veri: VeriServisi(istemci: sahteAg('2026-10-15'), depo: depo), gomulu: testGomulu(), buildNo: build, surumCekici: cekici, ios: ios);
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

  // ---- iOS dalı (31.10.2026): min_build_ios / son_build_ios, App Store düğmesi; Android davranışı değişmez ----
  testWidgets('iOS: min_build_ios büyükse güncelleme ekranı, düğme App Store', (tester) async {
    final d = await durumKur(
        build: 10, ios: true, cekici: () async => const SurumBilgi(minBuild: 0, minBuildIos: 12, sonBuildIos: 12, mesaj: 'Lütfen güncelleyin.'));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsOneWidget);
    expect(find.text('App Store\'da güncelle'), findsOneWidget);
    expect(find.text('Play Store\'da güncelle'), findsNothing);
  });

  testWidgets('iOS: yalnız Android anahtarı (min_build) varsa iOS kapısı YOK', (tester) async {
    final d = await durumKur(build: 10, ios: true, cekici: () async => const SurumBilgi(minBuild: 999, sonBuild: 999));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsNothing);
    expect(d.guncellemeZorunlu, isFalse);
    expect(d.guncellemeOnerilir, isFalse);
  });

  testWidgets('Android: min_build_ios yok sayılır', (tester) async {
    final d = await durumKur(build: 10, ios: false, cekici: () async => const SurumBilgi(minBuild: 5, minBuildIos: 999, sonBuildIos: 999));
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(find.text('Güncelleme gerekli'), findsNothing);
    expect(d.guncellemeOnerilir, isFalse);
  });

  test('SurumBilgi.coz: iOS alanları; eksik = 0, http bağlantı reddedilir', () {
    final a = SurumBilgi.coz('{"min_build": 16, "son_build": 17, "min_build_ios": "3", "son_build_ios": 4, "ios_magaza_url": "https://apps.apple.com/tr/app/x/id1"}')!;
    expect((a.minBuildIos, a.sonBuildIos, a.iosMagazaUrl), (3, 4, 'https://apps.apple.com/tr/app/x/id1'));
    expect((a.minBuildIcin(true), a.sonBuildIcin(true), a.minBuildIcin(false), a.sonBuildIcin(false)), (3, 4, 16, 17));
    final b = SurumBilgi.coz('{"min_build": 16, "ios_magaza_url": "http://kotu.example/x"}')!;
    expect((b.minBuildIos, b.sonBuildIos, b.iosMagazaUrl), (0, 0, varsayilanIosMagazaUrl));
    expect(varsayilanIosMagazaUrl, 'https://kimincenazesi.com/ios');
  });

  test('magazaAdresleri: Android market:// + https; iOS tek App Store bağlantısı (yoksa varsayılan)', () {
    expect(magazaAdresleri(ios: false), [marketUrl, webMarketUrl]);
    expect(magazaAdresleri(ios: true), [varsayilanIosMagazaUrl]);
    expect(magazaAdresleri(ios: true, iosUrl: 'https://apps.apple.com/x'), ['https://apps.apple.com/x']);
    expect((magazaAdi(false), magazaAdi(true)), ('Play Store', 'App Store'));
  });

  test('paylaşma metni ve mağaza bağlantısı platforma göre', () {
    expect(M.paylasMetin, contains('Play Store'));
    expect(M.magazaBaglanti, contains('play.google.com'));
    debugDefaultTargetPlatformOverride = TargetPlatform.iOS;
    try {
      sonIosMagazaUrl = null;
      expect(M.paylasMetin, contains('App Store'));
      expect(M.paylasMetin, isNot(contains('Play Store')));
      expect(M.magazaBaglanti, varsayilanIosMagazaUrl);
      sonIosMagazaUrl = 'https://apps.apple.com/tr/app/x/id1';
      expect(M.magazaBaglanti, 'https://apps.apple.com/tr/app/x/id1');
      expect(bildirimTeklifiAcik, isFalse); // iOS'ta bildirim menüsü/kartı yok
    } finally {
      debugDefaultTargetPlatformOverride = null;
      sonIosMagazaUrl = null;
    }
    expect(bildirimTeklifiAcik, isTrue);
  });
}
