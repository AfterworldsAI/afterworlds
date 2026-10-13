# Contributing-grant entitlement review — round 2

The three original reproductions are corrected; one concrete contributing-choice consistency defect remains. This is a static bounded re-review, not final readiness.

Reviewed `grants.py` SHA-256 `71c15d57f76ab78466cf4ed98bc9fc7b020a88479b776c5b1dc8cfaf4e11b329`, unchanged before/after inspection. Regression-test file SHA-256: `7810a38178fff026a970a9bc93f2daec01955df22db1bc0ab13896ad2c1a0442`. Task revision remains HEAD `1473426762970dd532a01924dcfcb6183ccdf603`; the working changes are the reviewed artifacts. Reused full #191, exact native C5 Owner acceptance and accepted successor identity `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69` from the coherent task. No new semantic authority is inferred.

## Original findings

| Finding | Disposition and static evidence | Regression coverage inspected |
| --- | --- | --- |
| Reusing one background/ASI increase under extra IDs | Original reproductions fixed. `grants.py:356–357,409–452` caps groups by earned instances and gives each feat group a distinct selection owner. | `test_bounded_checks.py:700–736`: positive single background, refusal of duplicate background and duplicate one-feat ASI. Existing `:289–310` covers valid ASI, wrong amount/pattern and insufficient level. |
| ASI feature rejects another qualifying feat | Fixed. `grants.py:237–258` now consumes the typed qualifying-feat alternative while retaining prerequisite and source-gain validation. | `test_bounded_checks.py:739–765`: Fighter 4 choosing Skilled successfully contributes Athletics proficiency. |
| Skilled splits its skill/tool allowance | Fixed for the reported mixed allowance and legal tool path. `grants.py:757–763` maps the tool branch to the same `skill` allowance; `:785–802` counts both collections; `:648,818` invoke that validation from both callers. The separate `tool` and `multiclass-tool` buckets preserve genuinely separate source choices. | `test_bounded_checks.py:768–813`: two skills plus one tool work; tool proficiency is recognized; three skills plus one tool refuse. |

## Remaining P1 — a linked choice need not be the choice executed

`grants.py:434–452` checks that an increase's `choice_id` occurs in a FeatSelection's `choice_ids`, but never resolves the ChoiceRecord to verify the granting source and selected ability identities. The subsequent rule check accepts any source-eligible ability. For direct-fact components, `_facts` (`:101–110`) does not read the linked choice at all.

Static example: reuse the valid Wizard-4 ASI fixture (`test_bounded_checks.py:256–285`), leave its `asi-4` ChoiceRecord selecting Strength and its earned FeatSelection unchanged, but change the single +2 adjustment to Dexterity while retaining `source.choice_id='asi-4'`. `_bind_to_earned` accepts the ID; the ASI rule admits Dexterity; `ability_score(DEX)` increases the unselected ability. A choice from another source can similarly be attached by ID. CRD Issue 2b verifies choice IDs exist and each choice's own schema/identities, not agreement between a grant and the choice it cites (`models/dnd5e_state.py:728–737`, `services/dnd5e_state/validation.py:219–241`).

The stored contract explicitly says `GrantSource.choice_id` identifies the ChoiceRecord that produced the grant (`models/dnd5e_state.py:127–138`). #191 requires validation of contributing choices before numeric use. Required correction: a contributing grant with an explicit linked choice must agree with that choice's source and selected identity, rather than treating ID membership as sufficient. The analogous direct skill/tool paths also use the allowed pool and count without reading linked selected values (`grants.py:529–568,734–782`); include these representative siblings in the same bounded consistency correction. The added tests use matching selections and do not exercise disagreement.

**Boundary classification:** repeated-hotspot review stop applied. This residue is an issue-scoped implementation defect at the existing recorded-choice-to-grant seam, not a new acquisition-order policy or a general character-build legality requirement. No Owner Decision is needed to refuse an explicit contradictory link. Do not expand the remedy into auditing unrelated character selections or inventing acquisition chronology.

No tests, application imports, stores, runtime actions, Git mutations or source edits were performed. Only this new review note was written. Test code was inspected, not executed; unfinished operation integration and broader gates remain outside this verdict.
