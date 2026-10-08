// Hatırla: Kaybettiklerimiz (5 kutucuk, canlı JSON) + Tarihte Bugün (canlı AA-GG.json).
// Liste numarası yok; sıralama ölçütü kullanıcıya yazılmaz; kabir bilgisi gösterilmez.
import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/kisi.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/veri.dart';
import '../cekirdek/yardimci.dart';

const _kategoriIkon = {
  'cumhurbaskanlari': 'cb',
  'basbakanlar': 'bb',
  'bakanlar': 'bak',
  'siyasetciler': 'siy',
  'sanatcilar': 'san',
};

class HatirlaEkrani extends StatelessWidget {
  const HatirlaEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    return Column(children: [
      BaslikCubugu(
        sol: LogoDugme(onTap: d.anaEkranaDon),
        sag: const MenuDugmesi(),
        ust: M.hatirlaUst,
        baslik: const BuyukBaslik(M.hatirlaBaslik),
      ),
      Expanded(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
          children: [
            KutucukIzgara([
              Kutucuk(
                ikon: 'lale',
                ad: M.kayBaslik,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const KaybettiklerimizEkrani())),
              ),
              Kutucuk(
                ikon: 'takvim',
                ad: M.tbBaslik,
                onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TarihteBugunEkrani())),
              ),
            ]),
          ],
        ),
      ),
    ]);
  }
}

Widget _geriBaslik(BuildContext context, String ust, String baslik) => BaslikCubugu(
      sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
      sag: const MenuDugmesi(),
      ust: ust,
      baslik: BuyukBaslik(baslik),
    );

class KaybettiklerimizEkrani extends StatelessWidget {
  const KaybettiklerimizEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          _geriBaslik(context, M.hatirlaUst, M.kayBaslik),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
              children: [
                KutucukIzgara([
                  for (final k in M.kayKategoriler)
                    Kutucuk(
                      ikon: _kategoriIkon[k[0]] ?? 'lale',
                      ad: k[1],
                      onTap: () => Navigator.of(context)
                          .push(MaterialPageRoute(builder: (_) => KategoriListesi(kategori: k[0], ad: k[1]))),
                    ),
                ]),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

/// Kişi kartı: sol rozet vefat yılı · orta "VEFAT · tarih" · sağ rozet yaş; ad, görev sırası, tanıtım
class KisiKarti extends StatelessWidget {
  final Kisi k;
  const KisiKarti(this.k, {super.key});

  Widget _rozet(CvRenk r, String ust, String alt) => Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(color: r.yuzey2, borderRadius: BorderRadius.circular(22)),
        alignment: Alignment.center,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(ust,
              style: TextStyle(
                  fontSize: ust.length > 3 ? 11 : 14, height: 1.1, fontWeight: FontWeight.w700, color: r.metin)),
          Text(alt, style: TextStyle(fontSize: 8, height: 1.1, fontWeight: FontWeight.w600, color: r.metin3)),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      margin: const EdgeInsets.only(bottom: R.s3),
      padding: const EdgeInsets.all(R.s5),
      decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Row(children: [
          _rozet(r, k.yil, 'YIL'),
          Expanded(
            child: Text(trBuyuk('Vefat · ${tarih(k.vefatTarihi)}'), textAlign: TextAlign.center, style: Y.ustEtiket(r)),
          ),
          _rozet(r, k.yas == null ? '–' : '${k.yasYaklasik ? '~' : ''}${k.yas}', 'YAŞ'),
        ]),
        const SizedBox(height: R.s3),
        Text(k.ad, textAlign: TextAlign.center, style: Y.kartAd(r)),
        if (k.gorev != null) ...[
          const SizedBox(height: 2),
          Text(k.gorev!, textAlign: TextAlign.center, style: Y.kucuk(r).copyWith(color: r.vurguMetin)),
        ],
        if (k.tanitim.isNotEmpty) ...[
          const SizedBox(height: 2),
          Text(k.tanitim, textAlign: TextAlign.center, style: Y.kucuk(r)),
        ],
      ]),
    );
  }
}

class KategoriListesi extends StatefulWidget {
  final String kategori;
  final String ad;
  const KategoriListesi({super.key, required this.kategori, required this.ad});
  @override
  State<KategoriListesi> createState() => _KategoriListesiState();
}

class _KategoriListesiState extends State<KategoriListesi> {
  KisiSonucu? _s;
  String _q = '';
  int _n = 60;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _yukle());
  }

  Future<void> _yukle() async {
    final s = await Kapsam.oku(context).veri.kaybettiklerimiz(widget.kategori);
    if (mounted) setState(() => _s = s);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final s = _s;
    final govde = <Widget>[];
    if (s == null) {
      govde.add(const SizedBox(height: 80));
      govde.add(Center(
          child: SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 2, color: r.vurgu))));
    } else if (s.liste == null) {
      govde.add(BosDurum(
          aciklama: s.durum == VeriDurumu.tamam
              ? M.tbHazirlaniyor
              : (s.durum == VeriDurumu.baglantiYok ? M.hataBaglanti : M.hataVeri)));
    } else {
      final q = sade(_q);
      final L = s.liste!.where((x) => q.isEmpty || sade(x.ad).contains(q)).toList();
      if (L.isEmpty) {
        govde.add(const BosDurum(baslik: M.kayBos));
      } else {
        govde.addAll(L.take(_n).map((x) => KisiKarti(x)));
        if (L.length > _n) {
          govde.add(IkincilDugme(M.kayDaha, onTap: () => setState(() => _n += 60)));
        }
      }
    }
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          _geriBaslik(context, M.hatirlaUst, widget.ad),
          AramaAlani(ipucu: M.kayAra, onChanged: (v) => setState(() {
                _q = v;
                _n = 60;
              })),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6), children: govde),
          ),
        ]),
      ),
    );
  }
}

class TarihteBugunEkrani extends StatefulWidget {
  const TarihteBugunEkrani({super.key});
  @override
  State<TarihteBugunEkrani> createState() => _TarihteBugunEkraniState();
}

class _TarihteBugunEkraniState extends State<TarihteBugunEkrani> {
  KisiSonucu? _s;
  final String _gun = bugunTr();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _yukle());
  }

  Future<void> _yukle() async {
    final s = await Kapsam.oku(context).veri.tarihteBugun(_gun);
    if (mounted) setState(() => _s = s);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final s = _s;
    final govde = <Widget>[];
    if (s == null) {
      govde.add(const SizedBox(height: 80));
      govde.add(Center(
          child: SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 2, color: r.vurgu))));
    } else if (s.liste == null || s.liste!.isEmpty) {
      govde.add(BosDurum(
          ikon: 'takvim',
          aciklama: s.durum == VeriDurumu.baglantiYok ? M.hataBaglanti : M.tbHazirlaniyor));
    } else {
      final tr = s.liste!.where((x) => x.turk).toList();
      final dn = s.liste!.where((x) => !x.turk).toList();
      if (tr.isNotEmpty) {
        govde.add(const Bolum(M.tbTurkiye));
        govde.addAll(tr.map((x) => KisiKarti(x)));
      }
      if (dn.isNotEmpty) {
        govde.add(const Bolum(M.tbDunya));
        govde.addAll(dn.map((x) => KisiKarti(x)));
      }
    }
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          _geriBaslik(context, M.tbUst(_gun), M.tbBaslik),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6), children: govde),
          ),
        ]),
      ),
    );
  }
}
