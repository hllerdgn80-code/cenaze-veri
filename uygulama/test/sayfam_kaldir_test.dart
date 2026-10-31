// 31.10.2026 (sahibi: "Sayfama ekle var ama sayfamdan kaldır yok"): Sayfam kartının altında yazılı
// "Sayfamdan kaldır" bağlantısı görünür ve onayla kaydı siler; ⋮ menüsü de durur.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/sayfam.dart';

import 'ortak.dart';
import 'widget_test.dart' show telefon;

void main() {
  testWidgets('Sayfam kartında yazılı "Sayfamdan kaldır" bağlantısı görünür', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await d.sayfamaEkle(Ilan.fromJson({'id': 'k1', 'ad_soyad': 'Ali Kaya', 'ilce': 'Merkez', 'cinsiyet': 'Erkek', 'namaz_tarihi': bugunTr()})!);
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: const Scaffold(body: SayfamEkrani()))));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('kaldir_k1')), findsOneWidget);
    expect(find.text(M.kartKaldir), findsOneWidget); // menü kapalıyken yalnız bağlantı
    expect(find.byTooltip('Seçenekler'), findsOneWidget); // ⋮ de duruyor
  });

  testWidgets('Bağlantı → Vazgeç kaydı tutar; → Kaldır kaydı siler', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await d.sayfamaEkle(Ilan.fromJson({'id': 'k1', 'ad_soyad': 'Ali Kaya', 'ilce': 'Merkez', 'cinsiyet': 'Erkek', 'namaz_tarihi': bugunTr()})!);
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: const Scaffold(body: SayfamEkrani()))));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const ValueKey('kaldir_k1')));
    await tester.tap(find.byKey(const ValueKey('kaldir_k1')));
    await tester.pumpAndSettle();
    expect(find.text(M.kaldirSoru), findsOneWidget);
    await tester.tap(find.text(M.kaldirVazgec));
    await tester.pumpAndSettle();
    expect(find.text('Ali Kaya'), findsOneWidget);
    expect(d.kayitli('k1'), isTrue);

    await tester.ensureVisible(find.byKey(const ValueKey('kaldir_k1')));
    await tester.tap(find.byKey(const ValueKey('kaldir_k1')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.kaldirTamam));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Ali Kaya'), findsNothing);
    expect(d.kayitli('k1'), isFalse);
    expect(find.text(M.bildirimKaldirildi), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });
}
