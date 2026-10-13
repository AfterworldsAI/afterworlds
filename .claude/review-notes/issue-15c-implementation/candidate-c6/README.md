# CRD Issue 15c — raw candidate C6: feat category and prerequisite authority

**RAW CANDIDATE ONLY.** It is not accepted, minted, recorded or published. It is for independent Codex review and, if cleared, explicit Owner semantic acceptance. Native C5, the recorded successor (`23e5d8e0…4f69`), schema 19 (`3734ccf7…d18f`) and the C1–C5 raw artifacts are unchanged; `derive_c6.py` digest-checks them before and after.

| File | SHA-256 |
| --- | --- |
| `c6.json` | `eb014b30e685543c435930913d00fe8762963c95b0fdcc9ce470c019bbfb554a` |
| `derive_c6.py` | see `git` once committed |

**Reproduce:** `venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c6/derive_c6.py`. Every fact's quote is asserted present on its pinned source line.

## Why

`grants.py` certifies a feat taken through a category choice (Human *Versatile*) or a "for which you qualify" choice (the class Ability Score Improvement features) only from the feat's typed category and prerequisite. The four Origin feats and the four Fighting Style feats state those only in prose (their `category` components are `prose_bound`). Every such path therefore refuses as `missing_authority`:
- Skilled through Versatile or an ASI;
- Alert through Versatile.

No accepted fact is changed. C6 only adds facts to prose-bound components.

## Facts

### C6-A — within schema 19 (no vocabulary change)

| Component | Fact | Source |
| --- | --- | --- |
| `feats.alert/category` | `feat_prerequisite(category=origin, …none)` | `feats.md:23` *"Origin Feat"* |
| `feats.magic_initiate/category` | same | `feats.md:33` |
| `feats.savage_attacker/category` | same | `feats.md:47` |
| `feats.skilled/category` | same | `feats.md:53` |

### C6-B — needs a schema-20 vocabulary expansion (surfaced as candidate content)

- **Vocabulary:** `FeatCategory` gains `fighting_style`, and `RequiredFeature` gains `fighting_style`. These are the printed *"Fighting Style Feat (Prerequisite: Fighting Style Feature)"* category and prerequisite. Neither member exists in schema 19.
- **Facts:**
  - **The four feats:** `feats.{archery,defense,great_weapon_fighting,two_weapon_fighting}/category` each get `feat_prerequisite(category=fighting_style, requires_feature=fighting_style)` (`feats.md:87/93/99/105`).
  - **The class features:** a `feat_choice(count=1, category=fighting_style)` on each of:
    - `classes.fighter.fighting_style/fighting_style` (`classes.md:4715`);
    - `classes.fighter.champion.additional_fighting_style/additional_fighting_style` (`:4803`);
    - `classes.paladin.fighting_style/fighting_style` (`:5578`);
    - `classes.ranger.fighting_style/fighting_style` (`:6362`).

## Sibling assessment of the feat-granting sources

| Source | Typed today | Consumed by an admitted path? | Disposition |
| --- | --- | --- | --- |
| Background feat (Acolyte, Criminal, Sage, Soldier) | `feat_grant` names the feat | yes (entitlement of the granted feat) | already safe: needs no category |
| Human *Versatile* | `feat_choice(category=origin)` | yes (Skilled's skill/tool grants; Alert as an initiative contributor) | C6-A supplies the Origin category |
| Class Ability Score Improvement (12 classes) | `feat_choice(named ASI, or any qualifying feat)` | yes | C6-A makes Origin feats certifiable. Fighting Style feats need C6-B, since their prerequisite is a feature. |
| Epic Boon (12 classes) | `feat_choice(category=epic_boon, or any qualifying)` | yes | already safe: Epic Boon feats carry typed prerequisites |
| Fighter / Champion / Paladin / Ranger Fighting Style | prose only | only by weapon attacks and AC, which are held on the combat-state contract | C6-B; may stay held until those operations need it |
| Paladin *Blessed Warrior* / Ranger *Druidic Warrior* | prose | no (cantrips: spellcasting is a non-goal) | out of scope; unchanged |
| Fighter's level-up Fighting Style swap | prose | no (a feat-replacement transition) | out of scope; refuses like the Weapon Mastery rest swap |

## Not typed (scope guard)

- No feat **benefit**: Alert's Initiative bonus, Skilled's picks (already typed in C5), Savage Attacker's reroll and the fighting-style bonuses stay contributors that refuse until executed.
- No general feat execution, and no character-builder legality.

## Cost

| Part | Affected accepted batches | Schema | What the native step would be |
| --- | --- | --- | --- |
| C6-A | 1 of 24: `character-origins-feats` | 19, unchanged | A replacement proposal for that one batch, recorded as a successor of `23e5d8e0…` the same way C5's eleven were. The other 23 batches stay byte-identical. |
| C6-B | 2 of 24: `character-origins-feats` and `classes` | 20 (two vocabulary members and a registered 19→20 lift) | Replacement proposals for both batches and a schema mint, with all identity-bound proofs refreshed |

**Recommendation for review.** Accept C6-A now: it unblocks the admitted Skilled and Alert entitlement paths with no schema change. Keep C6-B held until the weapon-attack and AC operations are implemented, because only they consume Fighting Style feats.
