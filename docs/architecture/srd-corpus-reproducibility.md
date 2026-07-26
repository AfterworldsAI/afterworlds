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
- **First-party transform source manifest:** the transform identity binds a
  canonical manifest over the committed first-party modules that produce the
  candidate corpus or its canonical identities (steps a0–b) — `pdf_source`,
  `ledger`, `transform`, `reconcile`, `policy`, `bundle`, `hashing`, `models`,
  `pipeline`, `transform_identity` (verification/persistence/publication modules
  are excluded because they cannot change the candidate bytes). Each entry is a
  repo-relative path + SHA-256 of that file's newline-normalized source, sorted
  by path; the aggregate `transform_source_hash` is a pure function of those
  bytes. A change to **any** covered module moves the hash automatically — no
  manual version bump — so a transform-code change (e.g. a segmentation or
  chunk-generation fix) yields a **new draft release** rather than reusing the
  predecessor's identity. Implemented in
  `afterworlds.ingestion.corpus.transform_identity`.

## Exhaustive authoritative-source extraction (Component A)

Source completeness is proven independently, not self-asserted. Because the
authoritative source hash is a bound constant rather than a function of the pages
actually extracted, a candidate covering only a *subset* of pages while carrying
the real PDF hash would otherwise pass. `afterworlds.ingestion.corpus`
`.source_completeness` closes this:

- an ordered per-page **extraction manifest** — `(page_index, printed_page,
  geometry, sha256(canonical_text))` for every page in order — is hashed to a
  single `source_extraction_hash`, compared to the golden
  `AUTHORITATIVE_SOURCE_EXTRACTION_HASH` derived once from a full extraction of
  the committed PDF (same hardcoded-verified-fact pattern as `PDF_SHA256`);
- structural checks assert the page sequence is exactly `1..364` contiguous with
  `page_index == printed_page - 1`, so an **omitted, duplicated, reordered, or
  substituted** page each produces a diagnosable failure.

`finalize_release` runs this proof **before any SQL or Chroma mutation**, so an
unproven candidate is rejected leaving no package/release/vector state; the reuse
path additionally re-checks that the persisted ledger covers every printed page.
The proof is over pre-segmentation **page** text, so it is stable across
downstream leaf/table segmentation changes — it attests exhaustive ordered
extraction, while concordance and the table row/cell accounting separately attest
structural fidelity.

## Structurally faithful tables (Component F)

SRD tables shade their cells with filled rectangles; a shaded row's per-column
rects give deterministic **column boundaries** and a y-band anchor, while the
**rows** come from the text lines that align to those columns
(`afterworlds.ingestion.corpus.tables`). Each row's canonical-text char span is
partitioned at the column boundaries into `TABLE_CELL` sub-spans, so the cells
exactly tile the same characters the row would otherwise occupy — the ledger's
disjoint+exhaustive page tiling is preserved (sibling cells adjacent within a
row, a single `\n` between rows). A cell is emitted exactly once; a wrapped
multi-line cell folds its continuation into one leaf, and a page-spanning table
continues as the same logical grid. Detection only ever consumes a maximal
contiguous line run and discards any candidate table whose cells fail span
validity or page concordance, so a mis-detection falls back to paragraph
segmentation and never corrupts tiling. Each cell records its table identity and
0-based row/column on the ledger leaf (`rp_ledger_leaves.table_id/table_row/
table_col`, migration 0019), under a `TABLE` container nested in its section.
Full-PDF `check_table_concordance` verifies every emitted cell's structural
consistency (unique row/col, in-range, non-empty) and on-page presence from the
reconstructed tables (independent of the generated RuleChunks) and surfaces the
detection coverage tally — candidate regions it cannot cleanly reconstruct
(shaded prose spanning both body columns) deliberately fall back to paragraph
segmentation, counted rather than silently capped.

## Persisted source membership (Component G)

The persisted-corpus digest binds every chunk's actual persisted `source_id` and
the complete canonically-ordered logical `RuleSource` set (`source_id`,
`rules_package_id`, `name`, `category`, `precedence_rank`, `is_enabled`;
operational `created_at` excluded), and `verify_single_source` enforces the
Issue-5c single-source invariant (exactly one authoritative source, deterministic
`source_id == package_uuid`, expected metadata, enabled, every chunk assigned to
it). Both are reconstructed from persisted state and gate publication/reuse, so a
chunk reassigned to a different source, or altered/disabled/extra/missing source
state, fails verification.

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
2. transform source/configuration hash (covers the extractor config, the frozen
   policy, **and the first-party transform source manifest/hash**);
3. canonical corpus-bundle root hash;
4. evidence-report hash;
5. persisted-corpus digest.

The package UUID is `uuid5(source_hash, transform_hash)` — new for new inputs yet
reproducible for identical inputs (Owner Decision 1). A changed source or
transform input (including the policy) produces a new draft release and can never
mutate a published one.

## Leaf identity vs. output chunk identity

Two distinct identities that must not be conflated:

- **Source `leaf_id`** — the provenance identity of a page-content occurrence,
  derived from source facts only (page, span, type, content). It is
  **release-independent**: the same occurrence keeps the same `leaf_id` across
  every release, so later work can consume it as a stable provenance key.
- **Output `chunk_id`** — the identity of a canonical `RuleChunk` (Component F).
  It is **release-scoped**: `content_id("chunk", package_uuid, leaf_id)`, so a new
  immutable release (a changed source, transform config, transform-source
  manifest, or embedding model — anything that moves `package_uuid`) mints
  distinct chunk IDs even for identical leaves. Because `rp_chunks.chunk_id` is a
  global primary key, this is what lets two releases coexist in one database
  instead of colliding; the downstream rules-corpus vector IDs
  (`rules:{package_uuid}:chunk:{chunk_id}`) and projection IDs are already/thereby
  package-scoped. Identical release inputs still regenerate byte-for-byte (the
  `package_uuid` is itself deterministic).

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
