# CRD Issue 5d (#137) — Monsters source corrections: integration review

**Status: REVIEW MATERIAL. Nothing is accepted, recorded, committed, pushed, published or activated.**
No Owner semantic acceptance exists for any artifact named here. The replacement chain and the
Monsters packet below are unaccepted proposals, ready for Codex review and then the Owner's exact
semantic acceptance. Recording is a separate later step that does not exist yet in any script.

The accepted oracle `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-574662e9-0ef.json`
is byte-unchanged: SHA-256 `fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62`, checked
at the start, inside every simulation run (`against_accepted` asserts it), and again at the end.

The candidate this integrates is `issue-5d-monsters-source-correction-candidate-review.md`.

## 1. Provenance corrections made before integration

The independent review of the candidate found five residue items. Each was corrected in place before
anything was integrated.

| Residue | Correction |
|---|---|
| `source_pin.json` (~l.396), the corrections doc (~l.278) and the candidate review (~l.33) called the Young White Dragon save correction "explicitly Owner-directed". | They now say it is an **official-source-backed correction proposed under an Owner-requested investigation**. It is family N in the corrections doc, and it is not an Owner decision and not a formal erratum. The **Veteran Warrior** naming is recorded separately as the Owner's explicit decision. The errata check is recorded as done first, on 2026-09-27, with its outcome. The D&D Beyond SRD page lists no SRD 5.2/5.2.1 errata document. The Monster Manual (2025) errata v1.0 has no Young White Dragon entry. The record states that this does not show no erratum exists, and none is claimed. The disagreement is recorded as it stands: the current official individual stat block prints −2, while the Basic Rules / SRD page prints `2`. |
| `scripts/regen_community_source_coverage.py` (~l.465–475) and the generated coverage `qualification.remaining` said the unsigned save was preserved. | Both now record the correction and the official-source disagreement. The coverage JSON was regenerated from the script. The review evidence (the PDF page prints it unsigned) is kept as an anomaly note. |
| Other alphabetical-part ordering was described as an undecided Owner rule. | It is now described as deferred and outside bounded scope. Source-order fidelity is settled. No broad reorder was made. |
| The candidate review said the task directory "could not be written". | That was a restriction asserted in a compaction summary. It was not a failed write, a tool error or an OS denial: no write was attempted and `permission_denials` was empty. The wording is corrected. Permissions were not probed or changed. Repository output is used. |
| The gate claim for scratch `check.py` overstated the evidence. Black was run after a failed check, with no final check, and Ruff covered only the three candidate files. | The claim now says exactly that. No duplicate unmodified suites were rerun. |

## 2. What was integrated

These are exactly the three reviewed source corrections and the scoped two-file order change. Nothing
else was changed.

| Change | Where |
|---|---|
| Succubus: `**AC** 15 **Initiative** +3 (13) <br>` on the AC line, before HP and Speed. The separate `**Initiative** +3 (13)` paragraph after CR is removed. The official PDF supports this. | `monsters-A-Z.md` |
| One *Veteran Warrior* identity: the heading `### Warrior Veteran` becomes `### Veteran Warrior`. This is the Owner's explicit decision. | `monsters-A-Z.md` |
| Young White Dragon INT SAVE `2` becomes `−2` (U+2212). The MOD was already `−2`. The current official individual stat block (DDB 5195287) prints −2. | `monsters-A-Z.md` |
| General *Monsters* rules before *Monsters A–Z*. The official PDF prints pp.254–257 before p.258. Only these two files move; every other file keeps its order. | `CORPUS_FILES` in `src/afterworlds/ingestion/corpus/source_units.py` |

Metadata was updated for these changes: `source_pin.json`, `PINNED-SOURCE.md`, the corrections doc,
and the regenerated coverage JSON. All 235 stat blocks are preserved.

## 3. The private release

The release was finalized through the native lifecycle into
`.claude/_rc/msc/rel/afterworlds.db`, a private scratch database. There were no shared-DB, Chroma,
publication or activation writes.

