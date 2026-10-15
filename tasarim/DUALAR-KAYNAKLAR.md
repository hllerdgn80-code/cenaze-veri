# Dualar sekmesi — kaynaklar ve doğrulama (08.10.2026)

Veri: `tasarim/dualar.json` (4 bölüm). Prototip: `prototip_yap.py` sonundaki ek bu dosyayı okur, şablondaki örnek `DUALAR` dizisinin yerine koyar, kartlara konu etiketi süzgeci, merhum/merhume sürümü ve not satırı ekler.

## Telif ilkesi
- Diyanet’in meal, hadis çevirisi ve dua kitabı metinleri **alınmadı**. Diyanet sayfaları yalnız **katalog** (hangi âyet/hadis hangi konu başlığında anılıyor) ve **numara/metin çapraz kontrolü** için okundu.
- Arapça metinler açık kaynaktan: Kur’an → api.quran.com (Uthmani, `text_uthmani`); hadis ve hadis kaynaklı dualar → fawazahmed0/hadith-api (cdn.jsdelivr.net, Arapça baskılar). Râvi zinciri atıldı, yalnız Peygamberimizin sözü (ya da menkıbedeki kişinin sözü) alındı; birden çok parça “ … ” ile birleştirildi.
- Türkçe “anlam”lar kendi sade cümlelerimizdir (meal/çeviri değil). Okunuşlar (Latin harfli) kendi standardımız: uzun ünlü ^, ayn/hemze ’/‘, takı kesmesi ’.
- Menkıbeler kendi cümlelerimizle 3–5 cümlelik özettir; olgular hadis metninden (API) ya da TDV İslâm Ansiklopedisi maddesinden kontrol edildi, ansiklopedi metni kopyalanmadı. Yunus Emre dizesi kamu malıdır.
- Kullanıcıya görünen kaynak satırlarında (k) yalnız klasik eser adı ve hadis numarası var; Diyanet/site adı `katalog` alanında (görünmez) durur.

## Açılan kaynaklar (08.10.2026)
| Kaynak | Kullanım |
|---|---|
| https://hadislerleislam.diyanet.gov.tr/icindekiler.php | İçindekiler → konu bölümlerinin sayfa aralığı |
| https://hadislerleislam.diyanet.gov.tr/sayfa.php?CILT=…&SAYFA=… (315 sayfa, 1,5 sn aralıkla) | Katalog + çapraz kontrol. Bölümler: Ölüm (7/545), Cenaze Merasimi (7/555), Kabir (7/567), Kabir Ziyareti (7/577), Kıyamet (7/599), Âhiret (7/609), Cenaze Namazı (2/231), Sabır (3/203), Musibetler ve Mümin (5/11), Şehitlik (4/517), Gazilik, Cihad, Hasta Ziyareti (4/377), Kader (1/597), Dua (2/35), Zikir, Sadaka (2/483), Haccetmek, Salih Amel, Merhamet, Dünyevîleşme, Anne ve Baba (4/177), Hz. Peygamber’in Duası (6/513), Tıp (7/331), Yolculuk (7/513), Dünya: Âhiretin Tarlası (1/337) |
| https://kurul.diyanet.gov.tr/tr/fetva/cenaze-namazi-nasil-kilinir/0193c42d-5ff0-7a8b-b744-96f510e9362a | Cenaze namazının kılınışı (d01 özet, kendi cümlemiz), Tirmizî 1024/1026 numaraları |
| https://kurul.diyanet.gov.tr/tr/fetva/yapilan-hayrin-veya-okunan-kuranin-sevabi-olen-kimseye-bagislanabilir-mi/0193c42d-631d-7de7-391c-bc2393c46d31 | Sevap bağışlama; İbn Mâce 1495, Buhârî 2760, Müslim 1004 numaraları |
| https://api.quran.com/api/v4/verses/by_key/{sure:âyet}?fields=text_uthmani | Âyet Arapçası (65 âyet) |
| https://api.alquran.cloud/v1/ayah/{sure:âyet}/quran-uthmani | İkinci Kur’an kaynağı: ünsüz iskeleti karşılaştırması |
| https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-{bukhari,muslim,tirmidhi,abudawud,nasai,ibnmajah}.min.json | Hadis Arapçası + el-Elbânî derecesi (Tirmizî, Ebû Dâvûd, İbn Mâce) |
| https://islamansiklopedisi.org.tr/{osman, ali, fatima, hamza, ebu-zer-el-gifari, bilal-i-habesi, muaz-b-cebel, mevlana-celaleddin-i-rumi, yunus-emre, gazzali, abdulkadir-i-geylani, haci-bayram-i-veli, hatice, ebu-bekir, omer, omer-b-abdulaziz} | Menkıbe olgu kontrolü (tarih, yer, olay) |

