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

---

## Round 6 — P1: every merged schema version must serialize its own key set

**Finding.** Schema 3 added `fact_qualifiers` to the canonical component payload while the
serializer branched on **schema 1 only**. A schema-2 candidate fell through to current behaviour
and gained a key its merged contract never had. `projection_payload` deliberately serializes
reconstructed history under the candidate's *own* recorded version, so the extra key re-derived
the projection UUID and payload hash and `verify_persisted_state` rejected otherwise unchanged
schema-2 state. Schema 2 also silently serialized a nonempty schema-3 qualifier where schema 1
refuses.

**Reproduced before fixing, and proved reachable rather than latent.**

```
payload hash, this branch  : 8a57c1e239dd196d02c951dce5e780ab38447890b32db80a1b5fdd53cb97d345
payload hash, merged shape : 5883adc051d22599856a5705c8bbfdab5c91e8e39b66fb22f4f11a2d9d88c39d
agree                      : False
```

`reconstruct_candidate` reads `header.representation_schema_version` verbatim
(`persistence.py:730`) with no version filter — that is why the `SCHEMA_1_VERSION` omission branch
exists at all — and `verify_persisted_state` calls `identify_projection` directly rather than
through `validate_schema_binding`.

**Owner Decision (2026-08-22), superseding the earlier "no schema-2 reconstruction branch"
direction.** That direction rested on the absence of accepted or published schema-2 authority, but
the relevant boundary is *persisted identity*, not publication: CRD Issue 5d permits persisted
proposed/draft state and requires persisted state to reconstruct deterministically.

**How it slipped through.** `b898922` widened
`test_the_current_component_payload_still_emits_both_schema_2_keys` to include `fact_qualifiers`
instead of leaving the schema-2 assertion intact and adding a schema-3 one. That widening deleted
the only guard, and nothing else pinned a merged version's payload shape when serializing under
that version.

**Fix — the general rule, not another version `if`.** `_MERGED_COMPONENT_FIELDS` gives every merged
version its own explicit component key set; `_COMPONENT_FIELDS` pairs each post-schema-1 key with
both its emitter and its `holds_meaning` proof, so the loop that omits a field is the loop that
proves the field is empty. The registry rows are written as literals rather than keyed by
`REPRESENTATION_SCHEMA_VERSION`, because keying the current row that way would let schema 4
silently inherit schema 3's row and delete schema 3's — the exact failure the table exists to
prevent. A module-level assertion requires the current version to have a row, so a mint that
forgets one makes the current contract unserializable rather than quietly wrong.

`UnsupportedSchemaVersionError` is distinct from `LegacySchemaPayloadError` on purpose: one means
*this draft* says more than the named contract can hold, the other means the contract itself is
unknown. The version is resolved once in `representation_payload`, before any component, so a
draft with **no components** still fails closed instead of deriving an identity under a contract
nobody recognises.

**Canaries, one per merged version, independently captured.** Every `SCHEMA_2_*` literal in
`test_review_round_9_schema_version_payloads.py` was produced by running the pre-change code at
`7395c52` (a `git archive` export of `origin/main`, not a worktree), so the claim is falsifiable.
The captured structural hash equals the `SCHEMA_2_HASH` literal `test_review_round_6_schema1_identity`
already pins from its own independent capture — the cross-check that the export really ran old
code. The widened round-6 assertion is split back into a schema-2 test and a separate schema-3 one.

**Negative control.** Restoring the pre-fix resolution (schema 1 special-cased, everything else
current) fails **16** tests.

**Sibling audit — two more schema-3 payload changes, both `already safe (fails closed)`.**
`SizeComparison` gained `at_most`/`measured`/`reference` and `MovementCostFact` gained
`payer`/`rounding`. Neither can produce a *silent* identity divergence: both are refused at the
reconstruction boundary (`any_of[0] is missing ['at_most', 'measured', 'reference']`,
`movement_cost payload is missing ['payer', 'rounding']`), so a schema-2 projection containing one
fails to reconstruct rather than re-identifying wrongly. Consequence stated rather than fixed: such
a projection **cannot be verified at all**, and reproducing it would require per-version fact
schemas plus a value for `payer` the source never stated. Found in this pass, before patching, and
dispositioned — not a returning review finding.

**No schema change.** Version and structural hash unmoved at
`43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05`; schema-3 semantics,
vocabulary, override behaviour, and current canonical payload untouched.

