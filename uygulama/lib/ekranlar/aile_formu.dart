// Aile / Tam Sayfa / Şehit formu (URUN-TASLAGI §15/§17/§21; sözleşme: deploy/AILE-ILAN-SOZLESME.md; ölçü: tasarim/prototip.html p-form).
// Adım 0 giriş kartı (aile: "Cenaze ilanı paylaşın"; Tam Sayfa: 200 ₺ fiyat kartı; şehit formu doğrudan 1. adımla açılır),
// 1 vefat eden · 2 cenaze · 3 başvuran (ad, TELEFON, yakınlık; e-posta ve T.C. YOK) · 4 belge kodu (aile: isteğe bağlı;
// Tam Sayfa: zorunlu; şehit: resmî duyuru bağlantısı) · 5 yasal beyan (Tam Sayfa: "Ödemeye geç" → ödeme ekranı).
// Gönderim: POST /aile/basvur → telefon kodu (WhatsApp/SMS) → POST /aile/dogrula → sonuç. Serbest metin yok; her alan en çok 60 karakter.
import 'dart:async';

import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/aile.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';
import 'sehit_bilgi.dart';

enum _Faz { form, kod, sonuc }

class AileFormu extends StatefulWidget {
  final String il;
  final String? ilce;
  final bool tam; // Tam Sayfa vefat ilanı (§17/2): il seçilebilir, fiyat kartı, ödeme adımı
  final bool sehit; // Şehit ilanı (§27): rütbe, tören yeri, resmî duyuru; ücret yok
  final AileServisi? servis; // testlerde sahte ağ; verilmezse uygulamanın http istemcisi + aileKok
  const AileFormu({super.key, required this.il, this.ilce, this.tam = false, this.sehit = false, this.servis});
  @override
  State<AileFormu> createState() => _AileFormuState();
}

class _AileFormuState extends State<AileFormu> {
  _Faz _faz = _Faz.form;
  late int _adim; // 0 giriş kartı, 1–5 adımlar (şehitte 1'den başlar)
  String? _cins;
  late String _il;
  String? _ilce;
  bool _odeme = false;
  bool _belgeTamam = false;
  String _vefat = bugunTr();
  String _namaz = bugunTr();
  String? _vakit; // 'Öğle namazı' … ya da seçilmemiş
  String _yakinlik = M.yakinlikSecenek.first;
  bool _onay = false;
  bool _yukleniyor = false;
  String? _hata;
  String? _basvuruId;
  int _kalan = 0;
  Timer? _sayac;
  bool _yayinda = false;
  String? _neden;
  final _kay = ScrollController();
  final _ad = TextEditingController();
  final _rutbe = TextEditingController();
  final _yas = TextEditingController();
  final _mahalle = TextEditingController();
  final _cami = TextEditingController();
  final _toren = TextEditingController();
  final _mezarlik = TextEditingController();
  final _belge = TextEditingController();
  final _basvuranAd = TextEditingController();
  final _tel = TextEditingController();
  final _kod = TextEditingController();

  bool get _sehit => widget.sehit;
  bool get _tam => widget.tam && !widget.sehit;
  bool get _ucretli => _tam && odemeAcik;
  int get _enAz => _sehit ? 1 : 0;

  @override
  void initState() {
    super.initState();
    _il = widget.il;
    _ilce = widget.ilce;
    _adim = _enAz;
  }

  @override
  void dispose() {
    _sayac?.cancel();
    _kay.dispose();
    for (final c in [_ad, _rutbe, _yas, _mahalle, _cami, _toren, _mezarlik, _belge, _basvuranAd, _tel, _kod]) {
      c.dispose();
    }
    super.dispose();
  }

  // ---- Denetimler (sunucu kuralları K2/K3 ile uyumlu; asıl denetim sunucuda) ----
  /// 10 haneli cep numarası (5xx…); +90 / 0 ile yazılsa da kabul (sunucu da aynı kuralı uygular)
  static String? _telNormal(String t) {
    var d = t.replaceAll(RegExp(r'[\s().-]'), '');
    if (d.startsWith('+90')) {
      d = d.substring(3);
    } else if (d.startsWith('0090')) {
      d = d.substring(4);
    } else if (d.startsWith('0')) {
      d = d.substring(1);
    }
    return RegExp(r'^5\d{9}$').hasMatch(d) ? d : null;
  }

