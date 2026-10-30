// Günlük cenaze bildirimi (0.1.4, URUN-TASLAGI §36/§22): metin kalıbı, "7 gün yeniden sorma", zamanlama, günde en çok 2 /
// 21:00–07:00 sessiz kuralı (saf Dart) + ilk açılış kartı (sahte bildirim arayüzüyle widget testi).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/bildirim.dart';
import 'package:kimin_cenazesi/cekirdek/bildirim_mantik.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';

class SahteBildirim implements BildirimArkayuzu {
  final bool izinVer;
  int izinSayisi = 0, planSayisi = 0, iptalSayisi = 0;
  SahteBildirim({this.izinVer = true});
  @override
  Future<bool> izinIste() async {
    izinSayisi++;
    return izinVer;
  }

  @override
  Future<void> planla() async => planSayisi++;
  @override
  Future<void> iptal() async => iptalSayisi++;
}

Future<AppDurum> kartliDurum(SahteBildirim b, {Map<String, Object> onceki = const {}, bool acilisAcik = false}) async {
  SharedPreferences.setMockInitialValues(onceki);
  final depo = await Depo.ac();
  final veri = VeriServisi(istemci: sahteAg(bugunTr()), depo: depo);
  return AppDurum(depo: depo, veri: veri, gomulu: testGomulu(), bildirim: b, bildirimSorusuAcik: true, acilisAcik: acilisAcik);
}

void telefon(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 2340);
  tester.view.devicePixelRatio = 3.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

