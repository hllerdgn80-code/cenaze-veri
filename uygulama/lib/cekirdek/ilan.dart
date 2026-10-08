// Cenaze ilanı modeli. Veri: <veri_kok>/<il>/son7gun.json (yayın süzgecinden geçmiş alanlar).
// KAPI: uygulama yalnız aşağıdaki alanları okur ve saklar; kaynak_ad, kaynak_url, anne_baba, ham
// gibi alanlar gelse bile modele ALINMAZ, ekranda gösterilmez, cihazda saklanmaz (URUN-TASLAGI §16.5, §28).
import 'yardimci.dart';

class Ilan {
  final String id;
  final String? il;
  final String? ilce;
  final String? mahalle;
  final String adSoyad;
  final int? yas;
  final String? vefatTarihi;
  final String? definYeri;
  final String? definZamani;
  final String? namazTarihi;
  final String? namazYeriVakti;
  final String? listeTarihi;
  final String? ilDisiIl;
  final String? ilDisiIlce;
  final String? cinsiyet; // 'e' | 'k' | null (kaynakta yazılıysa)
  final bool sehit;
  final String? rutbe;
  final String? toren;
  final bool bebek;
  final bool aile; // yakını paylaştı

  const Ilan({
    required this.id,
    required this.adSoyad,
    this.il,
    this.ilce,
    this.mahalle,
    this.yas,
    this.vefatTarihi,
    this.definYeri,
    this.definZamani,
    this.namazTarihi,
    this.namazYeriVakti,
    this.listeTarihi,
    this.ilDisiIl,
    this.ilDisiIlce,
    this.cinsiyet,
    this.sehit = false,
    this.rutbe,
    this.toren,
    this.bebek = false,
    this.aile = false,
  });

  static String? _s(dynamic v) {
    if (v == null) return null;
    final t = v.toString().trim();
    return t.isEmpty ? null : t;
  }

  static int? _i(dynamic v) {
    if (v is int) return v;
    if (v is num) return v.toInt();
    if (v is String) return int.tryParse(v);
    return null;
  }

  static String? _cins(dynamic v) {
    switch (v) {
      case 'Erkek':
      case 'erkek':
      case 'e':
        return 'e';
      case 'Kadın':
      case 'kadın':
      case 'k':
        return 'k';
    }
    return null;
  }

  /// JSON kaydından ilan; ad yoksa null (kart çizilmez)
  static Ilan? fromJson(Map<String, dynamic> j) {
    final ad = _s(j['ad_soyad']);
    if (ad == null) return null;
    final disi = j['il_disi_defin'];
    return Ilan(
      id: _s(j['id']) ?? '${ad}_${_s(j['vefat_tarihi']) ?? ''}',
      adSoyad: ad,
      il: _s(j['il']),
      ilce: _s(j['ilce']),
      mahalle: _s(j['mahalle']),
      yas: _i(j['yas']),
      vefatTarihi: _s(j['vefat_tarihi']),
      definYeri: _s(j['defin_yeri']),
      definZamani: _s(j['defin_zamani']),
      namazTarihi: _s(j['namaz_tarihi']),
      namazYeriVakti: _s(j['namaz_yeri_vakti']),
      listeTarihi: _s(j['liste_tarihi']),
      ilDisiIl: disi is Map ? _s(disi['il']) : null,
      ilDisiIlce: disi is Map ? _s(disi['ilce']) : null,
      cinsiyet: _cins(j['cinsiyet']),
      sehit: j['sehit'] == true,
      rutbe: _s(j['rutbe']),
      toren: _s(j['toren']),
      bebek: j['bebek'] == true,
      aile: j['aile'] == true || j['kaynak_turu'] == 'aile',
    );
  }

  /// Cihazda saklanan biçim (yalnız gösterilen alanlar)
  Map<String, dynamic> toJson() => {
        'id': id,
        'ad_soyad': adSoyad,
        'il': il,
        'ilce': ilce,
        'mahalle': mahalle,
        'yas': yas,
        'vefat_tarihi': vefatTarihi,
        'defin_yeri': definYeri,
        'defin_zamani': definZamani,
        'namaz_tarihi': namazTarihi,
        'namaz_yeri_vakti': namazYeriVakti,
        'liste_tarihi': listeTarihi,
        'il_disi_defin': ilDisiIl == null ? null : {'il': ilDisiIl, 'ilce': ilDisiIlce},
        'cinsiyet': cinsiyet,
        'sehit': sehit,
        'rutbe': rutbe,
        'toren': toren,
        'bebek': bebek,
        'aile': aile,
      };

