import test from "node:test";
import assert from "node:assert/strict";
import { isle } from "../src/index.js";
import { kartEslesir, listeDurumu, fotoGecerli, telefonNormalize, BEYAN_METNI } from "../src/gorevli.js";
import { kartKarar, yanitCoz, tcMaskele, UNVANLAR } from "../src/gorevli_kurallar.js";

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
const NOW = new Date("2026-10-15T09:00:00Z");
const FOTO = "/9j/" + "A".repeat(4000); // sahte JPEG gövdesi
// Sahte görüntü modeli: kart metni; JSON döner. ek -> JSON alanlarını ezer
const sahteAI = (metin, { ek = {} } = {}) => ({
  calls: 0, son: null,
  async run(model, girdi) {
    this.calls++; this.son = { model, girdi };
    return { response: JSON.stringify({ metin, diyanet_ibaresi: true, kart_turu_ibaresi: true, ad_soyad: "x", unvan: "İmam-Hatip", il_ilce_kurum: "Ordu Korgan İlçe Müftülüğü", sicil_var: true, fiziksel_kart: true, ...ek }) };
  },
});
const env = (ai, ek = {}) => ({ AILE: new KV(), GELISTIRME: "1", PANEL_ANAHTARI: "panel-x", AI: ai, ...ek });
let ipN = 0;
function istek(yol, govde, { method = "POST", ip, ek = {}, ham } = {}) {
  return new Request("https://w.test" + yol, { method, headers: { "Content-Type": "application/json", "CF-Connecting-IP": ip || `10.1.0.${++ipN}`, ...ek }, body: method === "POST" ? (ham ?? JSON.stringify(govde)) : undefined });
}
const cagir = async (e, yol, govde, o = {}) => { const r = await isle(istek(yol, govde, o), e, null, { now: o.now || NOW, ...(o.fetch ? { fetch: o.fetch } : {}) }); return { s: r.status, ...(await r.json()) }; };
const al = async (e, yol, ek = {}) => { const r = await isle(istek(yol, null, { method: "GET", ek }), e, null, { now: NOW }); return { s: r.status, ...(await r.json()) }; };
const PANEL = { "x-gizli": "panel-x" };
const TEL = "0532 111 22 33";
const KAYIT = (ek = {}) => ({ ad_soyad: "Mehmet Ali Yılmaz", il: "Ordu", ilce: "Korgan", gorev_yeri: "Korgan Merkez Camii", telefon: TEL, beyan: true, ...ek });
const KART = "T.C. DİYANET İŞLERİ BAŞKANLIĞI PERSONEL KİMLİK KARTI MEHMET ALİ YILMAZ İMAM-HATİP";
const LISTE = { ordu: { korgan: [{ ad_soyad: "Hafız Mehmet Ali Yılmaz", cami: "Merkez Camii" }] } };
const ilanGovde = (ek = {}) => ({ ad_soyad: "Deneme Örnek Kişi", cinsiyet: "e", yas: 80, vefat_tarihi: "2026-10-14", namaz_tarihi: "2026-10-15", namaz_yeri_vakti: "Merkez Camii öğle", koy: "Örnek Köyü", ...ek });

async function hesapAc(e, { kayit = KAYIT(), liste = true } = {}) {
  if (liste) { const r = await cagir(e, "/gorevli/liste", { liste: LISTE }, { ek: PANEL }); assert.equal(r.s, 200); }
  const a1 = await cagir(e, "/gorevli/kayit", kayit);
  assert.equal(a1.durum, "foto_gerek");
  assert.equal(a1.foto_kodu, undefined, "kâğıttaki kod kaldırıldı");
  const a2 = await cagir(e, "/gorevli/kayit", { kayit_id: a1.kayit_id, foto_base64: FOTO });
  return { a1, a2 };
}
const yenidenDene = (e, kayit_id) => cagir(e, "/gorevli/kayit", { kayit_id, foto_base64: FOTO });

