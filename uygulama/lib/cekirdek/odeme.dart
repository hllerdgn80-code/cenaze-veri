// Tam Sayfa ödemesi: YALNIZ Google Play Faturalandırma (URUN-TASLAGI §38). Kart bilgisi uygulamaya gelmez.
// Ürün: tek seferlik TÜKETİLEBİLİR `tam_sayfa_ilan` (fiyat Play Console'da 200 TRY). Satın alma, Worker'da doğrulandıktan SONRA tüketilir.
// Restore (geri yükleme) yok: ürün tüketildiği için bir sonraki ilan yeniden satın alınabilir.
import 'dart:async';
import 'dart:io' show Platform;

import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:in_app_purchase_android/in_app_purchase_android.dart';

const String tamSayfaUrunKimligi = 'tam_sayfa_ilan';

/// Mağazadan okunan ürün bilgisi ([fiyat]: yerelleştirilmiş, örn. "₺200,00")
class UrunBilgi {
  final String fiyat;
  const UrunBilgi(this.fiyat);
}

enum OdemeDurumu { tamam, iptal, hata }

/// Satın alma sonucu. [tamam] iken [token] ve [siparisNo] dolu.
class OdemeSonuc {
  final OdemeDurumu durum;
  final String token;
  final String siparisNo;
  final Object? ham; // tüketme için platform nesnesi
  const OdemeSonuc._(this.durum, this.token, this.siparisNo, this.ham);
  const OdemeSonuc.tamam({required String token, required String siparisNo, Object? ham})
      : this._(OdemeDurumu.tamam, token, siparisNo, ham);
  const OdemeSonuc.iptal() : this._(OdemeDurumu.iptal, '', '', null);
  const OdemeSonuc.hata() : this._(OdemeDurumu.hata, '', '', null);
}

/// Ödeme kapısı: gerçek uygulamada [PlayOdeme]; testlerde sahtesi verilir.
abstract class OdemeKapisi {
  /// Ürün mağazada tanımlı ve sorgulanabiliyorsa bilgisi, değilse null (düğme pasif kalır).
  Future<UrunBilgi?> urunSorgula();
  Future<OdemeSonuc> satinAl();

  /// Sunucu doğrulaması BAŞARILI olduktan sonra çağrılır; ürünü tüketir.
  Future<void> tuket(OdemeSonuc s);
}

class PlayOdeme implements OdemeKapisi {
  ProductDetails? _urun;

  @override
  Future<UrunBilgi?> urunSorgula() async {
    try {
      if (!Platform.isAndroid) return null;
      final iap = InAppPurchase.instance;
      if (!await iap.isAvailable()) return null;
      final y = await iap.queryProductDetails({tamSayfaUrunKimligi});
      if (y.error != null || y.productDetails.isEmpty) return null;
      _urun = y.productDetails.first;
      return UrunBilgi(_urun!.price);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<OdemeSonuc> satinAl() async {
    final u = _urun;
    if (u == null) return const OdemeSonuc.hata();
    final iap = InAppPurchase.instance;
    final c = Completer<OdemeSonuc>();
    late final StreamSubscription<List<PurchaseDetails>> abone;
    abone = iap.purchaseStream.listen((liste) {
      for (final p in liste) {
        if (p.productID != tamSayfaUrunKimligi || c.isCompleted) continue;
        switch (p.status) {
          case PurchaseStatus.pending:
            break;
          case PurchaseStatus.purchased:
          case PurchaseStatus.restored:
            c.complete(OdemeSonuc.tamam(
                token: p.verificationData.serverVerificationData, siparisNo: p.purchaseID ?? '', ham: p));
          case PurchaseStatus.canceled:
            c.complete(const OdemeSonuc.iptal());
          case PurchaseStatus.error:
            c.complete(const OdemeSonuc.hata());
        }
      }
    }, onError: (_) {
      if (!c.isCompleted) c.complete(const OdemeSonuc.hata());
    });
    try {
      // autoConsume: false — sunucu doğrulaması bitmeden tüketilmez
      final basladi = await iap.buyConsumable(purchaseParam: PurchaseParam(productDetails: u), autoConsume: false);
      if (!basladi && !c.isCompleted) c.complete(const OdemeSonuc.hata());
      return await c.future.timeout(const Duration(minutes: 10), onTimeout: () => const OdemeSonuc.iptal());
    } catch (_) {
      return const OdemeSonuc.hata();
    } finally {
      await abone.cancel();
    }
  }

  @override
  Future<void> tuket(OdemeSonuc s) async {
    final p = s.ham;
    if (p is! PurchaseDetails) return;
    try {
      final ek = InAppPurchase.instance.getPlatformAddition<InAppPurchaseAndroidPlatformAddition>();
      await ek.consumePurchase(p);
    } catch (_) {
      // tüketilemezse bir sonraki açılışta "zaten sahip" olarak görünebilir; ilan yine yayında kalır
    }
  }
}
