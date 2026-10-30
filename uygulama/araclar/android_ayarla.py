#!/usr/bin/env python3
"""CI'da `flutter create` sonrası Android iskeletini uygulamaya göre ayarlar (uygulama/ klasöründen çalıştırılır).
1) Paket adı (applicationId) = com.kimincenazesi.app   2) Uygulama adı = "Kimin Cenazesi"
3) İzinler: İNTERNET + POST_NOTIFICATIONS (0.1.4 günlük cenaze bildirimi; tam alarm izni YOK)   4) mailto bağlantıları için <queries>
   0.1.4: bildirim simgesi (tek renkli hilal) + flutter_local_notifications için Gradle ayarları (desugaring, compileSdk >= 37)
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
    if "android.permission.POST_NOTIFICATIONS" not in s:
        s = s.replace("<application", '<uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>\n    <application', 1)
    mailto = ('<intent>\n            <action android:name="android.intent.action.SENDTO"/>\n'
              '            <data android:scheme="mailto"/>\n        </intent>')
    if 'android:scheme="mailto"' not in s:
        if "<queries>" in s:
            s = s.replace("<queries>", "<queries>\n        " + mailto, 1)
        else:
            s = s.replace("</manifest>", "    <queries>\n        " + mailto + "\n    </queries>\n</manifest>", 1)
    m.write_text(s, encoding="utf-8")
    print("AndroidManifest.xml ayarlandı")


HILAL = """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M12,3c-4.97,0 -9,4.03 -9,9s4.03,9 9,9s9,-4.03 9,-9c0,-0.46 -0.04,-0.92 -0.1,-1.36c-0.98,1.37 -2.58,2.26 -4.4,2.26c-2.98,0 -5.4,-2.42 -5.4,-5.4c0,-1.81 0.89,-3.42 2.26,-4.4C12.92,3.04 12.46,3,12,3L12,3z"/>
</vector>
"""
KEEP = """<?xml version="1.0" encoding="utf-8"?>
<resources xmlns:tools="http://schemas.android.com/tools" tools:keep="@drawable/ic_bildirim" />
"""


def bildirim_simgesi():
    """Küçük bildirim simgesi: tek renkli (Android bildirim çubuğu yalnız alfa kanalını kullanır). Ad: ic_bildirim."""
    res = A / "app/src/main/res"
    (res / "drawable").mkdir(parents=True, exist_ok=True)
    (res / "raw").mkdir(parents=True, exist_ok=True)
    (res / "drawable/ic_bildirim.xml").write_text(HILAL, encoding="utf-8")
    (res / "raw/keep.xml").write_text(KEEP, encoding="utf-8")  # küçültme (shrinkResources) simgeyi silmesin
    print("bildirim simgesi yazıldı")


def gradle_bildirim(p):
    """flutter_local_notifications: çekirdek kütüphane desugaring + compileSdk >= 37 (eklenti README'si).
    Şablon değişmişse HATA vermez, uyarı yazar; derleme hatası ayrıca görünür."""
    s = p.read_text(encoding="utf-8")
    kts = p.suffix == ".kts"
    if "oreLibraryDesugaring" not in s:
        bayrak = "isCoreLibraryDesugaringEnabled = true" if kts else "coreLibraryDesugaringEnabled true"
        if "compileOptions {" in s:
            s = s.replace("compileOptions {", "compileOptions {\n        " + bayrak, 1)
        else:
            s = s.replace("android {", "android {\n    compileOptions {\n        " + bayrak + "\n    }", 1)
        bagimlilik = ('\ndependencies {\n    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")\n}\n' if kts
                      else "\ndependencies {\n    coreLibraryDesugaring 'com.android.tools:desugar_jdk_libs:2.1.4'\n}\n")
        s += bagimlilik
    m = re.search(r"compileSdk(?:Version)?\s*=?\s*(\S+)", s)
    if m:
        deger = m.group(1)
        yeni = None
        if deger.startswith("flutter."):
            yeni = "compileSdk = maxOf(37, flutter.compileSdkVersion)" if kts else "compileSdk Math.max(37, flutter.compileSdkVersion)"
        elif deger.isdigit() and int(deger) < 37:
            yeni = "compileSdk = 37" if kts else "compileSdk 37"
        if yeni:
            s = s[:m.start()] + yeni + s[m.end():]
    else:
        print("::warning::compileSdk satırı bulunamadı: flutter_local_notifications için 37 gerekebilir")
    p.write_text(s, encoding="utf-8")
    print("Gradle: desugaring + compileSdk ayarlandı")

UCTAN_UCA_IMPORT = ("import android.os.Bundle", "import androidx.core.view.WindowCompat")
UCTAN_UCA_SATIR = "        WindowCompat.setDecorFitsSystemWindows(window, false)\n"


def uctan_uca_kotlin():
    """30.10.2026 Play önerisi "uçtan uca ekran": SDK 35+ hedefleyen uygulamalar Android 15'te varsayılan uçtan uca çizilir.
    MainActivity.onCreate (super'den sonra) WindowCompat.setDecorFitsSystemWindows(window, false) ekler (= enableEdgeToEdge'in çekirdeği).
    Sınıf/onCreate tanınmazsa derleme DURUR (sessiz geçmez)."""
    ma = next(iter(sorted((A / "app/src/main").rglob("MainActivity.kt"))), None)
    if not ma:
        sys.exit("MainActivity.kt yok (uçtan uca yaması uygulanamadı)")
    k = ma.read_text(encoding="utf-8")
    if "setDecorFitsSystemWindows" in k:
        print("uçtan uca yaması zaten var")
        return
    for im in UCTAN_UCA_IMPORT:
        if im not in k:
            k = re.sub(r"(package [^\n]+\n)", lambda m, im=im: m.group(1) + "\n" + im, k, count=1)
    if re.search(r"override fun onCreate\(", k):
        k, n = re.subn(r"(super\.onCreate\(savedInstanceState\)[^\n]*\n)", lambda m: m.group(1) + UCTAN_UCA_SATIR, k, count=1)
        if n != 1:
            sys.exit("MainActivity.onCreate içinde super.onCreate(savedInstanceState) bulunamadı (uçtan uca yaması)")
    else:
        govde = ("    override fun onCreate(savedInstanceState: Bundle?) {\n        super.onCreate(savedInstanceState)\n"
                 + UCTAN_UCA_SATIR + "    }\n")
        m = re.search(r"class MainActivity\s*:\s*(\w+)\(\)\s*(\{\s*\}|\{)?", k)
        if not m:
            sys.exit("MainActivity sınıfı tanınmadı (uçtan uca yaması)")
        if m.group(2) is None:
            yer = "class MainActivity : %s() {\n%s}\n" % (m.group(1), govde)
        elif m.group(2) == "{":
            yer = "class MainActivity : %s() {\n%s" % (m.group(1), govde)
        else:
            yer = "class MainActivity : %s() {\n%s}\n" % (m.group(1), govde)
        k = k[:m.start()] + yer + k[m.end():]
    ma.write_text(k, encoding="utf-8")
    print("uçtan uca yaması uygulandı:", ma)


def uctan_uca_stil():
    """windowOptOutEdgeToEdgeEnforcement (Android 15 uçtan uca zorunluluğundan çıkış) varsa SİLİNİR; uygulama uçtan uca olmalı."""
    for st in sorted((A / "app/src/main/res").glob("values*/*.xml")):
        t = st.read_text(encoding="utf-8")
        t2 = re.sub(r"[ \t]*<item[^>]*windowOptOutEdgeToEdgeEnforcement[^>]*>[^<]*</item>\n?", "", t)
        if t2 != t:
            st.write_text(t2, encoding="utf-8")
            print("windowOptOutEdgeToEdgeEnforcement silindi:", st)


def gradle_uctan_uca(p):
    """androidx.core (WindowCompat) açıkça bağımlılık; targetSdk >= 35 (Flutter 3.47 varsayılanı 36: yalnız güvence)."""
    s = p.read_text(encoding="utf-8")
    kts = p.suffix == ".kts"
    if "androidx.core:core" not in s:
        s += ('\ndependencies {\n    implementation("androidx.core:core:1.15.0")\n}\n' if kts
              else "\ndependencies {\n    implementation 'androidx.core:core:1.15.0'\n}\n")
    m = re.search(r"targetSdk(?:Version)?\s*=?\s*(\S+)", s)
    if m:
        deger = m.group(1)
        yeni = None
        if deger.startswith("flutter."):
            yeni = "targetSdk = maxOf(35, flutter.targetSdkVersion)" if kts else "targetSdk Math.max(35, flutter.targetSdkVersion)"
        elif deger.isdigit() and int(deger) < 35:
            yeni = "targetSdk = 35" if kts else "targetSdk 35"
        if yeni:
            s = s[:m.start()] + yeni + s[m.end():]
    else:
        print("::warning::targetSdk satırı bulunamadı (Flutter varsayılanı 36 geçerli)")
    p.write_text(s, encoding="utf-8")
    print("Gradle: androidx.core + targetSdk>=35 ayarlandı")


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
    bildirim_simgesi()
    gradle_bildirim(g)
    gradle_uctan_uca(g)
    uctan_uca_kotlin()
    uctan_uca_stil()
    # (16.10.2026) ML Kit kalktı -> H68 R8 kuralları (proguard-rules.pro) artık gerekmiyor
    imza(g)
