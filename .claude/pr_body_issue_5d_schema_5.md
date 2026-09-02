# feat(mechanical): representation schema 5 — the roll a DC states, a consumption band, and one reading for a distance-scaled damage (CRD Issue 5d, #137)

## What was built

Representation **schema 5**, the smallest closed correction that closes the defect family the
`hazards-1` semantic review rejected: *mechanically distinct source meanings collapse or disappear
because their qualifiers or composition are not present in canonical typed authority.*

Four rules, each a closed structure rather than a predicate language:

1. **`AbilityCheckFact.context: RollContext`, required** (Owner Decision 2026-09-02, Option A).
   Admits exactly `ABILITY_CHECK` and `SAVING_THROW`. Malnutrition's DC 10 Constitution roll is a
   save; Falling's Strength (Athletics) / Dexterity (Acrobatics) alternation stays a check; a fact
   offering alternatives is itself an ability check. Not migrated onto `RollSpec` — actor polarity
   stays outside a DC source. Keyword-only so it is required without displacing `dc_value`.
2. **`ConsumptionBand`** — one closed two-sided band with per-bound inclusivity and an optional
   *sustained* duration of the band itself. `CONSUMPTION_THRESHOLD` now ranges over exactly that one
   field. Separates *"eats but consumes less than half"* (`0 < x < ½`) from *"eats nothing"*
   (`x = 0`) from *"eats nothing for 5 days"* — three rules schema 4 could not tell apart.
3. **`DamageFact.per: DamageInterval`** — the amount is dealt *per* interval, never beside a base.
   `ScalingFact` refuses `DISTANCE_FALLEN` outright and a component-level rule refuses the pair, so
   Falling has one reading: 1d6 per 10 feet fallen, capped at 20d6.
4. **A roll outcome answers to exactly one roll in its own scope.** *"On a successful check"* in a
   component that calls for no roll names the outcome of nothing.
5. **A skill qualifies an ability check, and nothing else.** The check/save axis applied consistently
   at both structures that carry a skill — `AbilityCheckFact` and `RollSpec` — through one shared
   `_check_skill_context`. A saving throw carries no skill and offers no alternatives; a skilled
   check keeps its correctly paired skill and its closed alternative set; a skill on `SAVING_THROW`,
   `ATTACK_ROLL`, `INITIATIVE` or `D20_TEST` fails closed. Refusing it on one structure alone was the
   asymmetry that deferred this rule, and one function is what removes it.

Succession `5d-lift-schema-4-to-5` is registered and resolved as a **path**: the committed
`conditions-1` artifact declares schema 3 and reaches schema 5 across two recorded crossings.

## Acceptance-criteria coverage

| Requirement | Where |
|---|---|
| 1 — required roll context, two members, alternatives rule, no `RollSpec` migration, distinct identities | `test_schema_5_representation_corrections.py` |
| 2 — partial / zero / five-day / continued accrual, no general predicate | same module + `test_schema_5_hazards_regeneration_fixtures.py` |
| 3 — one authoritative reading, schema rule + component invariant, docs reconciled | same module; docs in `representation.py`, ADR-005d, hazards closure checkpoint |
| 4 — registered succession, byte identity, no accepted `AbilityCheckFact`, 3→4→5 chain preserved, fail-closed | same module + `test_accept_across_schema_succession.py` |
| proposal-correction fixtures (5) | `test_schema_5_hazards_regeneration_fixtures.py` |
| every authority-bearing seam | `test_schema_5_persistence_and_overrides.py` |
| 5 — skill only on an ability check, both carriers, all seams | `test_schema_5_skill_context.py` |

## Test evidence

Four new modules, **118 tests** — 57 + 21 + 13 + 27, collected. Every item the issue names is covered, including: identical ability/DC
under check versus save yield distinct payloads **and** fact keys; invalid contexts and
mixed-context alternatives fail closed both directions; schema 4 rejects schema-5-only meaning for
all four carriers; the four consumption boundaries plus eight malformed bands; Falling refused as
base-plus-scaling at the fact, at the component, and inside an option arm; detached and ambiguous
roll outcomes; the 3→4→5 lift byte-for-byte over all six collections; and persistence, override and
wire round-trips for every new field through all three applicability loaders.

