# CRD Issue 5d — source-correction replacement packet (UNACCEPTED) (#132, #137)

**Status: ready for review. Nothing is accepted, recorded, published or activated.**

- No `oracles/` file is written, no resolution is recorded, and no acceptance stamp is copied.
- The committed oracle `srd-5-2-1-corpus-883aabdf-462.json` (sha256 `fdc698df61688d30f28872302cd9b0f53c8633058b3ff6eb320f6db31d056c87`) is still the accepted authority.

**Scope.** The packet covers the known source corrections and nothing more: the twelve accepted batches (136 records) and the six prior reference resolutions, regenerated on the corrected release. A broader error review comes after 5d.

**Equipment.** Equipment is separate and **UNACCEPTED**. It gets its own source and consumer review after the replacement. This packet asks for no decision on its content.

Background: `issue-5d-accepted-source-correction.md` records the defects and evidence. `docs/architecture/issue-5c-5d-clean-restart.md` §8.11 records the identity.

## 1. Release binding

| | Superseded (accepted) | Corrected (proposed) |
|---|---|---|
| Package UUID | `9717e288-c099-5217-b2d2-f89aeabd7b73` | `0b1a965e-28bd-55e6-ac13-bc7786a1bace` |
| Release version | `5.2.1-corpus.883aabdf-462` | `5.2.1-corpus.626c83f8-209` |
| Authoritative source hash | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` | unchanged |
| Units | 10,465 | 10,465 |

The corrected release was published only into the scratch store `.claude/_rc/newrel/afterworlds.db`.

**Accepted leaves.** All 691 accepted leaves survive the corrected build: none is missing and no occurrence moves.

- One leaf's content changes: Travel Pace goes from 613 to 593 characters, which is the reviewed two-row header (D4).
- Seven page citations change (D1, D2, D3, D5, D6). Chunk locators carry them; no proposal field holds a page.

## 2. Manifest (full hashes)

Proposals are in `.claude/review-notes/issue-5d-<batch>-REGEN-626c83f8-PROPOSAL.json`, all LF. `REPLACEMENT-ACCEPT.py` checks every row before it composes.

| # | Batch | `proposal_identity` | file sha256 |
|---:|---|---|---|
| 1 | conditions-pilot | `4b4a75569fed17ac9d2426ea6ddab1e167b5764f3fb92f042a86181918a6a041` | `0688c60b821e1533823045e2d82050fc8e6645a203fe9ce35a78aab511e58bcd` |
| 2 | actions-pilot | `976a795b2c886228f994e0e1751dde09323511cd0dbc54ef22488c6988c35429` | `c11410fc12364049b38fd3d50fd038244fd955cbaed0ca671ef2e0bdee4fe814` |
| 3 | reference-closure | `d704a1d112cb87552e54cbd7433103ffef460f3bb19d1e6344a8ae9ef8e21d9e` | `cdb6c3d78c9b398d6ae64acc9c95eac02661761b66010c55d1868517ec511fda` |
| 4 | movement-closure | `e6944aeadf69a4ad419a96ecf962b06e7c43f9812a49de1ccd3fa869312753c5` | `6e0ad499cbb4a35735dafc401264eb2c4ecea878cb3242afae4263abdc32c78e` |
| 5 | combat-turn-1 | `b6069ce56e7a5018bb202cfc3780b299533a4f066727f22f443380efd5ff04ac` | `1408b237b0f601ba441389c57196b84d20c54bbbfbc867a7a10e1d71b87e88cb` |
| 6 | damage-and-hit-points | `bcebfcd7390c460097c05c0128dc9ebd39cbc584691f5d506de1cbea1f61caf0` | `22815b07fe98f59da41773ae9ec253a4628808f14561e04048e38be7a3de9477` |
| 7 | combat-damage-breaking | `2182e3f0ef7db6e88d95c3722ce6908f16c46fe3ed8216db75dbf44cf5e9a387` | `a76562c12ea2e09288845338923e5ded305cb71b0f9b9638f9ca71e981816eb4` |
| 8 | checks-actions-rests | `12c35a404e54ca567b68277538373a0d69b0c51a2fb52bd4b4f5f743016b696e` | `efdec82afc0320dfcc97b9384c5909d9909110521790aa8db22013b47daf5b5b` |
| 9 | core-play-completion | `7c9b2c3df60f85f89b8932a376c9b91636cad70bd5555e9fd86ad930d41ecf00` | `a864faf4346b3420d2b3ee26c6797f678a6ef04afc4fb647c8068616f7f45608` |
| 10 | core-play-dependencies | `8c92d9bbd927d744680e8ff4f09a14a04fc8a6554773766c1d6e160c4e11b569` | `c863a1b678ab316368182dadee692c77990b470dbee5d5e6267da7b35bf8066e` |
| 11 | character-creation-foundations | `b931d6535495d6f9731d45bb22854ef91ceeecf8899c007028108bb40b878ce7` | `622c7d5abd7ce72a4bfa31e8d95244ceb072f171fe92b2309fd9d671049cda4f` |
| 12 | character-origins-feats | `81b1abf7c18dd4f77ba7bb2b1a61b6369471723de5846c68e5d3c602073092c8` | `be792837776c8edbf515018493a03146295e6f1b067213142fd66fdf95f56422` |

| Artifact | sha256 |
|---|---|
| `issue-5d-reference-resolutions-REGEN-626c83f8-DRAFTS.json` (6 drafts) | `586143277f0ed031d2d532a4a6297fe694e6c6f313147b1a947d5889215c3c01` |
| `issue-5d-source-correction-REPLACEMENT-ACCEPT.py` (simulation + prepared recording) | `ae1d370a67e28369137f97378d928d0e66188124787381d44e0c337e295af6f9` |
| `issue-5d-core-play-completion-generator.py` (corrected `TRAVEL_PACE_TABLE`) | `3c5b466a299728a344e728457c114aedcc038139970d34c1b962a31f98aaa174` |
| `.claude/_rc/simulate.txt` (simulation output) | `1e0f9a268aac31f5f6ae5d1468d4302ec4a6396984b7803d9a4b8949bd19c423` |
| `.claude/_rc/cmp_oracle.py` / `cmp_oracle.txt` (oracle comparison) | `899f54964778c0fccf7281458f9635b42d0b48fd00a288e20036745dac4b62c6` / `c84c2781a9a32d01218914ce8b2f0e284a2c5ffc3308bc60a77e18cda75983c1` |
| Committed oracle, unchanged | `fdc698df61688d30f28872302cd9b0f53c8633058b3ff6eb320f6db31d056c87` |

Equipment is outside this packet and is listed for identification only. Its REGEN proposal has identity `a581b3888559c0c7734481a10df760597a37cd1cb45d51163c7bfc9490a8bfc8` and sha256 `ab2e1c29a4491ed4d875a6a1fe6dfe68b83b22802d1e95882209a6b9abb79341`. Its drafts have sha256 `d284871b279e66cf7abd0b96534ea428c9814b46eba3cdbdf0f67b2926bf1ce4`.

## 3. What differs from the accepted chain

The committed oracle was compared with the simulated composition (`cmp_oracle.py`). Chunk, span and batch identities and the release binding were remapped, the reviewer, timestamp, rule and authorization fields were blanked, and the lists were compared as multisets. Everything matches except the following:

- **Derived, in all twelve batches.** The release binding differs. Every chunk ID re-mints (`content_id("chunk", package_uuid, leaf_id)`), which is 1,530 references. The six resolutions differ only in `release_binding`.
- **Known correction, core-play-completion only (D4).** The Travel Pace span `char_end` goes 613 → 593, as does the `travel_pace` prose binding's `chunk_char_end`. The span ID re-mints from `3a63e968-f4bf-5776-ba24-bca5e5e8fd20` to `b2b517d6-e7e4-55c9-8271-721569ece0d9`. That moves its sort position in the batch `diff` list and in `core-play-completion/exploration` `expected_rules[16].source_span_ids`. `semantic_diff_hash` goes `f2cc6a890a5c9b1db167c56d53fedf6e27b19dad62c4bbe38b4ec4e5dc33a012` → `9409049a625bd232c1166cc7de8e2bd06d41291d69b5196d571d67a86b81f72a`.
- **Unchanged.** Records, components, facts, references, dispositions and rationale do not change.

## 4. In-memory simulation (not an acceptance)

`python issue-5d-source-correction-REPLACEMENT-ACCEPT.py --simulate` composes the twelve proposals through the existing native seams. `accept_proposal` runs over each prior, with schema lifts carried natively. `resolve_references` runs after checks-actions-rests (attack roll), character-creation-foundations (armor_class, proficiency_bonus) and character-origins-feats (choose_background, choose_species, background_feat).

- **What it writes.** Nothing. The reviewer is the literal `SIMULATION - not an Owner approval`.
- **What it asserts.** The resolutions it records must equal the drafts file.
- **Result.** rc 0, with no native limitation hit.

| Check | Expected | Simulated |
|---|---|---|
| Batches / schema | 12 / `5d-representation-schema-16` | same |
| Records / spans / review units | 136 / 1,016 / 136 | same |
| Resolutions | 6 | 6 (equal to the drafts) |
| Findings | 9,443 uncovered leaves + 91 references | 9,443 + 91; 0 ambiguous; no other findings |
| Catalogue members in printed order, and `_select` per section | pass | pass |
| GameMaster view: absent passages, components out of source order | 0 / 0 | 0 / 0, over 594 components |
| Travel Pace table is the corrected leaf | yes | yes |

**Travel Pace heading association.** This parses the consumer's passage, expanding the `thead` colspan:

| Pace | Distance Traveled Per … / Minute | … / Hour | … / Day |
|---|---|---|---|
| Fast | 400 feet | 4 miles | 30 miles |
| Normal | 300 feet | 3 miles | 24 miles |
| Slow | 200 feet | 2 miles | 18 miles |

The simulated bytes (sha256 `d999a1fe6bef0e18001b051e5ee0127fa1d6f76a07f14fa935d312fb5a075bfd`, 2,464,793 bytes) are **not** the bytes a recording will produce, because those embed the real reviewer and timestamps.

## 5. Recording path (prepared, not executed)

The workflow is the established one: **one consolidated Owner approval** covering the twelve batches and six resolutions, **after which Claude records**.

1. Claude fills `APPROVAL` (the decision, verbatim), `AUTHORIZATION_REFERENCE` and `ACCEPTED_AT` (a UTC clock read taken just before recording) in `REPLACEMENT-ACCEPT.py`.
2. Claude runs `record`. It rebuilds the same chain with reviewer `Ravenlok (Owner)` and writes `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-626c83f8-209.json`.
3. `record` refuses while any of those fields is unset, and refuses if the target already exists.
4. `record` stamps one UTC clock read on all twelve acceptances and all three resolution actions, which departs from the per-step clock reads of the earlier `*-ACCEPT.py` scripts. Per-step reads are a small change at recording time if they are wanted.
5. The old oracle stays beside the new one. Retiring it and its `ACCEPT.py --verify` replays is follow-up work.

## 6. Mechanical test failures against this candidate

Mechanical tests: 64 failed, 3,718 passed, on the tree before one derived pin was updated. The pin update (`test_character_origins_feats_proposal.py`, `MULTI, UNLIKE_CHUNKS = 9, 7`) fixes one of them and that test was rerun, so 63 are expected. The full suite was not rerun.

Each failure's error line was checked. **None is a real incompatibility.** Every one replays the committed old-release authority against the new build:

| Cause | Tests |
|---|---|
| `ReleaseBinding` mismatch (old chain vs build) | composed_*, accepted-components printed order, reference-closure combat_pointer ×2, movement-closure disjoint / composed_the_four_close |
| Committed proposal bytes ≠ bytes the tree derives | committed-bytes, emit |
| `AcceptanceError` cross-release check | once_accepted |
| `PersistedStateReconstructionError` (old leaves not in the new ledger) | committed-authority printed_order, gains_no_membership |
| No oracle for the new package | publication_stays_blocked, breaking_objects, readiness |
| Old chunk IDs applied to the new release | actions-pilot composed |

The simulation reproduces each behavioural assertion on the new binding: counts, findings, catalogues and printed order. Recording creates the oracle for the new package. The byte and identity pins in the tests and the committed proposals still have to be re-pointed to the REGEN artifacts, so the branch will not be green from recording alone.

## 7. Gates and blockers

| Gate | Status |
|---|---|
| Corpus / source | 274 passed, 117 skipped |
| Black / Ruff / mypy | Clean on changed `src/`, tests and `REPLACEMENT-ACCEPT.py` |
| Mechanical | Red, as in §6 |
| detect-secrets | Blocked. The baseline edit was denied (Security Weaken) and that denial stands. |
| pip-audit | Deferred (31/11), non-green |

**detect-secrets detail.** Two finding sets are held for Owner terminal handling, and neither is independently verified:

- `.claude/_rc/secrets_delta.txt` (sha256 `c84f8bfb5bfdb9bdff2c03923d035b97cfd6618e272e3ce3f866acceb97a1845`): 221 findings.
- `.claude/_rc/secrets_delta_accept_script.json` (sha256 `6f58a6aeaf39c1136607f24dd259a211a33c6c0657e0f341c990838960e484dc`): 25 more, the public hex hashes in `REPLACEMENT-ACCEPT.py`.

**Blockers:**

1. Review of this packet, then one consolidated Owner approval.
2. Owner terminal handling of the secrets baseline.
3. After recording, the test pins re-pointed to the REGEN artifacts.
4. pip-audit.

No commit is made while gates are blocked.
