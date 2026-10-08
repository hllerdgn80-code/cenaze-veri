// Sayfam: kaydedilen merhum/merhumeler (cihazda; kendiliğinden silinmez) + 6 okuma sayacı.
import 'package:flutter/material.dart';

import '../bilesenler/ilan_karti.dart';
import '../bilesenler/menu.dart';
import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';

class SayfamEkrani extends StatelessWidget {
  const SayfamEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    final d = Kapsam.of(context);
    final liste = d.depo.sayfam();
    return Column(children: [
      BaslikCubugu(
        sol: LogoDugme(onTap: d.anaEkranaDon),
        sag: const MenuDugmesi(),
        ust: M.sayfamUst,
        baslik: const BuyukBaslik(M.sayfamBaslik),
      ),
      Expanded(
        child: liste.isEmpty
            ? ListView(children: const [BosDurum(baslik: M.sayfamBosBaslik, aciklama: M.sayfamBosAciklama)])
            : ListView(
                padding: const EdgeInsets.fromLTRB(R.s5, 0, R.s5, R.s6),
                children: [
                  for (final k in liste) IlanKarti(key: ValueKey('s_${k.ilan.id}'), ilan: k.ilan, sayacli: true),
                ],
              ),
      ),
    ]);
  }
}
