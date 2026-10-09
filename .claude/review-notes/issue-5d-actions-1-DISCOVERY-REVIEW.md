# CRD Issue 5d actions-1: review of the discovery stop

Reviewed local head `14d5ac4` against `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` on 2026-09-05. No push was needed. This review changes no implementation, accepted authority, or Owner Decision.

**Disposition: uphold the schema stop; correct the discovery checkpoint before using it to authorize a schema step.** Several real missing representations are established, including Dash's movement allowance and bounded effect duration. The asserted complete gap/boundary classification is not yet reliable.

## Verified locally

- One worktree, at the existing repository. Local `main` and `origin/main` both name `b5d386b`; the `main` reflog records the fast-forward. The action branch has two subsequent commits and changes only the two checkpoints, the frozen fixture, and `.secrets.baseline`.
- The frozen fixture and live oracle are both byte-identical to the baseline's committed oracle blob. Content SHA-256 is `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7`. Loading the fixture through `load_accepted_inputs` and computing `oracle_identity` reproduces `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245`.
- The baseline edit adds exactly one fixture path with 60 entries. Every pre-existing entry and all other baseline configuration are unchanged. The new finding data, excluding filename, equal the oracle's finding data.
- Independently ran the current `build_candidate` pipeline on the committed PDF. All five independently derivable source-binding values match. Selecting the Rules Definitions Action umbrella and twelve `[Action]` entries reproduces all per-entry leaf counts, 13 records, and 92 represented leaves. Inspected the resulting Attack, Help, Magic, and Ready source leaves directly.
- Python 3.12.10 runs outside the tool sandbox; the sandbox launcher failure is not a repository toolchain defect. The reported 1,935-test run was not repeated for this documentation/identical-fixture change. Its coverage failure remains disclosed; this review does not claim a green full suite or CI.

## Findings requiring discovery correction

### 1. [P2] Separate current schema limits from governing scope and Known Unknowns

Location: `issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md`, F10/F13/F15/F16 at lines 442–448 and Architecture Notes at lines 651 onward.

F16 calls Attack interleaving out of scope because Extra Attack is outside Rules Definitions. But the complete permission is explicitly in the in-scope Attack source leaf `2a4a9331-f52b-5d86-9e68-e1242e49eb49`, p.177. The text conditions the permission on a feature granting multiple attacks; it does not require importing the implementation of any named example feature. Keep representation of that permission in scope and assess any reference dependency separately. The module header's word “Untouched” records unfinished implementation, not a scope exclusion.

F13 labels declarative resource expenditure/non-expenditure a Known Unknown by citing parameterized adjustments. `docs/architecture/known_unknowns.md:375` confines that unknown to runtime parameter selection, its typed contract, and deterministic support. Its explicit CRD Issue 5d clarification distinguishes recording source rules from evaluating them. Recording Magic's no-expenditure rule or Ready's expenditure timing does not itself select a slot level, design a `RollAdjustmentOption`, or mutate character state. Reclassify the representation gap and identify the exact point at which a proposed design would cross into that downstream unknown.

F10 cites an ADR-005d Decision 4 “generic-actor boundary” that the decision does not state. It forbids generic escape hatches, executable rules, and inferred authority. The current `COUNTERPART` restriction is real, but a source-grounded closed DC shape need not weaken it. Likewise, a proposed change to component shape is not automatically an ADR contradiction solely because it changes a component rather than a fact. ADR-005d's Implementation Authority expressly leaves repository-native schema choices to engineering. Identify an actual governing conflict before demanding an Owner Decision or ADR amendment; do not silently implement a conflicting design either.

### 2. [P2] Reopen Help's unsupported actor and scope analysis

Location: H3/H6, lines 218–221; “Explicitly not gaps,” lines 454–456.

The `RollActor` precedent concerns the charmer rolling **against the subject**. Help's ally makes a check concerning something else, or attacks an enemy distinct from the helper. That precedent does not establish an encoding for Help. The source also specifies the **next** qualifying roll, the selected skill/tool, and a five-foot enemy distance. The checkpoint relegates these to contextual prose because no field holds them while calling the case already safe. That conflicts with its stated rule against using prose as a backlog for missing representation.

There is a related structural omission: H1 uses `ComponentDraft.options`, while H2–H7 assign prose to individual options. `ProseBindingDraft` addresses a component, not an option; `ComponentOption` has typed facts and typed applicability but no option-specific prose binding. Show a faithful existing shape or record this option/prose association as a gap. Neither shifting the subject nor binding both alternatives at component scope can be assumed harmless without showing that the participants, chosen arm, and expiry clock remain distinguishable.

