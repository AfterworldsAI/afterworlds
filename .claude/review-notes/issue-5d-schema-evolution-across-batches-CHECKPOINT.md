# CRD Issue 5d — schema evolution across accepted content batches

**Status: DESIGN ONLY.** Nothing implemented, minted, accepted, published, activated, or retired. No
branch. `accept_proposal` never called. `oracles/` untouched. Zero tracked changes.

**Baseline.** `origin/main` = `HEAD` = `319e61c0e9499d9bed68e7f06efd57beb615da90` on `main`.

**Supersedes on read, retained on disk:** the verdict sections of
`issue-5d-hazards-1-sibling-AUDIT.md` (§3–§4) and
`issue-5d-hazards-1-schema-closure-CHECKPOINT.md` (§3.2, §5, §6). The regenerated proposal and audit
JSON remain current and need no revision — they are schema-3 artifacts and are correct as such.

---

## 1. The defect, and two more found beside it

**Reported defect — confirmed.** `acceptance.py:257–263` rejects a proposal whose
`(schema_version, schema_hash)` differs from `prior.oracle`'s. The committed artifact declares
`5d-representation-schema-3` / `43ed330d…`; a hazards proposal requires schema 4. So `prior=` is
closed today.

Two further defects were found while reading the seam. **Both are latent only because
`oracle.schema_version` currently equals the build's `REPRESENTATION_SCHEMA_VERSION`.** They become
live the moment schema 4 merges, and they are the reason PR A cannot be "types only".

| | Defect | Site | Consequence when schema 4 merges |
|---|---|---|---|
| **D-2** | `oracle_payload` serializes the accepted representation under the **build's** current schema, not the artifact's own declaration — `representation_payload(oracle.representation)` with no `schema_version` argument | `oracle.py:311` (and `gate.py:294`) | a schema-3 artifact is canonicalized under schema-4 keys, silently re-identifying accepted authority. This is precisely the failure **Owner Decision 2026-08-20 (Option A)** was taken to prevent, reappearing at the oracle seam |
| **D-3** | `proposal_payload` serializes `proposed_representation` under the default rather than `proposal.schema_version` | `proposal.py:149` | the recorded `proposal_identity` of the conditions-1 proposal (`14587d5b…`) stops being reproducible from the retained proposal artifact on a schema-4 build |
| **D-4** | the committed-artifact loader checks key sets **exactly** (`_require` rejects missing *and* extra; `_applicability` delegates to `applicability_payload_violations`), with one narrow `optional` escape for the schema-1 component case | `oracle.py:338–360, 422+` | **the committed conditions-1 oracle stops loading altogether** as soon as schema 4 adds a field to `Applicability`, because the loader demands the new keys and the file does not have them |

**D-4 is the severe one.** Merging schema-4 types without version-aware loading does not merely block
`prior=` — it breaks the committed artifact and every test that loads it.

## 2. Exact blast radius on accepted authority

Read from the committed artifact. Schema 4's fifteen additions are strictly additive to the *type
surface*, but three of them touch structures the accepted artifact **contains**, and neither
`fact_payload` nor its nested value objects are version-aware:

`fact_payload` is `asdict()` over every field with **no version gate**, and `fact_key` is
`sha256(canonical_bytes(fact_payload))[:16]`. Nested value objects emit **all** fields including nulls —
verified against the committed bytes:

```
applies_when : {"any_of": [], "comparison": "equals", "kind": "quantity_threshold",
                "negated": false, "phase": null, "quantity": "condition_level",
                "trigger": null, "value": 6}
advantage    : {"family": "advantage", "state": "disadvantage",
                "roll": {"ability": "dexterity", "actor": "subject", "context": "saving_throw"}}
```

