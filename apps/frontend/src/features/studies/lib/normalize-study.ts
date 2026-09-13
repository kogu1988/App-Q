import type { Persona } from "../types";

/**
 * Study detay verisinin toleranslı okunması (refactor R1-2).
 *
 * Backend zaman içinde alan adlarını farklı biçimlerde (PascalCase/camelCase)
 * döndürebiliyor; UI'ı tek bir kanonik biçime indirgemek için buradaki
 * yardımcılar kullanılır. Hiçbir varsayılan veri üretilmez, yalnızca
 * mevcut değer normalize edilir.
 */

/** Büyük Beşli kanonik anahtarları. */
export type BigFiveKey =
  | "Openness"
  | "Conscientiousness"
  | "Extraversion"
  | "Agreeableness"
  | "Neuroticism";

export type BigFiveScores = Record<BigFiveKey, number>;

const BIG_FIVE_KEYS: BigFiveKey[] = [
  "Openness",
  "Conscientiousness",
  "Extraversion",
  "Agreeableness",
  "Neuroticism",
];

/** Tek bir kişilik özelliğini toleranslı okur; yoksa `fallback` döner. */
export function readTrait(
  raw: Record<string, number> | null | undefined,
  key: BigFiveKey,
  fallback = 50,
): number {
  if (!raw) return fallback;
  const lower = key.charAt(0).toLowerCase() + key.slice(1);
  const value = raw[key] ?? raw[lower];
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

/** Ham big_five nesnesini kanonik skorlara indirger. */
export function normalizeBigFive(
  raw: Record<string, number> | null | undefined,
  fallback = 50,
): BigFiveScores {
  return BIG_FIVE_KEYS.reduce((acc, key) => {
    acc[key] = readTrait(raw, key, fallback);
    return acc;
  }, {} as BigFiveScores);
}

/** Persona'nın Big Five verisi var mı (radar/çubuk gösterimi için). */
export function hasBigFive(persona: Persona | null | undefined): boolean {
  const raw = persona?.big_five;
  return !!raw && BIG_FIVE_KEYS.some(key => {
    const lower = key.charAt(0).toLowerCase() + key.slice(1);
    return typeof (raw[key] ?? raw[lower]) === "number";
  });
}
