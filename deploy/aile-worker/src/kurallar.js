// Aile ilanı kuralları K1-K9 (AILE-ILAN-SOZLESME.md). Saf fonksiyonlar: ağ/KV yok, test edilebilir.
import { ILCELER, MEZARLIK } from "./veri.js";
import { telefonNormalize } from "./dogrulama.js";

const TR = { "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u" };
const MEZ_EK = new Set(["mezarligi", "mezarlik", "mezarliginda", "mezarlikta", "mezarlari", "kabristanligi", "kabristani", "kabristanliginda", "mezari", "mez", "mzl", "kabristan"]);
const MEZ_KES = new Set(["pafta", "parsel", "ada", "kapisi", "kapi", "sira", "sistem", "sistemi", "bolum", "kisim", "blok", "no", "sokak", "cadde", "yol"]);

// okuyucu/ortak.py katla() ile aynı: küçük harf (İ->i, I->ı), Türkçe harf sadeleşmesi, harf/rakam dışı tek boşluk
export function katla(s) {
  let t = String(s ?? "").replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase();
  t = t.replace(/[çğıöşü]/g, (c) => TR[c]);
  return t.replace(/[^a-z0-9]+/g, " ").trim();
}
export function mezarlikNorm(ad) {
  const s = String(ad ?? "").split("/")[0];
  const toks = [];
  for (const t of katla(s).split(" ").filter(Boolean)) {
    if (MEZ_KES.has(t) || /\d/.test(t)) break;
    toks.push(t);
  }
  return toks.filter((t) => !MEZ_EK.has(t)).join(" ");
}
export const ilSlug = (il) => katla(il).replace(/ /g, "");