| Structure in the accepted artifact | Instances | Schema-4 addition | Payload changes? |
|---|--:|---|---|
| `RollSpec` (inside `advantage` ×22, `automatic_outcome` ×10) | **32** | H-11 `skill` | **yes** → 32 `fact_key`s move |
| `ConditionLevelFact` (Exhaustion) | **2** | H-5 `cause_scoped` | **yes** → 2 `fact_key`s move |
| `Applicability` (4 components + 1 option + 1 fact qualifier) | **6** | H-4/H-10/H-12/H-14 fields | **yes** |
| `ComponentDraft.recurs` | — | H-1 | **no** — already governed by `_MERGED_COMPONENT_FIELDS` |
| `ScalingFact` ×2 | 2 | H-7 adds an enum *member* | **no** — member addition does not alter existing payloads |
| `ReferenceDraft` ×15 | 15 | H-8 relaxes nullability | **no** — existing values are non-empty |
| `DamageFact`, `AbilityCheckFact` | **0 accepted instances** | H-9, H-11 `alternatives` | **no effect on accepted content** |
| `MovementCostFact` (the one `FactQualifier` target, `6e4c12d0fc868578`) | 1 | none | **no** — the qualifier's back-reference survives |
| all other families (`action_restriction`, `condition_effect`, `critical_hit_rule`, `damage_response`, `movement_permission`, `movement_transport`, `quantity_multiplier`, `sensory_capability`, `speed_modification`, `state_effect`, `transformation`) | 30 | none | **no** |

**That table describes the design as first drafted, and it no longer describes the build.** Under the
omission rule Owner Decision 2026-08-24 settled (§4.4), a post-schema-3 field is absent from the
canonical payload when it carries no meaning — so a `RollSpec` with no `skill`, a `ConditionLevelFact`
that is not cause-scoped, and an `Applicability` with none of the four new operands each emit exactly the
bytes they emitted under schema 3.

**Net, as built: zero fact keys and zero applicability payloads move.** All six inherited collections are
byte-identical, all 185 spans, all 16 records, all 54 component keys, all 15 prose bindings, all 15
references, all 161 stored provenance coordinates, and all batch/acceptance evidence are untouched, and
`oracle_identity` stays at `a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda`. The rows
above are retained because they name *which* structures the additions touch, which is still true and
still the reason the omission rule had to exist.

Designing schema 4 to avoid this is not available: H-4, H-5, H-10, H-11, H-12 and H-14 are each
required for `hazards-1` to reach zero.

---

## 3. Architectures compared

| | Architecture | Verdict |
|---|---|---|
| **1** | **Registered lift `(old version, old hash) → (new version, new hash)`, allowed only when verified element-by-element as a semantic superset** | **RECOMMENDED** |
| **2** | Normalize prior and proposed into a declared common schema before keyed union | **Reject.** The "common schema" for a schema-3 artifact and a schema-4 proposal *is* schema 4, so this is architecture 1 with the compatibility proof deleted. It also normalizes silently: a prior element that does **not** map cleanly would be reshaped rather than refused, which is the "reinterpreting prior authority" this design exists to prevent |
| **3** | Full reacceptance or supersession of earlier authority | **Reject.** Violates *"acceptance names the exact proposal the Owner reviewed"* — it would restamp the conditions batch against a proposal the Owner never saw, and discard the reviewer, timestamp, diff, and `proposal_identity` that are the acceptance action of record. `accept_proposal` has no supersession semantics and says so |
| **4** | Multiple per-schema artifacts composed later | **Reject.** Violates the settled one-artifact/one-oracle contract. `oracles/README.md` and the committed resolver refuse outright when two artifacts claim one release, and `committed_oracle_for` resolves exactly one. It also defers the compatibility question to compose time without ever answering it |

Architectures 2–4 each violate the one-artifact, disjoint-batch, prior-preservation contract. **One
recommendation: architecture 1.**

---

## 4. The recommended design

### 4.1 Where compatibility is declared

A registry in a new `schema_lift.py`, keyed by the **exact pair**, never by version ordering:

```python
LIFT_ID = "5d-lift-schema-3-to-4"

SCHEMA_LIFTS: dict[tuple[str, str], SchemaLift] = {
    ("5d-representation-schema-3", "43ed330d…e05"): SchemaLift(
        lift_id=LIFT_ID,
        to_version="5d-representation-schema-4",
        to_hash="<the schema-4 hash, pinned literally>",
        ...
    ),
}
```

A literal `to_hash` — not `representation_schema_hash()` — so an unrelated later edit to the union
invalidates the lift instead of silently re-authorizing it. `"newer version"` is never evidence: an
unregistered pair raises `UnknownSchemaLiftError` and `prior=` fails closed.

### 4.2 How an old artifact keeps loading

Loading becomes version-aware and stays strict. `load_accepted_inputs` resolves the artifact's declared
`(version, hash)` to a registered **shape contract** and parses under *that*, so a schema-3 file is
parsed as schema 3 forever — fixing **D-4**. The exact-key-set rule is preserved per version; it is the
*version* that is resolved, never the strictness that is relaxed. An artifact declaring a
`(version, hash)` pair with no registered contract fails to load rather than being parsed hopefully.

