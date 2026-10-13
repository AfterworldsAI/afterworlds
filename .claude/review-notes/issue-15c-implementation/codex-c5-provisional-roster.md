# CRD Issue 15c — provisional roster and grant-proof correction

Reviewed interim C5-A `d71b3cb3fc829d5b6dd89fa35884c719c3d8fba86494393e225717aed64906c3`, B `4eafaf587a924fd78c5e429a043da4ca72e7f33b4ba47d543a41bc180f8e0d1a`, capability `e392e861c82ecfb92216a1b0d3cfb766c4d14a32c112e8ff3e9e1d932d07dec4`. Mutable packet, not a final verdict. Fold these settled family corrections into current C5 before its final gate. No new Owner Decision or general feature/encounter/senses/healing engine.

## P1 — ordinary observer checks and damage-triggered zero-HP save are incorrectly excluded

Full approved #191 admits all eighteen skills, six ability saves, source-fixed/formula comparisons, bounded associated saves/effects, independent subjects and source-defined consequences of admitted damage. Stat-block placement is not an exclusion; missing predicates/state refuse explicitly.

- Raven Mimicry (`creatures[308].entries[0]`, animals.md:5381) is a **DC10 Wisdom (Insight)** check by a hearer discerning imitations. Capability wrongly says DC14 and “outside roster.”
- Green Hag Mimicry (`[101].entries[2]`, monsters-A-Z.md:8437) is DC14 Wisdom (Insight) by a creature hearing the imitations.
- Cube Transparent (`[80].entries[1]`, :6669) is DC15 Wisdom (Perception), qualified by not having witnessed the cube move or otherwise act. Being an observer does not exclude an admitted skill check; retain the predicate without a general senses engine.
- Zombie and Ogre Zombie Undead Fortitude (`[233/234].entries[0]`, :19481,19555) is a bounded damage-triggered **Constitution save, DC5 + damage taken**, unless damage is Radiant or from a Critical Hit; success substitutes 1 HP before ordinary zero-HP consequences. It is not healing or a general feature engine. Preserve the exact triggering damage event amount/type/critical identity, eligibility and synchronous linked resolution. It applies to those monsters regardless of character-style treatment. Missing structured authority/event inputs can hold the operation; “save to stay at 1HP” is not itself a new-mechanic exclusion.

Type source facts and predicates and state the specific capability prerequisites. Do not widen this bounded correction into every class/species feature. No alleged “Relentless” damage-threshold trait was located in these pinned creature files; do not import an older SRD version or add it from memory. Relentless Endurance/Rage are different source rules.

## P1 — exact tool selectors; P2 — proof labels

The independent A review found ad hoc selector strings such as `equipment.tools.musical_instrument (variants)`, `equipment.tools.gaming_set (variants)` and `equipment.tools (Artisan's Tools category)`. These are not exact accepted semantic keys. Bind choices through explicit typed record/component/variant/category selectors using existing source-backed tool membership. Field-name hashing does not validate selector values. Your Advisor is already addressing this; reuse that work rather than duplicate it.

`entitlement-examples.json` calls true source statements “invalid recorded grants”: e.g. Barbarian melee-only mastery, no multiclass saving throws/Simple weapons, and Grappler prerequisites. Its assertion helper checks fact shapes; it does not evaluate a concrete grant. Either make the examples concrete subject/source/selection/expected-validity distinctions or accurately label them source-rule assertions. Do not advertise them as runtime entitlement validation; dependent runtime validation/tests remain held for native semantic acceptance.

The repaired Lore eligibility, sampled starter/multiclass/mastery facts and explicit clause effect/branch links are improved. Reuse the unaffected evidence. Source conservation must remain separate from typed-field semantic completeness; whole `source_text` inclusion cannot make number accounting substantive.

All raw-pass native/implementation/acceptance/test/commit/publication boundaries remain unchanged. New source semantics still require final independent raw review, exact native review and explicit Owner acceptance before dependent execution.
