// Aile ilanı Worker'ı — AILE-ILAN-SOZLESME.md. Yalnız standart Workers API; bağımlılık yok.
// KV (AILE) anahtarları:
//   b:<basvuru_id>        bekleyen başvuru (TTL 15 dk): ilan alanları + başvuran + kod özeti
//   i:<ilan_id>           ilan (tam kayıt; başvuran 30 gün sonra silinir) — TTL 120 gün
//   x:<il_slug>:<ilan_id> dizin; metadata {n: ad_norm, v: vefat, t: namaz} (K5 ve liste)
//   e:<sha256(telefon)>   telefon başına yayınlanan ilan zamanları (TTL 7 gün) — K6
//   r:<ip_ozeti>:<saat>   IP başına saatlik istek sayacı (TTL 1 saat)
//   n:<ilan_id>           bildirim yapan IP özetleri (ilan ömrü)
//   st:<il_slug>          {yayinda, gizli, red} sayaçları (panel)
//   bo:<basvuru_id>       Tam Sayfa: ödeme bekleyen ilan_id (TTL 2 gün); /aile/odeme bununla ilanı bulur
//   pt:<sha256(token)>    kullanılmış Play purchase_token → {ilan_id} (süresiz; aynı makbuz ikinci kez kullanılamaz)
//   od:<zaman>:<özet>     ödeme kaydı {ilan_id, order_id, odeme_dogrulandi, ...}; GET /aile/odemeler (x-gizli) listeler
import { ILCELER } from "./veri.js";
import { gorevliIsle, gorevliBildir } from "./gorevli.js";
import { kodGonder as kodKanali, kanalGerekli } from "./dogrulama.js";
import { playDogrula, URUN_KIMLIGI } from "./odeme.js";
import { degerlendir, girdiTemizle, adNormalize, bugunTR, gunEkle, gunFarki, ilSlug } from "./kurallar.js";
import { GUVENLIK_BASLIK, sinirliMetin, kilitliMi, basarisizKaydet } from "./guvenlik.js";   // 21.10.2026 guvenlik duvari

const SAAT_LIMIT = 10;
const KOD_OMRU_SN = 900;
const AZAMI_DENEME = 3;
const GOVDE_LIMIT = 4096;
const SAKLAMA_GUN = 30;
const ILAN_TTL_SN = 120 * 86400;
const ODEME_BEKLEME_SN = 2 * 86400;

const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
export async function sha256(s) { return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s))); }
const rastgeleId = () => hex(crypto.getRandomValues(new Uint8Array(8)));
function kod6() { const a = new Uint32Array(1); crypto.getRandomValues(a); return String(a[0] % 1000000).padStart(6, "0"); }

function izinliOriginler(env) {
  return (env.IZINLI_ORIGIN || "https://kimincenazesi.com,https://www.kimincenazesi.com").split(",").map((x) => x.trim()).filter(Boolean);
}
function originIzinli(origin, env) {
  if (!origin) return true; // uygulama (tarayıcı dışı) Origin göndermez
  if (izinliOriginler(env).includes(origin)) return true;
  return env.GELISTIRME === "1" && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
}
function corsBasliklari(req, env) {
  const o = req.headers.get("Origin");
  const h = { "Vary": "Origin" };
  if (o && originIzinli(o, env)) {
    h["Access-Control-Allow-Origin"] = o;
    h["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
    h["Access-Control-Allow-Headers"] = "Content-Type, Authorization, x-gizli";
    h["Access-Control-Max-Age"] = "600";
  }
  return h;
}
function yanit(req, env, govde, durum = 200, ek = {}) {
  return new Response(JSON.stringify(govde), {
    status: durum,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...GUVENLIK_BASLIK, ...corsBasliklari(req, env), ...ek },
  });
}

