// Din görevlisi kaydı (0.1.9, URUN-TASLAGI §45; ölçü: tasarim/sablon.html gorevliAc/gkayitCiz).
// 1) KILAVUZ: kullanıcı adı (+ sabit @diyanet.gov.tr) + "Kodu gönder" + "nasıl giriş yapabilirim?" penceresi (6 madde)
// 2) KOD: "Kod gönderildi: x@diyanet.gov.tr", 5 maddelik tarif, 6 haneli kod, "Doğrula ve paneli aç", "Kodu yeniden gönder (5 dk)"
// 3) kod doğruysa panel HEMEN açılır (oturum depoya yazılır; bekleme/kontrol yok). Kart fotoğrafı ve telefon kodu adımları kaldırıldı.
import 'dart:async';

import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/gorevli.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import 'panel_sekmesi.dart';

/// Din görevlisi girişi: oturum varsa Panel sekmesi, yoksa kayıt ekranı (ilan kutusu bağlantısı kullanır)
Future<void> gorevliKapisi(BuildContext context, {required String il, String? ilce}) {
  final d = Kapsam.oku(context);
  if (d.depo.gorevliOturum != null) {
    d.panelSekmesiAc(); // oturum varsa Panel sekmesi (parola sorulur); URUN §53
    return Future.value();
  }
  return Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(builder: (_) => GorevliKayit(il: il, ilce: ilce)));
}

enum _Faz { kilavuz, kod }

/// Yeniden gönder bekleme (sn): 5 dakika (sahibi 16.10.2026)
const int kodBeklemeSn = 300;

class GorevliKayit extends StatefulWidget {
  final String il;
  final String? ilce;
  final GorevliServisi? servis;
  const GorevliKayit({super.key, required this.il, this.ilce, this.servis});
  @override
  State<GorevliKayit> createState() => _GorevliKayitState();
}

class _GorevliKayitState extends State<GorevliKayit> {
  _Faz _faz = _Faz.kilavuz;
  bool _yukleniyor = false;
  String? _hata;
  String _kullanici = ''; // gönderilen kullanıcı adı (küçük harf, @ yok)
  int _kalan = 0;
  Timer? _sayac;
  final _kul = TextEditingController();
  final _kod = TextEditingController();

  @override
  void dispose() {
    _sayac?.cancel();
    _kul.dispose();
    _kod.dispose();
    super.dispose();
  }

  GorevliServisi _servis() => widget.servis ?? GorevliServisi(istemci: Kapsam.oku(context).veri.istemci);

  /// "Ali.Kaya" ya da "ali.kaya@diyanet.gov.tr" -> "ali.kaya"; geçersizse null (sunucu aynı kuralı uygular)
  static String? kullaniciNormal(String t) {
    var u = t.trim().toLowerCase();
    final at = u.indexOf('@');
    if (at >= 0) {
      if (u.substring(at + 1) != 'diyanet.gov.tr') return null;
      u = u.substring(0, at);
    }
    return RegExp(r'^[a-z0-9._-]{3,40}$').hasMatch(u) ? u : null;
  }

  String get _adres => '$_kullanici${M.gorevliAlanAdi}';

  void _yenile([String? _]) => setState(() {});

