// UZAK AYAR (16.10.2026, sahibi: "uygulamada a'dan z'ye ne varsa hepsini uzak ayara bağla"). Sunucudaki site/ayarlar.json
// (veri.kimincenazesi.com/ayarlar.json) şu bölümleri taşıyabilir; olmayan anahtar = uygulamadaki varsayılan:
//   "yazilar":  {"<M anahtarı>": "metin"}            — bütün ekran yazıları (cekirdek/metin.dart'taki adlarla)
//   "kaliplar": {"<M anahtarı>": "… {0} … {1} …"}     — içinde ad/tarih/sayı geçen yazılar ({0},{1} yer tutucu)
//   "listeler": {"<M anahtarı>": ["…", …]  ya da  [["…","…"], …]}   — seçenek listeleri
//   "haritalar": {"<M anahtarı>": {"a": "…"}}
//   "bayraklar": {"<ad>": true/false}  — ekran kuralları;  "sayilar": {"<ad>": 5} — süreler, saatler
//   "acil_gizle": {"il": ["ordu"], "ilce": ["ordu/fatsa"], "id": ["0123…"]}  — ACİL DÜĞME (araclar/acil.py): bu ilan/ilçe/il uygulamada ANINDA gizlenir
//   (geriye dönük) üst düzey "ilce_sayfasinda_il_geneli", "bugun_bossa_dunu_goster"
// YAYIN İMZASI (25.10.2026): açık anahtar listesi doluysa dosya imzasız/bozuk/bayat ise UYGULANMAZ (cihazdaki son iyi değer kalır).
// Son iyi değer telefonda saklanır (çevrimdışı/hata = son değer). Açılışta yüklenir; ilanlar her yenilendiğinde tazelenir.
import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import 'anahtar.dart';
import 'imza.dart';

const String uzakAyarUrl = 'https://veri.kimincenazesi.com/ayarlar.json';

class UzakAyar {
  UzakAyar._();

  static Map<String, dynamic> _yazilar = {};
  static Map<String, dynamic> _kaliplar = {};
  static Map<String, dynamic> _listeler = {};
  static Map<String, dynamic> _haritalar = {};
  static Map<String, dynamic> _bayraklar = {};
  static Map<String, dynamic> _sayilar = {};
  static Map<String, Set<String>> _acil = {};

  /// Acil gizleme listesi (il / ilce / id -> değerler). Boş = hiçbir şey gizli değil.
  static Map<String, Set<String>> get acilGizle => _acil;

  /// İlçe sayfasında ilin ilçesiz/nakil ilanlarını "İl geneli" başlığıyla göster (varsayılan: GÖSTERME — sahibi 16.10.2026).
  static bool get ilceSayfasindaIlGeneli => bayrak('ilce_sayfasinda_il_geneli', false);
  static set ilceSayfasindaIlGeneli(bool v) => _bayraklar['ilce_sayfasinda_il_geneli'] = v;

  /// Bugün boşsa "Dün (…)" ilanlarını göster (URUN §57; varsayılan: GÖSTERME — sahibi 16.10.2026).
  static bool get bugunBossaDunuGoster => bayrak('bugun_bossa_dunu_goster', false);
  static set bugunBossaDunuGoster(bool v) => _bayraklar['bugun_bossa_dunu_goster'] = v;

  static String yazi(String k, String varsayilan) {
    final v = _yazilar[k];
    return v is String ? v : varsayilan;
  }

  /// Uzak kalıp varsa {0},{1}… yer tutucuları değerlerle doldurulur; yoksa uygulamadaki hazır metin döner.
  static String kalip(String k, String varsayilan, List<String> degerler) {
    final v = _kaliplar[k];
    if (v is! String) return varsayilan;
    var s = v;
    for (var i = 0; i < degerler.length; i++) {
      s = s.replaceAll('{$i}', degerler[i]);
    }
    return s;
  }

  static List<String> liste(String k, List<String> varsayilan) {
    final v = _listeler[k];
    if (v is List && v.every((x) => x is String)) return v.cast<String>();
    return varsayilan;
  }

