# CRD Issue 15c — raw candidate C7: consolidated C6-r2 + ammunition identity

**RAW CANDIDATE ONLY.** Nothing here is accepted, minted, recorded or published.

**Authority:** the Owner's direction of 12 October 2026 (`../owner-ammunition-inclusion-2026-10-12.md`) puts ammunition identity and compatibility into this issue. It does not accept the new semantic content.

**Preserved unchanged and digest-checked on every run:** C6 (`eb014b30…554a`), C6-r2 (`699718ff…23f4`), the recorded successor (`23e5d8e0…4f69`), and the pinned sources. C6-B (Fighting Style) stays withdrawn.

| File | SHA-256 |
| --- | --- |
| `c7.json` | `bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77` |

**Reproduce:**
```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-implementation/candidate-c7/derive_c7.py
```
Two runs are byte-identical.

## Content

**Part C6-r2: four facts.** They are byte-identical in content to `c6r2.json`, which Codex has already cleared. They remain schema 19.

**Part C7-ammunition: five facts.** The candidate proposes one schema-20 family, `ammunition_supply` (`AmmunitionSupplyFact`), with two fields:
- `kind`: the existing schema-19 `AmmunitionKind`;
- `for_weapons`: `tuple[ComponentReference, ...] | None`. It lists the weapons a row narrows a shared kind to. `None` means every weapon whose row names that kind.

| Gear component | Table row (`equipment.md`) | `kind` | `for_weapons` | Interpretation |
| --- | --- | --- | --- | --- |
| `adventuring_gear.arrows/arrows` | :1218 `Arrows` | arrow | — (Shortbow, Longbow) | I3 |
| `adventuring_gear.bolts/bolts` | :1225 `Bolts` | bolt | — (Light, Hand, Heavy Crossbow) | I3 |
| `adventuring_gear.needles/needles` | :1246 `Needles` | needle | — (Blowgun) | I3 |
| `adventuring_gear.bullets_sling/bullets_sling` | :1239 `Bullets, Sling` | bullet | Sling | I1 |
| `adventuring_gear.bullets_firearm/bullets_firearm` | :1232 `Bullets, Firearm` | bullet | Musket, Pistol | **I2** |

**Why the bullet rows need `for_weapons`.** The weapon side prints a single `Bullet` for the Sling, Musket and Pistol (:241, :431, :439). A shared `bullet` therefore can't separate sling bullets from firearm bullets. `for_weapons` preserves the source's distinction, so neither row is accepted by the other's weapons.

**Why a new family.** No existing family fits:
- No field typed `AmmunitionKind` exists outside the weapon-side `WeaponPropertyFact.ammunition`.
- The only `ComponentReference` fields carry proficiency or choice semantics:
  - `ToolSelector`;
  - the skill-choice families;
  - `ToolProficiencyGrantFact`;
  - `MulticlassProficiencyGrantFact`;
  - `AbilityIncreaseChoiceFact`.
- Reusing any of these would misstate the source.

**Not represented:**
- the amount, storage, weight and cost columns, which are not needed;
- ammunition recovery after a fight. It stays the represented `AmmunitionExpenditureFact.recovery` rule, and it is not executed.

## Interpretations for independent review

- **I1 — Sling bullets go with the Sling.**
  - The table row names the weapon: "Bullets, Sling".
  - The source states no other link.
- **I2 — Firearm bullets go with the Musket and the Pistol.** This is the weakest link.
  - The source never labels either weapon a firearm.
  - The only support is `character-creation.md:849`, "the firearms described in 'Equipment'". Those are the only gunpowder weapons in Equipment.
  - **Alternative for the Owner:**
    - The firearm row carries `bullet` with no weapon link.
    - The Musket and Pistol then stay `missing_authority`. That is not coverage.
    - The Sling is unaffected.
  - Code does not choose between these.
- **I3 — An unqualified row is the ammunition its singular kind names** (Arrows → Arrow, and so on).
  - Evidence: `equipment.md:778`, "A weapon's description specifies the type of ammunition used by the weapon … The Ammunition table lists the different types".

## Residues for the same review gate (not decided here)

1. **Loading and action economy.** Loading means one piece "when you use an action, a Bonus Action, or a Reaction to fire it, regardless of the number of attacks" (`equipment.md:78`).
   - Code cannot tell which attacks share an action. That is the action-economy classification already open for Nick and Light.
   - It now also blocks the Light Crossbow, Hand Crossbow, Heavy Crossbow, Musket, Pistol and Blowgun.
   - **Proposed bounded rule, for classification:** a Loading weapon fires at most once per delivered Turn.
2. **Free hand to load a one-handed weapon** (`equipment.md:70`).
   - 2b records `equipped` per item, not hand occupancy.
   - Deriving a free hand from the equipped one-handed weapons and Shield would be an interpretation of "equipped".
   - **Alternatives:** that derivation, or a GameMaster fact under OD-15c-1.
3. **Depletion.** An item instance must keep `quantity >= 1`, so spending the last piece needs a defined outcome. The options are removing the instance or a new zero state.
   - Under Invariant 11 the spend must be reconstructable. The audit row already records each expenditure effect.
   - **Proposed rule:** remove the row only through a holdings operation that records the expenditure.

## Next gate

1. Codex independent raw review of `c7.json` (`bf2a269c…`).
2. After raw clearance, the consolidated native preview. It covers:
   - the schema-20 lift;
   - the `character-origins-feats` batch;
   - the batch or batches owning the five gear components, to be identified natively.
3. One exact Owner semantic acceptance.

No recording, and no ammunition or Origin-category execution, until that acceptance. Code-side plumbing that doesn't depend on the authority continues meanwhile; ammunition weapons still refuse as `missing_authority`. This packet is not CRD Issue 15c completion.
