# CRD Issue 15c — C7 Owner packet (native SIMULATED preview)

**Status:** independently reviewed (`../issue-15c-implementation/codex-c7-native-review.md`); for the Owner's decision. Nothing is accepted, recorded, published or executed.

## The one decision asked

Accept or reject **C7 exactly as previewed**, as one semantic acceptance. It includes the disclosed source inference I2, described below. If accepted, the engineer records exactly these identities as a same-release successor of the recorded C5 successor (`23e5d8e0…`, which stays immutable):

| Item | Identity |
| --- | --- |
| Raw candidate C7 | `bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77` |
| Schema | `5d-representation-schema-20`, `759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a`; lift `5d-lift-schema-19-to-20` |
| Preview oracle file | `d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d` |
| Oracle identity | `cb04163ba0374e95ce0fcdaae939b00793e71f84ed3222593c4babfc9065ef6e` |
| Projection / payload | `8446ab6b-be75-5999-8a9b-74fa133c030a` / `cffcdbfa70a6e64351b852ff9b932aa32df81abdd45700ef6c0034aefdaeb65a` |
| Proposals | `character-origins-feats` `1e7b63d3800154eee539297b0ae5d4f9efbfe21c1776986db133e3cc046bfd28`; `equipment` `b8c65454cae97f82cdb96c857aad84c70ba8c78e96fa24f1e95e89360e144a76` |

## What it adds: nine typed facts in two batches

| Batch | Component | Fact |
| --- | --- | --- |
| equipment | Arrows | `ammunition_supply` kind `arrow` (any arrow weapon) |
| equipment | Bolts | `ammunition_supply` kind `bolt` (any bolt weapon) |
| equipment | Needles | `ammunition_supply` kind `needle` (any needle weapon) |
| equipment | Bullets, Sling | `ammunition_supply` kind `bullet`, for the **Sling** only |
| equipment | Bullets, Firearm | `ammunition_supply` kind `bullet`, for the **Musket and Pistol** only (I2) |
| character-origins-feats | Alert, Magic Initiate, Savage Attacker, Skilled | feat category: Origin |

**Interpretation I2.**
- **Evidence:**
  - the Weapons table's bullet users are the Sling (`equipment.md:241`), the Musket (`:431`) and the Pistol (`:439`);
  - the separate "Bullets, Sling" row (`:1239`) takes the Sling;
  - `character-creation.md:849` refers to "the firearms described in 'Equipment'".
- **What the source does not say:** it never literally labels the Musket or the Pistol "firearm". I2 is a bounded inference from these rows, accepted or rejected with the rest of C7. If C7 is rejected, it is re-cut.

Native validation refuses four kinds of bad supply:
- a reference to no component of the draft;
- a weapon without Ammunition;
- a kind mismatch;
- two rows of one kind claiming one weapon.

Malformed supply or weapon-side structure keeps its own structural refusal and is never read by that rule. So the sling and firearm bullets are disjoint by construction.

## What changes, and what is preserved (`reports/c7-preview.json` → `preservation`)

**Changed:**
- the nine components: each goes from prose-bound with no facts to `mixed` with its exact fact;
- the nine provenance claims and nine expected rules added for them;
- the two touched batches' proposals, re-declared at schema 20 with SIMULATED receipts;
- the schema declaration, 19 to 20;
- the `19→20` lift, appended;
- obligations, on the nine fact records only.

**Preserved:**
- the other 22 batches' ordered acceptance records, review units and anchors;
- all 24 batch positions;
- spans, references and resolutions;
- the release binding, policy and existing lifts;
- every other representation value.

## What acceptance does and does not authorize

**Acceptance authorizes** recording the identities above. Recording is followed by engineering verification of the recorded oracle: the recorded identities must equal these. Existing authority (`owner-ammunition-inclusion-2026-10-12.md`) then permits the dependent ammunition execution without another execution-policy decision. That execution covers identity, compatibility, held quantity and atomic expenditure. Action accounting, Loading and hand/grip facts are already approved and implemented on the main branch. They are not open Owner boundaries.

**Acceptance does not authorize:**
- merging, shared-runtime migration, publication/activation or app launch;
- ammunition recovery, which stays excluded.

C6/C6-r2 originals stay preserved and unaccepted. C6-B stays withdrawn.

## Reproduce and verify

The README has the full command. `build_c7_preview.py --twice` regenerates byte-identical outputs. The implementing session reran it independently on 2026-10-13 and got a byte-identical report.

The 2026-10-13 validator correction (relational admission order) changes neither the schema hash nor any preview identity. The valid preview has no structural violations, so it reads the same, and the schema-identity pins are unchanged.
