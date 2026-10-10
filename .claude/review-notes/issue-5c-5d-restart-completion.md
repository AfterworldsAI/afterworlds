# CRD Issues 5c/5d — restart completion: obligation (5) and reader retention

Verified 10 October 2026 UTC. Branch `codex/5c-5d-completion`, based on current
main `d3e803455013b97b4d1ac1dc1453ad82b5d45a0c`. PR #179 merged at
`2026-10-10T02:42:07Z` (9 October PDT); PR #178's historical merge commit is
`fcc4e1f…`.

**Scope and authority.** The Owner's bounded completion request, under the
21 September Owner Decision and ADR-005d. Codex review classified the reader
defect as settled-contract implementation work; it granted no authority.

**States, kept separate:**
- Bounded implementation and local verification: complete on this branch.
- Codex review and exact-head CI: pending.
- Reviewed and merged delivery: pending. Merge is an Owner boundary.
- Held, and not implied by merge: shared runtime publication and activation, and
  shared-database writes. The partial-publication block stands.

Merging this branch would not publish or activate anything, and would not declare
the restart operationally complete.

## §2.5 isolated operational obligations: all six discharged

Obligations (1)–(4) and (6) rest on the reused §8.5 evidence and their existing
tests, which were not rerun on this branch; its exact-head CI re-verifies them,
with the baseline-reset, vector-publication and readiness suites. Obligation (5)
is new on this branch.

| Obligation | Discharged by |
|---|---|
| (1) Persist → reconstruct → digest → gate → publish, with rollback and compensation | `tests/ingestion/corpus/test_source_lifecycle.py` (§8.5) |
| (2) Idempotent, verified reuse | `test_source_lifecycle.py` (§8.5) |
| (3) Verified operational load and vector publication on fresh-corpus data | `test_source_lifecycle.py` (§8.5) |
| (4) Recipe hash not quarantined | `test_source_release.py::test_the_candidate_is_not_the_quarantined_transform` |
| (5) 5d publish → activate → runtime-resolve | `tests/ingestion/mechanical/test_accepted_release_publication.py` (this branch) |
| (6) Baseline-reset digest proof | `tests/ingestion/corpus/test_source_baseline_reset.py` (§8.8.3) |

## Obligation (5)

**Inputs.** The module uses only production inputs:
- The real 5c state comes from `finalize_source_release` (`source_release_db`),
  copied into private SQLite files. Nothing is written to the shared fixture or
  any shared store.
- The draft is `candidate_from_accepted_inputs` over the committed
  `srd-5-2-1-corpus-8781d4e0-a3b.json`.
- Publication goes through `publish_from_committed_oracle`, which resolves the
  oracle from the packaged directory itself.
- No synthetic `AcceptedOracle`, no private `_publish_projection` and no
  rerecording are used.

**Monkeypatching.** The lifecycle and runtime nodes never patch a resolver. Only
the citation override cases supply an override set, using the same active
binding, as the established persisted-reader suites do.

| Node | Proves |
|---|---|
| `test_before_publication_runtime_answers_unpublished_not_empty` | The package reference is `RESOLVED`. `resolve_active_projection`, `resolve` ("no active mechanical projection") and a whole-package slice are typed `UNPUBLISHED`, with no slice |
| `test_the_public_path_publishes_exactly_the_accepted_projection` | `PUBLISHED` with zero gate failures, exactly projection `1f0db408-ee07-5e8d-897d-29838d614c53`. The header records the committed oracle identity and the evidence hash |
| `test_runtime_resolves_the_active_binding_with_empty_overrides` | Empty override state (`EMPTY_OVERRIDE_SET_UUID`). The exact four-part binding resolves by UUID, by UUID-string reference and with the expected release |
| `test_publication_is_committed_and_visible_to_a_fresh_session` | An engine and session opened independently after publication returned see `PUBLISHED`, the exact binding and a `glossary.blinded` slice |
| `test_the_packages_human_facing_slug_resolves_to_the_same_binding` | `package_slug` of the persisted package name is not a UUID. Resolving by that slug gives the same binding, and a slug-addressed record slice is `RESOLVED` (fresh session) |
| `test_the_runtime_slice_is_the_whole_accepted_authority` | Whole-package slice: all 1,835 records, none override-supplied |
| `test_a_selected_record_carries_its_exact_accepted_provenance` | `glossary.blinded` record and component `span_ids` equal the committed provenance. An unknown selector is `INVALID_REFERENCE` |
| `test_runtime_refuses_stale_evidence_and_a_superseded_binding` | A superseded recorded binding is `STALE`. Edited recorded evidence makes runtime `STALE`, and savepoint rollback restores the binding |
| `test_a_full_corpus_missing_three_leaves_is_refused_per_leaf` | Refused `INCOMPLETE` through the public path (categories below) |
| `test_the_refused_projection_left_nothing_active` | Header still a draft, no activation row, runtime `UNPUBLISHED` |
| `test_the_committed_authority_bytes_are_unchanged` | Oracle SHA-256 equals the pinned `CURRENT_SHA256` |

