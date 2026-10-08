// Cenaze İlanları (ana ekran): kayıtlı il/ilçe, bugün; 7 günlük tarih şeridi (cenaze günü);
// ilçe bölümleri, "İl geneli", boş durumlar; verisi olmayan ilde bilgi kartı + "Cenaze ilanı paylaş".
import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/ilan_karti.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/ilan.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/veri.dart';
import '../cekirdek/yardimci.dart';
import 'adres.dart';
import 'aile_formu.dart';

class IlanlarEkrani extends StatefulWidget {
  const IlanlarEkrani({super.key});
  @override
  State<IlanlarEkrani> createState() => _IlanlarEkraniState();
}

class _IlanlarEkraniState extends State<IlanlarEkrani> {
  IlSonucu? _sonuc;
  bool _yukleniyor = false;
  String? _yukluIl;
  int _anaSayac = -1;
  String _gun = bugunTr();
  final _kaydirma = ScrollController();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final d = Kapsam.of(context);
    if (d.anaEkranSayaci != _anaSayac) {
      _anaSayac = d.anaEkranSayaci;
      _gun = bugunTr();
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_kaydirma.hasClients) _kaydirma.jumpTo(0);
      });
    }
    if (d.il != null && d.il != _yukluIl) {
      _yukluIl = d.il;
      _sonuc = null;
      _yukle(ilk: true);
    }
  }

  @override
  void dispose() {
    _kaydirma.dispose();
    super.dispose();
  }

  Future<void> _yukle({bool ilk = false}) async {
    final d = Kapsam.oku(context);
    final il = d.il;
    if (il == null) return;
    if (ilk) {
      _yukleniyor = true; // didChangeDependencies içinden: setState gerekmez, ardından build gelir
    } else {
      setState(() => _yukleniyor = true);
    }
    final s = await d.veri.ilGetir(il);
    if (!mounted || il != d.il) return;
    setState(() {
      _sonuc = s;
      _yukleniyor = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    final r = context.renk;
    final il = d.il ?? '';
    final konum = d.ilce == null ? il : '$il · ${d.ilce}';
    final v = _sonuc?.veri;
    final kaynakli = v?.kaynakli ?? true;

    return Column(children: [
      BaslikCubugu(
        sol: LogoDugme(onTap: d.anaEkranaDon),
        sag: const MenuDugmesi(),
        ust: M.ilanlarUst,
        baslik: InkWell(
          borderRadius: BorderRadius.circular(R.dugme),
          onTap: () => Navigator.of(context, rootNavigator: true)
              .push(MaterialPageRoute(builder: (_) => const IlSecEkrani(degistir: true))),
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            const SizedBox(width: 18),
            Flexible(child: Text(konum, textAlign: TextAlign.center, style: Y.buyuk(r))),
            Ikon('asagi', boyut: 18, renk: r.vurguMetin),
          ]),
        ),
      ),
      if (v != null && kaynakli) _TarihSeridi(veri: v, ilce: d.ilce, secili: _gun, onSec: (g) => setState(() => _gun = g)),
      Expanded(
        child: RefreshIndicator(
          color: r.vurgu,
          backgroundColor: r.yuzey,
          onRefresh: _yukle,
          child: ListView(
            controller: _kaydirma,
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
            children: _icerik(context, d, r),
          ),
        ),
      ),
    ]);
  }

  List<Widget> _icerik(BuildContext context, AppDurum d, CvRenk r) {
    final s = _sonuc;
    if (s == null || (s.veri == null && _yukleniyor)) {
      return [
        const SizedBox(height: 120),
        Center(child: SizedBox(width: 28, height: 28, child: CircularProgressIndicator(strokeWidth: 2, color: r.vurgu))),
      ];
    }
    final v = s.veri;
    if (v == null) {
      return [
        BosDurum(
          ikon: 'kemer',
          baslik: null,
          aciklama: s.durum == VeriDurumu.baglantiYok ? M.hataBaglanti : M.hataVeri,
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: R.s8),
          child: IkincilDugme(M.hataTekrar, onTap: _yukle),
        ),
      ];
    }
    if (!v.kaynakli) return _kaynaksiz(context, d, r, v);

    final out = <Widget>[];
    if (s.zaman != null) {
      out.add(Padding(
        padding: const EdgeInsets.only(bottom: R.s1),
        child: Text(M.bilgiGuncelleme(saatTr(s.zaman!)), textAlign: TextAlign.center, style: Y.soluk(r)),
      ));
    }
    if (s.durum == VeriDurumu.onbellek) {
      out.add(Text(M.hataBaglanti, textAlign: TextAlign.center, style: Y.soluk(r)));
    }
    out.addAll(gunIcerigi(v, d.ilce, _gun, bugunTr()));
    return out;
  }

  List<Widget> _kaynaksiz(BuildContext context, AppDurum d, CvRenk r, IlVerisi v) {
    return [
      const SizedBox(height: R.s3),
      Container(
        padding: const EdgeInsets.all(R.s5),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: Column(children: [
          const Daire('kemer'),
          const SizedBox(height: R.s4),
          Text(M.kaynaksizBaslik(v.il),
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 17, height: 22 / 17, fontWeight: FontWeight.w600, color: r.metin)),
          const SizedBox(height: R.s2),
          Text(M.kaynaksizAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          const SizedBox(height: R.s5),
          AnaDugme(M.kaynaksizDugme,
              onTap: () => Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(
                    builder: (_) => AileFormu(il: v.il, ilce: d.ilce),
                  ))),
        ]),
      ),
    ];
  }
}

