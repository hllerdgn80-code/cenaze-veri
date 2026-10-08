// Birim testleri: tarih şeridi günü = kart etiketi, sayaç +1/−1, cinsiyet çözümleme, kapı (kaynak alanı yok/var),
// Türkçe yardımcılar.
import 'package:flutter_test/flutter_test.dart';
import 'package:kimin_cenazesi/cekirdek/cinsiyet.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'ortak.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Tarih şeridi günü = kart etiketi', () {
    test('namaz günü varsa etiket ve gruplama namaz gününü kullanır', () {
      final r = Ilan.fromJson({
        'id': 'a',
        'ad_soyad': 'Ahmet Örnek',
        'vefat_tarihi': '2026-10-06',
        'namaz_tarihi': '2026-10-08',
        'namaz_yeri_vakti': 'Öğle Namazını Müteakip-ORTA CAMİİ',
        'liste_tarihi': '2026-10-07',
      })!;
      expect(r.cenazeGunu, '2026-10-08');
      expect(r.etiket, 'Cenaze · 8 Ekim · Öğle');
      expect(r.etiket.split(' · ')[1], tarih(r.cenazeGunu, kisa: true));
      expect(r.namazParcalari, ['Öğle namazını müteakip', 'Orta Camii']);
    });

    test('namaz günü yoksa defin günü, o da yoksa liste tarihi', () {
      final a = Ilan.fromJson({'ad_soyad': 'X Y', 'defin_zamani': '2026-10-05', 'liste_tarihi': '2026-10-04'})!;
      expect(a.cenazeGunu, '2026-10-05');
      final b = Ilan.fromJson({'ad_soyad': 'X Y', 'defin_zamani': 'İkindi', 'liste_tarihi': '2026-10-04'})!;
      expect(b.cenazeGunu, '2026-10-04');
      expect(b.etiket, 'Cenaze · 4 Ekim');
    });

    test('örnek veride her kartın etiket günü bulunduğu günle aynı', () {
      final v = IlVerisi.fromJson('Ordu', ornekOrdu('2026-10-08'));
      for (final l in v.ilceler.values) {
        for (final r in l) {
          expect(v.gunDolu(null, r.cenazeGunu), isTrue);
          expect(r.etiket.split(' · ')[1], tarih(r.cenazeGunu, kisa: true));
        }
      }
    });
  });

  group('Sayaç +1 / −1', () {
    test('artar, geri alınır, sıfırın altına inmez, kaldırılınca silinir', () async {
      SharedPreferences.setMockInitialValues({});
      final d = await Depo.ac();
      expect(await d.sayacDegis('k1', 'f', 1), 1);
      expect(await d.sayacDegis('k1', 'f', 1), 2);
      expect(await d.sayacDegis('k1', 'f', -1), 1);
      expect(await d.sayacDegis('k1', 'f', -1), 0);
      expect(await d.sayacDegis('k1', 'f', -1), 0);
      await d.sayacDegis('k1', 'y', 1);
      expect(d.sayaclar('k1'), {'f': 0, 'y': 1});
      await d.sayfamdanKaldir('k1');
      expect(d.sayaclar('k1'), isEmpty);
    });
  });

  group('Cinsiyet çözümleme (merhum / merhume)', () {
    final c = CinsiyetCozucu(erkek: ['Ahmet', 'Cihan'], kadin: ['Ayşe', 'Cihan']);
    Ilan ilan(Map<String, dynamic> j) => Ilan.fromJson({'ad_soyad': 'Ad Soyad', ...j})!;

    test('kayıttaki cinsiyet önce gelir', () {
      expect(c.coz(ilan({'ad_soyad': 'Ahmet Y', 'cinsiyet': 'Kadın'})), 'k');
    });
    test('ad listesi: büyük harfli ad da çözülür', () {
      expect(c.coz(ilan({'ad_soyad': 'AHMET YILMAZ'})), 'e');
      expect(c.coz(ilan({'ad_soyad': 'Ayşe Kaya'})), 'k');
    });
    test('iki cinsiyetli ya da bilinmeyen ad: tahmin yok', () {
      expect(c.coz(ilan({'ad_soyad': 'Cihan Er'})), isNull);
      expect(c.coz(ilan({'ad_soyad': 'Zerdüş Er'})), isNull);
      expect(c.coz(ilan({'ad_soyad': 'Zerdüş Er'}), secim: 'k'), 'k');
    });
    test('şehit ve bebek önekleri', () {
      expect(c.coz(ilan({'ad_soyad': 'Ahmet Y', 'sehit': true})), 's');
      expect(c.coz(ilan({'ad_soyad': 'Ayşe Y', 'bebek': true})), 'b');
    });
    test('sayaç cümleleri', () {
      expect(sayacEtiket('f', 'e'), 'Merhuma 1 Fâtiha okudum');
      expect(sayacEtiket('y', 'k'), 'Merhumeye 1 Yâsîn okudum');
      expect(sayacEtiket('f', 's'), 'Şehidimize 1 Fâtiha okudum');
      expect(sayacEtiket('i', 'b'), 'Bebeğimize 3 İhlâs ve 1 Fâtiha okudum');
      expect(sayacEtiket('h', null), '1 Kur’ân-ı Kerîm hatmi okudum');
    });
  });

  group('Kapı: kaynak alanı', () {
    test('kaynak alanı olmayan kayıt ilan olur', () {
      final r = Ilan.fromJson({'id': 'z', 'ad_soyad': 'Fatma Örnek', 'liste_tarihi': '2026-10-08'});
      expect(r, isNotNull);
      expect(r!.adSoyad, 'Fatma Örnek');
    });
    test('kaynak/anne-baba alanı gelse bile saklanmaz', () {
      final r = Ilan.fromJson({
        'id': 'z',
        'ad_soyad': 'Fatma Örnek',
        'kaynak_ad': 'Bir Belediye',
        'kaynak_url': 'https://ornek',
        'anne_baba': 'A-B',
        'ham': {'x': 1},
      })!;
      final j = r.toJson();
      expect(j.containsKey('kaynak_ad'), isFalse);
      expect(j.containsKey('kaynak_url'), isFalse);
      expect(j.containsKey('anne_baba'), isFalse);
      expect(j.containsKey('ham'), isFalse);
    });
    test('adı olmayan kayıt çizilmez', () {
      expect(Ilan.fromJson({'id': 'q', 'ad_soyad': '  '}), isNull);
    });
  });

  group('Türkçe yardımcılar', () {
    test('bulunma eki', () {
      expect(ek('Kars'), 'Kars’ta');
      expect(ek('Ünye'), 'Ünye’de');
      expect(ek('Aybastı'), 'Aybastı’da');
      expect(ek('Ordu'), 'Ordu’da');
    });
    test('il kodu', () {
      expect(ilKodu('Şanlıurfa'), 'sanliurfa');
      expect(ilKodu('İstanbul'), 'istanbul');
      expect(ilKodu('Iğdır'), 'igdir');
      expect(ilKodu('Çanakkale'), 'canakkale');
    });
    test('harf düzeni', () {
      expect(baslikHarf('KARAÇAL MAH. AİLE MEZ.'), 'Karaçal Mah. Aile Mezarlığı');
      expect(trBuyuk('Cenaze · 8 Ekim · Öğle'), 'CENAZE · 8 EKİM · ÖĞLE');
      expect(tarihGun('2026-10-08'), '8 Ekim Perşembe');
      expect(bugunTr(DateTime.utc(2026, 10, 7, 22, 30)), '2026-10-08');
    });
  });
}
