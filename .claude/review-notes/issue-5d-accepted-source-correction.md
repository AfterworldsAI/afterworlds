# CRD Issue 5d — accepted-source correction (#132, #137)

Status: **corrections integrated into a corrected local build; replacement proposals prepared. Nothing accepted, recorded, published, activated or committed.**

Scope follows the Owner's latest direction (2026-09-24). It overrides the earlier preservation constraints:

- Continue the known-source correction, not a broader audit. Fix the known defects and add focused safeguards, then resume 5d. The broad error review is deferred until after 5d.
- Do not keep obsolete versions as history, legacy or documentation. Keep only actual current dependencies and useful regression fixtures, each with a named purpose. Remove a superseded copy only when no active code, replay or test needs it. Never remove a still-needed current oracle before a valid replacement exists.
- Existing acceptance allows a fresh proposal chain with no prior oracle. The cross-release check prevents extending the *old* chain; it does not prevent authoring a new proposal.
- A release rebuild is not, by itself, a new Owner contract decision. Generalized release succession or carry-forward is **not** approved and is not the goal.
- Nothing published or accepted is silently rewritten as accepted against a new binding.

Consolidated review packet: `issue-5d-source-correction-REPLACEMENT-PACKET.md`. Companion report: `issue-5d-accepted-source-recheck.md` (D1–D6).

## Result

| Defect | Accepted leaf | Legacy | Corrected (candidate) | Evidence | Record needing replacement approval |
|---|---|---|---|---|---|
| D1 relocated | [390] | p. 13 | **p. 14** | whole text printed once, on p14; `page14.png` | `play.combat.interacting` (review unit `combat-damage-breaking/combat`) |
| D2 relocated, straddle-certified | [412] | p. 15 (`anchored`) | **p. 14** | whole text printed once, on p14; `page14.png` | `play.combat.unseen_target`, `unseen_attacker`, `hidden_attacker` (same review unit) |
| D3 over-cite | [373] | pp. 12-13 | **p. 12** | whole text printed once, on p12 | `play.exploration.vehicles` (`core-play-completion/exploration`) |
| D3 over-cite | [391] | pp. 13-14 | **p. 13** | whole text printed once, on p13 | `play.combat.grid` |
| D3 over-cite | [425] | pp. 15-16 | **p. 15** | whole text printed once, on p15 | `play.combat.mounting` |
| D5 (new) | [271] | pp. 5-6 | **p. 6** | table geometry (p6, left column, 9 rows); `page6.png` | `play.six_abilities.ability_modifiers` (`core-play-completion/six_abilities`) |
| D6 (new) | [160] | pp. 84-85 | **p. 85** | whole text printed once, on p85 | `character_origins.elf.elven_lineage` (`character-origins-feats/elf`) |
| D4 Travel Pace header | [368] | flattened thead | two-row thead (below) | `p12_Pace.png` | `play.exploration.travel_pace`: the span must be re-cut (below) |
| Equipment I and J | none accepted | Food table snaked; *Saddle* as a data row; no Vehicles caption | reviewed patch | `issue-5d-equipment-source-repair-PLAN.md` | none (the catalogue is not accepted) |

The three extra-page (D3) findings were each checked against the official PDF before correcting. Each leaf's whole compact text occurs exactly once in the official page stream, entirely on the corrected single page. The other 684 accepted leaves keep their legacy pages under the corrected instrument.

## Implementation (uncommitted, working tree)

- **Source.** Both reviewed patches are applied:
  - `playing-the-game.md`: Travel Pace two-row header, family K. sha `7110c6ed…de76`.
  - `equipment.md`: Food group labels and printed-order list, the *Saddle* group row and the vehicles caption, families I and J. sha `ba4d96bf…645b`.

  Updated with them through the existing mechanisms: `source_pin.json` (25 corrections across 7 files; 1,892,657 controlled bytes), `PINNED-SOURCE.md`, the corrections record (new families I–K), `scripts/regen_community_source_coverage.py` and the regenerated coverage JSON.
