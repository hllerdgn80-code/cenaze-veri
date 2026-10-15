// Günlük cenaze bildirimi (URUN-TASLAGI §36): Firebase/sunucu YOK. Telefon arka planda (WorkManager) seçili
// il/ilçenin verisini çeker, o gün cenaze günü olan ilan varsa YEREL bildirim gösterir; yoksa sessiz kalır.
// Karar mantığı ve metin: bildirim_mantik.dart (saf, testli). Burada yalnız eklentiye bağlı işler var.
//
// Zamanlama: Android WorkManager "tam 08:00" garantisi VERMEZ. Her sabah/öğle penceresi için, hedef saate kadar
// beklemeli tek seferlik görev kaydedilir; görev çalışınca bir sonraki pencereleri yeniden kaydeder (zincir).
// Uygulama her açıldığında zincir yeniden kurulur (aynı ada sahip bekleyen görev varsa dokunulmaz).
import 'dart:io' show Platform;

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:workmanager/workmanager.dart' as wm;

import 'bildirim_mantik.dart';
import 'depo.dart';
import 'veri.dart';
import 'yardimci.dart';

const String _kanalKimligi = 'gunluk_cenaze';
const String _kanalAdi = 'Günlük cenaze ilanları';
const String _kanalAcikla = 'Bölgenizde o gün cenaze ilanı olduğunda sabah bir bildirim';
const String _simge = 'ic_bildirim'; // CI'da araclar/android_ayarla.py üretir (tek renkli hilal)
const String _gorevEtiketi = 'kc-bildirim';

final FlutterLocalNotificationsPlugin _eklenti = FlutterLocalNotificationsPlugin();

Future<void> _eklentiyiHazirla({DidReceiveNotificationResponseCallback? tiklandi}) async {
  await _eklenti.initialize(
    settings: const InitializationSettings(android: AndroidInitializationSettings(_simge)),
    onDidReceiveNotificationResponse: tiklandi,
  );
}

/// Uygulamanın bildirim arayüzü. Testlerde [YokBildirim] kullanılır (eklenti çağrılmaz).
abstract class BildirimArkayuzu {
  /// Sistem bildirim iznini ister (Android 13+). İzin varsa true.
  Future<bool> izinIste();

  /// Sabah 08:00 ve öğle 12:00 bakışlarını kurar
  Future<void> planla();

  /// Zamanlanmış bakışları kaldırır
  Future<void> iptal();
}

class YokBildirim implements BildirimArkayuzu {
  const YokBildirim();
  @override
  Future<bool> izinIste() async => true;
  @override
  Future<void> planla() async {}
  @override
  Future<void> iptal() async {}
}

class AndroidBildirim implements BildirimArkayuzu {
  AndroidBildirim();

  /// main() içinde bir kez: WorkManager + bildirim eklentisi. [tiklandi]: bildirime dokunulunca (uygulama açıkken
  /// ya da arka plandayken) bugünkü listeye dönülür; kapalıyken dokunma uygulamayı zaten bugünkü listede açar.
  Future<void> baslat({required void Function() tiklandi}) async {
    if (!Platform.isAndroid) return;
    try {
      await wm.Workmanager().initialize(bildirimGorevDagiticisi);
      await _eklentiyiHazirla(tiklandi: (_) => tiklandi());
    } catch (_) {}
  }

