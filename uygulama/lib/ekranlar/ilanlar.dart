// Cenaze İlanları (ana ekran): kayıtlı il/ilçe, bugün; 7 günlük tarih şeridi (cenaze günü);
// ilçe bölümleri, "İl geneli", boş durumlar; verisi olmayan ilde bilgi kartı + "Cenaze ilanı paylaş".
import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/ilan_karti.dart';
import '../bilesenler/kart_sayfa.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/ilan.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/uzak_ayar.dart';
import '../cekirdek/veri.dart';
import '../cekirdek/yardimci.dart';
import 'adres.dart';
import 'gorevli_kayit.dart';
import 'sehit_bilgi.dart';

/// Açılışta/sekmeye dönüşte yeniden çekme eşiği (URUN §56: veri en çok 5 dk eski). Aşağı çekince her zaman çekilir. Testte kısaltılır.
@visibleForTesting
Duration ilanYenilemeAraligi = const Duration(minutes: 5);

class IlanlarEkrani extends StatefulWidget {
  const IlanlarEkrani({super.key});
  @override
  State<IlanlarEkrani> createState() => _IlanlarEkraniState();
}

class _IlanlarEkraniState extends State<IlanlarEkrani> with WidgetsBindingObserver {
  IlSonucu? _sonuc;
  DateTime? _sonCekme;
  int _oncekiSekme = 0;
  bool _yukleniyor = false;
  String? _yukluIl;
  int _anaSayac = -1;
  String _gun = bugunTr();
  final _kaydirma = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  /// Uygulamaya dönüşte (arka plandan) veri 5 dk'dan eskiyse yeniden çekilir
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _eskiyseYenile();
  }

  void _eskiyseYenile() {
    if (!mounted || _yukleniyor || _sonCekme == null) return;
    if (DateTime.now().difference(_sonCekme!) >= ilanYenilemeAraligi) _yukle();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final d = Kapsam.of(context);
    if (d.sekme == 0 && _oncekiSekme != 0) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _eskiyseYenile()); // İlanlar sekmesine dönüş
    }
    _oncekiSekme = d.sekme;
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
    WidgetsBinding.instance.removeObserver(this);
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
    UzakAyar.tazele(d.veri.istemci).then((degisti) {
      if (degisti && mounted) setState(() {});
    });
    final s = await d.veri.ilGetir(il);
    if (!mounted || il != d.il) return;
    setState(() {
      _sonuc = s;
      _sonCekme = DateTime.now();
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
          child: KartListesi(
            controller: _kaydirma,
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

    final out = <Widget>[]; // 16.10.2026 sahibi: önce 'Bugün … bulunmuyor' / ilanlar, ilan kutusu ALTTA
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
    out.add(IlanKutusu(il: v.il, ilce: d.ilce));
    return out;
  }

  List<Widget> _kaynaksiz(BuildContext context, AppDurum d, CvRenk r, IlVerisi v) {
    // 16.10.2026 sahibi: "… yakınları tarafından paylaşılıyor" kartı TAMAMEN kaldırıldı; yalnız ilan kutusu
    final yer = d.ilce ?? v.il;
    return [
      BosDurum(baslik: M.bosBugunBaslik(yer), aciklama: M.bosBugunAciklama, kucuk: true),
      IlanKutusu(il: v.il, ilce: d.ilce),
    ];
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

  // İlçesi belirtilmemiş kayıtlar (ilçesiz kaynakta "İl geneli"; ilçeli kaynakta yalnız o gün kayıt varsa)
  List<Widget> genelBolumu(String g) {
    if (ilce != null && !UzakAyar.ilceSayfasindaIlGeneli) return <Widget>[]; // 16.10.2026 sahibi: ilçe sayfasında "İl geneli" yok (uzak ayar)
    final l = genelGun(g);
    if (l.isEmpty) return <Widget>[];
    return [Bolum(ilcesiz ? M.bolumIlGenelSade : M.bolumIlGeneli), ...kartlar(l)];
  }

  final yer = ilce ?? v.il;
  List<Widget> h = gunKartlari(gun);
  final genelGoster = ilce == null || UzakAyar.ilceSayfasindaIlGeneli;
  final genelBugun = (ilcesiz && genelGoster) ? genelGun(gun) : <Ilan>[];
  final bugunBos = h.isEmpty && (!genelGoster || genelGun(gun).isEmpty);
  if (h.isEmpty && genelBugun.isEmpty) {
    if (gun == bugun) {
      // 15.10.2026 sahibi: "ilçesine baktığında ilan varsa vardır, yoksa yoktur" — diğer ilçeler ve son 7 gün KENDİLİĞİNDEN AÇILMAZ
      // (karıştırma riski); yalnız "bulunmuyor" satırı. Geçmiş günler tarih şeridinden açılır.
      h = <Widget>[
        BosDurum(baslik: M.bosBugunBaslik(yer), aciklama: M.bosBugunAciklama, kucuk: true),
      ];
    } else {
      h = <Widget>[BosDurum(baslik: M.bosGecmisBaslik, aciklama: M.bosGecmisAciklama(gun, yer))];
    }
  }

  h.addAll(genelBolumu(gun));
  // URUN §57 (sahibi 16.10.2026: "uygulama bomboş görünüyor"): BUGÜN seçiliyken bugün hiç kayıt yoksa "bulunmuyor" satırının
  // altında DÜNÜN ilanları "Dün (15 Ekim)" başlığıyla kendiliğinden listelenir (yalnız dün; eskisi tarih şeridinden).
  if (gun == bugun && bugunBos && UzakAyar.bugunBossaDunuGoster) { // 16.10.2026 sahibi: varsayılan KAPALI (uzak ayar)
    final dun = gunEkle(bugun, -1);
    final dunKartlari = [...gunKartlari(dun), ...genelBolumu(dun)];
    if (dunKartlari.isNotEmpty) {
      h.add(Bolum(M.dunBolum(dun)));
      h.addAll(dunKartlari);
    }
  }
  return h;
}

/// İLAN KUTUSU (site sahibi 15.10.2026): her il/ilçe liste sayfasının ÜSTÜNDE sabit. Ücretsiz cenaze yakını ilanı KALKTI (15.10.2026 akşam):
/// yalnız tek paragraf talep metni + "Din görevlisi misiniz? Kayıt olun." bağlantısı.
class IlanKutusu extends StatelessWidget {
  final String il;
  final String? ilce;
  const IlanKutusu({super.key, required this.il, this.ilce});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Container(
      key: const ValueKey('ilan_kutusu'),
      width: double.infinity,
      margin: const EdgeInsets.only(top: R.s3, bottom: R.s4),
      padding: const EdgeInsets.all(R.s4),
      decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
      child: Column(children: [
        Text(M.ilanKutusuGorevli, key: const ValueKey('ilan_kutusu_talep'), textAlign: TextAlign.center, // 1. metinle aynı parlaklık: ana metin rengi, normal ağırlık, 15
            style: TextStyle(fontSize: 15, height: 20 / 15, fontWeight: FontWeight.w400, color: r.metin)),
        const SizedBox(height: R.s1),
        InkWell(
          key: const ValueKey('ilan_kutusu_gorevli'),
          onTap: () => gorevliKapisi(context, il: il, ilce: ilce),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: R.s2, horizontal: R.s3),
            child: Text(M.ilanKutusuKayit, textAlign: TextAlign.center, // bağlantı: vurgu (altın) rengi, altı çizili, 14
                style: TextStyle(fontSize: 14, height: 18 / 14, color: r.vurguMetin, decoration: TextDecoration.underline, decorationColor: r.vurguMetin)),
          ),
        ),
        InkWell(
          key: const ValueKey('ilan_kutusu_sehit'),
          onTap: () => sehitBilgiGoster(context),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: R.s2, horizontal: R.s3),
            child: Text(M.ilanKutusuSehit,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, height: 18 / 14, color: r.vurguMetin, decoration: TextDecoration.underline, decorationColor: r.vurguMetin)),
          ),
        ),
      ]),
    );
  }
}

