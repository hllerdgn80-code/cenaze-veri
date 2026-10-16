// Din görevlisi: Diyanet e-posta kodu doğrulaması (URUN §45, 16.10.2026) + panel/ilan/gözetim. node --test test/*.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { isle } from "../src/index.js";
import { kullaniciNormalize, telefonNormalize, UNVANLAR } from "../src/gorevli.js";

class KV {
  constructor() { this.m = new Map(); }
  async get(k) { return this.m.has(k) ? this.m.get(k).v : null; }
  async put(k, v, o = {}) { this.m.set(k, { v, meta: o.metadata, ttl: o.expirationTtl, exp: o.expiration }); }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = "" } = {}) {
    const keys = [...this.m.keys()].filter((k) => k.startsWith(prefix)).sort().map((name) => ({ name, metadata: this.m.get(name).meta }));
    return { keys, list_complete: true };
  }
}
const NOW = new Date("2026-10-16T09:00:00Z");
const dk = (sn) => new Date(NOW.getTime() + sn * 1000);
const env = (ek = {}) => ({ AILE: new KV(), GELISTIRME: "1", PANEL_ANAHTARI: "panel-x", ...ek });
let ipN = 0;
function istek(yol, govde, { method = "POST", ip, ek = {} } = {}) {
  return new Request("https://w.test" + yol, { method, headers: { "Content-Type": "application/json", "CF-Connecting-IP": ip || `10.2.0.${++ipN}`, ...ek }, body: method === "POST" ? JSON.stringify(govde ?? {}) : undefined });
}
const cagir = async (e, yol, govde, o = {}) => { const r = await isle(istek(yol, govde, o), e, null, { now: o.now || NOW, ...(o.fetch ? { fetch: o.fetch } : {}) }); return { s: r.status, ...(await r.json()) }; };
const al = async (e, yol, ek = {}) => { const r = await isle(istek(yol, null, { method: "GET", ek }), e, null, { now: NOW }); return { s: r.status, ...(await r.json()) }; };
const PANEL = { "x-gizli": "panel-x" };
const KU = "mehmet.yilmaz";
const PROFIL = (ek = {}) => ({ ad_soyad: "Mehmet Ali Yılmaz", il: "Ordu", ilce: "Korgan", gorev_yeri: "Korgan Merkez Camii", unvan: "İmam-Hatip", ...ek });
const ilanGovde = (ek = {}) => ({ ad_soyad: "Deneme Örnek Kişi", cinsiyet: "e", yas: 80, vefat_tarihi: "2026-10-15", namaz_tarihi: "2026-10-16", namaz_yeri_vakti: "Merkez Camii öğle", koy: "Örnek Köyü", ...ek });

// Kod iste + doğrula; Authorization başlığını döner
async function giris(e, ku = KU, o = {}) {
  const k = await cagir(e, "/gorevli/eposta-kod", { kullanici: ku }, o);
  assert.equal(k.s, 200, JSON.stringify(k));
  const d = await cagir(e, "/gorevli/eposta-dogrula", { kullanici: ku, kod: k.gelistirme_kodu }, o);
  assert.equal(d.s, 200, JSON.stringify(d));
  return { h: { Authorization: `Bearer ${d.oturum}` }, d, k };
}
async function hazir(e, ku = KU, profil = PROFIL()) {
  const { h, d } = await giris(e, ku);
  const p = await cagir(e, "/gorevli/profil", profil, { ek: h });
  assert.equal(p.s, 200, JSON.stringify(p));
  return { h, d };
}

test("saf: kullaniciNormalize — küçük harf, '@diyanet.gov.tr' atılır, başka alan adı/geçersiz biçim null", () => {
  assert.equal(kullaniciNormalize(" Mehmet.Yilmaz "), "mehmet.yilmaz");
  assert.equal(kullaniciNormalize("Mehmet.Yilmaz@Diyanet.gov.tr"), "mehmet.yilmaz");
  for (const x of ["a@gmail.com", "ab", "x".repeat(41), "ali kaya", "ali/kaya", "ali@evil.com@diyanet.gov.tr", "", null, 5]) assert.equal(kullaniciNormalize(x), null, String(x));
  assert.ok(UNVANLAR.includes("Din Hizmetleri Uzmanı"));
  assert.equal(telefonNormalize("0532 111 22 33"), "5321112233");
});

