// Şehit cenazesi ilanları YALNIZ din görevlisi panelinden verilir (site sahibi 15.10.2026, §27 + §37).
// "Şehit yakını" kapısı kalır ama forma gitmez: sade bilgi ekranı + "Din görevlisi misiniz? Kayıt olun." bağlantısı.
import 'package:flutter/material.dart';

import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import 'gorevli_kayit.dart';

class SehitBilgiEkrani extends StatelessWidget {
  const SehitBilgiEkrani({super.key});

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    final d = Kapsam.oku(context);
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          BaslikCubugu(
            sol: YuvarlakDugme(ikon: 'geri', anlam: 'Geri', onTap: () => Navigator.of(context).pop()),
            sag: YuvarlakDugme(ikon: 'kapat', anlam: 'Kapat', onTap: () => Navigator.of(context).pop()),
            ust: M.sehitBilgiUst,
            baslik: const BuyukBaslik(M.sehitFormBaslik),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(R.s5, R.s6, R.s5, R.s6),
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(R.s5),
                  decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
                  child: Column(children: [
                    Text(M.sehitBilgiBaslik, key: const ValueKey('sehit_bilgi_baslik'), textAlign: TextAlign.center, style: Y.adim(r)),
                    const SizedBox(height: R.s3),
                    Text(M.sehitBilgiGovde, key: const ValueKey('sehit_bilgi_govde'), textAlign: TextAlign.center, style: Y.govde(r)),
                    const SizedBox(height: R.s3),
                    Text(M.sehitBilgiKapanis, key: const ValueKey('sehit_bilgi_kapanis'), textAlign: TextAlign.center, style: Y.govde(r)),
                  ]),
                ),
                const SizedBox(height: R.s4),
                InkWell(
                  key: const ValueKey('sehit_bilgi_gorevli'),
                  onTap: () => gorevliKapisi(context, il: d.il ?? '', ilce: d.ilce),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: R.s3),
                    child: Text(M.ilanKutusuKayit, textAlign: TextAlign.center, style: TextStyle(fontSize: 14, height: 18 / 14, color: r.vurguMetin, decoration: TextDecoration.underline, decorationColor: r.vurguMetin)),
                  ),
                ),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}
