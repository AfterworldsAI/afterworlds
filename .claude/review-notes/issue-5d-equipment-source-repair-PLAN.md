# Equipment source repair, qualification and accepted-authority plan — CRD Issue 5c/5d (#132, #137)

**Status: PLAN ONLY. Nothing here is applied.** No source, pin, release, oracle,
resolution, DB or Chroma state has changed. The uncommitted Equipment proposal
`8725738d…f664` (file `bb1d6342…5a7c`) stays unaccepted and **source-fidelity
blocked**; it is superseded by whatever proposal the repaired release yields.
For Codex's independent review before any Owner boundary or settled correction.

## 1. The defect, from the official page

`equipment.md` is pinned byte-identical to upstream (`sha256 == upstream_sha256
== eef7cb05…9970`, 72402 bytes, `corrections: []`).

**Food, Drink, and Lodging (official pp.101–102).** The PDF sets one logical
`Item | Cost` list in two paired sub-columns that snake **column-major**: p.101
right page-column, sub-columns at x≈317 and x≈433, then p.102 left page-column,
sub-columns at x≈67 and x≈183. p.102 reprints the `Item Cost Item Cost` header.
The group labels are set in `GillSans-Italic` and their members are indented.
The community conversion read the table **row-major** as four columns. As a result it:

* pairs unrelated entries on one row (`Ale (mug) 4 CP | Comfortable 8 SP`);
* promotes two group labels into a second `<thead>` row (`Inn Stay per Day | | Meal |`);
* renders the third group label as a priceless item (`Wine (bottle) | ""`).

A reader of the released table gets the inn prices of Comfortable, Wealthy and
Aristocratic as meal prices, and the reverse.

This was verified from geometry, not only by eye. `.claude/_eq/food_pairs_probe.py`
reads each sub-column's lines in order, taking italic runs as group labels. It
yields exactly the 20-entry sequence in §3, and `MATCH` against the draft. The
renders are `.claude/_eq/p101_food.png` and `p102_food.png`.

**Tack, Harness, and Drawn Vehicles (official p.100).** The render
`.claude/_eq/p100_tack.png` sets *Saddle* in italic, with Exotic, Military and
Riding indented under it. The release has `Saddle | | ` as a data row. The values
keep their labels and their order, so no value is wrong. What is lost is the
group: "Saddle" reads as an item with no weight and no cost, and the three
members read as unqualified items called "Exotic", "Military" and "Riding".

**Why qualification admitted it.** `docs/architecture/issue-5c-5d-community-source-coverage.json`
→ `qualification.number_order_pass.pages_read_because_their_number_order_differs`
contains **101 and 102**. The corrections doc then disposed of all 64 such pages
with this sentence: "Every one is a two-column page whose reading order differs
from the snapshot's single column". That disposition is not admission here:

* A column-major table read row-major has the same ordered-number signature as a
  two-column page.
* The token multiset is unchanged.
* Every row has the header's width, so the table scan passes it too.

p.100 was never flagged. Saddle's numbers are in order, and only the italic group
structure is lost, which neither pass reads. That is a third blind spot: group
semantics carried by typeface.

## 2. Bounded sibling audit (Equipment only, per the Owner's scope)

**Defect family:** group and column structure the conversion lost while keeping
every character and every row width. It covers paired or snaked multi-column
tables and italic group labels flattened into data rows.
**Trigger:** Codex verified Food on pp.101–102, and Tack is a same-family sibling
that the first pass found.
**Instruments** (scratch; either becomes a committed check under §4 step 2):

* `.claude/_eq/sibling_scan.py` reads every `equipment.md` table (15) for:
  * column count;
  * header rows;
  * a paired header (`h[:n/2] == h[n/2:]`);
  * empty cells.

  It also reads pp.89–103 for header lines with a repeated column pair.
* `.claude/_eq/italic_runs_scan.py` reads every maximal run of small italic words
  on each line of pp.89–103 that the Markdown does not carry as an `<em>`/`_…_`
  label. It supersedes the first scan's whole-line italic test. That test missed
  *Wine (bottle)* because the label shares its line with "Comfortable 2 SP" in
  the neighbouring sub-column. The per-run scan reports exactly four labels:
  *Saddle* (p.100), *Inn Stay per Day* and *Meal* (p.101), and *Wine (bottle)*
  (p.102).

