# CRD Issue 5d — Equipment cited-targets packet (UNACCEPTED)

#132, #137. **Review packet only: nothing here is accepted, recorded,
published or activated, and no Owner approval exists for it.** The recorded
oracle `srd-5-2-1-corpus-3fe24ff6-4e3.json`
(`4ad85dab4ec9e5967779a0bb24f22c099e0aafdc9762088e340f7796b86290ba`; 22
batches, 1759 records, 10424 spans, 1459 units, 1247 resolutions; 252
reference findings, 29 uncovered leaves) is byte-unchanged.

_Status: complete, **UNACCEPTED**. Revised after consolidated independent
review (below); for independent review, then one consolidated Owner
acceptance offer. Nothing committed, pushed, recorded, published or
activated._

## Revision after consolidated review

Settled corrections; none needed a new Owner decision:

1. **Falling Net's qualified pointer.** `see "Adventuring Gear" for the Net's
   statistics` names the Net, so its draft now targets
   `equipment.adventuring_gear.net`, not the section. The earlier section
   draft repeated the mapping the review had rejected. Same-family check
   (only this packet's qualified targets): among the in-scope strings,
   "Adventuring Gear" is the only one that is a section title, so this is the
   only instance and it is **patched**. Every other draft names an item by
   its own name, plural or inverted alias (**already safe**). The 15 bare
   "Equipment" pointers are **out of scope**.
2. **Wand (2 refs: `monsters.mages.archmage`, `monsters.mages.mage`)** now
   resolves under the existing ADR-005d named-row authority (Decisions 3, 7,
   9). Official PDF p96 prints the Wand row (1 lb., 10 GP) in the Arcane
   Focuses table under the Arcane Focus rule. It uses no new edge, schema or
   component kind, and no second authority. The shape:
   - A peer `equipment.adventuring_gear.wand` record (`catalogue_member` →
     section) owns the row PRIMARY and reads, CONTEXTUAL, the Arcane Focus
     heading, its rule and the Arcane Focuses table head (`WAND_CONTEXT`).
   - `arcane_focus` still reads its whole entry in printed order, with the
     Wand row CONTEXTUAL. This uses the existing `EntryComponent.context`
     seam: a clause that prints a peer's named row reads it as context.
   - Wand is the table's last row. Wand owns **only its 81-char row**
     PRIMARY (`[488,569)` of the Arcane Focuses leaf). The table's 19-char
     close (`  </tbody>\n</table>`, `[569,588)`) is **Arcane Focus's
     PRIMARY**: the close belongs to the containing table, not to the
     removable Wand item. As with Pistol and Longsword, the Wand's direct
     read (`WAND_CONTEXT` + row) carries no table close.
   - **Correction of the previous round.** That round coupled row and
     close into one 100-char Wand span, claiming the close could not be
     located alone. That claim was false. The close prints five times
     among the gear leaves, but native `proposal.locate_span` accepts any
     unique containing anchor. Only `authoring.py`'s wrapper exposed cell
     anchors alone. The fix is bounded plumbing in that shared helper: a
     new `EntryBatch.anchors` field maps `(entry, text)` to a containing
     text the entry prints exactly once. It defaults to empty, so existing
     callers are unchanged. A text given both a cell anchor and an explicit
     anchor raises. Uniqueness and containment stay `locate_span`'s
     fail-closed checks. There are no offsets and no source rewrite. The
     generator anchors the close with the unique Wand row + close
     (`ANCHORS`, `ARCANE_FOCUSES_CLOSE`).
   - Consequence fixed: disabling or replacing Wand now removes only the
     Wand row. Arcane Focus keeps its rule, table head, other rows and the
     table's close.
3. **Spellbook stays unresolved.** Equipment prints no Spellbook item. The
   Wizard's Spellcasting feature justifies neither a generic-Book fallback
   nor moving the citation's scope.
4. **DELTA coordinate.** The printed-order key in `REPLACEMENT.py`
   (`_texts`, used by `coverage()` and `report()`) was the storage `row_id`;
   it is now the ledger's `occurrence_index`. The 70793-char / interval-union
   check the source reviewer ran in `occurrence_index` order is reused. The
   script now also **asserts** that the text is identical; before, it only
   printed the comparison.

Pre-revision artifacts are kept for comparison in local-only scratch,
never committed (`.claude/_sp/eqc/*-before-wand.*`, and
`*-before-close.*` for this round). Measured against them (`diff_wand.py`), the PROPOSAL
changes only as follows:

- +1 record, +1 component, +1 `catalogue_member` edge;
- `arcane_focus`'s one table span 4b314c4b is split into head, rows and
  Wand row, then (this round) the table close as its own span
  (466 → 468 → 469 spans);
- the bindings and provenance for those spans, and the Adventuring Gear
  review unit's span ids.

The DRAFTS change only by the Net retarget and the 2 Wand drafts (159 → 161).

Measured against the pre-close snapshot (`diff_close.py`), this round
changes the PROPOSAL only as follows:

- spans 468 → 469: `8335c087` `[488,588)` is replaced by `d7e540cf`
  `[488,569)` (the Wand row) and `d4a04e40` `[569,588)` (the close);
- bindings −2 / +3, provenance −3 / +4:
  - Wand PRIMARY `d7e540cf`;
  - Arcane Focus CONTEXTUAL `d7e540cf` and PRIMARY `d4a04e40`;
  - the Wand `catalogue_member` edge's context span is `d7e540cf`;
- the Adventuring Gear review unit: one span id.

The DRAFTS are unchanged.

## Candidate artifacts

| Artifact | SHA-256 |
|---|---|
| `issue-5d-equipment-cited-targets-generator.py` (copied generator) | `1f4b7487365c80909338d7cb33c1a9a8d39214fb8485aaad764d19bb9abf944d` |
| `issue-5d-equipment-cited-targets-PROPOSAL.json` (469 spans; accepted 409) | `13271e035f76316a6f78cf90ccca1f68ec233738ce31a93c7303052bc5bb02e0` |
| — its `proposal_identity` | `309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680` |
| `issue-5d-equipment-cited-targets-resolutions-DRAFTS.json` (161 drafts, ids `…-equipment-cited-1`) | `bfbf5a7ac78fa96fd568148d26bd2690415a4add9196d8ca393ef7b4f0c139eb` |
| `issue-5d-equipment-cited-targets-REPLACEMENT.py` (in-memory chain + delta) | `41b9bb4fd49e18d616e61ea3e27093da3fabed06895fd6ca2f0fab094ff63201` |
| `issue-5d-equipment-cited-targets-DELTA.txt` (full-text delta, `--delta`) | `7109c48c6b0bec450e8d83742def7286619128992d8fd6733c77a5d51a827fb2` |
| `tests/ingestion/mechanical/test_equipment_cited_targets_candidate.py` (new) | `129352fa11f31e9a0ef1f6762b4dd7aae2cc2c143a0aecc7ee4d86627afd2150` |

The generator is re-run against the published release copy and reproduces
both PROPOSAL and DRAFTS byte-for-byte (the test's first case).

## Scope and why it is an accepted change

The parent inventory's 162 unresolved Equipment-scoped references that print
something other than "Equipment" (64 strings) were each read in their citing
span (`.claude/_sp/eqc/ctx.json`). 161 name an item or rule Equipment prints;
each is today a **row or clause owned by a section or named record**
(`equipment.weapons` / `armor` / `tools` / `adventuring_gear` /
`mounts_and_vehicles`), not a record of their own.

ADR-005d Decision 7 lets a citation of a named item resolve only to that
item's one record, never to its section; Decision 3/9 give a table-part
member its row PRIMARY. A new batch cannot take those spans (the accepted
Equipment batch owns them PRIMARY, and the acceptance module has no
supersession: `acceptance.py` "nothing supersedes an accepted claim"), and a
contextual-only record over a section-owned row would be a second authority
and an invented component. So closing them needs the **accepted Equipment
batch itself** to name these items — a candidate replacement of one accepted
batch, presented here for review, not applied.

### Expense, and what does not change

* One regenerated proposal: Equipment, from a copied generator whose `diff`
  against the accepted generator is the source-level delta.
* Actual invalidation, measured (`.claude/_sp/eqc/inval.py`): of the 21 other
  recorded proposals, only Magic Items reads any Equipment span, and those 4
  are Attunement prose that no row re-cut touches. **The other 21 proposal
  files are reused byte-identical, not regenerated.**
* No recorded resolution cites from a component this packet re-homes (the only
  recorded Equipment-sourced resolution is `equipment.magic_items` →
  `spells.identify`).
* Because there is no supersession, recording would need a fresh 22-batch chain
  over no prior (the class-spell-tables and monsters-corrections precedent),
  with every other batch's recorded rule, reviewer and time and every recorded
  resolution re-applied verbatim. Here that chain is composed **in memory
  only**, to prove the preservation and the delta.

## Dispositions (162)

| Disposition | Refs | Strings |
|---|---|---|
| Needs a named record (candidate Equipment change), then draft | 158 | see the record table below |
| Qualified pointer to a named record: `see "Adventuring Gear" for the Net's statistics` → `equipment.adventuring_gear.net` | 1 | Adventuring Gear |
| Named row of the Arcane Focuses table: peer record `equipment.adventuring_gear.wand`, then draft | 2 | Wand |
| Unresolved: SRD 5.2.1 Equipment prints no Spellbook item; the Wizard's Spellcasting feature does not make a generic Book one, nor move the citation's scope | 1 | Spellbook |

Aliases and plurals follow recorded precedent (`Daggers`→`dagger`,
`Pouches`→`pouch`, `Traveler's Clothes`→`clothes_travelers`): `Javelins`,
`Handaxes`, `Iron Spike`→`Spikes, Iron`, `Bullseye Lantern`→`Lantern,
Bullseye`, `Musical Instruments`→`Musical Instrument`, `Bolts` (Ammunition
row). No category, composite or form is collapsed into a different item.

The 15 bare "Equipment" pointers and every other finding partition stay out of
scope.

## The 67 new records

All under their section with a `catalogue_member` edge (member → section,
Decision 9). Kind is `equipment` unless marked `[general_rule]`.

| Section | New records |
|---|---|
| `equipment.weapons` (26) | greatclub, handaxe, javelin, mace, sickle, light_crossbow, battleaxe, flail, greataxe, greatsword, longsword, morningstar, pike, rapier, scimitar, shortsword, warhammer, hand_crossbow, heavy_crossbow, longbow, pistol; properties heavy, reach `[general_rule]`; masteries cleave, graze, push `[general_rule]` |
| `equipment.armor` (9) | leather_armor, studded_leather_armor, chain_shirt, breastplate, half_plate_armor, chain_mail, splint_armor, plate_armor; strength `[general_rule]` |
| `equipment.tools` (9) | alchemists_supplies, jewelers_tools, leatherworkers_tools, smiths_tools, tinkers_tools, weavers_tools, woodcarvers_tools, musical_instrument, poisoners_kit |
| `equipment.adventuring_gear` (21) | alchemists_fire, burglars_pack, caltrops, component_pouch, dungeoneers_pack, entertainers_pack, explorers_pack, grappling_hook, holy_water, lantern_bullseye, mirror, net, pole, priests_pack, rope, sack, scholars_pack, spikes_iron, torch; bolts (Ammunition table row); wand (Arcane Focuses table row) |
| `equipment.mounts_and_vehicles` (2) | keelboat, rowboat |

Each is built the way the accepted generator already builds its sibling of
the same shape, through the same maps; only the vehicle rows have no
accepted sibling:

* **Weapon row** (like `dagger`, `musket`): PRIMARY its own Weapons-table
  row; CONTEXTUAL the weapon rules, table head and its group row (`Martial
  Melee Weapons` is newly cut as a group row). Row cells cite the section's
  category / melee_or_ranged / property / mastery components.
* **Armor row** (like `padded_armor`, `hide_armor`, via `ROW_AFTER`): its
  row under the head and group (`Heavy Armor` newly cut), then
  `ARMOR_RULES` as printed.
* **Property / mastery / Strength clause** (like `finesse`, `nick`,
  `stealth`): the section clause moves to its own record; the new masteries
  read `mastery_properties` first, as `nick` does (`AROUND`).
* **Tool clause** (like `calligraphers_supplies`, `thieves_tools`, via
  `AROUND`): `TOOL_RULES`, `artisans_tools` for an artisan's tool, then its
  own clause.
* **Gear clause + rows** (like `pouch`, via `ROWS_OF` from `GEAR_ROWS`): its
  own clause and its Adventuring Gear row under the gear head. `bolts` is an
  Ammunition-table row like `arrows`.
* **Arcane Focuses row** (`wand`): as a named row (`NAMED_ROWS`) under
  `WAND_CONTEXT`; `arcane_focus` keeps it as context (revision 2 above).
* **Vehicle row** (new shape; flagged below): the Airborne and Waterborne
  Vehicles table is re-cut from one span into head + per-row pieces;
  keelboat / rowboat own their row and read the table's introduction, the
  Speed note (printed before the table), the head, then (`ROW_AFTER`) the
  notes the introduction says apply — crew, passengers, damage threshold,
  ship repair — in printed order.

### Generator delta (accepted → candidate)

`git diff --no-index issue-5d-equipment-generator.py
issue-5d-equipment-cited-targets-generator.py`: +2408 / −612, all semantic
(the accepted generator is already Black-clean). Beyond origin and file
names:

* `WEAPON_GROUPS` + Martial Melee; `WEAPON_ROWS` +21; `ARMOR_GROUPS` +
  Heavy; `ARMOR_ROWS` +8; `GEAR_ROWS` +19; `AMMUNITION_ROWS` + Bolts;
  `VEHICLES_HEAD` / `VEHICLE_ROWS` / `VEHICLES_PIECES` (table re-cut).
* `NAMED_CLAUSES` + heavy, reach, cleave, graze, push, armor strength and 9
  tools.
* `MARTIAL_MELEE`, `VEHICLE_CONTEXT`, `VEHICLE_NOTES` context tuples.
* `ARCANE_FOCUSES_HEAD` / `WAND_ROW` / `ARCANE_FOCUSES_PIECES`,
  `WAND_CONTEXT`; `_components` reads a peer's named row as context.
* `NAMED_ROWS` gains the new row entries; `ROW_AFTER` and `AROUND` gain the
  new keys (they print as moved because `NAMED_ROWS` grows above them).
* Appended `CITED_DRAFTS` (161 literal tuples), `CITED_UNRESOLVED`
  (Spellbook) and `draft_cited_resolutions`; `main` also writes the DRAFTS.

## Native composition and delta (in memory)

`REPLACEMENT.py` rebuilds the recorded chain over no prior: 22 batches, each
with its **recorded** rule, reviewer and `accepted_at` (read from the pinned
oracle's ledger), and every recorded resolution re-applied verbatim after its
batch. Only the Equipment batch takes the candidate proposal, under the
simulated reviewer; the 161 drafts then apply under the simulated reviewer.

| State | Batches | Records | Spans | Units | Resolutions | Findings (reference, uncovered) | Violations |
|---|---|---|---|---|---|---|---|
| Recorded oracle | 22 | 1759 | 10424 | 1459 | 1247 | 252, 29 | 0 |
| Replayed with candidate | 22 | 1826 | 10484 | 1459 | 1247 | — | 0 |
| + 161 cited drafts | 22 | 1826 | 10484 | 1459 | 1408 | 91, 29 | 0 |

252 − 161 = 91, as predicted; the 29 uncovered leaves are unchanged (tracked
only). Simulated final bytes:
`26e234804aa4ddf809fa66945b78c793f46d1d45492de2bf44c38ecdf2841eff`.

**Preservation (asserted; the script exits 0):**

* Every lost or added item in 16 payload collections (14 changed;
  `review_unit_records` and `lifts` are 0 / 0; acceptance evidence blanked) is attributed to Equipment by an owner field (record/semantic
  key, from-record, source record, target key, `batch_id`, Equipment span
  set, `-equipment-cited-1` resolution id, all-`equipment.*` review units):
  **0 non-Equipment items lost or added**.
* Equipment's accepted text in printed order (`occurrence_index`, then
  `char_start`) is identical before and after:
  70793 chars, SHA-256
  `b32b6e72fb2b22ba6300bb01de39a93d92e14f30bb2a3a9096df04925a1f62b3`. The
  re-cut spans partition the same characters; nothing is dropped or read
  twice.

**Delta by collection** (full text, order-aware, in `DELTA.txt`):

| Collection | Lost | Added | Meaning |
|---|---|---|---|
| spans | 18 | 78 | multi-row spans split into per-row spans (and the Arcane Focuses close) |
| review_units | 5 | 5 | the affected units re-cut to the new spans |
| obligations | 4 | 71 | section obligations shrink; one per new record |
| reference_resolutions | 0 | 161 | the drafts |
| records | 0 | 67 | 61 `equipment` + 6 `general_rule` |
| components | 34 | 67 | 19 gear, 9 tool, 5 weapon (cleave, graze, heavy, push, reach) and armor `strength` section components move to their own records; + `wand` |
| references | 40 | 173 | the 40 re-homed 1:1 (same text, target, scope); 133 new row-cell refs (weapons category / melee_or_ranged 21 each, armor class / category 8 each, properties, masteries, ammunition) |
| relationships | 0 | 67 | `catalogue_member`: weapons 26, gear 21, armor 9, tools 9, vehicles 2 |
| prose_bindings | 82 | 344 | per-record bindings |
| provenance | 124 | 586 | per-record PRIMARY / CONTEXTUAL |
| acceptance.batches | 1 | 1 | the Equipment batch's identity and diff |
| acceptance.records | 18 | 78 | follows spans |
| reference_resolution_records | 0 | 161 | the drafts |
| schema_anchors | 1 | 1 | follows the Equipment batch |

**Invalidation.** Only the Equipment proposal changes; the other 21 are
reused byte-identical (Magic Items' 4 Equipment reads are untouched
Attunement prose). No recorded resolution cites from a re-homed component.

## Consumer evidence (production `RulesAuthorityService`)

`tests/ingestion/mechanical/test_equipment_cited_targets_candidate.py` runs
over a private copy of the published release, with the candidate persisted
as a draft (`persist_draft`, `identify_projection`), reusing the accepted
Equipment test helpers. **18 passed in 105.66s.**

* The bytes, identity and drafts are what the release derives.
* The accepted named records stay, in order; 67 are added across 5
  sections.
* Per section (5): the section read slices every member once, in printed
  order; the primary sequence is the section's whole text; no span is read
  twice.
* Every new member's **direct read** gives its own passages once, in printed
  order; **section + member combined equals the section read** (dedup).
* Exact direct reads: longsword = `MARTIAL_MELEE` + row; chain_mail = head,
  Heavy group, row, `ARMOR_RULES`; keelboat as above; smiths_tools =
  `TOOL_RULES` + artisan's tools + own clause. The Greatclub, Longsword and
  Pistol rows are owned by their members in the section read.
* **Wand / Arcane Focus**:
  - wand's direct read is `WAND_CONTEXT` + its row;
  - arcane_focus's direct read is its whole entry in printed order (gear
    head and row, heading, rule, the Arcane Focuses head, rows, Wand
    row and the table close);
  - within the section, only `wand` owns the Wand row PRIMARY and only
    `arcane_focus` owns the table close PRIMARY (the weapons and armor
    sections print the same close text in their own tables);
  - section + arcane_focus + wand equals the section read, and
    arcane_focus + wand reads no span twice;
  - **regression for this round:** with wand disabled or replaced,
    arcane_focus's direct read is its whole read minus the Wand row
    only: it keeps the rule, the table head, the other rows and the
    table close. Its portion of the section read is unchanged and still
    ends the table with the close. So the override is suppressed where
    the row is context too, and the table stays closed.
* **Disable / replace in the section read** (longsword, heavy, chain_mail,
  rope, wand, smiths_tools, keelboat): when disabled, the section is otherwise whole and a direct read
  is `INVALID_REFERENCE`; when replaced, the authored text reads at the
  member's position and none of the member's source text remains.
* A component selector on a section reads no new member.

## Gates

| Gate | Result |
|---|---|
| Black (generator, REPLACEMENT.py, test, `authoring.py`) | pass |
| Ruff (same) | pass |
| Focused pytest (changed test file) | 18 passed |
| `REPLACEMENT.py --delta DELTA.txt` | exit 0 |
| Generator byte reproduction | identical |
| mypy `src/` (strict; `authoring.py` changed) | pass, 235 files |
| Dependent: every proposal's committed-bytes reproduction test (all `build_entry_batch` callers) | 20 passed (all 20 `*_proposal.py` byte tests), exit 0 |
| pip-audit, expanded mypy | **deferred, non-green** (standing) |

Only the gates this revision affects were re-run. `src/` changed only by
the additive `EntryBatch.anchors` field (empty by default). So the
dependent check is limited to byte reproduction of every proposal built
through `build_entry_batch`. No oracle or accepted artifact changed.
**Not all-green.**

## Secrets baseline

This was a scoped update from the starting bytes only, using a private-settings
scan under the baseline's own plugins and filters (`.claude/_sp/eqc/bl/`).
`detect-secrets scan --baseline` was never run, and no `pragma: allowlist
secret` was added.

**First round.** The baseline went from `2d785478…347b` (118 files, 5527
entries) to `b9c335ae…3c1c` (123 files, 5555 entries): 28 added, 0 moved,
0 pruned. Each addition was verified as a named public value.

**This revision** changed the hashes of the candidate PROPOSAL, its identity
and the DRAFTS, which this packet's own files print:

- **Before:** `b9c335aec71384daec96e402f29d155a248474ce8b5b9ac8e626e809ccdf3c1c`
  (123 files, 5555 entries).
- **After:** `e05a05da0f15f82b831aabc98cbc22ff1f2df2946645fa15a86d0beb6eaaf887`
  (123 files, 5555 entries): 8 added, 8 pruned, 13 line numbers refreshed,
  0 other files touched.
- **Pruned (8):** only this packet's own superseded values, which the rescan
  no longer finds:
  - `REPLACEMENT.py` lines 115, 116, 118;
  - `DELTA.txt` line 3281 (×2);
  - the test's lines 36, 37, 39.
- **Added (8):** each was recovered from its line, checked against its
  SHA-1, and recomputed here as a named public value (`verify.json`, 0
  unverified of 8):
  - the new PROPOSAL SHA-256 and `proposal_identity`, and the new DRAFTS
    SHA-256, in `REPLACEMENT.py` (115, 116, 118) and the test (36, 37, 39);
  - in `DELTA.txt` (3335), the candidate identity and the replayed
    candidate Equipment batch's `batch_diff_hash`.
- **Line refreshes (13):** only in the touched files, where the entries
  shifted: 6 in the PROPOSAL and 7 in `DELTA.txt`. (The previous text
  said `DELTA.txt` only; that was wrong.)
- **Preserved** (asserted before writing): settings, plugins, filters,
  version and `generated_at`; every untouched file's entries; key order.
  Added entries are `is_verified: false`. LF.
- A rescan after writing finds 0 new and 0 obsolete in all 7 files
  (generator and this review: 0 findings).
- **Staged by name** (`git add -- .secrets.baseline`), because the hook
  refuses an unstaged baseline. Nothing is committed.

**Close round.** Splitting the table close changed the candidate PROPOSAL
hash and its identity (the DRAFTS are unchanged). The same scoped method
was used from the previous round's bytes:

- **Before:** `e05a05da0f15f82b831aabc98cbc22ff1f2df2946645fa15a86d0beb6eaaf887`
  (123 files, 5555 entries).
- **After:** `2bab5a741e65d0b64dec8799f2d29914cefc0652b60e1ca32b46e84228d9ad4f`
  (123 files, 5555 entries): 6 added, 6 pruned, 13 line numbers refreshed
  (6 PROPOSAL, 7 `DELTA.txt`), 0 other files touched.
- **Pruned (6):** this packet's superseded values only:
  - `REPLACEMENT.py` 115, 116;
  - `DELTA.txt` 3335 (×2);
  - the test's 36, 37.
- **Added (6)**, each verified as a named public value (0 unverified of 6):
  - the new PROPOSAL SHA-256 and `proposal_identity` in `REPLACEMENT.py`
    (115, 116) and in the test (36, 37);
  - in `DELTA.txt` (3341), the candidate identity and the replayed
    Equipment batch's `batch_diff_hash`.
- **Preserved:** the same assertions as above.
- **Rescan:** 0 new, 0 obsolete in all 7 files.

**Hook.** `detect-secrets-hook --baseline .secrets.baseline` on the final
bytes of the 7 files (`.claude/_sp/eqc/bl/files.txt`) plus the changed
`src/afterworlds/ingestion/mechanical/authoring.py`, run twice: exit 0
both times, and the baseline SHA-256 is unchanged (`2bab5a74…ad4f`).

## Unresolved boundaries

1. **Spellbook (1 ref)** remains unresolved (revision 3).
2. **Settled engineering, not fresh Owner policy.** Two things are settled
   by review and are not new policy choices:
   - The vehicle governing notes: keelboat / rowboat read the introduction's
     "The following notes apply" clauses (speed, crew, passengers, damage
     threshold, ship repair). The section ends with them, so none is left
     out.
   - The replay of the 21 unchanged proposals: they are reused
     byte-identical with their recorded rule, reviewer, time and evidence,
     and none is reauthored.
3. **Owner acceptance still required.** The Owner must still accept the
   exact semantics of the changed Equipment batch (the PROPOSAL above, 67 new
   records) and of the 161 new drafts. This packet does not do that.
4. **Recording.** Accepting this needs an Owner-approved fresh 22-batch
   chain over no prior (there is no supersession), re-applying every
   recorded rule, reviewer, time and resolution as `REPLACEMENT.py` does in
   memory. It is not done here. The standing Owner decision stays one
   bounded pass after the packets and before publication/activation; it is
   not reordered here.

## Owner acceptance offer (one, consolidated)

After independent review of this revision, the Owner is offered a single
decision. The offer is to accept the Equipment batch's exact semantics as
proposed:

- `13271e03…02e0`, identity `309e4405…1680`;
- the 161 drafts `bfbf5a7a…39eb`;

each for recording in a fresh chain as `REPLACEMENT.py` composes it. Until
then the candidate is **UNACCEPTED**.