// Telefon kodunu (yanıttaki gelistirme_kodu) girip doğrular; etkin oturum başlığını döner
async function oturum(e, a2) {
  assert.equal(a2.dogrulama, "kod");
  const d = await cagir(e, "/gorevli/dogrula", { kayit_id: a2.kayit_id, kod: a2.gelistirme_kodu });
  assert.equal(d.s, 200, JSON.stringify(d));
  return { Authorization: `Bearer ${d.oturum}` };
}

test("saf: kartEslesir Türkçe harf toleranslı, DİYANET ve tüm ad sözcükleri şart", () => {
  assert.ok(kartEslesir("DİYANET İŞLERİ\nMEHMET ALİ YILMAZ", "Mehmet Ali Yılmaz"));
  assert.ok(kartEslesir("diyanet isleri mehmet ali yilmaz", "Mehmet Ali Yılmaz"));
  assert.ok(!kartEslesir("DİYANET MEHMET YILMAZ", "Mehmet Ali Yılmaz"));
  assert.ok(!kartEslesir("MEHMET ALİ YILMAZ", "Mehmet Ali Yılmaz"));
});
test("saf: listeDurumu — liste yalnız PUAN; cami eşleşmesi zorunlu değil; liste yoksa 'liste_yok'; fotoGecerli", () => {
  const L = LISTE.ordu.korgan;
  assert.deepEqual(listeDurumu(L, "Mehmet Ali Yılmaz", "Korgan Merkez Camii"), { durum: "ad_var", cami_eslesti: true });
  assert.deepEqual(listeDurumu(L, "Mehmet Ali Yılmaz", "Yeni Camii"), { durum: "ad_var", cami_eslesti: false });
  assert.deepEqual(listeDurumu(L, "Ali Kaya", "Merkez Camii"), { durum: "listede_yok", cami_eslesti: false });
  assert.deepEqual(listeDurumu(undefined, "Ali Kaya", "Merkez Camii"), { durum: "liste_yok", cami_eslesti: false });
  assert.ok(fotoGecerli(FOTO) && !fotoGecerli("abc") && !fotoGecerli("/9j/" + "A".repeat(3 * 1024 * 1024)));
});

