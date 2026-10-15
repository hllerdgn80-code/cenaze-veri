// "Haritada aç": URL biçimi, url_launcher'a (sahte platform) giden bağlantı, kartta yalnız yer doluyken görünme, açılamazsa bildirim.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/cekirdek/harita.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';
import 'package:url_launcher_platform_interface/link.dart';
import 'package:url_launcher_platform_interface/url_launcher_platform_interface.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

class SahteLauncher extends UrlLauncherPlatform with MockPlatformInterfaceMixin {
  final List<String> acilan = [];
  bool basarili = true;
  @override
  LinkDelegate? get linkDelegate => null;
  @override
  Future<bool> canLaunch(String url) async => basarili;
  @override
  Future<bool> launchUrl(String url, LaunchOptions options) async {
    acilan.add(url);
    return basarili;
  }
}

void main() {
  test('haritaUri: "yer, ilçe, il" kodlanır', () {
    final u = haritaUri(yer: 'Merkez Camii', ilce: 'Ünye', il: 'Ordu');
    expect(u.toString(), startsWith('https://www.google.com/maps/search/?api=1&query='));
    expect(u.queryParameters['query'], 'Merkez Camii, Ünye, Ordu');
    expect(haritaUri(yer: 'Huzur Mezarlığı', ilce: null, il: '').queryParameters['query'], 'Huzur Mezarlığı');
  });

  testWidgets('Kart: harita bağlantıları yalnız yer doluyken görünür; dokununca dış uygulamaya gider; açılamazsa bildirim', (tester) async {
    telefon(tester);
    final sahte = SahteLauncher();
    UrlLauncherPlatform.instance = sahte;
    final d = await testDurumu();
    final dolu = Ilan.fromJson({
      'id': 'h1', 'ad_soyad': 'Veli Örnek', 'il': 'Ordu', 'ilce': 'Ünye',
      'defin_yeri': 'Huzur Mezarlığı', 'namaz_yeri_vakti': 'Öğle Namazını Müteakip-Merkez Camii', 'namaz_tarihi': '2026-10-14',
    })!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: dolu)));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('harita_cami_h1')), findsOneWidget);
    expect(find.byKey(const ValueKey('harita_mezar_h1')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('harita_mezar_h1')));
    await tester.pumpAndSettle();
    expect(sahte.acilan.single, contains('query=Huzur%20Mezarl%C4%B1%C4%9F%C4%B1%2C%20%C3%9Cnye%2C%20Ordu'));

    sahte.basarili = false;
    await tester.tap(find.byKey(const ValueKey('harita_cami_h1')));
    await tester.pump();
    expect(find.text(M.haritaAcilamadi), findsOneWidget);
    await tester.pumpAndSettle(const Duration(seconds: 5));

    final bos = Ilan.fromJson({'id': 'h2', 'ad_soyad': 'Ali Örnek', 'il': 'Ordu', 'ilce': 'Ünye', 'namaz_tarihi': '2026-10-14'})!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: bos)));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('harita_cami_h2')), findsNothing);
    expect(find.byKey(const ValueKey('harita_mezar_h2')), findsNothing);
  });
}
