# PR #142 Remediation Log — CRD Issue 5c recorded-evidence schema

Archive of detailed investigation and negative-control evidence for the stacked
5c recorded-evidence hardening. Kept out of the PR body so that body stays a
one-screen statement of what changed and why it is separately reviewable.

**Why this PR exists.** PR #141 round 4 produced a fourth consecutive finding in
the same 5c recorded-evidence verification seam. Its renewed stop condition
required escalation rather than a fifth local patch, so the hardening is
delivered here, reviewed on its own, and merged into
`feature/issue-5d-publication-gate`. It is based on that branch and not on
`main` because `verify_published_release` and the round-3 report helpers are
introduced by #141 and do not exist upstream yet.

---

## The finding, and the family behind it

Codex (PR #141, thread on `report.py:158`) is correct. `VERSION_CANARIES`
defines six required checks; round 3's `verdict_violations` iterated whatever
`version_canaries` happened to contain and required each present entry to be
`True`. It never required the map to *be* the canonical population. Once
`report_payload` and `evidence_report_hash` are edited together, `{}`,
`{"invented": true}`, or a partial map all satisfy recorded verdict validation,
and `verify_published_release` accepts evidence recording none of the required
version checks. `{}` is the sharpest case: `all(...)` over nothing is vacuously
true.

**Defect family:** *the recorded evidence validator checks required values but
does not prove the exact population of every closed schema inventory.*
`version_canaries` is one instance, and the fix is not a canary check.

## Inventory audit — every map classified explicitly

Audited before editing: the top-level report key set, `version_canaries`,
`findings`, `accounting`, every other nested map, `REQUIRED_REPORT_KEYS`,
`EVIDENCE_REPORT_SCHEMA_VERSION`, `VERSION_CANARIES`, `build_report`,
`verdict_violations`, `recorded_success_violations`, `run_gate`,
`verify_published_release`, fresh finalization, and verified reuse.

| Map | Classification | Population fixed by |
| --- | --- | --- |
| top-level report keys | **closed** | `REQUIRED_REPORT_KEYS` |
| `version_canaries` | **closed, verdict-bearing** | `VERSION_CANARIES` (derived) |
| `findings` | **closed, verdict-bearing** | `_ZERO_FINDINGS` |
| `accounting` | **closed, verdict-bearing** | `_ACCOUNTING_KEYS` |
| `reproduction_target` | **closed, structural** | `build_report` literal |
| `reconciliation_policy_reference` | **closed, structural** | `build_report` literal |
| `source_ledger_leaf_totals` | **open** | leaf types occurring in the corpus |
| `represented_totals` | **open** | leaf types occurring in the corpus |
| `excluded_totals_by_reason` | **open** | exclusion reasons actually applied |
| `transform_identity` | **open** | the recorded transform config's own identity payload |
| `rules_corpus_vector_identity` | **open** | the vector-identity builder |

The open maps are `Counter` results and config passthroughs: a release with no
table cells legitimately has no `table_cell` total, so demanding an exact
population would be demanding a particular corpus. That distinction is now
declared in code — `OPEN_REPORT_MAPS` — rather than left implicit, so nobody
later "hardens" it into a false failure.

## The correction

One canonical 5c-owned validator, as before; no second canary check anywhere, no
5d-side check, no parallel validator in `corpus.persistence`, no schema
framework.

- `CANONICAL_CANARY_NAMES = frozenset(c.name for c in VERSION_CANARIES)` —
  **derived**, so adding or retiring a canary moves the required population with
  no second list to remember.
- `_CLOSED_VERDICT_MAPS` and `_CLOSED_STRUCTURAL_MAPS` declare the closed
  inventories; `OPEN_REPORT_MAPS` declares the open ones.
- `_closed_map_violations` reports missing and unexpected entries separately —
  an omission and a foreign key are different findings.
- `verdict_violations` now checks **population before values** for the
  verdict-bearing maps. That runs on both sides of the boundary, which closes
  the same omission in `build_report`: `all(c.passed for c in ())` was vacuously
  true, so a report built from a partial canary run would have recorded `"pass"`.
  It cannot now.
- `recorded_success_violations` additionally requires the top-level key set to
  match **exactly** — previously only missing keys were reported, so an
  edited-and-rehashed payload could carry an unknown field under the same schema
  version — and closes the two structural maps.

**No schema-version bump.** The canonical payload shape is unchanged; this
enforces semantics every honestly built report already satisfies. Verified: the
real full-SRD report and the bounded fixture report both pass unchanged, and
`EVIDENCE_REPORT_SCHEMA_VERSION` is bound into the transform identity, so a bump
would mint a new 5c release identity for no shape change.

**Test-fixture consequence.** The bounded mechanical fixture built its report
with `canaries=()`. That is now refused, correctly, so it supplies the complete
canonical population via `BOUND_CANARIES`, derived from `VERSION_CANARIES` —
standing in for a real canary run exactly as the rest of that synthetic release
stands in for a real corpus. The bounded oracle needed no regeneration: the
report is not a bundle member and the six binding values are untouched.

## Negative controls

**Canary population** — `tests/ingestion/corpus/test_recorded_evidence.py`:
`{}`, invented-only, missing one canonical name, canonical plus one invented,
a canonical canary `False`, a canonical canary non-boolean; and the positive
control, the exact six all `True`, passing. Plus
`test_the_canonical_canary_set_is_derived_not_restated`, which holds the
constant to `VERSION_CANARIES` so a hand-written duplicate cannot creep back.

**Sibling inventories** — `findings` partial and with an extra key; `accounting`
with an extra key; `reproduction_target` empty and with an extra key;
`reconciliation_policy_reference` with wrong keys; an unknown top-level key.
And the counter-control: each of the five open maps accepts an arbitrary
content-derived key.

**Writing side** —
`test_build_report_refuses_to_claim_success_over_an_incomplete_canary_run`.

**End-to-end** — the mechanical bound-release matrix gained six cases that
rewrite the release's recorded report **and rehash it**, so the payload still
hashes to its recorded hash and all five proof identities are untouched: no
canaries, invented-only canary, one canonical canary omitted, an invented canary
added, an incomplete `findings` population, and an unknown top-level key. Each
returns `STALE` with exactly `{BOUND_RELEASE}` from
`publish_from_committed_oracle` — publication refused, not merely a validator
returning a string.

## Verification

`black` clean · `ruff check` clean · `mypy --strict` clean (210 files) ·
5c corpus + mechanical suites **764 passed** (includes the real-SRD production
control and the full 5c report/gate/persistence/finalization/reuse suites) ·
recorded-evidence module **49 passed** · mechanical publication **55 passed** ·
full default suite **3141 passed, 10 skipped** (93.42%).

No Chroma dependency, no Owner Decision, no ADR or Issue amendment, and nothing
outside the recorded-evidence schema was touched.

## Further stop condition

If review of this PR finds another omitted closed inventory in the same report
schema after this audit, the hand-maintained validation is replaced by an
explicit typed canonical report schema whose construction, hashing, persistence,
and recorded verification all use one object — not another field-by-field patch.

During this audit no part of `report.py` was found reconstructing the canonical
schema independently: `build_report` assembles the payload, and the declared
constants above are the single source for every population check. That is why a
typed schema object is not yet justified.
