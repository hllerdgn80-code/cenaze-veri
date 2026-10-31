#!/usr/bin/env python3
"""CI'da `flutter create --platforms ios` sonrası iOS iskeletini uygulamaya göre ayarlar (uygulama/ klasöründen çalıştırılır).
Kullanım:  python3 araclar/ios_ayarla.py [ios_klasoru]      (varsayılan: ./ios)
1) Info.plist: ITSAppUsesNonExemptEncryption=false · CFBundleDisplayName="Kimin Cenazesi" · yalnız dikey yön (iPhone + iPad anahtarı).
   CFBundleShortVersionString / CFBundleVersion Flutter değişkenleri ($(FLUTTER_BUILD_NAME)/$(FLUTTER_BUILD_NUMBER)) olarak KALIR.
   LSApplicationQueriesSchemes EKLENMEZ (uygulama canLaunchUrl kullanmıyor).
2) project.pbxproj: paket kimliği com.kimincenazesi.app (+ .RunnerTests), TARGETED_DEVICE_FAMILY = 1 (yalnız iPhone).
   IPHONEOS_DEPLOYMENT_TARGET'a DOKUNULMAZ, bulunan değer yazdırılır. Beklenen sayı tutmazsa HATA (sessiz geçmez).
3) Ortam değişkeni KC_IOS_TEAM_ID (10 karakter, A-Z0-9) varsa DEVELOPMENT_TEAM satırları eklenir/değiştirilir; yoksa dokunulmaz.
   CODE_SIGN_STYLE'a dokunulmaz (Codemagic `xcode-project use-profiles` imza ayarını yapar).
4) İkon yapılandırması flutter_launcher_icons-ios.yaml yoksa yazılır. Betik dart ÇAĞIRMAZ; CI şu adımı ayrıca çalıştırır:
       dart run flutter_launcher_icons -f flutter_launcher_icons-ios.yaml
   (1024x1024, alfa kanalsız PNG: remove_alpha_ios: true)
Gizli değer yazdırılmaz; çıktı GITHUB_OUTPUT'a da yazılır."""
import os, pathlib, re, sys

I = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ios")
UYGULAMA_KIMLIGI = "com.kimincenazesi.app"
ESKI_KIMLIK = "com.kimincenazesi.kiminCenazesi"
GOSTERIM_ADI = "Kimin Cenazesi"
# Flutter 3.47 şablonu: Runner (Debug/Release/Profile) = 3 ana kimlik, RunnerTests (Debug/Release/Profile) = 3 test kimliği,
# Runner proje düzeyi (Debug/Release/Profile) = 3 TARGETED_DEVICE_FAMILY. Şablon değişirse burası bilerek DURDURUR.
BEKLENEN_ANA, BEKLENEN_TEST, BEKLENEN_AILE = 3, 3, 3
IKON_YAML = """# iOS simgesi: `dart run flutter_launcher_icons -f flutter_launcher_icons-ios.yaml` (ios/ klasörü `flutter create` ile üretildikten sonra).
# Android simgesi pubspec.yaml'daki flutter_launcher_icons bölümüyle ayrıca üretilir.
flutter_launcher_icons:
  android: false
  ios: true
  image_path: "assets/ikon/ikon.png"
  remove_alpha_ios: true
"""


def cikti(ad, deger):
    yol = os.environ.get("GITHUB_OUTPUT")
    if yol:
        with open(yol, "a") as f:
            f.write(f"{ad}={deger}\n")
    print(f"{ad}={deger}")


def hata(mesaj):
    sys.exit(f"HATA: {mesaj}")


