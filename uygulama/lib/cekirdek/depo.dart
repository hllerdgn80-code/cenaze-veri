// Cihaz deposu (shared_preferences). Hiçbir veri cihaz dışına gönderilmez.
// Anahtarlar: il, ilce, tema, kayit (Sayfam), sayac, cins, izin, onbellek_<il>.
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

  // ---- Günlük bildirim (§36) ----
  // izin: true = açık · false = kapalı (ayardan kapatıldı / sistem izni verilmedi) · null = henüz cevap yok.
  bool? get bildirimIzni => _p.getBool('izin');
  Future<void> bildirimIzniKaydet(bool evet) => _p.setBool('izin', evet);

  /// "Şimdi değil" denen gün (ISO); 7 gün yeniden sorulmaz
  String? get bildirimErtele => _p.getString('izin_ertele');
  Future<void> bildirimErteleKaydet(String gun) => _p.setString('izin_ertele', gun);

  /// Arka plan görevi ayrı izolatta çalışır: diskteki son değerleri okumak için
  Future<void> yenile() => _p.reload();

  /// Gönderilen bildirimlerin kaydı: sabah/öğle bildirimi hangi gün gitti, sabahta hangi ilanlar vardı
  String? get bildirimSabahGunu => _p.getString('bil_sabah');
  String? get bildirimOgleGunu => _p.getString('bil_ogle');
  Set<String> get bildirimGorulen => (_p.getStringList('bil_gorulen') ?? const <String>[]).toSet();

  Future<void> bildirimSabahKaydet(String gun, Set<String> ilanlar) async {
    await _p.setString('bil_sabah', gun);
    await _p.setStringList('bil_gorulen', ilanlar.toList());
  }

  Future<void> bildirimOgleKaydet(String gun) => _p.setString('bil_ogle', gun);

  // ---- Din görevlisi oturumu (URUN-TASLAGI §37) ----
  // Belirteç yalnız ilan paylaşma yetkisi verir (180 gün); kart fotoğrafı ve kod cihazda HİÇ saklanmaz.
  String? get gorevliOturum {
    final v = _p.getString('gorevli_oturum');
    return (v == null || v.isEmpty) ? null : v;
  }

  Future<void> gorevliOturumKaydet(String? t) async {
    if (t == null) {
      await _p.remove('gorevli_oturum');
      await _p.remove('gorevli_yer');
    } else {
      await _p.setString('gorevli_oturum', t);
    }
  }

  /// Hesabın il/ilçesi (otomatik ilanı düzeltme yetkisi için; URUN §49). Panel her açılışta günceller, çıkışta silinir.
  ({String il, String ilce})? get gorevliYer {
    final v = _p.getString('gorevli_yer');
    if (v == null) return null;
    final i = v.indexOf('|');
    return i < 0 ? null : (il: v.substring(0, i), ilce: v.substring(i + 1));
  }

  Future<void> gorevliYerKaydet(String il, String ilce) => _p.setString('gorevli_yer', '$il|$ilce');

  /// Giriş yapılan Diyanet kullanıcı adı (yalnız cihazda; KVKK kabulü "hesap değişti mi" için)
  String? get gorevliKullanici => _p.getString('gorevli_kullanici');
  Future<void> gorevliKullaniciKaydet(String k) => _p.setString('gorevli_kullanici', k);

  /// KVKK aydınlatma kabulü (URUN §50): "kullanıcı|ISO tarih". Hesap kullanıcı adı değişmişse kabul geçersiz sayılır.
  String? get gorevliKvkkKabul => _p.getString('gorevli_kvkk');
  bool gorevliKvkkTamam() {
    final v = gorevliKvkkKabul;
    if (v == null) return false;
    final i = v.indexOf('|');
    return i >= 0 && v.substring(0, i) == (gorevliKullanici ?? '');
  }

  Future<void> gorevliKvkkKaydet(String tarih) => _p.setString('gorevli_kvkk', '${gorevliKullanici ?? ''}|$tarih');

  /// Son bilinen hesap durumu (onayli | kontrolde | silindi): arka plan işi yalnız "kontrolde" iken sunucuya bakar
  String? get gorevliDurumSon => _p.getString('gorevli_durum');
  Future<void> gorevliDurumKaydet(String? d) => d == null ? _p.remove('gorevli_durum') : _p.setString('gorevli_durum', d);

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
