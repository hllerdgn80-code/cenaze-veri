// Bot kapısı jetonu (25.10.2026): istek özeti Worker ile AYNI; jeton yalnız POST'a eklenir; sağlayıcı yok/hata -> başlık yok, istek yine gider.
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/aile.dart';
import 'package:kimin_cenazesi/cekirdek/guvenlik_jeton.dart';
import 'package:kimin_cenazesi/cekirdek/gorevli.dart';

class _Sahte implements JetonSaglayici {
  final String? jeton;
  final bool hata;
  String? gelenOzet;
  _Sahte(this.jeton, {this.hata = false});
  @override
  Future<String?> integrityJetonu(String istekOzeti) async {
    gelenOzet = istekOzeti;
    if (hata) throw StateError('play hizmeti yok');
    return jeton;
  }
}

void main() {
  tearDown(() => kcJetonSaglayici = null);

  test('istekOzeti: Worker integrity.js istekOzeti() çıktısıyla birebir aynı (node ile üretilmiş vektörler)', () {
    expect(istekOzeti('/gorevli/ilan', '{"a":1}'), 'VH1Vq4cTt0OwI41DWX-SwM58dn9M9sKk4dtvCEsQvS4');
    expect(istekOzeti('/aile/bildir', '{"ilan_id":"0123456789abcdef","neden":"yanlış bilgi"}'), 'Ggm5v9Dv7So5GXgfmo8q3n3kALANX2VDfgDRr8ZLPxg');
  });

  test('guvenlikBasliklari: sağlayıcı yok -> boş; jeton -> x-integrity; hata/boş jeton -> boş (asla fırlatmaz)', () async {
    expect(await guvenlikBasliklari('/aile/bildir', '{}'), isEmpty);
    final s = _Sahte('J' * 40);
    expect(await guvenlikBasliklari('/aile/bildir', '{}', saglayici: s), {'x-integrity': 'J' * 40});
    expect(s.gelenOzet, istekOzeti('/aile/bildir', '{}'));
    expect(await guvenlikBasliklari('/aile/bildir', '{}', saglayici: _Sahte(null)), isEmpty);
    expect(await guvenlikBasliklari('/aile/bildir', '{}', saglayici: _Sahte('', hata: false)), isEmpty);
    expect(await guvenlikBasliklari('/aile/bildir', '{}', saglayici: _Sahte('x', hata: true)), isEmpty);
  });

  test('istemciler: POST jetonlu gider (özet gövdeyle uyumlu), GET jetonsuz; sağlayıcı çökerse istek yine gider', () async {
    final gorulen = <http.BaseRequest>[];
    final govdeler = <String>[];
    final ist = MockClient((req) async {
      gorulen.add(req);
      govdeler.add(req.body);
      return http.Response('{}', 200, headers: {'content-type': 'application/json'});
    });
    kcJetonSaglayici = _Sahte('T' * 30);
    await GorevliServisi(istemci: ist, kok: 'https://w.test').epostaKodGonder('ali.kaya');
    await AileServisi(istemci: ist, kok: 'https://w.test').bildir('0123456789abcdef', 'yanlış');
    expect(gorulen[0].headers['x-integrity'], 'T' * 30);
    expect(gorulen[1].headers['x-integrity'], 'T' * 30);
    final s = kcJetonSaglayici as _Sahte;
    expect(s.gelenOzet, istekOzeti('/aile/bildir', govdeler[1]), reason: 'özet, gönderilen gövdeden hesaplanır');
    await GorevliServisi(istemci: ist, kok: 'https://w.test').durum('oturum'); // GET
    expect(gorulen.last.method, 'GET');
    expect(gorulen.last.headers.containsKey('x-integrity'), isFalse);
    kcJetonSaglayici = _Sahte('x', hata: true);
    final r = await AileServisi(istemci: ist, kok: 'https://w.test').bildir('0123456789abcdef', 'yanlış');
    expect(r.kod, 200);
    expect(jsonDecode(govdeler.last)['neden'], 'yanlış');
  });
}
