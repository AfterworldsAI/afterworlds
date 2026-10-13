# CRD Issue 15c — C8 r2 changed-delta RAW review

**Verdict: clear for isolated schema-21 preparation and a private SIMULATED native preview.** The two previous RAW corrections are closed, and the added Find Familiar fact preserves its source qualifications. No new blocking RAW finding was found. This clearance is not semantic acceptance, native equivalence, successor recording, type-dependent execution, or full Ghast/Ghoul acceptance coverage. The separate creature-species policy remains unapproved.

Reviewed immutable HEAD `1d4193c4b162e3db4df3a3240d00313f36dd918b`; it remained current at the final check. Reused the full governing authority and Library versions already read for `codex-c8-raw-review.md`. This is a changed-delta review only: the original 345-fact census, source interpretation and membership proof were not regenerated or re-reviewed. The separate gameplay and secrets-baseline changes in the same commit were not reviewed here.

## Closed corrections and conservation

1. **Mixed profile handling — already safe in the corrected contract.** `candidate-c8/schema-21-delta.md:38` now preserves all 336 profiles' existing mixed handling, prior facts/options, retention reasons and prose bindings, adding only type facts/provenance. The C8 schema metadata agrees. Species components remain the intended prose_bound → mixed additions. No accepted component has yet been rewritten; actual preservation remains part of native correspondence/replay proof.
2. **Vampire — source classification corrected.** Base type remains direct Undead (`monsters-A-Z.md:17626`); bat retention is explicitly I2 at `:17725`; mist has a separate form-state/semantics hold based on the full paragraph at `:17726`. No blanket base-Vampire hold remains. The packet does not claim an implemented mist refusal path. This represents the bounded current target semantics and does not execute forms or permit an unexecuted active effect to be ignored.
3. **Original work preserved.** Independent byte comparison with commit `f8be6caa8b6d3dc7e86c2d7c23b50718869ee2ba` found all eight files under `candidate-c8/r1/` exact matches: README, candidate, correspondence, inventory, schema plan, derivation script, validation script and validation output. The entire original 345-fact payload list is identical in r2. The only changed original correspondence field is Vampire's form disposition (`held` → `bat:kept;mist:held_form_state`); there is exactly one added correspondence row. Source/C7 pins are unchanged and still match current bytes.

## Find Familiar's added fact

**Already safe / no further RAW correction.** `candidate-c8/schema-21-delta.md:50–73` proposes one new `summoned_creature_type` family rather than turning a template's fixed type into a generic override. The one fact sits on the exact existing `spells.find_familiar/effect` component. Its quote equals the entire pinned `spells.md:2290` line.

- The eleven references are exactly Bat, Cat, Frog, Hawk, Lizard, Octopus, Owl, Rat, Raven, Spider and Weasel, in stable order with no duplicates. Each exact record/component exists and its already-reviewed C8 base type is Beast.
- `instead_of=beast` and `type_choice=[celestial,fey,fiend]` preserve the explicit source departure. The choice is source-qualified by the spell identity/component. Runtime use is expressly conditioned on the creature's exact `summon.source`, an admitted named form and a recorded allowed type (`schema-21-delta.md:71,89–92`). No generic creature-table inference, arbitrary enum override or familiar attack grant is introduced.
- Its claim spans exactly equal the existing component's C7 prose-binding span set; every span belongs to the already changed `spell-descriptions` batch. The prior component is prose_bound, facts/options empty, with retained prose reason `no_identified_structured_use`. Native preparation must preserve that prose/reason/binding context while moving it to mixed and adding the one fact.
- The declared schema invariants are sufficient for this payload: closed type enums; sorted, distinct choices of at least two; nonempty sorted, distinct component references; and a relational check that each referenced creature profile carries a fixed type equal to `instead_of`. C8 schema metadata says “creature profile”; the native validator must enforce that scope as well as reference existence. Actual invariant enforcement and negative controls are native-stage proof, not supplied by a valid RAW instance.
- The source's additional **“another Beast that has a Challenge Rating of 0”** branch is retained in the full quote and expressly held because CR authority is not typed. It is not silently discarded or advertised as covered. This bounded finite named-form fact does not claim to encode the spell's complete selection domain. Missing/contradictory source, form or selected type remains a refusal before dice; a missing familiar choice cannot fall back to the template's Beast type.

The added source choice costs **one fact/component in the existing spell-descriptions batch**: five spell components instead of four. Total is **346 facts, five changed batches, nineteen reused batches**. It adds one closed family to the previously proposed type-assignment family within schema 21; no accepted family or schema-20 descriptor needs to change. No additional source group, general casting, summoning lifecycle or form engine is admitted.

For the future dependent path, exact binding/certification must cover both the selected form's type component and the source spell's new choice component under the target's authority. The new family does not make an arbitrary stored `creature_type` trustworthy. These are applications of the existing issue/RAW contract, not new Owner decisions or permission to implement before acceptance.

## Species-input boundary remains held

`candidate-c8/owner-proposal-creature-species.md:3` and the coordinator's `owner-creature-species-input-proposal.md` both explicitly say proposed, not approved or implemented. They limit the proposal to exact accepted species identity, code-generated compatible options, the creature's own binding/revision, source-open individual species, audit and invalidation. They do not add taxonomy facts to C8, establish absent-tag negatives, grant species traits or authorize type changes. The separate Owner gate is truthful and does not block this type-only native preparation.

Before any later implementation, eligibility must be established from source-open template authority, not merely a Humanoid label plus absence of a species tag; the coordinator proposal states this explicitly. Current species-dependent Ghoul operations remain held where identity is unresolved. Such refusals and the unrepresented CR-0/form branches are not positive AC2/4/7 coverage. The existing promised admissions remain intact.

## Evidence and limits

Independent bounded output: `candidate-c8/codex-review/correction-inspection.json` (archived byte checks, payload conservation, exact changed correspondence, Familiar component/bindings/eligibility and current pins).

| Artifact | SHA-256 |
| --- | --- |
| C8 r2 RAW | `7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628` |
| r2 correspondence | `43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24` |
| r2 inventory | `3f05591efa78656132db3a179f174b560ca3e8f3d3ebfd525e56b400e87ce55d` |
| Engineer r2 validation | `c4e1c3ecbaf162cac3fb8f30e4625fca46ec8aa2084a000280168d0b9fb03e61` |
| r2 schema plan | `1c33046c692692f48e63766e61fa6f2b7785b9118f50db241503f5868223b1b5` |
| Preserved accepted C7 | `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` |

Checks were static source/document reads, raw Git diff/show, standard-library JSON/byte inspection and hashes using this checkout's Python. The engineer's supplied validation output was inspected, not rerun. No tests, derivation, native generation/replay, project imports, stores, source/code edits, Git mutations or network operations occurred. Only this report and its new bounded inspection output were written. Native reference validation, manifested invariant controls, exact preservation/conservation, no-movement lift and private replay remain due at their proper stage; prior unaffected proofs should be reused.

**Authorized review conclusion:** the coordinator may now continue isolated schema preparation and private SIMULATED native minting for this exact r2 delta. Bring back the pinned native packet for independent review and explicit Owner semantic acceptance. Preserve C1–C8 r1/r2 evidence and C7 authority; no real recording, dependent execution, policy implementation, publication/activation or merge follows from RAW clearance.