test("eposta-kod: başka alan adı 400; geçersiz kullanıcı 400; kod YALNIZ @diyanet.gov.tr'ye gider (Resend, Bearer, bağlantısız tek cümle)", async () => {
  const e = env({ RESEND_ANAHTARI: "re_x", GELISTIRME: "0" });
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: "ali@gmail.com" })).s, 400);
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: "a" })).s, 400);
  const giden = [];
  const f = async (url, init) => { giden.push({ url, init, govde: JSON.parse(init.body) }); return { ok: true }; };
  const r = await cagir(e, "/gorevli/eposta-kod", { kullanici: "Mehmet.Yilmaz@diyanet.gov.tr" }, { fetch: f });
  assert.equal(r.s, 200); assert.equal(r.adres, "mehmet.yilmaz@diyanet.gov.tr"); assert.equal(r.gelistirme_kodu, undefined, "üretimde kod yanıtta dönmez");
  assert.equal(giden.length, 1);
  assert.equal(giden[0].url, "https://api.resend.com/emails");
  assert.equal(giden[0].init.headers.Authorization, "Bearer re_x");
  assert.deepEqual(giden[0].govde.to, ["mehmet.yilmaz@diyanet.gov.tr"]);
  assert.equal(giden[0].govde.from, "Kimin Cenazesi <dogrulama@kimincenazesi.com>");
  assert.equal(giden[0].govde.subject, "Kimin Cenazesi doğrulama kodu");
  assert.match(giden[0].govde.text, /\d{6}/); assert.ok(!/https?:/.test(giden[0].govde.text), "bağlantı yok");
  assert.ok(e.AILE.m.get("gorevli:ek:mehmet.yilmaz").ttl <= 600, "10 dk");
});

test("eposta-kod: anahtar yok + GELISTIRME=0 -> 503; Resend hata verirse 502 ve kod saklanmaz; GELISTIRME=1 yanıtta kod", async () => {
  assert.equal((await cagir(env({ GELISTIRME: "0" }), "/gorevli/eposta-kod", { kullanici: KU })).s, 503);
  const e = env({ RESEND_ANAHTARI: "re_x", GELISTIRME: "0" });
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { fetch: async () => ({ ok: false }) })).s, 502);
  assert.equal(e.AILE.m.has("gorevli:ek:" + KU), false);
  const dev = await cagir(env(), "/gorevli/eposta-kod", { kullanici: KU });
  assert.match(dev.gelistirme_kodu, /^\d{6}$/);
});

test("doğrulama: doğru kod -> hesap HEMEN 'onayli' + oturum (kontrol/bekleme yok); kod tek kullanımlık; telefon/foto yok", async () => {
  const e = env();
  const { h, d } = await giris(e);
  assert.equal(d.durum, "onayli"); assert.equal(d.profil_tamam, false); assert.equal(d.eposta, "mehmet.yilmaz@diyanet.gov.tr");
  assert.equal(e.AILE.m.has("gorevli:ek:" + KU), false, "kod tüketildi");
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "onayli");
  for (const [k, v] of e.AILE.m) { assert.ok(!k.startsWith("gorevli:foto:") && !k.startsWith("gorevli:t:")); assert.ok(!/telefon/.test(String(v.v)), k); }
  const kayit = [...e.AILE.m].find(([k]) => k.startsWith("gorevli:k:"));
  assert.ok(JSON.parse(kayit[1].v).gozetim_bitis, "ilk 7 gün gözetim");
  assert.equal((await cagir(e, "/gorevli/eposta-dogrula", { kullanici: KU, kod: "123456" })).s, 410, "eski kod geçmez");
});

test("yanlış kod: 5. yanlışta kod geçersiz (429); 6 hane dışı 400; kod yoksa 410", async () => {
  const e = env();
  await cagir(e, "/gorevli/eposta-kod", { kullanici: KU });
  assert.equal((await cagir(e, "/gorevli/eposta-dogrula", { kullanici: KU, kod: "12ab" })).s, 400);
  let son;
  for (let i = 1; i <= 4; i++) { son = await cagir(e, "/gorevli/eposta-dogrula", { kullanici: KU, kod: "000000" }); assert.equal(son.s, 400); assert.equal(son.kalan_deneme, 5 - i); }
  son = await cagir(e, "/gorevli/eposta-dogrula", { kullanici: KU, kod: "000000" });
  assert.equal(son.s, 429); assert.equal(son.durum, "red");
  assert.equal((await cagir(e, "/gorevli/eposta-dogrula", { kullanici: KU, kod: "000000" })).s, 410);
  assert.equal((await cagir(env(), "/gorevli/eposta-dogrula", { kullanici: KU, kod: "000000" })).s, 410);
});