**Negative control.** The control is the full accepted candidate, with three
real heading leaves removed from the review units that alone accounted for them.
The committed oracle judges it. Its categories are exactly:
- `POPULATION_MISMATCH` ×3 and `SEMANTIC_VALIDATION` ×3, each naming a dropped
  leaf;
- `MISSING_AUTHORITY` ×3 and `UNEXPECTED_AUTHORITY` ×3, for the three edited
  units;
- `IDENTITY_MISMATCH` ×1.

There is no stale, release, policy, schema or residue category.

**Reused rather than repeated.** Full-corpus republication, re-proof refusal of
tampered content, `ACTIVE_CONFLICT` and concurrency stay covered on bounded
fixtures in `test_publication.py` and `test_concurrent_publication.py`. Under the
`resolve_active_projection` contract, runtime reads verify recorded-evidence
closure and binding currency; content re-proof belongs to publication.

## Reader-retention correction (ADR-005d Decision 7)

**Defect.** The deferred residue of `issue-5d-equipment-spell-references-review.md`
was refused even with no override:
- 37 accepted, resolved citations were refused as no longer stated;
- of these, 18 are component-owned with prose plus unbound supporting text,
  16 component-owned with unbound substantive text, 2 component-owned with both,
  and 1 record-owned with both (`glossary.grappling` "Grappled").

Decision 7 refuses a citation only once its citing record, component or prose is
disabled or replaced. The correction implements that settled contract within the
Owner's bounded completion request. Codex review classified it; it is not new
semantic acceptance.

**Change.** `services/rules_authority/service.py`: `citation_view` now calls one
predicate, `_citation_in_effect`. Each citing span is retained by its own
original source owner:
- **Bound as governing prose:** it must still be effective `SourceProse` of the
  citing record or component. This guard is unchanged.
- **Unbound `SUPPORTING_AUTHORITY`:**
  - The owner is the citation's own record (record-owned, as before) or its
    citing component.
  - It must be present and not override-supplied. There is no span-membership
    condition for supporting text.
  - A sibling's contextual provenance is never consulted, so the citation gains
    no new dependency.
- **Unbound `SUBSTANTIVE`:**
  - The owner is the span's unique PRIMARY `COMPONENT` provenance owner, taken
    from the reconstructed accepted representation.
  - It must be the citing component, or for a record-owned citation a component
    of the citing record.
  - It must be present, not override-supplied, and still claim the span. This
    span condition applies to substantive owners only.
  - An owner key that is not exactly `(record, component)` is malformed persisted
    state. It is refused through the typed reader contract (`INVALID_REFERENCE`),
    not unpacked.
- **Any other disposition, a missing or ambiguous owner, or a supplied owner:**
  refused, as before.

A record REPLACE deliberately keeps the replaced record's old span ids while naming
its supplier, so supplier identity, not span membership, is what refuses a
replaced owner. A component REPLACE carries no source span ids. There are no
reference, ownership, prose-binding, schema, oracle or destination changes.

**Explicit non-goals, unchanged:**
- fact-specific citation liveness (e.g. the shared Speed span);
- the suppress-all/empty-component policy (ADR-005d lines 1869–1873).

Decision 10's exact-target override semantics are preserved.