This generalizes the existing `_MERGED_COMPONENT_FIELDS` registry — a table of per-version key sets
written as literals for exactly this reason — from components to facts and nested value objects.

### 4.3 When and how the prior representation is lifted

Once, inside `accept_proposal`, before `_merge_representation`:

1. Load `prior` under its declared schema (§4.2).
2. Resolve `SCHEMA_LIFTS[(prior.version, prior.hash)]`; require its `to_*` to equal the proposal's
   declared pair exactly. Otherwise fail closed.
3. Walk every prior element and map it to schema 4. Every schema-4 field absent from schema 3 takes
   its **declared default**, which must be semantically neutral — verified per field:
   `RollSpec.skill=None` ("the source names no skill"), `ConditionLevelFact.cause_scoped=False`,
   every new `Applicability` field `None` under a kind that does not populate it,
   `DamageFact.maximum_dice=None`, `AbilityCheckFact.alternatives=()`.
4. **Rewrite `FactQualifier.fact_key` back-references whose target key moved**, and assert every
   qualifier still resolves. (For conditions-1 the single qualifier targets `MovementCostFact`, which
   is untouched, so its key `6e4c12d0fc868578` survives — but the lift must handle the general case.)
5. **Verify**: the prior's canonical payload is byte-identical under both schemas, collection by
   collection. *As built* this replaced steps 3 and 4 outright rather than supplementing them — the
   omission rule (§4.4) means an element accepted under schema 3 already has its schema-4 canonical
   form, so there is no default to apply and no key to rewrite. Any difference raises
   `SchemaLiftError`.
6. Record a `SchemaLiftRecord(lift_id, from_version, from_hash, to_version, to_hash,
   verified_collections)` on the **evidence** half of `AcceptedInputs`, never on `AcceptedOracle` —
   review and migration process is not identity-bearing, the same separation `batches`/`acceptances`
   already observe. The last field is the collections proved, by name. It carried per-collection
   element counts until #137 round 3, when they were removed as unverifiable: a committed artifact
   supersedes its predecessor and later batches merge into the same collections, so no loader can
   re-derive the pre-lift extent to check a count against (ADR-005d Decision 6, amended 2026-08-28).

Then `_merge_representation` runs unchanged: both sides are now schema 4, and the keyed union is
disjoint by batch as before.

### 4.4 Is the prior canonical payload byte-identical?

**Yes — proved element by element, not argued.** This section previously answered "no, and this is the
design's one real cost." Owner Decision 2026-08-24 rejected that cost, and the mechanism that removes it
is smaller than the one it replaces:

> A field introduced after schema 3 is **omitted from the canonical payload when it carries no meaning.**

An absent field and a field at its declared default say the same thing, so one canonical form serves
both — and a schema-3 element therefore *already has* its schema-4 canonical form. Nothing is rewritten
for it to be inherited.

The rule is **value-keyed, never version-keyed.** A fact's canonical form does not depend on which schema
is declared; the declared version decides only **legality**. That is what keeps it from being a second
canonicalization philosophy coexisting with Owner Decision 2026-08-20's version-keyed component rule —
there is one rule for content and one for component keys, and they do not overlap.

Fields introduced at or before schema 3 keep unconditional emission. That is load-bearing: the committed
artifact contains `"applies_when": null` and `"fact_qualifiers": []`, so switching them to omit-when-empty
would move exactly the identities this rule exists to hold still.

`verify_lift` therefore **proves** rather than transforms: it canonicalizes the prior under both the
source and the destination schema and compares bytes, collection by collection, before anything is
re-declared. Nothing is normalized, reshaped, or defaulted on the way through. A transforming lift has to
argue that its mapping preserved meaning; this one demonstrates that nothing moved.

### 4.5 Combined oracle payload and identity

`oracle_payload` gains the artifact's own `schema_version` (fixing **D-2**), so it canonicalizes under
what the artifact declares rather than what the build happens to implement. The merged artifact then
declares schema 4, its `representation_schema` block moves to `{version: …-4, hash: <schema-4 hash>}`,
its representation is the disjoint keyed union of lifted conditions plus hazards, its `spans` grows from
185 to 185 + the hazards scope, and `obligations` is re-derived. **`oracle_identity` changes** — the
expected consequence of extending content, and now also of the lift, which the `SchemaLiftRecord` makes
auditable rather than mysterious.

