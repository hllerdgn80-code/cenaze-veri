// Veri kapısı: veri.kimincenazesi.com önünde anahtar + User-Agent + hız sınırı + yol beyaz listesi.
// Hata yanıtları HEP boş gövde, başlıksız (açıklama/iz yok).
const UA_ONEK = "KiminCenazesi/";
const IL_YOL = /^\/veri\/[a-z0-9-]{2,40}\/son7gun\.json$/;
const KAYBETTIK_YOL = /^\/veri\/kaybettiklerimiz\/[A-Za-z0-9_\-\/]{1,120}\.json$/;

const bos = (durum) => new Response(null, { status: durum });

// Sabit zamanlı karşılaştırma
export function esit(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const x = new TextEncoder().encode(a), y = new TextEncoder().encode(b);
  let f = x.length ^ y.length;
  const n = Math.max(x.length, y.length);
  for (let i = 0; i < n; i++) f |= (x[i] || 0) ^ (y[i] || 0);
  return f === 0;
}

// Yol beyaz listesi. Dönüş: temizlenmiş yol ya da null.
export function yolIzinli(ham) {
  let yol;
  try { yol = decodeURIComponent(ham); } catch { return null; }
  if (yol.includes("..") || yol.includes("//") || yol.includes("\\") || yol.includes("\0")) return null;
  if (yol.split("/").some((p) => p.startsWith("_"))) return null; // "_" ile başlayan her yol kapalı
  const d = yol.split("/").pop();
  if (["ozet.json", "saglik.json", "kapi.json", "yerlestirme-raporu.json"].includes(d)) return null;
  if (IL_YOL.test(yol) || KAYBETTIK_YOL.test(yol)) return yol;
  return null;
}

// IP başına dakika sayacı: Durable Object (tek sayaç, tutarlı). Bağlama yoksa (test) env.LIMITER.limit({key}).
export class Sayac {
  constructor(state) { this.state = state; this.dk = 0; this.n = 0; }
  async fetch() {
    const dk = Math.floor(Date.now() / 60000);
    if (dk !== this.dk) { this.dk = dk; this.n = 0; }
    this.n += 1;
    return new Response(String(this.n));
  }
}

async function hizSiniri(env, ip) {
  const limit = parseInt(env.DAKIKA_LIMIT || "60", 10);
  if (env.SAYAC) {
    const y = await env.SAYAC.get(env.SAYAC.idFromName(ip)).fetch("https://sayac/");
    return parseInt(await y.text(), 10) <= limit;
  }
  if (env.LIMITER) return (await env.LIMITER.limit({ key: ip })).success;
  const dk = Math.floor(Date.now() / 60000);
  const k = `r:${ip}:${dk}`;
  const n = parseInt((await env.KAPI.get(k)) || "0", 10) + 1;
  if (n > limit) return false;
  await env.KAPI.put(k, String(n), { expirationTtl: 120 });
  return true;
}

export async function kapi(request, env, kaynakGetir = fetch) {
  try {
    if (request.method !== "GET" && request.method !== "HEAD") return bos(403);
    const h = request.headers;
    if (!env.KC_ANAHTAR || !esit(h.get("X-KC-Anahtar") || "", env.KC_ANAHTAR)) return bos(403);
    if (!(h.get("User-Agent") || "").startsWith(UA_ONEK)) return bos(403);
    const ip = h.get("CF-Connecting-IP") || "yok";
    if (!(await hizSiniri(env, ip))) return bos(429);
    const url = new URL(request.url);
    const yol = yolIzinli(url.pathname);
    if (!yol) return bos(404);
    const y = await kaynakGetir(env.KOKEN.replace(/\/$/, "") + yol, {
      method: "GET",
      headers: { Accept: "application/json" },
      cf: { cacheTtl: 60, cacheEverything: true },
    });
    // Pages bilinmeyen yolda 200 + HTML döndürebilir: yalnız JSON kabul edilir.
    if (y.status !== 200 || !(y.headers.get("Content-Type") || "").includes("json")) return bos(404);
    return new Response(request.method === "HEAD" ? null : y.body, {
      status: 200,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "private, max-age=120",
        "X-Robots-Tag": "noindex",
      },
    });
  } catch (e) {
    console.error(String(e)); // yalnız Cloudflare günlüğünde; yanıtta iz yok
    return bos(404);
  }
}

export default { fetch: (req, env) => kapi(req, env) };
