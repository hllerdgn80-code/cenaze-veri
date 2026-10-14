# 15 kaynaksız il: il/ilçe müftülükleri + tüm ilçe belediyeleri genel akış taraması (14.10.2026)

**Tembih beyanı:** `AJAN-TEMBIH-LISTESI.md` başı, YURUT §3 (H25–H46) ve `alternatif-yollar-2026-10-05.md` Yol 2 okundu; uyuldu (robots'a uyuldu, alan adı başına ≥3,5 sn, site başına ≤40 istek, 403/CAPTCHA dolanılmadı, kişi adı kaydedilmedi).

## SONUÇ (tek bakış)
- **Yeni, günlük çalışan, açık kaynak BULUNMADI.** İki kaynak sınıfı da 15 ilde taranınca okuyucuya yeni bağlanabilecek taze (son 14 gün) bir il/ilçe listesi çıkmadı; bu yüzden `okuyucu/<il>.py` dosyalarına **kaynak eklenmedi** (bayat ya da kişi ilanı içermeyen kaynağı yayına sokmak 08.10 Play kararına ve "cümle/neden saklanmaz" ilkesine aykırı olurdu).
- **Müftülükler (%100 olumsuz):** il müftülükleri `https://<il>.diyanet.gov.tr` (SharePoint), ilçe müftülükleri aynı alan adında alt yol `https://<il>.diyanet.gov.tr/<ilçe>/Sayfalar/...` (ilçe başına ayrı alt alan adı YOK; `midyat.diyanet.gov.tr` gibi adlar DNS'te yok). 15 il müftülüğü + 100'ü aşkın ilçe müftülüğünün "haber", "ilan/duyuru" ve ana sayfa içerikleri tarandı: **hiçbirinde cenaze namazı ilanı / vefat listesi yok.** İçerik yalnız sınav ilanı, vaaz, hutbe, kurban, etkinlik. Tek "vefat" eşleşmesi (Hakkari, 08–09.10) "vefat eden din görevlileri anıldı" mevlit haberi, kişi ilanı değil. RSS yok. (Bu, Diyanet'in merkezî olarak cenaze duyurusunu ilçe sitelerine yazdırmadığını gösteriyor; cenaze duyurusu camide anons/belediye/yerel basında.)
- **Belediyeler:** il merkezi + ilçe belediyeleri için `<ad>.bel.tr` (+ `www.`, `belediyesi.bel.tr`, `-bld.gov.tr`, `belediyesi.com` biçimleri) denendi; ana sayfa, menüdeki duyuru/haber/vefat bağlantıları (≤6), RSS (rel=alternate ya da /rss, /feed, /rss.xml) ve 12 standart vefat yolu (`--derin`) okundu. Son 14 günde **kişi ilanı içeren tek akış, ZATEN bağlı olanlar**: Çekerek ve Sorgun (Yozgat, `okuyucu/yozgat.py`), Çifteler (Eskişehir, `okuyucu/eskisehir.py`). Diğer tüm "vefat" sayfaları bayat (Vize son kayıt 25.04.2026; Bayburt 23.08.2026; Demirköy tarihsiz; Çemişgezek 29.08.2025; Pertek 07.04.2026; Lüleburgaz ve Şefaatli sayfalarında kişi kaydı yok (yalnız 31.03.2024 seçim tarihi geçiyor); Boğazlıyan 17.12.2024; Ağrı Bel. 27.06.2019; Kofçaz 01.09.2016; Pınarhisar 2016) ya da boş ("Toplam 0 Vefat Eden": Cizre, Nazımiye).
- **Genel haber/duyuru/RSS'te vefat kalıbı ("vefat", "başsağlığı", "cenaze", "Hakk'a yürüdü", "son yolculuğuna") — son 14 gün:** 15 ilde yalnız **tek** eşleşme: Pınarhisar RSS'te belediye başkanının cenaze törenine katıldığını anlatan 05.10 tarihli başsağlığı haberi; cenaze günü/yeri/camisi yok → okuyucuya uygun değil. Küçük belediyeler vefatı genel duyuruya yazmıyor.
- **Okuyucu için dürüst sonuç:** bu iki sınıf (müftülük + belediye genel akışı) 15 ildeki boşluğu KAPATMIYOR. Boşluk yerel basın (zaten bağlı), aile formu (H46) ve e-Devlet/belediye paneli yollarıyla kapanır.

## Yöntem
`araclar/kesif_muftu_belediye.py` (yeni; ortak dosyalara dokunmaz). `python3 araclar/kesif_muftu_belediye.py` (tarama) ve `... --derin` (vefat yolu sondajı + tarih istatistiği). Ham çıktı: `arastirma/kesif/muftu-belediye-2026-10-14.jsonl`, `muftu-belediye-derin-2026-10-14.jsonl`. Sonuç sınıfları: tarihli vefat penceresi ≤14 gün = VAR14; kalıp var ama eski = KALIP_ESKI; kalıp yok = ICERIK_YOK. Yumuşak 404 elemesi (H25): vefat listesi sayılması için vefat sözcüğü ≥6, ana sayfaya benzerlik <0,99, sayfada tarih var. Robots ayrıştırıcısı en uzun eşleşen kuralı uygular (H28).

## Sınırlar
- **Belde belediyeleri** sayılamadı: `ilceler.json` yalnız ilçeleri taşıyor, güvenilir bir 15 il belde listesi yok (Vikipedi'de derleme sayfası bulunamadı). Büyükşehir olan Mardin ve Eskişehir'de belde yok; diğer illerin beldeleri için resmî TÜİK/İçişleri belediye listesi gerekir (ayrı iş).
- Sayfa başına ilk sayfa okundu (sayfalama yok); menüdeki en çok 6 duyuru/haber bağlantısı. JS ile dolan listeler (örn. H41'de Manisa) görünmez.
- Engelli/erişilemeyen: Taşlıçay, Tutak, Adaklı, Aralık (HTTP 403, dolanılmadı); Bingöl Belediyesi `bingolbelediyesi.com` ve Nusaybin `nusaybinbelediyesi.com` zaman aşımı (Mac'te yeniden denenebilir); Yozgat Belediyesi robots.txt `Disallow:/`.
- Alan adı bulunamayan 17 belediye (tabloda "alan adı bulunamadı") farklı alan adı kullanıyor olabilir (örn. Muş Belediyesi, Mardin/Derik); bulunursa tek satırla eklenir.

## Gerekli kapı kaydı
Yok (yeni kaynak eklenmedi; `kapi.py`/`yayin_suz.py`/`topla.yml` değişikliği gerekmiyor).

## Tablo: il × kaynak
Sütunlar: kaynak · URL/alan adı (vefat sayfası varsa o sayfa) · erişim · son 14 günde vefat içeriği sayısı (pencere sayısı, kişi adı yok) · okuyucuya yazıldı mı.


### Ağrı
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Ağrı İl Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Ağrı Belediyesi | www.agri.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2019-06-27 (bayat/seyrek) |
| Diyadin İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Diyadin Belediyesi | diyadin.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Doğubayazıt İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Doğubayazıt Belediyesi | dogubayazit.bel.tr/taziye-ilanlari | açık | 0 | hayır — vefat listesi var ama son kayıt 2022-11-01 (bayat/seyrek) |
| Eleşkirt İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Eleşkirt Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Hamur İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Hamur Belediyesi | www.hamur.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Patnos İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Patnos Belediyesi | patnos.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Taşlıçay İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Taşlıçay Belediyesi | taslicay.bel.tr | engel (HTTP 403, dolanılmadı) | 0 | hayır — engel (HTTP 403, dolanılmadı) |
| Tutak İlçe Müftülüğü | agri.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Tutak Belediyesi | tutak.bel.tr | engel (HTTP 403, dolanılmadı) | 0 | hayır — engel (HTTP 403, dolanılmadı) |

### Ardahan
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Ardahan İl Müftülüğü | ardahan.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Ardahan Belediyesi | ardahan.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Çıldır İlçe Müftülüğü | ardahan.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çıldır Belediyesi | cildir.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Damal İlçe Müftülüğü | ardahan.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Damal Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Göle İlçe Müftülüğü | ardahan.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Göle Belediyesi | gole.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Hanak İlçe Müftülüğü | ardahan.diyanet.gov.tr | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Hanak Belediyesi | hanak.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Posof İlçe Müftülüğü | ardahan.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Posof Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |

### Bayburt
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Bayburt İl Müftülüğü | bayburt.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Bayburt Belediyesi | bayburt.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2026-08-23 (bayat/seyrek) |
| Aydıntepe İlçe Müftülüğü | bayburt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Aydıntepe Belediyesi | aydintepe.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Demirözü İlçe Müftülüğü | bayburt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Demirözü Belediyesi | demirozu.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2023-01-21 (bayat/seyrek) |

### Bingöl
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Bingöl İl Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Bingöl Belediyesi | bingolbelediyesi.com | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Adaklı İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Adaklı Belediyesi | adakli.bel.tr | engel (HTTP 403, dolanılmadı) | 0 | hayır — engel (HTTP 403, dolanılmadı) |
| Genç İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Genç Belediyesi | genc.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Karlıova İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Karlıova Belediyesi | karliova.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Kiğı İlçe Müftülüğü | bingol.diyanet.gov.tr | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Kiğı Belediyesi | kigi.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Solhan İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Solhan Belediyesi | solhan.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Yayladere İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yayladere Belediyesi | yayladere.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Yedisu İlçe Müftülüğü | bingol.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yedisu Belediyesi | yedisu.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Bitlis
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Bitlis İl Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Bitlis Belediyesi | bitlis.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Adilcevaz İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Adilcevaz Belediyesi | adilcevaz.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Ahlat İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Ahlat Belediyesi | ahlat.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Güroymak İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Güroymak Belediyesi | guroymak.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Hizan İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Hizan Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Mutki İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mutki Belediyesi | mutki.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Tatvan İlçe Müftülüğü | bitlis.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Tatvan Belediyesi | tatvan.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Eskişehir
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Eskişehir İl Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Eskişehir Belediyesi | eskisehir.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Alpu İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Alpu Belediyesi | alpu.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Beylikova İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Beylikova Belediyesi | beylikova.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Çifteler İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çifteler Belediyesi | www.cifteler.bel.tr/HOME/INDEX/HIZMET-VE-TESISLER/VEFAT-EDENLER | açık | 0 | zaten bağlı (okuyucu/eskisehir.py) |
| Günyüzü İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Günyüzü Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Han İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Han Belediyesi | han.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| İnönü İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| İnönü Belediyesi | www.inonu.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Mahmudiye İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mahmudiye Belediyesi | mahmudiye.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Mihalgazi İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mihalgazi Belediyesi | mihalgazi.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Mihalıççık İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mihalıççık Belediyesi | mihaliccik.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Odunpazarı İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Odunpazarı Belediyesi | www.odunpazari.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Sarıcakaya İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Sarıcakaya Belediyesi | saricakaya.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Seyitgazi İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Seyitgazi Belediyesi | seyitgazi.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Sivrihisar İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Sivrihisar Belediyesi | sivrihisar.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Tepebaşı İlçe Müftülüğü | eskisehir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Tepebaşı Belediyesi | tepebasi.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |

### Hakkari
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Hakkari İl Müftülüğü | hakkari.diyanet.gov.tr | açık | 0 (kişi ilanı) | hayır — yalnız "vefat eden din görevlileri anıldı" anma haberi; cenaze ilanı değil |
| Hakkari Belediyesi | hakkari.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Çukurca İlçe Müftülüğü | hakkari.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çukurca Belediyesi | cukurca.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Derecik İlçe Müftülüğü | hakkari.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Derecik Belediyesi | derecik.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Şemdinli İlçe Müftülüğü | hakkari.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Şemdinli Belediyesi | semdinli.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Yüksekova İlçe Müftülüğü | hakkari.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yüksekova Belediyesi | yuksekova.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Iğdır
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Iğdır İl Müftülüğü | igdir.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Iğdır Belediyesi | igdir.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Aralık İlçe Müftülüğü | igdir.diyanet.gov.tr | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Aralık Belediyesi | aralik.bel.tr | engel (HTTP 403, dolanılmadı) | 0 | hayır — engel (HTTP 403, dolanılmadı) |
| Karakoyunlu İlçe Müftülüğü | igdir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Karakoyunlu Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Tuzluca İlçe Müftülüğü | igdir.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Tuzluca Belediyesi | tuzluca.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Kırklareli
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Kırklareli İl Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Kırklareli Belediyesi | kirklareli.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Babaeski İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Babaeski Belediyesi | babaeski.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Demirköy İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Demirköy Belediyesi | demirkoy.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Kofçaz İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Kofçaz Belediyesi | www.kofcaz.bel.tr/vefat | açık | 0 | hayır — vefat listesi var ama son kayıt 2016-09-01 (bayat/seyrek) |
| Lüleburgaz İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Lüleburgaz Belediyesi | luleburgaz.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Pehlivanköy İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Pehlivanköy Belediyesi | pehlivankoy.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Pınarhisar İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Pınarhisar Belediyesi | pinarhisar.bel.tr | açık | 2 | hayır — RSS'te tek başsağlığı/tören haberi (gün-yer alanı yok) |
| Vize İlçe Müftülüğü | kirklareli.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Vize Belediyesi | vize.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2026-04-25 (bayat/seyrek) |

### Mardin
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Mardin İl Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mardin Belediyesi | mardin.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Artuklu İlçe Müftülüğü | mardin.diyanet.gov.tr | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Artuklu Belediyesi | artuklu.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Dargeçit İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Dargeçit Belediyesi | dargecit.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Derik İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Derik Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Kızıltepe İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Kızıltepe Belediyesi | kiziltepe.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Mazıdağı İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Mazıdağı Belediyesi | mazidagi.bel.tr/cenaze-hizmetlerinin-onu-yenilendi/ | açık | 0 | hayır — vefat listesi var ama son kayıt 2025-06-23 (bayat/seyrek) |
| Midyat İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Midyat Belediyesi | midyat.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Nusaybin İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Nusaybin Belediyesi | nusaybinbelediyesi.com | açılmadı (zaman aşımı/SSL) | 0 | hayır — açılmadı (zaman aşımı/SSL) |
| Ömerli İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Ömerli Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Savur İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Savur Belediyesi | savur.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Yeşilli İlçe Müftülüğü | mardin.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Yeşilli Belediyesi | yesilli.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Muş
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Muş İl Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Muş Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Bulanık İlçe Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Bulanık Belediyesi | bulanik.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Hasköy İlçe Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Hasköy Belediyesi | haskoy.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Korkut İlçe Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Korkut Belediyesi | korkut.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Malazgirt İlçe Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Malazgirt Belediyesi | malazgirt.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Varto İlçe Müftülüğü | mus.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Varto Belediyesi | varto.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |

### Siirt
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Siirt İl Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Siirt Belediyesi | siirt.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Baykan İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Baykan Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Eruh İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Eruh Belediyesi | eruh.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Kurtalan İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Kurtalan Belediyesi | kurtalanbelediyesi.com | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Pervari İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Pervari Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Şirvan İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Şirvan Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Tillo İlçe Müftülüğü | siirt.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Tillo Belediyesi | tillo.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Şırnak
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Şırnak İl Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Şırnak Belediyesi | sirnak.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Beytüşşebap İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Beytüşşebap Belediyesi | beytussebap.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Cizre İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Cizre Belediyesi | cizre.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Güçlükonak İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Güçlükonak Belediyesi | guclukonak.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| İdil İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| İdil Belediyesi | idil.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Silopi İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Silopi Belediyesi | silopi.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Uludere İlçe Müftülüğü | sirnak.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Uludere Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |

### Tunceli
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Tunceli İl Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Tunceli Belediyesi | tunceli.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Çemişgezek İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çemişgezek Belediyesi | www.cemisgezek.bel.tr/vefat-edenler/ | açık | 0 | hayır — vefat listesi var ama son kayıt 2025-08-29 (bayat/seyrek) |
| Hozat İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Hozat Belediyesi | hozat.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Mazgirt İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Mazgirt Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Nazımiye İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Nazımiye Belediyesi | nazimiye.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Ovacık İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Ovacık Belediyesi | ovacik.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Pertek İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Pertek Belediyesi | www.pertek.bel.tr/vefat-edenler/ | açık | 0 | hayır — vefat listesi var ama son kayıt 2026-04-07 (bayat/seyrek) |
| Pülümür İlçe Müftülüğü | tunceli.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Pülümür Belediyesi | pulumur.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |

### Yozgat
| Kaynak | URL / alan | Erişim | 14 gün | Yazıldı mı |
|---|---|---|---|---|
| Yozgat İl Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yozgat Belediyesi | yozgat.bel.tr | robots.txt kapalı | 0 | hayır — robots.txt kapalı |
| Akdağmadeni İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Akdağmadeni Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Aydıncık İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Aydıncık Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
| Boğazlıyan İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Boğazlıyan Belediyesi | bogazliyan.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2024-12-17 (bayat/seyrek) |
| Çandır İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çandır Belediyesi | candir.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Çayıralan İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çayıralan Belediyesi | cayiralan.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Çekerek İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Çekerek Belediyesi | cekerek.bel.tr/vefat-edenler | açık | 3 | zaten bağlı (okuyucu/yozgat.py) |
| Kadışehri İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Kadışehri Belediyesi | kadisehri.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Saraykent İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Saraykent Belediyesi | saraykent.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Sarıkaya İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — yalnız menü/eski anma haberi; cenaze ilanı yok |
| Sarıkaya Belediyesi | sarikaya.bel.tr | açık | 0 | hayır — vefat listesi bulunamadı; genel akışta kişi ilanı yok |
| Sorgun İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Sorgun Belediyesi | sorgun.bel.tr/vefat-edenler | açık | 1 | zaten bağlı (okuyucu/yozgat.py) |
| Şefaatli İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Şefaatli Belediyesi | sefaatli.bel.tr/vefat-edenler | açık | 0 | hayır — vefat listesi var ama son kayıt 2024-03-31 (bayat/seyrek) |
| Yenifakılı İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yenifakılı Belediyesi | yenifakili.bel.tr | açık | 0 | hayır — vefat/cenaze sayfası yok, genel haber/duyuru/RSS'te vefat içeriği yok |
| Yerköy İlçe Müftülüğü | yozgat.diyanet.gov.tr | açık | 0 | hayır — cenaze/vefat duyurusu yok (haber+ilan sayfaları) |
| Yerköy Belediyesi | - | alan adı bulunamadı | 0 | hayır — alan adı bulunamadı |