/// Eşit hücreler: [öbür gün] [Yarın] Bugün → 6 gün önce (15.10.2026: Yarın/öbür gün YALNIZ o güne ilan varsa eklenir); seçili altın dolgu; ilan olan günde nokta
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
    final ileri = <int>[
      for (final k in [2, 1])
        if (veri.gunDolu(ilce, gunEkle(bugun, k))) k
    ];
    final aralik = ileri.length > 1 ? 4.0 : 6.0;
    for (final n in [for (final k in ileri) -k, for (int i = 0; i < 7; i++) i]) {
      final g = gunEkle(bugun, -n);
      final sec = g == secili;
      final dolu = veri.gunDolu(ilce, g);
      if (hucreler.isNotEmpty) hucreler.add(SizedBox(width: aralik));
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
                  Text(n == 0 ? M.seritBugun : n == -1 ? M.seritYarin : gunKisa[haftaGunu(g)],
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

/// Test için açık sarmal: tarih şeridini dışarıdan sınamak (Yarın hücresi) için.
@visibleForTesting
class SeritSarmal extends StatelessWidget {
  final IlVerisi veri;
  final String? ilce;
  final String secili;
  const SeritSarmal({super.key, required this.veri, required this.ilce, required this.secili});

  @override
  Widget build(BuildContext context) => _TarihSeridi(veri: veri, ilce: ilce, secili: secili, onSec: (_) {});
}