This does not forbid affirmative prose for the GM's final say or fiction-dependent assistance. Separate those clauses from deterministic actor, quantity, range, and selection constraints.

### 3. [P2] The proposed F6 correction does not represent its principal witnesses

Location: F6, lines 397–408.

F6 proposes condition-state predicates and homogeneous disjunction, explicitly forbidding mixed kinds. Dodge's witness is `Incapacitated OR Speed = 0`, spanning condition-state and quantity predicates. Hide spans obscuration and cover, then a separate termination disjunction mixing events and contextual predicates. Concentration state is not a member of `ConditionKind`. The stated correction therefore leaves its own examples unrepresentable.

Keep the schema stop. Replace the proposed closure with an explicit witness-by-witness residual matrix: existing shape, proposed shape, represented distinction, and unresolved residue. An intact prose-bound trigger may be justified where meaning is genuinely contextual, as the accepted Suffocation treatment illustrates; it must not be presumed to settle every typed predicate gap.

Apply the same bounded check to F1: `ActionCost` contains economy slots, not attack-roll or weapon-interaction allowances. Ready permits acting by spending a Reaction; the source does not say it increases the number of Reaction slots. The proposed common allowance family must not silently imply an extra Reaction or claim that the existing enum covers all four witnesses.

### 4. [P2] Do not hard-code the proposed reference list as an exact validator result

Location: section 6, especially lines 477 and 504–515.

The fifteen-row list already excludes `condition.invisible` and `condition.incapacitated`, which are separately listed as resolving against the prior. Standalone validation has neither prior target, so it cannot report exactly those fifteen rows and then lose two of them on combination. If every proposed citation becomes a reference, standalone has those two additional source/target pairs; combined validation retains the fifteen external pairs. The checkpoint simultaneously defers whether several listed in-text terms should become references, so neither count is currently an established validator set.

Separate confirmed source citations, candidate in-text references awaiting classification, targets supplied by the frozen prior, and remaining external targets. Include the Action umbrella's explicit Playing the Game / Actions citation in that analysis rather than treating the external list as complete while classifying that citation only as supporting authority. Derive exact validator expectations after those source-role decisions. Reading Extra Attack as an illustrative example is also distinct from resolving it to a particular class feature.

### 5. [P2] Supply the required bound-source coordinates before calling the obligation ledger complete

Location: section 4, beginning line 165, and the determinism discussion near line 629.

The ledger has page numbers and prose summaries, but no leaf IDs or leaf-local half-open character ranges. Multi-leaf clauses and table rows are summarized without exact cell coordinates. This omits the kickoff's required source-to-claimant mapping, and prevents a reviewer from checking that every part of the 92-leaf cut has a disposition. The source-discovery script is also described as retained only in the session scratchpad.

Add a discovery source manifest and link each obligation to its exact bound leaf/subspan or table cells, including supporting text and unresolved meanings. Preserve a reproducible discovery command or script for the assertions made. This is discovery evidence, not a proposal generator, and does not require generating accepted/proposed authority or forcing the historical counts. Any counts not yet defined should remain explicitly undefined; obligations already present in this checkpoint can be counted independently of proposal authoring.

### 6. [P2] Establish whether suggested tables need new typed authority before declaring F9 blocking

Location: J7, line 248, and F9, lines 410–430.

The rejection of mandatory `AbilityCheckFact.alternatives` is sound. The next inference—that supporting authority necessarily discards the printed mapping—is not established. Supporting authority is first-class, source-exact content under ADR-005d Decision 2; affirmative GM-governed prose is also permitted where the source delegates the decision. Exact row/cell associations must survive whichever handling is chosen.

Determine what claim these tables make: suggestions for a GM-selected check, rather than an exhaustive permitted roll set. Compare source-exact supporting or governing prose with a typed non-binding representation and identify any meaning the existing approaches actually lose. F8's GM-selected ability remains a separate potential representation gap. Do not make recovering an ability from a suggested row the remedy for F8, because the source allows the GM to choose a check outside that suggested set.

## Next instruction to Claude

Stay on the existing local branch and retain the schema stop. Correct the discovery evidence and classifications as one bounded pass across the families above. Rebuild the source-to-shape residual matrix before proposing a schema implementation plan. Preserve the verified prior, live oracle, and accepted evidence unchanged. Do not author an acceptance-ready proposal, implement a schema change, or turn an unresolved representation problem into a new Owner Decision merely because the current code lacks a field.

Return the corrected checkpoint, exact source manifest, reproducible discovery evidence, and a concise list separating genuine schema gaps from reference dependencies and actual governing decisions. No push is required for local Codex inspection.
