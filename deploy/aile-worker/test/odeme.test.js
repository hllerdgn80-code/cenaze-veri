import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { isle } from "../src/index.js";

class KV {
  constructor() { this.m = new Map(); }
  async get(k) { return this.m.has(k) ? this.m.get(k).v : null; }
  async put(k, v, o = {}) { this.m.set(k, { v, meta: o.metadata }); }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = "" } = {}) {
    const keys = [...this.m.keys()].filter((k) => k.startsWith(prefix)).sort().map((name) => ({ name, metadata: this.m.get(name).meta }));
    return { keys, list_complete: true };
  }
}
const NOW = new Date("2026-10-14T09:00:00Z");
let ip = 0;
const env = (ek = {}) => ({ AILE: new KV(), GELISTIRME: "1", PANEL_ANAHTARI: "panel-gizli", ...ek });
const istek = (yol, govde, { method = "POST", basliklar = {} } = {}) =>
  new Request("https://w.test" + yol, { method, headers: { "Content-Type": "application/json", "CF-Connecting-IP": `10.1.0.${++ip}`, ...basliklar }, body: method === "POST" ? JSON.stringify(govde) : undefined });
const j = (r) => r.json();
const temel = (ek = {}) => ({
  il: "Adana", ilce: "Seyhan", ad_soyad: "Deneme Örnek Kişi", cinsiyet: "e", yas: 80, vefat_tarihi: "2026-10-13", namaz_tarihi: "2026-10-14",
  namaz_yeri_vakti: "Örnek Camii öğle", defin_yeri: "Örnek Mezarlığı",
  basvuran: { ad_soyad: "Deneme Başvuran", telefon: "0532 111 22 33", yakinlik: "oğlu" }, beyan: true, tam: true, ...ek,
});
const TOKEN = "kaaabbbcccdddeeefff.AO-J1Oxyz_123";
const odemeGovde = (id, ek = {}) => ({ basvuru_id: id, purchase_token: TOKEN, order_id: "GPA.3333-4444-5555-66666", urun: "tam_sayfa_ilan", ...ek });

async function odemeBekleyen(e, g = temel()) {
  const b = await j(await isle(istek("/aile/basvur", g), e, null, { now: NOW }));
  const d = await j(await isle(istek("/aile/dogrula", { basvuru_id: b.basvuru_id, kod: b.gelistirme_kodu }), e, null, { now: NOW }));
  assert.equal(d.durum, "odeme_bekliyor");
  return d;
}
const liste = async (e) => j(await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW }));

test("tam:false ya da tam yok: 400 'aile ilanı kaldırıldı'", async () => {
  const e = env();
  for (const g of [temel({ tam: false }), (({ tam, ...r }) => r)(temel())]) {
    const r = await isle(istek("/aile/basvur", g), e, null, { now: NOW });
    assert.equal(r.status, 400);
    assert.match((await j(r)).hata, /kaldırıldı/);
  }
});

test("ödeme gelmeden ilan listede YOK; makbuz kaydı (PLAY_SA_JSON yok) → yayında, odeme_dogrulandi:false", async () => {
  const e = env();
  const d = await odemeBekleyen(e);
  assert.equal((await liste(e)).kayitlar.length, 0);
  const r = await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW });
  assert.equal(r.status, 200);
  const rj = await j(r);
  assert.equal(rj.durum, "yayinda");
  assert.equal(rj.odeme_dogrulandi, false);
  const l = await liste(e);
  assert.equal(l.kayitlar.length, 1);
  assert.equal(l.kayitlar[0].id, d.ilan_id);
  const ham = JSON.stringify(l);
  for (const yasak of [TOKEN, "GPA.", "odeme", "5321112233", "Deneme Başvuran"]) assert.ok(!ham.includes(yasak), `sızıntı: ${yasak}`);
});

test("GET /aile/odemeler: x-gizli olmadan 403; ile kayıt (sipariş no, doğrulanmamış sayısı), token ham yazılmaz", async () => {
  const e = env();
  const d = await odemeBekleyen(e);
  await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW });
  assert.equal((await isle(istek("/aile/odemeler", null, { method: "GET" }), e, null, { now: NOW })).status, 403);
  assert.equal((await isle(istek("/aile/odemeler", null, { method: "GET", basliklar: { "x-gizli": "yanlis" } }), e, null, { now: NOW })).status, 403);
  const r = await isle(istek("/aile/odemeler", null, { method: "GET", basliklar: { "x-gizli": "panel-gizli" } }), e, null, { now: NOW });
  const rj = await j(r);
  assert.equal(rj.odemeler.length, 1);
  assert.equal(rj.odemeler[0].order_id, "GPA.3333-4444-5555-66666");
  assert.equal(rj.odemeler[0].odeme_dogrulandi, false);
  assert.equal(rj.dogrulanmamis, 1);
  assert.ok(!JSON.stringify(rj).includes(TOKEN));
});