| | Old (`.claude/_rc/corr/rel`) | New (`.claude/_rc/msc/rel`) |
|---|---|---|
| package_uuid | `ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` | `67c81736-15fd-5e82-8523-e84922f0a7c6` |
| release_version | `5.2.1-corpus.574662e9-0ef` | `5.2.1-corpus.3fe24ff6-4e3` |
| authoritative_source_hash | `8974902d…3d87` | unchanged |
| transform_config_hash | `2a7feddf…2e64d` | `648ac3dd…d947` |
| bundle_root_hash | `3da7b5b3…754689` | `87d95278…7f760` |
| persisted_corpus_digest | `df64eb40…acb02` | `8b7227d3…2d42` |
| leaves | 10465 | 10464 |
| citations | | located 9014, placed 22, anchored 85, inherited 1343 (was 1344); none unresolved |

The new database file has SHA-256 `ffeb731fa2aeaeecc4518014081bb1d503f65b0d7239c7756b87b43943d517e0`.

**Leaf delta, content-level (`leafdelta.py`).**

- The 116 *Monsters* rules leaves move ahead of *Monsters A–Z*. They are the same contents in the same
  internal order.
- Succubus AC: content changed (merged line). Its id re-mints `ce4c8770…` → `e4aa472b-e407-5c13-a66f-0b8c1fc5433d`, and it is now **located** (it was inherited).
- The Succubus ability table and Skills leaves re-mint only because the leaf id hashes the page,
  extent and content, and a leaf above them was removed:
  - ability table: `b2328b62…` → `0ca1f0e6…`;
  - Skills: `30431c78…` → `259abeef…`.
- The Succubus `**Initiative** +3 (13)` leaf `31ad8913…` is deleted.
- `### Veteran Warrior` keeps id `1f867f09-43ec-5b36-ad7d-a5a1211944fd`. Its citation goes from located to **inherited**, still p.337. The PDF prints "Warrior Veteran", so the heading no longer locates.
- The Young White Dragon table keeps id `912f6912-4d97-53ac-9d0c-3df02983e9c7`. Its content changed and it is still located.

## 4. Replacement of the twenty accepted batches and 1099 resolutions (native, fresh)

`issue-5d-monsters-corrections-REPLACEMENT.py` rebuilds the 20 batches from fresh `REGEN-3fe24ff6` proposals and drafts on the new release. Its only mode is `--simulate`, and that mode:

- writes nothing;
- uses the reviewer `SIMULATION - not an Owner approval`;
- carries no approval, and restamps no historical approval as a new one.

Spell Descriptions, Gameplay Toolbox and Magic Items are drafted with `prior=` their predecessor, as in the reviewed spell-correction replacement precedent. That precedent was applied as a pattern, not replayed.

