// Din görevlisi (0.1.5, URUN-TASLAGI §37): kayıt formu (iki adım, kart fotoğrafı, SMS kodu), panel (sabit başlık kartı,
// kontrolde iken pasif "İlan paylaş", onayda etkin, redde "hesap silindi"), il/ilçe kilidi, kartta rozet.
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/ortak.dart' show AnaDugme;
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/gorevli.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart' show trBuyuk;
import 'package:kimin_cenazesi/ekranlar/gorevli_kayit.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_panel.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

const _json = {'content-type': 'application/json; charset=utf-8'};
http.Response _y(Map<String, dynamic> m, [int kod = 200]) => http.Response(jsonEncode(m), kod, headers: _json);

Widget _ev(AppDurum d, Widget Function(BuildContext) ac) => Kapsam(
      durum: d,
      child: MaterialApp(
        theme: temaYap(true),
        home: Builder(builder: (c) => Scaffold(body: Center(child: ElevatedButton(onPressed: () => Navigator.of(c).push(MaterialPageRoute(builder: (_) => ac(c))), child: const Text('ac'))))),
      ),
    );

Finder _alan(String anahtar) => find.descendant(of: find.byKey(ValueKey(anahtar)), matching: find.byType(TextField));

Future<void> _yazF(WidgetTester t, String anahtar, String metin) async {
  final f = find.descendant(of: find.byKey(ValueKey(anahtar)), matching: find.byType(TextField));
  await t.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
  await t.enterText(f, metin);
  await t.pumpAndSettle();
}

Future<void> _yaz(WidgetTester t, String anahtar, String metin) async {
  final f = _alan(anahtar);
  await t.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
  await t.enterText(f, metin);
  await t.pumpAndSettle();
}