| Structure | Evidence | Disposition |
| --- | --- | --- |
| Food, Drink, and Lodging (pp.101–102) | the only paired header (4 cols, 2 head rows); 1 empty cell; 3 italic labels missing | **patch** (§3) |
| Tack, Harness, and Drawn Vehicles (p.100) | 2 empty cells; italic *Saddle* missing | **patch** (§3) |
| Weapons, Armor | group rows already `<th colspan="6"><em>…</em></th>`, and every PDF italic label is present | already safe: admitted by the per-run italic scan, which reports none missing on their pages |
| Coin Values, Adventuring Gear, Ammunition, Arcane/Druidic Focuses, Holy Symbols, Mounts and Other Animals, Hirelings, Spellcasting Services, Spell Scroll Costs | single header row, no paired header, no empty cell, no missing italic label on pp.89–103 | already safe for these three properties, by the two scans. They say nothing about cell association inside a table that is neither paired nor grouped |
| Vehicles table (no caption) | p.101 prints the caption *Airborne and Waterborne Vehicles* (GillSans-SemiBold, top 41) above the full-width table, before *Crew*. The md's order (Speed note, table, Crew) matches, and the prose above already names "The Airborne and Waterborne Vehicles table" | **patch, folded in (§3 edit 3), recommended.** It is a different family (missing caption), but it sits in the authored *Mounts and Vehicles* section, and every source correction mints a new release (§4.5). Deferring it would guarantee a second rebuild and a second §5 event. Codex may split it out; the cost of doing so is stated here |
| p.99 "Spell Scroll Spell Scroll" | glyph overlap from the heading `Spell Scroll (Cantrip, 30 GP; Level 1, 50 GP)` | not a table; no defect |
| Other files' two-column or snaked tables, and the other 62 order-flagged pages | not inspected | **not inspected; Owner/Codex decision needed.** The admission sentence in §1 is equally weak for them. Whether to re-admit them is a scope question this plan does not decide |

## 3. Draft source patch (NOT applied)

**The reviewable patch is `.claude/review-notes/issue-5d-equipment-source-repair.diff`**
(uncommitted). `git apply --check` is clean against the current `equipment.md`,
and the diff has 64 changed lines. It holds three edits in one file:

* Family **I, "A paired-column table snaked across columns and pages, and italic
  group labels flattened into data rows"**: 2 edits, Food and Tack. Group rows
  follow the file's own Weapons/Armor convention.
* Family **J, "A table caption the conversion did not carry"**: 1 edit, adding
  `**Airborne and Waterborne Vehicles**` above the Large Vehicles table, bound
  into the table's own unit by `_merge_table_context`.

The excerpts below are for reading. The diff is what applies.

**Food.** This replaces the whole `<table>` under `**Food, Drink, and Lodging**`
(lines 1982–2053), with the header row once and the list in PDF order:

```html
<table>
  <thead>
    <tr>
      <th>Item</th>
      <th>Cost</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Ale (mug)</td><td>4 CP</td></tr>
    <tr><td>Bread (loaf)</td><td>2 CP</td></tr>
    <tr><td>Cheese (wedge)</td><td>1 SP</td></tr>
    <tr><th colspan="2"><em>Inn Stay per Day</em></th></tr>
    <tr><td>Squalid</td><td>7 CP</td></tr>
    <tr><td>Poor</td><td>1 SP</td></tr>
    <tr><td>Modest</td><td>5 SP</td></tr>
    <tr><td>Comfortable</td><td>8 SP</td></tr>
    <tr><td>Wealthy</td><td>2 GP</td></tr>
    <tr><td>Aristocratic</td><td>4 GP</td></tr>
    <tr><th colspan="2"><em>Meal</em></th></tr>
    <tr><td>Squalid</td><td>1 CP</td></tr>
    <tr><td>Poor</td><td>2 CP</td></tr>
    <tr><td>Modest</td><td>1 SP</td></tr>
    <tr><td>Comfortable</td><td>2 SP</td></tr>
    <tr><td>Wealthy</td><td>3 SP</td></tr>
    <tr><td>Aristocratic</td><td>6 SP</td></tr>
    <tr><th colspan="2"><em>Wine (bottle)</em></th></tr>
    <tr><td>Common</td><td>2 SP</td></tr>
    <tr><td>Fine</td><td>10 GP</td></tr>
  </tbody>
</table>
```

