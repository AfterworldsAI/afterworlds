# Proposal for the Owner: a creature's species, where its stat block leaves it open

**Status: PROPOSED authority, not approved.** Nothing here is implemented. It does not block C8: the type assignments, character species and the Undead exclusion all proceed without it.

## The gap (codex-c8-raw-review, "Elf status")

The Ghoul's Claw spares an elf (`monsters-A-Z.md:6919`). For a character, the exact validated species identity (`character_origins.elf`) settles it. For a creature, nothing does:
- **The source leaves it open.** `monsters.md:55` says role and profession Humanoids include varied species, so a Mage can be an elf or not.
- **Tags don't settle it.** `monsters.md:67`: tags are categorization, and a missing tag is not a negative.
- **State doesn't record it.** `CreatureState` has no species, and validation checks none.

So "Ghoul Claw against a non-Undead creature" refuses today. **That is a promised gap, not completion.**

## The proposed input

For a creature instance whose template leaves species open, the GameMaster may record **one exact accepted species identity** on that creature, solely to answer "is this creature an elf?" for target predicates such as the Ghoul's.

1. **Code-generated options only.** The eligible values are the accepted species records under the creature's own binding (`character_origins.*` of kind `species`). There is no free text, no new taxonomy, and no Elf/not-Elf boolean.
2. **Where it may be recorded.** Only on a template whose source leaves species open: a Humanoid profile with no source-fixed species. It refuses on a template whose type or species is source-fixed and contradicts the choice, for example any non-Humanoid template. (Every C8 species is Humanoid.)
3. **How it is recorded.** On the creature's own state document, through the existing 2b compare-and-swap. It is audited like any state change: revision, binding and the event that set it. It is a fact about the instance, never about the template.
4. **What it may not do.**
   - It grants no species traits, character-build legality or type change.
   - It does not override a stored or source creature type.
   - It is not a faction or allegiance input.
5. **How it is read.** The rider reads it under the creature's binding and current revision, rechecked at commit like every subject the turn reads.
   - **Unknown or unrepresented:** the operation refuses before any die. A missing selection never means "not an elf".
   - **Contradicted** (a source-fixed identity, an unexecuted form effect, a binding without that species record): it refuses.
6. **Invalidation.** A change of template, binding or form, or a revision of the record, invalidates the selection, which must be re-recorded under the new authority.

## The question

> May a creature instance whose stat block leaves its species open record one exact accepted species identity, chosen from code-generated options and validated as above, solely so target rules like the Ghoul's elf exclusion can be decided — refusing whenever it is unrecorded?

**If no:** "Ghoul Claw against a non-Undead creature" stays held, as an explicit AC2/4/7 gap, not an exclusion.

**Either way:** this is not acceptance of C8, which has its own exact acceptance gate. The coordinator may consolidate the two asks.