test("FOTOĞRAF KV'ye YAZILMAZ: onaylı kayıtta hiçbir anahtar/değer fotoğrafı içermez", async () => {
  const ai = sahteAI(KART);
  const e = env(ai);
  const { a2 } = await hesapAc(e);
  assert.equal(a2.durum, "onayli");
  assert.equal(ai.calls, 1);
  for (const [k, v] of e.AILE.m) {
    assert.ok(!k.startsWith("gorevli:foto:"), `foto anahtarı: ${k}`);
    assert.ok(!String(v.v).includes(FOTO.slice(0, 200)), `fotoğraf içeriği KV'de: ${k}`);
  }
  const k = JSON.parse(e.AILE.m.get(`gorevli:k:${a2.kayit_id}`).v);
  assert.equal(k.dogrulama, "kart+muftuluk_listesi");
  assert.ok(k.gozetim_bitis, "ilk 7 gün gözetim");
});
test("ilk deneme tutmazsa deneme2: fotoğraf yine KV'de YOK", async () => {
  const e = env(sahteAI("alakasız metin", { ek: { diyanet_ibaresi: false } }));
  const { a2 } = await hesapAc(e);
  assert.equal(a2.durum, "deneme2");
  assert.equal(a2.wa_kod, undefined, "kart tutmadan WhatsApp doğrulaması başlamaz");
  for (const [k, v] of e.AILE.m) { assert.ok(!k.startsWith("gorevli:foto:")); assert.ok(!String(v.v).includes(FOTO.slice(0, 200))); }
});
test("NİHAİ KURAL: kart tutmazsa liste olsa bile onay YOK -> iki denemeden sonra kuyruk (fotoğraf 7 gün)", async () => {
  const e = env(sahteAI("alakasız", { ek: { diyanet_ibaresi: false } }));
  const { a1, a2 } = await hesapAc(e);
  assert.equal(a1.liste_eslesti, true);
  assert.equal(a2.durum, "deneme2");
  const b = await yenidenDene(e, a2.kayit_id);
  assert.equal(b.durum, "kuyruk");
  assert.equal(e.AILE.m.get(`gorevli:foto:${b.kayit_id}`).ttl, 7 * 86400);
});
test("KABUL KURALI B: kart geçerse LİSTE OLMASA DA onaylı; liste eşleşirse puan +1 ve dogrulama 'kart+muftuluk_listesi'", async () => {
  const e1 = env(sahteAI(KART));
  const { a2: a } = await hesapAc(e1, { liste: false });
  assert.equal(a.durum, "onayli"); assert.equal(a.liste_eslesti, false);
  const ka = JSON.parse(e1.AILE.m.get(`gorevli:k:${a.kayit_id}`).v);
  assert.equal(ka.dogrulama, "kart");
  const e2 = env(sahteAI(KART));
  const { a2: b } = await hesapAc(e2, { kayit: KAYIT({ gorev_yeri: "Başka Köyü Camii" }) });
  assert.equal(b.durum, "onayli"); assert.equal(b.cami_eslesti, false);
  const kb = JSON.parse(e2.AILE.m.get(`gorevli:k:${b.kayit_id}`).v);
  assert.equal(kb.kart_puan, ka.kart_puan + 1);
  // ad listede yok -> yine onaylı
  const e3 = env(sahteAI(KART.replace("MEHMET ALİ YILMAZ", "ALİ KAYA DEMİR")));
  const { a2: c } = await hesapAc(e3, { kayit: KAYIT({ ad_soyad: "Ali Kaya Demir" }) });
  assert.equal(c.durum, "onayli");
});
test("BEYAN: kutu işaretlenmeden kayıt 400; beyan_tarihi kaydedilir", async () => {
  const e = env(sahteAI(KART));
  assert.equal(BEYAN_METNI, "Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum.");
  const yok = await cagir(e, "/gorevli/kayit", { ...KAYIT(), beyan: undefined });
  assert.equal(yok.s, 400); assert.equal(yok.hata, "beyan_gerekli");
  assert.equal((await cagir(e, "/gorevli/kayit", KAYIT({ beyan: false }))).s, 400);
  const a1 = await cagir(e, "/gorevli/kayit", KAYIT());
  const k = JSON.parse(e.AILE.m.get(`gorevli:k:${a1.kayit_id}`).v);
  assert.equal(k.beyan, true); assert.equal(k.beyan_tarihi, NOW.toISOString());
});
test("KOD KANALI: WhatsApp şablonu -> Netgsm SMS -> GELISTIRME; yok + GELISTIRME=0 -> 503; kullanıcı kodu başvuru ekranına girer (dogrula)", async () => {
  assert.equal((await cagir(env(sahteAI(KART), { GELISTIRME: "0" }), "/gorevli/kayit", KAYIT())).s, 503);
  const e = env(sahteAI(KART), { WA_TOKEN: "tk", WA_PHONE_ID: "123", NETGSM_KULLANICI: "u", NETGSM_SIFRE: "p", NETGSM_BASLIK: "B" });
  await cagir(e, "/gorevli/liste", { liste: LISTE }, { ek: PANEL });
  const giden = [];
  const f = async (url, init) => { giden.push({ url, govde: JSON.parse(init.body) }); return { ok: true, json: async () => ({ code: "00" }) }; };
  const a1 = await cagir(e, "/gorevli/kayit", KAYIT());
  const a2 = await cagir(e, "/gorevli/kayit", { kayit_id: a1.kayit_id, foto_base64: FOTO }, { fetch: f });
  assert.equal(a2.kanal, "whatsapp"); assert.equal(a2.gelistirme_kodu, undefined);
  assert.equal(giden.length, 1); assert.equal(giden[0].govde.template.name, "kc_dogrulama"); assert.equal(giden[0].govde.to, "905321112233");
  const kod = giden[0].govde.template.components[0].parameters[0].text;
  const d = await cagir(e, "/gorevli/dogrula", { kayit_id: a2.kayit_id, kod });
  assert.equal(d.durum, "onayli"); assert.ok(d.oturum);
  const e2 = env(sahteAI(KART), { WA_TOKEN: "tk", WA_PHONE_ID: "123", NETGSM_KULLANICI: "u", NETGSM_SIFRE: "p", NETGSM_BASLIK: "B" });
  const g2 = [];
  const f2 = async (url) => { g2.push(url); return url.includes("graph.facebook") ? { ok: false } : { ok: true, json: async () => ({ code: "00" }) }; };
  const b1 = await cagir(e2, "/gorevli/kayit", KAYIT());
  const b2 = await cagir(e2, "/gorevli/kayit", { kayit_id: b1.kayit_id, foto_base64: FOTO }, { fetch: f2 });
  assert.equal(b2.kanal, "sms"); assert.equal(g2.length, 2);
  const e3 = env(sahteAI(KART), { WA_TOKEN: "tk", WA_PHONE_ID: "123" });
  const c1 = await cagir(e3, "/gorevli/kayit", KAYIT());
  assert.equal((await cagir(e3, "/gorevli/kayit", { kayit_id: c1.kayit_id, foto_base64: FOTO }, { fetch: async () => ({ ok: false }) })).s, 502);
  const { a2: dev } = await hesapAc(env(sahteAI(KART)));
  assert.match(dev.gelistirme_kodu, /^\d{6}$/); assert.equal(dev.kanal, null);
});
test("yanlış kod reddedilir; kod 60 sn içinde yeniden gönderilemez; sonra gönderilir", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  assert.equal((await cagir(e, "/gorevli/dogrula", { kayit_id: a2.kayit_id, kod: "000000" })).s, 400);
  assert.equal((await cagir(e, "/gorevli/kod", { kayit_id: a2.kayit_id })).s, 429);
  const sonra = new Date(NOW.getTime() + 61000);
  const y = await cagir(e, "/gorevli/kod", { kayit_id: a2.kayit_id }, { now: sonra });
  assert.equal(y.s, 200); assert.match(y.gelistirme_kodu, /^\d{6}$/);
  assert.equal((await cagir(e, "/gorevli/dogrula", { kayit_id: a2.kayit_id, kod: y.gelistirme_kodu }, { now: sonra })).durum, "onayli");
});
test("ONAY: kart tutmayan hesap kuyruğa düşer (panel açık, İlan paylaş pasif); sahibi onaylayınca durum sorgusu 'onayli' olur, Netgsm varsa yedek SMS gider", async () => {
  const e = env(sahteAI("alakasız", { ek: { diyanet_ibaresi: false } }));
  const { a2 } = await hesapAc(e);
  const b = await yenidenDene(e, a2.kayit_id);
  assert.equal(b.durum, "kuyruk");
  const h = await oturum(e, b);
  const lm = await al(e, "/gorevli/ilanlarim", h);
  assert.equal(lm.s, 200); assert.deepEqual(lm.ilanlar, []);
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).s, 403);
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "kuyruk");
  const hk = e.AILE.m.get(`gorevli:k:${b.kayit_id}`);
  assert.ok(hk.exp && hk.exp * 1000 <= NOW.getTime() + 14 * 86400000 + 1000, "en çok 14 gün");
  const q = await al(e, "/gorevli/kuyruk", PANEL);
  assert.equal(q.kuyruk.length, 1); assert.ok(q.kuyruk[0].foto_base64);
  Object.assign(e, { NETGSM_KULLANICI: "u", NETGSM_SIFRE: "p", NETGSM_BASLIK: "KIMINCENAZE" });
  const giden = [];
  const f = async (url, init) => { giden.push(JSON.parse(init.body)); return { ok: true, json: async () => ({ code: "00" }) }; };
  const k = await cagir(e, "/gorevli/karar", { id: b.kayit_id, onay: true }, { ek: PANEL, fetch: f });
  assert.equal(k.durum, "onayli");
  assert.equal(giden.length, 1);
  assert.match(giden[0].messages[0].msg, /din görevlisi başvurunuz onaylandı, paneliniz açıldı/);
  assert.equal(giden[0].messages[0].no, "5321112233");
  assert.equal(e.AILE.m.has(`gorevli:foto:${b.kayit_id}`), false);
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "onayli");
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).durum, "yayinda");
});
test("RED: hesap, oturum eşlemesi, foto, telefon dizini KV'den SİLİNİR; uygulama 'silindi' görür; aynı telefonla yeniden başvurulabilir", async () => {
  const e = env(sahteAI("alakasız", { ek: { diyanet_ibaresi: false } }));
  const { a2 } = await hesapAc(e);
  const b = await yenidenDene(e, a2.kayit_id);
  const h = await oturum(e, b);
  assert.ok(e.AILE.m.has(`gorevli:foto:${b.kayit_id}`));
  assert.equal((await cagir(e, "/gorevli/karar", { id: b.kayit_id, onay: false }, { ek: PANEL })).durum, "silindi");
  for (const [k] of e.AILE.m) {
    assert.ok(!k.startsWith("gorevli:foto:") && !k.startsWith("gorevli:k:") && !k.startsWith("gorevli:t:") && !k.startsWith("gorevli:ac:"), `kalıntı: ${k}`);
  }
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "silindi");
  assert.equal((await al(e, "/gorevli/ilanlarim", h)).s, 401);
  assert.equal((await cagir(e, "/gorevli/kayit", KAYIT())).durum, "foto_gerek");
});

