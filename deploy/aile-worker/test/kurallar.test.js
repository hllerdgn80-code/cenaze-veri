import test from "node:test";
import assert from "node:assert/strict";
import { isle, temizle, genel } from "../src/index.js";
import { katla, mezarlikNorm, ilSlug, degerlendir, girdiTemizle } from "../src/kurallar.js";
import { MEZARLIK } from "../src/veri.js";

// ---- sahte KV (get/put/delete/list + metadata) ----
class KV {
  constructor() { this.m = new Map(); }
  async get(k) { return this.m.has(k) ? this.m.get(k).v : null; }
  async put(k, v, o = {}) { this.m.set(k, { v, meta: o.metadata }); }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = "", cursor } = {}) {
    const keys = [...this.m.keys()].filter((k) => k.startsWith(prefix)).sort().map((name) => ({ name, metadata: this.m.get(name).meta }));
    return { keys, list_complete: true };
  }
}
const NOW = new Date("2026-10-14T09:00:00Z"); // TR günü 2026-10-14
const env = (ek = {}) => ({ AILE: new KV(), GELISTIRME: "1", ...ek });
let ipSayac = 0;
function istek(yol, govde, { method = "POST", ip, origin, ek = {} } = {}) {
  const h = { "Content-Type": "application/json", "CF-Connecting-IP": ip || `10.0.0.${++ipSayac}`, ...ek };
  if (origin) h.Origin = origin;
  return new Request("https://w.test" + yol, { method, headers: h, body: method === "POST" ? JSON.stringify(govde) : undefined });
}
const j = async (r) => r.json();

const temel = (ek = {}) => ({
  il: "Adana", ilce: "Seyhan", ad_soyad: "Deneme Örnek Kişi", cinsiyet: "e", yas: 80,
  vefat_tarihi: "2026-10-13", namaz_tarihi: "2026-10-14", namaz_yeri_vakti: "Örnek Camii öğle", defin_yeri: "Örnek Mezarlığı",
  basvuran: { ad_soyad: "Deneme Başvuran", telefon: "0532 111 22 33", yakinlik: "oğlu" }, beyan: true, tam: true, ...ek, // 15.10.2026: ücretsiz aile ilanı kalktı; her başvuru Tam Sayfa
});

async function ilanVer(e, g, secenek = {}) {
  const b = await isle(istek("/aile/basvur", g), e, null, { now: NOW, ...secenek });
  const bj = await j(b);
  assert.equal(b.status, 200, JSON.stringify(bj));
  const d = await isle(istek("/aile/dogrula", { basvuru_id: bj.basvuru_id, kod: bj.gelistirme_kodu }), e, null, { now: NOW });
  const dj = await j(d);
  if (dj.durum === "odeme_bekliyor") { // Tam Sayfa: Play ödemesi (PLAY_SA_JSON yok → istemci makbuzu kabul)
    const od = await isle(istek("/aile/odeme", { basvuru_id: dj.basvuru_id, purchase_token: `tok-${dj.ilan_id}-abcdefgh`, order_id: "GPA.1", urun: "tam_sayfa_ilan" }), e, null, { now: NOW });
    return { ...(await j(od)), basvuru_id: dj.basvuru_id };
  }
  return { ...dj };
}

test("yayında: geçerli ilan yayına girer, listede görünür, başvuran sızmaz", async () => {
  const e = env();
  const r = await ilanVer(e, temel({ edevlet_kodu: "ABCD1234EFGH" }));
  assert.equal(r.durum_, undefined);
  assert.equal(r.durum, "yayinda");
  assert.match(r.ilan_id, /^[0-9a-f]{16}$/);
  const l = await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW });
  const lj = await j(l);
  assert.equal(lj.il, "Adana");
  assert.equal(lj.kayitlar.length, 1);
  const k = lj.kayitlar[0];
  assert.equal(k.aile, true);
  assert.equal("dogrulandi" in k, false); // alan çıktıda yok (e-Devlet kodu kalktı)
  assert.equal(k.liste_tarihi, "2026-10-14");
  const ham = JSON.stringify(lj);
  for (const yasak of ["5321112233", "0532", "Deneme Başvuran", "oğlu", "ABCD1234EFGH", "telefon", "eposta", "basvuran", "edevlet", "ip"]) {
    assert.ok(!ham.includes(yasak), `sızıntı: ${yasak}`);
  }
  assert.ok(!JSON.stringify(genel({ basvuran: { telefon: "5329998877" }, id: "1", ad_soyad: "A B" })).includes("5329998877"));
});

