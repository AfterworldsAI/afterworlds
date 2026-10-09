# CRD Issue 5d — rules-glossary-completion — semantic review packet (UNACCEPTED)

Status: **proposal only, UNACCEPTED.** Nothing is accepted, recorded, published or written under
`oracles/`. No resolution draft. The coordinating Codex's full independent review, against the
official source and this batch, is **still pending**; this packet is not reviewed and not accepted.

## Settled final delta (Phase 6)

- **Truncated citation fixed.** *Hit Point Dice* cited `glossary.hit_points` with the source text
  `'Hit Point'`, which was cut out of "Hit Point maximum".
  - `GLOSSARY_TERMS` now leads with `("Hit Point maximum", "hit_points")`, so the whole phrase is cited
    at char 75 → `glossary.hit_points`.
  - The accepted character-origins-feats generator cites this phrase the same way.
  - Source meaning is unchanged. No other citation changed. The counts are unchanged: 121 references
    and 90 findings.
- **Matcher-family sweep.** Every glossary-term match in this batch was checked for a longer compound
  term continuing after it; the log is `.claude/_sp/gl_matchctx_{before,after}.log`.
  - This was the only truncation.
  - *Knocking Out*'s "1 Hit Point." is a complete singular phrase, and that component cites "Hit Points"
    first anyway.
  - *Reaction*'s "Opportunity Attack" is complete.
  - No accepted material was audited.
- **Pins.**
  - The proposal and the test `IDENTITY` were regenerated.
  - The test now also pins *Hit Point Dice*'s citations and that no reference cites a bare "Hit Point".
- **Dispositions, unchanged in substance.**
  - "Casting Spells" stays unresolved and is recorded as an after-5d structural follow-up (see below).
    It is not an Owner decision, and accepted spellcasting is not altered.
  - The batch residue safeguard, which catches rule words lost beside *See also*, is retained.
  - The shared review-unit coverage improvement is a documented after-5d follow-up.

## Artifacts

| Artifact | Identity |
|---|---|
| Generator `.claude/review-notes/issue-5d-rules-glossary-completion-generator.py` | literal review data over the committed `authoring.py` (no changes to production Python) |
| Proposal `.claude/review-notes/issue-5d-rules-glossary-completion-REGEN-626c83f8-PROPOSAL.json` | 225,813 bytes; `proposal_identity` `6cafaf579049783f32566cc695a5171f7809ebcf6bb8524129fbca05edfece16`; file SHA-256 `b31621c0bf97834dad28e136ad6516687d63010cf675ab87226d1527787658bd` |
| Test `tests/ingestion/mechanical/test_rules_glossary_completion_proposal.py` | 33 tests |
| Release | `0b1a965e-28bd-55e6-ac13-bc7786a1bace` / `5.2.1-corpus.626c83f8-209` |
| Prior (unchanged) | committed oracle SHA-256 `c5971b894a0e0f76bbb89956232cd2cddd306099002bb4079fe733641571572f`: 14 batches, 235 records, 1497 spans, 50 resolutions |

## Scope and coverage

- **60 entries, 133 leaves** (60 `####` headings and 73 body leaves). These are every *Rules Definitions*
  entry that none of the 14 accepted batches authors. *Improvised Weapons* is included.
  Each entry gets one ENTRY review unit and one `glossary_rule` record, in printed order.
- **Source qualification.** All 73 body leaves were read and checked against the official SRD 5.2.1 PDF,
  pp. 176–191. That covers wording, table grouping, qualifiers, run-in rules and reading order.
- **Composed with the committed oracle (test only).**
  - Exactly these 133 leaves gain coverage.
  - Two leaves of *Rules Definitions* (occurrences 7866–8349) stay unowned: its heading (7866) and its
    one-line introduction (7867).
  - The 95 accepted glossary entries plus these 60 give 155, which is every entry.
- **Not authored.**
  - *Glossary Conventions* (7858–7865). It describes how the glossary is written (tags, "you", *See also*,
    obsolete terms, abbreviations) and states no rule.
  - Individual spells, classes, monsters and magic items. Where the glossary names one, it is an example
    only: *Remove Curse*, *Greater Restoration*, *Polymorph*, *Protection from Evil and Good*,
    *Dispel Evil and Good*, Wild Shape, a Club.
- **Accepted material is an input only.** No accepted leaf, record, identity or byte is touched.

## Representation