test("YENİDEN GÖNDER 5 DAKİKA: 5 dk dolmadan 429 + kalan saniye; sonra yeni kod; günde en çok 5 kod", async () => {
  const e = env();
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU })).s, 200);
  const hemen = await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(61) });
  assert.equal(hemen.s, 429); assert.equal(hemen.hata, "cok_sik_tekrar"); assert.equal(hemen.bekle_sn, 239);
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(299) })).s, 429);
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(301) })).s, 200);
  for (let i = 2; i < 5; i++) assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(301 * i) })).s, 200);
  const alti = await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(301 * 5) });
  assert.equal(alti.s, 429); assert.equal(alti.hata, "gunluk_kod_siniri");
});

test("eski uçlar (/kayit /kod /giris /dogrula) 410 döner", async () => {
  const e = env();
  for (const y of ["/gorevli/kayit", "/gorevli/kod", "/gorevli/giris", "/gorevli/dogrula"]) assert.equal((await cagir(e, y, {})).s, 410, y);
});

test("PROFİL: ilan için önce ad-soyad/görev yeri/il/ilçe (bir kez); profil yokken ilan 409; geçersiz il/ilçe/unvan 400; ikinci kez 409", async () => {
  const e = env();
  const { h } = await giris(e);
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).hata, "profil_gerekli");
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL({ il: "Atlantis" }), { ek: h })).s, 400);
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL({ ilce: "Yok" }), { ek: h })).s, 400);
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL({ unvan: "Başkan" }), { ek: h })).s, 400);
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL({ ad_soyad: "Tek" }), { ek: h })).s, 400);
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL())).s, 401);
  const p = await cagir(e, "/gorevli/profil", PROFIL(), { ek: h });
  assert.equal(p.profil_tamam, true); assert.equal(p.gorev_yeri, "Korgan Merkez Camii");
  assert.equal((await cagir(e, "/gorevli/profil", PROFIL(), { ek: h })).s, 409);
  const d = await al(e, "/gorevli/durum", h);
  assert.equal(d.ad_soyad, "Mehmet Ali Yılmaz"); assert.equal(d.unvan, "İmam-Hatip"); assert.equal(d.profil_tamam, true);
});

test("tekrar giriş: aynı kullanıcı adı aynı hesaba döner (profil korunur); yeni oturum açılır", async () => {
  const e = env();
  await hazir(e);
  const { h, d } = await giris(e, KU, { now: dk(400) });
  assert.equal(d.profil_tamam, true); assert.equal(d.gorev_yeri, "Korgan Merkez Camii");
  assert.equal((await al(e, "/gorevli/ilanlarim", h)).hesap.ilce, "Korgan");
});

test("GÖREV YERİM DEĞİŞTİ: hesap güncellenir; sonraki ilan yeni il/ilçe/yerle; eski ilan değişmez; profil yokken 409; geçersiz 400; oturumsuz 401", async () => {
  const e = env();
  const { h: h0 } = await giris(e);
  assert.equal((await cagir(e, "/gorevli/gorev-yeri", { il: "Samsun", ilce: "Kavak", gorev_yeri: "Kavak Camii" }, { ek: h0 })).hata, "profil_gerekli");
  const e2 = env();
  const { h: hh } = await hazir(e2);
  const eski = await cagir(e2, "/gorevli/ilan", ilanGovde(), { ek: hh });
  assert.equal(eski.durum, "yayinda");
  assert.equal((await cagir(e2, "/gorevli/gorev-yeri", { il: "Samsun", ilce: "Kavak", gorev_yeri: "Kavak Camii" })).s, 401);
  assert.equal((await cagir(e2, "/gorevli/gorev-yeri", { il: "Samsun", ilce: "Yok", gorev_yeri: "Kavak Camii" }, { ek: hh })).s, 400);
  assert.equal((await cagir(e2, "/gorevli/gorev-yeri", { il: "Samsun", ilce: "Kavak", gorev_yeri: "K" }, { ek: hh })).s, 400);
  const g = await cagir(e2, "/gorevli/gorev-yeri", { il: "Samsun", ilce: "Kavak", gorev_yeri: "Kavak Camii", unvan: "Müezzin-Kayyım" }, { ek: hh });
  assert.equal(g.s, 200); assert.equal(g.il, "Samsun"); assert.equal(g.ilce, "Kavak"); assert.equal(g.gorev_yeri, "Kavak Camii"); assert.equal(g.unvan, "Müezzin-Kayyım");
  assert.equal(g.ad_soyad, "Mehmet Ali Yılmaz", "ad değişmez");
  const d = await al(e2, "/gorevli/durum", hh);
  assert.equal(d.gorev_yeri, "Kavak Camii"); assert.equal(d.il, "Samsun");
  const yeni = await cagir(e2, "/gorevli/ilan", ilanGovde({ ad_soyad: "Başka Örnek Kişi" }), { ek: hh });
  assert.equal(yeni.durum, "yayinda");
  const samsun = (await al(e2, "/gorevli/samsun.json")).kayitlar;
  assert.equal(samsun.length, 1); assert.equal(samsun[0].ilce, "Kavak"); assert.equal(samsun[0].gorev_yeri, "Kavak Camii");
  const ordu = (await al(e2, "/gorevli/ordu.json")).kayitlar;
  assert.equal(ordu.length, 1); assert.equal(ordu[0].gorev_yeri, "Korgan Merkez Camii", "eski ilan değişmez"); assert.equal(ordu[0].ilce, "Korgan");
});

