// Din görevlisi Worker istemcisi (URUN-TASLAGI §37; Worker: deploy/aile-worker/src/gorevli.js).
// Uç noktalar: POST /gorevli/kayit, /kod, /giris, /dogrula, /ilan, /ilan/iptal, /ilan/duzenle; GET /gorevli/durum, /ilanlarim.
// Kart fotoğrafı yalnız POST gövdesinde gider; cihazda diske YAZILMAZ. Oturum belirteci Depo'da tutulur.
import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;

import 'package:http/http.dart' as http;

import 'aile.dart' show AileYanit;
import 'anahtar.dart';
import 'veri.dart';

class GorevliServisi {
  final http.Client istemci;
  final String kok;
  const GorevliServisi({required this.istemci, this.kok = aileKok});

  static const _zamanAsimi = Duration(seconds: 15);
  static const _fotoZamanAsimi = Duration(seconds: 60); // OCR birkaç saniye sürebilir

  Future<AileYanit> _istek(String yontem, String yol, {Map<String, dynamic>? govde, String? oturum, Duration? sure}) async {
    try {
      final basliklar = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        ...kcBasliklar(),
        if (oturum != null) 'Authorization': 'Bearer $oturum',
      };
      final uri = Uri.parse('$kok$yol');
      final http.Response y;
      if (yontem == 'GET') {
        y = await istemci.get(uri, headers: basliklar).timeout(sure ?? _zamanAsimi);
      } else {
        y = await istemci.post(uri, headers: basliklar, body: jsonEncode(govde ?? const {})).timeout(sure ?? _zamanAsimi);
      }
      Map<String, dynamic>? j;
      try {
        final ham = jsonDecode(utf8.decode(y.bodyBytes));
        if (ham is Map) j = Map<String, dynamic>.from(ham);
      } catch (_) {}
      return AileYanit(y.statusCode, j);
    } on SocketException {
      return const AileYanit(0, null, agHatasi: true);
    } on TimeoutException {
      return const AileYanit(0, null, agHatasi: true);
    } on http.ClientException {
      return const AileYanit(0, null, agHatasi: true);
    } catch (_) {
      return const AileYanit(0, null, agHatasi: true);
    }
  }

  /// Adım 1 (foto yok): bilgiler (ad_soyad, il, ilce, gorev_yeri, unvan, telefon) -> {durum:"foto_gerek", kayit_id, liste_eslesti}
  Future<AileYanit> kayit(Map<String, dynamic> bilgi) => _istek('POST', '/gorevli/kayit', govde: bilgi);

  /// Adım 2: kayit_id + foto_base64 (cihazda ≤1600 px). Yanıt: onayli | kuyruk | deneme2 | kontrol_bekliyor (+ dogrulama:"kod", kanal)
  Future<AileYanit> foto(String kayitId, String fotoBase64) =>
      _istek('POST', '/gorevli/kayit', govde: {'kayit_id': kayitId, 'foto_base64': fotoBase64}, sure: _fotoZamanAsimi);

  Future<AileYanit> giris(String telefon) => _istek('POST', '/gorevli/giris', govde: {'telefon': telefon});
  Future<AileYanit> kodYenidenGonder(String kayitId) => _istek('POST', '/gorevli/kod', govde: {'kayit_id': kayitId});
  Future<AileYanit> dogrula(String kayitId, String kod) => _istek('POST', '/gorevli/dogrula', govde: {'kayit_id': kayitId, 'kod': kod});

  Future<AileYanit> durum(String oturum) => _istek('GET', '/gorevli/durum', oturum: oturum);
  Future<AileYanit> ilanlarim(String oturum) => _istek('GET', '/gorevli/ilanlarim', oturum: oturum);
  Future<AileYanit> ilan(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/ilan', govde: govde, oturum: oturum);
  Future<AileYanit> duzenle(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/ilan/duzenle', govde: govde, oturum: oturum);
  Future<AileYanit> iptal(String oturum, String ilanId) => _istek('POST', '/gorevli/ilan/iptal', govde: {'ilan_id': ilanId}, oturum: oturum);
}
