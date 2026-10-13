# CRD Issue 15c — C7 Owner packet (native SIMULATED preview)

**Status:** for Codex review, then Owner decision. Nothing is accepted, recorded, published or executed. Accepting this packet would authorize *recording* exactly the identities below as a same-release successor of the recorded C5 successor (`23e5d8e0…`). It would not authorize ammunition execution itself, which is separate implementation reviewed afterwards.

## What it adds

There are nine typed facts in two batches. Everything else in the oracle is byte-identical to the recorded successor; see `reports/c7-preview.json` → `preservation`.

| Batch | Component | Fact |
| --- | --- | --- |
| equipment | Arrows | `ammunition_supply` kind `arrow` (any arrow weapon) |
| equipment | Bolts | `ammunition_supply` kind `bolt` (any bolt weapon) |
| equipment | Needles | `ammunition_supply` kind `needle` (any needle weapon) |
| equipment | Bullets, Sling | `ammunition_supply` kind `bullet`, for the **Sling** only |
| equipment | Bullets, Firearm | `ammunition_supply` kind `bullet`, for the **Musket and Pistol** only (I2) |
| character-origins-feats | Alert, Magic Initiate, Savage Attacker, Skilled | feat category: Origin |

The schema is `5d-representation-schema-20` (`759dcc1f…`). It adds one family, `ammunition_supply`, and a lift `19→20` that moves nothing. Native validation refuses four bad supplies:
- a reference to no component of the draft;
- a weapon without Ammunition;
- a kind mismatch;
- two bullet rows claiming one weapon.

So the sling and firearm bullets are disjoint by construction.

## The decision asked of the Owner

1. **Accept or reject C7 as previewed**, identified by:
   - oracle identity `cb04163ba0374e95ce0fcdaae939b00793e71f84ed3222593c4babfc9065ef6e`;
   - oracle file `d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d`;
   - projection `8446ab6b-be75-5999-8a9b-74fa133c030a`, payload `cffcdbfa70a6e64351b852ff9b932aa32df81abdd45700ef6c0034aefdaeb65a`;
   - proposals `1e7b63d3…` (character-origins-feats) and `b8c65454…` (equipment).
2. **Interpretation I2.** Accept or reject that "Bullets, Firearm" supplies exactly the Musket and the Pistol.
   - **Evidence:** the Weapons table's bullet users are the Sling (`equipment.md:241`), the Musket (`:431`) and the Pistol (`:439`). The separate "Bullets, Sling" row (`:1239`) takes the Sling.
   - **What the source does not say:** it never literally labels the Musket or Pistol "firearm". I2 is a bounded inference from the two bullet rows and the remaining bullet users, not a printed tag.
   - **If rejected:** firearm bullets stay unnarrowed, and C7 must be re-cut.

## Reproduce and verify

The README has the full command. Running `build_c7_preview.py --twice` regenerates byte-identical outputs. The implementing session reran it independently on 2026-10-13 and got a byte-identical report.
