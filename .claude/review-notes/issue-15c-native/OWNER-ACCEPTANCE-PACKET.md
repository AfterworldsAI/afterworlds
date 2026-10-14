# CRD Issue 15c — Owner semantic acceptance packet (native preview, HELD)

**SIMULATION ONLY. NOTHING IS ACCEPTED.**

- The preview's 11 replacement acceptances carry reviewer `SIMULATION - not an Owner approval`, time `2026-10-12T00:00:00Z` and a `SIMULATION ONLY` rule.
- Nothing was recorded, published, activated, superseded, committed or pushed.
- The preview is outside the committed oracle directory.

## What the Owner would accept

All of the following, exactly by identity:
- the source contract: C5-A/B/C at the reviewed hashes;
- its native schema 19 and lift;
- the 11 replacement proposals;
- the successor oracle that results.

The capability file is not source and is never minted.

| Item | Identity |
| --- | --- |
| C5-A / C5-B / C5-C | `866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9` / `187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6` / `bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4` |
| Capability (not source, not minted) | `6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6` |
| Schema | `5d-representation-schema-19`, hash `3734ccf7d6be7f25e0a0d7c0395121c5525afcb87144f5cf9d6895e03c1cd18f` |
| Lift | `5d-lift-schema-18-to-19`, 18 `276c3d0c…8701` → 19 `3734ccf7…d18f`, verified byte-identical over all 6 collections of G1 |
| src change (pure insertion; 2 replaced lines) | `schema-19-src.diff` `cdfdd0284b83e393265449fef44ab4e2704e17f3206c1a431403023a9b06b2e6` |
| Test pin change (provisional) | `schema-19-tests.diff` `6daf1949ceed1131617f8b1e8c05008be3bd22199165e44c1f3d85b635b3cdf6` |
| Preview oracle file | `preview/srd-5-2-1-corpus-8781d4e0-a3b-15c-PREVIEW.json` SHA-256 `cd9d1d27428a1525955f83091125489e96bbc7bd0977bb9f3ce83933883a20d3` |
| Oracle identity | `000c4c108daf609c26eb9ae9f1197a26eef6fb80a3cb5c788f9e89ba20ad6e76` |
| Projection | UUID `44f212d5-32dd-5469-8f05-f0d236492347`, payload hash `ed8e21dc89ce519d6301e2bbf486405576069fe4348f0c8948bed4dbcb3e5188` |
| Persisted state digest (private store copy) | `b3a3ad3dc8bd3c8343ab64dabbd2fa11ba39bd6064ce4da92c5ebb62f269dee5` |
| Correspondence (C5 → native) | `correspondence.md` `30c37c6e86376cd66b3e616994ee8a1cb1ed0b5006a137309524edb411d47db7` |

Prior: G1 `2ccbaeba…1258` (oracle identity `3e7b27db…c05a`); predecessor `def7caa1…e58c`. Both are unchanged.

### The 11 replacement proposals

Each replayed identity equals its G1 schema anchor. Rendered files are in `preview/proposals/`.

