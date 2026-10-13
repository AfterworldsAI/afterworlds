# CRD Issue 15c — raw candidate C6-r2: feat category authority (revised)

**RAW CANDIDATE ONLY.** It is not accepted, minted, recorded or published. It revises C6 (`../candidate-c6/`, `c6.json` SHA-256 `eb014b30…554a`, preserved unchanged) in response to `../codex-feat-entitlement-boundary.md`. Native C5, the recorded successor (`23e5d8e0…4f69`) and schema 19 (`3734ccf7…d18f`) are unchanged.

| File | SHA-256 |
| --- | --- |
| `c6r2.json` | `699718ff9bac8298c08fc6da706309819b864b604685c88f462669d68e8923f4` |

**Reproduce:** `venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c6-r2/derive_c6_r2.py`. It reads C6, keeps C6-A byte-for-byte in content, and re-checks every quote against the pinned `feats.md` (`3894f4a1…`).

## Content

These are the four C6-A facts, which Codex inspected as faithful and as strictly parsing under schema 19. Each is a `feat_prerequisite(category=origin, no prerequisite)`:

| Component | Source |
| --- | --- |
| `feats.alert/category` | `feats.md:23` |
| `feats.magic_initiate/category` | `feats.md:33` |
| `feats.savage_attacker/category` | `feats.md:47` |
| `feats.skilled/category` | `feats.md:53` |

## Family disposition: earned contributing feat entitlement

| Element | Authority | Disposition |
| --- | --- | --- |
| Parent selected identity | the linked `ChoiceRecord` | Code: a feat selection citing a choice must be the feat that choice selected; an ability, skill or tool grant must agree with its choice. Fixed, with regression tests. |
| Per-source count | `feat_choice` count / count per gain × gained levels | Code, already enforced |
| Cross-source repeatability | typed `repeatable: true` on the Ability Score Improvement increase and on Skilled's skill choice | Code: more than one selection of a feat refuses as missing authority unless a typed fact states it repeatable. Null is not permission. No default rule is minted. Grappler-twice refuses; Magic Initiate's qualified repetition is not generalized. |
| Prerequisite qualification | typed `feat_prerequisite` (General and Epic Boon feats in C5; Origin feats with C6-r2) | Code. Feats with no typed category or prerequisite refuse under category and qualifying-feat choices. |
| "Any feat for which you qualify" | the typed `or_any_feat_whose_prerequisites_are_met` | Code: not limited to the choice's primary category (Epic Boon → General ASI admitted). Fixed, with a regression test. |
| Exclusive branch consumption (Paladin/Ranger Fighting Style versus Blessed/Druidic Warrior) | prose | **Not needed.** See C6-B below. |
| Champion qualification for Additional Fighting Style | prose | **Not needed.** See C6-B below. |

## C6-B: withdrawn, not revised

C6-B proposed:
- a schema-20 vocabulary for the Fighting Style category and prerequisite;
- unconditional one-feat grants on the four class Fighting Style features.

Codex found it incomplete: it omits the exclusive branch and Champion eligibility. Revising it is not necessary for #191:
- **Nothing consumes the entitlement.** The Fighting Style feats' benefits contribute to attack rolls, damage and Armor Class (Archery, Defense, Great Weapon Fighting, Two-Weapon Fighting). Under #191 AC4, an unsupported contributing feature refuses; it is not ignored. A character holding one has its weapon attacks and AC-dependent operations refused as an unsupported contributor.
- **So whether the selection was legitimately earned is never relied on,** and branch exclusivity and Champion qualification are never needed.
- **If they later become executable,** a fresh candidate will be needed. It would cover:
  - the Fighting Style category and prerequisite vocabulary (schema 20);
  - subclass/level eligibility on a feat choice;
  - the exclusive alternative between the feat and the Warrior option.

  It would get its own independent review and Owner acceptance.
- **Still excluded:** cantrip execution, feat replacement and the Fighter's level-up swap.

## Cost

**One of 24 accepted batches** (`character-origins-feats`) at schema 19, unchanged. The native step would be one replacement proposal recorded as a successor of `23e5d8e0…`. The other 23 batches stay byte-identical.
