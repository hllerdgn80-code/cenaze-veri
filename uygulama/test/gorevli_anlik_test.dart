// URUN §56 (din görevlisi ilanı ANINDA: Worker'dan cihazda birleşir) ve §56/B (yenileme: açılış, sekmeye/uygulamaya dönüş, aşağı çekme).
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/ilanlar.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';
import 'widget_test.dart' show telefon;

http.Response _json(Object o, [int kod = 200]) =>
    http.Response.bytes(utf8.encode(jsonEncode(o)), kod, headers: {'content-type': 'application/json; charset=utf-8'});

Map<String, dynamic> _gk(String id, String ad, {String? ilce = 'Ünye', int? yas, String? vefat, String? namaz, String? duzeltme, Map<String, dynamic> ek = const {}}) {
  final b = bugunTr();
  return {
    'id': id,
    'ad_soyad': ad,
    'il': 'Ordu',
    'ilce': ilce,
    'yas': yas,
    'vefat_tarihi': vefat ?? gunEkle(b, -1),
    'namaz_tarihi': namaz ?? b,
    'namaz_yeri_vakti': 'İkindi Namazını Müteakip-TEPE CAMİİ',
    'gorev_yeri': 'Tepe Camii',
    'dogrulandi': true,
    if (duzeltme != null) 'duzeltme_id': duzeltme,
    ...ek,
  };
}

/// Ordu son7gun = ornekOrdu (Ahmet Örnekoğlu, id ornek1, 67 yaş); Worker = [gorevli] ya da [gorevliYanit]
VeriServisi _servis(Future<http.Response> Function() gorevliYanit, {bool oduVarMi = true}) {
  final istemci = MockClient((req) async {
    if (req.url.path.endsWith('/ordu/son7gun.json')) {
      return oduVarMi ? _json(ornekOrdu(bugunTr())) : http.Response('yok', 404);
    }
    if (req.url.path == '/gorevli/ordu.json') return gorevliYanit();
    return http.Response('yok', 404);
  });
  return VeriServisi(istemci: istemci, depo: _depo);
}

late Depo _depo;

Future<List<String>> _adlar(VeriServisi s, {String? ilce}) async {
  final r = await s.ilGetir('Ordu');
  final v = r.veri!;
  return [for (final e in v.ilceler.entries) if (ilce == null || e.key == ilce) ...e.value.map((i) => i.id)];
}

