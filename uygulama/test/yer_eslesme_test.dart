// URUN §49a: görev yeri <-> cami/mahalle eşleşmesi (Python ve JS testleriyle AYNI 12 örnek).
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/yer_eslesme.dart';

void main() {
  const ornek = <List<Object?>>[
    ['Korgan Merkez Camii', 'MERKEZ CAMİİ', null, null, true],
    ['Çitlice Camii', null, 'Çitlice', null, true],
    ['Çitlice Camii', 'Merkez Camii', null, null, false],
    ['Çitlice Camii', 'Merkez Camii', 'Çitlice Mahallesi', null, true],
    ['', 'Merkez Camii', 'Merkez', null, false],
    ['Çitlice Camii', null, null, null, false],
    ['Merkez Camii', 'Korgan Merkez Camii', null, null, true],
    ['Ordu Merkez Camii', 'Korgan Merkez Camii', null, null, false],
    ['Ulu Camii', 'Yeni Camii', null, null, false],
    ['Tepe Köyü', '', 'TEPE KÖYÜ', null, true],
    ['Çitlice Camii', 'Çitlik Camii', null, null, false],
    ['Korgan Çitlice Camii', 'Korgan Merkez Camii', null, 'Korgan', false],
  ];
  test('yerEslesir 12 örnek', () {
    for (final o in ornek) {
      expect(yerEslesir(o[0] as String?, o[1] as String?, o[2] as String?, haric: o[3] as String?), o[4], reason: '$o');
    }
    expect(yerEslesir('Korgan Çitlice Camii', 'Korgan Merkez Camii', null), isTrue);
    expect(yerSade('ÇİTLİCE MAHALLESİ'), 'citlice');
    expect(yerSade('Mah. Ortaköy Camisi'), 'ortakoy');
    expect(namazCami('ÖĞLE NAMAZINDAN SONRA - MERKEZ CAMİİ'), 'MERKEZ CAMİİ');
    expect(namazCami('Öğle'), '');
  });
}
