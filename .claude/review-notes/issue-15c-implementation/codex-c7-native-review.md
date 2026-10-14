# CRD Issue 15c — independent native C7 review

Verdict: the exact nine-fact semantic delta is cleared; bounded validator and packet corrections remain before the final Owner gate. No Owner acceptance or real recording has occurred.

Reviewed preview worktree `agent-afb6123d0b7851456` at `ed23cb77fbd4e561b20c718fcb068df15b4de797` (schema source unchanged from `2d9f694941985dab14229b5e31005a1f9c0a8327`). Governing #191 draft SHA `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`; Owner ammunition instruction `owner-ammunition-inclusion-2026-10-12.md`. Applied installed Afterworlds Review 2026-09-25 and routing 2026-09-26, reusing the Library sources already verified for this coherent task under the routing reuse rule. Codex reviewed source/delta/preservation; a bounded Astra-high worker independently inspected schema/validator/lift changes. Claude remains the engineer.

## Exact reviewed identities

- Raw C7: `bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77`.
- Native preview file: `d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d`.
- Schema 20: `759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a`.
- Oracle identity: `cb04163ba0374e95ce0fcdaae939b00793e71f84ed3222593c4babfc9065ef6e`.
- Projection: `8446ab6b-be75-5999-8a9b-74fa133c030a`; payload `cffcdbfa70a6e64351b852ff9b932aa32df81abdd45700ef6c0034aefdaeb65a`.
- Immutable recorded C5 remains SHA `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69`.

## Verified semantic and preservation result

The four Origin-category facts equal the unaccepted C6-r2 content and printed `feats.md:23,33,47,53`. The five ammunition supplies correspond to `equipment.md:1218,1225,1232,1239,1246`, with the existing weapon-side kinds. Sling bullets narrow to Sling; firearm bullets narrow to Musket/Pistol. The latter is the disclosed source inference I2, supported by the separate bullet rows, the three Bullet weapon users, and `character-creation.md:849`; the source does not literally mark Musket/Pistol as firearms. The acceptance decision covers that inference with the rest of C7, not a second product-policy vote.

Independent read-only inspection (`inspect_c7_native.py`) confirmed: exactly nine components change only from prose-bound/no facts to mixed/the exact raw fact; all other component values and their relative order are retained; nine contextual provenance claims and nine ExpectedRules are added with no old claims/rules removed. The other representation collections are exactly unchanged. All 22 unaffected batches' ordered acceptance records, review-unit records and anchors are unchanged, and all 24 batch positions are retained. Touched batches preserve scope and disposition and use SIMULATED receipts. Existing lifts are unchanged with exactly 19-to-20 appended. Release/source/policy/reference identities and every reported pin remain exact. Obligations change only for the nine fact records.

Native parser/serialization and independently computed schema/oracle/projection/payload identities match the packet. Existing builder evidence reports zero candidate findings, native private-store round trips, own-gate success and both cross-oracle refusals. The builder's twice-run determinism and engineer's independent identical report are existing evidence, not rerun by Codex. No store, proposal, oracle or acceptance was created by this review. No tests/full suite/CI were run. These checks do not certify execution or merge readiness.

## P2 — relational reader observes already-refused ammunition structure

MERGE-BLOCKING DEFECT / implementation work, malformed-input refusal family. `validation.py:1040-1041` iterates `supply.for_weapons` and reads each member as a ComponentReference without structural admission. `validate_representation` collects `_validate_components` findings but subsequently calls this relational reader; `validate_candidate` likewise accumulates schema findings before continuing.

An exact `AmmunitionSupplyFact(kind=BULLET, for_weapons=(0,))` returns `for_weapons[0] must be ComponentReference, got int` from `fact_invariant_violations`, yet the relational reader raises `AttributeError: 'int' object has no attribute 'record_key'`. Codex reproduced that pure read-only path; the worker independently identified it statically. A rejected container or weapon-kind value must also not be re-observed by the new pass.

Retain the collected refusal and admit supply/weapon-property structure before relational observations. Cover malformed tuple members, tuple subclasses and invalid weapon-side ammunition values through the public validation path. This needs no schema redesign and should not change the valid preview's semantic identity. Reuse unaffected native evidence; demonstrate whether any corrected guard changes actually invalidate hashes before rebuilding.

## Packet corrections — settled specification, no new Owner Decision

`OWNER-PACKET.md` currently asks acceptance of C7 and then a separate acceptance of I2. Present ONE exact consolidated acceptance including disclosed I2, as the Owner instructed. Narrow "everything else byte-identical" to the verified preservation plus explicitly listed schema/receipt/obligation changes. Its final sentence must not describe action accounting and hand/grip as unresolved Owner boundaries: those inputs are approved and implementation now exists in the main checkout. Distinguish the candidate's recording gate from subsequent engineering verification; existing authority already permits dependent implementation once the exact semantics are accepted, without another execution-policy vote.

C6/r2 original artifacts stay preserved and unaccepted; C6-B remains withdrawn. Ammunition recovery remains excluded. No merge, shared-runtime migration, publication/activation or app launch is authorized.

## Claude-ready bounded correction

You are remediating the native C7 validation/packet review for CRD Issue 15c, not redesigning the candidate. Read this note and preserve the exact reviewed semantic content, immutable C5 and all original C6/r2 artifacts. Repair only the new relational reader's admission-order defect, retaining refusals and proving malformed structure cannot crash or be observed after rejection. Correct the packet to one consolidated exact semantic acceptance, including I2's disclosed inference and the current approved implementation boundaries. Report the changed source/packet hashes and relevant regression evidence; reuse the preview/native evidence if the correction leaves their identities unchanged. Do not record or execute new C7 authority before explicit Owner acceptance. Continue unrelated authorized implementation. No full-suite rerun for this correction; final exact-head gates remain separately required. Do not merge or touch shared runtime/publication/activation.