async function govdeOku(req) {
  const o = await sinirliMetin(req, GOVDE_LIMIT);   // 21.10.2026: Content-Length on kontrolu + akis sinirli okuma
  if (o.asildi) return { hata: "gövde çok büyük", durum: 413 };
  const m = o.metin;
  if (m.length > GOVDE_LIMIT) return { hata: "gövde çok büyük", durum: 413 };
  try { return { json: JSON.parse(m) }; } catch { return { hata: "geçersiz JSON", durum: 400 }; }
}

async function kvJson(kv, anahtar) {
  const v = await kv.get(anahtar);
  if (!v) return null;
  try { return JSON.parse(v); } catch { return null; }
}

async function hizSiniri(env, ipOzeti, now) {
  const saat = Math.floor(now.getTime() / 3600000);
  const k = `r:${ipOzeti}:${saat}`;
  const n = parseInt((await env.AILE.get(k)) || "0", 10);
  if (n >= SAAT_LIMIT) return false;
  await env.AILE.put(k, String(n + 1), { expirationTtl: 3700 });
  return true;
}

async function sayacArtir(env, slug, alan) {
  const k = `st:${slug}`;
  const s = (await kvJson(env.AILE, k)) || { yayinda: 0, gizli: 0, red: 0 };
  s[alan] = (s[alan] || 0) + 1;
  await env.AILE.put(k, JSON.stringify(s));
}

// ---- uç noktalar ----
async function basvur(req, env, o) {
  const g = await govdeOku(req);
  if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
  const t = girdiTemizle(g.json);
  if (t.hata) return yanit(req, env, { hata: t.hata }, 400);
  if (g.json?.tam !== true) return yanit(req, env, { hata: "aile ilanı kaldırıldı" }, 400); // 15.10.2026: ücretsiz aile ilanı yok; yalnız Tam Sayfa (200 ₺)
  if (g.json?.sehit === true) return yanit(req, env, { hata: "şehit ilanı yalnız din görevlisi" }, 400); // 15.10.2026: şehit ilanı yalnız din görevlisi panelinden
  if (kanalGerekli(env)) return yanit(req, env, { hata: "dogrulama_servisi_yok" }, 503);
  // Yeniden gönder: aynı telefon + ad + namaz tarihi, 15 dk içinde -> eski başvuru geçersiz, yeni kod; 60 sn'den sık 429. K6 sayacına yazılmaz (sayaç yalnız yayında artar).
  const tekrarKey = `bk:${await sha256(`${t.basvuran.telefon}|${adNormalize(t.ad_soyad)}|${t.namaz_tarihi}`)}`;
  const onceki = await kvJson(env.AILE, tekrarKey);
  if (onceki && o.now.getTime() - onceki.ts < 60000) return yanit(req, env, { hata: "cok_sik_tekrar", bekle_sn: Math.ceil((60000 - (o.now.getTime() - onceki.ts)) / 1000) }, 429, { "Retry-After": "60" });
  const id = rastgeleId();
  const kod = kod6();
  const kayit = { t, kod_ozeti: await sha256(`${id}:${kod}`), deneme: 0, olusturma: o.now.toISOString(), ip: o.ipOzeti };
  const kg = await kodKanali(env, o.fetch, t.basvuran.telefon, kod); // WhatsApp şablonu → Netgsm → (GELISTIRME=1) yanıtta
  if (kg.hata) return yanit(req, env, { hata: "kod_gonderilemedi" }, 502);
  if (onceki && onceki.id) await env.AILE.delete(`b:${onceki.id}`);
  await env.AILE.put(`b:${id}`, JSON.stringify(kayit), { expirationTtl: KOD_OMRU_SN });
  await env.AILE.put(tekrarKey, JSON.stringify({ id, ts: o.now.getTime() }), { expirationTtl: KOD_OMRU_SN });
  const cevap = { basvuru_id: id, dogrulama: "telefon", kanal: kg.kanal };
  if (kg.kod) cevap.gelistirme_kodu = kg.kod; // YALNIZ GELISTIRME=1 ve kanal yokken; üretimde asla
  return yanit(req, env, cevap);
}

