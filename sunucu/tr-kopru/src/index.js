const IZIN = ["ebelediye.kocaeli.bel.tr","ebelediye.aksaray.bel.tr","van.bel.tr","www.van.bel.tr","mebis.malatya.bel.tr","www.milas.bel.tr","www.arnavutkoy.bel.tr","www.19mayis.bel.tr"];
export default {
  async fetch(req, env) {
    if (req.headers.get("X-Kopru-Anahtar") !== env.ANAHTAR || !env.ANAHTAR) return new Response("yetkisiz", {status: 403});
    const u = new URL(req.url).searchParams.get("u");
    let hedef; try { hedef = new URL(u); } catch (e) { return new Response("gecersiz", {status: 400}); }
    if (hedef.protocol !== "https:" || !IZIN.includes(hedef.hostname)) return new Response("izinsiz alan adi", {status: 403});
    const h = new Headers();
    for (const k of ["user-agent","content-type","accept","accept-language","cookie","origin","referer"]) { const v = req.headers.get(k); if (v) h.set(k, v); }
    const init = {method: req.method, headers: h, redirect: "follow", cf: {cacheTtl: 0}};
    if (req.method === "POST") init.body = await req.arrayBuffer();
    const r = await fetch(hedef.toString(), init);
    const govde = await r.arrayBuffer();   // akis yerine tamamini tamponla: chunked yanit yarida kesilmesin
    const o = new Headers(r.headers); o.set("X-Kopru-Colo", req.cf && req.cf.colo || "?");
    for (const k of ["content-encoding","content-length","transfer-encoding"]) o.delete(k);
    return new Response(govde, {status: r.status, headers: o});
  }
};
