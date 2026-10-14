# CRD Issue 15c — contributing grant trust boundary

**P1, issue-scoped implementation/authority defect; no Owner Decision about general build legality.** Reviewed the current partial implementation on `1473426762970dd532a01924dcfcb6183ccdf603` while the raw C4 pass runs. No test, source mutation or runtime operation was performed.

CRD Issue 2b storage and readiness validate structure and source identity, not legality or eligibility. #191 explicitly assigns validation of contributing grants, choices and deterministic selectors to 15c, while excluding a full character-builder legality sweep.

The first broken seam is treating recorded provenance as entitlement:

- `services/dnd5e_state/validation.py:133–145` checks source record/component existence. The adjustment and skill-grant loops call that check (`:323–325`, `:391–406`) without deriving legal amounts, grants or expertise.
- `pipeline/rpg/checks.py:242–251` executes any recorded adjustment amount/maximum and invents a default cap of 20. It does not validate that this source granted that adjustment to this subject.
- `checks.py:420–431` applies the first matching recorded skill grant and doubles it whenever `expertise=True`, after only checking generic skill-proficiency application and the PB band. It does not validate the character's entitlement, eligible selection or expertise source.
- `tests/pipeline/rpg/test_bounded_checks.py:146–172` positively accepts Athletics/Expertise sourced from Wizard. `:175–186` accepts one Ability Score Improvement adjustment of +4 or +30 (capped to 20).
- The source's Ability Score Improvement feat is a level-4+ choice of +2 to one ability or +1 to two, with cap 20 (`docs/sources/community/dnd-5e-srd-markdown/feats.md:61–67`). Expertise requires an already proficient eligible skill and cannot duplicate (`rules-glossary.md:790–794`).

Accepted G1's Ability Score Improvement, glossary Expertise and Bard Expertise components remain prose-bound without the required structured amount/selection facts. Existing PB bands and generic proficiency-application facts can be reused after eligibility is established; their presence does not establish the particular grant's entitlement.

**Disposition:** in dependent 15c implementation, validate each contributing adjustment/grant/expertise against the exact bound source, applicable entitlement/level and linked typed choice/selector before numeric use. Refuse visibly when required authority or state is absent, invalid or unsupported. Correct the positive tests to use actually admitted source-backed grants and add invalid-source/amount/choice refusal coverage. Do not turn this into a general build-legality sweep.

**Candidate consequence:** before declaring the source packet sufficient for the promised adjusted/proficiency/expertise path, identify existing typed grant/selection authority and propose the smallest missing bounded facts. Those new facts still need independent review and exact native Owner acceptance. This review does not authorize runtime implementation during the raw C4 pass, nor any tests/full suite rerun, recording or publication. Ordinary candidate preparation can continue under the already-approved scope.