def plist():
    p = I / "Runner/Info.plist"
    if not p.exists():
        hata(f"{p} yok — `flutter create --platforms ios` çalıştı mı?")
    s = p.read_text(encoding="utf-8")

    # ITSAppUsesNonExemptEncryption = false
    if "ITSAppUsesNonExemptEncryption" in s:
        s, n = re.subn(r"(<key>ITSAppUsesNonExemptEncryption</key>\s*)<(?:true|false)/>", r"\1<false/>", s)
        if n != 1:
            hata("ITSAppUsesNonExemptEncryption değeri tanınmadı")
    else:
        s, n = re.subn(r"</dict>\s*</plist>", "\t<key>ITSAppUsesNonExemptEncryption</key>\n\t<false/>\n</dict>\n</plist>", s, count=1)
        if n != 1:
            hata("Info.plist kapanışı bulunamadı (şifreleme anahtarı eklenemedi)")

    # CFBundleDisplayName
    if "<key>CFBundleDisplayName</key>" in s:
        s, n = re.subn(r"(<key>CFBundleDisplayName</key>\s*)<string>[^<]*</string>", rf"\1<string>{GOSTERIM_ADI}</string>", s)
        if n != 1:
            hata("CFBundleDisplayName değeri tanınmadı")
    else:
        s, n = re.subn(r"(<key>CFBundleDevelopmentRegion</key>\s*<string>[^<]*</string>\n)",
                       lambda m: m.group(1) + f"\t<key>CFBundleDisplayName</key>\n\t<string>{GOSTERIM_ADI}</string>\n", s, count=1)
        if n != 1:
            hata("CFBundleDevelopmentRegion bulunamadı (görünen ad eklenemedi)")

    # Yön: yalnız dikey (iPhone ve iPad anahtarı)
    dikey = "<array>\n\t\t<string>UIInterfaceOrientationPortrait</string>\n\t</array>"
    for anahtar in ("UISupportedInterfaceOrientations", "UISupportedInterfaceOrientations~ipad"):
        s, n = re.subn(rf"(<key>{re.escape(anahtar)}</key>\s*)<array>.*?</array>", lambda m: m.group(1) + dikey, s, count=1, flags=re.S)
        if n != 1:
            hata(f"{anahtar} bulunamadı (şablon değişmiş olabilir)")

    # Sürüm değişkenlerine dokunulmaz ama bozulmadıklarını doğrula
    for k, v in (("CFBundleShortVersionString", "$(FLUTTER_BUILD_NAME)"), ("CFBundleVersion", "$(FLUTTER_BUILD_NUMBER)")):
        if not re.search(rf"<key>{k}</key>\s*<string>{re.escape(v)}</string>", s):
            hata(f"{k} artık {v} değil (şablon değişmiş olabilir)")
    p.write_text(s, encoding="utf-8")
    print("Info.plist ayarlandı (şifreleme muafiyeti, görünen ad, yalnız dikey)")


