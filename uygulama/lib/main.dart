// Kimin Cenazesi — v0.1 (kapalı test sürümü).
// Analitik, Firebase YOK (telefon numarası yalnız din görevlisi kaydında, SMS doğrulaması için sunucuya gider). 0.1.4: yerel günlük cenaze bildirimi (WorkManager + flutter_local_notifications);
// bildirim izni ilk açılışta tek kartla sorulur (URUN-TASLAGI §36).
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:http/http.dart' as http;

import 'cekirdek/bildirim.dart';
import 'cekirdek/cinsiyet.dart';
import 'cekirdek/depo.dart';
import 'cekirdek/durum.dart';
import 'cekirdek/tema.dart';
import 'cekirdek/uzak_ayar.dart';
import 'cekirdek/veri.dart';
import 'ekranlar/acilis_mesaji.dart';
import 'ekranlar/adres.dart';
import 'ekranlar/bildirim_sorusu.dart';
import 'ekranlar/guncelleme.dart';
import 'ekranlar/kabuk.dart';

Future<Gomulu> gomuluYukle() async {
  Future<dynamic> oku(String ad) async => jsonDecode(await rootBundle.loadString('assets/veri/$ad.json'));
  final ilc = Map<String, dynamic>.from(await oku('ilceler') as Map);
  return Gomulu(
    ilceler: ilc.map((k, v) => MapEntry(k, (v as List).map((x) => x.toString()).toList())),
    cinsiyet: CinsiyetCozucu.fromJson(Map<String, dynamic>.from(await oku('adlar') as Map)),
    dualar: Map<String, dynamic>.from(await oku('dualar') as Map),
    sureler: Map<String, dynamic>.from(await oku('sureler') as Map),
    haric: (await oku('haric') as List).map((x) => x.toString()).toSet(),
  );
}

/// 30.10.2026 uçtan uca ekran (Play: Android 15'te SDK 35+ uygulamalar varsayılan uçtan uca çizilir): durum ve gezinme çubukları şeffaf,
/// ikon rengi temaya göre (koyu tema → açık ikon). Ekran içeriği çubukların altına taşmasın diye ekranlar SafeArea / Scaffold ekleriyle sarılıdır.
SystemUiOverlayStyle sistemCubuklari(bool koyu) {
  final ikon = koyu ? Brightness.light : Brightness.dark;
  return SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    systemNavigationBarColor: Colors.transparent,
    systemNavigationBarDividerColor: Colors.transparent,
    systemNavigationBarContrastEnforced: false,
    statusBarIconBrightness: ikon,
    systemNavigationBarIconBrightness: ikon,
    statusBarBrightness: koyu ? Brightness.dark : Brightness.light, // iOS
  );
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  final gomulu = await gomuluYukle();
  final depo = await Depo.ac();
  await UzakAyar.yerelYukle(); // 16.10.2026 uzak ayar: son değer telefondan, tazesi ilanlar yüklenirken
  final veri = VeriServisi(istemci: http.Client(), depo: depo, haric: gomulu.haric);
  final bildirim = AndroidBildirim();
  final durum = AppDurum(depo: depo, veri: veri, gomulu: gomulu, bildirim: bildirim, bildirimSorusuAcik: true, acilisAcik: true);
  // Bildirime dokunuş: uygulama o ilçenin bugünkü listesine döner (il/ilçe depodan; tarih = bugün)
  // Din görevlisi onay bildirimine dokunuş: Panel sekmesini seçer (oturum depodadır)
  void gorevliPaneliAc() {
    if (!durum.panelSekmesiAc()) durum.sekmeSec(0); // Panel sekmesi; parola açılış başına bir kez sorulur (URUN §53)
  }

  durum.surumKontrol(); // açılış mesajı sürerken arka planda; hata = kapı açık (§42)
  await bildirim.baslat(tiklandi: durum.anaEkranaDon, gorevliTiklandi: gorevliPaneliAc);
  if (depo.bildirimIzni == true) await bildirim.planla(); // zincir her açılışta yeniden kurulur
  runApp(KiminCenazesi(durum: durum));
}

Widget _sonrakiEkran(AppDurum durum) => SurumKapisi(
    child: durum.bildirimSorusuGerek
        ? const BildirimSorusu()
        : (durum.adresVar ? const AnaKabuk() : const IlSecEkrani()));

Widget _ilkEkran(AppDurum durum) {
  if (!durum.acilisAcik) return _sonrakiEkran(durum);
  // 30.10.2026 HATA (0.1.7–0.1.16, sahibi yakaladı): AcilisMesaji sonrasını AYRI ROTA olarak açar (pushReplacement);
  // MaterialApp.home yeniden kurulsa da o rota değişmez → izin kartı "Evet/Şimdi değil"den sonra takılı kalıyordu,
  // il seçimine geçilmiyordu. Rotanın içeriği duruma bağlı yeniden kurulur.
  return AcilisMesaji(sonra: ListenableBuilder(listenable: durum, builder: (_, __) => _sonrakiEkran(durum)));
}

class KiminCenazesi extends StatelessWidget {
  final AppDurum durum;
  const KiminCenazesi({super.key, required this.durum});

  @override
  Widget build(BuildContext context) {
    return Kapsam(
      durum: durum,
      child: ListenableBuilder(
        listenable: durum,
        builder: (context, _) => MaterialApp(
          title: 'Kimin Cenazesi',
          debugShowCheckedModeBanner: false,
          theme: temaYap(durum.koyu),
          themeAnimationDuration: const Duration(milliseconds: 250),
          builder: (context, child) => AnnotatedRegion<SystemUiOverlayStyle>(
            value: sistemCubuklari(durum.koyu),
            child: child ?? const SizedBox.shrink(),
          ),
          locale: const Locale('tr', 'TR'),
          supportedLocales: const [Locale('tr', 'TR')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: _ilkEkran(durum),
        ),
      ),
    );
  }
}
