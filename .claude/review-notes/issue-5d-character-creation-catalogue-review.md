# CRD Issue 5d: Character Creation catalogue candidate and remaining-reference drafts #3 and #5 (#132, #137)

**Status: UNACCEPTED review material.** Nothing is accepted, recorded,
published or activated. There is no recording step, and no Owner approval
exists. The committed oracle is unchanged at
`15478aa5ea712b9946999ff865283cd12b36dd4f917137a76c225543066b8922`, which holds
23 batches, 1834 records, 10491 spans, 1475 units, 1438 resolutions, 64
reference findings and 0 uncovered leaves.

## What is proposed

| Artifact | sha256 / identity |
|---|---|
| `issue-5d-character-creation-catalogue-generator.py` | sha256 `7ffb2a6f969c5d7d23592b2cfc5e1cbd6c1367bef1239a2274b4d381e99c3433` |
| `issue-5d-character-creation-catalogue-PROPOSAL.json` | sha256 `98864a96933a3c967d0728b5bc2252f12a2af5e43accadf89595325e363adc2c`; proposal identity `cee3b640f955a34ed627fb720b8f9ec121d605dda6f792ba469ebe7ac429a5be` |
| `issue-5d-character-creation-catalogue-resolutions-DRAFTS.json` | sha256 `47167c97d16436905aee4149be1c56d1ee7cc98ea8778696bdec46bdc1597ae5` |
| `issue-5d-character-creation-catalogue-DELTA.txt` (full, 70 lines) | sha256 `d48ce267966e85bb218f0bdfe4b25a0e89d0363e40a43148cf0d011a4c556dc8` |

The candidate is one additive batch, `character-creation-catalogue`:

* **The part as a placed section.** It adds `character_creation.character_creation`
  (`general_rule`, no parent) on the part heading `# Character Creation`
  (@841, leaf `7eaded98…`).
  * It has one span, `fe74a641…` (0–20, substantive).
  * Its one component is prose-bound and heading-only, with reason
    `no_identified_structured_use`.
  * It has one unit, `character-creation-catalogue/character_creation`.
  * This is the shape of the recorded `animals.animals`.
  * Its placement omits the six sections' containers, so each member keeps
    its own placement.
* **Six `catalogue_member` edges**, one per accepted section. The actual
  source order is:

  | Position | Member |
  |---|---|
  | @843 | `character_creation.character_sheet` |
  | @846 | `character_creation.create_your_character` |
  | @942 | `character_creation.level_advancement` |
  | @964 | `character_creation.starting_at_higher_levels` |
  | @973 | `character_creation.multiclassing` |
  | @1006 | `character_creation.trinkets` |

  * Each edge carries one `contextual` provenance claim. The claim cites the
    member's first accepted `primary` span, found by the release's leaf order
    and char offset, and the generator asserts the six positions above.
  * The consumer orders members by that span.
  * The DELTA prints the relationship collection in its canonical key order,
    which puts `multiclassing` before `starting_at_higher_levels`. That is
    serialization order, not membership order.

The two drafts are applied in memory after the batch. Each resolves a
record-owned (`-`) reference that points at "Character Creation" in scope
`srd-5.2.1/character-creation`. Both target `character_creation.character_creation`:

* `resolve-glossary-character-sheet-record-character-creation-character-creation-catalogue-1`
  resolves `glossary.character_sheet`. Its provenance is the one span the
  oracle cites for the reference, `00b2af35-97d1-5651-b429-887254dcafcd`,
  which prints `_See also_ "Character Creation."`.
* `resolve-glossary-player-character-record-character-creation-character-creation-catalogue-1`
  resolves `glossary.player_character`. Its provenance is
  `78ab87ef-8471-54d0-968b-8ab25734d877`, which prints the same words.

The id form matches the six recorded record-owned resolutions, for example
`resolve-glossary-spell-attack-record-casting-spells-remaining-1`. Neither id
collides with the recorded 1438.

## Semantic delta

The delta is additive only: every collection shows 0 removed. By collection:

| Collection | Added |
|---|---|
| spans | 1 |
| review_units | 1 |
| obligations | 1 |
| reference_resolutions | 2 |
| records | 1 |
| components | 1 |
| relationships | 6 |
| prose_bindings | 1 |
| provenance | 7 |
| acceptance batches | 1 |
| acceptance records | 1 |
| review-unit records | 1 |
| resolution records | 2 |
| schema anchors | 1 |

`MC._preserved(old, new)` reports `[]`: no committed content is lost or
changed. The full delta, with text for every cited span, is in
`issue-5d-character-creation-catalogue-DELTA.txt`.

## Native validation

The candidate is accepted once with `accept_proposal`, under the simulated
reviewer, over `load_accepted_inputs(committed)`; the history is not rebuilt.
The drafts are then applied with `resolve_references`. Each state is checked
with `validate_candidate` on the bound release and with
`reference_resolution_violations`:

| State | batches, records, spans, units, resolutions | violations | reference, uncovered findings |
|---|---|---|---|
| accepted | 23, 1834, 10491, 1475, 1438 | 0 | 64, 0 |
| + candidate | 24, 1835, 10492, 1476, 1438 | 0 | 64, 0 |
| + drafts | 24, 1835, 10492, 1476, 1440 | 0 | 62, 0 |