async function ayniKisiVar(env, slug, adNorm, vefat) {
  let cursor;
  do {
    const l = await env.AILE.list({ prefix: `x:${slug}:`, cursor });
    for (const k of l.keys) {
      const m = k.metadata || {};
      if (m.n === adNorm && m.v && Math.abs(gunFarki(m.v, vefat)) <= 3) return true;
    }
    cursor = l.list_complete ? undefined : l.cursor;
  } while (cursor);
  return false;
}

async function dogrula(req, env, o) {
  const g = await govdeOku(req);
  if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
  const { basvuru_id, kod } = g.json || {};
  if (typeof basvuru_id !== "string" || !/^[0-9a-f]{16}$/.test(basvuru_id) || typeof kod !== "string" || !/^\d{6}$/.test(kod)) {
    return yanit(req, env, { hata: "basvuru_id ve 6 haneli kod gerekli" }, 400);
  }
  const bk = `b:${basvuru_id}`;
  const b = await kvJson(env.AILE, bk);
  if (!b) return yanit(req, env, { durum: "red", neden: "başvuru bulunamadı ya da süresi doldu" }, 410);
  if ((await sha256(`${basvuru_id}:${kod}`)) !== b.kod_ozeti) {
    b.deneme += 1;
    if (b.deneme >= AZAMI_DENEME) {
      await env.AILE.delete(bk);
      return yanit(req, env, { durum: "red", neden: "kod 3 kez yanlış girildi" }, 429);
    }
    await env.AILE.put(bk, JSON.stringify(b), { expirationTtl: KOD_OMRU_SN });
    return yanit(req, env, { hata: "kod_yanlis", kalan_deneme: AZAMI_DENEME - b.deneme }, 400);
  }
  await env.AILE.delete(bk); // kod tek kullanımlık
  const t = b.t;
  const slug = ilSlug(t.il);
  const eKey = `e:${await sha256(t.basvuran.telefon)}`;
  const gecmis = ((await kvJson(env.AILE, eKey)) || []).filter((z) => Date.parse(z) > o.now.getTime() - 7 * 86400000);
  const ayni = ILCELER[slug] ? await ayniKisiVar(env, slug, adNormalize(t.ad_soyad), t.vefat_tarihi) : false;
  const neden = degerlendir(t, { bugun: bugunTR(o.now), telefonIlanSayisi: gecmis.length, ayniKisiVar: () => ayni });
  if (neden) {
    await sayacArtir(env, ILCELER[slug] ? slug : "_gecersiz", "red");
    return yanit(req, env, { durum: "red", neden });
  }
  const ilanId = rastgeleId();
  const ilan = {
    id: ilanId, il: t.il, ilce: t.ilce, mahalle: t.mahalle ?? null, ad_soyad: t.ad_soyad, cinsiyet: t.cinsiyet, yas: t.yas ?? null,
    vefat_tarihi: t.vefat_tarihi, namaz_tarihi: t.namaz_tarihi, namaz_yeri_vakti: t.namaz_yeri_vakti ?? null, defin_yeri: t.defin_yeri ?? null,
    liste_tarihi: t.namaz_tarihi, aile: true,
    durum: t.tam ? "odeme_bekliyor" : "yayinda", olusturma: o.now.toISOString(), ip: o.ipOzeti,
    basvuran: { ad_soyad: t.basvuran.ad_soyad, telefon: t.basvuran.telefon, yakinlik: t.basvuran.yakinlik },
  };
  if (t.tam) {
    // Tam Sayfa (200 ₺): telefon kodu doğrulandı, ilan kaydedildi ama ÖDEME gelene dek yayında/dizinde/sayaçta değil
    ilan.tam = true;
    await env.AILE.put(`i:${ilanId}`, JSON.stringify(ilan), { expirationTtl: ODEME_BEKLEME_SN });
    await env.AILE.put(`bo:${basvuru_id}`, ilanId, { expirationTtl: ODEME_BEKLEME_SN });
    return yanit(req, env, { durum: "odeme_bekliyor", ilan_id: ilanId, basvuru_id });
  }
  await yayinaAl(env, ilan, slug, o.now);
  return yanit(req, env, { durum: "yayinda", ilan_id: ilanId });
}

