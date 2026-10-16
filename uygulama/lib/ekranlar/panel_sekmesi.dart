// Panel sekmesi (5. sekme, URUN-TASLAGI §53; ölçü: tasarim/sablon.html panelEkraniCiz).
// Parola yok -> "belirleyin"; bu açılışta girilmedi -> "parolanız"; girildi -> GorevliPanel (sekme içinde).
import 'dart:async';

import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/gorevli.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import 'gorevli_kayit.dart';
import 'gorevli_panel.dart';

class PanelSekmesi extends StatelessWidget {
  final GorevliServisi? servis;
  const PanelSekmesi({super.key, this.servis});

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    if (d.depo.gorevliOturum == null) return const _GorevliDegil();
    if (!d.depo.gorevliPinVar) return GorevliParolaBelirle(sekmede: true, servis: servis);
    if (!d.panelAcik) return _ParolaGir(servis: servis);
    return GorevliPanel(sekmede: true, servis: servis);
  }
}

/// Doğrulanmamış kullanıcı (ya da çıkıştan sonra): amblem + açıklama + "Kayıt olun" -> kayıt (kılavuz -> kod)
class _GorevliDegil extends StatelessWidget {
  const _GorevliDegil();

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    return Column(children: [
      BaslikCubugu(
        sol: const SizedBox(width: 40),
        sag: const SizedBox(width: 40),
        ust: M.gorevliUst,
        baslik: const BuyukBaslik(M.sekmePanel),
      ),
      Expanded(
        child: ListView(key: const ValueKey('panel_gorevli_degil'), padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s6), children: [
          const Center(child: Daire('kemer', boyut: 96)),
          const SizedBox(height: R.s5),
          Text(M.panelGorevliBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
          const SizedBox(height: R.s2),
          Text(M.panelGorevliAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          const SizedBox(height: R.s5),
          AnaDugme(M.panelKayitDugme,
              key: const ValueKey('panel_kayit'),
              onTap: () => Navigator.of(context, rootNavigator: true)
                  .push(MaterialPageRoute(builder: (_) => GorevliKayit(il: d.il ?? '', ilce: d.ilce)))),
        ]),
      ),
    ]);
  }
}

/// "Parolanız gönderildi" sayfası: açılınca /gorevli/parola-hatirlat çağrılır; "Tamam" parola giriş ekranına döner
class GorevliParolaGonderildi extends StatefulWidget {
  final GorevliServisi? servis;
  const GorevliParolaGonderildi({super.key, this.servis});
  @override
  State<GorevliParolaGonderildi> createState() => _GorevliParolaGonderildiState();
}

class _GorevliParolaGonderildiState extends State<GorevliParolaGonderildi> {
  bool _yukleniyor = true;
  bool _tamam = false;
  String _adres = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _gonder());
  }

  Future<void> _gonder() async {
    final d = Kapsam.oku(context);
    final tok = d.depo.gorevliOturum;
    _adres = '${d.depo.gorevliKullanici ?? ''}${M.gorevliAlanAdi}';
    var ok = false;
    if (tok != null) {
      final y = await (widget.servis ?? GorevliServisi(istemci: d.veri.istemci)).parolaHatirlat(tok);
      ok = y.tamam;
      final a = y.govde?['adres']?.toString();
      if (ok && a != null && a.isNotEmpty) _adres = a;
    }
    if (!mounted) return;
    setState(() {
      _yukleniyor = false;
      _tamam = ok;
    });
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: const SizedBox(width: 40),
            sag: const SizedBox(width: 40),
            ust: M.gorevliUst,
            baslik: const BuyukBaslik(M.pinGonderildiBaslik),
          ),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s6), children: [
              const Center(child: Daire('kemer', boyut: 96)),
              const SizedBox(height: R.s5),
              if (_yukleniyor)
                Text(M.gorevliYukleniyor, textAlign: TextAlign.center, style: Y.soluk(r))
              else if (_tamam) ...[
                Text(M.pinGonderildiBir, key: const ValueKey('pin_gonderildi'), textAlign: TextAlign.center, style: Y.adim(r)),
                const SizedBox(height: R.s2),
                Text(M.pinGonderildiIki(_adres), key: const ValueKey('pin_gonderildi_aciklama'), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
              ] else
                Text(M.pinGonderilemediSayfa, key: const ValueKey('pin_gonderilemedi'), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
              const SizedBox(height: R.s5),
              AnaDugme(M.pinTamam, key: const ValueKey('pin_tamam'), onTap: _yukleniyor ? null : () => Navigator.of(context).pop()),
            ]),
          ),
        ]),
      ),
    );
  }
}

