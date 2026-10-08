// ⋮ menü (270 px, ekranın ortasında): Adresi değiştir · Tema · Uygulamayı paylaş · Öneri ve tavsiyeleriniz · Hakkında · Gizlilik
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../ekranlar/adres.dart';
import 'ikonlar.dart';
import 'ortak.dart';

/// Başlık çubuğunun sağındaki ⋮ düğmesi
class MenuDugmesi extends StatelessWidget {
  final double genislik;
  const MenuDugmesi({super.key, this.genislik = 40});
  @override
  Widget build(BuildContext context) =>
      YuvarlakDugme(ikon: 'menu', anlam: 'Menü', genislik: genislik, onTap: () => menuAc(context));
}

Future<void> menuAc(BuildContext context) async {
  final d = Kapsam.oku(context);
  final secim = await showDialog<String>(
    context: context,
    barrierColor: const Color(0x8C000000),
    builder: (c) {
      final r = c.renk;
      Widget satir(String k, String ikon, String yazi) => InkWell(
            onTap: () => Navigator.of(c).pop(k),
            child: Container(
              height: 52,
              padding: const EdgeInsets.symmetric(horizontal: R.s4),
              decoration: BoxDecoration(border: Border(top: BorderSide(color: r.cizgi))),
              child: Row(children: [
                Ikon(ikon, boyut: 22, renk: r.vurguMetin),
                Expanded(
                  child: Text(yazi, textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: r.metin)),
                ),
                const SizedBox(width: 22),
              ]),
            ),
          );
      return Dialog(
        backgroundColor: r.yuzey,
        insetPadding: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
        clipBehavior: Clip.antiAlias,
        child: SizedBox(
          width: 270,
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const SizedBox(height: R.s1),
            satir('adres', 'konum', M.menuAdres),
            satir('tema', d.koyu ? 'gunes' : 'ay', d.koyu ? M.menuAcikTema : M.menuKoyuTema),
            satir('paylas', 'paylas', M.menuPaylas),
            satir('oneri', 'mektup', M.menuOneri),
            satir('hakkinda', 'bilgi', M.menuHakkinda),
            satir('gizlilik', 'kilit', M.menuGizlilik),
          ]),
        ),
      );
    },
  );
  if (secim == null || !context.mounted) return;
  switch (secim) {
    case 'adres':
      await Navigator.of(context, rootNavigator: true).push(MaterialPageRoute(
        builder: (_) => const IlSecEkrani(degistir: true),
      ));
      break;
    case 'tema':
      await d.temaDegistir();
      break;
    case 'paylas':
      await uygulamayiPaylas();
      break;
    case 'oneri':
      await oneriAc(context);
      break;
    case 'hakkinda':
      await metinPenceresi(context, M.hakkindaBaslik, M.hakkindaMetin, paylas: true);
      break;
    case 'gizlilik':
      await metinPenceresi(context, M.gizlilikBaslik, M.gizlilikMetin);
      break;
  }
}

Future<void> uygulamayiPaylas() async {
  try {
    await SharePlus.instance.share(ShareParams(text: M.paylasMetin));
  } catch (_) {}
}

/// mailto: taslağını açar (alanlar dolu). Gönderimi kullanıcı kendi e-posta uygulamasında yapar.
Future<bool> epostaTaslagi({required String konu, required String govde}) async {
  final uri = Uri.parse(
      'mailto:${M.iletisimEposta}?subject=${Uri.encodeComponent(konu)}&body=${Uri.encodeComponent(govde)}');
  try {
    return await launchUrl(uri, mode: LaunchMode.externalApplication);
  } catch (_) {
    return false;
  }
}

/// Hakkında / Gizlilik penceresi (ortalı)
Future<void> metinPenceresi(BuildContext context, String baslik, String metin, {bool paylas = false}) {
  return showDialog<void>(
    context: context,
    builder: (c) {
      final r = c.renk;
      return Dialog(
        backgroundColor: r.yuzey,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
        child: Padding(
          padding: const EdgeInsets.all(R.s5),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (paylas) ...[const Logo(boyut: 56, yaricap: 16), const SizedBox(height: R.s3)],
            Text(baslik, textAlign: TextAlign.center, style: Y.adim(r)),
            const SizedBox(height: R.s3),
            Text(metin, textAlign: TextAlign.left, style: Y.govde(r).copyWith(height: 22 / 15)),
            const SizedBox(height: R.s5),
            if (paylas) ...[
              IkincilDugme(M.menuPaylas, onTap: () {
                Navigator.of(c).pop();
                uygulamayiPaylas();
              }),
              const SizedBox(height: R.s3),
            ],
            AnaDugme(M.modalKapat, yukseklik: 48, onTap: () => Navigator.of(c).pop()),
          ]),
        ),
      );
    },
  );
}

