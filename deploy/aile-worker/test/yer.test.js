// URUN §49a: görev yeri <-> cami/mahalle eşleşmesi (Python ve Dart testleriyle AYNI 12 örnek). node --test test/*.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { yerEslesir, yerSade, namazCami } from "../src/yer.js";

const ORNEK = [
  ["Korgan Merkez Camii", "MERKEZ CAMİİ", null, null, true],
  ["Çitlice Camii", null, "Çitlice", null, true],
  ["Çitlice Camii", "Merkez Camii", null, null, false],
  ["Çitlice Camii", "Merkez Camii", "Çitlice Mahallesi", null, true],
  ["", "Merkez Camii", "Merkez", null, false],
  ["Çitlice Camii", null, null, null, false],
  ["Merkez Camii", "Korgan Merkez Camii", null, null, true],
  ["Ordu Merkez Camii", "Korgan Merkez Camii", null, null, false],
  ["Ulu Camii", "Yeni Camii", null, null, false],
  ["Tepe Köyü", "", "TEPE KÖYÜ", null, true],
  ["Çitlice Camii", "Çitlik Camii", null, null, false],
  ["Korgan Çitlice Camii", "Korgan Merkez Camii", null, "Korgan", false],
];
test("yerEslesir 12 örnek", () => {
  for (const [g, c, m, h, bek] of ORNEK) assert.equal(yerEslesir(g, c, m, h), bek, JSON.stringify([g, c, m, h]));
  assert.equal(yerEslesir("Korgan Çitlice Camii", "Korgan Merkez Camii", null), true);
  assert.equal(yerSade("ÇİTLİCE MAHALLESİ"), "citlice");
  assert.equal(yerSade("Mah. Ortaköy Camisi"), "ortakoy");
  assert.equal(namazCami("ÖĞLE NAMAZINDAN SONRA - MERKEZ CAMİİ"), "MERKEZ CAMİİ");
  assert.equal(namazCami("Öğle"), "");
});