  /// TEK KAYNAK: tarih şeridi gruplaması VE kart üst etiketi bu günü kullanır
  /// (cenaze namazı günü; yoksa defin günü; o da yoksa liste tarihi).
  String get cenazeGunu {
    final dz = definZamani ?? '';
    if (namazTarihi != null) return namazTarihi!;
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(dz)) return dz;
    return listeTarihi ?? vefatTarihi ?? '';
  }

  /// "Öğle", "İkindi", … (namaz metninden)
  String get vakit => vakitBul(namazYeriVakti);

  /// Kart üst etiketi: "Cenaze · 8 Ekim · Öğle" (şehitte "Cenaze töreni · …")
  String get etiket {
    final parcalar = <String>[sehit ? 'Cenaze töreni' : 'Cenaze', tarih(cenazeGunu, kisa: true), vakit];
    return parcalar.where((x) => x.isNotEmpty).join(' · ');
  }

  /// [vakit metni, cami] — "İkindi Namazını Müteakip-ORTAKÖY CAMİİ" → ["İkindi namazını müteakip", "Ortaköy Camii"]
  List<String> get namazParcalari => namazAyir(namazYeriVakti);
}

String vakitBul(String? s) {
  final m = RegExp(r'(sabah|öğle|ikindi|akşam|yatsı|cuma)').firstMatch(trKucuk(s ?? ''));
  return m == null ? '' : cumleHarf(m.group(1));
}

List<String> namazAyir(String? s) {
  if (s == null || s.isEmpty) return ['', ''];
  final i = s.indexOf('-');
  if (i < 0) return [cumleHarf(s), ''];
  return [cumleHarf(s.substring(0, i).trim()), baslikHarf(s.substring(i + 1).trim())];
}

/// Bir ilin son 7 günlük verisi
class IlVerisi {
  final String il;
  final bool kaynakli; // false: bu il için yayımlanan dosya yok (kaynaksız il ekranı)
  final Map<String, List<Ilan>> ilceler;
  final List<Ilan> genel; // ilçesi belirtilmemiş + il dışı defin
  final String? guncelleme;

  const IlVerisi({
    required this.il,
    required this.kaynakli,
    this.ilceler = const {},
    this.genel = const [],
    this.guncelleme,
  });

  static List<Ilan> _liste(dynamic v) {
    if (v is! List) return [];
    return v.whereType<Map>().map((m) => Ilan.fromJson(Map<String, dynamic>.from(m))).whereType<Ilan>().toList();
  }

  factory IlVerisi.fromJson(String il, Map<String, dynamic> j) {
    final ilc = <String, List<Ilan>>{};
    final ham = j['ilceler'];
    if (ham is Map) {
      ham.forEach((k, v) => ilc[k.toString()] = _liste(v));
    }
    return IlVerisi(
      il: il,
      kaynakli: true,
      ilceler: ilc,
      genel: [..._liste(j['ilce_belirsiz']), ..._liste(j['il_disi'])],
      guncelleme: j['guncelleme']?.toString(),
    );
  }

  /// Seçili ilçenin (ilce == null: tüm ilçeler) kayıtları, ilçe adına göre
  Map<String, List<Ilan>> secili(String? ilce) {
    if (ilce == null) return ilceler;
    return {ilce: ilceler[ilce] ?? const []};
  }

  /// Bir günde ilan var mı (tarih şeridindeki nokta)
  bool gunDolu(String? ilce, String gun) {
    for (final l in secili(ilce).values) {
      if (l.any((r) => r.cenazeGunu == gun)) return true;
    }
    return genel.any((r) => r.cenazeGunu == gun);
  }

  /// Tüm kayıtlar içinde kimlikle arama
  Ilan? bul(String id) {
    for (final l in ilceler.values) {
      for (final r in l) {
        if (r.id == id) return r;
      }
    }
    for (final r in genel) {
      if (r.id == id) return r;
    }
    return null;
  }
}