// İlanı yayına alır: kayıt, dizin, telefon sayacı (K6), il sayacı. Normal ilanda doğrulamadan, Tam Sayfa'da ödemeden sonra çağrılır.
async function yayinaAl(env, ilan, slug, now) {
  const eKey = `e:${await sha256(ilan.basvuran.telefon)}`;
  const gecmis = ((await kvJson(env.AILE, eKey)) || []).filter((z) => Date.parse(z) > now.getTime() - 7 * 86400000);
  ilan.durum = "yayinda";
  await env.AILE.put(`i:${ilan.id}`, JSON.stringify(ilan), { expirationTtl: ILAN_TTL_SN });
  await env.AILE.put(`x:${slug}:${ilan.id}`, "1", { metadata: { n: adNormalize(ilan.ad_soyad), v: ilan.vefat_tarihi, t: ilan.namaz_tarihi }, expirationTtl: ILAN_TTL_SN });
  gecmis.push(now.toISOString());
  await env.AILE.put(eKey, JSON.stringify(gecmis), { expirationTtl: 7 * 86400 });
  await sayacArtir(env, slug, "yayinda");
}

// POST /aile/odeme {basvuru_id, purchase_token, order_id, urun}: Play makbuzu → ilan odeme_bekliyor → yayinda
async function odeme(req, env, o) {
  const g = await govdeOku(req);
  if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
  const { basvuru_id, purchase_token, order_id, urun } = g.json || {};
  if (typeof basvuru_id !== "string" || !/^[0-9a-f]{16}$/.test(basvuru_id)) return yanit(req, env, { hata: "basvuru_id gerekli" }, 400);
  if (typeof purchase_token !== "string" || !/^[A-Za-z0-9._\-]{16,512}$/.test(purchase_token)) return yanit(req, env, { hata: "purchase_token geçersiz" }, 400);
  if (order_id != null && order_id !== "" && (typeof order_id !== "string" || !/^[A-Za-z0-9._\-]{1,64}$/.test(order_id))) return yanit(req, env, { hata: "order_id geçersiz" }, 400);
  if (urun !== URUN_KIMLIGI) return yanit(req, env, { hata: "urun geçersiz" }, 400);
  const ilanId = await env.AILE.get(`bo:${basvuru_id}`);
  const ilan = ilanId ? await kvJson(env.AILE, `i:${ilanId}`) : null;
  if (!ilan || ilan.tam !== true) return yanit(req, env, { hata: "odeme_bekleyen_ilan_yok" }, 404);
  const ozet = await sha256(purchase_token);
  const kullanilmis = await kvJson(env.AILE, `pt:${ozet}`);
  if (kullanilmis) {
    // Aynı makbuz aynı ilan için yeniden gelirse (ağ kopması sonrası deneme) sonuç tekrarlanır; başka ilanda KULLANILAMAZ
    if (kullanilmis.ilan_id === ilan.id && ilan.durum === "yayinda") return yanit(req, env, { durum: "yayinda", ilan_id: ilan.id, odeme_dogrulandi: ilan.odeme_dogrulandi === true });
    return yanit(req, env, { hata: "token_kullanilmis" }, 409);
  }
  if (ilan.durum === "yayinda") return yanit(req, env, { durum: "yayinda", ilan_id: ilan.id, odeme_dogrulandi: ilan.odeme_dogrulandi === true });
  let dogrulandi = false, siparisNo = order_id || null, test = false;
  if (env.PLAY_SA_JSON) {
    const p = await playDogrula(env, o.fetch, purchase_token, order_id || null, o.now);
    if (!p.tamam) return yanit(req, env, { durum: "red", neden: p.neden }, p.gecici ? 502 : 402);
    dogrulandi = true; siparisNo = p.siparis_no; test = p.test === true;
  }
  await env.AILE.put(`pt:${ozet}`, JSON.stringify({ ilan_id: ilan.id, ts: o.now.toISOString() }));
  await env.AILE.put(`od:${o.now.toISOString()}:${ozet.slice(0, 8)}`, JSON.stringify({
    ilan_id: ilan.id, ad_soyad: ilan.ad_soyad, il: ilan.il, ilce: ilan.ilce, order_id: siparisNo, token_ozeti: ozet,
    odeme_dogrulandi: dogrulandi, test, zaman: o.now.toISOString(),
  }));
  ilan.odeme_dogrulandi = dogrulandi;
  ilan.siparis_no = siparisNo;
  await yayinaAl(env, ilan, ilSlug(ilan.il), o.now);
  await env.AILE.delete(`bo:${basvuru_id}`);
  return yanit(req, env, { durum: "yayinda", ilan_id: ilan.id, odeme_dogrulandi: dogrulandi });
}

