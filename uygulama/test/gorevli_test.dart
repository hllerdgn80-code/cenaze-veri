// Din görevlisi (0.1.9, URUN-TASLAGI §45): Diyanet e-posta kodu (kılavuz -> kod -> panel), ⋮ menüsü (görev yerim değişti / çıkış), panel (sabit başlık kartı,
// kontrolde iken pasif "İlan paylaş", onayda etkin, redde "hesap silindi"), il/ilçe kilidi, kartta rozet.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/ortak.dart' show AnaDugme, IkincilDugme;
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/gorevli.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/tema.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_kayit.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_panel.dart';
import 'package:kimin_cenazesi/ekranlar/gorevli_yer.dart';

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

Future<void> _yaz(WidgetTester t, String anahtar, String metin) async {
  final f = _alan(anahtar);
  await t.scrollUntilVisible(f, 200, scrollable: find.byType(Scrollable).first);
  await t.enterText(f, metin);
  await t.pumpAndSettle();
}

void main() {
  GorevliServisi epostaServisi(Map<String, Map<String, dynamic>> istekler, {int dogrulaKod = 200, int kodKod = 200, Map<String, dynamic>? kodGovde}) => GorevliServisi(
        kok: 'https://g.test',
        istemci: MockClient((req) async {
          final govde = req.body.isEmpty ? <String, dynamic>{} : jsonDecode(req.body) as Map<String, dynamic>;
          istekler['${req.url.path}#${istekler.length}'] = govde;
          if (req.url.path == '/gorevli/eposta-kod') return _y(kodGovde ?? {'durum': 'kod_gonderildi', 'adres': '${govde['kullanici']}@diyanet.gov.tr'}, kodKod);
          if (req.url.path == '/gorevli/eposta-dogrula') {
            if (dogrulaKod == 200) return _y({'durum': 'onayli', 'oturum': 'tok123', 'profil_tamam': false});
            return _y({'hata': 'kod_yanlis', 'kalan_deneme': 4}, dogrulaKod);
          }
          if (req.url.path == '/gorevli/durum') return _y({'durum': 'onayli', 'profil_tamam': false});
          if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
          return http.Response('yok', 404);
        }),
      );

  testWidgets('Kılavuz ekranı: yalnız kullanıcı adı + sabit @diyanet.gov.tr; "nasıl giriş" penceresi 6 madde; kart/telefon alanı YOK', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: GorevliKayit(il: 'Kars', ilce: 'Merkez', servis: epostaServisi(istekler)))));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliEpostaBaslik), findsOneWidget);
    expect(find.text(M.gorevliEpostaAciklama), findsOneWidget);
    expect(find.text(M.gorevliAlanAdi), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget); // yalnız kullanıcı adı
    expect(find.textContaining('Cep telefonu'), findsNothing);
    expect(find.textContaining('kart'), findsNothing);
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, M.gorevliKodGonderDugme)).onTap, isNull);
    await tester.tap(find.text(M.gorevliNasilGiris));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('g_nasil_pencere')), findsOneWidget);
    expect(M.gorevliNasil6.length, 6);
    for (int i = 0; i < 6; i++) {
      expect(find.text('${i + 1}. ${M.gorevliNasil6[i]}'), findsOneWidget);
    }
    expect(find.textContaining('posta.diyanet.gov.tr'), findsWidgets);
  });

  testWidgets('Kod akışı: kullanıcı adı -> kod ekranı (adres, 5 madde, 10 dk, "(5 dk)" bekleme) -> yanlış kod uyarısı -> doğru kod -> panel HEMEN açılır', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final istekler = <String, Map<String, dynamic>>{};
    var yanlis = true;
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        final govde = req.body.isEmpty ? <String, dynamic>{} : jsonDecode(req.body) as Map<String, dynamic>;
        istekler['${req.url.path}#${istekler.length}'] = govde;
        if (req.url.path == '/gorevli/eposta-kod') return _y({'durum': 'kod_gonderildi', 'adres': 'x'});
        if (req.url.path == '/gorevli/eposta-dogrula') {
          if (yanlis) {
            yanlis = false;
            return _y({'hata': 'kod_yanlis', 'kalan_deneme': 4}, 400);
          }
          return _y({'durum': 'onayli', 'oturum': 'tok123', 'profil_tamam': false});
        }
        if (req.url.path == '/gorevli/durum') return _y({'durum': 'onayli', 'profil_tamam': false});
        if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: GorevliKayit(il: 'Kars', servis: servis))));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Mehmet.Yilmaz@diyanet.gov.tr'); // alan adı yazılsa da kullanıcı adına inilir
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliKodGonderDugme));
    await tester.pumpAndSettle();
    expect(istekler.values.first['kullanici'], 'mehmet.yilmaz');
    expect(find.text('Kod gönderildi: mehmet.yilmaz@diyanet.gov.tr'), findsOneWidget);
    for (int i = 0; i < 5; i++) {
      expect(find.byKey(ValueKey('g_tarif_$i')), findsOneWidget);
    }
    expect(find.byKey(const ValueKey('g_tarif_5')), findsNothing);
    expect(find.text('1. Adresiniz: mehmet.yilmaz@diyanet.gov.tr'), findsOneWidget);
    expect(find.text(M.gorevliKodGecerli), findsOneWidget);
    expect(find.text('Kodu yeniden gönder (5 dk)'), findsOneWidget); // 5 DAKİKA
    expect(tester.widget<IkincilDugme>(find.widgetWithText(IkincilDugme, 'Kodu yeniden gönder (5 dk)')).onTap, isNull);
    await tester.pump(const Duration(seconds: 61));
    expect(find.text('Kodu yeniden gönder (3:59)'), findsOneWidget); // dakika:saniye geri sayım
    // yanlış kod
    await _yaz(tester, 'g_kod', '000000');
    await tester.tap(find.text(M.gorevliKodDogrulaDugme));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliKodYanlis), findsOneWidget);
    expect(d.depo.gorevliOturum, isNull);
    // doğru kod -> oturum + panel HEMEN (bekleme/kontrol yok)
    await _yaz(tester, 'g_kod', '123456');
    await tester.tap(find.text(M.gorevliKodDogrulaDugme));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliOturum, 'tok123');
    expect(find.byType(GorevliPanel), findsOneWidget);
    expect(find.text(M.gorevliProfilYok), findsOneWidget); // ad/yer ilk "İlan paylaş"ta sorulur
    await tester.pumpWidget(const SizedBox());
  });

  test('Bekleme süresi 5 dk; kodBekle biçimi', () {
    expect(kodBeklemeSn, 300);
    expect(M.kodBekle(300), 'Kodu yeniden gönder (5 dk)');
    expect(M.kodBekle(65), 'Kodu yeniden gönder (1:05)');
    expect(M.kodBekle(9), 'Kodu yeniden gönder (0:09)');
  });

  testWidgets('429 cok_sik_tekrar: kod ekranına geçilir ve kalan süreyle geri sayılır', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final servis = epostaServisi({}, kodKod: 429, kodGovde: {'hata': 'cok_sik_tekrar', 'bekle_sn': 120});
    await tester.pumpWidget(Kapsam(durum: d, child: MaterialApp(theme: temaYap(true), home: GorevliKayit(il: 'Kars', servis: servis))));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'ali.kaya');
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliKodGonderDugme));
    await tester.pumpAndSettle();
    expect(find.text('Kodu yeniden gönder (2:00)'), findsOneWidget);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('Profil yok: ilk "İlan paylaş" ad/görev yeri formunu açar, kaydedince ilan formuna geçer', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    var tamam = false;
    Map<String, dynamic>? profilGovde;
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        if (req.url.path == '/gorevli/durum') {
          return tamam
              ? _y({'durum': 'onayli', 'profil_tamam': true, 'ad_soyad': 'Hasan Kurguluoğlu', 'il': 'Ordu', 'ilce': 'Korgan', 'gorev_yeri': 'Korgan Merkez Camii', 'unvan': 'İmam-Hatip'})
              : _y({'durum': 'onayli', 'profil_tamam': false});
        }
        if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
        if (req.url.path == '/gorevli/profil') {
          profilGovde = jsonDecode(req.body) as Map<String, dynamic>;
          tamam = true;
          return _y({'durum': 'onayli', 'profil_tamam': true});
        }
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: servis)));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliProfilYok), findsOneWidget);
    await tester.tap(find.text(M.gorevliIlanPaylas));
    await tester.pumpAndSettle();
    expect(find.byType(GorevliYerFormu), findsOneWidget);
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, M.gorevliKaydetDugme)).onTap, isNull);
    await tester.enterText(_alan('gy_ad'), 'Hasan Kurguluoğlu');
    await tester.enterText(_alan('gy_yer'), 'Korgan Merkez Camii');
    await tester.tap(find.text(M.alanIlce));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Ünye').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliKaydetDugme));
    await tester.pumpAndSettle();
    expect(profilGovde!['ad_soyad'], 'Hasan Kurguluoğlu');
    expect(profilGovde!['gorev_yeri'], 'Korgan Merkez Camii');
    expect(profilGovde!['ilce'], 'Ünye');
    expect(find.byType(GorevliIlanFormu), findsOneWidget);
  });

  testWidgets('⋮ menüsü: "Görev yerim değişti" ayrı sayfa açar; Kaydet -> geri dönülür ve başlık kartı yeni görev yerini gösterir', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    var yer = 'Korgan Merkez Camii', il = 'Ordu', ilce = 'Korgan';
    Map<String, dynamic>? giden;
    final servis = GorevliServisi(
      kok: 'https://g.test',
      istemci: MockClient((req) async {
        if (req.url.path == '/gorevli/durum') {
          return _y({'durum': 'onayli', 'profil_tamam': true, 'ad_soyad': 'Hasan Kurguluoğlu', 'il': il, 'ilce': ilce, 'gorev_yeri': yer, 'unvan': 'İmam-Hatip'});
        }
        if (req.url.path == '/gorevli/ilanlarim') return _y({'ilanlar': <dynamic>[]});
        if (req.url.path == '/gorevli/gorev-yeri') {
          giden = jsonDecode(req.body) as Map<String, dynamic>;
          yer = giden!['gorev_yeri'] as String;
          il = giden!['il'] as String;
          ilce = giden!['ilce'] as String;
          return _y({'durum': 'onayli', 'profil_tamam': true});
        }
        return http.Response('yok', 404);
      }),
    );
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: servis)));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    expect((tester.widget(find.byKey(const ValueKey('g_kart_1'))) as Text).data, 'Korgan Merkez Camii İmam Hatibi');
    expect(find.text(M.gorevliYerDegisti), findsNothing); // panelin içinde düğme YOK; yalnız ⋮ menüsünde
    await tester.tap(find.byKey(const ValueKey('g_menu')));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliCikisYap), findsOneWidget);
    await tester.tap(find.text(M.gorevliYerDegisti));
    await tester.pumpAndSettle();
    expect(find.byType(GorevliYerFormu), findsOneWidget);
    expect(find.text(M.gorevliYerDegisti), findsWidgets); // sayfa başlığı
    expect(find.byKey(const ValueKey('gy_ad')), findsNothing); // ad değişmez
    await tester.enterText(_alan('gy_yer'), 'Kavak Camii');
    await tester.tap(find.text('Ordu'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Kars').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.alanIlce));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Sarıkamış').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliYerKaydet));
    await tester.pumpAndSettle();
    expect(giden!['gorev_yeri'], 'Kavak Camii');
    expect(giden!['il'], 'Kars');
    expect(giden!['ilce'], 'Sarıkamış');
    expect(giden!.containsKey('ad_soyad'), isFalse);
    expect(find.byType(GorevliYerFormu), findsNothing); // geri dönüldü
    expect((tester.widget(find.byKey(const ValueKey('g_kart_1'))) as Text).data, 'Kavak Camii İmam Hatibi');
    expect((tester.widget(find.byKey(const ValueKey('g_kart_3'))) as Text).data, 'Kars · Sarıkamış');
  });

  testWidgets('⋮ menüsü: "Çıkış yap" oturumu siler ve paneli kapatır', (tester) async {
    telefon(tester);
    final d = await panelDurumu();
    await tester.pumpWidget(_ev(d, (_) => GorevliPanel(servis: panelServisi('onayli'))));
    await tester.tap(find.text('ac'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('g_menu')));
    await tester.pumpAndSettle();
    await tester.tap(find.text(M.gorevliCikisYap));
    await tester.pumpAndSettle();
    expect(d.depo.gorevliOturum, isNull);
    expect(find.byType(GorevliPanel), findsNothing);
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

  testWidgets('Kart: din görevlisi ilanında kaynak rozeti ve görev yeri GÖRÜNMEZ (sahibi 16.10)', (tester) async {
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
    expect(find.text('Mahallenin din görevlisi paylaştı'), findsNothing);
    expect(find.text('Yakını paylaştı'), findsNothing);
    expect(find.text('Korgan Merkez Camii'), findsNothing);
    expect(find.text('Fatma Örnek'), findsOneWidget);
  });
}

String bugun0() => '2026-10-15';
