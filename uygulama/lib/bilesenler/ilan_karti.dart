// İlan kartı (TASARIM-SISTEMI §5): ortalı; üst etiket "CENAZE · 8 EKİM · ÖĞLE" (tarih şeridindeki günle aynı),
// ad, vefat satırı, mahalle · ilçe, iki eşit sütun (Cenaze namazı | Defin), altta "Sayfama kaydet".
// Kaynak adı ve anne/baba adı GÖSTERİLMEZ (URUN-TASLAGI §16.5, §28).
import 'dart:ui' show FontFeature;

import 'package:flutter/material.dart';

import '../cekirdek/cinsiyet.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/ilan.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';
import 'ikonlar.dart';
import 'ortak.dart';

class IlanKarti extends StatelessWidget {
  final Ilan ilan;
  final bool sayacli; // Sayfam görünümü
  const IlanKarti({super.key, required this.ilan, this.sayacli = false});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    final sh = ilan.sehit;
    final np = ilan.namazParcalari;
    final cg = ilan.cenazeGunu;

    final icerik = <Widget>[
      if (sh) ...[
        const Hap(M.sehitEtiket, zemin: R.sehitAl, renk: Colors.white),
        const SizedBox(height: R.s3),
      ],
      if (ilan.aile) ...[
        Hap(M.kartYakini, zemin: r.vurguZemin, renk: r.vurguMetin),
        const SizedBox(height: R.s3),
      ],
      Text(trBuyuk(ilan.etiket), textAlign: TextAlign.center, style: Y.ustEtiket(r)),
      const SizedBox(height: R.s2),
      Text('${sh && ilan.rutbe != null ? '${ilan.rutbe} ' : ''}${ilan.adSoyad}',
          textAlign: TextAlign.center, style: Y.kartAd(r)),
      const SizedBox(height: 2),
      if (ilan.vefatTarihi != null)
        Text(
          '${sh ? 'Şehit oldu' : 'Vefat'}: ${tarih(ilan.vefatTarihi)}${ilan.yas != null ? ' · ${ilan.yas} yaş' : ''}',
          textAlign: TextAlign.center,
          style: Y.soluk(r),
        ),
      if ((ilan.mahalle ?? '').isNotEmpty || (ilan.ilce ?? '').isNotEmpty)
        Text(
          [baslikHarf(ilan.mahalle), ilan.ilce ?? ''].where((x) => x.isNotEmpty).join(' · '),
          textAlign: TextAlign.center,
          style: Y.soluk(r),
        ),
      _Ayrac(r),
      if (sh && ilan.toren != null) ...[
        Text(trBuyuk(M.sehitToren), textAlign: TextAlign.center, style: Y.sutunEtiket(r)),
        const SizedBox(height: R.s1),
        Text(ilan.toren!, textAlign: TextAlign.center, style: Y.kucuk(r)),
        _Ayrac(r),
      ],
      IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: _Sutun(baslik: M.kartNamaz, satirlar: [
                np[0],
                np[1],
                if (cg.isNotEmpty) tarihGun(cg),
              ]),
            ),
            Container(width: 1, color: r.cizgi, margin: const EdgeInsets.symmetric(horizontal: R.s3)),
            Expanded(
              child: _Sutun(baslik: M.kartDefin, satirlar: [
                baslikHarf(ilan.definYeri),
                if (ilan.ilDisiIl != null) '${ilan.ilDisiIl}${ilan.ilDisiIlce != null ? ' / ${ilan.ilDisiIlce}' : ''}',
              ]),
            ),
          ],
        ),
      ),
      if (sh) ...[
        const SizedBox(height: R.s4),
        Text(M.sehitKapanis, textAlign: TextAlign.center, style: Y.kucuk(r).copyWith(fontStyle: FontStyle.italic)),
      ],
      if (sayacli) ...[
        _Ayrac(r),
        SayacBlok(ilan: ilan),
      ] else ...[
        const SizedBox(height: R.s5),
        d.kayitli(ilan.id)
            ? Opacity(opacity: 0.6, child: _KayitliDugme(r))
            : AnaDugme(M.kartKaydet, onTap: () async {
                await d.sayfamaEkle(ilan);
                if (context.mounted) bildir(context, M.bildirimKaydedildi);
              }),
      ],
    ];

    final kart = Container(
      margin: const EdgeInsets.only(bottom: R.s3),
      decoration: BoxDecoration(
        color: r.yuzey,
        borderRadius: BorderRadius.circular(R.kart),
        boxShadow: const [BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 2))],
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          if (sh) Positioned(left: 0, right: 0, top: 0, child: Container(height: 4, color: R.sehitAl)),
          Padding(
            padding: const EdgeInsets.all(R.s5),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: icerik),
          ),
          if (sayacli)
            Positioned(
              top: R.s2,
              right: R.s2,
              child: _KartMenu(ilan: ilan),
            ),
        ],
      ),
    );
    return kart;
  }
}

class _Ayrac extends StatelessWidget {
  final CvRenk r;
  const _Ayrac(this.r);
  @override
  Widget build(BuildContext context) =>
      Container(height: 1, color: r.cizgi, margin: const EdgeInsets.symmetric(vertical: R.s4));
}

class _Sutun extends StatelessWidget {
  final String baslik;
  final List<String> satirlar;
  const _Sutun({required this.baslik, required this.satirlar});
  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(trBuyuk(baslik), textAlign: TextAlign.center, style: Y.sutunEtiket(r)),
        const SizedBox(height: R.s1),
        for (final s in satirlar.where((x) => x.isNotEmpty))
          Text(s, textAlign: TextAlign.center, style: Y.kucuk(r).copyWith(color: r.metin)),
      ],
    );
  }
}

