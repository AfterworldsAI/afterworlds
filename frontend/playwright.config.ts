import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { defineConfig } from "@playwright/test";

/**
 * DoR-B: the minimal-spine E2E suite runs against the BUILT app (FastAPI
 * serving frontend/dist -- the product configuration, not `vite dev`), with
 * faked provider passes so default CI never makes a real Anthropic call.
 */

// Round 12 remediation (PR #126 P2): a fixed repo-local `_e2e.db` was shared
// across every local run -- entitlement seeded by one run (or left behind by
// a prior failed/partial run) leaked into the next, invalidating the "fresh
// install, no runnable access path" scenario regardless of test order.
//
// Single source of truth for the per-run database path is
// `e2e/run-isolated.mjs` (the supported entry point, `npm run e2e`): it
// computes one unique temp directory and passes it down as
// AFTERWORLDS_DATABASE_URL / AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY before
// spawning `playwright test` as a child process, so the webServer and every
// test worker -- all descendants of that one process -- inherit the exact
// same values. Computing the path directly in *this* file would not work:
// Playwright reloads playwright.config.ts once per worker process, so a
// top-level mkdtempSync() here produces a different directory per worker
// than the one the webServer process got.
//
// This fallback only fires for the unsupported direct-invocation path
// (`npx playwright test`, bypassing the wrapper) -- it is best-effort, not
// guaranteed-consistent across workers, since each worker's config
// evaluation would compute its own path independently.
function fallbackE2eDir(): string {
  return mkdtempSync(join(tmpdir(), "afterworlds-e2e-"));
}

let databaseUrl = process.env.AFTERWORLDS_DATABASE_URL;
let retrievalPersistDirectory =
  process.env.AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY;
if (!databaseUrl || !retrievalPersistDirectory) {
  const dir = fallbackE2eDir();
  databaseUrl = `sqlite:///${join(dir, "e2e.db")}`;
  retrievalPersistDirectory = join(dir, "chroma");
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // single uvicorn worker product config (Binding Decision 8)
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "python -m uvicorn afterworlds.main:app --host 127.0.0.1 --port 8000",
    cwd: "..",
    url: "http://127.0.0.1:8000/api/health",
    reuseExistingServer: false,
    timeout: 30_000,
    env: {
      PYTHONPATH: "src",
      AFTERWORLDS_DATABASE_URL: databaseUrl,
      AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY: retrievalPersistDirectory,
      AFTERWORLDS_FRONTEND_DIST: "./frontend/dist",
      AFTERWORLDS_FAKE_PROVIDER: "1",
      AFTERWORLDS_CI: "1",
    },
  },
});
