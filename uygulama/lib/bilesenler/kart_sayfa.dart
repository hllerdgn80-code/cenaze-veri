// Ekranda tek ilan (URUN §51, 16.10.2026): her ilan kartı görünür alanı doldurur, kaydırınca sıradaki kartın başına oturur.
// Seçilen yol (en az riskli): kartlar kendi yüksekliğinde KALIR ama en az görünür alan kadardır (minHeight); ListView aynı kalır
// (RefreshIndicator, denetleyici, bölüm başlıkları değişmez). Snap: özel ScrollPhysics, kartların gerçek başlangıç ofsetlerini
// (ekrana kaydolmuş kartların RenderBox konumu) kullanır; bu yüzden bölüm başlığı/ilan kutusu gibi farklı yükseklikler bozmaz.
// Kart ekrandan uzunsa (hedef bir ekrandan uzakta) snap yapılmaz: kart içinde serbest kaydırılır.
import 'package:flutter/material.dart';
import 'package:flutter/physics.dart';

class KartKaydi {
  final Set<BuildContext> _k = {};
  void ekle(BuildContext c) => _k.add(c);
  void cikar(BuildContext c) => _k.remove(c);

  /// Kartların kaydırma uzayındaki başlangıç ofsetleri (sıralı)
  List<double> baslangiclar(BuildContext liste, double pixels) {
    final lb = liste.findRenderObject();
    if (lb is! RenderBox || !lb.attached) return const [];
    final ust = lb.localToGlobal(Offset.zero).dy;
    final out = <double>[];
    for (final c in _k) {
      if (!c.mounted) continue;
      final rb = c.findRenderObject();
      if (rb is! RenderBox || !rb.attached || !rb.hasSize) continue;
      out.add(rb.localToGlobal(Offset.zero).dy - ust + pixels);
    }
    out.sort();
    return out;
  }
}

class KartSayfasi extends InheritedWidget {
  final double? yukseklik; // bir kartın (alt boşluğuyla) kaplayacağı görünür yükseklik
  final KartKaydi kayit;
  const KartSayfasi({super.key, required this.yukseklik, required this.kayit, required super.child});

  static KartSayfasi? of(BuildContext c) => c.dependOnInheritedWidgetOfExactType<KartSayfasi>();

  @override
  bool updateShouldNotify(KartSayfasi o) => o.yukseklik != yukseklik;
}

/// Kartı listeye kaydeder (snap noktası olarak)
class KartIsareti extends StatefulWidget {
  final KartKaydi? kayit;
  final Widget child;
  const KartIsareti({super.key, required this.kayit, required this.child});
  @override
  State<KartIsareti> createState() => _KartIsaretiState();
}

class _KartIsaretiState extends State<KartIsareti> {
  KartKaydi? _k;
  @override
  void initState() {
    super.initState();
    _k = widget.kayit;
    _k?.ekle(context);
  }

  @override
  void dispose() {
    _k?.cikar(context);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

class KartSnapFizigi extends ScrollPhysics {
  final List<double> Function(double pixels) noktalar;
  const KartSnapFizigi({required this.noktalar, super.parent});

  @override
  KartSnapFizigi applyTo(ScrollPhysics? ancestor) => KartSnapFizigi(noktalar: noktalar, parent: buildParent(ancestor));

  @override
  Simulation? createBallisticSimulation(ScrollMetrics position, double velocity) {
    final tolerance = toleranceFor(position);
    final disarida = (velocity <= 0 && position.pixels <= position.minScrollExtent) ||
        (velocity >= 0 && position.pixels >= position.maxScrollExtent);
    if (disarida) return super.createBallisticSimulation(position, velocity);
    final n = noktalar(position.pixels)
        .map((x) => x.clamp(position.minScrollExtent, position.maxScrollExtent).toDouble())
        .toList();
    if (n.isEmpty) return super.createBallisticSimulation(position, velocity);
    final p = position.pixels;
    double? hedef;
    if (velocity > 250) {
      for (final x in n) {
        if (x > p + 1) {
          hedef = x;
          break;
        }
      }
    } else if (velocity < -250) {
      for (final x in n.reversed) {
        if (x < p - 1) {
          hedef = x;
          break;
        }
      }
    } else {
      hedef = n.reduce((a, b) => (a - p).abs() <= (b - p).abs() ? a : b);
    }
    // uzun kart: hedef bir ekrandan uzaktaysa kart içinde serbest kaydır
    if (hedef == null || (hedef - p).abs() > position.viewportDimension) {
      return super.createBallisticSimulation(position, velocity);
    }
    if ((hedef - p).abs() < tolerance.distance && velocity.abs() < tolerance.velocity) return null;
    return ScrollSpringSimulation(spring, p, hedef, velocity, tolerance: tolerance);
  }
}

/// Kartları ekran boyunda gösteren kaydırma listesi (İlanlar ve Sayfam)
class KartListesi extends StatefulWidget {
  final List<Widget> children;
  final ScrollController? controller;
  final EdgeInsets padding;
  const KartListesi({super.key, required this.children, this.controller, this.padding = EdgeInsets.zero});
  @override
  State<KartListesi> createState() => _KartListesiState();
}

class _KartListesiState extends State<KartListesi> {
  final _kayit = KartKaydi();
  final _anahtar = GlobalKey();

  List<double> _noktalar(double pixels) {
    final c = _anahtar.currentContext;
    return c == null ? const [] : _kayit.baslangiclar(c, pixels);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, k) {
      final h = k.maxHeight.isFinite ? k.maxHeight - widget.padding.top : null;
      return KartSayfasi(
        yukseklik: h,
        kayit: _kayit,
        child: ListView(
          key: _anahtar,
          controller: widget.controller,
          cacheExtent: 100000, // tüm kartlar kurulu: snap noktaları bilinsin (liste kısa: bir il, 7 gün)
          physics: KartSnapFizigi(noktalar: _noktalar, parent: const AlwaysScrollableScrollPhysics()),
          padding: widget.padding,
          children: widget.children,
        ),
      );
    });
  }
}