// GET /aile/odemeler (x-gizli: PANEL_ANAHTARI): ödeme kayıtları, en yeni önce. odeme_dogrulandi:false olanlar Play Console sipariş listesiyle karşılaştırılır.
async function odemeler(req, env) {
  const anahtar = req.headers.get("x-gizli") || "";
  const izin = env.PANEL_ANAHTARI ? sabitKarsilastir(anahtar, env.PANEL_ANAHTARI) : env.GELISTIRME === "1";
  if (!izin) return yanit(req, env, { hata: "yetkisiz" }, 403);
  const liste = [];
  let cursor;
  do {
    const l = await env.AILE.list({ prefix: "od:", cursor });
    for (const k of l.keys) { const v = await kvJson(env.AILE, k.name); if (v) liste.push(v); }
    cursor = l.list_complete ? undefined : l.cursor;
  } while (cursor);
  liste.reverse();
  return yanit(req, env, { odemeler: liste.slice(0, 500), dogrulanmamis: liste.filter((x) => !x.odeme_dogrulandi).length });
}

// Halka açık çıktıda yalnız bu alanlar bulunur; başvuran, telefon, IP, ödeme/sipariş bilgisi ASLA
const GENEL_ALANLAR = ["id", "il", "ilce", "mahalle", "ad_soyad", "cinsiyet", "yas", "vefat_tarihi", "namaz_tarihi", "namaz_yeri_vakti", "defin_yeri", "liste_tarihi"];
export function genel(ilan) {
  const r = {};
  for (const a of GENEL_ALANLAR) r[a] = ilan[a] ?? null;
  r.aile = true;
  return r;
}

async function liste(req, env, slug, o) {
  const il = ILCELER[slug];
  if (!il) return yanit(req, env, { hata: "il bulunamadı" }, 404);
  const sinir = gunEkle(bugunTR(o.now), -7);
  const kayitlar = [];
  let cursor;
  do {
    const l = await env.AILE.list({ prefix: `x:${slug}:`, cursor });
    for (const k of l.keys) {
      if (k.metadata && k.metadata.t && k.metadata.t < sinir) continue;
      const ilan = await kvJson(env.AILE, `i:${k.name.split(":")[2]}`);
      if (ilan && ilan.durum === "yayinda" && ilan.liste_tarihi >= sinir) kayitlar.push(genel(ilan));
    }
    cursor = l.list_complete ? undefined : l.cursor;
  } while (cursor);
  kayitlar.sort((a, b) => (a.namaz_tarihi < b.namaz_tarihi ? 1 : a.namaz_tarihi > b.namaz_tarihi ? -1 : a.id < b.id ? -1 : 1));
  return yanit(req, env, { il: il.il, kayitlar, guncelleme: o.now.toISOString() }, 200, { "Cache-Control": "public, max-age=60" });
}