| Node | Proves |
|---|---|
| `test_every_accepted_citation_is_in_effect_with_no_override` | Over one reconstruction of the persisted projection, the effective representation has 8,583 resolved reference rows under 8,047 distinct four-part citation keys (both pinned). The predicate admits all 8,047 keys with no override, including the 37 previously refused. Only the four examples below go through the public `citation_view`. The family census is pinned exactly: record supporting 138 + 1 (prose), component 18 / 16 / 2, record substantive+supporting 1 |
| `test_an_accepted_citation_reads_its_destination_at_runtime` ×4 | Each family's example reads its destination through the real runtime path: Proficiency, Incapacitated, Dehydration "Exhaustion", Grappled |
| `test_a_citation_whose_original_source_is_gone_is_refused` ×8 | Refused when the original source goes: Proficiency prose DISABLE and component REPLACE; Incapacitated owner DISABLE and REPLACE, and record DISABLE (the predicate's absent-source branch); Dehydration record REPLACE; Grappled `grappled_condition` DISABLE and record REPLACE |
| `test_a_citation_survives_edits_that_leave_its_source` ×3 | Disabling a sibling component (`check_proficiency`, `dodge_benefits`) or appending prose to `grapple_basis` keeps the citation |
| `tests/services/rules_authority/test_citation_owner_shape.py` ×4 | A well-formed two-part owner key keeps the Incapacitated-shaped citation. One-part, three-part and empty owner keys refuse rather than raise |

**Counts, distinguished.** These are different quantities:
- the effective, persisted representation: 8,583 resolved reference rows under
  8,047 distinct four-part citation keys;
- the stored committed representation: 8,047 reference rows, of which 6,561
  carry a stored target;
- the 1,486 recorded reference resolutions.

**Adjacent existing controls**, rerun by node: the source-gone, unrelated-override,
edit-keeps and destination-disable cases in
`test_equipment_spell_references_candidate`, `test_reference_alternatives_candidate`
and `test_finite_reference_routes_candidate`. Results are in the validation table.

## Validation

Native logs are in the private completion evidence directory. Focused runs carry
the runner's label: coverage off, diagnostics only, not gate evidence.

| Run | Native result |
|---|---|
| Real-path probe (isolated temp store) | 5c publish → `PUBLISHED` `1f0db408-…` → `RESOLVED` → 1,835 records → republish `ALREADY_PUBLISHED` |
| Module, first run (`focused-obl5-1.log`) | **Exit 1.** 6 passed, 1 failed, 2 errors. Causes: a `dataclasses.replace` on a Pydantic binding, and an empty leaf selection (every leaf a span classifies is cited, so dropping spans could not leave the representation intact). Both were fixed in the test |
| The three fixed nodes (`focused-obl5-2.log`) | Exit 0, 3 passed |
| Whole module before this pass (`focused-obl5-final.log`) | Exit 0, 9 passed in 345.97 s |
| Retention predicate over all citations, private probe | 8,047 distinct citation keys, 0 refused with no override |
| Whole module with this pass's tests (`focused-obl5-retention-1.log`) | Exit 0, 26 passed in 602.58 s. A docstring-only edit to the module was saved during this run after collection; the code under test was unchanged |
| Whole module, final bytes, with the Incapacitated record-DISABLE case (`focused-obl5-retention-final.log`) | Exit 0, 27 passed in 619.11 s; supersedes the run above as the receipt for the final file |
| Candidate-module controls (`focused-controls.log`): equipment-spell-references and final-ten control refusals, final-ten destination disable | Exit 0, 24 passed in 723.79 s. These refuse upstream of the retention predicate (unresolved targets, disabled destinations) and are unchanged |
| Bounded synthetic `citation_view` callers | None exist: only the four `*_candidate` modules and this module call it |
| Adjacent existing retention controls (`focused-adjacent-retention.log`, 7 node functions in three modules) | Exit 0, 18 passed in 675.29 s |
| Malformed-owner public reader probe (`owner-shape-probe.log`) | Codex's reproduction was `UNHANDLED ValueError` before the guard. After it: valid `RESOLVED`, malformed `INVALID_REFERENCE`, in a rolled-back transaction on the private probe store (store sha256 unchanged, `1de389c5…`) |
| Owner-shape regression (`focused-owner-shape.log`) | Exit 0, 4 passed |
| Count checks (`citation-count*.log`) | Stored 8,047 rows / 6,561 targeted / 1,486 resolutions; effective 8,583 rows / 8,047 keys; persisted 8,583 / 8,047 |
| `mypy src/` (strict), strict mypy on the changed test modules, Black, Ruff | Final native exits are in the final gate receipt |

The whole module was not rerun after this pass's arity guard and count pins, by
instruction. The guard affects only malformed owners, and the pins were checked
against the same persisted data. Required exact-head CI runs the complete suite.

Not run locally, by instruction: the full backend suite with coverage, audit,
frontend and E2E. These run once in the reviewed PR's exact-head CI.
