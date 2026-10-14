# C8 — proposed schema-21 delta (document only; nothing applied to `src`)

**Status.** This delta would be prepared in an isolated worktree at the native stage, after Codex clears the raw candidate. It is not applied to `src`. The accepted schema 20 (`759dcc1f…`) and C7 stay as they are.

## One new closed family

```python
class CreatureTypeKind(StrEnum):  # the 14 Creature Types, rules-glossary.md:515
    ABERRATION = "aberration"; BEAST = "beast"; CELESTIAL = "celestial"
    CONSTRUCT = "construct"; DRAGON = "dragon"; ELEMENTAL = "elemental"
    FEY = "fey"; FIEND = "fiend"; GIANT = "giant"; HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"; OOZE = "ooze"; PLANT = "plant"; UNDEAD = "undead"


@dataclass(frozen=True, kw_only=True)
class CreatureTypeFact:
    """A creature or species' printed creature type: one type, or the types a
    creator chooses among (*"Celestial, Fey, or Fiend (Your Choice)"*).
    The type only: descriptive tags stay prose, and their absence states
    nothing (for example, about being an elf)."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_TYPE
    type: CreatureTypeKind | None
    type_choice: tuple[CreatureTypeKind, ...]
```

**Vocabulary.** The values equal the 2b state vocabulary `models.dnd5e_vocabulary.CreatureType`. Native preparation would choose between two options:
- reuse that enum;
- or declare a representation enum and add a test pinning the two equal.

`TargetTag` is **not** reused. It is predicate vocabulary that mixes types, a species tag and "enemy".

**Intrinsic invariant** (manifested, so it is inside the schema hash): exactly one of the following holds:
- `type` is set and `type_choice` is empty;
- `type` is `None` and `type_choice` has at least two values, distinct and sorted.

**Applicability:**
- **Creature templates:** the fact sits on the profile component that already holds `creature_size`. **r2 correction (codex-c8-raw-review P2):** all 336 profile components are already `mixed`. Each keeps its existing handling, facts, options, prose retention reason and prose bindings; only the type fact and its provenance are added.
- **Species:** the fact sits on the prose-bound `creature_type` component, which becomes `mixed`. Its prose and retention reason are kept, as C7 did for its gear components.

**Lift:** `5d-lift-schema-20-to-21` is registered and moves nothing.

**No other change:**
- No field is added to an accepted family.
- No vocabulary is changed.
- The accepted schema-20 descriptor is untouched.

## A second closed family: the Find Familiar source choice (r2)

```python
@dataclass(frozen=True, kw_only=True)
class SummonedCreatureTypeFact:
    """A source that gives a creature it brings a type chosen among several,
    instead of its form's own type (Find Familiar: *"though it is a
    Celestial, Fey, or Fiend (your choice) instead of a Beast"*), for the
    named forms only. It is target authority for an existing familiar, not
    casting, creation, lifecycle or an attack grant."""

    FAMILY: ClassVar[FactFamily] = FactFamily.SUMMONED_CREATURE_TYPE
    type_choice: tuple[CreatureTypeKind, ...]
    instead_of: CreatureTypeKind
    forms: tuple[ComponentReference, ...]
```

**Placement and handling:** on `spells.find_familiar/effect`, which goes from prose-bound to `mixed`.

**Intrinsic invariant** (manifested): `type_choice` has at least two values, distinct and sorted; `forms` is non-empty, distinct and sorted.

**Relational rule** (`validate_representation`, as C7's `ammunition_supply`): each form is a component of the draft, carrying a `creature_type` whose `type` equals `instead_of`.

**Why it is separate from `creature_type`:** a template's own fixed type is never overridden generically. The departure is qualified by its source, so it is valid only for a creature whose `summon.source` is this spell and whose template is one of the named forms.

**Held:** "another Beast that has a Challenge Rating of 0" (no accepted fact types a Challenge Rating).

## Later dependent implementation

This is held until the Owner accepts the exact native packet. It is listed here only so its cost is visible.

**Ghast and Ghoul rider saves (`creature_attacks._check_rider`).** Read the target's type, then:

| Target | Type comes from | Exclusion |
| --- | --- | --- |
| A creature | its own binding's template `creature_type` | Undead suppresses the rider |
| A character | its validated species' `creature_type` | Undead suppresses the rider. Ghoul only: an exact `character_origins.elf` species also suppresses it. |
| A Ghoul's non-Undead creature target | — | Elf status is not represented, so it is **held** and refuses before any die (see the README) |

Hit damage applies whether or not the rider is suppressed.

**Familiar target type.** A creature's type is its stored `CreatureState.creature_type` only when all of the following hold. Otherwise the stored departure refuses before any die.
- its `summon.source` is `spells.find_familiar` (the record);
- its template is one of the fact's named forms;
- that stored type is in `type_choice`.

**Refusals before any die:**
- a missing type fact;
- a `type_choice` template whose stored `CreatureState.creature_type` is missing or not in the choice;
- a stored type departing from a fixed template type;
- unexecuted form effects.

**Vampire.** A vampire target is read by its recorded template: Undead, which its bat form keeps. No state records a mist form and no operation executes one, so no refusal path is claimed for it. The mist form's type stays an explicit hold, to be settled if a form state is ever represented.

**Certification:** `creature_type` components join `creature_attack`'s governing set, per subject, through the template certification already in place.

**Tests:** the positive and negative proof the classification lists:
- a valid target, with damage and the rider;
- an excluded target, with damage and no rider;
- missing or contradictory authority, refused with zero dice;
- a wrong or stale binding;
- target state advanced earlier in the turn.
