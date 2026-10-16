// Veri kapısı (v0.1.3): her istek anahtar + KiminCenazesi/ User-Agent taşır; veri adresi Cloudflare kapısı.
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/aile.dart';
import 'package:kimin_cenazesi/cekirdek/anahtar.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';

import 'ortak.dart';

void main() {
  test('veri adresi Cloudflare veri kapısı, github.io değil', () {
    expect(veriKok, 'https://veri.kimincenazesi.com/veri');
    expect(veriKok.contains('github.io'), isFalse);
  });

  test('kcBasliklar: anahtar dolu, User-Agent KiminCenazesi/ ile başlar', () {
    final b = kcBasliklar();
    expect(b['X-KC-Anahtar'], kcAnahtar);
    expect(kcAnahtar.length, greaterThanOrEqualTo(32));
    expect(b['User-Agent'], startsWith('KiminCenazesi/'));
    expect(b['User-Agent'], 'KiminCenazesi/$kcSurum');
  });

  test('VeriServisi tüm veri isteklerine kapı başlıklarını ekler', () async {
    final gorulen = <http.BaseRequest>[];
    final depo = (await testDurumu()).depo;
    final s = VeriServisi(
      istemci: MockClient((req) async {
        gorulen.add(req);
        return http.Response('yok', 404);
      }),
      depo: depo,
    );
    await s.ilGetir('Ordu');
    await s.kaybettiklerimiz('bakanlar');
    expect(gorulen, isNotEmpty);
    for (final r in gorulen) {
      expect(r.url.host, anyOf('veri.kimincenazesi.com', Uri.parse(aileKok).host)); // il verisi + görevli ilanı (§56)
      expect(r.headers['X-KC-Anahtar'], kcAnahtar);
      expect(r.headers['User-Agent'], startsWith('KiminCenazesi/'));
    }
  });

  test('AileServisi istekleri de kapı başlıklarını taşır', () async {
    http.BaseRequest? g;
    final s = AileServisi(
      istemci: MockClient((req) async {
        g = req;
        return http.Response('{}', 200, headers: {'content-type': 'application/json'});
      }),
      kok: 'https://aile.test',
    );
    await s.basvur({'a': 1});
    expect(g!.headers['X-KC-Anahtar'], kcAnahtar);
    expect(g!.headers['User-Agent'], startsWith('KiminCenazesi/'));
  });
}
