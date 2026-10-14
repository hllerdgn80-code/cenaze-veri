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
    // 14.10.2026 sahibi: ilan olmayan/eksik yerlerde de "ilan ver" bağlantısı olsun (yalnız kaynaksız ilde değil, her ilde, listenin sonunda)
    out.add(const SizedBox(height: R.s4));
    out.add(Padding(
      padding: const EdgeInsets.symmetric(horizontal: R.s5),
      child: Column(children: [
        Text(M.ilanVerAciklama, textAlign: TextAlign.center, style: Y.soluk(r)),
        const SizedBox(height: R.s3),
        IkincilDugme(M.kaynaksizDugme,
            onTap: () => Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(
                  builder: (_) => AileFormu(il: v.il, ilce: d.ilce),
                ))),
        const SizedBox(height: R.s6),
      ]),
    ));
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
      // §21/3 + prototip v8: bildirim izni teklifi (bir kez sorulur; Tarihte Bugün/Kaybettiklerimiz şeritleri YOK — §26)
      if (bildirimTeklifiAcik && d.depo.bildirimIzni == null) ...[
        const SizedBox(height: R.s3),
        Container(
          key: const ValueKey('izin_karti'),
          padding: const EdgeInsets.all(R.s5),
          decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
          child: Column(children: [
            const Daire('zil', boyut: 56),
            const SizedBox(height: R.s4),
            Text(M.izinSoru,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 17, height: 22 / 17, fontWeight: FontWeight.w600, color: r.metin)),
            const SizedBox(height: R.s4),
            IkiliSatir(
              sol: AnaDugme(M.izinEvet, onTap: () => _izinSec(context, d, true)),
              sag: IkincilDugme(M.izinHayir, yukseklik: 52, onTap: () => _izinSec(context, d, false)),
            ),
          ]),
        ),
      ],
    ];
  }

  Future<void> _izinSec(BuildContext context, AppDurum d, bool evet) async {
    await d.depo.bildirimIzniKaydet(evet);
    if (!mounted) return;
    setState(() {});
    bildir(this.context, evet ? M.izinEvetBildirim : M.izinHayirBildirim);
  }
}

/// Bir günün kartları (prototipteki ilanCiz ile aynı akış). Test edilebilsin diye ayrı işlev.
/// §27: şehit ilanı listenin EN ÜSTÜNDE (ilçe görünümünde de, il görünümünde de; ilçesi belirtilmemiş şehit kayıtları dahil).
/// §21/1: ilanları ilçe vermeyen kaynakta (v.ilceler boş) ilanlar "İl geneli" olarak ana içeriktir.
/// §21/2: seçili ilçede bugün ilan yoksa ilin bugün ilan okunan diğer ilçeleri gösterilir.
List<Widget> gunIcerigi(IlVerisi v, String? ilce, String gun, String bugun) {
  final secili = v.secili(ilce);
  final anahtarlar = secili.keys.toList()..sort(trKarsilastir);
  final ilcesiz = v.ilceler.isEmpty;

  List<Widget> kartlar(List<Ilan> l) => [for (final r in l) IlanKarti(key: ValueKey(r.id), ilan: r)];

  List<Ilan> sehitGun(String g) => [
        for (final k in anahtarlar) ...secili[k]!.where((r) => r.cenazeGunu == g && r.sehit),
        ...v.genel.where((r) => r.cenazeGunu == g && r.sehit),
      ];

  List<Ilan> genelGun(String g) => v.genel.where((r) => r.cenazeGunu == g && !r.sehit).toList();

  List<Widget> gunKartlari(String g, {bool tarihliBolum = false}) {
    final x = <Widget>[];
    final sehitler = sehitGun(g);
    if (sehitler.isNotEmpty) {
      if (ilce == null) x.add(Bolum(tarihliBolum ? '${tarih(g, kisa: true)} · ${M.sehitBolum}' : M.sehitBolum));
      x.addAll(kartlar(sehitler));
    }
    for (final k in anahtarlar) {
      final l = secili[k]!.where((r) => r.cenazeGunu == g && !r.sehit).toList();
      if (l.isEmpty) continue;
      if (ilce == null) x.add(Bolum(tarihliBolum ? '${tarih(g, kisa: true)} · $k' : k));
      x.addAll(kartlar(l));
    }
    return x;
  }

  // Geçmiş günler (son 7 gün açılırken): ilçesiz kaynakta "İl geneli" kayıtları da girer
  List<Widget> gecmisGun(String g) {
    final x = gunKartlari(g, tarihliBolum: true);
    if (ilcesiz) {
      final gl = genelGun(g);
      if (gl.isNotEmpty) {
        if (ilce == null) x.add(Bolum('${tarih(g, kisa: true)} · ${M.bolumIlGenelSade}'));
        x.addAll(kartlar(gl));
      }
    }
    return x;
  }

  // §21/2: ilin diğer ilçelerinde bugünün ilanları (şehit önce)
  List<Widget> digerIlceler(String g) {
    final d = <String, List<Ilan>>{};
    for (final e in v.ilceler.entries) {
      if (e.key == ilce) continue;
      final l = e.value.where((r) => r.cenazeGunu == g).toList();
      if (l.isNotEmpty) d[e.key] = l;
    }
    if (d.isEmpty) return <Widget>[];
    final adlar = d.keys.toList()..sort(trKarsilastir);
    final x = <Widget>[
      Bolum(M.digerIlcelerBaslik(v.il, adlar.take(3).toList(), devami: adlar.length > 3)),
    ];
    x.addAll(kartlar([for (final k in adlar) ...d[k]!.where((r) => r.sehit)]));
    for (final k in adlar) {
      final l = d[k]!.where((r) => !r.sehit).toList();
      if (l.isEmpty) continue;
      x.add(Bolum(k));
      x.addAll(kartlar(l));
    }
    return x;
  }

  final yer = ilce ?? v.il;
  List<Widget> h = gunKartlari(gun);
  final genelBugun = ilcesiz ? genelGun(gun) : <Ilan>[];
  if (h.isEmpty && genelBugun.isEmpty) {
    if (gun == bugun) {
      // Kaynak var, bugün ilan yok: önce ilin diğer ilçeleri (§21/2), sonra son 7 gün kendiliğinden açılır
      h = <Widget>[BosDurum(baslik: M.bosBugunBaslik(yer), aciklama: M.bosBugunAciklama, kucuk: true)];
      if (ilce != null && !ilcesiz) h.addAll(digerIlceler(bugun));
      for (int n = 1; n < 7; n++) {
        final g = gunEkle(bugun, -n);
        final x = gecmisGun(g);
        if (x.isEmpty) continue;
        if (ilce != null) h.add(Bolum(tarihGun(g)));
        h.addAll(x);
      }
    } else {
      h = <Widget>[BosDurum(baslik: M.bosGecmisBaslik, aciklama: M.bosGecmisAciklama(gun, yer))];
    }
  }

  final genel = genelGun(gun);
  if (ilcesiz) {
    if (genel.isNotEmpty) {
      h.add(const Bolum(M.bolumIlGenelSade));
      h.addAll(kartlar(genel));
    }
  } else {
    h.add(const Bolum(M.bolumIlGeneli));
    if (genel.isEmpty) {
      h.add(const BosDurum(aciklama: M.bosIlGeneli, kucuk: true));
    } else {
      h.addAll(kartlar(genel));
    }
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
