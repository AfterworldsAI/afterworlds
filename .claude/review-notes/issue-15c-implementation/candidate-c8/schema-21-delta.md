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
- **Creature templates:** the fact sits on the profile component that already holds `creature_size`. That component's handling stays `structured`.
- **Species:** the fact sits on the prose-bound `creature_type` component, which becomes `mixed`. Its prose and retention reason are kept, as C7 did for its gear components.

**Lift:** `5d-lift-schema-20-to-21` is registered and moves nothing.

**No other change:**
- No field is added to an accepted family.
- No vocabulary is changed.
- The accepted schema-20 descriptor is untouched.

## Later dependent implementation

This is held until the Owner accepts the exact native packet. It is listed here only so its cost is visible.

**Ghast and Ghoul rider saves (`creature_attacks._check_rider`).** Read the target's type, then:

| Target | Type comes from | Exclusion |
| --- | --- | --- |
| A creature | its own binding's template `creature_type` | Undead suppresses the rider |
| A character | its validated species' `creature_type` | Undead suppresses the rider. Ghoul only: an exact `character_origins.elf` species also suppresses it. |
| A Ghoul's non-Undead creature target | — | Elf status is not represented, so it is **held** and refuses before any die (see the README) |

Hit damage applies whether or not the rider is suppressed.

**Refusals before any die:**
- a missing type fact;
- a `type_choice` template whose stored `CreatureState.creature_type` is missing or not in the choice;
- a stored type departing from a fixed template type;
- a vampire (form-dependent);
- unexecuted form effects.

**Certification:** `creature_type` components join `creature_attack`'s governing set, per subject, through the template certification already in place.

**Tests:** the positive and negative proof the classification lists:
- a valid target, with damage and the rider;
- an excluded target, with damage and no rider;
- missing or contradictory authority, refused with zero dice;
- a wrong or stale binding;
- target state advanced earlier in the turn.
