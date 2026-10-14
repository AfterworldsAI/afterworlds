# CRD Issue 15c dependency-gate disposition — 13 October 2026

**Verdict: no dependency blocker and no new Owner Decision from the five reported Chroma rows.** The unchanged configured audit passes locally: exit 0, `No known vulnerabilities found, 5 ignored`. Correct the latest status/handoff to distinguish the unfiltered advisory inventory from the configured gate. Keep the existing four narrowly justified exceptions unchanged; exact final-head CI remains required.

## Verified evidence

- Checkout: `D:\AI\Claude\scratch\AW docs\issue2b-implementation\afterworlds`. Initial head `782f441`; concurrent engineering advanced it to `9477e766c6b1bd13940fdb959e9e78a4fd35e12c` during this review. This receipt is a local environment audit, not final-head CI evidence.
- Isolated interpreter: this checkout's `venv\Scripts\python.exe`, Python 3.12.10; `afterworlds.__file__` resolves to this checkout's `src\afterworlds\__init__.py`. Installed `chromadb=1.5.9`, `pip-audit=2.10.1`, `afterworlds=0.1.0`.
- `pyproject.toml:14` declares `chromadb>=0.5`, not a lock/pin. No tracked Python dependency lock/requirements file was found; the tracked dependency lock is `frontend/package-lock.json`. CRD Issue 15c's pyproject changes affect oracle packaging, not dependencies. CI installs `.[dev]` before auditing its own resolution.
- `.github/workflows/ci.yml:119-186` already documents the embedded-only ADR-018 deployment exception, separately justifies four CVEs, and invokes the exact flags below. Its blob is `41e1d5ec5b5102560f61c47c5df65dc300573a43`, identical to baseline `e83018c`. No CI or exception change is needed.
- Existing dependency history at `d720c61610034106a776abcf09a4de3c97396b64`, `.claude/review-notes/issue-5c-release-readiness/dependency-disposition.md` (Python section), explicitly records these same five rows as four unique CVEs and the configured audit passing. This is supporting policy/evidence, not a claim that preexisting vulnerabilities automatically pass.
- `src/afterworlds/pipeline/retrieval/` has no diff against `e83018c`. Current `client.py:17-54` constructs only `PersistentClient`/`EphemeralClient`; `config.py:61-71` preserves the absent server-mode/trust-remote-code configuration surface. A bounded search of `src/afterworlds` finds no executable `HttpClient`, `CHROMA_SERVER_*`, or `trust_remote_code` configuration. The reviewed exception's deployment assumptions remain intact.
- Existing public tool records in `../issue-15c-preparation/implementation-run/stream.jsonl` contain both the bare failing inventory (`toolu_011SuVyo1tpm9AEPdE68oDqw`) and a later exact configured command returning `exit=0` (`toolu_01KfMcyTUJtRsCpkuUVGMAqF`). Only tool-use and tool-result blocks were inspected; no private reasoning was read. This corroborates the distinction but does not establish the arguments of every later engineering run.

## Current upstream facts

Live PyPI still publishes [Chroma 1.5.9 as latest](https://pypi.org/project/chromadb/). The advisory records identify no released fixed version and list 1.5.9 as last affected:

| Reported row | Existing CI exception | Relevant vulnerable surface |
| --- | --- | --- |
| [PYSEC-2026-311](https://osv.dev/vulnerability/PYSEC-2026-311), twice | CVE-2026-45829 | Pre-auth server collection creation with attacker-selected model and remote-code trust |
| [PYSEC-2026-3813](https://osv.dev/vulnerability/PYSEC-2026-3813) | CVE-2026-45830 | Server cross-tenant authorization |
| [PYSEC-2026-3814](https://osv.dev/vulnerability/PYSEC-2026-3814) | CVE-2026-45833 | Authenticated server collection update with attacker-selected model and remote-code trust |
| [PYSEC-2026-3815](https://osv.dev/vulnerability/PYSEC-2026-3815) | CVE-2026-45831 | Server SimpleRBAC resource-scope authorization |

The linked upstream authorization repair [chroma-core/chroma#7602](https://github.com/chroma-core/chroma/pull/7602) is still open. It is not a released upgrade remedy. No bounded available package upgrade closes these four advisories today. Vendoring, downgrading, replacing Chroma, making Retrieval Memory optional, or broadening exceptions is not justified by this report.

## Audit receipt and disposition

Executed through `rtk proxy`, in the checkout above:

```powershell
.\venv\Scripts\python.exe -m pip_audit --ignore-vuln CVE-2026-45829 --ignore-vuln CVE-2026-45830 --ignore-vuln CVE-2026-45831 --ignore-vuln CVE-2026-45833
```

The first sandboxed attempt failed DNS resolution before an audit result. The same command with approved network access completed with exit 0:

```text
No known vulnerabilities found, 5 ignored
Name        Skip Reason
----------- --------------------------------------------------------------------------
afterworlds Dependency not found on PyPI and could not be audited: afterworlds (0.1.0)
```

**Defect class/disposition:** gate-evidence/status mismatch; ordinary documentation correction, not a new security-risk acceptance. Retain the unfiltered inventory as evidence of the existing unpatched residue; record the configured gate accurately. Applying the already accepted exceptions is not weakening the gate. A new advisory, changed deployment boundary, or new released fix would require fresh disposition rather than automatic carry-forward.

**Remaining boundary:** this local result does not replace final-head CI or any gameplay/full-suite gate. No source, dependency, baseline, CI, authority, protected checkout, shared runtime, or installed package was changed for this review. Only this report was written.