| Artifact | SHA-256 |
|---|---|
| `issue-5d-conditions-pilot-REGEN-3fe24ff6-PROPOSAL.json` | `f142f4886af7d006b3a993839aedd04f23d5b528812e9cd40e32d8734959ac71` |
| `issue-5d-actions-pilot-REGEN-3fe24ff6-PROPOSAL.json` | `52e27e59cbd577fa504fa7cc7d5cd880bbc9a4662a581d03e55d7d57bd183186` |
| `issue-5d-reference-closure-REGEN-3fe24ff6-PROPOSAL.json` | `916ebb077ff54b30a01b6edd73225a2e434c4840546b37fd4d2c7c8ea89e60fe` |
| `issue-5d-reference-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `7892d71ff3d873bff1c7451b03ef01d5d424b754e81b04407501f6a51d367668` |
| `issue-5d-movement-closure-REGEN-3fe24ff6-PROPOSAL.json` | `c8d55fdd5997fc54ce3627d975c48e570c1ad461be00ce461e0dc215631fe05d` |
| `issue-5d-combat-turn-1-REGEN-3fe24ff6-PROPOSAL.json` | `a19c134d15da05450836532cb49522b3f9bde7f20788621c227e39acf22a1ba7` |
| `issue-5d-damage-and-hit-points-REGEN-3fe24ff6-PROPOSAL.json` | `9d27e3fe5b47e055228b68d82017d6bcb1524cf56843e88899ee88eb4f2b74f6` |
| `issue-5d-combat-damage-breaking-REGEN-3fe24ff6-PROPOSAL.json` | `92a936cafc49cfef0c62ddc2afe8891082c24c925d294d338dc22aa23e1c2508` |
| `issue-5d-checks-actions-rests-REGEN-3fe24ff6-PROPOSAL.json` | `9ae8519578fa9a727716ff5bd8fa2d500c191b11e8fb500180e6285fa83cdf82` |
| `issue-5d-core-play-completion-REGEN-3fe24ff6-PROPOSAL.json` | `3faee5fc525aab542ec8993ac95f1b035085597ad74d7b7b2f17df1b96ff603e` |
| `issue-5d-core-play-dependencies-REGEN-3fe24ff6-PROPOSAL.json` | `87c1f5418ee22d092cdf73931107048d495e50132f303ba7857161da9454aa20` |
| `issue-5d-character-creation-foundations-REGEN-3fe24ff6-PROPOSAL.json` | `bf7f3c955413de03151aa67b1f0143731d705eec0cc22287fd6a422f40d11467` |
| `issue-5d-character-origins-feats-REGEN-3fe24ff6-PROPOSAL.json` | `bb85ca76fa6cd1c781d86389c72653ddd76e2c7bb1926e1625cdb698d1fd61d6` |
| `issue-5d-equipment-REGEN-3fe24ff6-PROPOSAL.json` | `12a124ce2b09f32a2d3d9d41256b4d0501692a7574a781e97c6ca9e61bd426f3` |
| `issue-5d-equipment-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `a672c7606aaf77af47ebbf7ee2c978f57c8a0c89f7f8d2d9e2406e33b10647ba` |
| `issue-5d-spellcasting-REGEN-3fe24ff6-PROPOSAL.json` | `cb0b1f97ed7a64f8ac59722bd3e51efb200d6beb6a33f6c77e4a79c82e456124` |
| `issue-5d-spellcasting-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `fd45ef74d3f1b34eb715bcac1711123d6524ba322349638c69eb51392ec5587c` |
| `issue-5d-rules-glossary-completion-REGEN-3fe24ff6-PROPOSAL.json` | `f16160d9523e2b43a3c2eb310104849e6a758c88d566683c90dbb579155aa473` |
| `issue-5d-classes-REGEN-3fe24ff6-PROPOSAL.json` | `5df314c3c8bd282c9ca72dc2048d9b30ba7131b7d1d464d21530a9e169788839` |
| `issue-5d-classes-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `819eacf602bd670a62e9c25ad7028b465db0f6a21b2acac2d5d8847e94c5f00e` |
| `issue-5d-class-option-catalogues-REGEN-3fe24ff6-PROPOSAL.json` | `64e4b9fc3094a620fdacc9795757a3abf156793c874a0fd109cfd0ca5017f695` |
| `issue-5d-spell-descriptions-REGEN-3fe24ff6-PROPOSAL.json` | `21d61891618928683ddb6f06f57a9d9dac0db2805dc9b5f66badbf61f611fe33` |
| `issue-5d-spell-descriptions-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `d85523852b036c80c73ff8d170622eaef3cf7f18bb2c6a95a402c45ae0bc29dd` |
| `issue-5d-gameplay-toolbox-REGEN-3fe24ff6-PROPOSAL.json` | `644d7ebf8f06dd19fc81a02fb8af89a9e95aea55240a11d6daf936ffab936542` |
| `issue-5d-gameplay-toolbox-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `c499cd7f36a26e02ed9b44c52326b0dac07c3518bf528e51bc7ccd046515f3f8` |
| `issue-5d-magic-items-REGEN-3fe24ff6-PROPOSAL.json` | `7107c4897ae10609298927a100558ec9fe3c77a52194df8c89d2660176896be0` |
| `issue-5d-magic-items-resolutions-REGEN-3fe24ff6-DRAFTS.json` | `c5bcd92e5235b8a3e86970e1a1a10e48daa84d5c119e1e5a8f8f92d1a60d9621` |
| `issue-5d-monsters-corrections-REPLACEMENT.py` | `fb11995a067bd52ca5227508d4a7da7be0059b901789c9a82d76b3c9a0cdc568` |
| simulated chain bytes (in memory) | `caad48afb76183296a4e8936efda93fa215f5837d21bb9894d39d65dbf88c3ae` |

