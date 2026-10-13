# CRD Issue 15c — C8 schema correction check

**Verdict: the P2 conditional-profile validation finding is closed at immutable preview commit `bf3fb2d17279114b0981da13ee76fd9f1ddc88bc`.** No new code finding was identified in this bounded correction. This is code clearance only; the separate native revalidation and final packet review remain due. It grants no C8 semantic acceptance, species-input approval, real recording, main integration or dependent runtime execution.

Reviewed the two-file fix against `277a235` and the original reviewed schema code `056d3d4fdf0617a0b4539778bbcdf7fbdcb637a8`. Working bytes matched the committed validation/test files and unchanged schema files before and after the probes. Prior RAW census, source content, schema review and C7 proofs are reused.

## Correction and independent proof

`validation.py:1084–1140` now preserves each fact's option scope. A referenced profile is marked conditional when its size/type occurs in an option, under component applicability, or under that exact fact's qualifier. Such a reference refuses instead of supplying unconditional profile/type evidence. The check uses the existing `qualifier_for(fact, option_key)` contract and does not add an option evaluator, transformed-form semantics or new source policy. Structurally refused facts continue to rely on their own validation finding.

Replayed the original small in-memory controls using the installed main interpreter with explicit isolated `PYTHONPATH`, `-B` and bytecode writes disabled; verified the import path. Exact-draft and component validation still admit all the legally conditional test shapes, demonstrating that the new relational rejection addresses the intended semantic defect rather than a malformed fixture.

| Control | Corrected relational result |
| --- | --- |
| Direct unqualified Tiny/Beast profile | admitted |
| Direct unqualified Fey type where Beast is required | refused as wrong fixed type |
| Beast present only in one of two mutually exclusive options | refused: no fixed profile |
| Component-wide applicability | refused: no fixed profile |
| Type fact's applicability qualifier | refused: no fixed profile |
| Size fact's applicability qualifier | refused: no fixed profile |

Evidence: `c8-schema-review/correction-controls.json`. New committed tests in `test_creature_type_facts.py:247–287` cover the four conditional variants and retain existing positive, wrong-type and malformed controls.

## Engineer diagnostics and preservation

Read only the two relevant public tool-result entries from `issue-15c-preparation/c8-native-review-remediation-run/stream.jsonl`; no private reasoning was inspected. Preserved their exact public output in `c8-schema-review/engineer-correction-public-results.json`:

- `toolu_011FkTnjA4SaaGuYcLCvbus1`: **44 passed in 0.11s, exit 0**, “All checks passed” and mypy clean for one source file. These are focused diagnostics, not a full repository gate.
- `toolu_019CnyLvgdqzb53aHzd7PYDZ`: the old-validator negative control reports exactly **four failures / 31 passes**, naming option-arms, component-applies-when, qualified-type and qualified-size. The final committed corrected source was independently confirmed afterward.

The earlier accidental ammunition edit is absent. `_validate_ammunition_supplies` matches the pre-C8 `1d4193c` function exactly; the entire validation prefix before the new C8 helper matches `056d3d4` byte-for-byte. No older C7 validator correction remains in this commit.

`representation.py`, `projection.py` and `schema_lift.py` are unchanged from `056d3d4`. Recomputed schema 21 remains `4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55`; schema 20 remains `759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a`. The fix changes relational enforcement and regression tests, not fact payload grammar, manifested schema, source semantics or the no-movement lift.

Selected code pins:

- `src/afterworlds/ingestion/mechanical/validation.py`: `3b32df131007deb4efcba401e3b2cc012015f8703a32df670422c377a25d499c`.
- `tests/ingestion/mechanical/test_creature_type_facts.py`: `5318fe6c5c15b4fa204c1e786d4bd5b0def53a6aeca40fd55593e0939631aef6`.

## Limits and next gate

No 2,993-test repetition, pytest run, native builder, source census, store access, source/Git/network/Claude mutation or incomplete native-artifact inspection was performed. Only this report and the bounded evidence files were written. Native revalidation was still a separate in-progress activity; this review neither certifies its result nor prescribes a full regeneration. Whether actual mapped rows, payload/order identities, preserved authority and refreshed code/report pins support reuse belongs to the completed native evidence review.

The coordinator may close the schema-code P2 and continue that artifact review. Keep exact Owner acceptance and all recording/runtime/integration boundaries intact.
