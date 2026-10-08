# CRD Issue 5d - reference 76: the missing explanatory pointer

Verified 6 October 2026. Source clarification and disposition, not a drafted
or accepted target mapping or a claim about the runtime adjudicator's completeness.

## Exact outstanding citation

The accepted representation has one unresolved reference with this identity:

- Source record: `play.d20_tests`.
- Owning component: `add_modifiers`.
- Printed wording: `Rules Glossary`.
- Committed scope: `srd-5.2.1/rules-glossary`.
- Target: empty; no recorded resolution for this identity.

Official PDF p.6 and qualified playing-the-game.md:186 explain that Playing the
Game and Rules Glossary explain which ability modifiers to use for various D20
Tests. The component's separate Proficiency pointer already targets
`play.proficiency`. The outstanding glossary pointer does not identify a missing
individual skill, action, or ability-modifier magnitude table.

## Source meaning and corrected diagnosis

The Owner correctly identified general guidance in Ability Descriptions,
Ability Check Examples, and Skills, with action-, feature-, spell-, and
effect-specific rules and exceptions supplying the rest. Playing the Game also
contains Saving Throw Examples and Attack Roll Abilities. The source's
Exceptions Supersede General Rules principle remains applicable.

Relevant source includes:

- playing-the-game.md:198: the relevant ability depends on the situation;
  the Ability Check Examples table illustrates its use.
- playing-the-game.md:283-291: saving throws respond to threats and their
  results are supplied by the effect; Saving Throw Examples supplies guidance.
- playing-the-game.md:344-379: Attack Roll Abilities supplies the ordinary
  melee, ranged, and spell-attack guidance and explicitly acknowledges feature
  exceptions such as Finesse.
- playing-the-game.md:590-600: Skills gives typical associations and the GM
  determines relevant skills; the general Ability Check rule covers attempts
  that are not tied to one of those proficiencies.
- rules-glossary.md:151-157, 243-245, 571-573, and 1236-1238: Ability Check,
  Ability Score and Modifier, Attack Roll, D20 Test, and Saving Throw definitions.
- rules-glossary.md:871-877, 1240-1242, 1380-1384, and 1491 onward: Hide,
  Search, Study, and Unarmed Strike provide concrete ability-selection rules.
  These are examples to guide the inventory, not an exhaustive target proposal.

The first report overstated the concern if read as requiring a single collective
glossary route to specify the ability for every possible D20 Test throughout
the SRD. The outstanding defect is an unresolved explanatory cross-reference.
Its context supports a bounded inventory of relevant glossary definitions and
operative glossary rules, with specific rules retaining their own ownership.
Do not invent a universal ability selector, an exhaustive improvised-action
taxonomy, or new skill rules to discharge this reference.

## Next candidate and boundaries

Disposition: ordinary source-grounded destination inventory and reader coverage,
not a new Owner Decision on gameplay adjudication. Determine the appropriate
glossary route from its context and verify what the effective reader exposes.
Preserve the distinction between choosing the relevant ability, applying its
modifier, and applying proficiency or situational modifiers. An ability-score
to-modifier table alone would not fulfill the explanatory pointer's context.

Do not claim recursive traversal of glossary See Also references, silent scope
changes, or exhaustive coverage of all specific cases. Preserve already-authored
source rules and separately accepted references. No native candidate or reader
test was run for this clarification.

The accepted oracle remains SHA-256
`5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d`,
with 1,476 resolutions and ten remaining reference findings. Exact candidate
acceptance and the existing restart gates remain required; no publication,
activation, shared-database write, commit, push, merge, or dependency repair
was performed or authorized by this clarification.