const redler = [
  ["yanlış ilçe", temel({ ilce: "Beşiktaş" }), /K1/],
  ["bilinmeyen il", temel({ il: "Atlantis" }), /K1/],
  ["4 gün sonra namaz", temel({ vefat_tarihi: "2026-10-10", namaz_tarihi: "2026-10-14" }), /K3/],
  ["namaz çok ileride", temel({ vefat_tarihi: "2026-10-18", namaz_tarihi: "2026-10-19" }), /K3/],
  ["namaz çok eski", temel({ vefat_tarihi: "2026-10-10", namaz_tarihi: "2026-10-11" }), /K3/],
  ["vefat namazdan sonra", temel({ vefat_tarihi: "2026-10-15", namaz_tarihi: "2026-10-14" }), /K3/],
  ["rakamlı ad", temel({ ad_soyad: "Ali Yılmaz 2" }), /K2/],
  ["tek sözcüklü ad", temel({ ad_soyad: "Ali" }), /K2/],
  ["URL'li ad", temel({ ad_soyad: "Ali www.x.com" }), /K2/],
  ["rakamlı başvuran adı", temel({ basvuran: { ad_soyad: "Ay5e Kaya", telefon: "0533 000 00 01", yakinlik: "kızı" } }), /K2/],
  ["beyan yok", temel({ beyan: false }), /K7/],
  ["mezarlık başka ilçede", temel({ ilce: "Yüreğir", defin_yeri: "Akkapı Asri Mezarlığı" }), /K4/],
  ["telefon alanda", temel({ namaz_yeri_vakti: "Ara 0532 123 45 67" }), /K8/],
  ["ölüm nedeni alanda", temel({ mahalle: "kanser nedeniyle" }), /K8/],
  ["TC alanda", temel({ mahalle: "12345678901" }), /K8/],
  ["uzun alan", temel({ mahalle: "x".repeat(61) }), /K8/],
];
for (const [ad, g, re] of redler) {
  test(`red: ${ad}`, async () => {
    const r = await ilanVer(env(), g);
    assert.equal(r.durum, "red", JSON.stringify(r));
    assert.match(r.neden, re);
  });
}

test("K4 mezarlık aynı ilçede kabul", async () => {
  assert.equal(MEZARLIK.adana["akkapi asri"], "Seyhan");
  const r = await ilanVer(env(), temel({ ilce: "Seyhan", defin_yeri: "Akkapı Asri Mezarlığı" }));
  assert.equal(r.durum, "yayinda");
});

test("Merkez ilçe kabul edilir", async () => {
  assert.equal((await ilanVer(env(), temel({ ilce: "Merkez", defin_yeri: undefined }))).durum, "yayinda");
});

test("K5 ikinci ilan (aynı il + ad ±3 gün) red", async () => {
  const e = env();
  assert.equal((await ilanVer(e, temel())).durum, "yayinda");
  const r = await ilanVer(e, temel({ basvuran: { ad_soyad: "Başka Kişi", telefon: "0534 000 00 02", yakinlik: "eşi" }, ad_soyad: "DENEME ÖRNEK KİŞİ" }));
  assert.equal(r.durum, "red");
  assert.match(r.neden, /K5/);
});

test("K6 telefon başına 7 günde 2 ilan", async () => {
  const e = env();
  assert.equal((await ilanVer(e, temel({ ad_soyad: "Bir Kişi" }))).durum, "yayinda");
  assert.equal((await ilanVer(e, temel({ ad_soyad: "İki Kişi" }))).durum, "yayinda");
  const r = await ilanVer(e, temel({ ad_soyad: "Üç Kişi" }));
  assert.equal(r.durum, "red");
  assert.match(r.neden, /K6/);
});

