// Telefon doğrulama kodu gönderimi — aile/şehit ilanı ve din görevlisi kaydı için TEK kanal (15.10.2026).
// Sıra: (a) WhatsApp Cloud API doğrulama şablonu → (b) Netgsm SMS → (c) GELISTIRME=1 ve ikisi de yoksa kod yanıtta döner.
// Telefon hiçbir halka açık çıktıda görünmez; burada yalnız gönderim vardır.
export const SMS_METNI = (kod) => `Kimin Cenazesi doğrulama kodunuz: ${kod}`;

// Telefon: +90 5xx xxx xx xx / 05xx… / 5xx… -> "5xxxxxxxxx" (10 hane) ya da null
export function telefonNormalize(t) {
  if (typeof t !== "string") return null;
  let d = t.replace(/[\s().-]/g, "");
  if (d.startsWith("+90")) d = d.slice(3); else if (d.startsWith("0090")) d = d.slice(4); else if (d.startsWith("90") && d.length === 12) d = d.slice(2); else if (d.startsWith("0")) d = d.slice(1);
  return /^5\d{9}$/.test(d) ? d : null;
}

// (a) WhatsApp Cloud API doğrulama şablonu (authentication kategorisi): POST graph.facebook.com/<sürüm>/<WA_PHONE_ID>/messages, Bearer WA_TOKEN.
// Şablon adı WA_SABLON (varsayılan kc_dogrulama), dil tr; kod hem gövde hem "kodu kopyala" düğmesi parametresidir.
export const waVar = (env) => !!(env.WA_TOKEN && env.WA_PHONE_ID);
export async function waSablonGonder(env, fetchFn, tel10, kod) {
  const r = await fetchFn(`https://graph.facebook.com/${env.WA_API_VERSION || "v21.0"}/${env.WA_PHONE_ID}/messages`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${env.WA_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      messaging_product: "whatsapp", recipient_type: "individual", to: "90" + tel10, type: "template",
      template: { name: env.WA_SABLON || "kc_dogrulama", language: { code: "tr" }, components: [
        { type: "body", parameters: [{ type: "text", text: kod }] },
        { type: "button", sub_type: "url", index: "0", parameters: [{ type: "text", text: kod }] },
      ] },
    }),
  });
  return r.ok;
}

// (b) Netgsm REST v2: POST /sms/rest/v2/send, HTTP Basic (kullanıcı kodu:şifre), gövde {msgheader, encoding:"TR", messages:[{msg,no}]}; başarı: {code:"00", jobid}
export const NETGSM_URL = "https://api.netgsm.com.tr/sms/rest/v2/send";
export const netgsmVar = (env) => !!(env.NETGSM_KULLANICI && env.NETGSM_SIFRE && env.NETGSM_BASLIK);
export async function smsGonder(env, fetchFn, tel10, metin) {
  const r = await fetchFn(NETGSM_URL, {
    method: "POST",
    headers: { "Authorization": "Basic " + btoa(`${env.NETGSM_KULLANICI}:${env.NETGSM_SIFRE}`), "Content-Type": "application/json" },
    body: JSON.stringify({ msgheader: env.NETGSM_BASLIK, encoding: "TR", messages: [{ msg: metin, no: tel10 }] }),
  });
  if (!r.ok) return false;
  try { const j = await r.json(); return String(j.code) === "00"; } catch { return false; }
}

export const kanalVar = (env) => waVar(env) || netgsmVar(env);
/** Üretimde en az bir kanal şart; GELISTIRME=1 iken kanal yoksa kod yanıtta döner. */
export const kanalGerekli = (env) => !kanalVar(env) && env.GELISTIRME !== "1";

/** Döner: {kanal:"whatsapp"|"sms"} | {kanal:null, kod} (yalnız GELISTIRME=1 ve kanal yokken) | {hata:true} */
export async function kodGonder(env, fetchFn, tel10, kod) {
  if (waVar(env)) {
    try { if (await waSablonGonder(env, fetchFn, tel10, kod)) return { kanal: "whatsapp" }; } catch { /* sıradaki kanal */ }
  }
  if (netgsmVar(env)) {
    try { if (await smsGonder(env, fetchFn, tel10, SMS_METNI(kod))) return { kanal: "sms" }; } catch { /* hata */ }
  }
  if (!kanalVar(env) && env.GELISTIRME === "1") return { kanal: null, kod }; // YALNIZ GELISTIRME=1; üretimde asla
  return { hata: true };
}

// ---- Diyanet e-posta kodu (URUN-TASLAGI §45, 16.10.2026) ----
// Adres DAİMA <kullanici>@diyanet.gov.tr. Gönderim: Resend API (Bearer env.RESEND_ANAHTARI). GELISTIRME=1 ve anahtar yoksa kod yanıtta döner.
export const ESTA = "diyanet.gov.tr";
export const RESEND_URL = "https://api.resend.com/emails";
export const EPOSTA_KONU = "Kimin Cenazesi doğrulama kodu";
export const EPOSTA_GONDEREN = "Kimin Cenazesi <dogrulama@kimincenazesi.com>";
export const EPOSTA_METNI = (kod) => `Kimin Cenazesi doğrulama kodunuz: ${kod} (10 dakika geçerlidir).`;
export const epostaVar = (env) => !!env.RESEND_ANAHTARI;
export const epostaGerekli = (env) => !epostaVar(env) && env.GELISTIRME !== "1";
/** Döner: {kanal:"eposta"} | {kanal:null, kod} (yalnız GELISTIRME=1 ve anahtar yokken) | {hata:true} */
export async function epostaKodGonder(env, fetchFn, adres, kod) {
  if (!adres.endsWith("@" + ESTA)) return { hata: true }; // başka alan adına ASLA
  if (epostaVar(env)) {
    try {
      const r = await fetchFn(RESEND_URL, {
        method: "POST",
        headers: { "Authorization": `Bearer ${env.RESEND_ANAHTARI}`, "Content-Type": "application/json" },
        body: JSON.stringify({ from: EPOSTA_GONDEREN, to: [adres], subject: EPOSTA_KONU, text: EPOSTA_METNI(kod) }),
      });
      return r.ok ? { kanal: "eposta" } : { hata: true };
    } catch { return { hata: true }; }
  }
  if (env.GELISTIRME === "1") return { kanal: null, kod };
  return { hata: true };
}