async function bildir(req, env, o) {
  const g = await govdeOku(req);
  if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
  const { ilan_id, neden } = g.json || {};
  if (typeof ilan_id !== "string" || !/^[0-9a-f]{16}$/.test(ilan_id)) return yanit(req, env, { hata: "ilan_id gerekli" }, 400);
  if (typeof neden !== "string" || neden.length > 60) return yanit(req, env, { hata: "neden en çok 60 karakter" }, 400);
  const ilan = await kvJson(env.AILE, `i:${ilan_id}`);
  if (!ilan || ilan.aile !== true) {
    const gb = await gorevliBildir(env, YARDIMCI, ilan_id, o.ipOzeti, o.now); // din görevlisi ilanı
    return gb ? yanit(req, env, gb) : yanit(req, env, { alindi: false }, 404);
  }
  const nk = `n:${ilan_id}`;
  const ipler = (await kvJson(env.AILE, nk)) || [];
  if (!ipler.includes(o.ipOzeti)) ipler.push(o.ipOzeti);
  await env.AILE.put(nk, JSON.stringify(ipler), { expirationTtl: ILAN_TTL_SN });
  if (ipler.length >= 2 && ilan.durum === "yayinda") {
    ilan.durum = "gizli";
    await env.AILE.put(`i:${ilan_id}`, JSON.stringify(ilan), { expirationTtl: ILAN_TTL_SN });
    const slug = ilSlug(ilan.il);
    await sayacArtir(env, slug, "gizli");
    const st = await kvJson(env.AILE, `st:${slug}`);
    if (st && st.yayinda > 0) { st.yayinda -= 1; await env.AILE.put(`st:${slug}`, JSON.stringify(st)); }
  }
  return yanit(req, env, { alindi: true });
}

function sabitKarsilastir(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let f = 0;
  for (let i = 0; i < a.length; i++) f |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return f === 0;
}

async function durum(req, env) {
  const yetki = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const izin = env.PANEL_ANAHTARI ? sabitKarsilastir(yetki, env.PANEL_ANAHTARI) : env.GELISTIRME === "1";
  if (!izin) return yanit(req, env, { hata: "yetkisiz" }, 403);
  const iller = {};
  let cursor;
  do {
    const l = await env.AILE.list({ prefix: "st:", cursor });
    for (const k of l.keys) iller[k.name.slice(3)] = (await kvJson(env.AILE, k.name)) || {};
    cursor = l.list_complete ? undefined : l.cursor;
  } while (cursor);
  return yanit(req, env, { iller });
}

// KVKK: 30 günden eski ilanlarda başvuran bilgisi ve IP özeti silinir; ilan kalır
export async function temizle(env, now = new Date()) {
  const esik = now.getTime() - SAKLAMA_GUN * 86400000;
  let cursor, temizlenen = 0;
  do {
    const l = await env.AILE.list({ prefix: "i:", cursor });
    for (const k of l.keys) {
      const ilan = await kvJson(env.AILE, k.name);
      if (ilan && (ilan.basvuran || ilan.ip) && Date.parse(ilan.olusturma) < esik) {
        ilan.basvuran = null; ilan.ip = null;
        await env.AILE.put(k.name, JSON.stringify(ilan), { expirationTtl: ILAN_TTL_SN });
        temizlenen++;
      }
    }
    cursor = l.list_complete ? undefined : l.cursor;
  } while (cursor);
  return temizlenen;
}

const YARDIMCI = { yanit, kvJson, sha256, rastgeleId, kod6, sabitKarsilastir };