Açılamayanlar (dolanılmadı): sunnah.com (Cloudflare “Just a moment” 403), dorar.net (Cloudflare 403), kuran.diyanet.gov.tr âyet sayfası (SSL hatası; ana sayfa açıldı, konu fihristi bulunamadı — âyet kataloğu Hadislerle İslâm dipnotlarından alındı).

## Doğrulama yöntemi
- **Âyet:** api.quran.com metni ile api.alquran.cloud metni harekesiz ünsüz iskeletinde karşılaştırıldı (kısmî âyetlerde seçilen kelimeler). Eşleşirse “iki kaynak”. Ayrıca `katalog`: âyet Hadislerle İslâm’ın ilgili bölüm dipnotunda geçiyorsa sayfası yazıldı; geçmeyenler “Diyanet katalog sayfalarında görülmedi” diye işaretli (konu uygunluğuyla seçildi).
- **Hadis / hadis kaynaklı dua:** hadith-api Arapçası + (a) Hadislerle İslâm’daki atıf numarası (B, M[genel numara], T, D, N, İM) ya da DİYK fetvasındaki numara, veya (b) Hadislerle İslâm sayfalarındaki Arapça metinde 5 kelimelik birebir (harekesiz) eşleşme / metnin tamamı. Biri varsa “iki kaynak”. Numaralar sunnah.com numaralandırmasıdır (Müslim: Abdülbâkî). Zayıf hadis alınmadı (el-Elbânî derecesi olan kitaplarda Sahih/Hasan şartı kodla denetlendi); Yâsîn rivayeti (Ebû Dâvûd 3121, İbn Mâce 1448) yalnız d18 notunda “senedi zayıf” diye anıldı.
- **Menkıbe:** olay hadis metninde (API) ve DİA maddesinde birlikte doğrulanınca “iki kaynak”; yalnız birinde ise “tek kaynak”.

| Bölüm | Kayıt | İki kaynak | Tek kaynak |
|---|---|---|---|
| Ölümle ilgili âyetler | 35 | 35 | 0 |
| Hadisler | 44 | 31 | 13 |
| Menkıbeler | 18 | 6 | 12 |
| Vefat eden yakınlarımız için dualar | 34 | 27 | 7 |