test("kod: 3 yanlış denemede red; yanlış kodla ilan çıkmaz", async () => {
  const e = env();
  const b = await j(await isle(istek("/aile/basvur", temel()), e, null, { now: NOW }));
  const yanlis = b.gelistirme_kodu === "000000" ? "111111" : "000000";
  let r = await isle(istek("/aile/dogrula", { basvuru_id: b.basvuru_id, kod: yanlis }), e, null, { now: NOW });
  assert.equal(r.status, 400);
  assert.equal((await j(r)).kalan_deneme, 2);
  await isle(istek("/aile/dogrula", { basvuru_id: b.basvuru_id, kod: yanlis }), e, null, { now: NOW });
  r = await isle(istek("/aile/dogrula", { basvuru_id: b.basvuru_id, kod: yanlis }), e, null, { now: NOW });
  assert.equal((await j(r)).durum, "red");
  r = await isle(istek("/aile/dogrula", { basvuru_id: b.basvuru_id, kod: b.gelistirme_kodu }), e, null, { now: NOW });
  assert.equal((await j(r)).durum, "red"); // başvuru silindi
  const lj = await j(await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW }));
  assert.equal(lj.kayitlar.length, 0);
});

test("üretimde (GELISTIRME!=1) anahtar yoksa 503 ve kod yanıtta YOK", async () => {
  const e = env({ GELISTIRME: "0" });
  const r = await isle(istek("/aile/basvur", temel()), e, null, { now: NOW });
  assert.equal(r.status, 503);
  assert.ok(!JSON.stringify(await j(r)).includes("gelistirme_kodu"));
});

test("kod kanalı: WhatsApp şablonu varsa WhatsApp ile gider (SMS'e düşmez), yanıtta DÖNMEZ", async () => {
  const e = env({ WA_TOKEN: "tk", WA_PHONE_ID: "123", GELISTIRME: "0" });
  const giden = [];
  const fetchSahte = async (url, o) => { giden.push({ url, o }); return new Response("{}", { status: 200 }); };
  const r = await isle(istek("/aile/basvur", temel()), e, null, { now: NOW, fetch: fetchSahte });
  const rj = await j(r);
  assert.equal(r.status, 200); assert.equal(rj.kanal, "whatsapp");
  assert.ok(!("gelistirme_kodu" in rj));
  assert.equal(giden.length, 1);
  assert.equal(giden[0].url, "https://graph.facebook.com/v21.0/123/messages");
  const g = JSON.parse(giden[0].o.body);
  assert.equal(g.to, "905321112233"); assert.equal(g.type, "template"); assert.equal(g.template.name, "kc_dogrulama"); assert.equal(g.template.language.code, "tr");
  const kod = g.template.components[0].parameters[0].text;
  assert.match(kod, /^\d{6}$/);
  const d = await j(await isle(istek("/aile/dogrula", { basvuru_id: rj.basvuru_id, kod }), e, null, { now: NOW }));
  assert.equal(d.durum, "odeme_bekliyor");
});

test("kod kanalı: WhatsApp başarısız -> Netgsm SMS; ikisi de başarısız -> 502; kanal yok + GELISTIRME=0 -> 503", async () => {
  const e = env({ WA_TOKEN: "tk", WA_PHONE_ID: "123", NETGSM_KULLANICI: "u", NETGSM_SIFRE: "p", NETGSM_BASLIK: "B", GELISTIRME: "0" });
  const giden = [];
  const f = async (url, o) => { giden.push(url); return url.includes("graph.facebook.com") ? new Response("x", { status: 400 }) : new Response(JSON.stringify({ code: "00", jobid: "1" }), { status: 200 }); };
  const r = await isle(istek("/aile/basvur", temel()), e, null, { now: NOW, fetch: f });
  assert.equal((await j(r)).kanal, "sms");
  assert.deepEqual(giden, ["https://graph.facebook.com/v21.0/123/messages", "https://api.netgsm.com.tr/sms/rest/v2/send"]);
  const e2 = env({ WA_TOKEN: "tk", WA_PHONE_ID: "123", GELISTIRME: "0" });
  const r2 = await isle(istek("/aile/basvur", temel()), e2, null, { now: NOW, fetch: async () => new Response("x", { status: 500 }) });
  assert.equal(r2.status, 502);
});