test("ilan: il/ilçe istekten değil hesaptan; liste JSON'da kişisel veri yok; iptal; K kuralları (K2, K3, K5)", async () => {
  const e = env();
  const { h } = await hazir(e);
  const il = await cagir(e, "/gorevli/ilan", ilanGovde({ il: "Adana", ilce: "Seyhan" }), { ek: h });
  assert.equal(il.durum, "yayinda");
  const ordu = await al(e, "/gorevli/ordu.json");
  const k = ordu.kayitlar[0];
  assert.equal(k.gorevli, true); assert.equal(k.ilce, "Korgan"); assert.equal(k.gorev_yeri, "Korgan Merkez Camii");
  const ham = JSON.stringify(ordu);
  for (const y of ["Mehmet Ali Yılmaz", "mehmet.yilmaz", "diyanet.gov.tr", "eposta", "kayit_id", "basvuran", "telefon"]) assert.ok(!ham.includes(y), `sızıntı ${y}`);
  assert.equal((await al(e, "/gorevli/adana.json")).kayitlar.length, 0);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ ad_soyad: "Tek" }), { ek: h })).neden, /K2/);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).neden, /K5/);
  assert.equal((await cagir(e, "/gorevli/ilan/iptal", { ilan_id: il.ilan_id }, { ek: h })).durum, "iptal");
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 0);
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde())).s, 401);
});

test("gözetim: 2 bildirim ilanı gizler ve hesabı dondurur; donmuş hesaba kod gitmez, giriş 403; sahibi açınca devam", async () => {
  const e = env();
  const { h } = await hazir(e);
  const il = await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h });
  assert.equal((await al(e, "/gorevli/kuyruk", PANEL)).gozetim.length, 1);
  await cagir(e, "/aile/bildir", { ilan_id: il.ilan_id, neden: "yanlış" });
  await cagir(e, "/aile/bildir", { ilan_id: il.ilan_id, neden: "yanlış" });
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 0);
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "donduruldu");
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(400) })).s, 403);
  const id = [...e.AILE.m.keys()].find((k) => k.startsWith("gorevli:k:")).slice(10);
  assert.equal((await cagir(e, "/gorevli/karar", { id, ac: true }, { ek: PANEL })).durum, "onayli");
  assert.equal((await cagir(e, "/gorevli/eposta-kod", { kullanici: KU }, { now: dk(400) })).s, 200);
});

test("sahibi dondurma tek tık; panel uçları anahtarsız 403", async () => {
  const e = env();
  await hazir(e);
  const id = [...e.AILE.m.keys()].find((k) => k.startsWith("gorevli:k:")).slice(10);
  assert.equal((await cagir(e, "/gorevli/karar", { id, dondur: true })).s, 403);
  assert.equal((await cagir(e, "/gorevli/karar", { id, dondur: true }, { ek: PANEL })).durum, "donduruldu");
});

test("ŞEHİT İLANI yalnız din görevlisi panelinden: rütbe ister; listede duyuru bağlantısı çıkmaz", async () => {
  const e = env();
  const { h } = await hazir(e);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true }), { ek: h })).neden, /rütbe/);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true, rutbe: "Piyade Uzman Çavuş", duyuru_url: "http://x.test/a" }), { ek: h })).neden, /https/);
  const r = await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true, rutbe: "Piyade Uzman Çavuş", toren_yeri: "Korgan Merkez Camii öğle", duyuru_url: "https://www.msb.gov.tr/duyuru/1" }), { ek: h });
  assert.equal(r.durum, "yayinda");
  const kayit = (await al(e, "/gorevli/ordu.json")).kayitlar[0];
  assert.equal(kayit.sehit, true); assert.ok(!JSON.stringify(kayit).includes("msb.gov.tr"));
});

