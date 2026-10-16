// Sekmeli kabuk: 4 eşit sekme (İlanlar · Sayfam · Dualar · Hatırla); din görevlisi oturumu varsa 5. sekme Panel (URUN §53); her sekmenin kendi gezgini var,
// alt ekranlarda (dua listesi, Kaybettiklerimiz) sekme çubuğu görünür kalır.
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../bilesenler/ikonlar.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import 'dualar.dart';
import 'guncelleme.dart';
import 'hatirla.dart';
import 'ilanlar.dart';
import 'panel_sekmesi.dart';
import 'sayfam.dart';

const _sekmeIkon = ['sk_ilan', 'sk_sayfam', 'sk_dua', 'sk_hatirla', 'sk_panel'];

class AnaKabuk extends StatelessWidget {
  const AnaKabuk({super.key});

  Widget _kok(int i) {
    switch (i) {
      case 0:
        return const IlanlarEkrani();
      case 1:
        return const SayfamEkrani();
      case 2:
        return const DualarEkrani();
      case 3:
        return const HatirlaEkrani();
      default:
        return const PanelSekmesi();
    }
  }

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    final r = context.renk;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (didPop) return;
        final nav = d.sekmeAnahtarlari[d.sekme].currentState;
        if (nav != null && nav.canPop()) {
          nav.pop();
        } else if (d.sekme != 0) {
          d.sekmeSec(0);
        } else {
          SystemNavigator.pop();
        }
      },
      child: Scaffold(
        body: SafeArea(
          bottom: false,
          child: Column(children: [
            const GuncellemeCubugu(),
            Expanded(
              child: IndexedStack(
                index: d.sekme < d.sekmeSayisi ? d.sekme : 0,
                children: [
                  for (int i = 0; i < d.sekmeSayisi; i++)
                    Navigator(
                      key: d.sekmeAnahtarlari[i],
                      onGenerateRoute: (_) => MaterialPageRoute(
                        builder: (_) => Scaffold(body: _kok(i)),
                      ),
                    ),
                ],
              ),
            ),
          ]),
        ),
        bottomNavigationBar: Container(
          decoration: BoxDecoration(
            color: r.zemin,
            border: Border(top: BorderSide(color: r.cizgi)),
          ),
          child: SafeArea(
            top: false,
            child: SizedBox(
              height: 56,
              child: Row(children: [
                for (int i = 0; i < d.sekmeSayisi; i++)
                  Expanded(
                    child: InkWell(
                      key: ValueKey('sekme_$i'),
                      onTap: () => d.sekmeSec(i),
                      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Ikon(_sekmeIkon[i], boyut: 24, renk: d.sekme == i ? r.vurguMetin : r.metin3),
                        const SizedBox(height: 3),
                        Text(i < 4 ? M.sekmeler[i] : M.sekmePanel,
                            maxLines: 1,
                            softWrap: false,
                            overflow: TextOverflow.ellipsis,
                            textAlign: TextAlign.center,
                            style: Y.sekme(d.sekme == i ? r.vurguMetin : r.metin3)),
                      ]),
                    ),
                  ),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}
