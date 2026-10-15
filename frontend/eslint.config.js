import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "src/api/schema.ts"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
  {
    // CRD Issue 19b: dice-core stays pure -- no imports beyond itself, no
    // browser or storage globals, no ambient randomness, no dynamic code.
    files: ["src/dice-core/**/*.ts"],
    ignores: ["src/dice-core/**/*.test.ts"],
    rules: {
      "no-restricted-imports": ["error", { patterns: ["*", "!./*"] }],
      "no-restricted-globals": [
        "error",
        "window",
        "document",
        "self",
        "globalThis",
        "navigator",
        "crypto",
        "localStorage",
        "sessionStorage",
        "fetch",
      ],
      "no-restricted-properties": [
        "error",
        { object: "Math", property: "random" },
      ],
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
    },
  },
);
