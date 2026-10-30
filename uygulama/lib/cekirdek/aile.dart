// Aile ilanı Worker istemcisi (sözleşme: deploy/AILE-ILAN-SOZLESME.md).
// Uç nokta: POST /aile/bildir (başvur/doğrula 25.10.2026'da kaldırıldı). Hiçbir yanıt cihazda saklanmaz.
import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;

import 'package:http/http.dart' as http;

import 'anahtar.dart';
import 'guvenlik_jeton.dart';
import 'veri.dart';

/// Worker yanıtı. [agHatasi]: bağlantı kurulamadı / zaman aşımı; [govde]: çözülebilen JSON nesnesi.
class AileYanit {
  final int kod;
  final Map<String, dynamic>? govde;
  final bool agHatasi;
  const AileYanit(this.kod, this.govde, {this.agHatasi = false});

  bool get tamam => !agHatasi && kod >= 200 && kod < 300;
  String? get durum => govde?['durum']?.toString();
  String? get neden {
    final n = govde?['neden']?.toString().trim();
    return (n == null || n.isEmpty) ? null : n;
  }
}

class AileServisi {
  final http.Client istemci;
  final String kok;
  const AileServisi({required this.istemci, this.kok = aileKok});

  static const _zamanAsimi = Duration(seconds: 15);

  Future<AileYanit> _gonder(String yol, Map<String, dynamic> govde) async {
    try {
      final metin = jsonEncode(govde);
      final y = await istemci
          .post(
            Uri.parse('$kok$yol'),
            headers: {'Content-Type': 'application/json; charset=utf-8', 'Accept': 'application/json', ...kcBasliklar(), ...await guvenlikBasliklari(yol, metin)},
            body: metin,
          )
          .timeout(_zamanAsimi);
      Map<String, dynamic>? j;
      try {
        final ham = jsonDecode(utf8.decode(y.bodyBytes));
        if (ham is Map) j = Map<String, dynamic>.from(ham);
      } catch (_) {}
      return AileYanit(y.statusCode, j);
    } on SocketException {
      return const AileYanit(0, null, agHatasi: true);
    } on TimeoutException {
      return const AileYanit(0, null, agHatasi: true);
    } on http.ClientException {
      return const AileYanit(0, null, agHatasi: true);
    } catch (_) {
      return const AileYanit(0, null, agHatasi: true);
    }
  }

  // 25.10.2026: /aile/basvur, /aile/dogrula, /aile/odeme KALDIRILDI (Tam Sayfa İlan; Worker 410). Aile ilanı yazma yolu yok; yalnız bildirim kalır.
  Future<AileYanit> bildir(String ilanId, String neden) => _gonder('/aile/bildir', {'ilan_id': bildirimKimligi(ilanId), 'neden': neden});

  /// 30.10.2026 HATA: veri hattı aile/görevli kayıtlarının kimliğine "aile-" / "gorevli-" öneki koyar (okuyucu/aile_al.py, gorevli_al.py),
  /// Worker ise çıplak 16 haneli kimliği ister (^[0-9a-f]{16}$) → önekli kimlikle "Bu ilanda bir yanlışlık mı var?" hep 400 dönüyordu.
  static String bildirimKimligi(String id) => id.replaceFirst(RegExp(r'^(aile|gorevli)-'), '');
}
