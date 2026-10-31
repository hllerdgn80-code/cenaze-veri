// Zorunlu güncelleme ekranı + kapı (URUN-TASLAGI §42). Kapı açılışın hemen sonrasında devreye girer.
import 'package:flutter/material.dart';

import '../cekirdek/durum.dart';
import '../cekirdek/surum.dart';

class GuncellemeGerekli extends StatelessWidget {
  final String mesaj;

  /// Testte enjekte edilir; null = çalışan platform. [iosUrl]: surum.json `ios_magaza_url`.
  final bool? ios;
  final String? iosUrl;
  const GuncellemeGerekli({super.key, required this.mesaj, this.ios, this.iosUrl});

  static const _zemin = Color(0xFF101828);
  static const _altin = Color(0xFFC9A45C);
  static const _krem = Color(0xFFF2EBDD);

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: Scaffold(
        backgroundColor: _zemin,
        body: SafeArea(
          child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(32, 36, 32, 40),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: Image.asset('assets/acilis/acilis.png', width: 140, height: 140, fit: BoxFit.cover),
              ),
              const SizedBox(height: 28),
              const Text('Güncelleme gerekli',
                  textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: _altin)),
              const SizedBox(height: 14),
              Text(mesaj, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, height: 1.5, color: _krem)),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  key: const ValueKey('guncelle_dugme'),
                  style: FilledButton.styleFrom(
                      backgroundColor: _altin, foregroundColor: _zemin, padding: const EdgeInsets.symmetric(vertical: 16)),
                  onPressed: () => magazayiAc(ios: ios, iosUrl: iosUrl),
                  child: Text('${magazaAdi(ios ?? iosMu)}\'da güncelle', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                ),
              ),
            ]),
          ),
          ),
        ),
      ),
    );
  }
}

/// Alt ağacı [child] sürüm kontrolü bitene kadar bekletir; zorunluysa yalnız güncelleme ekranını gösterir.
/// Ağ hatası = kapı açık. Uygulama öne dönünce sürüm yeniden kontrol edilir.
class SurumKapisi extends StatefulWidget {
  final Widget child;
  const SurumKapisi({super.key, required this.child});

  @override
  State<SurumKapisi> createState() => _SurumKapisiState();
}

class _SurumKapisiState extends State<SurumKapisi> with WidgetsBindingObserver {
  AppDurum? _d;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_d == null) {
      _d = Kapsam.oku(context);
      _d!.surumKontrol();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _d?.surumKontrol();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    if (d.guncellemeZorunlu) {
      return GuncellemeGerekli(mesaj: d.surum?.mesaj ?? varsayilanGuncellemeMesaji, ios: d.ios, iosUrl: d.surum?.iosMagazaUrl);
    }
    if (d.surumBekliyor) return const Scaffold(backgroundColor: Color(0xFF101828));
    return widget.child;
  }
}

/// Zorunlu olmayan bilgi çubuğu: yeni sürüm var (kapı değil).
class GuncellemeCubugu extends StatelessWidget {
  const GuncellemeCubugu({super.key});

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    if (!d.guncellemeOnerilir) return const SizedBox.shrink();
    return Material(
      color: const Color(0xFF101828),
      child: InkWell(
        key: const ValueKey('guncelleme_cubugu'),
        onTap: () => magazayiAc(ios: d.ios, iosUrl: d.surum?.iosMagazaUrl),
        child: const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(children: [
            Expanded(child: Text('Yeni sürüm var', style: TextStyle(fontSize: 13, color: Color(0xFFF2EBDD)))),
            Text('Güncelle', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Color(0xFFC9A45C))),
          ]),
        ),
      ),
    );
  }
}
