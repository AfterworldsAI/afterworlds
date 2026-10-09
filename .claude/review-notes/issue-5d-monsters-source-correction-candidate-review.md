This review is at `.claude/review-notes/issue-5d-monsters-source-correction-candidate-review.md` in the repository; repository output is acceptable. **Correction:** an earlier version of this line said the task directory could not be written. That was a restriction asserted in a compaction summary, not a failed write, tool error or OS denial: no write to the task directory was attempted and no permission denial was recorded.

**Provenance correction (2026-09-27), before integration.** This candidate was corrected in place for residue the independent review found: the Young White Dragon correction was wrongly called Owner-directed; the coverage `qualification.remaining` still said the unsigned save was preserved; the cross-file order note called a deferral an open Owner question; and the `check.py` gate claim overstated its evidence. §1, §2, §3, §6 and §9 now say what is true. Integration is recorded separately in `issue-5d-monsters-corrections-integration-review.md`.

# Monsters source/order correction: candidate for review (UNACCEPTED)

CRD Issue 5c/5d (#132, #137). Branch `codex/5c-5d-clean-restart`, head `5ed0657`.

**Status: this is a candidate. Nothing is integrated.** No controlled source, pin, release, accepted oracle, test, commit, push or shared-DB write was changed.

- The earlier Monsters acceptance offer has been withdrawn, and no semantic approval exists.
- The existing 414-record Monsters proposal and its 82 drafts stay UNACCEPTED. The tables below describe how they would change.
- Current accepted oracle: `srd-5-2-1-corpus-574662e9-0ef.json`, SHA-256 `fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62`. It holds 1250 records, 20 batches and 1099 resolutions, and it is untouched.
- The secrets baseline changed only by the scoped three-entry addition for this review's `.diff`: `1d870e18…b555` → `16ce260c…d22b`, staged, uncommitted (§6).

The Owner decisions and official URLs come from `monsters-source-corrections-research.md` in the task directory.

## 1. What the candidate corrects

| # | Correction | Kind | Official evidence |
|---|---|---|---|
| 1 | Reading order: `monsters.md` (the general Monsters rules, official pp.254–257) now precedes `monsters-A-Z.md` (p.258 onward) | ingestion order | Pinned PDF: p.254 opens *Monsters … Stat Block Overview*, and p.258 opens *Monsters A–Z* |
| 2 | Succubus: `Initiative +3 (13)` moves from a standalone paragraph after CR back onto the AC line, before HP and Speed | fidelity (family M) | Pinned PDF p.331 prints `AC 15 Initiative +3 (13)` and then `HP 71 (13d8 + 13)` |
| 3 | `### Warrior Veteran` becomes `### Veteran Warrior` | **OWNER CORRECTION, not publisher text** (family N) | See below |
| 4 | Young White Dragon INT save `2` becomes `−2` (U+2212) | **OFFICIAL-SOURCE-BACKED CORRECTION, not publisher SRD text and not an Owner decision** (family N); proposed under the Owner-requested lookup, pending the Owner's exact acceptance | See below |

Evidence for correction 3 (Veteran Warrior):
- The PDF (p.337) and its contents both print *Warrior Veteran*.
- Deck of Illusions (`magic-items.md`) prints *Veteran Warrior* for the same creature.
- The Owner decided the canonical name is **Veteran Warrior**.

Evidence for correction 4 (Young White Dragon INT save):
- SRD 5.2.1 p.340 and the Basic Rules rendering (<https://www.dndbeyond.com/sources/dnd/br-2024/creature-stat-blocks>) both print `INT 6 −2 2`.
- The current official individual stat block (<https://www.dndbeyond.com/monsters/5195287-young-white-dragon>, MM p.328; same AC 17, HP 123, CR 6) prints the save as `−2`.
- The Owner asked for this value to be looked up; the Owner did not decide it. The correction is proposed on the official individual stat block's evidence and awaits the Owner's exact acceptance.
- **Errata checked first** (the Owner's source-error policy), on 2026-09-27: the D&D Beyond SRD page (<https://www.dndbeyond.com/srd>) lists no SRD 5.2/5.2.1 errata document (it gives v5.2.1 of May 1, 2025 and v5.2.0 of April 22, 2025, and says future errata may bring new SRD versions); the official Monster Manual (2025) errata v1.0 (<https://media.dndbeyond.com/compendium-images/errata/MM-25/MM-2025_v1.pdf>, linked from <https://www.dndbeyond.com/sources/dnd/sae/monster-manual>) has 23 entries and none for Young White Dragon, Succubus or Warrior Veteran.
- **No formal erratum is claimed.** None was found in those sources, which is not evidence that none exists. The disagreement between the official sources is recorded in the manifest `why`.

**Sibling scan (bounded).** I scanned the pinned files for siblings of each correction:

| Check | Result |
|---|---|
| `**AC**` lines in `monsters-A-Z.md` | 235, and exactly one lacked Initiative (the Succubus, L16747) |
| Standalone `**Initiative**` lines | exactly one (the Succubus, L16806) |
| Ability save triples (1410) | exactly one unsigned save (Young White Dragon INT) |
| `###` stat-block headings | 235, before and after |
| "Warrior Veteran" | appears once (monsters-A-Z) |
| "Veteran Warrior" | appears once (magic-items) |

No broader source cleanup was done.

## 2. Where the order correction belongs

**The order correction belongs in ingestion order, not in reader coordinates or a cosmetic sort.** Here is how the order flows:

1. `CORPUS_FILES` (`src/afterworlds/ingestion/corpus/source_units.py:56`) is iterated by `load_pinned_sources`.
2. That iteration fixes the `build_structure` file index.
3. The file index fixes each leaf's global `occurrence_index`.
4. `services/rules_authority/service.py:434` (`source_leaf_order`) orders direct-read passages by `(occurrence_index, char_start)`.

**The fix.** The live tuple was `("legal-information.md",) + CONTENT_FILES`, with `CONTENT_FILES` alphabetical, so `monsters-A-Z.md` sorted before `monsters.md`. The candidate replaces it with an explicit 14-file tuple that swaps only those two files. `CONTENT_FILES` itself (the comparison's file set) is unchanged.

**What this preserves.** Nothing downstream changes:
- The override, context, one-authority and reader behaviour all stay in place.
- `source_ledger.py` imports `CORPUS_FILES` by name, so it follows automatically.
- `SOURCE_TRANSFORM_VERSION` stays `"4"`, because the ordered file list and the bytes are already inputs to `transform_source_hash`, so the order change re-mints the release on its own.

**Deferred, not corrected:** the other files keep the alphabetical order. For example, `animals.md` comes first, which is not the official chapter order. Source-order fidelity is already settled; reordering the other files is deferred as outside this bounded Monsters scope. It is not an undecided Owner rule, and no broad reorder is made.

## 3. Exact files and hashes

Each candidate file is a copy under `.claude/_sp/msc/cand/<same path>`. The byte-exact unified diff of all eight is `.claude/review-notes/issue-5d-monsters-source-correction-candidate.diff` (SHA-256 `e6c5aec6033fde5f4d5a31546e034049e8282fcaf7b59352a2a0f2ede8b7360a`, 40961 bytes, LF; regenerated after the provenance correction, previously `2dbfd43b…63c5`, 34225 bytes). It was produced with `git diff --no-index`, so its `b/` paths point at the candidate copies. It is for reading and won't `git apply` as-is. For integration, the candidate copies are the source of truth.

| File | Live SHA-256 / bytes | Candidate SHA-256 / bytes |
|---|---|---|
| `docs/sources/community/dnd-5e-srd-markdown/monsters-A-Z.md` | `61dcfe5a4a6af3da5497ed8035088b44dc37ecd2e1b4f04c09913f887a75d3cc` / 517136 | `e6581e2a330cd900dacbc321d9cb9533362f3b81e3f4adef342baf1b1a4864c2` / 517138 |
| `docs/sources/community/dnd-5e-srd-markdown/source_pin.json` | `d224e4ea8c28e346359e5e1ebe66aeb7f216da94450b7277e5c62016e189cd35` / 27836 | `2a68c67af6fbed0bdadb88df990ae56e08fd98ab64b7a565295736e0545dde89` / 29635 |
| `docs/sources/community/dnd-5e-srd-markdown/PINNED-SOURCE.md` | `309e14e7109080a1b46c23df8b60cc6e912621115d4ef46638cc036bee3107ad` / 6426 | `ac1848c413d8a261e0cb7405a8d40ec50a74048eabe78d9b4c0e14f3709005d1` / 6751 |
| `src/afterworlds/ingestion/corpus/source_units.py` | `853351169b7c58947061ff4a5cd938185e797fb5cb4b9fd2b1d8f406d988e306` / 16670 | `279d870885259c22e6c03c9209c6fba0819db221d8835c5cb92e0bc4238dc076` / 17160 |
| `docs/architecture/issue-5c-5d-community-source-corrections.md` | `9f97af50f24110a418d6a0ecf401407110ea6c6db893de385ab453968a8fda01` / 26039 | `ab1f90cc853c9144c519f948b00d0961c4993ee3f879c0b88bca97e8537b4581` / 29261 |
| `docs/architecture/issue-5c-5d-community-source-coverage.json` | `1e0f271cb391e1fff113b23a2df8ba816c9b80c6f7912ae167723997986f81b4` / 77831 | `59fa21ccfa439cf8e825bc499cdc3c9d24be19cd46e71b3c5081946875507bfc` / 78396 |
| `scripts/regen_community_source_coverage.py` | `7bc21591566b1a9631be7a5653057c4a37f40efda5b6a3fca200f5c46df97c10` / 22089 | `73edc0060d02865b2f4777d5918fb12a067f89ef45410d2367d9ac0850b41a5e` / 22933 |
| `tests/ingestion/source/test_community_source_structure.py` | `3f60edefbcbe86c9af6d7d4ca069d96b796ed3b01f130b9aa2fce2adaa082fe2` / 30966 | `dd17ae8ecef3a18db6e324a2faa0d59de257bf4584efe783ea40e39316321d7c` / 30585 |

**What each file change does:**
- **`monsters-A-Z.md`**: three `replace_once` edits. The byte count goes up by 2 overall:
  - the Initiative text moves (−2 bytes net: the blank line and newline);
  - the heading is renamed (0);
  - the minus sign is added (+3 in UTF-8).
- **`source_pin.json`**:
  - three new correction entries (p.331; p.337, which carries `OWNER CORRECTION, not publisher text`; p.340, which carries `OFFICIAL-SOURCE-BACKED CORRECTION, not publisher SRD text and not an Owner decision` and the errata sources checked);
  - `corrections_applied` goes from 32 to 35;
  - `preserved_official_defects` becomes `[]`;
  - `controlled_vendored_bytes` goes from 1893027 to 1893029.
- **`PINNED-SOURCE.md`**: the pin table and prose are updated, and "not corrected" becomes "`preserved_official_defects` is empty".
- **`source_units.py`**: the explicit `CORPUS_FILES` tuple, a comment explaining that the tuple is the reading order, and the unused `CONTENT_FILES` import removed.
- **Corrections doc**:
  - family M (Succubus) is added;
  - family N is added: the Veteran Warrior Owner correction and the Young White Dragon official-source-backed correction, each with its own provenance;
  - a "Reading order across files" section is added;
  - "Preserved rather than corrected" is removed;
  - the sibling-audit rows and residue/number-order text are updated.
- **Coverage JSON**: regenerated by the candidate copy of the regen script over the candidate root (see §5).
- **Regen script**: one new contents disposition ("Warrior Veteran", required: without it the live script raises `KeyError`), the number-order note (3 → 4 exceptions, adding p.340, called official-source-backed), and `qualification.remaining`, which no longer says the unsigned save is preserved: it records the official-source disagreement and the correction.
- **Structure test**: the ability-row shape test now asserts **zero** exceptions and an empty `preserved_official_defects`.

**Scratch scripts** (in `.claude/_sp/msc/`):

| Script | Purpose | SHA-256 |
|---|---|---|
| `make_cand.py` | builds the candidate | `ab86eafc58295df07f25cab02e1a884593874edd44b3eff2378ebb89b3d157c1` |
| `delta.py` | in-memory old/new release delta; output `delta.json` `b0d02716…07a1` | `19ab8dc2fce52fcea5eaaca2f45442058475176ff770950b6d8ce4fccaf93572` |
| `regen_cov.py` | coverage regen over the candidate root | `5dd308297778a3b6380d90c9042c2537830c9fdb97c825504a98b96b3c893fef` |
| `check.py` | targeted check | `592d285c926bc68449d9cb96ba11f921cd10a2d473fc61b8173fbc9eda4d1551` |
| `mkdiff.py` | writes the unified diff | `0bd945e89447a0af1be03368b63afda55ee06acbdae30b6a6d1c07724197b38b` |

`make_cand.py` built the first candidate. The provenance-correction text edits were applied to the candidate copies directly afterwards, so `make_cand.py` still emits the superseded p.340 `why` and no longer reproduces the candidate byte for byte. The candidate copies and the hashes above are the source of truth.

`cand/tests/ingestion/source/conftest.py` and `cand/tests/test_pinned_community_source.py` are unmodified copies of the live files. The conftest supplies the structure test's `official_pages` fixture. The pinned-source test runs against the candidate root.

## 4. Order-aware release delta (in memory; no finalize, DB or Chroma)

`delta.py` builds both releases with `build_source_candidate`. The old build reproduces the oracle's `release_binding` exactly, which validates the method.

| Binding field | Current (oracle) | Candidate |
|---|---|---|
| package_uuid | `ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` | `67c81736-15fd-5e82-8523-e84922f0a7c6` |
| release_version | `5.2.1-corpus.574662e9-0ef` | `5.2.1-corpus.3fe24ff6-4e3` |
| transform_config_hash | `2a7feddf7910684b8427745b9f9ecd5f394382d00955ed7b98920c2e12c0e64d` | `648ac3dd3b68b160d573338ad3bf50fba6c4726d5141da2f7b0c86224928d947` |
| bundle_root_hash | `3da7b5b30e23647c219d1630b5c5051be02b5882d17f0cd13421af8c57754689` | `87d95278c3349a5162ae7475a788c3d047bfdef30f56a73db9d7c22e3fe7f760` |
| transform_source_hash | `b0152615f08582c2fc0933ca4bd71656cf6a98b29062995c6c0a06d537eb80e7` | `6bf7a21f03ef1891a2436c5b04da2b21261cd202cb3619aaec0f57feec5de10d` |
| ledger_hash | `b81580c17d6f14a7424325e4efb140914d2f238adf9abd13af3e92c35c11cb1b` | `67bd4a59f3012718903671ebb824551cea63ef3134a4e850d4115366edc77932` |
| reconciliation_hash | `e812dcaf32ee1d9b3eb6d5a0d4c2cddee5d180ca46bbb573907b6befb675f9cf` | `23c34466b98cb5bc0419a8ecdb8b68212645469c6fbb4aab01ef4b40176c9e8b` |
| authoritative_source_hash (PDF) | `8974902d…3d87` | unchanged |
| persisted_corpus_digest | `df64eb40…acb02` | **undetermined**: only an integration finalize can produce it |

**Leaves: 10465 → 10464.**

**Citation report:**
- located 9014 → 9014;
- placed 22 → 22;
- anchored 85 → 85;
- inherited 1344 → 1343;
- no unresolved units;
- 361 cited pages, before and after;
- no uncited body pages.

**Per file:**

| File | Leaves | page_index | occurrence_index | Other |
|---|---|---|---|---|
| legal-information … magic-items (9 files) | unchanged | unchanged | unchanged | no change |
| `monsters.md` | 116 = 116 | 10 → 9 | −3026 for all 116 | no id or content change |
| `monsters-A-Z.md` | 3026 → 3025 | 9 → 10 | +116 for 2566 leaves, +115 for 456 (those after the removed Succubus paragraph) | see below |
| playing-the-game, rules-glossary, spells | unchanged | unchanged | −1 (one fewer leaf ahead) | no other change |

Other changes in `monsters-A-Z.md`:
- 2 unchanged-content leaves get new `leaf_id`s: the units between the Succubus AC line and the removed paragraph, because their compact offsets shift.
- 456 `container_path` changes: the container ids after the Succubus are line-based and the line numbers shift by −2.
- No printed page changes.

**Content changes (exactly four units):**

| Unit | Before | After |
|---|---|---|
| Succubus AC line, p.331 | `ce4c8770…`, citation inherited | `e4aa472b-e407-5c13-a66f-0b8c1fc5433d`, now **located** |
| Succubus `**Initiative** +3 (13)` paragraph `31ad8913…` | inherited | **deleted** |
| Heading `1f867f09-43ec-5b36-ad7d-a5a1211944fd`, p.337 | "### Warrior Veteran", located | **same id**, "### Veteran Warrior", **inherited** p.337 (the PDF prints the other order, so the heading no longer locates) |
| Young White Dragon ability table `912f6912-4d97-53ac-9d0c-3df02983e9c7`, p.340 | located | **same id** (the minus sign is not a compacted character), content changed, still located |

**leaf_id sets.** 4 ids exist only in the old release and 3 only in the new one, all in `monsters-A-Z.md`. The old-only ids are the Succubus AC, the Initiative paragraph and the 2 shifted units. The new-only ids are the new AC and the 2 re-minted units.

**Monsters scope:**
- 3142 → 3141 leaves (3140 → 3139 authored leaves plus the 2 part headings);
- `rules_before_a_z` goes from false to **true**;
- 235 stat-block headings before and after;
- there are still **235 stat blocks**. The only changes to the scoped leaves are the three declared corrections and the one-leaf reduction.

**Accepted oracle.** All 5978 span `leaf_id`s are present in both builds, none is in either Monsters file, and none changes content or relative order. The accepted content is therefore affected only in **derived identity**: the release binding, package-minted chunk ids and occurrence indices.

## 5. Coverage record delta (candidate regen)

| Field | Live | Candidate |
|---|---|---|
| window matched | 1068390 | 1068429 |
| runs over floor | 57 | 58: one new p.337 run (`veteranwarrior…`, 108 chars). p.337 is quiet in the token pass (`on_a_page_the_token_pass_also_reports` stays 39), so it is a word-order difference, not missing content |
| `community_additions.files_with_runs_over_floor["monsters-A-Z.md"]` (snapshot-only text) | Succubus `…cr4(xp1,100;pb+2)initiative+3(13)traits…` (109) | the p.337 `veteranwarrior…` text (108); the Succubus snapshot-only text is gone |
| runs below floor / chars | 114 / 10168 | 111 / 9927 |
| quiet body pages | 289 | 288 |
| pages with residue | 71 | 72 (new p.340: PDF `2`, snapshot `-2`) |
| number-order pages read | 64 | 64 (p.331 now matches; p.340 added) |
| contents titles matching a heading | 477 | 476 (a "Warrior Veteran" disposition was added) |
| ability rows not in shape | 1 | 0 |
| corrections applied / monsters-A-Z | 32 / 3 | 35 / 6 |
| preserved official defects | 1 | 0 |

**Surfaced:** the live corrections doc says "Seventy" body pages with residue, but the live JSON records 71. That is a pre-existing off-by-one. The candidate text says "Seventy-two", which matches the candidate JSON, so it also corrects the old miscount. That fix is disclosed here, not silent.

## 6. Checks run on the candidate (targeted only; no full suites)

- **`check.py`: exit 0.**
  - Every vendored file's bytes match its candidate pin sha/bytes.
  - Upstream equality holds exactly when a file has no corrections.
  - `controlled_vendored_bytes` is 1893029.
  - 35 corrections: 8 Owner corrections, and exactly 1 (p.340) official-source-backed, whose `why` does not say "Owner direction"; `preserved_official_defects` is `[]`.
  - Exactly one Succubus `AC … Initiative` line and no standalone Initiative lines; all 235 AC lines carry Initiative.
  - One `### Veteran Warrior`, and no "Warrior Veteran" left in `monsters-A-Z.md`.
  - The Young White Dragon row reads `6 −2 −2`.
  - 235 `###` headings.
  - The `CORPUS_FILES` order is: legal first, `monsters.md` immediately before `monsters-A-Z.md`, the rest alphabetical.
- **Candidate structure test:** `pytest .claude/_sp/msc/cand/tests/ingestion/source/test_community_source_structure.py -q -p no:cacheprovider --no-cov` → **50 passed**, exit 0. It ran against the candidate root through its own `parents[3]`. After the provenance correction both candidate test files ran again together (`pytest .claude/_sp/msc/cand/tests -q -p no:cacheprovider --no-cov`): **105 passed**, exit 0.
- **`black --check` / `ruff check`.** *Correction:* the earlier claim here overstated the evidence. `check.py` had been reformatted by Black after a failed check with no final `--check`, and Ruff had covered only the three candidate `.py` files. After the provenance correction: `black --check` on `check.py`, `regen_cov.py` and the three candidate `.py` files, exit 0; `ruff check` on the same five found one E741 (`l` as a name) in `check.py`, fixed, then exit 0. `check.py` then ran with exit 0.
- **Unmodified live `tests/test_pinned_community_source.py`, copied into `cand/tests/`** so its `parents[1]` resolves to the candidate root: **55 passed**, exit 0. The claim that this file needs no edit is therefore tested, not assumed.
- **Not run:** `tests/ingestion/source/test_community_compare.py` and the other coverage-consistency tests against the candidate. The full suites were not run, as instructed.
- **detect-secrets:** the hook over this `.md` and the `.diff` flagged three Hex High Entropy strings in the `.diff`, at lines 56, 58 and 60. They are the `upstream_sha256` and old/new `sha256` context lines of `source_pin.json`. Two runs gave identical output. I handled it as the authorized scoped addition:
  - I ran `detect-secrets scan` (without `--baseline`) on a copy under `.claude/_sp/msc/probe/`.
  - I appended exactly those three entries to `.secrets.baseline` under `.claude\review-notes\issue-5d-monsters-source-correction-candidate.diff`: `hashed_secret` `0a58a4a5…40ab`, `274138f9…c4cb` and `ffb4a568…c878`. Nothing else changed.
  - The baseline went from `1d870e184324b076c71637943bb41314f6f4df22bd84bdad9fbcbe7b248bb555` to `16ce260c02e7bb83e02444adebbedb665917662b7b111884a3a44b4990c2d22b` (+23 lines) and is staged by name, as it was before.
  - The hook then ran twice with exit 0 both times.
  - No pragma or config change was used.
  - The `.diff` was regenerated after the provenance correction. `monsters-A-Z.md` is its first file and is unchanged, so the three flagged lines stay at 56, 58 and 60. The hook ran twice over the new `.diff`, exit 0 both times, and the baseline stayed `16ce260c…d22b`.

## 7. Consumers whose expectations change at integration

**The candidate does not change these files. They must be updated when the change is integrated.**

**Source-layer consumers (the candidate already carries the new version):**
- `tests/ingestion/source/test_community_source_structure.py`;
- the coverage JSON;
- the regen script.

`tests/test_pinned_community_source.py` needs no edit: its unmodified copy passed 55/55 against the candidate root (§6).

**Consumers pinned to the release (they fail until a replacement is recorded):**
- `src/afterworlds/ingestion/mechanical/oracles/README.md`;
- `tests/ingestion/mechanical/_replacement_chain.py`;
- tests in `tests/ingestion/mechanical/`:
  - `test_accepted_inputs`, `test_committed_accepted_authority`, `test_oracle`, `test_packaging`;
  - `test_source_release_readiness`, `test_character_creation_foundations_proposal`;
  - `test_character_origins_feats_acceptance` / `_proposal`, `test_classes_proposal`;
  - `test_equipment_acceptance` / `_proposal`, `test_spellcasting_acceptance`;
  - `test_spell_descriptions_proposal`, `test_gameplay_toolbox_proposal`;
  - `test_magic_items_proposal`, `test_monsters_proposal`;
- every review-notes batch PROPOSAL/ACCEPT artifact bound to `574662e9-0ef`.

**Historical document:** `docs/architecture/issue-5c-5d-clean-restart.md` holds historical correction counts and the old Young White Dragon wording. It is a historical record, so it is out of scope and not edited.

**Monsters proposal consumer (`tests/ingestion/mechanical/test_monsters_proposal.py`, untracked):**

| Location | Current expectation | Expected after integration |
|---|---|---|
| L196 | `(82, 79)` | `(83, 78)` (Deck of Illusions now resolves: 31 → 32 deck members) |
| L209 | "Veteran Warrior" in the unresolved set | removed |
| L222, L374, L382 | 3140 authored leaves | 3139 |
| L374 | `1099 + 82` | `1099 + 83` |
| L396 | `315 - 82` | `315 - 83` |
| Docstring L22–23 and `_read` L437–446 | assume "the release prints Monsters A-Z before the rules part" | inverts: the governing rules precede the creature's own text; the exact form comes from the production service at regeneration, not hand-edited |
| Succubus header literals | old form | the corrected AC/Initiative line |

**Monsters generator:**
- The key `monsters.warriors.warrior_veteran` becomes `monsters.warriors.veteran_warrior`. This is **the same record identity renamed, not a second authority and not an alias**.
- The Deck of Illusions draft then resolves to it.
- Surfaced items 1, 2, 3 and 11 in the Monsters review close.

## 8. Integration and replacement dependencies (required next steps)

A new release binding means the accepted chain cannot be extended. The cross-release `AcceptanceError` refuses it, and generalized carry-forward is **not** approved. The precedent is the spell-table Owner correction. `issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py` regenerated the 17 accepted batches and 51 resolutions over the corrected release, under one Owner approval. The Gameplay Toolbox and Magic Items `ACCEPT.py` scripts later extended that chain.

1. **Codex reviews this candidate independently.** This is the current step.
2. **Integration.** Apply the eight files as reviewed, then build and finalize the new release `5.2.1-corpus.3fe24ff6-4e3`. The finalize fixes `persisted_corpus_digest`.
3. **Fresh replacement chain.** Regenerate all 20 accepted batches and 1099 resolutions over the new release. The change to them is identity-only: same leaves, content and relative order. This needs its own Codex review and then an **Owner replacement approval and recording**, in a new `…-REPLACEMENT-ACCEPT.py` following the precedent.
4. **Release-pinned updates.** Update the tests and README listed in §7 to the recorded replacement bytes, including the `_replacement_chain.py` chain and `COMMITTED_SHA256`.
5. **Monsters.** Regenerate the Monsters proposal and drafts over the new release: expected 83 drafts, 3139 authored leaves, rules-first reading, and the `veteran_warrior` key. Then comes an exact regenerated packet, Codex review, and **Owner semantic acceptance**.

Nothing in steps 2–5 has been started.

## 9. Unresolved boundaries

- **Deferred, outside this bounded scope:** the cross-file reading order beyond Monsters. The other files stay alphabetical, which is not the official chapter order. This is not an undecided Owner rule.
- **Integration note:** `persisted_corpus_digest` for the candidate is known only after finalize.
- **Disclosed:** this candidate also corrects the pre-existing "Seventy" vs 71 miscount in the corrections doc.
- **Out of scope:** Animals; the broad accepted review; Casting Spells; shared coverage (after 5d).
