// Zorunlu güncelleme kapısı (URUN-TASLAGI §42). Sürüm bilgisi depodaki site/surum.json'dan gelir (veri.kimincenazesi.com/surum.json).
import 'dart:convert';

import 'package:flutter/foundation.dart' show defaultTargetPlatform, TargetPlatform;
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import 'anahtar.dart';
import 'imza.dart';

/// Derlemedeki build numarası (CI: --dart-define=BUILD_NO=${{ github.run_number }}). 0 = geliştirme/test: kapı atlanır.
const int buildNoDerleme = int.fromEnvironment('BUILD_NO', defaultValue: 0);

const String surumUrl = 'https://veri.kimincenazesi.com/surum.json';
const String paketAdi = 'com.kimincenazesi.app';
const String marketUrl = 'market://details?id=$paketAdi';
const String webMarketUrl = 'https://play.google.com/store/apps/details?id=$paketAdi';
/// iOS mağaza bağlantısı: surum.json `ios_magaza_url` yoksa bu (App Store kaydı olunca surum.json'a gerçek bağlantı yazılır).
const String varsayilanIosMagazaUrl = 'https://kimincenazesi.com/ios';
const String varsayilanGuncellemeMesaji = 'Yeni bir sürüm yayımlandı. Devam etmek için güncelleyin.';

/// Çalışan platform iOS mu (testte AppDurum(ios: true) ile ezilir).
bool get iosMu => defaultTargetPlatform == TargetPlatform.iOS;

/// Son bilinen iOS mağaza bağlantısı (surum.json'dan; paylaşma metni için). Sürüm bilgisi gelmediyse null.
String? sonIosMagazaUrl;

String magazaAdi(bool ios) => ios ? 'App Store' : 'Play Store';

class SurumBilgi {
  final int minBuild;
  final int sonBuild;
  // iOS'un build numarası (iOS iş akışının run/build sayacı) Android'inkinden bağımsızdır → ayrı anahtarlar; yoksa 0 = zorunlu güncelleme yok.
  final int minBuildIos;
  final int sonBuildIos;
  final String iosMagazaUrl;
  final String sonSurum;
  final String mesaj;
  const SurumBilgi(
      {this.minBuild = 0,
      this.sonBuild = 0,
      this.minBuildIos = 0,
      this.sonBuildIos = 0,
      this.iosMagazaUrl = varsayilanIosMagazaUrl,
      this.sonSurum = '',
      this.mesaj = varsayilanGuncellemeMesaji});

  int minBuildIcin(bool ios) => ios ? minBuildIos : minBuild;
  int sonBuildIcin(bool ios) => ios ? sonBuildIos : sonBuild;

  static SurumBilgi? coz(String govde) {
    try {
      final j = jsonDecode(govde);
      if (j is! Map) return null;
      int sayi(Object? v) => v is num ? v.toInt() : (int.tryParse('${v ?? ''}') ?? 0);
      final m = (j['mesaj'] ?? '').toString().trim();
      final u = (j['ios_magaza_url'] ?? '').toString().trim();
      return SurumBilgi(
        minBuild: sayi(j['min_build']),
        sonBuild: sayi(j['son_build']),
        minBuildIos: sayi(j['min_build_ios']),
        sonBuildIos: sayi(j['son_build_ios']),
        iosMagazaUrl: u.startsWith('https://') ? u : varsayilanIosMagazaUrl,
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

SurumCekici varsayilanSurumCekici(http.Client istemci, {ImzaDogrulayici? imza}) => () async {
      final r = await istemci
          .get(Uri.parse('$surumUrl?k=${DateTime.now().millisecondsSinceEpoch ~/ 60000}'),
              headers: {...kcBasliklar(), 'Accept': 'application/json'}) // veri kapısı anahtar + UA ister (yoksa 403 → kapı hiç çalışmaz)
          .timeout(const Duration(seconds: 3));
      if (r.statusCode != 200) return null;
      // imzasız/bozuk sürüm bilgisi uygulanmaz (sahte "zorunlu güncelleme" kapısı kurulamaz)
      if (!(imza ?? ImzaDogrulayici.varsayilan()).kabul('surum.json', r.bodyBytes)) return null;
      return SurumBilgi.coz(utf8.decode(r.bodyBytes));
    };

/// Mağaza adresleri: Android'de önce market://, sonra https; iOS'ta surum.json'daki (yoksa varsayılan) App Store bağlantısı.
List<String> magazaAdresleri({required bool ios, String? iosUrl}) =>
    ios ? [(iosUrl == null || iosUrl.isEmpty) ? varsayilanIosMagazaUrl : iosUrl] : [marketUrl, webMarketUrl];

/// Mağazayı açar (Android: Play Store; iOS: App Store). [ios] verilmezse çalışan platform.
Future<void> magazayiAc({bool? ios, String? iosUrl}) async {
  for (final u in magazaAdresleri(ios: ios ?? iosMu, iosUrl: iosUrl ?? sonIosMagazaUrl)) {
    try {
      if (await launchUrl(Uri.parse(u), mode: LaunchMode.externalApplication)) return;
    } catch (_) {}
  }
}