def proje():
    p = I / "Runner.xcodeproj/project.pbxproj"
    if not p.exists():
        hata(f"{p} yok")
    s = p.read_text(encoding="utf-8")

    # önce RunnerTests, sonra ana kimlik (ana desen ".RunnerTests"i yakalamaz: sonu ';' ister)
    s, n_test = re.subn(rf"PRODUCT_BUNDLE_IDENTIFIER = {re.escape(ESKI_KIMLIK)}\.RunnerTests;",
                        f"PRODUCT_BUNDLE_IDENTIFIER = {UYGULAMA_KIMLIGI}.RunnerTests;", s)
    s, n_ana = re.subn(rf"PRODUCT_BUNDLE_IDENTIFIER = {re.escape(ESKI_KIMLIK)};",
                       f"PRODUCT_BUNDLE_IDENTIFIER = {UYGULAMA_KIMLIGI};", s)
    s, n_aile = re.subn(r'TARGETED_DEVICE_FAMILY = "1,2";', "TARGETED_DEVICE_FAMILY = 1;", s)
    # toplam = yeni yazılmış + zaten düzeltilmiş (betik ikinci kez çalışırsa da geçer)
    t_ana = len(re.findall(rf"PRODUCT_BUNDLE_IDENTIFIER = {re.escape(UYGULAMA_KIMLIGI)};", s))
    t_test = len(re.findall(rf"PRODUCT_BUNDLE_IDENTIFIER = {re.escape(UYGULAMA_KIMLIGI)}\.RunnerTests;", s))
    t_aile = len(re.findall(r"TARGETED_DEVICE_FAMILY = 1;", s))
    print(f"değiştirilen: ana kimlik {n_ana} · RunnerTests kimliği {n_test} · TARGETED_DEVICE_FAMILY {n_aile}")
    print(f"sonuç (toplam): ana kimlik {t_ana} · RunnerTests {t_test} · TARGETED_DEVICE_FAMILY=1 {t_aile}")
    if (t_ana, t_test, t_aile) != (BEKLENEN_ANA, BEKLENEN_TEST, BEKLENEN_AILE) or '"1,2"' in s:
        hata(f"beklenen sayılar {BEKLENEN_ANA}/{BEKLENEN_TEST}/{BEKLENEN_AILE}, bulunan {t_ana}/{t_test}/{t_aile} — şablon değişmiş, betik güncellenmeli")
    if any(ESKI_KIMLIK in k for k in re.findall(r"PRODUCT_BUNDLE_IDENTIFIER = ([^;]+);", s)):
        hata("eski paket kimliği hâlâ var")

    hedefler = sorted(set(re.findall(r"IPHONEOS_DEPLOYMENT_TARGET = ([^;]+);", s)))
    print("IPHONEOS_DEPLOYMENT_TARGET (dokunulmadı):", ", ".join(hedefler) or "yok")
    cikti("ios_hedef_surum", ",".join(hedefler))

    takim = os.environ.get("KC_IOS_TEAM_ID", "").strip()
    if takim:
        if not re.fullmatch(r"[A-Z0-9]{10}", takim):
            hata("KC_IOS_TEAM_ID 10 karakterlik A-Z0-9 olmalı")
        # her PRODUCT_BUNDLE_IDENTIFIER satırının bulunduğu buildSettings bloğunda DEVELOPMENT_TEAM ekle/değiştir
        s, n_var = re.subn(r"DEVELOPMENT_TEAM = [^;]*;", f"DEVELOPMENT_TEAM = {takim};", s)
        # DEVELOPMENT_TEAM'i olmayan bloklara ekleme: blok başına tek kez (önceki 12 satırda yoksa)
        satirlar = s.split("\n")
        cikis, eklenen = [], 0
        for i, l in enumerate(satirlar):
            if "PRODUCT_BUNDLE_IDENTIFIER = " in l and not any("DEVELOPMENT_TEAM = " in x for x in satirlar[max(0, i - 25):i + 25]):
                girinti = l[: len(l) - len(l.lstrip())]
                cikis.append(f"{girinti}DEVELOPMENT_TEAM = {takim};")
                eklenen += 1
            cikis.append(l)
        s = "\n".join(cikis)
        print(f"DEVELOPMENT_TEAM: {n_var} değiştirildi, {eklenen} eklendi (değer yazdırılmaz)")
    else:
        print("KC_IOS_TEAM_ID yok: DEVELOPMENT_TEAM'e dokunulmadı (Codemagic imza adımı ayarlar)")
    p.write_text(s, encoding="utf-8")


def ikon_yapilandirmasi():
    y = pathlib.Path("flutter_launcher_icons-ios.yaml")
    if not y.exists():
        y.write_text(IKON_YAML, encoding="utf-8")
        print("flutter_launcher_icons-ios.yaml yazıldı")
    print("SIRADAKİ CI ADIMI: dart run flutter_launcher_icons -f flutter_launcher_icons-ios.yaml")


if __name__ == "__main__":
    if not I.is_dir():
        hata(f"{I} klasörü yok — önce `flutter create --platforms ios .`")
    plist()
    proje()
    ikon_yapilandirmasi()
    cikti("ios_ayarlandi", "true")
