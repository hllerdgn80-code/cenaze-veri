// Diyanet personel kartı denetimi — TÜM eşikler ve sabitler BU DOSYADA (gerçek kart örneği gelince burası ayarlanır). Saf fonksiyonlar, ağ yok.
// Karar (site sahibi 15.10.2026, §37 ek-4; kâğıttaki kod 15.10 akşam KALDIRILDI): 1 ibare, 2 ad-soyad, 3 unvan, 6 fiziksel kart ZORUNLU; 4 il/ilçe ve 5 sicil varsa puan, yoksa uyarı notu.
// Fotoğraf yalnız uygulama içi kameradan gelir (galeri yok); bu kural istemcidedir, sunucu `fiziksel_kart` kontrolüyle ekran görüntüsü/düz metni eler.
import { katla } from "./kurallar.js";

export const OCR_MODEL = "@cf/meta/llama-3.2-11b-vision-instruct";
export const OCR_MAX_TOKEN = 600;

export const DIYANET_IBARESI = "diyanet"; // katla'lı metinde aranır (DİYANET İŞLERİ BAŞKANLIĞI)
export const KART_TURU_IBARELERI = ["personel kimlik karti", "gorev kimlik karti"]; // katla'lı
export const KART_TURU_ZORUNLU = true; // false yapılırsa yalnız DİYANET ibaresi yeter
export const UNVANLAR = ["Cami İmam-Hatibi", "İmam-Hatip", "Müezzin-Kayyım", "Kur'an Kursu Öğreticisi", "Vaiz", "Müftü", "Müftü Yardımcısı", "Din Hizmetleri Uzmanı", "Şube Müdürü"];
export const UNVAN_KATLA = UNVANLAR.map((u) => katla(u));
export const PUAN = { il: 1, sicil: 1 };

// Modele TEK istekte sorulur; kayıttaki ad/kod isteme YAZILMAZ (model uydurmasın)
export const ISTEM = `Bu fotoğraf bir personel kimlik kartı olabilir. Yalnızca geçerli JSON döndür, başka metin yazma. Alanlar:
"metin": kartta görünen TÜM yazılar, satır satır, olduğu gibi. Okunmayanı uydurma.
"diyanet_ibaresi": kartta "T.C. DİYANET İŞLERİ BAŞKANLIĞI" yazıyor mu (true/false)
"kart_turu_ibaresi": kartta "PERSONEL KİMLİK KARTI" ya da "GÖREV KİMLİK KARTI" yazıyor mu (true/false)
"ad_soyad": kartta yazan ad ve soyad
"unvan": kartta yazan unvan
"il_ilce_kurum": kartta il, ilçe ya da kurum adı yazıyorsa o metin, yoksa null
"sicil_var": kartta sicil ya da kurum sicil numarası alanı ve bir rakam dizisi var mı (true/false; rakamı YAZMA)
"fiziksel_kart": bu gerçek, fiziksel bir plastik kartın fotoğrafı mı; üzerinde logo ve vesikalık fotoğraf var mı; ekran görüntüsü, ekrandan çekim ya da düz metin DEĞİL mi (true/false)`;

// 11 haneli rakam dizileri (TC) OCR metninde görülürse maskelenir: yanıta/loga/kayda hiçbir yolla yazılmaz (zaten hiçbiri saklanmıyor)
export const tcMaskele = (t) => String(t ?? "").replace(/(?<!\d)(?:\d[\s.\-]?){10}\d(?!\d)/g, "***********");
export function yanitCoz(ham) {
  const s = tcMaskele(ham);
  const a = s.indexOf("{"), b = s.lastIndexOf("}");
  if (a >= 0 && b > a) {
    try { const j = JSON.parse(s.slice(a, b + 1)); if (j && typeof j === "object") return { ...j, metin: String(j.metin ?? s) }; } catch { /* düz metin */ }
  }
  return { metin: s }; // JSON gelmediyse: ham metin; bool alanlar yok -> fiziksel_kart belirsiz -> ret/kuyruk
}

export function adEslesir(metin, adSoyad) {
  const t = " " + katla(metin) + " ";
  const w = katla(adSoyad).split(" ").filter((x) => x.length >= 2);
  return w.length >= 2 && w.every((x) => t.includes(x));
}
// k: {ad_soyad, il, ilce}. Döner {gecti, nedenler[], puan, uyarilar[]}. Fotoğraf/değer saklanmaz: sicil yalnız bool.
export function kartKarar(y, k) {
  const metin = String(y.metin ?? "");
  const t = " " + katla(metin) + " ";
  const nedenler = [], uyarilar = [];
  let puan = 0;
  const diyanet = t.includes(DIYANET_IBARESI);
  const turu = KART_TURU_IBARELERI.some((x) => t.includes(x));
  if (!diyanet) nedenler.push("diyanet_ibaresi_yok");
  else if (KART_TURU_ZORUNLU && !turu) nedenler.push("kart_turu_ibaresi_yok");
  if (!adEslesir(metin, k.ad_soyad)) nedenler.push("ad_soyad_uyusmuyor");
  const unvanMetni = " " + katla(`${y.unvan ?? ""} ${metin}`) + " ";
  if (!UNVAN_KATLA.some((u) => unvanMetni.includes(" " + u + " "))) nedenler.push("unvan_tanimsiz");
  if (y.fiziksel_kart !== true) nedenler.push("fiziksel_kart_degil_ya_da_belirsiz");
  const ilMetni = y.il_ilce_kurum ? katla(y.il_ilce_kurum) : "";
  if (!ilMetni) uyarilar.push("kartta_il_ilce_yok");
  else if (ilMetni.includes(katla(k.il)) || (k.ilce && k.ilce !== "Merkez" && ilMetni.includes(katla(k.ilce)))) puan += PUAN.il;
  else uyarilar.push("kart_il_ilce_uyumsuz");
  if (y.sicil_var === true) puan += PUAN.sicil; else uyarilar.push("sicil_alani_yok");
  return { gecti: nedenler.length === 0, nedenler, puan, uyarilar };
}
