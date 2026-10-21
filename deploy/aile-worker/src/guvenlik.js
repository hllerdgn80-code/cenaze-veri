// Guvenlik yardimcilari (21.10.2026, guvenlik duvari maddeleri 1, 3, 4). Bagimlilik yok; yalniz standart Workers API.
// - Guvenlik basliklari: her yanita (JSON API; sayfa DEGIL) eklenir.
// - sinirliMetin: govdeyi Content-Length on kontrolu + akis sinirli okur (azami baytı asan istek bellege alinmaz).
// - Basarisiz gizli-anahtar denemesi sayaci (isolate bellek; en iyi caba): ayni IP 10 dakikada 10 yanlis denemeden sonra 10 dk kilitlenir.
export const GUVENLIK_BASLIK = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "no-referrer",
  "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  "Strict-Transport-Security": "max-age=31536000",
  "Cross-Origin-Resource-Policy": "cross-origin",   // API baska alandan (kimincenazesi.com) okunur; CORS ayri
};

export async function sinirliMetin(req, azami) {
  const cl = parseInt(req.headers.get("content-length") || "0", 10);
  if (cl > azami) return { asildi: true };
  if (!req.body) return { metin: "" };
  const okuyucu = req.body.getReader();
  const parcalar = [];
  let toplam = 0;
  for (;;) {
    const { done, value } = await okuyucu.read();
    if (done) break;
    toplam += value.byteLength;
    if (toplam > azami) { try { await okuyucu.cancel(); } catch { /* yoksay */ } return { asildi: true }; }
    parcalar.push(value);
  }
  const hepsi = new Uint8Array(toplam);
  let k = 0;
  for (const p of parcalar) { hepsi.set(p, k); k += p.byteLength; }
  return { metin: new TextDecoder().decode(hepsi) };
}

const DENEME = new Map();      // ip -> { n, ilk, kilit }
const PENCERE_MS = 10 * 60 * 1000;
const ESIK = 10;

export function kilitliMi(ip, simdi = Date.now()) {
  const k = DENEME.get(ip);
  return !!(k && k.kilit && k.kilit > simdi);
}
export function basarisizKaydet(ip, simdi = Date.now()) {
  if (DENEME.size > 5000) DENEME.clear();
  let k = DENEME.get(ip);
  if (!k || simdi - k.ilk > PENCERE_MS) k = { n: 0, ilk: simdi, kilit: 0 };
  k.n += 1;
  if (k.n >= ESIK) k.kilit = simdi + PENCERE_MS;
  DENEME.set(ip, k);
  return k.n;
}
export function basarisizSifirla() { DENEME.clear(); }
