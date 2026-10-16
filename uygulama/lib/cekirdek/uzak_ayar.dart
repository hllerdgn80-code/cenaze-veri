// UZAK AYAR (16.10.2026, sahibi: "sürüm değişikliği olmadan değiştirilebilsin"). Ekran kuralları sunucudaki
// site/ayarlar.json'dan (veri.kimincenazesi.com/ayarlar.json) okunur; son iyi değer telefonda saklanır (çevrimdışı/hata = son değer,
// hiç yoksa derlemedeki varsayılan). Açılışta ve ilanlar her yenilendiğinde arka planda tazelenir.
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'anahtar.dart';

const String uzakAyarUrl = 'https://veri.kimincenazesi.com/ayarlar.json';

class UzakAyar {
  UzakAyar._();

  /// İlçe sayfasında ilin ilçesiz/nakil ilanlarını "İl geneli" başlığıyla göster (varsayılan: GÖSTERME — sahibi 16.10.2026).
  static bool ilceSayfasindaIlGeneli = false;

  /// Bugün seçiliyken bugün ilan yoksa "Dün (…)" ilanlarını altında göster (URUN §57). Varsayılan: GÖSTERME — sahibi 16.10.2026
  /// ("o gün cenaze yoksa sadece yok desin, altında ilan linkleri olsun").
  static bool bugunBossaDunuGoster = false;

  static const _anahtar = 'uzak_ayar';
  static DateTime? _son;

  static void uygula(Map j) {
    final v = j['ilce_sayfasinda_il_geneli'];
    if (v is bool) ilceSayfasindaIlGeneli = v;
    final d = j['bugun_bossa_dunu_goster'];
    if (d is bool) bugunBossaDunuGoster = d;
  }

  /// Telefonda saklı son değeri yükler (açılışta, ağdan önce).
  static Future<void> yerelYukle() async {
    try {
      final p = await SharedPreferences.getInstance();
      final s = p.getString(_anahtar);
      if (s != null) {
        final j = jsonDecode(s);
        if (j is Map) uygula(j);
      }
    } catch (_) {}
  }

  /// Sunucudan tazeler; değer değiştiyse true. En çok dakikada bir istek.
  static Future<bool> tazele(http.Client istemci) async {
    final simdi = DateTime.now();
    if (_son != null && simdi.difference(_son!) < const Duration(minutes: 1)) return false;
    _son = simdi;
    try {
      final r = await istemci
          .get(Uri.parse('$uzakAyarUrl?k=${simdi.millisecondsSinceEpoch ~/ 60000}'), headers: {...kcBasliklar(), 'Accept': 'application/json'})
          .timeout(const Duration(seconds: 4));
      if (r.statusCode != 200) return false;
      final govde = utf8.decode(r.bodyBytes);
      final j = jsonDecode(govde);
      if (j is! Map) return false;
      final once = '$ilceSayfasindaIlGeneli|$bugunBossaDunuGoster';
      uygula(j);
      final p = await SharedPreferences.getInstance();
      await p.setString(_anahtar, govde);
      return once != '$ilceSayfasindaIlGeneli|$bugunBossaDunuGoster';
    } catch (_) {
      return false;
    }
  }
}
