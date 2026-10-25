// Sûre ekranı (25.10.2026): Yâsîn, Mülk, Nebe’. Arapça tam metin; sol üstteki düğme sayfayı TÜMÜYLE Türkçe okunuşa çevirir
// ("Türkçe yazılışını oku" ↔ "Arapçasını oku"). Kaynak: assets/veri/sureler.json (tasarim/sureler.json).
import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';

/// 1 → "١", 83 → "٨٣" (Arapça-Hint rakamları)
String arapcaRakam(int n) => n.toString().split('').map((c) => String.fromCharCode(0x0660 + int.parse(c))).join();

class SureEkrani extends StatefulWidget {
  final Map<String, dynamic> sure;
  final String besmeleAr;
  final String besmeleOk;
  const SureEkrani({super.key, required this.sure, required this.besmeleAr, required this.besmeleOk});
  @override
  State<SureEkrani> createState() => _SureEkraniState();
}

class _SureEkraniState extends State<SureEkrani> {
  bool _okunus = false;
  final _kaydirma = ScrollController();

  @override
  void dispose() {
    _kaydirma.dispose();
    super.dispose();
  }

  void _degistir() {
    setState(() => _okunus = !_okunus);
    if (_kaydirma.hasClients) _kaydirma.jumpTo(0);
  }

  String _s(dynamic v) => (v ?? '').toString();

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final sure = widget.sure;
    final ayetler = (sure['ayetler'] as List? ?? const []).whereType<Map>().toList();
    final besmele = sure['besmele'] != false;

    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: const MenuDugmesi(),
            ust: _s(sure['alt']),
            baslik: BuyukBaslik(_s(sure['ad'])),
          ),
          // Sol üstte belirgin geçiş düğmesi
          Padding(
            padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s3),
            child: Align(
              alignment: Alignment.centerLeft,
              child: _GecisDugmesi(
                yazi: _okunus ? M.sureArapcaDugme : M.sureOkunusDugme,
                onTap: _degistir,
              ),
            ),
          ),
          Expanded(
            child: ListView(
              controller: _kaydirma,
              padding: const EdgeInsets.fromLTRB(R.s5, R.s2, R.s5, R.s6),
              children: [
                if (_okunus) ..._okunusKip(r, ayetler, besmele) else ..._arapcaKip(r, ayetler, besmele),
                const SizedBox(height: R.s5),
                Text(_s(sure['k']), textAlign: TextAlign.center, style: Y.soluk(r).copyWith(fontSize: 12)),
              ],
            ),
          ),
        ]),
      ),
    );
  }

  List<Widget> _arapcaKip(CvRenk r, List<Map> ayetler, bool besmele) {
    final arStil = TextStyle(fontFamily: 'serif', fontSize: 24, height: 2.0, color: r.metin);
    return [
      if (besmele) ...[
        Text(widget.besmeleAr,
            textAlign: TextAlign.center,
            textDirection: TextDirection.rtl,
            style: arStil.copyWith(fontSize: 26, color: r.vurguMetin)),
        const SizedBox(height: R.s4),
        Divider(height: 1, thickness: 1, color: r.cizgi),
        const SizedBox(height: R.s4),
      ],
      Text.rich(
        TextSpan(children: [
          for (final a in ayetler) ...[
            TextSpan(text: _s(a['ar']).trim()),
            const TextSpan(text: ' '),
            WidgetSpan(
              alignment: PlaceholderAlignment.middle,
              child: _AyetNo(no: (a['n'] as num).toInt()),
            ),
            const TextSpan(text: ' '),
          ],
        ]),
        textAlign: TextAlign.justify,
        textDirection: TextDirection.rtl,
        style: arStil,
      ),
    ];
  }

  List<Widget> _okunusKip(CvRenk r, List<Map> ayetler, bool besmele) {
    final stil = TextStyle(fontSize: 16, height: 26 / 16, color: r.metin);
    return [
      if (besmele) ...[
        Text(widget.besmeleOk, textAlign: TextAlign.center, style: stil.copyWith(color: r.vurguMetin, fontWeight: FontWeight.w600)),
        const SizedBox(height: R.s4),
        Divider(height: 1, thickness: 1, color: r.cizgi),
        const SizedBox(height: R.s4),
      ],
      for (final a in ayetler)
        Padding(
          padding: const EdgeInsets.only(bottom: R.s3),
          child: Text.rich(
            TextSpan(children: [
              TextSpan(text: '${a['n']}. ', style: TextStyle(fontWeight: FontWeight.w700, color: r.vurguMetin)),
              TextSpan(text: _s(a['ok'])),
            ]),
            textAlign: TextAlign.left,
            style: stil,
          ),
        ),
    ];
  }
}

/// Âyet sonu: küçük daire içinde Arapça-Hint rakamlı numara
class _AyetNo extends StatelessWidget {
  final int no;
  const _AyetNo({required this.no});
  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    // WidgetSpan'da Container(alignment) satırın tamamını kaplar; bu yüzden Center(widthFactor/heightFactor: 1) ile sarılır
    return DecoratedBox(
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(14), border: Border.all(color: r.vurgu, width: 1.2)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
        child: Center(
          widthFactor: 1,
          heightFactor: 1,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),
            child: Text(arapcaRakam(no),
                textDirection: TextDirection.rtl,
                style: TextStyle(fontSize: 13, height: 1.2, fontWeight: FontWeight.w600, color: r.vurguMetin)),
          ),
        ),
      ),
    );
  }
}

/// Belirgin (≥44 px) hap düğme: ikon + yazı
class _GecisDugmesi extends StatelessWidget {
  final String yazi;
  final VoidCallback onTap;
  const _GecisDugmesi({required this.yazi, required this.onTap});
  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Semantics(
      button: true,
      label: yazi,
      child: Material(
        color: r.vurguZemin,
        shape: StadiumBorder(side: BorderSide(color: r.vurgu, width: 1.2)),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 44),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: R.s4),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Ikon('sure', boyut: 20, renk: r.vurguMetin),
                const SizedBox(width: R.s2),
                Flexible(
                  child: Text(yazi,
                      maxLines: 1,
                      softWrap: false,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 15, height: 20 / 15, fontWeight: FontWeight.w600, color: r.vurguMetin)),
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
