const IZIN = ["ebelediye.kocaeli.bel.tr","ebelediye.aksaray.bel.tr","van.bel.tr","www.van.bel.tr","mebis.malatya.bel.tr","www.milas.bel.tr","www.arnavutkoy.bel.tr","www.19mayis.bel.tr"];
// 21.10.2026 güvenlik duvarı (madde 3, 5): anahtar karşılaştırması SABİT ZAMANLI; beklenmeyen hata genel 502 (iç bilgi yok).
function esit(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let f = x.length ^ y.length;
  const n = Math.max(x.length, y.length);
  for (let i = 0; i < n; i++) f |= (x[i] || 0) ^ (y[i] || 0);
  return f === 0;
}
export default {
  async fetch(req, env) {
    try {
      if (!env.ANAHTAR || !esit(req.headers.get("X-Kopru-Anahtar") || "", env.ANAHTAR)) return new Response("yetkisiz", {status: 403});
      const u = new URL(req.url).searchParams.get("u");
      let hedef; try { hedef = new URL(u); } catch (e) { return new Response("gecersiz", {status: 400}); }
      if (hedef.protocol !== "https:" || !IZIN.includes(hedef.hostname)) return new Response("izinsiz alan adi", {status: 403});
      const h = new Headers();
      for (const k of ["user-agent","content-type","accept","accept-language","cookie","origin","referer"]) { const v = req.headers.get(k); if (v) h.set(k, v); }
      const init = {method: req.method, headers: h, redirect: "follow", cf: {cacheTtl: 0}};
      if (req.method === "POST") {
        const cl = parseInt(req.headers.get("content-length") || "0", 10);
        if (cl > 1_000_000) return new Response("govde buyuk", {status: 413});   // 21.10.2026: belediye formlari kucuktur
        init.body = await req.arrayBuffer();
      }
      const r = await fetch(hedef.toString(), init);
      const govde = await r.arrayBuffer();   // akis yerine tamamini tamponla: chunked yanit yarida kesilmesin
      const o = new Headers(r.headers); o.set("X-Kopru-Colo", req.cf && req.cf.colo || "?");
      o.set("X-Content-Type-Options", "nosniff");
      for (const k of ["content-encoding","content-length","transfer-encoding"]) o.delete(k);
      return new Response(govde, {status: r.status, headers: o});
    } catch (e) {
      console.error("kopru hata:", String((e && e.stack) || e).slice(0, 300));
      return new Response("kopru hatasi", {status: 502});
    }
  }
};