The full per-batch manifest (identity, counts, findings) is in `.claude/_rc/msc/regen.log`.

**The chain against the accepted 1250 records (`cmp_oracle.py`, and `against_accepted` in the script).**
The full artifact was compared order-aware and untruncated. Only release-derived identities were mapped:

- binding values;
- chunk ids;
- span ids, paired by (leaf, extent);
- `proposal_identity`.

Acceptance evidence was blanked, and the actual historical approvals are listed in `cmp_oracle.txt` as evidence.

- **0 positional differences.**
- Four lists hold the same multiset in a different order: `acceptance.records`, `acceptance.review_unit_records`, `representation.prose_bindings` and `representation.provenance`. Each is `canonical_order` (ADR-005d Decision 6) in both artifacts, so its order follows re-minted ids (`cmp_order.txt`). This is a derived change, not a semantic one.
- All 5978 distinct accepted span leaves (6450 spans) survive in the new release. None has changed content, pages or status.
- The chain counts are (20, 1250, 6450, 950, 1099), with 0 resolution violations and findings 315 references / 4003 uncovered leaves. The old release had 4004 uncovered leaves: the difference is the Succubus leaf that no longer exists.

## 5. The regenerated Monsters packet

| Artifact | Value |
|---|---|
| `issue-5d-monsters-PROPOSAL.json` | SHA-256 `cdf06f4307bd09786f73cc16e4cf75c6609595c9a041ef4d1f47c9dbcf9a4336`; identity `0fd9e1698985748b81499def620a37b89c52a6b8cdc5a4ead69a1b57911239df` |
| `issue-5d-monsters-resolutions-DRAFTS.json` (83 drafts) | `1733d78c91f56092b163732e0fc354cf5d21e6fd907f32fe33f7c440f74dc792` |
| `issue-5d-monsters-generator.py` | `760dfb9699a0e144b97b602895f2d14c79ba268684a18f9142fa98857472b192` |
| `issue-5d-monsters-source.py` | `1f9d3d221813f4cc61ec23262218b3de4821150beb8cc2aacf5f956c913f3ae8` |

The generator now composes over the unaccepted replacement chain (`current()` loads the REPLACEMENT simulation, held to `caad48af…`), not over fc62. It scopes 3139 leaves:

- 414 records (2 rules, 177 groups, 235 creatures);
- 948 components;
- 7046 bindings;
- 2348 references;
- 9732 provenance claims;
- 414 review units.

The anticipated 83 drafts and 3139 leaves are the actual counts.

**Old → new (`cmp_monsters.py`).** The old packet was rebuilt byte-exact in scratch (`rebuild_old.py`, reproducing `d8508c64…` / `61131f91…` on the old release). Only release-derived ids were mapped. Object lists were confirmed to be in derived set order on the raw artifacts and were compared as multisets, and that includes the draft list; scalar lists were compared positionally. So the comparator alone does not prove draft order. Codex review 11816 closed that gap independently: all 82 unique old resolution ids remain in exact sequence in the new DRAFTS, around the sole insertion of the Veteran Warrior draft at zero-based index 54. Together with the normalized payload equality below, this establishes that draft order is unchanged apart from that insertion. The comparator was not rerun. With ids mapped alone there were 162 differences. With the reviewed rename (`warrior_veteran` → `veteran_warrior`, "Warrior Veteran" → "Veteran Warrior") also applied to the old side, **16 differences** remain, all expected:

