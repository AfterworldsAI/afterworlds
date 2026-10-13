# CRD Issue 15c C8: superseding planning addendum on Ghoul target domain

**Status: planning correction only.** This adopts `../issue-15c-implementation/codex-elf-type-domain-classification.md`.

**What it supersedes.** It replaces the dependent-coverage wording in these files:
- `candidate-c8/README.md` ("Held", item 1);
- `candidate-c8/schema-21-delta.md` ("Later dependent implementation", the Ghoul's non-Undead row);
- `candidate-c8/owner-proposal-creature-species.md` ("The gap" and "If no").

Those files stay byte-identical, as pinned RAW-r2 evidence (`schema-21-delta.md` is a build pin, `1c33046c…b1b5`).

**What it does not change:**
- no RAW payload, schema, preview byte or identity;
- no acceptance, species-input approval or runtime implementation.

## The corrected statement

The earlier wording overstated the gap. It said: "Ghoul Claw against a creature that is not Undead is held; every such target needs species input."

**The deduction.** After exact C8 acceptance, an ordinary target whose authoritative, applicable base type is non-Humanoid is **non-Elf**. This follows from the contrapositive of the represented assignment Elf ⇒ Humanoid:
- the source makes type a species trait (`character-origins.md:77–81`);
- it assigns the Elf Humanoid (`:180–186`), and C8 represents that assignment.

This is a code-owned deduction from accepted facts. It is not a new negative-taxonomy fact or an Owner policy. It never reasons from a missing tag, a name or the converse.

| Target proof | Ghoul elf/type determination | Disposition |
| --- | --- | --- |
| Character with an exact validated Elf species | Elf: rider suppressed, hit damage kept | Existing identity path |
| Character with another exact validated species | Not an Elf | Existing identity path |
| Validated applicable Undead type | Undead exclusion settles the rider | After C8 acceptance |
| Ordinary creature: certified fixed non-Humanoid, non-Undead base type and validated unchanged state | Not an Elf, by the contrapositive; the rider stays eligible | **Settled implementation after C8 acceptance. No Owner policy.** |
| Ordinary Humanoid with no established individual species (source-open role/profession, `monsters.md:55`) | Type cannot decide | **Held**: the one remaining Owner input question |
| Humanoid whose species is claimed by name, description or a missing tag | Not established by that claim | Inspect the actual typed identity; not auto-enrolled in the input policy |
| Find Familiar named form, with exact source, permitted form and allowed recorded type | Celestial/Fey/Fiend supports not-Elf | After C8 acceptance, with exact source/form/choice validation. Settles type only |
| Otherworldly Steed with its recorded permitted type | Non-Humanoid choice supports not-Elf | A missing choice refuses. Parameterized AC and other inputs stay independent holds |
| Retained-type monster form | A proved unchanged type may be used | Never the visual form's header |
| Unresolved form, unexecuted contributing effect, contradictory type, unrepresented choice, missing state or authority | No inference | Refuse before any die and name the actual hold |

### What must prove the ordinary domain (later implementation)

- **Use the subject's own state:** its exact binding, certified profile/species facts, current revision and applicable recorded state.
- **Absent is not empty.** Recorded empty effects (`()`) are not the same as unrecorded effects (`None`). None of these proves "unchanged": an absent `form_record_key`, an absent type override, or an unrecorded effect family.
- **Insufficient on its own:**
  - a bare stored type;
  - missing form fields;
  - the `other_effects` mastery-source allowlist;
  - a Beast-looking form.
- **These keep their actual holds:** conditional transformations (Polymorph, Shapechange, Animal Shapes, Wild Shape keep the type; True Polymorph; Mask's treated-as), type masks, unrepresented choices and independent parameterized inputs.
- **Required tests:**
  - an ordinary non-Humanoid target receives the rider;
  - an excluded target takes damage without the rider;
  - zero-dice refusal for missing or contradictory state, invalid source/form/choice, and stale binding or revision.

## The remaining Owner input question (unapproved)

> May a **source-open Humanoid individual** record one exact accepted species selection, from code-generated compatible options, with audit, revision and binding checks, and refusing whenever it is unrecorded or unknown?

Approval would resolve only those individuals' missing identity. It does not resolve:
- conditional forms;
- unknown or unrepresented species;
- source-fixed conflicts;
- parameterized creature inputs.

None of those becomes an accepted exclusion, and a refusal is not coverage.
