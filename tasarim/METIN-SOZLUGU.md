# Kimin Cenazesi — Ekran Metinleri Sözlüğü (08.10.2026)

Bağlayıcı kural (site sahibi): **"Cenaze konusunda seçeceğimiz her kelime hassas olmalı."** Dil ilkesi: `URUN-TASLAGI.md §22`.
Süzgeç (her yeni metin buradan geçer):
1. Pazar/satış dili yok: "yeni", "fırsat", "kaçırma", "hemen", "son dakika", ünlem (!).
2. Sayı yok: ölüm/ilan/kişi sayısı yazılmaz ("3 ilan", "Altınordu · 3", "245 kişi" yok). İzinli sayılar: tarih, yaş, fiyat (200 ₺), adım (Adım 2 / 5), kullanıcının KENDİ okuma sayaçları.
3. "İlan" yerine mümkün olan yerde: vefat, cenaze, uğurlama, merhum/merhume, rahmetli, Hakk'a yürüdü. "İlan" yalnız ürün adı ve belge anlamında kalır ("cenaze ilanı", "vefat ilanı").
4. Emir değil davet: "-ın/-in" nezaket kipi ("bakabilirsiniz", "görün", "paylaşın"), soru ("haber verelim mi?").
5. Başsağlığı ölçülü: "Başınız sağ olsun", "Allah rahmet eylesin"; abartı yok.
6. Kaynak adı (belediye, site) HİÇBİR metinde geçmez (§16.5).
7. Bildirim içerik vermez: ad, cami, saat, sayı yok.
9. **Merhum / merhume (site sahibi, bağlayıcı):** erkek için "merhum", kadın için "merhume"; cinsiyet bilinen her kişiye bağlı metinde ayrım yapılır: merhum/merhume · merhuma/merhumeye · merhumun/merhumenin. Cinsiyet kaynağı: (a) ilan verenin formda seçtiği cinsiyet — kesin, tahmin yok; (b) belediye kayıtlarında tek fonksiyon `prototip_yap.py → cinsiyet_coz`: kaynaktaki cinsiyet → ad listesi → yok (yoksa kullanıcı Sayfam'da "Merhum mu, merhume mi?" ile seçer). Bilinmiyorsa nötr kalıp: "vefat eden yakınınız", "vefat eden"; sayaçlarda "1 Fâtiha okudum" ve ilk dokunuşta "Merhum mu, merhume mi?" sorusu. ASLA yanlış cinsiyet yazılmaz. Genel/kişisiz metinlere (ör. sahibin "Merhuma ait bilgileri buraya ekleyebilirsiniz.") dokunulmaz.
8. Onay dili yok: "elle onay", "moderatör onayı", "görevli onayı" yazılmaz → "kontrol edilir", "kontrolden sonra yayımlanır" (site sahibi 08.10.2026). Kullanıcının kendi onayı ("Onayla ve gönder", "Okudum, kabul ediyorum") bu kuralın dışındadır.

Simge: ✎ = prototipteki metin değiştirildi (eski → yeni) · ＋ = yeni metin · ✓ = olduğu gibi kaldı.
Yer tutucular: `{il}`, `{ilce}`, `{yer}` (ilçe, yoksa il), `{yer’de}` (bulunma eki ile: Ünye’de, Kars’ta, Aybastı’da — kod: `ek()`), `{tarih}`, `{ad}`.

---

## 1. Açılış ve adres seçimi
| Anahtar | Metin | Durum · neden |
|---|---|---|
| acilis.marka | Kimin Cenazesi | ✓ |
| acilis.alt | Bulunduğunuz ili seçin | ✓ davet, kısa |
| il.ara | İl ara | ✓ yer tutucu |
| il.satir.sayi | *(boş)* | ✎ "Ordu 98" → sayı kaldırıldı · ölüm sayısı listede durmaz |
| il.bos | Bu adla bir il bulunamadı | ✎ "İl bulunamadı" → tam cümle, yumuşak |
| ilce.ust | İlçe seçin | ✓ |
| ilce.geri | İller | ✓ |
| ilce.ara | İlçe ara | ✓ |
| ilce.tumu | Tüm ilçeler | ✓ |
| ilce.satir.sayi | *(boş)* | ✎ ilçe başına ilan sayısı kaldırıldı |
| ilce.bos | Bu adla bir ilçe bulunamadı | ＋ |
| ilce.prototip-notu | Bu prototipte örnek kayıtlar Ordu için, verisi olmayan il örneği ise Kars, Tunceli ve Kilis için yüklendi. Uygulamada her ilin ilçeleri burada listelenir. | ✎ yalnız prototipte |
| ilce.prototip-dugme | Ordu örneğini açın · Kars örneğini açın | ✎ "Ordu örneğini aç" → davet kipi |

## 2. Cenaze İlanları (ana ekran)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| ilanlar.ust | Cenaze İlanları | ✓ ürün adı |
| ilanlar.konum | {il} · {ilce} | ✓ dokununca adres seçimi |
| serit.bugun | Bugün | ✓ |
| bolum.ilce | {ilce} | ✎ "Altınordu · 3" → sayı kaldırıldı |
| bolum.ilgeneli | İl geneli (ilçe belirtilmemiş) | ✓ |
| bolum.gecmis-gun | {tarih} {haftagünü} (ör. "4 Ekim Pazar") | ＋ son 7 gün kendiliğinden açıldığında |
| kart.ust | Cenaze · {cenaze günü} · {vakit} (ör. "Cenaze · 4 Ekim · Öğle") | ✎ "Vefat · {tarih} · {yaş} yaş" → üst etiket artık tarih şeridindeki günle AYNI (cenaze namazı günü; yoksa defin, o da yoksa liste tarihi). Site sahibi 08.10.2026: 4 Ekim sekmesinde "Vefat · 2 Ekim" yazan kart kafa karıştırdı |
| kart.vefat | Vefat: {tarih yıl} · {yaş} yaş (ör. "Vefat: 2 Ekim 2026 · 67 yaş") | ＋ adın altında küçük satır |
| kart.anne-baba | *(gösterilmez)* | ✎ kaldırıldı · URUN-TASLAGI §28: kartta anne/baba adı yok (iç veride kalır; yayın süzgeci soyar) — 08.10.2026 uçtan uca denetim |
| kart.namaz | Cenaze namazı | ✓ |
| kart.defin | Defin | ✓ |
| kart.kaydet | Sayfama kaydet | ✓ site sahibinin ifadesi (§17) |
| kart.kaydedildi | Sayfamda ✓ | ✓ |
| kart.yakini | Yakını paylaştı | ＋ aile formuyla gelen ilan; kaynak adı yazılmaz (§21) |
| kart.kaldir | Sayfamdan kaldır | ＋ Sayfam kartının ⋮ menüsü; site sahibi isteği |
| kaldir.soru | Bu kaydı sayfanızdan kaldırmak istiyor musunuz? | ＋ sakin, ünlemsiz |
| kaldir.vazgec / kaldir.tamam | Vazgeç / Kaldır | ＋ |
| bildirim.kaldirildi | Sayfanızdan kaldırıldı | ＋ |
| bildirim.bellek | Eklendi. Bu önizlemede kayıt sayfa kapanınca silinir | ＋ yalnız localStorage yoksa (file://, sandbox önizleme) |
| bildirim.kaydedildi | Sayfanıza eklendi | ✎ "Sayfanıza kaydedildi" → merhum "eklenir", dosya gibi "kaydedilmez" |
| bos.bugun.baslik | Bugün {yer’de} cenaze ilanı bulunmuyor | ✎ "Bu gün için ilan yok" → site sahibinin kalıbı (§21.4) |
| bos.bugun.aciklama | Son yedi günün cenaze ilanları aşağıda. | ＋ son 7 gün kendiliğinden açılır |
| bos.gecmis.baslik | Bu tarihte cenaze ilanı bulunmuyor | ✎ "Bu gün için ilan yok" |
| bos.gecmis.aciklama | {tarih} · {yer} | ✎ "…için kayıtlı cenaze ilanı bulunmuyor." → "kayıtlı" (bürokratik) çıktı, davet eklendi |
| bos.ilgeneli | Bu tarihte ilçesi belirtilmemiş cenaze ilanı bulunmuyor. | ✎ "Bu gün için ilçesi belirtilmemiş ilan yok." |

## 3. Verisi olmayan il (§21.3) — YENİ EKRAN
| Anahtar | Metin | Durum · neden |
|---|---|---|
| kaynaksiz.baslik | {il’de} cenaze ilanları şu an yakınları tarafından paylaşılıyor. | ＋ site sahibinin kalıbı (ör. "Kars’ta…"); "yok" demez, olanı söyler |
| kaynaksiz.aciklama | Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra burada görünür. | ＋ |
| kaynaksiz.dugme | Cenaze ilanı paylaş | ＋ site sahibinin ifadesi |
| kaynaksiz.bolum.bugun | Bugün | ＋ aile ilanı varsa |
| izin.soru | Bölgenizde cenaze olduğunda size haber vermemizi ister misiniz? | ＋ site sahibinin metni (§36, 15.10.2026; ilk açılış kartı) |
| izin.evet | Evet, haber verin | ＋ |
| izin.hayir | Şimdi değil | ＋ |
| izin.evet.bildirim | Bölgenizdeki cenazeler için sabahları haber vereceğiz | ＋ |
| izin.verilmedi | Bildirim izni verilmedi. Telefonunuzun ayarlarından açabilirsiniz. | ＋ menüden açarken sistem izni reddedilirse |
| menu.bildirim | Cenaze bildirimini aç · Cenaze bildirimini kapat | ＋ §36 aç-kapa |
| izin.hayir.bildirim | Bildirim gönderilmeyecek | ＋ |
| (yok) | — | Komşu il gösterimi YOK; Tarihte Bugün / Kaybettiklerimiz şeritleri de YOK (site sahibi 08.10.2026: o ile ait sanılıyor; basitlik ilkesi §26) |

## 4. Aile formu — "Cenaze ilanı paylaş" (ücretsiz; §15 adımları) — YENİ
| Anahtar | Metin | Durum · neden |
|---|---|---|
| aile.baslik | Cenaze İlanı | ＋ |
| aile.ust.giris | Cenaze bilgisi paylaşımı | ✎ "Ücretsiz paylaşım" → "ücretsiz" kelimesi uygulamada geçmez (08.10.2026 denetim) |
| aile.giris.baslik | Cenaze ilanı paylaşın | ＋ |
| aile.giris.aciklama | Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra {il} sayfasında görünür. | ＋ |
| aile.giris.etiket | Yakınlar için | ✎ "Ücretsiz" → aynı neden |
| aile.giris.not | Yalnız vefat edenin yakınları paylaşabilir | ✎ "Yalnız merhumun yakınları…" → cinsiyet bilinmiyor, nötr |
| aile.giris.madde1–4 | Ölüm belgesi e-Devlet koduyla doğrulanır · Telefonunuz SMS ile doğrulanır · Kontrolden sonra il ve ilçe sayfasında görünür · Belge dosyası saklanmaz | ＋ |
| aile.alan.mahalle | Mahalle — yer tutucu: Mahallesi (eski: "Merhumun mahallesi"; cinsiyet bilinmiyor) | ＋ (Âyet/dua alanı aile formunda yok) |
| aile.adim5 | Adım 5: Yasal beyan ve ödeme → aile formunda düğme "Onayla ve gönder", ödeme satırı yok | ＋ |
| aile.not | İlanınız kontrolden sonra yayımlanır. | ＋ |
| aile.bitti.ust | Gönderildi | ＋ |
| aile.bitti.baslik | İlanınız alındı | ＋ |
| aile.bitti.aciklama | İlan kontrolden sonra {il} sayfasında yayımlanır. Başınız sağ olsun. | ＋ ölçülü başsağlığı |
| aile.bitti.dugme | Tamam | ＋ |

## 5. Ortak form metinleri (Tam Sayfa + aile)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| form.ust | Adım {n} / 5 | ✓ |
| form.devam | Devam | ✓ |
| adim1.baslik | Vefat eden yakınınızın bilgileri | ✎ "Merhumun bilgileri" → form doldurulurken cinsiyet bilinmiyor, nötr kalıp |
| adim1.aciklama | Bilgiler ilanda göründüğü biçimde yayımlanır. | ✓ |
| alan.cinsiyet | Vefat eden — Erkek · Kadın | ＋ ZORUNLU, 1. adımın başında, iki eşit düğme; seçim kayda `cinsiyet` olarak yazılır, kart/sayaç/bildirim merhum–merhume buna göre (tahmin yok; Cihan, Deniz gibi iki cinsiyette kullanılan adlar yüzünden). Aile formu, Tam Sayfa ve şehit formunda |
| alan.ad.yer-tutucu | Merhumun adı ve soyadı (Erkek seçilince) · Merhumenin adı ve soyadı (Kadın) · Adı ve soyadı (seçim yapılmadan) · Şehidimizin adı ve soyadı (şehit formu) | ＋ |
| alan.ad | Ad soyad — Adı ve soyadı | ✎ yer tutucu "Merhumun adı ve soyadı" → nötr |
| alan.anne / alan.baba | Anne adı · Baba adı | ✓ |
| alan.vefat | Vefat tarihi | ✓ |
| alan.namaz | Namaz vakti — Öğle namazı · İkindi namazı · Cuma namazı · Saat belirt | ✓ |
| alan.il / alan.ilce | İl · İlçe | ✓ |
| alan.cami | Cami — Cenaze namazının kılınacağı cami | ✓ |
| alan.mezarlik | Mezarlık — Defin yeri | ✓ |
| alan.ayet | Âyet / dua (yalnız Tam Sayfa) | ✓ |
| adim2.baslik | Ölüm belgesi doğrulama | ✓ |
| adim2.aciklama | e-Devlet’ten aldığınız Ölüm Belgesi’nin doğrulama kodunu girin. Belge dosyası saklanmaz. | ✓ |
| adim2.alan | Belge doğrulama kodu — Örn. ABCD-1234-EFGH | ✓ |
| adim2.dugme | Belgeyi doğrula | ✓ |
| adim2.tamam | Belge doğrulandı | ✓ |
| adim3.baslik | Telefon doğrulama | ✓ |
| adim3.aciklama | Kimliğiniz SMS ile doğrulanır. Tam T.C. kimlik numaranız saklanmaz. | ✎ "İlanı veren yakının kimliği…" → doğrudan kişiye hitap |
| adim3.ad | Ad soyad — Adınız ve soyadınız | ✎ yer tutucu "İlanı veren" |
| adim3.tc / yakinlik | T.C. son 4 hane · Yakınlık (Oğlu / kızı · Eşi · Kardeşi · Torunu · Gelini / damadı · Diğer) | ✓ |
| adim3.tel | Cep telefonu — 05xx xxx xx xx | ✓ |
| adim3.sms | SMS kodu gönder · Kodu yeniden gönder · 6 haneli kod | ✓ |
| adim3.tamam | Telefon doğrulandı | ✓ |
| adim4.baslik | Bilgilerin denetimi | ✎ "Tutarlılık denetimi" → teknik terim çıktı |
| adim4.aciklama | Bilgileriniz yayından önce kontrol edilir. | ✎ "…otomatik olarak denetlenir ve moderatör onayına gider." |
| adim4.maddeler | Ölüm belgesindeki ad soyad ilanla eşleşiyor · Başvuranın soyadı / anne-baba adı eşleşiyor · Cami ve mezarlık seçilen ilçede kayıtlı · Defin tarihi vefattan en çok 3 gün sonra · Aynı kişi için ikinci ilan yok | ✓ |
| adim4.onay | Kontrol · genellikle 30 dakika içinde | ✎ "Moderatör onayı · hedef süre 30 dakika" |
| adim5.aciklama | Lütfen aşağıdaki metni okuyun. | ✓ |
| hukuk.baslik | YASAL UYARI — Yanlış beyanın cezai sorumluluğu vardır | ✓ |
| hukuk.metin | Verdiğim bilgilerin doğru ve eksiksiz olduğunu, ilanı vermeye yetkili yakın olduğumu kabul ve beyan ederim. Yanıltıcı, gerçek dışı veya başkasının hakkını ihlal eden bilgi vermem hâlinde 5237 sayılı Türk Ceza Kanunu’nun ilgili hükümleri (m. 206 resmî belgenin düzenlenmesinde yalan beyan, m. 267 iftira, m. 136 kişisel verileri hukuka aykırı olarak verme) uyarınca hakkımda hukuki ve cezai işlem başlatılmasını, ilanın derhal kaldırılmasını ve hesabımın kalıcı olarak kapatılmasını kabul ediyorum. | ✓ site sahibinin hukuki metni (§17); bilerek sert, değiştirilmedi |
| hukuk.kutu | Okudum, kabul ediyorum. | ✓ |
| bildirim.kod-eksik | Lütfen kodu eksiksiz yazın | ✎ "Kodu eksiksiz girin" |
| bildirim.tel-eksik | Lütfen telefon numaranızı yazın | ✎ "Telefon numarasını girin" |
| bildirim.kod-gitti | Doğrulama kodu gönderildi | ✎ "Kod gönderildi" |

## 6. Tam Sayfa (ücretli vefat ilanı)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| tam.ust | Türkiye geneli | ✓ |
| tam.baslik | Tam Sayfa | ✎ "Tam Sayfa İlan" → "ilan" tekrarı azaltıldı |
| tam.dugme | Vefat ilanı hazırlayın | ✎ "İlan ver" (+ artı simgesi) → satış çağrısı değil davet; simge kaldırıldı |
| tam.bolum | Yayımlanan vefat ilanları | ✎ "Yayımlanan ilanlar" |
| tam.ornek | ÖRNEK | ✓ prototip |
| tam.harita | Cami · haritada aç · Mezarlık · haritada aç | ✓ |
| form.tam.baslik | Vefat İlanı | ✎ "İlan ver" |
| form.tam.ust | Tam sayfa | ✎ "Tam sayfa ilan" |
| fiyat.baslik | Tam sayfa vefat ilanı | ✎ "Tam sayfa cenaze ilanı" → gazete geleneğindeki ad |
| fiyat.aciklama | Gazetedeki vefat ilanının uygulamadaki karşılığı. | ✓ |
| fiyat.etiket | Tek seferlik | ✓ |
| fiyat.tutar | 200 ₺ | ✓ |
| fiyat.not | Abonelik değildir, bir kez ödenir | ✓ |
| fiyat.madde1 | Türkiye genelinde görünür | ✎ "Ülke genelinde görünür" |
| fiyat.madde2 | Metni sizinle birlikte hazırlanır | ✎ "Metin ve tasarım bizden" → reklam sloganı tınısı çıktı |
| fiyat.madde3 | Cami ve mezarlık haritada gösterilir | ✎ "Cami ve mezarlık haritada" |
| fiyat.madde4 | Yayından önce doğrulanır ve kontrol edilir | ✓ |
| adim5.tam.baslik | Yasal beyan ve ödeme | ✓ |
| adim5.tam.tutar | Ödenecek: 200 ₺ | ✓ |
| adim5.tam.dugme | Ödemeye geç | ✓ |
| adim5.tam.not | İlanınız ödeme ve kontrolden sonra yayımlanır. | ✎ "İlan, ödemeden sonra moderatör onayıyla yayımlanır." |
| odeme.baslik | Ödeme — Mağaza içi satın alma | ✓ |
| odeme.urun | Tam sayfa cenaze ilanı — Kimin Cenazesi · tek seferlik satın alma | ✓ mağaza ürün adı |
| odeme.satir | Tutar 200,00 ₺ · Hesap · Yayın: Kontrolden sonra | ✎ "Moderatör onayından sonra" |
| odeme.dugme | Ödemeyi onayla | ✎ "Satın al" → alışveriş dili çıktı |
| odeme.not | Gerçek uygulamada bu ekranı App Store / Google Play açar; ödeme bilgisi uygulamaya gelmez. | ✓ prototip |

## 7. Sayfam
| Anahtar | Metin | Durum · neden |
|---|---|---|
| sayfam.ust | Rahmetle anıyoruz | ✓ |
| sayfam.baslik | Sayfam | ✓ |
| sayfam.bos.baslik | Sayfanızda henüz kimse yok | ✎ "Sayfanız boş" → merhumlar "boşluk" değildir |
| sayfam.bos.aciklama | Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez. | ✎ "…bir ilanı buraya ekleyin. Kaydettiğiniz ilanlar silinmez…" → kişi merkezli, davet |
| sayac.fatiha | Merhuma / Merhumeye 1 Fâtiha okudum | ✓ site sahibinin ifadesi; "1" kullanıcının kendi okuması (ölüm sayısı değil) |
| sayac.ihlas | Merhuma / Merhumeye / (nötr) 3 İhlâs ve 1 Fâtiha okudum | ＋ site sahibi isteği; Fâtiha'dan sonra 2. satır, uzun cümle iki satıra ortalı iner |
| sayac.yasin | Merhuma / Merhumeye 1 Yâsîn okudum | ✓ |
| sayac.dua | Merhuma / Merhumeye 1 dua okudum | ✓ |
| sayac.hatim | Merhuma / Merhumeye 1 Kur’ân-ı Kerîm hatmi okudum | ✓ |
| sayac.tevhid | Merhuma / Merhumeye 1 Kelime-i Tevhid hatmi okudum | ✓ |
| sayac.cinsiyetsiz | 1 Fâtiha okudum (…) | ✓ cinsiyet bilinmeyince |
| sayac.geri | −1 (erişilebilirlik: "Geri al") | ✓ |
| cins.soru | Merhum mu, merhume mi? — Merhum · Merhume | ✓ |
| sayac.toplam | Okuduklarınızın toplamı: {n} | ✎ "Bu sayfada toplam {n} okuma" → kart merhuma aittir, "sayfa" değil |

## 8. Kaybettiklerimiz ve Tarihte Bugün
| Anahtar | Metin | Durum · neden |
|---|---|---|
| hatirla.ust / baslik | Rahmetle anıyoruz · Hatırla | ＋ |
| hatirla.kutu | Kaybettiklerimiz · Tarihte Bugün | ＋ iki kutucuk |
| kay.ust / kay.baslik | Rahmetle anıyoruz · Kaybettiklerimiz | ✓ (sol düğme: Hatırla’ya geri) |
| kay.kutu | Cumhurbaşkanları · Başbakanlar · Bakanlar · Siyasetçiler · Sanat, Edebiyat ve Bilim | ✎ "Sanatçılar" → kapsam genişledi (site sahibi 08.10.2026) |
| kay.kutu.sayi | *(boş)* | ✎ "245 kişi" → kaldırıldı |
| kay.liste.ust | Rahmetle anıyoruz | ✎ "{n} kişi · en yeniden" → sıralama ölçütünü anlatan not kullanıcıya gösterilmez (site sahibi 08.10.2026) |
| kay.ara | Ad ara | ✓ |
| kay.bos | Bu adla bir kayıt bulunamadı | ✎ "Sonuç yok" |
| kay.daha | Devamını gösterin | ✎ "Daha fazla göster ({n})" → sayı ve "daha fazla" çıktı |
| kisi.rozet | YIL · YAŞ | ✎ "SIRA" rozeti ve liste numarası (1., 2.) kaldırıldı — sıralama izlenimi veriyordu |
| kisi.gorev | {n}. Cumhurbaşkanı · {n}. Başbakan | ＋ yalnız görev sırası; altın renkte |
| kisi.tanitim | {Meslek — Sanat, Edebiyat ve Bilim’de en çok 3, virgülle, en bilinen önce (ör. "Şarkıcı, oyuncu, besteci"); diğer kategorilerde yalnız ilki, tek kimlik; görev satırındaki kelime tekrar edilmez} · {neden tanınır} (ör. "Sinema oyuncusu · Yeşilçam'ın güldürü ustası") | ＋ veri yoksa yalnız ad ve tarihler; "Vikipedi'de N dilde…" gibi yöntem izi taşıyan parçalar gösterilmez |
| kisi.ust | Vefat · {tarih} | ✓ |
| kisi.kabir | *(gösterilmez)* | ✎ "Mezarı: {il}" / "Mezar yeri bilinmiyor" → kabir bilgisi kartta hiç yer almaz (site sahibi 08.10.2026) |
| tb.ust | {gün ay} · hayatını kaybedenler | ✓ |
| tb.baslik | Tarihte Bugün | ✓ |
| tb.bolum | Türkiye · Dünya | ✎ "Türkiye · {n}" / "Dünya · {n}" → sayı kaldırıldı |

## 8b. Dualar ve Âyetler (§26) — YENİ SEKME
Kural: Arapça (varsa) + okunuş + sade anlam (kendi çevirimiz; Diyanet meali birebir alınmaz) + kaynak satırı. Menkıbeler kendi cümlelerimizle özettir.
| Anahtar | Metin | Durum |
|---|---|---|
| dua.sekme | Dualar | ＋ |
| dua.ust / baslik | Rahmetle anıyoruz · Dualar ve Âyetler | ＋ |
| dua.kutu | Ölümle ilgili âyetler · Hadisler · Menkıbeler · Vefat eden yakınlarımız için dualar | ＋ |
| dua.panel | Ölümle ilgili · Âyetler / Hadisler / Menkıbeler — Vefat eden yakınlarımız için · Dualar (kısa başlık, üst etiket) | ＋ |
| ayet.1 | Bakara 2:156 — Başlarına bir musibet geldiğinde “Biz Allah’a aitiz ve O’na döneceğiz” derler. · Kur’ân-ı Kerîm · Bakara 2:156 | ＋ |
| ayet.2 | Âl-i İmrân 3:185 — Her can ölümü tadacaktır. · (âyetin ilk cümlesi) | ＋ |
| ayet.3 | Ankebût 29:57 — Her can ölümü tadacaktır; sonra bize döndürüleceksiniz. | ＋ |
| hadis.1 | Dünyada bir yolcu gibi — Buhârî, Kitâbü’r-Rikâk (6416) | ＋ |
| hadis.2 | Cenazenin ardından gitmek — Buhârî, Kitâbü’l-Cenâiz (1240) | ＋ |
| hadis.3 | Kabir ziyareti ölümü hatırlatır — Müslim, Kitâbü’l-Cenâiz (976) | ＋ |
| menkibe.1 | Hz. Ömer: Kendinizi hesaba çekin — Tirmizî, Sıfatü’l-Kıyâme (2459’un ardından) | ＋ |
| menkibe.2 | İmam Gazâlî’nin son sabahı — İbnü’l-Cevzî, es-Sebât inde’l-memât (özet) | ＋ |
| menkibe.3 | Mevlânâ ve “düğün gecesi” — Eflâkî, Menâkıbü’l-Ârifîn (özet) | ＋ |
| dua.1 | Cenaze namazı duası — Müslim, Kitâbü’l-Cenâiz (963), Avf bin Mâlik rivayeti | ＋ |
| dua.2 | Kabir ziyareti duası — Müslim, Kitâbü’l-Cenâiz (975) | ＋ |
| dua.3 | Fâtiha ve Yâsîn — “Vefat eden yakınlarımız için Fâtiha ve Yâsîn okumak Anadolu’da köklü bir gelenektir.” | ＋ |

## 8c. Şehit ilanları (§27)
Kural: "vefat etti" / "Hakk’a yürüdü" YAZILMAZ → "şehit oldu". Ölüm nedeni yazılmaz. Bayrak/ay-yıldız yok; yalnız kartın üstünde ince al şerit (#E30A17, paletteki tek istisna). Şehit ilanı o gün listenin EN ÜSTÜNDE.
| Anahtar | Metin | Durum |
|---|---|---|
| sehit.etiket | ŞEHİT | ＋ al zemin üstünde beyaz |
| sehit.ust | Cenaze töreni · {tören günü} · {vakit} | ＋ sekme günüyle aynı |
| sehit.vefat | Şehit oldu: {tarih yıl} · {yaş} yaş | ＋ adın altında küçük satır |
| sehit.ad | {Rütbe} {Ad Soyad} (ör. "Piyade Uzman Çavuş Örnekalp Yıldırımhan") | ＋ rütbe adın başında |
| sehit.hitap | Şehidimiz {Rütbe Ad Soyad} | ＋ metin içinde anarken |
| sehit.toren | Cenaze töreni — {tören yeri} | ＋ |
| sehit.namaz / defin | Cenaze namazı — {vakit, cami, gün} · Defin — {şehitlik} | ＋ |
| sehit.kapanis | Ruhu şad olsun, mekânı cennet olsun. | ＋ |
| sehit.bolum | Şehidimiz | ＋ tüm ilçeler görünümünde listenin başı |
| sehit.sayac | Şehidimize 1 Fâtiha okudum (Yâsîn, dua, Kur’ân-ı Kerîm hatmi, Kelime-i Tevhid hatmi) | ＋ cinsiyet kalıbı yerine |
| sehit.tam.dugme | Şehidimiz için ilan hazırlayın | ＋ Tam Sayfa ekranı |
| sehit.form.baslik / ust | Şehit İlanı · Adım {n} / 5 | ＋ form doğrudan 1. adımla açılır; ücret söz konusu edilmez |
| sehit.adimlar | Şehidimizin bilgileri · Resmî duyuru doğrulaması · Telefon doğrulama · Bilgilerin denetimi · Yasal beyan | ＋ |
| sehit.alan | Rütbe / unvan (Ör. Piyade Uzman Çavuş) · Cenaze töreni yeri · Mezarlık: Şehitlik | ＋ |
| sehit.duyuru | Valilik, Emniyet, Jandarma ya da Türk Silahlı Kuvvetleri duyurusunun bağlantısını girin. İlan bu duyuruyla karşılaştırılır. · Resmî duyuru bağlantısı · Duyuruyu doğrula · Duyuru doğrulandı | ＋ |
| sehit.son.dugme | Onayla ve gönder | ＋ |
| sehit.yasak | “ücretsiz”, “ücretsizdir” — şehit akışında hiçbir yerde geçmez (site sahibi 08.10.2026) | kural |
| sehit.denetim | Resmî duyurudaki ad ve rütbe ilanla eşleşiyor | ＋ |
| sehit.bitti | İlan kontrolden sonra Tam Sayfa’da yayımlanır. Şehidimizin ruhu şad olsun. | ＋ |
| push.sehit | İlçenizde bir şehit cenazesi var | ＋ içerik yok (ad, rütbe, yer yazılmaz) |

## 9. Menü, Hakkında, Gizlilik
| Anahtar | Metin | Durum · neden |
|---|---|---|
| menu.adres | Adresi değiştir | ✓ site sahibinin ifadesi (§17) |
| menu.tema | Açık tema · Koyu tema | ✓ |
| menu.hakkinda / gizlilik | Hakkında · Gizlilik | ✓ |
| menu.paylas | Uygulamayı paylaş | ＋ ⋮ menüde ve Hakkında penceresinde |
| paylas.baslik | Uygulamayı paylaş | ＋ |
| paylas.metin | Kimin Cenazesi — il ve ilçenizdeki cenaze ilanları. Play Store: {bağlantı} | ＋ sakin, ünlemsiz; Telegram'da bağlantı ayrı alanda gider |
| paylas.secenek | WhatsApp · Telegram · Diğer | ＋ üç eşit düğme |
| paylas.kapat | Kapat | ＋ |
| menu.oneri | Öneri ve tavsiyeleriniz | ＋ |
| oneri.baslik | Öneri ve tavsiyeleriniz | ＋ |
| oneri.alan | Mesajınız — Görüşünüzü yazın · E-posta (isteğe bağlı) — ornek@eposta.com | ＋ |
| oneri.dugme | Vazgeç · Gönder | ＋ mesaj boşken "Gönder" pasif |
| oneri.tamam | Teşekkür ederiz · Mesajınız bize ulaştı. · Tamam | ＋ sahibin metni |
| dua.suzgec | Tümü + bölümde en sık geçen en çok 4 konu | ＋ basitlik; kalan konular yalnız "Tümü" içinde |
| menu.sifirla | Seçimi sıfırla (test) — bildirim: Seçim sıfırlandı | ✓ yalnız prototip |
| hakkinda.metin | İl ve ilçenizdeki cenaze ilanlarını her gün bir arada gösterir. Sayfanıza eklediğiniz bilgiler silinmez. Sürüm 0.1 · prototip | ✎ "Kaydettiğiniz ilanları Sayfam’da saklar, okuduklarınızı sayar." → merhum merkezli; kaynak/yöntem anlatılmaz (§16) |
| gizlilik.metin | Seçtiğiniz adres ve Sayfanıza eklediğiniz bilgiler yalnız bu cihazda tutulur. Konum izni istenmez, uygulamada reklam yoktur. | ✎ aile formu cümlesi eklendi |
| modal.kapat | Tamam | ✓ |

## 10. Bildirimler (push) — §22 (prototipte yok, uygulamada kullanılır)
Kural: içerik yok (ad, cami, saat, sayı yazılmaz); günde en çok 2; 21:00–07:00 sessiz. Dokununca o ilçenin bugünkü listesi açılır.
| Anahtar | Metin | Neden |
|---|---|---|
| push.gunluk (ana kalıp) | {ilce’de} bugünkü cenaze ilanlarını göster | site sahibinin onaylı kalıbı |
| push.alt1 | Bugün {ilce’de} uğurlananlar | sakin alternatif |
| push.alt2 | {ilce’de} bugün Hakk’a yürüyenler | sakin alternatif |
| push.alt3 | {ilce’de} bugünkü vefat ilanları | sakin alternatif |
| push.kaynaksiz | {ilce’de} bir cenaze ilanı paylaşıldı | izin kartını onaylayan kaynaksız ilçeler için; "yeni" ve sayı yok |
| push.fatiha | Merhum {ad} için bugün bir Fâtiha (erkek) · Merhume {ad} için bugün bir Fâtiha (kadın) · {ad} için bugün bir Fâtiha (cinsiyet bilinmiyor) | §22: kullanıcı açarsa; yalnız ad |
| push.izin.sistem (iOS/Android izin açıklaması) | İlçenizde cenaze ilanı paylaşıldığında haber vermek için bildirim izni gerekir. | işletim sisteminin izin penceresi metni |
| YASAK örnekler | "Yeni ilan var!" · "3 yeni cenaze ilanı" · "Kaçırmayın" · "Hemen bakın" · "Son dakika" | pazar dili |

## 11. Hata ve uyarı metinleri (uygulama; prototipte yok)
| Anahtar | Metin |
|---|---|
| hata.baglanti | Bağlantı kurulamadı. İlanlar bağlantı gelince yenilenir. |
| hata.veri | Cenaze ilanları şu an yüklenemedi. Biraz sonra yeniden deneyin. |
| hata.tekrar | Yeniden deneyin |
| bilgi.guncelleme | Son güncelleme {saat} |
| bildir.dugme | Bu ilanda bir yanlışlık mı var? |
| bildir.secenek | Kişi bilgisi yanlış · Cenaze bilgisi yanlış · Bu ilan gerçek değil · Diğer |
| bildir.gonder | Bildirin |
| bildir.tamam | Bildiriminiz alındı. Teşekkür ederiz. |
| aile.red | İlan yayımlanamadı. Bilgiler doğrulanamadı. |
| aile.yayinda | İlanınız yayımlandı. Allah rahmet eylesin. |
| odeme.iptal | Ödeme tamamlanmadı. Bilgileriniz saklandı. |

## 12. Alt sekme çubuğu
| Anahtar | Metin | Durum · neden |
|---|---|---|
| sekme.1 | İlanlar | ✓ 78 px sekmeye "Cenaze İlanları" sığmaz; ekran başlığı tam adı taşır |
| sekme.2 | Tam Sayfa | ✓ |
| sekme.3 | Sayfam | ✓ |
| sekme.4 | Dualar | ＋ (§26) |
| sekme.5 | Hatırla | ＋ Kaybettiklerimiz + Tarihte Bugün tek sekmede; 6 sekmede "Kaybettiklerimiz" etiketi 63 px, sekme 65 px — sığmıyor |

## 13. Mağaza metinleri (§16.6: kaynak/yöntem anlatılmaz)
| Anahtar | Metin |
|---|---|
| magaza.baslik | Kimin Cenazesi: Cenaze İlanı |
| magaza.kisa (≤80 karakter; genel metin, "merhumlar" çoğulu kişiye bağlı değil) | İl ve ilçenizdeki cenaze ilanları her gün bir arada; merhumları rahmetle anın. |
| magaza.uzun.giris | Kimin Cenazesi, il ve ilçenizdeki cenaze ilanlarını her sabah bir arada gösterir: vefat edenin adı, cenaze namazının kılınacağı cami ve vakit, defin yeri. Rahmetle andığınız kişileri Sayfanıza ekleyebilir, onlar için okuduğunuz Fâtiha ve Yâsîn’leri sayabilirsiniz. |
| magaza.yasak | "En güncel", "binlerce ilan", "belediye sitelerinden otomatik", ünlem, rakamla ilan sayısı |

## 14. Kısa ve düz dil turu (site sahibi 08.10.2026)
Ölçü: sahibin kendi yazdığı Sayfam metni — "Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez." Kural: her açıklama en çok 2 kısa cümle; dolambaç yok; "düğmesiyle", "buradan … yapabilirsiniz" gibi kılavuz dili yok.
| Anahtar | Eski | Yeni |
|---|---|---|
| sayfam.bos.aciklama | Cenaze ilanındaki “Sayfama kaydet” düğmesiyle merhumu buraya ekleyebilirsiniz. Eklediğiniz merhumlar silinmez; onlar için okuduklarınızı burada sayabilirsiniz. | Merhuma/merhumeye ait bilgileri buraya ekleyebilirsiniz. Sayfama eklediğiniz bilgiler silinmez. *(sahibin metni)* |
| bos.bugun.aciklama | Son yedi günün cenaze ilanları aşağıdadır. | Son yedi günün cenaze ilanları aşağıda. |
| bos.gecmis.aciklama | {tarih} tarihinde {yer’de} cenaze ilanı bulunmuyor. Üstteki şeritten başka bir güne bakabilirsiniz. | {tarih} · {yer} *(başlık zaten "Bu tarihte cenaze ilanı bulunmuyor" diyor)* |
| kaynaksiz.aciklama | … İlan doğrulandıktan sonra burada görünür. | Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra burada görünür. |
| aile.giris.aciklama | … İlan, doğrulandıktan sonra {il} sayfasında görünür. | Yakınınızın cenaze ilanını paylaşabilirsiniz. İlan kontrolden sonra {il} sayfasında görünür. |
| adim2.aciklama | e-Devlet’ten aldığınız “Ölüm Belgesi”nin doğrulama kodunu girin. Belgedeki ad soyad ilandakiyle aynı olmalıdır. Belge dosyası saklanmaz. | e-Devlet’ten aldığınız Ölüm Belgesi’nin doğrulama kodunu girin. Belge dosyası saklanmaz. |
| sehit.duyuru | Valilik, Türk Silahlı Kuvvetleri, Emniyet ya da Jandarma tarafından yayımlanan resmî duyurunun bağlantısını girin. İlan, duyuruyla karşılaştırılarak kontrol edilir. | Valilik, Emniyet, Jandarma ya da Türk Silahlı Kuvvetleri duyurusunun bağlantısını girin. İlan bu duyuruyla karşılaştırılır. |
| adim5.aciklama | Son adım. Lütfen aşağıdaki metni dikkatle okuyun. | Lütfen aşağıdaki metni okuyun. |
| adim5.tam.not | Ödemenin ardından ilanınız kontrolden sonra yayımlanır. | İlanınız ödeme ve kontrolden sonra yayımlanır. |
| aile.bitti.aciklama | Bilgiler doğrulandıktan sonra ilan {il} sayfasında yayımlanır. Başınız sağ olsun. | İlan kontrolden sonra {il} sayfasında yayımlanır. Başınız sağ olsun. |
| sehit.bitti | İlan, resmî duyuruyla karşılaştırıldıktan sonra Tam Sayfa’da yayımlanır. Şehidimizin ruhu şad olsun. | İlan kontrolden sonra Tam Sayfa’da yayımlanır. Şehidimizin ruhu şad olsun. |
| izin.hayir.bildirim | Dilediğinizde menüden açabilirsiniz | Bildirim gönderilmeyecek |
| hakkinda.metin | Kimin Cenazesi, il ve ilçenizdeki cenaze ilanlarını her gün bir arada gösterir. Sayfanıza eklediğiniz merhumları saklar, onlar için okuduklarınızı sayar. | İl ve ilçenizdeki cenaze ilanlarını her gün bir arada gösterir. Sayfanıza eklediğiniz bilgiler silinmez. |
| gizlilik.metin | Seçtiğiniz il ve ilçe, Sayfanıza eklediğiniz merhumlar ve okuduklarınızın sayısı yalnız bu cihazda tutulur. Konum izni istenmez; adresinizi siz seçersiniz. Cenaze ilanı paylaşırken girdiğiniz ölüm belgesi kodu yalnız doğrulama için kullanılır; belge dosyası saklanmaz. Uygulamada reklam yoktur. | Seçtiğiniz adres ve Sayfanıza eklediğiniz bilgiler yalnız bu cihazda tutulur. Konum izni istenmez, uygulamada reklam yoktur. *(belge dosyasının saklanmadığı form adımında zaten yazıyor)* |
| dua.3 (Fâtiha ve Yâsîn) | … gelenektir. Okuduklarınızı Sayfam’daki sayaçlarla merhum adına sayabilirsiniz. | Vefat eden yakınlarımız için Fâtiha ve Yâsîn okumak Anadolu’da köklü bir gelenektir. |
| hata.baglanti | Bağlantı kurulamadı. Cenaze ilanları, bağlantı geldiğinde yenilenir. | Bağlantı kurulamadı. İlanlar bağlantı gelince yenilenir. |
| hata.veri | Cenaze ilanları şu an yüklenemedi. Biraz sonra yeniden bakabilirsiniz. | Cenaze ilanları şu an yüklenemedi. Biraz sonra yeniden deneyin. |
| bildir.tamam | Bildiriminiz alındı. İlgilendiğiniz için teşekkür ederiz. | Bildiriminiz alındı. Teşekkür ederiz. |
| aile.red | İlan yayımlanamadı. Bilgiler doğrulanamadı; dilerseniz yeniden başvurabilirsiniz. | İlan yayımlanamadı. Bilgiler doğrulanamadı. |
| odeme.iptal | Ödeme tamamlanmadı. Bilgileriniz saklandı; dilediğinizde kaldığınız yerden sürdürebilirsiniz. | Ödeme tamamlanmadı. Bilgileriniz saklandı. |
| push.izin.sistem | İlçenizde cenaze ilanı paylaşıldığında size haber verebilmemiz için bildirim izni gerekir. | İlçenizde cenaze ilanı paylaşıldığında haber vermek için bildirim izni gerekir. |
Değişmeden kalan (zaten kısa ve düz): Kimliğiniz SMS ile doğrulanır. Tam T.C. kimlik numaranız saklanmaz. · Bilgileriniz yayından önce kontrol edilir. · Gazetedeki vefat ilanının uygulamadaki karşılığı. · Bilgiler ilanda göründüğü biçimde yayımlanır. · İlçenizde cenaze ilanı paylaşıldığında haber verelim mi?

## 15. Merhum / merhume turu (site sahibi 08.10.2026)
| Anahtar | Eski | Yeni |
|---|---|---|
| adim1.baslik | Merhumun bilgileri | Vefat eden yakınınızın bilgileri |
| alan.ad (yer tutucu) | Merhumun adı ve soyadı | Adı ve soyadı |
| aile.alan.mahalle (yer tutucu) | Merhumun mahallesi | Mahallesi |
| aile.giris.not | Yalnız merhumun yakınları paylaşabilir | Yalnız vefat edenin yakınları paylaşabilir |
| tam.ornek.2 (gazete ilanı) | merhum Feyzullah ve Hanzade Kurguluoğlu’nun oğlu | merhum Feyzullah ve merhume Hanzade Kurguluoğlu’nun oğlu |
| push.fatiha | Merhum {ad} için bugün bir Fâtiha | Merhum {ad} … (erkek) · Merhume {ad} … (kadın) · {ad} için bugün bir Fâtiha (bilinmiyor) |
| magaza.uzun.giris | … merhumun adı, cenaze namazının … | … vefat edenin adı, cenaze namazının … |
| alan.cinsiyet (yeni) | — | 1. adımda zorunlu "Vefat eden: Erkek · Kadın"; yer tutucu seçime göre "Merhumun / Merhumenin adı ve soyadı" |
Dokunulmayan: "Merhuma ait bilgileri buraya ekleyebilirsiniz." (sahibin genel cümlesi) · sayaçlar (zaten Merhuma/Merhumeye/Şehidimize; bilinmiyorsa "1 Fâtiha okudum") · "Merhum mu, merhume mi?" seçicisi.

## 16. Vefat eden: Erkek · Kadın · Şehit · Bebek (site sahibi 08.10.2026, URUN-TASLAGI §32)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| alan.cinsiyet | Vefat eden — Erkek · Kadın · Şehit · Bebek | ✎ iki düğme → dört EŞİT düğme (tek satır, 4 sütun). ZORUNLU, 1. adımın başında; aile formu, Tam Sayfa ve şehit formunda |
| form.baslik.sehit | Şehit İlanı | ✎ "Şehit" seçilince başlık ve adımlar şehit akışına geçer (rütbe, tören yeri, resmî duyuru doğrulaması, ücret yok); şehit formu doğrudan açıldığında "Şehit" seçili gelir |
| alan.cinsiyet.kucuk | Cinsiyet — Erkek · Kadın (şehit) / Erkek · Kız (bebek) | ＋ küçük seçici, isteğe bağlı |
| alan.ad.bebek | Bebeğin adı — Bebeğin adı ve soyadı | ＋ ZORUNLU |
| alan.ad.bebek.uyari | Lütfen bebeğin adını yazın | ＋ "Bebek", "İsimsiz", "Adsız", "Kız Bebek", "Yeni Doğan", "Bebek 1" gibi yer tutucu girilirse görünür; Devam pasif kalır |
| alan.yas.bebek | Yaşı — Örn. 3 · Birim: Gün · Ay | ＋ yalnız bebekte, isteğe bağlı |
| kart.bebek.etiket | Bebek | ＋ kartın üstünde küçük rozet (Yakını paylaştı rozeti gibi) |
| bebek.sayac | Bebeğimize 1 Fâtiha okudum (3 İhlâs ve 1 Fâtiha · 1 Yâsîn · 1 dua · 1 Kur’ân-ı Kerîm hatmi · 1 Kelime-i Tevhid hatmi) | ＋ cinsiyet sorusu ("Merhum mu, merhume mi?") bebekte sorulmaz |
| liste.bebek.isimsiz | (metin yok) | kural: adı olmayan bebek kaydı ("Bebek", "Kız/Erkek Bebek", "İsimsiz", "Adsız", "Yeni Doğan", "… Bebeği", yalnız "Bebek <Soyad>") ne uygulamada ne prototipte gösterilir; adı olan bebek gösterilir, addan "Bebek" sözcüğü atılır |
| liste.tekil | (metin yok) | kural: aynı kişi iki ilçe kaynağında (ör. Muğla: Fethiye + Seydikemer) TEK kart; ilk ilçe korunur |

---
**Sayım (08.10.2026, 8. tur):** 51 satırda metin değiştirildi (✎), 79 yeni metin satırı (＋); değişiklik turları §14–§15'te eski→yeni listeli.

## 16. Uygulama v0.1 ekleri (Flutter, 08.10.2026)
Gerekçe: v0.1'de sunucu/SMS yok; form ve öneri kullanıcının e-posta uygulamasını açar. "İlanınız alındı", "Mesajınız bize ulaştı" gönderim gerçekleşmeden doğru olmadığı için bu ekranlarda kullanılmaz.
| Anahtar | Metin | Durum · neden |
|---|---|---|
| aile.eposta.not | Gönderimi e-posta uygulamanızda tamamlayabilirsiniz. | ＋ aile formu bitiş ekranının başlığı ve öneri penceresinin teşekkür metni (aile.bitti.baslik ve oneri.tamam yerine) |
| aile.giris.madde2 | *(v0.1'de gösterilmez)* | "Telefonunuz SMS ile doğrulanır" — SMS yok |
| tam.yakinda | Tam sayfa vefat ilanları yakında | ＋ ücretli ilan ilk sürümde kapalı (URUN-TASLAGI §28); altında fiyat.aciklama, sonra ÖRNEK ilanlar |
| tb.hazirlaniyor | Bugün için liste hazırlanıyor | ＋ Tarihte Bugün/Kaybettiklerimiz dosyası henüz yoksa |
| hakkinda.metin | … Sürüm 0.1 | ✎ "· prototip" uygulamada yazılmaz |
| adim5.baslik (aile) | Yasal beyan | ✎ aile formunda ödeme yok; şehit akışındaki başlıkla aynı |


## 17. Uygulama v0.1.2 ekleri — aile ilanı Worker hattı (14.10.2026, deploy/AILE-ILAN-SOZLESME.md)
Gerekçe: form artık e-posta taslağı açmaz; Worker'a gönderilir, e-posta koduyla doğrulanır, kurallardan geçen ilan hemen yayına girer. Telefon ve T.C. alanı yok. §16'daki `aile.eposta.not` ve `aile.giris.madde2` bu sürümde formda kullanılmaz.
| Anahtar | Metin | Durum · neden |
|---|---|---|
| form.ust (aile) | Adım {n} / 5 | ✓ 1 vefat eden · 2 cenaze · 3 başvuran · 4 belge kodu (isteğe bağlı) · 5 yasal beyan |
| adim.cenaze.baslik | Cenaze bilgileri | ＋ 2. adım |
| adim.cenaze.aciklama | Bildiğiniz kadarını yazabilirsiniz. | ＋ |
| alan.yas / yer tutucu | Yaş · Biliyorsanız | ＋ isteğe bağlı |
| alan.namaz.tarihi | Cenaze namazı tarihi | ＋ |
| adim2.aciklama (belge) | İsteğe bağlı. e-Devlet’ten aldığınız Ölüm Belgesi’nin doğrulama kodunu girerseniz ilanda “Doğrulandı” işareti görünür. Belge dosyası saklanmaz. | ✎ belge kodu artık isteğe bağlı |
| adim3.baslik | Başvuran bilgileri | ✎ "Telefon doğrulama" → telefon yok |
| adim3.aciklama | Doğrulama kodu e-posta adresinize gönderilir. | ＋ |
| adim3.eposta / yer tutucu | E-posta · ornek@eposta.com | ＋ |
| aile.giris.madde1 | e-Devlet belge kodu isteğe bağlıdır | ✎ "Ölüm belgesi e-Devlet koduyla doğrulanır" |
| aile.giris.madde3 | Bilgiler kurallardan geçince ilan il ve ilçe sayfasında görünür. | ✎ anında yayın modeli |
| aile.not | İlanınız kurallardan geçtiğinde yayımlanır. | ✎ anında yayın modeli |
| kod.ust / kod.baslik | Doğrulama · Doğrulama kodu | ＋ |
| kod.aciklama | Doğrulama kodunu {eposta} adresine gönderdik. | ＋ |
| kod.alan / kod.yer | Kod · 6 haneli kod | ＋ |
| kod.dugme | Doğrula | ＋ |
| kod.yeniden / kod.bekle | Kodu yeniden gönder · Kodu yeniden gönder ({n} sn) | ＋ 60 sn bekleme |
| kod.eksik | Lütfen kodu eksiksiz yazın | ✓ (bildirim.kod-eksik) |
| kod.gitti | Doğrulama kodu gönderildi | ✓ (bildirim.kod-gitti) |
| kod.hatali | Kod doğru değil. Yeniden deneyebilirsiniz. | ＋ |
| aile.ag.hata | İşlem tamamlanamadı. Bilgileriniz silinmedi; biraz sonra yeniden deneyebilirsiniz. | ＋ ağ/sunucu hatası; düğme "Yeniden deneyin" |
| aile.yayinda / aile.red | §11'dekiyle aynı (sonuç ekranı; red'de sunucunun nedeni altında) | ✓ |
| aile.davet.metin | Yakınınızın cenaze bilgilerini siz paylaşabilirsiniz | ＋ "Bugün … cenaze ilanı bulunmuyor" kartının hemen altında |
| aile.davet.dugme | Cenaze bilgilerini paylaş | ✓ (§22 kalıbı) |
| kart.dogrulandi | Doğrulandı | ＋ yalnız `dogrulandi:true` aile ilanında, "Yakını paylaştı" yanında |
| bildir.dugme | Bu ilanda bir yanlışlık mı var? | ✓ §11; yalnız `aile:true` kartlarda, kartın alt satırında küçük bağlantı |
| bildir.secenek → neden | Kişi bilgisi yanlış / Cenaze bilgisi yanlış → "yanlış bilgi" · Bu ilan gerçek değil → "böyle bir kişi yok" · Diğer → "diğer" | ✓ Worker'a giden değerler |
| bildir.gonder / bildir.tamam | Bildirin · Bildiriminiz alındı. Teşekkür ederiz. | ✓ |


## §37 Din görevlisi ve ilan kutusu (0.1.5 — 15.10.2026)
Kaynak: `uygulama/lib/cekirdek/metin.dart` (`M.gorevli*`, `M.ilanKutusu*`, `M.kartGorevli`). Dil §22: sade, ünlem yok, pazar dili yok.

| Anahtar | Metin | Durum · neden |
|---|---|---|
| ilanKutusu.baslik | Cenaze ilanınızın burada görülmesini istiyorsanız: | ＋ sıra: başlık → düğme → "veya" → talep metni → küçük bağlantı; her il/ilçe liste sayfasının ÜSTÜNDE; kaynaksız ilde de aynı kutu (eski "Cenaze ilanı paylaş" düğmesi ve davet metni kutuya birleşti) |
| ilanKutusu.yakin | Cenaze yakını olarak ilanı paylaş | ＋ A) aile formunu açar |
| gorevli.dugme | Din görevlisiyim | ＋ Tam Sayfa sekmesi, üçüncü kapı |
| gorevli.fotoAciklama | Personel kartınızın fotoğrafı yalnızca doğrulama anında kullanılır, saklanmaz. TC kimlik numaranız bizim sistemimizde görünmez. | ＋ kart ekranının EN ÜSTÜNDE, kamera düğmesinden önce |
| gorevli.kuyrukUyari | Doğrulama yapılamadı; fotoğrafınız en çok 7 gün kontrol için saklanır, sonra silinir. | ＋ §37 tek istisna |
| gorevli.fotoSaklama | Doğrulama için kartınızın fotoğrafı en çok 7 gün kontrol amacıyla saklanır, sonra silinir. | ＋ "kontrolde" sonucunda |
| gorevli.kontrolBilgi | Başvurunuz kontrol ediliyor. Hesabınız onaylanınca paneldeki "İlan paylaş" düğmesi etkin hale gelir. Onay verilmezse panel ve hesap silinir. | ＋ panel bilgi kutusu ve pasif düğme açıklaması |
| gorevli.kontrolMetin | Başvurunuz kontrol ediliyor. Onaylanınca tarafınıza bilgi verilecek ve din görevlisi paneliniz açılacaktır. | ＋ kayıt sonrası ekran |
| gorevli.onaylandi / paneleGit | Hesabınız onaylandı · Panele git | ＋ |
| gorevli.silindi | Başvurunuz onaylanmadı; hesap silindi. | ＋ red sonrası ilk açılış |
| gorevli.onayBildirimi | Başvurunuz onaylandı; din görevlisi paneliniz açıldı. | ＋ yerel bildirim; SMS yedeği: "Kimin Cenazesi: din görevlisi başvurunuz onaylandı, paneliniz açıldı." |
| gorevli.ciftKayit | Hesap kontrol bekliyor | ＋ aynı ad + görev yeri için ikinci başvuru |
| gorevli.baslikKartı | "{görev yeri} {unvan}" / "{ad soyad}" / "{il} · {ilçe}" | ＋ sabit başlık kartı; ör. Korgan Merkez Camii İmam Hatibi |
| gorevli.ilanPaylas / ilanlarim | İlan paylaş · İlanlarım ({n}) | ＋ iki büyük düğme |
| gorevli.yerKilit | İl ve ilçe görev yerinize göre sabittir. | ＋ |
| kart.gorevli | Mahallenin din görevlisi paylaştı | ＋ rozet ("Yakını paylaştı" kalıbı); altında görev yeri |

### §37 düzeltmeleri ve eklemeler (15.10.2026 akşam; yukarıdaki satırların yerine geçer)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| ilanKutusu.veya | veya | ＋ düğmenin altında ortalı küçük |
| ilanKutusu.gorevli | Bulunduğunuz bölgedeki cami din görevlisinden bunu talep edin. | ＋ "veya"nın altında |
| ilanKutusu.kayit | Din görevlisi misiniz? Kayıt olun. | ＋ en altta küçük bağlantı (noktalı) |
| gorevli.girisNot | Hesabınız Diyanet personel kartınızla doğrulanır. | ✎ kayıt ekranı alt başlığı (noktalı) |
| gorevli.telefon / not | Cep telefonu · Telefon numaranız yalnız doğrulama ve bilgilendirme için kullanılır; ilanlarda görünmez. | ＋ e-posta alanı yok |
| gorevli.beyan | Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum. | ＋ formun EN ALTINDA zorunlu onay kutusu; Worker `beyan:true` + `beyan_tarihi` ister |
| gorevli.basvuruGonder | Başvuruyu gönder | ＋ beyan işaretlenmeden pasif |
| gorevli.fotoUst | Diyanet personel kartı | ✎ ekran başlığı (kart ekranı) |
| gorevli.fotoAciklama | Personel kartınızın fotoğrafı yalnızca doğrulama anında kullanılır, saklanmaz. TC kimlik numaranız bizim sistemimizde görünmez. | ✓ sahibinin metni, ekranın EN ÜSTÜNDE |
| gorevli.fotoYonerge | Diyanet İşleri Başkanlığı'nın size verdiği personel kimlik kartınızın ön yüzünü çekin. | ＋ açıklama kutusunun altında |
| gorevli.kamera | Personel kartımı çek | ✎ tek düğme; yalnız uygulama içi kamera; "Galeriden seç" YOK; kâğıt kodu YOK (iptal) |
| gorevli.deneme2 | Kart doğrulanamadı. Işığı kontrol edip bir kez daha çekin. | ✎ kod ibaresi kalktı |
| gorevli.kodGirin | Telefonunuza gönderilen 6 haneli kodu girin. | ＋ kod ekranı; 60 sn sonra "Kodu yeniden gönder" |
| aile.telefon (adım 3) | Cep telefonu · 5xx xxx xx xx · Telefon numaranız yalnız doğrulama için kullanılır; ilanda görünmez. | ✎ e-posta yerine; kod ekranı: "Telefonunuza gönderilen 6 haneli kodu girin." |
| sehit.bilgi.baslik | Şehit cenazesi ilanları yalnızca din görevlileri tarafından paylaşılır. | ＋ "Şehit yakını" kapısı ve Tam Sayfa "Şehidimiz için ilan hazırlayın" bu bilgi ekranını açar; form YOK |
| sehit.bilgi.govde | Şehidimizin yakınıysanız, cenaze töreninin yapılacağı caminin din görevlisine iletmeniz yeterlidir; ilan buradan duyurulur. | ＋ |
| sehit.bilgi.kapanis | Başınız sağ olsun. Şehidimizin ruhu şad olsun. | ＋ altında bağlantı: Din görevlisi misiniz? Kayıt olun. |
| gorevli.sehitAnahtar | Şehit cenazesi | ＋ panel ilan formunda anahtar; açılınca rütbe, tören yeri, resmî duyuru bağlantısı (isteğe bağlı); liste satırı "Şehidimiz <Rütbe Ad Soyad>" |

### Otomatik TC karartma (15.10.2026 akşam; "parmağınızla kapatın" cümlesi KALDIRILDI)
| Anahtar | Metin | Durum · neden |
|---|---|---|
| gorevli.fotoAciklama | Personel kartınızın fotoğrafı yalnızca doğrulama anında kullanılır, saklanmaz. TC kimlik numaranız bizim sistemimizde görünmez. | ✎ kart ekranının EN ÜSTÜ; kuyruk istisnası metni ("…en çok 7 gün…") aynen kalır |
| gorevli.kartIslenemedi | Fotoğraf işlenemedi. Lütfen kartı yeniden çekin. | ＋ karartma/tanıma hatasında fotoğraf GÖNDERİLMEZ |
