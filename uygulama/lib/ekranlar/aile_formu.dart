// Aile formu — "Cenaze ilanı paylaş" (verisi olmayan iller, URUN-TASLAGI §15/§21).
// v0.1: SMS/sunucu yok; "Onayla ve gönder" alanları dolu bir e-posta taslağı açar (iletisim@kimincenazesi.com).
// İlan kontrolden sonra yayımlanır. Belge dosyası istenmez, tam T.C. kimlik numarası istenmez.
import 'package:flutter/material.dart';

import '../bilesenler/ikonlar.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';

class AileFormu extends StatefulWidget {
  final String il;
  final String? ilce;
  const AileFormu({super.key, required this.il, this.ilce});
  @override
  State<AileFormu> createState() => _AileFormuState();
}

class _AileFormuState extends State<AileFormu> {
  String? _cins;
  String? _ilce;
  String _vefat = bugunTr();
  String _namaz = M.namazSecenek.first;
  String _yakinlik = M.yakinlikSecenek.first;
  bool _onay = false;
  bool _bitti = false;
  final _ad = TextEditingController();
  final _mahalle = TextEditingController();
  final _cami = TextEditingController();
  final _mezarlik = TextEditingController();
  final _belge = TextEditingController();
  final _basvuranAd = TextEditingController();
  final _tc = TextEditingController();
  final _tel = TextEditingController();

  @override
  void initState() {
    super.initState();
    _ilce = widget.ilce;
  }

  @override
  void dispose() {
    for (final c in [_ad, _mahalle, _cami, _mezarlik, _belge, _basvuranAd, _tc, _tel]) {
      c.dispose();
    }
    super.dispose();
  }

  bool get _hazir =>
      _cins != null &&
      _ad.text.trim().length >= 3 &&
      _belge.text.trim().length >= 6 &&
      _basvuranAd.text.trim().length >= 3 &&
      _tel.text.replaceAll(RegExp(r'\D'), '').length >= 10 &&
      _onay;

  Future<void> _gonder() async {
    final govde = [
      'Vefat eden: ${_cins == 'e' ? M.erkek : M.kadin}',
      '${M.alanAd}: ${_ad.text.trim()}',
      '${M.alanVefat}: ${tarih(_vefat)}',
      '${M.alanNamaz}: $_namaz',
      '${M.alanIl}: ${widget.il}',
      '${M.alanIlce}: ${_ilce ?? '-'}',
      '${M.alanMahalle}: ${_mahalle.text.trim()}',
      '${M.alanCami}: ${_cami.text.trim()}',
      '${M.alanMezarlik}: ${_mezarlik.text.trim()}',
      '',
      '${M.adim2Alan}: ${_belge.text.trim()}',
      '',
      '${M.adim3Ad}: ${_basvuranAd.text.trim()}',
      '${M.adim3Tc}: ${_tc.text.trim()}',
      '${M.adim3Yakinlik}: $_yakinlik',
      '${M.adim3Tel}: ${_tel.text.trim()}',
      '',
      '${M.hukukKutu} ✓',
    ].join('\n');
    final ok = await epostaTaslagi(konu: 'Cenaze ilanı · ${widget.il}${_ilce != null ? ' / $_ilce' : ''}', govde: govde);
    if (!mounted) return;
    if (ok) setState(() => _bitti = true);
  }

  Future<void> _tarihSec() async {
    final simdi = gunCoz(bugunTr())!;
    final s = gunCoz(_vefat) ?? simdi;
    final g = await showDatePicker(
      context: context,
      initialDate: DateTime(s.year, s.month, s.day),
      firstDate: DateTime(simdi.year, simdi.month, simdi.day).subtract(const Duration(days: 7)),
      lastDate: DateTime(simdi.year, simdi.month, simdi.day),
    );
    if (g != null && mounted) setState(() => _vefat = gunYaz(g));
  }

