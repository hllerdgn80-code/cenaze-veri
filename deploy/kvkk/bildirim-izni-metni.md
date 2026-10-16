# Bildirim izni — ilk açılış kartı için aydınlatma satırı

Ürün gerçeği (kod): bildirim telefonda üretilir; Firebase/sunucu yok; telefon arka planda seçilen ilin listesine bakar; konum alınmaz; "bölge" kullanıcının seçtiği il/ilçedir ve cihazda durur (`bildirim.dart`, `depo.dart`). Bildirim izni sunucumuza gönderilmez.

## Kartın metni (mevcut, değişmez)

> Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz?
> [Evet, haber verin] [Şimdi değil]

## Kartın altına eklenecek tek satır (küçük yazı)

> Bildirimler telefonunuzda hazırlanır; bunun için konumunuz ya da kişisel bilginiz alınmaz, yalnız seçeceğiniz il/ilçenin listesine bakılır. İzni istediğiniz zaman telefon ayarlarından kapatabilirsiniz. [Gizlilik]

(Uzun yol: "Gizlilik" bağlantısı `aydinlatma-metni.md §3` bölümüne gider.)

## Neden bu kadar yeter

- Bu işlemde veri sorumlusu olarak bizde kişisel veri **tutulmaz**; bildirim izni ve il/ilçe cihazda durur (cihazda kalan veri bizim işlememiz değildir). Bu nedenle ayrı açık rıza kutusu gerekmez; kullanıcının sorulan soruya "Evet" demesi izin akışıdır (Android bildirim izni ayrıca sistem tarafından sorulur).
- Kurum ilkesi: aydınlatma, verinin elde edilmesi sırasında yapılır ve anlaşılır, sade olmalıdır; işlemenin amacı belirli olmalıdır (Tebliğ md.5/g, ğ). Satır bunu tek cümlede karşılar.
- Din görevlisi hesabı varsa onay haberi de yerel bildirimle gelir; bu, hesap bölümünün (aydınlatma §4) kapsamındadır, ek metin gerekmez.

## Uygulamaya koyulacak

`uygulama/lib/cekirdek/metin.dart` — `izinSoru`, `izinEvet`, `izinHayir` yanına yeni sabit `izinAydinlatma` (yukarıdaki satır). Kodu bu görevde değiştirmedim.

---
**Dayanılan resmî belgeler:**
- Aydınlatma Tebliği md.5: https://www.resmigazete.gov.tr/eskiler/2018/03/20180310-5.htm
- Aydınlatma Yükümlülüğü: https://www.kvkk.gov.tr/Icerik/2033/Aydinlatma-Yukumlulugu-