/// Parolayı hesaba (Worker'da şifreli) yazar; ağ/sunucu yoksa false (cihaz parolası yine geçerli)
Future<bool> _sunucuyaYaz(AppDurum d, GorevliServisi? servis, String parola) async {
  final tok = d.depo.gorevliOturum;
  if (tok == null) return false;
  final y = await (servis ?? GorevliServisi(istemci: d.veri.istemci)).parolaKaydet(tok, parola);
  return y.tamam;
}

/// "Parolamı değiştir" (⋮ menüsü): eski parola -> yeni parola (iki kez); hem cihaza hem Worker'a yazılır
class GorevliParolaDegistir extends StatefulWidget {
  final GorevliServisi? servis;
  const GorevliParolaDegistir({super.key, this.servis});
  @override
  State<GorevliParolaDegistir> createState() => _GorevliParolaDegistirState();
}

class _GorevliParolaDegistirState extends State<GorevliParolaDegistir> {
  final _e = TextEditingController();
  final _a = TextEditingController();
  final _b = TextEditingController();
  String? _hata;

  @override
  void dispose() {
    _e.dispose();
    _a.dispose();
    _b.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    final d = Kapsam.oku(context);
    if (!d.depo.gorevliPinDogru(_e.text)) return setState(() => _hata = M.pinEskiYanlis);
    if (!RegExp(r'^\d{4}$').hasMatch(_a.text)) return setState(() => _hata = M.pinRakam);
    if (_a.text != _b.text) return setState(() => _hata = M.pinFarkli);
    await d.depo.gorevliPinKur(_a.text);
    final sunucu = await _sunucuyaYaz(d, widget.servis, _a.text);
    if (!mounted) return;
    bildir(context, sunucu ? M.pinDegisti : M.pinSunucuyaYok);
    Navigator.of(context).pop();
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
            ust: M.gorevliUst,
            baslik: const BuyukBaslik(M.pinDegistirBaslik),
          ),
          Expanded(
            child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6), children: [
              const SizedBox(height: R.s4),
              FormAlani(key: const ValueKey('pin_eski'), etiket: M.pinEski, ipucu: '••••', denetleyici: _e, klavye: TextInputType.number, enCok: 4, gizli: true),
              FormAlani(key: const ValueKey('pin_1'), etiket: M.pinYeni, ipucu: '••••', denetleyici: _a, klavye: TextInputType.number, enCok: 4, gizli: true),
              FormAlani(key: const ValueKey('pin_2'), etiket: M.pinAlan2, ipucu: '••••', denetleyici: _b, klavye: TextInputType.number, enCok: 4, gizli: true),
              if (_hata != null) Text(_hata!, key: const ValueKey('pin_hata'), textAlign: TextAlign.center, style: Y.kucuk(r)),
              const SizedBox(height: R.s3),
              AnaDugme(M.pinKaydet, key: const ValueKey('pin_kaydet'), onTap: _kaydet),
            ]),
          ),
        ]),
      ),
    );
  }
}

/// Parola belirleme: kod doğrulanınca (sekmede=false, tam ekran) ya da parolası olmayan oturumda (sekmede=true)
class GorevliParolaBelirle extends StatefulWidget {
  final bool sekmede;
  final GorevliServisi? servis;
  const GorevliParolaBelirle({super.key, this.sekmede = false, this.servis});
  @override
  State<GorevliParolaBelirle> createState() => _GorevliParolaBelirleState();
}

class _GorevliParolaBelirleState extends State<GorevliParolaBelirle> {
  final _a = TextEditingController();
  final _b = TextEditingController();
  String? _hata;

  @override
  void dispose() {
    _a.dispose();
    _b.dispose();
    super.dispose();
  }

