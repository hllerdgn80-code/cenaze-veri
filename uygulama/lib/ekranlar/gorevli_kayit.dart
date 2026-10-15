// Din görevlisi kaydı (0.1.5, URUN-TASLAGI §37; ölçü: tasarim/prototip.html p-gorevli).
// Adım 1 bilgiler (ad-soyad, il/ilçe, görev yeri, unvan, telefon) + zorunlu BEYAN kutusu -> "Başvuruyu gönder" -> Adım 2 Diyanet personel kartı
// (YALNIZ uygulama içi kamera; fotoğraf cihazda ≤1600 px'e küçültülür, diske yazılmaz, yalnız gövdede gider)
// -> telefona gönderilen 6 haneli kod (WhatsApp/SMS; 60 sn sonra yeniden gönder) -> sonuç: onaylandı (panel) / kontrol ediliyor.
// "Hesabım var" ile telefon girişi de buradadır.
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/gorevli.dart';
import '../cekirdek/kart_kamera.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';
import 'gorevli_panel.dart';

/// Uygulama içi kameradan, TC karartılmış 1600 px JPEG (GALERİ YOK). Testlerde sahte verilir. Hata: [KartIslenemedi].
typedef FotoAl = Future<Uint8List?> Function();

/// Din görevlisi girişi: oturum varsa panel, yoksa kayıt ekranı (Tam Sayfa düğmesi ve ilan kutusu bağlantısı kullanır)
Future<void> gorevliKapisi(BuildContext context, {required String il, String? ilce}) {
  final d = Kapsam.oku(context);
  final nav = Navigator.of(context, rootNavigator: true);
  return nav.push(MaterialPageRoute(
      builder: (_) => d.depo.gorevliOturum != null ? const GorevliPanel() : GorevliKayit(il: il, ilce: ilce)));
}

enum _Faz { bilgi, foto, giris, kod, sonuc }

class GorevliKayit extends StatefulWidget {
  final String il;
  final String? ilce;
  final GorevliServisi? servis;
  final FotoAl? fotoAl;
  const GorevliKayit({super.key, required this.il, this.ilce, this.servis, this.fotoAl});
  @override
  State<GorevliKayit> createState() => _GorevliKayitState();
}

class _GorevliKayitState extends State<GorevliKayit> {
  _Faz _faz = _Faz.bilgi;
  late String _il;
  String? _ilce;
  String _unvan = M.gorevliUnvanlar.first[1];
  bool _yukleniyor = false;
  String? _hata;
  String? _bilgi; // foto ekranının üstündeki ek not
  String? _kayitId;
  bool _listeEslesti = false;
  bool _beyan = false; // zorunlu onay kutusu
  int _kalan = 0; // koddan sonra "yeniden gönder" bekleme (sn)
  Timer? _sayac;
  bool _girisKodu = false; // kod ekranına "Hesabım var" yolundan mı gelindi
  String? _sonDurum; // onayli | kontrolde | kuyruk | kontrol_bekliyor
  String? _oturum;
  final _ad = TextEditingController();
  final _yer = TextEditingController();
  final _tel = TextEditingController();
  final _kod = TextEditingController();

  @override
  void initState() {
    super.initState();
    _il = widget.il;
    _ilce = widget.ilce;
  }

  @override
  void dispose() {
    _sayac?.cancel();
    for (final c in [_ad, _yer, _tel, _kod]) {
      c.dispose();
    }
    super.dispose();
  }

  GorevliServisi _servis() => widget.servis ?? GorevliServisi(istemci: Kapsam.oku(context).veri.istemci);

  static bool _adGecerli(String s) {
    final n = s.trim().split(RegExp(r'\s+')).where((x) => x.isNotEmpty).length;
    return n >= 2 && n <= 5;
  }

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

  bool get _bilgiHazir =>
      _beyan &&
      _adGecerli(_ad.text) && _ilce != null && _yer.text.trim().length >= 2 && _telNormal(_tel.text) != null;

  void _yenile([String? _]) => setState(() {});