### 4.6 How prior proposal identity stays truthful

`AcceptanceBatch.proposal_identity` for `conditions-1` stays `14587d5b…` **verbatim**. It is stored, not
recomputed, and it names the schema-3 proposal the Owner actually reviewed — which is the invariant
*"acceptance names the exact proposal the Owner reviewed"*. The lift never touches `batches`,
`acceptances`, `rule`, `resolved_scope`, `diff`, `semantic_diff_hash`, `reviewer`, or `accepted_at`.

Fixing **D-3** is what keeps that identity *reproducible*: with `proposal_payload` passing
`proposal.schema_version`, re-deriving `14587d5b…` from the retained schema-3 proposal artifact still
works on a schema-4 build. Without the fix the recorded value would become unverifiable.

### 4.7 Fail-closed behaviour

| Transition | Result |
|---|---|
| `(version, hash)` pair not in `SCHEMA_LIFTS` | `UnknownSchemaLiftError` — refused |
| registered lift whose `to_*` ≠ the proposal's declared pair | refused |
| same version, different hash (union edited without a mint) | refused — the pair is exact, so a restamp is not a lift |
| schema/hash restamped on the artifact without an authorized lift | refused at load: the declared pair resolves to a shape contract the file does not satisfy |
| a prior element that does not map cleanly | `SchemaLiftError` — never normalized away |
| a prior element altered in the file | refused: the lift's verification compares against what was loaded, and the loader is exact-key-set strict |
| meaning-bearing data that a target version has no key for | the existing `LegacySchemaPayloadError` guard, extended from components to facts |

The equality check at `acceptance.py:257` is **not removed and not weakened**. It becomes: *equal, or a
registered lift that verified*. Everything else still fails.

### 4.8 Production seams, persistence, migration

| Seam | Change |
|---|---|
| `acceptance.accept_proposal` | equality check widened to the lift path; lift invoked before `_merge_representation`; `SchemaLiftRecord` recorded |
| `oracle.load_accepted_inputs` / `_representation` / `_applicability` / `_span` | version-aware shape resolution (**D-4**) |
| `oracle.oracle_payload` | pass `oracle.schema_version` (**D-2**) |
| `gate._comparable_collections` | pass the draft's schema version explicitly (**D-2**) |
| `proposal.proposal_payload` | pass `proposal.schema_version` (**D-3**) |
| `projection._MERGED_COMPONENT_FIELDS` | explicit `SCHEMA_4_VERSION` row: `{"applies_when", "options", "fact_qualifiers", "recurs"}` — its own assertion fails closed if omitted |
| `representation.fact_payload` | version-aware key set for facts and nested value objects |
| `AcceptedInputs` | new evidence field `lifts: tuple[SchemaLiftRecord, ...]`; serialized outside `AcceptedOracle` |
| ORM | one nullable JSON column `rp_mech_components.recurs`, the same pattern schema 2 used for `applies_when`. New fact families ride the family-keyed payload path with **no ORM change** |
| `reconstruct_candidate` | round-trip `recurs`; persisted-state digest changes shape |
| `validate_schema_binding` | unchanged — the merged artifact declares schema 4, which the build implements |

**No 5c seam is touched.** No published projection exists to migrate.

### 4.9 Does #137 or ADR-005d need clarification?

**ADR-005d — yes, one narrow amendment.** Decision 8 says meaning-changing corrections mint a new
projection UUID, and Decision 6 binds *"representation schema and semantic policy"* into projection
identity. Neither contemplates an accepted artifact spanning a schema succession. The amendment should
record that accepted authority may be carried across a schema succession **only** through a registered,
verified, semantically neutral lift; that the lift is evidence and never identity-bearing; and that a
lift is authorized per exact `(version, hash)` pair, never by version ordering.

**Issue #137 — no change required.** Contract 4 already requires the build to be reproducible from a
clean checkout and publication to compare persisted output against independent accepted authority; a
verified lift satisfies both. Contract 2's "silence is not acceptance" is untouched — the lift accepts
nothing.

---

## 5. Required tests