## Tek kaynak kalanlar
- `h07` Rahata eren — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h08` Ölümün sıkıntıları — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h09` Ameller sonlarına göredir — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h14` Vefat eden adına hac — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h15` Cenazenin ardından gitmek — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h17` Cenazeyi geciktirmemek — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h18` Kırk kişinin duası — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h22` “O da bir can değil mi?” — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h29` Diken batması bile — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h31` Küçük yaşta vefat eden çocuklar — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h33` Cenaze evine yemek — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h39` Şehitler beş kısımdır — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `h44` Denizdeki parmak — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `m03` Hz. Osman: Kur’ân okurken — https://islamansiklopedisi.org.tr/osman
- `m04` Hz. Ali: Sabah namazında — https://islamansiklopedisi.org.tr/ali
- `m06` Hz. Hamza: Şehitlerin efendisi — https://islamansiklopedisi.org.tr/hamza
- `m07` Ebû Zer: Rebeze’de yalnız bir vefat — https://islamansiklopedisi.org.tr/ebu-zer-el-gifari
- `m08` Hz. Bilâl: Susan ezan — https://islamansiklopedisi.org.tr/bilal-i-habesi
- `m09` Muâz bin Cebel: Amvâs salgını — https://islamansiklopedisi.org.tr/muaz-b-cebel
- `m10` Ebû Talha ve eşinin sabrı — hadith-api Buhârî 1301
- `m12` Hz. Hatice ve hüzün yılı — https://islamansiklopedisi.org.tr/hatice
- `m14` Yunus Emre: Canlar ölesi değil — Yunus Emre Divanı (kamu malı); DİA maddesinde dize bulunmadı
- `m15` İmam Gazâlî’nin son sabahı — önceki prototip kartı; vefat tarihi ve yeri: https://islamansiklopedisi.org.tr/gazzali
- `m17` Abdülkâdir-i Geylânî’nin vasiyeti — https://islamansiklopedisi.org.tr/abdulkadir-i-geylani
- `m18` Hacı Bayram-ı Velî — https://islamansiklopedisi.org.tr/haci-bayram-i-veli
- `d02` Sübhâneke (cenaze namazında) — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d03` Salli ve Bârik duaları — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d06` Cenaze namazı duası (Vâsile rivayeti) — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d13` Kabre koyarken — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d14` Defin bitince — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d21` Peygamberimizin son duası — hadith-api (Diyanet sayfasında eşleşme bulunmadı)
- `d26` Sıkıntı anında — hadith-api (Diyanet sayfasında eşleşme bulunmadı)

## Merhum / merhume
Arapça zamiri cinsiyete göre değişen dualarda (d04, d05, d06, d09, d14, d22, d23) `kadin` alanında dişil sürüm (ar + okunuş) verildi; prototipte “Merhum için / Merhume için” başlıklarıyla iki sürüm görünür. Dişil sürümler hadis metninden zamir uyarlamasıdır (hadiste erkek zamiriyle geçer) ve kodla kelime düzeyinde üretildi. Açıklamalarda nötr ifade (“vefat eden yakınınız”) kullanıldı.

## Etiketler
Ölüm · Sabır · Kader · Âhiret · Kabir · Taziye · Dua · Cenaze · Şehitlik · Ölünün ardından (`hayır`) · Hastalık. Her bölümde yalnız o bölümde geçen etiketler süzgeç düğmesi olarak çıkar (“Tümü” + etiketler).

## Yeniden üretim
Üretim betiği oturum çalışma alanındaydı (`build_dualar.py`); veri değişince `dualar.json` elle düzenlenebilir, `python3 prototip_yap.py` prototipi yeniden kurar.

## Menkıbeler yeniden yazıldı (15.10.2026)
Site sahibi isteği: sıcak anlatım + "kıssadan hisse". 18 maddenin `an` metni yeniden yazıldı (olgu eklenmedi; Buhârî 1387, 3700, 3625, 1301, 4463 eng-bukhari metniyle yeniden okundu), her maddeye `h` (hisse) alanı eklendi ve `an`'ın son paragrafı "Kıssadan hisse: …" olarak durur. Dört yeni madde (m19–m22) Mevlânâ, Mesnevî (Nicholson çevirisi, archive.org/details/RUMITheMathnawiVol1Vol2): Süleyman–Azrâil (I, 956–970), tüccar ve papağan (I, 1547–1845), Cühî ve cenaze (II, 3116–3128), hasta ziyareti/Mûsâ (II, 2156–2163). Ana dosya `tasarim/dualar.json`; uygulama kopyası (`uygulama/assets/veri/dualar.json`) aynı içeriğin `id/dogrulama/katalog` alanları atılmış, sıkıştırılmış biçimi (kopyalama betiği yok, elle eşlendi).