- **`source_citations.py`.** `cite_units` has one path: the whole-text, bound-limited instrument described under Result. The earlier window-only path and the `unit_scoped` flag are **removed**, not retained to reproduce old identifiers. `CitationReport` counts all five outcomes (`located`, `placed`, `anchored`, `inherited`, `unresolved`). Its payload's `statuses_are` says a status names the mechanism, "not a proof it is right".
- **`source_ledger.py`.** `SOURCE_TRANSFORM_VERSION` goes from 3 to 4, and `citation_instrument` describes the new instrument.
- **`report.py`.** `EVIDENCE_REPORT_SCHEMA_VERSION` goes from `5c-evidence-4` to `5c-evidence-5`, because of the new payload keys. Publication readiness requires the current version, so a `5c-evidence-4` report is now refused. Only the superseded release carries one.
- **Tests.**
  - `test_source_units.py`: the defect and preservation cases now run on the default path. The "default is unchanged" case is removed. A new test checks that the report's counts equal the per-status tally and sum to the units.
  - `test_source_lifecycle.py`: the mapping assertion sums all four mapped statuses.
  - `test_community_source_structure.py`: four new cases pin the corrected Food, Saddle, vehicles-caption and Travel Pace structures.
- **Generators.** Only the literals that must match the corrected leaves changed:
  - `issue-5d-core-play-completion-generator.py` (tracked): `TRAVEL_PACE_TABLE`.
  - `issue-5d-equipment-generator.py` (untracked): `TACK_TABLE`, `VEHICLES_TABLE`, `FOOD_DRINK_AND_LODGING_TABLE` and the docstring that called those renderings "kept as released".
- **Identity record.** New `docs/architecture/issue-5c-5d-clean-restart.md` §8.11. Closed entries are not edited.

## Corrected build and replacement proposals

The corrected release `0b1a965e-28bd-55e6-ac13-bc7786a1bace` / `5.2.1-corpus.626c83f8-209` was built with `finalize_source_release`. It went only into the private scratch store `.claude/_rc/newrel/`, mirroring `tests/ingestion/conftest.py::source_release_db`. Citations: located 9,016, placed 22, anchored 83, inherited 1,344; 0 unresolved; 0 uncited body pages.

**Accepted leaves (691).**

- 0 missing and 0 occurrence changes.
- 1 content change: Travel Pace, 613 → 593 characters.
- 7 page changes, as in the Result table (D1–D3, D5, D6).

**Regenerated through the native seam.** All twelve accepted batches and Equipment were regenerated, and each re-derives its proposal identity.

- Eleven accepted batches differ only in derived identity: the five release-binding fields and the re-minted chunk IDs.
- core-play-completion also differs by the Travel Pace span re-cut (0–613 → 0–593, span `3a63e968…` → `b2b517d6…`).
- Equipment's records, components and references are identical. Only its three corrected tables change span length. 80 positional leaf IDs re-mint after the Food table; none is accepted.
- Resolution drafts: the 6 recorded resolutions differ only in `release_binding`; Equipment's 43 drafts are re-bound.

Exact identities and hashes are in the packet, `issue-5d-source-correction-REPLACEMENT-PACKET.md`.

**In-memory composition.** `issue-5d-source-correction-REPLACEMENT-ACCEPT.py --simulate` composes the twelve REGEN proposals and the six resolutions through `accept_proposal` and `resolve_references`. It runs under a marked simulated reviewer and writes nothing.

- Result: 136 records, 1,016 spans, 136 review units, 6 resolutions.
- Findings: 9,443 uncovered leaves and 91 references.
- Catalogue order and GameMaster source order: intact.
- Travel Pace heading association: correct.

The results are in packet §4. Equipment is not part of the replacement and stays unaccepted.

## Verification evidence

- **Whole-corpus sweep of the citation seam.**
  - Unit-scoped and legacy output were compared over all 10,465 units: 57 units change pages (Appendix).
  - 40 of the changes are units whose whole text is printed once.
  - 16 are order-resolved or token-placed. Each was checked: the text is absent from every legacy page it drops, and present on the new page, at the top or bottom as a carry-over would be (`.claude/_rc/contain4.py`).
  - D5 was checked by geometry and render.
  - No change moves a unit more than one page outside its legacy pages.
- **Change families found.**
  - Relocation: D1, D2, and the rogue, ranger and warlock features.
  - A page dropped: 33 units in all, namely D3, D6, D5 (placed) and 28 others (Appendix). Of the 57 changes, 19 move to another page and 5 add a page.
  - Under-cite, where the text really crosses a page the legacy partition missed: units 1845, 1924, 2047, 2250 and 8993. None is accepted.
  - A stat block's carried-over head on the next page: dragon and animal stat blocks.
