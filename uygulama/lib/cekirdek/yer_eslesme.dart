// Görev yeri <-> ilanın camisi/mahallesi eşleşmesi (URUN §49a). AYNI MANTIK: okuyucu/ortak.py (yer_eslesir) ve deploy/aile-worker/src/yer.js.
const _ek = {'camii', 'camisi', 'cami', 'mescidi', 'mescit', 'mahallesi', 'mahalle', 'mah', 'koyu', 'koy'};
const _genel = {'merkez', 'yeni', 'eski', 'ulu', 'buyuk', 'kucuk', 'orta', 'asagi', 'yukari', 'cumhuriyet', 'ilce', 'belediye'};
const _tr = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'â': 'a', 'î': 'i', 'û': 'u'};

List<String> _sade(String? s) {
  final b = StringBuffer();
  for (final r in (s ?? '').runes) {
    var c = String.fromCharCode(r);
    if (c == 'I') {
      c = 'ı';
    } else if (c == 'İ') {
      c = 'i';
    } else {
      c = c.toLowerCase();
    }
    c = _tr[c] ?? c;
    b.write(RegExp(r'^[a-z0-9]$').hasMatch(c) ? c : ' ');
  }
  return b.toString().split(' ').where((w) => w.isNotEmpty && !_ek.contains(w)).toList();
}

/// "Korgan Merkez Camii" -> "korgan merkez"
String yerSade(String? s) => _sade(s).join(' ');

/// "ÖĞLE NAMAZINDAN SONRA - MERKEZ CAMİİ" -> "MERKEZ CAMİİ" (ilk '-' sonrası; yoksa boş)
String namazCami(String? nyv) {
  final s = nyv ?? '';
  final i = s.indexOf('-');
  return i < 0 ? '' : s.substring(i + 1).trim();
}

bool _son(List<String> x, List<String> y) => x.length <= y.length && y.sublist(y.length - x.length).join(' ') == x.join(' ');

/// Görev yeri ilanın camisi ya da mahallesi/köyü ile eşleşiyor mu? İlanda ikisi de yoksa false.
/// Eşit | biri diğerinin SON sözcük dizisi | 4+ harfli ortak ayırt edici sözcük (genel sözcükler ve [haric] [il/ilçe adı] hariç).
bool yerEslesir(String? gorevYeri, String? cami, String? mahalle, {String? haric}) {
  final g = _sade(gorevYeri);
  if (g.isEmpty) return false;
  final yasak = _sade(haric).toSet();
  for (final aday in [cami, mahalle]) {
    final a = _sade(aday);
    if (a.isEmpty) continue;
    if (_son(a, g) || _son(g, a)) return true;
    if (g.toSet().any((w) => w.length >= 4 && a.contains(w) && !_genel.contains(w) && !yasak.contains(w))) return true;
  }
  return false;
}
