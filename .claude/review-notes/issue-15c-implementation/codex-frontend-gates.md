# CRD Issue 15c frontend local gates (2026-10-13)

Scope: unchanged frontend and CI workflow relative to `e83018c`. No tracked frontend files were edited. This is a reusable local signal for unchanged inputs; final-head CI remains required.

- Root `.nvmrc`: Node 22. Active local runtime: Node v25.4.0, npm 11.7.0. This does not match the pinned CI runtime or frontend engine `>=22 <23`.
- Existing `frontend/node_modules` was present; `npm ls --depth=0 --all=false` exited 0. No packages were installed or updated.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0.
- `npm run format:check`: exit 0.
- `npm run test`: initial exit 1 before test collection because Vitest could not rename a temporary cache file in the sandbox (`EPERM`). Retry with `TEMP`, `TMP`, and `TMPDIR` set under this gate log directory: exit 0, six files and 45 tests passed.
- `npm run build`: exit 0.
- `npm audit --audit-level=high`: exit 1 because DNS lookup of `registry.npmjs.org` failed in the sandbox. A network-enabled retry was rejected by automatic approval review: the audit would send project dependency metadata to the external npm registry without direct user authorization. Audit status is unknown, not a vulnerability finding.
- OpenAPI type drift and E2E were not run because they depend on final-head schema or app launch. No backend gate was run.

Input proof: `tracked-before.tsv` and `tracked-after.tsv` contain SHA-256 hashes for all 30 tracked frontend files and are identical. `git diff --exit-code e83018c -- frontend .github/workflows/ci.yml` exited 0 after the gates; `git status --short -- frontend .github/workflows/ci.yml` was empty. Raw gate logs are in `../issue-15c-preparation/frontend-overnight-gates/`.

Limits: these passes used unsupported local Node 25, so the Node 22 CI run remains authoritative. Dependency audit needs authorized registry access or CI.

