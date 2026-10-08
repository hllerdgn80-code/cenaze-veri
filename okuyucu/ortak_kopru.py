"""GitHub (yurt dışı) sunucularından açılmayan ama Cloudflare köprü Worker'ı üzerinden açılan kaynaklar.
CENAZE_KOPRU ve CENAZE_KOPRU_ANAHTAR ortam değişkenleri doluysa ve adres izinli alan adındaysa istek köprüye yönlendirilir;
değilse (ör. Mac) hiçbir şey değişmez."""
import os, urllib.parse

KOPRU_ALANLAR = {  "www.arnavutkoy.bel.tr"}


def kopru_url(url):
    kopru = os.environ.get("CENAZE_KOPRU", "").rstrip("/")
    anahtar = os.environ.get("CENAZE_KOPRU_ANAHTAR", "")
    if kopru and anahtar and urllib.parse.urlparse(url).hostname in KOPRU_ALANLAR:
        return f"{kopru}/?u={urllib.parse.quote(url, safe='')}", {"X-Kopru-Anahtar": anahtar}
    return url, {}
