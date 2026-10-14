# Schema 22 delta: `creature_skills` (CRD Issue 15b, candidate C9)

**Plan, with a local preview implementation for review. Nothing here is accepted or recorded.** Main stays
on accepted C8 at schema 21.

## Type surface

| Element | Shape | Manifested invariant |
| --- | --- | --- |
| `CreatureSkillBonus` (new value shape) | `skill: Skill`, `ability: AbilityScore`, `bonus: int` | `ability` is the skill's usual ability (`SKILL_ABILITY`), the one pairing the printed total is for. Both vocabularies already exist, so no member is added |
| `CreatureSkillsFact`, family `creature_skills` | `skills: tuple[CreatureSkillBonus, ...]` | entries are distinct by skill and sorted by `skill` value. **Empty is legal**: it states that the stat block prints no Skills entry (interpretation S1) |

**The relational rule** lives in `validation.validate_representation`, on the C8 `summoned_creature_type`
terms. A `creature_skills` fact may sit only on a creature profile, meaning a component of a `creature`
record that carries `creature_size`. That component may carry at most one such fact. A fact refused by
its own invariants is not judged relationally; its own refusal is the finding.

**What the schema does not do.** It does not require every profile to carry the fact. Completeness is
a property of the accepted content, and C9's `validate_c9.py` proves it for the release. A profile
without the fact is *missing authority*, and the consumer refuses it. That gap is exactly what the
absence/missing distinction needs.

**The lift** is `5d-lift-schema-21-to-22`. It moves nothing:
- one new family;
- one new value shape;
- no field on any accepted family;
- no component key;
- no vocabulary member.

`verify_lift` proves byte identity element by element. A schema-21 declaration that carries the new
family is refused by the introduction manifest.

## Consumer contract

This is execution under 15b Group 17, held until C9 is recorded. Every rule below reads accepted facts
only; nothing reads prose at play time.

| A creature's check | Bonus |
| --- | --- |
| Skill listed in its `creature_skills`, used with its usual ability | the printed `bonus`, complete. Ability modifier, PB and Expertise are never added (interpretation S3, qualified in r2) |
| Skill listed, used with another ability (for example Strength (Acrobatics)) | **refusal before any die**, unless separately supported authority exists. This is a bounded adapter exclusion: the source permits the pairing (`playing-the-game.md`:239), but the printed total is not decomposable (Assassin, `monsters-A-Z.md`:532) |
| Skill not listed; the fact is present | not proficient. The chosen ability's modifier under any pairing: the printed modifier where the accepted `creature_ability_score` fact records one, otherwise the score's modifier by the certified `play.six_abilities/ability_modifiers` rule |
| No skill (a plain ability check) | the ability's modifier, as above |
| The profile carries no `creature_skills` fact | refusal, `MISSING_AUTHORITY`, before any die |

**Contributors still apply or refuse as they do for every creature roll.** That covers typed
`creature_roll_modifier` traits (for example Keen Senses), conditions and unexecuted effects. The
fact types the printed Skills entry only.

**Forms are carried from C8:**
- A Shape-Shift that keeps game statistics, and the Vampire's bat form, read the base profile.
- "Another stat block" forms read their own template.
- The Vampire's mist form stays held.

## Why the schema code is not in this PR

The schema code would break the active release, so it is not in this PR. Moving
`REPRESENTATION_SCHEMA_VERSION` to 22 before a recorded C9 successor exists has two consequences:

1. The accepted C8 projection can no longer validate as current authority. `projection.py`:1421
   requires the candidate's schema to equal the build's.
2. The release's projection identity moves when C8 is lifted. The C8 preview recorded this precedent:
   C7, projection `8446ab6b…`, lifted to schema 21 became `7ea06d93…`.

`capability.CERTIFIED_RELEASE` pins C8's projection `e4f8f4fb…`, so every certified 15c operation would
refuse as `INCOMPATIBLE_CERTIFICATION`. The local preview branch demonstrates this; see `README.md`.

C8 handled the same sequencing this way: schema 21 was a preview commit (`e4221ded`), and it landed
together with the recorded successor (`183a664e`) and recertification. C9 follows that sequence. The
schema code lands with the recorded C9 successor, after Owner acceptance of the exact native packet.

## Native stage

**Status: now built.** Packet: preview branch `codex/issue-15b-c9-schema-preview` @ `002de94d`, `.claude/review-notes/issue-15b-c9-native/README.md` (preview oracle `3ad7bdcb…`, projection `3703faf5…`, report `c9-packet.json` `d61ed1b4…`). Its builder, `issue-15b-c9-native/build_c9_preview.py`, reads private, pinned copies of the inputs below; Codex authorized that read-only reuse on 2026-10-14. The original plan follows.

### Plan as written for r1

After raw review clears C9, the native SIMULATED preview has this scope:
- rebuild four proposals at schema 22: monsters (235 facts), animals (95), spell-descriptions (4) and
  magic-items (2);
- add 336 provenance claims and expected rules;
- excise and re-accept those four batches in anchor order;
- record one `21→22` lift;
- round-trip private-store copies;
- assemble a pinned packet.

**Cost.** C8 rebuilt five batches, including monsters and animals, in 849 s. Expect about 15 minutes.

**Why it is not started.** It needs inputs this assignment may not use:
- the C8 builder read git-ignored accepted proposals from preserved preview worktrees;
- it read a copy of the isolated release store `g1-work/rel/afterworlds.db`.

Codex must authorize those inputs, or equivalent regenerated ones, before the native stage begins.
