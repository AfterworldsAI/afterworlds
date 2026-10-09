# `equipment-spell-references` review packet — CRD Issue 5d (#132, #137)

**Status: UNACCEPTED CANDIDATE.** Nothing here is accepted, recorded, staged, published or activated.
Exact Owner acceptance of this candidate is required before any recording.

**Authority.** The Owner authorization of the four Equipment/cursed-item references (rows 24, 35, 37,
46) and the nine spell references (rows 79–86, 89), with rows 34, 36, 39, 48, 54, 57, 60, 76, 87 and 88
deferred; the Codex reader-correction handoff (2026-10-03), applying existing authority without a new
Owner Decision; CRD Issue 5d; ADR-005d Decision 7 with its 24 August amendment (record-owned
references; effective-source retention). Row numbers are from
`issue-5d-current-reference-disposition-2026-10-03.md`. The original and corrective dispatch handoffs
exist in the current local coordination directory; candidate-work authorization is distinct from exact
candidate acceptance.

## Composition

| | |
|---|---|
| Constructor | `issue-5d-equipment-spell-references-CANDIDATE.py`, sha `623f0509812dc64872d09f8fa98d09b07b9b5a6f28b197cdb451933817bd6b7e`. `--write` writes the two artifacts; with no arguments it checks them |
| Accepted base | `srd-5-2-1-corpus-3fe24ff6-4e3.json`, sha `e9678ab30c27ba92deda5757de4be082aba8bfc44690b6bf94f7bc1f747a45ca`, schema 17. Not modified |
| Action | One native `resolve_references` call over the accepted artifact under the simulated reviewer. Additive: no batch is replaced. Not a recording |
| Candidate bytes (in memory, simulated) | sha `faa46e9c5f4668bad2ed5ad764fccd9f1f8fb2f9471f5986186523961e418290`; reload to the same bytes; persisted round trip True |
| Proposal | `issue-5d-equipment-spell-references-PROPOSAL.json`, sha `b9bf5638902b2384da3875963f4846d794339e3656efd2c8321c4c6094d8056d`, 778 lines |
| Delta | `issue-5d-equipment-spell-references-DELTA.txt`, sha `0e00a0d6cd7576ba43651f0b06d69062ed9e3ab7e40783b6bfc4ea48e2a8c601`, 121 lines |

These three hashes equal the original thirteen-reference run (cand3) byte for byte; the constructor
edits since then (lint wraps, a variable rename, and removing then restoring row 37) are output-neutral.

## Mappings

| Row | Citation (record / component / text) | Route(s) |
|---|---|---|
| #24 | `character_creation.create_your_character` / `starting_equipment` / "Equipment" | Equipment: the whole chapter, in printed order |
| #35 | `monsters.parts_of_a_stat_block` / `equipping_a_monster_with_other_items` / "Equipment" | Equipment: the whole chapter, in printed order |
| #37 | `play.exploration` / (record) / `See "Equipment" for rules on many items` | Equipment: the whole chapter, in printed order |
| #46 | `gameplay_toolbox.curses_and_magical_contagions` / `cursed_magic_items` / "Magic Items" | Four routes, `Cursed item: {name}` — Armor of Vulnerability, Berserker Axe, Demon Armor, Shield of Missile Attraction |
| #79–#86 | the Spellcasting / Pact Magic feature of Bard, Cleric, Druid, Paladin, Ranger, Sorcerer, Warlock, Wizard / "Spells" | Spellcasting rules: Gaining Spells, then Casting Spells |
| #89 | `glossary.spell` / `spell` / "Spells" | `spells.casting_spells` (single destination, plain target) |

The Equipment route is the chapter's fourteen `##` sections in printed order, Coins the landing; the
reader adds their one-hop catalogue members, so the read is all 147 `equipment.` records. The spell
route reads `spells.gaining_spells` then `spells.casting_spells` and its nine members, never
`spells.spell_descriptions`. `_sources` checks every group against the pinned markdown and the accepted
representation. The `magic_items.cursed_items` rule is not a #46 destination: the citation sends the GM
to the four cursed item descriptions, not to the general rule.

## Findings, counts, preservation

