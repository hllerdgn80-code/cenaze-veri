// "Haritada aç": koordinat/OSM verisi yok; "yer, ilçe, il" metniyle Google Haritalar araması (Haritalar uygulaması kuruluysa o açılır).
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'metin.dart';

/// Arama bağlantısı: https://www.google.com/maps/search/?api=1&query=<yer, ilçe, il>
Uri haritaUri({required String yer, String? ilce, String? il}) {
  final q = [yer, ilce, il].where((x) => x != null && x.trim().isNotEmpty).map((x) => x!.trim()).join(', ');
  return Uri.parse('https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(q)}');
}

/// Açamazsa "Harita açılamadı" bildirimi gösterir. Dönüş: açıldı mı.
Future<bool> haritadaAc(BuildContext context, {required String yer, String? ilce, String? il}) async {
  var acildi = false;
  try {
    acildi = await launchUrl(haritaUri(yer: yer, ilce: ilce, il: il), mode: LaunchMode.externalApplication);
  } catch (_) {}
  if (!acildi && context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(M.haritaAcilamadi)));
  return acildi;
}
