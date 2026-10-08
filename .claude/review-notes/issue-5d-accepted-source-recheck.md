# CRD Issue 5d — accepted-material source recheck (#132, #137)

Status: investigation only. Nothing here changes accepted artifacts or history,
the source release or pin, pending Equipment work, or acceptance rules. The
corrections below are **proposed and not applied**. No commits.

Pins checked against:
- Official PDF `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, sha256 `8974902d…3d87`.
- Oracle `srd-5-2-1-corpus-883aabdf-462.json`, sha256 `fdc698df…c56c87`
  (136 records, 1016 spans, 12 batches, 6 resolutions).

## Question and answer

**Question:** does the Equipment source/representation defect family affect
the 136 accepted records? That family covers lost row/column associations,
continuation order, group headings/captions, ranges, qualifiers, and
heading-to-description ownership.

**Answer:** it does not affect them in the way it affected Equipment. The
official PDF was the independent source throughout. On that basis:
- No accepted table data row has lost its column association. One
  header row is demoted (D4).
- No continuation is reordered.
- No group label or caption is missing.
- No leaf is attached to the wrong heading.

Two defect classes do reach accepted records:

1. **Page provenance.** Two leaves cite the wrong official page, and three
   more over-cite a second page.
2. **One header demotion.** The Travel Pace table header is misrepresented.

Neither class alters rule text, and no structured fact is derived from the
Travel Pace header. This result is limited to the checks listed below. It is
not a claim of universal correctness.

## Method

The accepted leaves are the 691 ledger leaves carrying spans in the accepted
oracle: 638 paragraphs, 40 tables, 9 lists and 4 headings. The ledger was
rebuilt in memory from the pinned sources (`build_source_ledger`), because the
local DB is empty.

| Check | Instrument (scratch in `.claude/_rc/`) | Oracle of truth |
|---|---|---|
| Table rows/columns | `table_geom2.py`: strict cell matcher (each cell is a consecutive word run on one PDF line, left to right) → `table_geom2.txt` | PDF word geometry |
| Table captions/group labels | `table_bbox.py`: PDF words inside each matched table's bounding box that are absent from the MD → `table_bbox.txt` | PDF |
| Visual table checks | Renders `p12_Pace.png`, `p15_Three.png`, `p21_adjust.png`, `page{13,14,15,19,21,22,24,85,86,181,185}.png` | Rendered PDF |
| Prose/list order and continuation | `prose_flow.py`: containment and order of 24-char chunks in PDF content-stream order → `prose_flow.txt`, with break detail in `prose_flag_detail.txt` | PDF content stream |
| Citations | `cite_check2.py`: ledger locator vs the pages holding the leaf's uniquely placed chunks → `cite_check2.txt` | PDF page text |
| Heading ownership | `heading_owner.py`: innermost MD owner heading vs the last PDF heading (GillSans ≥11.5pt) before the leaf, searched within the leaf's cited pages → `heading_owner.txt` | PDF content stream |
| D1/D2 mechanism | Raw vs kept anchors from `label_positions` over each unit's compact span (inline run; results under D1/D2) | Ledger internals |
| Consumer trace | `trace.py`: leaf → spans → prose bindings/provenance/facts → `defect_trace.txt` | Accepted oracle |

## Coverage

### Tables (40 of 40)

Every row was checked.
- **Strict geometric match:** 38 tables fully matched.
- **Checked visually:** the remaining tables plus the hard cases.
  - Class Overview has wrapped cells and continues from the left column to
    the right on p19. The repeated header is correctly dropped (13 rows).
  - Travel Pace, p12.
  - Cover, p15 ("Three-Quarters").
  - Starting Equipment at Higher Levels, p24. The PDF itself prints "5,000
    gp" in lowercase.
  - Elven Lineages, p85, and Fiendish Legacies, p86 (wrapped cells).
  - Water Needs per Day, p181.
- **Paired tables keep the same-line pairing:** Score/Cost, Score/Modifier,
  Typical DCs, Water, and Proficiency Bonus.
- **Column-major lists** carry no pairing semantics, and their caption status
  matches the PDF:
  - Rare Languages.
  - The conditions table [503] and the creature-types table [507]. Both are
    uncaptioned in the PDF as well.
- **Continuations are correct:**
  - Ability Scores and Backgrounds, p19→20.
  - Actions, p9→10.
  - Trinkets, p26→27 (three segments).
  - Damage Types, p180 left→right.
- **Qualifiers:** the Rare Languages "\*Primordial includes…" footnote is
  present in the accepted leaf.
- **Captions and group labels:** the bbox residue check found only adjacent
  prose. No accepted table is missing a caption or group label.

### Headings (4 of 4)

Tier 1 (Levels 1–4) through Tier 4 (Levels 17–20) on p24 match the PDF,
ranges included.

### Prose and lists (651 of 651)

- 638 leaves are contiguous and in order in the PDF content stream.
- The other 13 were broken by the instrument. Each was inspected, and none
  has a text or order defect. The causes are sidebars interrupting the flow,
  the p22 formula blocks (leaves 59/60/69, correctly split), run-in labels,
  and the "1½" glyph.
- The p19 step list [1] was checked visually. All five labels are paired
  with the correct descriptions.
- The continuations around sidebars are correct: [49] p21→22, [84], [100],
  [302], [355] and [443].

### Heading ownership (687 non-heading leaves)

- 666 leaves agree with the PDF.
- 12 differ only structurally and are **not defects**:
  - Sidebars (blockquotes) that the MD places under the section they
    interrupt: [95], [269], [270], [308], [362], [391], [437], [450].
  - Floated tables whose MD owner is the section whose text cites them by
    name, with the citing leaf adjacent:
    - [98] ← [96] "Starting Equipment at Higher Levels table".
    - [161] ← [158] "Elven Lineages table".
    - [316] ← [317] "Skills table".
  - [207] "_Origin Feat_" is Alert's category line. The PDF sets the feat
    name in a smaller heading face than the threshold.
- 9 leaves were not located by this instrument: tables [33], [40], [271],
  [311], [503], [507] and [521], plus [390] and [412].
  - All seven tables were verified row by row in the table checks above
    (content).
  - Their ownership was checked by hand: each sits directly after the MD
    paragraph that introduces it, under the same heading.
    - [33] Point Cost / Generate Your Scores.
    - [40] Determine Ability Modifiers.
    - [271] Ability Modifiers.
    - [311] Proficiency.
    - [521] Dehydration.
  - For the uncaptioned [503] and [507], the PDF text flow on p179 was
    checked. It reads "Condition … This glossary defines these conditions:
    Blinded … Unconscious" and "Creature Type … These are the game's creature
    types: Aberration … Undead". This matches the MD owners `Condition` and
    `Creature Type`.
  - [390] and [412] are not found because their cited page is wrong (see
    D1/D2).
- The earlier candidates [470], [621], [690], [140], [630] and [632] were
  artifacts of repeated-text location. With page-scoped search, they agree
  with the PDF.

### Citations (691 of 691)

- 685 leaves are consistent.
- 6 were flagged, and 5 of those are real (D1–D3).
- [12] "pp. 19-20" is correct: the table spans both pages.
- **Addendum (correction run):** the whole-text re-citation in
  `issue-5d-accepted-source-correction.md` found two more among the 685
  (D5, D6). The corrected count is 683 consistent and 7 wrong (D1–D3, D5,
  D6), plus D4, which is a header defect.

## Defects

Rule text is intact in every case below. Consumers are affected through the
chunk locator path:

`source_ledger.chunk_locators` → `transform.py` (`source_locator_value`) →
bundle and persisted rule chunks → `pipeline/retrieval/corpus_windows.py:188`
→ `source_locator_value` on retrieval results.

A Sojourner-facing or GM-facing citation therefore shows the page listed.

### D1 — [390] cites p. 13; the text is on official p. 14

- **Source text:** "The GM might require you to use an action for any of
  these activities when it needs special care…" This is the continuation of
  Interacting with Objects, printed on p14.
- **Citation status:** the ledger citation is `inherited`.
- **Why it happens:** the MD places this text before the p13 "Playing on a
  Grid" sidebar. The leaf has 166 unique p14 anchors, and every one of them
  contradicts file order, so all are dropped. The leaf inherits p13 from its
  neighbour.
- **Affected records:**
  - `play.combat.interacting`: prose binding, `gamemaster_latitude`.
  - A supporting-authority span on the same component.
- **Consumer consequence:** the retrieved chunk cites p. 13.
- **Smallest correction:** the leaf's locator should read `p. 14`.

### D2 — [412] "Unseen Attackers and Targets" sidebar cites p. 15; it is printed on p. 14

- **Evidence:** the sidebar body ("When you make an attack roll against a
  target you can't see, you have Disadvantage…") is in p14's text. It was
  confirmed visually in `page14.png`, at the bottom of the right column. D1
  is also visible there, at the top of the left column.
- **Citation status:** 28 of 28 uniquely placed chunks are on p14, but the
  ledger calls the citation `anchored` at p15.
- **Why it happens:** the MD places the sidebar after "Making an Attack"
  text that continues onto p15.
  - All 346 of the leaf's raw unique p14 anchors are dropped as order
    contradictions.
  - The single "anchored" position is labelled p15. Its window starts inside
    this unit but runs into the next unit's p15 text.
  - So the `anchored` status is earned by a window straddling the unit
    boundary, not by the leaf's own wording. This is a secondary weakness of
    the anchored/inherited evidence label.
- **Affected records:**
  - `play.combat.unseen_target`, with fact `fbaaa92520bd7011`.
  - `play.combat.unseen_attacker`, with fact `23d02aa73c175fe9`.
  - `play.combat.hidden_attacker`.
- **Consumer consequence:** these prose bindings and their fact provenance
  cite p. 15.
- **Smallest correction:** the locator should read `p. 14`.

### D3 — over-cites (the extra page is not wrong text, just an extra page)

| Leaf | Locator | Correct locator | Record/component |
|---|---|---|---|
| [373] | pp. 12-13 | p. 12 | `play.exploration.vehicles` |
| [391] | pp. 13-14 | p. 13 | `play.combat.grid` |
| [425] | pp. 15-16 | p. 15 | `play.combat.mounting` (fact `c27aeb895bc35859`) |

For all three, every uniquely placed chunk is on the single page given.

### D4 — [368] Travel Pace (p12): the two-row header is flattened

- **Official layout:** "Pace" heads the first column. "Distance Traveled
  Per…" spans three columns, with Minute / Hour / Day beneath it.
- **Accepted MD:** the thead is `Pace | Distance Traveled Per… | (empty) |
  (empty)`, and "Minute | Hour | Day" is the first body row.
- **Affected records:** `play.exploration.travel_pace` (prose binding,
  `contextual_applicability`). No structured fact depends on the header.
- **Consumer consequence:**
  - Positionally, the meaning survives.
  - A header-keyed reader sees empty Hour/Day headers and a spurious
    "Minute/Hour/Day" data row.
- **Smallest correction:** a two-row thead, with row 1 `(empty) |
  Distance Traveled Per… (colspan 3)` and row 2 `Pace | Minute | Hour | Day`.
  Placing "Pace" in row 2 matches the printed layout (`p12_Pace.png`) and
  avoids a rowspan, which the table-width check does not count. This
  supersedes the rowspan shape first proposed here.

### D5 — [271] Ability Modifiers table cites pp. 5-6; it is printed on p. 6 only

- **Evidence:** table geometry puts it at (p6, left column, row 9), and
  `page6.png` shows it there.
- **Why it happens:** the PDF extracts its numbers column by column. No
  window of the row-major MD text matches any page, so the table has no
  anchor of its own. Its p5 label comes from the preceding text, and its p6
  label comes from a 5-character straddle ("30+10").
- **Affected record:** `play.six_abilities.ability_modifiers`.
- **Smallest correction:** the locator should read `p. 6`.

### D6 — [160] Elf spellcasting-ability paragraph cites pp. 84-85; it is printed on p. 85 only

- **Evidence:** the paragraph's whole text ("Intelligence, Wisdom, or
  Charisma is your spellcasting ability for the spells you cast with this
  trait (choose the ability when you select the lineage).") occurs exactly
  once in the official page stream, and entirely on
  p85.
- **Affected record:** `character_origins.elf.elven_lineage`.
- **Smallest correction:** the locator should read `p. 85`. This is the same
  over-cite family as D3.

### Not a defect

- Typical DCs has a stray empty `<td colspan="2">`. It carries no content.

## Why D1–D4 need an Owner decision (not applied here)

> **Superseded (2026-09-24):** the Owner has since directed that these are
> routine source and citation defect fixes. See
> `issue-5d-accepted-source-correction.md`. Only release succession and
> rebinding remain deferred. The rest of this section is kept as history.

- **D1–D3 cause:** the citation partition in `source_citations.cite_units` /
  `community_tokens.label_positions`. Its labels only move forward through a
  file, and the MD moves relocated sidebars. A monotone partition therefore
  mislabels text placed out of PDF page order, and it lets a label boundary
  bleed across leaf ends.
- **D1–D3 correction options:**
  - An algorithm change.
  - A reviewed per-leaf locator override.
  - Either way, ledger and bundle hashes change, and so do locators in any
    released bundle.
- **D4 correction:** requires editing controlled Markdown, which changes the
  source pin.
- **Why this report does not apply them:** each change touches the source
  pin, the ledger, or the release, which this investigation must leave
  unchanged. They also bear on the deferred release-succession question.
- **What is preserved:** the accepted history stands as the record of what
  was approved. These defects are errors in that approved material. Approval
  does not make them correct.

## Not exposed and not checked (limits)

- **Structured facts vs prose:** not re-read semantically. For example,
  whether each fact's value faithfully restates its span was not checked.
  Only source representation and provenance were checked.
- **Order oracle:** PDF content-stream order. It was confirmed visually only
  for the 13 flagged prose leaves and the hard tables. The 638 contiguous
  leaves were not individually viewed.
- **Sidebar placement:** judged structurally, as an owner section plus
  adjacency, not as a rule on where sidebars should live.
- **Lists:** all 9 accepted lists were dumped with their owners: [1], [22],
  [116], [275], [353], [364], [524], [589] and [632]. Each is a plain
  enumeration under the correct heading, and each is contained in PDF order.
  None was rendered. The only labelled list, [1], was checked visually.
- **Out of scope:** unaccepted catalogues, including pending Equipment.
- **Tests:** none were rerun for this investigation. Unchanged hashes and
  passing tests are not offered as evidence of correctness.
