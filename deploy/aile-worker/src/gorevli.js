// Din görevlisi ilan kapısı — URUN-TASLAGI.md §45 (16.10.2026): doğrulama = Diyanet e-posta kodu (kullanıcı adı@diyanet.gov.tr), kod doğruysa panel HEMEN açılır.
// Eski kart fotoğrafı + telefon kodu uçları (/kayit /kod /giris /dogrula) KALDIRILDI: 410 döner.
// index.js'ten H (yardımcılar) alır; döngüsel içe aktarma yok.
// KV (AILE) anahtarları, hepsi "gorevli:" önekli:
//   k:<kayit_id>            hesap kaydı: kayit_id = sha256("eposta:"+kullanici)[0:16]; {kullanici, eposta, durum, dogrulama:"diyanet_eposta", ad_soyad/il/ilce/gorev_yeri/unvan (ilk ilan öncesi /gorevli/profil ile)}. TELEFON/FOTOĞRAF YOK.
//   ek:<kullanici>          bekleyen e-posta kodu {ozet, deneme, zaman} (TTL 10 dk)
//   ph:<kayit_id>:<gün>     günlük parola hatırlatma sayacı (≤3); hesap kaydında parola_sifreli {ct,iv} (AES-GCM, PAROLA_ANAHTARI)
//   eks:<kullanici>:<gün>   günlük kod sayacı (günde ≤5)
//   liste:<il>:<ilce>       müftülük personel listesi [{ad_soyad, cami}] (CI'dan POST /gorevli/liste ile)
//   foto:<kayit_id>         (eski akış kalıntısı; yeni kayıt üretmez, karar uçları siler)
//   oturum:<sha256(token)>  -> kayit_id (TTL 180 gün); RED sonrası "RED" işareti (30 gün): uygulama "hesap silindi" der
//   ot:<kayit_id>           hesabın oturum özetleri (RED'de silinir)
//   i:<ilan_id>             ilan;  x:<slug>:<ilan_id> dizin (metadata n,v,t);  h:<kayit_id>:<ilan_id> hesabın ilanları
//   g:<ilan_id>             gözetimdeki hesabın ilanı (çapraz kontrol bekliyor; TTL 8 gün)
//   n:<ilan_id>             bildirim yapan IP özetleri;  gs:<kayit_id>:<gün> günlük ilan sayacı
import { ILCELER } from "./veri.js";
import { yerEslesir } from "./yer.js";
import { smsGonder, netgsmVar, epostaVar, epostaGerekli, epostaKodGonder, parolaAnahtariVar, parolaSifrele, parolaCoz, parolaEpostaGonder, ESTA, SMS_METNI, NETGSM_URL, telefonNormalize } from "./dogrulama.js";
export { telefonNormalize, smsGonder, netgsmVar, SMS_METNI, NETGSM_URL };
import { degerlendir, adGecerli, adNormalize, katla, metinTemiz, bugunTR, gunEkle, ilSlug } from "./kurallar.js";

export const UNVANLAR = ["İmam-Hatip", "Müezzin-Kayyım", "Kur'an Kursu Öğreticisi", "Vaiz", "Müftü", "Müftü Yardımcısı", "Din Hizmetleri Uzmanı"];
const UNVAN_KATLA = UNVANLAR.map((u) => katla(u));
const LISTE_GOVDE_LIMIT = 8_000_000;
const GOVDE_LIMIT = 4096;
const KOD_OMRU_SN = 600; // 10 dk
const AZAMI_KOD_DENEME = 5;
const GUNLUK_KOD = 5;
const KOD_ARALIK_MS = 300000; // yeniden gönder bekleme: 5 dk (sahibi 16.10 08:05)
const KULLANICI_RE = /^[a-z0-9._-]{3,40}$/;
const OTURUM_TTL = 180 * 86400;
const GUNLUK_HATIRLAT = 3; // parola hatırlatma e-postası: hesap başına günde ≤3
const KONTROL_GUN = 14; // "kontrolde"/"kuyruk" hesabı en çok 14 gün yaşar, sonra KV TTL ile kendiliğinden silinir
const ILAN_TTL = 120 * 86400;
const FOTO_TTL = 7 * 86400;
const GOZETIM_GUN = 7;
const GUNLUK_ILAN = 10;
const P = "gorevli:";
const GIRIS_DURUMLARI = ["onayli", "kontrolde", "kuyruk"]; // panel açılabilen durumlar (yeni akışta hesap doğrudan "onayli"; diğerleri eski kayıtlar için)
const CAMI_GENEL = new Set(["cami", "camii", "camisi", "mescidi", "mescit", "camii serif", "serif", "koyu", "mahallesi"]);
export const ONAY_SMS = "Kimin Cenazesi: din görevlisi başvurunuz onaylandı, paneliniz açıldı.";
export const BEYAN_METNI = "Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum.";
// ---- saf yardımcılar (test edilir) ----
/** "Ali.Kaya@Diyanet.gov.tr" -> "ali.kaya"; başka alan adı ya da geçersiz biçim -> null */
export function kullaniciNormalize(x) {
  if (typeof x !== "string") return null;
  let u = x.trim().toLowerCase();
  const at = u.indexOf("@");
  if (at >= 0) { if (u.slice(at + 1) !== "diyanet.gov.tr") return null; u = u.slice(0, at); }
  return KULLANICI_RE.test(u) ? u : null;
}
const DUZELTME_RE = /^[0-9a-f]{8,32}$/;
const GENEL = ["id", "duzeltme_id", "il", "ilce", "ad_soyad", "cinsiyet", "yas", "vefat_tarihi", "namaz_tarihi", "namaz_yeri_vakti", "defin_yeri", "liste_tarihi"];
// Halka açık çıktı: görevlinin adı/telefonu/IP'si/hesap durumu ASLA yok
export function genelGorevli(ilan) {
  const r = {};
  for (const a of GENEL) r[a] = ilan[a] ?? null;
  r.mahalle = ilan.mahalle || ilan.koy || null;
  r.gorevli = true;
  r.gorev_yeri = ilan.gorev_yeri ?? null;
  if (ilan.sehit === true) { r.sehit = true; r.rutbe = ilan.rutbe ?? null; r.toren = ilan.toren ?? null; } // §27; duyuru bağlantısı çıkmaz
  r.dogrulandi = ilan.dogrulandi === true;
  return r;
}
const ilceSlug = (s) => katla(s).replace(/ /g, "");

