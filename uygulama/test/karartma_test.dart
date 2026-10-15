// TC otomatik karartma (saf Dart): sahte görüntü üzerinde 11 haneli dizi, aralıklı yazılmış dizi ve etiket yanındaki sayı SİYAH olur;
// diğer yerler (10 haneli sayı, ad) bozulmaz; 1600 px sınırı; tanıma başarısız olursa hata (fotoğraf gönderilmez).
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:kimin_cenazesi/cekirdek/karartma.dart';

Uint8List _beyaz(int w, int h) {
  final g = img.Image(width: w, height: h);
  img.fill(g, color: img.ColorRgb8(255, 255, 255));
  return Uint8List.fromList(img.encodeJpg(g, quality: 95));
}

MetinOgesi _o(String m, int s, int u, int sg, int a) => MetinOgesi(m, Kutu(s, u, sg, a));
bool _siyah(img.Image g, int x, int y) => g.getPixel(x, y).luminance < 40;
bool _beyazMi(img.Image g, int x, int y) => g.getPixel(x, y).luminance > 215;

void main() {
  test('11 haneli tek dizi, aralıklı dizi ve "Kimlik No" etiketinin yanındaki sayı bulunur; 10 haneli sayı ve ad bulunmaz', () {
    final satirlar = [
      MetinSatiri([_o('MEHMET', 10, 10, 60, 30), _o('YILMAZ', 70, 10, 120, 30)]),
      MetinSatiri([_o('12345678901', 20, 50, 140, 70)]), // tek dizi (TC)
      MetinSatiri([_o('123', 20, 90, 50, 110), _o('456', 56, 90, 86, 110), _o('789', 92, 90, 122, 110), _o('01', 128, 90, 148, 110)]), // aralıklı
      MetinSatiri([_o('1234567890', 20, 130, 140, 150)]), // 10 hane: TC değil
      MetinSatiri([_o('T.C.', 10, 170, 40, 190), _o('Kimlik', 46, 170, 90, 190), _o('No', 96, 170, 116, 190), _o('9876543', 124, 170, 190, 190)]), // etiket + kısa sayı
    ];
    final k = tcBolgeleri(satirlar);
    expect(k.length, 3);
    expect(k.any((x) => x.sol == 20 && x.ust == 50), isTrue);
    expect(k.any((x) => x.sol == 20 && x.ust == 90 && x.sag == 148), isTrue); // dört öğe tek kutu
    expect(k.any((x) => x.sol == 124 && x.ust == 170), isTrue);
    expect(k.any((x) => x.ust == 130 || x.ust == 10), isFalse);
  });

  test('karartVeKucult: bulunan bölgeler piksel düzeyinde siyah, dışı beyaz kalır', () {
    final jpeg = _beyaz(240, 220);
    final sonuc = karartVeKucult(jpeg, [const Kutu(20, 50, 140, 70)]);
    final g = img.decodeJpg(sonuc)!;
    expect(g.width, 240); // küçük görüntü büyütülmez
    expect(_siyah(g, 80, 60), isTrue);
    expect(_siyah(g, 22, 52), isTrue);
    expect(_beyazMi(g, 80, 130), isTrue);
    expect(_beyazMi(g, 200, 20), isTrue);
  });

  test('1600 px sınırı: 3200x1600 görüntü 1600x800 olur ve karartma küçültmeden önce uygulanır', () {
    final jpeg = _beyaz(3200, 1600);
    final sonuc = karartVeKucult(jpeg, [const Kutu(1000, 600, 1400, 700)]);
    final g = img.decodeJpg(sonuc)!;
    expect(g.width, 1600);
    expect(g.height, 800);
    expect(_siyah(g, 600, 325), isTrue); // (1000..1400, 600..700) / 2
    expect(_beyazMi(g, 100, 100), isTrue);
  });

  test('kartiHazirla: sahte tanıma 11 haneli diziyi bildirir -> çıktıda o bölge siyah; tanıma hata verirse istisna (gönderilmez)', () async {
    final jpeg = _beyaz(400, 300);
    final sonuc = await kartiHazirla('x.jpg', jpeg, (_) async => [
          MetinSatiri([_o('12345678901', 100, 100, 260, 130)]),
        ]);
    final g = img.decodeJpg(sonuc)!;
    expect(_siyah(g, 180, 115), isTrue);
    expect(_beyazMi(g, 20, 20), isTrue);
    expect(() => kartiHazirla('x.jpg', jpeg, (_) async => throw StateError('ml kit yok')), throwsA(isA<StateError>()));
    expect(() => karartVeKucult(Uint8List.fromList([1, 2, 3]), const []), throwsA(anything)); // bozuk JPEG
  });
}
