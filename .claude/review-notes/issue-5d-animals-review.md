# CRD Issue 5d — Animals packet (UNACCEPTED), for Codex review

This is the remaining **Animals** part of the Owner-authorized 5d clean restart. It is one coherent packet. The
proposal and drafts are **UNACCEPTED**. Nothing was recorded, committed, pushed, published or activated, and
there was no shared-DB or Chroma write. Partial publication stays blocked. This is not an all-green claim.

## Artifacts

| File | Role | SHA-256 |
|---|---|---|
| `issue-5d-animals-source.py` | 835 qualified leaves `(path, text)`, in printed order | — |
| `issue-5d-animals-generator.py` | the generator; reuses the accepted Monsters generator (`MG`) unchanged | — |
| `issue-5d-animals-PROPOSAL.json` | `5d-proposal-2`, identity `19685bc2…53cd` | `a3057b73…5ebb` |
| `issue-5d-animals-resolutions-DRAFTS.json` | 65 unrecorded resolution drafts | `924ef579…66ac` |
| `tests/ingestion/mechanical/test_animals_proposal.py` | new gate, 11 tests | — |

- **Composed over:** the recorded 21-batch oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json` (`02f3a11b…dc54`).
  - It holds 21 batches, 1664 records, 9589 spans, 1364 units, 1182 resolutions, and 317 references and 864
    uncovered leaves as findings.
  - Its bytes, identities, approvals, times and resolutions are unchanged. It was rehashed after the generator
    reruns.
- **Release:** `67c81736-…` / `5.2.1-corpus.3fe24ff6-4e3`.
- **Generator runs:** on a copy of `.claude/_rc/msc/rel/afterworlds.db`. Two runs, the second after Black/Ruff,
  both exit 0, with byte-identical artifacts. The scratch DB was unchanged (`ffeb731f…17e0`).
- **Root DB:** `afterworlds.db` is unchanged (`7a3a1814…dc2e`).

## Scoped qualification (official pinned PDF, pp343–364)

| Check | Result |
|---|---|
| Leaves below `# Animals` | 835, occurrences 6–840, pp344–364. The part heading itself (occurrence 5) is left to shared coverage. |
| Leaves qualified against the PDF | 836 (including the heading): 741 prose ok, 95 tables; 0 failures |
| Tables | 95 ability tables. 285/285 rows match. MOD/SAVE columns are preserved (3 MOD + 3 SAVE per table). |
| Printed order | 0 breaks in column and flow modes, cursor anchored at `# Animals`. Full-page mode, which reads across both columns, reports 839 breaks. That mode was not compared line by line with the Monsters log (`_sp/mon/order.log` reports 70 column-mode breaks, so it is not the same pattern), and it is not relied on. |
| Arithmetic consistency | HP and damage averages, initiative score vs DEX, passive Perception vs the Perception skill: 95 blocks, 0 flags |
| Containers | Traits 116, Actions 224, Bonus Actions 16, Reactions 4 (leaf counts). Each is its own `###` heading. No Legendary Actions. |
| Headings and variants | 95 `##` stat blocks directly under the part, with no group headings. Each type line matches `MG.TYPE_LINE`. No duplicate leaf within a block. |

**Source errors:** none found. No errata or DDB escalation was needed, and there is nothing to notify under
`source-error-policy.md`.

## Authority identification (before authoring)

- **No collision:** no accepted record or component, whether a Monsters stat block, a Spell creature or an Item
  creature, has an Animals name or slug. `set(MG.BLOCK_KEY) & NAMES` is empty, and `current()` asserts that no
  `animals.*` record exists.
- **Animals is a section of Monsters in the source's own words:**
  - *Wild Shape*: `see "Animals" in "Monsters"`.
  - *Polymorph*: `See the "Animals" section of "Monsters"`.

  So Magic Items saying a stat block "is in Monsters" is consistent, with no source error and no Owner decision.
  It also means the accepted *Parts of a Stat Block* rules govern an Animals stat block exactly as they govern a
  Monsters A–Z one.

## Native composition

- **Grain:** 95 `creature` records `animals.<block>`. Each has one PROSE_BOUND component for its own leaves, then
  one per printed container.
  - Totals: 253 components, 835 spans and 95 review units (ENTRY).
  - Typed contracts are unchanged, and no schema was added.
- **Latitude:** only the *Swarm of Insects* names the GM: `Climb or Fly 20 ft. (GM's choice)`.
  - It is recorded as `NOT_LATITUDE`, a choice among printed options, following the accepted Half-Dragon
    precedent.
  - Every other component is asserted free of `MG.DELEGATING`.
  - Every component carries `no_identified_structured_use`.