- Findings (refs, leaves): control (23, 0); Equipment and cursed items alone → (19, 0); all thirteen →
  (10, 0). The ten that remain are the deferred rows. No new reference or leaf finding.
- Counts (batches, …, resolutions): (24, 1835, 10493, 1476, 1463) → (24, 1835, 10493, 1476, 1476).
- Preserved verbatim: every accepted item, including the 1,463 resolutions and their 1,463 approvals
  and the 24 batches. Added: 13 `reference_resolutions` and 13
  `acceptance.reference_resolution_records`, simulated reviewer only.
- Fail-closed control: with the resolutions absent, every drafted citation is `INVALID_REFERENCE`
  (`test_the_control_refuses_every_drafted_citation`).

## Reader correction (Architecture Notes)

**Conformance to accepted Decision 7, not a new rule.** `issue-5d-core-play-completion-generator.py` records
`EQUIPMENT_POINTER` as record-grain supporting text of `play.exploration` and its "Equipment" pointer as
a record-owned reference (`SUPPORTING`, `RECORD_REFERENCES`). The accepted span `2e7f7342…` is
`SUPPORTING_AUTHORITY`, accepted, and bound as no component's prose. `citation_view` admitted citing spans
only through component `SourceProse`, so every citation read from record-level supporting text was
refused whatever it resolved to. That was a reader defect against the Decision 7 contract.

`RulesAuthorityService.citation_view` now partitions the cited spans:

- spans bound as governing prose in the projection must still be carried by the effective source.
  This is unchanged, whoever owns the citation;
- spans bound as no prose are admitted only when **all** of these hold:
  - the citation is record-owned;
  - every such span is `SUPPORTING_AUTHORITY` in the reconstructed classification ledger;
  - the source record is present;
  - no source record is supplied by an override (`supplied_by_override_id is None`).

A same-key REPLACE keeps the old `span_ids`, so they are never used as evidence. Nothing is fabricated:
no binding, no component, no re-keyed reference, no reclassification. The accepted oracle is not
mutated.

Residue: component-owned citations with unbound spans stay refused. So do citations with unbound spans
of any other disposition. See the sibling audit.

## Sibling audit (bounded)

**Defect family:** the citation reader's source-retention guard was blind to supporting text.
**Trigger:** the row 37 failures in `focused2.log`. **Census:** every resolved effective reference line in the accepted
oracle and the candidate, grouped by owner and by the kind of its citing spans. The script is
`.claude/_sp/esr/census.py`; its raw output is `census.log`, run on the final 13-row constructor.

| Accepted effective reference lines (distinct citations) | Owner | Citing spans | Disposition |
|---|---|---|---|
| 8146 (7851); candidate 8195 (7863) | component | governing prose | already safe. Unchanged guard: the spans must be in effective `SourceProse` |
| 135 (135); candidate 149 (136): #37 adds 1 citation, 14 lines | record | unbound `SUPPORTING_AUTHORITY` only | **patched**. Admitted while the source record is present and not override-supplied |
| 1 (`glossary.grappling` "Unarmed Strike") | record | `grapple_basis` prose + unbound supporting | **patched**. The prose part keeps the prose guard; the supporting part keeps the record guard |
| 1 (`glossary.grappling` "Grappled") | record | unbound substantive + unbound supporting | out of scope; later source-retention triage required. A substantive span bound as no prose has no admission path in the reader. Still refused |
| 18 (e.g. `play.d20_tests`/`add_modifiers` "Proficiency") | component | prose + unbound supporting | out of scope. Component-grain supporting retention was not authorized. Still refused |
| 16 (e.g. `glossary.dodge`/`benefits_lost` "Incapacitated") | component | unbound substantive | out of scope; later source-retention triage required. Still refused |
| 2 (e.g. `glossary.dehydration` "Exhaustion") | component | unbound substantive + supporting | out of scope; later source-retention triage required. Still refused |

The candidate's 12 component-owned rows add 12 component-prose citations and 49 effective lines. Every
other row has equal counts in the accepted oracle and the candidate.
The residue rows were refused before this change and are refused after it. Nothing out of scope was
fixed. No test locks them in.

## Tests