test("aynı purchase_token ikinci ilanda kullanılamaz (409); aynı ilanda tekrar gelirse sonuç tekrarlanır", async () => {
  const e = env();
  const d1 = await odemeBekleyen(e);
  assert.equal((await isle(istek("/aile/odeme", odemeGovde(d1.basvuru_id)), e, null, { now: NOW })).status, 200);
  const d2 = await odemeBekleyen(e, temel({ ad_soyad: "Başka Örnek Kişi", basvuran: { ad_soyad: "Başka Başvuran", telefon: "0533 000 00 09", yakinlik: "eşi" } }));
  const r2 = await isle(istek("/aile/odeme", odemeGovde(d2.basvuru_id)), e, null, { now: NOW });
  assert.equal(r2.status, 409);
  assert.equal((await j(r2)).hata, "token_kullanilmis");
  assert.equal((await liste(e)).kayitlar.length, 1);
  // aynı ilan: bekleyen anahtar silindi → 404; idempotent yol yalnız ilan hâlâ bekliyorsa
  const r3 = await isle(istek("/aile/odeme", odemeGovde(d1.basvuru_id)), e, null, { now: NOW });
  assert.ok([200, 404].includes(r3.status));
});

test("geçersiz gövde: token biçimi, ürün, bilinmeyen basvuru_id", async () => {
  const e = env();
  const d = await odemeBekleyen(e);
  assert.equal((await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id, { purchase_token: "kisa" })), e, null, { now: NOW })).status, 400);
  assert.equal((await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id, { urun: "baska" })), e, null, { now: NOW })).status, 400);
  assert.equal((await isle(istek("/aile/odeme", odemeGovde("0".repeat(16))), e, null, { now: NOW })).status, 404);
  assert.equal((await liste(e)).kayitlar.length, 0);
});

// ---- Play doğrulaması (PLAY_SA_JSON var): sahte Google ----
function saUret() {
  const { privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  return JSON.stringify({ client_email: "sa@proje.iam.gserviceaccount.com", private_key: privateKey.export({ type: "pkcs8", format: "pem" }) });
}
function sahteGoogle(alanlar, cagrilar = []) {
  return async (url, init = {}) => {
    cagrilar.push({ url: String(url), method: init.method || "GET", body: init.body });
    if (String(url).startsWith("https://oauth2.googleapis.com/token")) return new Response(JSON.stringify({ access_token: "erisim" }), { status: 200 });
    if (String(url).includes(":acknowledge")) return new Response("{}", { status: 200 });
    if (String(url).includes("/purchases/products/tam_sayfa_ilan/tokens/")) return new Response(JSON.stringify(alanlar), { status: alanlar ? 200 : 404 });
    return new Response("yok", { status: 404 });
  };
}

test("Play doğrulaması: purchaseState 0 → acknowledge edilir, ilan yayında, odeme_dogrulandi:true; JWT RS256 ile istenir", async () => {
  const e = env({ PLAY_SA_JSON: saUret() });
  const d = await odemeBekleyen(e);
  const cagrilar = [];
  const f = sahteGoogle({ purchaseState: 0, consumptionState: 0, acknowledgementState: 0, orderId: "GPA.3333-4444-5555-66666", purchaseType: 0 }, cagrilar);
  const r = await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW, fetch: f });
  assert.equal(r.status, 200);
  assert.equal((await j(r)).odeme_dogrulandi, true);
  const tok = cagrilar.find((c) => c.url.includes("oauth2"));
  assert.match(String(tok.body), /grant_type=.*jwt-bearer&assertion=[\w-]+\.[\w-]+\.[\w-]+/);
  assert.ok(cagrilar.some((c) => c.url.includes("com.kimincenazesi.app/purchases/products/tam_sayfa_ilan/tokens/") && c.url.endsWith(":acknowledge") && c.method === "POST"));
  assert.equal((await liste(e)).kayitlar.length, 1);
});

test("Play doğrulaması: iptal/bekleyen (purchaseState≠0), tüketilmiş, sipariş no uyuşmaz, bilinmeyen token → ilan yayına GİRMEZ", async () => {
  for (const [alan, neden] of [
    [{ purchaseState: 1, consumptionState: 0 }, "satin_alma_tamam_degil"],
    [{ purchaseState: 0, consumptionState: 1 }, "makbuz_tuketilmis"],
    [{ purchaseState: 0, consumptionState: 0, orderId: "GPA.BASKA" }, "siparis_no_uyusmuyor"],
    [null, "makbuz_gecersiz"],
  ]) {
    const e = env({ PLAY_SA_JSON: saUret() });
    const d = await odemeBekleyen(e);
    const r = await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW, fetch: sahteGoogle(alan) });
    assert.equal(r.status, 402);
    assert.equal((await j(r)).neden, neden);
    assert.equal((await liste(e)).kayitlar.length, 0);
    // token yanmadı: düzeltilmiş makbuzla yeniden denenebilir
    const r2 = await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW, fetch: sahteGoogle({ purchaseState: 0, consumptionState: 0, acknowledgementState: 1, orderId: "GPA.3333-4444-5555-66666" }) });
    assert.equal(r2.status, 200);
  }
});

test("Play API'ye ulaşılamazsa 502 (geçici); ilan beklemede kalır", async () => {
  const e = env({ PLAY_SA_JSON: saUret() });
  const d = await odemeBekleyen(e);
  const r = await isle(istek("/aile/odeme", odemeGovde(d.basvuru_id)), e, null, { now: NOW, fetch: async () => new Response("x", { status: 503 }) });
  assert.equal(r.status, 502);
  assert.equal((await liste(e)).kayitlar.length, 0);
});