| Batch | Replayed (G1 anchor) | Preview proposal identity | Rendered SHA-256 | Facts | Claims | Expected rules |
| --- | --- | --- | --- | --- | --- | --- |
| animals | `9241c2b876b8cee294948463d6fde415b0741e32b91fbb4301dc50e8d75f8e69` | `efa248a979c21d293701253cda86b561b876bec332667437769abebbb06221c9` | `7186c42a3c731b805a3adce43ca5d2af91a46833e70295872193a1c71dc68631` | 1031 | 4379 | 488 |
| character-origins-feats | `6120f64771725581d478b9bdcd29a13588ee3dd9f9776c42d2628c2ad6bf3702` | `20716b7dcadd5e1216ff3594c5aa654cb41c2961fe49048b0c853c1eed381838` | `a8928f18d65538d21993e7f94090272bdc7e279c412134ebb8ffc996ada48b89` | 39 | 39 | 39 |
| checks-actions-rests | `d96c50a32e269ae17bac1b312b643ba468ed2065e89fcfef7030ce59a55a113a` | `f459a65ded7f0f5eab59c6e57a357e8015efff973976aa17a89fb42c9422096d` | `b9be25d90ee4fb998b298059eed9158808660a90775451e82548ace8a4ba7fe6` | 13 | 13 | 7 |
| classes | `ab357393ce9c3d3bcbc06e7f18ff9c6cadb13c852fdb8dce09fb0ec43737df54` | `536c569f4226be24496edd8c1c1f27e59a6f873c7fcd53188aad9abc3a821e83` | `f072c480f6331d98003de46020f679b3b6ca6b633ee95e9a9aeb1c7ab6957945` | 124 | 124 | 124 |
| combat-damage-breaking | `b11159c1f9663a28b64e1351f7c1a954cb42de2fd1e79e8818bff965f942df51` | `75ce69ce7e2e5da48743dcb24c066540b90bdf9a116ba84e78959759be5cea7d` | `b079df28332cb88ec6276a441c39709d5dfa0422ae8810a6aca3c695baee0ebd` | 16 | 16 | 15 |
| core-play-completion | `96afa186fb7be74d70bd6864327efc7ad7f91ecd97dc02a7b376382233615bd2` | `a9330308d5905b1ab6c296d34b149c2bf95332b91e5a7c75e94c6c50a33becb6` | `dc94ebd7f782a1a5532f2cc3868e1ea226467de186ea49f69714f6b7e453f6f8` | 1 | 1 | 1 |
| equipment | `8a8a737b0d1e47410de86bbeca44b66522b46511e078727d20760678943b5345` | `b01f54b917653f83b7dbeebd6ad54757bdf183f71235d76e9198815f21789c4b` | `7f8dadcd28c072cc22965dc36e7e1d7debb99aec3139c9f8b72178be06aff4b6` | 275 | 286 | 221 |
| magic-items | `54a402acd35a15887b94f286a30804a87dd32e92e91d2b075bbb2367324eed5a` | `bc4979d74a841065af99502e0cf20d157ab4bedd1fd7a9724a2130ffa092e712` | `28a7f4d5ceeaa8a2a19bb4d09313dc97cdc9b9263a2b37230f4ac882eb3c0e31` | 27 | 127 | 10 |
| monsters | `bc559c6ec6bd1e84a000c5656682067b24a9cd868d98440ac19ec1e61ed2c48a` | `ff24d9daf6dd81a760778865a011a5da236b56514a32753c2a8034f5f3eec617` | `9f30cf57619ceca946444a331644b90c1f7af6720962cb936abc0faa20b1474f` | 3912 | 14276 | 2147 |
| spell-descriptions | `93c816fba0698f551123cac5124f161e7b1ef2c7780b8d5bd35ab42dd4205d83` | `dce22fbd6f89a61cbd7ab5efa0be75f81eec87840ae91731e8162c8fabfbbdc9` | `e8830765f3e8a728b810627bd4f58de86d37ed3ba9c447756ade368cf027957d` | 64 | 252 | 30 |
| spellcasting | `4783913aeda24baed59b4d5c61487f6cfb64a25563d6203ab8d6ff8c3873fb8e` | `1033979c0b9308aed91f413826477c0318c054ae6af074b0a17b1fd3fe05363f` | `60a851733d07e9da2f5e0b7e403edb41b6743739f7af1219e41bdcac0d3cb7db` | 2 | 2 | 2 |

The totals are 19,515 provenance claims and 3,084 expected rules. The facts column counts distinct fact objects. Replicated common tool facts are counted once there, and per placement in `reports/reconcile.json` (5,515 placements from 5,504 native facts).

## Supersession of the earlier preview Codex pinned

| Item | Earlier (overwritten) | Current |
| --- | --- | --- |
| Schema hash | `85896c8271a9…be0f` | `3734ccf7d6be…d18f` |
| Preview SHA-256 | `aa9fe91e948b…0593` | `cd9d1d27428a…20d3` |
| Oracle identity | `0d2ea513e0c9…270f` | `000c4c108daf…6e76` |
| Projection | `37c56dbd-c0fd-5158-8087-da23e354f122` / `d4115d18…b318` | `44f212d5-32dd-5469-8f05-f0d236492347` / `ed8e21dc…5188` |
| Persisted state digest | `6382dfc2…baee` | `b3a3ad3d…dee5` |

