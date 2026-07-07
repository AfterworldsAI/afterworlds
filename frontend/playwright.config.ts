import { defineConfig } from "@playwright/test";

/**
 * DoR-B: the minimal-spine E2E suite runs against the BUILT app (FastAPI
 * serving frontend/dist -- the product configuration, not `vite dev`), with
 * faked provider passes so default CI never makes a real Anthropic call.
 */
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
      AFTERWORLDS_DATABASE_URL: "sqlite:///./_e2e.db",
      AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY: "./_e2e_chroma",
      AFTERWORLDS_FRONTEND_DIST: "./frontend/dist",
      AFTERWORLDS_FAKE_PROVIDER: "1",
      AFTERWORLDS_CI: "1",
    },
  },
});