  static List<List<String>> ikiliListe(String k, List<List<String>> varsayilan) {
    final v = _listeler[k];
    if (v is List && v.every((x) => x is List && x.every((y) => y is String))) {
      return [for (final x in v) (x as List).cast<String>()];
    }
    return varsayilan;
  }

  static Map<String, String> harita(String k, Map<String, String> varsayilan) {
    final v = _haritalar[k];
    if (v is Map && v.values.every((x) => x is String)) return {...varsayilan, ...v.cast<String, String>()};
    return varsayilan;
  }

  static bool bayrak(String k, bool varsayilan) {
    final v = _bayraklar[k];
    return v is bool ? v : varsayilan;
  }

  static int sayi(String k, int varsayilan) {
    final v = _sayilar[k];
    return v is num ? v.toInt() : varsayilan;
  }

  /// Saniye cinsinden uzak süre; anahtar yoksa varsayılan.
  static Duration sure(String k, Duration varsayilan) {
    final v = _sayilar[k];
    return v is num ? Duration(milliseconds: (v * 1000).round()) : varsayilan;
  }

  static Map<String, dynamic> _harita(Object? v) => v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

  static void uygula(Map j) {
    _yazilar = _harita(j['yazilar']);
    _kaliplar = _harita(j['kaliplar']);
    _listeler = _harita(j['listeler']);
    _haritalar = _harita(j['haritalar']);
    _bayraklar = _harita(j['bayraklar']);
    _sayilar = _harita(j['sayilar']);
    final a = _harita(j['acil_gizle']);
    _acil = {
      for (final k in const ['il', 'ilce', 'id'])
        if (a[k] is List && (a[k] as List).isNotEmpty) k: {for (final x in a[k] as List) x.toString()}
    };
    for (final k in const ['ilce_sayfasinda_il_geneli', 'bugun_bossa_dunu_goster']) {
      if (j[k] is bool && !_bayraklar.containsKey(k)) _bayraklar[k] = j[k];
    }
  }

  /// Testler için: her şeyi varsayılana döndür.
  static void sifirla() {
    uygula(const {});
    _son = null;
    _imza = '';
  }

  static const _anahtar = 'uzak_ayar';
  static DateTime? _son;
  static String _imza = '';

  /// Telefonda saklı son değeri yükler (açılışta, ağdan önce).
  static Future<void> yerelYukle({ImzaDogrulayici? imza}) async {
    try {
      final p = await SharedPreferences.getInstance();
      final s = p.getString(_anahtar);
      final d = imza ?? ImzaDogrulayici.varsayilan();
      // saklı kopya da imzalı olmalı (imzasız sürümden kalan kopya kullanılmaz); yaş sınırı yok: çevrimdışı son iyi değer
      if (s != null && d.kabul('ayarlar.json', Uint8List.fromList(utf8.encode(s)), yasKontrol: false)) {
        final j = jsonDecode(s);
        if (j is Map) {
          uygula(j);
          _imza = s;
        }
      }
    } catch (_) {}
  }

  /// Sunucudan tazeler; içerik değiştiyse true. En çok dakikada bir istek.
  static Future<bool> tazele(http.Client istemci, {ImzaDogrulayici? imza}) async {
    final simdi = DateTime.now();
    if (_son != null && simdi.difference(_son!) < const Duration(minutes: 1)) return false;
    _son = simdi;
    try {
      final r = await istemci
          .get(Uri.parse('$uzakAyarUrl?k=${simdi.millisecondsSinceEpoch ~/ 60000}'), headers: {...kcBasliklar(), 'Accept': 'application/json'})
          .timeout(const Duration(seconds: 4));
      if (r.statusCode != 200) return false;
      if (!(imza ?? ImzaDogrulayici.varsayilan()).kabul('ayarlar.json', r.bodyBytes)) return false; // imzasız/bozuk/bayat ayar UYGULANMAZ
      final govde = utf8.decode(r.bodyBytes);
      final j = jsonDecode(govde);
      if (j is! Map) return false;
      if (govde == _imza) return false;
      uygula(j);
      _imza = govde;
      final p = await SharedPreferences.getInstance();
      await p.setString(_anahtar, govde);
      return true;
    } catch (_) {
      return false;
    }
  }
}
