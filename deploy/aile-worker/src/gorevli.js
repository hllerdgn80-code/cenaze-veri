// Din görevlisi ilan kapısı — URUN-TASLAGI.md §37 (15.10.2026) + ek kararlar (müftülük listesi, taklit önlemi).
// index.js'ten H (yardımcılar) alır; döngüsel içe aktarma yok.
// KV (AILE) anahtarları, hepsi "gorevli:" önekli:
//   k:<kayit_id>            hesap kaydı (ad, il, ilçe, görev yeri, telefon [YALNIZ SMS için; hiçbir çıktıda yok], durum, dogrulama, kod özeti). FOTOĞRAF İÇERMEZ.
//   t:<sha256(telefon)>     -> kayit_id
//   tk:<sha256(telefon)>:<gün> günlük yeni kayıt sayacı
//   ac:<ad|cami katla>      -> kayit_id (TEK HESAP kuralı)
//   liste:<il>:<ilce>       müftülük personel listesi [{ad_soyad, cami}] (CI'dan POST /gorevli/liste ile)
//   foto:<kayit_id>         YALNIZ durum "kuyruk" iken, TTL 7 gün; karar verilince silinir
//   oturum:<sha256(token)>  -> kayit_id (TTL 180 gün); RED sonrası "RED" işareti (30 gün): uygulama "hesap silindi" der
//   ot:<kayit_id>           hesabın oturum özetleri (RED'de silinir)
//   i:<ilan_id>             ilan;  x:<slug>:<ilan_id> dizin (metadata n,v,t);  h:<kayit_id>:<ilan_id> hesabın ilanları
//   g:<ilan_id>             gözetimdeki hesabın ilanı (çapraz kontrol bekliyor; TTL 8 gün)
//   n:<ilan_id>             bildirim yapan IP özetleri;  gs:<kayit_id>:<gün> günlük ilan sayacı
import { ILCELER } from "./veri.js";
import { telefonNormalize, smsGonder, netgsmVar, kodGonder as kodKanali, kanalGerekli, SMS_METNI, NETGSM_URL, waVar } from "./dogrulama.js";
export { telefonNormalize, smsGonder, netgsmVar, SMS_METNI, NETGSM_URL };
import { degerlendir, adGecerli, adNormalize, katla, metinTemiz, bugunTR, gunEkle, ilSlug } from "./kurallar.js";

