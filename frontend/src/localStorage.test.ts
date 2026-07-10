import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { localStorageState } from "./localStorage";

function listSourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      if (entry === "api") continue; // generated/client module, not app code
      out.push(...listSourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

describe("permitted-localStorage allowlist", () => {
  it("localStorage is touched only inside localStorage.ts", () => {
    const offenders = listSourceFiles(__dirname)
      .filter(
        (f) =>
          !f.endsWith("localStorage.ts") &&
          !f.endsWith(".test.ts") &&
          !f.endsWith(".test.tsx"),
      )
      .filter((f) => readFileSync(f, "utf-8").includes("localStorage."));
    expect(offenders).toEqual([]);
  });

  it("round-trips draft text per story", () => {
    localStorageState.setDraft("story-1", "hello");
    expect(localStorageState.getDraft("story-1")).toBe("hello");
    localStorageState.setDraft("story-1", "");
    expect(localStorageState.getDraft("story-1")).toBe("");
  });

  it("round-trips last-selected story id", () => {
    localStorageState.setLastStoryId("story-42");
    expect(localStorageState.getLastStoryId()).toBe("story-42");
  });
});