- **Bounded siblings.** The corrections doc's family 5 is "a block attributed to the neighbouring page's span, pp.14/15, 275/277, 293/295":
  - pp. 14/15 are D1 and D2;
  - pp. 275/277 are units 5027 (p. 276) and 5057 (p. 277);
  - pp. 293/295 are units 5628 (p. 294), 5629 (p. 294) and 5664 (p. 295).

  Far-repeated text is not relocated: unit 2350 stays on p. 92, and the pairs 9296/10199 and 9833/10318 each stay on their own printing.
- **Not corrected (fallback path, reported as uncertified).**
  - Units 2968, 6208, 6836 and 7403 are repeated text printed on both of their cited pages, so the bounds cannot separate them. They stay multi-page with status `inherited`. No accepted leaf is among them.
  - Units 862, 1683 and 9902 are multi-page fallback units whose text really does cross the page, so they keep both pages.
- **Status redistribution.**

  | Scope | located | inherited | anchored | placed |
  |---|---|---|---|---|
  | All units | 9,017 | 1,345 | 81 | 22 |
  | Accepted leaves | 652 | 21 | 15 | 3 |

  These rows measure the instrument on the *unpatched* source. Legacy mode had counted most of the 1,345 as `anchored`: every unit shorter than a window, and the units certified only by a straddle.

  On the corrected build the counts are located 9,016, inherited 1,344, anchored 83 and placed 22. All four differences come from the patched tables:
  - Food moves from `inherited` to `anchored`.
  - Travel Pace moves from `located` to `anchored`. Its rebuilt header no longer matches the PDF extraction order, but its page is unchanged.
  - Tack stays `located` on p. 100, and the vehicles table stays `located` on p. 101.

## Gates (final working tree, nothing committed)

| Gate | Result |
|---|---|
| Corpus/source (`tests/ingestion/corpus`, `tests/ingestion/source`, `tests/test_pinned_community_source.py`) | 274 passed, 117 skipped, rc 0. The skips are the pre-existing quarantined reconstruction (`tests/ingestion/conftest.py:144`). |
| Black, Ruff (changed files and generators) | clean |
| mypy strict (`src/`) | 235 files, no issues |
| Mechanical (`tests/ingestion/mechanical`) | **64 failed**, 3,718 passed, 14 skipped, rc 1, on the tree *before* the one-line `UNLIKE_CHUNKS` pin update (`.claude/_rc/gate_mechanical2.txt`). The pin update flips 1 test, which was rerun and passes, so the final tree is expected to show 63 failures. The full suite was **not** rerun after the pin edit. Classified below. |
| detect-secrets | **blocked**. 221 Hex High Entropy additions, 13 moved, 0 removed, across 16 files. 219 are in the 15 REGEN/DRAFT files. 2 are in `source_pin.json` (L174, L335), both sha1 of the new file digests. The baseline is untouched (`.claude/_rc/secrets_delta.txt`, sha `c84f8bfb…1845`), awaiting Owner terminal handling. |
| pip-audit | not run. Deferred and non-green (31/11). |

**Mechanical failures, by cause.** The buckets are disjoint by test ID and sum to 64. None is a regression in what the tree builds. Every failure either replays the old authority against a tree that now builds `626c83f8-209`, or pins a derived identity.

