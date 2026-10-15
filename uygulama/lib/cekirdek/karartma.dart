// Kimlik numarası (TC) OTOMATİK KARARTMA — saf Dart (eklenti yok; test edilebilir). Site sahibi 15.10.2026:
// fotoğraf gönderilmeden ÖNCE cihaz içi metin tanıma sonucu (satır/öğe kutuları) ile 11 haneli rakam dizileri ve
// "T.C. Kimlik No" etiketinin yanındaki sayılar bulunur, piksel düzeyinde SİYAH dikdörtgenle kapatılır, sonra en uzun kenar 1600 px'e küçültülüp JPEG verilir.
// Tanıma/karartma başarısız olursa fotoğraf GÖNDERİLMEZ (kart_kamera.dart hata verir): kapatılamayan görüntü sunucuya ulaşmaz.
import 'dart:typed_data';

import 'package:image/image.dart' as img;

class Kutu {
  final int sol, ust, sag, alt;
  const Kutu(this.sol, this.ust, this.sag, this.alt);
  @override
  String toString() => 'Kutu($sol,$ust,$sag,$alt)';
}

/// Metin tanımanın bir öğesi (kelime): metin + piksel kutusu (tanımanın gördüğü, EXIF uygulanmış görüntüde)
class MetinOgesi {
  final String metin;
  final Kutu kutu;
  const MetinOgesi(this.metin, this.kutu);
}

class MetinSatiri {
  final List<MetinOgesi> ogeler;
  const MetinSatiri(this.ogeler);
  String get metin => ogeler.map((o) => o.metin).join(' ');
}

/// Fotoğraf dosyası yolundan satırları verir (üretimde ML Kit, testte sahte)
typedef MetinTanima = Future<List<MetinSatiri>> Function(String yol);

const int kartEnUzunKenar = 1600;
const int _tcHane = 11;
const int _bosluk = 6; // kutunun her yanına eklenen piksel payı

final RegExp _sayiOgesi = RegExp(r'^[\d.\-]+$');
final RegExp _tcEtiketi = RegExp(r'(kimlik\s*(no|numaras)|t\.?\s?c\.?\s*(kimlik|no))', caseSensitive: false);

String _rakamlar(String s) => s.replaceAll(RegExp(r'\D'), '');

Kutu _birlestir(Iterable<Kutu> k) {
  var sol = 1 << 30, ust = 1 << 30, sag = -1, alt = -1;
  for (final x in k) {
    if (x.sol < sol) sol = x.sol;
    if (x.ust < ust) ust = x.ust;
    if (x.sag > sag) sag = x.sag;
    if (x.alt > alt) alt = x.alt;
  }
  return Kutu(sol, ust, sag, alt);
}

/// Karartılacak bölgeler:
///  a) tek öğede ≥11 rakam (ör. 12345678901),
///  b) art arda sayısal öğelerin (aralıklı yazılmış 123 456 789 01) rakam toplamı ≥11 ise TÜM dizi,
///  c) "T.C. Kimlik No" etiketi olan satırdaki ≥6 haneli sayılar (etiketin yanındaki sayı).
List<Kutu> tcBolgeleri(List<MetinSatiri> satirlar) {
  final out = <Kutu>[];
  for (final satir in satirlar) {
    final o = satir.ogeler;
    for (final e in o) {
      if (_rakamlar(e.metin).length >= _tcHane) out.add(e.kutu);
    }
    var i = 0;
    while (i < o.length) {
      if (!_sayiOgesi.hasMatch(o[i].metin)) {
        i++;
        continue;
      }
      var j = i, toplam = 0;
      while (j < o.length && _sayiOgesi.hasMatch(o[j].metin)) {
        toplam += _rakamlar(o[j].metin).length;
        j++;
      }
      if (j - i > 1 && toplam >= _tcHane) out.add(_birlestir(o.sublist(i, j).map((e) => e.kutu)));
      i = j;
    }
    if (_tcEtiketi.hasMatch(satir.metin)) {
      for (final e in o) {
        if (_sayiOgesi.hasMatch(e.metin) && _rakamlar(e.metin).length >= 6) out.add(e.kutu);
      }
    }
  }
  return out;
}

/// JPEG'i çözer (EXIF döndürmesi uygulanır), [kutular]ı siyaha boyar, en uzun kenarı [enUzun] px'e indirir, JPEG döner.
Uint8List karartVeKucult(Uint8List jpeg, List<Kutu> kutular, {int enUzun = kartEnUzunKenar, int kalite = 85}) {
  final ham = img.decodeJpg(jpeg);
  if (ham == null) throw const FormatException('JPEG çözülemedi');
  var g = img.bakeOrientation(ham);
  final siyah = img.ColorRgb8(0, 0, 0);
  for (final k in kutular) {
    img.fillRect(
      g,
      x1: (k.sol - _bosluk).clamp(0, g.width - 1).toInt(),
      y1: (k.ust - _bosluk).clamp(0, g.height - 1).toInt(),
      x2: (k.sag + _bosluk).clamp(0, g.width - 1).toInt(),
      y2: (k.alt + _bosluk).clamp(0, g.height - 1).toInt(),
      color: siyah,
    );
  }
  final uzun = g.width > g.height ? g.width : g.height;
  if (uzun > enUzun) {
    g = g.width >= g.height ? img.copyResize(g, width: enUzun) : img.copyResize(g, height: enUzun);
  }
  return Uint8List.fromList(img.encodeJpg(g, quality: kalite));
}

/// Tanı → bul → karart → küçült. Hata fırlatırsa çağıran fotoğrafı GÖNDERMEZ.
Future<Uint8List> kartiHazirla(String yol, Uint8List jpeg, MetinTanima tanima) async {
  final satirlar = await tanima(yol);
  return karartVeKucult(jpeg, tcBolgeleri(satirlar));
}
