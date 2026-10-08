# CRD Issue 5d (#132, #137): finite reference atoms — UNACCEPTED candidate

**Status: not accepted, not recorded.** Nothing is committed, published or
activated. Exact Owner acceptance of the five proposals below is required
before any recording; no ACCEPT script exists.

## Authority and scope

- ADR-005d Decision 7: a citation is (source record, owning component, exact
  printed wording, scope). Decision 5: ownership unchanged.
- Authoring permits exact literal substrings of retained source; targets are
  record keys (record grain).
- Inventory: `issue-5d-remaining-references-review.md` rows 1–91; the 19
  M-list rows were inspected as one family.
- Consolidated Codex review corrections applied: #48 retained (incomplete
  source coverage); #6/#14/#15 assessed under the accepted singular
  spell-list authority and changed. All other held families stay held.
- Base: accepted `ea0c219feec8571142c797ebd127713d55595db7309c64670a1436756b4413de`,
  24 / 1835 / 10492 / 1476 / 1440, findings refs 62 / leaves 0. Baseline
  before this task `d7e9b2f79dac6b34901301a049d3697c85bdeab53f15c87fc01043cc2e5c5235`.

## Review point: retiring the chapter pointer

Rule applied: an unresolved chapter pointer ("see Monsters", "appear in Rules
Glossary") is removed from its component **only when every destination its
sentence prints has its own resolved citation identity in the same
component** (existing or added here). The chapter name is then the qualifier
of those destinations, not a further pointer. This extends the #34/#38
precedent ("the qualifier is not a second pointer"), which declined to author
a pointer, to removing one from an accepted proposal. A sentence that also
permits destinations it does not enumerate (#48: "one of the normal forms for
your familiar or one of the following special forms") is not covered by its
enumerated atoms, so its pointer stays. The Animals catalogue
candidate left #47/#63 open under a different rule (part-as-such); this
candidate does not touch them.

No citation carries two destinations, no empty edge remains beside a resolved
identity of the same wording, and nothing reads references as eligibility
(the rules-authority services do not read references; only the projection
does).

## Artifacts

| File | SHA-256 |
|---|---|
| `issue-5d-finite-reference-atoms-REPLACEMENT.py` (constructor) | `01b5d7669769c361bb17ee57bebfabf474e45614f6b60580cf70830044b34a12` |
| `issue-5d-classes-finite-reference-atoms-PROPOSAL.json` | `89061117d1b13c2823056a23e72720374e94b13c92f156b4b6d8703e11a73b54` |
| `issue-5d-character-origins-feats-finite-reference-atoms-PROPOSAL.json` | `8e5db24b651a53cf8da4300b8ab5d592d23a5670b4b4f81bcd0e2860ee023c83` |
| `issue-5d-spell-descriptions-finite-reference-atoms-PROPOSAL.json` | `fddde0cfbee8e8a4d2bc616bf553e90b648f56cd14a805c55cb1f087761659e6` |
| `issue-5d-magic-items-finite-reference-atoms-PROPOSAL.json` | `4aa393a42f93942f358e3012964b0b65432fd544be80fd3c2c2a2adeae3f97eb` |
| `issue-5d-monsters-finite-reference-atoms-PROPOSAL.json` | `f6ec2a0e7618e3267d95fa9343848b528a2b823e36e5ab02733867051a396c8c` |
| `issue-5d-finite-reference-atoms-DELTA.txt` (102 lines) | `50c2f78cf324eb7dac30b94591c8e6c0f3658caee1b539ea0241f334442cda25` |

The first-round class-option-catalogues candidate is deleted; the accepted
class-option-catalogues proposal is reused unchanged. The spell-descriptions,
magic-items and monsters candidates are byte-identical to the first round.

Proposal identities (candidate ← recorded):

| Batch | Candidate identity | Recorded identity |
|---|---|---|
| classes | `45c355850a7e74283f4556b0ab980244935c7a2e3d313a5fbb9cc7dc0a6a8b60` | `c98ed194f954eeec7c9005788192edba893512b1064ff6b38a4280812b9a2b03` |
| character-origins-feats | `17ed7fd338d2d52e77c227215e5f095aadfa0c50e918edd26d7b25277c87c813` | `8ce962407320ee246ec6d07ad51cddbff5b57d87fe966b3e73fc115f06bcd051` |
| spell-descriptions | `20ee428e126b8b33b1399ebddc21f27212609658672a0fdb4b5a6b6dabc955ca` | `737040bbd065f97f37f2438f23fe8827ebc31b2fa446a545f99be96ce9e6fafc` |
| magic-items | `48cb3c4726d395f06dd2ca639a50d001e5491b307fa3176618850d04ce04ca71` | `20e68a02a2dedfbeb43e56d505d216dc7d7b108b83a5dba589cc641c7da8c458` |
| monsters | `e39e622107d443713d17e25bc64f73210241af3f83d4cd86cf73132eaf4de327` | `791b52c3cc3f899e716bc22e5feb053d27d679ad49307cb9a041a88432e9c3f5` |

Resolution drafts: **none**. Rekeys: **none**. Every added atom is authored
with its target; every retired pointer was unresolved (`target ""`, asserted).
All 1440 accepted resolutions are kept verbatim (payload-equal).

Simulated composed state (in memory, never written):
`490ac660f7bb8e01cbed2053cb10ac46b00c2276ab4182ebe4bf626e30139b47`,
counts 24 / 1835 / 10492 / 1476 / 1440, violations 0, findings 52 / 0.

## Construction

One constructor, one build per changed batch. Each batch is rebuilt from its
recorded generator batch (magic-items and monsters through
`RR.candidate_batch` first, magic-items with `read_accepted`), then each edit
replaces the retired `(text, target)` pair in the component's `refs` in place
by the added atoms (none for pure retirements). Source prose, spans, units,
overrides, expectations and order are untouched; no record-owned reference
names a retired pointer (asserted).

The chain is the recorded one rebuilt from recorded evidence (`APC.composed`
extended through `REMAINING.resolved`, `ANIMALS_CATALOGUE.resolved`,
`FRAMING.composed`, `CHARACTER_CREATION.composed` + `.resolved` at their
recorded times), the five batches substituted under the simulated reviewer in
their recorded positions.

Controls (both runs):

```
control: classes rebuilds issue-5d-classes-REGEN-3fe24ff6-PROPOSAL.json True
control: character-origins-feats rebuilds issue-5d-character-origins-feats-REGEN-3fe24ff6-PROPOSAL.json True
control: spell-descriptions rebuilds issue-5d-spell-descriptions-REGEN-3fe24ff6-PROPOSAL.json True
control: magic-items rebuilds issue-5d-magic-items-remaining-references-PROPOSAL.json True
control: monsters rebuilds issue-5d-monsters-remaining-references-PROPOSAL.json True
control: the recorded chain rebuilds the committed artifact True
```

## Changes (10 retired, 16 added)

| Row | Record / component | Span | Retired | Destinations (identity → target) |
|---|---|---|---|---|
| #26 | `classes.monk` / `core_traits` | ffecf855 | `Equipment` | kept `Artisan's Tools` → `equipment.tools.artisans_tools`; kept `Musical Instrument` → `equipment.tools.musical_instrument` |
| #6 | `classes.bard.magical_secrets` / `magical_secrets` | d7211994 | `Bard, Cleric, Druid, and Wizard spell lists` | **new** `Bard` → `classes.bard`, `Cleric` → `classes.cleric`, `Druid` → `classes.druid`, `Wizard` → `classes.wizard` |
| #14 | `classes.bard.college_of_lore.magical_discoveries` / `magical_discoveries` | f800d93d | `Cleric, Druid, or Wizard spell list` | **new** `Cleric` → `classes.cleric`, `Druid` → `classes.druid`, `Wizard` → `classes.wizard` (existing `cantrip` → `glossary.cantrip` kept) |
| #15 | `feats.magic_initiate` / `two_cantrips` (character-origins-feats) | 647b8905 | `Cleric, Druid, or Wizard spell list` | **new** `Cleric` → `classes.cleric`, `Druid` → `classes.druid`, `Wizard` → `classes.wizard` |
| #56 | `spells.animate_dead` / `effect` | 07dc161d | `Monsters` | kept `Skeleton` → `monsters.skeletons.skeleton`, `Zombie` → `monsters.zombies.zombie` |
| #59 | `spells.create_undead` / `using_a_higher_level_spell_slot` | 44b9874b | `Monsters` | kept `Ghouls` → `monsters.ghoul.ghoul`, `Ghasts` → `monsters.ghast.ghast`, `Wights` → `monsters.wight.wight`, `Mummies` → `monsters.mummies.mummy` |
| #28 | `magic_items.crafting_magic_items` / `crafting_magic_items` | 58be38f3 | `Equipment` | **new** `brewing _Potions of Healing_` → `equipment.brewing_potions_of_healing`; **new** `scribing _Spell Scrolls_` → `equipment.scribing_spell_scrolls` (the crafting rules, not the items; the existing item atoms are kept) |
| #31 | `magic_items.folding_boat` / `folding_boat` | 9fc720fe | `Equipment` | kept `Rowboat` → `equipment.mounts_and_vehicles.rowboat`, `Keelboat` → `equipment.mounts_and_vehicles.keelboat` |
| #74 | `monsters.parts_of_a_stat_block` / `speed` | fa7f80a7 | `Rules Glossary` | kept `Speed` → `glossary.speed`; **new** `Burrow` → `glossary.burrow_speed`, `Climb` → `glossary.climb_speed`, `Fly` → `glossary.fly_speed`, `Swim` → `glossary.swim_speed` ("the following speeds": the speed entries, not `glossary.climbing`/`swimming`) |
| #75 | `monsters.parts_of_a_stat_block` / `spellcasting` | 5bbea148 | `Rules Glossary` | kept `Magic action` → `glossary.magic`, `Concentration` → `glossary.concentration` |

Printed sentences (from the spans): #26 "Choose one type of Artisan's Tools or
Musical Instrument (see Equipment)"; #6 "...choose any of your new prepared
spells from the Bard, Cleric, Druid, and Wizard spell lists, and the chosen
spells count as Bard spells for you (see a class's section for its spell
list)"; #14 "These spells can come from the Cleric, Druid, or Wizard spell list
or any combination thereof (see a class's section for its spell list)"; #15
"You learn two cantrips of your choice from the Cleric, Druid, or Wizard spell
list."; #28 '"Equipment" contains rules on
brewing _Potions of Healing_ and scribing _Spell Scrolls_.'; #31 'Statistics
for the Rowboat and Keelboat appear in "Equipment."'; #56 'a
**Skeleton** ... or a **Zombie** ... (see "Monsters" for the stat blocks)';
#59 '...**Ghouls** ... **Ghasts** ... **Wights** ... **Mummies**. See
"Monsters" for these stat blocks.'; #74 'Some monsters have one or more of the
following speeds: Burrow, Climb, Fly, Swim. Rules for Speed and these specials
speeds appear in "Rules Glossary."'; #75 '...must take the Magic action ...
maintain Concentration ..., as described in "Rules Glossary."'. The source's
"specials speeds" typo is retained verbatim (not a cited text).

#6/#14/#15 authority: the accepted classes generator targets a singular
"<Class> spell list" at the class record (`issue-5d-classes-generator.py`
POINTERS, lines 541–549) and places each class's Spell List on that record
(`spell_list`, `cantrips`, `level_N` components, lines 941–950); #6/#14 print
"see a class's section for its spell list". A multi-class list stayed
unresolved only because one reference takes one target; one atom per printed
class removes that limit without a generator, schema or ownership change. The
choice conditions ("any combination thereof", "count as Bard spells", the
slot and cantrip limits) stay in the unchanged prose. Disclosures: "Bard"
appears four times in d7211994 (Bard level, Bard Features table, the list,
Bard spells); the one `Bard` identity cites the component, and every
occurrence names the Bard class, whose record holds the list. The `Bard` atom
is a Bard-record component citing its own class record. The generator
comment naming *Magic Initiate* as a kept unresolved case describes the
recorded proposal and is not edited.

#28 note: these are the first accepted source texts containing `_`; the
authoring substring check strips only `**`, and the exact texts matched the
span as printed, so the build accepted them without any normalization. Each
new text contains the wording of an existing item atom in the same span
(`Potions of Healing`, `Spell Scrolls`): distinct exact wording, so distinct
identities with distinct targets (the crafting rule versus the item). The
item atoms are unchanged.

## Evidence (checks asserted by the constructor)

- **Proposal delta** (per batch, references and provenance, all other
  collections empty): classes −3/+7; character-origins-feats −1/+3;
  spell-descriptions −2/+0; magic-items −2/+2; monsters −2/+4.
- **State delta** (`DELTA.txt`): `representation.references` −10 +16,
  `representation.provenance` −10 +16, `acceptance.batches` −5 +5 and
  `acceptance.schema_anchors` −5 +5. The batch records and anchors differ only
  in `proposal_identity`, `semantic_diff_hash`, `diff` (asserted); each new
  `proposal_identity` equals the candidate file's. Records, spans, units,
  resolutions: unchanged.
- **Identities.** Per edit: the retired key is present before and absent
  after; each destination has exactly one identity in the component with a
  non-empty target and is printed in the cited sentence; each new atom's
  provenance cites exactly that span. The other 8030 citation identities keep
  their targets.
- **Findings** (multisets): 62 / 0 → 52 / 0; cleared exactly
  `{srd-5.2.1/classes:'Bard, Cleric, Druid, and Wizard spell lists': 1,
  srd-5.2.1/classes:'Cleric, Druid, or Wizard spell list': 2,
  srd-5.2.1/equipment:'Equipment': 3, srd-5.2.1/monsters:'Monsters': 2,
  srd-5.2.1/rules-glossary:'Rules Glossary': 2}`; nothing new; violations 0.
- **Native projection.** `candidate_from_accepted_inputs(final)` projects the
  16 new atoms to their target records (each an accepted record);
  `identify_projection` → `c66f56d2-570d-55b2-ad2d-19268f6baee4`.
- **Preservation.** `RR.owned` (prose bindings) and `RR.expectations`
  (reviewed expectations) equal before/after. The consumer reading (members,
  readings, direct reads via `apply_override_set`) is equal with no override,
  with `disable-magic_items.folding_boat-record`, and with
  `disable-monsters.parts_of_a_stat_block-speed`; under the latter the speed
  component's spans are absent from direct reads. Consumer equality is
  supporting evidence only; the source and navigation reading above is the
  deciding proof.
- The committed oracle is byte-unchanged (`ea0c219f…`) before and after.

## M-list family (19 rows) dispositions

| Row | Disposition | Reason |
|---|---|---|
| #6, #14, #15, #26, #28, #31, #56, #59, #74, #75 | **Changed** (above) | every printed destination has its own resolved identity |
| #48 | Retained | incomplete source coverage: the sentence permits "one of the normal forms for your familiar **or** one of the following special forms"; the seven atoms cover only the specials, and Find Familiar's other CR 0 Beast option is reached only through an unresolved indirect citation |
| #13, #16, #21 | Retained (held) | the sentences ("A Cleric or Paladin can use a Holy Symbol as a Spellcasting Focus"; Druid or Ranger; Sorcerer, Warlock, or Wizard) state who may use the focus: a use condition with no navigation cue to a class section. The rule it applies is each class's Spellcasting feature, which the printed class name does not name; citing the class record would present an eligibility statement as navigation. Not reassessed beyond this |
| #68, #69, #70 | Retained (held) | 'detailed in / see "Playing the Game"' for ability scores, modifiers, saving throws, AC, Initiative and Hit Points; not reassessed this round |
| #71 | Retained (held) | "different kinds of attacks": ambiguous scope |
| #73 | Retained | "any special senses" is unenumerated; Passive Perception alone would leave the pointer beside a partial set |

The first round's "component-target contract boundary" for #6, #13–16, #21
and #68–70 is withdrawn: the accepted singular spell-list authority disproves
it for #6/#14/#15, and it is not the reason for any row held above.

## Remaining findings (52) dispositioned

| Rows | Count | Disposition |
|---|---|---|
| #79–86 "See Spells for rules on spellcasting" | 8 | Held: Casting Spells alone excludes Gaining Spells; await reconciled whole/compound authority |
| #37 (2e7f7342 `See "Equipment" for rules on many items`) | 1 | Held: whole-chapter case with the other ancestor-catalogue cases |
| #34 (2909e2fc `a purchase cost in "Equipment"`) | 1 | Held: dynamic item cost |
| #38 (32591758 `see "Equipment" for descriptions`) | 1 | Held: applicable focus |
| #54 (`the stat block is in "Monsters."`; `How to read and use a stat block is explained in "Monsters."`) | 2 | Held: dynamic creature; the second names two 18pt sections, with no record-grain single target |
| M-list retained: #13, #16, #21, #48, #68, #69, #70, #71, #73 | 9 | As above |
| M-set: #17–20, #22, #46, #49, #76, #89 | 9 | Retained: unenumerated sets |
| M-dynamic: #4, #8–12, #23, #36, #51–53, #55, #57, #60 | 14 | Retained: chosen at play (#4 stays held) |
| U-part: #7, #24, #35, #87, #88 | 5 | Retained: the part as such (nested-catalogue reach boundary) |
| #39 Spellbook | 1 | Held deferral |
| #40 Origin Feats | 1 | Held (K-contract) |
| **Total** | **52** | |

No aliases, inferred runtime filters, generic Book substitution, recursive
catalogue policy or eligibility change.

## Gates

- Constructor: Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0.
- Corrected `--write` run EXIT 0 (`.claude/_sp/fra/write2.txt`); verify-only
  run on the final constructor bytes EXIT 0 with identical output
  (`.claude/_sp/fra/verify2.txt`). First-round logs (`write.txt`,
  `verify.txt`) are superseded.
- Not run: pytest (no test changed; no accepted artifact changed), broad
  suite, pip-audit, expanded mypy. Not claimed green.
- detect-secrets: scoped rescan (`PYTHONUTF8=1`, the baseline's own plugins
  and filters) of the eight current files. Each candidate proposal's hashes
  equal exactly the set baselined for its recorded proposal file (classes 583,
  character-origins-feats 6, spell-descriptions 269, magic-items 6, monsters
  6); DELTA 16 (`proposal_identity`, `schema_hash`, `semantic_diff_hash`);
  constructor 1 (`ACCEPTED_SHA256`); this packet 0. Baseline
  `68349c3ec5f4ee16c9e6170fae1bfb8cab8e53ab0d7845b1df02c0e6deb1f0df` →
  `1c08091d2f8c38ddbf30d9e7345e7b93b55b6a9d6b842bf9622cbbc3a9b50508`:
  added 10 (feats candidate 6; DELTA 4 public proposal identities and a
  semantic diff hash), pruned 10 (deleted class-option-catalogues candidate 6
  and its key; DELTA 4 superseded), line refreshes only in the constructor,
  classes candidate and DELTA; settings, filters, `generated_at` and every
  other file's entries identical. Staged by name. Hook run twice on the eight
  files: see `.claude/_sp/fra/bl/hook2.log`. Evidence: `.claude/_sp/fra/bl/`
  (`scan2.json`, `baseline-delta2.json`).
- No test enumerates review-notes proposal files (the only globs are over the
  oracles directory), so the five unaccepted candidates reach no test.

## Not done

No recording, acceptance, commits, push, publication or activation. No
source errata encountered.
