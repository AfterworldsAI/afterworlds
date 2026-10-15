/**
 * dice-core (CRD Issue 19b): generic dice math, no RPG rules.
 *
 * Pure TypeScript -- no React, browser, backend or storage dependency (the
 * ESLint override for this directory enforces it). Randomness is injected as
 * a source of uniform 32-bit words; the browser adapter lives outside.
 *
 * Two distinct inputs:
 * - backend structured terms (`DiceTerm`), executed as given -- the live
 *   pending-roll path. Bounds mirror the backend's (1-100 dice, 2-1000 sides).
 * - a narrow text grammar (`parseExpression`): `NdM` for d4/d6/d8/d10/d12/
 *   d20/d100, integer constants, `+` and `-`. It never parses a pending
 *   roll's display expression and never limits structured terms.
 *
 * Every result here is a non-authoritative preview: the backend derives
 * selections, totals and outcomes itself.
 */

export type SelectionRule = "sum_all" | "keep_highest" | "keep_lowest";
export type Contribution = "add" | "subtract";

/** Structurally the backend's player-visible roll term. */
export interface DiceTerm {
  term_id: string;
  count: number;
  sides: number;
  selection_rule: SelectionRule;
  keep_count?: number | null;
  contribution: Contribution;
}

/** Returns a uniform integer in [0, 2^32). */
export type Uint32Source = () => number;

export class DiceError extends Error {}

export const TERM_LIMITS = {
  minDice: 1,
  maxDice: 100,
  minSides: 2,
  maxSides: 1000,
};
export const TEXT_LIMITS = {
  maxLength: 100,
  maxPools: 10,
  maxDicePerPool: 100,
  maxTotalDice: 100,
  sides: [4, 6, 8, 10, 12, 20, 100] as readonly number[],
};

const WORD = 2 ** 32;
const MAX_REJECTIONS = 64;

/** One face of a `sides`-sided die, by rejection sampling (no modulo bias). */
export function drawFace(next: Uint32Source, sides: number): number {
  const limit = WORD - (WORD % sides);
  for (let attempt = 0; attempt < MAX_REJECTIONS; attempt++) {
    const word = next();
    if (!Number.isInteger(word) || word < 0 || word >= WORD) {
      throw new DiceError("The random source returned an invalid value.");
    }
    if (word < limit) return (word % sides) + 1;
  }
  throw new DiceError("The random source kept returning rejected values.");
}

function isIntIn(value: unknown, min: number, max: number): value is number {
  return (
    Number.isSafeInteger(value) &&
    (value as number) >= min &&
    (value as number) <= max
  );
}

/** Throws a DiceError for anything the backend would not have issued. */
export function validateTerms(terms: readonly DiceTerm[]): void {
  if (terms.length === 0) throw new DiceError("No dice to roll.");
  const ids = new Set<string>();
  for (const term of terms) {
    if (ids.has(term.term_id)) throw new DiceError("Repeated term id.");
    ids.add(term.term_id);
    if (!isIntIn(term.count, TERM_LIMITS.minDice, TERM_LIMITS.maxDice)) {
      throw new DiceError("Unsupported dice count.");
    }
    if (!isIntIn(term.sides, TERM_LIMITS.minSides, TERM_LIMITS.maxSides)) {
      throw new DiceError("Unsupported die size.");
    }
    if (term.contribution !== "add" && term.contribution !== "subtract") {
      throw new DiceError("Unsupported contribution.");
    }
    if (term.selection_rule === "sum_all") {
      if (term.keep_count != null)
        throw new DiceError("Unexpected keep count.");
    } else if (
      term.selection_rule === "keep_highest" ||
      term.selection_rule === "keep_lowest"
    ) {
      if (!isIntIn(term.keep_count, 1, term.count)) {
        throw new DiceError("Unsupported keep count.");
      }
    } else {
      throw new DiceError("Unsupported selection rule.");
    }
  }
}

/** Every raw face of every term, in term order. */
export function rollTerms(
  terms: readonly DiceTerm[],
  next: Uint32Source,
): number[][] {
  validateTerms(terms);
  return terms.map((term) =>
    Array.from({ length: term.count }, () => drawFace(next, term.sides)),
  );
}

/** Kept dice indexes in roll order; ties keep the earlier die (as the backend). */
export function keptIndexes(
  values: readonly number[],
  term: DiceTerm,
): number[] {
  if (term.selection_rule === "sum_all") return values.map((_, i) => i);
  const high = term.selection_rule === "keep_highest";
  const order = values
    .map((_, i) => i)
    .sort(
      (a, b) =>
        (high ? values[b]! - values[a]! : values[a]! - values[b]!) || a - b,
    );
  return order.slice(0, term.keep_count ?? 0).sort((a, b) => a - b);
}

export interface TermScore {
  term_id: string;
  values: number[];
  kept: boolean[];
  /** Sum of the kept faces with the term's sign applied. */
  subtotal: number;
}