  Future<void> _ilceSec() async {
    final d = Kapsam.oku(context);
    final liste = d.ilceListesi(widget.il);
    final s = await showDialog<String>(
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
    if (s != null && mounted) setState(() => _ilce = s);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: const SizedBox(width: 40, height: 40),
            ust: M.aileUstGiris,
            baslik: const BuyukBaslik(M.aileBaslik),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s8),
              children: _bitti ? _bittiGorunumu(r) : _form(r),
            ),
          ),
        ]),
      ),
    );
  }

  List<Widget> _bittiGorunumu(CvRenk r) => [
        const SizedBox(height: R.s6),
        BosDurum(ikon: 'tik', baslik: M.aileEpostaNot, aciklama: M.aileNot),
        AnaDugme(M.aileBittiDugme, onTap: () => Navigator.of(context).pop()),
      ];

  Widget _madde(CvRenk r, String metin) => Padding(
        padding: const EdgeInsets.only(top: R.s3),
        child: Row(children: [
          Ikon('tik', boyut: 20, renk: r.vurguMetin),
          Expanded(child: Text(metin, textAlign: TextAlign.center, style: Y.kucuk(r))),
          const SizedBox(width: 20),
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
    return [
      // Giriş kartı
      Container(
        padding: const EdgeInsets.all(R.s5),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: Column(children: [
          Text(M.aileGirisBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
          const SizedBox(height: R.s2),
          Text(M.aileGirisAciklama(widget.il), textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
          const SizedBox(height: R.s4),
          Text(trBuyuk(M.aileGirisEtiket), textAlign: TextAlign.center, style: Y.ustEtiket(r)),
          const SizedBox(height: R.s1),
          Text(M.aileGirisNot, textAlign: TextAlign.center, style: Y.kucuk(r)),
          _madde(r, M.aileMadde1),
          _madde(r, M.aileMadde3),
          _madde(r, M.aileMadde4),
        ]),
      ),
      // 1. Vefat eden
      _baslik(r, M.adim1Baslik, M.adim1Aciklama),
      _secenekler(r, M.alanCinsiyet, const [M.erkek, M.kadin], _cins == 'e' ? M.erkek : (_cins == 'k' ? M.kadin : ''),
          (v) => setState(() => _cins = v == M.erkek ? 'e' : 'k')),
      FormAlani(etiket: M.alanAd, ipucu: M.alanAdYer(_cins), denetleyici: _ad, onChanged: yenile),
      _secimDugmesi(r, M.alanVefat, tarih(_vefat), _tarihSec),
      _secenekler(r, M.alanNamaz, M.namazSecenek, _namaz, (v) => setState(() => _namaz = v)),
      _secimDugmesi(r, M.alanIl, widget.il, () {}),
      _secimDugmesi(r, M.alanIlce, _ilce ?? M.alanIlce, _ilceSec),
      FormAlani(etiket: M.alanMahalle, ipucu: M.alanMahalleYer, denetleyici: _mahalle),
      FormAlani(etiket: M.alanCami, ipucu: M.alanCamiYer, denetleyici: _cami),
      FormAlani(etiket: M.alanMezarlik, ipucu: M.alanMezarlikYer, denetleyici: _mezarlik),
      // 2. Ölüm belgesi
      _baslik(r, M.adim2Baslik, M.adim2Aciklama),
      FormAlani(etiket: M.adim2Alan, ipucu: M.adim2AlanYer, denetleyici: _belge, onChanged: yenile),
      // 3. Başvuran
      _baslik(r, M.adim3Baslik),
      FormAlani(etiket: M.adim3Ad, ipucu: M.adim3AdYer, denetleyici: _basvuranAd, onChanged: yenile),
      FormAlani(etiket: M.adim3Tc, denetleyici: _tc, klavye: TextInputType.number, enCok: 4),
      _secenekler(r, M.adim3Yakinlik, M.yakinlikSecenek, _yakinlik, (v) => setState(() => _yakinlik = v)),
      FormAlani(
          etiket: M.adim3Tel, ipucu: M.adim3TelYer, denetleyici: _tel, klavye: TextInputType.phone, onChanged: yenile),
      // 4. Yasal beyan
      _baslik(r, M.adim5Baslik, M.adim5Aciklama),
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
      const SizedBox(height: R.s5),
      AnaDugme(M.sonDugme, onTap: _hazir ? _gonder : null),
      const SizedBox(height: R.s3),
      Text(M.aileNot, textAlign: TextAlign.center, style: Y.soluk(r)),
    ];
  }
}
