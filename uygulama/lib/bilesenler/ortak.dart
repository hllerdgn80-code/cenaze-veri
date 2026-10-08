// Ortak bileşenler: başlık çubuğu (40 | 1fr | 40), yuvarlak düğme, bölüm başlığı, boş durum,
// ana/ikincil düğme, kutucuk, hap, arama alanı. Simetri kuralları: TASARIM-SISTEMI §9.
import 'package:flutter/material.dart';

import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';
import 'ikonlar.dart';

/// Ekran üstü: sol (logo/geri) · orta (üst etiket + büyük başlık) · sağ (⋮); sol ve sağ AYNI genişlik
class BaslikCubugu extends StatelessWidget {
  final Widget sol;
  final Widget sag;
  final String ust;
  final Widget baslik;
  final double yanGenislik;
  const BaslikCubugu({
    super.key,
    required this.sol,
    required this.sag,
    required this.ust,
    required this.baslik,
    this.yanGenislik = 40,
  });

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Padding(
      padding: const EdgeInsets.fromLTRB(R.s5, R.s2, R.s5, R.s3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          SizedBox(width: yanGenislik, child: Center(child: sol)),
          const SizedBox(width: R.s3),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(trBuyuk(ust), textAlign: TextAlign.center, style: Y.ustEtiket(r)),
                const SizedBox(height: 2),
                baslik,
              ],
            ),
          ),
          const SizedBox(width: R.s3),
          SizedBox(width: yanGenislik, child: Center(child: sag)),
        ],
      ),
    );
  }
}

/// Ortalı büyük başlık metni (iki satıra inebilir, kesme yok)
class BuyukBaslik extends StatelessWidget {
  final String metin;
  const BuyukBaslik(this.metin, {super.key});
  @override
  Widget build(BuildContext context) =>
      Text(metin, textAlign: TextAlign.center, style: Y.buyuk(context.renk));
}

