// Mutabık ekran kuralları: §27 şehit en üstte, §21/1 ilçesiz kaynak "İl geneli", §21/2 diğer ilçeler,
// §21/3 bildirim teklifi, §32 bebek rozeti, 4 sekme, şehit bilgi penceresi, Bildir.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/bilesenler/ilan_karti.dart';
import 'package:kimin_cenazesi/bilesenler/ortak.dart';
import 'package:kimin_cenazesi/cekirdek/ilan.dart';
import 'package:kimin_cenazesi/cekirdek/metin.dart';
import 'package:kimin_cenazesi/cekirdek/uzak_ayar.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:kimin_cenazesi/ekranlar/ilanlar.dart';
import 'package:kimin_cenazesi/main.dart';

import 'ortak.dart';
import 'widget_test.dart' show kapsamli, telefon;

Map<String, dynamic> kayit(String id, String ad, String ilce, String gun, {bool sehit = false, bool bebek = false}) => {
      'id': id,
      'ad_soyad': ad,
      'ilce': ilce,
      'namaz_tarihi': gun,
      'namaz_yeri_vakti': 'Öğle Namazını Müteakip-ÖRNEK CAMİİ',
      if (sehit) 'sehit': true,
      if (sehit) 'rutbe': 'Piyade Uzman Çavuş',
      if (bebek) 'bebek': true,
    };

IlVerisi veriYap(String bugun, {Map<String, List<Map<String, dynamic>>> ilceler = const {}, List<Map<String, dynamic>> belirsiz = const []}) =>
    IlVerisi.fromJson('Muğla', {'ilceler': ilceler, 'ilce_belirsiz': belirsiz, 'il_disi': []});

