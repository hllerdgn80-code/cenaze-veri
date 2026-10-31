// 30.10.2026 kod denetimi gerileme testleri (deploy/arastirma/kod-denetim-2026-10-30.md): her biri o gün bulunup düzeltilen bir hatayı kilitler.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/menu.dart' show MenuDugmesi;
import 'package:kimin_cenazesi/cekirdek/aile.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/gorevli.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/kisi.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/cekirdek/uzak_ayar.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_panel.dart';
import 'package:kimin_cenazesi/ekranlar/sayfam.dart';
import 'package:kimin_cenazesi/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';
import 'widget_test.dart' show telefon;

const _json = {'content-type': 'application/json; charset=utf-8'};

void main() {
  group('Bildir: veri hattının önekli kimliği Worker\'ın istediği çıplak 16 hane olur', () {
    test('bildirimKimligi "aile-" ve "gorevli-" önekini atar, başka kimliğe dokunmaz', () {
      expect(AileServisi.bildirimKimligi('gorevli-0123456789abcdef'), '0123456789abcdef');
      expect(AileServisi.bildirimKimligi('aile-0123456789abcdef'), '0123456789abcdef');
      expect(AileServisi.bildirimKimligi('0123456789abcdef'), '0123456789abcdef');
      expect(AileServisi.bildirimKimligi('a1'), 'a1');
    });

    test('POST /aile/bildir gövdesinde önek yok', () async {
      Map<String, dynamic>? giden;
      final s = AileServisi(
        kok: 'https://aile.test',
        istemci: MockClient((req) async {
          giden = jsonDecode(req.body) as Map<String, dynamic>;
          return http.Response(jsonEncode({'alindi': true}), 200, headers: _json);
        }),
      );
      final y = await s.bildir('gorevli-0123456789abcdef', 'yanlış bilgi');
      expect(y.tamam, isTrue);
      expect(giden, {'ilan_id': '0123456789abcdef', 'neden': 'yanlış bilgi'});
    });
  });

  testWidgets('Acil düğme: ayar ilanlardan SONRA gelse de gizlenen ilan ekrandan düşer', (tester) async {
    UzakAyar.sifirla();
    addTearDown(UzakAyar.sifirla);
    telefon(tester);
    final bugun = bugunTr();
    final d = await testDurumu(
      onceki: {'il': 'Ordu', 'ilce': 'Ünye'},
      istemci: MockClient((req) async {
        if (req.url.path.endsWith('/ordu/son7gun.json')) {
          return http.Response.bytes(utf8.encode(jsonEncode(ornekOrdu(bugun))), 200, headers: _json);
        }
        if (req.url.path.endsWith('/ayarlar.json')) {
          await Future<void>.delayed(const Duration(milliseconds: 800)); // ilanlardan sonra gelir
          return http.Response(jsonEncode({'acil_gizle': {'id': ['ornek1']}}), 200, headers: _json);
        }
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Ahmet Örnekoğlu'), findsOneWidget); // ilan geldi, ayar henüz yok
    await tester.pump(const Duration(seconds: 2));
    await tester.pumpAndSettle();
    expect(find.text('Ahmet Örnekoğlu'), findsNothing); // ayar geldi → gizlendi
  });

  test('İlin verisi daha önce indiyse kapıdan gelen 404 "ilan yok" değil, önbellekli geçici hata sayılır', () async {
    var kapiDustu = false;
    final d = await testDurumu(
      istemci: MockClient((req) async {
        if (req.url.path.endsWith('/ordu/son7gun.json')) {
          if (kapiDustu) return http.Response('', 404); // kapı, kaynağın hatasını 404'e çevirir
          return http.Response.bytes(utf8.encode(jsonEncode(ornekOrdu(bugunTr()))), 200, headers: _json);
        }
        return http.Response('yok', 404);
      }),
    );
    final ilk = await d.veri.ilGetir('Ordu');
    expect(ilk.veri!.kaynakli, isTrue);
    kapiDustu = true;
    final ikinci = await d.veri.ilGetir('Ordu');
    expect(ikinci.veri!.kaynakli, isTrue);
    expect(ikinci.veri!.bul('ornek1'), isNotNull);
    expect(ikinci.durum, VeriDurumu.onbellek);
    final kars = await d.veri.ilGetir('Kars'); // hiç verisi olmayan il: gerçekten kaynaksız
    expect(kars.veri!.kaynakli, isFalse);
  });

  // ---- Gezgin (Navigator) akışları, GERÇEK uygulamadaki gibi açılış mesajı AÇIKKEN (acilisAcik: true) ----
  Future<AppDurum> acilisliDurum(Map<String, Object> onceki, {http.Client? istemci}) async {
    SharedPreferences.setMockInitialValues(onceki);
    final depo = await Depo.ac();
    return AppDurum(depo: depo, veri: VeriServisi(istemci: istemci ?? sahteAg(bugunTr()), depo: depo), gomulu: testGomulu(), acilisAcik: true);
  }

  Future<void> acilisBitir(WidgetTester tester, AppDurum d) async {
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pump();
    await tester.pump(const Duration(seconds: 12));
    await tester.pumpAndSettle();
  }

  testWidgets('Açılış mesajı açıkken: kayıtlı il → kabuk; başlıktan ve menüden adres değişir, seçim ekranları kapanır', (tester) async {
    telefon(tester);
    final d = await acilisliDurum({'il': 'Ordu', 'ilce': 'Ünye'});
    await acilisBitir(tester, d);
    expect(find.text('Ordu · Ünye'), findsOneWidget);

    await tester.tap(find.text('Ordu · Ünye')); // başlık → il seçimi
    await tester.pumpAndSettle();
    expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    await tester.tap(find.text('Kars'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Merkez'));
    await tester.pumpAndSettle();
    expect(find.text('Kars · Merkez'), findsOneWidget);
    expect(find.text('Bulunduğunuz ili seçin'), findsNothing);

    await tester.tap(find.byType(MenuDugmesi).first); // ⋮ → Adresi değiştir
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.menuAdres));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ordu'));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.ilceTumu));
    await tester.pumpAndSettle();
    expect(find.text('Bulunduğunuz ili seçin'), findsNothing);
    expect(find.text('Ordu'), findsWidgets);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Açılış mesajı açıkken: ilk kurulum il → ilçe → kabuk, beş sekme açılır', (tester) async {
    telefon(tester);
    final d = await acilisliDurum({});
    await acilisBitir(tester, d);
    expect(find.text('Bulunduğunuz ili seçin'), findsOneWidget);
    await tester.tap(find.text('Ordu'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ünye'));
    await tester.pumpAndSettle();
    expect(find.text('Ordu · Ünye'), findsOneWidget);
    for (final i in [1, 2, 3, 4, 0]) {
      await tester.tap(find.byKey(ValueKey('sekme_$i')));
      await tester.pumpAndSettle();
    }
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Açılış mesajı açıkken: din görevlisi kaydı → parola → KVKK → sorumluluk → panel → kilitle/aç → çıkış', (tester) async {
    telefon(tester);
    final ist = MockClient((req) async {
      final p = req.url.path;
      if (p.endsWith('/ordu/son7gun.json')) return http.Response.bytes(utf8.encode(jsonEncode(ornekOrdu(bugunTr()))), 200, headers: _json);
      http.Response y(Map<String, dynamic> m) => http.Response(jsonEncode(m), 200, headers: _json);
      if (p == '/gorevli/eposta-kod') return y({'durum': 'kod_gonderildi', 'adres': 'ali@diyanet.gov.tr'});
      if (p == '/gorevli/eposta-dogrula') return y({'durum': 'onayli', 'oturum': 'tok', 'profil_tamam': true});
      if (p == '/gorevli/parola' || p == '/gorevli/kvkk-kabul' || p == '/gorevli/sorumluluk-kabul') return y({'durum': 'kaydedildi'});
      if (p == '/gorevli/durum') {
        return y({'durum': 'onayli', 'profil_tamam': true, 'ad_soyad': 'Hasan K', 'il': 'Ordu', 'ilce': 'Ünye', 'gorev_yeri': 'Merkez Camii', 'unvan': 'İmam-Hatip'});
      }
      if (p == '/gorevli/ilanlarim') return y({'ilanlar': <dynamic>[]});
      return http.Response('yok', 404);
    });
    final d = await acilisliDurum({'il': 'Ordu', 'ilce': 'Ünye'}, istemci: ist);
    await acilisBitir(tester, d);
    Finder alan(String anahtar) => find.descendant(of: find.byKey(ValueKey(anahtar)).last, matching: find.byType(TextField));

    await tester.tap(find.byKey(const ValueKey('sekme_4')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('panel_kayit')));
    await tester.pumpAndSettle();
    await tester.enterText(alan('g_kullanici'), 'ali');
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliKodGonderDugme));
    await tester.pumpAndSettle();
    await tester.enterText(alan('g_kod'), '123456');
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliKodDogrulaDugme));
    await tester.pumpAndSettle();
    expect(find.text(M.pinBelirleBaslik), findsWidgets); // tam ekran parola belirleme
    await tester.enterText(alan('pin_1'), '1234');
    await tester.enterText(alan('pin_2'), '1234');
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('pin_kaydet')).last);
    await tester.pumpAndSettle();
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliKvkkBaslik), findsOneWidget);
    await tester.tap(find.text(M.gorevliKvkkOku));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliSorumlulukBaslik), findsOneWidget);
    await tester.tap(find.text(M.gorevliSorumlulukKabul));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliIlanPaylas), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('g_menu'))); // kilitle → parolayla yeniden aç
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.panelKilitle));
    await tester.pumpAndSettle();
    expect(find.text(M.pinGirBaslik), findsOneWidget);
    await tester.enterText(alan('pin_gir'), '1234');
    await tester.tap(find.byKey(const ValueKey('pin_ac')));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliIlanPaylas), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('g_menu'))); // çıkış → İlanlar sekmesi
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliCikisYap));
    await tester.pumpAndSettle();
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliOturum, isNull);
    expect(d.sekme, 0);
    await tester.pumpWidget(const SizedBox());
  });

  group('Namaz vakti yalnız vakit kısmından okunur', () {
    test('cami adındaki "Sabah"/"Cuma" sözcüğü vakit sayılmaz', () {
      expect(vakitBul('-SABAHATTİN CAMİİ'), '');
      expect(vakitBul('İkindi Namazını Müteakip-CUMA CAMİİ'), 'İkindi');
      expect(vakitBul('Öğle Namazını Müteakip-ÖRNEK CAMİİ'), 'Öğle');
      expect(vakitBul('Cuma Namazını Müteakip'), 'Cuma');
      expect(vakitBul(null), '');
    });
  });

  group('Kaybettiklerimiz tanıtım satırı: Türkçe harf', () {
    test('i ile başlayan meslek "İ" ile büyür (Iktisatçı değil)', () {
      expect(tanitimYap({'meslek': 'iktisatçı'}), 'İktisatçı');
      expect(tanitimYap({'meslek': 'ilahiyatçı, imam', 'neden_onemli': ''}, enCok: 2), 'İlahiyatçı, imam');
    });

    test('yaş ve sitelink metin gelse de kayıt çökmez', () {
      final k = Kisi.fromJson({'ad': 'Ali Veli', 'wikidata_id': 'Q1', 'vefat_yasi': '70', 'sitelink': '12', 'meslek': 'imam'});
      expect(k.yas, 70);
      expect(k.sitelink, 12);
      expect(k.tanitim, 'İmam');
    });
  });

  // Kapsam testi (hata değildi: bildirim, kart yeniden çizilmeden önce gösteriliyor): akış bozulursa yakalansın
  testWidgets('Sayfam: kaydı kaldırınca "Sayfanızdan kaldırıldı" bildirimi görünür', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await d.sayfamaEkle(Ilan.fromJson({'id': 'k1', 'ad_soyad': 'Ali Kaya', 'ilce': 'Merkez', 'cinsiyet': 'Erkek', 'namaz_tarihi': bugunTr()})!);
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: const Scaffold(body: SayfamEkrani()))));
    await tester.pumpAndSettle();
    expect(find.text('Ali Kaya'), findsOneWidget);

    await tester.tap(find.byTooltip('Seçenekler'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(PopupMenuItem<String>, M.kartKaldir)); // 31.10: kart altında da aynı yazı var
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.kaldirTamam));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Ali Kaya'), findsNothing);
    expect(find.text(M.bildirimKaldirildi), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  /// Din görevlisinin kendi ilanını düzenleme formunu açar; sunucuya giden gövdeleri yoluna göre toplar
  Future<Map<String, Map<String, dynamic>>> duzenleFormu(WidgetTester tester) async {
    telefon(tester);
    final d = await testDurumu();
    await d.depo.gorevliOturumKaydet('tok');
    final govdeler = <String, Map<String, dynamic>>{};
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        govdeler[req.url.path] = jsonDecode(req.body) as Map<String, dynamic>;
        return http.Response(jsonEncode({'durum': 'yayinda', 'ilan_id': '0123456789abcdef'}), 200, headers: _json);
      }),
    );
    final bugun = bugunTr();
    await tester.pumpWidget(Kapsam(
      durum: d,
      child: MaterialApp(
        theme: temaYap(true),
        home: GorevliIlanFormu(
          hesap: const GorevliHesap('onayli', 'Hasan Kaya', 'Ordu', 'Korgan', 'Merkez Camii', 'İmam-Hatip'),
          servis: servis,
          duzenle: {
            'id': '0123456789abcdef',
            'ad_soyad': 'Ali Kaya',
            'cinsiyet': 'e',
            'yas': 70,
            'vefat_tarihi': bugun,
            'namaz_tarihi': bugun,
            'defin_yeri': 'Örnek Mezarlığı',
            'namaz_yeri_vakti': 'Öğle Namazını Müteakip-Merkez Camii',
          },
        ),
      ),
    ));
    await tester.pumpAndSettle();
    return govdeler;
  }

  Future<void> kaydet(WidgetTester tester) async {
    await tester.scrollUntilVisible(find.text(M.gorevliKaydet), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text(M.gorevliKaydet));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
  }

  testWidgets('Din görevlisi ilanını düzenlerken yaş "Belirtilmedi" yapılır ve mezarlık silinirse sunucuya açıkça null gider', (tester) async {
    final govdeler = await duzenleFormu(tester);
    Finder alan(String anahtar) => find.descendant(of: find.byKey(ValueKey(anahtar)), matching: find.byType(TextField));
    await tester.scrollUntilVisible(find.byKey(const ValueKey('gi_yas_yok')), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.byKey(const ValueKey('gi_yas_yok')));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(alan('gi_mezarlik'), 200, scrollable: find.byType(Scrollable).first);
    await tester.enterText(alan('gi_mezarlik'), '');
    await tester.pumpAndSettle();
    await kaydet(tester);

    final g = govdeler['/gorevli/ilan/duzenle'];
    expect(g, isNotNull);
    expect(g!['ilan_id'], '0123456789abcdef');
    expect(g.containsKey('yas'), isTrue);
    expect(g['yas'], isNull);
    expect(g.containsKey('defin_yeri'), isTrue);
    expect(g['defin_yeri'], isNull);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Kendi ilanını düzenlerken yalnız vakit değişirse cami adı korunur (kayıtlı vakit/cami forma yüklenir)', (tester) async {
    final govdeler = await duzenleFormu(tester);
    await tester.scrollUntilVisible(find.text('İkindi Namazını Müteakip'), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('İkindi Namazını Müteakip'));
    await tester.pumpAndSettle();
    await kaydet(tester);

    final g = govdeler['/gorevli/ilan/duzenle'];
    expect(g, isNotNull);
    expect(g!['namaz_yeri_vakti'], 'İkindi Namazını Müteakip-Merkez Camii');
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });
}