  static int _kelime(String s) => s.trim().split(RegExp(r'\s+')).where((x) => x.isNotEmpty).length;
  static bool _adGecerli(String s) {
    final n = _kelime(s);
    return n >= 2 && n <= 5;
  }

  bool get _yasGecerli {
    final t = _yas.text.trim();
    if (t.isEmpty) return true;
    final n = int.tryParse(t);
    return n != null && n >= 0 && n <= 130;
  }

  bool get _adim1Hazir =>
      _cins != null &&
      _adGecerli(_ad.text) &&
      _ilce != null &&
      _yasGecerli &&
      (!_sehit || _rutbe.text.trim().length >= 2);
  bool get _adim3Hazir =>
      _adGecerli(_basvuranAd.text) && _telNormal(_tel.text) != null;
  bool get _belgeZorunlu => _tam || _sehit;
  bool get _adim4Hazir => !_belgeZorunlu || _belgeTamam;
  bool get _hazir => _adim1Hazir && _adim3Hazir && _adim4Hazir && _onay;

  bool get _devamHazir {
    switch (_adim) {
      case 1:
        return _adim1Hazir;
      case 3:
        return _adim3Hazir;
      case 4:
        return _adim4Hazir;
      default:
        return true;
    }
  }

  bool get _geriCikabilir => _faz == _Faz.sonuc || (_faz == _Faz.form && _adim == _enAz && !_odeme);