/// 40×40 yuvarlak düğme (geri, ⋮) ya da hap (genislik > 40)
class YuvarlakDugme extends StatelessWidget {
  final String ikon;
  final String? yazi;
  final VoidCallback onTap;
  final double genislik;
  final String anlam;
  const YuvarlakDugme({
    super.key,
    required this.ikon,
    required this.onTap,
    required this.anlam,
    this.yazi,
    this.genislik = 40,
  });

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Semantics(
      button: true,
      label: anlam,
      child: Material(
        color: r.yuzey,
        borderRadius: BorderRadius.circular(20),
        child: InkWell(
          borderRadius: BorderRadius.circular(20),
          onTap: onTap,
          child: SizedBox(
            width: genislik,
            height: 40,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Ikon(ikon, boyut: 20, renk: r.metin2),
                if (yazi != null) ...[
                  const SizedBox(width: 2),
                  Flexible(
                    child: Text(yazi!,
                        maxLines: 1,
                        softWrap: false,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: r.metin2)),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Logo işareti düğmesi (dokununca İlanlar ana ekranı)
class LogoDugme extends StatelessWidget {
  final VoidCallback onTap;
  const LogoDugme({super.key, required this.onTap});
  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: 'İlanlar ana ekranı',
        child: GestureDetector(onTap: onTap, child: const Logo(boyut: 40, yaricap: 12)),
      );
}

/// Bölüm başlığı: — METİN — (büyük harf, iki yanda ince çizgi)
class Bolum extends StatelessWidget {
  final String metin;
  const Bolum(this.metin, {super.key});
  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Padding(
      padding: const EdgeInsets.only(top: R.s6, bottom: R.s3),
      // Metin, iki yanda en az 24 px çizgi + boşluk kalacak şekilde sınırlanır; uzun ilçe adı taşmaz, … ile kesilir.
      child: LayoutBuilder(
        builder: (context, c) => Row(
          children: [
            Expanded(child: Container(height: 1, color: r.cizgi)),
            const SizedBox(width: R.s3),
            ConstrainedBox(
              constraints: BoxConstraints(maxWidth: (c.maxWidth - 2 * (24 + R.s3)).clamp(0.0, double.infinity)),
              child: Text(
                trBuyuk(metin),
                textAlign: TextAlign.center,
                maxLines: 1,
                softWrap: false,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    fontSize: 11, height: 13 / 11, fontWeight: FontWeight.w600, letterSpacing: 1.32, color: r.metin3),
              ),
            ),
            const SizedBox(width: R.s3),
            Expanded(child: Container(height: 1, color: r.cizgi)),
          ],
        ),
      ),
    );
  }
}

/// Altın zeminli daire içinde ikon
class Daire extends StatelessWidget {
  final String ikon;
  final double boyut;
  const Daire(this.ikon, {super.key, this.boyut = 72});
  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      width: boyut,
      height: boyut,
      decoration: BoxDecoration(color: r.vurguZemin, shape: BoxShape.circle),
      alignment: Alignment.center,
      child: Ikon(ikon, boyut: boyut * 0.42, renk: r.vurguMetin),
    );
  }
}

/// Boş durum: daire + başlık + açıklama, ortalı
class BosDurum extends StatelessWidget {
  final String? baslik;
  final String? aciklama;
  final String ikon;
  final bool kucuk;
  const BosDurum({super.key, this.baslik, this.aciklama, this.ikon = 'kemer', this.kucuk = false});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Padding(
      padding: EdgeInsets.symmetric(vertical: kucuk ? R.s5 : R.s8),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 280),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Daire(ikon, boyut: kucuk ? 56 : 72),
              if (baslik != null) ...[
                const SizedBox(height: R.s4),
                Text(baslik!,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 17, height: 22 / 17, fontWeight: FontWeight.w600, color: r.metin)),
              ],
              if (aciklama != null) ...[
                const SizedBox(height: R.s2),
                Text(aciklama!, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Tam genişlik altın düğme (52 yükseklik); onTap null → pasif (%32)
class AnaDugme extends StatelessWidget {
  final String yazi;
  final VoidCallback? onTap;
  final double yukseklik;
  const AnaDugme(this.yazi, {super.key, this.onTap, this.yukseklik = 52});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final pasif = onTap == null;
    return Opacity(
      opacity: pasif ? 0.32 : 1,
      child: Material(
        color: r.vurgu,
        borderRadius: BorderRadius.circular(R.dugme),
        child: InkWell(
          borderRadius: BorderRadius.circular(R.dugme),
          onTap: onTap,
          child: SizedBox(
            height: yukseklik,
            width: double.infinity,
            child: Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: R.s3),
                child: Text(yazi,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: r.vurguUst)),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Yüzey renkli ikincil düğme
class IkincilDugme extends StatelessWidget {
  final String yazi;
  final VoidCallback? onTap;
  final double yukseklik;
  final bool secili;
  const IkincilDugme(this.yazi, {super.key, this.onTap, this.yukseklik = 48, this.secili = false});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Material(
      color: secili ? r.vurguZemin : r.yuzey2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(R.dugme),
        side: BorderSide(color: secili ? r.vurgu : Colors.transparent),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(R.dugme),
        onTap: onTap,
        child: SizedBox(
          height: yukseklik,
          width: double.infinity,
          child: Center(
            child: Text(yazi,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 15, fontWeight: FontWeight.w600, color: secili ? r.vurguMetin : r.metin)),
          ),
        ),
      ),
    );
  }
}

/// İki eşit düğme yan yana
class IkiliSatir extends StatelessWidget {
  final Widget sol, sag;
  const IkiliSatir({super.key, required this.sol, required this.sag});
  @override
  Widget build(BuildContext context) => Row(children: [
        Expanded(child: sol),
        const SizedBox(width: R.s3),
        Expanded(child: sag),
      ]);
}

/// Kutucuk: altın halka içinde ikon + ad (eşit boy ızgara)
class Kutucuk extends StatelessWidget {
  final String ikon;
  final String ad;
  final VoidCallback onTap;
  final double yukseklik;
  const Kutucuk({super.key, required this.ikon, required this.ad, required this.onTap, this.yukseklik = 132});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Material(
      color: r.yuzey,
      borderRadius: BorderRadius.circular(R.kart),
      child: InkWell(
        borderRadius: BorderRadius.circular(R.kart),
        onTap: onTap,
        child: SizedBox(
          height: yukseklik,
          child: Padding(
            padding: const EdgeInsets.all(R.s3),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: r.vurgu, width: 1.4)),
                  alignment: Alignment.center,
                  child: Ikon(ikon, boyut: 24, renk: r.vurguMetin),
                ),
                const SizedBox(height: R.s3),
                Text(ad,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 15, height: 19 / 15, fontWeight: FontWeight.w600, color: r.metin)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Kutucuk ızgarası: 2 eşit sütun; tek kalan son kutucuk tam genişlik
class KutucukIzgara extends StatelessWidget {
  final List<Widget> kutular;
  const KutucukIzgara(this.kutular, {super.key});
  @override
  Widget build(BuildContext context) {
    final satirlar = <Widget>[];
    for (int i = 0; i < kutular.length; i += 2) {
      if (i > 0) satirlar.add(const SizedBox(height: R.s3));
      if (i + 1 < kutular.length) {
        satirlar.add(Row(children: [
          Expanded(child: kutular[i]),
          const SizedBox(width: R.s3),
          Expanded(child: kutular[i + 1]),
        ]));
      } else {
        satirlar.add(kutular[i]);
      }
    }
    return Column(children: satirlar);
  }
}

/// Ortalı hap etiketi ("Yakını paylaştı", "ŞEHİT", "ÖRNEK")
class Hap extends StatelessWidget {
  final String yazi;
  final Color zemin;
  final Color renk;
  const Hap(this.yazi, {super.key, required this.zemin, required this.renk});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: R.s3, vertical: 4),
        decoration: BoxDecoration(color: zemin, borderRadius: BorderRadius.circular(999)),
        child: Text(yazi,
            style: TextStyle(fontSize: 11, height: 13 / 11, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: renk)),
      );
}

/// Arama alanı: 20 | yazı (ortalı) | 20
class AramaAlani extends StatelessWidget {
  final String ipucu;
  final ValueChanged<String> onChanged;
  final TextEditingController? denetleyici;
  const AramaAlani({super.key, required this.ipucu, required this.onChanged, this.denetleyici});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      height: 44,
      margin: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s3),
      padding: const EdgeInsets.symmetric(horizontal: R.s4),
      decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.dugme)),
      child: Row(children: [
        Ikon('ara', boyut: 20, renk: r.metin3),
        const SizedBox(width: R.s2),
        Expanded(
          child: TextField(
            controller: denetleyici,
            onChanged: onChanged,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 16, color: r.metin),
            decoration: InputDecoration(
              isCollapsed: true,
              border: InputBorder.none,
              hintText: ipucu,
              hintStyle: TextStyle(fontSize: 16, color: r.metin3),
            ),
          ),
        ),
        const SizedBox(width: R.s2),
        const SizedBox(width: 20),
      ]),
    );
  }
}

/// Kısa bildirim (snackbar), ortalı
void bildir(BuildContext context, String metin) {
  final m = ScaffoldMessenger.maybeOf(context);
  if (m == null) return;
  m.hideCurrentSnackBar();
  m.showSnackBar(SnackBar(
    content: Text(metin, textAlign: TextAlign.center),
    duration: const Duration(milliseconds: 1700),
  ));
}