- **References:** precise only, using `MG.creature_refs` unchanged.
  - The accepted Rules Glossary terms, plus the *Giant Owl* Actions' italic spells: Detect Evil and Good, Detect
    Magic and Clairvoyance.
  - There are no bold creature references and no quoted pointers.
  - The Giant Owl is the only caster (`CASTING == NAMING`).
- **Governing rules, read in place:** each component reads, `CONTEXTUAL`, exactly the spans that
  `MG.header_context` / `MG.part_context` select for the same printed text. These are spans of the accepted
  `monsters.parts_of_a_stat_block`.
  - Mechanism: `read_accepted` once per reader, over the accepted representation cut to that reader's span ids.
    The rules therefore stay `PRIMARY` on their accepted owner.
  - Scale: 1133 reads, and `bindings = 835 own + 1133 read = 1968`.
- **Batch findings:** these equal `expected_representation_findings` exactly.
  - partition 0 and review_units 0;
  - representation 3757, which is 358 out-of-batch reference targets plus 3 × 1133 accepted-read findings.

  Each is shown to close in the composition test below.

### Drafts (native `ReferenceResolution`, scope = the reference's own)

- **65 drafts:**
  - 58 MONSTERS-scope exact Animals names, from Bag of Tricks, Wand of Wonder, Find Familiar, Figurine of
    Wondrous Power (including `silver_raven`), Hat of Many Spells, Staff of the Python, Cloak of the Bat, Pipes
    of the Sewers, Robe of Useful Items, Phantom Steed and Pact of the Chain;
  - 4 ANIMALS-scope (*Wild Shape*): Rat, Riding Horse, Spider, Wolf;
  - 3 reviewed plurals, each to the stat block its source names: `2 **Giant Wasps** (100 XP each)` →
    `animals.giant_wasp`, `6 **Giant Rats** (25 XP each)` → `animals.giant_rat`, and the Robe of Useful Items
    row `84–90 | 2 Mastiffs` → `animals.mastiff`.
- **19 left unresolved**, as printed: the chapter pointers "Animals" ×2 (Wild Shape, Polymorph) and "Monsters"
  ×17. There is no broad-section fallback.

## Consumer (production `RulesAuthorityService`, one persisted draft on a tmp copy)

- **Direct read:** an animal reads each printed container's own text, then the governing rules not yet read.
  - Checked for Wolf, Giant Owl and Swarm of Insects.
  - Each own leaf appears once, in printed order.
  - Each governing passage is the accepted rules span itself.
- **Disclosed ordering:** this is the reverse of Monsters, which reads the rules first. The consumer orders a
  component's passages by leaf occurrence, and the release prints *Animals* (occurrences 5–840) before the
  Monsters rules. This is a derived consequence of release order, not a choice made here.
- **Spellcasting:** only the Giant Owl reads the spellcasting rules. The Wolf does not.
- **Suppression:**
  - disabling `parts_of_a_stat_block/hit_points` or `/running_a_monster` removes exactly that text from the Wolf;
  - a REPLACE override of `hit_points` removes the printed rule and leaves every other passage in order. What
    the reader shows in its place (the house text or nothing) is **not pinned**.
- **Combined dedup:** PARTS + Wolf, Wolf + Giant Owl, and Aboleth + Wolf each read Hit Points, Alignment and
  Running a Monster once, and every span once.

## In-memory composition (test-only; no oracle write)

- Accept, then resolve the 65 drafts, over `current()`.
- `_preserved` is empty (append-only), and the first 21 batches are identical.
- **Totals:**
  - records 1664+95
  - spans 9589+835
  - units 1364+95
  - resolutions 1182+65
- **Findings:**
  - reference-resolution violations: 0;
  - uncovered leaves fall by exactly 835, with none new;
  - the remaining findings are exactly the prior 317 unresolved references less the 65 drafted, which is 252;
  - the oracle directory's bytes are unchanged.

## Gates (raw)

