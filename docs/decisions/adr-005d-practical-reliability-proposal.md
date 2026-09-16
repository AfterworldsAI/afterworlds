# ADR-005d practical reliability amendment — accepted

**Date:** 2026-09-16\
**Status:** Accepted by Owner Decision 2026-09-16; implementation pending.\
**Parent:** [ADR-005d](adr-005d-complete-typed-mechanical-authority.md)\
**Companion:** [complete amended issue #137](../architecture/issue-5d-practical-reliability-draft.md)\
**Evidence and next steps:** [Speed comparison](../architecture/issue-5d-speed-comparison.md)

**Owner Decision, 2026-09-16:** “I approve adopting this policy in CRD Issue 5d and ADR-005d.”

This amendment and the coordinated issue text are adopted. Implementation remains pending. This
decision accepts no new corpus batch and authorizes no publication, activation, or merge. PR #169
records the decision in the repository; issue #137 carries the amended construction contract.

## Purpose

Keep complete SRD rule coverage while requiring a concrete reason for representation and verification
work. A rule that can be expressed as fields does not automatically need those fields. A source
paragraph may deserve preservation without becoming a separate mechanical component.

For each proposed kind of work, answer:

1. Why must this passage be classified and recorded?
2. Why must this rule detail become a structured field?
3. What would fail during play, explanation, or correction if we omitted that work?

An answer may cover a repeated family of rules or an entire coherent section. These questions do not
create a mandatory form for every passage or field. A foreseeable v1 use counts; a consumer need not
already exist. Mere reducibility, possible future extensibility, or a desired representation count is
insufficient.

## Superseded requirements and preserved decisions

The provisions below supersede only the corresponding requirements of ADR-005d. The
historical schema amendments and accepted batches remain evidence of the contracts under which they
were created. No accepted schema, input, identity, or runtime behavior changes merely by adopting
this text. Any necessary implementation/schema transition must be explicit and versioned.

New accepted review inventories, coverage decisions, and handling policies are meaning-bearing inputs
and participate in the projection identity. Incidental review metadata remains outside semantic
identity. Existing recorded identities are not reinterpreted under the new policy.

| Parent provision | Adopted change |
|---|---|
| Central Decision; Decision 1 | Full actual-rule coverage remains. Choose fields for identified code uses and exact prose for remaining governing meaning. Reducibility alone does not force a field. |
| Decision 2 | Review coherent entries, tables, or sections against an inventory covering the source. Replace mandatory gap-free classification of every extracted leaf with the coverage contract below. |
| Decision 3 | Preserve stable semantic records, exact source references, and source/authored-prose separation. A review unit need not become a record or component. |
| Decision 4 | Keep closed, validated field families and hand-authored execution. Add a family when an identified use needs it, rather than whenever prose can be formalized. |
| Decision 5 | Check reviewed expected rules and required fields against rebuilt stored output. Prose alone is a defect when a required structured use is unmet, not because prose was selected. |
| Decision 8 | Retain direct source integrity, reconstruction, and atomic publication. Use focused checks for the failure modes described below, without a new parallel historical proof implementation per batch. |
| Decisions 6–7 and 9–11 | Preserve identities, reference resolution, binding, retained override versions, override behavior, and downstream ownership. |

## 1. Complete coverage with proportionate review

The reviewed inventory must cover the whole bound SRD corpus at meaningful section, entry, or table
boundaries. Each unit resolves to exact source membership; gaps in the inventory, unreviewed units,
unresolved rules, and missing expected rules block publication. Expected entries and table rows must
be derived from the source and checked in review, not inferred from the output being tested.

Within a reviewed unit:

- Every actual rule, qualification, and exception has an accepted home in structured data, exact
  governing prose, or both.
- Repeated statements may share one rule representation with their relevant source links. Preserve
  differences in scope or effect; similar wording alone does not establish duplication.
- Examples and explanations may remain supporting text. If one introduces a rule or exception, that
  meaning must be represented as authority.
- Pure flavor, navigation, licensing, and non-rule advice may be excluded from mechanical authority
  with a reason for the applicable group. They remain in the immutable 5c source.

This replaces a requirement for an accepted classification row for every character interval of every
extracted leaf. It does not replace source review with an aggregate percentage or an unattended
classifier. Existing accepted span partitions remain valid and are not rewritten.

The inventory is the review scope and coverage evidence, not a second copy of the source. Exact
subspan references remain where needed for a fact, rule, qualification, citation, or correction.
Ordinary shared tooling may derive membership/offsets; the reviewer accepts the actual scope and
meaning, not merely the generator's claim that it is complete.

## 2. Fields serve identified uses; prose can govern

A field is required when an identified code-owned operation needs it for play, explanation, or
correction. Examples include arithmetic, legality checks, selection, relationships, and targeted
overrides. Name the operation and the consequence of omission. Shared uses justify shared fields
once for the family; do not require repeated justifications for every row.

Use exact governing prose for remaining rule meaning. This includes genuine judgment and meaning
that is technically reducible but has no identified need for a separate field. Such prose remains
part of the bound rule authority, available through the GameMaster view with exact source references.
It is not merely a citation or explanatory footnote.

The handling states remain structured, prose-bound, and mixed. A prose choice records its actual
reason. Do not label reducible text as irreducible to satisfy today's catalog. A versioned policy
change must distinguish at least judgment-required prose from prose retained without a separate
structured use. Old reason values keep their historical meanings.

This does not authorize a model to extract a number or interpret prose into a trusted mutation at
runtime. If a planned v1 code operation needs a field, supply it before that operation relies on the
rule. Missing required fields are explicit failures. The 15c-owned validated application path for
GameMaster decisions remains a separate obligation, not an escape hatch supplied by this amendment.

## 3. Operational checks and shared machinery

Retain direct integrity checking of the published 5c source, accepted input validation, reconstruction
of stored authority, identity verification, unique reference resolution, and atomic publication.
Published projections remain immutable; partial projections cannot activate.

Acceptance evidence must identify the reviewed source scope, proposal, accepted meaning changes, and
decision. Reuse the existing `accept_proposal` seam and production validators where possible. A common
loader, accept/verify command, and parameterized tests may replace duplicated future batch machinery.
Neither unattended generation nor a passing test constitutes semantic acceptance.

Independence means the expected rule meaning and required cases were reviewed against the source
independently of the built output. It does not require a second handwritten implementation of the
acceptance procedure for every batch. Tests must exercise failures, not just compare a shared helper
to itself. Keep retained accepted inputs and historical replay fixtures; simplifying future tooling
does not authorize their deletion.

Check concrete failures: an omitted rule or exception, a missing field required by a named operation,
a wrong/unresolvable source reference, a changed source or stored payload under an unchanged identity,
an unaccepted proposal, and partial publication. Existing binding and override failure tests remain.
Add a check for a newly discovered failure when it has a concrete consequence. Do not construct a new
recursive proof system or prescribe a second generator solely to call its output independent.

## 4. Demonstrate ordinary production work before scaling

Keep the accepted Speed representation. Consolidate the common batch machinery first, with Speed as
a retained reproduction case, without rewriting its accepted authority or historical fixtures.

Then propose one coherent regular section, including its exceptions, for an ordinary authoring pilot.
The engineer selects and names the actual section after inspecting the source and existing field
families; the selection is not permission to reduce final coverage or skip awkward rows.

The pilot must show what reused existing fields, what new fields were necessary and why, what remained
governing/supporting prose, and whether review found omissions. Report actual authoring/review effort
and batch-specific code added; no invented throughput target or overall completion percentage.
If the pilot still requires a large custom program, diagnose that cost before starting more batches.

## Scope and sequencing

The coordinated issue/ADR wording is adopted. Next, Claude implements the shared-tool and any required
versioned policy changes, preserving accepted meaning and exercising the failures above. Review that
work before conducting the regular-section pilot and resuming broader corpus authoring.

Full substantive SRD coverage, exact citations, immutable base identity, the four-part runtime binding,
replayable override versions, authored house-rule provenance, final effective handling, and the
APPEND-only OPTION target remain intact. 5c is read-only. 2b owns character state; 15c owns execution,
capability certification, and application of adjudicated effects. Retrieval is not mechanical
authority. Frozen work remains frozen. Progress-percentage accounting is outside this amendment.
