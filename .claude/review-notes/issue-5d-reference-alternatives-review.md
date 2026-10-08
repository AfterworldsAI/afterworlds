# Issue 5d — Reference routes: consolidated review packet

CRD Issue 5d (#132, #137). **UNACCEPTED CANDIDATE.** This packet records nothing as accepted. It does not
publish, activate, commit or push anything. It covers the thirteen remaining inventory findings #4, #7–12,
#17–20, #22 and #40 from `issue-5d-remaining-references-review.md`, under the Owner Decisions of 2026-10-01:

- *"Okay, do that then."* approves one identity per feat, with class-labelled destinations.
- *"You might as well do the other ones we worked on as well with this batch (if that's reasonable)."*

This revision applies the consolidated correction to that batch: routes instead of exclusive alternatives,
actual target coverage, governing caveats as source, #7 implemented, #40 finished, the schema trust seam,
the selection fix with a narrow reader, and a native lift-plus-resolve action. Claude Code is the engineer
and Codex reviews. The exact final candidate must be accepted before anything is recorded. The Owner
requires one bounded order pass after the packets and before publication.

## 1. Result

| | |
|---|---|
| Accepted oracle (unchanged) | `srd-5-2-1-corpus-3fe24ff6-4e3.json`, SHA256 `5f37fb080a8493a1acb6584ef9bd2297c388d34683200bd7f486007ade668676`. Counts 24/1835/10492/1476/1440. |
| Lifted 16→17, no decision | `9c34a8809a004201b91dbc283fd1932a5c9c6938c3f3b2e929b49d26b75e70b2` (the same bytes as the previous manual lift, now produced by the native action) |
| Candidate (lift + 13 resolutions in one action, simulated reviewer) | `f5721870b057f6455b98ca17f9455ddfdab1c8207fa65b1181e98e6467dd0439`. It reloads to identical bytes. |
| `issue-5d-reference-alternatives-PROPOSAL.json` | `17c5ac2562d5c67bd6434290fa3affddc86d6cd1721b4c654eb76bcbb677b7f0` (1861 lines) |
| `issue-5d-reference-alternatives-DELTA.txt` | `7e5de293c33b91e80346d4b263cc90d76a6d9eb74efedd0fb2a3e8dddfaf9bf0` (210 lines: 13 `-`, 197 `+`) |
| Representation schema | 17, hash `4881e51fb2fa73e52f7ff951ad7d00b863188c1a22133fb0e2873c7d32d10ada` (unchanged by this correction), lift `5d-lift-schema-16-to-17` |
| Derived publication findings | (46 reference, 0 uncovered) → (33, 0). 13 cleared, 0 new. |
| Resolutions / routes / destinations | 13 / 132 / 197 |
| Persisted round trip | True. The candidate was persisted to a temporary copy of the scratch DB (built with `Base.metadata.create_all`) and reconstructed to the same identity. |

The counts are derived, not promised. The harness is
`.claude/review-notes/issue-5d-reference-alternatives-REPLACEMENT.py`. Running it without arguments checks
the PROPOSAL and DELTA byte for byte; `--write` regenerates them.

## 2. Dispositions and exact mappings

A **route** is the set of destinations sharing one label within a citation. Its members are read together in
the stated order: the first is where the reader lands, and the rest is supporting text that route needs.
Routes are not exclusive, and no class has to qualify. Every destination is a record, and where stated a
component, that the accepted authority already contains. No record or component was minted. Each feat keeps
one identity.

Notation:
- `K` ranges over the 12 classes: barbarian, bard, cleric, druid, fighter, monk, paladin, ranger, rogue,
  sorcerer, warlock, wizard.
- `CC` = `character_creation.create_your_character`, `LA` = `character_creation.level_advancement`,
  `MC` = `character_creation.multiclassing`, `AMC(K)` =
  `classes.K.as_a_multiclass_character/as_a_multiclass_character`.
- `classes.K` without a component is the **whole class**: the record plus, one `CATALOGUE_MEMBER` hop away,
  the records it prints, which are its table and its Level N feature descriptions.
- Situations: INITIAL, LATER, ENTERING, ADVANCING, SINGLE, MULTI.

| # | Citation (record / component, "wording", scope) | Routes / destinations | Routes, members in reviewed order |
|---|---|---|---|
| 4 | `glossary.hit_point_dice` / `hit_point_dice`, "Character Creation", character-creation | 2 / 3 | INITIAL: [`CC/hit_points`]. LATER: [`LA/hit_points_and_hit_point_dice`, `MC/hit_points`]. The multiclass rule keeps the fixed value and the minimum, and a new class's first level does not restart first-level hit points. |
| 7 | `CC/choose_class`, "Classes", classes | 13 / 13 | "Class Overview table (summary of every class)": [`CC/choose_class`]. Per K: "K (details)", class K: [`classes.K`]. |
| 8 | `CC/class_features`, "Classes", classes | 24 / 36 | Per K, INITIAL, class K: [`classes.K`]. Per K, ENTERING, class K: [`AMC(K)`, `classes.K`]. |
| 9 | `CC/class_proficiencies`, "Classes", classes | 24 / 48 | Per K, INITIAL, class K: [`classes.K/as_a_level_1_character`, `classes.K/core_traits`]. Per K, ENTERING, class K: [`AMC(K)`, `classes.K/core_traits`]. |
| 10 | `LA/class_features`, "Classes", classes | 24 / 36 | Per K, ADVANCING, class K: [`classes.K`]. Per K, ENTERING, class K: [`AMC(K)`, `classes.K`]. |
| 11 | `LA/proficiency_bonus`, "Classes", classes | 13 / 14 | Per K, SINGLE, class K: [`classes.K/progression`]. MULTI: [`LA/character_advancement`, `MC/proficiency_bonus`]. |
| 12 | `MC/proficiencies`, "Classes", classes | 12 / 24 | Per K, ENTERING, class K: [`AMC(K)`, `classes.K/core_traits`]. |
| 17 | `feats.archery/category`, "Fighting Style Feature", classes | 3 / 3 | "Fighter level 1" [`classes.fighter.fighting_style/fighting_style`], fighter ≥ 1. "Paladin level 2" [`classes.paladin.fighting_style/…`], ≥ 2. "Ranger level 2" [`classes.ranger.fighting_style/…`], ≥ 2. |
| 18 | `feats.defense/category`, same | 3 / 3 | Same as #17 |
| 19 | `feats.great_weapon_fighting/category`, same | 3 / 3 | Same as #17 |
| 20 | `feats.two_weapon_fighting/category`, same | 3 / 3 | Same as #17 |
| 22 | `feats.boon_of_spell_recall/category`, "Spellcasting Feature", classes | 7 / 7 | "K level 1: Spellcasting" [`classes.K.spellcasting/spellcasting`], class K ≥ 1, for bard, cleric, druid, paladin, ranger, sorcerer and wizard |
| 40 | `gameplay_toolbox.creating_a_background/step_2_choose_a_feat`, "Origin Feats", feats | 1 / 4 | "Origin Feats (examples; not every Origin feat)": [`feats.alert`, `feats.magic_initiate`, `feats.savage_attacker`, `feats.skilled`] (§4) |

How the correction reads the source:
- **Coverage (#8–10).** A class route reads the whole class: its table and its feature descriptions. It no
  longer reads only `progression` and the `class_features` heading. The reader proves this on the real
  candidate: entering Paladin reaches more than two `classes.paladin.*` feature records (§6).
- **Grant instructions (#9).** The core table is read together with the instructions that grant from it:
  "As a Level 1 Character" when initial, and "As a Multiclass Character" when entering.
- **Multiclass entry (#8–10, #12).** Entry follows "As a Multiclass Character", which also covers creating
  a higher-level multiclass character. Entry never grants all Core Traits. Later progression stays based on
  class level (ADVANCING reads the class, not the multiclass instructions).
- **Caveats are source, not labels (#4, #11).** MULTI reads the Character Advancement table together with
  `MC/proficiency_bonus`, which states the total-character-level rule. The LATER route reads
  `MC/hit_points` together with the level-advancement rule. Labels say no more than the route's
  destinations already say.
- **#7** lands on the Class Overview table in `CC/choose_class`, plus one route per class. This was
  already decided, so no Owner confirmation is requested.

Source verification, from the pinned `classes.md`:
- **Fighting Style** is granted at Fighter level 1 (line 4713), Paladin level 2 (5576) and Ranger level 2 (6360).
- **Spellcasting** is granted at level 1 at lines 824, 2146, 3416, 5552, 6321, 7530 and 10144.

Exclusions, each verified against its granting description:
- The Champion's *Additional Fighting Style* (4801) is a different feature from a subclass, and is not the
  cited Fighting Style feature.
- Warlock *Pact Magic* (8909) is not Spellcasting. Class membership alone satisfies neither prerequisite.

Routes direct a reader to the governing text. They do not decide eligibility, so a feat is never equated
with the feature. #22's **Level 19+** prerequisite is preserved in the accepted
`boon_of_spell_recall/category` prose, which this batch does not touch.

No errata source is tracked in the repository (`git ls-files | grep -i errata` is empty). No member was
blocked by a source contradiction.

## 3. Design reconciliation

ADR-005d Decision 7's **proposed, not accepted** amendment
(`docs/decisions/adr-005d-complete-typed-mechanical-authority.md`, after the 2026-09 citation-identity
amendment) was rewritten in the same change as the code. It quotes only the two Owner statements above.

- **Representation (unchanged by this correction).** Schema 17 adds five omit-when-empty `ReferenceDraft`
  fields: `target_component_key`, `alternative_label`, `situation` (`ReferenceSituation`),
  `class_record_key` and `minimum_class_level`. A singleton keeps its schema-16 canonical payload and its
  5-tuple coordinate. `reference_target_key` appends `(component, label)` only when either is set. The
  schema hash `4881e51f…` is unchanged: this correction changed validation and docstrings, not the schema.
- **Validation (`relationship_and_reference_violations`).** Destinations sharing a label are one route;
  every member of a route must state the same `(situation, class, minimum level)`. Several routes are
  legal. Two or more unlabelled destinations remain ambiguous. A lone labelled destination is a finding.
  The component, class, level and label checks are as before.
- **Schema trust seam.** `reference_resolution_violations(..., schema_version=…)` runs
  `declared_meaning_violations` over the **effective** representation, so a schema-16 artifact cannot
  acquire route fields through a resolution. Both callers pass it: the acceptance seam (`accept_proposal`
  and `resolve_references`) and the loader (`oracle.py`). `None` is kept only for the version-pinned
  historical verifiers.
- **Native lift-plus-resolve.** `resolve_references(prior, ..., lift_to=(version, hash))` lifts through the
  registered crossings and resolves in one action, appending each lift record. A refused lift
  (`SchemaLiftError`, `LegacySchemaPayloadError`) or a refused resolution raises `AcceptanceError`, and the
  caller's artifact is unchanged. Omitted, the action is unchanged. It runs in memory; nothing is recorded.
- **Selection.** `AlternativeSelection(situations, class_record_keys, class_levels)`. `select_alternatives`
  drops a route only when a stated condition is known to be false: a known situation that does not hold,
  a class not among the known `class_record_keys`, or — independently — a known level in that class below
  the minimum. Unknown values keep the route. Several classes are several applicable routes, not a
  contradiction. `routes(refs)` groups by label in first-seen order.
- **Narrow reader.** `RulesAuthorityService.citation_view(request, citation=, selection=)` finds the
  citation's references in the effective authority, selects routes and reads their destinations through
  the ordinary record and component selectors (`_narrow`, which `_scoped_authority` now shares), so
  overrides apply and stale or disabled targets refuse. It returns `RESOLVED` with the routes and the
  GameMaster view. An unknown or unresolved citation is `INVALID_REFERENCE`; a selection that rules out
  every route is `INVALID_SELECTOR`. It is not a builder, an eligibility engine or a sheet mutation.
  - **Source in effect.** The citation must still be stated by the *effective* source, not only the base
    projection. Every provenance span of the citation's references must still be source prose of the
    effective citing record, and of the citing component when the citation names one. Disabling the citing record,
    component or prose, or replacing the record, component or prose, makes the citation
    `INVALID_REFERENCE`. Edits that keep the citing passage (a prose append, an override elsewhere) leave
    it `RESOLVED`. On the real candidate each of the 13 citations has exactly one provenance span, inside
    its citing component's prose.
  - **Order.** The view's components are stably ordered by the first selected destination that reads them,
    so routes appear in stated order and each route's landing precedes its support. A whole-record
    destination ranks the record and its catalogue members; inside a destination, source order is kept.
    Only this reader's returned view is reordered; `_select` and other views are unchanged. Before, the
    view followed `_select`'s sorted keys, and `classes.paladin` sorts before
    `classes.paladin.as_a_multiclass_character`. That is inferred from key order: the new order test was
    not run against the pre-fix code.
- **Persistence.** Alembic `0036_reference_alternatives` adds the five columns with empty defaults. Its
  downgrade refuses while any route field is stated.

## 4. #40: the Origin Feats group route

`gameplay-toolbox.md:159` cites "Origin Feats". `feats.md:19–58` prints `### Origin Feats` with "for
examples", followed by Alert, Magic Initiate, Savage Attacker and Skilled, each marked *Origin Feat*.

- **Destination.** One route, labelled "Origin Feats (examples; not every Origin feat)", whose four members
  are the existing feat records in source order. The citation therefore resolves to one unit, not four
  pseudo-alternatives.
- **Ownership unchanged.** `feats.feat_descriptions` still owns all 17 feats through its `CATALOGUE_MEMBER`
  edges. No edge was moved or duplicated, no catalogue owner was added, and the category taxonomy
  (`feats.feat_descriptions/categories`) is not used.
- **Validated against the source.** `_origin_feats` in the harness refuses unless:
  - the headings between `### Origin Feats` and `### General Feats` are exactly those four, in order
    (containment and order);
  - each states *Origin Feat* before the next heading (category);
  - each feat's `CATALOGUE_MEMBER` owners are exactly `{feats.feat_descriptions}`.

  Release binding is checked by `resolve_references` for every destination.
- **Read.** `citation_view` returns the four effective records. An override applies; disabling
  `feats.alert` makes the citation `INVALID_REFERENCE` rather than silently reading three (§6).
- **Meaning preserved.** The label states that the list is examples and is not exhaustive. The heading
  itself stays navigation-only: no record or component was created for it.

## 5. Deviations (Architecture Notes)

1. **Generator default pin.** `EntryBatch.schema` defaults to the literal schema-16 pair, so the accepted
   generators keep minting the bytes their packets recorded. New schema-17 meaning is reached only through
   the lift.
2. **Lift-plus-resolve is native.** The previous revision appended the lift records by hand in the harness.
   That is replaced by `resolve_references(..., lift_to=…)` (§3). It produces the same lifted bytes
   (`9c34a880…`). Old actions, the protected scripts and old byte replay are unchanged.
3. **The build is ahead of the committed oracle: an engineering compatibility gap.** Until now, every schema
   mint in this repository coincided with an acceptance that crossed the lift. An unaccepted mint produces a
   state this repository has never had: the build implements 17 while the committed oracle and every
   replayed accepted state remain at 16. When the build judges such a state, it adds exactly 2 findings
   (`candidate declares representation schema '…-16', build implements '…-17'`). The accepted state hash
   `5f37fb08…` is unchanged, and no accepted byte moves.
   - **Protected standalone verifiers (not edited, still refuse as-is).** Five accepted verifiers assert
     that the oracle schema equals the build schema. Run unchanged under build 17, they still refuse with
     the 2 schema findings. This packet does **not** claim they pass unchanged:
     - `issue-5d-framing-coverage-ACCEPT.py:261`;
     - `issue-5d-character-creation-catalogue-ACCEPT.py:368`;
     - `issue-5d-finite-reference-atoms-ACCEPT.py:391`;
     - `issue-5d-playing-the-game-atoms-ACCEPT.py:381`;
     - `issue-5d-equipment-class-eligibility-ACCEPT.py:386`.

     Unpinning would re-mint accepted bytes, and admitting an earlier contract in `validate_candidate`
     would be the silent restamp Decision 6 refuses. Neither was done. This was previously described as an
     Owner-decision blocker until recording; it is reclassified as an engineering compatibility gap. It
     closes only when an accepted batch that crosses 16→17 is recorded. Exact candidate acceptance comes
     before recording; the Owner's order pass is a separate step, after the packets and before publication.
     Nothing is recorded to make these verifiers pass.
   - **Compatibility shown by the editable harness.** The five `test_animals_proposal` tests that drive
     those verifiers' `_check` now pass `lifted(prior)` and `lifted(recorded)` (or `committed`) through the
     existing `_schema_pins.lifted()`, with a NOTE comment. Their byte and replay assertions are not
     weakened. Result in §8.
   - **Editable test sites (unchanged from the previous revision).** Where a test means "the accepted state
     as the build judges it", the replayed state crosses its registered lifts through `lifted()` before
     `validate_candidate`, the pattern `test_character_origins_feats_acceptance` already used. No expected
     count was bumped. The full-chain canary in `test_committed_accepted_authority` gains
     `5d-lift-schema-16-to-17`.

   **Sibling-audit note.**
   - **Family:** an accepted state at schema 16 is judged by a schema-17 build.
   - **Trigger:** the full mechanical-suite run, with 36 failures across 13 test files.
   - **Structures inspected:** every `validate_candidate(candidate_from_accepted_inputs(…))` site in the
     failing files; the `persisted` fixture in `test_spell_descriptions_proposal`; the three
     composed-coverage tests that assert the prior's schema; the chain canary.
   - **Regression coverage:** attached per-file runs (§8).
   - **Dispositions:** 31 `patched` in the previous revision. 5 (the protected-verifier tests) are now
     `patched` in the editable harness only; the protected scripts themselves are unchanged and still
     refuse standalone.

   Files edited for the family (untracked files, which belong to the in-progress restart work, are marked
   `??`):
   - `test_committed_accepted_authority.py`: chain-list append;
   - `test_character_origins_feats_acceptance.py`: one wrap;
   - `test_animals_proposal.py` ??: one wrap plus the import (previous revision), and the five verifier
     calls (this revision);
   - `test_monsters_proposal.py` ??, `test_gameplay_toolbox_proposal.py` ??, `test_magic_items_proposal.py`
     ??, `test_equipment_acceptance.py` ??, `test_spellcasting_acceptance.py` ??, `test_classes_proposal.py`
     ??: one `lifted()` wrap each, plus the import;
   - `test_spell_descriptions_proposal.py` ??: one wrap plus the fixture wrap;
   - `test_rules_glossary_completion_proposal.py` ??: one wrap plus `prior = lifted(prior)`;
   - `test_spellcasting_proposal.py` ?? and `test_equipment_proposal.py` ??: `prior = lifted(prior)`.

   **Limitation.** These 11 untracked test files have no before-images: there is no HEAD to diff against
   and no copy was taken. "Only these hunks changed" is inferred from the Ruff import-only fixes and from the
   patch scripts, and is not verified.

   Also edited for the schema canaries: `test_schema_12_practical_reliability.py` (17 subtracted beside
   12–16) and `test_character_origins_feats_proposal.py` (the proposal is pinned to its minted 16 pair, and
   the composed lift now crosses 16→17).
4. **#11 cross-scope self-record.** The MULTI route targets `LA/character_advancement`, the citing record,
   outside the citation's `classes` scope, because the total-level table lives there.
5. **Test fixture lift.** `tests/ingestion/mechanical/data/bounded_oracle.json` was lifted 16→17 by a
   minimal textual edit: the lift record was appended and `representation_schema` restamped. An earlier
   attempt was undone with `git checkout` on that one file. The file was clean at HEAD, so only committed
   bytes were restored.
6. **Reader double reconstruct.** `citation_view` reconstructs once to find the citation's references and
   once through the ordinary path (marked `ponytail:` in the code). It is correct but not optimal; share
   the reconstruction if reading cost matters.

## 6. Compatibility and test evidence

`tests/ingestion/mechanical/test_reference_alternatives.py` covers:
- serialization and reconstruction; singleton compatibility (payload and coordinate unchanged; the
  schema-16 and schema-17 payloads are equal);
- routes: a landing plus supporting members under one label is legal; several routes coexist; split
  conditions within a route, unlabelled members and a lone label are findings;
- selection: a known class and a known level both constrain a route; several qualifying classes keep
  every route; an unknown level keeps a known class's route; class level is never total level;
- the schema seam: a schema-16 artifact refuses routes at `resolve_references`, and the loader refuses a
  schema-16 file that states one;
- the native action: lift record appended, reload byte-identical, a refused lift or a refused resolution
  raises with the prior's bytes unchanged; a schema-16 singleton resolves with no lift and no route fields;
- release and provenance mismatch, override conflicts, the publication gate, malformed committed
  destinations, and migration 0036 upgrade defaults and downgrade refusal.

New file `tests/ingestion/mechanical/test_reference_alternatives_candidate.py` reads the **real** candidate
through `citation_view`. The harness's `resolved()` builds it; it is persisted as a draft into a private copy
of the `source_release_db` fixture. Only binding resolution is stood in (as in the other draft-read tests);
reconstruction, overrides, selection and the GameMaster view are production code.
- Paladin 1 / Ranger 3 on #17 → only the Ranger route, with the Fighting Style prose.
- #11 MULTI → both destinations; `MC/proficiency_bonus` text contains "total character level".
- #8 entering Paladin → [`AMC(paladin)`, `classes.paladin`], reaching more than two `classes.paladin.*`
  records.
- #40 → one route with the four feats in order; `feats.alert/category` reads "Origin Feat".
- Disabling `classes.fighter.fighting_style` while reading for Ranger → `RESOLVED` with that override
  applied; read with an unknown selection → `INVALID_REFERENCE`. Disabling `feats.alert` → #40 is
  `INVALID_REFERENCE`.
- An unknown citation → `INVALID_REFERENCE`; a Wizard-only selection on #17 → `INVALID_SELECTOR`.
- Source authority on #17 (`feats.archery/category`): the record disabled, the component disabled, the
  prose disabled, and the prose replaced → each `INVALID_REFERENCE` ("effective source"). A prose append on
  that component plus disabling the unrelated `feats.defense` → `RESOLVED`, both overrides applied, Ranger
  Fighting Style read.
- Order: #9 entering Paladin reads `[(classes.paladin.as_a_multiclass_character, as_a_multiclass_character),
  (classes.paladin, core_traits)]`, landing first; #8 entering Paladin reads `AMC(paladin)` first, then only
  `classes.paladin*` components. Paladin #9 with no selection keeps both routes, and the view follows the
  route destinations in stated order. #40 reads alert, magic_initiate, savage_attacker, skilled.

Harness consumer check: Paladin 1 / Ranger 3 → `['Ranger level 2: Fighting Style']`; an unknown selection
keeps all 3.

## 7. Remaining boundaries

- **Engineering compatibility gap (§5.3).** The five protected standalone verifiers still refuse under
  build 17 and are not edited. Compatibility is shown only through the editable harness.
- The ADR amendment is proposed only.
- Recording requires exact acceptance of this candidate first. The Owner's one bounded order pass comes
  after the packets and before publication. The native lift-plus-resolve action exists; no recording step
  was run.
- No accepted artifact, generator, PROPOSAL, DELTA, packet or ACCEPT script was rewritten. The singleton
  reading is preserved.
- Not run, and **not green**: pip-audit, mypy beyond the changed sources, coverage, and a full-suite rerun.
  Focused runs use `--no-cov`; an earlier focused run with coverage exited 1 below the global threshold, and
  that is not called green.

## 8. Gates

All runs used `RTK_DISABLED=1`, `PYTHONUTF8=1` and `venv/Scripts/python.exe`, attached unless stated. They
ran on the uncommitted working tree; nothing was committed or staged.

**Consolidated correction (previous round).** Its reader row (6 passed) and the `service.py` and
candidate-test parts of its Black/Ruff/mypy rows are superseded by the reader-defect block below; the rest
still describes the final tree.

| Gate | Result |
|---|---|
| Black `--check` | 7 changed src files, the 3 changed tests and the harness: 11 unchanged, exit 0 |
| Ruff | Same files: "All checks passed!", exit 0 |
| mypy `--strict` (`MYPYPATH=src`) | The 7 changed src modules: "Success: no issues found", exit 0 |
| `test_reference_alternatives.py` + `test_reference_resolution.py` | 179 passed, exit 0 |
| `test_reference_alternatives_candidate.py` | 6 passed (231 s), exit 0. This run started before the harness module-docstring rewrite and possibly before Black's reformat of the test file; both changes are behaviour-neutral, and the harness check mode afterwards reproduced the same candidate and PROPOSAL/DELTA bytes. |
| `tests/services/rules_authority` (the `_narrow` refactor) | 430 passed, exit 0 |
| Schema and committed-authority canaries (`schema_version_legality`, `representation_schema_identity`, `review_round_7`, `review_round_9`, `schema_12_practical_reliability`, `committed_accepted_authority`) | 369 passed, exit 0 |
| `test_animals_proposal.py`, the five verifier tests (`-k` the five names, `--no-cov`) | 5 passed, 15 deselected, 579 s, exit 0 (12:15:38Z–12:25:20Z). Recorded (reference, uncovered-leaf) findings per test: framing (64, 0), character-creation catalogue (62, 0), finite-reference atoms (52, 0), playing-the-game atoms (49, 0), equipment class eligibility (46, 0). Each check's own assertions held, including "DELTA, line for line" where the check prints it (framing, finite reference, playing the game, ECE) and "resolutions verbatim, in order" (the last three). A first attempt (task `bivq7ifj3`) piped output through `Select-Object -Last` and was killed when the session ended, leaving no output and no exit code; it is not evidence. The rerun was detached with raw output and exit code written to `.claude/_sp/rb/animals5.log` / `animals5.exit`. |
| Harness check mode | OK, exit 0. PROPOSAL and DELTA byte-identical; hashes as §1. |

**Reader-defect correction (this round: source in effect, route order, authority wording).** Changed:
`service.py` (`citation_view` only), `test_reference_alternatives_candidate.py`, this packet and the ADR
amendment bullet. Ingestion code, the harness, the candidate, PROPOSAL and DELTA are untouched, so their
identities (§1) stand without regeneration.

| Gate | Result |
|---|---|
| Black `--check`, both changed Python files | 2 unchanged, exit 0 |
| Ruff, same files | "All checks passed!", exit 0 |
| mypy `--strict` (`MYPYPATH=src`), `service.py` | "Success: no issues found in 1 source file", exit 0 |
| `test_reference_alternatives_candidate.py` (`--no-cov`, detached, raw log `.claude/_sp/rb/reader.log`) | 13 passed in 359.54 s, exit 0 (12:38:33Z–12:44:34Z): the 6 earlier tests plus 4 source-gone cases, the source-kept case and the 2 order tests |
| `tests/services/rules_authority` | 430 passed in 61.28 s, exit 0 (ended 12:45:54Z). Both runs started after the last edits to `service.py` (12:38:19Z) and the test (12:38:12Z). |
| Plain `detect-secrets scan` to stdout over the 4 changed files | no results; the baseline holds no entries for them, so it is unchanged this round (`63c8358d…`) |

Reused without rerun, because this round touches none of their inputs: the 5 animals verifier tests (5
passed, exit 0), the focused pair (179 passed), the schema canaries (369 passed), and harness check mode.
The broad suite, the five historical tests standalone, historical reconstruction and proposal generation
were not run.

**Reused from the previous revision, not rerun (no blanket rerun was ordered).** Recovered from the session
log; these ran before this correction and do not cover it:
- the earlier focused pair: 173 passed;
- schema canaries: 427 passed / 5 failed, then 115 passed / 1 failed, then 1 passed;
- mint-consequence sites: 91 and 237 passed; animals 15 passed / 5 failed;
- one background full run of `tests/ingestion/mechanical` + alembic + the rules-authority migration, before
  the earlier fixes: 4055 passed, 29 failed, 7 errors, 14 skipped. **No full-suite rerun since.**

**Secrets.** The scoped baseline evidence `fbe8ebc6… → eaa04672859b16d0261bec1063fcd53161736a4dedb7fae35ce1c42ace74b1ea`
(+10 / −1, 10 moved lines) is reused for its entries: this correction changed no schema hash. A plain
`detect-secrets scan` to stdout over the 15 files this revision touched finds the same 10 hashed secrets
the baseline already holds, and none new (the packet's hashes are unquoted and not flagged). Six of their
line numbers moved, so the baseline is not reusable byte for byte. Those six numbers alone were edited in
place: the PROPOSAL's 312→304, 313→305, 315→307, 317→309 and 1414→1859, and the harness's 116→120. No
entry was added or pruned, and settings are unchanged. Baseline `eaa04672…` →
`63c8358dbffdc7c2ff24166cfbed6d74dea6e86271f267ab712963a69972d1be`, unstaged; the index is untouched. The
final hook command and its result are
recorded in the final report, not here: this packet is written before that run. Earlier evidence: a
private-copy hook run exited 0 at 11:12:39Z (copy unchanged) and was **content coverage only, not staged
hook behaviour**; the real hook against the unstaged baseline exited 1; and the previous report was edited
at 11:12:43 and 11:14:11, after that hook ran. No pragma was added and `scan --baseline` was not used.