  void _sayacBaslat([int sn = kodBeklemeSn]) {
    _sayac?.cancel();
    _kalan = sn;
    _sayac = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) {
        t.cancel();
        return;
      }
      setState(() => _kalan = _kalan > 0 ? _kalan - 1 : 0);
      if (_kalan <= 0) t.cancel();
    });
  }

  /// Kod iste (ilk gönderim ve yeniden gönder). ilk=true: kılavuz ekranından kod ekranına geçer.
  Future<void> _kodGonder({required bool ilk}) async {
    if (_yukleniyor) return;
    final ku = ilk ? kullaniciNormal(_kul.text) : _kullanici;
    if (ku == null) {
      setState(() => _hata = M.gorevliKullaniciHata);
      return;
    }
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final y = await _servis().epostaKodGonder(ku);
    if (!mounted) return;
    final bekle = int.tryParse('${y.govde?['bekle_sn'] ?? ''}');
    setState(() => _yukleniyor = false);
    if (y.tamam) {
      setState(() {
        _kullanici = ku;
        _kod.clear();
        _faz = _Faz.kod;
      });
      _sayacBaslat();
      if (!ilk) bildir(context, M.kodGitti);
    } else if (y.kod == 429 && y.govde?['hata'] == 'cok_sik_tekrar' && bekle != null) {
      // 5 dk dolmadan yeni kod verilmez; önceki kod hâlâ geçerli -> kod ekranına geç, kalan süreyle geri say
      setState(() {
        _kullanici = ku;
        _faz = _Faz.kod;
      });
      _sayacBaslat(bekle);
    } else if (y.kod == 429) {
      setState(() => _hata = M.gorevliGunlukSinir);
    } else if (y.kod == 400) {
      setState(() => _hata = M.gorevliKullaniciHata);
    } else if (y.kod == 403) {
      setState(() => _hata = M.gorevliDondurulmus);
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

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
    final y = await _servis().epostaDogrula(_kullanici, kod);
    if (!mounted) return;
    final tok = y.govde?['oturum']?.toString();
    if (y.tamam && tok != null && tok.isNotEmpty) {
      final depo = Kapsam.oku(context).depo;
      await depo.gorevliOturumKaydet(tok);
      await depo.gorevliKullaniciKaydet(_kullanici);
      await depo.gorevliDurumKaydet('onayli');
      await depo.gorevliSorumlulukSil();
      await depo.gorevliKvkkSil(); // her girişte KVKK penceresi yeniden (URUN §50a)
      if (!mounted) return;
      _sayac?.cancel();
      // 5. sekme belirir; ÖNCE parola belirlenir (URUN §53), sonra Panel sekmesi + KVKK penceresi
      Kapsam.oku(context).oturumDegisti();
      Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => GorevliParolaBelirle(servis: widget.servis)));
      return;
    }
    setState(() => _yukleniyor = false);
    if (y.kod == 429) {
      setState(() => _hata = M.gorevliKodGecersiz);
    } else if (y.kod == 403) {
      setState(() => _hata = M.gorevliDondurulmus);
    } else if (y.agHatasi || y.kod >= 500) {
      setState(() => _hata = M.aileAgHata);
    } else {
      setState(() => _hata = M.gorevliKodYanlis); // 400 yanlış / 410 süresi doldu
    }
  }

  void _geri() {
    if (_faz == _Faz.kod) {
      _sayac?.cancel();
      setState(() {
        _faz = _Faz.kilavuz;
        _hata = null;
      });
    } else {
      Navigator.of(context).pop();
    }
  }

  void _nasilPenceresi() {
    showDialog<void>(
      context: context,
      builder: (c) {
        final r = c.renk;
        return Dialog(
          key: const ValueKey('g_nasil_pencere'),
          backgroundColor: r.yuzey,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
          child: Padding(
            padding: const EdgeInsets.all(R.s5),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(M.gorevliNasilBaslik, style: Y.adim(r)),
              const SizedBox(height: R.s3),
              for (int i = 0; i < M.gorevliNasil6.length; i++)
                Padding(padding: const EdgeInsets.only(bottom: R.s2), child: Text('${i + 1}. ${M.gorevliNasil6[i]}', style: Y.govde(r).copyWith(fontSize: 14))),
              const SizedBox(height: R.s3),
              IkincilDugme(M.gorevliTamam, onTap: () => Navigator.of(c).pop()),
            ]),
          ),
        );
      },
    );
  }

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

  // ---- Görünüm ----
  List<Widget> _kilavuzGorunumu(CvRenk r) => [
        _baslik(r, M.gorevliEpostaBaslik, M.gorevliEpostaAciklama),
        Text(M.gorevliKullanici, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
        const SizedBox(height: 6),
        Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
          Expanded(
              child: FormAlani(
                  key: const ValueKey('g_kullanici'), etiket: '', ipucu: M.gorevliKullaniciYer, denetleyici: _kul, klavye: TextInputType.emailAddress, enCok: 40, onChanged: _yenile)),
          const SizedBox(width: R.s2),
          Text(M.gorevliAlanAdi, key: const ValueKey('g_alan_adi'), style: Y.satir(r)), // sabit; değiştirilemez
        ]),
        const SizedBox(height: R.s3),
        IkincilDugme(M.gorevliNasilGiris, onTap: _nasilPenceresi),
      ];

  List<Widget> _kodGorunumu(CvRenk r) {
    final tarif = M.gorevliTarif5(_adres);
    return [
      _baslik(r, M.kodBaslik),
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(R.s4),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: Text(M.gorevliKodGitti(_adres), key: const ValueKey('g_kod_gitti'), textAlign: TextAlign.center, style: Y.satir(r)),
      ),
      const SizedBox(height: R.s3),
      for (int i = 0; i < tarif.length; i++)
        Padding(padding: const EdgeInsets.only(bottom: R.s2), child: Text('${i + 1}. ${tarif[i]}', key: ValueKey('g_tarif_$i'), style: Y.govde(r).copyWith(fontSize: 14))),
      const SizedBox(height: R.s3),
      FormAlani(key: const ValueKey('g_kod'), etiket: M.kodAlan, ipucu: M.kodYer, denetleyici: _kod, klavye: TextInputType.number, enCok: 6),
      const SizedBox(height: R.s2),
      IkincilDugme(_kalan > 0 ? M.kodBekle(_kalan) : M.kodYeniden, onTap: (_kalan > 0 || _yukleniyor) ? null : () => _kodGonder(ilk: false)),
      const SizedBox(height: R.s2),
      Text(M.gorevliKodGecerli, key: const ValueKey('g_kod_gecerli'), textAlign: TextAlign.center, style: Y.soluk(r)),
      if (_hata != null) ...[
        const SizedBox(height: R.s3),
        Text(_hata!, key: const ValueKey('g_kod_hata'), textAlign: TextAlign.center, style: Y.kucuk(r)),
      ],
    ];
  }

  Widget _alt(CvRenk r) {
    final kilavuz = _faz == _Faz.kilavuz;
    final yazi = kilavuz ? M.gorevliKodGonderDugme : M.gorevliKodDogrulaDugme;
    final VoidCallback? onTap = kilavuz
        ? ((kullaniciNormal(_kul.text) != null && !_yukleniyor) ? () => _kodGonder(ilk: true) : null)
        : (_yukleniyor ? null : _kodDogrula);
    return Container(
      padding: const EdgeInsets.fromLTRB(R.s5, R.s3, R.s5, R.s5),
      decoration: BoxDecoration(color: r.zemin, border: Border(top: BorderSide(color: r.cizgi))),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        if (_hata != null && kilavuz)
          Padding(padding: const EdgeInsets.only(bottom: R.s3), child: Text(_hata!, key: const ValueKey('g_hata'), textAlign: TextAlign.center, style: Y.kucuk(r))),
        AnaDugme(yazi, onTap: onTap),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return PopScope(
      canPop: _faz == _Faz.kilavuz,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _geri();
      },
      child: Scaffold(
        body: SafeArea(
          child: Column(children: [
            BaslikCubugu(
              sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: _geri),
              sag: YuvarlakDugme(ikon: 'kapat', anlam: 'Kapat', onTap: () => Navigator.of(context).pop()),
              ust: _faz == _Faz.kod ? M.kodUst : M.gorevliUst,
              baslik: const BuyukBaslik(M.gorevliBaslik),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
                children: _faz == _Faz.kilavuz ? _kilavuzGorunumu(r) : _kodGorunumu(r),
              ),
            ),
            _alt(r),
          ]),
        ),
      ),
    );
  }
}