void main() {
  testWidgets('Kayıt formu: bilgiler (telefon, e-posta YOK) + BEYAN kutusu; işaretlenmeden "Başvuruyu gönder" pasif; sonra kart (yalnız kamera, kâğıt kodu YOK); telefon kodu', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        final govde = req.body.isEmpty ? <String, dynamic>{} : jsonDecode(req.body) as Map<String, dynamic>;
        istekler['${req.url.path}#${istekler.length}'] = govde;
        if (req.url.path == '/gorevli/kayit' && !govde.containsKey('foto_base64')) {
          return _y({'durum': 'foto_gerek', 'kayit_id': 'k1', 'liste_eslesti': true});
        }
        if (req.url.path == '/gorevli/kayit') return _y({'durum': 'kuyruk', 'kayit_id': 'k1', 'dogrulama': 'kod', 'kanal': 'sms'});
        if (req.url.path == '/gorevli/dogrula') return _y({'durum': 'kuyruk', 'oturum': 'tok123'});
        return http.Response('yok', 404);
      }),
    );
    var cekilen = 0;
    await tester.pumpWidget(Kapsam(
      durum: d,
      child: MaterialApp(
        theme: temaYap(true),
        home: GorevliKayit(
          il: 'Kars',
          ilce: 'Merkez',
          servis: servis,
          fotoAl: () async {
            cekilen++;
            return Uint8List.fromList([0xFF, 0xD8, 0xFF, 1, 2, 3]);
          },
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliGirisNot), findsOneWidget); // "Hesabınız Diyanet personel kartınızla doğrulanır." (üstte, görünür)
    expect(find.text('E-posta'), findsNothing);
    await _yaz(tester, 'g_ad', 'Hasan Kurguluoğlu');
    await _yaz(tester, 'g_yer', 'Korgan Merkez Camii');
    await _yaz(tester, 'g_telefon', '0532 111 22 33'); // alan kaydırılarak görünür kılınır (ListView tembel kurar)
    expect(find.text(M.gorevliTelefon), findsOneWidget);
    expect(find.text(M.gorevliTelefonNot), findsOneWidget); // KVKK notu
    // beyan işaretlenmeden pasif
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, M.gorevliBasvuruGonder)).onTap, isNull);
    await tester.scrollUntilVisible(find.byKey(const ValueKey('g_beyan')), 200, scrollable: find.byType(Scrollable).first);
    expect(find.text(M.gorevliBeyan), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('g_beyan')));
    await tester.pumpAndSettle();
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, M.gorevliBasvuruGonder)).onTap, isNotNull);
    await tester.tap(find.text(M.gorevliBasvuruGonder));
    await tester.pumpAndSettle();

    final ilk = istekler.values.first;
    expect(ilk['telefon'], '5321112233');
    expect(ilk['beyan'], true);
    expect(ilk.containsKey('eposta'), isFalse);
    expect(ilk['gorev_yeri'], 'Korgan Merkez Camii');
    // kart ekranı: başlık, sahibinin metni EN ÜSTTE, yönerge, tek düğme "Personel kartımı çek"; kâğıt kodu ve galeri YOK
    expect(find.text(trBuyuk(M.gorevliFotoUst)), findsWidgets); // BaslikCubugu üst etiketi BÜYÜK HARF basar (trBuyuk)
    expect(find.text(M.gorevliFotoAciklama), findsOneWidget);
    expect(find.text(M.gorevliFotoYonerge), findsOneWidget);
    expect(find.text(M.gorevliListedeBulundu), findsNothing); // liste artık onay şartı değil; kullanıcıya gösterilmez
    expect(find.byKey(const ValueKey('g_foto_kodu')), findsNothing);
    expect(find.textContaining('kâğıt'), findsNothing);
    expect(find.text('Galeriden seç'), findsNothing);
    final kutuY = tester.getTopLeft(find.byKey(const ValueKey('g_foto_aciklama'))).dy;
    final kameraY = tester.getTopLeft(find.text('Personel kartımı çek')).dy;
    expect(kutuY < kameraY, isTrue);

    await tester.tap(find.text('Personel kartımı çek'));
    await tester.pumpAndSettle();
    expect(cekilen, 1);
    final foto = istekler.values.elementAt(1);
    expect(foto['kayit_id'], 'k1');
    expect(base64Decode(foto['foto_base64'] as String).length, 6);
    // telefon kodu ekranı + saklama bilgisi + yeniden gönder (60 sn bekleme)
    expect(find.text(M.gorevliKodAciklama), findsOneWidget);
    expect(find.text(M.gorevliKuyrukUyari), findsOneWidget);
    expect(find.text(M.kodBekle(60)), findsOneWidget);
    await _yaz(tester, 'g_kod', '123456');
    await tester.tap(find.text(M.kodDugme));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliKontrolMetin), findsOneWidget);
    expect(d.depo.gorevliOturum, 'tok123');
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Kart tutmazsa aynı ekranda yeniden çekilir (kod yok); iki kez tutmazsa 7 gün uyarısı', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    var foto = 0;
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        final g = req.body.isEmpty ? <String, dynamic>{} : jsonDecode(req.body) as Map<String, dynamic>;
        if (req.url.path == '/gorevli/kayit' && g.containsKey('foto_base64')) {
          foto++;
          return foto == 1 ? _y({'durum': 'deneme2', 'kayit_id': 'k1'}) : _y({'durum': 'kuyruk', 'kayit_id': 'k1', 'dogrulama': 'kod'});
        }
        if (req.url.path == '/gorevli/kayit') return _y({'durum': 'foto_gerek', 'kayit_id': 'k1'});
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(Kapsam(
      durum: d,
      child: MaterialApp(theme: temaYap(true), home: GorevliKayit(il: 'Kars', ilce: 'Merkez', servis: servis, fotoAl: () async => Uint8List.fromList([0xFF, 0xD8, 1]))),
    ));
    await _yaz(tester, 'g_ad', 'Hasan Kurguluoğlu');
    await _yaz(tester, 'g_yer', 'Korgan Merkez Camii');
    await _yaz(tester, 'g_telefon', '5321112233');
    await tester.scrollUntilVisible(find.byKey(const ValueKey('g_beyan')), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.byKey(const ValueKey('g_beyan')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliBasvuruGonder));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Personel kartımı çek'));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliDeneme2), findsOneWidget);
    await tester.tap(find.text('Personel kartımı çek'));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliKuyrukUyari), findsOneWidget); // OCR iki kez tutmadı
    await tester.pumpWidget(const SizedBox());
  });

  Future<AppDurum> panelDurumu() async {
    final d = await testDurumu();
    await d.depo.gorevliOturumKaydet('tok');
    return d;
  }

  GorevliServisi panelServisi(String durum, {List<Map<String, dynamic>> ilanlar = const []}) => GorevliServisi(
        kok: 'https://g.test',
        istemci: MockClient((req) async {
          if (req.url.path == '/gorevli/durum') {
            if (durum == 'silindi') return _y({'durum': 'silindi'});
            return _y({'durum': durum, 'ad_soyad': 'Hasan Kurguluoğlu', 'il': 'Ordu', 'ilce': 'Korgan', 'gorev_yeri': 'Korgan Merkez Camii', 'unvan': 'İmam-Hatip'});
          }
          if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': ilanlar});
          return http.Response('yok', 404);
        }),
      );

  testWidgets('Panel (kontrolde): sabit başlık kartı, bilgi kutusu, İlan paylaş PASİF (dokununca açıklama), İlanlarım boş', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: panelServisi('kuyruk'))));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect((tester.widget(find.byKey(const ValueKey('g_kart_1'))) as Text).data, 'Korgan Merkez Camii İmam Hatibi');
    expect((tester.widget(find.byKey(const ValueKey('g_kart_2'))) as Text).data, 'Hasan Kurguluoğlu');
    expect((tester.widget(find.byKey(const ValueKey('g_kart_3'))) as Text).data, 'Ordu · Korgan');
    expect(find.byKey(const ValueKey('g_kontrol_kutusu')), findsOneWidget);
    expect(find.text(M.gorevliIlanlarim(0)), findsOneWidget);
    // başlık kartı kaydırınca kaybolmaz: ListView'ın DIŞINDA
    expect(find.descendant(of: find.byType(ListView), matching: find.byKey(const ValueKey('g_baslik_karti'))), findsNothing);
    // pasif düğme: soluk, dokununca açıklama
    final op = tester.widget<Opacity>(find.descendant(of: find.byKey(const ValueKey('g_ilan_paylas')), matching: find.byType(Opacity)).first);
    expect(op.opacity < 1, isTrue);
    await tester.tap(find.byKey(const ValueKey('g_ilan_paylas')));
    await tester.pump();
    expect(find.text(M.gorevliKontrolBilgi), findsNWidgets(2)); // bilgi kutusu + açıklama (snackbar)
    expect(find.byType(GorevliIlanFormu), findsNothing);
  });

  testWidgets('Panel (onaylı): düğme etkin; ilan formunda il ve ilçe KİLİTLİ görünür ama değiştirilemez', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: panelServisi('onayli', ilanlar: [
          {'id': 'i1', 'ad_soyad': 'Nurcihan Örneksoy', 'namaz_tarihi': bugun0(), 'durum': 'yayinda'},
        ]))));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('g_kontrol_kutusu')), findsNothing);
    expect(find.text(M.gorevliIlanlarim(1)), findsOneWidget);
    expect(find.text('Nurcihan Örneksoy'), findsOneWidget); // son ilanlar
    await tester.tap(find.text(M.gorevliIlanPaylas));
    await tester.pumpAndSettle();
    expect(find.byType(GorevliIlanFormu), findsOneWidget);
    expect(find.text('Ordu'), findsOneWidget);
    expect(find.text('Korgan'), findsOneWidget);
    expect(find.text(M.gorevliYerKilit), findsOneWidget);
    // il/ilçe satırları dokunmaya kapalı (onTap null): açılan seçim penceresi yok
    await tester.tap(find.text('Ordu'));
    await tester.pumpAndSettle();
    expect(find.byType(Dialog), findsNothing);
  });

  testWidgets('Panel (onaylı): "Şehit cenazesi" anahtarı §27 alanlarını açar ve şehit:true gönderir; liste satırı "Şehidimiz <Rütbe Ad>"', (tester) async {
    // UZUN ekran: form ListView'ı tamamen kurulur, kaydırma gerekmez (tembel kurulum ve çoklu Scrollable belirsizliği yok)
    tester.view.physicalSize = const Size(1080, 7000);
    tester.view.devicePixelRatio = 3.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final d = await panelDurumu();
    Map<String, dynamic>? giden;
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        if (req.url.path == '/gorevli/durum') return _y({'durum': 'onayli', 'ad_soyad': 'Hasan Kurguluoğlu', 'il': 'Ordu', 'ilce': 'Korgan', 'gorev_yeri': 'Korgan Merkez Camii', 'unvan': 'İmam-Hatip'});
        if (req.url.path == '/gorevli/ilanlarim') {
          return _y({'ilanlar': [{'id': 'i2', 'ad_soyad': 'Örnekalp Yıldırımhan', 'sehit': true, 'rutbe': 'Piyade Uzman Çavuş', 'namaz_tarihi': '2026-10-15', 'durum': 'yayinda'}]});
        }
        if (req.url.path == '/gorevli/ilan') {
          giden = jsonDecode(req.body) as Map<String, dynamic>;
          return _y({'durum': 'yayinda', 'ilan_id': 'i3'});
        }
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: servis)));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect(find.text('Şehidimiz Piyade Uzman Çavuş Örnekalp Yıldırımhan'), findsOneWidget);
    await tester.tap(find.text(M.gorevliIlanPaylas));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('gi_rutbe')), findsNothing);
    expect(find.byKey(const ValueKey('gi_sehit')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('gi_sehit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('gi_rutbe')), findsOneWidget);
    expect(find.byKey(const ValueKey('gi_toren')), findsOneWidget);
    expect(find.byKey(const ValueKey('gi_duyuru')), findsOneWidget);
    await tester.tap(find.text(M.erkek));
    Finder alan(String k) => find.descendant(of: find.byKey(ValueKey(k)), matching: find.byType(TextField));
    await tester.enterText(alan('gi_ad'), 'Örnekalp Yıldırımhan');
    await tester.enterText(alan('gi_rutbe'), 'Piyade Uzman Çavuş');
    await tester.enterText(alan('gi_toren'), 'Selâmet Meydanı');
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliGonder));
    await tester.pumpAndSettle();
    expect(giden!['sehit'], true);
    expect(giden!['rutbe'], 'Piyade Uzman Çavuş');
    expect(giden!['toren_yeri'], 'Selâmet Meydanı');
    expect(giden!.containsKey('il'), isFalse); // il/ilçe sunucuda kilitli
    expect(giden!.containsKey('ilce'), isFalse);
  });

  testWidgets('RED: sunucu "silindi" derse oturum silinir, "hesap silindi" gösterilir, giriş kartına dönülür', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: panelServisi('silindi'))));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliSilindi), findsOneWidget);
    expect(d.depo.gorevliOturum, isNull);
    expect(find.byType(GorevliPanel), findsNothing);
    expect(find.text('ac'), findsOneWidget);
  });

  testWidgets('Kart: "Mahallenin din görevlisi paylaştı" rozeti ve görev yeri; "Yakını paylaştı" görünmez', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final r = Ilan.fromJson({
      'id': 'g1', 'ad_soyad': 'Fatma Örnek', 'ilce': 'Korgan', 'namaz_tarihi': '2026-10-15', 'namaz_yeri_vakti': 'Öğle namazı-Merkez Camii',
      'gorevli': true, 'gorev_yeri': 'Korgan Merkez Camii',
    })!;
    expect(r.gorevli, isTrue);
    expect(Ilan.fromJson(r.toJson())!.gorevYeri, 'Korgan Merkez Camii');
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Mahallenin din görevlisi paylaştı'), findsOneWidget);
    expect(find.text('Yakını paylaştı'), findsNothing);
    expect(find.text('Korgan Merkez Camii'), findsOneWidget);
  });
}

String bugun0() => '2026-10-15';
