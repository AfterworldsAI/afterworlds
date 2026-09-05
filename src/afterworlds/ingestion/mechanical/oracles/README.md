# Committed accepted authority — CRD Issue 5d

One JSON file per published CRD Issue 5c release, holding the accepted
meaning-bearing inputs the production build consumes and the publication gate
judges against: the exact release binding, the declared semantic policy, the
accepted span classification, the review evidence that accepted it, the accepted
record/component/fact/prose-binding/relationship/reference/provenance inventory,
and the accepted per-record obligations.

The schema is whatever `oracle.load_accepted_inputs` accepts; it rejects a
missing key, an extra key, and an undeclared enum value rather than defaulting
any of them.

## What is committed here

`srd-5-2-1-corpus-36b786d8-fa2.json` — accepted authority for the SRD 5.2.1
release (`4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` /
`5.2.1-corpus.36b786d8-fa2`), currently holding **batches `conditions-1` and
`hazards-1`** — 22 accepted records over 281 accepted spans.

The file is named for the release, not for the batch, because the resolver
matches on the release binding and refuses outright when two artifacts claim one
release. A later batch therefore **extends this file** — `accept_proposal` takes
the loaded artifact as `prior` and merges, so an added batch cannot silently
discard an earlier one's reviewed work — rather than adding a second file. That
is how `hazards-1` was accepted on 2026-09-03, over the `conditions-1` prior.

**The CRD Issue 5d corpus is incomplete, so this release still cannot publish.**
Batch `actions-1` has not begun, and nothing is published or activated.
Accepted authority now exists and resolves, but the publication gate compares it
against the *whole* persisted projection: a projection carrying any record this
artifact does not accept fails with `MISSING_AUTHORITY` / `UNEXPECTED_AUTHORITY`.
Nothing here publishes, activates, or retires anything — committing an accepted
artifact is the acceptance action of record and nothing more.

Files here are review artifacts, not build output. Nothing in `src/` writes to
this directory, and no accepted artifact may be generated from a candidate or
from persisted projection state: an oracle derived from the thing it checks
proves only that the code agrees with itself.

## The workflow

```text
machine proposal  →  human semantic review  →  explicit acceptance  →  commit
```

**Propose.** A tool builds a `MechanicalProposal`
(`afterworlds.ingestion.mechanical.proposal`) and writes `proposal_payload` to a
working path — never to this directory. A proposal is a *different shape* from
accepted authority at every level: a different `artifact_kind`, spans under
`proposed_spans` carrying a per-span origin and rationale, representation under
`proposed_representation`, and no `acceptance` or `obligations` blocks at all.
It therefore cannot be loaded as accepted authority by renaming it, moving it
into this directory, or editing one field.

**Review.** A human reads the proposal and decides the exact scope to accept.
The rationale on each proposed span is what makes that reviewable.

**Accept.** `acceptance.accept_proposal` records the action: the exact resolved
scope, the full semantic diff of what it changed, the selection rule as
evidence, and who accepted it when. Only spans named in the scope are accepted —
silence is never acceptance. Accepting over a prior artifact merges rather than
replaces, so a later content batch cannot silently discard an earlier one's
reviewed work.

**Commit.** `oracle.accepted_inputs_payload` writes the artifact; the reviewer
commits it here. That commit *is* the acceptance action of record.

## One artifact, two halves

The file carries both the accepted result and the review evidence, and the
loader keeps them separate:

* `AcceptedInputs.oracle` is what the publication gate judges against. It
  excludes reviewer, timestamp, batch grouping, and diff, because review process
  is not identity-bearing — re-reviewing an unchanged classification must not
  remint a projection (#137 acceptance criterion 11).
* `AcceptedInputs.batches` / `.acceptances` are the auditable evidence. The
  build carries them into persistence, because the gate requires an explicit
  acceptance record for every span in reconstructed state.

They live in one file so they cannot drift apart. The independence that matters
is untouched: this is committed bytes a reviewer accepted, never anything
derived from a candidate or from persisted output.
