// Uygulama durumu: adres, tema, Sayfam değişiklikleri, sekme geçişi. Tek ChangeNotifier, InheritedNotifier ile dağıtılır.
import 'package:flutter/material.dart';

import 'bildirim.dart';
import 'bildirim_mantik.dart';
import 'cinsiyet.dart';
import 'depo.dart';
import 'ilan.dart';
import 'metin.dart';
import 'surum.dart';
import 'veri.dart';
import 'yardimci.dart';

/// Uygulamaya gömülü veriler (assets/veri) — testlerde doğrudan verilir
class Gomulu {
  final Map<String, List<String>> ilceler; // 81 il → ilçeler (il sırası korunur)
  final CinsiyetCozucu cinsiyet;
  final Map<String, dynamic> dualar;
  final Map<String, dynamic> sureler; // 25.10.2026: Yâsîn, Mülk, Nebe’ (assets/veri/sureler.json)
  final Set<String> haric;
  const Gomulu(
      {required this.ilceler, required this.cinsiyet, this.dualar = const {}, this.sureler = const {}, this.haric = const {}});

  List<String> get iller => ilceler.keys.toList();
}

class AppDurum extends ChangeNotifier {
  final Depo depo;
  final VeriServisi veri;
  final Gomulu gomulu;

  /// Bildirim arayüzü: gerçek uygulamada [AndroidBildirim], testlerde [YokBildirim] (eklenti çağrılmaz)
  final BildirimArkayuzu bildirim;

  /// [acilisAcik]: yalnız main() true verir (0.1.7 açılış mesajı, §41); testlerde atlanır
  final bool acilisAcik;

  /// [bildirimSorusuAcik]: yalnız main() true verir; testlerde ilk açılış kartı atlanır
  AppDurum({
    required this.depo,
    required this.veri,
    required this.gomulu,
    this.bildirim = const YokBildirim(),
    bool bildirimSorusuAcik = false,
    this.acilisAcik = false,
    SurumCekici? surumCekici,
    this.buildNo = buildNoDerleme,
    bool? ios,
  })  : ios = ios ?? iosMu,
        _surumCekici = surumCekici ?? varsayilanSurumCekici(veri.istemci),
         il = depo.il,
        ilce = depo.ilce,
        koyu = depo.koyu,
        bildirimSorusuGerek = bildirimSorusuAcik &&
            bildirimTeklifiAcik &&
            soruZamaniGeldi(izin: depo.bildirimIzni, erteleGunu: depo.bildirimErtele, bugun: bugunTr());

  // ---- Zorunlu güncelleme kapısı (§42) ----
  final SurumCekici _surumCekici;

  /// Çalışan sürümün build numarası; 0 = kapı atlanır (geliştirme/test)
  final int buildNo;

  /// iOS mu (iOS'ta surum.json'un min_build_ios / son_build_ios anahtarları geçerli; testte enjekte edilir)
  final bool ios;
  SurumBilgi? surum;
  bool surumBekliyor = false;
  Future<void>? _surumIs;

  bool get guncellemeZorunlu => buildNo > 0 && surum != null && buildNo < surum!.minBuildIcin(ios);
  bool get guncellemeOnerilir => buildNo > 0 && surum != null && !guncellemeZorunlu && buildNo < surum!.sonBuildIcin(ios);

  /// Sürüm bilgisini çeker (3 sn); hata = kapı açık. Sürerken tekrar çağrılırsa aynı işi döndürür.
  Future<void> surumKontrol() {
    if (buildNo <= 0) return Future.value();
    return _surumIs ??= () async {
      surumBekliyor = surum == null;
      try {
        final s = await _surumCekici().timeout(const Duration(seconds: 3));
        if (s != null) {
          surum = s;
          sonIosMagazaUrl = s.iosMagazaUrl;
        } // hata/boş yanıt: önceki bilgi korunur, yoksa kapı açık
      } catch (_) {}
      surumBekliyor = false;
      _surumIs = null;
      notifyListeners();
    }();
  }

  String? il;
  String? ilce; // null = tüm ilçeler
  bool koyu;

  // Sekmeli kabuk
  int sekme = 0;
  final List<GlobalKey<NavigatorState>> sekmeAnahtarlari = List.generate(5, (_) => GlobalKey<NavigatorState>());

  /// Logoya dokunma ya da adres değişimi: İlanlar sekmesi, bugün
  int anaEkranSayaci = 0;

  bool get adresVar => il != null;

  // ---- Günlük bildirim (§36) ----
  /// İlk açılış kartı gösterilsin mi (başka hiçbir ekrandan önce)
  bool bildirimSorusuGerek;

  bool get bildirimAcik => depo.bildirimIzni == true;

  /// İlk açılış kartı cevabı. Evet → sistem izni → normal akış. Şimdi değil → 7 gün sorulmaz.
  Future<void> bildirimSorusunuYanitla(bool evet) async {
    if (evet) {
      await bildirimAyarla(true);
    } else {
      await depo.bildirimErteleKaydet(bugunTr());
    }
    bildirimSorusuGerek = false;
    notifyListeners();
  }

  /// Menüdeki aç-kapa. Açarken sistem izni istenir; verilmezse kapalı kalır. Sonuç: gerçekten açık mı.
  Future<bool> bildirimAyarla(bool ac) async {
    if (ac && await bildirim.izinIste()) {
      await depo.bildirimIzniKaydet(true);
      await bildirim.planla();
      notifyListeners();
      return true;
    }
    await depo.bildirimIzniKaydet(false);
    await bildirim.iptal();
    notifyListeners();
    return false;
  }

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

  /// Sekme sayısı HER ZAMAN 5 (… · Panel); oturumsuzken Panel sekmesi "din görevlileri kullanabilir" mesajını gösterir (URUN §53, 16.10 10:50)
  int get sekmeSayisi => 5;

  /// Panel parolası bu uygulama açılışında girildi mi (yalnız bellekte; açılış başına bir kez sorulur)
  bool panelAcik = false;

  /// Oturum açıldı/kapandı ya da parola belirlendi: sekme çubuğunu yeniler
  void oturumDegisti() => notifyListeners();

  /// Parola belirlendi: panel açık sayılır ve Panel sekmesi seçilir
  void gorevliGirisTamam() {
    panelAcik = true;
    sekme = 4;
    notifyListeners();
  }

  void paneliKilitle() {
    panelAcik = false;
    notifyListeners();
  }

  /// Panel sekmesini seç (bildirim / ilan kutusu bağlantısı); oturum yoksa seçmez (çağıran kayıt ekranını açar)
  bool panelSekmesiAc() {
    if (depo.gorevliOturum == null) return false;
    sekmeSec(4);
    return true;
  }

  /// Çıkış: oturum + parola + görev bilgisi + KVKK kaydı silinir, sekme çubuğu 4'e döner
  Future<void> gorevliCikis() async {
    await depo.gorevliOturumKaydet(null);
    panelAcik = false;
    if (sekme >= 4) sekme = 0;
    notifyListeners();
  }

  void sekmeSec(int i) {
    if (i < 0 || i >= sekmeSayisi) return;
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
