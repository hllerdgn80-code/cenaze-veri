// Görev yeri <-> ilanın camisi/mahallesi eşleşmesi (URUN §49a). AYNI MANTIK: okuyucu/ortak.py (yer_eslesir) ve uygulama/lib/cekirdek/yer_eslesme.dart.
const EK = new Set(["camii", "camisi", "cami", "mescidi", "mescit", "mahallesi", "mahalle", "mah", "koyu", "koy"]);
const GENEL = new Set(["merkez", "yeni", "eski", "ulu", "buyuk", "kucuk", "orta", "asagi", "yukari", "cumhuriyet", "ilce", "belediye"]);
const TR = { "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u" };

export function yerSade(s) {
  let t = String(s ?? "").replace(/İ/g, "i").replace(/I/g, "ı").toLowerCase();
  t = t.replace(/[çğıöşüâîû]/g, (c) => TR[c]);
  return t.replace(/[^a-z0-9]+/g, " ").split(" ").filter((w) => w && !EK.has(w)).join(" ");
}

export function namazCami(nyv) {
  const s = String(nyv ?? "");
  const i = s.indexOf("-");
  return i < 0 ? "" : s.slice(i + 1).trim();
}

export function yerEslesir(gorevYeri, cami, mahalle, haric) {
  const g = yerSade(gorevYeri).split(" ").filter(Boolean);
  if (!g.length) return false;
  const yasak = new Set(haric ? yerSade(haric).split(" ").filter(Boolean) : []);
  const son = (x, y) => x.length <= y.length && y.slice(y.length - x.length).join(" ") === x.join(" ");
  for (const aday of [cami, mahalle]) {
    const a = yerSade(aday).split(" ").filter(Boolean);
    if (!a.length) continue;
    if (son(a, g) || son(g, a)) return true;
    if ([...new Set(g)].some((w) => w.length >= 4 && a.includes(w) && !GENEL.has(w) && !yasak.has(w))) return true;
  }
  return false;
}
