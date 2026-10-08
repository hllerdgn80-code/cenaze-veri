// Dualar ve Âyetler: 4 kutucuk; her bölümde konu süzgeci (en sık 4 konu + Tümü); merhum/merhume sürümleri.
// Kaynak: assets/veri/dualar.json (tasarim/dualar.json; meal ve çeviriler kendi sade çevirimiz).
import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';

class DualarEkrani extends StatelessWidget {
  const DualarEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    final bolumler = (d.gomulu.dualar['bolumler'] as List? ?? const []).whereType<Map>().toList();
    return Column(children: [
      BaslikCubugu(
        sol: LogoDugme(onTap: d.anaEkranaDon),
        sag: const MenuDugmesi(),
        ust: M.duaUst,
        baslik: const BuyukBaslik(M.duaBaslik),
      ),
      Expanded(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
          children: [
            KutucukIzgara([
              for (final b in bolumler)
                Kutucuk(
                  ikon: (b['ikon'] ?? 'kitap').toString(),
                  ad: (b['ad'] ?? '').toString(),
                  yukseklik: 156,
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => DuaListesi(bolum: Map<String, dynamic>.from(b)),
                  )),
                ),
            ]),
          ],
        ),
      ),
    ]);
  }
}

class DuaListesi extends StatefulWidget {
  final Map<String, dynamic> bolum;
  const DuaListesi({super.key, required this.bolum});
  @override
  State<DuaListesi> createState() => _DuaListesiState();
}

class _DuaListesiState extends State<DuaListesi> {
  String? _secili;

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    final etk = Map<String, dynamic>.from(d.gomulu.dualar['etiketler'] as Map? ?? const {});
    final liste = (widget.bolum['liste'] as List? ?? const []).whereType<Map>().toList();
    final kisa = (widget.bolum['kisa'] as List? ?? const ['', '']).map((x) => x.toString()).toList();

    // Bölümde en sık geçen en çok 4 konu
    final say = <String, int>{};
    for (final x in liste) {
      for (final t in (x['e'] as List? ?? const [])) {
        final k = t.toString();
        if (etk.containsKey(k)) say[k] = (say[k] ?? 0) + 1;
      }
    }
    final konular = say.keys.toList()
      ..sort((a, b) {
        final c = say[b]!.compareTo(say[a]!);
        return c != 0 ? c : trKarsilastir(etk[a].toString(), etk[b].toString());
      });
    final dort = konular.take(4).toList();
    final gorunen = liste.where((x) => _secili == null || (x['e'] as List? ?? const []).contains(_secili)).toList();

    Widget cip(String? k, String ad) {
      final sec = _secili == k;
      return Material(
        color: sec ? r.vurguZemin : r.yuzey,
        shape: StadiumBorder(side: BorderSide(color: sec ? r.vurgu : r.cizgi)),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: () => setState(() => _secili = k),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 7, horizontal: 4),
            child: Text(ad,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.fade,
                softWrap: false,
                style: TextStyle(fontSize: 13, height: 18 / 13, color: sec ? r.vurguMetin : r.metin2)),
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: const MenuDugmesi(),
            ust: kisa.isNotEmpty ? kisa[0] : '',
            baslik: BuyukBaslik(kisa.length > 1 ? kisa[1] : ''),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
              children: [
                SizedBox(width: double.infinity, child: cip(null, M.duaTumu)),
                if (dort.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Row(children: [
                    for (int i = 0; i < dort.length; i++) ...[
                      if (i > 0) const SizedBox(width: 6),
                      Expanded(child: cip(dort[i], etk[dort[i]].toString())),
                    ],
                  ]),
                ],
                const SizedBox(height: R.s3),
                for (final x in gorunen) _DuaKarti(x: Map<String, dynamic>.from(x)),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

class _DuaKarti extends StatelessWidget {
  final Map<String, dynamic> x;
  const _DuaKarti({required this.x});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final kadin = x['kadin'] is Map ? Map<String, dynamic>.from(x['kadin'] as Map) : null;
    final kd = kadin ?? const <String, dynamic>{};
    final cift = (kd['ar'] ?? '').toString().isNotEmpty;
    String s(dynamic v) => (v ?? '').toString();
    final arStil = TextStyle(fontFamily: 'serif', fontSize: 22, height: 40 / 22, color: r.metin);
    final okStil = TextStyle(fontSize: 14, height: 20 / 14, fontStyle: FontStyle.italic, color: r.metin2);
    final surum = Y.soluk(r);

    return Container(
      margin: const EdgeInsets.only(bottom: R.s3),
      padding: const EdgeInsets.all(R.s5),
      decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(s(x['b']), textAlign: TextAlign.center, style: Y.adim(r)),
        if (cift) ...[const SizedBox(height: R.s3), Text(M.duaMerhumIcin, textAlign: TextAlign.center, style: surum)],
        if (s(x['ar']).isNotEmpty) ...[
          const SizedBox(height: R.s3),
          Text(s(x['ar']), textAlign: TextAlign.center, textDirection: TextDirection.rtl, style: arStil),
        ],
        if (s(x['ok']).isNotEmpty) ...[
          const SizedBox(height: R.s2),
          Text(s(x['ok']), textAlign: TextAlign.center, style: okStil),
        ],
        if (cift) ...[
          const SizedBox(height: R.s3),
          Text(M.duaMerhumeIcin, textAlign: TextAlign.center, style: surum),
          const SizedBox(height: R.s3),
          Text(s(kd['ar']), textAlign: TextAlign.center, textDirection: TextDirection.rtl, style: arStil),
          if (s(kd['ok']).isNotEmpty) ...[
            const SizedBox(height: R.s2),
            Text(s(kd['ok']), textAlign: TextAlign.center, style: okStil),
          ],
        ],
        const SizedBox(height: R.s3),
        Text(s(x['an']), textAlign: TextAlign.left, style: TextStyle(fontSize: 15, height: 23 / 15, color: r.metin)),
        if (s(x['not']).isNotEmpty) ...[
          const SizedBox(height: R.s2),
          Text(s(x['not']), textAlign: TextAlign.left, style: Y.govde(r).copyWith(fontSize: 14, height: 21 / 14)),
        ],
        const SizedBox(height: R.s3),
        Text(s(x['k']), textAlign: TextAlign.center, style: Y.soluk(r).copyWith(fontSize: 12)),
      ]),
    );
  }
}
