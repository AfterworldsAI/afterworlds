# CRD Issue 15c — save contributor scan

**Method:** `grep -n -i "saving throw"` over the pinned `classes.md`, filtered for advantage, bonus, proficiency, add, reroll, succeed, instead and fail. Plus `grep -n -i "saving throw\|D20 Test"` over `character-origins.md` and `feats.md`. Each hit was read in its feature entry, and each key was checked against the recorded successor oracle.

## The saver's own contributors

| Kind | Entry (source line) | Relevance |
| --- | --- | --- |
| Feature | Danger Sense (classes.md:270) | Dex saves |
| Feature | Indomitable (:4761) | any; reroll |
| Feature | Monk Evasion (:5133) | Dex half-damage saves |
| Feature | Disciplined Survivor (:5163) | any; reroll |
| Feature | Aura of Protection (:5625) | any |
| Feature | Aura of Courage | Frightened |
| Feature | Aura of Devotion | Charmed |
| Feature | Holy Nimbus (:5988) | any; source creature type |
| Feature | Rogue Evasion (:7016) | Dex |
| Feature | Dark One's Own Luck (:9719) | any |
| Feat | Boon of Fate (feats.md:139) | any |
| Trait | Dwarven Resilience (character-origins.md:172) | Poisoned |
| Trait | Fey Ancestry (:229) | Charmed |
| Trait | Gnomish Cunning (:245) | Int/Wis/Cha |
| Trait | Brave (:287) | Frightened |
| Trait | Halfling Luck (:291) | any |

Each of these refuses when relevant. Proficiency grants (Slippery Mind, Disciplined Survivor's proficiency) are read through validated save-proficiency grants.

## Not save contributors here

- **Owned by other operations:** Relentless Rage (:315) and Survivor's Defy Death (:4817).
- **Active effects:** Rage (:246) and Staggering Blow (:323). Active effects refuse.
- **Concentration-only:** :7678 and :9005.

## Boundary, surfaced for Codex

Some contributors are held by *another* creature: an ally's Aura of Protection, Boon of Fate's Improve Fate, Countercharm (:876), and creature traits whose subject is `others` or `self_and_allies`.
- A save loads only its saver, so these are neither detected nor executed.
- Executing them needs an OD-15c-1 spatial fact: which holders are in range.
- Detecting them needs a story-wide holder scan.
- Classification is needed: either refuse when any story subject holds one, or take a GameMaster in-range selection.