| Bucket (tests) | Count | Mechanism |
|---|---:|---|
| `test_the_committed_bytes_are_what_the_published_release_derives`, `test_the_published_release_still_derives_the_accepted_bytes` | 18 | committed old proposal or oracle bytes ≠ bytes derived from the new build |
| `test_publication_stays_blocked*` | 12 | the old oracle's snapshot is empty for the new package, e.g. (0, 0) == (9651, 9443); set-difference asserts |
| `test_composed_*` (composed-prior targets and coverage) | 10 | the prior's `ReleaseBinding` (883aabdf) ≠ the new build's; actions-pilot fails as a target-list mismatch |
| `test_*printed_order*` | 8 | 3 character-origins-feats acceptance catalogue cases and 1 character-creation-foundations acceptance case: `PersistedStateReconstructionError` (old oracle's leaves absent from the new ledger). 2 `test_the_accepted_components_read_in_printed_order`: `ReleaseBinding` mismatch. 2 `test_a_gamemaster_reads_every_component_in_printed_order`: derived `UNLIKE_CHUNKS`. The character-origins-feats pin was updated 6 → 7 and passes on rerun; Equipment's 63 → 68 is in the stale untracked test. |
| `test_emit_writes_only_what_its_gate_admits` (actions, movement, reference), movement `…disjoint_from_the_acceptance…`, reference `…combat_pointer…` ×2 | 6 | committed bytes or the old oracle's binding |
| `test_once_accepted_*_resolve_through_the_native_seam` | 4 | `AcceptanceError`, "binds a different 5c release than the prior": the cross-release check, working as intended |
| `test_source_release_readiness` ×2 | 2 | no oracle for the new package (`None`; `ABSENT` vs `UNRESOLVED`) |
| `test_breaking_objects_stays_separately_owned_and_the_title_unowned` | 1 | old oracle absent (0 == 3) |
| character-origins-feats `test_the_accepted_authority_gains_no_membership` | 1 | `PersistedStateReconstructionError` |
| Equipment `test_each_table…[FOOD…]`, `test_the_release_renderings_that_differ_from_the_pdf_are_kept_as_released` | 2 | the untracked stale test pins the old Food table (11 `<tr>`, now 21) and asserts the defect the correction removes |

The untracked `test_equipment_proposal.py` accounts for 6 of the 64, spread over the bucket rows above.

Those "old authority" tests are deliberately *not* rewritten against the new binding: the old oracle stays authority until a replacement exists. **Stop condition:** the branch cannot be green until the Owner records a new acceptance chain on `626c83f8-209`. That is structural, not a defect. No commit was made, because detect-secrets is blocked and the mechanical gate is red.

**Untracked Equipment artifacts and their dispositions.**

| File | Status |
|---|---|
| `issue-5d-equipment-PROPOSAL.json` | superseded by the REGEN; no dependency except the stale test |
| `issue-5d-equipment-REVIEW-PACKET.md` | superseded; no consumers (sole reference was this row); **removed** (was untracked, sha256 `92b9a1594fa3e64a1336e11f6806d91c57c1e3f90342f8a7e9c93cdf274d69dc`) |
| `issue-5d-equipment-source-repair-PLAN.md` | **kept**: the family I/J findings record cited under Result and Limits |
| `issue-5d-equipment-source-repair.diff` | kept only as the fixture that reproduces `equipment.md` sha `ba4d96bf…` |
| `tests/ingestion/mechanical/test_equipment_proposal.py` | stale until a replacement acceptance; then retarget it to the REGEN |

None was removed. Removing an untracked file is irreversible, and the preserve-scratch constraint applies.

## Architecture Notes

**Deviation.** The stated principle of `source_citations` ("a lookup, not a search … no second instrument") is replaced. Citation is now a whole-text search bounded by the partition's kept anchors, and the module docstring says so.

This is an engineering algorithm choice under the Owner's direction, not an Owner decision. It is surfaced because the documented principle changes. No Known Unknown was touched. Release succession or carry-forward is **not** implemented. The corrected build is used only to prepare proposals, and the old oracle is untouched.

## Limits

- **Fact values were not re-reviewed.** Only source representation and provenance were checked, not whether each fact's value is semantically accurate.
- **Correctness is established only for what was checked:** the 57 changed units and the named cases. It is not claimed for:
  - the 1,426 fallback (inherited or anchored) units as a whole;
  - the pages that the corrected instrument leaves unchanged.
- **Equipment findings come from the earlier reviewed plan.** They were not re-derived here. This work only reproduced the patched sha and the citations, and adapted the generator's three table literals.
- **The source structure is not re-derived.** Re-qualification of the patched source is limited to the pinned-source, structure and coverage checks under Gates. No broader audit was run.

## Appendix — page changes, corrected instrument vs superseded (pre-correction source)

| Unit | File | Accepted leaf | Legacy | Unit-scoped | Status | Evidence | Text (compact, first 40) |
|---|---|---|---|---|---|---|---|
| 121 | animals.md |  | pp. 346-347 | p. 347 | located | text absent from legacy page, present on new | `bite.meleeattackroll:+4,reach5ft.hit:6(1` |
| 205 | animals.md |  | pp. 348-349 | p. 349 | located | text absent from legacy page, present on new | `amphibious.thefrogcanbreatheairandwater.` |
| 286 | animals.md |  | pp. 350-351 | p. 351 | located | whole text printed once | `rend.meleeattackroll:+5,reach5ft.hit:5(1` |
| 570 | animals.md |  | pp. 357-358 | p. 358 | located | whole text printed once | `modsavemodsavemodsavestr433dex15+2+2con1` |
| 773 | animals.md |  | pp. 362-363 | p. 363 | located | whole text printed once | `swarm.theswarmcanoccupyanothercreature's` |
| 1072 | character-origins.md | [160] | pp. 84-85 | p. 85 | located | whole text printed once | `intelligence,wisdom,orcharismaisyourspel` |
| 1660 | classes.md |  | pp. 53-54 | p. 53 | located | whole text printed once | `yourblessedtouchcanhealwounds.youhaveapo` |
| 1755 | classes.md |  | p. 58 | p. 57 | located | whole text printed once | `youhavelearnedtochannelthemagicalessence` |
| 1756 | classes.md |  | p. 58 | p. 57 | located | whole text printed once | `spellslots.therangerfeaturestableshowsho` |
| 1839 | classes.md |  | pp. 61-62 | p. 61 | located | whole text printed once | `asarogue,yougainthefollowingclassfeature` |
| 1841 | classes.md |  | p. 62 | p. 61 | located | text absent from legacy page, present on new | `level1:expertise` |
| 1842 | classes.md |  | p. 62 | p. 61 | located | whole text printed once | `yougainexpertiseintwoofyourskillproficie` |
| 1843 | classes.md |  | p. 62 | p. 61 | located | whole text printed once | `atroguelevel6,yougainexpertiseintwomoreo` |
| 1844 | classes.md |  | p. 62 | p. 61 | located | text absent from legacy page, present on new | `level1:sneakattack` |
| 1845 | classes.md |  | p. 62 | pp. 61-62 | located | whole text printed once | `youknowhowtostrikesubtlyandexploitafoe's` |
| 1858 | classes.md |  | p. 62 | p. 63 | located | text absent from legacy page, present on new | `level4:abilityscoreimprovement` |
| 1859 | classes.md |  | pp. 62-63 | p. 63 | located | whole text printed once | `yougaintheabilityscoreimprovementfeat(se` |
| 1924 | classes.md |  | p. 64 | pp. 64-65 | located | whole text printed once | `spellslots.thesorcererfeaturestableshows` |
| 1925 | classes.md |  | pp. 64-65 | p. 65 | located | whole text printed once | `preparedspellsoflevel1+.youpreparethelis` |
| 2044 | classes.md |  | p. 71 | p. 70 | located | text absent from legacy page, present on new | `level1:eldritchinvocations` |
| 2045 | classes.md |  | p. 71 | p. 70 | located | whole text printed once | `youhaveunearthedeldritchinvocations,piec` |
| 2046 | classes.md |  | p. 71 | p. 70 | located | whole text printed once | `prerequisites.ifaninvocationhasaprerequi` |
| 2047 | classes.md |  | p. 71 | pp. 70-71 | located | whole text printed once | `replacingandgaininginvocations.whenevery` |
| 2230 | classes.md |  | pp. 77-78 | p. 77 | located | whole text printed once | `cantrips.youknowthreewizardcantripsofyou` |
| 2250 | classes.md |  | p. 78 | pp. 78-79 | located | whole text printed once | `yougainawizardsubclassofyourchoice.theev` |
| 2252 | classes.md |  | p. 78 | p. 79 | located | text absent from legacy page, present on new | `level4:abilityscoreimprovement` |
| 2253 | classes.md |  | pp. 78-79 | p. 79 | located | whole text printed once | `yougaintheabilityscoreimprovementfeat(se` |
| 3073 | magic-items.md |  | pp. 204-205 | p. 204 | located | whole text printed once | `unlessitsdescriptionnotesotherwise,arodc` |
| 4272 | magic-items.md |  | pp. 248-249 | p. 248 | located | whole text printed once | `thistalismanisamightysymbolofgoodness.af` |
| 4330 | magic-items.md |  | pp. 250-251 | p. 250 | located | whole text printed once | `thiswandhas7charges.whileholdingit,youca` |
| 4782 | monsters-A-Z.md |  | pp. 268-269 | p. 268 | located | whole text printed once | `sleepbreath.constitutionsavingthrow:dc18` |
| 4814 | monsters-A-Z.md |  | p. 269 | p. 270 | placed | text absent from legacy page, present on new | `amphibious.thedragoncanbreatheairandwate` |
| 4816 | monsters-A-Z.md |  | p. 269 | p. 270 | located | text absent from legacy page, present on new | `multiattack.thedragonmakestworendattacks` |
| 4817 | monsters-A-Z.md |  | pp. 269-270 | p. 270 | located | whole text printed once | `rend.meleeattackroll:+5,reach5ft.hit:8(1` |
| 5027 | monsters-A-Z.md |  | pp. 275-276 | p. 276 | located | text absent from legacy page, present on new | `rend.meleeattackroll:+4,reach5ft.hit:7(1` |
| 5057 | monsters-A-Z.md |  | pp. 276-277 | p. 277 | located | text absent from legacy page, present on new | `pounce.thedragonmovesuptohalfitsspeed,an` |
| 5529 | monsters-A-Z.md |  | p. 290 | p. 291 | placed | text absent from legacy page, present on new | `traits` |
| 5530 | monsters-A-Z.md |  | p. 290 | p. 291 | placed | text absent from legacy page, present on new | `amphibious.thedragoncanbreatheairandwate` |
| 5532 | monsters-A-Z.md |  | p. 290 | p. 291 | located | text absent from legacy page, present on new | `multiattack.thedragonmakestworendattacks` |
| 5533 | monsters-A-Z.md |  | pp. 290-291 | p. 291 | located | whole text printed once | `rend.meleeattackroll:+6,reach5ft.hit:9(1` |
| 5561 | monsters-A-Z.md |  | pp. 291-292 | p. 291 | located | whole text printed once | `weakeningbreath.strengthsavingthrow:dc21` |
| 5628 | monsters-A-Z.md |  | p. 293 | p. 294 | placed | text absent from legacy page, present on new | `multiattack.thedragonmakesthreerendattac` |
| 5629 | monsters-A-Z.md |  | pp. 293-294 | p. 294 | located | whole text printed once | `rend.meleeattackroll:+7,reach10ft.hit:11` |
| 5664 | monsters-A-Z.md |  | pp. 294-295 | p. 295 | located | whole text printed once | `mindinvasion.thedragonusesspellcastingto` |
| 5886 | monsters-A-Z.md |  | pp. 300-301 | p. 301 | located | whole text printed once | `modsavemodsavemodsavestr622dex17+3+3con1` |
| 6418 | monsters-A-Z.md |  | pp. 315-316 | p. 315 | located | whole text printed once | `divineaid(2/day).theplanetarcastscurewou` |
| 6525 | monsters-A-Z.md |  | pp. 318-319 | p. 319 | located | whole text printed once | `firebreath(recharge56).dexteritysavingth` |
| 6803 | monsters-A-Z.md |  | pp. 326-327 | p. 327 | located | whole text printed once | `legendaryactionuses:3.immediatelyafteran` |
| 7548 | playing-the-game.md | [271] | pp. 5-6 | p. 6 | placed | geometry + render (p6 L) | `abilitymodifiersscoremodifierscoremodifi` |
| 7702 | playing-the-game.md | [373] | pp. 12-13 | p. 12 | located | whole text printed once | `travelersinwagons,carriages,orotherlandv` |
| 7725 | playing-the-game.md | [390] | p. 13 | p. 14 | located | whole text printed once | `thegmmightrequireyoutouseanactionforanyo` |
| 7726 | playing-the-game.md | [391] | pp. 13-14 | p. 13 | located | whole text printed once | `playingonagridifyouplayusingasquaregrida` |
| 7755 | playing-the-game.md | [412] | p. 15 | p. 14 | located | whole text printed once | `unseenattackersandtargetswhenyoumakeanat` |
| 7778 | playing-the-game.md | [425] | pp. 15-16 | p. 15 | located | whole text printed once | `duringyourmove,youcanmountacreaturethati` |
| 8993 | spells.md |  | p. 125 | pp. 125-126 | located | whole text printed once | `onecreatureyoucanseewithinrangemustsucce` |
| 8995 | spells.md |  | pp. 125-126 | p. 126 | located | whole text printed once | `usingahigherlevelspellslot.yourconcentra` |
| 9141 | spells.md |  | pp. 130-131 | p. 130 | located | text absent from legacy page, present on new | `usingahigherlevelspellslot.usethespellsl` |
