# PR #157 — CRD Issue 5d representation schema 3 — remediation log

Detail for the Codex review rounds on PR #157 (`feature/issue-5d-representation-schema-3`).
The PR body carries only the summary, the deviation, and the gate evidence; this file carries
the reasoning, the defect-family audits, and the deliberately deferred items.

Sibling to `pr-155-issue-137-remediation-log.md`, which covers the schema-2 rounds.

Nothing in this PR accepts, publishes, activates, or persists mechanical authority.
`accept_proposal` is never called, no production `AcceptedInputs` exists, and
`src/afterworlds/ingestion/mechanical/oracles/` still holds only its `README.md`.

---

## Round 1 — P1: the counterpart rule was not enforced on final effective authority

**Finding.** Schema 3 admits `ParticipantRole.COUNTERPART` only where a closed structure in the
same component establishes the binary relation — in schema 3, `MovementTransportFact`. That was
enforced during base `RepresentationDraft` validation only, so `apply_override_set()` could
publish an effective state the base schema rejects.

**Defect family.** Identical in shape to the option-set contract remediated on PR #155: a
per-scope override operation cannot see the whole component's final state. A complete component
patch never sees what it replaced, and a fact-scoped `DISABLE` is not resolved into removal until
`_finalize_component`.

**Fix.** `_verify_final_participant_rules`, a sibling of `_verify_final_option_sets`, run after
the whole ordered set is applied and suppression resolved. It projects the effective view back
into the representation's own types and calls `component_participant_violations` — the same
function the corpus is built under — rather than restating the rule, which would drift from the
schema it enforces.

**Negative control.** Disabling the new check fails 5 refusal tests.

**Found in the same pass, not reported.** Counterpart establishment was flattened across option
arms: a transport fact in one arm established the counterpart for a mutually exclusive sibling.
Fixed in `1c73c2f` with directional establishment — a component-level fact establishes for every
arm, an option-level fact only for its own.

---

## Round 2 — P2: malformed input crashed the participant scan instead of reporting

**Finding.** A draft carrying a malformed fact or applicability raised `TypeError` out of the
participant scan, destroying the whole collected report rather than adding a finding to it.

**Defect family.** Validation must return findings, never raise. Audited all four paths that walk
declared facts; guarded each with `_is_declared_fact`.

**Negative control.** Bypassing the guard restores the `TypeError`.

---

## Round 3 — P1: schema 3 could not represent its own motivating rule

**Finding.** Grappled's *"unless you are Tiny or two or more sizes smaller than it"* qualifies the
grappler-paid surcharge **alone**, not the transport permission beside it. A component-level
`applies_when` made transport vanish for a Tiny subject; splitting the facts into two components
was refused by the counterpart rule, because the second component would establish nothing.

**Boundary stop, and an owner correction.** The first proposed fix — relaxing the counterpart rule
to record scope — was refused by the Owner on a cardinality ground the code could not see: *"One
Grapple per Hand"* limits the **grappler's** capacity, never the target's, so one Grappled
condition may carry several concurrent grapple relations. A record-scoped relaxation would have
encoded "exactly one counterpart per record", which the source does not say.

**Corpus check — not a Grappled anomaly.** Water Elemental's Whelm and the Aboleth's curse each
qualify exactly one of three coordinate claims; Cleave and Light do the same for a damage
modifier.

**Design.** `FactQualifier(fact_key, applies_when, option_key="")` held on `ComponentDraft`,
addressed by `(option_key, fact_key)` — the content-derived coordinates provenance and override
targeting already use. Component, option, and fact applicability compose conjunctively.

**Second boundary stop, and Owner Decision.** `_provenance_index` collapses claims by
`(target_kind, target_key)`, so a FACT-targeted qualifier span could not be separated from the
fact's own span set. Three dispositions were put to the Owner; option (a) was chosen: a distinct
`ProvenanceTargetKind.FACT_QUALIFIER` sharing the fact's coordinates, with the *kind* doing the
separating. Changing `fact_target_key`'s shape would have moved stored override targets and the
schema-1 identity literals; overloading `ProvenanceRole` would have misclassified substantive
authority as supporting.

`FACT_QUALIFIER` joins `PROVENANCE_REQUIRED_KINDS`. It is **not** a `RuleOverride` target kind —
qualifiers are not independently overridable.

**Storage.** `rp_mech_facts.applies_when`, additive nullable JSON, migration `0029`, no backfill.
The fact row carries the qualifier's exact scope, so a dangling qualifier is unrepresentable
rather than merely invalid.

---

## Round 4a — P2: malformed qualifier coordinates crashed before they were consumed

**Finding.** `declared_provenance_targets` raised `TypeError: unhashable type: 'list'` on a
qualifier whose `fact_key` was a list. `fact_qualifier_violations` recorded the finding correctly,
but the pass continued into the `FACT_QUALIFIER` target-key set and hashed the tuple containing it.

**Family audit found a second, already-broken site.** `component_participant_violations` keys a
scope dict by `option_key` and raised the same way — it would have been the next crash after an
isolated patch to the reported line.