- **72 components.** Each is one per printed leaf-rule, and all are `prose_bound` with no facts.
  - Multi-rule entries follow the PDF's run-in rules:
    - *Heroic Inspiration*: 2
    - *Illusions*: 2
    - *Improvised Weapons*: 5 (definition, Proficiency, Damage, Range, Weapon Equivalents)
    - *Knocking Out a Creature*: 2
    - *Telepathy*: 3
    - *Teleportation*: 4
  - *Action*'s table is the release's own headless 3×4 table, placed after the entry's prose. The PDF
    prints the same twelve actions in columns.
- **Reason codes.**
  - `gamemaster_latitude` (5):
    - *D20 Test* (whether a test is warranted)
    - *Ally* and *Enemy* (who counts is the GM's designation)
    - *Improvised Weapons* Damage and Weapon Equivalents
  - `contextual_applicability` (2):
    - the *Improvised Weapons* definition (what is being wielded against its design)
    - *Illusions* in space
  - `no_identified_structured_use`: the other 65.
  - Note: *Simultaneous Effects* hands the ordering to whoever's turn it is, so it is not GM latitude.
- **See-alsos.** All 42 *See also* sentences are record-owned supporting spans. A partial-leaf span is
  used where the sentence shares a leaf with the rule.

## References (121 drafted)

- **See-also targets.**
  - A glossary entry points to its record.
  - "Playing the Game" ("X") points to the accepted `play.*` section X.
  - "Equipment" ("Armor" / "Magic Items" / "Weapons") points to `equipment.armor`, `equipment.magic_items`
    and `equipment.weapons`.
- **Equipment rules named in the definitions**, following the accepted Equipment batch's citations:
  - "Simple" → `equipment.weapons.category`
  - "Ranged weapon" → `equipment.weapons.melee_or_ranged`
  - "Thrown property" → `equipment.weapons.thrown`
  - "Light" → `equipment.armor.category`
  - "Shield" → `equipment.armor.shield`
- **Spells rule.** *Spellcasting Focus*'s "Material components" → `spells.components`.
- **Glossary terms.** Each is cited from prose only, by its printed name, once per component. An entry
  never cites itself. A compound name is cited whole: *Hit Point Dice* cites "Hit Point maximum"
  → `glossary.hit_points`, never the truncated "Hit Point".
  - The *Action* table cites its twelve actions. The entry calls them "defined elsewhere in this
    glossary".
  - Everyday words are not cited, and neither is "Proficiency Bonus", which no entry defines.
- **NPC.** *Monster*'s "NPC" → `glossary.nonplayer_character`. That entry defines the abbreviation, and
  the Conventions abbreviation table expands NPC to "Nonplayer character".
- **Improvised Weapons.** Equipment's accepted citation already targets
  `glossary.improvised_weapons`. That citation closes by key once this batch is accepted, so no
  resolution draft is needed.

### Unresolved external citations (preserved explicitly — 8)

| From | Printed | Scope |
|---|---|---|
| *Cantrip*, *Ritual* (see-also); *Spell* (component) | "Spells" | `srd-5.2.1/spells` |
| *Spell Attack*, *Spellcasting Focus* (see-also) | "Casting Spells" | `srd-5.2.1/spells` |
| *Character Sheet*, *Player Character* (see-also); *Hit Point Dice* (component) | "Character Creation" | `srd-5.2.1/character-creation` |

"Spells" and "Character Creation" name a whole part. The accepted batches leave such pointers unresolved,
and so does this one. An accepted `character_creation.character_sheet` record exists, but the pointer
names the part, not that record.

### Known structural defect — "Casting Spells" (not corrected here)

- **The defect.**
  - In the official PDF, *Casting Spells* is an 18-pt heading that contains the sections *Casting Time*
    through *Combining Spell Effects* (14/12 pt). Those include *Components* and *Attack Rolls*, which
    *Spell Attack* and *Spellcasting Focus* rely on.
  - The release makes those sections siblings of *Casting Spells*, and the accepted spellcasting batch
    follows the release. So `spells.casting_spells` is narrower than the section the pointer names.
- **Consequence.**
  - Resolving the two pointers to `spells.casting_spells` would silently narrow them.
  - They therefore stay unresolved: 2 of the 8 above.
  - This does not block the batch.
- **Structural follow-up (after 5d; not an Owner decision now).**
  1. Add a container relationship or record for the PDF's whole *Casting Spells* span, *Casting Time*
     through *Combining Spell Effects*.
  2. Then resolve these two pointers to it.

  Until then, leaving them unresolved is correct, because the available record is narrower. Accepted
  spellcasting is not changed here.

## Consumer behaviour (production seams, test-only, in memory)

- **GameMaster view.** Every component appears once. Records are in key order. Within a record,
  components and passages are in printed order, with each clause's text whole.
- **Rules-authority service, on a private DB copy.** For *Improvised Weapons*, *Teleportation*,
  *Telepathy* and *Action*:
  - each entry reads its rules in printed order, where key order would differ;
  - narrowing to some components keeps printed order;
  - a disabled record stays gone (`INVALID_REFERENCE` on direct read);
  - a replaced component reads as replaced, in its printed place;
  - an authored addition reads after the source rules.
- **`accept_proposal`.** It succeeds in memory over the committed oracle: 295 records, 50 resolutions
  unchanged, the *Improvised Weapons* unknown target closed, and no span left unaccepted. Oracle files on
  disk are byte-identical before and after.
- **Recorded resolutions.** The 50 recorded resolutions still apply to the composed representation.

## Findings

- **Batch alone: 90 representation findings, as expected.**
  - 82 are accepted out-of-batch targets. They are unknown to the batch on its own and close when
    composed.
  - 8 are the unresolved citations above.
  - Partition and review-unit findings: 0.
- **Composed: 66 reference findings.** That is 59 prior − 1 (*Improvised Weapons*) + 8.
- **Framework gap (surfaced, not fixed).** The shared review-unit check treats a leaf as claimed if any
  supporting span touches it. So a rule dropped from a leaf that also holds its *See also* is not reported
  there; *Weapon Attack* is pinned as the example. The test file's residue check catches the leftover
  words, so this batch is covered. That residue safeguard is retained. Every accepted glossary batch
  shares this leaf pattern.
  - Documented after-5d follow-up: review-unit leaf coverage should count PRIMARY component spans only,
    not SUPPORTING ones.
  - That change is in production `authoring.py`. No production rewrite or hunt through the accepted
    corpus is done now.
- **Retention.** No review-notes file was retired, because this batch supersedes no existing artifact.
  The only things removed were this run's own scratch codegen fragments in `.claude/_sp/`.
- **Dropping the *Action* table fails loudly** ("'Attack' … cites no clause"). That is the intended
  behaviour.

## Gates (this working tree; logs in `.claude/_sp/gl_gate_*.log`)

| Gate | Result |
|---|---|
| pytest: new test file on its final bytes (`--no-cov`), Phase 6 | 33 passed (`gl_gate_pytest_phase6.log`) |
| pytest: `test_spellcasting_acceptance.py`, which pins the oracle through the resolver | Phase 5: passed in a 38-pass run. Not rerun, because no input it reads changed. |
| Black `--check` (generator, test), Phase 6 | clean |
| Ruff (generator, test), Phase 6 | clean |
| mypy `src/` (strict) | Phase 5: no issues, 235 files. Not rerun, because no `src/` change. |
| detect-secrets hook, run on a temporary copy of the baseline (copy deleted), Phase 6 | the same 8 flags, all public hashes (see below). `.secrets.baseline` unchanged at `4554f802…efb2f`. |
| CR check, Phase 6 | 0 `\r` in generator, proposal, test and this packet |
| Protected state | oracle `c5971b89…572f`; baseline `4554f802…efb2f`; REPLACEMENT-PACKET `e462e235…cae1` untouched; 4 stashes |
| Full suite / coverage | not run. Per-file runs use `--no-cov`, so there is no full-suite claim. pip-audit 31/11 remains deferred and non-green. |

**New public-hash detect-secrets findings, for later Owner terminal reconciliation.**

- **Proposal JSON, lines 7943–7954 (release binding):**
  - `authoritative_source_hash`
  - `bundle_root_hash`
  - `persisted_corpus_digest`
  - `transform_config_hash`
  - ledger `hash`
  - `semantic_policy_hash`
- **Test file:**
  - line 118: `IDENTITY` (proposal identity)
  - line 125: `ORACLE_SHA256`

No pragma was added and no baseline was written.

## Questions for Codex

1. Is every clause text the governing prose of its record, with run-in rules split where the PDF
   splits them?
2. Are the five `gamemaster_latitude` components and the two `contextual_applicability` components
   correct, and are there no others?
3. The *NPC* → *Nonplayer Character* target: is it correct?
4. Are any glossary-term citations missing, or are any spurious? See `GLOSSARY_TERMS` and the
   per-component dump in the test's references section.

The earlier questions on "Casting Spells" and the *Hit Point* truncation are settled; see the settled
final delta above.