class _KayitliDugme extends StatelessWidget {
  final CvRenk r;
  const _KayitliDugme(this.r);
  @override
  Widget build(BuildContext context) => Container(
        height: 52,
        decoration: BoxDecoration(color: r.vurguZemin, borderRadius: BorderRadius.circular(R.dugme)),
        alignment: Alignment.center,
        child: Text(M.kartKaydedildi,
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: r.vurguMetin)),
      );
}

/// Sayfam kartının ⋮ menüsü: "Sayfamdan kaldır" (onaylı)
class _KartMenu extends StatelessWidget {
  final Ilan ilan;
  const _KartMenu({required this.ilan});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return PopupMenuButton<String>(
      tooltip: 'Seçenekler',
      color: r.yuzey2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.dugme)),
      icon: Ikon('menu', boyut: 20, renk: r.metin3),
      onSelected: (_) => kaldirOnay(context, ilan),
      itemBuilder: (_) => [
        PopupMenuItem<String>(
          value: 'kaldir',
          child: Center(child: Text(M.kartKaldir, style: TextStyle(color: r.metin))),
        ),
      ],
    );
  }
}

Future<void> kaldirOnay(BuildContext context, Ilan ilan) async {
  final d = Kapsam.oku(context);
  final r = context.renk;
  final evet = await showDialog<bool>(
    context: context,
    builder: (c) => Dialog(
      backgroundColor: r.yuzey,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
      child: Padding(
        padding: const EdgeInsets.all(R.s5),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(M.kaldirSoru,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 17, height: 22 / 17, fontWeight: FontWeight.w600, color: r.metin)),
          const SizedBox(height: R.s5),
          IkiliSatir(
            sol: IkincilDugme(M.kaldirVazgec, onTap: () => Navigator.of(c).pop(false)),
            sag: AnaDugme(M.kaldirTamam, yukseklik: 48, onTap: () => Navigator.of(c).pop(true)),
          ),
        ]),
      ),
    ),
  );
  if (evet == true) {
    await d.sayfamdanKaldir(ilan.id);
    if (context.mounted) bildir(context, M.bildirimKaldirildi);
  }
}

/// Sayaç satırları (Sayfam): −1 (44) | cümle düğmesi (+1, 56 yükseklik) | sayı (44)
class SayacBlok extends StatefulWidget {
  final Ilan ilan;
  const SayacBlok({super.key, required this.ilan});
  @override
  State<SayacBlok> createState() => _SayacBlokState();
}

class _SayacBlokState extends State<SayacBlok> {
  String? _bekleyen; // cinsiyet sorulurken bekleyen sayaç

  Future<void> _degis(String tur, int fark) async {
    final d = Kapsam.oku(context);
    await d.depo.sayacDegis(widget.ilan.id, tur, fark);
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    final cins = d.cinsiyetCoz(widget.ilan);
    final s = d.depo.sayaclar(widget.ilan.id);
    final toplam = s.values.fold<int>(0, (a, b) => a + b);

    return Column(children: [
      for (final t in sayacTurleri) ...[
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Row(children: [
            SizedBox(
              width: 44,
              height: 44,
              child: Semantics(
                button: true,
                label: M.sayacGeri,
                child: Material(
                  color: r.yuzey2,
                  borderRadius: BorderRadius.circular(22),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(22),
                    onTap: (s[t[0]] ?? 0) > 0 ? () => _degis(t[0], -1) : null,
                    child: Center(
                      child: Text('−1',
                          style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: (s[t[0]] ?? 0) > 0 ? r.metin2 : r.metin3.withAlpha(60))),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: R.s2),
            Expanded(
              child: Material(
                color: r.yuzey2,
                borderRadius: BorderRadius.circular(R.dugme),
                child: InkWell(
                  key: ValueKey('sayac_${t[0]}'),
                  borderRadius: BorderRadius.circular(R.dugme),
                  onTap: () {
                    if (cins == null) {
                      setState(() => _bekleyen = t[0]);
                      return;
                    }
                    _degis(t[0], 1);
                  },
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(minHeight: 56),
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: R.s2, vertical: 6),
                        child: Text(sayacEtiket(t[0], cins),
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 14, height: 18 / 14, color: r.metin)),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(width: R.s2),
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(color: r.vurgu, shape: BoxShape.circle),
              alignment: Alignment.center,
              child: Text('${s[t[0]] ?? 0}',
                  key: ValueKey('sayi_${t[0]}'),
                  style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: r.vurguUst,
                      fontFeatures: const [FontFeature.tabularFigures()])),
            ),
          ]),
        ),
      ],
      if (_bekleyen != null) ...[
        const SizedBox(height: R.s3),
        Text(M.cinsSoru, textAlign: TextAlign.center, style: Y.govde(r)),
        const SizedBox(height: R.s2),
        IkiliSatir(
          sol: IkincilDugme(M.cinsMerhum, onTap: () => _cinsSec('e')),
          sag: IkincilDugme(M.cinsMerhume, onTap: () => _cinsSec('k')),
        ),
      ],
      const SizedBox(height: R.s3),
      Text(M.sayacToplam(toplam), textAlign: TextAlign.center, style: Y.soluk(r)),
    ]);
  }

  Future<void> _cinsSec(String c) async {
    final d = Kapsam.oku(context);
    final bek = _bekleyen;
    await d.cinsKaydet(widget.ilan.id, c);
    if (!mounted) return;
    setState(() => _bekleyen = null);
    if (bek != null) await _degis(bek, 1);
  }
}
