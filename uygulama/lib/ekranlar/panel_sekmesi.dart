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
    if (d.depo.gorevliOturum == null) return const SizedBox.shrink();
    if (!d.depo.gorevliPinVar) return const GorevliParolaBelirle(sekmede: true);
    if (!d.panelAcik) return const _ParolaGir();
    return GorevliPanel(sekmede: true, servis: servis);
  }
}

/// Parola belirleme: kod doğrulanınca (sekmede=false, tam ekran) ya da parolası olmayan oturumda (sekmede=true)
class GorevliParolaBelirle extends StatefulWidget {
  final bool sekmede;
  const GorevliParolaBelirle({super.key, this.sekmede = false});
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
    if (!mounted) return;
    bildir(context, M.pinKaydedildi);
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
  const _ParolaGir();
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

  /// "Parolamı unuttum": çıkış (oturum, parola, görev bilgisi silinir) + e-posta koduyla yeniden giriş
  Future<void> _unuttum() async {
    final d = Kapsam.oku(context);
    final nav = Navigator.of(context, rootNavigator: true);
    await d.gorevliCikis();
    nav.push(MaterialPageRoute(builder: (_) => GorevliKayit(il: d.il ?? '', ilce: d.ilce)));
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
