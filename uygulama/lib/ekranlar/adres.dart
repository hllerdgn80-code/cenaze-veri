// İl → ilçe seçimi (yalnız ilk açılışta sorulur; sonra ⋮ → "Adresi değiştir").
import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';

/// Liste satırı: 36 | ad (ortalı) | 36 (ok işareti)
class _Satir extends StatelessWidget {
  final String yazi;
  final VoidCallback onTap;
  final bool vurgulu;
  final bool ilk;
  const _Satir({required this.yazi, required this.onTap, this.vurgulu = false, this.ilk = false});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return InkWell(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 52),
        padding: const EdgeInsets.symmetric(horizontal: R.s4, vertical: R.s2),
        decoration: BoxDecoration(border: ilk ? null : Border(top: BorderSide(color: r.cizgi))),
        child: Row(children: [
          const SizedBox(width: 36),
          const SizedBox(width: R.s3),
          Expanded(
            child: Text(yazi,
                textAlign: TextAlign.center,
                style: Y.satir(r).copyWith(
                    color: vurgulu ? r.vurguMetin : r.metin, fontWeight: vurgulu ? FontWeight.w600 : FontWeight.w400)),
          ),
          const SizedBox(width: R.s3),
          SizedBox(width: 36, child: Center(child: Ikon('ok', boyut: 18, renk: r.metin3))),
        ]),
      ),
    );
  }
}

class _Liste extends StatelessWidget {
  final List<Widget> satirlar;
  const _Liste(this.satirlar);
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
        decoration: BoxDecoration(color: context.renk.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        clipBehavior: Clip.antiAlias,
        child: Column(children: satirlar),
      );
}

class IlSecEkrani extends StatefulWidget {
  final bool degistir; // ⋮ → Adresi değiştir ile açıldı
  const IlSecEkrani({super.key, this.degistir = false});
  @override
  State<IlSecEkrani> createState() => _IlSecEkraniState();
}

class _IlSecEkraniState extends State<IlSecEkrani> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    final iller = d.gomulu.iller.where((i) => sade(i).contains(sade(_q))).toList();
    return Scaffold(
      body: SafeArea(
        child: CustomScrollView(slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s5),
              child: Column(children: [
                const Logo(boyut: 72, yaricap: 18),
                const SizedBox(height: R.s4),
                Text(M.acilisMarka, textAlign: TextAlign.center, style: Y.acilis(r)),
                const SizedBox(height: R.s2),
                Text(M.acilisAlt, textAlign: TextAlign.center, style: Y.govde(r)),
              ]),
            ),
          ),
          SliverToBoxAdapter(child: AramaAlani(ipucu: M.ilAra, onChanged: (v) => setState(() => _q = v))),
          SliverToBoxAdapter(
            child: iller.isEmpty
                ? const BosDurum(baslik: M.ilBos, ikon: 'konum', kucuk: true)
                : _Liste([
                    for (int i = 0; i < iller.length; i++)
                      _Satir(
                        yazi: iller[i],
                        ilk: i == 0,
                        onTap: () => Navigator.of(context).push(MaterialPageRoute(
                          builder: (_) => IlceSecEkrani(il: iller[i], degistir: widget.degistir),
                        )),
                      ),
                  ]),
          ),
        ]),
      ),
    );
  }
}

class IlceSecEkrani extends StatefulWidget {
  final String il;
  final bool degistir;
  const IlceSecEkrani({super.key, required this.il, this.degistir = false});
  @override
  State<IlceSecEkrani> createState() => _IlceSecEkraniState();
}

class _IlceSecEkraniState extends State<IlceSecEkrani> {
  String _q = '';

  Future<void> _sec(String? ilce) async {
    final d = Kapsam.oku(context);
    final nav = Navigator.of(context);
    await d.adresKaydet(widget.il, ilce);
    // İlk açılışta kök ekran adres kaydını görüp sekmeli kabuğa geçer; her iki durumda seçim ekranları kapanır
    nav.popUntil((r) => r.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    final tum = d.ilceListesi(widget.il);
    final liste = tum.where((i) => sade(i).contains(sade(_q))).toList();
    final satirlar = <Widget>[
      if (_q.isEmpty) _Satir(yazi: M.ilceTumu, vurgulu: true, ilk: true, onTap: () => _sec(null)),
      for (int i = 0; i < liste.length; i++)
        _Satir(yazi: liste[i], ilk: _q.isNotEmpty && i == 0, onTap: () => _sec(liste[i])),
    ];
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            yanGenislik: 76,
            sol: YuvarlakDugme(
              ikon: 'geri',
              yazi: M.ilceGeri,
              genislik: 76,
              anlam: 'İllere dön',
              onTap: () => Navigator.of(context).pop(),
            ),
            sag: const MenuDugmesi(genislik: 76),
            ust: M.ilceUst,
            baslik: BuyukBaslik(widget.il),
          ),
          AramaAlani(ipucu: M.ilceAra, onChanged: (v) => setState(() => _q = v)),
          Expanded(
            child: ListView(children: [
              satirlar.isEmpty ? const BosDurum(baslik: M.ilceBos, ikon: 'konum', kucuk: true) : _Liste(satirlar),
            ]),
          ),
        ]),
      ),
    );
  }
}