The rows are compacted here for review. The applied bytes use the file's
one-cell-per-line indentation, exactly as `.claude/_eq/repair_probe.py` emits
them.

**Tack** (lines 1783–1787):

```diff
     <tr>
-      <td>Saddle</td>
-      <td></td>
-      <td></td>
+      <th colspan="3"><em>Saddle</em></th>
     </tr>
```

**Rendering choice, for review.** The PDF's four physical columns carry no
meaning of their own; they are two halves of one list, laid out to fit.
Correcting cells in place inside four columns is not possible: the rows on p.101
and p.102 pair different entries. So the only rendering that keeps every cost
with its item and its group is the single logical `Item | Cost` list. The
precedent is lossless re-layout ("Preserved rather than corrected" item 3, the
flattened spanning header).

**Caption (J)**, inserted between the *Speed* note's last line and `<table>`:

```diff
 These vehicles can't be rowed against any significant current, … weighs 100 pounds.

+**Airborne and Waterborne Vehicles**
+
 <table>
```

**Resulting bytes (probe, all three edits):** `sha256 ba4d96bf7c08a44103b11be1ae5385e6e09f3f5478d56c3a2f38f97bd77d645b`,
72594 bytes. I and J alone would give `89f80a68…6fbc`, 72556 bytes.

**Unit stability.** `build_structure` over all 14 `CORPUS_FILES` gives **10465
units before and after**, and every unit outside `equipment.md` keeps its file,
compact start and compact end. `build_leaves` sets
`occurrence_index = index` over exactly those units (`source_units.py:392–412`),
so no non-Equipment leaf's `leaf_id` or `occurrence_index` moves. Within
`equipment.md`, 376 units before and after: 85 differ, from the Tack table
(unit 291) onward. Those are the edited table leaves themselves, plus later
units whose per-file compact offsets shift.

## 4. Source repair steps (each needs the authorization named)

1. **Apply** `issue-5d-equipment-source-repair.diff` to `equipment.md`. Add all
   three edits to `source_pin.json`:
   * `files[equipment.md].sha256` and `bytes`;
   * `corrections[]` with pages, section, change and why;
   * `corrections_applied` 21 → 24.

   Add families I and J to `issue-5c-5d-community-source-corrections.md`, and
   its sibling-audit dispositions. Amend its "Sixty-four body pages…"
   paragraph: pp.101–102 were not reading-order differences, and the
   ordered-number pass cannot admit a snaked table.
   `SOURCE_TRANSFORM_VERSION` stays `"3"`. By its own comment a bump is for recipe
   changes that `transform_config` does not already see, and pin digests are in
   `transform_config`. *Owner-authorized* ("source correction"). **Applying it is
   the next step.**
2. **Regression coverage** in `tests/ingestion/source/test_community_source_structure.py`.
   Name Food and Tack as values: the Inn/Meal/Wine members and their costs, and
   Saddle's members. Also name the Vehicles caption as bound to its table's unit. Add one bounded property for `equipment.md`: no `<thead>`
   with more than one row, no paired header, no data row whose value cells are
   all empty. Add a planted-defect control that re-injects the upstream Food
   table and must fail, per the family-E precedent. Run it against the
   uncorrected bytes to show it fails there.
3. **Regenerate** the coverage record with `scripts/regen_community_source_coverage.py`.
   Pages 101/102 may stay in the order list, because the PDF's line-wise
   extraction still reads row-major. Their disposition text then changes from
   reading order to "column-major table, family I". The token pass should also
   newly count `Item`/`Cost` on p.102: the PDF prints the header twice and the
   corrected md once. That is preserved family 1 (a header reprinted at a page
   break), not a regression. Verify both; don't assume them.
4. **Re-qualification.** `source_pin.json` says `status: qualified`, reviewed by
   Codex at `b70d016`, scope "the corrected bytes against the official PDF". New
   bytes after that review reopen that gate for `equipment.md` at least.
   **Codex/Owner process decision**: a scoped re-review of families I and J, or a
   renewed whole-source qualification.
5. **Release.** The new pin digests change `transform_config_hash`, which is
   derived from `SOURCE_PIN`. That yields a new `package_uuid`
   (`content_id("package", PDF_SHA256, transform_hash)`), a new release version
   `5.2.1-corpus.<new12>`, `bundle_root_hash` and `persisted_corpus_digest`.
   Build it isolated, in a scratch DB only. **Publication or activation, and any
   shared DB/Chroma write, is a separate Owner authorization.**