export async function gorevliIsle(req, env, o, H, yol) {
  const { yanit, kvJson, sha256, rastgeleId, kod6 } = H;
  const kv = env.AILE;
  const gun = bugunTR(o.now);

  async function govde(limit = GOVDE_LIMIT) {
    const m = await req.text();
    if (m.length > limit) return { hata: "gövde çok büyük", durum: 413 };
    try { return { json: JSON.parse(m) }; } catch { return { hata: "geçersiz JSON", durum: 400 }; }
  }
  const panelIzin = () => {
    const y = req.headers.get("x-gizli") || (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    if (env.PANEL_ANAHTARI) return H.sabitKarsilastir(y, env.PANEL_ANAHTARI);
    return env.GELISTIRME === "1";
  };
  async function oturumKid() {
    const tok = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    if (!/^[0-9a-f]{64}$/.test(tok)) return null;
    return await kv.get(`${P}oturum:${await sha256(tok)}`);
  }
  async function hesap() { // oturumdan hesap
    const kid = await oturumKid();
    if (!kid || kid === "RED") return null;
    return (await kvJson(kv, `${P}k:${kid}`)) || null;
  }
  // "kontrolde"/"kuyruk": oluşturmadan en çok 14 gün sonra kendiliğinden silinir (mutlak son kullanma); onaylı hesap kalıcı
  const kayitYaz = (k, ttl) => {
    if (k.durum === "kontrolde" || k.durum === "kuyruk") {
      const son = Math.floor((Date.parse(k.olusturma) + KONTROL_GUN * 86400000) / 1000);
      return kv.put(`${P}k:${k.id}`, JSON.stringify(k), { expiration: Math.max(son, Math.floor(o.now.getTime() / 1000) + 120) });
    }
    return kv.put(`${P}k:${k.id}`, JSON.stringify(k), ttl ? { expirationTtl: ttl } : {});
  };
  const ilanYaz = (i) => kv.put(`${P}i:${i.id}`, JSON.stringify(i), { expirationTtl: ILAN_TTL });

  async function hesapIlanlari(k) {
    const out = [];
    let cursor;
    do {
      const l = await kv.list({ prefix: `${P}h:${k.id}:`, cursor });
      for (const key of l.keys) {
        const i = await kvJson(kv, `${P}i:${key.name.split(":")[3]}`);
        if (i) out.push(i);
      }
      cursor = l.list_complete ? undefined : l.cursor;
    } while (cursor);
    return out.sort((a, b) => (a.olusturma < b.olusturma ? 1 : -1));
  }
  async function ilanlariDegistir(k, eskiler, yeni) {
    for (const i of await hesapIlanlari(k)) if (eskiler.includes(i.durum)) { i.durum = yeni; await ilanYaz(i); await kv.delete(`${P}g:${i.id}`); }
  }
  async function dondur(k, not) {
    if (k.durum !== "donduruldu") k.onceki_durum = k.durum;
    k.durum = "donduruldu"; k.not = not;
    await ilanlariDegistir(k, ["yayinda", "bekliyor"], "gizli");
    await kayitYaz(k, 0);
  }
  // Sahibi onayında kayıtlı telefona yedek SMS (asıl yol: uygulama arka planda /gorevli/durum'a bakar). Netgsm yoksa sessiz geçer.
  async function onaySms(k) {
    if (!netgsmVar(env)) return false;
    try { return k.telefon ? await smsGonder(env, o.fetch, k.telefon, ONAY_SMS) : false; } catch { return false; }
  }
  const gozetimde = (k) => k.gozetim_bitis && Date.parse(k.gozetim_bitis) > o.now.getTime();

  const dogrulu = (k) => k && k.eposta_dogrulandi === true;
  const hesapId = async (ku) => (await sha256(`eposta:${ku}`)).slice(0, 16);

  // ---- POST /gorevli/eposta-kod {kullanici} ----
  // Kod YALNIZ <kullanici>@diyanet.gov.tr adresine gider. 10 dk geçerli, 5 yanlış deneme, günde ≤5 kod, aynı kullanıcıya yeni kod 5 dk dolmadan verilmez.
  async function epostaKod() {
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const ku = kullaniciNormalize(g.json?.kullanici);
    if (!ku) return yanit(req, env, { hata: "kullanici_gecersiz" }, 400);
    if (epostaGerekli(env)) return yanit(req, env, { hata: "dogrulama_servisi_yok" }, 503);
    const mevcut = await kvJson(kv, `${P}k:${await hesapId(ku)}`);
    if (mevcut && mevcut.durum === "donduruldu") return yanit(req, env, { durum: "donduruldu" }, 403);
    const onceki = await kvJson(kv, `${P}ek:${ku}`);
    if (onceki && o.now.getTime() - onceki.zaman < KOD_ARALIK_MS) return yanit(req, env, { hata: "cok_sik_tekrar", bekle_sn: Math.ceil((KOD_ARALIK_MS - (o.now.getTime() - onceki.zaman)) / 1000) }, 429, { "Retry-After": String(Math.ceil((KOD_ARALIK_MS - (o.now.getTime() - onceki.zaman)) / 1000)) });
    const sk = `${P}eks:${ku}:${gun}`;
    const n = parseInt((await kv.get(sk)) || "0", 10);
    if (n >= GUNLUK_KOD) return yanit(req, env, { hata: "gunluk_kod_siniri" }, 429);
    const kod = kod6();
    const kg = await epostaKodGonder(env, o.fetch, `${ku}@${ESTA}`, kod);
    if (kg.hata) return yanit(req, env, { hata: "kod_gonderilemedi" }, 502);
    await kv.put(`${P}ek:${ku}`, JSON.stringify({ ozet: await sha256(`${ku}:${kod}`), deneme: 0, zaman: o.now.getTime() }), { expirationTtl: KOD_OMRU_SN });
    await kv.put(sk, String(n + 1), { expirationTtl: 90000 });
    const c = { durum: "kod_gonderildi", adres: `${ku}@${ESTA}` };
    if (kg.kod) c.gelistirme_kodu = kg.kod; // YALNIZ GELISTIRME=1 ve anahtar yokken; üretimde asla
    return yanit(req, env, c);
  }

  // ---- POST /gorevli/eposta-dogrula {kullanici, kod} -> hesap "onayli" + oturum; panel hemen açılır ----
  async function epostaDogrula() {
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const ku = kullaniciNormalize(g.json?.kullanici);
    const kod = g.json?.kod;
    if (!ku) return yanit(req, env, { hata: "kullanici_gecersiz" }, 400);
    if (typeof kod !== "string" || !/^\d{6}$/.test(kod)) return yanit(req, env, { hata: "6 haneli kod gerekli" }, 400);
    const ek = await kvJson(kv, `${P}ek:${ku}`);
    if (!ek) return yanit(req, env, { durum: "red", neden: "kod bulunamadı ya da süresi doldu" }, 410);
    if ((await sha256(`${ku}:${kod}`)) !== ek.ozet) {
      ek.deneme += 1;
      if (ek.deneme >= AZAMI_KOD_DENEME) { await kv.delete(`${P}ek:${ku}`); return yanit(req, env, { durum: "red", neden: "kod 5 kez yanlış girildi" }, 429); }
      const kalanSn = Math.max(60, KOD_OMRU_SN - Math.floor((o.now.getTime() - ek.zaman) / 1000));
      await kv.put(`${P}ek:${ku}`, JSON.stringify(ek), { expirationTtl: kalanSn });
      return yanit(req, env, { hata: "kod_yanlis", kalan_deneme: AZAMI_KOD_DENEME - ek.deneme }, 400);
    }
    await kv.delete(`${P}ek:${ku}`);
    const id = await hesapId(ku);
    let k = await kvJson(kv, `${P}k:${id}`);
    if (k && k.durum === "donduruldu") return yanit(req, env, { durum: "donduruldu" }, 403);
    if (!k) {
      k = { id, kullanici: ku, eposta: `${ku}@${ESTA}`, olusturma: o.now.toISOString(), durum: "onayli", dogrulama: "diyanet_eposta", dogrulama_tarih: gun,
        eposta_dogrulandi: true, gozetim_bitis: new Date(o.now.getTime() + GOZETIM_GUN * 86400000).toISOString() }; // ilk 7 gün: 2 bildirim -> dondur
    } else { k.eposta_dogrulandi = true; if (k.durum !== "onayli") k.durum = "onayli"; k.dogrulama_tarih = gun; }
    await kayitYaz(k, 0);
    const tok = [...crypto.getRandomValues(new Uint8Array(32))].map((x) => x.toString(16).padStart(2, "0")).join("");
    const oh = await sha256(tok);
    await kv.put(`${P}oturum:${oh}`, k.id, { expirationTtl: OTURUM_TTL });
    const ot = (await kvJson(kv, `${P}ot:${k.id}`)) || [];
    ot.push(oh);
    await kv.put(`${P}ot:${k.id}`, JSON.stringify(ot.slice(-10)), { expirationTtl: OTURUM_TTL });
    return yanit(req, env, { durum: "onayli", oturum: tok, eposta: k.eposta, profil_tamam: profilTamam(k), ad_soyad: k.ad_soyad ?? null, il: k.il ?? null, ilce: k.ilce ?? null, gorev_yeri: k.gorev_yeri ?? null, unvan: k.unvan ?? null });
  }
  const profilTamam = (k) => !!(k && k.ad_soyad && k.il && k.ilce && k.gorev_yeri);

  // Ortak doğrulama: ad_soyad (yalnız ilk profilde), il, ilçe, görev yeri, unvan
  function yerDogrula(b, adGerek) {
    const s = (x) => (typeof x === "string" ? x.trim().replace(/\s+/g, " ") : x);
    const ad = s(b.ad_soyad), il = s(b.il), ilce = s(b.ilce), yer = s(b.gorev_yeri);
    if (adGerek && !adGecerli(ad)) return { hata: "ad_soyad gecersiz" };
    const ilv = ILCELER[ilSlug(il || "")];
    if (!ilv) return { hata: "il gecersiz" };
    if (ilce !== "Merkez" && !ilv.ilceler.includes(ilce)) return { hata: "ilce gecersiz" };
    if (typeof yer !== "string" || yer.length < 2 || yer.length > 60 || metinTemiz(yer)) return { hata: "gorev_yeri gecersiz" };
    const unv = typeof b.unvan === "string" ? UNVANLAR.find((u) => katla(u) === katla(b.unvan)) : null;
    if (b.unvan != null && b.unvan !== "" && !unv) return { hata: "unvan gecersiz" };
    return { ad, il: ilv.il, ilce, yer, unvan: unv ?? null };
  }
  const hesapOzeti = (k) => ({ durum: k.durum, profil_tamam: profilTamam(k), ad_soyad: k.ad_soyad ?? null, il: k.il ?? null, ilce: k.ilce ?? null, gorev_yeri: k.gorev_yeri ?? null, unvan: k.unvan ?? null });

  // ---- POST /gorevli/profil (oturumlu): panelde ilk "İlan paylaş"ta BİR KEZ sorulan ad-soyad / il / ilçe / görev yeri / unvan ----
  async function profil() {
    const k = await hesap();
    if (!k || !dogrulu(k) || k.durum !== "onayli") return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    if (profilTamam(k)) return yanit(req, env, { hata: "profil_kayitli" }, 409); // değişiklik için /gorevli/gorev-yeri
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const v = yerDogrula(g.json || {}, true);
    if (v.hata) return yanit(req, env, { hata: v.hata }, 400);
    Object.assign(k, { ad_soyad: v.ad, il: v.il, ilce: v.ilce, gorev_yeri: v.yer, unvan: v.unvan, profil_tarih: gun });
    await kayitYaz(k, 0);
    return yanit(req, env, hesapOzeti(k));
  }

  // ---- POST /gorevli/gorev-yeri (oturumlu): "Görev yerim değişti" — yeni görev yeri / unvan / il / ilçe; ad-soyad değişmez.
  // Sonraki ilanlar yeni yerle paylaşılır; mevcut ilanlar (kendi kayıtlarındaki il/ilçe/görev yeriyle) DEĞİŞMEZ. ----
  async function gorevYeri() {
    const k = await hesap();
    if (!k || !dogrulu(k) || k.durum !== "onayli") return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    if (!profilTamam(k)) return yanit(req, env, { hata: "profil_gerekli" }, 409);
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const v = yerDogrula(g.json || {}, false);
    if (v.hata) return yanit(req, env, { hata: v.hata }, 400);
    k.onceki_yer = { il: k.il, ilce: k.ilce, gorev_yeri: k.gorev_yeri, unvan: k.unvan ?? null, tarih: gun };
    Object.assign(k, { il: v.il, ilce: v.ilce, gorev_yeri: v.yer, unvan: v.unvan ?? k.unvan ?? null, yer_degisti: gun });
    await kayitYaz(k, 0);
    return yanit(req, env, hesapOzeti(k));
  }

  // ---- ilan yardımcıları ----
  async function ayniKisiVar(slug, adNorm, vefat, haricId) {
    for (const onek of [`${P}x:${slug}:`, `x:${slug}:`]) {
      let cursor;
      do {
        const l = await kv.list({ prefix: onek, cursor });
        for (const key of l.keys) {
          if (haricId && key.name.endsWith(":" + haricId)) continue;
          const m = key.metadata || {};
          if (m.n === adNorm && m.v && Math.abs((Date.parse(m.v + "T00:00:00Z") - Date.parse(vefat + "T00:00:00Z")) / 86400000) <= 3) return true;
        }
        cursor = l.list_complete ? undefined : l.cursor;
      } while (cursor);
    }
    return false;
  }
  const ALAN_IZIN = ["ad_soyad", "cinsiyet", "yas", "vefat_tarihi", "namaz_tarihi", "namaz_yeri_vakti", "defin_yeri", "mahalle", "koy", "sehit", "rutbe", "toren_yeri", "duyuru_url"];
  async function ilanDegerlendir(k, a, haricId) {
    const s = (x) => (typeof x === "string" ? x.trim().replace(/\s+/g, " ") : x);
    const t = { il: k.il, ilce: k.ilce, ad_soyad: s(a.ad_soyad), cinsiyet: a.cinsiyet, vefat_tarihi: s(a.vefat_tarihi), namaz_tarihi: s(a.namaz_tarihi), beyan: true,
      basvuran: { ad_soyad: k.ad_soyad, yakinlik: "din görevlisi" } };
    for (const f of ["mahalle", "namaz_yeri_vakti", "defin_yeri"]) if (a[f] != null && a[f] !== "") t[f] = s(a[f]);
    if (a.yas != null && a.yas !== "") t.yas = Number(a.yas);
    for (const f of ["ad_soyad", "vefat_tarihi", "namaz_tarihi"]) if (typeof t[f] !== "string" || !t[f]) return { neden: `${f} gerekli` };
    if (a.koy != null && a.koy !== "") { t.koy = s(a.koy); const n = metinTemiz(t.koy); if (n) return { neden: `K8 koy: ${n}` }; }
    // ŞEHİT İLANI (§27) YALNIZ din görevlisi panelinden: rütbe zorunlu, tören yeri ve resmî duyuru bağlantısı isteğe bağlı (bağlantı yalnız sahibi için saklanır, halka açık çıktıda yok)
    if (a.sehit === true) {
      t.sehit = true;
      t.rutbe = s(a.rutbe);
      if (typeof t.rutbe !== "string" || t.rutbe.length < 2 || metinTemiz(t.rutbe)) return { neden: "şehit ilanında rütbe gerekli" };
      if (a.toren_yeri != null && a.toren_yeri !== "") { t.toren_yeri = s(a.toren_yeri); const n = metinTemiz(t.toren_yeri); if (n) return { neden: `K8 toren_yeri: ${n}` }; }
      if (a.duyuru_url != null && a.duyuru_url !== "") { t.duyuru_url = s(a.duyuru_url); if (typeof t.duyuru_url !== "string" || t.duyuru_url.length > 150 || !/^https:\/\/[^\s]+$/.test(t.duyuru_url)) return { neden: "duyuru bağlantısı https olmalı" }; }
    }
    const slug = ilSlug(k.il);
    const ayni = await ayniKisiVar(slug, adNormalize(t.ad_soyad), t.vefat_tarihi, haricId);
    const neden = degerlendir(t, { bugun: gun, telefonIlanSayisi: 0, ayniKisiVar: () => ayni }); // K6 yerine hesap başına günlük tavan
    return { neden, t, slug };
  }
  const dizinYaz = (slug, id, t) => kv.put(`${P}x:${slug}:${id}`, "1", { metadata: { n: adNormalize(t.ad_soyad), v: t.vefat_tarihi, t: t.namaz_tarihi }, expirationTtl: ILAN_TTL });
  const aktifHesap = (k) => k && k.durum === "onayli" && dogrulu(k); // panel/ilan yalnız onaylı hesaba

  async function ilan() {
    const k = await hesap();
    if (!aktifHesap(k)) return yanit(req, env, { hata: "yetkisiz", durum: k ? k.durum : null }, k ? 403 : 401);
    if (!profilTamam(k)) return yanit(req, env, { hata: "profil_gerekli" }, 409); // ad-soyad/görev yeri ilk ilandan önce /gorevli/profil ile
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const gs = `${P}gs:${k.id}:${gun}`;
    const n = parseInt((await kv.get(gs)) || "0", 10);
    if (n >= GUNLUK_ILAN) return yanit(req, env, { durum: "red", neden: "günlük ilan sınırı" }, 429);
    // §49: otomatik ilanı düzeltme. duzeltme_id = düzeltilen kaydın id'si; aynı hesabın aynı duzeltme_id'li canlı kaydı varsa YENİSİ açılmaz, o güncellenir
    let duz = null;
    if (g.json && g.json.duzeltme_id != null && g.json.duzeltme_id !== "") {
      if (typeof g.json.duzeltme_id !== "string" || !DUZELTME_RE.test(g.json.duzeltme_id)) return yanit(req, env, { hata: "duzeltme_id_gecersiz" }, 400);
      duz = g.json.duzeltme_id;
      // §49a: düzeltme yetkisi = hesabın görev yeri ile düzeltilen ilanın orijinal camisi/mahallesi eşleşmeli (il/ilçe zaten kayıttan gelir)
      if (!yerEslesir(k.gorev_yeri, g.json.orijinal_cami, g.json.orijinal_mahalle, k.ilce)) return yanit(req, env, { hata: "yetki_disi" }, 403);
    }
    const eski = duz ? (await hesapIlanlari(k)).find((x) => x.duzeltme_id === duz && ["yayinda", "bekliyor"].includes(x.durum)) : null;
    const r = await ilanDegerlendir(k, g.json || {}, eski ? eski.id : null); // il/ilçe istekten ALINMAZ: kayıttan
    if (r.neden) return yanit(req, env, { durum: "red", neden: r.neden });
    if (eski) {
      const tt = r.t;
      Object.assign(eski, { ad_soyad: tt.ad_soyad, cinsiyet: tt.cinsiyet, yas: tt.yas ?? null, vefat_tarihi: tt.vefat_tarihi, namaz_tarihi: tt.namaz_tarihi, liste_tarihi: tt.namaz_tarihi,
        namaz_yeri_vakti: tt.namaz_yeri_vakti ?? null, defin_yeri: tt.defin_yeri ?? null, mahalle: tt.mahalle ?? null, koy: tt.koy ?? null, guncelleme: o.now.toISOString() });
      await ilanYaz(eski);
      await dizinYaz(r.slug, eski.id, tt);
      return yanit(req, env, { durum: eski.durum, ilan_id: eski.id, guncellendi: true });
    }
    const t = r.t, id = rastgeleId();
    const yayinda = true; // aktifHesap yalnız onaylı hesaba izin verir
    const rec = {
      id, il: k.il, ilce: k.ilce, mahalle: t.mahalle ?? null, koy: t.koy ?? null, gorev_yeri: k.gorev_yeri, ad_soyad: t.ad_soyad, cinsiyet: t.cinsiyet, yas: t.yas ?? null,
      vefat_tarihi: t.vefat_tarihi, namaz_tarihi: t.namaz_tarihi, namaz_yeri_vakti: t.namaz_yeri_vakti ?? null, defin_yeri: t.defin_yeri ?? null,
      sehit: t.sehit === true, rutbe: t.rutbe ?? null, toren: t.toren_yeri ?? null, duyuru_url: t.duyuru_url ?? null,
      liste_tarihi: t.namaz_tarihi, gorevli: true, duzeltme_id: duz, dogrulandi: k.durum === "onayli", durum: yayinda ? "yayinda" : "bekliyor",
      kayit_id: k.id, olusturma: o.now.toISOString(),
    };
    await ilanYaz(rec);
    await kv.put(`${P}h:${k.id}:${id}`, "1", { expirationTtl: ILAN_TTL });
    await dizinYaz(r.slug, id, t);
    if (gozetimde(k)) await kv.put(`${P}g:${id}`, "1", { expirationTtl: 8 * 86400 });
    await kv.put(gs, String(n + 1), { expirationTtl: 90000 });
    return yanit(req, env, { durum: rec.durum, ilan_id: id });
  }

  // ---- POST /gorevli/kvkk-kabul (oturumlu): panel ilk açılışta KVKK aydınlatmasını "Okudum, anladım" ile kabul etti (§50) ----
  async function kvkkKabul() {
    const k = await hesap();
    if (!k || !dogrulu(k) || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    k.kvkk_kabul = o.now.toISOString();
    await kayitYaz(k, k.durum === "onayli" ? 0 : undefined);
    return yanit(req, env, { kvkk_kabul: k.kvkk_kabul });
  }

  // ---- POST /gorevli/sorumluluk-kabul (oturumlu): panel ilk açılışta sorumluluk uyarısını "Anladım, kabul ediyorum" ile kabul etti (§54) ----
  async function sorumlulukKabul() {
    const k = await hesap();
    if (!k || !dogrulu(k) || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    k.sorumluluk_kabul = o.now.toISOString();
    await kayitYaz(k, k.durum === "onayli" ? 0 : undefined);
    return yanit(req, env, { sorumluluk_kabul: k.sorumluluk_kabul });
  }

  // ---- POST /gorevli/parola {parola} (oturumlu): 4 haneli panel parolası hesap kaydına AES-GCM ile şifreli yazılır (§53) ----
  async function parolaKaydet() {
    const k = await hesap();
    if (!k || !dogrulu(k) || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    const g = await govde(2000);
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const p = g.json?.parola;
    if (typeof p !== "string" || !/^\d{4}$/.test(p)) return yanit(req, env, { hata: "parola_gecersiz" }, 400);
    if (!parolaAnahtariVar(env)) return yanit(req, env, { hata: "parola_servisi_yok" }, 503);
    k.parola_sifreli = await parolaSifrele(env, p);
    await kayitYaz(k, k.durum === "onayli" ? 0 : undefined);
    return yanit(req, env, { durum: "kaydedildi" });
  }

  // ---- POST /gorevli/parola-hatirlat (oturumlu): parolayı çözüp hesabın <kullanici>@diyanet.gov.tr adresine yollar; günde ≤3 ----
  async function parolaHatirlat() {
    const k = await hesap();
    if (!k || !dogrulu(k) || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    if (!parolaAnahtariVar(env) || !epostaVar(env)) return yanit(req, env, { hata: "parola_servisi_yok" }, 503);
    if (!k.parola_sifreli) return yanit(req, env, { hata: "parola_yok" }, 404);
    const sk = `${P}ph:${k.id}:${gun}`;
    const n = parseInt((await kv.get(sk)) || "0", 10);
    if (n >= GUNLUK_HATIRLAT) {
      const bekle = Math.max(60, Math.ceil((Date.parse(gunEkle(gun, 1) + "T00:00:00+03:00") - o.now.getTime()) / 1000));
      return yanit(req, env, { hata: "gunluk_sinir", bekle_sn: bekle }, 429, { "Retry-After": String(bekle) });
    }
    const p = await parolaCoz(env, k.parola_sifreli);
    if (!p) return yanit(req, env, { hata: "parola_yok" }, 404);
    const adres = `${k.kullanici}@${ESTA}`;
    const r = await parolaEpostaGonder(env, o.fetch, adres, p);
    if (r.hata) return yanit(req, env, { hata: "gonderilemedi" }, 502);
    await kv.put(sk, String(n + 1), { expirationTtl: 90000 });
    return yanit(req, env, { durum: "gonderildi", adres });
  }

  async function ilanlarim() {
    const k = await hesap();
    if (!k || !dogrulu(k) || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    const l = k.durum === "onayli" ? await hesapIlanlari(k) : []; // "kontrolde": panel açık, liste boş

    return yanit(req, env, { hesap: { durum: k.durum, profil_tamam: profilTamam(k), il: k.il ?? null, ilce: k.ilce ?? null, gorev_yeri: k.gorev_yeri ?? null, unvan: k.unvan ?? null, ad_soyad: k.ad_soyad ?? null }, ilanlar: l.map((i) => ({ ...genelGorevli(i), durum: i.durum })) });
  }
  // GET /gorevli/durum — uygulama her açılışta sorar: "kontrolde" iken panel kapalı, "onayli" olunca açılır
  async function ben() {
    if ((await oturumKid()) === "RED") return yanit(req, env, { durum: "silindi" }); // sahibi reddetti: hesap silindi
    const k = await hesap();
    if (!k) return yanit(req, env, { hata: "yetkisiz" }, 401);
    return yanit(req, env, { durum: k.durum, profil_tamam: profilTamam(k), ad_soyad: k.ad_soyad ?? null, il: k.il ?? null, ilce: k.ilce ?? null, gorev_yeri: k.gorev_yeri ?? null, unvan: k.unvan ?? null, kvkk_kabul: k.kvkk_kabul ?? null, sorumluluk_kabul: k.sorumluluk_kabul ?? null });
  }
  async function kendiIlanYukle(k, id) {
    if (typeof id !== "string" || !/^[0-9a-f]{16}$/.test(id)) return null;
    const i = await kvJson(kv, `${P}i:${id}`);
    return i && i.kayit_id === k.id ? i : null;
  }
  async function iptal() {
    const k = await hesap();
    if (!aktifHesap(k)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const i = await kendiIlanYukle(k, g.json?.ilan_id);
    if (!i) return yanit(req, env, { hata: "ilan_bulunamadi" }, 404);
    i.durum = "iptal";
    await ilanYaz(i);
    await kv.delete(`${P}x:${ilSlug(i.il)}:${i.id}`);
    await kv.delete(`${P}g:${i.id}`);
    return yanit(req, env, { durum: "iptal" });
  }
  async function duzenle() {
    const k = await hesap();
    if (!aktifHesap(k)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const i = await kendiIlanYukle(k, g.json?.ilan_id);
    if (!i || !["yayinda", "bekliyor"].includes(i.durum)) return yanit(req, env, { hata: "ilan_duzenlenemez" }, i ? 409 : 404);
    const yeni = { ...i };
    yeni.toren_yeri = i.toren; yeni.duyuru_url = i.duyuru_url;
    for (const a of ALAN_IZIN) if (a in (g.json || {})) yeni[a] = g.json[a];
    const r = await ilanDegerlendir(k, yeni, i.id);
    if (r.neden) return yanit(req, env, { durum: "red", neden: r.neden });
    const t = r.t;
    Object.assign(i, { ad_soyad: t.ad_soyad, cinsiyet: t.cinsiyet, yas: t.yas ?? null, vefat_tarihi: t.vefat_tarihi, namaz_tarihi: t.namaz_tarihi, liste_tarihi: t.namaz_tarihi,
      namaz_yeri_vakti: t.namaz_yeri_vakti ?? null, defin_yeri: t.defin_yeri ?? null, mahalle: t.mahalle ?? null, koy: t.koy ?? null,
      sehit: t.sehit === true, rutbe: t.rutbe ?? null, toren: t.toren_yeri ?? null, duyuru_url: t.duyuru_url ?? null });
    await ilanYaz(i);
    await dizinYaz(r.slug, i.id, t);
    return yanit(req, env, { durum: i.durum, ilan_id: i.id });
  }

  // ---- sahibi paneli ----
  async function tumHesaplar() {
    const out = [];
    let cursor;
    do {
      const l = await kv.list({ prefix: `${P}k:`, cursor });
      for (const key of l.keys) { const k = await kvJson(kv, key.name); if (k) out.push(k); }
      cursor = l.list_complete ? undefined : l.cursor;
    } while (cursor);
    return out;
  }
  const ozet = (k) => ({ unvan: k.unvan ?? null, not: k.kontrol_notu === "liste_yok" ? "liste yok" : k.kontrol_notu === "listede_yok" ? "listede bulunamadı" : k.durum === "kuyruk" ? "kart doğrulaması tutmadı" : null, cami_eslesti: k.cami_eslesti ?? null, kart_puan: k.kart_puan ?? null, kart_uyarilar: k.kart_uyarilar ?? [], kart_nedenler: k.kart_nedenler ?? [], id: k.id, ad_soyad: k.ad_soyad, il: k.il, ilce: k.ilce, gorev_yeri: k.gorev_yeri, durum: k.durum, dogrulama: k.dogrulama ?? null, olusturma: k.olusturma });
  async function kuyruk() {
    if (!panelIzin()) return yanit(req, env, { hata: "yetkisiz" }, 403);
    const c = { kuyruk: [], gozetim: [], cakisma: [] }; // kuyruk = "kontrolde" (kart tamam, listede yok) + "kuyruk" (kart tutmadı)
    for (const k of await tumHesaplar()) {
      if (k.durum === "kuyruk" || k.durum === "kontrolde") { const f = await kv.get(`${P}foto:${k.id}`); c.kuyruk.push({ ...ozet(k), foto_var: !!f, foto_base64: f }); }
      else if (k.durum === "donduruldu" && String(k.not || "").startsWith("cift_kayit")) c.cakisma.push({ ...ozet(k), not: k.not, onceki_durum: k.onceki_durum });
      if (k.durum === "onayli" && gozetimde(k)) c.gozetim.push({ ...ozet(k), gozetim_bitis: k.gozetim_bitis, capraz_toplam: k.capraz_toplam || 0, capraz_eslesen: k.capraz_eslesen || 0 });
    }
    return yanit(req, env, c);
  }
  // Karar: {id,onay} hesap (kontrolde/kuyruk) | {id,dondur:true} | {id,ac:true} (dondurmayı kaldır)
  async function karar() {
    if (!panelIzin()) return yanit(req, env, { hata: "yetkisiz" }, 403);
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const j = g.json || {};
    const k = typeof j.id === "string" && /^[0-9a-f]{16}$/.test(j.id) ? await kvJson(kv, `${P}k:${j.id}`) : null;
    if (!k) return yanit(req, env, { hata: "kayit_bulunamadi" }, 404);
    if (j.dondur === true) {
      await dondur(k, "sahibi");
    } else if (j.ac === true) {
      if (k.durum !== "donduruldu") return yanit(req, env, { hata: "dondurulmus_degil" }, 409);
      k.durum = GIRIS_DURUMLARI.includes(k.onceki_durum) ? k.onceki_durum : "kuyruk"; k.not = null;
      await kayitYaz(k, 0);
    } else if (j.onay === true) {
      if (!["kuyruk", "kontrolde"].includes(k.durum)) return yanit(req, env, { hata: "kuyrukta_degil" }, 409);
      k.dogrulama = k.durum === "kontrolde" ? "kart+elle" : "elle"; k.durum = "onayli"; k.dogrulama_tarih = gun;
      k.gozetim_bitis = new Date(o.now.getTime() + GOZETIM_GUN * 86400000).toISOString();
      await kayitYaz(k, 0);
      await onaySms(k); // yedek SMS (Netgsm varsa); asıl yol: uygulama durum sorgusu + arka plan bildirimi
    } else if (j.onay === false) {
      if (!["kuyruk", "kontrolde"].includes(k.durum)) return yanit(req, env, { hata: "kuyrukta_degil" }, 409);
      // RED: hesap, oturum ve fotoğraf KV'den SİLİNİR (yalnız "RED" işareti 30 gün kalır: uygulama "hesap silindi" der)
      for (const oh of (await kvJson(kv, `${P}ot:${k.id}`)) || []) await kv.put(`${P}oturum:${oh}`, "RED", { expirationTtl: 30 * 86400 });
      await kv.delete(`${P}ot:${k.id}`);
      await kv.delete(`${P}foto:${k.id}`); await kv.delete(`${P}kod:${k.id}`);
      if (k.telefon) await kv.delete(`${P}t:${await sha256(k.telefon)}`); // eski kayıt kalıntısı
      await kv.delete(`${P}ac:${katla(k.ad_soyad || "")}|${katla(k.gorev_yeri || "")}`);
      await kv.delete(`${P}k:${k.id}`);
      return yanit(req, env, { durum: "silindi" });
    } else return yanit(req, env, { hata: "onay, dondur ya da ac gerekli" }, 400);
    await kv.delete(`${P}foto:${k.id}`); // karar sonrası fotoğraf silinir
    return yanit(req, env, { durum: k.durum });
  }

  // ---- CI -> Worker: müftülük listesi (x-gizli). Gövde {liste:{il_slug:{ilce_slug:[{ad_soyad,cami}]}}}. Değişmeyen ilçeye KV yazılmaz (ücretsiz plan: 1000 yazma/gün). ----
  async function listeYukle() {
    if (!panelIzin()) return yanit(req, env, { hata: "yetkisiz" }, 403);
    const g = await govde(LISTE_GOVDE_LIMIT);
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const L = g.json?.liste;
    if (!L || typeof L !== "object") return yanit(req, env, { hata: "liste gerekli" }, 400);
    let yazilan = 0, ayni = 0;
    for (const [il, ilceler] of Object.entries(L)) {
      if (!ILCELER[il] || !ilceler || typeof ilceler !== "object") continue;
      for (const [ilce, kayitlar] of Object.entries(ilceler)) {
        if (!/^[a-z0-9]{2,40}$/.test(ilce) || !Array.isArray(kayitlar)) continue;
        const temiz = kayitlar.filter((x) => x && typeof x.ad_soyad === "string" && typeof x.cami === "string" && x.ad_soyad.length <= 80 && x.cami.length <= 80).map((x) => ({ ad_soyad: x.ad_soyad, cami: x.cami }));
        const yeni = JSON.stringify(temiz);
        const key = `${P}liste:${il}:${ilce}`;
        if ((await kv.get(key)) === yeni) { ayni++; continue; }
        await kv.put(key, yeni);
        yazilan++;
      }
    }
    return yanit(req, env, { yazilan, ayni });
  }

  // ---- gözetim çapraz kontrolü: GET /gorevli/capraz (bekleyen ilanlar) , POST /gorevli/capraz {sonuclar:[{ilan_id, eslesti}]} (x-gizli) ----
  async function capraz() {
    if (!panelIzin()) return yanit(req, env, { hata: "yetkisiz" }, 403);
    if (req.method === "GET") {
      const out = [];
      let cursor;
      do {
        const l = await kv.list({ prefix: `${P}g:`, cursor });
        for (const key of l.keys) {
          const i = await kvJson(kv, `${P}i:${key.name.slice((P + "g:").length)}`);
          if (i && i.capraz === undefined && ["yayinda", "bekliyor"].includes(i.durum)) out.push({ ilan_id: i.id, il: i.il, ilce: i.ilce, ad_soyad: i.ad_soyad, vefat_tarihi: i.vefat_tarihi, namaz_tarihi: i.namaz_tarihi });
        }
        cursor = l.list_complete ? undefined : l.cursor;
      } while (cursor);
      return yanit(req, env, { ilanlar: out });
    }
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    let islenen = 0;
    for (const sn of (Array.isArray(g.json?.sonuclar) ? g.json.sonuclar : []).slice(0, 200)) {
      const i = typeof sn?.ilan_id === "string" ? await kvJson(kv, `${P}i:${sn.ilan_id}`) : null;
      if (!i || i.capraz !== undefined) continue;
      i.capraz = sn.eslesti === true;
      await ilanYaz(i);
      const k = await kvJson(kv, `${P}k:${i.kayit_id}`);
      if (k) { k.capraz_toplam = (k.capraz_toplam || 0) + 1; if (i.capraz) k.capraz_eslesen = (k.capraz_eslesen || 0) + 1; await kayitYaz(k, 0); }
      islenen++;
    }
    return yanit(req, env, { islenen });
  }

  // ---- halka açık liste ----
  async function liste(slug) {
    const il = ILCELER[slug];
    if (!il) return yanit(req, env, { hata: "il bulunamadı" }, 404);
    const sinir = gunEkle(gun, -7);
    const kayitlar = [];
    let cursor;
    do {
      const l = await kv.list({ prefix: `${P}x:${slug}:`, cursor });
      for (const key of l.keys) {
        if (key.metadata && key.metadata.t && key.metadata.t < sinir) continue;
        const i = await kvJson(kv, `${P}i:${key.name.split(":")[3]}`);
        if (i && i.durum === "yayinda" && i.liste_tarihi >= sinir) kayitlar.push(genelGorevli(i));
      }
      cursor = l.list_complete ? undefined : l.cursor;
    } while (cursor);
    kayitlar.sort((a, b) => (a.namaz_tarihi < b.namaz_tarihi ? 1 : a.namaz_tarihi > b.namaz_tarihi ? -1 : a.id < b.id ? -1 : 1));
    return yanit(req, env, { il: il.il, kayitlar, guncelleme: o.now.toISOString() }, 200, { "Cache-Control": "public, max-age=60" });
  }

  const m = req.method;
  if (m === "GET") {
    const lm = yol.match(/^\/gorevli\/([a-z0-9]{2,30})\.json$/);
    if (lm) return liste(lm[1]);
    if (yol === "/gorevli/ilanlarim") return ilanlarim();
    if (yol === "/gorevli/durum" || yol === "/gorevli/ben") return ben();
    if (yol === "/gorevli/kuyruk") return kuyruk();
    if (yol === "/gorevli/capraz") return capraz();
    return yanit(req, env, { hata: "bulunamadı" }, 404);
  }
  if (m === "POST") {
    switch (yol) {
      case "/gorevli/eposta-kod": return epostaKod();
      case "/gorevli/eposta-dogrula": return epostaDogrula();
      case "/gorevli/profil": return profil();
      case "/gorevli/gorev-yeri": return gorevYeri();
      case "/gorevli/kayit": case "/gorevli/kod": case "/gorevli/giris": case "/gorevli/dogrula":
        return yanit(req, env, { hata: "kaldirildi", ileti: "Doğrulama artık Diyanet e-posta koduyla: /gorevli/eposta-kod" }, 410);
      case "/gorevli/kvkk-kabul": return kvkkKabul();
      case "/gorevli/sorumluluk-kabul": return sorumlulukKabul();
      case "/gorevli/parola": return parolaKaydet();
      case "/gorevli/parola-hatirlat": return parolaHatirlat();
      case "/gorevli/ilan": return ilan();
      case "/gorevli/ilan/iptal": return iptal();
      case "/gorevli/ilan/duzenle": return duzenle();
      case "/gorevli/karar": return karar();
      case "/gorevli/liste": return listeYukle();
      case "/gorevli/capraz": return capraz();
    }
  }
  return yanit(req, env, { hata: "yöntem_desteklenmiyor" }, 405);
}

// /aile/bildir görevli ilanları için de çalışır: 2 farklı IP -> ilan gizli; gözetimdeki (ilk 7 gün) hesapta hesap da donar. Bulunamazsa null.
export async function gorevliBildir(env, H, ilanId, ipOzeti, now = new Date()) {
  const kv = env.AILE;
  const ilan = await H.kvJson(kv, `${P}i:${ilanId}`);
  if (!ilan) return null;
  const nk = `${P}n:${ilanId}`;
  const ipler = (await H.kvJson(kv, nk)) || [];
  if (!ipler.includes(ipOzeti)) ipler.push(ipOzeti);
  await kv.put(nk, JSON.stringify(ipler), { expirationTtl: ILAN_TTL });
  if (ipler.length >= 2 && ilan.durum === "yayinda") {
    ilan.durum = "gizli";
    await kv.put(`${P}i:${ilanId}`, JSON.stringify(ilan), { expirationTtl: ILAN_TTL });
    const k = await H.kvJson(kv, `${P}k:${ilan.kayit_id}`);
    if (k && k.gozetim_bitis && Date.parse(k.gozetim_bitis) > now.getTime() && k.durum === "onayli") {
      k.onceki_durum = k.durum; k.durum = "donduruldu"; k.not = "gozetim_bildirim";
      await kv.put(`${P}k:${k.id}`, JSON.stringify(k));
      let cursor;
      do {
        const l = await kv.list({ prefix: `${P}h:${k.id}:`, cursor });
        for (const key of l.keys) {
          const i = await H.kvJson(kv, `${P}i:${key.name.split(":")[3]}`);
          if (i && ["yayinda", "bekliyor"].includes(i.durum)) { i.durum = "gizli"; await kv.put(`${P}i:${i.id}`, JSON.stringify(i), { expirationTtl: ILAN_TTL }); }
        }
        cursor = l.list_complete ? undefined : l.cursor;
      } while (cursor);
    }
  }
  return { alindi: true };
}
