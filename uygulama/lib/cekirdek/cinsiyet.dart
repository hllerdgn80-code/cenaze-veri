// Merhum / merhume kuralı (METIN-SOZLUGU §9, URUN-TASLAGI §28): asla yanlış cinsiyet yazılmaz.
// Sıra: şehit → bebek → kayıttaki cinsiyet → gömülü ad listesi (adlar.json) → kullanıcının seçimi → bilinmiyor (nötr).
import 'ilan.dart';
import 'yardimci.dart';

/// 'e' erkek · 'k' kadın · 's' şehit · 'b' bebek · null bilinmiyor
class CinsiyetCozucu {
  final Set<String> erkek;
  final Set<String> kadin;

  CinsiyetCozucu({required Iterable<String> erkek, required Iterable<String> kadin})
      : erkek = erkek.toSet(),
        kadin = kadin.toSet();

  factory CinsiyetCozucu.fromJson(Map<String, dynamic> j) => CinsiyetCozucu(
        erkek: (j['e'] as List? ?? const []).map((x) => x.toString()),
        kadin: (j['k'] as List? ?? const []).map((x) => x.toString()),
      );

  /// Yalnız ad listesine göre: iki listede de varsa ya da hiçbirinde yoksa null
  String? addan(String adSoyad) {
    final parca = adSoyad.trim().split(RegExp(r'\s+'));
    if (parca.isEmpty || parca.first.isEmpty) return null;
    final ilk = trBuyuk(parca.first.substring(0, 1)) + trKucuk(parca.first.substring(1));
    final e = erkek.contains(ilk), k = kadin.contains(ilk);
    if (e && !k) return 'e';
    if (k && !e) return 'k';
    return null;
  }

  /// Kayıt için çözüm; [secim] kullanıcının daha önce Sayfam'da yaptığı seçim
  String? coz(Ilan r, {String? secim}) {
    if (r.sehit) return 's';
    if (r.bebek) return 'b';
    if (r.cinsiyet != null) return r.cinsiyet;
    final a = addan(r.adSoyad);
    if (a != null) return a;
    return secim;
  }
}

/// Sayaç türleri (Sayfam, 6 satır — URUN-TASLAGI §31)
const List<List<String>> sayacTurleri = [
  ['f', '1 Fâtiha okudum'],
  ['i', '3 İhlâs ve 1 Fâtiha okudum'],
  ['y', '1 Yâsîn okudum'],
  ['d', '1 dua okudum'],
  ['h', '1 Kur’ân-ı Kerîm hatmi okudum'],
  ['t', '1 Kelime-i Tevhid hatmi okudum'],
];

/// "Merhuma 1 Fâtiha okudum" · "Merhumeye …" · "Şehidimize …" · "Bebeğimize …" · nötr "1 Fâtiha okudum"
String sayacEtiket(String tur, String? cins) {
  final govde = sayacTurleri.firstWhere((x) => x[0] == tur, orElse: () => sayacTurleri.first)[1];
  final onek = switch (cins) {
    's' => 'Şehidimize ',
    'b' => 'Bebeğimize ',
    'e' => 'Merhuma ',
    'k' => 'Merhumeye ',
    _ => '',
  };
  return '$onek$govde';
}