| # | Difference |
|---|---|
| 1–3 | The Succubus Initiative span `a43d45a6…` is removed, together with its prose binding and its primary provenance. |
| 4–7 | The Succubus AC span and binding: extent 0–75 → 0–98 (the merged line). |
| 8–11 | The Young White Dragon table span and binding: extent 0–866 → 0–867 (U+2212 adds one character). |
| 12–13 | The Succubus review unit loses the Initiative span and leaf. Its leaf-id order is id-derived. |
| 14–15 | The Young White Dragon review unit has the same span set, in id-derived order. |
| 16 | New draft at zero-based index 54 (the 55th of 83): `resolve-magic-items-deck-of-illusions-deck-of-illusions-veteran-warrior-monsters-1`. It resolves `magic_items.deck_of_illusions` / `deck_of_illusions` "Veteran Warrior" → `monsters.warriors.veteran_warrior`, with provenance span `b7732ec0-937a-53a4-a6c0-faeb668e42e9`. |

| Count | Old | New |
|---|---|---|
| spans | 3140 | 3139 |
| prose bindings | 7047 | 7046 |
| provenance | 9733 | 9732 |
| drafts | 82 | 83 |
| records, components, references, relationships, review units | | unchanged |

**Composed in memory** (accepted and then resolved, over the replacement chain; nothing recorded):

- counts (21, 1664, 9589, 1364, 1182);
- 0 resolution violations;
- the twenty-batch chain is preserved byte-for-byte in payload;
- findings go from 315 references / 4003 uncovered to 317 references / 864 uncovered. That is 315 − 83 drafted + 85 left unresolved in the packet, and 4003 − 3139 = 864.

No unexpected semantic delta was found at the candidate or native level.

## 6. Production consumer: rules-first reading order (derived, disclosed)

The production rules-authority service orders each component's governing prose by the release's leaf `occurrence_index` (`application.py`, prose sort key). The order change in §2 puts the rules first, so a creature read is now, per component, **the governing *Parts of a Stat Block* rules not yet read, then the creature's own leaves**. It used to be the creature's own leaves, then the rules. The reviewed `CORPUS_FILES` comment already names this: "direct reads order passages by that index".

A probe was run through the service over one persisted draft, on all 235 stat blocks (`.claude/_rc/msc/probe_monsters_read.py`; output `reads.json`, SHA-256 `8b9b73fa…73e1`):

- **235/235** reads have exactly the same texts as before, as a multiset: no content is gained or lost;
- **235/235** reads equal the rules-then-own model.

The Aboleth read now opens with seven rule passages before `### Aboleth`:

1. alignment;
2. Initiative;
3. Initiative score;
4. Hit Points;
5. ability scores;
6. *Running a Monster*;
7. telepathy.

This is a product-visible consequence the Owner should see at acceptance. It is listed separately from the 16 artifact rows. Restoring own-then-rules would be a service-ordering change, which is outside this bounded scope and is not made. Overrides and suppression, context, dedup (each governing span once per read and per multi-selection), references and group reach are all unchanged and tested (§7).

## 7. Tests and pins

`tests/ingestion/mechanical/test_monsters_proposal.py` now pins the new packet identity and hashes. Its `prior` fixture requires the chain it composes over to be the REPLACEMENT simulation (`SIMULATED_SHA256`, and the new release UUID). It does **not** treat the accepted oracle as new: `ORACLES` is still checked byte-unchanged on disk.

Updated counts:

- (82, 79) → (83, 78);
- 3140 → 3139;
- 4004 → 4003;
- 1099 + 83;
- 315 − 83.

`_read` now models rules-then-own (§6). The following tests were added.

`test_the_release_carries_the_reviewed_corrections`:

- the release's leaves are `LEAVES` in occurrence order;
- the rules part comes first;
- the Succubus merged AC/Initiative line, and no standalone Initiative leaf;
- one Veteran Warrior (no "Warrior Veteran" anywhere, one heading, one creature record, `BLOCK_KEY`);
- the Young White Dragon INT `6 / −2 / −2`.

