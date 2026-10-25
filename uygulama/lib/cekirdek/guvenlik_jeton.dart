// BOT KAPISI JETONU (25.10.2026, GÜVENLİK PAKETİ madde 1). Yazan (POST) her isteğe `x-integrity` başlığıyla Play Integrity jetonu eklenir;
// Worker (deploy/aile-worker/src/integrity.js) jetonu Google'a çözdürüp paket adı + istek özeti + zaman + cihaz bütünlüğünü denetler.
// Bu dosya SAF Dart'tır (test edilir). Gerçek jeton sağlayıcısı Android platform kanalındadır: lib/cekirdek/integrity_kopru.dart
// (Kotlin kaynağı ve Play Console adımları: deploy/GUVENLIK-PAKETI-2026-10-25.md §3). Sağlayıcı yoksa / hata verirse başlık EKLENMEZ ve istek yine gider:
// Worker modu "kapali" ya da "izle" iken sorun olmaz; "zorunlu" iken Worker 403 verir (karar Worker'dadır, istemci asla "geçti" varsaymaz).
import 'dart:convert';

import 'package:crypto/crypto.dart' as c;

/// Worker `istekOzeti(yol, govdeMetni)` ile AYNI: base64url(sha256(yol + "\n" + gövde)), dolgusuz.
String istekOzeti(String yol, String govde) =>
    base64Url.encode(c.sha256.convert(utf8.encode('$yol\n$govde')).bytes).replaceAll('=', '');

/// Jeton üretici (Play Integrity "standard request"): [istekOzeti] requestHash olarak jetona gömülür.
abstract class JetonSaglayici {
  Future<String?> integrityJetonu(String istekOzeti);
}

/// Uygulama başlarken bir kez atanır (Android'de PlayIntegrityKopru). Atanmazsa bot kapısı jetonu eklenmez.
JetonSaglayici? kcJetonSaglayici;

/// POST için ek başlıklar. [govde]: istekte gönderilecek TAM metin (jsonEncode çıktısı). Hata/sağlayıcı yok -> boş.
Future<Map<String, String>> guvenlikBasliklari(String yol, String govde, {JetonSaglayici? saglayici}) async {
  final s = saglayici ?? kcJetonSaglayici;
  if (s == null) return const {};
  try {
    final t = await s.integrityJetonu(istekOzeti(yol, govde)).timeout(const Duration(seconds: 4));
    return t == null || t.isEmpty ? const {} : {'x-integrity': t};
  } catch (_) {
    return const {};
  }
}
