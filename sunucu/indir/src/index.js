// kimincenazesi.com/indir/<dosya> → KV'den akıtır (APK; Pages 25 MB sınırı ve büyük dosya yüklemesi için).
// 21.10.2026 güvenlik duvarı (madde 1, 5): güvenlik başlıkları + beklenmeyen hatada genel 503 (iç bilgi yok).
const IZIN = { "kimin-cenazesi.apk": "application/vnd.android.package-archive" };
const GUVENLIK = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "no-referrer",
  "content-security-policy": "default-src 'none'; frame-ancestors 'none'; sandbox",
  "strict-transport-security": "max-age=31536000",
  "cross-origin-resource-policy": "same-site",
};
const yok = (durum = 404, metin = "Bulunamadı") => new Response(metin, { status: durum, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", ...GUVENLIK } });
export default {
  async fetch(req, env) {
    try {
      const ad = new URL(req.url).pathname.replace(/^\/indir\//, "");
      const tur = IZIN[ad];
      if (!tur || (req.method !== "GET" && req.method !== "HEAD")) return yok();
      const { value, metadata } = await env.DOSYA.getWithMetadata(ad, { type: "stream" });
      if (!value) return yok();
      const h = new Headers({ "content-type": tur, "content-disposition": `attachment; filename="${ad}"`, "cache-control": "public, max-age=300", ...GUVENLIK });
      if (metadata && metadata.boyut) h.set("content-length", String(metadata.boyut));
      return new Response(req.method === "HEAD" ? null : value, { headers: h });
    } catch (e) {
      console.error("indir hata:", String((e && e.stack) || e).slice(0, 300));
      return yok(503, "Geçici hata");
    }
  },
};