void main() {
  group('bildirim metni (§22)', () {
    test('ilçe seçiliyse ilçe, değilse il; onaylı kalıp', () {
      expect(bildirimMetni('Ordu', 'Ünye'), 'Ünye’de bugünkü cenaze ilanlarını göster');
      expect(bildirimMetni('Ordu', null), 'Ordu’da bugünkü cenaze ilanlarını göster');
      expect(bildirimMetni('Kars', ''), 'Kars’ta bugünkü cenaze ilanlarını göster');
      expect(bildirimMetni('Kars', 'Merkez'), 'Kars Merkez’de bugünkü cenaze ilanlarını göster');
    });

    test('sayı, ünlem, pazar dili yok', () {
      final t = bildirimMetni('Ordu', 'Ünye');
      expect(RegExp(r'\d').hasMatch(t), isFalse);
      expect(t.contains('!'), isFalse);
      for (final yasak in ['yeni', 'Yeni', 'hemen', 'Kaçırma', 'Son dakika']) {
        expect(t.contains(yasak), isFalse);
      }
    });
  });

  group('7 gün yeniden sorulmaz (§36)', () {
    test('cevap yoksa ve hiç ertelenmediyse sorulur', () {
      expect(soruZamaniGeldi(izin: null, erteleGunu: null, bugun: '2026-10-15'), isTrue);
    });
    test('evet ya da hayır cevabı varsa sorulmaz', () {
      expect(soruZamaniGeldi(izin: true, erteleGunu: null, bugun: '2026-10-15'), isFalse);
      expect(soruZamaniGeldi(izin: false, erteleGunu: null, bugun: '2026-10-15'), isFalse);
    });
    test('"Şimdi değil" sonrası 7 gün dolana dek sorulmaz', () {
      expect(soruZamaniGeldi(izin: null, erteleGunu: '2026-10-15', bugun: '2026-10-15'), isFalse);
      expect(soruZamaniGeldi(izin: null, erteleGunu: '2026-10-15', bugun: '2026-10-21'), isFalse);
      expect(soruZamaniGeldi(izin: null, erteleGunu: '2026-10-15', bugun: '2026-10-22'), isTrue);
      expect(soruZamaniGeldi(izin: null, erteleGunu: '2026-10-28', bugun: '2026-11-04'), isTrue);
      expect(soruZamaniGeldi(izin: null, erteleGunu: '2026-10-28', bugun: '2026-11-03'), isFalse);
    });
  });

  group('zamanlama', () {
    test('sonraki pencere: bugün henüz gelmediyse bugün, geçtiyse yarın', () {
      expect(sonrakiPencere(DateTime(2026, 10, 15, 7, 59), 8), DateTime(2026, 10, 15, 8));
      expect(sonrakiPencere(DateTime(2026, 10, 15, 8), 8), DateTime(2026, 10, 16, 8));
      expect(sonrakiPencere(DateTime(2026, 10, 15, 13), 12), DateTime(2026, 10, 16, 12));
      expect(sonrakiPencere(DateTime(2026, 10, 31, 23), 8), DateTime(2026, 11, 1, 8));
    });
    test('sabah 08:00, öğle 12:00', () {
      final s = DateTime(2026, 10, 15, 9);
      expect(sonrakiCalisma(s, BildirimRolu.sabah), DateTime(2026, 10, 16, 8));
      expect(sonrakiCalisma(s, BildirimRolu.ogle), DateTime(2026, 10, 15, 12));
    });
    test('21:00–07:00 sessiz', () {
      expect(sessizSaat(DateTime(2026, 10, 15, 21)), isTrue);
      expect(sessizSaat(DateTime(2026, 10, 15, 20, 59)), isFalse);
      expect(sessizSaat(DateTime(2026, 10, 15, 6, 59)), isTrue);
      expect(sessizSaat(DateTime(2026, 10, 15, 7)), isFalse);
    });
  });

  group('günde en çok iki bildirim', () {
    const bugun = '2026-10-15';
    final sabah8 = DateTime(2026, 10, 15, 8, 4);
    final ogle12 = DateTime(2026, 10, 15, 12, 6);

    bool bak(BildirimRolu r, DateTime t, {bool izin = true, String? sabahGunu, String? ogleGunu}) =>
        bakmayaDeger(rol: r, simdi: t, bugun: bugun, izinAcik: izin, sabahGunu: sabahGunu, ogleGunu: ogleGunu);

    test('izin kapalıysa ya da sessiz saatteyse hiç bakılmaz', () {
      expect(bak(BildirimRolu.sabah, sabah8, izin: false), isFalse);
      expect(bak(BildirimRolu.sabah, DateTime(2026, 10, 15, 22)), isFalse);
      expect(bak(BildirimRolu.sabah, DateTime(2026, 10, 15, 3)), isFalse);
    });
    test('sabah: bugün henüz gönderilmediyse bakılır', () {
      expect(bak(BildirimRolu.sabah, sabah8), isTrue);
      expect(bak(BildirimRolu.sabah, sabah8, sabahGunu: bugun), isFalse);
      expect(bak(BildirimRolu.sabah, sabah8, sabahGunu: '2026-10-14'), isTrue);
    });
    test('öğle: yalnız sabah bildirimi gittiyse ve ikincisi gitmediyse', () {
      expect(bak(BildirimRolu.ogle, ogle12), isFalse); // sabah bildirimi yok
      expect(bak(BildirimRolu.ogle, ogle12, sabahGunu: '2026-10-14'), isFalse); // dünkü kayıt sayılmaz
      expect(bak(BildirimRolu.ogle, ogle12, sabahGunu: bugun), isTrue);
      expect(bak(BildirimRolu.ogle, ogle12, sabahGunu: bugun, ogleGunu: bugun), isFalse);
    });
    test('sabah: ilan varsa gönder, yoksa sessiz', () {
      expect(bildirimGonderilsin(rol: BildirimRolu.sabah, bugunkuler: {'a'}, sabahGorulen: {}), isTrue);
      expect(bildirimGonderilsin(rol: BildirimRolu.sabah, bugunkuler: {}, sabahGorulen: {}), isFalse);
    });
    test('öğle: yalnız sabahtan sonra YENİ ilan düştüyse', () {
      expect(bildirimGonderilsin(rol: BildirimRolu.ogle, bugunkuler: {'a'}, sabahGorulen: {'a'}), isFalse);
      expect(bildirimGonderilsin(rol: BildirimRolu.ogle, bugunkuler: {'a', 'b'}, sabahGorulen: {'a'}), isTrue);
      expect(bildirimGonderilsin(rol: BildirimRolu.ogle, bugunkuler: {}, sabahGorulen: {'a'}), isFalse);
    });
  });

  group('bugünkü ilanlar (bölge)', () {
    final bugun = bugunTr();
    test('seçili ilçedeki bugünün ilanları; başka ilçe ve başka gün sayılmaz', () {
      final v = IlVerisi.fromJson('Ordu', ornekOrdu(bugun));
      expect(bugunIlanlari(v, 'Ünye', bugun), {'ornek1'});
      expect(bugunIlanlari(v, null, bugun), {'ornek1'});
      expect(bugunIlanlari(v, 'Altınordu', bugun), isEmpty);
      expect(bugunIlanlari(v, 'Ünye', gunEkle(bugun, 1)), isEmpty);
    });
    test('kaynaksız il boş döner', () {
      expect(bugunIlanlari(const IlVerisi(il: 'Kars', kaynakli: false), null, bugun), isEmpty);
    });
  });

  group('ilk açılış kartı', () {
    const soru = 'Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?';

    testWidgets('başka ekrandan önce çıkar; Evet → sistem izni → zamanlama → il seçimi', (tester) async {
      telefon(tester);
      final b = SahteBildirim();
      final d = await kartliDurum(b);
      await tester.pumpWidget(KiminCenazesi(durum: d));
      await tester.pumpAndSettle();
      expect(find.text(soru), findsOneWidget);
      expect(find.text('Bulunduğunuz ili seçin'), findsNothing);

      await tester.tap(find.text('Evet, haber verin'));
      await tester.pumpAndSettle();
      expect(b.izinSayisi, 1);
      expect(b.planSayisi, 1);
      expect((await SharedPreferences.getInstance()).getBool('izin'), isTrue);
      expect(find.text(soru), findsNothing);
      expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    });

    // 30.10.2026 gerileme testi (sahibi: "Evet dedim, ekran takıldı, il seçimine ilerlemedi"): açılış mesajı AÇIKKEN
    // (gerçek uygulamadaki akış) kart cevaptan sonra kapanmalı. Hata: AcilisMesaji sonrasını ayrı rota olarak açıyordu.
    testWidgets('açılış mesajından sonra gelen kart cevaplanınca il seçimine geçer (Evet ve Şimdi değil)', (tester) async {
      for (final dugme in ['Evet, haber verin', 'Şimdi değil']) {
        telefon(tester);
        final b = SahteBildirim();
        final d = await kartliDurum(b, acilisAcik: true);
        await tester.pumpWidget(KiminCenazesi(durum: d));
        await tester.pump();
        expect(find.text(soru), findsNothing); // önce açılış mesajı
        await tester.pump(const Duration(seconds: 12));
        await tester.pumpAndSettle();
        expect(find.text(soru), findsOneWidget);
        await tester.tap(find.text(dugme));
        await tester.pumpAndSettle();
        expect(find.text(soru), findsNothing);
        expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
        await tester.pumpWidget(const SizedBox());
      }
    });

    testWidgets('sistem izni verilmezse kapalı kalır, il seçimine geçilir', (tester) async {
      telefon(tester);
      final b = SahteBildirim(izinVer: false);
      final d = await kartliDurum(b);
      await tester.pumpWidget(KiminCenazesi(durum: d));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Evet, haber verin'));
      await tester.pumpAndSettle();
      expect(b.planSayisi, 0);
      expect((await SharedPreferences.getInstance()).getBool('izin'), isFalse);
      expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    });

    testWidgets('Şimdi değil → bugün kaydedilir, izin istenmez, zamanlama yok', (tester) async {
      telefon(tester);
      final b = SahteBildirim();
      final d = await kartliDurum(b);
      await tester.pumpWidget(KiminCenazesi(durum: d));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Şimdi değil'));
      await tester.pumpAndSettle();
      final p = await SharedPreferences.getInstance();
      expect(p.getString('izin_ertele'), bugunTr());
      expect(p.getBool('izin'), isNull);
      expect(b.izinSayisi, 0);
      expect(b.planSayisi, 0);
      expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    });

    testWidgets('7 gün dolmadıysa yeniden çıkmaz; dolduysa çıkar', (tester) async {
      telefon(tester);
      final yeni = await kartliDurum(SahteBildirim(), onceki: {'izin_ertele': gunEkle(bugunTr(), -3)});
      expect(yeni.bildirimSorusuGerek, isFalse);
      final eski = await kartliDurum(SahteBildirim(), onceki: {'izin_ertele': gunEkle(bugunTr(), -7)});
      expect(eski.bildirimSorusuGerek, isTrue);
      await tester.pumpWidget(KiminCenazesi(durum: eski));
      await tester.pumpAndSettle();
      expect(find.text(soru), findsOneWidget);
    });

    testWidgets('cevap vermiş kullanıcıya sorulmaz; testlerde (bildirimSorusuAcik=false) kart atlanır', (tester) async {
      final cevaplamis = await kartliDurum(SahteBildirim(), onceki: {'izin': true});
      expect(cevaplamis.bildirimSorusuGerek, isFalse);
      final d = await testDurumu();
      expect(d.bildirimSorusuGerek, isFalse);
    });
  });

  group('ayarlardan aç-kapa', () {
    test('açınca izin istenir ve zamanlanır; kapatınca iptal edilir', () async {
      final b = SahteBildirim();
      final d = await kartliDurum(b, onceki: {'izin': false});
      expect(d.bildirimAcik, isFalse);
      expect(await d.bildirimAyarla(true), isTrue);
      expect(d.bildirimAcik, isTrue);
      expect(b.planSayisi, 1);
      expect(await d.bildirimAyarla(false), isFalse);
      expect(d.bildirimAcik, isFalse);
      expect(b.iptalSayisi, 1);
    });
    test('sistem izni verilmezse açılmaz', () async {
      final b = SahteBildirim(izinVer: false);
      final d = await kartliDurum(b, onceki: {'izin': false});
      expect(await d.bildirimAyarla(true), isFalse);
      expect(d.bildirimAcik, isFalse);
      expect(b.planSayisi, 0);
    });
  });
}
