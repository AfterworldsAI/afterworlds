# PR #141 Remediation Log — CRD Issue 5d PR 2

Archive of detailed Codex/Claude review-remediation history for PR #141. This
material was moved out of the PR body to keep that body focused on the
implemented result, acceptance coverage, durable Architecture Notes, current
boundaries, and final verification status.

---

## Remediation round 1 — authority reconstructed, not declared

### Root defect (one family, five symptoms)

**The mechanical-publication lifecycle accepted a declaration as proof.** At five
seams a caller-supplied or persisted *claim* was treated as the authoritative
state it claims to represent, instead of that state being reconstructed and
re-verified.

| Codex symptom | The declaration that was trusted | Authority never reconstructed |
| --- | --- | --- |
| `publication.py:370` — overridable oracle directory | the caller's `directory` argument | the packaged committed oracle |
| `gate.py:480` — binding compared candidate↔oracle only | two agreeing six-value bindings | the published `rp_corpus_releases` row and its proof |
| `oracle.py:448` — obligations accepted as given | the file's `obligations` array | the accepted representation the obligations must reconcile with |
| `publication.py:234` — direct activation | `publication_status='published'` + a non-NULL hash | the gate, the oracle, and the recorded evidence |
| `publication.py:307` — reuse on a hash comparison | `evidence_report_hash` | the `report_payload` that hash identifies, and the freshly derived report |

Classification: **merge-blocking defect family**, in scope for CRD Issue 5d
PR 2 under ADR-005d Decisions 5 and 8. No Owner Decision, Known Unknown, issue
amendment, or ADR amendment was required — source inspection did not show
otherwise. One architectural correction applied.

### Architecture selected

**One supported publication surface.** `mechanical/publication.py` now exports
`publish_from_committed_oracle`, `resolve_active_projection`, and the result
types — nothing else. `publish_projection` and `activate_projection` became
`_publish_projection` and `_activate_projection`: the first takes the judging
oracle, so exporting it is the same bypass as an oracle-directory parameter, and
the second is a step of a publication that has already passed the full gate.
`committed_oracle_for` lost its `directory` parameter; directory-parameterized
resolution moved to the private `_resolve_committed_oracle`, used only by tests.

**5c owns the release proof.** `corpus/persistence.py::verify_published_release`
is the new narrow seam, called by `mechanical/gate.py` before anything derived
from the release is read. It reuses 5c's existing reconstruction and proof
primitives (`_load_policy`, `_load_ledger`, `_load_reconciliation`,
`_load_members`, `ledger_hash`, `reconciliation_hash`, `build_bundle`,
`report_hash`, `_report_schema_ok`, `verify_single_source`,
`verify_chunk_runtime_membership`). No 5c proof logic is duplicated in 5d.
A new `GateFailureCategory.BOUND_RELEASE` maps to `PublicationOutcome.STALE`.

**One closed recorded-evidence seam.** `_recorded_evidence_closure` (payload
present, supported schema, hash *of that payload*, publication fields present)
is used by `resolve_active_projection`; `_recorded_evidence_failures` adds the
freshly-derived comparisons and is used before `ALREADY_PUBLISHED`.

**One obligation derivation.** `oracle.derive_obligations` states what an
accepted representation claims per record; `load_oracle` requires the committed
file's obligations to equal it exactly (total, no duplicates, no phantom
records, kind and family and prose-bound sets reconciling), and `gate` reads
structured families and prose-bound handling the same way — so every obligation
that loads is one the gate can satisfy.

### Sibling audit

**Trigger:** five findings in one PR round resolving to one authority/evidence
closure family across `oracle.py`, `gate.py`, and `publication.py`.

| Sibling inspected | Disposition |
| --- | --- |
| `publish_projection` | **patched** — privatized; accepts the judging authority |
| `publish_from_committed_oracle` | **patched** — `directory` removed |
| `activate_projection` | **patched** — privatized; post-gate only |
| `resolve_active_projection` | **patched** — resolves the target header, requires published status and closed recorded evidence; forged/cross-package/draft/cleared-evidence rows resolve `STALE` |
| `PublicationOutcome` / `PublicationResult` / `ActiveProjection` | already safe — data, no authority |
| `committed_oracle_for` | **patched** — `directory` removed |
| `load_oracle` | **patched** — closed obligation relation; takes no session and cannot publish |
| `_resolve_committed_oracle` | new, private, non-production test seam |
| `AcceptedOracle` built in memory | out of scope — not committed authority; the existing drift test compares the in-memory fixture with the committed file through `oracle_payload` |
| `load_bound_corpus` | already safe, unchanged — a draft-construction resolution seam that never asserted publication authority. a stricter publication-authority seam was added alongside it rather than changing draft behaviour |
| `verify_persisted_page_coverage` | out of scope — asserts the full 364-page SRD ledger; a 5c reuse-path completeness check, not a property of an arbitrary bound release |
| `verify_persisted_digest` / `recompute_persisted_digest` | see the boundary below |
| `build_evidence_report` / `report_hash` | already safe — the report reads no `publication_status`, which is what makes exact payload comparison against a published header sound |
| `record_persisted_state_digest` | already safe — the gate still verifies what it recorded |
| `GateResult.passed` | **patched** — now also requires a proven bound release |

**Audit question — can any caller, malformed row set, partial migration, direct
database edit, or stale stored claim cause a projection to be published,
activated, reused, or reported as active without the complete committed oracle,
the exact verified published 5c release, reconstructed persisted state, and the
recorded evidence payload all agreeing?**

No, with one named exception below. Every `PUBLISHED` / `ALREADY_PUBLISHED` /
active-authority answer now passes through the full committed-oracle gate (which
itself begins by proving the bound release) and the closed recorded-evidence
seam, or — for `resolve_active_projection` — through recorded-evidence closure
under an explicitly stated contract.