| Gate | Result | Exit |
|---|---|---|
| `test_animals_proposal.py` (pre-format) | 11 passed, 276.47s | 0 |
| `test_animals_proposal.py` + `test_monsters_proposal.py` (final bytes) | 25 passed, 678.44s | 0 |
| Black `--check` (generator, source, test) | clean after reformatting 2 files | 0 |
| Ruff (same) | clean after removing an unused `re` import and wrapping 2 lines (Black) | 0 |
| mypy `src/` | no issues, 235 files (no `src/` change) | 0 |
| mypy on the new test | `import-untyped` noise, the same as the existing sibling tests; expanded mypy is deferred and non-green | 1 |
| `detect-secrets-hook` ×2 (6 files: generator, source, PROPOSAL, DRAFTS, test, recorded-followup) | stable at `e7580932…d3ff` | 0, 0 |
| `detect-secrets-hook` ×2 (the same 6 files plus this review) | stable at `e7580932…d3ff` | 0, 0 |
| pip-audit | deferred, non-green | — |

### Scanner maintenance (scoped `.secrets.baseline` delta)

- **From → to:** `81e2f7a7…ef4d` → `e7580932…d3ff`.
- **Delta:** 14 added, 0 pruned, 0 line-refreshed. Entries went from 5504 to 5518 and files from 113 to 117.
  Settings, filters, other files' entries, key order and `is_verified` flags are preserved.
- **Evidence:** every added value was recovered from its line and verified as a named public hash
  (`.claude/_sp/ani/verify.json`):
  - `CURRENT_SHA256`, the recorded oracle file's SHA-256;
  - `IDENTITY`, `PROPOSAL_SHA256` and `DRAFTS_SHA256`, recomputed from this packet;
  - `authoritative_source_hash`, `hash` and `semantic_policy_hash`, printed at HEAD in tracked files;
  - `bundle_root_hash`, `persisted_corpus_digest` and `transform_config_hash`, the recorded oracle's release
    binding, already baselined in 30 files.
- **Process:** no `pragma: allowlist secret` was added, and there was no `scan --baseline`. `.secrets.baseline`
  is staged by name, as the hook requires. There was no new denial.

## Recorded-followup correction

`issue-5d-monsters-corrections-recorded-followup.md` was corrected in two places.

- **Retention:**
  - `msc/rel/afterworlds.db` serves the existing `REPLACEMENT._findings` verifier/simulation seam, which only the
    ACCEPT `--verify`/replay paths call. The live tests rebuild native fixtures from `source_release_db`.
  - It is retained while replay needs it. This is no new product decision and no broad retirement.
  - The 574662e9 oracle's current purpose was determined and recorded, with no cleanup: directory-listing tests,
    the REPLACEMENT's refused `ACCEPTED_PATH`, and the historical REGEN/ACCEPT replays. Retiring it still needs
    Owner authorization.
- **Gates:** the table now records that the parent separately closed the missing final Monsters-generator hook:
  two exit-0 runs, stable at `81e2f7a7…ef4d`.

## Concrete unresolved boundaries

1. **19 chapter pointers** ("Animals" ×2, "Monsters" ×17) stay unresolved. There is no record-level target, and
   broad-section fallback is prohibited. Partial publication stays blocked.
2. **The `# Animals` part heading** (1 leaf) is left to the deferred shared-coverage pass, with the other part
   headings.
3. **Deferred and non-green:** pip-audit and expanded mypy.
4. Broad accepted review, Casting Spells and shared coverage come after 5d.

## Process disclosures

- **`cd` in Bash, twice, in earlier sessions of this run.** Both were harmless:
  - one Bash call began `cd /d/AI/Claude/afterworlds 2>/dev/null;`;
  - the `refs.py` run used `cd $cd_ && …`.

  A later `cd_=x;` was a variable assignment, not a `cd`.
- **Bare `python` for patch scripts.** Some Bash text-patching of scratch scripts and the new test ran bare
  `python` from PATH, not the explicit venv. No gate, generator or scan ran under it.
- **Staging:** `.secrets.baseline` was staged by name because the hook requires it. Nothing else was staged.
- **Nothing committed, pushed or published:** no activation, no shared-DB or Chroma write, no `git gc`/`prune`,
  no `--no-verify`. No task-dir permissions were probed.
- **Left untouched:** the quarantined 36b786d8 oracle, the protected REPLACEMENT-PACKET, the 574662e9 oracle, the
  4 stashes and the pre-existing staged deletions.
- **Connectors:** Context7, Expedia, Google Calendar, Intuit TurboTax and Shopify need authorization in claude.ai
  connector settings. They were not used.

## Sources

- https://www.dndbeyond.com/srd
- https://media.dndbeyond.com/compendium-images/errata/MM-25/MM-2025_v1.pdf
- https://www.dndbeyond.com/sources/dnd/sae/monster-manual
- https://www.dndbeyond.com/posts/1950-sage-advice-and-errata-for-the-new-core-rules-is
