// Günlük cenaze bildirimi — SAF MANTIK (eklenti yok; birim testlenir). Karar: URUN-TASLAGI §36, dil kuralları §22.
// Eklentiye bağlı kısım (izin, WorkManager, bildirim gösterme): bildirim.dart.
import 'ilan.dart';
import 'yardimci.dart';

/// Sabah bakışı 08:00, öğle bakışı 12:00 (cihaz saati). 21:00–07:00 arası hiçbir bildirim gönderilmez.
const int sabahSaat = 8;
const int ogleSaat = 12;
const int sessizBaslangic = 21;
const int sessizBitis = 7;

/// "Şimdi değil" diyene kaç gün yeniden sorulmaz
const int erteleGunSayisi = 7;

enum BildirimRolu { sabah, ogle }

int _saat(BildirimRolu r) => r == BildirimRolu.sabah ? sabahSaat : ogleSaat;

/// §22 onaylı kalıp: "Ünye’de bugünkü cenaze ilanlarını göster" (ilçe seçiliyse ilçe, değilse il).
/// Sayı, ad, cami, saat YAZILMAZ. "Merkez" tek başına anlamsız olduğundan "Kars Merkez" biçiminde yazılır.
String bildirimMetni(String il, String? ilce) {
  final yer = (ilce == null || ilce.isEmpty) ? il : (ilce == 'Merkez' ? '$il Merkez' : ilce);
  return '${ek(yer)} bugünkü cenaze ilanlarını göster';
}

/// Bildirim sorusu (ilk açılış kartı) şimdi gösterilsin mi?
/// [izin] null = evet/hayır cevabı yok. [erteleGunu] = "Şimdi değil" denen gün (ISO). 7 gün dolmadan yeniden sorulmaz.
bool soruZamaniGeldi({required bool? izin, required String? erteleGunu, required String bugun}) {
  if (izin != null) return false;
  if (erteleGunu == null || erteleGunu.isEmpty) return true;
  return bugun.compareTo(gunEkle(erteleGunu, erteleGunSayisi)) >= 0;
}

/// [simdi]'den SONRAKİ ilk gün içi [saat]:00 (bugünse bugün, geçtiyse yarın). Cihaz yerel saati.
DateTime sonrakiPencere(DateTime simdi, int saat) {
  final bugun = DateTime(simdi.year, simdi.month, simdi.day, saat);
  if (bugun.isAfter(simdi)) return bugun;
  return DateTime(simdi.year, simdi.month, simdi.day + 1, saat);
}

/// Bir rolün bir sonraki çalışma anı
DateTime sonrakiCalisma(DateTime simdi, BildirimRolu rol) => sonrakiPencere(simdi, _saat(rol));

bool sessizSaat(DateTime simdi) => simdi.hour >= sessizBaslangic || simdi.hour < sessizBitis;

/// Seçili bölgenin (ilçe == null: tüm il) bugün cenaze günü olan ilanlarının kimlikleri.
/// Kapsam, listede görünenle aynıdır (ilçesi belirtilmemiş/il dışı kayıtlar dahil).
Set<String> bugunIlanlari(IlVerisi v, String? ilce, String bugun) {
  if (!v.kaynakli) return <String>{};
  final s = <String>{};
  for (final l in v.secili(ilce).values) {
    for (final r in l) {
      if (r.cenazeGunu == bugun) s.add(r.id);
    }
  }
  for (final r in v.genel) {
    if (r.cenazeGunu == bugun) s.add(r.id);
  }
  return s;
}

/// Ağa gitmeden önceki ucuz kapı: bu çalışmada veriye bakmaya değer mi?
bool bakmayaDeger({
  required BildirimRolu rol,
  required DateTime simdi,
  required String bugun,
  required bool izinAcik,
  required String? sabahGunu,
  required String? ogleGunu,
}) {
  if (!izinAcik || sessizSaat(simdi)) return false;
  if (rol == BildirimRolu.sabah) return sabahGunu != bugun;
  // Öğle: yalnız sabah bildirimi gönderilmişse ve ikinci bildirim henüz gitmemişse
  return sabahGunu == bugun && ogleGunu != bugun;
}

/// Veri geldikten sonra karar. Sabah: bugün ilan varsa gönder. Öğle: sabah bildiriminden sonra YENİ ilan
/// (sabah bildiriminde görülmeyen) düştüyse gönder. Günde en çok 2.
bool bildirimGonderilsin({
  required BildirimRolu rol,
  required Set<String> bugunkuler,
  required Set<String> sabahGorulen,
}) {
  if (bugunkuler.isEmpty) return false;
  if (rol == BildirimRolu.sabah) return true;
  return bugunkuler.any((id) => !sabahGorulen.contains(id));
}