### New import edge, stated rather than left to be found

`mechanical/gate.py` now imports `corpus/persistence.py`, which imports
`chromadb` at module scope through `vector_publication`. That edge is
deliberate: the 5c proof stays owned by the 5c package and is called from 5d,
and every reconstruction primitive `verify_published_release`
needs already lives in that module. The alternative — a second 5c-shaped proof
inside `mechanical/` — is exactly the duplication that ownership rule forbids. The cost is an
import-time dependency on an installed package, not a runtime retrieval call:
nothing on the mechanical publication path opens a Chroma client.

### Unresolved boundary (not a Known Unknown)

`rp_corpus_releases.persisted_corpus_digest` binds the **actual read-back vector
logical state** as well as SQL (CRD Issue 5c Component A). It is therefore not
recomputable from a `Session` alone, and threading a Chroma client into the
offline mechanical publication path would put a retrieval dependency into 5d and
exceed this PR's scope.

`verify_published_release` therefore verifies the digest as an exact recorded
value cross-checked against the recorded evidence report, and re-derives every
*SQL-grounded* identity that release records — `ledger_hash`,
`reconciliation_hash`, `bundle_root_hash` (which covers the ledger, the
authoritative chunks, and the reconciliation), and the policy chain via
`_load_policy`. The cross-store half remains proven by 5c's own
`finalize_release`, the only path permitted to set it. This is stated in the
function docstring, not left implied.

### Negative controls added

Surface: no exported publication function accepts `oracle` or `directory`;
`committed_oracle_for` accepts no `directory`; `publish_projection` and
`activate_projection` are no longer module attributes; the production entry
raises `TypeError` on `directory=` while a loadable self-authored oracle sits in
that directory.

Bound release: a fabricated six-value binding that the projection *and* the
oracle both carry; release still draft; package not published; package disabled;
release evidence cleared; recorded ledger proof that does not reconstruct;
release content edited under its recorded proof.

Oracle: no obligations at all; one record uncovered; duplicate; nonexistent
record; wrong record kind; understated and overstated fact families;
understated prose-bound set; prose-bound naming a structured component;
prose-bound naming a nonexistent component.

Evidence: cleared `report_payload`; payload edited under an unchanged hash;
payload and hash edited together; wrong judging-oracle identity; a hand-marked
`published` header that cannot become active; a forged activation row that does
not resolve as valid authority; an active projection whose evidence was cleared.

Positive behaviour retained: first publication succeeds; identical
re-publication fully re-verifies and is idempotent; competing publication is an
active conflict; a failed publication leaves no partial evidence or activation;
the production incomplete-content control still fails exactly, per leaf, with no
threshold.

### Gates on the branch head

`black` clean · `ruff check` clean · `mypy --strict` clean (210 files) ·
mechanical suite **443 passed** · production-corpus control **8 passed** ·
CRD Issue 5c ingestion/corpus suite **186 passed** (now a direct dependency,
and it carries the migration/schema-parity checks) · full default suite
**3008 passed, 10 skipped**, coverage 93.33%.

Coverage on the changed modules: `gate.py` 97%, `oracle.py` 97%,
`publication.py` 96% — the only uncovered lines being the documented-unreachable
post-activation rollback and the exception re-raise.

`pip-audit` reports pre-existing advisories in `setuptools` and `urllib3`,
neither introduced nor touched by this change.

*Local run boundary:* the 3008-test full-suite run completed before three
additive test functions were appended (`test_a_missing_publication_evidence_field_…`,
`test_an_obsolete_evidence_schema_…`, `test_the_production_entry_is_absent_for_an_unknown_projection`).
`src/` was byte-identical at that point and those three are covered by the
443-test mechanical run. CI on branch head `21f5fcc` is the authoritative
full-suite result and is green on all three jobs (`Lint, Type-check, Test,
Audit` 25m14s; frontend 1m3s; Playwright e2e 1m41s).

### Review-loop stop condition

Round 1 findings were concrete and in scope, so one architectural correction was
applied. If a later Codex round returns to this same **authority/evidence
closure** family in `oracle.py`, `gate.py`, or `publication.py`, the patch cycle
stops before code changes and the remaining feedback is classified as issue
scope, Known Unknown, or ownership semantics.

Two candidates are already anticipated and would be classified rather than
patched:

* **`derive_obligations` makes the committed `obligations` array derivable**, so
  why commit it as a file field at all. That is an ownership/semantics question
  about the oracle file format, not a defect — the independence that matters is
  oracle-versus-projection, and it is untouched.
* **`resolve_active_projection`'s contract.** It asserts recorded-evidence
  closure, not a re-run of the publication proof, so consistently-edited
  evidence and a release retired after publication are outside what it detects.
  Both are caught by `publish_from_committed_oracle`; revalidating the effective
  runtime binding on read is CRD Issue 5d PR 3's. This is the PR 2 / PR 3
  boundary, stated in the function docstring.

### Test-fixture consequence

The bounded 5c release in `tests/ingestion/mechanical/conftest.py` was a
hand-written row set with invented `ledger_hash` / `policy_hash` /
`reconciliation_hash`. Under the new gate that is a forgery, so it is now built
from genuine CRD Issue 5c model objects and persisted through 5c's own
primitives (`_persist_package_and_source`, `_persist_release_record`,
`_persist_bundle_rows`). `RELEASE_BINDING.bundle_root_hash` is consequently the
real bundle root, and `data/bounded_oracle.json` carries that one changed value.
`tests/ingestion/mechanical/test_production_release.py` now restates the
published transition after `persist_release`, which writes step-c drafts — the
5d gate refuses to publish over a draft 5c release, correctly.