The skill/context correction adds: a Constitution save with no skill; Athletics and Acrobatics each
refused on a save, *correctly paired* so the refusal is about context rather than pairing; a save
offering alternatives refused for its context rather than for set-completeness; a skilled check and a
skilled `RollSpec` check still valid; every skill-free context refused on `RollSpec` with the
unskilled control in all four; the pairing rule surviving context admission; both carriers refusing
in the same words; and the wire, representation-validator, schema-binding, persistence-reconstruction,
override-patch and committed-loader seams.

**Zero-movement proof** (re-run against the final declarations):

```
lift chain           : 5d-lift-schema-3-to-4 → 5d-lift-schema-4-to-5
verified collections : all six, each step
collections moved    : NONE
spans 185 · obligations 16 · acceptances 185 · batches — unchanged
anchor               : conditions-1 @ 5d-representation-schema-3
representation       : carried by object identity
ability_check facts in accepted authority : 0   (asserted, not assumed)
committed artifact   : bytes unchanged
```

## Architecture Notes

**Deviation from design principles: none in the projection contract.** Schema 5 adds only closed
value objects and one required member of an existing closed vocabulary; `Applicability` still cannot
combine two of itself, and no Boolean predicate, executable expression, dictionary, or key/value
escape hatch was introduced. The one place the design leans on existing semantics rather than adding
structure is *"each subsequent day without food"*, which rides `ComponentDraft.applies_when`'s
declared meaning (*"when this component applies at all"*) composed with `recurs`; that sentence is
quoted in the log so a reviewer can check the inference rather than trust it.

**Three deviations are recorded rather than silent**, all in
`.claude/review-notes/pr-issue-5d-representation-schema-5-remediation-log.md` §5a:

1. **Two existing test properties are weakened**, because schema 5 disproves them. Strict growth of
   the component key set per succession and set-distinctness between versions both held
   *incidentally* across schemas 1–4, since every earlier succession happened to add a component
   key; schema 5 widens the contract without one. What actually guards the rule —
   `_emitted_component_fields` failing closed and the module-level assertion — is untouched, and
   every earlier version's row is unchanged.
2. **One stored override identity moved**: `APPEND_COMPONENT` in
   `test_review_round_5_component_patch_schema2`, because its payload carries an `AbilityCheckFact`
   and that family gained a required meaning-bearing field. The other two legacy pins are
   byte-identical, which bounds the change to exactly the meaning that widened. ADR-005d Decision 6
   behaving correctly, not a refactor leaking into stored state.
3. **Schema 4's declaration about `ScalingFact.threshold` under `DISTANCE_FALLEN` is withdrawn**, not
   left standing beside its replacement — in the docstring, in ADR-005d Decision 4, and in the
   hazards closure checkpoint. The lift module's own doctrine is corrected too: the omission rule is
   not why *this* succession moves nothing; `verify_lift` proving byte identity element by element
   is, and the row is registrable only because no accepted fact is an ability check.

**Boundary check fired and is recorded.** `.claude/review-notes/issue-5d-representation-schema-5-sibling-AUDIT.md`
puts all twenty qualifier- and composition-bearing structures to the defect family's own test:
**5 patched · 14 already safe · 1 out of scope · 0 owner decisions remaining** across 20 inspected
structures. Both owner decisions from the first cut are resolved: `AttackRollFact` is `already safe`
(the family discriminator *is* its roll context, and `attack_kind` carries the closed subtype, so a
`RollContext` field would restate one axis in two places), and a skill under a saving throw is
**patched** on both structures that carry a skill. The count is 14 rather than the 15 anticipated
because only one of the two reclassified rows became `already safe` — the other was implemented; the
audit reconciles the arithmetic to the rows rather than to the expectation.

**No migration.** Schema 5 adds no component key: `context` and `per` ride the family-keyed fact
payload, `band` rides the existing `rp_mech_components.applies_when` JSON column. Proved by round
trip against a real session rather than asserted from the column types.

## Stop condition

This PR mints and proves a schema. It **accepts nothing**: `accept_proposal` is never called,
`oracles/` is read and asserted byte-unchanged, proposal `6277ff73…a259` is not reused or blessed,
nothing is published, activated or retired, and `actions-1` is not begun. `hazards-1` will be
regenerated from the bound 5c source after this is Owner-merged, and will receive a new identity and
a fresh semantic review.
