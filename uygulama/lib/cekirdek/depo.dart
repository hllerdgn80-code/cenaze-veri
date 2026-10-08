// Cihaz deposu (shared_preferences). Hiçbir veri cihaz dışına gönderilmez.
// Anahtarlar: il, ilce, tema, kayit (Sayfam), sayac, cins, onbellek_<il>.
import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'ilan.dart';

class SayfamKaydi {
  final Ilan ilan;
  final int zaman; // eklenme anı (ms) — en yeni üstte
  const SayfamKaydi(this.ilan, this.zaman);
}

class Depo {
  final SharedPreferences _p;
  Depo(this._p);

  static Future<Depo> ac() async => Depo(await SharedPreferences.getInstance());

  // ---- Adres ----
  String? get il => _p.getString('il');

  /// null = tüm ilçeler
  String? get ilce {
    final v = _p.getString('ilce');
    return (v == null || v.isEmpty) ? null : v;
  }

  Future<void> adresKaydet(String il, String? ilce) async {
    await _p.setString('il', il);
    await _p.setString('ilce', ilce ?? '');
  }

  // ---- Tema ('koyu' varsayılan) ----
  bool get koyu => (_p.getString('tema') ?? 'koyu') == 'koyu';
  Future<void> temaKaydet(bool koyu) => _p.setString('tema', koyu ? 'koyu' : 'acik');

  // ---- JSON yardımcıları ----
  Map<String, dynamic> _harita(String k) {
    final s = _p.getString(k);
    if (s == null) return {};
    try {
      final v = jsonDecode(s);
      return v is Map ? Map<String, dynamic>.from(v) : {};
    } catch (_) {
      return {};
    }
  }

  Future<void> _yaz(String k, Map<String, dynamic> v) => _p.setString(k, jsonEncode(v));

  // ---- Sayfam (kendiliğinden silinmez; yalnız kullanıcı kaldırır) ----
  bool kayitli(String id) => _harita('kayit').containsKey(id);

  Future<void> sayfamaEkle(Ilan r) async {
    final k = _harita('kayit');
    if (k.containsKey(r.id)) return;
    k[r.id] = {'r': r.toJson(), 't': DateTime.now().millisecondsSinceEpoch};
    await _yaz('kayit', k);
  }

  List<SayfamKaydi> sayfam() {
    final out = <SayfamKaydi>[];
    _harita('kayit').forEach((id, v) {
      if (v is Map && v['r'] is Map) {
        final r = Ilan.fromJson(Map<String, dynamic>.from(v['r'] as Map));
        if (r != null) out.add(SayfamKaydi(r, (v['t'] as num?)?.toInt() ?? 0));
      }
    });
    out.sort((a, b) => b.zaman.compareTo(a.zaman));
    return out;
  }

  Future<void> sayfamdanKaldir(String id) async {
    for (final a in ['kayit', 'sayac', 'cins']) {
      final o = _harita(a);
      o.remove(id);
      await _yaz(a, o);
    }
  }

  // ---- Sayaçlar ----
  Map<String, int> sayaclar(String id) {
    final v = _harita('sayac')[id];
    if (v is! Map) return {};
    return v.map((k, n) => MapEntry(k.toString(), (n as num?)?.toInt() ?? 0));
  }

  /// +1 ya da −1; sayaç 0'ın altına inmez. Yeni değeri döner.
  Future<int> sayacDegis(String id, String tur, int fark) async {
    final s = _harita('sayac');
    final m = s[id] is Map ? Map<String, dynamic>.from(s[id] as Map) : <String, dynamic>{};
    final eski = (m[tur] as num?)?.toInt() ?? 0;
    final yeni = (eski + fark) < 0 ? 0 : eski + fark;
    m[tur] = yeni;
    s[id] = m;
    await _yaz('sayac', s);
    return yeni;
  }

  // ---- Kullanıcının cinsiyet seçimi (cinsiyet bilinmeyen kayıt) ----
  String? cinsSecimi(String id) => _harita('cins')[id] as String?;

  Future<void> cinsKaydet(String id, String c) async {
    final o = _harita('cins');
    o[id] = c;
    await _yaz('cins', o);
  }

  // ---- Son başarılı veri yanıtı (çevrimdışı gösterim) ----
  String? onbellek(String kod) => _p.getString('onbellek_$kod');
  int? onbellekZamani(String kod) => _p.getInt('onbellek_${kod}_t');

  Future<void> onbellekYaz(String kod, String govde) async {
    await _p.setString('onbellek_$kod', govde);
    await _p.setInt('onbellek_${kod}_t', DateTime.now().millisecondsSinceEpoch);
  }
}
