# PR #178 dependency-vulnerability disposition (9 October 2026)

On 9 October 2026 the Owner withdrew the after-restart dependency deferral: "Yep. I withdraw the
dependency deferral. Let's address them before the merge of PR #178." This note records the bounded
remediation. It is the Codex-reviewed additive correction to `d9b1532` delivered in this revision. Exact committed-head remote CI remains required; the PR records the subsequent gate disposition.
Merge, runtime publication or activation, shared-database writes and restart completion remain held.

Exact-head CI `37905287134` on `d9b1532` passed the backend, static, frontend
typecheck/lint/format/test and E2E steps. `npm audit` failed with 6 findings (2 moderate, 4 high), so
that job's OpenAPI drift check and production build were skipped. Both pass locally on the candidate
(below); those frontend-job steps require remote proof on the dependency head. The separate E2E job's
production build passed on `d9b1532`. The configured pip-audit passed with 5 findings
ignored. All results below are raw native audit output from disposable Linux (Node 22.22.2 / npm 10.9.7,
Python 3.12), checked against the official GitHub advisory records and PyPI.

## Frontend (`npm audit`, clean `npm ci` on the locked graph)

| Advisory (official) | Severity | Package and path | Vulnerable range, first patched | Before | After |
|---|---|---|---|---|---|
| GHSA-82fw-gwwq-j7x9 / CVE-2026-84373 | moderate | `vitest`, `@vitest/mocker` (direct dev) | `>=2.1.0 <4.1.11`, 4.1.11 | 4.1.10 | 4.1.11 |
| GHSA-q2hr-2g5m-vwhr / CVE-2026-102277 | moderate | `brace-expansion` (root override; `minimatch`, `@redocly/openapi-core`) | `>=4.0.0 <5.0.12`, 5.0.12 | 5.0.9 | 5.0.12 |
| GHSA-qhr7-859c-m2p7 / CVE-2026-102278 | high | same | `>=4.0.0 <5.0.11`, 5.0.11 | 5.0.9 | 5.0.12 |
| GHSA-6j4f-fj2g-mc7p / CVE-2026-102276 | high | same | `>=4.0.0 <5.0.10`, 5.0.10 | 5.0.9 | 5.0.12 |
| GHSA-68fv-2mgg-jv7q / CVE-2026-93749 | high | `source-map-js` (`vite` → `postcss`; new root override) | `>=1.0.0 <1.2.2`, 1.2.2 | 1.2.1 | 1.2.2 |

Before the change, the audit reported 6 vulnerabilities (exit 1). After it, `npm audit` and
`npm audit --audit-level=high` both report 0 (exit 0). `vitest`, `@vitest/mocker` and `source-map-js`
each have a single locked instance. `brace-expansion` has two patched instances: 5.0.12 at the root
and 2.1.7 under `@redocly/openapi-core` (see below).

Changes:

- `frontend/package.json` sets the `brace-expansion` override to 5.0.12, adds a `source-map-js` 1.2.2
  override, and sets `vitest` to `^4.1.11`. It also replaces the `@redocly/openapi-core` scoped
  override `minimatch: ^10` with `brace-expansion: 2.1.7` (see below).
- `frontend/package-lock.json` was regenerated rather than hand-edited. The vitest re-resolution also
  moved three packages within their existing ranges: `chai` 6.2.2 → 6.3.0, `tinyrainbow` 3.1.0 → 3.2.0
  and `@jridgewell/sourcemap-codec` 1.5.5 → 1.6.0.
- The audit threshold is unchanged, and `npm audit fix --force` was not used.

npm 10.9.7 crashes while re-resolving vitest ("Cannot read properties of null (reading 'edgesOut')").
The lock was therefore regenerated in two steps:

1. npm 10, `--package-lock-only`.
2. npm 11.7.0, `install --package-lock-only -D vitest@^4.1.11` only.

A third step, npm 10 `--package-lock-only`, applied the `@redocly/openapi-core` correction below.
Rerunning all three steps from the `d9b1532` lock reproduces the final lock byte for byte
(`lock-repro-1`), and a further npm 10 pass leaves it unchanged. CI itself installs with npm 10, and on
this lock `npm ci` runs cleanly with npm 10.

**`@redocly/openapi-core` resolver correction.** This defect predates the candidate. It has existed
since `7c64908` (25 July 2026) and is present at `d9b1532` and on `main`.

- `@redocly/openapi-core` 1.34.17 declares an exact `minimatch` 5.1.9 dependency and calls it as a
  function (`lib/utils.js`, `match()`, used for `resolve.http.headers` URL matching).