import { OCR_MODEL, OCR_MAX_TOKEN, ISTEM, UNVANLAR, UNVAN_KATLA, yanitCoz, kartKarar } from "./gorevli_kurallar.js";
export { OCR_MODEL };
const FOTO_AZAMI_BAYT = 2 * 1024 * 1024;
const KAYIT_GOVDE_LIMIT = 3_200_000;
const LISTE_GOVDE_LIMIT = 8_000_000;
const GOVDE_LIMIT = 4096;
const KOD_OMRU_MS = 15 * 60 * 1000;
const AZAMI_KOD_DENEME = 3;
const OTURUM_TTL = 180 * 86400;
const KONTROL_GUN = 14; // "kontrolde"/"kuyruk" hesabı en çok 14 gün yaşar, sonra KV TTL ile kendiliğinden silinir
const ILAN_TTL = 120 * 86400;
const FOTO_TTL = 7 * 86400;
const GOZETIM_GUN = 7;
const GUNLUK_YENI_KAYIT = 3;
const GUNLUK_ILAN = 10;
const P = "gorevli:";
const GIRIS_DURUMLARI = ["onayli", "kontrolde", "kuyruk"]; // telefon koduyla oturum alabilen durumlar (ilan YALNIZ "onayli")
const CAMI_GENEL = new Set(["cami", "camii", "camisi", "mescidi", "mescit", "camii serif", "serif", "koyu", "mahallesi"]);
export const ONAY_SMS = "Kimin Cenazesi: din görevlisi başvurunuz onaylandı, paneliniz açıldı.";
export const BEYAN_METNI = "Verdiğim bilgilerin doğru olduğunu, yanıltıcı bilgi vermem hâlinde hakkımda yasal işlem yapılmasını kabul ediyorum.";
// ---- saf yardımcılar (test edilir) ----
export function kartEslesir(metin, adSoyad) {
  const t = " " + katla(metin) + " ";
  if (!t.includes("diyanet")) return false;
  const kelimeler = katla(adSoyad).split(" ").filter((w) => w.length >= 2);
  return kelimeler.length >= 2 && kelimeler.every((w) => t.includes(w));
}
export function fotoGecerli(b64) {
  if (typeof b64 !== "string" || !/^[A-Za-z0-9+/]+={0,2}$/.test(b64)) return false;
  if (Math.floor((b64.length * 3) / 4) > FOTO_AZAMI_BAYT) return false;
  return b64.startsWith("/9j/"); // JPEG
}
// Müftülük listesi: KABUL KURALI B (15.10.2026) — liste onay şartı DEĞİL, yalnız PUAN (eşleşirse liste_eslesti). Cami eşleşmesi de şart değil (not).
// Dönüş: {durum:"liste_yok"|"listede_yok"|"ad_var", cami_eslesti:bool}.
export function listeDurumu(kayitlar, adSoyad, goreYeri) {
  if (!Array.isArray(kayitlar) || kayitlar.length === 0) return { durum: "liste_yok", cami_eslesti: false };
  const ad = katla(adSoyad).split(" ").filter(Boolean);
  const yer = new Set(katla(goreYeri).split(" ").filter(Boolean));
  let adVar = false, cami = false;
  if (ad.length >= 2) {
    for (const k of kayitlar) {
      const la = new Set(katla(k.ad_soyad).split(" ").filter(Boolean));
      if (!ad.every((w) => la.has(w))) continue;
      adVar = true;
      const anlamli = katla(k.cami).split(" ").filter((w) => w && !CAMI_GENEL.has(w));
      if (anlamli.length && anlamli.filter((w) => yer.has(w)).length >= Math.min(2, anlamli.length)) cami = true;
    }
  }
  return { durum: adVar ? "ad_var" : "listede_yok", cami_eslesti: adVar && cami };
}
const GENEL = ["id", "il", "ilce", "ad_soyad", "cinsiyet", "yas", "vefat_tarihi", "namaz_tarihi", "namaz_yeri_vakti", "defin_yeri", "liste_tarihi"];
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
  // Kod BİZDEN gider (kullanıcı başvuru ekranına girer): WhatsApp şablonu → Netgsm SMS → GELISTIRME=1'de yanıtta (dogrulama.js)
  async function kodGonder(k) {
    const kod = kod6();
    k.kod_ozeti = await sha256(`${k.id}:${kod}`);
    k.kod_deneme = 0;
    k.kod_zaman = o.now.getTime();
    return await kodKanali(env, o.fetch, k.telefon, kod);
  }
  // "kontrolde"/"kuyruk": oluşturmadan en çok 14 gün sonra kendiliğinden silinir (mutlak son kullanma); onaylı hesap kalıcı
  const kayitYaz = (k, ttl) => {
    if (k.durum === "kontrolde" || k.durum === "kuyruk") {
      const son = Math.floor((Date.parse(k.olusturma) + KONTROL_GUN * 86400000) / 1000);
      return kv.put(`${P}k:${k.id}`, JSON.stringify(k), { expiration: Math.max(son, Math.floor(o.now.getTime() / 1000) + 120) });
    }
    return kv.put(`${P}k:${k.id}`, JSON.stringify(k), ttl ? { expirationTtl: ttl } : {});
  };
  const kalici = (k) => (k.tel_dogrulandi ? 0 : 86400);
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
    try { return await smsGonder(env, o.fetch, k.telefon, ONAY_SMS); } catch { return false; }
  }
  const gozetimde = (k) => k.gozetim_bitis && Date.parse(k.gozetim_bitis) > o.now.getTime();

  // ---- POST /gorevli/kayit ----
  // Adım 1 (foto yok): bilgiler -> {durum:"foto_gerek", kayit_id, liste_eslesti}. Adım 2 (kayit_id + foto_base64): OCR.
  // Liste eşleşmesi TEK BAŞINA onay vermez; kart OCR'ı şart. Fotoğraf yalnız bellekte, yalnız "kuyruk" sonucunda ≤7 gün KV'de.
  async function kayit() {
    const g = await govde(KAYIT_GOVDE_LIMIT);
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const b = g.json || {};
    const dev = env.GELISTIRME === "1";
    if (kanalGerekli(env)) return yanit(req, env, { hata: "dogrulama_servisi_yok" }, 503);
    if (b.kayit_id == null && b.beyan !== true) return yanit(req, env, { hata: "beyan_gerekli" }, 400); // zorunlu onay kutusu (K7 kalıbı)
    const s = (x) => (typeof x === "string" ? x.trim().replace(/\s+/g, " ") : x);
    const fotoVar = b.foto_base64 != null && b.foto_base64 !== "";
    if (fotoVar && !fotoGecerli(b.foto_base64)) return yanit(req, env, { hata: "foto_gecersiz" }, 400);
    let k;
    if (b.kayit_id != null) {
      if (typeof b.kayit_id !== "string" || !/^[0-9a-f]{16}$/.test(b.kayit_id)) return yanit(req, env, { hata: "kayit_id gecersiz" }, 400);
      k = await kvJson(kv, `${P}k:${b.kayit_id}`);
      if (!k || !["foto_bekliyor", "deneme2"].includes(k.durum)) return yanit(req, env, { hata: "kayit_bulunamadi" }, 404);
    } else {
      const ad = s(b.ad_soyad), il = s(b.il), ilce = s(b.ilce), yer = s(b.gorev_yeri), tel = telefonNormalize(b.telefon);
      if (!adGecerli(ad)) return yanit(req, env, { hata: "ad_soyad gecersiz" }, 400);
      const ilv = ILCELER[ilSlug(il || "")];
      if (!ilv) return yanit(req, env, { hata: "il gecersiz" }, 400);
      if (ilce !== "Merkez" && !ilv.ilceler.includes(ilce)) return yanit(req, env, { hata: "ilce gecersiz" }, 400);
      if (typeof yer !== "string" || yer.length < 2 || yer.length > 60 || metinTemiz(yer)) return yanit(req, env, { hata: "gorev_yeri gecersiz" }, 400);
      if (!tel) return yanit(req, env, { hata: "telefon gecersiz" }, 400);
      const eh = await sha256(tel);
      const varId = await kv.get(`${P}t:${eh}`);
      if (varId) {
        const eski = await kvJson(kv, `${P}k:${varId}`);
        if (eski && ["foto_bekliyor", "deneme2"].includes(eski.durum)) k = eski; // yarım kalan kayıt: sayaç sıfırlanmaz
        else if (eski) return yanit(req, env, { hata: "hesap_var" }, 409);
      }
      if (!k) {
        const sk = `${P}tk:${eh}:${gun}`;
        const n = parseInt((await kv.get(sk)) || "0", 10);
        if (n >= GUNLUK_YENI_KAYIT) return yanit(req, env, { hata: "cok_fazla_kayit" }, 429);
        await kv.put(sk, String(n + 1), { expirationTtl: 90000 });
        k = { id: rastgeleId(), deneme: 0, olusturma: o.now.toISOString(), ip: o.ipOzeti, tel_dogrulandi: false, durum: "foto_bekliyor" };
      }
      const unv = typeof b.unvan === "string" ? UNVANLAR.find((u) => katla(u) === katla(b.unvan)) : null;
      if (b.unvan != null && b.unvan !== "" && !unv) return yanit(req, env, { hata: "unvan gecersiz" }, 400);
      Object.assign(k, { ad_soyad: ad, il: ilv.il, ilce, gorev_yeri: yer, telefon: tel, beyan: true, beyan_tarihi: k.beyan_tarihi ?? o.now.toISOString(), unvan: unv ?? k.unvan ?? null });
      await kv.put(`${P}t:${eh}`, k.id, { expirationTtl: 86400 });
      const liste = await kvJson(kv, `${P}liste:${ilSlug(k.il)}:${ilceSlug(k.ilce)}`);
      const ld = listeDurumu(liste, k.ad_soyad, k.gorev_yeri);
      k.liste_durum = ld.durum; k.cami_eslesti = ld.cami_eslesti; k.liste_eslesti = ld.durum === "ad_var";
      await kayitYaz(k, 86400);
    }
    if (!fotoVar) return yanit(req, env, { durum: "foto_gerek", kayit_id: k.id, liste_eslesti: k.liste_eslesti === true });
    if (!env.AI) return yanit(req, env, { hata: "ocr_yok" }, 503);
    // OCR: fotoğraf yalnız bu fonksiyonun belleğinde
    let metin = "";
    try {
      const r = await env.AI.run(OCR_MODEL, {
        messages: [{ role: "user", content: [{ type: "text", text: ISTEM }, { type: "image_url", image_url: { url: `data:image/jpeg;base64,${b.foto_base64}` } }] }],
        max_tokens: OCR_MAX_TOKEN,
      });
      metin = String((r && (r.response ?? r.description)) ?? "");
    } catch { return yanit(req, env, { hata: "ocr_gecici_hata" }, 503); } // deneme hakkı yanmaz
    k.deneme += 1;
    let fotoSakla = false;
    const kk = kartKarar(yanitCoz(metin), k); // fotoğraf ve sicil değeri hiçbir yere yazılmaz
    if (!k.unvan) { // seçilmediyse karttan (okunan unvan, listedeki ilk eşleşme)
      const ham = " " + katla(`${yanitCoz(metin).unvan ?? ""}`) + " ";
      const i = UNVAN_KATLA.findIndex((u) => ham.includes(" " + u + " "));
      if (i >= 0) k.unvan = UNVANLAR[i];
    }
    if (k.liste_eslesti) kk.puan += 1; // müftülük listesi eşleşmesi PUAN (şart değil)
    k.kart_puan = kk.puan; k.kart_uyarilar = kk.uyarilar; k.kart_nedenler = kk.gecti ? [] : kk.nedenler;
    if (kk.gecti) { // KABUL KURALI B: kart kontrolleri (ibare, ad, unvan, fiziksel kart) geçerse onaylı; liste şart değil
      k.durum = "onayli"; k.dogrulama = k.liste_eslesti ? "kart+muftuluk_listesi" : "kart";
      k.gozetim_bitis = new Date(o.now.getTime() + GOZETIM_GUN * 86400000).toISOString(); // ilk 7 gün gözetim (çapraz kontrol + 2 bildirim)
    } else if (k.deneme < 2) {
      k.durum = "deneme2";
      await kayitYaz(k, 86400);
      return yanit(req, env, { durum: "deneme2", kayit_id: k.id, liste_eslesti: k.liste_eslesti === true, neden: kk.nedenler });
    } else {
      k.durum = "kuyruk"; fotoSakla = true; // kart iki kez tutmadı: fotoğraf ≤7 gün sahibinin bakması için
    }
    k.dogrulama_tarih = gun;
    // TEK HESAP: aynı ad + görev yeri için ikinci hesap -> ikisi de dondurulur
    const acKey = `${P}ac:${katla(k.ad_soyad)}|${katla(k.gorev_yeri)}`;
    const oncekiId = await kv.get(acKey);
    const onceki = oncekiId && oncekiId !== k.id ? await kvJson(kv, `${P}k:${oncekiId}`) : null;
    if (fotoSakla) await kv.put(`${P}foto:${k.id}`, b.foto_base64, { expirationTtl: FOTO_TTL }); // TEK İSTİSNA: sahibinin elle bakması için ≤7 gün
    if (onceki && [...GIRIS_DURUMLARI, "donduruldu"].includes(onceki.durum)) {
      await dondur(onceki, `cift_kayit:${k.id}`);
      await dondur(k, `cift_kayit:${onceki.id}`);
      return yanit(req, env, { durum: "kontrol_bekliyor", kayit_id: k.id });
    }
    await kv.put(acKey, k.id);
    const kg = await kodGonder(k);
    if (kg.hata) return yanit(req, env, { hata: "kod_gonderilemedi" }, 502);
    await kayitYaz(k, 86400); // telefon doğrulanana dek 1 gün
    const c = { durum: k.durum, kayit_id: k.id, dogrulama: "kod", kanal: kg.kanal, liste_eslesti: k.liste_eslesti === true, cami_eslesti: k.cami_eslesti === true };
    if (kg.kod) c.gelistirme_kodu = kg.kod;
    return yanit(req, env, c);
  }

  // ---- POST /gorevli/kod (kodu yeniden gönder) | /gorevli/giris {telefon} ----
  async function kodIste(giris) {
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    let k;
    if (giris) {
      const tl = telefonNormalize(g.json?.telefon);
      const kid = tl ? await kv.get(`${P}t:${await sha256(tl)}`) : null;
      k = kid ? await kvJson(kv, `${P}k:${kid}`) : null;
      if (!k || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { dogrulama: "kod", kayit_id: rastgeleId() }); // varlık sızdırmaz
    } else {
      const kid = g.json?.kayit_id;
      k = typeof kid === "string" && /^[0-9a-f]{16}$/.test(kid) ? await kvJson(kv, `${P}k:${kid}`) : null;
      if (!k || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "kayit_bulunamadi" }, 404);
    }
    if (k.kod_zaman && o.now.getTime() - k.kod_zaman < 60000) return yanit(req, env, { hata: "cok_sik_tekrar" }, 429, { "Retry-After": "60" });
    if (kanalGerekli(env)) return yanit(req, env, { hata: "dogrulama_servisi_yok" }, 503);
    const kg = await kodGonder(k);
    if (kg.hata) return yanit(req, env, { hata: "kod_gonderilemedi" }, 502);
    await kayitYaz(k, kalici(k));
    const c = { dogrulama: "kod", kanal: kg.kanal, kayit_id: k.id };
    if (kg.kod) c.gelistirme_kodu = kg.kod;
    return yanit(req, env, c);
  }

  // ---- POST /gorevli/dogrula ----
  async function dogrula() {
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const { kayit_id, kod } = g.json || {};
    if (typeof kayit_id !== "string" || !/^[0-9a-f]{16}$/.test(kayit_id) || typeof kod !== "string" || !/^\d{6}$/.test(kod)) return yanit(req, env, { hata: "kayit_id ve 6 haneli kod gerekli" }, 400);
    const k = await kvJson(kv, `${P}k:${kayit_id}`);
    if (!k || !k.kod_ozeti) return yanit(req, env, { durum: "red", neden: "kayıt bulunamadı ya da kod yok" }, 410);
    if (k.durum === "red" || k.durum === "donduruldu") return yanit(req, env, { durum: k.durum }, 403);
    if (!GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "kart_dogrulamasi_bitmedi" }, 409);
    if (o.now.getTime() - k.kod_zaman > KOD_OMRU_MS) return yanit(req, env, { hata: "kod_suresi_doldu" }, 410);
    if ((await sha256(`${kayit_id}:${kod}`)) !== k.kod_ozeti) {
      k.kod_deneme += 1;
      if (k.kod_deneme >= AZAMI_KOD_DENEME) { k.kod_ozeti = null; await kayitYaz(k, kalici(k)); return yanit(req, env, { durum: "red", neden: "kod 3 kez yanlış girildi" }, 429); }
      await kayitYaz(k, kalici(k));
      return yanit(req, env, { hata: "kod_yanlis", kalan_deneme: AZAMI_KOD_DENEME - k.kod_deneme }, 400);
    }
    k.kod_ozeti = null; k.tel_dogrulandi = true;
    if (k.durum === "onayli") await kv.put(`${P}t:${await sha256(k.telefon)}`, k.id); // kalıcı
    else await kv.put(`${P}t:${await sha256(k.telefon)}`, k.id, { expirationTtl: KONTROL_GUN * 86400 });
    await kayitYaz(k, 0);
    const tok = [...crypto.getRandomValues(new Uint8Array(32))].map((x) => x.toString(16).padStart(2, "0")).join("");
    const oh = await sha256(tok);
    await kv.put(`${P}oturum:${oh}`, k.id, { expirationTtl: OTURUM_TTL });
    const ot = (await kvJson(kv, `${P}ot:${k.id}`)) || [];
    ot.push(oh);
    await kv.put(`${P}ot:${k.id}`, JSON.stringify(ot.slice(-10)), { expirationTtl: OTURUM_TTL });
    return yanit(req, env, { durum: k.durum, oturum: tok, ad_soyad: k.ad_soyad, il: k.il, ilce: k.ilce, gorev_yeri: k.gorev_yeri, unvan: k.unvan ?? null });
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
      basvuran: { ad_soyad: k.ad_soyad, telefon: k.telefon, yakinlik: "din görevlisi" } };
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
  const aktifHesap = (k) => k && k.durum === "onayli" && k.tel_dogrulandi === true; // panel/ilan yalnız onaylı hesaba

  async function ilan() {
    const k = await hesap();
    if (!aktifHesap(k)) return yanit(req, env, { hata: "yetkisiz", durum: k ? k.durum : null }, k ? 403 : 401);
    const g = await govde();
    if (g.hata) return yanit(req, env, { hata: g.hata }, g.durum);
    const gs = `${P}gs:${k.id}:${gun}`;
    const n = parseInt((await kv.get(gs)) || "0", 10);
    if (n >= GUNLUK_ILAN) return yanit(req, env, { durum: "red", neden: "günlük ilan sınırı" }, 429);
    const r = await ilanDegerlendir(k, g.json || {}, null); // il/ilçe istekten ALINMAZ: kayıttan
    if (r.neden) return yanit(req, env, { durum: "red", neden: r.neden });
    const t = r.t, id = rastgeleId();
    const yayinda = true; // aktifHesap yalnız onaylı hesaba izin verir
    const rec = {
      id, il: k.il, ilce: k.ilce, mahalle: t.mahalle ?? null, koy: t.koy ?? null, gorev_yeri: k.gorev_yeri, ad_soyad: t.ad_soyad, cinsiyet: t.cinsiyet, yas: t.yas ?? null,
      vefat_tarihi: t.vefat_tarihi, namaz_tarihi: t.namaz_tarihi, namaz_yeri_vakti: t.namaz_yeri_vakti ?? null, defin_yeri: t.defin_yeri ?? null,
      sehit: t.sehit === true, rutbe: t.rutbe ?? null, toren: t.toren_yeri ?? null, duyuru_url: t.duyuru_url ?? null,
      liste_tarihi: t.namaz_tarihi, gorevli: true, dogrulandi: k.durum === "onayli", durum: yayinda ? "yayinda" : "bekliyor",
      kayit_id: k.id, olusturma: o.now.toISOString(),
    };
    await ilanYaz(rec);
    await kv.put(`${P}h:${k.id}:${id}`, "1", { expirationTtl: ILAN_TTL });
    await dizinYaz(r.slug, id, t);
    if (gozetimde(k)) await kv.put(`${P}g:${id}`, "1", { expirationTtl: 8 * 86400 });
    await kv.put(gs, String(n + 1), { expirationTtl: 90000 });
    return yanit(req, env, { durum: rec.durum, ilan_id: id });
  }

  async function ilanlarim() {
    const k = await hesap();
    if (!k || k.tel_dogrulandi !== true || !GIRIS_DURUMLARI.includes(k.durum)) return yanit(req, env, { hata: "yetkisiz" }, k ? 403 : 401);
    const l = k.durum === "onayli" ? await hesapIlanlari(k) : []; // "kontrolde": panel açık, liste boş

    return yanit(req, env, { hesap: { durum: k.durum, il: k.il, ilce: k.ilce, gorev_yeri: k.gorev_yeri, unvan: k.unvan ?? null, ad_soyad: k.ad_soyad }, ilanlar: l.map((i) => ({ ...genelGorevli(i), durum: i.durum })) });
  }
  // GET /gorevli/durum — uygulama her açılışta sorar: "kontrolde" iken panel kapalı, "onayli" olunca açılır
  async function ben() {
    if ((await oturumKid()) === "RED") return yanit(req, env, { durum: "silindi" }); // sahibi reddetti: hesap silindi
    const k = await hesap();
    if (!k) return yanit(req, env, { hata: "yetkisiz" }, 401);
    return yanit(req, env, { telefon_dogrulandi: k.tel_dogrulandi === true, durum: k.durum, ad_soyad: k.ad_soyad, il: k.il, ilce: k.ilce, gorev_yeri: k.gorev_yeri, unvan: k.unvan ?? null, ilan_sayisi: undefined });
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
      await kv.delete(`${P}t:${await sha256(k.telefon)}`);
      await kv.delete(`${P}ac:${katla(k.ad_soyad)}|${katla(k.gorev_yeri)}`);
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
      case "/gorevli/kayit": return kayit();
      case "/gorevli/kod": return kodIste(false);
      case "/gorevli/giris": return kodIste(true);
      case "/gorevli/dogrula": return dogrula();
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