void main() {
  final bugun = bugunTr();

  testWidgets('16.10.2026 sahibi: bugün boşsa YALNIZ "bulunmuyor" (dün açılmaz; uzak ayar varsayılanı)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final dun = gunEkle(bugun, -1);
    final v = veriYap(bugun, ilceler: {'Bodrum': [kayit('a', 'Dünkü Bir', 'Bodrum', dun)]});
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugün Bodrum’da cenaze ilanı bulunmuyor'), findsOneWidget);
    expect(find.text('Dünkü Bir'), findsNothing);
    expect(find.text(trBuyuk(M.dunBolum(dun))), findsNothing);
  });

  testWidgets('§57 (uzak ayar bugun_bossa_dunu_goster=true): bugün boş + dün 2 kayıt → "Dün (…)" bölümü ve 2 kart; bulunmuyor satırı üstte', (tester) async {
    UzakAyar.bugunBossaDunuGoster = true;
    addTearDown(() => UzakAyar.bugunBossaDunuGoster = false);
    telefon(tester);
    final d = await testDurumu();
    final dun = gunEkle(bugun, -1);
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Dünkü Bir', 'Bodrum', dun), kayit('b', 'Dünkü İki', 'Bodrum', dun), kayit('c', 'Evvelki Gün', 'Bodrum', gunEkle(bugun, -2))],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugün Bodrum’da cenaze ilanı bulunmuyor'), findsOneWidget);
    expect(find.text(trBuyuk(M.dunBolum(dun))), findsOneWidget);
    expect(find.text('Dünkü Bir'), findsOneWidget);
    expect(find.text('Dünkü İki'), findsOneWidget);
    expect(find.text('Evvelki Gün'), findsNothing); // yalnız dün
    expect(tester.getTopLeft(find.text('Bugün Bodrum’da cenaze ilanı bulunmuyor')).dy < tester.getTopLeft(find.text('Dünkü Bir')).dy, isTrue);
  });

  testWidgets('§57: bugün de dün de boş → "Dün" bölümü yok, yalnız bulunmuyor satırı', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('c', 'Evvelki Gün', 'Bodrum', gunEkle(bugun, -2))],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugün Bodrum’da cenaze ilanı bulunmuyor'), findsOneWidget);
    expect(find.textContaining('Dün ('), findsNothing);
    expect(find.text('Evvelki Gün'), findsNothing);
  });

  testWidgets('§57: bugün ilan VARSA "Dün" bölümü açılmaz', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final dun = gunEkle(bugun, -1);
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Bugünkü', 'Bodrum', bugun), kayit('b', 'Dünkü Bir', 'Bodrum', dun)],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugünkü'), findsOneWidget);
    expect(find.text('Dünkü Bir'), findsNothing);
  });

  testWidgets('§27: ilçe görünümünde de şehit kartı listenin başında (ilçesi belirtilmemiş şehit dahil)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun)],
    }, belirsiz: [kayit('s', 'Örnekalp Yıldırımhan', '', bugun, sehit: true)]);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    final sehitY = tester.getTopLeft(find.textContaining('Örnekalp Yıldırımhan')).dy;
    final aliY = tester.getTopLeft(find.text('Ali Örnek')).dy;
    expect(sehitY < aliY, isTrue);
    expect(find.text('ŞEHİT'), findsOneWidget);
    expect(find.text('Ruhu şad olsun, mekânı cennet olsun.'), findsOneWidget);
  });

  testWidgets('§21/1: ilçesiz kaynakta ilanlar "İl geneli" altında, "bugün yok" denmez', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, belirsiz: [kayit('g', 'Veli Örnek', '', bugun)]);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, null, bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Veli Örnek'), findsOneWidget);
    expect(find.textContaining('cenaze ilanı bulunmuyor'), findsNothing);
    expect(find.text(trBuyuk('İl geneli')), findsOneWidget);
  });

  testWidgets('16.10.2026 sahibi: ilçe sayfasında "İl geneli" bölümü YOK (nakil/ilçesiz kayıt yalnız il görünümünde)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', gunEkle(bugun, -3))],
    }, belirsiz: [kayit('g', 'Nakil Kişi', '', bugun)]);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Nakil Kişi'), findsNothing);
    expect(find.textContaining('İL GENELİ'), findsNothing);
    expect(find.text('Bugün Bodrum’da cenaze ilanı bulunmuyor'), findsOneWidget);
  });

  testWidgets('16.10.2026 UZAK AYAR: ayarlar.json ilce_sayfasinda_il_geneli=true ise ilçe sayfasında "İl geneli" görünür (sürümsüz)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', gunEkle(bugun, -3))],
    }, belirsiz: [kayit('g', 'Nakil Kişi', '', bugun)]);
    UzakAyar.uygula({'ilce_sayfasinda_il_geneli': true});
    addTearDown(() => UzakAyar.ilceSayfasindaIlGeneli = false);
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Bodrum', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Nakil Kişi'), findsOneWidget);
  });

  testWidgets('15.10.2026 sahibi: ilçede bugün ilan yoksa YALNIZ "bulunmuyor" satırı; diğer ilçeler ve son 7 gün açılmaz', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun)],
      'Milas': [kayit('b', 'Hasan Örnek', 'Milas', bugun)],
      'Marmaris': [kayit('e', 'Dünkü Örnek', 'Marmaris', gunEkle(bugun, -1))],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: gunIcerigi(v, 'Marmaris', bugun, bugun))));
    await tester.pumpAndSettle();
    expect(find.text('Bugün Marmaris’te cenaze ilanı bulunmuyor'), findsOneWidget);
    expect(find.textContaining('Son yedi gün'), findsNothing);
    expect(find.text(trBuyuk('Muğla’da bugün: Bodrum, Milas')), findsNothing);
    expect(find.text('Ali Örnek'), findsNothing);
    expect(find.text('Hasan Örnek'), findsNothing);
    // 16.10.2026 sahibi: bugün kayıt yoksa dün de AÇILMAZ (uzak ayar varsayılanı kapalı)
    expect(find.text('Dünkü Örnek'), findsNothing);
  });

  testWidgets('15.10.2026: yarına kayıt varsa şeritte "Yarın" görünür, seçilince içeriği açılır; Bugün varsayılan', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final yarin = gunEkle(bugun, 1);
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun), kayit('y', 'Yarın Örnek', 'Bodrum', yarin)],
    });
    await tester.pumpWidget(kapsamli(d, Column(children: [
      SizedBox(height: 80, child: SeritSarmal(veri: v, ilce: 'Bodrum', secili: bugun)),
      ...gunIcerigi(v, 'Bodrum', yarin, bugun),
    ])));
    await tester.pumpAndSettle();
    expect(find.text(M.seritYarin), findsOneWidget);
    expect(find.byKey(ValueKey('gun_$yarin')), findsOneWidget);
    expect(find.text('Yarın Örnek'), findsOneWidget);
    expect(find.text('Ali Örnek'), findsNothing);
  });

  testWidgets('30.10.2026 §58: yarına kayıt YOK olsa da şeritte "Yarın" VAR (öbür gün yok); 7 geçmiş gün yine var', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final v = veriYap(bugun, ilceler: {
      'Bodrum': [kayit('a', 'Ali Örnek', 'Bodrum', bugun)],
    });
    await tester.pumpWidget(kapsamli(d, SizedBox(height: 80, child: SeritSarmal(veri: v, ilce: 'Bodrum', secili: bugun))));
    await tester.pumpAndSettle();
    expect(find.text(M.seritYarin), findsOneWidget);
    expect(find.byKey(ValueKey('gun_${gunEkle(bugun, 1)}')), findsOneWidget);
    expect(find.byKey(ValueKey('gun_${gunEkle(bugun, 2)}')), findsNothing);
    for (int n = 0; n < 7; n++) {
      expect(find.byKey(ValueKey('gun_${gunEkle(bugun, -n)}')), findsOneWidget);
    }
  });

  testWidgets('§32: adı olan bebek kaydında "Bebek" rozeti', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final r = Ilan.fromJson(kayit('c', 'Elif Örnek', 'Ünye', bugun, bebek: true))!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Bebek'), findsOneWidget);
  });

  testWidgets('§36: bildirim sorusu listede değil, yalnız ilk açılış kartında (test durumunda kapalı)', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Kars', 'ilce': 'Merkez'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    expect(bildirimTeklifiAcik, isTrue);
    expect(find.text('İlçenizde cenaze ilanı paylaşıldığında haber verelim mi?'), findsNothing);
    expect(find.byKey(const ValueKey('ilan_kutusu')), findsOneWidget); // 15.10: ilan kutusu (kaynaksız il)
    expect(find.text('Cenaze yakını olarak ilanı paylaş'), findsNothing); // ücretsiz aile ilanı kalktı
  });

  testWidgets('İlan kutusu (15.10): tek paragraf talep metni → kayıt bağlantısı; "Cenaze yakını" düğmesi ve "veya" YOK', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await tester.pumpWidget(kapsamli(d, const IlanKutusu(il: 'Kars', ilce: 'Merkez')));
    await tester.pumpAndSettle();
    expect(find.text('Cenaze ilanınızın burada görülmesini istiyorsanız'), findsNothing); // eski başlık kalktı
    final bY = tester.getTopLeft(find.text('Cenaze ilanınızın bu sayfada görülmesini istiyorsanız bulunduğunuz bölgedeki din görevlisinden cenaze ilanınızı paylaşmasını talep edebilirsiniz.')).dy;
    final linkY = tester.getTopLeft(find.text('Din görevlisi misiniz? Kayıt olun.')).dy;
    expect(bY < linkY, isTrue); // tek paragraf → bağlantı
    expect(find.text('Cenaze yakını olarak ilanı paylaş'), findsNothing);
    expect(find.text('veya'), findsNothing);
    expect(find.byKey(const ValueKey('ilan_kutusu_veya')), findsNothing);
  });

  testWidgets('İlan kutusu: "Din görevlisi misiniz? Kayıt olun" kayıt ekranını açar (oturum varsa paneli)', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await tester.pumpWidget(kapsamli(d, const IlanKutusu(il: 'Kars', ilce: 'Merkez')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Din görevlisi misiniz? Kayıt olun.'));
    await tester.pumpAndSettle();
    expect(find.text(M.gorevliBaslik), findsWidgets);
    expect(find.text(M.gorevliEpostaAciklama), findsOneWidget); // kılavuz ekranı açıklaması (telefon alanı ekran dışında kalabilir: ListView tembel kurar)
  });

  testWidgets('Sekme çubuğu oturumsuz da 5 sekme (İlanlar · Sayfam · Dualar · Hatırla · Panel)', (tester) async {
    telefon(tester);
    final d = await testDurumu(onceki: {'il': 'Ordu', 'ilce': 'Ünye'});
    await tester.pumpWidget(KiminCenazesi(durum: d));
    await tester.pumpAndSettle();
    for (int i = 0; i < 5; i++) {
      expect(find.byKey(ValueKey('sekme_$i')), findsOneWidget);
    }
    expect(find.byKey(const ValueKey('sekme_5')), findsNothing);
    expect(find.text(M.sekmePanel), findsOneWidget);
    expect(M.sekmeler, ['İlanlar', 'Sayfam', 'Dualar', 'Hatırla']);
  });

  testWidgets('Şehit cenazesi: ilan kutusundaki bağlantı bilgi PENCERESİ açar (yalnız din görevlisi); form yok', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    await tester.pumpWidget(kapsamli(d, const IlanKutusu(il: 'Kars', ilce: 'Merkez')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('ilan_kutusu_sehit')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('sehit_bilgi_pencere')), findsOneWidget);
    expect(find.text(M.sehitBilgiBaslik), findsOneWidget);
    expect(find.text(M.sehitBilgiGovde), findsOneWidget);
    expect(find.text(M.sehitBilgiKapanis), findsOneWidget);
    expect(find.text('Şehit İlanı'), findsNothing); // form başlığı yok
    await tester.tap(find.text(M.aileBittiDugme));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('sehit_bilgi_pencere')), findsNothing);
  });

  testWidgets('Kart: aile kaydında rozet yok; Bildir akışı (Doğrulandı rozeti yok)', (tester) async {
    telefon(tester);
    Map<String, dynamic>? giden;
    final d = await testDurumu(
      istemci: MockClient((req) async {
        if (req.url.path == '/aile/bildir') {
          giden = jsonDecode(req.body) as Map<String, dynamic>;
          return http.Response(jsonEncode({'alindi': true}), 200, headers: {'content-type': 'application/json; charset=utf-8'});
        }
        return http.Response('yok', 404);
      }),
    );
    final r = Ilan.fromJson({
      'id': 'a1',
      'ad_soyad': 'Veli Örnek',
      'ilce': 'Merkez',
      'aile': true,
      'dogrulandi': true, // eski veri gelse bile rozet çıkmaz
      'namaz_tarihi': '2026-10-14',
    })!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Doğrulandı'), findsNothing);

    await tester.tap(find.text('Bu ilanda bir yanlışlık mı var?'));
    await tester.pumpAndSettle();
    expect(tester.widget<AnaDugme>(find.widgetWithText(AnaDugme, 'Bildirin')).onTap, isNull);
    await tester.tap(find.text('Bu ilan gerçek değil'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(AnaDugme, 'Bildirin'));
    await tester.pumpAndSettle();
    expect(giden, {'ilan_id': 'a1', 'neden': 'böyle bir kişi yok'});
    expect(find.text('Bildiriminiz alındı. Teşekkür ederiz.'), findsOneWidget);
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('Kartta aile alanı yoksa Bildir yok', (tester) async {
    telefon(tester);
    final d = await testDurumu();
    final r = Ilan.fromJson({'id': 'x', 'ad_soyad': 'Hasan Örnek', 'namaz_tarihi': '2026-10-14'})!;
    await tester.pumpWidget(kapsamli(d, IlanKarti(ilan: r)));
    await tester.pumpAndSettle();
    expect(find.text('Doğrulandı'), findsNothing);
    expect(find.text('Bu ilanda bir yanlışlık mı var?'), findsNothing); // Bildir yalnız aile kartlarında
  });
}