test("telefon: eksik ya da geçersiz telefon 400; e-posta tek başına yetmez; şehit ilanı 400 (yalnız din görevlisi)", async () => {
  const e = env();
  const yok = temel(); delete yok.basvuran.telefon; yok.basvuran.eposta = "x@example.com";
  assert.equal((await isle(istek("/aile/basvur", yok), e, null, { now: NOW })).status, 400);
  assert.equal((await isle(istek("/aile/basvur", temel({ basvuran: { ad_soyad: "Deneme Başvuran", telefon: "12345", yakinlik: "oğlu" } })), e, null, { now: NOW })).status, 400);
  const sh = await isle(istek("/aile/basvur", temel({ sehit: true, rutbe: "Piyade Uzman Çavuş" })), e, null, { now: NOW });
  assert.equal(sh.status, 400);
  assert.equal((await j(sh)).hata, "şehit ilanı yalnız din görevlisi");
});

test("hız sınırı: IP başına saatte 10 istek", async () => {
  const e = env();
  let son;
  for (let i = 0; i < 11; i++) son = await isle(istek("/aile/bildir", { ilan_id: "0123456789abcdef", neden: "yanlış" }, { ip: "9.9.9.9" }), e, null, { now: NOW });
  assert.equal(son.status, 429);
  const sonraki = await isle(istek("/aile/bildir", { ilan_id: "0123456789abcdef", neden: "yanlış" }, { ip: "9.9.9.9" }), e, null, { now: new Date(NOW.getTime() + 3600000) });
  assert.equal(sonraki.status, 404); // yeni saat: sınır sıfır, ilan yok
});

test("bildir: 2 farklı IP'den bildirimde ilan gizlenir; aynı IP iki kez sayılmaz", async () => {
  const e = env();
  const { ilan_id } = await ilanVer(e, temel());
  const b = (ip) => isle(istek("/aile/bildir", { ilan_id, neden: "yanlış bilgi" }, { ip }), e, null, { now: NOW });
  assert.equal((await j(await b("1.1.1.1"))).alindi, true);
  await b("1.1.1.1");
  let lj = await j(await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW }));
  assert.equal(lj.kayitlar.length, 1);
  await b("2.2.2.2");
  lj = await j(await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW }));
  assert.equal(lj.kayitlar.length, 0);
});

test("liste: 7 günden eski ilan çıkmaz; bilinmeyen il 404", async () => {
  const e = env();
  await ilanVer(e, temel());
  const gec = new Date(NOW.getTime() + 9 * 86400000);
  const lj = await j(await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: gec }));
  assert.equal(lj.kayitlar.length, 0);
  assert.equal((await isle(istek("/aile/yokil.json", null, { method: "GET" }), e, null, { now: NOW })).status, 404);
});

test("CORS: izinli origin başlık alır, izinsiz 403; Origin'siz (uygulama) geçer", async () => {
  const e = env({ GELISTIRME: "0" });
  const ok = await isle(istek("/aile/adana.json", null, { method: "GET", origin: "https://kimincenazesi.com" }), e, null, { now: NOW });
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), "https://kimincenazesi.com");
  const kotu = await isle(istek("/aile/adana.json", null, { method: "GET", origin: "https://kotu.example" }), e, null, { now: NOW });
  assert.equal(kotu.status, 403);
  const pf = await isle(new Request("https://w.test/aile/basvur", { method: "OPTIONS", headers: { Origin: "https://kimincenazesi.com" } }), e, null, { now: NOW });
  assert.equal(pf.status, 204);
  assert.equal((await isle(istek("/aile/adana.json", null, { method: "GET" }), e, null, { now: NOW })).status, 200);
});

test("durum: PANEL_ANAHTARI olmadan 403; doğru anahtarla sayılar", async () => {
  const e = env({ GELISTIRME: "0", PANEL_ANAHTARI: "gizli-anahtar" });
  assert.equal((await isle(istek("/aile/durum", null, { method: "GET" }), e, null, { now: NOW })).status, 403);
  const e2 = env({ GELISTIRME: "1", PANEL_ANAHTARI: "gizli-anahtar" });
  await ilanVer(e2, temel());
  const r = await isle(istek("/aile/durum", null, { method: "GET", ek: { Authorization: "Bearer gizli-anahtar" } }), e2, null, { now: NOW });
  assert.equal((await j(r)).iller.adana.yayinda, 1);
});

