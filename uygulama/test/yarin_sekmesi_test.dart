// URUN §58 (site sahibi 30.10.2026): "Yarın" sekmesi HER ZAMAN şeritte; boşsa "henüz girilmedi"; yarının ilanı Yarın'da hemen görünür.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';
import 'widget_test.dart' show telefon;

/// Ordu/Ünye örnek verisine verilen günlerde ek kayıt ekleyen sahte ağ
http.Client agIle(String bugun, List<String> ekGunler) => MockClient((req) async {
      if (req.url.path.endsWith('/ordu/son7gun.json')) {
        final m = ornekOrdu(bugun);
        final l = ((m['ilceler'] as Map)['Ünye'] as List);
        for (final g in ekGunler) {
          l.add({
            'id': 'ek-$g',
            'il': 'Ordu',
            'ilce': 'Ünye',
            'ad_soyad': 'Ek ${g.substring(8)} Örnek',
            'namaz_tarihi': g,
            'namaz_yeri_vakti': 'İkindi Namazını Müteakip-ÖRNEK CAMİİ',
            'liste_tarihi': bugun,
          });
        }
        return http.Response.bytes(utf8.encode(jsonEncode(m)), 200, headers: {'content-type': 'application/json; charset=utf-8'});
      }
      return http.Response('yok', 404);
    });

Future<void> ac(WidgetTester tester, List<String> ekGunler) async {
  telefon(tester);
  final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'}, istemci: agIle(bugunTr(), ekGunler));
  await tester.pumpWidget(KiminCenazesi(durum: d));
  await tester.pumpAndSettle();
}

void main() {
  final bugun = bugunTr();
  final yarin = gunEkle(bugun, 1);
  final obur = gunEkle(bugun, 2);

  testWidgets('1) hiç ileri kayıt yokken şeritte Yarın hücresi ve "Yarın" yazısı var; öbür gün yok', (tester) async {
    await ac(tester, const []);
    expect(find.byKey(ValueKey('gun_$yarin')), findsOneWidget);
    expect(find.text(M.seritYarin), findsOneWidget);
    expect(find.byKey(ValueKey('gun_$obur')), findsNothing);
    // Bugün varsayılan seçili: bugünün kartı görünür
    expect(find.text('Ahmet Örnekoğlu'), findsOneWidget);
  });

  testWidgets('2) boş Yarın tıklanınca "henüz cenaze ilanı girilmedi" + açıklama; bugünün kartı görünmez; "diğer ilçeler/dün" yok', (tester) async {
    await ac(tester, const []);
    await tester.tap(find.byKey(ValueKey('gun_$yarin')));
    await tester.pumpAndSettle();
    expect(find.text('Yarın Ünye için henüz cenaze ilanı girilmedi'), findsOneWidget);
    expect(find.text(M.bosYarinAciklama), findsOneWidget);
    expect(find.text('Ahmet Örnekoğlu'), findsNothing);
    expect(find.text('Bu tarihte cenaze ilanı bulunmuyor'), findsNothing); // geçmiş metni değil
    expect(find.textContaining('Bugün Ünye'), findsNothing);
  });

  testWidgets('3) yarına kayıt varsa Yarın tıklanınca kart görünür ve hücrede nokta dolu', (tester) async {
    await ac(tester, [yarin]);
    await tester.tap(find.byKey(ValueKey('gun_$yarin')));
    await tester.pumpAndSettle();
    expect(find.text('Ek ${yarin.substring(8)} Örnek'), findsOneWidget);
    expect(find.text('Ahmet Örnekoğlu'), findsNothing);
    expect(find.textContaining('henüz cenaze ilanı girilmedi'), findsNothing);
    // nokta: hücrenin içinde 4x4 daire (Yarın dolu), boşken yok
    Finder nokta(String g) => find.descendant(
        of: find.byKey(ValueKey('gun_$g')),
        matching: find.byWidgetPredicate((w) => w is Container && w.constraints?.maxWidth == 4 && w.constraints?.maxHeight == 4));
    expect(nokta(yarin), findsOneWidget);
    expect(nokta(bugun), findsOneWidget); // bugünün kaydı var (karşılaştırma)
    expect(nokta(gunEkle(bugun, -1)), findsNothing); // dün boş
  });

  testWidgets('4) öbür güne kayıt yoksa hücresi YOK, varsa VAR; boş öbür gün de "henüz girilmedi" metnini taşır', (tester) async {
    await ac(tester, const []);
    expect(find.byKey(ValueKey('gun_$obur')), findsNothing);
    await tester.pumpWidget(const SizedBox());
    await ac(tester, [obur]);
    expect(find.byKey(ValueKey('gun_$obur')), findsOneWidget);
    expect(find.byKey(ValueKey('gun_$yarin')), findsOneWidget); // Yarın, öbür gün doluyken de var (kayıtsız)
    await tester.tap(find.byKey(ValueKey('gun_$yarin')));
    await tester.pumpAndSettle();
    expect(find.text('Yarın Ünye için henüz cenaze ilanı girilmedi'), findsOneWidget);
    await tester.tap(find.byKey(ValueKey('gun_$obur')));
    await tester.pumpAndSettle();
    expect(find.text('Ek ${obur.substring(8)} Örnek'), findsOneWidget);
  });
}