| Batch | Proposal identity old → new | Rendered SHA-256 old → new | Facts/claims/rules equal |
| --- | --- | --- | --- |
| animals | `7bb7976e1db3…` → `efa248a979c2…` | `d031c7c1ebf5…` → `7186c42a3c73…` | yes |
| character-origins-feats | `338dc9940706…` → `20716b7dcadd…` | `b93c0259ef51…` → `a8928f18d655…` | yes |
| checks-actions-rests | `3ac491cfb53a…` → `f459a65ded7f…` | `d7b96c751487…` → `b9be25d90ee4…` | yes |
| classes | `307ff11eeb7f…` → `536c569f4226…` | `d26992617c58…` → `f072c480f633…` | yes |
| combat-damage-breaking | `ddbb7dabed20…` → `75ce69ce7e2e…` | `0c53f292c818…` → `b079df28332c…` | yes |
| core-play-completion | `0c455c5f3509…` → `a9330308d590…` | `bfb11f7b8a37…` → `dc94ebd7f782…` | yes |
| equipment | `0ecf8da2e79f…` → `b01f54b91765…` | `57953e289c66…` → `7f8dadcd28c0…` | yes |
| magic-items | `57eb5f139abc…` → `bc4979d74a84…` | `7e5c0634306a…` → `28a7f4d5ceea…` | yes |
| monsters | `b566da06e7b9…` → `ff24d9daf6dd…` | `b06bc8efdb33…` → `9f30cf57619c…` | yes |
| spell-descriptions | `417304636453…` → `dce22fbd6f89…` | `47f8241b4fea…` → `e8830765f3e8…` | yes |
| spellcasting | `3459f537fb71…` → `1033979c0b93…` | `84d3131da477…` → `60a851733d07…` | yes |

**Only the schema descriptor changed** (`schema19/registry.py`). A focused test found Python class names in one invariant row's rule text. The changes:
- **Rule text:** `a nested DiceExpression or Rational is held…` → `a nested dice expression or rational number is held…`.
- **Ids:** `schema_19.integer-domain.{bound}` → `integer-field.domain.{bound}`, and `schema_19.accepted-value-objects` → `nested-value-object.accepted-rules`.
- **Loci:** `schema-19:integer-fields` → `fields:integer`, and `schema-19:nested-value-objects` → `fields:nested-value-objects`.

The schema hash moved, and so did every identity bound to it.

**What shows the content is the same.** The earlier preview bytes were overwritten, so no direct byte diff was run. The evidence is indirect:
- Both runs passed `verify_preview` against G1, with the same byte-identity results and the same representation delta (1,103 components replaced, 19,515 claims added).
- Per-batch facts, claims, expected rules and components are equal (table).
- `reports/reconcile.json` is byte-identical across both hashes (`276ec8fe…`).

## What acceptance would mean, and what it would not

**It would mean:**
- The 11 batches' accepted representation becomes the replayed proposal plus the C5 source facts, under schema 19.
- Every other accepted row stays byte-identical. That covers the 13 untouched batches and all spans, resolutions, binding and policy.

**It would not mean:**
- execution or certification;
- gameplay;
- runtime grant validation or `checks.py`;
- Capability stays code-owned and fails closed (Decision 4).

### Semantic deltas to accept explicitly

See `correspondence.md`.

1. **`tool_activity` is a new schema-19 identity family.**
   - It holds the 34 reviewed C5 activity keys.
   - A tool with two or more activities becomes a choice with one option per activity. Each option replicates the tool's common facts.
   - A single-activity tool states its activity directly.
   - Codex classified this as representing reviewed C5 identities, needing no separate scope decision.
2. **Two address corrections inside their own batches:**
   - temporary-HP absorption → `play.damage_and_healing/lost_first`;
   - Shield training → the nested `equipment.armor.shield/shield` (a nested-record relocation).
