# Sahibine düşen 4 adım (14.10.2026 gece) — her biri 1–3 dakika, sıra önemli değil

## A. GitHub secret: KC_ANAHTAR (veri kapısı anahtarı)
1. Değer: `cenaze-uygulamasi/deploy/.kc-anahtar` dosyasının tek satırı (Mac'te açıp kopyalayın; bana yazmayın).
2. github.com/hllerdgn80-code/cenaze-veri → Settings → Secrets and variables → Actions → **New repository secret** → Name `KC_ANAHTAR` → Secret: yapıştır → Add secret.

## B. Cloudflare API belirteci + GitHub secret: CLOUDFLARE_API_TOKEN (veri yayını için; şu an Pages boş)
1. dash.cloudflare.com → sağ üst profil → **My Profile → API Tokens → Create Token → Create Custom Token**: Name `cenaze-pages`; Permissions: **Account · Cloudflare Pages · Edit**; Account Resources: hesabınız; Continue → Create Token → değeri kopyalayın.
2. Aynı değeri iki yere: (a) GitHub secret `CLOUDFLARE_API_TOKEN` (A'daki yol); (b) Mac'te: `pbpaste > ~/Desktop/model-arastirmasi/haber-motoru/.cf/api-token` (cf_api.py için).

## C. Cloudflare güvenlik (dashboard; API belirteci bölge ayarına yetmiyor)
dash.cloudflare.com → kimincenazesi.com → Security → Settings → Security level **High**; Bots → **Bot Fight Mode: On**.

## D. Play: 0.1.2 paketi
Chrome'daki "Yeni sürüm" sayfasında **Yükle** → masaüstü `KIMIN-CENAZESI-PLAY-11.aab`. (0.1.3 için A ve B tamamlanmalı; sonra derleme/gönderim bende.)