| # | Proves | Shape |
|--:|---|---|
| T-1 | schema-3 conditions authority lifts into schema 4 **with no payload difference at all** | load the committed artifact, canonicalize it under both schemas, and assert every one of the six collections is byte-identical — and byte-identical to the committed bytes themselves. Asserted as equality, not as an enumerated difference set: under the omission rule there is no difference to enumerate, and a test that listed one would re-encode the withdrawn design |
| T-2 | conditions acceptance evidence remains exact | `batches`, `acceptances`, `rule`, `resolved_scope`, `diff`, `semantic_diff_hash`, `reviewer`, `accepted_at`, and `proposal_identity == "14587d5b…"` byte-identical before and after |
| T-2b | the recorded proposal identity stays reproducible | re-derive `proposal_identity` from the retained schema-3 proposal artifact on a schema-4 build and assert `14587d5b…` (regression for **D-3**) |
| T-3 | schema-4 hazards merges as a disjoint keyed union | after the lift, `accept_proposal(prior=…)` succeeds; span scopes disjoint; all 16 conditions records **and** all 6 hazards records present; no duplicate semantic key |
| T-4 | unknown transitions fail | an unregistered `(version, hash)` pair raises `UnknownSchemaLiftError`; a lift whose `to_*` disagrees with the proposal is refused |
| T-5 | restamping without an authorized lift fails | edit the artifact's `representation_schema` to schema 4 leaving schema-3 content: load fails on the shape contract. Also: same version, different hash is refused |
| T-6 | altered prior content fails rather than being normalized | mutate one accepted fact, one applicability, and one provenance target in the artifact; assert refusal, not silent reshaping |
| T-7 | lifting is deterministic and idempotent | lift twice → byte-identical output; lifting an already-schema-4 artifact is a no-op that neither changes bytes nor records a second `SchemaLiftRecord` |
| T-8 | the result strictly reloads and reproduces its combined identity | serialize → `load_accepted_inputs` → `oracle_identity` equals the value computed before writing; `candidate_from_accepted_inputs` reproduces a projection whose derived ids are stable across the round trip |
| T-9 | **D-2 regression** | `oracle_payload` of a schema-3 artifact is byte-identical on a schema-3 build and a schema-4 build |
| T-10 | **D-4 regression** | the committed schema-3 artifact loads unchanged on a schema-4 build |

---

## 6. The fifteen additions, and H-16

Recorded here so this checkpoint is self-contained; the reasoning is in the ledger and audit.

**Admitted (15).** H-1 recurrence · H-2 effect/hazard termination · H-3 size-keyed quantity ·
H-4 threshold against a table-required quantity · H-5 cause-scoped condition levels ·
H-6 removal restriction · H-7 distance-fallen scaling · H-8 record-grain reference ownership ·
H-9 maximum damage dice · H-10 damage-outcome applicability · H-11 skill axis + check alternatives ·
H-12 roll-outcome applicability · H-13 damage modification · H-14 elapsed-duration threshold ·
H-15 ability-modifier-derived quantity with a floor.

Admission follows Issue #137 contract 3 and ADR-005d Decision 4 — *type it, or affirmatively
prose-bind it* — not a sibling count. The ≥2-rules/≥2-sections bar is a review heuristic from
`issue-5d-consolidated-schema-closure-CHECKPOINT.md` §4 and appears in no accepted authority. The
overfitting guard kept: *single-instance but structurally coherent* (a nullable `int`, a boolean, a
member whose parameters are data) is admitted; *clause-shaped* (an enum whose members each name one SRD
clause) is not.

**Rejected (1) — H-16 heterogeneous state trigger**, on semantics independent of sibling count: half its
operand (*"is choking"*) is fiction the SRD never defines mechanically.

### 6.1 H-6 verification — cause-scoped, not cross-record

```python
ConditionRemovalRestrictionFact(
    condition: ConditionKind,
    cause_scoped: bool,      # invariant: MUST be True for this family
    until: Applicability,
)
```

The fact lives on `hazard.dehydration` and states: *levels of Exhaustion **caused by this record**
cannot be removed until `until` holds.* It does not name, reference, or edit `condition.exhaustion`'s
own removal rule. It is a property of the levels this record causes.

**The `cause_scoped=True` invariant is the guard.** Without it the fact would claim something about
*all* Exhaustion, which would be an edit to another record's authority. With it, composition with
`condition.exhaustion`'s *"Finishing a Long Rest removes 1 of your Exhaustion levels"* is resolved at
adjudication time, which is where cross-record composition belongs (ADR-005d Decision 11 — 15c owns
adjudication).

