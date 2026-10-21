// 21.10.2026 guvenlik duvari: basliklar, govde siniri, hatali-anahtar kilidi, genel yakalayici
import test from "node:test";
import assert from "node:assert/strict";
import worker, { isle } from "../src/index.js";
import { sinirliMetin, kilitliMi, basarisizKaydet, basarisizSifirla, GUVENLIK_BASLIK } from "../src/guvenlik.js";

class KV {
  constructor() { this.m = new Map(); }
  async get(k) { return this.m.has(k) ? this.m.get(k) : null; }
  async put(k, v) { this.m.set(k, v); }
  async delete(k) { this.m.delete(k); }
  async list() { return { keys: [], list_complete: true }; }
}
const env = (ek = {}) => ({ AILE: new KV(), GELISTIRME: "0", PANEL_ANAHTARI: "panel-gizli-0123456789", ...ek });
const ctx = { waitUntil() {} };

test("her yanita guvenlik basliklari eklenir (404 dahil)", async () => {
  const r = await isle(new Request("https://w.test/aile/yok"), env(), ctx);
  for (const [k, v] of Object.entries(GUVENLIK_BASLIK)) assert.equal(r.headers.get(k), v, k);
});

test("sinirliMetin: Content-Length ve akis siniri", async () => {
  const buyuk = new Request("https://w.test/x", { method: "POST", body: "a".repeat(5000) });
  assert.equal((await sinirliMetin(buyuk, 4096)).asildi, true);
  const kucuk = new Request("https://w.test/x", { method: "POST", body: "merhaba" });
  assert.equal((await sinirliMetin(kucuk, 4096)).metin, "merhaba");
  const bos = new Request("https://w.test/x", { method: "GET" });
  assert.equal((await sinirliMetin(bos, 10)).metin, "");
});

test("buyuk govde 413 (basvur)", async () => {
  const r = await isle(new Request("https://w.test/aile/basvur", { method: "POST", headers: { "CF-Connecting-IP": "10.9.9.1" }, body: JSON.stringify({ x: "a".repeat(6000) }) }), env(), ctx);
  assert.equal(r.status, 413);
});

test("yanlis panel anahtari 10 kez -> IP kilitlenir (429), dogru anahtar da o IP'den reddedilir; baska IP etkilenmez", async () => {
  basarisizSifirla();
  const e = env();
  const iste = (ip, anahtar) => worker.fetch(new Request("https://w.test/aile/durum", { headers: { "CF-Connecting-IP": ip, Authorization: "Bearer " + anahtar } }), e, ctx);
  for (let i = 0; i < 10; i++) assert.equal((await iste("10.8.8.8", "yanlis")).status, 403);
  assert.equal((await iste("10.8.8.8", "panel-gizli-0123456789")).status, 429);
  assert.equal((await iste("10.8.8.9", "panel-gizli-0123456789")).status, 200);
  basarisizSifirla();
});

test("kilit penceresi: 10 dk sonra acilir", () => {
  basarisizSifirla();
  const t0 = 1_000_000;
  for (let i = 0; i < 10; i++) basarisizKaydet("ip1", t0);
  assert.equal(kilitliMi("ip1", t0 + 1000), true);
  assert.equal(kilitliMi("ip1", t0 + 11 * 60 * 1000), false);
  basarisizSifirla();
});

test("beklenmeyen hata: 500 sunucu_hatasi, iz yok", async () => {
  const bozuk = { AILE: { get() { throw new Error("ic hata ayrintisi"); }, put() {}, list() { throw new Error("x"); } }, PANEL_ANAHTARI: "k" };
  const r = await worker.fetch(new Request("https://w.test/aile/ordu.json", { headers: { "CF-Connecting-IP": "10.7.7.7" } }), bozuk, ctx);
  assert.equal(r.status, 500);
  const g = await r.text();
  assert.ok(!g.includes("ayrinti") && !g.includes("Error") && !g.includes("stack"), g);
  assert.equal(r.headers.get("x-frame-options"), "DENY");
});