  void _yukariKay() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_kay.hasClients) _kay.jumpTo(0);
    });
  }

  void _adimGit(int a) {
    setState(() {
      _adim = a;
      _hata = null;
    });
    _yukariKay();
  }

  void _geri() {
    if (_odeme) {
      setState(() {
        _odeme = false;
        _hata = null;
      });
      _yukariKay();
    } else if (_faz == _Faz.kod) {
      _sayac?.cancel();
      setState(() {
        _faz = _Faz.form;
        _hata = null;
      });
    } else if (_faz == _Faz.form && _adim > _enAz) {
      _adimGit(_adim - 1);
    } else {
      Navigator.of(context).pop();
    }
  }

  // ---- Ağ ----
  AileServisi _servis() => widget.servis ?? AileServisi(istemci: Kapsam.oku(context).veri.istemci);

  String? _bos(String s) {
    final t = s.trim().replaceAll(RegExp(r'\s+'), ' ');
    return t.isEmpty ? null : t;
  }

  Map<String, dynamic> _govde() {
    final mahalle = _bos(_mahalle.text);
    final yas = int.tryParse(_yas.text.trim());
    final cami = _bos(_cami.text);
    final namazYeri = _vakit != null && cami != null ? '$_vakit-$cami' : (cami != null ? '-$cami' : _vakit);
    final mezarlik = _bos(_mezarlik.text);
    final belge = _bos(_belge.text);
    final rutbe = _bos(_rutbe.text);
    final toren = _bos(_toren.text);
    return {
      'il': _il,
      'ilce': _ilce,
      if (mahalle != null) 'mahalle': mahalle,
      'ad_soyad': _bos(_ad.text),
      'cinsiyet': _cins,
      if (yas != null) 'yas': yas,
      'vefat_tarihi': _vefat,
      'namaz_tarihi': _namaz,
      if (namazYeri != null) 'namaz_yeri_vakti': namazYeri,
      if (mezarlik != null) 'defin_yeri': mezarlik,
      'basvuran': {
        'ad_soyad': _bos(_basvuranAd.text),
        'telefon': _telNormal(_tel.text),
        'yakinlik': _yakinlik,
      },
      'beyan': true,
      // Tam Sayfa ve şehit alanları (sözleşmeye eklenecek: Worker tarafı `tam`, `sehit`, `rutbe`, `toren_yeri`, `duyuru_url`)
      if (_tam) 'tam': true,
      if (_sehit) 'sehit': true,
      if (_sehit && rutbe != null) 'rutbe': rutbe,
      if (_sehit && toren != null) 'toren_yeri': toren,
      if (_sehit && belge != null) 'duyuru_url': belge,
      if (!_sehit && belge != null) 'edevlet_kodu': belge,
    };
  }

  void _sayacBaslat() {
    _sayac?.cancel();
    _kalan = 60;
    _sayac = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() => _kalan = _kalan > 0 ? _kalan - 1 : 0);
      if (_kalan <= 0) t.cancel();
    });
  }

  void _redGoster(String? neden) {
    _sayac?.cancel();
    setState(() {
      _faz = _Faz.sonuc;
      _yayinda = false;
      _neden = neden;
    });
  }

  /// 5. adımdaki ana düğme: Tam Sayfa'da ödeme ekranına geçer, diğerlerinde doğrudan gönderir.
  Future<void> _gonder() async {
    if (_ucretli) {
      setState(() {
        _odeme = true;
        _hata = null;
      });
      _yukariKay();
      return;
    }
    await _basvur();
  }

  /// Ödeme ekranındaki "Ödemeyi onayla" da buraya gelir.
  /// TODO(Play Billing): gerçek tahsilat bağlanınca burada önce satın alma doğrulanır; şimdilik ödeme adımı yalnız görünümdür
  /// ve ardından mevcut Worker gönderimi (tam:true) çalışır.
  Future<void> _basvur() async {
    if (_yukleniyor || !_hazir) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().basvur(_govde());
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    final id = y.govde?['basvuru_id']?.toString();
    if (y.tamam && id != null && id.isNotEmpty) {
      setState(() {
        _basvuruId = id;
        _faz = _Faz.kod;
        _odeme = false;
        _kod.clear();
      });
      _sayacBaslat();
      _yukariKay();
    } else if (y.durum == 'red') {
      _redGoster(y.neden);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  Future<void> _yenidenGonder() async {
    if (_yukleniyor || _kalan > 0) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().basvur(_govde());
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    final id = y.govde?['basvuru_id']?.toString();
    if (y.tamam && id != null && id.isNotEmpty) {
      setState(() => _basvuruId = id);
      _sayacBaslat();
      bildir(context, M.kodGitti);
    } else if (y.durum == 'red') {
      _redGoster(y.neden);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  Future<void> _dogrula() async {
    if (_yukleniyor) return;
    final kod = _kod.text.trim();
    if (kod.length != 6) {
      bildir(context, M.kodEksik);
      return;
    }
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().dogrula(_basvuruId ?? '', kod);
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    if (y.durum == 'yayinda') {
      _sayac?.cancel();
      setState(() {
        _faz = _Faz.sonuc;
        _yayinda = true;
        _neden = null;
      });
    } else if (y.durum == 'red') {
      _redGoster(y.neden);
    } else if (y.agHatasi || y.kod >= 500) {
      setState(() => _hata = M.aileAgHata);
    } else {
      bildir(context, M.kodHatali);
    }
  }

  /// Prototipteki "Belgeyi/Duyuruyu doğrula": biçim denetimi; asıl doğrulama sunucuda (K9)
  void _belgeDogrula() {
    final v = _belge.text.replaceAll(RegExp(r'[^A-Za-z0-9]'), '');
    if (v.length < 8) {
      bildir(context, M.kodEksik);
      return;
    }
    setState(() => _belgeTamam = true);
  }

  Future<void> _tarihSec() async {
    final simdi = gunCoz(bugunTr())!;
    final s = gunCoz(_vefat) ?? simdi;
    final g = await showDatePicker(
      context: context,
      initialDate: DateTime(s.year, s.month, s.day),
      // Sözleşme K3: namaz tarihi bugün-1'den önce olamaz ve vefattan en çok 3 gün sonra olabilir
      firstDate: DateTime(simdi.year, simdi.month, simdi.day).subtract(const Duration(days: 4)),
      lastDate: DateTime(simdi.year, simdi.month, simdi.day),
    );
    if (g != null && mounted) {
      setState(() {
        _vefat = gunYaz(g);
        _namazUydur();
      });
    }
  }

  String get _namazAlt {
    final alt = gunEkle(bugunTr(), -1);
    return _vefat.compareTo(alt) > 0 ? _vefat : alt;
  }

  String get _namazUst {
    final u1 = gunEkle(_vefat, 3), u2 = gunEkle(bugunTr(), 3);
    return u1.compareTo(u2) < 0 ? u1 : u2;
  }

  void _namazUydur() {
    if (_namaz.compareTo(_namazAlt) < 0) _namaz = _namazAlt;
    if (_namaz.compareTo(_namazUst) > 0) _namaz = _namazUst;
  }

  DateTime _yerel(String g) {
    final d = gunCoz(g)!;
    return DateTime(d.year, d.month, d.day);
  }

  Future<void> _namazTarihSec() async {
    final g = await showDatePicker(
      context: context,
      initialDate: _yerel(_namaz),
      firstDate: _yerel(_namazAlt),
      lastDate: _yerel(_namazUst),
    );
    if (g != null && mounted) setState(() => _namaz = gunYaz(g));
  }

  Future<void> _ilSec() async {
    final d = Kapsam.oku(context);
    final s = await _listeSec(d.gomulu.iller);
    if (s != null && mounted && s != _il) {
      setState(() {
        _il = s;
        _ilce = null;
      });
    }
  }

  Future<void> _ilceSec() async {
    final d = Kapsam.oku(context);
    final s = await _listeSec(d.ilceListesi(_il));
    if (s != null && mounted) setState(() => _ilce = s);
  }

  Future<String?> _listeSec(List<String> liste) {
    return showDialog<String>(
      context: context,
      builder: (c) {
        final r = c.renk;
        return Dialog(
          backgroundColor: r.yuzey,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 480, maxWidth: 320),
            child: ListView(shrinkWrap: true, children: [
              for (final i in liste)
                InkWell(
                  onTap: () => Navigator.of(c).pop(i),
                  child: Container(
                    height: 48,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(border: Border(top: BorderSide(color: r.cizgi))),
                    child: Text(i, style: Y.satir(r)),
                  ),
                ),
            ]),
          ),
        );
      },
    );
  }


  @override
  Widget build(BuildContext context) {
    if (widget.sehit) return const SehitBilgiEkrani(); // 15.10.2026: şehit ilanı yalnız din görevlisi panelinden
    final r = context.renk;
    String ust;
    if (_faz == _Faz.sonuc) {
      ust = M.aileBittiUst;
    } else if (_faz == _Faz.kod) {
      ust = M.kodUst;
    } else if (_odeme) {
      ust = M.odemeUst;
    } else if (_adim == 0) {
      ust = _tam ? M.formTamUst : M.aileUstGiris;
    } else {
      ust = M.formUst(_adim);
    }
    final baslik = _sehit ? M.sehitFormBaslik : (_tam ? M.formTamBaslik : M.aileBaslik);
    final cubukGorunur = _faz == _Faz.form && _adim >= 1 && !_odeme;
    return PopScope(
      canPop: _geriCikabilir,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _geri();
      },
      child: Scaffold(
        body: SafeArea(
          child: Column(children: [
            BaslikCubugu(
              sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: _geri),
              sag: YuvarlakDugme(ikon: 'kapat', anlam: 'Kapat', onTap: () => Navigator.of(context).pop()),
              ust: ust,
              baslik: BuyukBaslik(baslik),
            ),
            _ilerleme(r, cubukGorunur),
            Expanded(
              child: ListView(
                controller: _kay,
                padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
                children: _faz == _Faz.sonuc
                    ? _sonucGorunumu(r)
                    : (_faz == _Faz.kod ? _kodGorunumu(r) : (_odeme ? _odemeGorunumu(r) : _form(r))),
              ),
            ),
            _altCubuk(r),
          ]),
        ),
      ),
    );
  }

  /// Prototipteki 5 parçalı ilerleme çubuğu (giriş, ödeme ve sonuç ekranlarında gizli ama yer tutar)
  Widget _ilerleme(CvRenk r, bool gorunur) => Opacity(
        opacity: gorunur ? 1 : 0,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s4),
          child: Row(children: [
            for (int i = 1; i <= 5; i++) ...[
              if (i > 1) const SizedBox(width: 6),
              Expanded(
                child: Container(
                  key: ValueKey('adim_$i'),
                  height: 4,
                  decoration: BoxDecoration(
                    color: i <= _adim ? r.vurgu : r.yuzey2,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ],
          ]),
        ),
      );

  /// Prototipteki alt çubuk (alt-cubuk): [Ödenecek] + ana düğme + küçük not
  Widget _altCubuk(CvRenk r) {
    String yazi;
    VoidCallback? onTap;
    String? not;
    var odenecek = false;
    if (_faz == _Faz.sonuc) {
      yazi = M.aileBittiDugme;
      onTap = () => Navigator.of(context).pop();
    } else if (_faz == _Faz.kod) {
      yazi = _hata != null ? M.hataTekrar : M.kodDugme;
      onTap = _yukleniyor ? null : _dogrula;
    } else if (_odeme) {
      yazi = _hata != null ? M.hataTekrar : M.odemeDugme;
      onTap = _yukleniyor ? null : _basvur;
    } else if (_adim < 5) {
      yazi = M.formDevam;
      onTap = _devamHazir ? () => _adimGit(_adim + 1) : null;
    } else {
      if (_ucretli) {
        yazi = M.adim5TamDugme;
        not = M.adim5TamNot;
        odenecek = true;
      } else {
        yazi = _hata != null ? M.hataTekrar : M.sonDugme;
        not = _sehit ? M.sehitNot : M.aileNot;
      }
      onTap = (_hazir && !_yukleniyor) ? _gonder : null;
    }
    return Container(
      padding: const EdgeInsets.fromLTRB(R.s5, R.s3, R.s5, R.s5),
      decoration: BoxDecoration(color: r.zemin, border: Border(top: BorderSide(color: r.cizgi))),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        if (_hata != null && _faz == _Faz.form && (_odeme || _adim == 5)) _hataKutusu(r),
        if (_hata != null && _faz == _Faz.kod) _hataKutusu(r),
        if (odenecek) ...[
          Text(M.adim5TamTutar, textAlign: TextAlign.center, style: Y.kucuk(r).copyWith(fontSize: 13)),
          const SizedBox(height: R.s2),
        ],
        AnaDugme(yazi, onTap: onTap),
        if (not != null) ...[
          const SizedBox(height: R.s2),
          Text(not, textAlign: TextAlign.center, style: Y.soluk(r).copyWith(fontSize: 12)),
        ],
      ]),
    );
  }

  /// Prototipteki ödeme ekranı: "Ödeme / Mağaza içi satın alma", logo + ürün + üç satır, not
  List<Widget> _odemeGorunumu(CvRenk r) {
    Widget satir(String et, String deger) => Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: R.s5, vertical: R.s3),
          decoration: BoxDecoration(border: Border(top: BorderSide(color: r.cizgi))),
          child: Column(children: [
            Text(et, textAlign: TextAlign.center, style: TextStyle(fontSize: 15, color: r.metin2)),
            const SizedBox(height: 2),
            Text(deger, textAlign: TextAlign.center, style: TextStyle(fontSize: 15, color: r.metin)),
          ]),
        );
    return [
      _baslik(r, M.odemeUst, M.odemeAlt),
      Container(
        decoration: BoxDecoration(
          color: r.yuzey,
          borderRadius: BorderRadius.circular(R.kart),
          boxShadow: const [BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 2))],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s4),
            child: Column(children: [
              const Logo(boyut: 64, yaricap: 16),
              const SizedBox(height: R.s3),
              Text(M.odemeUrunAd,
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: r.metin)),
              const SizedBox(height: 2),
              Text(M.odemeUrunAlt, textAlign: TextAlign.center, style: Y.soluk(r)),
            ]),
          ),
          satir(M.odemeTutarEt, M.odemeTutar),
          satir(M.odemeHesapEt, M.odemeHesap),
          satir(M.odemeYayinEt, M.odemeYayin),
        ]),
      ),
      const SizedBox(height: R.s4),
      Text(M.odemeNot, textAlign: TextAlign.center, style: Y.soluk(r)),
    ];
  }

  List<Widget> _sonucGorunumu(CvRenk r) {
    final moderasyonlu = _tam || _sehit;
    return [
      const SizedBox(height: R.s6),
      if (_yayinda && !moderasyonlu)
        const BosDurum(ikon: 'tik', baslik: M.aileYayinda)
      else if (_yayinda)
        BosDurum(
            ikon: 'tik',
            baslik: M.aileBittiBaslik,
            aciklama: _sehit ? M.sehitBittiYazi : M.aileBittiAciklama(_il))
      else
        BosDurum(ikon: 'uyari', baslik: M.aileRed, aciklama: _neden),
      if (!_yayinda) ...[
        const SizedBox(height: R.s3),
        IkincilDugme(M.odemeGeri, onTap: () {
          setState(() {
            _faz = _Faz.form;
            _odeme = false;
            _onay = false;
          });
          _adimGit(_enAz == 0 ? 1 : _enAz);
        }),
      ],
    ];
  }

  Widget _hataKutusu(CvRenk r) => _hata == null
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.only(bottom: R.s3),
          child: Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r)),
        );

  List<Widget> _kodGorunumu(CvRenk r) => [
        _baslik(r, M.kodBaslik, M.kodAciklamaTel),
        FormAlani(
            key: const ValueKey('f_kod'),
            etiket: M.kodAlan,
            ipucu: M.kodYer,
            denetleyici: _kod,
            klavye: TextInputType.number,
            enCok: 6),
        const SizedBox(height: R.s2),
        IkincilDugme(_kalan > 0 ? M.kodBekle(_kalan) : M.kodYeniden,
            onTap: (_kalan > 0 || _yukleniyor) ? null : _yenidenGonder),
      ];

  /// Prototipteki durum-kutu: [tik] metin [boşluk]
  Widget _durum(CvRenk r, String metin, {bool kartIci = false}) => Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: R.s2),
        padding: const EdgeInsets.symmetric(horizontal: R.s4, vertical: R.s3),
        decoration: BoxDecoration(
          color: kartIci ? r.yuzey2 : r.yuzey,
          borderRadius: BorderRadius.circular(R.dugme),
        ),
        child: Row(children: [
          Ikon('tik', boyut: 20, renk: r.vurguMetin),
          const SizedBox(width: R.s3),
          Expanded(child: Text(metin, textAlign: TextAlign.center, style: TextStyle(fontSize: 14, height: 19 / 14, color: r.metin))),
          const SizedBox(width: R.s3 + 20),
        ]),
      );

  /// Prototipteki fiyat-kart: üst etiket, (varsa 44 pt tutar), küçük not, durum kutuları
  Widget _girisKarti(CvRenk r, String etiket, String? tutar, String not, List<String> maddeler) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: R.s5, vertical: R.s6),
        decoration: BoxDecoration(
          color: r.yuzey,
          borderRadius: BorderRadius.circular(R.kart),
          boxShadow: const [BoxShadow(color: Color(0x14000000), blurRadius: 12, offset: Offset(0, 2))],
        ),
        child: Column(children: [
          Text(trBuyuk(etiket), textAlign: TextAlign.center, style: Y.ustEtiket(r)),
          if (tutar != null) ...[
            const SizedBox(height: R.s2),
            Text(tutar,
                textAlign: TextAlign.center,
                style: TextStyle(
                    fontSize: 44, height: 52 / 44, fontWeight: FontWeight.w700, letterSpacing: -1, color: r.vurguMetin)),
          ] else
            const SizedBox(height: 6),
          Text(not, textAlign: TextAlign.center, style: Y.soluk(r)),
          const SizedBox(height: R.s5),
          for (final m in maddeler) _durum(r, m, kartIci: true),
        ]),
      );

  Widget _baslik(CvRenk r, String b, [String? a]) => Padding(
        padding: const EdgeInsets.only(top: R.s6, bottom: R.s3),
        child: Column(children: [
          Text(b, textAlign: TextAlign.center, style: Y.adim(r)),
          if (a != null) ...[
            const SizedBox(height: R.s1),
            Text(a, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          ],
        ]),
      );

  Widget _secimDugmesi(CvRenk r, String etiket, String deger, VoidCallback onTap) => Padding(
        padding: const EdgeInsets.only(bottom: R.s3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
          const SizedBox(height: 6),
          IkincilDugme(deger, onTap: onTap),
        ]),
      );

  Widget _secenekler(CvRenk r, String etiket, List<String> secenek, String secili, ValueChanged<String> sec) {
    final satirlar = <Widget>[];
    for (int i = 0; i < secenek.length; i += 2) {
      if (i > 0) satirlar.add(const SizedBox(height: R.s2));
      satirlar.add(IkiliSatir(
        sol: IkincilDugme(secenek[i], yukseklik: 44, secili: secili == secenek[i], onTap: () => sec(secenek[i])),
        sag: i + 1 < secenek.length
            ? IkincilDugme(secenek[i + 1],
                yukseklik: 44, secili: secili == secenek[i + 1], onTap: () => sec(secenek[i + 1]))
            : const SizedBox(height: 44),
      ));
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: R.s3),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
        const SizedBox(height: 6),
        ...satirlar,
      ]),
    );
  }

  List<Widget> _form(CvRenk r) {
    void yenile(String _) => setState(() {});
    switch (_adim) {
      case 0:
        if (_tam) {
          return [
            _baslik(r, M.fiyatBaslik, M.fiyatAciklama),
            _girisKarti(r, M.fiyatEtiket, M.fiyatTutar, M.fiyatNot,
                [M.fiyatMadde1, M.fiyatMadde2, M.fiyatMadde3, M.fiyatMadde4]),
          ];
        }
        return [
          _baslik(r, M.aileGirisBaslik, M.aileGirisAciklama(_il)),
          _girisKarti(r, M.aileGirisEtiket, null, M.aileGirisNot, [M.aileMadde1, M.aileMadde3, M.aileMadde4]),
        ];
      case 1:
        return [
          _baslik(r, _sehit ? M.sehitAdim1 : M.adim1Baslik, M.adim1Aciklama),
          if (_sehit)
            FormAlani(
                key: const ValueKey('f_rutbe'),
                etiket: M.sehitRutbe,
                ipucu: M.sehitRutbeYer,
                denetleyici: _rutbe,
                enCok: 60,
                onChanged: yenile),
          _secenekler(r, M.alanCinsiyet, const [M.erkek, M.kadin],
              _cins == 'e' ? M.erkek : (_cins == 'k' ? M.kadin : ''), (v) => setState(() => _cins = v == M.erkek ? 'e' : 'k')),
          FormAlani(
              key: const ValueKey('f_ad'),
              etiket: M.alanAd,
              ipucu: _sehit ? M.sehitAdYer : M.alanAdYer(_cins),
              denetleyici: _ad,
              enCok: 60,
              onChanged: yenile),
          FormAlani(
              key: const ValueKey('f_yas'),
              etiket: M.alanYas,
              ipucu: M.alanYasYer,
              denetleyici: _yas,
              klavye: TextInputType.number,
              enCok: 3,
              onChanged: yenile),
          _secimDugmesi(r, M.alanIl, _il, (_tam || _sehit) ? _ilSec : () {}),
          _secimDugmesi(r, M.alanIlce, _ilce ?? M.alanIlce, _ilceSec),
          FormAlani(etiket: M.alanMahalle, ipucu: M.alanMahalleYer, denetleyici: _mahalle, enCok: 60),
        ];
      case 2:
        return [
          _baslik(r, M.adimCenazeBaslik, M.adimCenazeAciklama),
          _secimDugmesi(r, M.alanVefat, tarih(_vefat), _tarihSec),
          _secimDugmesi(r, M.alanNamazTarihi, tarih(_namaz), _namazTarihSec),
          _secenekler(r, M.alanNamaz, M.namazSecenek.take(6).toList(), _vakit ?? '', (v) => setState(() => _vakit = v)),
          FormAlani(etiket: M.alanCami, ipucu: M.alanCamiYer, denetleyici: _cami, enCok: 40),
          if (_sehit)
            FormAlani(
                key: const ValueKey('f_toren'),
                etiket: M.sehitTorenYeri,
                ipucu: M.sehitTorenYer,
                denetleyici: _toren,
                enCok: 60),
          FormAlani(
              etiket: M.alanMezarlik,
              ipucu: _sehit ? M.sehitMezarlikYer : M.alanMezarlikYer,
              denetleyici: _mezarlik,
              enCok: 60),
        ];
      case 3:
        return [
          _baslik(r, M.adim3Baslik, M.adim3Aciklama),
          FormAlani(
              key: const ValueKey('f_basvuran'),
              etiket: M.adim3Ad,
              ipucu: M.adim3AdYer,
              denetleyici: _basvuranAd,
              enCok: 60,
              onChanged: yenile),
          FormAlani(
              key: const ValueKey('f_telefon'),
              etiket: M.adim3Eposta,
              ipucu: M.adim3EpostaYer,
              denetleyici: _tel,
              klavye: TextInputType.phone,
              enCok: 16,
              onChanged: yenile),
          Padding(
            padding: const EdgeInsets.only(bottom: R.s3),
            child: Text(M.adim3TelefonNot, key: const ValueKey('f_telefon_not'), textAlign: TextAlign.center, style: Y.soluk(r)),
          ),
          _secenekler(r, M.adim3Yakinlik, M.yakinlikSecenek, _yakinlik, (v) => setState(() => _yakinlik = v)),
        ];
      case 4:
        return [
          _baslik(r, _sehit ? M.sehitAdimDuyuru : M.adim2Baslik, _sehit ? M.sehitDuyuruAciklama : M.adim2Aciklama),
          FormAlani(
              key: const ValueKey('f_belge'),
              etiket: _sehit ? M.sehitDuyuruAlan : M.adim2Alan,
              ipucu: _sehit ? M.sehitDuyuruYer : M.adim2AlanYer,
              denetleyici: _belge,
              enCok: _sehit ? 60 : 30,
              onChanged: (_) => setState(() => _belgeTamam = false)),
          if (_belgeZorunlu) ...[
            IkincilDugme(_sehit ? M.sehitDuyuruDugme : M.belgeDugme, onTap: _belgeDogrula),
            if (_belgeTamam) ...[
              const SizedBox(height: R.s3),
              _durum(r, _sehit ? M.sehitDuyuruTamam : M.belgeTamam),
            ],
          ],
        ];
      default:
        return [
          _baslik(r, _ucretli ? M.adim5TamBaslik : M.adim5Baslik, M.adim5Aciklama),
          Container(
            padding: const EdgeInsets.all(R.s5),
            decoration: BoxDecoration(
              color: r.vurguZemin,
              borderRadius: BorderRadius.circular(R.kart),
              border: Border.all(color: r.vurgu, width: 2),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Row(children: [
                Ikon('uyari', boyut: 20, renk: r.vurguMetin),
                Expanded(
                  child: Text(M.hukukBaslik,
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 12, height: 16 / 12, fontWeight: FontWeight.w700, color: r.vurguMetin)),
                ),
                const SizedBox(width: 20),
              ]),
              const SizedBox(height: R.s3),
              Text(M.hukukMetin, textAlign: TextAlign.left, style: Y.govde(r).copyWith(fontSize: 14, height: 21 / 14)),
              const SizedBox(height: R.s4),
              InkWell(
                onTap: () => setState(() => _onay = !_onay),
                child: Row(children: [
                  SizedBox(
                    width: 28,
                    height: 28,
                    child: Checkbox(
                      key: const ValueKey('beyan_kutu'),
                      value: _onay,
                      activeColor: r.vurgu,
                      checkColor: r.vurguUst,
                      onChanged: (v) => setState(() => _onay = v ?? false),
                    ),
                  ),
                  Expanded(
                    child: Text(M.hukukKutu,
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: r.metin)),
                  ),
                  const SizedBox(width: 28),
                ]),
              ),
            ]),
          ),
        ];
    }
  }
}
