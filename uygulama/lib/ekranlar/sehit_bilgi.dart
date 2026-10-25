// Şehit cenazesi ilanları YALNIZ din görevlisi panelinden verilir (site sahibi 15.10.2026, §27 + §37).
// "Şehit yakını" kapısı kalır ama forma gitmez: prototipteki gibi PENCERE (alttan açılan sayfa) + "Din görevlisi misiniz? Kayıt olun." bağlantısı.
import 'package:flutter/material.dart';

import '../bilesenler/ortak.dart';
import '../cekirdek/durum.dart';
import '../cekirdek/metin.dart';
import '../cekirdek/tema.dart';
import 'gorevli_kayit.dart';

/// Bilgi penceresini açar (tam ekran DEĞİL). Bağlantıya dokunulursa pencere kapanır ve din görevlisi kayıt ekranı (oturum varsa panel) açılır.
Future<void> sehitBilgiGoster(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (c) => const _SehitBilgiPenceresi(),
  );
}

class _SehitBilgiPenceresi extends StatelessWidget {
  const _SehitBilgiPenceresi();

  @override
  Widget build(BuildContext context) {
    final r = context.renk;
    return SafeArea(
      child: Container(
        key: const ValueKey('sehit_bilgi_pencere'),
        width: double.infinity,
        margin: const EdgeInsets.all(R.s3),
        padding: const EdgeInsets.all(R.s5),
        decoration: BoxDecoration(color: r.yuzey, borderRadius: BorderRadius.circular(R.kart)),
        child: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(M.sehitBilgiBaslik, key: const ValueKey('sehit_bilgi_baslik'), textAlign: TextAlign.center, style: Y.adim(r)),
            const SizedBox(height: R.s3),
            Text(M.sehitBilgiGovde, key: const ValueKey('sehit_bilgi_govde'), textAlign: TextAlign.center, style: Y.govde(r)),
            const SizedBox(height: R.s3),
            Text(M.sehitBilgiKapanis, key: const ValueKey('sehit_bilgi_kapanis'), textAlign: TextAlign.center, style: Y.govde(r)),
            const SizedBox(height: R.s4),
            InkWell(
              key: const ValueKey('sehit_bilgi_gorevli'),
              onTap: () {
                // pencere kapanmadan önce gerekenler alınır; kayıt/panel kök gezginde açılır
                final d = Kapsam.oku(context);
                final nav = Navigator.of(context, rootNavigator: true);
                Navigator.of(context).pop();
                if (d.depo.gorevliOturum != null) {
                  d.panelSekmesiAc(); // oturum varsa Panel sekmesi (parola sorulur; URUN §53)
                } else {
                  nav.push(MaterialPageRoute(builder: (_) => GorevliKayit(il: d.il ?? '', ilce: d.ilce)));
                }
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: R.s3),
                child: Text(M.ilanKutusuKayit,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 14, height: 18 / 14, color: r.vurguMetin, decoration: TextDecoration.underline, decorationColor: r.vurguMetin)),
              ),
            ),
            AnaDugme(M.aileBittiDugme, onTap: () => Navigator.of(context).pop()),
          ]),
        ),
      ),
    );
  }
}