## 5. Accepted authority: what survives, and why no supported path carries it

Current authority: release `9717e288-c099-5217-b2d2-f89aeabd7b73` /
`5.2.1-corpus.883aabdf-462`, oracle `srd-5-2-1-corpus-883aabdf-462.json`
`fdc698df…6c87`. It holds 136 records, 1016 spans, 12 batches, 6 resolutions,
and their authorizations.

**Content identity survives the repair, by construction:**

* `leaf_id = content_id("source-leaf", file, compact_start, compact_end)` with
  per-file offsets. The oracle's 691 leaves are all in rules-glossary (221),
  playing-the-game (211), character-creation (124), character-origins (78) and
  feats (57), and none is in `equipment.md`. So every accepted `leaf_id` is
  unchanged, and so is every semantic `span_id`
  (`content_id("semantic_span", leaf_id, start, end)`).
* Corpus-wide unit count and every non-Equipment unit are unchanged (§3), so no
  accepted leaf's `occurrence_index` moves. The oracle stores none: `source_leaf_order` reads it from the bound
  release's own ledger, scoped to its package, so this is a consumer-ordering
  fact, not an identity one.
* Page coordinates of accepted leaves are unchanged, because no accepted file is
  edited.

**Release identity does not survive:**

* The oracle's `release_binding`, and the `release_binding` of each of the 6
  recorded `ReferenceResolution`s, name all six coordinates of the old release.
  That is 7 occurrences of the package uuid.
* All **765** `chunk_id` occurrences change, because
  `chunk_id = content_id("chunk", package_uuid, leaf_id)` (`corpus/transform.py:110`).

**Every existing seam refuses to carry authority across releases, deliberately:**

* `acceptance.py:369–373`: "this proposal binds a different 5c release than the
  prior accepted authority it would extend".
* `AcceptedOracle` (`oracle.py:232–236`): "A projection bound to any other
  release is judged by nothing and fails as mismatched".
  `committed_oracle_for(new release)` returns `None`, meaning "no accepted
  authority is committed for this release".
* `ReferenceResolution` (`models.py`): its six-coordinate binding exists so that
  a resolution "pasted into another release's artifact [is] a mismatch rather
  than a silent re-application of a decision nobody made about that release".
* `schema_lift.py` is the only succession mechanism. It lifts one accepted
  artifact across a *representation schema* transition by proving the inherited
  elements byte-identical, and it refuses transforming lifts. A release change
  rewrites `chunk_id`s and bindings, so it is a transforming lift by that
  module's own definition.

So the repaired release starts with **no accepted authority**. Every
consumer-facing path (gate, build, rules-authority `EffectiveAuthority`) judges
it by nothing until one of these two happens. **Owner decision; not implemented,
and not decidable in code:**

* **(A) Release-succession contract** (new; the `schema_lift` pattern extended
  to releases). It would be an explicit, recorded authorization of one exact
  transition, old binding → new binding. It proves that every inherited leaf,
  span, content and page is byte-identical across the two ledgers. It
  re-derives each `chunk_id` from the new `package_uuid`, and states nothing
  else as changed. It re-binds the 12 batches and 6 resolutions under a new
  oracle for the new release, and records the succession as evidence. The old
  oracle `fdc698…` stays committed as the historical authority for `883aabdf-462`
  and is not rewritten. This is a genuine new acceptance/identity-migration
  contract: it needs an ADR-005d amendment or an Owner Decision before any code.
* **(B) Re-acceptance.** The Owner re-accepts the 12 batches and 6 resolutions
  against the new release, through the existing `accept_proposal` and
  `resolve_references` seams, with regenerated proposals. This needs no new
  mechanism, but it is 12 + 1 fresh Owner acceptances of content that did not
  change. It is also not a rubber stamp of identical bytes. Regenerated
  proposals carry today's representation schema and policy and new proposal
  identities, while a committed batch keeps the schema it was built under.
  So (B) is 12 re-reviews of possibly re-lifted artifacts.

**Not proposed:**

* restamping `fdc698…` in place;
* editing bindings in the committed oracle;
* treating the ~30 test files that pin `883aabdf-462`/`9717e288` as data to find-and-replace.

