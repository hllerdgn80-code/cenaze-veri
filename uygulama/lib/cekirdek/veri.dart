// Canlı veri: her açılışta ve aşağı çekince indirilir; son başarılı yanıt cihazda saklanır.
import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;

import 'package:http/http.dart' as http;

import 'depo.dart';
import 'ilan.dart';
import 'kisi.dart';
import 'yardimci.dart';

/// Veri kök adresi. Veri Cloudflare'e taşınınca YALNIZ bu satır değişir.
const String veriKok = 'https://hllerdgn80-code.github.io/cenaze-veri/veri';

enum VeriDurumu { tamam, onbellek, baglantiYok, hata }

class IlSonucu {
  final IlVerisi? veri;
  final VeriDurumu durum;
  final DateTime? zaman; // verinin güncellenme anı (gösterim: "Son güncelleme 09:02")
  const IlSonucu(this.veri, this.durum, this.zaman);
}

class KisiSonucu {
  final List<Kisi>? liste; // null: dosya yok (henüz hazırlanıyor) ya da hata
  final VeriDurumu durum;
  const KisiSonucu(this.liste, this.durum);
}

class VeriServisi {
  final http.Client istemci;
  final Depo depo;
  final Set<String> haric; // hariç tutulan Wikidata kimlikleri (ikinci kilit)
  final String kok;
  final Map<String, List<Kisi>> _kisiOnbellek = {};

  VeriServisi({required this.istemci, required this.depo, this.haric = const {}, this.kok = veriKok});

  static const _zamanAsimi = Duration(seconds: 15);

  Future<http.Response> _getir(String yol) =>
      istemci.get(Uri.parse('$kok/$yol'), headers: {'Accept': 'application/json'}).timeout(_zamanAsimi);

  DateTime? _guncellemeZamani(IlVerisi v, int? yedek) {
    final g = v.guncelleme == null ? null : DateTime.tryParse(v.guncelleme!);
    if (g != null) return g;
    return yedek == null ? null : DateTime.fromMillisecondsSinceEpoch(yedek);
  }

  IlSonucu _onbellektenOku(String il, String kod, VeriDurumu yoksa) {
    final s = depo.onbellek(kod);
    if (s != null) {
      try {
        final v = IlVerisi.fromJson(il, Map<String, dynamic>.from(jsonDecode(s) as Map));
        return IlSonucu(v, VeriDurumu.onbellek, _guncellemeZamani(v, depo.onbellekZamani(kod)));
      } catch (_) {}
    }
    return IlSonucu(null, yoksa, null);
  }

  /// Bir ilin son 7 günü. 404 → kaynaksız il (ilanlar yakınları tarafından paylaşılır).
  Future<IlSonucu> ilGetir(String il) async {
    final kod = ilKodu(il);
    try {
      final y = await _getir('$kod/son7gun.json');
      if (y.statusCode == 404) {
        return IlSonucu(IlVerisi(il: il, kaynakli: false), VeriDurumu.tamam, null);
      }
      if (y.statusCode != 200) return _onbellektenOku(il, kod, VeriDurumu.hata);
      final govde = utf8.decode(y.bodyBytes);
      final v = IlVerisi.fromJson(il, Map<String, dynamic>.from(jsonDecode(govde) as Map));
      await depo.onbellekYaz(kod, govde);
      return IlSonucu(v, VeriDurumu.tamam, _guncellemeZamani(v, DateTime.now().millisecondsSinceEpoch));
    } on SocketException {
      return _onbellektenOku(il, kod, VeriDurumu.baglantiYok);
    } on TimeoutException {
      return _onbellektenOku(il, kod, VeriDurumu.baglantiYok);
    } on http.ClientException {
      return _onbellektenOku(il, kod, VeriDurumu.baglantiYok);
    } catch (_) {
      return _onbellektenOku(il, kod, VeriDurumu.hata);
    }
  }

  Future<KisiSonucu> _kisiDosyasi(String yol, {String? kategori}) async {
    if (_kisiOnbellek.containsKey(yol)) return KisiSonucu(_kisiOnbellek[yol], VeriDurumu.tamam);
    try {
      final y = await _getir(yol);
      if (y.statusCode == 404) return const KisiSonucu(null, VeriDurumu.tamam);
      if (y.statusCode != 200) return const KisiSonucu(null, VeriDurumu.hata);
      final ham = jsonDecode(utf8.decode(y.bodyBytes));
      if (ham is! List) return const KisiSonucu(null, VeriDurumu.hata);
      final L = ham
          .whereType<Map>()
          .map((m) => Kisi.fromJson(Map<String, dynamic>.from(m), kategori: kategori))
          .where((k) => !haric.contains(k.wikidataId))
          .toList();
      _kisiOnbellek[yol] = L;
      return KisiSonucu(L, VeriDurumu.tamam);
    } on SocketException {
      return const KisiSonucu(null, VeriDurumu.baglantiYok);
    } on TimeoutException {
      return const KisiSonucu(null, VeriDurumu.baglantiYok);
    } on http.ClientException {
      return const KisiSonucu(null, VeriDurumu.baglantiYok);
    } catch (_) {
      return const KisiSonucu(null, VeriDurumu.hata);
    }
  }

  /// Kaybettiklerimiz: cumhurbaşkanları, başbakanlar, bakanlar ve siyasetçiler vefat tarihine göre (yeniden eskiye);
  /// Sanat, Edebiyat ve Bilim tanınırlığa göre. Siyasi listelerdeki kişi sanatçılarda tekrar gösterilmez.
  Future<KisiSonucu> kaybettiklerimiz(String kategori) async {
    final s = await _kisiDosyasi('kaybettiklerimiz/$kategori.json', kategori: kategori);
    if (s.liste == null) return s;
    var L = List<Kisi>.from(s.liste!);
    if (kategori == 'sanatcilar') {
      final siyasi = <String>{};
      for (final k in ['cumhurbaskanlari', 'basbakanlar', 'bakanlar', 'siyasetciler']) {
        final x = await _kisiDosyasi('kaybettiklerimiz/$k.json', kategori: k);
        for (final p in x.liste ?? const <Kisi>[]) {
          if (p.wikidataId.isNotEmpty) siyasi.add(p.wikidataId);
        }
      }
      L = L.where((x) => !siyasi.contains(x.wikidataId)).toList();
      L.sort((a, b) {
        final c = b.sitelink.compareTo(a.sitelink);
        return c != 0 ? c : trKarsilastir(a.ad, b.ad);
      });
    } else {
      L.sort((a, b) => (b.vefatTarihi ?? '').compareTo(a.vefatTarihi ?? ''));
    }
    return KisiSonucu(L, VeriDurumu.tamam);
  }

  /// Tarihte Bugün: tarihte_bugun/AA-GG.json; Türkler önce, sonra tanınırlık
  Future<KisiSonucu> tarihteBugun(String gun) async {
    final ag = gun.length >= 10 ? gun.substring(5, 10) : gun;
    final s = await _kisiDosyasi('kaybettiklerimiz/tarihte_bugun/$ag.json');
    if (s.liste == null) return s;
    final L = List<Kisi>.from(s.liste!)
      ..sort((a, b) {
        if (a.turk != b.turk) return a.turk ? -1 : 1;
        return b.sitelink.compareTo(a.sitelink);
      });
    return KisiSonucu(L, VeriDurumu.tamam);
  }
}