3. **Mechanical normalizations** (correspondence §Normalizations 1–12):
   - closed vocabularies for phrases;
   - union splits;
   - the possessor drop (all 25 have `turn_of = source`);
   - the profile decomposition into accepted families;
   - Weakening Breath's `ability_based`;
   - four `WeaponPropertyFact` fields.
4. **Context-shared single-value vocabularies** (provisional test detector):
   - `success` (save-override choice and repeated-save end);
   - `source_dies` (duration end and trigger);
   - `weapon` (conditional-defense attack and mastery damage type).

   Two value-object pairs share field names only; their field types differ.

## Evidence (focused diagnostics only; no full suite, no CI)

All of these ran on the final schema hash. All exit 0 unless stated.

| Check | Result |
| --- | --- |
| `lift_check.py` | 18→19 verified; G1 and predecessor unchanged |
| `scalar_diagnostics.py` | 164 integer fields at domain bounds; nested dice/rational; 0 failures |
| `invariant_exemplars.py` | 17 explicit rows refused and admitted from real facts; exactly-one rows witnessed both ways where data allow |
| `native_map` round-trip (re-run on the final hash) | 5,504 payloads are fixed points |
| `reconcile.py` | Per batch, by address and full payload: 0 missing, 0 extra, no replayed fact lost. Tool vocabulary equals the C5 keys. Each activity is on its own tool. Negative controls hold on the unchanged `option_set_violations`. |
| `build_candidate.py` (×2) | Sequential control reproduces G1. Changed chain accepted natively with no merge conflict. Byte-identical across two runs (preview and 11 proposals). |
| `verify_preview.py` | 36/36 (see the checks list below) |
| `run_focused_tests.py` on `test_representation_schema_identity.py` | **1 failed, 56 passed** (see below) |

`verify_preview.py` covers:
- 0 native findings;
- persist/reconstruct/re-identify;
- the preview's own gate passes;
- G1 is refused on schema only;
- cross-oracle refusal both ways;
- the 13 untouched batches' ordered rows are byte-identical;
- affected batches keep their ids and scopes, with simulated evidence only;
- lifts are G1's plus 18→19;
- resolutions, spans, binding and policy are byte-identical;
- the representation changed by exactly the replayed→new proposal delta (1,103 components replaced, 19,515 claims added);
- pins unchanged.

## Genuine dependencies and blockers

- **Owner semantic acceptance of the exact identities above (held).**
- **Landing needs a recorded successor.** A build at schema 19 refuses the committed schema-18 G1 oracle on the production path (`verify-preview.json`: G1's own gate fails on schema only). Merging the src change therefore requires the accepted successor oracle to be recorded natively in the same change. The successor is recorded like G1: G1 kept byte for byte and skipped by digest.
- **Remaining test failure:** `test_the_declaration_is_identity_bearing_in_the_oracle`.
  - It reads the committed `tests/.../data/bounded_oracle.json`, which is historical schema-18 accepted authority shared by 18 test files.
  - Updating it, `_schema_pins.CURRENT_SCHEMA_*` and the other schema-pinning files (legality, round 7, round 9, schema 12 and others) is landing work and was not run here.
  - This file is **not** reported as passing.
- **Before commit:**
  - `.secrets.baseline` entries for the new digests;
  - full gates (Black/Ruff/mypy/pytest with coverage, pip-audit, detect-secrets);
  - CI and Codex review.

## Final Codex independent review

The current preview at SHA-256 `cd9d1d27428a1525955f83091125489e96bbc7bd0977bb9f3ce83933883a20d3` is independently reviewed and ready for explicit Owner semantic acceptance. See `../issue-15c-implementation/codex-native-final-review.md` and `codex-native-final-inspection.json` there. The inspection directly reconciles the serialized preview's 5,515 added placements with the reviewed mapping, independently pins both relocation destinations and links all 11 rendered proposal identities. The historical-fixture test failure remains disclosed and must be reconciled before merge readiness. This review records no acceptance and authorizes no runtime publication or activation.
