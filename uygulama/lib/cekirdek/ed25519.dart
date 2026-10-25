// Ed25519 İMZA DOĞRULAMA (RFC 8032 §5.1) — saf Dart, ek paket YOK (yalnız package:crypto'nun SHA-512'si).
// Neden elle: yeni bağımlılık eklemek derleme zincirini (flutter pub get / sürüm kilidi) değiştirir; burada yalnız DOĞRULAMA gerekir ve
// gizli veri işlenmediği için sabit zamanlı olması şart değildir. RFC 8032 vektörleri ve Python (cryptography) ile üretilmiş imzalar
// test/imza_test.dart içinde denenir. İmzalama bu uygulamada YOK (gizli anahtar cihaza girmez).
import 'dart:typed_data';

import 'package:crypto/crypto.dart' as c;

final BigInt _p = (BigInt.one << 255) - BigInt.from(19);
final BigInt _q = (BigInt.one << 252) + BigInt.parse('27742317777372353535851937790883648493');
BigInt _inv(BigInt x) => x.modPow(_p - BigInt.two, _p);
final BigInt _d = (-BigInt.from(121665) * _inv(BigInt.from(121666))) % _p;
final BigInt _i = BigInt.two.modPow((_p - BigInt.one) ~/ BigInt.from(4), _p);

class _Nokta {
  final BigInt x, y, z, t;
  const _Nokta(this.x, this.y, this.z, this.t);
}

BigInt _okuLE(List<int> b) {
  var r = BigInt.zero;
  for (var i = b.length - 1; i >= 0; i--) {
    r = (r << 8) | BigInt.from(b[i]);
  }
  return r;
}

BigInt? _xKurtar(BigInt y, int isaret) {
  if (y >= _p) return null;
  final x2 = ((y * y - BigInt.one) * _inv(_d * y * y + BigInt.one)) % _p;
  if (x2 == BigInt.zero) return isaret == 1 ? null : BigInt.zero;
  var x = x2.modPow((_p + BigInt.from(3)) ~/ BigInt.from(8), _p);
  if ((x * x - x2) % _p != BigInt.zero) x = (x * _i) % _p;
  if ((x * x - x2) % _p != BigInt.zero) return null;
  if ((x.isOdd ? 1 : 0) != isaret) x = _p - x;
  return x;
}

_Nokta? _ac(List<int> b) {
  if (b.length != 32) return null;
  var y = _okuLE(b);
  final isaret = (y >> 255).toInt();
  y = y & ((BigInt.one << 255) - BigInt.one);
  final x = _xKurtar(y, isaret);
  if (x == null) return null;
  return _Nokta(x, y, BigInt.one, (x * y) % _p);
}

_Nokta _topla(_Nokta a, _Nokta b) {
  final aa = ((a.y - a.x) * (b.y - b.x)) % _p;
  final bb = ((a.y + a.x) * (b.y + b.x)) % _p;
  final cc = (BigInt.two * a.t * b.t * _d) % _p;
  final dd = (BigInt.two * a.z * b.z) % _p;
  final e = bb - aa, f = dd - cc, g = dd + cc, h = bb + aa;
  return _Nokta((e * f) % _p, (g * h) % _p, (f * g) % _p, (e * h) % _p);
}

_Nokta _carp(BigInt s, _Nokta p) {
  var q = _Nokta(BigInt.zero, BigInt.one, BigInt.one, BigInt.zero);
  while (s > BigInt.zero) {
    if (s.isOdd) q = _topla(q, p);
    p = _topla(p, p);
    s >>= 1;
  }
  return q;
}

bool _esit(_Nokta a, _Nokta b) =>
    (a.x * b.z - b.x * a.z) % _p == BigInt.zero && (a.y * b.z - b.y * a.z) % _p == BigInt.zero;

final _Nokta _g = () {
  final gy = (BigInt.from(4) * _inv(BigInt.from(5))) % _p;
  final gx = _xKurtar(gy, 0)!;
  return _Nokta(gx, gy, BigInt.one, (gx * gy) % _p);
}();

/// [imza] (64 bayt), [mesaj] için [acik] (32 bayt) anahtarıyla atılmış geçerli Ed25519 imzası mı?
bool ed25519Dogrula(List<int> acik, List<int> mesaj, List<int> imza) {
  if (acik.length != 32 || imza.length != 64) return false;
  final a = _ac(acik);
  final r = _ac(imza.sublist(0, 32));
  if (a == null || r == null) return false;
  final s = _okuLE(imza.sublist(32));
  if (s >= _q) return false;
  final girdi = Uint8List.fromList([...imza.sublist(0, 32), ...acik, ...mesaj]);
  final h = _okuLE(c.sha512.convert(girdi).bytes) % _q;
  return _esit(_carp(s, _g), _topla(r, _carp(h, a)));
}
