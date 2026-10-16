// Tam Sayfa ödemesi (URUN-TASLAGI §38): Google Play Faturalandırma makbuzunun sunucu doğrulaması.
// PLAY_SA_JSON (servis hesabı anahtarı, secret) VARSA: Google Play Developer API purchases.products.get ile doğrulanır, acknowledge edilir.
// YOKSA (ilk aşama): istemci makbuzu `od:` kaydına yazılır, ilan yayına girer, `odeme_dogrulandi:false` kalır;
// sahibi haftalık gününde Play Console sipariş listesiyle karşılaştırır (GET /aile/odemeler, x-gizli: PANEL_ANAHTARI).
export const PAKET_ADI = "com.kimincenazesi.app";
export const URUN_KIMLIGI = "tam_sayfa_ilan";
const KAPSAM = "https://www.googleapis.com/auth/androidpublisher";
const TOKEN_URL = "https://oauth2.googleapis.com/token";
const API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications";

const b64u = (buf) => {
  const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const x of b) s += String.fromCharCode(x);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const b64uMetin = (o) => b64u(new TextEncoder().encode(JSON.stringify(o)));

function pemToDer(pem) {
  const b = pem.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const ham = atob(b);
  const d = new Uint8Array(ham.length);
  for (let i = 0; i < ham.length; i++) d[i] = ham.charCodeAt(i);
  return d.buffer;
}

// Servis hesabı JWT'si (RS256) → OAuth erişim belirteci
export async function erisimBelirteci(saJson, fetchFn, now = new Date()) {
  const sa = typeof saJson === "string" ? JSON.parse(saJson) : saJson;
  const iat = Math.floor(now.getTime() / 1000);
  const basi = `${b64uMetin({ alg: "RS256", typ: "JWT" })}.${b64uMetin({ iss: sa.client_email, scope: KAPSAM, aud: TOKEN_URL, iat, exp: iat + 3000 })}`;
  const anahtar = await crypto.subtle.importKey("pkcs8", pemToDer(sa.private_key), { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
  const imza = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", anahtar, new TextEncoder().encode(basi));
  const r = await fetchFn(TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=${encodeURIComponent("urn:ietf:params:oauth:grant-type:jwt-bearer")}&assertion=${basi}.${b64u(imza)}`,
  });
  if (!r.ok) throw new Error(`oauth ${r.status}`);
  return (await r.json()).access_token;
}

// Döner: {tamam:true, siparis_no} | {tamam:false, neden}
export async function playDogrula(env, fetchFn, token, siparisNo, now) {
  let erisim;
  try { erisim = await erisimBelirteci(env.PLAY_SA_JSON, fetchFn, now); } catch { return { tamam: false, neden: "play_oauth", gecici: true }; }
  const temel = `${API}/${PAKET_ADI}/purchases/products/${URUN_KIMLIGI}/tokens/${encodeURIComponent(token)}`;
  const baslik = { Authorization: `Bearer ${erisim}` };
  let r;
  try { r = await fetchFn(temel, { headers: baslik }); } catch { return { tamam: false, neden: "play_ag", gecici: true }; }
  if (r.status >= 500) return { tamam: false, neden: "play_ag", gecici: true };
  if (!r.ok) return { tamam: false, neden: "makbuz_gecersiz" };
  const p = await r.json();
  if (p.purchaseState !== 0) return { tamam: false, neden: "satin_alma_tamam_degil" }; // 0 = satın alındı; 1 iptal, 2 beklemede
  if (p.consumptionState === 1) return { tamam: false, neden: "makbuz_tuketilmis" };
  if (p.orderId && siparisNo && p.orderId !== siparisNo) return { tamam: false, neden: "siparis_no_uyusmuyor" };
  if (p.acknowledgementState !== 1) {
    try { await fetchFn(`${temel}:acknowledge`, { method: "POST", headers: { ...baslik, "Content-Type": "application/json" }, body: "{}" }); } catch { /* tüketme zaten onaylar */ }
  }
  return { tamam: true, siparis_no: p.orderId || siparisNo || null, test: p.purchaseType === 0 };
}
