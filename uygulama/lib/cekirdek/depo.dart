// Cihaz deposu (shared_preferences). Hiçbir veri cihaz dışına gönderilmez.
// Anahtarlar: il, ilce, tema, kayit (Sayfam), sayac, cins, izin, onbellek_<il>.
import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
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
      // çıkış (URUN §53/§50a): oturum, parola, görev bilgisi ve KVKK kabul kaydı cihazdan silinir
      for (final k in ['gorevli_oturum', 'gorevli_yer', 'gorevli_kullanici', 'gorevli_durum', 'gorevli_kvkk', 'gorevli_sorumluluk', ..._pinAnahtarlar]) {
        await _p.remove(k);
      }
    } else {
      await _p.setString('gorevli_oturum', t);
    }
  }

  // ---- Panel parolası (URUN §53): 4 rakam, cihazda sha256(tuz + parola) karması; düz parola saklanmaz ----
  static const _pinAnahtarlar = ['gorevli_pin', 'gorevli_pin_tuz', 'gorevli_pin_yanlis', 'gorevli_pin_kilit'];
  /// 5 yanlışta bekleme (sn)
  static const pinKilitSn = 60;
  static const pinEnCok = 5;

  bool get gorevliPinVar => (_p.getString('gorevli_pin') ?? '').isNotEmpty;

  static String pinKarma(String tuz, String pin) => sha256.convert(utf8.encode('$tuz|$pin')).toString();

  Future<void> gorevliPinKur(String pin) async {
    final r = Random.secure();
    final tuz = List.generate(16, (_) => r.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
    await _p.setString('gorevli_pin_tuz', tuz);
    await _p.setString('gorevli_pin', pinKarma(tuz, pin));
    await _p.remove('gorevli_pin_yanlis');
    await _p.remove('gorevli_pin_kilit');
  }

  bool gorevliPinDogru(String pin) {
    final k = _p.getString('gorevli_pin');
    final t = _p.getString('gorevli_pin_tuz');
    return k != null && t != null && k == pinKarma(t, pin);
  }

  /// Kilidin kalan saniyesi (0 = kilit yok). Süre dolunca sayaç sıfırlanır.
  int gorevliPinKilitKalanSn([DateTime? simdi]) {
    final ms = _p.getInt('gorevli_pin_kilit');
    if (ms == null) return 0;
    final kalan = ((ms - (simdi ?? DateTime.now()).millisecondsSinceEpoch) / 1000).ceil();
    return kalan > 0 ? kalan : 0;
  }

  /// Yanlış parola kaydı: 5. yanlışta 1 dk kilit; döner: kalan hak (kilitlendiyse 0)
  Future<int> gorevliPinYanlisKaydet([DateTime? simdi]) async {
    final n = (_p.getInt('gorevli_pin_yanlis') ?? 0) + 1;
    if (n >= pinEnCok) {
      await _p.setInt('gorevli_pin_kilit', (simdi ?? DateTime.now()).add(const Duration(seconds: pinKilitSn)).millisecondsSinceEpoch);
      await _p.remove('gorevli_pin_yanlis');
      return 0;
    }
    await _p.setInt('gorevli_pin_yanlis', n);
    return pinEnCok - n;
  }

  Future<void> gorevliPinSayacSifirla() async {
    await _p.remove('gorevli_pin_yanlis');
    await _p.remove('gorevli_pin_kilit');
  }

  /// Hesabın il/ilçesi ve görev yeri (otomatik ilanı düzeltme yetkisi için; URUN §49/§49a). Panel her açılışta günceller, çıkışta silinir.
  ({String il, String ilce, String gorevYeri})? get gorevliYer {
    final v = _p.getString('gorevli_yer');
    if (v == null) return null;
    final p = v.split('|');
    return p.length < 2 ? null : (il: p[0], ilce: p[1], gorevYeri: p.length > 2 ? p.sublist(2).join('|') : '');
  }

  Future<void> gorevliYerKaydet(String il, String ilce, [String gorevYeri = '']) => _p.setString('gorevli_yer', '$il|$ilce|$gorevYeri');

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

  /// Sorumluluk uyarısı kabulü (URUN §54): giriş başına bir kez; çıkışta silinir
  String? get gorevliSorumlulukKabul => _p.getString('gorevli_sorumluluk');
  bool gorevliSorumlulukTamam() => (gorevliSorumlulukKabul ?? '').isNotEmpty;
  Future<void> gorevliSorumlulukKaydet(String tarih) => _p.setString('gorevli_sorumluluk', tarih);
  Future<void> gorevliSorumlulukSil() => _p.remove('gorevli_sorumluluk');
  Future<void> gorevliKvkkSil() => _p.remove('gorevli_kvkk');
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