test("kayıt: il/ilçe/görev yeri kayıttan alınır (istekteki il/ilçe yok sayılır) ve ilan anında yayında; liste JSON'da kişisel veri yok", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  const il = await cagir(e, "/gorevli/ilan", ilanGovde({ il: "Adana", ilce: "Seyhan" }), { ek: h });
  assert.equal(il.durum, "yayinda");
  const ordu = await al(e, "/gorevli/ordu.json");
  assert.equal(ordu.kayitlar.length, 1);
  const k = ordu.kayitlar[0];
  assert.equal(k.gorevli, true); assert.equal(k.ilce, "Korgan"); assert.equal(k.gorev_yeri, "Korgan Merkez Camii"); assert.equal(k.mahalle, "Örnek Köyü");
  const ham = JSON.stringify(ordu);
  for (const y of ["Mehmet Ali Yılmaz", "5321112233", "532", "telefon", "eposta", "kayit_id", "basvuran", "KC-", "wa_"]) assert.ok(!ham.includes(y), `sızıntı ${y}`);
  assert.equal((await al(e, "/gorevli/adana.json")).kayitlar.length, 0);
  const lm = await al(e, "/gorevli/ilanlarim", h);
  assert.equal(lm.ilanlar.length, 1);
  assert.equal((await cagir(e, "/gorevli/ilan/iptal", { ilan_id: il.ilan_id }, { ek: h })).durum, "iptal");
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 0);
});
test("K kuralları görevli ilanında da işler (K2 ad, K3 tarih, K5 yinelenen); oturumsuz 401", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde())).s, 401);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ ad_soyad: "Tek" }), { ek: h })).neden, /K2/);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ namaz_tarihi: "2026-10-25", vefat_tarihi: "2026-10-24" }), { ek: h })).neden, /K3/);
  assert.equal((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).durum, "yayinda");
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h })).neden, /K5/);
});
test("TEK HESAP: aynı ad + cami için ikinci kayıt -> iki hesap da donar, ilanlar gizlenir, kuyruk 'cakisma' listeler", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h });
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 1);
  const { a2: b2 } = await hesapAc(e, { kayit: KAYIT({ telefon: "0533 222 33 44" }) });
  assert.equal(b2.durum, "kontrol_bekliyor");
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 0);
  const q = await al(e, "/gorevli/kuyruk", PANEL);
  assert.equal(q.cakisma.length, 2);
  assert.equal((await al(e, "/gorevli/ilanlarim", h)).s, 403);
});
test("gözetim: onaylı hesap (ilk 7 gün) kuyruğun 'gozetim' bölümünde; 2 bildirim ilanı gizler ve hesabı dondurur; /aile/bildir görevli ilanı için çalışır", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  const il = await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h });
  assert.equal((await al(e, "/gorevli/kuyruk", PANEL)).gozetim.length, 1);
  const cl = await al(e, "/gorevli/capraz", PANEL);
  assert.equal(cl.ilanlar.length, 1);
  await cagir(e, "/gorevli/capraz", { sonuclar: [{ ilan_id: il.ilan_id, eslesti: false }] }, { ek: PANEL });
  assert.equal((await al(e, "/gorevli/kuyruk", PANEL)).gozetim[0].capraz_toplam, 1);
  await cagir(e, "/aile/bildir", { ilan_id: il.ilan_id, neden: "yanlış" });
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 1);
  await cagir(e, "/aile/bildir", { ilan_id: il.ilan_id, neden: "yanlış" });
  assert.equal((await al(e, "/gorevli/ordu.json")).kayitlar.length, 0);
  assert.equal((await al(e, "/gorevli/durum", h)).durum, "donduruldu");
});
test("sahibi dondurma tek tık; panel uçları anahtarsız 403; OCR geçici hata deneme hakkını yakmaz", async () => {
  let n = 0;
  const gercek = sahteAI(KART);
  const ai = { async run(m, g) { if (++n === 1) throw new Error("x"); return gercek.run(m, g); } };
  const e = env(ai);
  await cagir(e, "/gorevli/liste", { liste: LISTE }, { ek: PANEL });
  const a1 = await cagir(e, "/gorevli/kayit", KAYIT());
  const hata = await cagir(e, "/gorevli/kayit", { kayit_id: a1.kayit_id, foto_base64: FOTO });
  assert.equal(hata.s, 503);
  assert.equal(JSON.parse(e.AILE.m.get(`gorevli:k:${a1.kayit_id}`).v).deneme, 0, "OCR hatasında deneme yanmaz");
  const ok = await cagir(e, "/gorevli/kayit", { kayit_id: a1.kayit_id, foto_base64: FOTO });
  assert.equal(ok.durum, "onayli");
  assert.equal((await cagir(e, "/gorevli/karar", { id: ok.kayit_id, dondur: true })).s, 403);
  assert.equal((await cagir(e, "/gorevli/liste", { liste: LISTE })).s, 403);
  assert.equal((await cagir(e, "/gorevli/karar", { id: ok.kayit_id, dondur: true }, { ek: PANEL })).durum, "donduruldu");
});
test("giriş (Hesabım var): telefon + kod; bilinmeyen telefon aynı biçimde yanıt alır ama kod üretilmez; hız sınırı", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  await oturum(e, a2);
  const sonra = new Date(NOW.getTime() + 61000);
  const g = await cagir(e, "/gorevli/giris", { telefon: "+90 532 111 22 33" }, { ip: "9.9.9.9", now: sonra });
  assert.equal(g.kayit_id, a2.kayit_id); assert.equal(g.dogrulama, "kod"); assert.match(g.gelistirme_kodu, /^\d{6}$/);
  const d = await cagir(e, "/gorevli/dogrula", { kayit_id: g.kayit_id, kod: g.gelistirme_kodu }, { now: sonra });
  assert.equal(d.durum, "onayli");
  assert.equal((await al(e, "/gorevli/durum", { Authorization: `Bearer ${d.oturum}` })).durum, "onayli");
  const g2 = await cagir(e, "/gorevli/giris", { telefon: "0555 999 99 99" });
  assert.equal(g2.s, 200); assert.equal(g2.dogrulama, "kod"); assert.notEqual(g2.kayit_id, a2.kayit_id); assert.equal(g2.gelistirme_kodu, undefined);
  assert.equal((await cagir(e, "/gorevli/kayit", { kayit_id: a2.kayit_id, foto_base64: "abc" })).s, 400);
  let son;
  for (let i = 0; i < 11; i++) son = await cagir(e, "/gorevli/giris", { telefon: "0555 888 88 88" }, { ip: "7.7.7.7" });
  assert.equal(son.s, 429);
});
test("ŞEHİT İLANI yalnız din görevlisi panelinden: sehit:true rütbe ister; listede sehit/rutbe/toren çıkar, duyuru bağlantısı ÇIKMAZ; https olmayan bağlantı red", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true }), { ek: h })).neden, /rütbe/);
  assert.match((await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true, rutbe: "Piyade Uzman Çavuş", duyuru_url: "http://x.test/a" }), { ek: h })).neden, /https/);
  const r = await cagir(e, "/gorevli/ilan", ilanGovde({ sehit: true, rutbe: "Piyade Uzman Çavuş", toren_yeri: "Korgan Merkez Camii öğle", duyuru_url: "https://www.msb.gov.tr/duyuru/1" }), { ek: h });
  assert.equal(r.durum, "yayinda");
  const kayit = (await al(e, "/gorevli/ordu.json")).kayitlar[0];
  assert.equal(kayit.sehit, true); assert.equal(kayit.rutbe, "Piyade Uzman Çavuş"); assert.equal(kayit.toren, "Korgan Merkez Camii öğle");
  assert.ok(!JSON.stringify(kayit).includes("msb.gov.tr"));
  const e2 = env(sahteAI(KART));
  const { a2: b2 } = await hesapAc(e2);
  const h2 = await oturum(e2, b2);
  await cagir(e2, "/gorevli/ilan", ilanGovde(), { ek: h2 });
  assert.equal((await al(e2, "/gorevli/ordu.json")).kayitlar[0].sehit, undefined);
});

