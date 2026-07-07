import { execFileSync } from "node:child_process";

/**
 * Grants hosted entitlement for the local Sojourner against the E2E-only
 * sqlite file (see playwright.config.ts's webServer env and
 * scripts/seed_e2e_entitlement.py). Called only by the specific spine tests
 * that need a runnable access path (DELIVERED / INTERACTION_REJECTED
 * rendering) -- other tests deliberately run without it, so the
 * entitlement-blocked path is exercised the same way a fresh install would
 * hit it (production create_app() never auto-grants entitlement).
 */
export function seedEntitlement(): void {
  execFileSync(
    "python",
    ["scripts/seed_e2e_entitlement.py", "--db-url", "sqlite:///./_e2e.db"],
    { cwd: "..", stdio: "inherit" },
  );
}
