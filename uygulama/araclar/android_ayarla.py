#!/usr/bin/env python3
"""CI'da `flutter create` sonrası Android iskeletini uygulamaya göre ayarlar (uygulama/ klasöründen çalıştırılır).
1) Paket adı (applicationId) = com.kimincenazesi.app   2) Uygulama adı = "Kimin Cenazesi"
3) Yalnız İNTERNET izni (başka izin yok)               4) mailto bağlantıları için <queries>
5) İmza: ANDROID_KEYSTORE_BASE64 + şifreler ortam değişkenlerinde varsa release imzası kurulur;
   yoksa şablonun hata ayıklama (debug) imzası kalır ve GITHUB_OUTPUT'a imzali=false yazılır.
Şifreler ekrana YAZILMAZ; anahtar dosyası yalnız CI makinesinde, derleme süresince durur."""
import base64, os, pathlib, re, sys

U = pathlib.Path.cwd()
A = U / "android"
UYGULAMA_KIMLIGI = "com.kimincenazesi.app"


def cikti(ad, deger):
    yol = os.environ.get("GITHUB_OUTPUT")
    if yol:
        with open(yol, "a") as f:
            f.write(f"{ad}={deger}\n")
    print(f"{ad}={deger}")


def manifest():
    m = A / "app/src/main/AndroidManifest.xml"
    s = m.read_text(encoding="utf-8")
    s = re.sub(r'android:label="[^"]*"', 'android:label="Kimin Cenazesi"', s, count=1)
    if "android.permission.INTERNET" not in s:
        s = s.replace("<application", '<uses-permission android:name="android.permission.INTERNET"/>\n    <application', 1)
    mailto = ('<intent>\n            <action android:name="android.intent.action.SENDTO"/>\n'
              '            <data android:scheme="mailto"/>\n        </intent>')
    if 'android:scheme="mailto"' not in s:
        if "<queries>" in s:
            s = s.replace("<queries>", "<queries>\n        " + mailto, 1)
        else:
            s = s.replace("</manifest>", "    <queries>\n        " + mailto + "\n    </queries>\n</manifest>", 1)
    m.write_text(s, encoding="utf-8")
    print("AndroidManifest.xml ayarlandı")


def gradle_dosyasi():
    for ad in ("build.gradle.kts", "build.gradle"):
        p = A / "app" / ad
        if p.exists():
            return p
    sys.exit("android/app/build.gradle(.kts) bulunamadı — `flutter create` çalıştı mı?")


def kimlik(p):
    s = p.read_text(encoding="utf-8")
    if p.suffix == ".kts":
        s, n = re.subn(r'applicationId\s*=\s*"[^"]*"', f'applicationId = "{UYGULAMA_KIMLIGI}"', s)
    else:
        s, n = re.subn(r'applicationId\s+"[^"]*"', f'applicationId "{UYGULAMA_KIMLIGI}"', s)
    if n != 1:
        sys.exit("applicationId satırı bulunamadı")
    p.write_text(s, encoding="utf-8")
    print("applicationId =", UYGULAMA_KIMLIGI)


def imza(p):
    b64 = os.environ.get("ANDROID_KEYSTORE_BASE64", "").strip()
    sifre = os.environ.get("ANDROID_KEYSTORE_PASSWORD", "")
    takma = os.environ.get("ANDROID_KEY_ALIAS", "")
    ksifre = os.environ.get("ANDROID_KEY_PASSWORD", "") or sifre
    if not (b64 and sifre and takma):
        print("::warning::İmza anahtarı (ANDROID_KEYSTORE_* secret'ları) yok: hata ayıklama imzalı APK üretilecek, "
              "Play Console'a yüklenecek AAB üretilmeyecek. Kurulum: deploy/ANDROID-IMZA.md")
        cikti("imzali", "false")
        return
    (A / "app/yukleme-anahtari.jks").write_bytes(base64.b64decode(b64))
    (A / "key.properties").write_text(
        f"storePassword={sifre}\nkeyPassword={ksifre}\nkeyAlias={takma}\nstoreFile=yukleme-anahtari.jks\n",
        encoding="utf-8")
    s = p.read_text(encoding="utf-8")
    if p.suffix == ".kts":
        s = "import java.util.Properties\nimport java.io.FileInputStream\n\n" + s
        yukle = ('\nval anahtarAyar = Properties()\n'
                 'val anahtarDosyasi = rootProject.file("key.properties")\n'
                 'if (anahtarDosyasi.exists()) { anahtarAyar.load(FileInputStream(anahtarDosyasi)) }\n')
        # plugins { ... } bloğunun hemen ardına
        i = s.find("plugins {")
        j = s.find("\n}", i) + 2
        s = s[:j] + yukle + s[j:]
        blok = ('    signingConfigs {\n'
                '        create("release") {\n'
                '            keyAlias = anahtarAyar["keyAlias"] as String\n'
                '            keyPassword = anahtarAyar["keyPassword"] as String\n'
                '            storeFile = file(anahtarAyar["storeFile"] as String)\n'
                '            storePassword = anahtarAyar["storePassword"] as String\n'
                '        }\n'
                '    }\n\n')
        s = s.replace("    buildTypes {", blok + "    buildTypes {", 1)
        s, n = re.subn(r'signingConfig\s*=\s*signingConfigs\.getByName\("debug"\)',
                       'signingConfig = signingConfigs.getByName("release")', s)
    else:
        yukle = ('\ndef anahtarAyar = new Properties()\n'
                 'def anahtarDosyasi = rootProject.file("key.properties")\n'
                 'if (anahtarDosyasi.exists()) { anahtarAyar.load(new FileInputStream(anahtarDosyasi)) }\n')
        i = s.find("plugins {")
        j = s.find("\n}", i) + 2
        s = s[:j] + yukle + s[j:]
        blok = ('    signingConfigs {\n'
                '        release {\n'
                '            keyAlias anahtarAyar["keyAlias"]\n'
                '            keyPassword anahtarAyar["keyPassword"]\n'
                '            storeFile file(anahtarAyar["storeFile"])\n'
                '            storePassword anahtarAyar["storePassword"]\n'
                '        }\n'
                '    }\n\n')
        s = s.replace("    buildTypes {", blok + "    buildTypes {", 1)
        s, n = re.subn(r'signingConfig\s*=?\s*signingConfigs\.debug', 'signingConfig = signingConfigs.release', s)
    if n != 1:
        sys.exit("release imza satırı bulunamadı (şablon değişmiş olabilir)")
    p.write_text(s, encoding="utf-8")
    print("release imzası kuruldu")
    cikti("imzali", "true")


if __name__ == "__main__":
    manifest()
    g = gradle_dosyasi()
    kimlik(g)
    imza(g)