- `7c64908` added the scoped override `minimatch: ^10`, but the lock was never re-resolved and kept the
  nested 5.1.9. As a result, `npm ls --all` exits 1 (`ELSPROBLEMS`, invalid `minimatch@5.1.9`).
- That nested `minimatch` 5.1.9 also took the root `brace-expansion` 5.x override, so it throws
  `expand is not a function` when called. It is latent only because API-type generation never reaches
  `match()`.
- Honoring `^10` is not an alternative: `minimatch` 10's CommonJS export is an object, not a callable
  function, so `openapi-core`'s call would break.

The correction replaces that scoped override with `brace-expansion: 2.1.7`, the patched 2.x release
that `minimatch` 5's API expects. 2.1.7 is the 2.x fix for all three `brace-expansion` advisories above,
and the root `brace-expansion: 5.0.12` override is unchanged. The lock change adds only
`openapi-core/node_modules/brace-expansion@2.1.7` and its `balanced-match@1.0.2` dependency, resolved
by npm 10 `--package-lock-only` with no crash.

The replaced `minimatch: ^10` entry was not a security override. Per `7c64908`, its purpose was
compatibility consolidation, and the lock never applied it. GitHub's advisory database lists no
advisory affecting `minimatch@5.1.9` or `brace-expansion@2.1.7`. The same query returns all three
advisories for the vulnerable `brace-expansion@2.1.4`. `npm audit` reports 0.

The first candidate run, `npm-after-1`, recorded `npm ls` exit 1 but did not fold that exit into its
own exit 0; it stands as a failed dependency-inventory receipt. On the corrected graph, `npm-after-2`:

- `npm ls --all` exits 0;
- the nested `minimatch` 5.1.9 runs and matches both a URL glob and a brace pattern (exit 0).

Gates that use the changed graph were rerun on the final candidate (`npm-after-2`, Linux, Node 22):

- `npm ci` 0; `npm ls --all` 0; audits 0; typecheck 0; lint 0.
- Format: `npm-after-2` exited 1 only on `test-results/.last-run.json`, which earlier local E2E runs
  left in the scratch tree and which is gitignored. With that directory removed, the format check
  exits 0 (`format-after-2`).
- Tests 0 (6 files, 45 passed).
- `generate-api-types` 0, and the generated schema is byte-identical to `d9b1532`. This comparison is
  diagnostic (exported tree, no Git); the native CI drift check follows delivery.
- Build 0.

Isolated E2E, warm cache: 7 of 7 passed on the `d9b1532` graph, on the first candidate graph, and on
the final graph (`e2e-after-6`). Earlier
cold-cache local runs failed identically on both graphs, at the Branching delivered-turn test. The cause
was environmental: on first use, chromadb's default embedding fetches its 79 MB ONNX model, and the
local network was too slow for the test's 5 s expectation. Remote CI E2E passed on `d9b1532`.

## Python (`pip-audit` on a clean CI-equivalent install)

The CI step upgrades pip, runs `pip install -e ".[dev]"`, then audits that fresh resolution.

| Advisory (official) | Package | Vulnerable range, first patched | Clean install | Disposition |
|---|---|---|---|---|
| CVE-2026-4539 / GHSA-5239-wwwm-4pmq | Pygments (transitive) | `<2.20.0`, 2.20.0 | 2.21.0 | Fixed upstream; the ignore is **removed** |
| CVE-2026-3219 / GHSA-58qw-9mgm-455v | pip (CI tooling) | `<=26.0.1`, 26.1 | 26.2.1 | Fixed upstream; the ignore is **removed** |
| CVE-2026-59890 / GHSA-h35f-9h28-mq5c | setuptools (direct dev and build backend) | `<83.0.0`, 83.0.0 | 84.0.0 | Both floors raised from `>=68` to `>=83.0.0` |
| CVE-2026-45829 / GHSA-f4j7-r4q5-qw2c (critical) | chromadb | `>=1.0.0 <=1.5.9`, none | 1.5.9 | Retained (residue below) |
| CVE-2026-45830 / GHSA-2wm9-hf6c-p5cr (high) | chromadb | `>=0.4.17 <=1.5.9`, none | 1.5.9 | Retained |
| CVE-2026-45831 / GHSA-xph7-9rjv-w5fr (high) | chromadb | `>=0.5.0 <=1.5.9`, none | 1.5.9 | Retained |
| CVE-2026-45833 / GHSA-36p7-vc44-83pf (critical) | chromadb | `>=0.4.17 <=1.5.9`, none | 1.5.9 | Retained |
| CVE-2026-45832 / GHSA-x97m-f58v-9cwg (unreviewed) | chromadb | no package entry | — | Not reported by pip-audit; no flag (unchanged) |

Raw results:

