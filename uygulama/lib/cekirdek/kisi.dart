// Kaybettiklerimiz / Tarihte Bugün kişi kaydı (Wikidata, CC0). Kabir bilgisi gösterilmez.
// Tanıtım satırı prototip_yap.py → tanitim()/tanitim_g()/gorev_sirasi() kurallarının sade karşılığıdır.

class Kisi {
  final String ad;
  final String? vefatTarihi;
  final int? yas;
  final bool yasYaklasik;
  final String wikidataId;
  final int sitelink;
  final bool turk;
  final String? gorev; // "9. Cumhurbaşkanı" (yalnız cumhurbaşkanı/başbakan)
  final String tanitim;

  const Kisi({
    required this.ad,
    required this.wikidataId,
    this.vefatTarihi,
    this.yas,
    this.yasYaklasik = false,
    this.sitelink = 0,
    this.turk = false,
    this.gorev,
    this.tanitim = '',
  });

  String get yil => (vefatTarihi != null && vefatTarihi!.length >= 4) ? vefatTarihi!.substring(0, 4) : '–';

  factory Kisi.fromJson(Map<String, dynamic> j, {String? kategori}) {
    final gorev = gorevSirasi(j, kategori);
    final t = tanitimYap(j, enCok: kategori == 'sanatcilar' ? 3 : 1);
    return Kisi(
      ad: (j['ad'] ?? '').toString(),
      wikidataId: (j['wikidata_id'] ?? '').toString(),
      vefatTarihi: j['vefat_tarihi']?.toString(),
      yas: (j['vefat_yasi'] as num?)?.toInt(),
      yasYaklasik: j['vefat_yasi_yaklasik'] == true,
      sitelink: ((j['sitelink'] ?? j['sitelink_sayisi'] ?? 0) as num).toInt(),
      turk: j['turk'] == true,
      gorev: gorev,
      tanitim: gorev == null ? t : _gorevsiz(t, gorev),
    );
  }
}

String _buyukIlk(String t) => t.isEmpty ? t : t.substring(0, 1).toUpperCase() + t.substring(1);

/// "Türk ressam" → "Ressam" (milliyet sıfatı yazılmaz; özel ad öbeklerine dokunulmaz)
String _turkSil(String t) {
  t = t.trim();
  if (t.startsWith('“')) return t;
  t = t.replaceAll(
      RegExp(r'(?<![\wçğıöşü])(?:[A-ZÇĞİÖŞÜ][\wçğıöşü]+-)?Türk[ -](?!Silahlı|Telekom|Hava|Dil|Tarih|Sinema|Giyim|müziği|Halk müziği|Sanat müziği)'),
      '');
  t = t.replaceAll(RegExp(r'^[ ,]+|[ ,]+$'), '');
  return _buyukIlk(t);
}

Set<String> _kok(String t) =>
    RegExp(r'\p{L}{4,}', unicode: true).allMatches(t).map((m) {
      final w = m.group(0)!.toLowerCase();
      return w.length > 5 ? w.substring(0, 5) : w;
    }).toSet();

/// Meslek (sanatçılarda en çok 3) · neden tanınır
String tanitimYap(Map<String, dynamic> x, {int enCok = 1}) {
  final ham = x['meslek'];
  final List<String> parcalar = ham is String
      ? ham.split(',')
      : (ham is List ? ham.map((e) => e.toString()).toList() : <String>[]);
  final m = <String>[];
  for (final p in parcalar) {
    final t = p.trim().toLowerCase();
    if (t.isNotEmpty && !m.contains(t)) m.add(t);
  }
  final secili = m.take(enCok).toList();
  var ms = _buyukIlk(secili.join(', '));

  String neden = '';
  final no = (x['neden_onemli'] ?? '').toString();
  for (var t in no.split(RegExp(r';|(?<!\d)\.\s+(?=[A-ZÇĞİÖŞÜ])'))) {
    t = t.replaceAll(RegExp(r'\s*\(.*?\)'), '').trim();
    t = t.replaceAll(RegExp(r'^[ .]+|[ .]+$'), '');
    if (t.isEmpty || t.contains('Vikipedi') || RegExp(r'\d+ dilde').hasMatch(t) || t.startsWith('Ödül')) continue;
    t = t.replaceFirst(RegExp(r'^(Görev|Önemli eserleri?):\s*'), '');
    if (t.toLowerCase() == ms.toLowerCase() || secili.contains(t.toLowerCase())) continue;
    neden = t;
    break;
  }
  if (neden.isEmpty && x['aciklama_kaynak'] == 'wikidata_tr') {
    final a = (x['aciklama'] ?? '').toString().replaceAll(RegExp(r'\s*\(.*?\)\s*'), ' ').trim();
    if (a.isNotEmpty && !RegExp(r'^Türk (politikacı|siyasetçi)$').hasMatch(a)) neden = a;
  }
  ms = _turkSil(ms);
  neden = _buyukIlk(_turkSil(neden));
  if (neden.isNotEmpty && (neden.toLowerCase() == ms.toLowerCase() || _kok(ms).intersection(_kok(neden)).isNotEmpty)) {
    neden = '';
  }
  return [ms, neden].where((t) => t.isNotEmpty).join(' · ');
}

/// "9. Cumhurbaşkanı" / "20. Başbakan" (yalnız bu iki kategoride)
String? gorevSirasi(Map<String, dynamic> x, String? k) {
  final ad = {'cumhurbaskanlari': 'Cumhurbaşkanı', 'basbakanlar': 'Başbakan'}[k];
  if (ad == null) return null;
  final s = RegExp(r'\d+').firstMatch((x['sira'] ?? '').toString());
  if (s != null) return '${int.parse(s.group(0)!)}. $ad';
  final metin = '${x['aciklama'] ?? ''} ${x['neden_onemli'] ?? ''}';
  final r = RegExp(r"(\d+)\.\s*(?:Türkiye(?: Cumhuriyeti)?'?n?i?n? )?" +
          (k == 'cumhurbaskanlari' ? '[Cc]umhurbaşkan' : '[Bb]aşbakan'))
      .firstMatch(metin);
  return r == null ? null : '${int.parse(r.group(1)!)}. $ad';
}

/// Tanıtım, üstteki görev satırının kelimelerini tekrar etmez
String _gorevsiz(String t, String g) {
  final gk = RegExp(r'[\p{L}\p{N}]+', unicode: true)
      .allMatches(g)
      .map((m) => m.group(0)!)
      .where((w) => int.tryParse(w) == null)
      .map((w) => w.toLowerCase())
      .toSet();
  final kalan = <String>[];
  for (final p in t.split(' · ')) {
    if (p.isEmpty) continue;
    if (RegExp(r'^\d+\. (Türkiye )?(Cumhurbaşkanı|[Bb]aşbakanı?)').hasMatch(p)) continue;
    final kelimeler = RegExp(r'[\p{L}\p{N}]+', unicode: true).allMatches(p).map((m) => m.group(0)!.toLowerCase());
    if (kelimeler.any((w) => gk.any((g2) => w.startsWith(g2)))) continue;
    kalan.add(p);
  }
  return kalan.join(' · ');
}