**Fix.** One shared predicate, `_usable_qualifier_coordinates`, encoding the rule *an invalid
coordinate is reported by validation and never subsequently consumed by code that assumes a valid
one*, applied at every coordinate-keying site: `declared_provenance_targets`, the counterpart
scan's scope dict, `ComponentDraft.qualifier_for`, and the override path's supplied-qualifier dict.
`qualifier_for` **declines** rather than compares, so a malformed coordinate is never coerced into
a match.

**Checked and deliberately left alone.** `_qualifiers_for` in `persistence.py` builds coordinates
from `String` columns; `_build_fact_qualifier` in `patches.py` already rejects non-string
coordinates as `InvalidPatchError` before a body exists.

**Negative control.** Weakening the predicate to its old shape fails 10 tests.

---

## Round 4b — P2: the validator and its consumers disagreed on what a string is

**Finding.** The consumers declined anything not exactly `str`; the validator still used
`isinstance`. It disagreed in both directions, and both were defects:

* an unhashable `str` subclass passed validation and then raised in the membership test; and
* an ordinarily hashable `str` subclass passed validation **with no finding** while every consumer
  silently dropped it — authority vanishing with nothing recording that it existed, and no crash
  to notice. That is the worse of the two, and it cannot be caught by a "does it crash" assertion.

**Fix.** The validator uses the same shared predicate, applied before `scope` is constructed or
hashed, with an assertion that the two agree so they cannot drift again. Type and emptiness are
reported separately: "not a string" and "names no fact" are different defects.

**Negative control.** Restoring `isinstance` fails 5 tests.

---

## Round 5 — Owner Decision on finding 6: REPLACE drops the qualifier

**Finding (P1, `[OWNER DECISION]`).** The implemented semantics retargeted a surviving
source-authored qualifier from the replaced fact's key onto the replacement's. Codex read ADR-005d
Decision 10's "complete validated replacement" as incompatible with that. The risk was reproduced
empirically: `REPLACE` constrains nothing about the replacement's *family*, so Grappled's size
clause could end up limiting an unrelated `StateEffectFact` while still citing the size clause's
source span.

**Owner Decision.** Drop the existing `FactQualifier` when its fact is `REPLACE`d. Do not retarget
or inherit. Family or type compatibility is not sufficient evidence that the old qualifier remains
semantically applicable, and automatic inheritance would preserve source-authored semantics the
replacement payload never declared.

**Settled override semantics.**

| Operation | Qualifier |
| --- | --- |
| `FACT` `REPLACE` | old fact and its qualifier both leave the view; the replacement is unqualified |
| `FACT` `DISABLE` | fact and qualifier disappear together (by construction — it lives on the fact) |
| `FACT` `APPEND` | appended fact is unqualified |
| `COMPONENT`/`RECORD` complete replacement | may explicitly carry `fact_qualifiers` with the body |
| any | qualifiers remain not independently `RuleOverride`-targetable |

This **preserves** existing `REPLACE` semantics rather than changing them, so no ADR-005d or
CRD Issue 5d amendment is required.

**Consequence, pinned deliberately.** Dropping a qualifier is a *widening*, and a qualifier can
name `COUNTERPART` — so a component whose only counterpart reference lived in a dropped qualifier
now accepts a `DISABLE` of its transport where it previously refused one. That is the correct
consequence of the decision, not a weakened invariant, and it is asserted with a control case
proving `_verify_final_participant_rules` still reads qualifiers at all.

**A conditional replacement is still authorable** — as a component patch carrying its own
`fact_qualifiers`, where the qualifier is the override's own authority and names no 5c span.
That path is unchanged and already covered.

**Unconsumed provenance after application is pre-existing and by design.** After `REPLACE` the
candidate's `FACT_QUALIFIER` provenance claim has no consumer in the effective view. `DISABLE`
already does exactly this to a suppressed fact's own span claims. Override application layers over
an immutable base projection; the candidate's provenance is not rewritten by it.

---

## Deferred — recorded, not fixed in this PR

* **`option_set_violations` hashes `option.semantic_key` without an exact-type check.** An
  unhashable `str` subclass raises `TypeError` out of validation, the same family as round 4a/4b.
  Present unchanged on `origin/main` at `ad32b4f`, so it is **not introduced by `FactQualifier`**
  and is outside PR #157's scope. Owner direction: do not widen this PR for it; record it for
  separate remediation. Disposition: `out of scope`.

* **Source-authored cross-record suppression of a surcharge** (Shambling Mound's Engulf, *"costing
  it no extra movement"*). Unresolved **base-projection** semantics. Owner direction: do not assign
  source-authored cross-record suppression to `RuleOverride` — an override is authored suppression,
  while this is what the source itself says. Retained in `docs/architecture/known_unknowns.md`.
  Disposition: `owner decision needed`.

* The five further schema-3 successors retained in `known_unknowns.md`: counterpart establishment
  outside transport, third-party size comparisons, ratio-form movement costs, rounding supplied by
  the governing rule, and applicability over a capability predicate. Disposition: `out of scope`.
