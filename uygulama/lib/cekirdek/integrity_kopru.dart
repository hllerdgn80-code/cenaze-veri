// PLAY INTEGRITY KÖPRÜSÜ (Android platform kanalı) — İSKELET (25.10.2026). Etkinleştirme adımları ve Kotlin kodu:
// cenaze-uygulamasi/deploy/GUVENLIK-PAKETI-2026-10-25.md §3 (Play Console > Uygulama bütünlüğü, Cloud projesi, servis hesabı, secret).
// Kotlin tarafı YAPILACAK İŞ (bu pakete girmedi): android/ klasörü CI'da üretildiği için araclar/android_ayarla.py MainActivity.kt'yi yazacak:
//   StandardIntegrityManager ile hazırla (bulut projesi numarası) -> prepareIntegrityToken -> request(requestHash) -> token
// Gradle bağımlılığı: com.google.android.play:integrity:1.4.0 (android_ayarla.py eklemeli).
// Kanal yoksa (iOS/web/test) MissingPluginException yakalanır, null döner: uygulama jetonsuz çalışır.
import 'package:flutter/services.dart';

import 'guvenlik_jeton.dart';

class PlayIntegrityKopru implements JetonSaglayici {
  static const _kanal = MethodChannel('kc/integrity');

  @override
  Future<String?> integrityJetonu(String istekOzeti) async {
    try {
      final t = await _kanal.invokeMethod<String>('jeton', {'requestHash': istekOzeti});
      return t;
    } on MissingPluginException {
      return null;
    } on PlatformException {
      return null;
    }
  }
}

/// main() içinde bir kez: `kcJetonSaglayici = PlayIntegrityKopru();` (ana dosyaya EKLENMEDİ: Kotlin tarafı hazır olmadan kanal çağrısı gereksiz gecikme yaratır).
