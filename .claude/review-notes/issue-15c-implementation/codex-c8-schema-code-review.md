# CRD Issue 15c — bounded C8 schema-code review

**Verdict: one P2 relational-validation correction remains at committed preview `056d3d4fdf0617a0b4539778bbcdf7fbdcb637a8`.** The two-family parser, intrinsic manifest, introductions, prior schema contract and no-movement serialization/lift structure otherwise match the adopted RAW-r2 delta. The finding does not alter any of the reviewed 346 RAW payloads or invalidate their source census. Native build outputs were deliberately not inspected: the build was still running, so this is not a native-packet review.

Scope: immutable `056d3d4` versus `1d4193c4b162e3db4df3a3240d00313f36dd918b`, in `.claude/worktrees/agent-aa5b1ea6bf4ee4f39`. Read the adopted RAW-r2 review/native-preparation request, the four changed production files, changed tests/fixture/pins and `.gitignore`. Reused C7 acceptance/recording proof and C8 RAW content proof. Main schema integration, Owner acceptance, species-input policy, recording, runtime implementation and merge remain held.

## P2 — Do not establish a fixed form type by flattening conditional scopes

**MERGE-BLOCKING DEFECT; disposition: bounded implementation correction.** In preview `src/afterworlds/ingestion/mechanical/validation.py:1093–1110`, `_validate_summoned_creature_types` combines direct facts and all option facts into one sequence, collects size/type from anywhere, and `:1121` then treats a singleton matching type as the referenced profile's fixed `instead_of` type. It also does not inspect component applicability or the qualifying facts' own applicability. This can certify the required fixed Beast relationship from a conditional statement.

The existing schema explicitly says each `ComponentOption` is mutually exclusive (`representation.py:15442–15448`), component `applies_when=None` means unconditional (`:15568–15569`), and fact qualifiers compose conjunctively with enclosing scopes (`:15507–15536`). The new reference is only a record/component key; it selects neither an option nor a condition. Therefore a Beast claim in one arm cannot establish the whole component as the fixed Beast form that the new relation requires.

Independent in-memory counterexample, with the intended positive/negative controls:

| Referenced creature profile | Exact draft checks | Component checks | New relational result |
| --- | --- | --- | --- |
| Direct Tiny size + fixed Beast type | clear | clear | clear (correct positive) |
| Direct Tiny size + fixed Fey type | clear | clear | refuses “not exactly beast” (correct negative) |
| Two legal options: first has Tiny size + Beast type; second has Small size and **no type** | clear | clear | **clear (incorrect)** |
| Direct size/type under component applicability `PHASE/WHILE_ACTIVE` | clear | clear | **clear (not fixed)** |
| Direct Beast fact with its own `PHASE/WHILE_ACTIVE` qualifier | clear | clear | **clear (not fixed)** |

The same bounded sibling inspection also found that a qualified size fact is counted as unconditional profile evidence. Results are in `c8-schema-review/form-scope-probe.json` and `qualifier-scope-probe.json`. These exercise the new helper together with the production exact-draft/component checks; they are not claimed to be complete source/provenance/store acceptance fixtures.

**Smallest sufficient correction:** for this bounded family, establish the reference only from an unambiguous, unqualified creature profile/type relationship. Refuse option-dependent or applicability-dependent evidence that the `ComponentReference` cannot resolve, rather than implementing new option/form evaluation. Apply the same rule to the size evidence used to identify a creature profile. Preserve valid direct profiles and the existing malformed/wrong-type refusals. Add focused controls for the demonstrated choice and component/fact qualifier cases; do not extend the source/fact roster or invent a form policy.

This is one defect family—conditional authority promoted to unconditional authority—not another RAW semantic decision. Current C8 named forms are direct, unconditional accepted profiles; the correction need not rebuild or re-review the 345/346 source content. Let the coordinator determine what the correction actually invalidates in completed native evidence/code pins. This report does not request terminating or automatically repeating the running build.

## Checks that support the remaining code