  Future<void> _kaydet() async {
    final d = Kapsam.oku(context);
    if (!RegExp(r'^\d{4}$').hasMatch(_a.text)) return setState(() => _hata = M.pinRakam);
    if (_a.text != _b.text) return setState(() => _hata = M.pinFarkli);
    await d.depo.gorevliPinKur(_a.text);
    final sunucu = await _sunucuyaYaz(d, widget.servis, _a.text);
    if (!mounted) return;
    bildir(context, sunucu ? M.pinKaydedildi : M.pinSunucuyaYok);
    if (!widget.sekmede) Navigator.of(context, rootNavigator: true).popUntil((r) => r.isFirst);
    d.gorevliGirisTamam(); // Panel sekmesi seçilir, panel açık sayılır (KVKK penceresi panel ilk açılışında)
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final icerik = Column(children: [
      BaslikCubugu(
        sol: widget.sekmede
            ? const SizedBox(width: 40)
            : YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
        sag: const SizedBox(width: 40),
        ust: M.gorevliUst,
        baslik: const BuyukBaslik(M.sekmePanel),
      ),
      Expanded(
        child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6), children: [
          const SizedBox(height: R.s4),
          Text(M.pinBelirleBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
          const SizedBox(height: R.s2),
          Text(M.pinBelirleAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          const SizedBox(height: R.s4),
          FormAlani(key: const ValueKey('pin_1'), etiket: M.pinAlan1, ipucu: '••••', denetleyici: _a, klavye: TextInputType.number, enCok: 4, gizli: true),
          FormAlani(key: const ValueKey('pin_2'), etiket: M.pinAlan2, ipucu: '••••', denetleyici: _b, klavye: TextInputType.number, enCok: 4, gizli: true),
          if (_hata != null) Text(_hata!, key: const ValueKey('pin_hata'), textAlign: TextAlign.center, style: Y.kucuk(r)),
          const SizedBox(height: R.s3),
          AnaDugme(M.pinKaydet, key: const ValueKey('pin_kaydet'), onTap: _kaydet),
        ]),
      ),
    ]);
    return widget.sekmede ? icerik : Scaffold(body: SafeArea(child: icerik));
  }
}

class _ParolaGir extends StatefulWidget {
  final GorevliServisi? servis;
  const _ParolaGir({this.servis});
  @override
  State<_ParolaGir> createState() => _ParolaGirState();
}

class _ParolaGirState extends State<_ParolaGir> {
  final _p = TextEditingController();
  String? _hata;
  int _kilit = 0;
  Timer? _sayac;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _kilitGuncelle());
  }

  @override
  void dispose() {
    _sayac?.cancel();
    _p.dispose();
    super.dispose();
  }

  void _kilitGuncelle() {
    if (!mounted) return;
    final depo = Kapsam.oku(context).depo;
    final k = depo.gorevliPinKilitKalanSn();
    _sayac?.cancel();
    if (k > 0) {
      _sayac = Timer.periodic(const Duration(seconds: 1), (_) {
        if (!mounted) return;
        final yeni = depo.gorevliPinKilitKalanSn();
        setState(() {
          _kilit = yeni;
          if (yeni == 0) _hata = null;
        });
        if (yeni == 0) {
          _sayac?.cancel();
          depo.gorevliPinSayacSifirla();
        }
      });
    }
    setState(() {
      _kilit = k;
      if (k > 0) _hata = M.pinBekle(k);
    });
  }

  Future<void> _gir() async {
    final d = Kapsam.oku(context);
    if (d.depo.gorevliPinKilitKalanSn() > 0) return _kilitGuncelle();
    if (d.depo.gorevliPinDogru(_p.text)) {
      await d.depo.gorevliPinSayacSifirla();
      _p.clear();
      d.panelAcik = true;
      d.oturumDegisti();
      return;
    }
    final kalan = await d.depo.gorevliPinYanlisKaydet();
    if (!mounted) return;
    _p.clear();
    if (kalan == 0) return _kilitGuncelle();
    setState(() => _hata = M.pinYanlisKalan(kalan));
  }

  /// "Parolamı unuttum": çıkış YOK, parola silinmez; AYRI sayfa açılır, parola hesabın Diyanet adresine e-postalanır (URUN §53)
  void _unuttum() {
    Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(builder: (_) => GorevliParolaGonderildi(servis: widget.servis)));
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Column(children: [
      BaslikCubugu(
        sol: const SizedBox(width: 40),
        sag: const SizedBox(width: 40),
        ust: M.gorevliUst,
        baslik: const BuyukBaslik(M.sekmePanel),
      ),
      Expanded(
        child: ListView(padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6), children: [
          const SizedBox(height: R.s4),
          Text(M.pinGirBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
          const SizedBox(height: R.s2),
          Text(M.pinGirAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          const SizedBox(height: R.s4),
          FormAlani(key: const ValueKey('pin_gir'), etiket: M.pinGirAlan, ipucu: '••••', denetleyici: _p, klavye: TextInputType.number, enCok: 4, gizli: true),
          if (_hata != null) Text(_hata!, key: const ValueKey('pin_hata'), textAlign: TextAlign.center, style: Y.kucuk(r)),
          const SizedBox(height: R.s3),
          AnaDugme(M.pinGir, key: const ValueKey('pin_ac'), onTap: _kilit > 0 ? null : _gir),
          const SizedBox(height: R.s2),
          IkincilDugme(M.pinUnuttum, key: const ValueKey('pin_unuttum'), onTap: _unuttum),
        ]),
      ),
    ]);
  }
}
