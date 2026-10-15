import { describe, expect, it } from "vitest";

import {
  DiceError,
  drawFace,
  keptIndexes,
  parseExpression,
  parseFaceList,
  rollExpression,
  rollTerms,
  score,
  validateTerms,
} from ".";
import type { DiceTerm, Uint32Source } from ".";

const WORD = 2 ** 32;

/** Deterministic words, then a failure if the code asks for more. */
function words(...values: number[]): Uint32Source {
  return () => {
    if (values.length === 0) throw new Error("source exhausted");
    return values.shift()!;
  };
}

/** Words that land on the given faces for a die of `sides` (face - 1). */
function facesOf(...faces: number[]): Uint32Source {
  return words(...faces.map((f) => f - 1));
}

function term(over: Partial<DiceTerm> = {}): DiceTerm {
  return {
    term_id: "t1",
    count: 1,
    sides: 20,
    selection_rule: "sum_all",
    contribution: "add",
    ...over,
  };
}

describe("drawFace", () => {
  it("maps words to faces without modulo bias by rejecting the uneven tail", () => {
    // 2^32 % 6 === 4: the last four words would favour faces 1-4.
    const limit = WORD - (WORD % 6);
    expect(limit % 6).toBe(0);
    expect(drawFace(words(0), 6)).toBe(1);
    expect(drawFace(words(5), 6)).toBe(6);
    expect(drawFace(words(limit - 1), 6)).toBe(6);
    // Rejected words are skipped, never folded onto a face.
    expect(drawFace(words(limit, WORD - 1, 7), 6)).toBe(2);
    // A power of two has no tail.
    expect(drawFace(words(WORD - 1), 4)).toBe(4);
    expect(drawFace(words(WORD - 1, 999), 1000)).toBe(1000);
  });

  it("refuses invalid words and a source that only yields rejected words", () => {
    for (const bad of [-1, WORD, 1.5, Number.NaN]) {
      expect(() => drawFace(words(bad), 6)).toThrow(DiceError);
    }
    expect(() => drawFace(() => WORD - 1, 6)).toThrow(DiceError);
  });
});

describe("structured terms", () => {
  it("validates the backend bounds and keep rules without truncating", () => {
    expect(() =>
      validateTerms([term({ count: 100, sides: 1000 })]),
    ).not.toThrow();
    expect(() => validateTerms([term({ sides: 2 })])).not.toThrow();
    expect(() => validateTerms([term({ sides: 3 })])).not.toThrow();
    for (const bad of [
      term({ count: 0 }),
      term({ count: 101 }),
      term({ sides: 1 }),
      term({ sides: 1001 }),
      term({ count: 1.5 }),
      term({ keep_count: 1 }),
      term({ selection_rule: "keep_highest" }),
      term({ selection_rule: "keep_highest", count: 2, keep_count: 3 }),
      term({ selection_rule: "keep_lowest", count: 2, keep_count: 0 }),
      term({ contribution: "multiply" as never }),
      term({ selection_rule: "explode" as never }),
    ]) {
      expect(() => validateTerms([bad])).toThrow(DiceError);
    }
    expect(() => validateTerms([])).toThrow(DiceError);
    expect(() => validateTerms([term(), term()])).toThrow(DiceError);
  });

  it("rolls every raw face of every term, in order", () => {
    const terms = [
      term({
        term_id: "a",
        count: 2,
        sides: 20,
        selection_rule: "keep_highest",
        keep_count: 1,
      }),
      term({ term_id: "b", count: 3, sides: 6 }),
    ];
    expect(rollTerms(terms, facesOf(4, 17, 1, 2, 6))).toEqual([
      [4, 17],
      [1, 2, 6],
    ]);
  });

  it("keeps the highest or lowest, several at once, ties to the earlier die", () => {
    const four = term({
      count: 4,
      selection_rule: "keep_highest",
      keep_count: 2,
    });
    expect(keptIndexes([3, 6, 6, 1], four)).toEqual([1, 2]);
    expect(keptIndexes([6, 2, 6, 6], four)).toEqual([0, 2]);
    const low = term({
      count: 4,
      selection_rule: "keep_lowest",
      keep_count: 3,
    });
    expect(keptIndexes([5, 1, 1, 2], low)).toEqual([1, 2, 3]);
    expect(keptIndexes([2, 2, 2, 2], low)).toEqual([0, 1, 2]);
  });

  it("scores signed, mixed and repeated terms and adds the visible modifiers once", () => {
    const terms: DiceTerm[] = [
      term({
        term_id: "adv",
        count: 2,
        sides: 20,
        selection_rule: "keep_highest",
        keep_count: 1,
      }),
      term({ term_id: "d6a", count: 2, sides: 6 }),
      term({ term_id: "d6b", count: 1, sides: 6 }),
      term({
        term_id: "pen",
        count: 4,
        sides: 4,
        selection_rule: "keep_lowest",
        keep_count: 2,
        contribution: "subtract",
      }),
    ];
    const card = score(terms, [[4, 17], [3, 5], [6], [4, 1, 3, 2]], 3);
    expect(card.terms.map((t) => t.subtotal)).toEqual([17, 8, 6, -3]);
    expect(card.terms[0]!.kept).toEqual([false, true]);
    expect(card.terms[3]!.kept).toEqual([false, true, false, true]);
    expect(card.terms[3]!.values).toEqual([4, 1, 3, 2]); // every raw face
    expect(card.modifierTotal).toBe(3);
    expect(card.total).toBe(17 + 8 + 6 - 3 + 3);
  });

  it("refuses values that do not match the terms", () => {
    const terms = [term({ count: 2, sides: 6 })];
    for (const values of [
      [[1]],
      [[1, 7]],
      [[0, 1]],
      [[1, 2.5]],
      [[1, 2], [3]],
    ]) {
      expect(() => score(terms, values, 0)).toThrow(DiceError);
    }
    expect(() => score(terms, [[1, 2]], 0.5)).toThrow(DiceError);
  });
});

