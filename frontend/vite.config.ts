/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // Dev proxy to FastAPI -- same-origin serving in the product
    // configuration, no CORS middleware needed (DoR-C).
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    // e2e/ is Playwright's own test.spec.ts suite (separate `test`/`expect`
    // globals, run via `npm run e2e`) -- exclude it from Vitest discovery.
    exclude: ["e2e/**", "node_modules/**"],
  },
});