**Therefore R-6 (cross-record suppression) is not reached.** Verified, not assumed.

### 6.2 H-16 verification — the OR must not become an AND

Source: *"When a creature runs out of breath **or** is choking, it gains 1 Exhaustion level at the end
of each of its turns."*

The hazard is real and specific: `ComponentDraft.applies_when`, `ComponentOption.applies_when` and
`FactQualifier.applies_when` **compose conjunctively** — `FactQualifier`'s own docstring says *"Scopes
narrow inward and never replace one another."* So putting the typed breath-expiry arm on `applies_when`
and the open arm in a prose binding on the same component would read as **AND**, publishing a rule the
source never wrote.

**Required representation: two sibling components**, each independently applicable:

| Component | Handling | Trigger | Facts |
|---|---|---|---|
| `suffocation_accrual_breath` | STRUCTURED | `applies_when` = the H-15 breath-expiry threshold | `ConditionLevelFact(EXHAUSTION, GAIN, 1)` + `recurs` |
| `suffocation_accrual_choking` | PROSE_BOUND | prose binding over *" or is choking"*, `contextual_applicability` | same accrual, same `recurs` |

Two independently-applicable sibling components are a disjunction expressed as a sum of products — no
operator, no nesting, no predicate language. They must **not** be `ComponentOption`s: options are an
**exhaustive actor choice**, and these are triggers the actor does not choose.

**One verification item PR A must settle before the manifest is construction-ready:** whether
`validate_representation` permits two sibling components of one record holding the same typed fact. If
it does not, the fallback is a single component with a disjunctive trigger, which would reopen H-16.
This is an engineering verification, not a decision.

---

## 7. PR sequencing

**Adopted as proposed, and repository evidence strengthens it rather than disproving it.**

**PR A — schema 4 and the evolution mechanism.** The fifteen types with validation and tests; the
`SCHEMA_LIFTS` registry and lift; version-aware loading and canonical emission (**D-2, D-3, D-4**);
`_MERGED_COMPONENT_FIELDS[SCHEMA_4_VERSION]`; the `recurs` migration and round-trip; typed override
coverage for the new families and a decision on whether `recurs` is overridable; the ADR-005d
amendment in §4.9; T-1 … T-10. **No production proposal acceptance, no oracle modification.**

**D-4 makes PR A indivisible.** Schema-4 types cannot merge without version-aware loading, or the
committed conditions-1 artifact stops loading and its tests fail. "Types only" is not a viable smaller
PR.

**Between A and B.** Regenerate `hazards-1` against the *exact merged* schema 4 — never against a
design sketch — and put the zero-unresolved proposal through human semantic review.

**PR B — acceptance.** `accept_proposal(prior=<the sole committed artifact>)` extending it in place.
**No schema development.** The lift executes here for the first time in production, on the path PR A's
tests already exercised.

### Stop conditions

Stop and surface rather than widening scope if:

* any prior element fails to lift cleanly — that is a semantic change, not a merge conflict;
* preserving `conditions-1` would require weakening the equality check, restamping the artifact, or
  re-accepting the batch;
* the lift would need to alter any accepted span, disposition, semantic key, or evidence field;
* two sibling components holding one fact are rejected by validation (§6.2), reopening H-16;
* the regenerated `hazards-1` does not reach zero against merged schema 4 — re-report, do not widen the
  mint;
* a second artifact or a second oracle for the release becomes attractive for any reason;
* any R-1…R-7 successor becomes load-bearing beyond the recorded R-3 disposition.

---

## 8. Owner Decision — one, narrow

Not manufactured from an evidence heuristic. It is an identity-preservation question on which the Owner
has already ruled once, in the adjacent seam.

> **Owner Decision 2026-08-20 (Option A)** established, at the `0027 → 0028` boundary, that a projection
> persisted under schema 1 must still reconstruct with its original UUID, payload hash, derived IDs and
> recorded digest after a schema upgrade — and that *"every merged version serializes exactly its own
> key set."*

That ruling governs **persisted projections**. This is the **accepted-artifact** case, and it is not
identical: no projection is persisted, published, or activated here.

**The exact question:**

> When accepted authority is lifted across a schema succession, may the derived `fact_key`s of already
> accepted facts move, or must schema 4 preserve them byte-for-byte?

### Settled — zero identity movement

**Owner Decision 2026-08-24, against the recommendation this checkpoint originally made.**

