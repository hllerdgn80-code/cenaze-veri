// Zorunlu güncelleme kapısı (URUN-TASLAGI §42). Sürüm bilgisi depodaki site/surum.json'dan gelir (veri.kimincenazesi.com/surum.json).
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import 'anahtar.dart';

/// Derlemedeki build numarası (CI: --dart-define=BUILD_NO=${{ github.run_number }}). 0 = geliştirme/test: kapı atlanır.
const int buildNoDerleme = int.fromEnvironment('BUILD_NO', defaultValue: 0);

const String surumUrl = 'https://veri.kimincenazesi.com/surum.json';
const String paketAdi = 'com.kimincenazesi.app';
const String marketUrl = 'market://details?id=$paketAdi';
const String webMarketUrl = 'https://play.google.com/store/apps/details?id=$paketAdi';
const String varsayilanGuncellemeMesaji = 'Yeni bir sürüm yayımlandı. Devam etmek için güncelleyin.';

class SurumBilgi {
  final int minBuild;
  final int sonBuild;
  final String sonSurum;
  final String mesaj;
  const SurumBilgi({this.minBuild = 0, this.sonBuild = 0, this.sonSurum = '', this.mesaj = varsayilanGuncellemeMesaji});

  static SurumBilgi? coz(String govde) {
    try {
      final j = jsonDecode(govde);
      if (j is! Map) return null;
      int sayi(Object? v) => v is num ? v.toInt() : (int.tryParse('${v ?? ''}') ?? 0);
      final m = (j['mesaj'] ?? '').toString().trim();
      return SurumBilgi(
        minBuild: sayi(j['min_build']),
        sonBuild: sayi(j['son_build']),
        sonSurum: (j['son_surum'] ?? '').toString(),
        mesaj: m.isEmpty ? varsayilanGuncellemeMesaji : m,
      );
    } catch (_) {
      return null;
    }
  }
}

/// Sürüm bilgisini çeker; ağ/ayrıştırma hatasında null (kapı AÇIK kalır).
typedef SurumCekici = Future<SurumBilgi?> Function();

SurumCekici varsayilanSurumCekici(http.Client istemci) => () async {
      final r = await istemci
          .get(Uri.parse('$surumUrl?k=${DateTime.now().millisecondsSinceEpoch ~/ 60000}'),
              headers: {...kcBasliklar(), 'Accept': 'application/json'}) // veri kapısı anahtar + UA ister (yoksa 403 → kapı hiç çalışmaz)
          .timeout(const Duration(seconds: 3));
      if (r.statusCode != 200) return null;
      return SurumBilgi.coz(utf8.decode(r.bodyBytes));
    };

/// Play Store'u açar: önce market://, olmazsa https.
Future<void> magazayiAc() async {
  for (final u in [marketUrl, webMarketUrl]) {
    try {
      if (await launchUrl(Uri.parse(u), mode: LaunchMode.externalApplication)) return;
    } catch (_) {}
  }
}
