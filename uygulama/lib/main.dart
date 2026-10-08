// Kimin Cenazesi — v0.1 (kapalı test sürümü).
// Bildirim, analitik, SMS, Firebase YOK; izin istenmez (yalnız internet).
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:http/http.dart' as http;

import 'cekirdek/cinsiyet.dart';
import 'cekirdek/depo.dart';
import 'cekirdek/durum.dart';
import 'cekirdek/tema.dart';
import 'cekirdek/veri.dart';
import 'ekranlar/adres.dart';
import 'ekranlar/kabuk.dart';

Future<Gomulu> gomuluYukle() async {
  Future<dynamic> oku(String ad) async => jsonDecode(await rootBundle.loadString('assets/veri/$ad.json'));
  final ilc = Map<String, dynamic>.from(await oku('ilceler') as Map);
  return Gomulu(
    ilceler: ilc.map((k, v) => MapEntry(k, (v as List).map((x) => x.toString()).toList())),
    cinsiyet: CinsiyetCozucu.fromJson(Map<String, dynamic>.from(await oku('adlar') as Map)),
    dualar: Map<String, dynamic>.from(await oku('dualar') as Map),
    haric: (await oku('haric') as List).map((x) => x.toString()).toSet(),
  );
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final gomulu = await gomuluYukle();
  final depo = await Depo.ac();
  final veri = VeriServisi(istemci: http.Client(), depo: depo, haric: gomulu.haric);
  runApp(KiminCenazesi(durum: AppDurum(depo: depo, veri: veri, gomulu: gomulu)));
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
          locale: const Locale('tr', 'TR'),
          supportedLocales: const [Locale('tr', 'TR')],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: durum.adresVar ? const AnaKabuk() : const IlSecEkrani(),
        ),
      ),
    );
  }
}