`test_the_corrected_stat_blocks_read_as_printed`: the Succubus, Veteran Warrior and Young White Dragon, read through the production service, show their own printed leaves in order, and the read equals the model.

The live chain dependencies are untouched:

- the `REGEN-574662e9` files;
- the SD, Gameplay Toolbox and Magic Items PROPOSAL/DRAFTS;
- `corr/rel/afterworlds.db`;
- `issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`;
- the COMMITTED/RECORDED pins in `tests/ingestion/mechanical/_replacement_chain.py` and the oracles README.

Tests that replay the committed old-release authority against the new build are therefore red by construction until a recording moves them (§8).

`issue-5d-monsters-review.md`, the prior round, carries a superseded banner for the facts this packet changes.

## 8. Gates (actual exits)

| Gate | Result |
|---|---|
| `test_monsters_proposal.py` | 13 passed, exit 0 (500.8 s). Black reformatting of this file and the REPLACEMENT import/`extent` typing fix landed while that run was in progress. They are formatting-only and typing-only. The script was re-verified by the rerun below. |
| REPLACEMENT `--simulate` (rerun after the edits) | exit 0. Output identical to the first run: 0 differences from accepted; chain and Monsters counts and findings as in §4–5. |
| Black `--check` (REPLACEMENT, generator, test) | exit 0 |
| Ruff (same three) | exit 0 |
| mypy strict, targeted (`MYPYPATH=src`) | exit 1. The three changed files are clean. The 3 errors are in the pre-existing, unchanged `tests/ingestion/mechanical/test_character_origins_feats_proposal.py` (l.888, 1755, 1759), which mypy follows through an import. Not changed here. |
| Ingestion suite (`tests/ingestion`) | **exit 1**: 82 failed, 4151 passed, 131 skipped, 37 errors (47 min 20 s; log `.claude/_rc/msc/suite.log`). `test_monsters_proposal.py` passed inside the run. Every failure and error is classified in the table below, and no semantic delta was found. The suite was not rerun after the pin repair below. |
| Three release-derived pins, repaired (only these three tests run) | **3 passed, exit 0** (102.79 s): CCF `test_a_gamemaster_reads_every_component_whole`, Equipment `test_a_gamemaster_reads_every_component_in_printed_order`, Glossary `test_scope_is_every_unauthored_entry_one_record_each`. Command: `rtk proxy D:\AI\Claude\afterworlds\venv\Scripts\python.exe -m pytest <3 node ids> -q -p no:cacheprovider --no-cov`. Black `--check` and Ruff on the three files: exit 0. |
| detect-secrets hook, 44 files ×2 (final baseline) | `rtk proxy venv\Scripts\detect-secrets-hook.exe --baseline .secrets.baseline <44 files from .claude/_sp/msc_files.txt>`: run 1 exit 0, 0 output lines; run 2 exit 0, 0 output lines. Baseline sha `ffc66c34…b190` before and after both runs. See the note after the suite table. |
| detect-secrets hook, three edited tests ×2 | exit 0 twice, baseline sha stable. The three files have no baseline entries. |
| pip-audit | Deferred, non-green |
| expanded mypy | Non-green, deferred |

**Suite failures by cause.** `conftest.source_release_db` builds the repo snapshot, which is now the private release `67c81736…/3fe24ff6-4e3`. The committed chain still binds `ebdd9333…/574662e9-0ef`. So every red below except the last family replays the old-release authority against the new build, the same shape as REPLACEMENT-PACKET §6. Those 79 failures and 37 errors are not fixed here and stay honestly non-green until recording, because re-pointing them before acceptance would make the tests pretend the accepted oracle is new. The last family (3 failures) does not depend on the old release and is repaired pre-acceptance; see below.

