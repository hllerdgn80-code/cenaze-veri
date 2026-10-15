// Veri kapısı anahtarı (14.10.2026, URUN-TASLAGI §16). Worker'daki KC_ANAHTAR secret'ı ile AYNI olmalı.
// Depoda YER TUTUCU durur; gercek anahtar GitHub secret KC_ANAHTAR (ve yerelde deploy/.kc-anahtar). Depo public iken sizinti olmasin (14.10.2026).
const String kcSurum = '0.1.4';
const String kcAnahtar = 'YERTUTUCU_CI_SECRET_KC_ANAHTAR';   // CI (android.yml) derlemede secrets.KC_ANAHTAR ile degistirir; gercek deger depoda DURMAZ

/// Veri kapısına (veri.kimincenazesi.com) ve aile Worker'ına giden her isteğin ortak başlıkları.
Map<String, String> kcBasliklar() => const {
      'X-KC-Anahtar': kcAnahtar,
      'User-Agent': 'KiminCenazesi/$kcSurum',
    };
