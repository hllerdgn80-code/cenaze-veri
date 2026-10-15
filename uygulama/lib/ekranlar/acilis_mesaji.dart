// Açılış mesajı (URUN-TASLAGI §41, 0.1.7): tam ekran, 6 sn; dokunarak atlama yok, geri tuşu kapatmaz.
import 'dart:async';

import 'package:flutter/material.dart';

import '../cekirdek/metin.dart';

class AcilisMesaji extends StatefulWidget {
  final Duration sure;
  final Widget sonra;
  const AcilisMesaji({super.key, this.sure = const Duration(seconds: 6), required this.sonra});

  @override
  State<AcilisMesaji> createState() => _AcilisMesajiState();
}

class _AcilisMesajiState extends State<AcilisMesaji> {
  static const _zemin = Color(0xFF101828);
  static const _altin = Color(0xFFC9A45C);
  static const _krem = Color(0xFFF2EBDD);
  Timer? _sayac;

  @override
  void initState() {
    super.initState();
    _sayac = Timer(widget.sure, () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(PageRouteBuilder<void>(
        pageBuilder: (_, __, ___) => widget.sonra,
        transitionDuration: const Duration(milliseconds: 600),
        transitionsBuilder: (_, a, __, c) => FadeTransition(opacity: a, child: c),
      ));
    });
  }

  @override
  void dispose() {
    _sayac?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final genislik = MediaQuery.of(context).size.width;
    final simge = (genislik * 0.62).clamp(0.0, 250.0);
    return PopScope(
      canPop: false,
      child: Scaffold(
        backgroundColor: _zemin,
        body: Stack(children: [
          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(28, 36, 28, 40),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Container(
                  width: simge,
                  height: simge,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(32),
                    boxShadow: const [BoxShadow(color: Color(0x73000000), blurRadius: 50, offset: Offset(0, 18))],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Image.asset('assets/acilis/acilis.png', fit: BoxFit.cover),
                ),
                const SizedBox(height: 28),
                const Text(M.acilisArapca,
                    textDirection: TextDirection.rtl,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 30, height: 1.7, color: _altin)),
                const SizedBox(height: 14),
                const Text(M.acilisMeal,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 17, height: 1.5, fontWeight: FontWeight.w500, color: _krem)),
                const SizedBox(height: 10),
                Text(M.acilisKaynak,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, height: 1.4, color: _krem.withValues(alpha: 0.72))),
              ]),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 46,
            child: Center(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(2),
                child: SizedBox(
                  width: 120,
                  height: 3,
                  child: TweenAnimationBuilder<double>(
                    tween: Tween(begin: 0, end: 1),
                    duration: widget.sure,
                    builder: (_, v, __) => LinearProgressIndicator(
                      value: v,
                      minHeight: 3,
                      backgroundColor: _krem.withValues(alpha: 0.18),
                      valueColor: const AlwaysStoppedAnimation(_altin),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}
