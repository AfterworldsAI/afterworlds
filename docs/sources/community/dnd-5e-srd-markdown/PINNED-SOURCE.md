# Pinned community source: `downfallx/dnd-5e-srd-markdown`

**Status: qualified.** One Afterworlds-controlled copy, pinned so that every
correction is a reviewable diff against a known baseline rather than an edit
with no baseline. It has been compared against the official PDF and corrected
where the comparison found defects, and the final source boundary was reviewed
independently at `b70d016` (`source-structure-final-review.md`). Qualified or
not, this is a copy of a community conversion: it is a machine-readable
representation of the source, never a rules authority in its own right, and
qualification of these bytes is not a semantic acceptance of what the rules
mean.

Established under Step 2 of the Recorded Owner Decision of 21 September 2026
(`docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md`).

## What is pinned

| | |
|---|---|
| Upstream repository | <https://github.com/downfallx/dnd-5e-srd-markdown> |
| Upstream commit | `1b4b99dcb786cdd1a2fb26f8acec1551191f1ca4` |
| Pinned on | 2026-09-21 |
| Upstream tracked files at that commit | 21 |
| Files vendored here | 16 (1,893,352 bytes upstream; 1,893,029 as corrected) |
| Controlled additions | 1 (`legal-information.md`, official p.1) |
| Corrections applied | 35, across 7 files (8 of them Owner corrections, 1 official-source-backed) |

`source_pin.json` records the SHA-256 and byte length of **all 21** upstream
tracked files, including the five deliberately not vendored and the reason for
each. `tests/test_pinned_community_source.py` re-hashes the vendored bytes
against that manifest, so a silent edit to this directory fails a test rather
than becoming an unrecorded change to a pinned source.

Each file carries two digests. `upstream_sha256` is the **upstream Git blob**
(LF line endings) and never changes: it is the baseline every correction is a
diff against. `sha256` is the bytes this repository controls, and it equals
`upstream_sha256` exactly when that file's `corrections` list is empty — a test
asserts the equivalence in both directions, so correcting a file cannot mean
quietly restamping its expected digest. `.gitattributes` marks this directory
`-text` so no platform's checkout rewrites the bytes; without that, the pin
would verify only on the machine that wrote it.

Content is Markdown with embedded HTML tables (`colspan`, empty cells, and
repeated ability-grid headers all occur), which is why the files are kept as
source text rather than normalized on the way in.

## Corrections and additions

Thirty-five corrections are applied, each recorded in `source_pin.json` against
the official page and section it was checked at, with what changed and why:
three creature ability grids whose cell boundaries were lost, five grids whose
MOD/SAVE legend sat over the wrong columns, two class tables with a sixteenth
empty column, one table row dropped under a header repeated across a page
break, four sentences split into two paragraphs at a printed column break, one
sentence the official PDF does not carry, and six stat blocks emitted at the
heading depth of the entry that summons them, which had ended those entries
and captured the entries after them, one glossary heading emitted at the wrong
rank, one two-row table header flattened into a header and a data row, two
tables whose italic group labels had become data rows (one of them also a
paired-column list read row-major), one table caption the conversion did
not carry, and one stat-block Initiative emitted after the CR line instead of
beside AC. Eight more are **Owner corrections, not publisher text**: four
Level 2 class spell tables (Bard, Druid, Sorcerer, Wizard) are made to agree
with the spell descriptions the official PDF prints, by the Owner's decision
that the descriptions are correct and those table cells wrong; the stat block
the PDF names *Warrior Veteran* is named *Veteran Warrior*, the name Deck of
Illusions prints for it. Each carries `OWNER CORRECTION, not publisher text`
in its manifest `why`. One more is an **official-source-backed correction,
not publisher text and not an Owner decision**: the Young White Dragon's INT
save carries the minus sign the current official individual stat block
prints, where the SRD page and the Basic Rules print it unsigned; it was
proposed under an Owner-requested lookup and awaits the Owner's exact
acceptance. The official PDF itself is unchanged and remains the evidence. The reasoning and the evidence are in
`docs/architecture/issue-5c-5d-community-source-corrections.md`.

`legal-information.md` is a **controlled addition**, not upstream content: the
snapshot omits the SRD's Legal Information page, and CC-BY-4.0 requires the
attribution statement to travel with derived work. It is built from official
p.1 and compacts identically to that page. Official p.1 is the attribution
page; it is not the navigation-only table of contents on pp.2–4.

Upstream `README.md` and `CHANGELOG.md` are kept with `role: upstream-process`.
They are the community repository's own process and licence history, are not
ingested as SRD content, and are not part of the thirteen content files the
comparison covers.

`preserved_official_defects` is empty. It held the Young White Dragon's
unsigned INT save until the official-source-backed correction above replaced
it.

## Authority

The official WotC SRD 5.2.1 PDF remains the ultimate source authority:

| | |
|---|---|
| Path | `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf` |
| SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| Size | 6,031,375 bytes, 364 pages |

Corrected Markdown may become the canonical machine-readable representation of
that document. It does not thereby become an independent rules authority. Where
this snapshot and the PDF disagree, the PDF decides, and the discrepancy is
resolved — never silenced by updating an expected checksum.

Wording need not match the PDF word for word. Meaning and relationships must be
faithful. Where wording differs, either restore the official wording or retain
the Markdown where meaning is preserved; cosmetic identity is not forced and
substantive differences are not waived.

Comparison coverage against the PDF - every section, table and entry, with
each remaining difference named and dispositioned - is recorded in
`docs/architecture/issue-5c-5d-community-source-coverage.json`.

## Licence and attribution

Upstream `LICENSE` is vendored verbatim in this directory. The content derives
from the System Reference Document 5.2.1 released by Wizards of the Coast under
**CC BY 4.0**; attribution requirements travel with any derived corpus built
from it. Nothing in this directory may be relicensed, and the attribution must
survive extraction into machine-readable form.