export interface Scorecard {
  terms: TermScore[];
  modifierTotal: number;
  total: number;
}

/** The preview: signed term subtotals plus the visible modifier total, once. */
export function score(
  terms: readonly DiceTerm[],
  values: readonly (readonly number[])[],
  modifierTotal: number,
): Scorecard {
  validateTerms(terms);
  if (values.length !== terms.length || !Number.isSafeInteger(modifierTotal)) {
    throw new DiceError("Values do not match the terms.");
  }
  let total = modifierTotal;
  const scored = terms.map((term, t) => {
    const faces = [...values[t]!];
    if (
      faces.length !== term.count ||
      !faces.every((v) => isIntIn(v, 1, term.sides))
    ) {
      throw new DiceError("Values do not match the terms.");
    }
    const keep = new Set(keptIndexes(faces, term));
    const sum = faces.reduce((acc, v, i) => (keep.has(i) ? acc + v : acc), 0);
    const subtotal = term.contribution === "subtract" ? -sum : sum;
    total += subtotal;
    return {
      term_id: term.term_id,
      values: faces,
      kept: faces.map((_, i) => keep.has(i)),
      subtotal,
    };
  });
  return { terms: scored, modifierTotal, total };
}

export type FaceListResult =
  { ok: true; values: number[] } | { ok: false; error: string };

/**
 * Faces typed by a Sojourner for one term: whole numbers separated by spaces
 * or commas, exactly `count` of them, each in [1, sides]. Nothing is coerced
 * ("1.0", "0x3", "1e1", "+3" are refused, not read as faces).
 */
export function parseFaceList(
  text: string,
  count: number,
  sides: number,
): FaceListResult {
  const tokens = text.split(/[\s,]+/).filter(Boolean);
  if (!tokens.every((token) => /^[0-9]+$/.test(token))) {
    return { ok: false, error: "Enter whole numbers only." };
  }
  const values = tokens.map((token) => Number(token));
  if (values.length !== count) {
    return {
      ok: false,
      error: `Enter exactly ${count} ${count === 1 ? "face" : "faces"}.`,
    };
  }
  if (!values.every((v) => isIntIn(v, 1, sides))) {
    return { ok: false, error: `Each face must be from 1 to ${sides}.` };
  }
  return { ok: true, values };
}

export interface TextExpression {
  terms: DiceTerm[];
  constant: number;
}

const SIGN = /\s*([+-])\s*/y;
const ITEM = /(?:(\d+)d(\d+)|(\d+))/y;

/** Parses the bounded text grammar; throws a DiceError for anything else. */
export function parseExpression(text: string): TextExpression {
  if (text.length > TEXT_LIMITS.maxLength)
    throw new DiceError("Expression too long.");
  const terms: DiceTerm[] = [];
  let constant = 0;
  let dice = 0;
  let pos = text.length - text.trimStart().length;
  const end = text.trimEnd().length;
  if (pos >= end) throw new DiceError("Empty expression.");
  let first = true;
  while (pos < end) {
    let sign: "+" | "-" = "+";
    SIGN.lastIndex = pos;
    const s = SIGN.exec(text);
    if (s) {
      sign = s[1] as "+" | "-";
      pos = SIGN.lastIndex;
    } else if (!first) {
      throw new DiceError("Expected + or -.");
    }
    ITEM.lastIndex = pos;
    const m = ITEM.exec(text);
    if (!m) throw new DiceError("Expected NdM or a whole number.");
    pos = ITEM.lastIndex;
    if (m[3] !== undefined) {
      const value = Number(m[3]);
      constant += sign === "-" ? -value : value;
      if (!Number.isSafeInteger(value) || !Number.isSafeInteger(constant)) {
        throw new DiceError("Number too large.");
      }
    } else {
      const count = Number(m[1]);
      const sides = Number(m[2]);
      if (!TEXT_LIMITS.sides.includes(sides))
        throw new DiceError("Unsupported die size.");
      if (!isIntIn(count, 1, TEXT_LIMITS.maxDicePerPool)) {
        throw new DiceError("Unsupported dice count.");
      }
      dice += count;
      if (
        terms.length === TEXT_LIMITS.maxPools ||
        dice > TEXT_LIMITS.maxTotalDice
      ) {
        throw new DiceError("Too many dice.");
      }
      terms.push({
        term_id: `text-${terms.length + 1}`,
        count,
        sides,
        selection_rule: "sum_all",
        contribution: sign === "-" ? "subtract" : "add",
      });
    }
    first = false;
  }
  return { terms, constant };
}

/** Rolls a text expression (the grammar above) to a preview scorecard. */
export function rollExpression(text: string, next: Uint32Source): Scorecard {
  const { terms, constant } = parseExpression(text);
  if (terms.length === 0)
    return { terms: [], modifierTotal: constant, total: constant };
  return score(terms, rollTerms(terms, next), constant);
}
