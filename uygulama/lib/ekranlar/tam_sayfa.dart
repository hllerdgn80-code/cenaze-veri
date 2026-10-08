// Tam Sayfa (gazetedeki vefat ilanının karşılığı). v0.1: ücretli ilan KAPALI (URUN-TASLAGI §28) —
// sekme görünür; sakin "yakında" metni + iki ÖRNEK ilan (kişiler kurgusaldır). Ödeme yok.
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import '../cekirdek/yardimci.dart';

class _Ornek {
  final String tur, ar, ok, meal, sure, sifat, ad, il, ilce, cenaze, kapanis, not;
  final String? unvan, soy, imza;
  final int vefatGun;
  final List<List<String>> aile;
  const _Ornek({
    required this.tur,
    required this.ar,
    required this.ok,
    required this.meal,
    required this.sure,
    required this.sifat,
    required this.ad,
    required this.il,
    required this.ilce,
    required this.cenaze,
    required this.kapanis,
    required this.not,
    required this.vefatGun,
    required this.aile,
    this.unvan,
    this.soy,
    this.imza,
  });
}

// ÖRNEK ilanlar (prototipteki kurgusal kişiler; ekranda "ÖRNEK" olarak işaretli)
List<_Ornek> _ornekler(String bugun) {
  final dun = gunEkle(bugun, -1);
  return [
    _Ornek(
      tur: 'VEFAT',
      ar: 'ٱلَّذِينَ إِذَآ أَصَـٰبَتْهُم مُّصِيبَةٌ قَالُوٓا۟ إِنَّا لِلَّهِ وَإِنَّآ إِلَيْهِ رَٰجِعُونَ',
      ok: 'Ellezîne izâ esâbethüm musîbetün kâlû innâ lillâhi ve innâ ileyhi râciûn.',
      meal: 'Başlarına bir musibet geldiğinde “Biz Allah’a aitiz ve O’na döneceğiz” derler.',
      sure: 'Bakara 2:156',
      sifat: 'Sevgili eşimiz, canım annemiz',
      ad: 'Nurcihan Örneksoy',
      il: 'Nurşehir',
      ilce: 'Selâmiye',
      vefatGun: -1,
      cenaze: 'Cenazesi ${tarih(bugun)} ${gunAdlari[haftaGunu(bugun)]} günü öğle namazını müteakip Sükûn Tepesi Camii, '
          'Selâmiye/Nurşehir’de kılınacak cenaze namazından sonra Huzurbahçe Mezarlığı’na defnedilecektir.',
      kapanis: 'Allah rahmet eylesin.',
      aile: const [
        ['Eşi', 'Kerami Örneksoy'],
        ['Çocukları', 'Ilgın, Bahadır, Nevra'],
        ['Torunları', 'Ruhsar, Tanyeli, Aksun'],
      ],
      not: 'Taziyeler Selâmiye’deki aile evinde kabul edilir.',
    ),
    _Ornek(
      tur: 'ACI KAYBIMIZ',
      ar: 'يَـٰٓأَيَّتُهَا ٱلنَّفْسُ ٱلْمُطْمَئِنَّةُ ٱرْجِعِىٓ إِلَىٰ رَبِّكِ رَاضِيَةً مَّرْضِيَّةً فَٱدْخُلِى فِى عِبَـٰدِى وَٱدْخُلِى جَنَّتِى',
      ok: 'Yâ eyyetühe’n-nefsü’l-mutmeinneh. İrciî ilâ rabbiki râdıyeten mardıyyeh. Fedhulî fî ibâdî. Vedhulî cennetî.',
      meal: 'Ey huzura ermiş can! Hoşnut olarak, hoşnut edilmiş olarak Rabbine dön. Kullarımın arasına gir, cennetime gir.',
      sure: 'Fecr 89:27–30',
      unvan: 'Emekli öğretmen',
      sifat: 'Aile büyüğümüz, saygın insan',
      ad: 'Hayrullah Kurguluoğlu',
      soy: 'merhum Feyzullah ve merhume Hanzade Kurguluoğlu’nun oğlu',
      il: 'Gülkent',
      ilce: 'Sükûnet',
      vefatGun: -2,
      cenaze: 'Cenazesi ${tarih(dun)} ${gunAdlari[haftaGunu(dun)]} günü ikindi namazını müteakip Nurlu Kubbe Camii’nde '
          'kılınacak cenaze namazından sonra Servili Yamaç Mezarlığı’nda toprağa verilecektir.',
      kapanis: 'Mekânı cennet olsun.',
      aile: const [
        ['Eşi', 'Pervin Kurguluoğlu'],
        ['Çocukları ve eşleri', 'Tolunay & Sırma, Esmanur & Kayra'],
        ['Torunları', 'Atlas, Melisa'],
        ['Kardeşleri', 'Zerrin, Nusret'],
      ],
      imza: 'KURGULUOĞLU AİLESİ',
      not: 'Çelenk yerine bir eğitim vakfına bağış yapılması rica olunur.',
    ),
  ];
}

