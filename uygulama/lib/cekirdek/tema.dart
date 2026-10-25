// Tasarım sistemi (tasarim/TASARIM-SISTEMI.md §1–§4): L13 paleti, koyu varsayılan + açık tema.
// Kural: altından başka renk yok; tek istisna şehit kartının al şeridi.
import 'dart:ui' show FontFeature;

import 'package:flutter/material.dart';

class R {
  R._();
  // Boşluk ızgarası (4'ün katı)
  static const double s1 = 4, s2 = 8, s3 = 12, s4 = 16, s5 = 20, s6 = 24, s8 = 32;
  // Köşe yarıçapı
  static const double kart = 20, dugme = 14, cip = 14;
  // Marka
  static const komur = Color(0xFF25282D);
  static const altin = Color(0xFFC9A45C);
  static const krem = Color(0xFFF2EBDD);
  static const sehitAl = Color(0xFFE30A17);
  static const gazeteKagit = Color(0xFFFBF8F1);
  static const gazeteMurekkep = Color(0xFF1B1C1E);
}

/// Temaya bağlı renkler (CSS değişkenlerinin karşılığı)
@immutable
class CvRenk extends ThemeExtension<CvRenk> {
  final Color zemin, yuzey, yuzey2, cizgi, metin, metin2, metin3, vurgu, vurguMetin, vurguUst, vurguZemin;
  const CvRenk({
    required this.zemin,
    required this.yuzey,
    required this.yuzey2,
    required this.cizgi,
    required this.metin,
    required this.metin2,
    required this.metin3,
    required this.vurgu,
    required this.vurguMetin,
    required this.vurguUst,
    required this.vurguZemin,
  });

  static const koyu = CvRenk(
    zemin: Color(0xFF1F2226),
    yuzey: Color(0xFF2A2E34),
    yuzey2: Color(0xFF33383F),
    cizgi: Color(0x17F2EBDD), // krem %9
    metin: Color(0xFFF2EBDD),
    metin2: Color(0xB3F2EBDD), // %70
    metin3: Color(0x75F2EBDD), // %46
    vurgu: Color(0xFFC9A45C),
    vurguMetin: Color(0xFFD9B873),
    vurguUst: Color(0xFF25282D),
    vurguZemin: Color(0x21C9A45C), // %13
  );

  static const acik = CvRenk(
    zemin: Color(0xFFF2EBDD),
    yuzey: Color(0xFFFBF8F2),
    yuzey2: Color(0xFFEEE5D3),
    cizgi: Color(0x1A25282D), // kömür %10
    metin: Color(0xFF25282D),
    metin2: Color(0xB825282D), // %72
    metin3: Color(0x8025282D), // %50
    vurgu: Color(0xFFC9A45C),
    vurguMetin: Color(0xFF8A6A2C),
    vurguUst: Color(0xFF25282D),
    vurguZemin: Color(0x2EC9A45C), // %18
  );

  @override
  CvRenk copyWith() => this;

  @override
  CvRenk lerp(ThemeExtension<CvRenk>? other, double t) {
    if (other is! CvRenk) return this;
    Color l(Color a, Color b) => Color.lerp(a, b, t)!;
    return CvRenk(
      zemin: l(zemin, other.zemin),
      yuzey: l(yuzey, other.yuzey),
      yuzey2: l(yuzey2, other.yuzey2),
      cizgi: l(cizgi, other.cizgi),
      metin: l(metin, other.metin),
      metin2: l(metin2, other.metin2),
      metin3: l(metin3, other.metin3),
      vurgu: l(vurgu, other.vurgu),
      vurguMetin: l(vurguMetin, other.vurguMetin),
      vurguUst: l(vurguUst, other.vurguUst),
      vurguZemin: l(vurguZemin, other.vurguZemin),
    );
  }
}

extension RenkErisim on BuildContext {
  CvRenk get renk => Theme.of(this).extension<CvRenk>() ?? CvRenk.koyu;
}

ThemeData temaYap(bool koyu) {
  final r = koyu ? CvRenk.koyu : CvRenk.acik;
  final sema = ColorScheme(
    brightness: koyu ? Brightness.dark : Brightness.light,
    primary: r.vurgu,
    onPrimary: r.vurguUst,
    primaryContainer: r.vurguZemin,
    onPrimaryContainer: r.vurguMetin,
    secondary: r.vurgu,
    onSecondary: r.vurguUst,
    error: r.vurguMetin,
    onError: r.vurguUst,
    surface: r.yuzey,
    onSurface: r.metin,
    onSurfaceVariant: r.metin2,
    surfaceContainerHighest: r.yuzey2,
    outlineVariant: r.cizgi,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: koyu ? Brightness.dark : Brightness.light,
    colorScheme: sema,
    scaffoldBackgroundColor: r.zemin,
    canvasColor: r.zemin,
    dividerColor: r.cizgi,
    splashFactory: InkRipple.splashFactory,
    extensions: [r],
    snackBarTheme: SnackBarThemeData(
      backgroundColor: r.yuzey2,
      contentTextStyle: TextStyle(color: r.metin, fontSize: 14),
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.dugme)),
    ),
    textSelectionTheme: TextSelectionThemeData(cursorColor: r.vurgu),
  );
}

/// Tipografi (TASARIM-SISTEMI §2); sistem yazı tipi, rakamlar eşit genişlik
class Y {
  Y._();
  static const _tab = [FontFeature.tabularFigures()];
  static TextStyle acilis(CvRenk r) =>
      TextStyle(fontSize: 30, height: 36 / 30, fontWeight: FontWeight.w700, color: r.metin);
  static TextStyle buyuk(CvRenk r) =>
      TextStyle(fontSize: 26, height: 32 / 26, fontWeight: FontWeight.w700, letterSpacing: -0.4, color: r.metin);
  static TextStyle kartAd(CvRenk r) =>
      TextStyle(fontSize: 22, height: 28 / 22, fontWeight: FontWeight.w600, letterSpacing: -0.3, color: r.metin);
  static TextStyle adim(CvRenk r) =>
      TextStyle(fontSize: 20, height: 26 / 20, fontWeight: FontWeight.w600, color: r.metin);
  static TextStyle satir(CvRenk r) => TextStyle(fontSize: 17, height: 22 / 17, color: r.metin);
  static TextStyle govde(CvRenk r) => TextStyle(fontSize: 15, height: 20 / 15, color: r.metin2);
  static TextStyle kucuk(CvRenk r) =>
      TextStyle(fontSize: 13, height: 18 / 13, color: r.metin2, fontFeatures: _tab);
  static TextStyle soluk(CvRenk r) =>
      TextStyle(fontSize: 13, height: 18 / 13, color: r.metin3, fontFeatures: _tab);
  static TextStyle ustEtiket(CvRenk r) => TextStyle(
      fontSize: 11, height: 13 / 11, fontWeight: FontWeight.w600, letterSpacing: 1.32, color: r.vurguMetin, fontFeatures: _tab);
  static TextStyle sutunEtiket(CvRenk r) =>
      TextStyle(fontSize: 10, height: 12 / 10, fontWeight: FontWeight.w600, letterSpacing: 1.2, color: r.metin3);
  static TextStyle sekme(Color c) =>
      TextStyle(fontSize: 10, height: 12 / 10, fontWeight: FontWeight.w600, letterSpacing: -0.4, color: c);
}