This section once presented two options and recommended the one that let derived keys move, arguing that
the accepted-artifact case lacked the persisted-state consumers which motivated Owner Decision
2026-08-20. The Owner answered that argument directly:

> Do not permit previously accepted fact keys or provenance coordinates to move… The absence of published
> consumers or overrides does not authorize identity churn.

**Consumer absence is not the authorization.** The recommendation is withdrawn in full, and the option
table that carried it is deleted rather than annotated — a superseded prescription left standing beside
the live one gives the next reader two contradictory instructions, which is exactly the failure this
document exists to prevent. What the reasoning was is recorded in the paragraph above; what it
*prescribed* is gone.

**What the Owner's ruling required, and what was built:**

| Required | Built | Evidence |
|---|---|---|
| The combined oracle declares schema 4 with a new oracle identity | `REPRESENTATION_SCHEMA_VERSION = "5d-representation-schema-4"`; the artifact's own identity follows from its declaration | `test_accept_across_schema_succession` |
| New hazards content uses schema-4 shapes | Ten additions across five new families, four widened fields, one component key | `representation.py`, `test_fact_families` |
| Every inherited `conditions-1` element retains its canonical payload and target coordinates | All six collections byte-identical against the committed bytes; `oracle_identity` unmoved at `a0f0bd2f…`; 15 references and every coordinate re-derive | zero-movement probe, `test_record_owned_references`, `test_declared_schema_canonicalization` |
| Schema-4 fields carrying no meaning are absent from an inherited element's canonical payload | `_PostSchema3Field` / `_POST_SCHEMA_3_FIELDS`, value-keyed rather than version-keyed | `test_declared_schema_canonicalization` |
| A schema-3 declaration carrying schema-4 meaning fails closed | `post_schema_3_violations` over the identity-bound `introduction_manifest()` — every schema-4 family, every widened vocabulary member, every new field, and the record-owned reference form — plus `LegacySchemaPayloadError` at both canonicalizing seams | `test_schema_version_legality`, `test_declared_schema_canonicalization`, `test_record_owned_references` |

The correction that made zero movement cheap rather than philosophically awkward: this checkpoint once
framed it as a *second* canonicalization philosophy coexisting with 2026-08-20's. It is not. The omission
rule is value-keyed, so a fact's canonical form does not depend on which schema is declared at all — **the
declared version decides only legality**. One rule, stated once, with 2026-08-20's version-keyed component
rule left exactly as it was.

### Architecture choice 1 — CONFIRMED as built

The registered lift was implemented as recommended and is unchanged in substance, with two hardenings the
implementation forced:

* the destination hash is **pinned literally**, not computed from `representation_schema_hash()` —
  computing it would let an unrelated later edit to the type surface silently re-authorize a transition
  nobody reviewed;
* `verify_lift` proves **byte-identity per collection** rather than asserting a superset, and runs both
  `post_schema_3_violations` and `held_structure_violations` on the prior first, so a restamped or
  misrepresenting prior is refused as such rather than reported as a payload difference.

### Final schema-4 identity

| | Value | Status |
|---|---|---|
| `SCHEMA_3_HASH` (lift source) | `43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05` | **unmoved**, asserted by the re-pin helper |
| `SCHEMA_4_HASH` (lift destination) | `3ec08804524213358422988980698689f3b135b242f1458a413134be56d523d5` | **final**. Moved twice, both times to put a contract *inside* the identity it governs: in round 1 the introduction manifest (version legality), in round 6 the invariant manifest (the intrinsic validation contract). Neither can now be loosened without invalidating this pin. Earlier values `f67588ff…` and `e1fed378…` are superseded. |
| committed `oracle_identity` | `a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda` | **unmoved** |

H-8 widened `from_component_key`'s *domain*, not the declared type surface, so the destination hash did
not move when the last family landed. It moved once afterwards, deliberately: `introduction_manifest()`
is emitted by `representation_schema_payload()`, so removing a legality row to let something through
changes this hash, the destination pin stops matching, and `lift_for` refuses the transition. The
schema-3 **source** pin was asserted unchanged across that re-pin, and the zero-movement probe was rerun
against it.

**Not raised as decisions:** the architecture choice (1 over 2–4), the fifteen additions, the H-16
rejection, the H-6 and H-16 shapes, the two-PR boundary, or the R-3 disposition. All ordinary
engineering under the governing Issue and ADR.
