# SRD Corpus Reproducibility — CRD Issue 5c (#132), ADR-005c Completion Contract A

The authoritative SRD 5.2.1 corpus is a **byte-for-byte reproducible** release
derived deterministically from the authoritative PDF. This document defines the
acyclic proof lifecycle (Component K) and the determinism rules that make a clean
checkout regenerate an identical release.

**Scope of the claim.** Reproducibility is byte-for-byte **within the recorded
reproduction environment**: the pinned extractor (below), Python 3.12, and the
platform recorded in the evidence report (`reproduction_environment`). The corpus
content identities (ledger, bundle root, persisted-corpus digest, package UUID)
depend only on the PDF and the transform configuration, not on the platform; the
environment is recorded so a divergence — should a future extractor or platform
change extraction output — is observable rather than silent. Cross-platform
byte-identity has not been independently proven and is verified per environment.

## Inputs (committed)

- **Authoritative source:** `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`
  (SHA-256 `8974902d…3d87`, 6,031,375 bytes, CC BY 4.0). Verified before any
  extraction; a mismatch fails closed.
- **Pinned extractor:** `pdfplumber==0.11.10` / `pdfminer.six==20260107`
  (`pyproject.toml`). The transform records these identities; bumping either is a
  transform-config change that yields a **new draft release**.
- **Frozen reconciliation policy:** committed source in
  `afterworlds.ingestion.corpus.policy` (closed exclusion-reason set, projection
  roles + overlap semantics, normalization identity). Frozen before any output.

## Acyclic proof lifecycle (Component K, steps a0–g)

Implemented by `afterworlds.ingestion.corpus.pipeline.build_release`:

| Step | Action | Module |
|------|--------|--------|
| a0 | Freeze the reconciliation policy (covered by the transform-config hash) | `policy` |
| a1 | Extract the PDF and derive + hash the frozen source ledger | `pdf_source`, `ledger` |
| a2 | Generate canonical corpus members **from the frozen ledger** | `transform` |
| a3 | Reconcile by applying **only** the frozen policy → reconciliation member | `reconcile` |
| b | Compute the bundle-root hash (excludes itself and the report) | `bundle` |
| c | Persist the canonical logical state into SQL (+ informational vectors) | `persistence` |
| d | Compute the persisted-corpus digest from the persisted state | `bundle` |
| e | Generate the post-persistence evidence report (no self-hash) | `report` |
| f | Hash the completed evidence report | `report` |
| g | Record the five top-level hashes and run the publication gate | `gate` |

No artifact is ever covered by a hash it contains, and the evidence report is
never generated before persistence. The ledger is derived from the PDF
independent of any output; the corpus is generated from the frozen ledger; the
reconciliation checks output-vs-ledger — so gap-free, zero-unresolved coverage is
honest-by-construction, and concordance + six version canaries (Component E/J)
independently verify correspondence to the real PDF.

## The five top-level release identities (Component A)

Recorded in the external release/publication record (`rp_corpus_releases`):

1. authoritative source hash;
2. transform source/configuration hash (covers the frozen policy);
3. canonical corpus-bundle root hash;
4. evidence-report hash;
5. persisted-corpus digest.

The package UUID is `uuid5(source_hash, transform_hash)` — new for new inputs yet
reproducible for identical inputs (Owner Decision 1). A changed source or
transform input (including the policy) produces a new draft release and can never
mutate a published one.

## Determinism rules

- **Content-derived identities only** (`uuid5`/SHA-256 over canonical JSON). No
  `uuid4`, no wall-clock timestamps in any hashed artifact or the digest.
- **Canonical serialization**: sorted keys, compact separators, UTF-8, `\n`
  newlines (`afterworlds.ingestion.corpus.hashing`).
- **Geometry rounding**: extracted coordinates are rounded before hashing so
  float rendering cannot perturb a proof identity.
- **Reading order**: content-stream flow (`use_text_flow=True`), lines grouped by
  vertical proximity — verified faithful against the six canary pages.

## Regenerating the corpus

```bash
python scripts/ingest_srd.py --db-url sqlite:///afterworlds.db
```

This builds the release from the PDF, runs the publication gate, and persists a
new immutable release only if the gate passes. It never reads the quarantined
legacy artifact (Owner Decision 1); see `docs/legacy/quarantine/README.md`.

## What corpus publication proves — and does not

Publication proves **source-corpus integrity only**: authoritative-source
identity, complete atomic-leaf accounting with zero unresolved leaves, gap-free
declared-projection coverage, passing concordance, and byte-for-byte
reproducibility. It does **not** certify that any mechanic is deterministically
executable — that is Issue 5d's and Issue 15c's separate, later claim
(ADR-005c Decisions 1, 6).
