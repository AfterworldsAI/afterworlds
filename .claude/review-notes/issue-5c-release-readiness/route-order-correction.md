# PR #178 — labelled route order correction (9 October 2026)

Prepared on parent `5795e93` and accepted by Codex after independent code,
preservation and gate-evidence review. Additive Git delivery uses the existing
Owner authorization; merge, runtime publication, activation and shared writes
remain held.

## Defect

ADR-005d Decision 7 (amendment accepted 1 October) reads a labelled citation's
routes in stated order, each route's landing before its support.
`representation_payload` sorted all references by canonical bytes, so a reordered
route derived the same projection UUID and payload hash. `load_raw_state` read
rows without `ORDER BY`. After two stored destinations were swapped, the
persisted digest was unchanged and the publication gate passed (Codex
reproduction `route-order-repro.py`). Classification: an issue-scoped
implementation defect under settled semantics.

## Correction

- `projection.py`: `_references_payload` keeps each labelled citation's
  references as one run in stated order and sorts only the runs, by citation.
  Unlabelled references keep the plain canonical order, so any payload without
  labelled references is byte-identical to before.
- `raw_state.py`: rows are read with `ORDER BY row_id`. `persist_draft` already
  inserts references in stated order, and `row_id` is the autoincrement key, so
  no migration or field is needed.
- The digest and gate need no change. Reconstruction now re-derives the stated
  order, so a reordered store derives another identity. The gate reports
  `PERSISTED_STATE` ("reconstructed state derives …"), which publication maps to
  `STALE`.

## Identity effects (`route-baseline-prefix-2` vs `route-baseline-postfix-1`)

Unchanged: the oracle file (`def7caa1…`) and its re-serialized bytes,
`oracle_identity`, the accepted representation payload hash (`e5861194…`; zero
directly authored labelled references), all 24 recorded proposal identities
(`test_committed_accepted_authority` passes), and all 76 loadable on-disk
proposal identities. The labelled counts (42 citations, 385 routes, 133
multi-member routes) are also unchanged.

Changed (derived only): the effective projection UUID changes from
`8d8cb42c-aefe-559c-9d85-6ba975c038af` to `1f0db408-ee07-5e8d-897d-29838d614c53`,
and the payload hash from `69299de5…` to `a2bdf177…`. The Owner-accepted
candidate document `issue-5c-release-order-candidate.md` (line 136; unmodified in Git)
records `8d8cb42c` as the derived new-projection UUID, and so do its reader-proof
and recording evidence (`reader-proof2.json`, `codex-native-persistence.json`,
`recorded-canonical-reconstruction.json`, `codex-canonical-reconstruction.json`).
All are left unchanged as pre-fix history; they record a derived value, not an
accepted input. A grep of `tests/`, `scripts/`, `src/` and `.github/` finds no
pin of `8d8cb42c`, `69299de5` or the fixture UUIDs outside this test file, and no
test that reads those documents.

## Pre-fix stored projections

A projection persisted before the fix fails closed when its stated order
differed from canonical order. Its UUID no longer re-derives, the gate fails
`PERSISTED_STATE`, and publication returns `STALE`; the disposition is to rebuild
from the accepted inputs. Reuse is allowed only when the complete corrected
identity payload reproduces the stored identity and the existing verification
passes; no pre-fix projection is grandfathered. Grouping labelled runs can
also change the payload even when individual routes were already in canonical
order. No legacy compatibility path was added, and nothing is published or
activated.

## Family map

| Member | Disposition |
|---|---|
| Unlabelled singleton references | already safe: same canonical sort, same bytes (`test_independent_citations_stay_canonically_unordered`, accepted payload hash unchanged) |
| Permutation across independent citations | already safe: runs sorted by citation (same test) |
| Route or member reorder within a citation | patched: identity-bearing (`test_route_and_member_order_are_identity_bearing`) |
| Multiple labelled routes | patched by the same run (two-route case in the same test) |
| Grouped source-order routes and the reader | patched by the reconstruction order (`test_the_stated_route_order_round_trips_through_sql`); the heavy reader tests run in CI only |
| Overridden source or destination refusal | already safe: unchanged validator and override paths; covered by the heavy candidate tests in CI |
| Stored swap: digest and gate | patched (`test_a_swapped_destination_changes_the_digest_and_fails_the_gate`) |
| Pre-fix store | fails closed (`test_a_projection_persisted_before_route_order_counted_is_stale`; pins the pre-fix UUID captured from the unfixed build) |
| Runtime reader re-verification | boundary, pre-existing: `RulesAuthorityService` trusts activation and does not re-derive identity; not changed here |

The touched test file also had 7 pre-existing strict mypy errors (object
indexing on `dict[str, object]` payloads; present at `5795e93`). They are closed
by a checked `_entries` helper, with no ignore, `Any` or weakened assertion.

## Receipts (private `linux/`, Python 3.12.3; diagnostics only, coverage off)

| Receipt | Exit | Result |
|---|---|---|
| `static-11` | 1 | Black 0, Ruff 0, mypy 7 errors (pre-existing; `head-mypy-2` shows the same 7 at `5795e93`) |
| `diag-route-1` | 0 | 519 passed across 8 test files, including committed-authority, persistence, raw-state closure and digest recording (Black checked 10 files) |
| `red-route-1` | 0 (wrapper = restore sync) | Against the `5795e93` production files pytest's native exit was 1: four tests failed on behavior, and the fifth raised `AttributeError` because the `_references_payload` seam is absent there. The restore sync exited 0 (1594 files, 0 mismatches). The pre-fix fail-closed claim rests on the pinned UUID matching the unfixed build (`route-baseline-prefix-2`: `29b1d00f…`). |
| `route-baseline-postfix-1` | 0 | identity effects above |
| `static-12` | 0 | Black 0, Ruff 0, `MYPYPATH=src mypy --strict` 0 on the 3 changed files |
| `diag-route-2` | 0 | 52 passed (retyped file) |
| `secrets-route-1` | 0 | 1 Hex High Entropy finding: a pinned pre-fix digest literal in the test (removed; the test pins only the pre-fix UUID) |
| `static-13` | 0 | Black 0, Ruff 0, strict mypy 0 on the final 3 files |
| `secrets-route-2` | 0 | 0 findings in the 5 changed files (content scan, no baseline write) |
| `diag-route-3` | 0 | 52 passed (final test file) |

Remote exact-head CI, including the complete aggregate gate, remains required
after delivery.