test("KVKK: 30 gün sonra başvuran bilgisi silinir, ilan kalır", async () => {
  const e = env();
  const { ilan_id } = await ilanVer(e, temel({ edevlet_kodu: "ABCD1234EFGH" }));
  assert.equal(await temizle(e, new Date(NOW.getTime() + 10 * 86400000)), 0);
  assert.equal(await temizle(e, new Date(NOW.getTime() + 31 * 86400000)), 1);
  const ilan = JSON.parse(await e.AILE.get(`i:${ilan_id}`));
  assert.equal(ilan.basvuran, null);
  assert.ok(!("edevlet_kodu" in ilan));
  assert.equal(ilan.ad_soyad, "Deneme Örnek Kişi");
});

test("bozuk/büyük gövde", async () => {
  const e = env();
  const r1 = await isle(new Request("https://w.test/aile/basvur", { method: "POST", headers: { "CF-Connecting-IP": "5.5.5.5" }, body: "{bozuk" }), e, null, { now: NOW });
  assert.equal(r1.status, 400);
  const r2 = await isle(new Request("https://w.test/aile/basvur", { method: "POST", headers: { "CF-Connecting-IP": "5.5.5.6" }, body: JSON.stringify({ x: "a".repeat(5000) }) }), e, null, { now: NOW });
  assert.equal(r2.status, 413);
  const r3 = await isle(istek("/aile/basvur", { il: "Adana" }), e, null, { now: NOW });
  assert.equal(r3.status, 400);
});

test("katla / mezarlikNorm / ilSlug Python ortak.py ile aynı", () => {
  assert.equal(katla("ADANA ASRİ MEZARLIĞI"), "adana asri mezarligi");
  assert.equal(mezarlikNorm("Yeni Mezarlığı"), "yeni");
  assert.equal(mezarlikNorm("Şehir Mezarlığı / Pafta 3"), "sehir");
  assert.equal(mezarlikNorm("Ali Hocalı Kabristanlığı"), "ali hocali");
  assert.equal(mezarlikNorm("ADANA ASRİ MEZARLIĞI"), "adana asri");
  assert.equal(mezarlikNorm("Çankaya Mah. 12 Mezarlık"), "cankaya mah");
  assert.equal(ilSlug("Şanlıurfa"), "sanliurfa");
  assert.equal(ilSlug("Afyonkarahisar"), "afyonkarahisar");
});

test("yeniden gönder: 60 sn içinde 429; sonra yeni kod, eski başvuru geçersiz, K6 sayacı artmaz", async () => {
  const e = env();
  const b1 = await j(await isle(istek("/aile/basvur", temel()), e, null, { now: NOW }));
  const r2 = await isle(istek("/aile/basvur", temel()), e, null, { now: new Date(NOW.getTime() + 30000) });
  assert.equal(r2.status, 429);
  const b2 = await j(await isle(istek("/aile/basvur", temel()), e, null, { now: new Date(NOW.getTime() + 90000) }));
  assert.notEqual(b2.basvuru_id, b1.basvuru_id);
  const eski = await isle(istek("/aile/dogrula", { basvuru_id: b1.basvuru_id, kod: b1.gelistirme_kodu }), e, null, { now: NOW });
  assert.equal((await j(eski)).durum, "red");
  const yeni = await j(await isle(istek("/aile/dogrula", { basvuru_id: b2.basvuru_id, kod: b2.gelistirme_kodu }), e, null, { now: NOW }));
  assert.equal(yeni.durum, "odeme_bekliyor");
  // K6: bu ilan 1 sayılır, ikinci ilan hâlâ geçer
  assert.equal((await ilanVer(e, temel({ ad_soyad: "İki Kişi" }))).durum, "yayinda");
});

test("bildir: bilinmeyen id -> 404 {alindi:false}", async () => {
  const r = await isle(istek("/aile/bildir", { ilan_id: "0123456789abcdef", neden: "x" }), env(), null, { now: NOW });
  assert.equal(r.status, 404);
  assert.deepEqual(await r.json(), { alindi: false });
});