/// Bir günün kartları (prototipteki ilanCiz ile aynı akış). Test edilebilsin diye ayrı işlev.
List<Widget> gunIcerigi(IlVerisi v, String? ilce, String gun, String bugun) {
  final secili = v.secili(ilce);
  final anahtarlar = secili.keys.toList()..sort(trKarsilastir);

  List<Widget> gunKartlari(String g, {bool tarihliBolum = false}) {
    final x = <Widget>[];
    final sehitler = [for (final k in anahtarlar) ...secili[k]!.where((r) => r.cenazeGunu == g && r.sehit)];
    if (sehitler.isNotEmpty) {
      if (ilce == null) x.add(Bolum(tarihliBolum ? '${tarih(g, kisa: true)} · ${M.sehitBolum}' : M.sehitBolum));
      x.addAll(sehitler.map((r) => IlanKarti(key: ValueKey(r.id), ilan: r)));
    }
    for (final k in anahtarlar) {
      final l = secili[k]!.where((r) => r.cenazeGunu == g && !r.sehit).toList();
      if (l.isEmpty) continue;
      if (ilce == null) x.add(Bolum(tarihliBolum ? '${tarih(g, kisa: true)} · $k' : k));
      x.addAll(l.map((r) => IlanKarti(key: ValueKey(r.id), ilan: r)));
    }
    return x;
  }

  final yer = ilce ?? v.il;
  var h = gunKartlari(gun);
  if (h.isEmpty && gun == bugun) {
    // Kaynak var, bugün ilan yok: son 7 gün kendiliğinden açılır
    h = [BosDurum(baslik: M.bosBugunBaslik(yer), aciklama: M.bosBugunAciklama, kucuk: true)];
    for (int n = 1; n < 7; n++) {
      final g = gunEkle(bugun, -n);
      final x = gunKartlari(g, tarihliBolum: true);
      if (x.isEmpty) continue;
      if (ilce != null) h.add(Bolum(tarihGun(g)));
      h.addAll(x);
    }
  } else if (h.isEmpty) {
    h = [BosDurum(baslik: M.bosGecmisBaslik, aciklama: M.bosGecmisAciklama(gun, yer))];
  }
  final genel = v.genel.where((r) => r.cenazeGunu == gun).toList();
  h.add(const Bolum(M.bolumIlGeneli));
  if (genel.isEmpty) {
    h.add(const BosDurum(aciklama: M.bosIlGeneli, kucuk: true));
  } else {
    h.addAll(genel.map((r) => IlanKarti(key: ValueKey(r.id), ilan: r)));
  }
  return h;
}

/// 7 eşit hücre: Bugün → 6 gün önce; seçili altın dolgu; ilan olan günde nokta
class _TarihSeridi extends StatelessWidget {
  final IlVerisi veri;
  final String? ilce;
  final String secili;
  final ValueChanged<String> onSec;
  const _TarihSeridi({required this.veri, required this.ilce, required this.secili, required this.onSec});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final bugun = bugunTr();
    final hucreler = <Widget>[];
    for (int n = 0; n < 7; n++) {
      final g = gunEkle(bugun, -n);
      final sec = g == secili;
      final dolu = veri.gunDolu(ilce, g);
      if (n > 0) hucreler.add(const SizedBox(width: 6));
      hucreler.add(Expanded(
        child: Material(
          key: ValueKey('gun_$g'),
          color: sec ? r.vurgu : r.yuzey,
          borderRadius: BorderRadius.circular(R.cip),
          child: InkWell(
            borderRadius: BorderRadius.circular(R.cip),
            onTap: () => onSec(g),
            child: SizedBox(
              height: 64,
              child: Stack(alignment: Alignment.center, children: [
                Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Text(n == 0 ? M.seritBugun : gunKisa[haftaGunu(g)],
                      maxLines: 1,
                      softWrap: false,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                          fontSize: 11, height: 13 / 11, fontWeight: FontWeight.w500, color: sec ? r.vurguUst : r.metin3)),
                  const SizedBox(height: 2),
                  Text('${int.parse(g.substring(8))}',
                      style: TextStyle(
                          fontSize: 18, height: 22 / 18, fontWeight: FontWeight.w700, color: sec ? r.vurguUst : r.metin)),
                ]),
                if (dolu)
                  Positioned(
                    bottom: 7,
                    child: Container(
                      width: 4,
                      height: 4,
                      decoration: BoxDecoration(color: sec ? r.vurguUst : r.vurgu, shape: BoxShape.circle),
                    ),
                  ),
              ]),
            ),
          ),
        ),
      ));
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s3),
      child: Row(children: hucreler),
    );
  }
}