  Future<String?> _listeSec(List<String> liste) => showDialog<String>(
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

  Future<void> _ilSec() async {
    final s = await _listeSec(Kapsam.oku(context).gomulu.iller);
    if (s != null && mounted && s != _il) setState(() {
      _il = s;
      _ilce = null;
    });
  }

  Future<void> _ilceSec() async {
    final s = await _listeSec(Kapsam.oku(context).ilceListesi(_il));
    if (s != null && mounted) setState(() => _ilce = s);
  }

  String? _bos(String s) {
    final t = s.trim().replaceAll(RegExp(r'\s+'), ' ');
    return t.isEmpty ? null : t;
  }

  // ---- Adım 1: bilgiler ----
  Future<void> _bilgiGonder() async {
    if (_yukleniyor || !_bilgiHazir) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().kayit({
      'ad_soyad': _bos(_ad.text),
      'il': _il,
      'ilce': _ilce,
      'gorev_yeri': _bos(_yer.text),
      'unvan': _unvan,
      'telefon': _telNormal(_tel.text),
      'beyan': true,
    });
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    if (y.tamam && y.durum == 'foto_gerek') {
      setState(() {
        _kayitId = y.govde?['kayit_id']?.toString();
        _listeEslesti = y.govde?['liste_eslesti'] == true;
        _bilgi = null; // müftülük listesi onay şartı değil (yalnız sunucuda puan); kullanıcıya gösterilmez
        _faz = _Faz.foto;
      });
    } else if (y.kod == 409) {
      setState(() => _hata = M.gorevliCiftKayitNot);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  // ---- Adım 2: kart fotoğrafı ----
  Future<void> _fotoCek() async {
    if (_yukleniyor || _kayitId == null) return;
    Uint8List? b;
    try {
      b = await (widget.fotoAl ?? kartCek)();
    } on KartIslenemedi {
      if (mounted) setState(() => _hata = M.gorevliKartIslenemedi); // karartılamayan görüntü GÖNDERİLMEZ
      return;
    } catch (_) {
      b = null;
    }
    if (b == null || !mounted) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().foto(_kayitId!, base64Encode(b));
    if (!mounted) return;
    final durum = y.durum;
    if (durum == 'deneme2') {
      setState(() {
        _yukleniyor = false;
        _bilgi = M.gorevliDeneme2; // kod yok: aynı ekranda yeniden çekilir
      });
    } else if (durum == 'kontrol_bekliyor') {
      setState(() {
        _yukleniyor = false;
        _sonDurum = 'kontrol_bekliyor';
        _faz = _Faz.sonuc;
      });
    } else if (y.tamam && (durum == 'onayli' || durum == 'kontrolde' || durum == 'kuyruk')) {
      setState(() {
        _yukleniyor = false;
        _sonDurum = durum;
        _girisKodu = false;
        _kod.clear();
        _faz = _Faz.kod;
      });
      _sayacBaslat();
    } else {
      setState(() {
        _yukleniyor = false;
        _hata = M.aileAgHata;
      });
    }
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

  Future<void> _yenidenGonder() async {
    if (_yukleniyor || _kalan > 0 || _kayitId == null) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().kodYenidenGonder(_kayitId!);
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    if (y.tamam) {
      _sayacBaslat();
      bildir(context, M.kodGitti);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  // ---- Telefon girişi ("Hesabım var") ----
  Future<void> _girisKodGonder() async {
    if (_yukleniyor || _telNormal(_tel.text) == null) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().giris(_telNormal(_tel.text) ?? '');
    if (!mounted) return;
    final id = y.govde?['kayit_id']?.toString();
    setState(() {
      _yukleniyor = false;
      if (y.tamam && id != null) {
        _kayitId = id;
        _girisKodu = true;
        _kod.clear();
        _faz = _Faz.kod;
        _sayacBaslat();
      } else {
        _hata = M.aileAgHata;
      }
    });
  }

  // ---- E-posta kodu ----
  Future<void> _kodDogrula() async {
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
    final y = await _servis().dogrula(_kayitId ?? '', kod);
    if (!mounted) return;
    final tok = y.govde?['oturum']?.toString();
    if (y.tamam && tok != null && tok.isNotEmpty) {
      final depo = Kapsam.oku(context).depo;
      await depo.gorevliOturumKaydet(tok);
      await depo.gorevliDurumKaydet(y.durum == 'onayli' ? 'onayli' : 'kontrolde');
      if (!mounted) return;
      setState(() {
        _yukleniyor = false;
        _oturum = tok;
        _sonDurum = y.durum;
        _faz = _Faz.sonuc;
      });
    } else if (y.kod == 400 && y.govde?['hata'] == 'kod_yanlis') {
      setState(() => _yukleniyor = false);
      bildir(context, M.kodHatali);
    } else if (y.agHatasi || y.kod >= 500) {
      setState(() {
        _yukleniyor = false;
        _hata = M.aileAgHata;
      });
    } else {
      setState(() => _yukleniyor = false);
      bildir(context, M.kodHatali);
    }
  }

  void _geri() {
    if (_faz == _Faz.foto || _faz == _Faz.giris) {
      setState(() {
        _faz = _Faz.bilgi;
        _hata = null;
      });
    } else if (_faz == _Faz.kod && _girisKodu) {
      setState(() {
        _faz = _Faz.giris;
        _hata = null;
      });
    } else {
      Navigator.of(context).pop();
    }
  }

  // ---- Görünüm ----
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

  Widget _unvanSecenekleri(CvRenk r) {
    final u = M.gorevliUnvanlar;
    final satirlar = <Widget>[];
    for (int i = 0; i < u.length; i += 2) {
      if (i > 0) satirlar.add(const SizedBox(height: R.s2));
      satirlar.add(IkiliSatir(
        sol: IkincilDugme(u[i][0], yukseklik: 44, secili: _unvan == u[i][1], onTap: () => setState(() => _unvan = u[i][1])),
        sag: i + 1 < u.length
            ? IkincilDugme(u[i + 1][0], yukseklik: 44, secili: _unvan == u[i + 1][1], onTap: () => setState(() => _unvan = u[i + 1][1]))
            : const SizedBox(height: 44),
      ));
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: R.s3),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(M.gorevliUnvan, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
        const SizedBox(height: 6),
        ...satirlar,
      ]),
    );
  }

  /// Kart fotoğrafı açıklama kutusu: ekranın EN ÜSTÜNDE, kamera düğmesinden önce
  Widget _aciklamaKutusu(CvRenk r) => Container(
        key: const ValueKey('g_foto_aciklama'),
        width: double.infinity,
        padding: const EdgeInsets.all(R.s4),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: Text(M.gorevliFotoAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
      );

  List<Widget> _bilgiGorunumu(CvRenk r) => [
        _baslik(r, M.gorevliBaslik, M.gorevliGirisNot),
        FormAlani(
            key: const ValueKey('g_ad'), etiket: M.gorevliAd, ipucu: M.gorevliAdYer, denetleyici: _ad, enCok: 60, onChanged: _yenile),
        _secimDugmesi(r, M.alanIl, _il, _ilSec),
        _secimDugmesi(r, M.alanIlce, _ilce ?? M.alanIlce, _ilceSec),
        FormAlani(
            key: const ValueKey('g_yer'), etiket: M.gorevliYer, ipucu: M.gorevliYerYer, denetleyici: _yer, enCok: 60, onChanged: _yenile),
        _unvanSecenekleri(r),
        FormAlani(
            key: const ValueKey('g_telefon'),
            etiket: M.gorevliTelefon,
            ipucu: M.gorevliTelefonYer,
            denetleyici: _tel,
            klavye: TextInputType.phone,
            enCok: 16,
            onChanged: _yenile),
        Text(M.gorevliTelefonNot, key: const ValueKey('g_telefon_not'), textAlign: TextAlign.center, style: Y.soluk(r)),
        const SizedBox(height: R.s2),
        IkincilDugme(M.gorevliGirisYap, onTap: () => setState(() => _faz = _Faz.giris)),
        const SizedBox(height: R.s4),
        // BEYAN: formun EN ALTINDA zorunlu onay kutusu; işaretlenmeden "Başvuruyu gönder" pasif
        InkWell(
          key: const ValueKey('g_beyan'),
          onTap: () => setState(() => _beyan = !_beyan),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Checkbox(value: _beyan, onChanged: (v) => setState(() => _beyan = v ?? false)),
            Expanded(child: Padding(padding: const EdgeInsets.only(top: 12), child: Text(M.gorevliBeyan, style: Y.govde(r).copyWith(fontSize: 13)))),
          ]),
        ),
      ];

  List<Widget> _fotoGorunumu(CvRenk r) => [
        // sahibinin metni EN ÜSTTE, kamera düğmesinden önce
        const SizedBox(height: R.s4),
        _aciklamaKutusu(r),
        const SizedBox(height: R.s3),
        Text(M.gorevliFotoYonerge, key: const ValueKey('g_foto_yonerge'), textAlign: TextAlign.center, style: Y.adim(r)),
        if (_bilgi != null) ...[
          const SizedBox(height: R.s3),
          Text(_bilgi!, key: const ValueKey('g_bilgi'), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
        ],
        const SizedBox(height: R.s5),
        AnaDugme(M.gorevliKamera, onTap: _yukleniyor ? null : _fotoCek), // yalnız kamera; galeri seçeneği yok
        if (_yukleniyor) ...[
          const SizedBox(height: R.s4),
          Text(M.gorevliYukleniyor, textAlign: TextAlign.center, style: Y.soluk(r)),
        ],
      ];

  List<Widget> _girisGorunumu(CvRenk r) => [
        _baslik(r, M.gorevliGirisBaslik, M.gorevliGirisAciklama),
        FormAlani(
            key: const ValueKey('g_giris_telefon'),
            etiket: M.gorevliTelefon,
            ipucu: M.gorevliTelefonYer,
            denetleyici: _tel,
            klavye: TextInputType.phone,
            enCok: 16,
            onChanged: _yenile),
      ];

  List<Widget> _kodGorunumu(CvRenk r) => [
        _baslik(r, M.kodBaslik, M.gorevliKodAciklama),
        if (!_girisKodu && (_sonDurum == 'kontrolde' || _sonDurum == 'kuyruk'))
          Padding(
            padding: const EdgeInsets.only(bottom: R.s3),
            child: Text(_sonDurum == 'kuyruk' ? M.gorevliKuyrukUyari : M.gorevliFotoSaklama,
                key: const ValueKey('g_saklama'), textAlign: TextAlign.center, style: Y.soluk(r)),
          ),
        FormAlani(key: const ValueKey('g_kod'), etiket: M.kodAlan, ipucu: M.kodYer, denetleyici: _kod, klavye: TextInputType.number, enCok: 6),
        const SizedBox(height: R.s2),
        IkincilDugme(_kalan > 0 ? M.kodBekle(_kalan) : M.kodYeniden, onTap: (_kalan > 0 || _yukleniyor) ? null : _yenidenGonder),
      ];

  List<Widget> _sonucGorunumu(CvRenk r) {
    final onayli = _sonDurum == 'onayli';
    final cift = _sonDurum == 'kontrol_bekliyor';
    final baslik = onayli ? M.gorevliOnaylandi : (cift ? M.gorevliCiftKayit : M.gorevliKontrolMetin);
    return [
      const SizedBox(height: R.s6),
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(R.s5),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: Column(children: [
          Text(baslik, key: const ValueKey('g_sonuc'), textAlign: TextAlign.center, style: Y.adim(r)),
          if (cift) ...[
            const SizedBox(height: R.s2),
            Text(M.gorevliCiftKayitNot, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          ],
          if (!onayli && !cift && (_sonDurum == 'kontrolde' || _sonDurum == 'kuyruk')) ...[
            const SizedBox(height: R.s2),
            Text(_sonDurum == 'kuyruk' ? M.gorevliKuyrukUyari : M.gorevliFotoSaklama,
                textAlign: TextAlign.center, style: Y.soluk(r)),
          ],
        ]),
      ),
    ];
  }

  Widget _alt(CvRenk r) {
    String yazi;
    VoidCallback? onTap;
    switch (_faz) {
      case _Faz.bilgi:
        yazi = _hata != null ? M.hataTekrar : M.gorevliBasvuruGonder;
        onTap = (_bilgiHazir && !_yukleniyor) ? _bilgiGonder : null;
      case _Faz.giris:
        yazi = M.gorevliKodGonder;
        onTap = (_telNormal(_tel.text) != null && !_yukleniyor) ? _girisKodGonder : null;
      case _Faz.kod:
        yazi = _hata != null ? M.hataTekrar : M.kodDugme;
        onTap = _yukleniyor ? null : _kodDogrula;
      case _Faz.sonuc:
        if (_sonDurum == 'onayli' && _oturum != null) {
          yazi = M.gorevliPaneleGit;
          onTap = () => Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => GorevliPanel(servis: widget.servis)));
        } else {
          yazi = M.aileBittiDugme;
          onTap = () => Navigator.of(context).pop();
        }
      case _Faz.foto:
        return const SizedBox.shrink(); // düğmeler içerikte (kamera / galeri)
    }
    return Container(
      padding: const EdgeInsets.fromLTRB(R.s5, R.s3, R.s5, R.s5),
      decoration: BoxDecoration(color: r.zemin, border: Border(top: BorderSide(color: r.cizgi))),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        if (_hata != null) Padding(padding: const EdgeInsets.only(bottom: R.s3), child: Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r))),
        AnaDugme(yazi, onTap: onTap),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final ust = _faz == _Faz.foto ? M.gorevliFotoUst : (_faz == _Faz.kod ? M.kodUst : (_faz == _Faz.sonuc ? M.gorevliBittiUst : M.gorevliUst));
    return PopScope(
      canPop: _faz == _Faz.bilgi || _faz == _Faz.sonuc,
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
              baslik: const BuyukBaslik(M.gorevliBaslik),
            ),
            if (_hata != null && _faz == _Faz.foto)
              Padding(padding: const EdgeInsets.all(R.s3), child: Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r))),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
                children: switch (_faz) {
                  _Faz.bilgi => _bilgiGorunumu(r),
                  _Faz.foto => _fotoGorunumu(r),
                  _Faz.giris => _girisGorunumu(r),
                  _Faz.kod => _kodGorunumu(r),
                  _Faz.sonuc => _sonucGorunumu(r),
                },
              ),
            ),
            _alt(r),
          ]),
        ),
      ),
    );
  }
}
