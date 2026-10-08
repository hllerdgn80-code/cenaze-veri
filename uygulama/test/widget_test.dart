// Ekran testleri: il-ilçe seçimi kaydı, kayıtlı adresle doğrudan İlanlar, kart etiketi = şerit günü,
// Sayfam sayacı (+1/−1), kaynaksız il ekranı, kaynak alanı olmayan kayıt kartı.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';

/// Tek bir bileşeni uygulama kapsamı ve temasıyla çizer
Widget kapsamli(AppDurum d, Widget w) => Kapsam(
      durum: d,
      child: MaterialApp(
        theme: temaYap(true),
        home: Scaffold(body: SingleChildScrollView(padding: const EdgeInsets.all(20), child: w)),
      ),
    );

void main() {
  testWidgets('İlk açılış: il → ilçe seçimi cihaza kaydedilir ve İlanlar açılır', (tester) async {
    final d = await testDurumu();
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();

    expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    await tester.tap(find.text('Ordu'));
    await tester.pumpAndSettle();

    expect(find.text(trBuyuk('İlçe seçin')), findsOneWidget); // üst etiket Türkçe büyük harfle
    expect(find.text('Tüm ilçeler'), findsOneWidget);
    await tester.tap(find.text('Ünye'));
    await tester.pumpAndSettle();

    final p = await SharedPreferences.getInstance();
    expect(p.getString('il'), 'Ordu');
    expect(p.getString('ilce'), 'Ünye');
    expect(find.text('Ordu · Ünye'), findsOneWidget);
    expect(find.text('Ahmet Örnekoğlu'), findsOneWidget);
  });

  testWidgets('Kayıtlı adresle açılış doğrudan İlanlar; kart etiketi seçili günle aynı', (tester) async {
    final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();

    expect(find.text('Bulunduğunuz ili seçin'), findsNothing);
    final bugun = bugunTr();
    // Bugün seçili; örnek ilanın cenaze günü bugün → etiket bugünün tarihini taşır
    expect(find.text(trBuyuk('Cenaze · ${tarih(bugun, kisa: true)} · Öğle')), findsOneWidget);
    expect(find.text('Son güncelleme 09:02'), findsOneWidget);

    // Dün seçilince bugünün kartı görünmez, boş durum çıkar
    await tester.tap(find.byKey(ValueKey('gun_${gunEkle(bugun, -1)}')));
    await tester.pumpAndSettle();
    expect(find.text('Ahmet Örnekoğlu'), findsNothing);
    expect(find.text('Bu tarihte cenaze ilanı bulunmuyor'), findsOneWidget);
  });

  testWidgets('Sayfam sayacı: +1 artar, −1 geri alır', (tester) async {
    final d = await testDurumu();
    final r = Ilan.fromJson({
      'id': 's1',
      'ad_soyad': 'Mehmet Örnek',
      'namaz_tarihi': '2026-10-08',
      'namaz_yeri_vakti': 'İkindi Namazını Müteakip-ÖRNEK CAMİİ',
    })!;
    await d.sayfamaEkle(r);
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r, sayacli: true)));
    await tester.pumpAndSettle();

    expect(find.text('Merhuma 1 Fâtiha okudum'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('sayac_f')));
    await tester.pumpAndSettle();
    expect((tester.widget(find.byKey(const ValueKey('sayi_f'))) as Text).data, '1');
    expect(find.text('Okuduklarınızın toplamı: 1'), findsOneWidget);

    await tester.tap(find.text('−1').first);
    await tester.pumpAndSettle();
    expect((tester.widget(find.byKey(const ValueKey('sayi_f'))) as Text).data, '0');
  });

  testWidgets('Verisi olmayan il: bilgi kartı ve "Cenaze ilanı paylaş" düğmesi', (tester) async {
    final d = await testDurumu(onceki: {'il': 'Kars', 'ilce': 'Merkez'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();

    expect(find.text('Kars’ta cenaze ilanları şu an yakınları tarafından paylaşılıyor.'), findsOneWidget);
    expect(find.text('Cenaze ilanı paylaş'), findsOneWidget);
  });

  testWidgets('Kapı: kaynak alanı olmayan kayıt kart olarak çizilir, kaynak adı görünmez', (tester) async {
    final d = await testDurumu();
    final r = Ilan.fromJson({
      'id': 'k1',
      'ad_soyad': 'Fatma Örnek',
      'mahalle': 'ÖRNEK',
      'ilce': 'Ünye',
      'yas': 80,
      'vefat_tarihi': '2026-10-07',
      'liste_tarihi': '2026-10-08',
      'defin_yeri': 'ÖRNEK MEZ.',
      'kaynak_ad': 'Bir Belediye',
    })!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();

    expect(find.text('Fatma Örnek'), findsOneWidget);
    expect(find.text('Örnek Mezarlığı'), findsOneWidget);
    expect(find.text('Sayfama kaydet'), findsOneWidget);
    expect(find.textContaining('Belediye'), findsNothing);

    await tester.tap(find.text('Sayfama kaydet'));
    await tester.pumpAndSettle();
    expect(find.text('Sayfamda ✓'), findsOneWidget);
    await tester.pump(const Duration(seconds: 3)); // bildirim zamanlayıcısı kapansın
    await tester.pumpAndSettle();
  });
}
