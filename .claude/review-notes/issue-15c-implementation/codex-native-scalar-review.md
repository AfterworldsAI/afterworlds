# CRD Issue 15c — provisional native scalar validation review

**P1 representation-validation family; settled implementation correction, not an Owner Decision.** Read-only draft review before native identities are frozen. C5 source semantics and raw hashes remain unchanged. The drafts and their integrated copy are still being edited; verify this against the settled registration rather than assuming an early line number is final.

`schema19/registry.py:_declared_typed_findings` sends every `int` to `_int_field`, which checks exact type only. Six family/seven shape rules mostly check exclusive alternatives. The draft consequently admits impossible source values:

- `ElapsedSpan(amount=-1)` (`classes.py:24–29`);
- `ForcedMove(distance_ft=-5)` (`:119–125`);
- `MultiattackPart(count=-2)` (`:225–229`);
- `WeaponMasteryChoiceFact(kinds_of_weapons=-2)` (`rules.py:591–605`);
- negative `RestDurationFact.hours` (`:190–196`).

Parallel nested-value defect: non-fact dataclasses `DiceExpression` and `Rational` recurse through type checks but lack their accepted shape validators in `_SCHEMA_19_SHAPE_RULES`. Thus `DamageTerm.dice` can use zero/negative dice count and `AmmunitionRecovery.fraction` can use denominator zero. Accepted `_check_dice` and `_check_rational` already reject these and allow signed dice modifiers. Nested accepted **fact** dispatch alone does not cover these accepted **value objects**.

Correct the family coherently: delegate to existing accepted value-object validators, and enforce field-specific source-valid domains for new quantities/counts, elapsed durations, ranges/distances, levels and maximum/HP values. Preserve signed bonuses, modifiers and effect deltas; permit zero where its field semantics actually allow it (zero HP trigger, zero Speed, a no-grant multiclass choice, etc.). Do not impose blanket positivity or invent global SRD limits unrelated to the represented field. Type closure is necessary but not sufficient for valid mechanics.

Keep the constraints in the declared schema invariant/hash contract and demonstrate representative positive, zero/signed where valid, and invalid/boolean/nested rejection cases through focused schema diagnostics. Do not broaden into full-suite or gameplay tests in this preparation pass. This is code-owned source validation, not a new semantic candidate, source rewrite, generic effects framework or scope expansion. All acceptance/recording/runtime/commit/publication stops remain held.
