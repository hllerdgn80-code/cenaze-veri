// Din görevlisi paneli (0.1.5, URUN-TASLAGI §37; ölçü: tasarim/prototip.html p-gorevli-panel).
// EN ÜSTTE sabit başlık kartı: "<Görev yeri> <Unvan>" / ad-soyad / "İl · İlçe" (kaydırınca kaybolmaz).
// Altında "İlan paylaş" ve "İlanlarım (n)"; en altta son ilanlar. Hesap "kontrolde" iken panel AÇIK ama "İlan paylaş" PASİF
// (dokununca açıklama), İlanlarım boş; sahibi onaylayınca düğme etkinleşir (her açılışta GET /gorevli/durum).
// RED: sunucu hesabı siler -> "Başvurunuz onaylanmadı; hesap silindi." ve giriş kartına dönülür. İl/ilçe KİLİTLİ.

import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/gorevli.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';
import 'gorevli_yer.dart';

/// §27 dili: şehit ilanında "Şehidimiz <Rütbe> <Ad Soyad>"
String _ilanAdi(Map<String, dynamic> i) {
  final ad = i['ad_soyad']?.toString() ?? '';
  if (i['sehit'] != true) return ad;
  final rutbe = i['rutbe']?.toString() ?? '';
  return 'Şehidimiz ${rutbe.isEmpty ? '' : '$rutbe '}$ad';
}

/// Durum etiketi + "Düzeltildi" (otomatik ilanı düzelten kayıt; yalnız panelde, halka açık kartta YOK — H75)
String _durumYaz(Map<String, dynamic> i) {
  final d = M.gorevliDurumEtiket[i['durum']?.toString()] ?? '';
  final duz = (i['duzeltme_id']?.toString() ?? '').isNotEmpty;
  return [d, if (duz) M.gorevliDuzeltildi].where((x) => x.isNotEmpty).join(' · ');
}

class GorevliHesap {
  final String durum; // onayli | kontrolde | kuyruk
  final String adSoyad, il, ilce, gorevYeri;
  final String? unvan;
  final String? kvkkKabul; // sunucudaki kabul tarihi (başka cihazdan/yeniden girişten)
  const GorevliHesap(this.durum, this.adSoyad, this.il, this.ilce, this.gorevYeri, this.unvan, [this.kvkkKabul]);
  bool get onayli => durum == 'onayli';
  /// ad-soyad, il, ilçe ve görev yeri dolu mu (kod doğrulandıktan sonra ilk ilanda bir kez sorulur)
  bool get profilTamam => adSoyad.isNotEmpty && il.isNotEmpty && ilce.isNotEmpty && gorevYeri.isNotEmpty;
  static GorevliHesap? coz(Map<String, dynamic>? j) {
    if (j == null) return null;
    String s(String k) => j[k]?.toString() ?? '';
    final d = s('durum');
    if (d.isEmpty) return null;
    return GorevliHesap(d, s('ad_soyad'), s('il'), s('ilce'), s('gorev_yeri'), j['unvan']?.toString(), j['kvkk_kabul']?.toString());
  }
}

class GorevliPanel extends StatefulWidget {
  final GorevliServisi? servis;
  const GorevliPanel({super.key, this.servis});
  @override
  State<GorevliPanel> createState() => _GorevliPanelState();
}

