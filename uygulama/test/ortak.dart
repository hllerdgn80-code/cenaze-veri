// Testler için ortak kurulum: sahte ağ (MockClient), bellek içi cihaz deposu, küçük gömülü veri.
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:kimin_cenazesi/cekirdek/cinsiyet.dart';
import 'package:kimin_cenazesi/cekirdek/depo.dart';
import 'package:kimin_cenazesi/cekirdek/durum.dart';
import 'package:kimin_cenazesi/cekirdek/veri.dart';
import 'package:kimin_cenazesi/cekirdek/yardimci.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Yayın biçiminde örnek il verisi (kişiler kurgusaldır). Kaynak alanı YOK (yayın süzgeci soymuş).
Map<String, dynamic> ornekOrdu(String bugun) => {
      'il': 'Ordu',
      'guncelleme': '${bugun}T09:02:00+03:00',
      'toplam': 2,
      'ilceler': {
        'Ünye': [
          {
            'id': 'ornek1',
            'il': 'Ordu',
            'ilce': 'Ünye',
            'mahalle': 'ÖRNEK MAHALLESİ',
            'ad_soyad': 'Ahmet Örnekoğlu',
            'yas': 67,
            'vefat_tarihi': gunEkle(bugun, -1),
            'defin_yeri': 'ÖRNEK MEZ.',
            'defin_zamani': null,
            'namaz_tarihi': bugun,
            'namaz_yeri_vakti': 'Öğle Namazını Müteakip-ÖRNEK CAMİİ',
            'liste_tarihi': bugun,
            'il_disi_defin': null,
          },
        ],
      },
      'ilce_belirsiz': [],
      'il_disi': [],
    };

Gomulu testGomulu() => Gomulu(
      ilceler: const {
        'Kars': ['Merkez', 'Sarıkamış'],
        'Ordu': ['Altınordu', 'Ünye'],
      },
      cinsiyet: CinsiyetCozucu(erkek: const ['Ahmet', 'Mehmet'], kadin: const ['Ayşe', 'Fatma']),
    );

/// Sahte ağ: Ordu → örnek veri; diğer iller → 404 (kaynaksız il)
http.Client sahteAg(String bugun) => MockClient((req) async {
      if (req.url.path.endsWith('/ordu/son7gun.json')) {
        return http.Response.bytes(utf8.encode(jsonEncode(ornekOrdu(bugun))), 200,
            headers: {'content-type': 'application/json; charset=utf-8'});
      }
      return http.Response('yok', 404);
    });

Future<AppDurum> testDurumu({Map<String, Object> onceki = const {}}) async {
  SharedPreferences.setMockInitialValues(onceki);
  final depo = await Depo.ac();
  final veri = VeriServisi(istemci: sahteAg(bugunTr()), depo: depo);
  return AppDurum(depo: depo, veri: veri, gomulu: testGomulu());
}
