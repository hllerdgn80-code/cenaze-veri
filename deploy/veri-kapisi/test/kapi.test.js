import test from "node:test";
import assert from "node:assert/strict";
import { Sayac, kapi, yolIzinli, esit } from "../src/index.js";

class KV {
  constructor() { this.m = new Map(); }
  async get(k) { return this.m.has(k) ? this.m.get(k) : null; }
  async put(k, v) { this.m.set(k, v); }
}
const env = () => ({ KC_ANAHTAR: "gizli-anahtar", KOKEN: "https://o.test", DAKIKA_LIMIT: "60", KAPI: new KV() });
const kaynak = async (u) => u.includes("/html/") ? new Response("<html>", { status: 200, headers: { "Content-Type": "text/html" } })
  : new Response('{"ok":1}', { status: u.includes("/yok/") ? 404 : 200, headers: { "Content-Type": "application/json" } });
const istek = (yol, b = {}, ip = "1.1.1.1") =>
  new Request("https://veri.kimincenazesi.com" + yol, {
    headers: { "X-KC-Anahtar": "gizli-anahtar", "User-Agent": "KiminCenazesi/0.1.3", "CF-Connecting-IP": ip, ...b },
  });

test("başlıksız → 403 boş", async () => {
  const r = await kapi(new Request("https://x.test/veri/ordu/son7gun.json"), env(), kaynak);
  assert.equal(r.status, 403); assert.equal(await r.text(), "");
});
test("yanlış anahtar / yanlış UA → 403", async () => {
  assert.equal((await kapi(istek("/veri/ordu/son7gun.json", { "X-KC-Anahtar": "x" }), env(), kaynak)).status, 403);
  assert.equal((await kapi(istek("/veri/ordu/son7gun.json", { "User-Agent": "curl/8" }), env(), kaynak)).status, 403);
});
test("doğru başlık → 200 JSON + başlıklar", async () => {
  const r = await kapi(istek("/veri/ordu/son7gun.json"), env(), kaynak);
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("Cache-Control"), "private, max-age=120");
  assert.equal(r.headers.get("X-Robots-Tag"), "noindex");
  assert.deepEqual(await r.json(), { ok: 1 });
});
test("kaybettiklerimiz açık", async () => {
  assert.equal((await kapi(istek("/veri/kaybettiklerimiz/bakanlar.json"), env(), kaynak)).status, 200);
  assert.equal((await kapi(istek("/veri/kaybettiklerimiz/tarihte_bugun/10-14.json"), env(), kaynak)).status, 200);
});
test("kapalı yollar → 404", async () => {
  for (const y of ["/veri/ozet.json", "/veri/saglik.json", "/veri/kapi.json", "/veri/yerlestirme-raporu.json", "/veri/_x/son7gun.json",
    "/veri/ordu/_gizli.json", "/veri/ordu/ozet.json", "/", "/veri/", "/veri/ordu/../ozet.json", "/veri/%5Fx/son7gun.json", "/veri/ordu/kaynak.json"]) {
    const r = await kapi(istek(y), env(), kaynak);
    assert.equal(r.status, 404, y); assert.equal(await r.text(), "");
  }
});
test("kaynak 404 → boş 404", async () => {
  const r = await kapi(istek("/veri/yok/son7gun.json"), env(), kaynak);
  assert.equal(r.status, 404); assert.equal(await r.text(), "");
});
test("61. istek → 429; başka IP etkilenmez", async () => {
  const e = env();
  for (let i = 0; i < 60; i++) assert.equal((await kapi(istek("/veri/ordu/son7gun.json"), e, kaynak)).status, 200);
  const r = await kapi(istek("/veri/ordu/son7gun.json"), e, kaynak);
  assert.equal(r.status, 429); assert.equal(await r.text(), "");
  assert.equal((await kapi(istek("/veri/ordu/son7gun.json", {}, "2.2.2.2"), e, kaynak)).status, 200);
});
test("POST → 403; anahtarsız secret → 403", async () => {
  assert.equal((await kapi(new Request("https://x.test/veri/ordu/son7gun.json", { method: "POST" }), env(), kaynak)).status, 403);
  const e = env(); e.KC_ANAHTAR = "";
  assert.equal((await kapi(istek("/veri/ordu/son7gun.json", { "X-KC-Anahtar": "" }), e, kaynak)).status, 403);
});
test("yolIzinli / esit", () => {
  assert.equal(yolIzinli("/veri/ordu/son7gun.json"), "/veri/ordu/son7gun.json");
  assert.equal(yolIzinli("/veri/%E0%A4%A"), null);
  assert.equal(esit("a", "a"), true); assert.equal(esit("a", "ab"), false);
});
test("Pages HTML yedek sayfası → 404", async () => {
  assert.equal((await kapi(istek("/veri/html/son7gun.json"), env(), kaynak)).status, 404);
});
test("LIMITER bağlaması kullanılır", async () => {
  const e = env(); let n = 0; e.LIMITER = { limit: async () => ({ success: ++n <= 2 }) };
  const r = [];
  for (let i = 0; i < 3; i++) r.push((await kapi(istek("/veri/ordu/son7gun.json"), e, kaynak)).status);
  assert.deepEqual(r, [200, 200, 429]);
});
test("Durable Object sayacı: 61. istek 429", async () => {
  const nesneler = new Map();
  const e = env();
  e.SAYAC = { idFromName: (a) => a, get: (id) => { if (!nesneler.has(id)) nesneler.set(id, new Sayac({})); return nesneler.get(id); } };
  let son;
  for (let i = 0; i < 61; i++) son = (await kapi(istek("/veri/ordu/son7gun.json"), e, kaynak)).status;
  assert.equal(son, 429);
});

// 21.10.2026 guvenlik duvari: basarili yanitta guvenlik basliklari, hata yanitlari bos ve basliksiz
test("basarili yanit guvenlik basliklari tasir; hata yaniti bos + basliksiz", async () => {
  const env = { KC_ANAHTAR: "k".repeat(24), KOKEN: "https://kaynak.test", DAKIKA_LIMIT: "60", LIMITER: { limit: async () => ({ success: true }) } };
  const kaynak = async () => new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } });
  const ok = await kapi(new Request("https://veri.test/veri/ordu/son7gun.json", { headers: { "X-KC-Anahtar": env.KC_ANAHTAR, "User-Agent": "KiminCenazesi/1.0", "CF-Connecting-IP": "1.2.3.4" } }), env, kaynak);
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get("x-content-type-options"), "nosniff");
  assert.equal(ok.headers.get("x-frame-options"), "DENY");
  assert.match(ok.headers.get("content-security-policy"), /default-src 'none'/);
  const red = await kapi(new Request("https://veri.test/veri/ordu/son7gun.json"), env, kaynak);
  assert.equal(red.status, 403);
  assert.equal(await red.text(), "");
  assert.equal(red.headers.get("x-content-type-options"), null);
});
