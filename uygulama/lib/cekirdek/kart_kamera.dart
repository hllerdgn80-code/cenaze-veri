// Din görevlisi kartı: YALNIZ uygulama içi kamera (galeri yok) + cihaz içi metin tanıma ile TC karartma (internetsiz) + 1600 px.
// Eklentiler burada toplanır; saf mantık karartma.dart'tadır (testli).
import 'dart:typed_data';

import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';

import 'karartma.dart';

/// Fotoğraf işlenemedi (tanıma/karartma hatası): görüntü gönderilmez, kullanıcı yeniden çeker
class KartIslenemedi implements Exception {
  const KartIslenemedi();
}

/// ML Kit (Latin, cihaz içi) ile satır ve öğe kutuları
Future<List<MetinSatiri>> mlKitTanima(String yol) async {
  final tanici = TextRecognizer(script: TextRecognitionScript.latin);
  try {
    final r = await tanici.processImage(InputImage.fromFilePath(yol));
    return [
      for (final b in r.blocks)
        for (final s in b.lines)
          MetinSatiri([
            for (final e in s.elements)
              MetinOgesi(e.text, Kutu(e.boundingBox.left.round(), e.boundingBox.top.round(), e.boundingBox.right.round(), e.boundingBox.bottom.round())),
          ]),
    ];
  } finally {
    await tanici.close();
  }
}

/// Kamerayı açar; çekilen kartı karartıp 1600 px JPEG olarak döner. İptal -> null. İşlenemezse [KartIslenemedi].
Future<Uint8List?> kartCek() async {
  final x = await ImagePicker().pickImage(source: ImageSource.camera, maxWidth: 2400, maxHeight: 2400, imageQuality: 90);
  if (x == null) return null;
  try {
    return await kartiHazirla(x.path, await x.readAsBytes(), mlKitTanima);
  } catch (_) {
    throw const KartIslenemedi();
  }
}
