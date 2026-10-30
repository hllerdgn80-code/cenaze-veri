// Din görevlisi görev bilgileri sayfası (URUN §45): (1) İLK KEZ: panelde "İlan paylaş" basılınca ad-soyad, il/ilçe, görev yeri, unvan
// -> POST /gorevli/profil; (2) ⋮ menüsünden "Görev yerim değişti" AYRI SAYFASI (alanlar: görev yeri, il, ilçe, unvan; altta Kaydet): il/ilçe, görev yeri, unvan -> POST /gorevli/gorev-yeri (ad değişmez; eski ilanlar değişmez).
import 'package:flutter/material.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/gorevli.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';

class GorevliYerFormu extends StatefulWidget {
  final bool ilk; // true: ad-soyad da istenir (profil); false: görev yeri değişti
  final bool duzenle; // 16.10.2026 sahibi: "girdiği tüm bilgileri düzeltme" — ad-soyad dahil hepsi ön dolu, değişen kaydedilir
  final String? ad, il, ilce, gorevYeri, unvan; // mevcut hesap (değişiklikte ön dolu)
  final GorevliServisi? servis;
  const GorevliYerFormu({super.key, required this.ilk, this.duzenle = false, this.ad, this.il, this.ilce, this.gorevYeri, this.unvan, this.servis});
  @override
  State<GorevliYerFormu> createState() => _GorevliYerFormuState();
}

class _GorevliYerFormuState extends State<GorevliYerFormu> {
  late String _il;
  String? _ilce;
  late String _unvan;
  bool _yukleniyor = false;
  String? _hata;
  final _ad = TextEditingController();
  final _yer = TextEditingController();

  @override
  void initState() {
    super.initState();
    // ilk kayıtta kullanıcının uygulamada seçtiği il önerilir (sabit 'Ordu' yerine); yoksa 'Ordu'
    _il = (widget.il ?? '').isEmpty ? (Kapsam.oku(context).il ?? 'Ordu') : widget.il!;
    _ilce = (widget.ilce ?? '').isEmpty ? null : widget.ilce;
    final u = widget.unvan;
    _unvan = M.gorevliUnvanlar.any((x) => x[1] == u) ? u! : M.gorevliUnvanlar.first[1];
    _ad.text = widget.ad ?? '';
    _yer.text = widget.gorevYeri ?? '';
  }

  @override
  void dispose() {
    _ad.dispose();
    _yer.dispose();
    super.dispose();
  }

  GorevliServisi _servis() => widget.servis ?? GorevliServisi(istemci: Kapsam.oku(context).veri.istemci);

  static bool _adGecerli(String s) {
    final n = s.trim().split(RegExp(r'\s+')).where((x) => x.isNotEmpty).length;
    return n >= 2 && n <= 5;
  }

  bool get _hazir => (!(widget.ilk || widget.duzenle) || _adGecerli(_ad.text)) && _ilce != null && _yer.text.trim().length >= 2;

  String _bos(String s) => s.trim().replaceAll(RegExp(r'\s+'), ' ');

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
    if (s != null && mounted && s != _il) {
      setState(() {
        _il = s;
        _ilce = null;
      });
    }
  }

  Future<void> _ilceSec() async {
    final s = await _listeSec(Kapsam.oku(context).ilceListesi(_il));
    if (s != null && mounted) setState(() => _ilce = s);
  }

  Future<void> _kaydet() async {
    if (_yukleniyor || !_hazir) return;
    final tok = Kapsam.oku(context).depo.gorevliOturum;
    if (tok == null) return;
    setState(() {
      _yukleniyor = true;
      _hata = null;
    });
    final govde = <String, dynamic>{'il': _il, 'ilce': _ilce, 'gorev_yeri': _bos(_yer.text), 'unvan': _unvan, if (widget.ilk) 'ad_soyad': _bos(_ad.text)};
    final s = _servis();
    var y = widget.ilk ? await s.profil(tok, govde) : await s.gorevYeri(tok, govde);
    // düzenleme kipinde ad-soyad değiştiyse ayrıca kaydedilir (sunucu: /gorevli/ad-soyad, en çok 5 kez)
    final yeniAd = _ad.text.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (y.tamam && widget.duzenle && yeniAd != (widget.ad ?? '').trim()) y = await s.adSoyad(tok, yeniAd);
    if (!mounted) return;
    setState(() => _yukleniyor = false);
    if (!y.tamam && y.kod == 429) {
      setState(() => _hata = M.gorevliAdHakDoldu);
      return;
    }
    if (y.tamam) {
      Navigator.of(context).pop(true);
    } else if (y.kod == 409 && widget.ilk) {
      Navigator.of(context).pop(true); // profil zaten kayıtlı: panel yeniden yüklenir
    } else {
      setState(() => _hata = M.aileAgHata);
    }
  }

  Widget _secim(CvRenk r, String etiket, String deger, VoidCallback onTap) => Padding(
        padding: const EdgeInsets.only(bottom: R.s3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
          const SizedBox(height: 6),
          IkincilDugme(deger, onTap: onTap),
        ]),
      );

  Widget _unvanlar(CvRenk r) {
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

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop(false)),
            sag: YuvarlakDugme(ikon: 'kapat', anlam: 'Kapat', onTap: () => Navigator.of(context).pop(false)),
            ust: M.gorevliUst,
            baslik: BuyukBaslik(widget.ilk ? M.gorevliProfilBaslik : widget.duzenle ? M.gorevliBilgiDuzenle : M.gorevliYerDegisti),
          ),
          Expanded(
            child: ListView(
              key: const ValueKey('gy_liste'),
              padding: const EdgeInsets.fromLTRB(R.s5, R.s3, R.s5, R.s6),
              children: [
                Text(widget.ilk ? M.gorevliProfilAciklama : widget.duzenle ? M.gorevliBilgiDuzenleAciklama : M.gorevliYerDegistiAciklama,
                    key: const ValueKey('gy_aciklama'), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
                const SizedBox(height: R.s4),
                if (widget.ilk || widget.duzenle)
                  FormAlani(key: const ValueKey('gy_ad'), etiket: M.gorevliAd, ipucu: M.gorevliAdYer, denetleyici: _ad, enCok: 60, onChanged: (_) => setState(() {})),
                _secim(r, M.alanIl, _il, _ilSec),
                _secim(r, M.alanIlce, _ilce ?? M.alanIlce, _ilceSec),
                FormAlani(key: const ValueKey('gy_yer'), etiket: M.gorevliYer, ipucu: M.gorevliYerYer, denetleyici: _yer, enCok: 60, onChanged: (_) => setState(() {})),
                _unvanlar(r),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.fromLTRB(R.s5, R.s3, R.s5, R.s5),
            decoration: BoxDecoration(color: r.zemin, border: Border(top: BorderSide(color: r.cizgi))),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              if (_hata != null) Padding(padding: const EdgeInsets.only(bottom: R.s3), child: Text(_hata!, textAlign: TextAlign.center, style: Y.kucuk(r))),
              AnaDugme(widget.ilk ? M.gorevliKaydetDugme : widget.duzenle ? M.gorevliAdKaydet : M.gorevliYerKaydet, onTap: (_hazir && !_yukleniyor) ? _kaydet : null),
            ]),
          ),
        ]),
      ),
    );
  }
}