  @override
  Future<bool> izinIste() async {
    if (!Platform.isAndroid) return false;
    try {
      await _eklentiyiHazirla();
      final a = _eklenti.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
      return (await a?.requestNotificationsPermission()) ?? false;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> planla() async {
    if (!Platform.isAndroid) return;
    try {
      await bildirimPlanla();
    } catch (_) {}
  }

  @override
  Future<void> iptal() async {
    if (!Platform.isAndroid) return;
    try {
      await wm.Workmanager().cancelByTag(_gorevEtiketi);
    } catch (_) {}
  }
}

/// Sabah ve öğle pencereleri için bir sonraki çalışmayı kaydeder. Görev adı hedef günü taşır
/// ("kc-sabah-2026-10-16"): çalışmakta olan görevin kendi adı yeniden kaydedilmez, bekleyen aynı adlı görev korunur.
Future<void> bildirimPlanla() async {
  final simdi = DateTime.now();
  for (final rol in BildirimRolu.values) {
    final hedef = sonrakiCalisma(simdi, rol);
    await wm.Workmanager().registerOneOffTask(
      'kc-${rol.name}-${gunYaz(hedef)}',
      rol.name,
      initialDelay: hedef.difference(simdi),
      constraints: wm.Constraints(networkType: wm.NetworkType.connected),
      existingWorkPolicy: wm.ExistingWorkPolicy.keep,
      backoffPolicy: wm.BackoffPolicy.exponential,
      backoffPolicyDelay: const Duration(minutes: 10),
      tag: _gorevEtiketi,
    );
  }
}

/// WorkManager'ın ayrı izolatta çağırdığı giriş noktası
@pragma('vm:entry-point')
void bildirimGorevDagiticisi() {
  wm.Workmanager().executeTask((gorev, girdi) async {
    try {
      await bildirimPlanla(); // önce zinciri sürdür: aşağıdaki iş patlasa bile ertesi pencere kurulu kalır
    } catch (_) {}
    try {
      await arkaPlandaBak(gorev == BildirimRolu.ogle.name ? BildirimRolu.ogle : BildirimRolu.sabah);
    } catch (_) {}
    return true;
  });
}

/// Bir bakış: veriyi çek (X-KC-Anahtar + User-Agent başlıklarıyla, VeriServisi üzerinden), kararı ver, gerekirse göster.
Future<void> arkaPlandaBak(BildirimRolu rol, {DateTime? simdiVerilen}) async {
  final depo = Depo(await SharedPreferences.getInstance());
  await depo.yenile();
  final il = depo.il;
  if (il == null) return;
  final simdi = simdiVerilen ?? DateTime.now();
  final bugun = bugunTr();
  if (!bakmayaDeger(
    rol: rol,
    simdi: simdi,
    bugun: bugun,
    izinAcik: depo.bildirimIzni == true,
    sabahGunu: depo.bildirimSabahGunu,
    ogleGunu: depo.bildirimOgleGunu,
  )) {
    return;
  }
  final istemci = http.Client();
  try {
    final sonuc = await VeriServisi(istemci: istemci, depo: depo).ilGetir(il);
    final v = sonuc.veri;
    if (v == null) return;
    final ilce = depo.ilce; // il/ilçe her bakışta depodan okunur: kullanıcı değiştirirse bildirim bölgesi de değişir
    final bugunkuler = bugunIlanlari(v, ilce, bugun);
    final gonder = bildirimGonderilsin(
      rol: rol,
      bugunkuler: bugunkuler,
      sabahGorulen: depo.bildirimGorulen,
    );
    if (!gonder) return;
    await _goster(rol, bildirimMetni(il, ilce));
    if (rol == BildirimRolu.sabah) {
      await depo.bildirimSabahKaydet(bugun, bugunkuler);
    } else {
      await depo.bildirimOgleKaydet(bugun);
    }
  } finally {
    istemci.close();
  }
}

Future<void> _goster(BildirimRolu rol, String metin) async {
  await _eklentiyiHazirla();
  await _eklenti.show(
    id: rol == BildirimRolu.sabah ? 1 : 2,
    title: 'Kimin Cenazesi',
    body: metin,
    notificationDetails: const NotificationDetails(
      android: AndroidNotificationDetails(
        _kanalKimligi,
        _kanalAdi,
        channelDescription: _kanalAcikla,
        importance: Importance.defaultImportance,
        priority: Priority.defaultPriority,
        icon: _simge,
      ),
    ),
    payload: 'bugun',
  );
}