| Cause | Failed | Errors | Representative tests |
|---|---|---|---|
| Committed proposal bytes ≠ bytes the tree now derives | 28 | – | every `test_the_committed_bytes_are_what_the_published_release_derives` and `…still_derives_the_accepted_bytes`; `emit_writes_only…` |
| `ReleaseBinding` / session binding mismatch | 17 | – | `composed_*`, `accepted_components_read_in_printed_order`, reference-closure `combat_pointer` ×2, movement-closure `disjoint` / `four_close`, `a_session_is_the_published_release` ×2 |
| `AcceptanceError` cross-release check | 7 | 27 | `once_accepted_*`; the magic-items, equipment, gameplay-toolbox and spell fixtures that accept the prior chain |
| `PersistedStateReconstructionError` (old release not in the new ledger) | 5 | – | `committed_authority_reads_in_printed_order`, origins `each_catalogue_in_printed_order` ×3, `gains_no_membership` |
| Old-release binding read against the new DB (empty snapshot) | 13 | – | `publication_stays_blocked*` `(0, 0) == …` ×8, `set() - {…}` ×3, movement `0 == 10280`, core-play `breaking_objects` `0 == 3` |
| No oracle for the new package (`committed_inputs_for` → `None`) | 2 | 10 | readiness `only_the_two_pilot_authorities` and `unreviewed_projection_is_typed_refused` (ABSENT vs UNRESOLVED); classes/glossary `prior` fixtures |
| Old chunk ids applied to the new release | 7 | – | actions-pilot `composed` (88 prose-binding findings), magic-items `batch_checks`; `accepted_then_resolved…` for gameplay-toolbox, magic-items and spell-descriptions (`(18578, 5620)` vs `(143, 5621)`, …); equipment/spellcasting `publication_stays_blocked` (`prose binding` findings, not `reference`) |
| Release-derived coordinate / opaque-id pins (**repaired since the run**) | 3 | – | Glossary `RULES_DEFINITIONS = range(7866, 8350)`: `ability_check` now starts at 7867, a −1 shift. Monsters precede rules-glossary in `CORPUS_FILES`, and the reviewed Succubus merge removes one leaf (10465 → 10464); the second members of the `(…, 5620)` pairs show the same −1. Unlike-chunk-order counts: CCF `18 == 17`, Equipment `(120, 72) == (120, 68)`. These count opaque chunk-UUID order; the printed-order assertion in the same tests held. |
| **Total** | **82** | **37** | |

The last family is the only one not in the precedent table. It is derived, not semantic: one leaf shift from a reviewed correction, and chunk-UUID reshuffling from the new package identity. It does not replay the old release, so it is repaired before semantic acceptance, as the precedent packet did for `MULTI, UNLIKE_CHUNKS = 9, 7`. Each expectation was confirmed against the current source (the private release DB):

- CCF unlike-chunk-order count `17` → `18` (`test_character_creation_foundations_proposal.py`);
- Equipment `MULTI, UNLIKE_CHUNKS = 120, 68` → `120, 72` (`test_equipment_proposal.py`);
- Glossary `RULES_DEFINITIONS = range(7866, 8350)` → `range(7865, 8349)`, with the paired `[7866, 7867]` → `[7865, 7866]` (`test_rules_glossary_completion_proposal.py`). In the release, leaf 7865 is `## Rules Definitions`, 7866 its introduction, 7867 `#### Ability Check`, 8348 the last Weapon Attack leaf and 8349 `# Spells`.

Recorded authority was not re-pointed, and the printed-order assertions are unchanged. The `[7865, 7866]` pair sits in `test_composed_every_target_closes_and_133_leaves_gain_coverage`, whose `prior` fixture errors until recording (no oracle for the new package), so that one assertion cannot execute before recording.

**Secrets baseline.** The baseline went from `16ce260c…d22b` to `d4bd7305…dbcd`, then to `ffc66c346a4db95084d3a9cbd7f4eb8c74a7b2bd68939be1cfed445e24d9b190` (staged, 4503 entries).

