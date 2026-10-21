// Din görevlisi Worker istemcisi (URUN-TASLAGI §37; Worker: deploy/aile-worker/src/gorevli.js).
// Uç noktalar (URUN §45): POST /gorevli/eposta-kod, /eposta-dogrula, /profil, /gorev-yeri, /ilan, /ilan/iptal, /ilan/duzenle; GET /gorevli/durum, /ilanlarim.
// Oturum belirteci Depo'da tutulur. Kart fotoğrafı ve telefon kodu yolları kaldırıldı.
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

  /// Diyanet e-posta kodu iste: kullanıcı adı (@ öncesi). Yanıt {durum:"kod_gonderildi", adres}; 429 {hata:"cok_sik_tekrar", bekle_sn} | gunluk_kod_siniri
  Future<AileYanit> epostaKodGonder(String kullanici) => _istek('POST', '/gorevli/eposta-kod', govde: {'kullanici': kullanici});

  /// Kod doğruysa {durum:"onayli", oturum, profil_tamam, ...}: panel HEMEN açılır. Yanlış: 400 {hata:"kod_yanlis", kalan_deneme}; 429 {durum:"red"}; 410 süresi doldu
  Future<AileYanit> epostaDogrula(String kullanici, String kod) =>
      _istek('POST', '/gorevli/eposta-dogrula', govde: {'kullanici': kullanici, 'kod': kod});

  /// İlk "İlan paylaş"ta bir kez: ad_soyad, il, ilce, gorev_yeri, unvan
  Future<AileYanit> profil(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/profil', govde: govde, oturum: oturum);

  /// "Görev yerim değişti": il, ilce, gorev_yeri, unvan (ad değişmez); eski ilanlar değişmez
  Future<AileYanit> gorevYeri(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/gorev-yeri', govde: govde, oturum: oturum);
  Future<AileYanit> adSoyad(String oturum, String ad) => _istek('POST', '/gorevli/ad-soyad', govde: {'ad_soyad': ad}, oturum: oturum);

  Future<AileYanit> durum(String oturum) => _istek('GET', '/gorevli/durum', oturum: oturum);
  Future<AileYanit> ilanlarim(String oturum) => _istek('GET', '/gorevli/ilanlarim', oturum: oturum);
  Future<AileYanit> ilan(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/ilan', govde: govde, oturum: oturum);
  Future<AileYanit> duzenle(String oturum, Map<String, dynamic> govde) => _istek('POST', '/gorevli/ilan/duzenle', govde: govde, oturum: oturum);
  /// KVKK aydınlatmasını kabul ettiğini hesaba yazar (URUN §50)
  Future<AileYanit> kvkkKabul(String oturum) => _istek('POST', '/gorevli/kvkk-kabul', oturum: oturum);

  /// Sorumluluk uyarısı kabulünü hesaba yazar (URUN §54)
  Future<AileYanit> sorumlulukKabul(String oturum) => _istek('POST', '/gorevli/sorumluluk-kabul', oturum: oturum);
  /// Panel parolasını hesaba şifreli yazar (URUN §53; "unuttum" e-postası için)
  Future<AileYanit> parolaKaydet(String oturum, String parola) => _istek('POST', '/gorevli/parola', govde: {'parola': parola}, oturum: oturum);

  /// "Parolamı unuttum": parola hesabın Diyanet adresine e-postayla gönderilir (günde ≤3)
  Future<AileYanit> parolaHatirlat(String oturum) => _istek('POST', '/gorevli/parola-hatirlat', oturum: oturum);
  /// Hesabı ve bütün ilanlarını siler (Play hesap silme şartı; Worker POST /gorevli/hesap-sil). 200 {durum:"silindi"}; 401 = hesap zaten yok
  Future<AileYanit> hesapSil(String oturum) => _istek('POST', '/gorevli/hesap-sil', oturum: oturum);
  Future<AileYanit> iptal(String oturum, String ilanId) => _istek('POST', '/gorevli/ilan/iptal', govde: {'ilan_id': ilanId}, oturum: oturum);
}
