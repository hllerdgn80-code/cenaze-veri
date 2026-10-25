// Canlı veri: her açılışta, sekmeye dönüşte (5 dk geçtiyse) ve aşağı çekince indirilir; son başarılı yanıt cihazda saklanır.
import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import 'depo.dart';
import 'anahtar.dart';
import 'gorevli_birlestir.dart';
import 'ilan.dart';
import 'imza.dart';
import 'kisi.dart';
import 'uzak_ayar.dart';
import 'yardimci.dart';

/// Veri kök adresi: Cloudflare Worker veri kapısı (anahtar + User-Agent ister; deploy/veri-kapisi).
const String veriKok = 'https://veri.kimincenazesi.com/veri';

/// Aile ilanı Worker adresi (sözleşme: deploy/AILE-ILAN-SOZLESME.md). Site sahibi gerçek adresi yazar.
const String aileKok = 'https://kimincenazesi-aile.tr-kopru.workers.dev';

/// dogrulanamadi: veri indi ama yayın imzası yok/bozuk/bayat (GÜVENLİK PAKETİ 25.10.2026) -> GÖSTERİLMEZ
enum VeriDurumu { tamam, onbellek, baglantiYok, hata, dogrulanamadi }

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
  final String gorevliKok; // Worker: GET <gorevliKok>/gorevli/<il>.json (URUN §56)
  final Map<String, List<Kisi>> _kisiOnbellek = {};
  final ImzaDogrulayici imza; // yayın imzası (açık anahtar listesi boşsa doğrulama kapalı)

  VeriServisi({required this.istemci, required this.depo, this.haric = const {}, this.kok = veriKok, this.gorevliKok = aileKok, ImzaDogrulayici? imza})
      : imza = imza ?? ImzaDogrulayici.varsayilan();

  /// Sunucu kökünden göreli yol (imza mesajına girer): `kok/yol` -> `veri/ordu/son7gun.json`.
  String _imzaYolu(String yol) => Uri.parse('$kok/$yol').path.replaceFirst(RegExp(r'^/'), '');

  /// İmza denetimi. Nesne dosyasında imza dosyanın içindedir; dizi dosyasında yan dosyadadır ("<ad>-imza.json").
  Future<bool> _imzaTamam(String yol, http.Response y, {required bool dizi}) async {
    if (!imza.etkin) return true;
    final p = _imzaYolu(yol);
    if (!dizi) return imza.denetle(p, y.bodyBytes) == ImzaSonuc.gecerli;
    try {
      final yan = await _getir(yol.replaceFirst(RegExp(r'\.json$'), '-imza.json'));
      if (yan.statusCode != 200) return false;
      return imza.denetle(p, y.bodyBytes, yan: yan.bodyBytes) == ImzaSonuc.gecerli;
    } catch (_) {
      return false;
    }
  }

  static const _zamanAsimi = Duration(seconds: 15);
  static const _gorevliZamanAsimi = Duration(seconds: 5);

  Future<http.Response> _getir(String yol) =>
      istemci.get(Uri.parse('$kok/$yol'), headers: {'Accept': 'application/json', ...kcBasliklar()}).timeout(_zamanAsimi);

  DateTime? _guncellemeZamani(IlVerisi v, int? yedek) {
    final g = v.guncelleme == null ? null : DateTime.tryParse(v.guncelleme!);
    if (g != null) return g;
    return yedek == null ? null : DateTime.fromMillisecondsSinceEpoch(yedek);
  }

  IlSonucu _onbellektenOku(String il, String kod, VeriDurumu yoksa) {
    final s = depo.onbellek(kod);
    if (s != null) {
      // cihazdaki kopya da imzalı olmalı (eski imzasız sürümden kalan kopya kullanılmaz); yaş sınırı yok: çevrimdışı son iyi veri
      if (imza.etkin && imza.denetle(_imzaYolu('$kod/son7gun.json'), Uint8List.fromList(utf8.encode(s)), yasKontrol: false) != ImzaSonuc.gecerli) {
        return IlSonucu(null, yoksa, null);
      }
      try {
        final v = IlVerisi.fromJson(il, Map<String, dynamic>.from(jsonDecode(s) as Map));
        return IlSonucu(v, VeriDurumu.onbellek, _guncellemeZamani(v, depo.onbellekZamani(kod)));
      } catch (_) {}
    }
    return IlSonucu(null, yoksa, null);
  }

  /// Bir ilin son 7 günü + din görevlisi ilanları (URUN §56: saatlik turu beklemeden, Worker'dan anında; iki istek paralel).
  /// Görevli isteği 5 sn'de kesilir, hata olursa sessizce atlanır.
  Future<IlSonucu> ilGetir(String il) async {
    final gorevliIs = _gorevliGetir(il);
    final s = await _ilTemel(il);
    final g = await gorevliIs;
    final v = s.veri;
    if (v == null) return s;
    final b = g.isEmpty ? v : gorevliBirlestir(v, g);
    final f = acilSuz(b, UzakAyar.acilGizle);      // ACİL DÜĞME (araclar/acil.py): ayarlardaki il/ilçe/ilan listesi anında uygulanır
    return identical(f, v) ? s : IlSonucu(f, s.durum, s.zaman);
  }

  /// `GET /gorevli/<il>.json`; yalnız beyaz listedeki alanlar alınır ([gorevliKayitlari]). Her hata → boş liste.
  Future<List<Ilan>> _gorevliGetir(String il) async {
    try {
      final y = await istemci
          .get(Uri.parse('$gorevliKok/gorevli/${ilKodu(il)}.json'), headers: {'Accept': 'application/json', ...kcBasliklar()})
          .timeout(_gorevliZamanAsimi);
      if (y.statusCode != 200) return const [];
      return gorevliKayitlari(jsonDecode(utf8.decode(y.bodyBytes)), bugunTr());
    } catch (_) {
      return const [];
    }
  }

  Future<IlSonucu> _ilTemel(String il) async {
    final kod = ilKodu(il);
    try {
      final y = await _getir('$kod/son7gun.json');
      if (y.statusCode == 404) {
        return IlSonucu(IlVerisi(il: il, kaynakli: false), VeriDurumu.tamam, null);
      }
      if (y.statusCode != 200) return _onbellektenOku(il, kod, VeriDurumu.hata);
      if (!await _imzaTamam('$kod/son7gun.json', y, dizi: false)) return const IlSonucu(null, VeriDurumu.dogrulanamadi, null);
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
      if (!await _imzaTamam(yol, y, dizi: true)) return const KisiSonucu(null, VeriDurumu.dogrulanamadi);
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