- At `d9b1532`, the unfiltered audit lists only chromadb 1.5.9 and exits 1. It prints 5 rows, which are
  4 unique advisories: PYSEC-2026-311 (CVE-2026-45829) appears twice, alongside -3813, -3814 and -3815. Pygments and pip were already patched in that resolution, so their two
  ignores no longer matched anything.
- On the candidate:
  - the unfiltered audit lists the same chromadb rows;
  - the exact CI command with the four remaining flags reports "No known vulnerabilities found, 5
    ignored" and exits 0. The 5 ignored rows are those same 4 unique CVEs;
  - both packaging tests (`tests/ingestion/{corpus,mechanical}/test_packaging.py`, 3 tests) pass under
    `setuptools` 84.0.0;
  - Black and Ruff exit 0 on the one changed test file, whose change is docstring-only.

**Floor rule.** A floor was raised only for a direct dependency that the observed audits found
vulnerable and that has a fix: setuptools is the only one. This was not an exhaustive sweep of every
direct floor against historical advisories. Transitive packages are governed by the now-unignored gate
running on fresh resolution. No other repository manifest (`requirements*`, `constraints*`, Dockerfile,
or a second lockfile) exists. The pre-commit config pins only `detect-secrets` v1.5.0.

**chromadb residue.** PyPI's latest chromadb is 1.5.9, and every official record lists no patched
version. The ADR-018 embedded-only exception therefore stands. A re-grep at `d9b1532` confirms that all
clients come from `pipeline/retrieval/client.py::build_chroma_client`, which returns only
`PersistentClient`/`EphemeralClient`. There is no `HttpClient`, server process or `CHROMA_SERVER_*`
setting. `trust_remote_code` appears only in prose saying it is never set. The CI comments' "as of"
dates are refreshed to 2026-10-09. Their wording now describes chromadb's `>=0.5` floor rather than a
pin. No suppression is added, and Retrieval Memory is not made optional. This is unpatched residue under
existing policy, distinct from the advisories repaired above.

## Original source environment

The source checkout's existing `venv` was audited read-only: pip-audit 2.10.0 reports 35 vulnerabilities
in 12 packages (exit 1), and its `pip freeze` is identical before and after. The 7 October receipt showed
36 in 13. The difference is click 8.3.1, PYSEC-2026-2132 (CVE-2026-7246), which was withdrawn on
2026-10-07.

Every remaining non-chromadb row is a stale local install that a clean resolution replaces with a patched version:

| Package | Stale | Fixed in | Clean resolution |
|---|---|---|---|
| anyio | 4.13.0 | 4.14.2 | 4.15.1 |
| cryptography | 49.0.0 | 50.0.0 | 50.0.2 |
| fsspec | 2026.3.0 | 2026.6.0 | 2026.9.0 |
| idna | 3.11 | 3.15 | 3.20 |
| mako | 1.3.10 | 1.3.12 | 1.4.3 |
| msgpack | 1.1.2 | 1.2.1 | 1.2.3 |
| oauthlib | 3.3.1 | 4.0.0 | 4.0.0 |
| pip | 26.0.1 | 26.1 / 26.1.2 / 26.2 | 26.2.1 |
| pydantic-settings | 2.13.1 | 2.14.2 | 2.15.0 |
| setuptools | 82.0.1 | 83.0.0 | 84.0.0 (floor now enforces it) |
| urllib3 | 2.6.3 | 2.7.0 / 2.8.0 | 2.8.0 |

The only other row is chromadb 1.5.7, which has no fix and is covered by the residue above.

That historical environment was preserved unchanged. Use a fresh resolved environment for current
work; this delivery does not claim to have patched the old physical venv. The clean audit runs on
Linux to match CI; Windows-only marker dependencies are not covered by it.

## Guidance state

The source checkout's `CLAUDE.md` and `AGENTS.md` are unchanged and still say that dependency repairs
remain deferred; the withdrawal supersedes that line. In this delivery worktree, the parent replaced
exactly that one sentence in each file with the withdrawal. These edits are part of this candidate:

| File | Before (`d9b1532`) | After |
|---|---|---|
| `AGENTS.md` | `2a58013c…` | `686a4e2e…` |
| `CLAUDE.md` | `1fb1f870…` | `e4b0a8b4…` |

## Changed-input secrets gate

The native staged-relative hook flagged 295 Base64 strings, all on `integrity` lines in
`frontend/package-lock.json`. Codex checked each against the lock's public `registry.npmjs.org`
package records and its 64-byte SHA-512 structure. Only these exact public package-integrity
false positives were added to `.secrets.baseline`; every prior row and detector/filter setting
was preserved. The first hook failure is retained. The real relative hook must pass on the
final staged inputs before commit; content-only scans do not substitute for that gate.
