// Türkçe metin ve tarih yardımcıları (prototipteki sablon.html işlevlerinin karşılığı).
// Dart'ın toLowerCase/toUpperCase işlevleri Türkçe İ/ı harflerini bilmez; burada elle çevrilir.

const List<String> aylar = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
];
// Pazar = 0 (prototipteki GUNU/GUNK dizileriyle aynı sıra)
const List<String> gunAdlari = [
  'Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi',
];
const List<String> gunKisa = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'];

/// Türkçe küçük harf: I → ı, İ → i
String trKucuk(String s) {
  final b = StringBuffer();
  for (final r in s.runes) {
    final c = String.fromCharCode(r);
    if (c == 'I') {
      b.write('ı');
    } else if (c == 'İ') {
      b.write('i');
    } else {
      b.write(c.toLowerCase());
    }
  }
  // "İ".toLowerCase() bazı ortamlarda "i̇" (i + birleşik nokta) verir; temizlenir
  return b.toString().replaceAll('i̇', 'i');
}

/// Türkçe büyük harf: i → İ, ı → I
String trBuyuk(String s) {
  final b = StringBuffer();
  for (final r in s.runes) {
    final c = String.fromCharCode(r);
    if (c == 'i') {
      b.write('İ');
    } else if (c == 'ı') {
      b.write('I');
    } else {
      b.write(c.toUpperCase());
    }
  }
  return b.toString();
}

/// Arama için sadeleştirme: küçük harf + Türkçe harfler ASCII'ye
String sade(String s) {
  const m = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'â': 'a', 'î': 'i', 'û': 'u'};
  final k = trKucuk(s);
  final b = StringBuffer();
  for (final r in k.runes) {
    final c = String.fromCharCode(r);
    b.write(m[c] ?? c);
  }
  return b.toString();
}

/// İl adından veri klasörü kodu: "Şanlıurfa" → "sanliurfa", "İstanbul" → "istanbul"
String ilKodu(String il) => sade(il).replaceAll(RegExp(r'[^a-z0-9]'), '');

/// Türkçe bulunma eki: Kars’ta, Ünye’de, Aybastı’da
String ek(String ad) {
  if (ad.isEmpty) return ad;
  final k = trKucuk(ad);
  const unluler = 'aeıioöuüâîû';
  String v = 'a';
  for (int i = k.length - 1; i >= 0; i--) {
    if (unluler.contains(k[i])) {
      v = k[i];
      break;
    }
  }
  final son = k[k.length - 1];
  final sessiz = 'çfhkpsşt'.contains(son) ? 't' : 'd';
  final unlu = 'eiöüî'.contains(v) ? 'e' : 'a';
  return '$ad’$sessiz$unlu';
}

/// Her sözcüğün ilk harfi büyük; "Mez." → "Mezarlığı"
String baslikHarf(String? s) {
  if (s == null || s.isEmpty) return '';
  var t = s.replaceAllMapped(RegExp(r'\.(?=[^\s\d])'), (m) => '. ');
  t = trKucuk(t)
      .split(' ')
      .map((w) => w.isEmpty ? w : trBuyuk(w.substring(0, 1)) + w.substring(1))
      .join(' ');
  return t.replaceAllMapped(RegExp(r'(^|\s)Mez\.(?=\s|$)'), (m) => '${m.group(1)}Mezarlığı');
}

/// Yalnız ilk harf büyük
String cumleHarf(String? s) {
  if (s == null || s.isEmpty) return '';
  final k = trKucuk(s);
  return trBuyuk(k.substring(0, 1)) + k.substring(1);
}

/// "2026-10-08" → DateTime (UTC, gün hesabı için)
DateTime? gunCoz(String? t) {
  if (t == null) return null;
  final m = RegExp(r'^(\d{4})-(\d{2})-(\d{2})').firstMatch(t);
  if (m == null) return null;
  return DateTime.utc(int.parse(m.group(1)!), int.parse(m.group(2)!), int.parse(m.group(3)!));
}

String _iki(int n) => n.toString().padLeft(2, '0');

String gunYaz(DateTime d) => '${d.year}-${_iki(d.month)}-${_iki(d.day)}';

/// Türkiye saatiyle bugün (UTC+3, yaz saati yok)
String bugunTr([DateTime? simdi]) {
  final s = (simdi ?? DateTime.now()).toUtc().add(const Duration(hours: 3));
  return gunYaz(s);
}

/// Türkiye saatiyle "09:02"
String saatTr(DateTime anUtc) {
  final s = anUtc.toUtc().add(const Duration(hours: 3));
  return '${_iki(s.hour)}:${_iki(s.minute)}';
}

String gunEkle(String t, int n) {
  final d = gunCoz(t);
  if (d == null) return t;
  return gunYaz(d.add(Duration(days: n)));
}

/// Pazar = 0
int haftaGunu(String t) {
  final d = gunCoz(t);
  if (d == null) return 0;
  return d.weekday % 7;
}

/// "2026-10-08" → "8 Ekim 2026" (kisa: "8 Ekim"); "2026" ve "2026-10" biçimleri de desteklenir
String tarih(String? t, {bool kisa = false}) {
  if (t == null || t.isEmpty) return '';
  final p = t.split('-').map((x) => int.tryParse(x) ?? 0).toList();
  if (p.length == 1) return '${p[0]}';
  if (p.length == 2) return '${aylar[(p[1] - 1).clamp(0, 11)]} ${p[0]}';
  final s = '${p[2]} ${aylar[(p[1] - 1).clamp(0, 11)]}';
  return kisa ? s : '$s ${p[0]}';
}

/// "8 Ekim Perşembe"
String tarihGun(String t) => '${tarih(t, kisa: true)} ${gunAdlari[haftaGunu(t)]}';

/// Türkçe alfabe sırasıyla karşılaştırma (localeCompare('tr') karşılığı)
int trKarsilastir(String a, String b) {
  const abc = 'abcçdefgğhıijklmnoöprsştuüvyzâîû';
  final x = trKucuk(a), y = trKucuk(b);
  final n = x.length < y.length ? x.length : y.length;
  for (int i = 0; i < n; i++) {
    final ix = abc.indexOf(x[i]), iy = abc.indexOf(y[i]);
    final kx = ix < 0 ? 1000 + x.codeUnitAt(i) : ix;
    final ky = iy < 0 ? 1000 + y.codeUnitAt(i) : iy;
    if (kx != ky) return kx - ky;
  }
  return x.length - y.length;
}
