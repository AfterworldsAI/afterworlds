import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

function listSourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...listSourceFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

describe("API client is the single request path", () => {
  it("no component calls fetch() directly outside api/client.ts", () => {
    const clientPath = join(__dirname, "api", "client.ts");
    const offenders = listSourceFiles(__dirname)
      .filter(
        (f) =>
          f !== clientPath &&
          !f.endsWith(".test.ts") &&
          !f.endsWith(".test.tsx"),
      )
      .filter((f) => /\bfetch\s*\(/.test(readFileSync(f, "utf-8")));
    expect(offenders).toEqual([]);
  });
});
