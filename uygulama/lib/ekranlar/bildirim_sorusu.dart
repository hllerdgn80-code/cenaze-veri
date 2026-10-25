// İlk açılış kartı (URUN-TASLAGI §36): başka hiçbir ekrandan önce tek soru.
// Evet → sistem bildirim izni (Android 13+) → il/ilçe seçimi. Şimdi değil → 7 gün yeniden sorulmaz.
import 'package:flutter/material.dart';

import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';

class BildirimSorusu extends StatefulWidget {
  const BildirimSorusu({super.key});
  @override
  State<BildirimSorusu> createState() => _BildirimSorusuState();
}

class _BildirimSorusuState extends State<BildirimSorusu> {
  bool _mesgul = false; // çift dokunuşta iki kez izin istenmesin

  Future<void> _sec(bool evet) async {
    if (_mesgul) return;
    setState(() => _mesgul = true);
    final d = Kapsam.oku(context);
    await d.bildirimSorusunuYanitla(evet);
    // Kart kapanır (ana pencere seçim ekranına/kabuğa geçer); yine de ekran hâlâ açıksa düğmeler çözülür
    if (mounted) setState(() => _mesgul = false);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(R.s5),
            child: Container(
              key: const ValueKey('izin_karti'),
              padding: const EdgeInsets.all(R.s5),
              decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Daire('zil', boyut: 64),
                const SizedBox(height: R.s4),
                Text(M.izinSoru,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18, height: 24 / 18, fontWeight: FontWeight.w600, color: r.metin)),
                const SizedBox(height: R.s5),
                AnaDugme(M.izinEvet, onTap: _mesgul ? null : () => _sec(true)),
                const SizedBox(height: R.s3),
                IkincilDugme(M.izinHayir, yukseklik: 52, onTap: _mesgul ? null : () => _sec(false)),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