* The batch alone moves no finding; the list is identical string for string.
* The drafts clear exactly two findings:
  `reference srd-5.2.1/character-creation:'Character Creation': unresolved reference`.
  No finding is new.
* The one remaining finding in this scope is #4, `glossary.hit_point_dice`
  (M-dynamic). It stays held.

## Consumer evidence (`apply_override_set`, via `RR.consumer`)

**Membership and reads.**

| Check | Result |
|---|---|
| Members before | none |
| Members after | the six, in the source order above |
| Direct read of `character_creation.character_creation` | `['# Character Creation']` |
| Its reading | 125 spans, each exactly once |
| Every other membership, reading and direct read (225, 225, 1834) | unchanged, including each member's own direct read |

The reading is the section's own span plus the 124 primary spans of its six
members' direct reads, each placed at its printed position.

**Overrides.**

| Override | Result |
|---|---|
| DISABLE `character_creation.multiclassing` | Members become the other five, in order. The reading is the full reading without that member's spans. |
| DISABLE `character_creation.character_creation` | The section leaves members, readings and direct reads. Everything else equals the accepted consumer state. |

REPLACE is not exercised. This packet makes no claim about it.

**Raw output.** The raw run output is in `.claude/_sp/ccc/run/write.txt`
(the `--write` run) and `.claude/_sp/ccc/run/check.txt` (the check-mode
rerun, EXIT 0). The generator asserts every line of evidence above.

## Decisions for the Owner and disclosures

1. **Two units cover the heading leaf @841.**
   * The accepted `framing-coverage/character_creation` unit excludes it as a
     part opening. The generator asserts that unit is kept byte-identical.
   * This batch adds its own unit and a substantive span over it.
   * No validator rule forbids two units on one leaf, or a span on a leaf
     another unit excludes. The merged candidate validates clean.
   * The framing packet left the heading open for a later catalogue. Whether
     the part-opening exclusion should stand alongside the catalogue is an
     Owner call.
2. **The edges are appended by a wrapper; acceptance is native.**
   * `EntryBatch.edges` must cite a span of the batch's own entry, and the
     members' spans belong to accepted batches. So the six edges and their
     claims are appended to the built proposal with `dataclasses.replace`, as
     `framing-coverage` appended its units.
   * On its own, the proposal's `relationship_and_reference_violations` is
     exactly six `unknown record` findings, one per member, and nothing else.
     The generator pins this.
   * `accept_proposal`, the merged `validate_candidate` and the consumer all
     admit the cross-batch `contextual` claims.
   * There is no native contract blocker.
3. **Held boundaries, untouched.**
   * #7 (Classes), #24, #35 (Equipment), #87 and #88 (Spells) would need to
     reach members nested in ordinary catalogues. ADR ordinary reach is one
     hop, and whole-component parents that overlap are refused.
   * This packet does not change traversal, ownership or aliases, and adds
     no fallback.
   * Every other multi-target, dynamic, OriginFeats and Spellbook residue
     stays separate.
4. **Source errata:** none encountered.
5. **Process disclosure.** One early read-only probe in Bash used `cd`, which
   breaks the standing rule. Every later call used absolute paths.

## Gates

* **Generator:** Black, Ruff and `mypy --strict` (`MYPYPATH=src`) are clean.
* **Tests:** none run. No `src/` or test file is changed, so no test is
  affected, and no test result is claimed.
* **Deferred, not green:** pip-audit and expanded mypy.
* **detect-secrets (`PYTHONUTF8=1`):** see the section below.

## detect-secrets baseline

* **How the scan was run.**
  * The scan was scoped to this packet's five files.
  * It used the baseline's own plugins and filters, with `PYTHONUTF8=1`.
  * It did not use `detect-secrets scan --baseline`.
* **What it found.**
  * The scan found 18 findings, and every value was recovered as a named
    public hash.
  * Generator: 1, the oracle's `ACCEPTED_SHA256`.
  * PROPOSAL: 6, the release-binding and policy hashes.
  * DRAFTS: 4, the release-binding hashes.
  * DELTA: 7, the release binding, `proposal_identity`, `schema_hash` and
    `semantic_diff_hash`.
  * The review document itself: 0.
* **What changed in the baseline.**
  * The 18 findings were added as new entries under the four files, with no
    other change.
  * 0 entries were pruned and 0 were moved.
  * The settings and all 142 prior files are byte-for-byte identical.
  * No `pragma: allowlist secret` was added.
* **Resulting baseline:** 146 files, 5777 entries, sha256
  `0df63f1ddd85f8019ab2c6c61c45e382193fc80593ca48e01e243ad687f41d60`, up from
  `127eba6cfa4a099388cfb90c1fc2ee0b93e828a17db07124c86d33691347e58d`. It is
  staged by name.
* **Hook runs.** The final affected-file hook runs are logged in
  `.claude/_sp/ccc/bl/hook.log`. Each runs twice with `PYTHONUTF8=1`, using
  paths relative to the repository root.