void main() {
  setUp(() async => _depo = (await testDurumu()).depo);

  test('A: Worker\'daki görevli ilanı son7gun\'da yoksa o ilçenin listesine eklenir (gorevli:true, ilçe kaydın ilçesi)', () async {
    final s = _servis(() async => _json({'il': 'Ordu', 'kayitlar': [_gk('g1', 'Veli Tepeli', yas: 80)]}));
    final r = await s.ilGetir('Ordu');
    expect(r.durum, VeriDurumu.tamam);
    final l = r.veri!.ilceler['Ünye']!;
    expect(l.map((i) => i.id), containsAll(['ornek1', 'gorevli-g1']));
    final g = l.firstWhere((i) => i.id == 'gorevli-g1');
    expect(g.gorevli, isTrue);
    expect(g.gorevYeri, 'Tepe Camii');
    expect(g.ilce, 'Ünye');
  });

  test('A: aynı id ya da aynı kişi (ad + gün ±2 + yaş ±1) zaten listedeyse çift kart olmaz; yaş farkı >1 ise ayrı kişidir', () async {
    final b = bugunTr();
    final s = _servis(() async => _json({'kayitlar': [
          _gk('ornek1', 'Başka Ad'), // id 'gorevli-ornek1' ≠ 'ornek1' → kişi kuralı: ad farklı → eklenir (kontrol altta)
          _gk('x2', 'AHMET ÖRNEKOĞLU', yas: 68, namaz: gunEkle(b, 1)), // aynı kişi: yaş +1, gün +1
          _gk('x3', 'Ahmet Örnekoğlu', yas: 40), // yaş farkı büyük → başka kişi
        ]}));
    final ids = await _adlar(s);
    expect(ids, contains('gorevli-x3'));
    expect(ids, isNot(contains('gorevli-x2')));
    expect(ids, contains('gorevli-ornek1'));
    expect(ids.where((x) => x == 'ornek1'), hasLength(1));

    // aynı id (veri hattı birleştirmiş): son7gun'da zaten 'gorevli-g9' var
    final h = ornekOrdu(b);
    ((h['ilceler'] as Map)['Ünye'] as List).add({..._gk('g9', 'Hat Birleştirdi'), 'id': 'gorevli-g9', 'gorevli': true});
    final s2 = VeriServisi(
      istemci: MockClient((req) async => req.url.path.endsWith('/ordu/son7gun.json') ? _json(h) : _json({'kayitlar': [_gk('g9', 'Hat Birleştirdi')]})),
      depo: _depo,
    );
    final ids2 = await _adlar(s2);
    expect(ids2.where((x) => x == 'gorevli-g9'), hasLength(1));
  });

  test('A: duzeltme_id → hedef otomatik kayıt kalkar, görevli kaydı yerine konur', () async {
    final s = _servis(() async => _json({'kayitlar': [_gk('d1', 'Ahmet Örnekoğlu Doğru', duzeltme: 'ornek1')]}));
    final ids = await _adlar(s);
    expect(ids, contains('gorevli-d1'));
    expect(ids, isNot(contains('ornek1')));
  });

  test('A: Worker hatası / zaman aşımı / bozuk yanıt → son7gun aynen, sessizce', () async {
    for (final y in <Future<http.Response> Function()>[
      () async => http.Response('hata', 500),
      () async => throw http.ClientException('ağ yok'),
      () async => http.Response('{bozuk', 200),
      () async => _json({'kayitlar': 'liste degil'}),
    ]) {
      final r = await _servis(y).ilGetir('Ordu');
      expect(r.durum, VeriDurumu.tamam);
      expect(r.veri!.ilceler['Ünye']!.map((i) => i.id), ['ornek1']);
    }
  });

  test('A: kaynaksız il (son7gun 404) + görevli kaydı → il kaynaklı sayılır, kayıt görünür; görevli yoksa kaynaksız kalır', () async {
    final r = await _servis(() async => _json({'kayitlar': [_gk('g1', 'Veli Tepeli', ilce: 'Merkez')]}), oduVarMi: false).ilGetir('Ordu');
    expect(r.veri!.kaynakli, isTrue);
    expect(r.veri!.ilceler['Merkez']!.single.id, 'gorevli-g1');
    final bos = await _servis(() async => _json({'kayitlar': []}), oduVarMi: false).ilGetir('Ordu');
    expect(bos.veri!.kaynakli, isFalse);
  });

  test('A: pencere dışı cenaze günü ve beyaz liste dışı alan (telefon) alınmaz', () async {
    final b = bugunTr();
    final s = _servis(() async => _json({'kayitlar': [
          _gk('eski', 'Çok Eski', namaz: gunEkle(b, -9)),
          _gk('ileri', 'Çok İleri', namaz: gunEkle(b, 5)),
          _gk('t1', 'Telefonlu Kişi', ek: {'telefon': '05320000000', 'basvuran': 'Hoca X', 'eposta': 'a@b.c'}),
        ]}));
    final r = await s.ilGetir('Ordu');
    final l = r.veri!.ilceler['Ünye']!;
    expect(l.map((i) => i.id), isNot(contains('gorevli-eski')));
    expect(l.map((i) => i.id), isNot(contains('gorevli-ileri')));
    final t = l.firstWhere((i) => i.id == 'gorevli-t1');
    final js = jsonEncode(t.toJson());
    expect(js.contains('0532'), isFalse);
    expect(js.contains('Hoca X'), isFalse);
    expect(js.contains('a@b.c'), isFalse);
  });

  group('B: yenileme', () {
    Future<int Function()> kur(WidgetTester tester) async {
      telefon(tester);
      var say = 0;
      final d = await testDurumu(
        onceki: {'il': 'Ordu', 'ilce': 'Ünye'},
        istemci: MockClient((req) async {
          if (req.url.path.endsWith('/ordu/son7gun.json')) {
            say++;
            return _json(ornekOrdu(bugunTr()));
          }
          return http.Response('yok', 404);
        }),
      );
      final eski = ilanYenilemeAraligi;
      ilanYenilemeAraligi = Duration.zero;
      addTearDown(() => ilanYenilemeAraligi = eski);
      await tester.pumpWidget(KiminCenazesi(durum: d));
      await tester.pumpAndSettle();
      _durum = d;
      return () => say;
    }

    testWidgets('açılışta bir kez; İlanlar sekmesine dönünce yeniden çekilir', (tester) async {
      final say = await kur(tester);
      expect(say(), 1);
      _durum.sekmeSec(1);
      await tester.pumpAndSettle();
      expect(say(), 1); // başka sekmede çekilmez
      _durum.sekmeSec(0);
      await tester.pumpAndSettle();
      expect(say(), 2);
    });

    testWidgets('uygulamaya dönüşte (resumed) eşik geçtiyse yeniden çekilir; eşik geçmediyse çekilmez', (tester) async {
      final say = await kur(tester);
      ilanYenilemeAraligi = const Duration(minutes: 5);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(say(), 1); // 5 dk dolmadı
      ilanYenilemeAraligi = Duration.zero;
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(say(), 2);
    });

    testWidgets('listeyi aşağı çekince (RefreshIndicator) her zaman yeniden çekilir', (tester) async {
      final say = await kur(tester);
      ilanYenilemeAraligi = const Duration(hours: 1);
      await tester.drag(find.descendant(of: find.byType(RefreshIndicator), matching: find.byType(ListView)), const Offset(0, 400));
      await tester.pumpAndSettle();
      expect(say(), 2);
    });
  });
}

late AppDurum _durum;
