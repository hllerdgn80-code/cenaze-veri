#!/usr/bin/env bash
# 16.10.2026 H76: ortak, cakismaya dayanikli push. Kullanim: bash araclar/guvenli_push.sh [dal]
# Onkosul: commit zaten atilmis olmali. En cok 5 deneme; her denemede `git pull --rebase --autostash -X theirs` + push.
# -X theirs: rebase sirasinda "theirs" = yeniden oynatilan YEREL commit (bu kosunun urettigi en yeni veri); cakisan hunk'ta yerel veri kazanir.
# Denemeler arasi 10-30 sn rastgele bekleme (iki is ayni anda yeniden deneyip yine carpismasin).
# 5'inde de olmazsa ::warning:: yazar ve BASARILI (0) biter: kosu kirmizi olmaz, veri sonraki turda gider (veri-tr her tur yeniden uretilir,
# kesif durumu dosyada kalir). Uyari metni "PUSH_VAZGECILDI" icerir; bekci (kc_saglik.py) basarili kosularda bu notu arar ve kayit tutar.
dal="${1:-${GITHUB_REF_NAME:-main}}"
son=""
for i in 1 2 3 4 5; do
  if son="$(git pull --rebase --autostash -X theirs origin "$dal" 2>&1)"; then
    if son="$(git push origin "HEAD:$dal" 2>&1)"; then
      echo "push tamam (deneme $i)"
      exit 0
    fi
  else
    git rebase --abort >/dev/null 2>&1 || true   # yarim kalan rebase sonraki denemeyi bozmasin (autostash geri gelir)
  fi
  echo "push denemesi $i/5 basarisiz: $(printf '%s' "$son" | tail -n 3 | tr '\n' ' ')"
  [ "$i" -lt 5 ] && sleep $((10 + RANDOM % 21))
done
echo "::warning::PUSH_VAZGECILDI: 5 denemede depoya yazilamadi; veri sonraki turda gider. Son hata: $(printf '%s' "$son" | tail -n 3 | tr '\n' ' ')"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "## PUSH_VAZGECILDI - veri depoya yazilamadi (5 deneme); sonraki turda gider" >> "$GITHUB_STEP_SUMMARY"
exit 0