- **What was appended.** 1183 Hex High Entropy entries, all public literals, under the real backslash keys: 973 sixteen-character public fact identifiers and 210 SHA-256 literals (64 characters), with 0 unmatched. There is no header, setting or flag change and no pragma. Scanning ran on copies under `.claude/_sp/msc/`, and those copies were byte-identical to the files at scan time. Stripping the 1183 entries from `d4bd7305…` reproduces `16ce260c…` byte-exactly, so that first step is a pure append. Before and after copies are in `.claude/_sp/mscrec/`.
- **First hook pair.** Exit 1 and exit 1; it reported all 1183 entries. The cause was my own defect: each entry's `filename` field still carried the `.claude\_sp\msc\` copy prefix. I corrected that field to match the key, which is the convention of every pre-existing entry. This was not a scanner denial of a new value.
- **Original 44-file hooks after that fix** (every file I scanned). Run 1: exit 3 with zero "Potential secrets"; the hook rewrote the baseline (saved as `.claude/_sp/hook_rewrite_baseline.json`). Run 2: exit 1, "baseline unstaged". An earlier staged-set run (`.secrets.baseline` alone, exit 0 twice) is not coverage of these files and is withdrawn as evidence.
- **Scoped maintenance (already authorized).** From the hook's rewrite, only the entries of the five touched files were taken; every other key, the key order, the 16 empty keys, the header, settings, flags and LF formatting are unchanged, and the hook's CRLF rewrite was not used. In those five files, 11 existing entries were refreshed (line number only) and 12 verified-absent historical values were pruned: `source_pin.json` 32 → 31, the Monsters generator 1 → 0 (key kept as `[]`), PROPOSAL 9 → 6, DRAFTS 7 → 4, `test_monsters_proposal.py` 7 → 3. Every live finding is kept. Result: `ffc66c34…b190`, 4515 → 4503 entries.
- **Why 8f7c655 does not govern these twelve.** That commit restored four different values, which were not even in this run's starting baseline. It is not an Owner decision about these twelve, and this settled maintenance needs no renewed Owner decision.
- **Final hook coverage.** The same 44 files, twice against the final baseline: exit 0 and exit 0, 0 output lines each, sha `ffc66c34…b190` unchanged (§8 table).

## 9. Dispositions

| Item | Disposition |
|---|---|
| Three source corrections plus the two-file order | patched (reviewed) |
| Rules-first creature reads (§6) | derived consequence, disclosed; the service is unchanged; the Owner sees it at acceptance |
| Other alphabetical parts | out of scope (deferred) |
| Pre-existing "Seventy" vs 71 miscount in the corrections doc | corrected in the candidate ("Seventy-two" matches the JSON); disclosed there |
| Heading located → inherited (p.337) | derived; disclosed |
| Old-release replay tests red | red by construction until the Owner records; pins not bumped |
| Derived coordinate and chunk-order pins (glossary `RULES_DEFINITIONS`, CCF `17`, Equipment `(120, 68)`) | patched pre-acceptance (confirmed against current source; the three tests pass) |
| Historical secrets-baseline entries the hook trims (12 values in 5 files) | pruned as authorized maintenance; 11 locations refreshed |
| Recording script | not written; added only after the Owner's exact semantic acceptance |

## 10. Scratch retention

`.claude/_rc/msc/` is kept, uncommitted. It holds the evidence that §3–6 cite:

- `rel/`;
- `old/`;
- `sim/`;
- `regen.log`;
- `cmp_*.py` and `cmp_*.txt`;
- `leafdelta.py`;
- `rebuild_old.py`;
- `probe_monsters_read.py` and `reads.json`;
- `simulate*.log`;
- `suite.log`;
- `mypy.log`.

Also kept, uncommitted, is the secrets evidence cited in §8:

- `.claude/_sp/msc/` (the scan copies);
- `msc_delta.json`;
- `msc_files.txt`;
- `mscrec/` (baseline before and after);
- `hook_rewrite_baseline.json` (its entries for the five touched files are now applied).

The temporary copies of the staged and HEAD baselines were deleted, because git can recover them.

All of this can be deleted once the Owner has decided. `.claude/_*` is never committed.

## 11. Next

1. Codex review.
2. The Owner's exact semantic acceptance of the 20-batch/1099-resolution replacement and of the Monsters packet with its 83 drafts, including the §6 consequence.
3. Only then, a recording script and the move of the live pins.