`tests/ingestion/mechanical/test_equipment_spell_references_candidate.py`, sha `00111b870eb8f0c3e9fcc45da20ff2695fa6ac283c4b7a69abc876063fc7f8b5`. It reads
through the actual persisted reader (`persist_draft` into a private release copy, then `citation_view`):

- **Row 37:**
  - the control refuses it;
  - it reads as drafted;
  - it reads the whole Equipment chapter (147 records, Coins first, sections in order).
- **`test_a_citation_whose_source_is_gone_is_refused`.** Each case first proves the citation resolves,
  then shows it refused under:
  - row 37: record DISABLE, and same-key record REPLACE;
  - "Unarmed Strike": record DISABLE, record REPLACE, `grapple_basis` component DISABLE, and
    `grapple_basis` prose DISABLE;
  - #24: `starting_equipment` component DISABLE, and prose REPLACE.
- **`test_an_unrelated_override_keeps_a_record_owned_citation`.** For row 37 and "Unarmed Strike", a
  prose APPEND on the citing record plus an unrelated record DISABLE still resolve, and both are
  reported as applied.

This task's `service.py` change has three parts:

- the `SemanticDisposition` import (line 38);
- in `citation_view`, `candidate = self._reconstruct(...)` replacing the inline `.representation`;
- the record-owned paragraph of the retention comment, and the `bound` / `supporting` / `unbound` /
  `record_text` guard with its rewritten `if` (lines 458–471).

The rest of the file's working-tree diff against HEAD predates this candidate and is unchanged by it.
That includes `_narrow`, `AuthorityResult.routes` and the rest of `citation_view`.

`src/afterworlds/services/rules_authority/service.py`, sha `4a33bf3c5f07120623c943b06f22e327f53d47dafba820677d5780b008877e2d`.

## Evidence (raw logs and exits in `.claude/_sp/esr/`)

| Run | What | Result |
|---|---|---|
| cand1, cand2 | early 13-row drafts | exit 1 (source anchor; single-destination shape), fixed |
| cand3 | 13-row `--write` | exit 0; the hashes above |
| cand4, cand5 | 12-row `--write` / check, row 37 retained | exit 0; **superseded** (`dbfb44a6…`, PROPOSAL `2e2752ee…`, DELTA `feef03e0…`, 23→20→11) |
| cand6 | 13-row `--write` after restoring row 37 | exit 0; byte-identical to cand3 |
| focused1 | whole test file | exit 2 (bad runner flags); no tests run |
| focused2 | whole test file, before the reader fix | exit 1: 39 passed, 2 failed (row 37 `INVALID_REFERENCE`) — the defect fixed here |
| focused3 | 12-row file | **aborted** by me before completion; no exit; not green |
| focused4 | targeted: row 37 ×3, the 8 retention cases, 2 unrelated-override cases, the #24/#79 destination-disable test, `test_reference_alternatives_candidate` source-gone ×4 and edit-keeps, `test_finite_reference_routes_candidate` destination-disable | exit 0: **20 passed** in 620.70 s. FOCUSED DIAGNOSTICS ONLY, not acceptance or full-gate evidence |

Black, Ruff and `mypy --strict` pass on the service, the constructor and the test file.

**Secrets baseline (working tree only, unstaged; index blob `4884b897` unchanged).** The six task files
were scanned under the baseline's own plugins and filters (`.claude/_sp/esr/bl/`). Eleven findings
were added, all Hex High Entropy flags on public hashes:

- the accepted-oracle sha `e9678ab3…`;
- the release binding's source, bundle-root, corpus-digest and transform-config hashes;
- the schema-17 hash, all present in the accepted oracle.

The additions are: constructor 1, PROPOSAL 6, DELTA 4. Nothing was pruned, and no settings or other
file's entries changed. `.secrets.baseline` moved from `6b3b3fbf…620a15b0` to
`5796c5ac…9144b44d`. No `pragma: allowlist secret` was added, and `scan --baseline` was not run.

## Not done / boundaries

- No recording, staging, commit, push, publication or activation. No shared-database write.
- The ten deferred citations are not drafted.
- The residue above is surfaced, not fixed.
- The full test file and the broad suite were not rerun. The 39 earlier passing diagnostics (focused2)
  cover the unchanged twelve mappings. The reader change affects only `citation_view`, and its targeted
  regressions are listed above.