- `CreatureTypeFact` and `SummonedCreatureTypeFact` are registered in the closed fact union, builders, invariant checker and introduction manifest. Fourteen closed type values match the state enum by an explicit test. The existing declared JSON builder and typed checker enforce exact strings/enums, arrays/tuples, nested references and unknown/missing field rejection before family rules read them (`representation.py:12310–12376,12565–12634`).
- Fixed type versus at-least-two choice is exclusive. Choices and form references are nonempty where required, sorted and unique; the new source-choice invariant additionally refuses offering the same type it says it replaces (`:12786–12809`). This restriction is explicit in the intrinsic manifest. It does not change any C8 payload.
- Schema-20 declarations still refuse both new families and the new vocabulary. The schema-21 serialization rows preserve existing component keys, record-owned references, option prose, prose retention and alternative-reference behavior (`projection.py`). No existing draft vocabulary or component/reference descriptor changed.
- Independent descriptor comparison using verified imports from main schema 20 and preview schema 21 found every prior fact descriptor, introduction row and invariant row preserved exactly; only the two new families and their new contract rows were added. Schema 20 remains `759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a`; schema 21 is `4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55`. See `c8-schema-review/descriptor-delta.json`.
- The registered `5d-lift-schema-20-to-21` uses those exact hashes. The existing `verify_lift` still rejects inadmissible prior meaning before comparing canonical bytes collection by collection (`schema_lift.py:999–1049`). The bounded fixture changes only the added lift receipt and terminal schema pair; it does not change represented content. The current test pins and explicit crossing expectations were advanced; old unknown-version refusal probes moved to version 22 rather than being deleted.
- New tests provide genuine illegal-choice, duplicate/sort, wrong/unknown/missing form, wrong type, non-profile, schema-version refusal and manifested-control cases. They do **not** exercise the conditional-scope gap above. The supplied 2,993-pass / 641.92-second / exit-0 focused result is reused as engineer diagnostics, not independent full-gate acceptance; it was not rerun.
- `.gitignore` adds only the generated C8 preview directory. It does not hide source, scripts, tests or the other review reports, and changes no secrets/CI gate.

Mixed/prose conservation is preserved by the unchanged serialization contracts, but **actual** C8 mixed-profile mapping, Familiar/species retained prose, exact facts/claims, nineteen unchanged ordered receipts, C7 no-movement replay and private-store round trips remain native-packet proof. No incomplete native artifacts were used to infer success.

## Pins, limits and Claude-ready correction

Reviewed file bytes matched immutable commit `056d3d4`; no working source changes were found during this review. Selected SHA-256 pins:

- `src/afterworlds/ingestion/mechanical/representation.py`: `7f0abd45113548f32f35ee6d58cf986a8cea59877b63995cfedd96ac2a0f052c`.
- `src/afterworlds/ingestion/mechanical/validation.py`: `d770b26c293f6ee3b7792f8c09f9c10d28ed1402a423921959afc851b7e377a7`.
- `src/afterworlds/ingestion/mechanical/projection.py`: `56a9b0cfe17d5757aa74698a8acc68db2fc9acaa4ce7ea33273c399f27486df4`.
- `src/afterworlds/ingestion/mechanical/schema_lift.py`: `46df4ccb1e4418c955358f195c798ddf9dd4a6b53709492fd6cfb0a87e44d00f`.

Read-only/in-memory probes used main's installed `venv/Scripts/python.exe -B`, `PYTHONDONTWRITEBYTECODE=1`, and explicit preview `PYTHONPATH`; verified `afterworlds.__file__` points into the isolated preview. Descriptor comparison separately verified main and preview imports. No pytest, full suite, native builder/rederive, stores, network, source edits, Git mutations or Claude actions were performed. Only this report and bounded review outputs under main's `c8-schema-review/` were written.

> Correct the new C8 summoned-type relation without extending its semantics. A component reference must not establish a fixed replacement type by collecting facts from mutually exclusive options or conditional component/fact scopes. Preserve the cleared direct profile control and existing exact-type/wrong-type refusals; add focused regression evidence for the demonstrated conditional cases. Keep the 346 RAW facts, accepted C7/schema-20 contract and all prior artifacts intact. No form engine, species policy, runtime execution, acceptance or recording is authorized. Report the bounded source/test delta and which native evidence/code pins actually need refreshing; do not automatically repeat unaffected expensive work.