test("KVKK: e-posta adresi yalnız hesap kaydında; halka açık liste, durum ve kuyruk çıktısında e-posta/kullanıcı adı yok", async () => {
  const e = env();
  const { h } = await hazir(e);
  await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h });
  for (const y of [await al(e, "/gorevli/ordu.json"), await al(e, "/gorevli/durum", h), await al(e, "/gorevli/ilanlarim", h), await al(e, "/gorevli/kuyruk", PANEL)]) {
    const ham = JSON.stringify(y);
    assert.ok(!ham.includes("diyanet.gov.tr") && !ham.includes("mehmet.yilmaz"), ham.slice(0, 120));
  }
});

test("DÜZELTME (§49): duzeltme_id doğrulanır; çıktıda görünür; aynı id ikinci kez yeni kayıt açmaz, eskisini günceller; başka hesap ayrı kayıt", async () => {
  const e = env();
  const { h } = await hazir(e);
  for (const kotu of ["XYZ", "../x", "a".repeat(40), 5]) assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde({ duzeltme_id: kotu }), { ek: h })).s, 400, String(kotu));
  const a = await cagir(e, "/gorevli/ilan", ilanGovde({ duzeltme_id: "a30d5cab8953", ad_soyad: "Fatma Doğru Ad" }), { ek: h });
  assert.equal(a.durum, "yayinda");
  const b = await cagir(e, "/gorevli/ilan", ilanGovde({ duzeltme_id: "a30d5cab8953", ad_soyad: "Fatma Doğru Ad", defin_yeri: "Korgan Mezarlığı" }), { ek: h });
  assert.equal(b.ilan_id, a.ilan_id); assert.equal(b.guncellendi, true);
  const ordu = (await al(e, "/gorevli/ordu.json")).kayitlar;
  assert.equal(ordu.length, 1); assert.equal(ordu[0].duzeltme_id, "a30d5cab8953"); assert.equal(ordu[0].defin_yeri, "Korgan Mezarlığı");
  const lm = (await al(e, "/gorevli/ilanlarim", h)).ilanlar;
  assert.equal(lm.length, 1); assert.equal(lm[0].duzeltme_id, "a30d5cab8953");
  const c = await cagir(e, "/gorevli/ilan", ilanGovde({ ad_soyad: "Düz Yeni Kişi" }), { ek: h });
  assert.notEqual(c.ilan_id, a.ilan_id);
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.find((x) => x.ad_soyad.startsWith("Düz")).duzeltme_id, null);
});

test("KVKK KABUL (§50): oturumsuz 401; kabul hesap kaydına tarih yazar; /durum ve /ilanlarim kabul tarihini döner", async () => {
  const e = env();
  assert.equal((await cagir(e, "/gorevli/kvkk-kabul", {})).s, 401);
  const { h } = await hazir(e);
  assert.equal((await al(e, "/gorevli/durum", h)).kvkk_kabul, null);
  const r = await cagir(e, "/gorevli/kvkk-kabul", {}, { ek: h });
  assert.equal(r.s, 200); assert.equal(r.kvkk_kabul, NOW.toISOString());
  assert.equal((await al(e, "/gorevli/durum", h)).kvkk_kabul, NOW.toISOString());
});

test("SORUMLULUK KABUL (§54): oturumsuz 401; kabul hesap kaydına tarih yazar; /durum sorumluluk_kabul döner; kvkk kaydını etkilemez", async () => {
  const e = env();
  assert.equal((await cagir(e, "/gorevli/sorumluluk-kabul", {})).s, 401);
  const { h } = await hazir(e);
  assert.equal((await al(e, "/gorevli/durum", h)).sorumluluk_kabul, null);
  const r = await cagir(e, "/gorevli/sorumluluk-kabul", {}, { ek: h });
  assert.equal(r.s, 200); assert.equal(r.sorumluluk_kabul, NOW.toISOString());
  const d = await al(e, "/gorevli/durum", h);
  assert.equal(d.sorumluluk_kabul, NOW.toISOString()); assert.equal(d.kvkk_kabul, null);
});
