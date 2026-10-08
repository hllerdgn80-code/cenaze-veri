// Uygulama durumu: adres, tema, Sayfam değişiklikleri, sekme geçişi. Tek ChangeNotifier, InheritedNotifier ile dağıtılır.
import 'package:flutter/material.dart';

import 'cinsiyet.dart';
import 'depo.dart';
import 'ilan.dart';
import 'veri.dart';
import 'yardimci.dart';

/// Uygulamaya gömülü veriler (assets/veri) — testlerde doğrudan verilir
class Gomulu {
  final Map<String, List<String>> ilceler; // 81 il → ilçeler (il sırası korunur)
  final CinsiyetCozucu cinsiyet;
  final Map<String, dynamic> dualar;
  final Set<String> haric;
  const Gomulu({required this.ilceler, required this.cinsiyet, this.dualar = const {}, this.haric = const {}});

  List<String> get iller => ilceler.keys.toList();
}

class AppDurum extends ChangeNotifier {
  final Depo depo;
  final VeriServisi veri;
  final Gomulu gomulu;

  AppDurum({required this.depo, required this.veri, required this.gomulu})
      : il = depo.il,
        ilce = depo.ilce,
        koyu = depo.koyu;

  String? il;
  String? ilce; // null = tüm ilçeler
  bool koyu;

  // Sekmeli kabuk
  int sekme = 0;
  final List<GlobalKey<NavigatorState>> sekmeAnahtarlari = List.generate(5, (_) => GlobalKey<NavigatorState>());

  /// Logoya dokunma ya da adres değişimi: İlanlar sekmesi, bugün
  int anaEkranSayaci = 0;

  bool get adresVar => il != null;

  Future<void> adresKaydet(String yeniIl, String? yeniIlce) async {
    il = yeniIl;
    ilce = yeniIlce;
    await depo.adresKaydet(yeniIl, yeniIlce);
    anaEkranaDon();
  }

  Future<void> temaDegistir() async {
    koyu = !koyu;
    await depo.temaKaydet(koyu);
    notifyListeners();
  }

  void sekmeSec(int i) {
    if (i == sekme) {
      sekmeAnahtarlari[i].currentState?.popUntil((r) => r.isFirst);
    }
    sekme = i;
    notifyListeners();
  }

  void anaEkranaDon() {
    sekmeAnahtarlari[0].currentState?.popUntil((r) => r.isFirst);
    sekme = 0;
    anaEkranSayaci++;
    notifyListeners();
  }

  // ---- Sayfam ----
  bool kayitli(String id) => depo.kayitli(id);

  Future<void> sayfamaEkle(Ilan r) async {
    await depo.sayfamaEkle(r);
    notifyListeners();
  }

  Future<void> sayfamdanKaldir(String id) async {
    await depo.sayfamdanKaldir(id);
    notifyListeners();
  }

  String? cinsiyetCoz(Ilan r) => gomulu.cinsiyet.coz(r, secim: depo.cinsSecimi(r.id));

  Future<void> cinsKaydet(String id, String c) async {
    await depo.cinsKaydet(id, c);
    notifyListeners();
  }

  List<String> ilceListesi(String il) {
    final l = List<String>.from(gomulu.ilceler[il] ?? const <String>[]);
    l.sort(trKarsilastir);
    return l;
  }
}

class Kapsam extends InheritedNotifier<AppDurum> {
  const Kapsam({super.key, required AppDurum durum, required super.child}) : super(notifier: durum);

  static AppDurum of(BuildContext context) {
    final k = context.dependOnInheritedWidgetOfExactType<Kapsam>();
    assert(k != null, 'Kapsam bulunamadı');
    return k!.notifier!;
  }

  /// Dinlemeden erişim (olay işleyicilerinde)
  static AppDurum oku(BuildContext context) {
    final k = context.getInheritedWidgetOfExactType<Kapsam>();
    return k!.notifier!;
  }
}
