// YAYIN İMZASI testleri (25.10.2026): Ed25519 (RFC 8032 + Python ile üretilmiş vektörler), biçim kuralı, VeriServisi/UzakAyar/Sürüm entegrasyonu, acil gizleme.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/ed25519.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/imza.dart';
import 'package:kimin_cenazesi/cekirdek/surum.dart';
import 'package:kimin_cenazesi/cekirdek/uzak_ayar.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';

import 'ortak.dart';

List<int> hex(String s) => [for (var i = 0; i < s.length; i += 2) int.parse(s.substring(i, i + 2), radix: 16)];
Uint8List b(String s) => Uint8List.fromList(utf8.encode(s));

void main() {
  final vek = jsonDecode(File('test/imza_vektorleri.json').readAsStringSync()) as Map<String, dynamic>;
  final vakalar = (vek['vakalar'] as List).cast<Map<String, dynamic>>();
  Map<String, dynamic> vaka(String ad) => vakalar.firstWhere((v) => (v['ad'] as String).startsWith(ad));
  ImzaDogrulayici dogrulayici({List<String>? anahtar}) => ImzaDogrulayici(
        b64Anahtarlar: anahtar ?? [vek['acik_anahtar_b64'] as String],
        azamiYas: Duration(seconds: vek['azami_yas'] as int),
        simdi: () => DateTime.fromMillisecondsSinceEpoch((vek['simdi'] as int) * 1000),
      );

  test('Ed25519: RFC 8032 test 1 ve 2 doğrulanır; mesaj/imza/anahtar bozulunca reddedilir', () {
    const t1 = [
      'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a',
      '',
      'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'
    ];
    const t2 = [
      '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
      '72',
      '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00'
    ];
    for (final t in [t1, t2]) {
      expect(ed25519Dogrula(hex(t[0]), hex(t[1]), hex(t[2])), isTrue);
      expect(ed25519Dogrula(hex(t[0]), [...hex(t[1]), 1], hex(t[2])), isFalse);
      final bozuk = hex(t[2])..[5] ^= 1;
      expect(ed25519Dogrula(hex(t[0]), hex(t[1]), bozuk), isFalse);
      expect(ed25519Dogrula(hex(t[0]).sublist(1), hex(t[1]), hex(t[2])), isFalse);
      expect(ed25519Dogrula(hex(t[0]), hex(t[1]), hex(t[2]).sublist(1)), isFalse);
    }
    final s = hex(t1[2]);
    for (var i = 32; i < 64; i++) {
      s[i] = 0xff; // s >= q
    }
    expect(ed25519Dogrula(hex(t1[0]), hex(t1[1]), s), isFalse);
  });

  test('ortak vektörler (Python üretimi): her vaka beklenen sonucu verir', () {
    final d = dogrulayici();
    expect(vakalar.length, greaterThanOrEqualTo(14));
    for (final v in vakalar) {
      final yan = v['yan'] as String?;
      final s = d.denetle(v['yol'] as String, b(v['dosya'] as String), yan: yan == null ? null : b(jsonEncode(yan))); // yan dosya içeriği = JSON metni "ts.imza"
      expect(s.name, v['beklenen'], reason: v['ad'] as String);
    }
  });

  test('kabul(): anahtar listesi boşsa doğrulama KAPALI (her şey geçer); doluysa yalnız geçerli imza', () {
    final kapali = ImzaDogrulayici();
    expect(kapali.etkin, isFalse);
    expect(kapali.kabul('x.json', b('{"a":1}')), isTrue);
    final acik = dogrulayici();
    expect(acik.etkin, isTrue);
    expect(acik.kabul('x.json', b('{"a":1}')), isFalse);
    final g = vaka('geçerli (kompakt');
    expect(acik.kabul(g['yol'] as String, b(g['dosya'] as String)), isTrue);
    // yanlış anahtar
    final baska = dogrulayici(anahtar: [base64.encode(List<int>.filled(32, 7))]);
    expect(baska.kabul(g['yol'] as String, b(g['dosya'] as String)), isFalse);
    // iki anahtardan biri doğruysa kabul (anahtar değiştirme dönemi)
    final cift = dogrulayici(anahtar: [base64.encode(List<int>.filled(32, 7)), vek['acik_anahtar_b64'] as String]);
    expect(cift.kabul(g['yol'] as String, b(g['dosya'] as String)), isTrue);
    // bayat imza: yaş kontrolü kapalıysa geçerli
    final eski = vaka('imza 15 günlük');
    expect(acik.kabul(eski['yol'] as String, b(eski['dosya'] as String)), isFalse);
    expect(acik.kabul(eski['yol'] as String, b(eski['dosya'] as String), yasKontrol: false), isTrue);
  });

  group('VeriServisi', () {
    final il = vaka('geçerli (kompakt');
    final dizi = vaka('dizi dosyası + yan imza geçerli');
    final diziBozuk = vaka('dizi dosyası değiştirildi');

    http.Client sahte(Map<String, String> yollar) => MockClient((req) async {
          final y = req.url.path;
          return yollar.containsKey(y) ? http.Response.bytes(utf8.encode(yollar[y]!), 200) : http.Response('', 404);
        });

    test('imzalı il verisi gösterilir; imzasız/bozuk/başka yola taşınmış veri GÖSTERİLMEZ (dogrulanamadi)', () async {
      final depo = (await testDurumu()).depo;
      VeriServisi s(String govde, {ImzaDogrulayici? d}) =>
          VeriServisi(istemci: sahte({'/veri/ordu/son7gun.json': govde}), depo: depo, imza: d ?? dogrulayici());
      var r = await s(il['dosya'] as String).ilGetir('Ordu');
      expect(r.durum, VeriDurumu.tamam);
      expect(r.veri!.ilceler['Fatsa']!.single.adSoyad, 'Mehmet Yıldız');
      for (final ad in ['imzasız', 'gövde değiştirildi', 'ilan eklendi']) {
        final v = vaka(ad);
        r = await s(v['dosya'] as String).ilGetir('Ordu');
        expect(r.durum, VeriDurumu.dogrulanamadi, reason: ad);
        expect(r.veri, isNull);
      }
      // başka ilin dosyası bu yola konmuş (Rize imzalı, Ordu yoluna kopya)
      r = await s(il['dosya'] as String, d: dogrulayici()).ilGetir('Rize'); // Rize isteği /veri/rize/... -> 404
      expect(r.veri == null || r.durum != VeriDurumu.tamam || r.veri!.kaynakli == false, isTrue);
      // doğrulama kapalıyken imzasız veri gösterilir (geçiş dönemi)
      r = await s(vaka('imzasız')['dosya'] as String, d: ImzaDogrulayici()).ilGetir('Ordu');
      expect(r.durum, VeriDurumu.tamam);
    });

    test('doğrulanamayan veri önbelleğe YAZILMAZ; eski imzasız önbellek kopyası etkin doğrulamada KULLANILMAZ', () async {
      final d = await testDurumu();
      final kotu = VeriServisi(istemci: sahte({'/veri/ordu/son7gun.json': vaka('imzasız')['dosya'] as String}), depo: d.depo, imza: dogrulayici());
      await kotu.ilGetir('Ordu');
      expect(d.depo.onbellek('ordu'), isNull);
      await d.depo.onbellekYaz('ordu', vaka('imzasız')['dosya'] as String); // eski sürümden kalan imzasız kopya
      final cevrimdisi = VeriServisi(istemci: MockClient((_) async => throw const SocketLikeError()), depo: d.depo, imza: dogrulayici());
      final r = await cevrimdisi.ilGetir('Ordu');
      expect(r.veri, isNull);
      // imzalı kopya (yaşı önemsiz) çevrimdışı gösterilir
      await d.depo.onbellekYaz('ordu', il['dosya'] as String);
      final r2 = await cevrimdisi.ilGetir('Ordu');
      expect(r2.durum, VeriDurumu.onbellek);
      expect(r2.veri!.ilceler['Fatsa'], isNotEmpty);
    });

    test('dizi dosyası (kaybettiklerimiz): yan imza şart; bozuk dizi reddedilir', () async {
      final depo = (await testDurumu()).depo;
      final yan = dizi['yan'] as String;
      final kok = 'https://veri.kimincenazesi.com';
      final ok = VeriServisi(
          istemci: sahte({'/kaybettiklerimiz/bakanlar.json': dizi['dosya'] as String, '/kaybettiklerimiz/bakanlar-imza.json': jsonEncode(yan)}),
          depo: depo, kok: kok, imza: dogrulayici());
      var r = await ok.kaybettiklerimiz('bakanlar');
      expect(r.durum, VeriDurumu.tamam);
      expect(r.liste, isNotNull);
      final bozuk = VeriServisi(
          istemci: sahte({'/kaybettiklerimiz/bakanlar.json': diziBozuk['dosya'] as String, '/kaybettiklerimiz/bakanlar-imza.json': jsonEncode(yan)}),
          depo: depo, kok: kok, imza: dogrulayici());
      r = await bozuk.kaybettiklerimiz('bakanlar');
      expect(r.durum, VeriDurumu.dogrulanamadi);
      final yansiz = VeriServisi(istemci: sahte({'/kaybettiklerimiz/bakanlar.json': dizi['dosya'] as String}), depo: depo, kok: kok, imza: dogrulayici());
      expect((await yansiz.kaybettiklerimiz('bakanlar')).durum, VeriDurumu.dogrulanamadi);
    });
  });

  group('UzakAyar / Sürüm', () {
    setUp(UzakAyar.sifirla);

    test('imzasız ayar dosyası UYGULANMAZ; imzalı uygulanır', () async {
      TestWidgetsFlutterBinding.ensureInitialized();
      final imzali = vaka('geçerli (girintili');
      // girintili vakadaki ayarlar.json: {"yazilar": {"hataVeri": "Yükleme hatası: Muğla, Şırnak"}, "bayraklar": {"a": true}}
      http.Client ist(String g) => MockClient((_) async => http.Response.bytes(utf8.encode(g), 200));
      expect(await UzakAyar.tazele(ist(vaka('imzasız')['dosya'] as String), imza: dogrulayici()), isFalse);
      expect(UzakAyar.yazi('hataVeri', 'varsayılan'), 'varsayılan');
      UzakAyar.sifirla(); // dakikada bir sınırı sıfırla
      expect(await UzakAyar.tazele(ist(imzali['dosya'] as String), imza: dogrulayici()), isTrue);
      expect(UzakAyar.yazi('hataVeri', 'varsayılan'), 'Yükleme hatası: Muğla, Şırnak');
    });

    test('sürüm bilgisi: imzasız -> null (sahte zorunlu güncelleme kapısı kurulamaz)', () async {
      final surum = vaka('geçerli (gövdede imza işareti metni geçiyor)'); // yol "surum.json"
      MockClient ist(String g) => MockClient((_) async => http.Response.bytes(utf8.encode(g), 200));
      expect(await varsayilanSurumCekici(ist(vaka('imzasız')['dosya'] as String), imza: dogrulayici())(), isNull);
      // geçerli imzalı gövde SurumBilgi.coz'a ulaşır (gövdede min_build yok -> varsayılan değerler)
      expect(await varsayilanSurumCekici(ist(surum['dosya'] as String), imza: dogrulayici())(), isNotNull);
      // doğrulama kapalıyken (anahtar yok) imzasız gövde de çözülür
      expect(await varsayilanSurumCekici(ist(vaka('imzasız')['dosya'] as String), imza: ImzaDogrulayici())(), isNotNull);
    });
  });

  group('Acil düğme', () {
    test('acil_gizle: ayardaki id / ilçe / il kayıtları ilan listesinden anında düşer', () async {
      TestWidgetsFlutterBinding.ensureInitialized();
      final bugun = '2026-10-25';
      final depo = (await testDurumu()).depo;
      final ham = ornekOrdu(bugun);
      MockClient ist() => MockClient((req) async => req.url.path.endsWith('son7gun.json') ? http.Response.bytes(utf8.encode(jsonEncode(ham)), 200) : http.Response('', 404));
      final s = VeriServisi(istemci: ist(), depo: depo, imza: ImzaDogrulayici());
      UzakAyar.uygula(const {});
      var r = await s.ilGetir('Ordu');
      expect(r.veri!.ilceler['Ünye'], hasLength(1));
      UzakAyar.uygula({'acil_gizle': {'id': ['ornek1']}});
      r = await s.ilGetir('Ordu');
      expect(r.veri!.ilceler.values.expand((x) => x), isEmpty);
      UzakAyar.uygula({'acil_gizle': {'ilce': ['ordu/unye']}});
      r = await s.ilGetir('Ordu');
      expect(r.veri!.ilceler.values.expand((x) => x), isEmpty);
      UzakAyar.uygula({'acil_gizle': {'ilce': ['ordu/fatsa']}});
      r = await s.ilGetir('Ordu');
      expect(r.veri!.ilceler['Ünye'], hasLength(1), reason: 'başka ilçe etkilenmez');
      UzakAyar.uygula({'acil_gizle': {'il': ['Ordu']}});
      r = await s.ilGetir('Ordu');
      expect(r.veri!.ilceler, isEmpty);
      expect(r.veri!.genel, isEmpty);
      UzakAyar.uygula({'acil_gizle': {'il': ['Rize']}});
      expect((await s.ilGetir('Ordu')).veri!.ilceler['Ünye'], hasLength(1), reason: 'başka il etkilenmez');
      UzakAyar.sifirla();
      expect(UzakAyar.acilGizle, isEmpty);
      // acilSuz doğrudan: değişiklik yoksa aynı nesne
      final v = IlVerisi.fromJson('Ordu', Map<String, dynamic>.from(ham));
      expect(identical(acilSuz(v, const {}), v), isTrue);
      expect(identical(acilSuz(v, {'id': {'yok'}}), v), isTrue);
    });
  });
}

class SocketLikeError implements Exception {
  const SocketLikeError();
}