export async function isle(req, env, ctx, secenek = {}) {
  const o = { now: secenek.now || new Date(), fetch: secenek.fetch || fetch };
  const url = new URL(req.url);
  const yol = url.pathname.replace(/\/+$/, "");
  if (!yol.startsWith("/aile/") && !yol.startsWith("/gorevli/")) return yanit(req, env, { hata: "bulunamadı" }, 404);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsBasliklari(req, env) });
  const origin = req.headers.get("Origin");
  if (origin && !originIzinli(origin, env)) return yanit(req, env, { hata: "origin_izinli_degil" }, 403);

  const hizli = req.method === "POST" && yol.startsWith("/gorevli/") && !["/gorevli/karar", "/gorevli/liste", "/gorevli/capraz"].includes(yol);
  if (hizli) {
    o.ipOzeti = await sha256(`${req.headers.get("CF-Connecting-IP") || "yok"}|${env.IP_TUZ || "aile"}`);
    if (!(await hizSiniri(env, o.ipOzeti, o.now))) return yanit(req, env, { hata: "cok_fazla_istek" }, 429, { "Retry-After": "3600" });
  }
  if (yol.startsWith("/gorevli/")) return gorevliIsle(req, env, o, YARDIMCI, yol);
  if (req.method === "GET") {
    const m = yol.match(/^\/aile\/([a-z0-9]{2,30})\.json$/);
    if (m) return liste(req, env, m[1], o);
    if (yol === "/aile/durum") return durum(req, env);
    if (yol === "/aile/odemeler") return odemeler(req, env);
    return yanit(req, env, { hata: "bulunamadı" }, 404);
  }
  if (req.method === "POST" && ["/aile/basvur", "/aile/dogrula", "/aile/bildir", "/aile/odeme"].includes(yol)) {
    o.ipOzeti = await sha256(`${req.headers.get("CF-Connecting-IP") || "yok"}|${env.IP_TUZ || "aile"}`);
    if (!(await hizSiniri(env, o.ipOzeti, o.now))) return yanit(req, env, { hata: "cok_fazla_istek" }, 429, { "Retry-After": "3600" });
    if (yol === "/aile/basvur") return basvur(req, env, o);
    if (yol === "/aile/dogrula") return dogrula(req, env, o);
    if (yol === "/aile/odeme") return odeme(req, env, o);
    return bildir(req, env, o);
  }
  return yanit(req, env, { hata: "yöntem_desteklenmiyor" }, 405);
}

// Panel/yonetici anahtari isteyen yollar: yanlis anahtar (403) 10 dk'da 10 kez olursa IP 10 dk kilitlenir (isolate bellek; en iyi caba)
const GIZLI_YOLLAR = new Set(["/aile/durum", "/aile/odemeler", "/gorevli/karar", "/gorevli/liste", "/gorevli/capraz"]);

export default {
  async fetch(req, env, ctx) {
    try {
      const url = new URL(req.url);
      const gizli = GIZLI_YOLLAR.has(url.pathname.replace(/\/+$/, ""));
      const ip = req.headers.get("CF-Connecting-IP") || "yok";
      if (gizli && kilitliMi(ip)) return new Response(JSON.stringify({ hata: "cok_fazla_deneme" }), { status: 429, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "Retry-After": "600", ...GUVENLIK_BASLIK } });
      const cache = typeof caches !== "undefined" ? caches.default : null;
      const onbellekli = cache && req.method === "GET" && /^\/(aile|gorevli)\/[a-z0-9]+\.json$/.test(url.pathname) && !req.headers.get("Origin");
      if (onbellekli) {
        const hit = await cache.match(req);
        if (hit) return hit;
      }
      const r = await isle(req, env, ctx);
      if (gizli && r.status === 403) basarisizKaydet(ip);
      if (onbellekli && r.status === 200) ctx.waitUntil(cache.put(req, r.clone()));
      return r;
    } catch (e) {
      console.error("aile beklenmeyen hata:", String(e && e.stack || e).slice(0, 500));   // yalniz Cloudflare gunlugunde; yanitta iz yok
      return new Response(JSON.stringify({ hata: "sunucu_hatasi" }), { status: 500, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...GUVENLIK_BASLIK } });
    }
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(temizle(env));
  },
};