class _GorevliPanelState extends State<GorevliPanel> {
  GorevliHesap? _hesap;
  List<Map<String, dynamic>> _ilanlar = const [];
  bool _yukleniyor = true;
  String? _hata;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _yukle());
  }

  GorevliServisi _servis() => widget.servis ?? GorevliServisi(istemci: Kapsam.oku(context).veri.istemci);

  Future<void> _cik(String mesaj) async {
    final d = Kapsam.oku(context).depo;
    await d.gorevliOturumKaydet(null);
    await d.gorevliDurumKaydet(null);
    if (!mounted) return;
    bildir(context, mesaj);
    Navigator.of(context).pop();
  }

  Future<void> _yukle() async {
    final depo = Kapsam.oku(context).depo;
    final tok = depo.gorevliOturum;
    if (tok == null) {
      Navigator.of(context).pop();
      return;
    }
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final s = _servis();
    final y = await s.durum(tok);
    if (!mounted) return;
    if (y.durum == 'silindi') return _cik(M.gorevliSilindi);
    if (y.kod == 401) return _cik(M.gorevliOturumDoldu);
    final h = GorevliHesap.coz(y.govde);
    if (!y.tamam || h == null) {
      setState(() {
        _yukleniyor = false;
        _hata = M.aileAgHata;
      });
      return;
    }
    await depo.gorevliDurumKaydet(h.onayli ? 'onayli' : 'kontrolde');
    if (h.il.isNotEmpty) await depo.gorevliYerKaydet(h.il, h.ilce);
    // URUN §50: ilk açılışta (ya da hesap değişince) KVKK aydınlatması; kabul edilmeden panel görünmez
    if (!depo.gorevliKvkkTamam()) {
      if (h.kvkkKabul != null && h.kvkkKabul!.isNotEmpty) {
        await depo.gorevliKvkkKaydet(h.kvkkKabul!); // sunucuda kabul var: yeniden sorulmaz
      } else {
        final kabul = await Navigator.of(context, rootNavigator: true)
            .push<bool>(MaterialPageRoute(fullscreenDialog: true, builder: (_) => GorevliKvkk(servis: widget.servis)));
        if (!mounted) return;
        if (kabul != true) {
          Navigator.of(context).pop();
          return;
        }
      }
    }
    final l = await s.ilanlarim(tok);
    if (!mounted) return;
    final liste = <Map<String, dynamic>>[
      for (final x in (l.govde?['ilanlar'] as List? ?? const [])) if (x is Map) Map<String, dynamic>.from(x),
    ];
    setState(() {
      _hesap = h;
      _ilanlar = liste;
      _yukleniyor = false;
    });
  }

  Future<void> _ilanAc([Map<String, dynamic>? duzenle]) async {
    final h = _hesap;
    if (h == null) return;
    if (!h.onayli) {
      bildir(context, M.gorevliKontrolBilgi);
      return;
    }
    var hesap = h;
    if (!hesap.profilTamam) {
      // ilk "İlan paylaş": ad-soyad / görev yeri / il-ilçe / unvan BİR KEZ sorulur ve hesapta saklanır
      final kayitli = await Navigator.of(context, rootNavigator: true).push<bool>(MaterialPageRoute(
          builder: (_) => GorevliYerFormu(ilk: true, servis: widget.servis)));
      if (kayitli != true || !mounted) return;
      await _yukle();
      final yeni = _hesap;
      if (!mounted || yeni == null || !yeni.profilTamam) return;
      hesap = yeni;
    }
    if (!mounted) return;
    final tamam = await Navigator.of(context, rootNavigator: true).push<bool>(MaterialPageRoute(
        builder: (_) => GorevliIlanFormu(hesap: hesap, servis: widget.servis, duzenle: duzenle)));
    if (tamam == true && mounted) _yukle();
  }

  /// "Görev yerim değişti": yeni görev yeri/unvan/il-ilçe; başlık kartı hemen yeni yeri gösterir; eski ilanlar değişmez
  Future<void> _yerDegisti() async {
    final h = _hesap;
    if (h == null || !h.onayli || !h.profilTamam) return;
    final tamam = await Navigator.of(context, rootNavigator: true).push<bool>(MaterialPageRoute(
        builder: (_) => GorevliYerFormu(ilk: false, ad: h.adSoyad, il: h.il, ilce: h.ilce, gorevYeri: h.gorevYeri, unvan: h.unvan, servis: widget.servis)));
    if (tamam == true && mounted) {
      await _yukle();
      if (mounted) bildir(context, M.gorevliYerGuncellendi);
    }
  }

  Future<void> _ilanlarimAc() async {
    await Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(
        builder: (_) => GorevliIlanlarim(ilanlar: _ilanlar, onayli: _hesap?.onayli == true, servis: widget.servis, duzenle: _ilanAc)));
    if (mounted) _yukle();
  }

  Widget _baslikKarti(CvRenk r, GorevliHesap h) => Container(
        key: const ValueKey('g_baslik_karti'),
        width: double.infinity,
        margin: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s3),
        padding: const EdgeInsets.symmetric(horizontal: R.s5, vertical: R.s5),
        decoration: BoxDecoration(
          color: r.yuzey,
          borderRadius: BorderRadius.circular(R.kart),
          boxShadow: const [BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 2))],
        ),
        child: !h.profilTamam
            ? Text(M.gorevliProfilYok, key: const ValueKey('g_kart_profil_yok'), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14))
            : Column(children: [
          Text(M.gorevliBaslikKart(h.gorevYeri, h.unvan), key: const ValueKey('g_kart_1'), textAlign: TextAlign.center, style: Y.adim(r)),
          const SizedBox(height: 2),
          Text(h.adSoyad, key: const ValueKey('g_kart_2'), textAlign: TextAlign.center, style: Y.kartAd(r)),
          const SizedBox(height: R.s1),
          Text('${h.il} · ${h.ilce}', key: const ValueKey('g_kart_3'), textAlign: TextAlign.center, style: Y.soluk(r)),
        ]),
      );

  Widget _ilanSatiri(CvRenk r, Map<String, dynamic> i) {
    final durum = _durumYaz(i);
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: R.s2),
      padding: const EdgeInsets.symmetric(horizontal: R.s4, vertical: R.s3),
      decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.dugme)),
      child: Column(children: [
        Text(_ilanAdi(i), textAlign: TextAlign.center, style: Y.satir(r)),
        Text([tarih(i['namaz_tarihi']?.toString()), durum].where((x) => x.isNotEmpty).join(' · '), textAlign: TextAlign.center, style: Y.soluk(r)),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final h = _hesap;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: PopupMenuButton<String>(
              key: const ValueKey('g_menu'),
              tooltip: 'Menü',
              icon: const Icon(Icons.more_vert),
              onSelected: (v) {
                if (v == 'yer') _yerDegisti();
                if (v == 'cikis') _cik(M.gorevliCikisYapildi);
              },
              itemBuilder: (_) => [
                PopupMenuItem(value: 'yer', enabled: h != null && h.onayli && h.profilTamam, child: const Text(M.gorevliYerDegisti)),
                const PopupMenuItem(value: 'cikis', child: Text(M.gorevliCikisYap)),
              ],
            ),
            ust: M.gorevliPanelUst,
            baslik: const BuyukBaslik(M.gorevliUst),
          ),
          if (h != null) _baslikKarti(r, h), // SABİT: ListView'ın dışında
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
              children: [
                if (_yukleniyor && h == null) Padding(padding: const EdgeInsets.only(top: R.s6), child: Text(M.gorevliYukleniyor, textAlign: TextAlign.center, style: Y.soluk(r))),
                if (_hata != null) ...[
                  Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r)),
                  const SizedBox(height: R.s3),
                  IkincilDugme(M.hataTekrar, onTap: _yukle),
                ],
                if (h != null) ...[
                  if (!h.onayli)
                    Container(
                      key: const ValueKey('g_kontrol_kutusu'),
                      width: double.infinity,
                      margin: const EdgeInsets.only(bottom: R.s3),
                      padding: const EdgeInsets.all(R.s4),
                      decoration: BoxDecoration(color: r.yuzey2, borderRadius: BorderRadius.circular(R.kart)),
                      child: Text(M.gorevliKontrolBilgi, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
                    ),
                  // "İlan paylaş": kontrolde iken pasif (soluk) ama dokununca açıklama gösterir
                  GestureDetector(
                    key: const ValueKey('g_ilan_paylas'),
                    behavior: HitTestBehavior.opaque,
                    onTap: h.onayli ? null : () => bildir(context, M.gorevliKontrolBilgi),
                    child: Opacity(opacity: h.onayli ? 1 : 0.45, child: AnaDugme(M.gorevliIlanPaylas, onTap: h.onayli ? () => _ilanAc() : null)),
                  ),
                  const SizedBox(height: R.s3),
                  AnaDugme(M.gorevliIlanlarim(_ilanlar.length), onTap: _ilanlarimAc),
                  const Bolum(M.gorevliSonIlanlar),
                  if (_ilanlar.isEmpty)
                    Text(M.gorevliIlanYok, textAlign: TextAlign.center, style: Y.soluk(r))
                  else
                    for (final i in _ilanlar.take(3)) _ilanSatiri(r, i),
                ],
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

/// İlanlarım: tüm ilanlar; Düzenle / İlanı kaldır
class GorevliIlanlarim extends StatefulWidget {
  final List<Map<String, dynamic>> ilanlar;
  final bool onayli;
  final GorevliServisi? servis;
  final Future<void> Function([Map<String, dynamic>? duzenle]) duzenle;
  const GorevliIlanlarim({super.key, required this.ilanlar, required this.onayli, required this.duzenle, this.servis});
  @override
  State<GorevliIlanlarim> createState() => _GorevliIlanlarimState();
}

class _GorevliIlanlarimState extends State<GorevliIlanlarim> {
  late List<Map<String, dynamic>> _l;
  @override
  void initState() {
    super.initState();
    _l = List.of(widget.ilanlar);
  }

  Future<void> _kaldir(Map<String, dynamic> i) async {
    final d = Kapsam.oku(context);
    final tok = d.depo.gorevliOturum;
    if (tok == null) return;
    final y = await (widget.servis ?? GorevliServisi(istemci: d.veri.istemci)).iptal(tok, i['id']?.toString() ?? '');
    if (!mounted) return;
    if (y.tamam) {
      setState(() => _l.removeWhere((x) => x['id'] == i['id']));
      bildir(context, M.gorevliIlanKalkti);
    } else {
      bildir(context, M.aileAgHata);
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: const SizedBox(width: 40),
            ust: M.gorevliPanelUst,
            baslik: const BuyukBaslik(M.gorevliIlanlarimBaslik),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
              children: [
                if (_l.isEmpty) Padding(padding: const EdgeInsets.only(top: R.s6), child: Text(M.gorevliIlanYok, key: const ValueKey('g_ilanlarim_bos'), textAlign: TextAlign.center, style: Y.soluk(r))),
                for (final i in _l)
                  Container(
                    margin: const EdgeInsets.only(bottom: R.s3),
                    padding: const EdgeInsets.all(R.s4),
                    decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
                    child: Column(children: [
                      Text(_ilanAdi(i), textAlign: TextAlign.center, style: Y.kartAd(r)),
                      Text([tarih(i['namaz_tarihi']?.toString()), _durumYaz(i)].where((x) => x.isNotEmpty).join(' · '),
                          textAlign: TextAlign.center, style: Y.soluk(r)),
                      if (widget.onayli && (i['durum'] == 'yayinda')) ...[
                        const SizedBox(height: R.s3),
                        IkiliSatir(
                          sol: IkincilDugme(M.gorevliDuzenle, yukseklik: 44, onTap: () async {
                            Navigator.of(context).pop();
                            await widget.duzenle(i);
                          }),
                          sag: IkincilDugme(M.gorevliKaldir, yukseklik: 44, onTap: () => _kaldir(i)),
                        ),
                      ],
                    ]),
                  ),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

/// Cenaze ilanı formu: aile formuyla aynı alanlar + mahalle/köy; il ve ilçe KİLİTLİ (kayıttan gelir, değiştirilemez).
class GorevliIlanFormu extends StatefulWidget {
  final GorevliHesap hesap;
  final GorevliServisi? servis;
  final Map<String, dynamic>? duzenle; // dolu ise var olan ilan düzenlenir (duzeltmeId varsa: otomatik ilan verisiyle dolu YENİ düzeltme kaydı)
  final String? duzeltmeId; // URUN §49: düzeltilen otomatik ilanın id'si
  const GorevliIlanFormu({super.key, required this.hesap, this.servis, this.duzenle, this.duzeltmeId});
  @override
  State<GorevliIlanFormu> createState() => _GorevliIlanFormuState();
}

class _GorevliIlanFormuState extends State<GorevliIlanFormu> {
  String? _cins;
  bool _sehit = false; // "Şehit cenazesi" anahtarı: §27 alanları (rütbe, tören yeri, resmî duyuru bağlantısı isteğe bağlı)
  String _vefat = bugunTr();
  String _namaz = bugunTr();
  String? _vakit;
  bool _yukleniyor = false;
  String? _hata;
  final _ad = TextEditingController();
  final _yas = TextEditingController();
  final _mahalle = TextEditingController();
  final _cami = TextEditingController();
  final _mezarlik = TextEditingController();
  final _rutbe = TextEditingController();
  final _toren = TextEditingController();
  final _duyuru = TextEditingController();

  @override
  void initState() {
    super.initState();
    final d = widget.duzenle;
    if (d != null) {
      _ad.text = d['ad_soyad']?.toString() ?? '';
      _cins = d['cinsiyet']?.toString();
      _yas.text = d['yas']?.toString() ?? '';
      _vefat = d['vefat_tarihi']?.toString() ?? _vefat;
      _namaz = d['namaz_tarihi']?.toString() ?? _namaz;
      _mahalle.text = d['mahalle']?.toString() ?? '';
      _mezarlik.text = d['defin_yeri']?.toString() ?? '';
      _sehit = d['sehit'] == true;
      _rutbe.text = d['rutbe']?.toString() ?? '';
      _toren.text = d['toren']?.toString() ?? '';
      if (widget.duzeltmeId != null) {
        _vakit = _bos(d['namaz_vakti']?.toString() ?? '');
        _cami.text = d['namaz_cami']?.toString() ?? '';
      }
    }
  }

  @override
  void dispose() {
    for (final c in [_ad, _yas, _mahalle, _cami, _mezarlik, _rutbe, _toren, _duyuru]) {
      c.dispose();
    }
    super.dispose();
  }

  static int _kelime(String s) => s.trim().split(RegExp(r'\s+')).where((x) => x.isNotEmpty).length;
  bool get _hazir => (!_sehit || _rutbe.text.trim().length >= 2) && _cins != null && _kelime(_ad.text) >= 2 && _kelime(_ad.text) <= 5 && (_yas.text.trim().isEmpty || int.tryParse(_yas.text.trim()) != null);
  String? _bos(String s) {
    final t = s.trim().replaceAll(RegExp(r'\s+'), ' ');
    return t.isEmpty ? null : t;
  }

  DateTime _yerel(String g) {
    final d = gunCoz(g)!;
    return DateTime(d.year, d.month, d.day);
  }

  Future<void> _tarihSec(bool vefat) async {
    final simdi = _yerel(bugunTr());
    var ilk = _yerel(vefat ? _vefat : _namaz);
    var son = vefat ? simdi : simdi.add(const Duration(days: 3));
    var bas = simdi.subtract(const Duration(days: 4));
    if (ilk.isBefore(bas)) bas = ilk; // düzeltmede otomatik ilanın tarihi 4 günden eski olabilir
    if (ilk.isAfter(son)) son = ilk;
    final g = await showDatePicker(context: context, initialDate: ilk, firstDate: bas, lastDate: son);
    if (g != null && mounted) setState(() => vefat ? _vefat = gunYaz(g) : _namaz = gunYaz(g));
  }

  Map<String, dynamic> _govde() {
    final cami = _bos(_cami.text);
    final namazYeri = _vakit != null && cami != null ? '$_vakit-$cami' : (cami != null ? '-$cami' : _vakit);
    final mahalle = _bos(_mahalle.text);
    final mezarlik = _bos(_mezarlik.text);
    final yas = int.tryParse(_yas.text.trim());
    return {
      if (widget.duzenle != null && widget.duzeltmeId == null) 'ilan_id': widget.duzenle!['id'],
      if (widget.duzeltmeId != null) 'duzeltme_id': widget.duzeltmeId,
      'ad_soyad': _bos(_ad.text),
      'cinsiyet': _cins,
      if (yas != null) 'yas': yas,
      'vefat_tarihi': _vefat,
      'namaz_tarihi': _namaz,
      if (namazYeri != null) 'namaz_yeri_vakti': namazYeri,
      if (mezarlik != null) 'defin_yeri': mezarlik,
      if (mahalle != null) 'koy': mahalle,
      if (_sehit) 'sehit': true,
      if (_sehit) 'rutbe': _bos(_rutbe.text),
      if (_sehit && _bos(_toren.text) != null) 'toren_yeri': _bos(_toren.text),
      if (_sehit && _bos(_duyuru.text) != null) 'duyuru_url': _bos(_duyuru.text),
      // il / ilçe GÖNDERİLMEZ: sunucu kayıttan alır (kilit)
    };
  }

  Future<void> _gonder() async {
    if (_yukleniyor || !_hazir) return;
    final d = Kapsam.oku(context);
    final tok = d.depo.gorevliOturum;
    if (tok == null) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final s = widget.servis ?? GorevliServisi(istemci: d.veri.istemci);
    final y = (widget.duzenle != null && widget.duzeltmeId == null) ? await s.duzenle(tok, _govde()) : await s.ilan(tok, _govde());
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    if (y.tamam && y.durum == 'yayinda') {
      bildir(context, widget.duzeltmeId != null ? M.gorevliDuzeltmeAlindi : (widget.duzenle != null ? M.gorevliIlanGuncel : M.gorevliIlanTamam));
      Navigator.of(context).pop(true);
    } else if (y.durum == 'red') {
      setState(() => _hata = y.neden ?? M.aileRed);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  Widget _kilit(CvRenk r, String etiket, String deger) => Padding(
        padding: const EdgeInsets.only(bottom: R.s3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
          const SizedBox(height: 6),
          Opacity(opacity: 0.6, child: IkincilDugme(deger, onTap: null)),
        ]),
      );

  Widget _secim(CvRenk r, String etiket, String deger, VoidCallback onTap) => Padding(
        padding: const EdgeInsets.only(bottom: R.s3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
          const SizedBox(height: 6),
          IkincilDugme(deger, onTap: onTap),
        ]),
      );

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    void yenile(String _) => setState(() {});
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: const SizedBox(width: 40),
            ust: M.gorevliPanelUst,
            baslik: const BuyukBaslik(M.gorevliIlanFormBaslik),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
              children: [
                _kilit(r, M.alanIl, widget.hesap.il),
                _kilit(r, M.alanIlce, widget.hesap.ilce),
                Text(M.gorevliYerKilit, key: const ValueKey('g_yer_kilit'), textAlign: TextAlign.center, style: Y.soluk(r)),
                const SizedBox(height: R.s4),
                // Şehit cenazesi anahtarı: açılınca §27 alanları ve dili ("Şehidimiz [Rütbe Ad Soyad]", "Cenaze töreni"); ilan sehit:true ile yayına girer, listede en üstte
                SwitchListTile(
                  key: const ValueKey('gi_sehit'),
                  value: _sehit,
                  onChanged: (v) => setState(() => _sehit = v),
                  title: Text(M.gorevliSehitAnahtar, style: Y.satir(r)),
                  contentPadding: EdgeInsets.zero,
                ),
                if (_sehit) ...[
                  FormAlani(key: const ValueKey('gi_rutbe'), etiket: M.sehitRutbe, ipucu: M.sehitRutbeYer, denetleyici: _rutbe, enCok: 60, onChanged: yenile),
                  FormAlani(key: const ValueKey('gi_toren'), etiket: M.sehitTorenYeri, ipucu: M.sehitTorenYer, denetleyici: _toren, enCok: 60),
                  FormAlani(key: const ValueKey('gi_duyuru'), etiket: '${M.sehitDuyuruAlan} (isteğe bağlı)', ipucu: 'https://', denetleyici: _duyuru, enCok: 150),
                ],
                Row(children: [
                  Expanded(child: IkincilDugme(M.erkek, yukseklik: 44, secili: _cins == 'e', onTap: () => setState(() => _cins = 'e'))),
                  const SizedBox(width: R.s2),
                  Expanded(child: IkincilDugme(M.kadin, yukseklik: 44, secili: _cins == 'k', onTap: () => setState(() => _cins = 'k'))),
                ]),
                const SizedBox(height: R.s3),
                FormAlani(key: const ValueKey('gi_ad'), etiket: M.alanAd, denetleyici: _ad, enCok: 60, onChanged: yenile),
                FormAlani(key: const ValueKey('gi_yas'), etiket: M.alanYas, ipucu: M.alanYasYer, denetleyici: _yas, klavye: TextInputType.number, enCok: 3, onChanged: yenile),
                FormAlani(key: const ValueKey('gi_mahalle'), etiket: M.gorevliMahalleKoy, denetleyici: _mahalle, enCok: 60),
                _secim(r, M.alanVefat, tarih(_vefat), () => _tarihSec(true)),
                _secim(r, M.alanNamazTarihi, tarih(_namaz), () => _tarihSec(false)),
                for (final v in [...M.namazSecenek.take(6), if (_vakit != null && !M.namazSecenek.take(6).contains(_vakit)) _vakit!])
                  Padding(padding: const EdgeInsets.only(bottom: R.s2), child: IkincilDugme(v, yukseklik: 44, secili: _vakit == v, onTap: () => setState(() => _vakit = v))),
                FormAlani(key: const ValueKey('gi_cami'), etiket: M.alanCami, ipucu: M.alanCamiYer, denetleyici: _cami, enCok: 40),
                FormAlani(key: const ValueKey('gi_mezarlik'), etiket: M.alanMezarlik, ipucu: M.alanMezarlikYer, denetleyici: _mezarlik, enCok: 60),
                if (_hata != null) Padding(padding: const EdgeInsets.only(bottom: R.s3), child: Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r))),
                AnaDugme(widget.duzenle != null && widget.duzeltmeId == null ? M.gorevliKaydet : (widget.duzeltmeId != null ? M.gorevliKaydet : M.gorevliGonder), onTap: (_hazir && !_yukleniyor) ? _gonder : null),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}


/// URUN §50: panel ilk açılışta tam ekran KVKK aydınlatması. Geri tuşu kapatmaz; tek yol "Okudum, anladım" (true döner).
class GorevliKvkk extends StatefulWidget {
  final GorevliServisi? servis;
  const GorevliKvkk({super.key, this.servis});
  @override
  State<GorevliKvkk> createState() => _GorevliKvkkState();
}

class _GorevliKvkkState extends State<GorevliKvkk> {
  bool _bekle = false;

  Future<void> _kabul() async {
    if (_bekle) return;
    setState(() => _bekle = true);
    final d = Kapsam.oku(context);
    final tok = d.depo.gorevliOturum;
    final tarih = DateTime.now().toUtc().toIso8601String();
    await d.depo.gorevliKvkkKaydet(tarih);
    if (tok != null) {
      // sunucu kaydı en iyi çabayla: ağ yoksa cihaz kaydı yeter, sonraki girişte sunucu "kabul yok" derse bir kez daha sorulur
      await (widget.servis ?? GorevliServisi(istemci: d.veri.istemci)).kvkkKabul(tok);
    }
    if (mounted) Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return PopScope(
      canPop: false,
      child: Scaffold(
        body: SafeArea(
          child: Column(children: [
            Expanded(
              child: ListView(
                key: const ValueKey('g_kvkk'),
                padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s4),
                children: [
                  Text(M.gorevliKvkkBaslik, textAlign: TextAlign.center, style: Y.buyuk(r)),
                  const SizedBox(height: R.s4),
                  for (final m in M.gorevliKvkkMetin)
                    Padding(
                      padding: const EdgeInsets.only(bottom: R.s3),
                      child: Text(m, style: Y.govde(r).copyWith(fontSize: 15)),
                    ),
                  Center(
                    child: TextButton(
                      key: const ValueKey('g_kvkk_tam'),
                      onPressed: () => metinPenceresi(context, M.gizlilikBaslik, M.gizlilikMetin),
                      child: const Text(M.gorevliKvkkTam),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s5),
              child: AnaDugme(M.gorevliKvkkOku, onTap: _bekle ? null : _kabul),
            ),
          ]),
        ),
      ),
    );
  }
}
