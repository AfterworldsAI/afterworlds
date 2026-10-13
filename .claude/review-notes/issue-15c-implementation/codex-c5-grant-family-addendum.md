# CRD Issue 15c — settled grant-family completeness addendum

Fold into the active raw C5 pass, not another micro-patch round. No new scope or Owner Decision: #191 already requires code-owned validation of contributing grants/choices for six saves, tools, weapon proficiency, armor training and mastery eligibility. Full build legality and general rest/feature execution remain excluded.

The independent sibling audit establishes that final C4-A has **no typed entitlements** for saving-throw proficiency, weapon proficiency, armor training, tool grants or Weapon Mastery choices/counts. `tool_entry` and `mastery_effect` describe tools/effects, not who earns them. G1 class `core_traits`, class `weapon_mastery` and background `tool_proficiency` components are prose-bound with no facts. Existing weapon category/mastery facts and class feature progression levels are safe and reusable, but do not supply the missing grant constraints. C4-C armor/shield consequences likewise do not prove earned training.

Representative pinned source distinctions:

- Barbarian starting Core Traits: Strength/Constitution saves, Simple/Martial weapons, Light/Medium armor and Shields (`classes.md:18–30`); multiclass grants differ (`:50`).
- Bard starting Core Traits: Simple weapons, choice of three Musical Instruments and Light armor (`:394–404`); multiclass grants one skill, one instrument and Light armor (`:424`).
- Barbarian Weapon Mastery: two **melee** weapons, later source-table counts (`:264–266`); Fighter three Simple/Martial choices with later table counts (`:4729–4731`); Ranger two weapons with which the character has proficiency (`:6347`). G1 `progression_entry` for initial mastery has `quantity=None` and cannot supply the choice count.
- Soldier's Gaming Set choice (`character-origins.md:61–62`) and Skilled's skill/tool choices (`feats.md:51–55`) also need earned option/count validation. Other contributing source grants require the same bounded family assessment.

Required outcome: a recorded proficiency/training/mastery grant must be validated against its exact source entitlement, starting-versus-multiclass context, gain level, choice vocabulary/count and contributing eligibility qualifiers before it can affect an admitted operation. Type the missing source constraints coherently across representative parallel structures; preserve and reuse the already correct G1 weapon identities/progression and repaired C4 skill/ASI/expertise facts. Do not replace this with mere source-reference existence or a blanket assertion that state recording certified legality.

Keep source facts and source-defined choices separate from `ChoiceRecord` storage, adapter procedures and capability judgments. Source rest-swap qualifiers remain faithfully represented without admitting a general rest-resource engine; any out-of-scope transition refuses explicitly. The affected classes and character-origins batches are already in the current 11-batch transition; recompute only if actual placement requires it. Grant execution/code/test changes remain held until exact native semantic acceptance.

Proof should demonstrate complete relevant entitlement coverage and source-backed positive/invalid entitlement distinctions in the candidate, with exact hashes and ordinary family dispositions. No full suite, native generation, production implementation, acceptance, commits or publication in this raw pass. All prior artifacts and stop boundaries remain unchanged.
