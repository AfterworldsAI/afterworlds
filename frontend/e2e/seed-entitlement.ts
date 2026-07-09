import { execFileSync } from "node:child_process";

/**
 * Grants hosted entitlement for the local Sojourner against the E2E-only
 * sqlite file (see playwright.config.ts's webServer env and
 * scripts/seed_e2e_entitlement.py). Called only by the specific spine tests
 * that need a runnable access path (DELIVERED / INTERACTION_REJECTED
 * rendering) -- other tests deliberately run without it, so the
 * entitlement-blocked path is exercised the same way a fresh install would
 * hit it (production create_app() never auto-grants entitlement).
 *
 * Round 12 remediation (PR #126 P2): reads `AFTERWORLDS_DATABASE_URL` from
 * the environment instead of duplicating the `sqlite:///./_e2e.db` literal
 * -- playwright.config.ts is the single source of truth for the per-run
 * database path (a unique temp directory, not a fixed repo-local file), and
 * test worker processes inherit the env vars it sets on `process.env`.
 */
export function seedEntitlement(): void {
  const dbUrl = process.env.AFTERWORLDS_DATABASE_URL;
  if (!dbUrl) {
    throw new Error(
      "AFTERWORLDS_DATABASE_URL is not set -- seedEntitlement() must run" +
        " under Playwright, which computes it in playwright.config.ts.",
    );
  }
  execFileSync(
    "python",
    ["scripts/seed_e2e_entitlement.py", "--db-url", dbUrl],
    { cwd: "..", stdio: "inherit" },
  );
}
