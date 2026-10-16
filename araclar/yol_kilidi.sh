#!/usr/bin/env bash
# 16.10.2026 H76: DEPO YOLU KILIDI. Izlenen dosyalar arasinda satir sonu / ':' / 200+ karakter / 30+ klasor derinligi olan yol varsa
# ::warning:: ile listeler ve (en cok 20 yol) `git rm --cached` + commit + push ile depodan temizler. Mac runner'da (PATH_MAX 1024) checkout'u
# ENAMETOOLONG ile dusuren 14-15.10 olayinin (liste tek yola donusmustu) tekrarini engeller. Bu depoda mesru yolda bu karakterler/uzunluk yoktur
# (15.10 ag aci taramasi: 796 girdinin yalniz bozuk zincir 86 girdisi eslesti). 20'den fazla eslesme = bir hata/saldiri belirtisi: SILMEZ, yalniz uyarir.
# Hicbir kosulda kosuyu kirmaz (exit 0).
set -u
kotu=()
n=0
while IFS= read -r -d '' p; do
  n=$((n+1))
  kes="${p//[^\/]/}"
  case "$p" in
    *$'\n'*|*:*) kotu+=("$p") ;;
    *) if [ "${#p}" -gt 200 ] || [ "${#kes}" -gt 30 ]; then kotu+=("$p"); fi ;;
  esac
done < <(git -c core.quotepath=off ls-files -z)
echo "izlenen dosya: $n, bozuk yol: ${#kotu[@]}"
[ "${#kotu[@]}" -eq 0 ] && exit 0
for p in "${kotu[@]:0:20}"; do echo "::warning::bozuk depo yolu (${#p} karakter): $(printf '%q' "${p:0:100}")"; done
if [ "${#kotu[@]}" -gt 20 ]; then
  echo "::warning::20'den fazla bozuk yol (${#kotu[@]}): otomatik silme YAPILMADI, elle bakilmali"
  exit 0
fi
git config user.name "cenaze-bot"
git config user.email "cenaze-bot@users.noreply.github.com"
for p in "${kotu[@]}"; do git rm --cached -q -- "$p" || echo "::warning::git rm basarisiz"; done
if git diff --cached --quiet; then exit 0; fi
git commit -q -m "yol kilidi: bozuk depo yolu temizlendi (${#kotu[@]})"
bash araclar/guvenli_push.sh "${GITHUB_REF_NAME:-main}"
exit 0