/// Öneri ve tavsiyeleriniz: metin + isteğe bağlı e-posta → iletisim@ adresine e-posta taslağı
Future<void> oneriAc(BuildContext context) {
  return showDialog<void>(context: context, builder: (_) => const _OneriPenceresi());
}

class _OneriPenceresi extends StatefulWidget {
  const _OneriPenceresi();
  @override
  State<_OneriPenceresi> createState() => _OneriPenceresiState();
}

class _OneriPenceresiState extends State<_OneriPenceresi> {
  final _mesaj = TextEditingController();
  final _eposta = TextEditingController();
  bool _bitti = false;

  @override
  void dispose() {
    _mesaj.dispose();
    _eposta.dispose();
    super.dispose();
  }

  Future<void> _gonder() async {
    final e = _eposta.text.trim();
    final ok = await epostaTaslagi(
      konu: M.oneriBaslik,
      govde: '${_mesaj.text.trim()}${e.isNotEmpty ? '\n\nE-posta: $e' : ''}',
    );
    if (!mounted) return;
    if (ok) setState(() => _bitti = true);
  }

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Dialog(
      backgroundColor: r.yuzey,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(R.kart)),
      child: Padding(
        padding: const EdgeInsets.all(R.s5),
        child: _bitti
            ? Column(mainAxisSize: MainAxisSize.min, children: [
                Text(M.oneriTamamBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
                const SizedBox(height: R.s3),
                Text(M.aileEpostaNot, textAlign: TextAlign.center, style: Y.govde(r)),
                const SizedBox(height: R.s5),
                AnaDugme(M.oneriTamamDugme, yukseklik: 48, onTap: () => Navigator.of(context).pop()),
              ])
            : Column(mainAxisSize: MainAxisSize.min, children: [
                Text(M.oneriBaslik, textAlign: TextAlign.center, style: Y.adim(r)),
                const SizedBox(height: R.s4),
                FormAlani(etiket: M.oneriMesaj, ipucu: M.oneriMesajYer, denetleyici: _mesaj, satir: 4,
                    onChanged: (_) => setState(() {})),
                FormAlani(etiket: M.oneriEposta, ipucu: M.oneriEpostaYer, denetleyici: _eposta,
                    klavye: TextInputType.emailAddress),
                const SizedBox(height: R.s2),
                IkiliSatir(
                  sol: IkincilDugme(M.oneriVazgec, onTap: () => Navigator.of(context).pop()),
                  sag: AnaDugme(M.oneriGonder, yukseklik: 48, onTap: _mesaj.text.trim().length < 3 ? null : _gonder),
                ),
              ]),
      ),
    );
  }
}

/// Etiketli form alanı (etiket ve yazı ortalı)
class FormAlani extends StatelessWidget {
  final String etiket;
  final String? ipucu;
  final TextEditingController? denetleyici;
  final int satir;
  final TextInputType? klavye;
  final ValueChanged<String>? onChanged;
  final int? enCok;
  const FormAlani({
    super.key,
    required this.etiket,
    this.ipucu,
    this.denetleyici,
    this.satir = 1,
    this.klavye,
    this.onChanged,
    this.enCok,
  });

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return Padding(
      padding: const EdgeInsets.only(bottom: R.s3),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(etiket, textAlign: TextAlign.center, style: Y.sutunEtiket(r).copyWith(fontSize: 12, letterSpacing: 0.4)),
        const SizedBox(height: 6),
        TextField(
          controller: denetleyici,
          onChanged: onChanged,
          minLines: satir,
          maxLines: satir,
          maxLength: enCok,
          keyboardType: klavye,
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16, color: r.metin),
          decoration: InputDecoration(
            counterText: '',
            hintText: ipucu,
            hintStyle: TextStyle(color: r.metin3),
            filled: true,
            fillColor: r.yuzey2,
            contentPadding: const EdgeInsets.symmetric(horizontal: R.s4, vertical: R.s3),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(R.dugme), borderSide: BorderSide.none),
            focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(R.dugme), borderSide: BorderSide(color: r.vurgu)),
          ),
        ),
      ]),
    );
  }
}
