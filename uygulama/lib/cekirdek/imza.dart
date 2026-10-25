// YAYIN İMZASI DOĞRULAMA (25.10.2026, GÜVENLİK PAKETİ madde 2). Biçim ve kural okuyucu/imza.py ile BİREBİR aynıdır
// (ortak vektörler: test/imza_vektorleri.json = okuyucu/imza_vektorleri.json). Özet:
//   mesaj = "KC1\n" + yol + "\n" + ts + "\n" + gövde
//   kök nesne: imza dosyanın İÇİNDE, son anahtar  …,"imza":"<ts>.<base64url>"}   (gövde = bu eki atıp '}' ile kapatılmış hâli; yeniden serileştirme yok)
//   kök dizi : yan dosya "<ad>-imza.json" içinde JSON metni "<ts>.<base64url>"
// Kural: [etkin] iken (açık anahtar listesi dolu) imzasız / bozuk / bayat veri GÖSTERİLMEZ; liste boşsa doğrulama kapalıdır (geçiş).
import 'dart:convert';
import 'dart:typed_data';

import 'ed25519.dart';
import 'imza_anahtari.dart';

enum ImzaSonuc { gecerli, imzasiz, bozuk, eski }

class ImzaDogrulayici {
  final List<Uint8List> acikAnahtarlar;
  final Duration azamiYas;
  final DateTime Function() simdi;

  ImzaDogrulayici({List<String> b64Anahtarlar = const [], this.azamiYas = const Duration(days: 14), DateTime Function()? simdi})
      : acikAnahtarlar = [for (final k in b64Anahtarlar) Uint8List.fromList(base64.decode(k))],
        simdi = simdi ?? DateTime.now;

  /// Derlemeye gömülü açık anahtarlarla (lib/cekirdek/imza_anahtari.dart).
  factory ImzaDogrulayici.varsayilan() => ImzaDogrulayici(b64Anahtarlar: kcImzaAcikAnahtarlar);

  bool get etkin => acikAnahtarlar.isNotEmpty;

  static final RegExp _ek = RegExp(r'^(\d{9,12})\.([A-Za-z0-9_-]{86})$');
  static final Uint8List _isaretVirgul = Uint8List.fromList(utf8.encode(',"imza":"'));
  static final Uint8List _isaretBas = Uint8List.fromList(utf8.encode('{"imza":"'));

  static Uint8List _sagTemiz(Uint8List b) {
    var n = b.length;
    while (n > 0 && (b[n - 1] == 0x20 || b[n - 1] == 0x09 || b[n - 1] == 0x0D || b[n - 1] == 0x0A)) {
      n--;
    }
    return Uint8List.sublistView(b, 0, n);
  }

  static int _sonIndeks(Uint8List b, Uint8List ara) {
    for (var i = b.length - ara.length; i >= 0; i--) {
      var ok = true;
      for (var j = 0; j < ara.length; j++) {
        if (b[i + j] != ara[j]) {
          ok = false;
          break;
        }
      }
      if (ok) return i;
    }
    return -1;
  }

  static Uint8List _mesaj(String yol, int ts, Uint8List govde) =>
      Uint8List.fromList([...utf8.encode('KC1\n$yol\n$ts\n'), ...govde]);

  static Uint8List? _b64uCoz(String s) {
    try {
      return Uint8List.fromList(base64Url.decode(base64Url.normalize(s)));
    } catch (_) {
      return null;
    }
  }

  ImzaSonuc _karar(String yol, Uint8List govde, int ts, Uint8List imza, {required bool yasKontrol}) {
    var tamam = false;
    final m = _mesaj(yol, ts, govde);
    for (final k in acikAnahtarlar) {
      if (ed25519Dogrula(k, m, imza)) {
        tamam = true;
        break;
      }
    }
    if (!tamam) return ImzaSonuc.bozuk;
    if (!yasKontrol) return ImzaSonuc.gecerli;
    final simdiS = simdi().millisecondsSinceEpoch ~/ 1000;
    if (ts > simdiS + 600 || simdiS - ts > azamiYas.inSeconds) return ImzaSonuc.eski;
    return ImzaSonuc.gecerli;
  }

  /// [yol]: sunucu kökünden göreli yol ("veri/ordu/son7gun.json", "ayarlar.json"). [yan]: kök dizi dosyalarının yan imza dosyası gövdesi
  /// (JSON metni). [yasKontrol] false: yalnız imza geçerli mi (cihazda saklı eski kopya için).
  ImzaSonuc denetle(String yol, Uint8List bayt, {Uint8List? yan, bool yasKontrol = true}) {
    if (yan != null) {
      String? s;
      try {
        final j = jsonDecode(utf8.decode(yan));
        s = j is String ? j : null;
      } catch (_) {}
      final e = s == null ? null : _ek.firstMatch(s);
      final im = e == null ? null : _b64uCoz(e.group(2)!);
      if (e == null || im == null || im.length != 64) return ImzaSonuc.bozuk;
      return _karar(yol, bayt, int.parse(e.group(1)!), im, yasKontrol: yasKontrol);
    }
    final t = _sagTemiz(bayt);
    if (t.length < 4 || t[t.length - 2] != 0x22 || t[t.length - 1] != 0x7D) return ImzaSonuc.imzasiz; // '"}' ile bitmiyor
    for (final isaret in [_isaretVirgul, _isaretBas]) {
      final i = _sonIndeks(t, isaret);
      if (i < 0 || (identical(isaret, _isaretBas) && i != 0)) continue; // '{"imza":"…"}' yalnız dosyanın BAŞINDA geçerli (boş nesne)
      final eks = utf8.decode(Uint8List.sublistView(t, i + isaret.length, t.length - 2), allowMalformed: true);
      final e = _ek.firstMatch(eks);
      if (e == null) continue;
      final im = _b64uCoz(e.group(2)!);
      if (im == null || im.length != 64) return ImzaSonuc.bozuk;
      final govde = identical(isaret, _isaretVirgul) ? Uint8List.fromList([...Uint8List.sublistView(t, 0, i), 0x7D]) : Uint8List.fromList([0x7B, 0x7D]);
      return _karar(yol, govde, int.parse(e.group(1)!), im, yasKontrol: yasKontrol);
    }
    return ImzaSonuc.imzasiz;
  }

  /// Gösterilebilir mi? Doğrulama kapalıysa (anahtar yok) her zaman evet.
  bool kabul(String yol, Uint8List bayt, {Uint8List? yan, bool yasKontrol = true}) =>
      !etkin || denetle(yol, bayt, yan: yan, yasKontrol: yasKontrol) == ImzaSonuc.gecerli;
}