describe("parseFaceList (physical entry)", () => {
  it("accepts whole faces in range, exactly as many as the term rolls", () => {
    expect(parseFaceList("4, 17", 2, 20)).toEqual({
      ok: true,
      values: [4, 17],
    });
    expect(parseFaceList(" 3 ", 1, 6)).toEqual({ ok: true, values: [3] });
  });

  it("never coerces malformed input into a face", () => {
    for (const text of [
      "1.0",
      "0x3",
      "1e1",
      "+3",
      "-2",
      "3a",
      "Infinity",
      "½",
      "٣",
    ]) {
      expect(parseFaceList(text, 1, 20).ok).toBe(false);
    }
    expect(parseFaceList("", 1, 20).ok).toBe(false);
    expect(parseFaceList("1 2", 1, 20).ok).toBe(false);
    expect(parseFaceList("0", 1, 20).ok).toBe(false);
    expect(parseFaceList("21", 1, 20).ok).toBe(false);
    expect(parseFaceList("99999999999999999999", 1, 20).ok).toBe(false);
  });
});

describe("text grammar", () => {
  it("parses NdM pools, constants, plus and minus", () => {
    expect(parseExpression("1d20 + 5")).toEqual({
      terms: [term({ term_id: "text-1" })],
      constant: 5,
    });
    const parsed = parseExpression("-2d6+1d4-3+1d100");
    expect(parsed.constant).toBe(-3);
    expect(parsed.terms.map((t) => [t.count, t.sides, t.contribution])).toEqual(
      [
        [2, 6, "subtract"],
        [1, 4, "add"],
        [1, 100, "add"],
      ],
    );
    for (const sides of [4, 6, 8, 10, 12, 20, 100]) {
      expect(() => parseExpression(`1d${sides}`)).not.toThrow();
    }
  });

  it("rejects everything outside the grammar and its limits", () => {
    for (const text of [
      "",
      "   ",
      "d20",
      "1d3",
      "1d2",
      "1d1000",
      "2d20kh1",
      "4d6dl1",
      "1d6!",
      "adv",
      "1d20 adv",
      "2*3",
      "6/2",
      "(1d6)",
      "1d20 + ",
      "1d20 3",
      "--5",
      "1 d20",
      "0d6",
      "101d6",
      "60d6+50d6",
      "1d4+1d4+1d4+1d4+1d4+1d4+1d4+1d4+1d4+1d4+1d4",
      "1".repeat(20),
      "1d6+" + "1".repeat(101),
      "Math.random()",
      "1d6;alert(1)",
    ]) {
      expect(() => parseExpression(text), text).toThrow(DiceError);
    }
  });

  it("rolls a text expression to a preview", () => {
    expect(rollExpression("2d6 - 1", facesOf(3, 4))).toMatchObject({
      total: 6,
    });
    expect(rollExpression("7", words())).toMatchObject({ total: 7 });
  });
});