// Türkiye günü (UTC+3) YYYY-AA-GG
export function bugunTR(now = new Date()) {
  return new Date(now.getTime() + 3 * 3600 * 1000).toISOString().slice(0, 10);
}
export function gunEkle(iso, n) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
export function gunFarki(a, b) { // a - b (gün)
  return Math.round((Date.parse(a + "T00:00:00Z") - Date.parse(b + "T00:00:00Z")) / 86400000);
}
export function gecerliTarih(s) {
  if (typeof s !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const d = new Date(s + "T00:00:00Z");
  return !isNaN(d) && d.toISOString().slice(0, 10) === s;
}

const KELIME = /^[\p{L}][\p{L}'’.\-]*$/u;
export function adGecerli(ad) {
  if (typeof ad !== "string") return false;
  const t = ad.trim().replace(/\s+/g, " ");
  if (t.length > 60 || /[\d@]|https?:|www\.|\.com|\.tr\b/i.test(t)) return false;
  const k = t.split(" ");
  return k.length >= 2 && k.length <= 5 && k.every((w) => KELIME.test(w));
}
export function adNormalize(ad) { return katla(ad); }

const YASAK_NEDEN = /\b(kanser|kaza|intihar|cinayet|covid|korona|kalp krizi|kalp|hastalik|hastane|tumor|ameliyat|yangin|boguldu|trafik|olum nedeni|olum sebebi)\b/;
export function metinTemiz(v) { // K8: serbest metin yok; sabit alanlar <=60, telefon/TC/URL/e-posta/ölüm nedeni yok
  const s = String(v);
  if (s.length > 60) return "uzun alan";
  if (/https?:|www\.|@|\.com|\.tr\b/i.test(s)) return "bağlantı/e-posta";
  if (/\d{11}/.test(s.replace(/[\s.\-]/g, ""))) return "kimlik/telefon numarası";
  if (/(?:\d[\s.\-()]*){10,}/.test(s)) return "telefon numarası";
  if (YASAK_NEDEN.test(katla(s))) return "ölüm nedeni";
  return null;
}

const SABIT_METIN = ["mahalle", "namaz_yeri_vakti", "defin_yeri"];

// Girdi biçimi (400): eksik/yanlış tip. Döner: temizlenmiş nesne ya da {hata}
export function girdiTemizle(g) {
  if (!g || typeof g !== "object") return { hata: "gövde JSON nesnesi olmalı" };
  const s = (x) => (typeof x === "string" ? x.trim().replace(/\s+/g, " ") : x);
  const o = {
    il: s(g.il), ilce: s(g.ilce), ad_soyad: s(g.ad_soyad), cinsiyet: g.cinsiyet,
    vefat_tarihi: s(g.vefat_tarihi), namaz_tarihi: s(g.namaz_tarihi), beyan: g.beyan === true,
  };
  for (const a of SABIT_METIN) { if (g[a] != null && g[a] !== "") o[a] = s(g[a]); }
  if (g.yas != null && g.yas !== "") o.yas = Number(g.yas);
  // 15.10.2026: e-Devlet ölüm belgesi kodu kalktı; gövdede gelirse YOK SAYILIR. Tek doğrulama telefon kodu.
  if (g.tam === true) o.tam = true; // Tam Sayfa (200 ₺): ilan ödeme gelene dek yayında değil
  const b = g.basvuran;
  if (!b || typeof b !== "object") return { hata: "basvuran gerekli" };
  o.basvuran = { ad_soyad: s(b.ad_soyad), telefon: telefonNormalize(b.telefon), yakinlik: s(b.yakinlik) }; // 10 hane (5xxxxxxxxx); e-posta alanı kalktı
  for (const a of ["il", "ilce", "ad_soyad", "vefat_tarihi", "namaz_tarihi"]) {
    if (typeof o[a] !== "string" || !o[a]) return { hata: `${a} gerekli` };
  }
  if (typeof o.basvuran.ad_soyad !== "string" || typeof o.basvuran.yakinlik !== "string") return { hata: "basvuran alanları gerekli" };
  if (!o.basvuran.telefon) return { hata: "telefon biçimi geçersiz" };
  return o;
}

// Kuralları değerlendirir. ctx: {bugun, ayniKisiVar(il_slug, ad_norm, vefat)->bool, telefonIlanSayisi:number}
// Döner: null (geçti) ya da neden dizgisi (red)
export function degerlendir(o, ctx) {
  // K7 beyan
  if (o.beyan !== true) return "K7 beyan onaylanmadı";
  // K8 yasak/serbest alanlar
  for (const a of [...SABIT_METIN, "ilce"]) {
    if (o[a] != null) { const n = metinTemiz(o[a]); if (n) return `K8 ${a}: ${n}`; }
  }
  const yk = metinTemiz(o.basvuran.yakinlik);
  if (yk || o.basvuran.yakinlik.length < 2) return "K8 yakınlık alanı geçersiz";
  // K1 il / ilçe
  const slug = ilSlug(o.il);
  const il = ILCELER[slug];
  if (!il) return "K1 il listede yok";
  o.il = il.il;
  if (o.ilce !== "Merkez" && !il.ilceler.includes(o.ilce)) return "K1 ilçe bu ilin listesinde yok";
  // K2 adlar
  if (!adGecerli(o.ad_soyad)) return "K2 ad biçimi geçersiz";
  if (!adGecerli(o.basvuran.ad_soyad)) return "K2 başvuran adı biçimi geçersiz";
  if (o.cinsiyet !== "e" && o.cinsiyet !== "k") return "K2 cinsiyet geçersiz";
  if (o.yas != null && (!Number.isInteger(o.yas) || o.yas < 0 || o.yas > 120)) return "K2 yaş geçersiz";
  // K3 tarihler
  if (!gecerliTarih(o.vefat_tarihi) || !gecerliTarih(o.namaz_tarihi)) return "K3 tarih biçimi geçersiz";
  const bugun = ctx.bugun;
  if (o.vefat_tarihi > o.namaz_tarihi) return "K3 vefat tarihi namaz tarihinden sonra";
  if (gunFarki(o.namaz_tarihi, o.vefat_tarihi) > 3) return "K3 namaz vefattan 3 günden fazla sonra";
  if (o.namaz_tarihi < gunEkle(bugun, -1)) return "K3 namaz tarihi çok eski";
  if (o.namaz_tarihi > gunEkle(bugun, 3)) return "K3 namaz tarihi 3 günden uzak";
  // K4 mezarlık başka ilçede
  if (o.defin_yeri) {
    const m = (MEZARLIK[slug] || {})[mezarlikNorm(o.defin_yeri)];
    if (m && m !== o.ilce) return "K4 mezarlık başka ilçede";
  }
  // K5 ikinci ilan
  if (ctx.ayniKisiVar(slug, adNormalize(o.ad_soyad), o.vefat_tarihi)) return "K5 bu kişi için ilan zaten var";
  // K6 telefon başına 7 günde en çok 2 ilan
  if (ctx.telefonIlanSayisi >= 2) return "K6 telefon başına 7 günde en çok 2 ilan";
  return null;
}