**Two consequences found by the gate, not by review, and fixed in the same commit.**

1. *`verify_persisted_state` must report an unrecognised declaration, not raise.* Failing closed
   and collecting findings are the same act there: a stored `representation_schema_version` this
   build cannot serialize is tamper or a downgrade, and raising past a caller assembling findings
   would destroy the rest of the report — the same rule round 2 applied to the participant scan.
   The `UnsupportedSchemaVersionError` is caught beside the existing
   `PersistedStateReconstructionError` and returned as a finding. Negative control: removing the
   catch fails the new tamper test with the raw exception.

2. *`test_representation_schema_identity.py` used a fabricated `"5d-representation-schema-99"` in
   seven places.* Those cases passed only because a fabricated version silently borrowed the
   current component shape — the borrowing this remediation removes — so they were exercising the
   defect. Five now use `SCHEMA_2_VERSION` with its real captured hash, which is the truer stand-in
   (an actual superseded union rather than a hypothetical one). `OTHER_VERSION` is kept where
   nothing is serialized under it: the oracle payload, the hash-only half of the perturbation test,
   and the new unknown-declaration tamper case.

   `test_a_candidate_of_only_unaffected_families_still_reidentifies` is the one whose assertion
   changed rather than moved, and it is called out here because an edited identity canary is
   exactly the shape this round's finding was about. Its whole-payload equality was satisfiable
   *only* under the fabricated borrowing. It now asserts the equality where it holds — the records
   block and the component's own facts are byte-identical across the two contracts — and still
   asserts the UUIDs differ, which is the defect the declaration exists to prevent. The property it
   used to need is now guaranteed structurally instead: no two merged versions share a component
   key set, so content alone cannot collide across contracts before the declaration is consulted.

---

## Round 7 — P2: the verifier reported half the refusal family and raised the other half

**Finding.** Round 6 taught `verify_persisted_state` to *report* an unrecognised stored
declaration. It taught it only half the family: rows carrying meaning their declared version has
no key for raise `LegacySchemaPayloadError` from the same `identify_projection` call, and that
still propagated. Codex reproduced it by giving a persisted schema-2 fact row a non-null
`applies_when` — reconstruction succeeds, the disagreement surfaces only on re-serialization.

**Disposition.** Operational reliability, not a new security model. Malformed or inconsistent
persisted authority fails closed; verification and publication callers receive actionable findings.
No signing, authentication, MACs, or other adversarial-security machinery is introduced — the
change is one `except` clause widened to the sibling exception.

**Why it is the same defect.** Either the version is one this build cannot serialize, or the rows
carry meaning that version has no key for. Both mean the stored declaration and the stored rows
disagree, no identity can be derived, and a caller assembling findings must receive one rather
than an exception through the middle of its report. Failing closed and reporting are the same act.

**Sibling audit, bounded to this function's own raise sites as directed.**

| Call | Raises | Disposition |
| --- | --- | --- |
| `_header` | `ProjectionNotPersistedError` | already handled |
| `reconstruct_candidate` | `PersistedStateReconstructionError` | already handled — and it already wraps `MalformedFactPayloadError` / `UnknownFactFamilyError` |
| `identify_projection` | `UnsupportedSchemaVersionError` | handled in round 6 |
| `identify_projection` | `LegacySchemaPayloadError` | **patched** |
| `compute_persisted_state_digest` | both of the above, via `projection_payload` | `already safe` — reached only after the call above proves neither fires. An ordering, not a coincidence, and the source now says so |

Not widened past those. No unrelated historical-schema work.

**Coverage.** A persisted schema-2 row carrying schema-3 qualifier data yields a finding naming
both `fact_qualifiers` and the contract it arrived with; the valid schema-2 projection beside it
still verifies clean; a genuine payload-hash and derived-id mismatch is still reported, proving the
early return did not swallow the ordinary comparisons; and the publication gate returns a
`PERSISTED_STATE` refusal rather than raising out of the publication path. The gate case is built
on the bound-release fixture rather than this module's own package, because the gate stops at step
0 on a release it cannot verify and would never reach the persisted-state proof.

**Negative control.** Narrowing the catch back to `UnsupportedSchemaVersionError` alone fails 2
tests with the raw exception.

**No schema, vocabulary, identity, or hash change.** Version and structural hash unmoved at
`43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05`.
