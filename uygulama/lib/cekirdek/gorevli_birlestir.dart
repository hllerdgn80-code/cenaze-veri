// Din görevlisi ilanlarını cihazda il verisiyle birleştirir (URUN-TASLAGI §56).
// Kural veri hattıyla aynıdır (okuyucu/gorevli_birlestir.py, kapi.ayni_kisi): aynı id ya da aynı kişi (ad + cenaze günü ±2 gün + yaş ±1)
// zaten listedeyse listedeki kayıt kalır; `duzeltme_id` varsa o id'li otomatik kayıt çıkarılır, görevli kaydı yerine konur; yoksa eklenir.
import 'ilan.dart';
import 'yardimci.dart';

/// Worker yanıtı (`GET /gorevli/<il>.json` → {kayitlar:[…]}) → yalnız beyaz listedeki alanlarla [Ilan] listesi.
/// Penceresi dışındaki (cenaze günü bugün−7 … bugün+2) ve adsız/tarihsiz kayıtlar alınmaz (gorevli_al.py ile aynı).
List<Ilan> gorevliKayitlari(dynamic yanit, String bugun) {
  final ham = yanit is Map ? yanit['kayitlar'] : null;
  if (ham is! List) return const [];
  final alt = gunEkle(bugun, -7), ust = gunEkle(bugun, 2);
  final out = <Ilan>[];
  for (final m in ham.whereType<Map>()) {
    final j = Map<String, dynamic>.from(m);
    final nam = j['namaz_tarihi']?.toString() ?? '';
    final vef = j['vefat_tarihi']?.toString() ?? '';
    if (gunCoz(nam) == null || gunCoz(vef) == null) continue;
    if (nam.compareTo(alt) < 0 || nam.compareTo(ust) > 0) continue;
    final id = j['id']?.toString() ?? '';
    if (id.isEmpty) continue;
    j['id'] = 'gorevli-${id.length > 32 ? id.substring(0, 32) : id}';
    j['gorevli'] = true;
    j.remove('kaynak_turu');
    j.remove('aile');
    final i = Ilan.fromJson(j);
    if (i != null) out.add(i);
  }
  return out;
}

String _adAnahtar(String s) => sade(s).replaceAll(RegExp(r'\s+'), ' ').trim();

List<DateTime> _tarihler(Ilan i) {
  final out = <DateTime>[];
  for (final t in [i.vefatTarihi, i.namazTarihi, i.definZamani]) {
    final d = gunCoz(t);
    if (d != null) out.add(d);
  }
  if (out.isEmpty) {
    final d = gunCoz(i.listeTarihi);
    if (d != null) out.add(d);
  }
  return out;
}

/// Python `kapi.ayni_kisi` ile aynı kural
bool ayniKisi(Ilan a, Ilan b) {
  if (_adAnahtar(a.adSoyad) != _adAnahtar(b.adSoyad)) return false;
  if (a.yas != null && b.yas != null && (a.yas! - b.yas!).abs() > 1) return false;
  for (final x in _tarihler(a)) {
    for (final y in _tarihler(b)) {
      if (x.difference(y).inDays.abs() <= 2) return true;
    }
  }
  return false;
}

/// [v] içindeki kayıtlara [gorevli] kayıtlarını katar. Eklenecek/değişecek bir şey yoksa [v] aynen döner.
/// İlde yayımlanan dosya yoksa (kaynaksız il) görevli kaydı varsa il kaynaklı sayılır.
IlVerisi gorevliBirlestir(IlVerisi v, List<Ilan> gorevli) {
  if (gorevli.isEmpty) return v;
  final ilceler = {for (final e in v.ilceler.entries) e.key: List<Ilan>.of(e.value)};
  final genel = List<Ilan>.of(v.genel);
  var degisti = false;

  Iterable<Ilan> hepsi() sync* {
    for (final l in ilceler.values) {
      yield* l;
    }
    yield* genel;
  }

  for (final g in gorevli) {
    if (hepsi().any((r) => r.id == g.id)) continue; // veri hattı zaten birleştirmiş
    final duz = g.duzeltmeId;
    if (duz != null) {
      for (final l in ilceler.values) {
        l.removeWhere((r) => r.id == duz);
      }
      genel.removeWhere((r) => r.id == duz);
    } else if (hepsi().any((r) => ayniKisi(r, g))) {
      continue;
    }
    final ilce = g.ilce;
    if (ilce == null || ilce.isEmpty) {
      genel.add(g);
    } else {
      ilceler.putIfAbsent(ilce, () => <Ilan>[]).add(g);
    }
    degisti = true;
  }
  if (!degisti) return v;
  ilceler.removeWhere((ad, l) => l.isEmpty && !v.ilceler.containsKey(ad)); // yalnız düzeltmeyle boşalan yeni anahtar kalmasın
  return IlVerisi(il: v.il, kaynakli: true, ilceler: ilceler, genel: genel, guncelleme: v.guncelleme);
}
