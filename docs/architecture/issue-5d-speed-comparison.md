# 5d recovery: Speed comparison and proposed next steps

**Date:** 2026-09-16\
**Inspected repository:** `02a432f2`, merged Speed acceptance PR #167.\
**Status:** Reviewable design proposal. No accepted rules or runtime code changed.

## Recommendation

Keep the accepted Speed data. Change the rules for deciding what future content needs structured
fields, and consolidate the repeated batch machinery. Speed does not demonstrate that its seventeen
facts should be deleted. It does demonstrate costs beyond recording and reviewing the rule itself.

Review the [proposed ADR amendment](../decisions/adr-005d-practical-reliability-proposal.md) and the
[complete replacement draft for issue #137](issue-5d-practical-reliability-draft.md) together. They
preserve complete SRD rule coverage while changing how representation work earns its place.

## What Speed actually contains

The accepted batch combines the Combat and Rules Glossary printings into one `glossary.speed` record:
9 components, 17 facts, 36 classified spans across 16 source leaves, and 9 references. Sixteen spans
are substantive and twenty are supporting. It has no governing-prose bindings.

Repeated wording is already combined where appropriate: seven distinct facts carry primary source
claims; two have three primary claims each. Examples are retained as supporting text. Neither a
separate fact for every printed occurrence nor treating every example as a new mechanic is the
observed problem here.

This batch is not all movement rules. It leaves references to Burrow Speed, Climb Speed, Climbing,
Crawling, Fly Speed, Flying, Jumping, Swim Speed, and Swimming for other records. Acceptance is not
publication or executable movement support.

## Compare the accepted data with the proposed approach

The right column describes plausible v1 purposes, not a claim that movement execution is already
implemented. Direct fact-name searches primarily found representation/validation plumbing. The
downstream implementation must confirm the actual consumer contract before adding or changing fields.

| Accepted component | Facts | Proposed disposition and concrete purpose |
|---|---:|---|
| `speed_definition` | 1 | Retain. The foot unit and own-turn window make the measure explicit. A future numeric consumer must not infer its units from prose. |
| `movement_allowance` | 1 | Retain. Names own Speed as the movement allowance and its turn window. Needed to calculate an allowance without inventing a character's actual Speed. |
| `movement_composition` | 2 | Retain. Records whether the named movement forms can combine with regular movement or occupy the entire move; supports legality checks and explanations. |
| `movement_depletion` | 1 | Retain. States what movement uses up and when movement stops; supports tracking remaining allowance. |
| `movement_modes` | 4 | Retain. Identifies the permitted climb/crawl/jump/swim forms. Lets downstream code distinguish permissions without parsing a sentence. |
| `special_speeds` | 4 | Retain. Distinguishes the named special-speed modes from general movement permissions. The list is explicitly non-exhaustive; it must not become a closed list of everything a creature could have. |
| `speed_selection` | 2 | Retain. Records selection before moving and switching during movement; supports checking a declared move. |
| `speed_switch_limit` | 1 | Retain. Records subtraction of distance already moved and the nonpositive-limit restriction; directly affects a movement calculation. |
| `speed_change_propagation` | 1 | Retain. Records the stated scope, amount, and duration of a Speed change affecting special speeds. Preserve the examples and source meaning; this data does not by itself settle an execution algorithm for every modifier. |

Under the new policy, definition/category material could remain exact governing prose when no
identified code use needs its fields. That is a prospective option, not a demonstrated reason to
rewrite these accepted facts. Retaining useful existing fields is cheaper and safer than migrating
accepted identities merely to make the representation look smaller.

**Concrete comparison result:** same accepted Speed meaning and fields; fewer repeated programs and
checks for future authoring; no new rule that all reducible meaning must become fields. Simpler work
does not require deleting useful data.

## Where the avoidable work appears

At the inspected commit, the Speed proposal generator is 3,604 physical lines, its acceptance script
is 1,846 lines, and its separate reproduction test is 327 lines. These are file sizes, not measured
engineering time or a prediction of removable code. Some lines contain necessary source-specific
declarations and historical evidence.

The reproduction test explicitly follows the Cover test clause for clause and reconstructs the
proposal independently of the acceptance script. Both use the existing production `accept_proposal`
function. Proposal JSON is reloaded using private oracle parsers in the acceptance script. This gives
a concrete consolidation target rather than a reason to invent a new acceptance architecture.

| Task | Current Speed pattern | Proposed pattern for subsequent batches |
|---|---|---|
| Name source scope and rules | Source manifest plus a large custom generator | Reviewed batch data using common source/representation helpers; source-specific code only where the actual shape requires it |
| Reload the reviewed proposal | Batch script reconstructs it using private parsers | One supported loader with schema validation and identity verification |
| Record acceptance | Batch script wraps `accept_proposal` with many pinned checks | Common command uses the exact reviewed proposal, scope, prior inputs, and decision; acceptance remains explicit |
| Verify retained acceptance | Batch script plus a second reproduction implementation | Shared replay/verification with independent source-reviewed expectations and focused failure tests |
| Explain the result | Large batch report repeats mechanism details | Concise source scope, meaning changes, exceptions, evidence, and unresolved matters; common behavior documented once |

The proposed common command must preserve the recorded scope order when reproducing historical
acceptance: the current Speed test demonstrates that reordered scope can preserve semantic identity
while changing retained evidence bytes. Consolidation must not erase that distinction.

The generator's audit describes what it generated; it is not independent evidence that it interpreted
the SRD correctly. That evidence comes from source review and accepted expectations. Sharing a loader
does not remove source review, and using two loaders does not substitute for it.

## How this addresses the four problems

| Problem | Concrete change | Evidence that the change helped |
|---|---|---|
| 1. Practical reliability did not extend far enough into 5d | Check source identity, required content, stored reconstruction, references, and publication directly. Stop requiring a new parallel acceptance implementation per batch. | A common path catches actual omission/corruption/staleness cases and reproduces retained Speed acceptance. |
| 2. Coverage became a mandate to formalize every reducible detail | Require a named play/explanation/correction use for a new field. Permit exact governing prose without falsely declaring it irreducible. Review sections/entries/tables with coverage checks rather than human classifications for every fragment. | A pilot preserves every rule and exception while showing why each new field is needed and where prose suffices. |
| 3. Reuse was promised before ordinary throughput was demonstrated | Run one regular-section pilot including exceptions after the common path works. | Record actual effort, reuse, new families, and batch-specific code. Diagnose remaining custom work before scaling. |
| 4. Batch-specific machinery kept multiplying | Reuse acceptance, loading, verification, and test infrastructure; keep only genuine content differences in each batch. | The pilot needs no copied acceptance/reproduction implementation. Any custom code has an identified source-shape reason. |

This proposal does not address overall completion-percentage accounting.

## Concrete sequence after design adoption

1. Record adoption of the coordinated issue and ADR wording. The complete issue draft preserves all
   25 acceptance-criterion numbers and the later override amendments.
2. Claude implements the smallest shared loader/accept/verify changes around existing production
   code. Use retained Speed inputs as a reproduction case; preserve its accepted data and replay
   evidence. Keep already-supported historical schemas honest.
3. Implement the versioned representation-policy and coverage changes needed to admit the new prose
   reasons and review units. Do not relabel reducible text with an old irreducibility code or silently
   reinterpret an old schema. Keep legacy accepted partitions readable and verifiable.
4. Exercise concrete failures: remove a required rule or exception; remove a field a named operation
   needs; corrupt a source link or stored payload; attempt unaccepted input or partial publication.
   Keep existing binding/override tests. Test the common behavior once and add content-specific cases
   for actual exceptions, rather than duplicating the machinery for each batch.
5. Select and author one coherent regular section using that path. Equipment is a candidate only
   after checking the actual section, its exceptions, and reusable fields. Present its exact scope
   and proposal for the ordinary explicit semantic acceptance; do not assume this design review
   accepts unseen corpus content.
6. Review that pilot's correctness and work cost, resolve any demonstrated obstacle, then resume
   broader authoring. Preserve the seven accepted batches unless a concrete defect requires correction.

Ordinary implementation choices remain Claude's. No universal rules engine, source re-ingestion,
movement simulator, or new Planner/Writer authority path is part of this work. The same full-rule
publication boundary remains, and the remaining movement references are not declared resolved.

## Evidence checked

- [Speed acceptance checkpoint](../../.claude/review-notes/issue-5d-speed-1-ACCEPTANCE-CHECKPOINT.md)
- [Speed proposal](../../.claude/review-notes/issue-5d-batch-speed-1-PROPOSAL.json)
- [Speed generator](../../.claude/review-notes/issue-5d-batch-speed-1-generator.py)
- [Speed acceptance script](../../.claude/review-notes/issue-5d-batch-speed-1-ACCEPT.py)
- [Speed reproduction tests](../../tests/ingestion/mechanical/test_speed_1_acceptance_reproduction.py)
- [Shared acceptance function](../../src/afterworlds/ingestion/mechanical/acceptance.py)
- [Proposal serialization](../../src/afterworlds/ingestion/mechanical/proposal.py)
- [Accepted ADR, including schema 11 and later override decisions](../decisions/adr-005d-complete-typed-mechanical-authority.md)
- [Live issue #137](https://github.com/AfterworldsAI/afterworlds/issues/137), retrieved 2026-09-16;
  the companion issue draft is based on that body, not the older attachment.

Validation of this change is document consistency, source/code inspection, and diff/link checks.
Historical checkpoint test results are not new test results for this branch. No runtime behavior has
been changed or newly certified.
