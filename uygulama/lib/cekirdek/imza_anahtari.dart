// YAYIN İMZASI AÇIK ANAHTARLARI (25.10.2026, GÜVENLİK PAKETİ madde 2). Açık anahtar GİZLİ DEĞİLDİR; gizli tohum (KC_IMZA_ANAHTARI)
// yalnız GitHub Actions secret'ında durur, diskte/depoda YOKTUR. Üretim: python3 araclar/imza_anahtar_uret.py (bu dosyayı kendisi yazar).
// BOŞ LİSTE = doğrulama KAPALI (geçiş dönemi: eski/imzasız veri gösterilir). Dolu liste = imzasız ya da bozuk veri GÖSTERİLMEZ.
// ANAHTAR DEĞİŞTİRME: önce yeni açık anahtarı BU LİSTEYE EKLE (eskisi kalsın), yeni uygulama sürümü yaygınlaşınca sunucudaki tohumu değiştir,
// eski anahtar bir sonraki sürümde listeden çıkar. Sırayı bozarsan eski sürümler "veri doğrulanamadı" der.
const List<String> kcImzaAcikAnahtarlar = <String>[];
