# e-Devlet'in arkasındaki kaynaklar (14.10.2026)

Bulgu 1: e-Devlet hizmet sayfaları ("... işbirliği ile e-Devlet Kapısı altyapısı üzerinden sunulmaktadır") arka sistemi ADLANDIRMIYOR; bağlantı da vermiyor. Asıl kaynağı belediyenin kendi sitesinde aramak gerekti.
Bulgu 2: Açık veri portalları (İBB CKAN 'vefat/mezarlık/defin/cenaze': yalnız "Mezarlık adres bilgileri"; İzmir acikveri: 0; Bursa/Kocaeli: ulaşılamadı) kişi listesi YAYIMLAMIYOR. Mobil uygulama API'si keşfi yapılmadı (anonim, belgelenmiş uç yok).
Bulgu 3: Tek yeni, açık, listelenebilir il geneli kaynak: **Tekirdağ BB "Vefat Edenler - Güncel liste"**.

| İl/hizmet | Asıl kaynak URL | Erişim | Günlük kayıt | Alanlar | Lisans/robots | Yazılabilir |
|---|---|---|---|---|---|---|
| Tekirdağ BB | tekirdag.bel.tr/merhumlar | AÇIK (girişsiz, CAPTCHA yok; robots.txt 404) | ~12/gün (yalnız güncel gün) | ad, ilçe, vakit+tarih, cami, mezarlık | lisans belirtilmemiş; olgu verisi | EVET (yazıldı) |
| İstanbul BB | ibb.istanbul yalnız "cenaze işlemleri nasıl yapılır"; cenaze./mezarlik(lar).ibb.istanbul DNS yok | liste yok | - | - | - | HAYIR |
| İzmir BB | cbs.izmir.bel.tr/CbsUygulamalar/MezarlikBilgiSistemi (Mevta/Vefat Bilgisi Sorgulama) | açık ama AD+SOYAD ZORUNLU (kişi sorgusu) | liste yok | - | robots yok | HAYIR |
| Bursa BB | bursa.bel.tr/mezarlik-bilgi-sistemi "Bugün Defnedilenler" | açık | zaten okunuyor (bursa.py) | - | - | MEVCUT |
| Sakarya BB | mebis.sakarya.bel.tr/BugunVefatEdenler | CAPTCHA | - | - | - | HAYIR (dolanılmaz) |
| Kocaeli BB | ebelediye.kocaeli.bel.tr/sosyalhizmetler/vefatlistesi | açık | zaten okunuyor; mezarlik.kocaeli.bel.tr SSL süresi dolmuş | - | - | MEVCUT |
| Diyarbakır BB | mezarlik.diyarbakir.bel.tr (MEBİS) | açık ama yalnız "Mezar Ara" (ad/soyad, mezarlık) | liste yok; /BugunVefatEdenler 404 | - | - | HAYIR |
| Erzurum BB | erzurum.bel.tr/cenaze-hizmetleri | yalnız bilgi sayfası | liste yok | - | - | HAYIR |
| İstanbul ilçeleri (Pendik, Bağcılar, Üsküdar, Küçükçekmece, Bahçelievler, Kağıthane, Beylikdüzü, Gaziosmanpaşa, Tuzla, Arnavutköy) | ana sayfa bağlantıları ve /vefat-edenler denemeleri | liste sayfası yok (404/500/yönlendirme); Sultangazi ve Büyükçekmece sitesi açılmadı | - | - | - | HAYIR (Silivri/Arnavutköy zaten istanbul.py'de) |

## Yapılan
`okuyucu/tekirdag.py` 3. kaynak "Büyükşehir" (slug `tekirdag-bb`): Süleymanpaşa ve Muratlı satırları çift kayıt olmasın diye atlanır. Test (Mac terminal; sandbox SSL zinciri hatası verir): önce 0 kayıt, sonra 14.10 için 8 kayıt (12 satırın 4'ü Süleymanpaşa); 8 kaydın ilçe/mezarlık alanı gözle doğru; 1 kayıtta ilçe boş (merkez) -> `ilce_belirsiz: true`. Kişi adı/ölüm nedeni/yakın bilgisi alınmaz.
Kapı: kaynak_turu diğer Tekirdağ okuyucularıyla aynı (None); `tekirdag-bb` için ayrı kapı kaydı gerekiyorsa kapi.py'deki resmî/YEREL_BASIN listesine eklenmeli (dokunulmadı). hepsi.py'de tekirdag zaten var. Liste yalnız güncel günü gösterdiği için günde en az 1 koşu gerekir (saatlik cron'a eklenebilir, 1 istek).
## Sonuç
e-Devlet'e yük bindirmeden yeni il geneli kaynak: yalnız Tekirdağ BB. Diğer büyükşehirlerde (İBB, İzmir, Diyarbakır) belediyenin kendi sistemi de kişi sorgusu; liste yalnız e-Devlet/ilçe sitelerinde. İstanbul/İzmir için kalan yol: ilçe belediye sitelerindeki ilan sayfaları (tek tek keşif).