Each of these is the silent rebind the Owner excluded.

## 6. Record grain: engineering remedy vs genuine product choice

The packet's §2.1 rationale restated a helper limitation as grain: "an item
cannot be a record without dropping its price", and "containment is not
membership". It is retired. The facts:

* `authoring.heading_group` (`authoring.py:579–594`) excludes every placed
  record's heading leaf, unconditionally, as "section heading: names the section
  and states no rule".
* The unit validator admits a leaf reached by several decisions
  (`projection.py`, "one leaf may legitimately be reached by several"). So a
  clause reading `#### Acid (25 GP)` while that leaf is also excluded would
  *pass silently* and state something false. The remedy therefore cannot be
  "let the clause win". It has to be an explicit declaration.
* Reference resolutions target a **record key only**
  (`ReferenceResolution.target_record_key`; there is no component target).
  Exactness of a destination is therefore decided by record grain.
* The consumer contract for catalogue sections already exists.
  `EffectiveAuthority.members` (`services/rules_authority/application.py:318`)
  says: "A catalogue section's own record holds only its introduction; this is
  how a consumer that names the section still reaches the entries it prints."
  It is built from `CATALOGUE_MEMBER` edges and used by the accepted
  origins/feats batch (`members=MEMBERS`).

**Consumer consequence of section grain, measured on the 43 drafts:**

* 14 gear citations resolve to the whole 81-entry Adventuring Gear record, not
  the item: Arrows, Book ×2, Crowbar, Healer's Kit, Holy Symbol, Parchment ×2,
  Pouches, Quiver, Robe ×2 and Traveler's Clothes ×2.
* 11 tool citations resolve to all of *Tools*.
* 16 weapon/armor citations resolve to the whole Weapons or Armor section.
* A consumer following "Crowbar" is handed 81 items' rules.