class TamSayfaEkrani extends StatelessWidget {
  const TamSayfaEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.of(context);
    final bugun = bugunTr();
    return Column(children: [
      BaslikCubugu(
        sol: LogoDugme(onTap: d.anaEkranaDon),
        sag: const MenuDugmesi(),
        ust: M.tamUst,
        baslik: const BuyukBaslik(M.tamBaslik),
      ),
      Expanded(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
          children: [
            Container(
              padding: const EdgeInsets.all(R.s5),
              decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
              child: Column(children: [
                const Daire('kemer', boyut: 56),
                const SizedBox(height: R.s4),
                Text(M.tamYakinda,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 17, height: 22 / 17, fontWeight: FontWeight.w600, color: r.metin)),
                const SizedBox(height: R.s2),
                Text(M.fiyatAciklama, textAlign: TextAlign.center, style: Y.govde(r).copyWith(fontSize: 14)),
              ]),
            ),
            const Bolum(M.tamOrnek),
            for (final o in _ornekler(bugun)) _GazeteIlani(o: o, bugun: bugun),
          ],
        ),
      ),
    ]);
  }
}

const _kurdele = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72">'
    '<path d="M0 0h30L0 30z" fill="#1B1C1E"/><path d="M42 0h12L0 54V42z" fill="#1B1C1E"/></svg>';

class _GazeteIlani extends StatelessWidget {
  final _Ornek o;
  final String bugun;
  const _GazeteIlani({required this.o, required this.bugun});

  @override
  Widget build(BuildContext context) {
    const m = R.gazeteMurekkep;
    const serif = 'serif';
    TextStyle s(double b, {FontWeight w = FontWeight.w400, FontStyle st = FontStyle.normal, double ls = 0}) =>
        TextStyle(fontFamily: serif, fontSize: b, height: 1.45, color: m, fontWeight: w, fontStyle: st, letterSpacing: ls);
    Widget cizgi() => Container(height: 1, color: const Color(0x331B1C1E), margin: const EdgeInsets.symmetric(vertical: 14));

    return Container(
      margin: const EdgeInsets.only(bottom: R.s3),
      decoration: BoxDecoration(color: R.gazeteKagit, borderRadius: BorderRadius.circular(R.kart)),
      clipBehavior: Clip.antiAlias,
      child: Stack(children: [
        Positioned(left: 0, top: 0, child: SvgPicture.string(_kurdele, width: 64, height: 64)),
        Positioned(
          right: 14,
          top: 14,
          child: Hap(M.tamOrnek, zemin: const Color(0x221B1C1E), renk: m),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(R.s6, R.s8, R.s6, R.s6),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text(o.tur, textAlign: TextAlign.center, style: s(13, w: FontWeight.w700, ls: 3)),
            const SizedBox(height: 10),
            Text(o.ar, textAlign: TextAlign.center, textDirection: TextDirection.rtl, style: s(20)),
            const SizedBox(height: 4),
            Text(o.ok, textAlign: TextAlign.center, style: s(12, st: FontStyle.italic)),
            Text(o.meal, textAlign: TextAlign.center, style: s(13)),
            Text('(${o.sure})', textAlign: TextAlign.center, style: s(11)),
            cizgi(),
            if (o.unvan != null) Text(o.unvan!, textAlign: TextAlign.center, style: s(13)),
            Text(o.sifat, textAlign: TextAlign.center, style: s(14, st: FontStyle.italic)),
            const SizedBox(height: 6),
            Text(trBuyuk(o.ad), textAlign: TextAlign.center, style: s(22, w: FontWeight.w700, ls: 1)),
            if (o.soy != null) Text(o.soy!, textAlign: TextAlign.center, style: s(13)),
            const SizedBox(height: 6),
            Text('${tarih(gunEkle(bugun, o.vefatGun))} tarihinde Hakk’a yürümüştür.', textAlign: TextAlign.center, style: s(14)),
            cizgi(),
            Text(o.cenaze, textAlign: TextAlign.center, style: s(14)),
            const SizedBox(height: 12),
            Text(o.kapanis, textAlign: TextAlign.center, style: s(14, st: FontStyle.italic)),
            const SizedBox(height: 12),
            for (final a in o.aile) ...[
              Text(trBuyuk(a[0]), textAlign: TextAlign.center, style: s(11, w: FontWeight.w700, ls: 1.5)),
              Text(a[1], textAlign: TextAlign.center, style: s(14)),
              const SizedBox(height: 6),
            ],
            if (o.imza != null) ...[
              const SizedBox(height: 6),
              Text(o.imza!, textAlign: TextAlign.center, style: s(14, w: FontWeight.w700, ls: 2)),
            ],
            cizgi(),
            Text(o.not, textAlign: TextAlign.center, style: s(12).copyWith(color: const Color(0xFF555555))),
          ]),
        ),
      ]),
    );
  }
}
