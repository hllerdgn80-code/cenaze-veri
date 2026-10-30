#!/usr/bin/env bash
# YEREL flutter analyze + flutter test (30.10.2026). Bu Mac'te `flutter test` "objective_c ... dart assets" diye durur (Command Line Tools SDK bozuk,
# paket yalnız iOS/macOS eklentilerinden gelir, Android uygulaması kullanmaz). Çözüm: uygulamayı GEÇİCİ klasöre kopyala, `objective_c` paketini boş bir
# taslakla değiştir (dependency_overrides) → yerel derleme kancası kalmaz, testler ve analiz koşar. Depodaki pubspec.yaml/pubspec.lock DEĞİŞMEZ.
# Kullanım (uygulama/ klasöründen):  bash araclar/yerel_test.sh [analiz | test/dosya_test.dart ...]   (parametresiz: analiz + tüm testler)
# NOT: test/veri_kapi_test.dart "anahtar dolu" yerelde düşer (kcAnahtar CI'da KC_ANAHTAR secret'ıyla doldurulur); beklenen durumdur.
set -euo pipefail
U="$(cd "$(dirname "$0")/.." && pwd)"
FLUTTER="${FLUTTER_BIN:-$U/../../araclar/flutter-sdk/flutter/bin}"
[ -x "$FLUTTER/flutter" ] || FLUTTER="$U/../araclar/flutter-sdk/flutter/bin"   # 30.10: uygulama/ (kanonik) ve yuklenecek/uygulama/ yerleşimlerinin ikisi de
export PATH="$FLUTTER:$PATH" FLUTTER_SUPPRESS_ANALYTICS=true CI=true
T="$(mktemp -d "${TMPDIR:-/tmp}/kc-yerel-test.XXXXXX")"
trap 'rm -rf "$T"' EXIT
cp -R "$U/lib" "$U/test" "$U/assets" "$U/pubspec.yaml" "$U/analysis_options.yaml" "$T/"
[ -f "$U/pubspec.lock" ] && cp "$U/pubspec.lock" "$T/"
mkdir -p "$T/stub_oc/lib"
printf 'name: objective_c\nversion: 9.9.9\nenvironment:\n  sdk: ">=3.5.0 <4.0.0"\n' > "$T/stub_oc/pubspec.yaml"
echo "// stub" > "$T/stub_oc/lib/objective_c.dart"
printf '\ndependency_overrides:\n  objective_c:\n    path: stub_oc\n' >> "$T/pubspec.yaml"
cd "$T"
flutter pub get >/dev/null
if [ "${1:-}" = "analiz" ]; then flutter analyze --no-fatal-infos; exit 0; fi
if [ $# -eq 0 ]; then flutter analyze --no-fatal-infos || true; fi
flutter test "$@"
