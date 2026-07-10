#!/usr/bin/env node
// Round 12 remediation (PR #126 P2): a fixed repo-local `_e2e.db` was shared
// across every local run -- entitlement seeded by one run (or left behind by
// a prior failed/partial run) leaked into the next, invalidating the "fresh
// install, no runnable access path" scenario regardless of test order.
//
// Playwright reloads playwright.config.ts once per worker process, so
// computing the per-run database path directly at the top of that file
// (tried first) produces a *different* temp directory in the webServer's
// process than in each test worker's process -- every module evaluation
// re-runs mkdtempSync independently. Computing it here instead, once, in
// the process that spawns `playwright test` as a child, guarantees every
// descendant process (webServer, every worker) inherits the exact same
// values via normal OS process-env inheritance, not Playwright's internal
// config/lifecycle ordering.
import { spawnSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const e2eRunDir = mkdtempSync(join(tmpdir(), "afterworlds-e2e-"));

// shell:true is required on Windows to resolve `npx` (a .cmd shim), but
// Node does not reliably re-quote array-form args for the shell it spawns
// -- an arg containing a space (e.g. a --grep pattern) silently split into
// two argv entries. Building one pre-quoted command string is the
// documented-safe pattern for shell:true instead.
const args = ["playwright", "test", ...process.argv.slice(2)];
const quotedArgs = args.map((arg) => (/\s/.test(arg) ? `"${arg}"` : arg));
const command = `npx ${quotedArgs.join(" ")}`;

const result = spawnSync(command, {
  stdio: "inherit",
  shell: true,
  env: {
    ...process.env,
    AFTERWORLDS_DATABASE_URL: `sqlite:///${join(e2eRunDir, "e2e.db")}`,
    AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY: join(e2eRunDir, "chroma"),
  },
});

process.exit(result.status ?? 1);