| Destination shape | Drafts | Classification |
| --- | --- | --- |
| Priced `####` gear entries (81) and `###` lifestyle options (7) | 14 gear | **Settled engineering remedy.** Make them per-entry records, plus `CATALOGUE_MEMBER` of their section, as in origins/feats. The only obstacle is the heading exclusion. The fix is a declared, default-off `Placement` field meaning "this heading states the entry's price", which moves that heading from the excluded group to governing prose. It is the same substance as the Tier fix (`600c22c`, level ranges moved from excluded headings to governing prose), except that the Tier fix was batch data only, while this one changes the shared helper. Default-off makes it byte-neutral for all 12 accepted batches; the committed replay tests would show that. Not implemented; it goes through Codex review as a helper change |
| `####` category headings in *Tools* (*Artisan's Tools*, *Other Tools*) | 1 exact ("Artisan's Tools") | Same remedy. It also narrows the 8 item-named tool drafts below to their category record (Calligrapher's Supplies → *Artisan's Tools*; Thieves' Tools, Gaming Set → *Other Tools*) |
| Bold-block entries: individual tools (`**Thieves' Tools (25 GP)**` + Ability/Weight/Utilize/Craft lines) and weapon properties (`**Light.**`) | 8 tool, 3 property | **Genuine product/schema choice → Owner.** The "heading" is a bold line inside a rule-bearing leaf, and there is no record precedent for a record whose name shares a leaf with its rules. Until then these resolve to the enclosing record |
| Table-row or group/category items (Daggers, Quarterstaff, Shortbow, Spear, "Melee weapon", "Ranged weapons"; "Light, Medium, or Heavy armor") | 7 | **Genuine product/schema choice → Owner.** There is no precedent for a table-row-grain record, and a component-level target would be new schema policy. They resolve to the section record, which is truthful but approximate |
| The part itself ("the equipment described in "Equipment""; "See "Equipment" for rules on many items") | 2 unresolved citations (not drafts) | **Stay unresolved.** No section truthfully stands for the part. A part-level destination record would be a new record kind, which is a schema question for the Owner, not a draft. They stay detectably unresolved, as `reference_resolution` intends |

The 10 section-locating "Equipment" drafts, read against their source sentences:

| Source | Target |
| --- | --- |
| "The categories of armor are described in "Equipment."" (CC l.118) | Armor |
| "calculate your AC using the rules in "Equipment."" (CC l.631) | Armor |
| "Look up the damage and properties of your weapons in "Equipment."" (CC l.638) | Weapons |
| "the firearms described in "Equipment"" (CC l.849) | Weapons |
| "the Finesse property (see "Equipment")" (PtG l.371) | Weapons |
| "See "Equipment" for weapons' damage dice" (PtG l.1158) | Weapons |
| "Tools are detailed in "Equipment."" (CO l.25) | Tools |
| "Gaming Set (see "Equipment")" (CO l.62) | Tools |
| "see "Equipment" for a selection of mounts for sale" (PtG l.818) | Mounts and Vehicles |
| ""Equipment" includes vehicles for sale" (PtG l.869) | Mounts and Vehicles |

Each names the thing its target prices or defines. None is a whole-part
citation re-dressed.

**Authoring adaptation the repair forces** (minimal, Owner-authorized):

* The Food and Tack clause literals and tests change to the corrected rows,
  including three new group rows and Saddle as a group.
* Every `equipment.md` leaf and span id from the Tack table onward changes, which none
  of the accepted authority uses.
* The proposal identity, its file hash and the 8 detect-secrets hashes are
  superseded.

The grain remedy in row 1 is the only structural change, and it is gated on
Codex review of the helper change. It takes the batch from 14 records to about
104: 81 gear entries, 7 lifestyle options, 2 tool categories and 14 sections.
That is the review effort the Owner would be accepting.

## 7. Detect-secrets baseline: evidence retained, request deferred

On the exact uncommitted files, `venv/Scripts/detect-secrets-hook --baseline .secrets.baseline`
exited **1** with 8 `Hex High Entropy String` findings, all public
content/identity hashes:

* `.claude/review-notes/issue-5d-equipment-PROPOSAL.json` lines 17461, 17462,
  17464, 17466, 17469 and 17472: the release binding, schema and policy hashes.
* `tests/ingestion/mechanical/test_equipment_proposal.py` lines 108–109: the
  accepted-oracle SHA `fdc698…` and the proposal identity `8725738d…`.

The baseline splice that would have recorded them was rejected by auto mode as
"Security Weaken". The baseline is unchanged and staged at `bf73d440…3cd3`. The
action was not retried, worked around, or handed to another writer.

**No Owner action is requested now.** §4–§6 supersede the proposal identity, the
file and every line number above. Approving these 8 would approve obsolete
hashes. Once the repaired proposal settles, the Owner runs the scanner update
directly from their own shell, on the final files only:

```bash
venv/Scripts/detect-secrets scan --baseline .secrets.baseline <final proposal JSON> <final test file>
git diff .secrets.baseline   # expect the new public-hash entries; check every REMOVED entry
venv/Scripts/detect-secrets-hook --baseline .secrets.baseline <final proposal JSON> <final test file>   # must exit 0
```

If the rescan removes historical findings the repository deliberately keeps,
restore them before staging, as `8f7c655` did. This is the standing-approved
scan, with no permission, settings, pragma or detector change.

## 8. Next authorized step, and what stays open

**Next step (Owner-authorized source correction, pending Codex's review of this
plan):** apply §3 and §4 steps 1–3 on the topic branch. That means:

* the `equipment.md` bytes from the reviewable diff, `source_pin.json`, the
  corrections doc (families I and J, and the amended order-pass disposition);
* the regression test with its planted-defect control;
* the regenerated coverage record.

The gates are the source tests, Black, Ruff, `mypy src/`, detect-secrets on
those files, and pytest on the source suites. Commit only on green. Nothing past
that moves without the decisions below.

**Owner/Codex decisions this plan surfaces and does not make:**

1. Re-qualification scope after a post-`b70d016` correction (§4.4).
2. Accepted-authority carriage to the repaired release: a new release-succession
   contract (A) or re-acceptance (B) (§5).
3. Tool/property bold-block and table-row grain; a part-level destination (§6).
4. Whether the other 62 order-flagged pages need re-admission (§2).
5. Whether to keep the Vehicles caption (J) folded in. The recommendation is
   yes: splitting it out costs a second release and a second §5 event.

**Unchanged:**

* pip-audit stays deferred and non-green (31 vulnerabilities in 11 packages).
* No commit, push, publication, activation or shared DB/Chroma write has
  occurred.
* The uncommitted Equipment generator, proposal, test and packet are preserved.
