# ADR-0003 — Character Sheet Architecture Correction (Issue 2a)

**Status:** Accepted
**Date:** 2026-03-31
**Issue:** 2a (GitHub Issue #24)
**Corrects:** ADR-0002 Decision 3 (naming scope)

---

## Context

Issue 2 established the character sheet as a first-class persistent object
with a base-plus-concrete structure (`RpgCharacterSheetBase` /
`Dnd5eCharacterSheet`).  That was architecturally correct.

Issue 2a identified a narrower drift: the Issue 2 implementation blurred the
boundary between the base persistence layer and the ruleset-specific layer in
two ways:

1. **`AbilityScores` was named without a ruleset prefix** despite encoding
   D&D 5e-specific validation (1–30 score range).  The generic name implied
   it was a system-agnostic universal model, which it is not.

2. **`RpgCharacterSheetBase` docstring claimed "fields common to all RPG
   systems"** — an explicit universality assertion that does not belong in a
   v1 implementation targeting a single ruleset.

3. **A `ge=0` floor was present on `current_hp`** in `Dnd5eCharacterSheet`,
   encoding a universal HP floor assumption.  Rules consequences for HP
   state (e.g. what happens at or below zero) belong to the adjudication
   layer, not the persistence model.

The active Rules Package and future adjudication layer must determine rules
meaning and legality.  The base persistence layer stores structured state and
must not make universal claims about RPG mechanics.

---

## Decision 1 — Rename `AbilityScores` to `Dnd5eAbilityScores`

**Decision:** The ability scores model is renamed from `AbilityScores` to
`Dnd5eAbilityScores`.

**Rationale:** The 1–30 validation range is a D&D 5e rule, not a universal
RPG truth.  The generic name `AbilityScores` implied a cross-system contract
that does not exist at this scope.  The explicit `Dnd5e` prefix makes the
ruleset scope clear at the type level and prevents future code from treating
the D&D 5e field structure as universally applicable.

**Scope:** This is a load-bearing schema naming change.  Any storage layer
(Issue 3) serializing model field names must account for this rename.

---

## Decision 2 — Remove the `ge=0` floor from `current_hp`

**Decision:** `Dnd5eCharacterSheet.current_hp` is typed as `int` with no
lower-bound constraint.

**Rationale:** Imposing a `ge=0` floor on the stored HP value is a
rules-adjudication claim, not a structural / data-integrity constraint.
The character sheet is a persistence model; what happens when HP reaches or
falls below zero is a rules consequence determined by the active Rules
Package.  Some house rules and tracking scenarios (e.g. massive damage
overflow) require storing negative values.  The `current_hp` cannot exceed
`maximum_hp` constraint is retained because it is an explicitly D&D 5e-scoped
constraint on this concrete model and is defensible as a data-integrity
invariant for D&D 5e state.

---

## Decision 3 — Correct `RpgCharacterSheetBase` scope language

**Decision:** The `RpgCharacterSheetBase` docstring no longer claims to contain
"fields common to all RPG systems."  It is described as a structural base for
the v1 implementation, explicitly not a universal contract.

**Rationale:** The docstring was making a universality claim that the
implementation does not support.  Broader cross-system abstractions are
deferred to Issue 5a/5b.

---

## Preserved from Issue 2

- The character sheet remains a distinct first-class persistent model.
- It remains structured and typed — not a blob or freeform dict.
- Persistent mutable character resources (`current_hp`, `maximum_hp`,
  `spell_slots`) remain on the sheet as the source of truth.
- `RpgSessionState` must not store competing copies of these values.
- All D&D 5e-scoped validators in `Dnd5eCharacterSheet` are retained; they
  are now documented explicitly as D&D 5e-scoped, not universal.

---

## Known Unknowns Not Touched

No items from `known_unknowns.md` were resolved by this issue.  All open
items remain as documented.
