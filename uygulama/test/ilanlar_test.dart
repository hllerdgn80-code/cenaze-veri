// Mutabık ekran kuralları: §27 şehit en üstte, §21/1 ilçesiz kaynak "İl geneli", §21/2 diğer ilçeler,
// §21/3 bildirim teklifi, §32 bebek rozeti, Tam Sayfa "Vefat ilanı hazırlayın" + onay kutusu kilidi.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/ortak.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/ilanlar.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

Map<String, dynamic> kayit(String id, String ad, String ilce, String gun, {bool sehit = false, bool bebek = false}) => {
      'id': id,
      'ad_soyad': ad,
      'ilce': ilce,
      'namaz_tarihi': gun,
      'namaz_yeri_vakti': 'Öğle Namazını Müteakip-ÖRNEK CAMİİ',
      if (sehit) 'sehit': true,
      if (sehit) 'rutbe': 'Piyade Uzman Çavuş',
      if (bebek) 'bebek': true,
    };

IlVerisi veriYap(String bugun, {Map<String, List<Map<String, dynamic>>> ilceler = const {}, List<Map<String, dynamic>> belirsiz = const []}) =>
    IlVerisi.fromJson('Muğla', {'ilceler': ilceler, 'ilce_belirsiz': belirsiz, 'il_disi': []});

void main() {
  final bugun = bugunTr();

  testWidgets('§27: ilçe görünümünde de şehit kartı listenin başında (ilçesi belirtilmemiş şehit dahil)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun)],
    }, belirsiz: [kayit('s', 'Örnekalp Yıldırımhan', '', bugun, sehit: true)]);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    final sehitY = tester.getTopLeft(find.textContaining('Örnekalp Yıldırımhan')).dy;
    final aliY = tester.getTopLeft(find.text('Ali Örnek')).dy;
    expect(sehitY < aliY, isTrue);
    expect(find.text('ŞEHİT'), findsOneWidget);
    expect(find.text('Ruhu şad olsun, mekânı cennet olsun.'), findsOneWidget);
  });

  testWidgets('§21/1: ilçesiz kaynakta ilanlar "İl geneli" altında, "bugün yok" denmez', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, belirsiz: [kayit('g', 'Veli Örnek', '', bugun)]);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Merkez', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Veli Örnek'), findsOneWidget);
    expect(find.textContaining('cenaze ilanı bulunmuyor'), findsNothing);
    expect(find.text(trBuyuk('İl geneli')), findsOneWidget);
  });

  testWidgets('§21/2: ilçede bugün ilan yoksa ilin diğer ilçelerinin ilanları gösterilir', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun)],
      'Milas': [kayit('b', 'Hasan Örnek', 'Milas', bugun)],
      'Marmaris': [],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Marmaris', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugün Marmaris’te cenaze ilanı bulunmuyor'), findsOneWidget);
    expect(find.text(trBuyuk('Muğla’da bugün: Bodrum, Milas')), findsOneWidget);
    expect(find.text('Ali Örnek'), findsOneWidget);
    expect(find.text('Hasan Örnek'), findsOneWidget);
  });

  testWidgets('§32: adı olan bebek kaydında "Bebek" rozeti', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final r = Ilan.fromJson(kayit('c', 'Elif Örnek', 'Ünye', bugun, bebek: true))!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Bebek'), findsOneWidget);
  });

  testWidgets('§21/3: bildirim teklifi kapalı sabitle gizli (push paketi yok)', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Kars', 'ilce': 'Merkez'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(bildirimTeklifiAcik, isFalse);
    expect(find.text('İlçenizde cenaze ilanı paylaşıldığında haber verelim mi?'), findsNothing);
    expect(find.text('Cenaze ilanı paylaş'), findsOneWidget);
  });

  testWidgets('Bugün ilan yoksa "ilan yok" kartının hemen altında paylaşma bağlantısı; dokununca form açılır', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {'Marmaris': []});
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Marmaris', bugun, bugun))));
    await tester.pumpAndSettle();
    final bosY = tester.getTopLeft(find.text('Bugün Marmaris’te cenaze ilanı bulunmuyor')).dy;
    final davetY = tester.getTopLeft(find.text('Yakınınızın cenaze bilgilerini siz paylaşabilirsiniz')).dy;
    expect(davetY > bosY, isTrue);
    await tester.tap(find.text('Cenaze bilgilerini paylaş'));
    await tester.pumpAndSettle();
    expect(find.text('Cenaze ilanı paylaşın'), findsOneWidget); // form giriş kartıyla açılır
    expect(find.text(trBuyuk(M.aileUstGiris)), findsOneWidget);
  });

  testWidgets('Tam Sayfa: iki giriş, "Yayımlanan vefat ilanları" önizlemeleri, fiyat kartıyla açılan form, şehit formu', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('sekme_1')));
    await tester.pumpAndSettle();
    expect(odemeAcik, isTrue);
    expect(find.text('Vefat ilanı hazırlayın'), findsOneWidget);
    expect(find.text('Şehidimiz için ilan hazırlayın'), findsOneWidget);
    expect(find.text(trBuyuk('Yayımlanan vefat ilanları')), findsOneWidget);
    expect(find.text('NURCİHAN ÖRNEKSOY'), findsOneWidget); // önizleme kartı

    // Önizlemeye dokununca tam ilan + harita bağlantıları
    await tester.tap(find.byKey(const ValueKey('tam_Nurcihan Örneksoy')));
    await tester.pumpAndSettle();
    expect(find.text('Cami · haritada aç'), findsOneWidget);
    expect(find.text('Mezarlık · haritada aç'), findsOneWidget);
    await tester.tap(find.byType(YuvarlakDugme).first);
    await tester.pumpAndSettle();

    // "Vefat ilanı hazırlayın" → fiyat kartı (200 ₺)
    await tester.tap(find.text('Vefat ilanı hazırlayın'));
    await tester.pumpAndSettle();
    expect(find.text('Vefat İlanı'), findsOneWidget);
    expect(find.text('200 ₺'), findsOneWidget);
    expect(find.text(M.fiyatMadde4), findsOneWidget);
    await tester.tap(find.byType(YuvarlakDugme).first);
    await tester.pumpAndSettle();

    // "Şehidimiz için ilan hazırlayın" → 1. adım, ücret yok
    await tester.tap(find.text('Şehidimiz için ilan hazırlayın'));
    await tester.pumpAndSettle();
    expect(find.text('Şehit İlanı'), findsOneWidget);
    expect(find.text(trBuyuk('Adım 1 / 5')), findsOneWidget);
    expect(find.textContaining('₺'), findsNothing);
    final devam = tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Devam'));
    expect(devam.onTap, isNull);
  });
}