test("KART KONTROLLERİ: zorunlu 1 ibare, 2 ad, 3 unvan, 6 fiziksel kart tek tek reddeder; kâğıt kodu YOK; 4/5 yalnız puan-uyarı", () => {
  const k = { ad_soyad: "Mehmet Ali Yılmaz", il: "Ordu", ilce: "Korgan" };
  const iyi = { metin: KART, unvan: "İmam-Hatip", il_ilce_kurum: "Ordu Korgan", sicil_var: true, fiziksel_kart: true };
  const r = kartKarar(iyi, k);
  assert.equal(r.gecti, true); assert.equal(r.puan, 2); assert.deepEqual(r.uyarilar, []);
  const red = (ek) => kartKarar({ ...iyi, ...ek }, k).nedenler;
  assert.ok(red({ metin: "PERSONEL KİMLİK KARTI MEHMET ALİ YILMAZ İMAM-HATİP" }).includes("diyanet_ibaresi_yok"));
  assert.ok(red({ metin: "T.C. DİYANET İŞLERİ BAŞKANLIĞI MEHMET ALİ YILMAZ İMAM-HATİP" }).includes("kart_turu_ibaresi_yok"));
  assert.ok(red({ metin: KART.replace("MEHMET ALİ YILMAZ", "AHMET KAYA") }).includes("ad_soyad_uyusmuyor"));
  assert.ok(red({ metin: KART.replace("İMAM-HATİP", "MEMUR"), unvan: "Memur" }).includes("unvan_tanimsiz"));
  assert.ok(red({ fiziksel_kart: false }).includes("fiziksel_kart_degil_ya_da_belirsiz"));
  assert.ok(red({ fiziksel_kart: undefined }).includes("fiziksel_kart_degil_ya_da_belirsiz"));
  assert.ok(!red({}).some((x) => x.includes("kod")), "kâğıttaki kod artık aranmaz");
  const az = kartKarar({ ...iyi, il_ilce_kurum: null, sicil_var: false }, k);
  assert.equal(az.gecti, true); assert.equal(az.puan, 0); assert.deepEqual(az.uyarilar.sort(), ["kartta_il_ilce_yok", "sicil_alani_yok"]);
  assert.ok(kartKarar({ ...iyi, il_ilce_kurum: "Rize Pazar" }, k).uyarilar.includes("kart_il_ilce_uyumsuz"));
  assert.ok(UNVANLAR.includes("Din Hizmetleri Uzmanı") && UNVANLAR.includes("Müftü Yardımcısı"));
  assert.deepEqual(yanitCoz("düz metin").metin, "düz metin");
});
test("model istemi: kayıttaki ad modele GÖNDERİLMEZ, kâğıt/kod anılmaz; görüntü bellekten data URI", async () => {
  const ai = sahteAI(KART);
  const e = env(ai);
  await hesapAc(e);
  const gonderilen = JSON.stringify(ai.son.girdi.messages[0].content[0]);
  assert.ok(!gonderilen.includes("Mehmet") && !/kâğıt/i.test(gonderilen));
  assert.match(ai.son.girdi.messages[0].content[1].image_url.url, /^data:image\/jpeg;base64,/);
  assert.equal(ai.son.model, "@cf/meta/llama-3.2-11b-vision-instruct");
});
test("unvan: kayıtta seçilen ya da karttan okunan; geçersiz unvan 400; durum yanıtında", async () => {
  const e = env(sahteAI(KART));
  assert.equal((await cagir(e, "/gorevli/kayit", KAYIT({ unvan: "Başkan" }))).s, 400);
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  assert.equal((await al(e, "/gorevli/durum", h)).unvan, "İmam-Hatip");
  const e2 = env(sahteAI(KART));
  const b1 = await cagir(e2, "/gorevli/kayit", KAYIT({ unvan: "Müezzin-Kayyım" }));
  assert.equal(JSON.parse(e2.AILE.m.get(`gorevli:k:${b1.kayit_id}`).v).unvan, "Müezzin-Kayyım");
});
test("telefon: +90 / 0 / boşluklu biçimler 10 haneye iner; geçersiz telefon 400; e-posta alanı artık yok", async () => {
  for (const t of ["+90 532 111 22 33", "0532 111 22 33", "532-111-22-33", "905321112233", "00905321112233"]) assert.equal(telefonNormalize(t), "5321112233");
  for (const t of ["123", "0212 111 22 33", "532111223", undefined, 5321112233]) assert.equal(telefonNormalize(t), null);
  const e = env(sahteAI(KART));
  assert.equal((await cagir(e, "/gorevli/kayit", KAYIT({ telefon: "12345" }))).s, 400);
  assert.equal((await cagir(e, "/gorevli/kayit", { ...KAYIT(), telefon: undefined, eposta: "x@example.com" })).s, 400);
});
test("KVKK: telefon hiçbir halka açık çıktıda, kuyrukta ya da durum yanıtında görünmez", async () => {
  const e = env(sahteAI(KART));
  const { a2 } = await hesapAc(e);
  const h = await oturum(e, a2);
  await cagir(e, "/gorevli/ilan", ilanGovde(), { ek: h });
  for (const y of [await al(e, "/gorevli/ordu.json"), await al(e, "/gorevli/durum", h), await al(e, "/gorevli/ilanlarim", h), await al(e, "/gorevli/kuyruk", PANEL)]) {
    const ham = JSON.stringify(y);
    assert.ok(!ham.includes("5321112233") && !ham.includes("telefon\"") && !ham.includes("wa_id"), ham.slice(0, 120));
  }
});

test("TC güvencesi: OCR metnindeki 11 haneli diziler maskelenir (yanıt/log/kayıt); 10 haneli sayı dokunulmaz", async () => {
  assert.equal(tcMaskele("TC 12345678901 ve 123 456 789 01 ve 1234567890"), "TC *********** ve *********** ve 1234567890");
  const y = yanitCoz(JSON.stringify({ metin: "KART 12345678901", fiziksel_kart: true }));
  assert.ok(!y.metin.includes("12345678901"));
  const e = env(sahteAI(KART + " 12345678901"));
  const { a2 } = await hesapAc(e);
  assert.equal(a2.durum, "onayli");
  assert.ok(![...e.AILE.m.values()].some((v) => String(v.v).includes("12345678901")), "KV'de TC yok");
  assert.ok(!JSON.stringify(a2).includes("12345678901"));
});
