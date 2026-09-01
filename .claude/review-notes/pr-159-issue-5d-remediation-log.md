# PR #159 — CRD Issue 5d remediation log

Round 1, Codex review of `140ff48`. Three threads, all actionable.

The two P1s are **one systemic defect family**, not two coincidences: *schema 4 added
things, and the code that has to recognise them was only partly updated.* One half is
reconstruction (a new operand is serialized but not read back), the other is legality (a
new type or value is not refused under the old declaration). Both were audited as a family
rather than patched at the cited example.

---

## 1. Applicability reconstruction — P1

**Reproduced before touching anything.** Every schema-4 applicability kind failed at both
loader boundaries:

```
ROLL_OUTCOME           oracle       RAISES: roll_outcome applicability states no outcome
DAMAGE_OUTCOME         persistence  RAISES: damage_outcome applicability states no damage_outcome
CONSUMPTION_THRESHOLD  oracle       RAISES: consumption_threshold applicability states no fraction
ELAPSED_DURATION       persistence  RAISES: elapsed_duration applicability states no unit
```

The operand is serialized, dropped on the way back, and the rebuilt value then fails its own
invariants — so an accepted artifact carrying one **cannot load**, a persisted candidate
**cannot reconstruct**, and an equivalent override **is refused**.

### Sibling audit — every production `Applicability` builder

Trigger: two review rounds are not required here; the P1 itself named three sites, which is
the "narrow fix followed by a sibling" shape. Enumerated by construction site, not by
grepping the cited names:

| # | Builder | Site | Disposition |
|--:|---|---|---|
| 1 | accepted-input loader | `oracle._applicability` | **patched** — all five operands |
| 2 | persisted-state loader | `persistence._applicability_from_row` | **patched** — all five operands |
| 3 | override patch builder | `patches._build_applicability` | **patched** — all five operands |
| 4 | nested-fact builder | `representation.py` (reached by `fact_from_payload` for `ConditionRemovalRestrictionFact.until`) | **already safe** — it read all five from the start; now pinned by a test so the disposition stays true |
| 5 | build-time authoring | direct `Applicability(...)` construction in generators and tests | **already safe** — nothing is parsed, so nothing can be dropped |

Total production construction sites: 4. `grep` for `Applicability(` across `src/` returns
exactly those four, so the enumeration is complete rather than sampled.

### What the fix had to get right

* **`.get`, not `[...]`.** The five operands are post-schema-3 keys, so the canonical payload
  omits one carrying no meaning and a *legal schema-3 payload has no such key at all*.
  Indexing would fail on entirely honest content. The schema-3 control case in the test
  module is what holds that distinction.
* **A second defect found while fixing the first.** `_rational_operand` initially accepted a
  fraction object carrying an extra key, silently discarding it. That is the same defect one
  level down — an undeclared key entering unchecked — so the helper now enforces the exact
  key set, in all three modules. Found by my own test, not by review.

### Coverage

`tests/ingestion/mechanical/test_schema_4_applicability_boundaries.py` — 46 tests.
Parameterized across **four kinds × three boundaries**, plus a schema-3 control, plus the
nested-fact builder, plus malformed / missing-required-operand / extra-key / wrong-enum /
malformed-fraction cases each asserted against **its own** typed error class
(`OracleLoadError`, `PersistedStateReconstructionError`, `InvalidPatchError`).

---

## 2. Schema-version legality — P1

**Reproduced:** `post_schema_3_violations(EffectTerminationFact(), "…schema-3")` returned
**no violation**, and the fact serialized identically under both requested versions — so
`verify_lift` would have authorized restamped authority no schema-3 reviewer could have
reviewed.

### The family, not the example

`_POST_SCHEMA_3_FIELDS` gates **fields**. That leaves two thirds of the delta unguarded, and
the second gap is the one no field-keyed rule can ever close:

| Axis | Why a field registry misses it | Rows |
|---|---|--:|
| new **fact families** | the family declares no post-schema-3 field, so there is nothing to gate | 5 |
| **vocabulary members** added to fields schema 3 already had | the field is old; only the *value* is new | 38 |
| new **fields** | already covered by `_POST_SCHEMA_3_FIELDS` | — |
| **reference ownership** (H-8) | covered at the serialization seam, but not at the legality seam | 1 |

The delta was **derived from the declarations**, by diffing the branch against
`origin/main`, not transcribed from the PR description:

```
entirely-new vocabularies : DamageModDirection, DamageOutcome, MeasureUnit, RecurrenceBoundary,
                            RequiredQuantity, Skill, TerminationScope, TimePeriod
pre-existing + members    : ApplicabilityKind (+4), Comparison (+1), ScalingBasis (+1), TimeUnit (+1)
new fact families         : condition_removal_restriction, damage_modification, derived_quantity,
                            effect_termination, size_keyed_quantity
```

`EffectTerminationFact` is **not** special-cased. Nothing in the implementation or the tests
names it as a case; it is one row of five in a table the recursion reads uniformly.

### Identity-bound, so it cannot be quietly loosened

`introduction_manifest()` is emitted by `representation_schema_payload()`, so the schema hash
covers it. Removing a row to let something through **moves the hash**, the destination pin in
`schema_lift` no longer matches, and `lift_for` refuses the transition. Loosening the legality
contract invalidates the registered lift — which is the failure this module is built around.
Proved by `test_dropping_a_manifest_row_moves_the_hash_and_breaks_the_pin`.

### Two things the invariants forced, both caught by existing tests

* **No class name may appear in the schema payload** (`test_no_python_class_name_appears_in_the_contract`).
  The first manifest emitted `owner` as a class name. The payload now renders a vocabulary the
  way `draft_vocabularies` does — by its complete admitted value set — with the class-keyed
  index kept internal and unemitted.
* **The internal index must stay class-keyed.** A value-only decision would over-refuse: the
  values `day` and `increase` are each admitted by both a schema-3 vocabulary and a schema-4
  one. Checked explicitly (227 schema-3 values vs 38 new members → 2 collisions) rather than
  assumed.

### Seams

| Seam | Covered by | Wired? |
|---|---|---|
| serialization | `representation_payload` → `LegacySchemaPayloadError` (H-8 ownership) | yes, pre-existing |
| acceptance | `accept_proposal` → `post_schema_3_violations` on both sides | yes, pre-existing call, now sees the whole delta |
| `verify_lift` | legality step runs **before** byte-identity | yes, pre-existing call, now sees the whole delta |
| identity | `representation_schema_payload` carries the manifest | yes — the binding above |

### Coverage

`tests/ingestion/mechanical/test_schema_version_legality.py` — 40 tests. Thirteen exemplars
spanning every axis; an over-refusal control set; the committed oracle asserted **legal**
under the schema it declares (the discriminating test — a manifest that over-classifies would
accuse the artifact that can no longer move); a coverage guard asserting every manifest group
is exercised by a live object, which caught two gaps in my own exemplar set.

### Hash re-pin

The destination pin moved **twice**, deliberately, and the **source pin was asserted unchanged
across both**:

```
cddba504…  →  f67588ff…   (manifest joined the schema payload)
f67588ff…  →  e1fed378…   (manifest rendered without class names)
SCHEMA_3_HASH = 43ed330d…  unchanged throughout
```

Zero movement rerun after each: all six collections byte-identical, committed bytes
reproduced under both schemas, `oracle_identity` unmoved at `a0f0bd2f…`.

---

## 3. Checkpoint — P2

Codex was right that appending a WITHDRAWN section left two live prescriptions. **Rewritten,
not annotated:**

* **§2** — the "exactly 34 fact keys and 6 applicability payloads move" conclusion is replaced
  with "zero fact keys and zero applicability payloads move." The structure table above it is
  kept, because it still correctly names *which* structures the additions touch, which is the
  reason the omission rule had to exist.
* **§4.4** — answer flipped from "No, and this is the design's one real cost" to "Yes — proved
  element by element, not argued," with the omission rule and the proves-not-transforms
  property stated.
* **§5 T-1** — no longer prescribes asserting an enumerated 34-key difference set. Under the
  omission rule there is no difference to enumerate, and a test that listed one would
  re-encode the withdrawn design.
* **§8** — the Options A/B table is **deleted**, not annotated. The reasoning that was rejected
  survives as a paragraph; what it *prescribed* is gone.
* Stale destination hash corrected.

---

## 4. pip-audit — chromadb

Four advisories audited individually against the enforced embedded-only client boundary
(`pipeline/retrieval/client.py`, the single construction choke point). All four are
**server-side authorization/authentication** defects in a component this repository never runs.

| CVE | What it is | Reachable? | Disposition |
|---|---|---|---|
| **CVE-2026-45830** | missing authorization validation lets an *authenticated* user reach any tenant's collection | **no** — requires the HTTP server's authenticated multi-tenant surface; there is no server, so no authenticated user and no tenant boundary | ignore + rationale + removal trigger |
| **CVE-2026-45831** | `SimpleRBACAuthorizationProvider` ignores which tenant/database/collection a permission applies to | **no** — that provider is instantiated only by the server auth stack; no `CHROMA_SERVER_*` setting, no auth provider, and `RetrievalMemoryConfig` exposes no server-mode knob | ignore + rationale + removal trigger |
| **CVE-2026-45833** | code injection via a malicious model repository with `trust_remote_code=true` on `POST …/collections/{id}` | **no** — same shape as the already-dispositioned CVE-2026-45829; the endpoint requires the server, and `trust_remote_code` is never set anywhere (it appears only in prose saying so — verified by grep across `src/`, `tests/`, `pyproject.toml`) | ignore + rationale + removal trigger |
| **CVE-2026-45832** | V1 collection-level endpoints pass `None` for tenant and database to the authorization layer | **no** — same boundary | **audited now, no ignore added** — see below |

**Removal trigger, all three:** remove the flag when chromadb ships a patched release and the
pin is raised. OSV lists **no fix version** for any of them (`last_affected: 1.5.9`).

**CVE-2026-45832 is deliberately not suppressed.** It *does* cover the pinned version — OSV
records it against chromadb 0.5.0–1.5.9 — but pip-audit does not report it, because the OSV
record carries only a GIT/CPE range and no PyPI package entry. An `--ignore-vuln` for it today
would be dead configuration. If that record gains a PyPI entry the step will fail on it, and
the fix is to add it there with this same rationale — **not** to widen any existing flag.

No broad or family-level suppression was added: three separate flags, three separate
rationales. The dependency was **not** changed to silence the gate.

---

## Residue

* **Scope disclosure carried forward.** `held_structure_violations` reuses two full semantic
  validators, so `accept_proposal` enforces exhaustiveness, duplicate-key, and qualifier-scope
  rules it previously left to the gate. Unchanged by this round; still in Architecture Notes.
* **The `fb23a04` gate refusal remains an uncategorized fail-closed exception**, not fail-open.
  No test shows publication proceeding.
* **`urllib3`, `setuptools`, `pip`, `msgpack`, `pydantic-settings` advisories are pre-existing
  environment dependencies.** `git diff origin/main..HEAD -- pyproject.toml` is empty: this PR
  introduces zero dependencies and changes no pin.


---

# Round 2

Codex review of `22231b7`. Three findings, remediated as **two** families.

## Correction to my round-2 report

I initially told Codex that all malformed `recurs` shapes escaped as `TypeError`. **That was wrong** — my probe called a two-argument function with three arguments, so the `TypeError` I measured was my own. Re-verified with the correct arity:

```
['start_of_turn']  -> typed refusal  OK
'start_of_turn'    -> typed refusal  OK
7 / 3.5 / True     -> TypeError  <-- the real leak
```

Only **non-iterable scalars** escape. Codex's conclusion stands; my reproduction of it did not, and the fix is a mapping guard rather than a rewrite of the shape checks.

---

## Family 1 — schema succession and acceptance legality (R2-1, R2-3)

### The invariant, stated once

> A representation interpreted under a declared schema may not carry meaning that schema cannot state.

Legality was previously checked **only where the schema changed** — inside `verify_lift`, on the *prior*. That left three acceptance paths open, and the proposed half unchecked on all of them.

### R2-1 — enforced before every branch

The guard runs in `accept_proposal` on the **proposed** representation unconditionally, and on the prior when there is one, *before* the branch that decides whether a lift is involved.

**Not** added to `representation_payload`. That function's contract is to emit the declared key set; a full recursive walk there would run on every identity computation, every gate comparison, and both sides of every verified lift — which already runs the check explicitly. Acceptance is the seam authority is *created* at, so nothing reaches canonicalization as accepted authority without passing it first.

All six branches, executed:

```
OVER-REFUSAL CONTROLS (must be ACCEPTED)
  clean schema-3, equal-schema prior           ACCEPTED  lifts=0
  clean schema-3, no prior                     ACCEPTED  lifts=0
  schema-4 content, lifted prior               ACCEPTED  lifts=1
  schema-4 content, no prior                   ACCEPTED  lifts=0

THE DEFECT (must be refused)
  schema-4 family declared schema-3, prior     refused
  schema-4 family declared schema-3, no prior  refused
```

The over-refusal controls are the ones the new guard could plausibly have broken, and they were run first.

### The non-executing test, replaced

`test_acceptance_reports_the_restamp_as_an_acceptance_failure` asserted `issubclass(AcceptanceError, Exception)` and described in a comment what it would have tested. Replaced with real `accept_proposal` calls parameterized over all three branches in both directions, plus a message-content assertion. Seven executable tests where there was one vacuous one.

### R2-3 — loaded evidence validated against the registered chain

`lift_chain_violations(lifts, declared)` in `schema_lift.py`, called from `load_accepted_inputs`. Six properties:

1. **Registered** — the source pair is a key in `SCHEMA_LIFTS` and the registered `lift_id`, destination version and destination hash all match. This one check subsumes *invented*, *reversed*, and *hash-mismatched*: none has a registry row whose destination agrees.
2. **Continuous, oldest first** — each destination is the next source. *Reordered* and *omitted* both break the join, so neither needs its own rule.
3. **Terminal** — the last destination is what the artifact declares.
4. **Non-repeating** — a succession is crossed once; a repeat is a duplicate or a cycle.
5. **Exactly the representation's collections** — the proof extent is derived from `REPRESENTATION_COLLECTIONS`, itself derived from `_DRAFT_ELEMENT_TYPES`, so the validator and the payload cannot drift.
6. **Empty is legal** — the committed artifact has `lifts == ()`, and property 3 must not fire on it.

Rejection matrix, all executed end to end through `load_accepted_inputs`:

```
legal: no lifts at all (committed)       LOADED  OK
legal: one registered lift               LOADED  OK
invented transition                      refused
registered source, wrong destination     refused
registered source, wrong lift_id         refused
reversed                                 refused
duplicated                               refused
terminal disagrees with declaration      refused
invented proof collection                refused
proof extent missing a collection        refused
disconnected chain                       refused
```

---

## Family 2 — typed persisted-state reconstruction (R2-2)

### Sibling audit — every JSON reconstruction boundary in the PR

| Boundary | Malformed shapes probed | Disposition |
|---|---|---|
| `_recurrence_from_row` | int, float, bool, str, list, tuple, dict | **patched** — mapping guard before inspection; the `cast("dict[str, Any]", payload)` above it was the actual lie and is removed |
| `_applicability_from_row` | same | **already safe** — `applicability_payload_violations` checks the mapping shape first; now pinned by a test, since a later edit could reorder that |
| `_fact_from_row` → `fact_from_payload` | same | **patched** — `fact_from_payload` meets a scalar with `AttributeError`, which the row loader's `except` did not catch |
| `raw_state._valid_target_key` (provenance `target_key`) | — | **already safe** — `isinstance(value, list) and all(type(v) is str …)`, returns a bool rather than raising |
| component `options` JSON | — | **already safe** — reconstructed through `parse_enum` and the applicability boundary above |

Post-patch probe: `_recurrence_from_row` and `_applicability_from_row` both leak **nothing** across all seven shapes.

### The gate verdict, asserted on the gate

`run_publication_gate` now returns `PERSISTED_STATE` for a corrupted `recurs` column rather than aborting. That is the property the typed error exists for: the gate's contract is that a caller receives a refusal, not an exception. The previous behaviour was fail-closed in the wrong currency — and uncategorized, the same shape as the `fb23a04` residue item.

---

## No re-pin

These are enforcement changes, not representation-surface changes, and the identity-bearing payload confirms it:

```
schema payload hash : e1fed378a23e5984ddcc7f0fc08e03118fe05db1594e31b449facdf12fdadbc9
SCHEMA_4_HASH pin   : e1fed378a23e5984ddcc7f0fc08e03118fe05db1594e31b449facdf12fdadbc9  (unchanged)
SCHEMA_3_HASH       : 43ed330d…  (unchanged)
ZERO MOVEMENT       : HOLDS
```

---

# Round 3

One finding, `schema_lift.py:307` (P2): the loaded proof extent validated only the *set* of collection
names, so a duplicated row collapsed before the comparison saw it and any per-collection element count
passed — `999999` as readily as the truth. Same family as R2-3: evidence that is well-formed but
unverified.

## The determination that had to come first

The finding's suggested remedy is to *"reconcile its count with retained or verifiable lift evidence."*
That was checked against the repository before any implementation was chosen, and it is not available:

| Question | Answer |
|---|---|
| Where does the count come from? | `verify_lift` measures the **prior** representation, at lift time |
| What does the artifact hold afterwards? | the inherited elements **merged with** the batch that triggered the lift, and every batch after it (`acceptance.py` appends `batch` and `lift_record` in the same acceptance) |
| Is the predecessor retained? | no — resolution is one artifact per `(package_uuid, release_version)`, and the successor supersedes the file |
| Does anything anchor the crossing in the batch sequence? | no — `SchemaLiftRecord` carries no batch, ordinal, or timestamp |
| Can elements be attributed to a batch? | only through provenance to spans to acceptance records, which is not total: "substantive but unclaimed" elements have no claim to attribute |

So the loader can bound a count (`0 ≤ count ≤ len(loaded collection)`) and never confirm one. A bound is
not a reconciliation, and a plausible number is exactly what the finding objects to. The two honest
alternatives were: retain a sufficient proof anchor — the pre-lift artifact or per-element identities,
which materially expands accepted-history retention beyond PR A and would need an Owner Decision — or
remove the unverifiable claim. **The second is the smallest correct solution and needs no Owner Decision:
it removes a claim rather than expanding retention.**

## What changed

`SchemaLiftRecord.verified_counts: tuple[tuple[str, int], ...]` → `verified_collections: tuple[str, ...]`.

`verify_lift` still proves every collection byte-identical and still raises rather than returning a partial
proof, so the extent it records is a property of the contract instead of a number asking to be believed.
`lift_chain_violations` now checks **exactly-once explicitly, before the set comparison** — the set was the
defect — and then equality against `REPRESENTATION_COLLECTIONS`. The wire form is a string list, so a
leftover `verified_counts` key is refused by `_require` as unexpected rather than ignored.

## Field audit — every `SchemaLiftRecord` field, bounded to this evidence model

| Field | Disposition |
|---|---|
| `from_version`, `from_hash` | **independently validated** — must be a key in `SCHEMA_LIFTS` |
| `lift_id`, `to_version`, `to_hash` | **independently validated** — must equal the registered destination, and the last record's destination must equal the artifact's own declaration |
| `verified_collections` | **independently validated** — exactly `REPRESENTATION_COLLECTIONS`, each once, derived from `_DRAFT_ELEMENT_TYPES` rather than restated |
| ~~`verified_counts`~~ | **removed** — was the only "structurally checked only" field, and unverifiable in principle |
| `SchemaLift.rationale` (registry side, not loaded) | **intentionally documentary** — states why a transition was authorized; never loaded from an artifact, so nothing external can assert it |

## The eight required tests

| Required | Where |
|---|---|
| a real record survives serialization and loading | `test_a_real_record_survives_writing_and_loading` — real `lift_accepted_inputs` → `accepted_inputs_payload` → `load_accepted_inputs` |
| one fabricated count fails | no referent: the count is gone. Nearest executable form: `test_a_count_claim_cannot_re_enter_through_the_wire` refuses `verified_counts` as an unexpected key |
| duplicate rows for one genuine collection fail | `duplicated-collection-row`, `duplicate-standing-in-for-a-missing-collection`, and end-to-end `duplicate-row` |
| missing and invented collections still fail | `proof-extent-missing-a-collection`, `invented-proof-collection`, both also end-to-end |
| zero and nontrivial real counts accepted when proved | no referent as counts; the property that survives is that an **empty** collection is still proved and recorded — asserted on the real record (`relationships == ()`) |
| no-lift schema-3 authority remains legal | `test_no_evidence_is_legal`, `test_the_committed_artifact_still_loads` |
| tampering fails through `load_accepted_inputs` | `test_the_loader_refuses_a_tampered_extent_end_to_end` (3 cases), `test_the_loader_refuses_invented_evidence_end_to_end` |
| post-lift additions not mistaken for the pre-lift extent | `test_growth_after_the_crossing_leaves_no_recoverable_pre_lift_extent` — a real acceptance grows `records`, `components` and `provenance` past what the lift saw, and the evidence still validates because it claims only what remains true |

## No re-pin

Evidence validation only; `SchemaLiftRecord` is not part of `representation_schema_payload()`.

```
SCHEMA_3_HASH  : 43ed330d…  (unchanged)
SCHEMA_4_HASH  : e1fed378…  (unchanged, == representation_schema_hash())
six collections byte-identical : yes
oracle_identity                : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda (unmoved)
committed artifact round-trips to identical payload : yes
ZERO MOVEMENT  : HOLDS
```

---

# Round 4

One finding, P1: `load_accepted_inputs` reconstructed accepted authority from committed bytes and never
asked whether that content was legal under the schema the file declares. With no lift evidence
`lift_chain_violations` returned clean, so a schema-3 artifact carrying an `EffectTerminationFact` became
committed accepted authority.

## Reproduced first, on the real committed artifact

Seven one-field tampers, each loaded through the real `load_accepted_inputs`, at `d632971` and again
after the fix:

| tamper | before | after |
|---|---|---|
| clean control | LOADED | LOADED |
| schema-4 fact family (obligations reconciled) | **LOADED** | refused |
| schema-4 vocabulary member on a schema-3 field | **LOADED** | refused |
| post-schema-3 field holding meaning | **LOADED** | refused |
| record-owned reference (H-8 ownership) | **LOADED** | refused |
| unknown declared version | **LOADED** | refused |
| invented hash | **LOADED** | refused |
| schema-3 version with schema-4's hash | **LOADED** | refused |

The family case needed its record obligation updated to reconcile — obligations are *derived* from the
accepted representation, so an artifact that adds a family and updates the obligation is internally
consistent everywhere except in what its declaration is allowed to state. That is what makes this a
declaration defect rather than a consistency one.

## One invariant, stated once

`schema_lift.schema_binding_violations(draft, declared)` — a representation and the schema identity it
declares are admissible together only when both halves hold:

1. **Its meaning is legal under the declared version** —
   `representation.declared_meaning_violations`, which is `post_schema_3_violations` (field, family,
   vocabulary member, ownership form) plus `held_structure_violations` (a structure outside the closed
   declaration, illegal under *every* version).
2. **Its exact pair is a contract this build accepts authority under** — `accepted_schema_contracts()`,
   derived as the live pair plus every registered succession endpoint. Unknown version, invented hash, and
   known-version-wrong-hash are one refusal rather than three: in each case the union that decides what
   these facts may mean cannot be established.

Neither half implies the other, and empty lift history exempts neither. Returned as findings rather than
raised, so each seam wraps them in the error its callers already handle.

Deliberately **not** derived from what the build can *serialize*: schema 1 and schema 2 payloads stay
reproducible for historical reconstruction, and reproducing an identity is not admitting new accepted
authority under it.

## Bounded sibling audit — every seam that creates or admits authority

| Seam | Disposition |
|---|---|
| committed JSON → `load_accepted_inputs` | **patched** — `OracleLoadError`, before the lift-chain check |
| `load_oracle`, `committed_oracle_for`, `committed_inputs_for`, `_resolve_committed_*` | **intentionally downstream-protected** — every one resolves through `load_accepted_inputs`; a second check would be a second place to forget |
| proposal → `accept_proposal` (no-prior, equal-schema, lift branches) | **patched** — one call replacing the two ad-hoc `post_schema_3_violations` calls, now covering the recognition half too |
| prior → `verify_lift` | **patched** — routed through the same helper, so it is provably the same code path rather than a parallel implementation |
| reconstructed candidate → `validate_schema_binding` | **patched** — the meaning half added; publication keeps its stricter live-pair rule, which is the same invariant at its strict end |
| reconstructed candidate → identity/digest raise paths | **already safe** — `verify_persisted_state` catches `UnsupportedSchemaVersionError`/`LegacySchemaPayloadError` and reports; the gate catches the same pair on the oracle at entry and around the element comparison. Verified by running the gate on a downgraded projection: `SCHEMA_MISMATCH`, no exception |
| `proposal` module | **out of scope, by the finding's own terms** — it has no loader, and constructing a proposal is not accepted authority |

## Over-refusal controls

The committed artifact still loads, and is still byte-identical when written back out. Schema-1 and
schema-2 historical reconstruction is unchanged (`test_review_round_6_schema1_identity`,
`test_representation_schema_identity`). One fixture was genuinely illegitimate and is corrected rather
than exempted: the packaging sentinel oracle declared `"sentinel"/"f"*64`, which the resolver now refuses
while scanning the packaged directory. It declares the live pair now — its *release binding* is what makes
that test unambiguous, and that is untouched.

Five message assertions moved with the unified wording. Each still asserts the cause rather than the fact
of refusal: `"stealth" and schema-4` for the restamped prior, `"must be DiceExpression"` for the two
subclass seams, and the recognition phrase for the three unauthorized-transition cases — whose
authorization half is still covered by `test_the_reverse_transition_is_refused`, where both pairs are
recognized and no lift exists between them.

## One behavioural consequence, named rather than left implicit

`_resolve_committed_inputs` loads **every** `*.json` in the oracle directory before filtering by release
binding, so a file that cannot be loaded now blocks resolution for every release rather than being filtered
out. That is not new in kind — the loader already refused a malformed shape, a missing key, an obligation
that does not reconcile, and incomplete acceptance evidence, and the resolver has always propagated those.
This round only widens the set of files that refuse.

Kept fail-closed deliberately. The directory is packaged accepted authority, not a drop box: a file there
that is not loadable accepted authority is either tampered or misplaced, and skipping it would mean
publication resolving *around* a committed artifact nobody can read. The one file this actually caught was
the packaging sentinel, which was a test fixture declaring a fake contract, not a legitimate artifact.

## No re-pin

Enforcement of the already identity-bound contract; nothing touches `representation_schema_payload()`.

```
SCHEMA_3_HASH  : 43ed330d…  (unchanged)
SCHEMA_4_HASH  : e1fed378…  (unchanged, == representation_schema_hash())
six collections byte-identical : yes
oracle_identity                : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda (unmoved)
committed artifact round-trips to identical payload : yes
ZERO MOVEMENT  : HOLDS
```

---

# Round 5

One finding, P1: `applicability_violations` checked that `Applicability.fraction` held the exact type
`Rational` and stopped there, so `Rational(1, 0)`, `Rational(1, -2)` and `Rational(-1, 2)` satisfied it.
Every other boundary delegates to that function, so the invalid value survived acceptance, committed
loading, persistence, overrides and publication validation.

## Reproduced first

```
case                       applicability_violations   nested-fact builder
zero denominator           passes                     passes
negative denominator       passes                     passes
negative numerator         passes                     passes
boolean numerator          passes                     passes
non-integer member         passes                     passes
valid one-half (control)   passes                     passes
```

`Rational("1", 2)` passing is the clearest statement of the gap: the field's *own* type was checked and
its members were not.

## The change

```python
typed.extend(_check_optional_rational(applicability.fraction, "fraction"))
```

One line, replacing the type check with the rule the other four Rational owners already use. Nothing is
restated in the oracle, persistence, patch, acceptance or schema-binding layers — they each already
validate the rebuilt value through `applicability_violations`, which is why correcting the shared
validator corrected all of them.

The shared contract is preserved exactly as written: non-negative numerator over a positive denominator.
No normalization, no reduction to lowest terms, no consumption-specific bound. `Rational(2, 4)` and
`Rational(3, 2)` are still admitted, and there are tests saying so, because delegating must not import a
stricter rule by accident.

## Bounded Rational-owner audit

| Owner | Disposition |
|---|---|
| `SizeQuantity.amount` | **already delegating** — `_check_rational` in `_check_size_keyed_quantity` |
| `CreatureChallengeFact.challenge_rating` | **already delegating** — `_check_rational` |
| `EquipmentDescriptorFact.weight_pounds` | **already delegating** — `_check_optional_rational` |
| `DamageModificationFact.factor` | **already delegating** — `_check_rational`, plus its own direction/factor agreement rule on top |
| `Applicability.fraction` | **patched** — the one owner that checked the type and skipped the invariants |

Pinned as one parametrized table, so a sixth owner has an obvious place to be and no place to restate the
rule instead.

## Every applicability construction path

| Path | Disposition |
|---|---|
| direct `ComponentDraft` / `ComponentOption` / `FactQualifier` applicability | **corrected through the shared validator** — each validates through `applicability_violations` |
| `ConditionRemovalRestrictionFact.until` | **corrected through the shared validator** — `_check_removal_restriction` delegates |
| accepted-input loader (`oracle._applicability`) | **corrected through the shared validator** — post-construction call raises `OracleLoadError` |
| persisted-state reconstruction (`persistence._applicability_from_row`) | **corrected through the shared validator** — raises `PersistedStateReconstructionError` |
| rules-authority patch builder (`patches._build_applicability`) | **corrected through the shared validator** — raises `InvalidPatchError` |

None of the five needed a numeric rule of its own. That is the property the new tests pin: each returns
its *own* typed refusal for the same invalid fraction, from one definition of validity.

## No re-pin

Value-object validation only: no serialized field, vocabulary, optionality, or canonical payload changes.

```
SCHEMA_3_HASH  : 43ed330d…  (unchanged)
SCHEMA_4_HASH  : e1fed378…  (unchanged, == representation_schema_hash())
six collections byte-identical : yes
oracle_identity                : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda (unmoved)
committed artifact round-trips to identical payload : yes
ZERO MOVEMENT  : HOLDS
```

---

# Round 6

Two P1s, and one audit that treats them as instances rather than as the problem.

## R6-1 — ELAPSED_DURATION admitted negative time

The non-negative rule was written on `QUANTITY_THRESHOLD`'s branch rather than on the field, so
`ELAPSED_DURATION` inherited nothing when it was added.

```
before                          after
value=-5   passes               REFUSED
value=0    passes               passes
value=6    passes               passes
```

Zero is preserved deliberately. Nothing in the governing contract asks for a positive bound, and turning
"not below zero" into "above zero" while fixing a range would refuse a real state. The rule now lives on a
`_NONNEGATIVE_VALUE_KINDS` set, so a later kind that ranges over `value` joins it by joining the set —
which is exactly what `elapsed_duration` failed to do.

## R6-2 — alternatives were checked without ever being compared to the fact

```
                                          before   after
real Falling shape (Str/Ath or Dex/Acro)  passes   passes
empty alternatives                        passes   passes
member rolled as a saving throw           passes   REFUSED
closed set omitting the fact's own pair    passes   REFUSED
declared pair named twice, distinct rolls  passes   REFUSED
```

The last case is the one payload uniqueness cannot see: two members differing in `actor` are distinct
rolls that name the same ability and skill. Only comparing the set against the fact catches it.

`_check_alternatives` now takes the fact's `ability` and `skill`, and the field documentation is corrected:
`alternatives` is the **complete** closed choice including the pair the fact carries, not extras beside it.

**Actor consistency — audited, deliberately not enforced.** The settled invariant (hazards-1 closure
checkpoint, invariant 4) says: *"empty or ≥2 entries, each a distinct RollSpec; the DC stays on the
fact"*. It states nothing about actors, and the H-11 authority text does not either. The three corpus
rules (Falling, Grappling, Rope of Entanglement) are all subject-rolled, which is evidence but not a
settled rule — a set offering one creature's check or another's would be refused by *no* existing
authority. Surfaced rather than invented. Note that the declared-pair rule already refuses the specific
shape most likely to be meant by it: the same ability and skill under two different actors.

## The bounded schema-4 invariant-closure audit

| Addition | Settled intrinsic invariants | Shared validator | Result |
|---|---|---|---|
| H-1 recurrence | `whose` stated exactly for a turn boundary | `recurrence_violations` | already safe |
| H-2 effect/hazard termination | none beyond its vocabulary | `_check_effect_termination` | already safe |
| H-3 size-keyed quantity | ≥1 row, each size once, size-declaration order | `_check_size_keyed_quantity` | already safe |
| H-4 consumption threshold | `fraction` is a rational share | `applicability_violations` | **patched in round 5** |
| H-5 cause-scoped condition levels | `cumulative` only for an accrual; amount/all_levels exclusive | `_check_condition_level` | already safe |
| H-6 removal restriction | `cause_scoped` always true; `until` is a checked applicability | `_check_removal_restriction` | already safe |
| H-7 distance-fallen scaling | `threshold` ≥ 0; exactly one increment | `_check_scaling` | already safe |
| H-8 record-grain reference ownership | empty owner names a declared record | `validation` / `raw_state` (relational) | already safe |
| H-9 maximum damage dice | caps a stated expression, never below its count | `_check_damage` | already safe |
| H-10 damage-outcome applicability | closed field matrix | `applicability_violations` | already safe |
| H-11 skill axis + check alternatives | closed choice reconciled with the fact | `_check_alternatives` | **patched (R6-2)** |
| H-12 roll-outcome applicability | closed field matrix | `applicability_violations` | already safe |
| H-13 damage modification | a **positive** rational other than one, agreeing with direction | `_check_damage_modification` | **patched** — `Rational(0, 1)` passed, and the direction rule actively endorsed it (`0 < 1` agrees with `reduce`). Settled invariant 7 says positive |
| H-14 elapsed duration | `value` ≥ 0 | `applicability_violations` | **patched (R6-1)** |
| H-15 derived quantity with a floor | floor states both an amount and a unit, or neither | `_check_derived_quantity` | already safe |

**Surfaced, not patched.** `DerivedQuantityFact.base` admits a negative constant (`base=-3` passes). No
governing authority settles a sign for it — *"1 + your Constitution modifier minutes"* fixes no minimum,
and a rule phrased as a modifier minus a constant is expressible. Inventing a bound here would be policy,
so it is recorded rather than decided.

**Also excluded from the manifest, deliberately:** schema-3-era value ranges this succession did not
touch — a flat damage amount's minimum, an armour class's floor, a multiplier's minimum. Declaring them
would make the identity churn on edits that have nothing to do with schema 4.

## Schema identity now binds the intrinsic contract

`invariant_manifest()` — 16 rows — is emitted by `representation_schema_payload()`. Rows name a serialized
locus and field: a family discriminator (`fact:ability_check`), an applicability kind
(`applicability:elapsed_duration`), or, for a nested value object that carries no tag at all, its sorted
wire field set (`shape:denominator+numerator`). No Python class or function name appears, and no source,
bytecode, comment or docstring is read.

Executable by construction: `test_every_declared_invariant_is_executable` asserts the declared row set
equals the covered row set, and each row carries one exemplar the shared validator refuses and one it
admits. A row nothing demonstrates fails the suite.

`test_weakening_an_invariant_declaration_breaks_the_registered_lift` drops a row, shows the hash moves, and
shows `lift_for` then refuses the transition — the contract cannot be loosened while the registered
succession keeps working.

## Re-pin — destination only

```
SCHEMA_3_HASH  : 43ed330d…  UNCHANGED (asserted by the re-pin helper)
SCHEMA_4_HASH  : e1fed378…  →  3ec08804524213358422988980698689f3b135b242f1458a413134be56d523d5
```

Repinned by `repin-schema-4.py`: the lift's destination pin by name, `bounded_oracle.json`, and the three
literal canaries. Zero movement re-run against the finalized hash:

```
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
oracle_identity                : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda (unmoved)
committed artifact round-trips to identical payload : yes
registered lift verifies to the finalized destination : yes
```

**detect-secrets: exactly one field moved.** `results[bounded_oracle.json][line 191].hashed_secret`,
`ac3f36eb…` → `7ff74fa7…`, edited surgically rather than by rescanning. `generated_at`, `filters_used`,
`plugins_used` and the other five recorded results are untouched. (A full `detect-secrets scan --baseline`
was tried first and rejected: it swept untracked working files in `.claude/review-notes/` into the
baseline, which would have committed hundreds of rows nothing asked for.)

---

# Round 7

## R7-1 — a destination restamp loaded clean

Reproduced first, changing exactly one field of the committed artifact and nothing else:

```
committed declares 5d-representation-schema-3, lifts: none
  -> rewrite representation_schema to the live schema-4 pair, keep everything else

LOADED. declares 5d-representation-schema-4 | lifts = () | batches retained: ['conditions-1']
>>> schema-3-reviewed authority is now committed schema-4 accepted authority
```

Nothing in the file disagreed with anything else in the file. The representation is legal under schema 4,
the batch, its semantic diff, its diff hash and its proposal identity are the committed ones, the
obligations reconcile, and an empty lift history had nothing to contradict — because acceptance evidence
never recorded *which schema each batch was reviewed under*. An empty lift history therefore had two
readings that could not be told apart: genuinely first accepted under schema 4, or reviewed under schema 3
and re-declared.

**`BatchSchemaAnchor(batch_id, proposal_identity, schema_version, schema_hash)`**, on the evidence half
beside the batches and never inside them. An `AcceptanceBatch` records what a human accepted; a batch
accepted before anchors existed does not acquire a field because a later succession needed one. Keyed by
batch id *and* proposal identity so an anchor cannot be moved onto another batch or left pointing at a
proposal that was rewritten. Nothing else is retained: no predecessor artifact, no per-element identity,
no count, no timestamp, no signature.

`succession_evidence_violations(batches, anchors, lifts, declared)` is one reader for the three halves
that only mean something together:

| Rule | Refusal |
|---|---|
| anchored, or the exact legacy form | absence is admitted only for a pre-schema-4 declaration with no lifts, where it has one possible meaning; the same absence under schema 4 is the restamp |
| real and unrewritten | anchor names a retained batch and repeats that batch's own proposal identity |
| recognized | anchored pair is in `accepted_schema_contracts()` |
| declared, or lifted | a batch anchored at the declaration needs nothing; anchored earlier needs a registered chain starting there and terminating at the declaration |
| required | `lifts[0]`'s source must be a pair some batch was reviewed under — a crossing nothing was carried across was not crossed |

Also: no batches means no review to describe, so an artifact with no batches is unanchored legitimately —
which is what the packaging sentinel is.

`accept_proposal` now emits an anchor for the batch it appends, and materializes anchors for a prior
loaded in the legacy form at that prior's own declaration. `lift_accepted_inputs` does the same at the
pair being lifted *from*, so a lifted artifact records where its review happened rather than only where it
ended up.

**Ordering matters and was corrected once:** the succession check runs *after* `validate_acceptance`, so an
artifact whose evidence does not reconcile with itself still says so in those terms rather than through a
succession finding.

## R7-2 — the manifest declared H-7 by its threshold alone

`_check_scaling` enforces a second rule H-7's own content depends on — Falling's *"1d6 for every 10
feet"* is an increment, and scaling other than `effective_spell_level` must state exactly one of a dice
increment or a flat amount. Declared now as `scaling.increment.exactly-one`, with its own witness.

**Reconciliation, one invariant at a time — every `_check_scaling` branch:**

| Branch | Classification |
|---|---|
| `threshold < 0` | **identity-bound and exercised** — `scaling.threshold.not-below-zero` |
| non-`effective_spell_level` states exactly one increment | **identity-bound and exercised** — `scaling.increment.exactly-one`, added this round |
| `effective_spell_level` carries an increment | **inapplicable to H-7** — keyed by *effect*; H-7 added a *basis*, and distance-fallen scaling never states that effect |
| `effective_spell_level` direction must increase | **inapplicable to H-7** — same branch, same reason |
| `amount < 1` | **inapplicable to H-7** — distance-fallen content states a dice increment (Falling's `1d6`), so the flat-amount magnitude branch is never reached by it; the exactly-one rule above already forces that choice |
| `DECREASE` only for `d20_test`/`speed` | **inapplicable to H-7** — keyed by effect and predates H-7; falling damage increases |
| type and vocabulary checks | already bound by the wire contract the payload declares |

**Rows are now keyed by a stable invariant id**, not by `(locus, field)`: two independent rules live on
`fact:scaling`, and a field-keyed table would let one rule's witness stand in for the other's. The
executable matrix is keyed the same way.

**The completeness claim is corrected.** `test_every_declared_invariant_is_executable` proves every
declared row executes in both directions and that no witness exists for an undeclared row. It cannot prove
no declaration was *omitted* — both halves are written by the same hand, and R7-2 is the demonstration:
the scaling increment rule was enforced, settled, and absent from both, and the test passed. Completeness
comes from this bounded authority-to-manifest reconciliation, and the test holds the result honest rather
than deriving it.

**Not constrained, per instruction and prior audit:** `DerivedQuantityFact.base` and alternative-roll
actors. Existing authority settles neither.

## Re-pin — destination only, provisional until review is clean

```
SCHEMA_3_HASH  : 43ed330d…  UNCHANGED (asserted by the re-pin helper)
SCHEMA_4_HASH  : 3ec08804…  →  241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9
```

Zero movement against the corrected destination:

```
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
proposal identities            : unchanged (14587d5b5d51…)
oracle_identity                : a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda (unmoved)
committed artifact round-trips to identical payload : yes
registered lift reaches only the corrected destination : yes
restamp of that same artifact : refused
```

**detect-secrets, exactly:** the bounded fixture gained an eight-line `schema_anchors` block, so its
recorded rows moved with it. One row added — the schema-hash literal, now first seen at line 63 (the
scanner records a repeated literal once, at its first occurrence, which is why the declaration's own
line has no separate row). Three rows shifted by eight lines with identical `hashed_secret` (81→89,
134→142, 194→202). Two rows unchanged. `generated_at`, `filters_used` and `plugins_used` untouched:
the file was merged from a scan of that one fixture rather than regenerated, because a full rescan sweeps
untracked working files in `.claude/review-notes/` into the baseline.

---

# Round 8

## R8-1 — the loader's check was satisfied by evidence acceptance had just written

Reproduced first, exactly as specified: the real committed schema-3 artifact, its declared pair
overwritten in memory and nothing else touched, passed straight to `accept_proposal`.

```
3. accept_proposal(prior=restamped in-memory artifact):
   ACCEPTED. anchors synthesized:
     conditions-1           reviewed under 5d-representation-schema-4
     laundering-probe-1     reviewed under 5d-representation-schema-4
   lifts: ()
4. does the produced artifact load? YES — 5d-representation-schema-4, 2 batches, no lifts
   >>> the schema-3 review is now schema-4 authority, and the file proves it
```

Round 7 closed the *file* boundary and left the *transformation* boundary open. `_carried_anchors` read
the prior's declaration to fill in what its evidence never said, so the acceptance seam manufactured
precisely the evidence the loader would later check — and the check passed because the transformation had
written it.

## The fix: validate before carrying, through the loader's own rule

`schema_lift.carried_anchors(inputs)` runs `succession_evidence_violations` over the prior's complete
evidence and raises rather than repairing. Nothing deletes, rewrites, or works around malformed evidence.
The one default survives in its exact shape: no anchors, no lifts, and the **recognized legacy schema-3
pair** — narrowed this round from "any pre-schema-4 contract" to that exact pair, so an unknown version or
an invented hash falls outside it rather than being compared against a boundary.

In `accept_proposal` the call runs **before the lift is looked up, before the representations are merged,
and before any anchor is carried or synthesized** — an artifact whose own evidence does not hold is not a
base to extend, so nothing should be computed from it at all.

```
before:  ACCEPTED, anchors synthesized at schema 4, artifact loads
after :  AcceptanceError — "this proposal would extend prior accepted authority whose own
         succession evidence does not hold: … no batch states the representation schema it
         was reviewed under"
```

## Bounded sibling audit — every seam taking `AcceptedInputs`

| Seam | Transforms schema evidence? | Disposition |
|---|---|---|
| `accept_proposal` / `_carried_anchors` | synthesizes and carries | **patched** — validates through the shared rule before anything is computed from the prior |
| `lift_accepted_inputs` | re-declares and synthesizes | **patched** — same function, not a second implementation; a dangling-anchor prior is refused rather than lifted |
| `schema_lift.carried_anchors` | the rule itself | validating by construction |
| `load_accepted_inputs` | reads and constructs | **already validating** — this is the contract the two above now share |
| `committed_oracle_for`, `committed_inputs_for`, `_resolve_committed_*` | none | **protected by a validated caller** — every one resolves through `load_accepted_inputs` |
| `candidate_from_accepted_inputs` | reads the oracle only | **no evidence transformation** |
| `accepted_inputs_payload` | serializes what it is given | **no synthesis** — both producers validate, and the loader refuses anything else on the way back in |
| `AcceptedInputs.classification()` | batches and acceptances only | out of scope — carries no schema evidence |

One test fixture was itself the defect: `test_the_reverse_transition_is_refused` built its schema-4 prior
by re-declaring the committed artifact with no anchors. It now anchors that prior at schema 4, so the test
proves what it is named for — the registry has no 4-to-3 row — rather than passing on a restamp the guard
should refuse.

## Enforcement only — no re-pin

```
SCHEMA_3_HASH  : 43ed330d…  unchanged
SCHEMA_4_HASH  : 241860418b…  unchanged, and still == representation_schema_hash()
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
oracle_identity                : a0f0bd2f… unmoved
committed artifact round-trips to identical payload : yes
alembic                        : 0030 (head), no migration
```

---

# Round 9

## R9-1 — a key the serializer always writes was treated as optional

Reproduced first, on `{"boundary": "end_of_day"}` through all three production builders:

```
oracle._recurrence                 Recurrence(boundary=END_OF_DAY, whose=None)
persistence._recurrence_from_row   Recurrence(boundary=END_OF_DAY, whose=None)
patches._build_recurrence          Recurrence(boundary=END_OF_DAY, whose=None)
```

`recurrence_payload` emits every field of this value object unconditionally — a day-boundary cadence
serializes to `{"boundary": "end_of_day", "whose": null}` — and the schema grammar does not declare
`whose` omitted-when-empty. So an object without it is a shape nothing ever wrote, and rebuilding it as an
explicit null gives an incomplete row a meaning rather than refusing it.

**The omission that *is* declared is one level up and untouched:** `recurs` itself is absent when a
component states no cadence, which is what keeps an inherited schema-3 component byte-identical under
schema 4. This round changed the shape *inside* a present recurrence, never whether one is present.

## Single-sourced, three readers

`representation.RECURRENCE_KEYS` is derived from the declared type — `frozenset(f.name for f in
fields(Recurrence))` — rather than restated, so it cannot drift from what the serializer emits. Each
builder reads it and keeps its own typed error, which is how every other shape in these modules is
checked. No new parsing framework for a two-field value object.

```
case                       oracle            persistence       patches
{boundary} only            OracleLoadError   PersistedState…   InvalidPatchError
{boundary, whose: null}    rebuilds          rebuilds          rebuilds
turn + whose               rebuilds          rebuilds          rebuilds
turn, whose null           refused           refused           refused
day + whose set            refused           refused           refused
unknown key                refused           refused           refused
whose only (no boundary)   refused           refused           refused
```

Every row runs against all three builders in one parametrized class, so a fourth builder joins the rule by
joining the table and no builder can quietly diverge.

## What the end-to-end tests had to account for

A cadence *is* schema-4 meaning, so an artifact carrying one must declare schema 4 — otherwise round 4's
legality guard refuses the file before the key shape is ever read, and the test would pass for the wrong
reason. The loader tests therefore declare schema 4 and anchor their batches there (the fresh-schema-4
shape round 7 admits), and the missing-`whose` case asserts the refusal names `missing ['whose']`.

## Aligns reconstruction with the declared schema — nothing re-pinned

```
live payload hash : 241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9
SCHEMA_4_HASH     : unmoved, and still equal to it
SCHEMA_3_HASH     : 43ed330d…  unchanged
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
oracle_identity                : a0f0bd2f… unmoved
committed artifact round-trips to identical payload : yes
alembic                        : 0030 (head), no migration
```

---

# Round 10 — `431d199` → this commit

Two accepted P1s, both merge-blocking, both enforcement/API corrections. No schema hash re-pinned.

## R10-1 — an artifact already at its target could not be lifted to it

Checkpoint T-7 requires that carrying accepted authority to the schema it already declares be a
byte-identical no-op recording no second `SchemaLiftRecord`. `lift_accepted_inputs` called `lift_for`
unconditionally, so the equal pair went to the registry and was refused:

```
before   lift_accepted_inputs(schema-4 artifact, schema 4)
         UnknownSchemaLiftError: no authorized representation-schema lift from
         '5d-representation-schema-4' (241860418b…) to '5d-representation-schema-4' (241860418b…)

after    returns (inputs, None) — the same object, and no record
```

`lift_for` was right and is unchanged. An equal pair is not a registered succession, and teaching the
registry to answer for one would merge two different questions — *is this transition authorized?* and *is
there anything to do?* — into one row that every future schema would acquire for free. The no-op therefore
lives in the caller, which is the layer that has both questions.

**Idempotent is not unconditional.** "Already at the target" is a claim about the artifact, so the same two
checks the crossing path runs must hold before it can be made: `schema_binding_violations` (the
representation is legal under the pair, and the pair is a contract this build accepts authority under) and
the complete succession evidence. An unknown pair, an illegal representation and malformed anchor or lift
evidence are each refused on the equal-pair path.

Nothing is synthesized on it. The object returned *is* the object passed in — byte-identity by
construction, not by a comparison that could be satisfied loosely — so no anchor is derived, no
declaration rewritten, and no record appended. `carried_anchors` is deliberately **not** called here: it
synthesizes legacy anchors for the exact schema-3/no-lift shape, which is the one thing the no-op path may
not do. Both it and the no-op instead call a new private `_require_succession_evidence`, so there is one
statement of the rule and two readers of it rather than two spellings that could drift.

The return type is now `SchemaLiftRecord | None`. No production caller exists — `accept_proposal` uses
`lift_for`/`verify_lift` directly and assembles `lifts` itself — so the widening reaches tests only, and
the existing schema-3→schema-4 behaviour and its one real record are untouched.

**The middle state is refused, and that is deliberate.** `lift_accepted_inputs` returns its record
*separately* rather than appending it, so the artifact straight out of a genuine lift declares schema 4
while anchored at schema 3 with `lifts=()`. That is incomplete evidence — a succession claimed by the
declaration and evidenced nowhere — and rule 4 of `succession_evidence_violations` refuses it. The
idempotence test builds the fully evidenced artifact (`replace(lifted, lifts=(record,))`), and a separate
test pins that the un-evidenced middle state is refused rather than papering over it.

## R10-2 — the closed structure was enforced in two of its four places

`verify_lift` certified all three top-level subclass axes as unchanged:

```
before   draft subclass      CERTIFIED — 5d-lift-schema-3-to-4, 6 collections
         tuple subclass      CERTIFIED — 5d-lift-schema-3-to-4, 6 collections
         element subclass    CERTIFIED — 5d-lift-schema-3-to-4, 6 collections

after    draft subclass      SchemaLiftError … representation must be RepresentationDraft
         tuple subclass      SchemaLiftError … representation.records must be tuple
         element subclass    SchemaLiftError … representation.records[0] must be RecordDraft
```

Byte-identity is the wrong proof to run on any of them, for the reason it is wrong on a nested subclass: a
subclass canonicalizes to its declared base's payload, so proving *that* unchanged proves the wrong thing.

`representation_draft_violations` already existed and already stated the whole top-level rule — the draft,
the exact `tuple` type of each of the six collections, and the exact type of every element. It was enforced
at `accept_proposal` and at `validate_representation`, and the reusable invariant simply never called it:
`declared_meaning_violations` ran `post_schema_3_violations` + `held_structure_violations`, which is the
nested remainder. So the rule was complete and its shared boundary was not, and every seam reading that
boundary — `verify_lift`, `lift_accepted_inputs` including the new no-op, and `validate_schema_binding` —
inherited the gap. One call closes all of them, which is why the fix is a routing change rather than a new
check.

**The top-level check returns immediately rather than accumulating.** That is a correctness requirement,
not tidiness. `RepresentationDraft` is not a closed value object, so `_declared_type` resolves a hostile
draft subclass to *itself* and the post-schema-3 walk below would iterate `fields()` and read its smuggled
field; `held_structure_violations` would consult a hostile collection's `__iter__`. Observing the value is
what is being refused, so nothing may look at it once the shape is known to be wrong. The tests assert
**exactly one** finding per axis, which is that ordering stated as an assertion rather than as a comment.

**`acceptance.py`'s pre-merge check is untouched, and is not redundant.** Its ordering protects the keyed
union: it runs before the merge that compares elements to decide what is already accepted, where a
redefined `__eq__` only has to be consulted once. A later shared check cannot restore an element the merge
has already collapsed.

## Bounded sibling audit — every caller of the shared representation invariant

**Family.** *A shared invariant exists and a seam does not route through it.* Rounds 4, 8 and 10-2 are
one family: round 4 found `load_accepted_inputs` never checking declared-schema legality, round 8 found
`accept_proposal` synthesizing the evidence the loader would check, and round 10-2 found the invariant
itself calling only the nested half of the closed-structure rule. `schema_lift.py` has now taken rounds 3,
4, 7, 8 and 10, so the standing boundary trigger has fired.

**Trigger.** Repeated rounds on the same hotspot and the same defect family. Round 8's audit was bounded to
*seams accepting `AcceptedInputs`*; it did not cover *callers of the invariant*, which is the axis this
round's defect sat on. This audit closes that gap as a report.

**Scope.** Every production call of the four functions that state the rule, enumerated exhaustively over
`src/`: `declared_meaning_violations`, `schema_binding_violations`, `representation_draft_violations`,
`held_structure_violations`.

| Seam | Reads the rule through | Disposition |
|---|---|---|
| `oracle.load_accepted_inputs` | `schema_binding_violations` | already safe — closed in round 4 |
| `acceptance.accept_proposal`, proposed half | `schema_binding_violations` | already safe — round 4 |
| `acceptance.accept_proposal`, prior half | `schema_binding_violations` | already safe — round 4 |
| `acceptance._merge`, pre-merge | `representation_draft_violations` + `held_structure_violations`, directly | already safe — deliberately direct and **unchanged**; its ordering protects the keyed union, and a later shared check cannot restore an element the merge has already collapsed |
| `schema_lift.verify_lift` | `schema_binding_violations` | **patched** — inherited the gap; the reported defect |
| `schema_lift.lift_accepted_inputs`, no-op | `schema_binding_violations` | new this round, on the shared rule from the start |
| `projection.validate_schema_binding` | `declared_meaning_violations` | **patched** by the same routing change; now covered by its own three-axis test rather than inferred from the shared call |
| `validation.validate_representation` | `representation_draft_violations`, then its own walkers over the same underlying rules | already safe |

No caller was found outside this set, and none is left routing around the invariant. Nothing here is
`out of scope`, `Known Unknown`, or `owner decision needed`.

**One residue, reported rather than decided.** The invariant manifest has 17 rows and none for the
top-level closed shape. The manifest declares intrinsic *value* invariants — what a value may hold —
whereas exact runtime type is a property of the Python object graph rather than of the serialized
contract, and declaring it would move the schema hash for a rule that is neither new nor serialized. Left
as a manifest-completeness question for the Owner rather than resolved in an enforcement round.

## Enforcement only — no re-pin

Neither manifest changed. `representation_schema_payload()` is built from the type, vocabulary and
invariant *declarations*; this round rerouted an existing rule and widened a return type, and touched
neither. No `_Invariant` row was added for the top-level closed shape: it is not new enforcement, and
declaring it would move a hash this round has no reason to move.

```
live payload hash : 241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9
SCHEMA_4_HASH     : unmoved, and still equal to it
SCHEMA_3_HASH     : 43ed330d…  unchanged
lift_for(4,4), lift_for(3,3)   : still unregistered
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
proposal identities            : unchanged
oracle_identity                : a0f0bd2f… unmoved
committed artifact round-trips to identical payload : yes
alembic                        : 0030 (head), no migration
```

---

# Round 11 — `1b0d208` → this commit

One accepted merge-blocking P1. Enforcement only; neither schema hash moved.

## R11-1 — round 10 checked the elements, not the containers they sit in

Round 10 closed the top-level boundary — the draft, the exact `tuple` type of each of the six collections,
and the exact type of every element in them. It did not reach the tuples nested *inside* those elements,
and every one of those was checked with `isinstance` (which admits a subclass) or was not checked at all.

```
before
  AbilityCheckFact.alternatives = SmuggledTuple(...)   CLEAN — admitted
  SizeKeyedQuantityFact.values  = SmuggledTuple(...)   CLEAN — admitted
  subclass vs exact tuple: same fact_key? True   same payload? True

  alternatives = HostileTuple(...)   AssertionError: __iter__ was invoked
  values       = HostileTuple(...)   AssertionError: __iter__ was invoked

  alternatives = TwoFacedTuple(...)  validation iterates and sees 0 members
                                     indexing shows 2
                                     finding: "no member states the fact's own pair"

after
  every case above    "<field> must be tuple, got <Type>"   nothing iterated, nothing rendered
```

Three distinct leaks, and the middle one is why `isinstance` was never enough on its own:

* **hidden state** — a subclass carries meaning no canonical payload emits, so two facts asserting
  different authority produce one `fact_key`;
* **hostile `__iter__`** — the validator and the serializer observe different contents from one object, so
  the finding produced describes content the artifact does not have. The two-faced case is the sharpest
  form: the old code returned a complaint about an *empty* choice while the fact held two rolls;
* **hostile `__hash__`/`__eq__`** — `ProvenanceClaim.target_key` is a *key*, resolved by set membership, so
  a subclass can match a target it is not.

## The rule, and why it is a separate helper

`exact_tuple_violations(value, field)` reports `type(value).__name__` and nothing else. No iteration, no
length, and deliberately no `repr` — unlike `exact_type_violations`, which interpolates the value and is
safe only because its callers have already established the container. A subclass may override `__repr__`
too, and a refusal that renders the thing it refuses has observed it. One test pins this with a container
whose `__iter__` *and* `__repr__` raise.

The inventory is derived, not listed: `declared_tuple_fields(cls)` reads the dataclass, and
`held_container_violations(value, tag)` checks every tuple field the value's *declared* type declares. A
new authority dataclass, or a new tuple field on an existing one, joins the audited surface by being
declared. A test asserts the parametrized witness table equals the derived set, so a tenth field fails the
suite rather than shipping unaudited.

## Ordering — the part the field-by-field patch did not settle

Patching each validator was not sufficient, and the hostile-iteration test is what proved it: several
functions read a component's facts. `option_set_violations` builds `fact_key` signatures to compare arms
and `fact_qualifier_violations` builds scoped keys, and both receive the tuples **already unpacked as
parameters** — so neither can be where the container is checked, because by then its caller has iterated.

So the containers a component holds are scanned *whole*, at every depth, before any reader touches one, and
the component is skipped entirely if anything is not an exact tuple. An earlier attempt gated on "any
content finding" instead and suppressed an unrelated option-subclass finding; the gate is specifically the
container scan, so ordinary semantic findings still report as they did.

Element containers are also checked at the top-level boundary in `representation_draft_violations`, right
after each element's exact type is established. That is what protects `validate_representation`'s
provenance pass, where `target_key` reaches set membership.

## Bounded family audit — every tuple-valued field of a serialized authority dataclass

**Enumeration method.** Derived from `_CLOSED_TYPES ∪ _DRAFT_ELEMENT_TYPES ∪ {RepresentationDraft}` via
`fields()`, filtering on the declared annotation — not read off the review comment. **15 fields on 58
dataclasses.** No sequence-shaped annotation spelled anything other than `tuple` exists on that surface.

| Field | Before | Disposition |
|---|---|---|
| `AbilityCheckFact.alternatives` | `isinstance` + element scan behind `or`, iterated to decide | **patched** |
| `SizeKeyedQuantityFact.values` | `isinstance` + element scan behind `or`, iterated to decide | **patched** |
| `DamageResponseFact.except_types` | `isinstance`, correctly ordered before its loop | **patched** — exactness only; the ordering was already right |
| `Applicability.any_of` | `isinstance` + element scan behind `or` | **patched** — short-circuits the element scan without disturbing the delegated `fraction` check |
| `ComponentDraft.facts` | unchecked container; iterated to build scopes and keys | **patched** — in the pre-scan, not in the consumers |
| `ComponentDraft.options` | unchecked container; iterated to build scopes | **patched** |
| `ComponentDraft.fact_qualifiers` | unchecked container | **patched** |
| `ComponentOption.facts` | unchecked container; keyed by `option_set_violations` | **patched** |
| `ProvenanceClaim.target_key` | **never type-checked at all**; reached set membership directly | **patched (previously unchecked)** |
| `RepresentationDraft.records` | exact-`tuple` checked before iteration | already safe — round 10 |
| `RepresentationDraft.components` | exact-`tuple` checked before iteration | already safe — round 10 |
| `RepresentationDraft.prose_bindings` | exact-`tuple` checked before iteration | already safe — round 10 |
| `RepresentationDraft.relationships` | exact-`tuple` checked before iteration | already safe — round 10 |
| `RepresentationDraft.references` | exact-`tuple` checked before iteration | already safe — round 10 |
| `RepresentationDraft.provenance` | exact-`tuple` checked before iteration | already safe — round 10 |

**Excluded, and named rather than omitted.** The evidence-side tuples —
`AcceptedInputs.batches`/`acceptances`/`schema_anchors`/`lifts`, `AcceptedOracle.spans`/`obligations`, and
`SchemaLiftRecord.verified_collections` — are `out of scope` for this round: they are acceptance and
succession evidence, not representation authority, and they are loader-built from JSON rather than
authored. Parser-local arrays, constants, function parameters and non-authority implementation tuples are
excluded by the same scoping.

## Enforcement only — no re-pin, and no manifest row

JSON already declares each of these fields as an array. Exact Python container type adds no serialized
grammar, so no `_Invariant` row was added and the schema payload is unchanged.

```
live payload hash : 241860418b183f67bcc4d914d1fdaa3bbcea1705f28cdd460eb05716d40ce3e9
SCHEMA_4_HASH     : unmoved, and still equal to it
SCHEMA_3_HASH     : 43ed330d…  unchanged
six collections byte-identical : yes
185 provenance coordinates, 15 references : re-derive identically
proposal identity              : 14587d5b… unchanged
oracle_identity                : a0f0bd2f… unmoved
committed artifact round-trips to identical payload : yes
alembic                        : 0030 (head), no migration
```

---

# Round 12 — boundary classification, recorded before any code changed

## Defect family

**Closed-structure observation-order violation.** Not "one more tuple subclass".

Round 11 established that a nested container must be an exact `tuple` before any reader iterates it, and
added `held_container_violations` as the pre-scan that enforces it. That pre-scan calls
`_declared_type(value)` and then reads the value's tuple fields with `getattr` — *before* the owning object
has passed its own exact-runtime-type gate. A hostile subclass therefore executes `__getattribute__` before
`fact_invariant_violations` or `applicability_violations` refuses it.

This is the same invariant every subclass round since round 4 has been protecting, stated one level up:
**a rejected authority object must not be observed before it is rejected.** Rounds 10 and 11 each closed one
face of it — the element, then the container — while the *order* between the two remained implicit.

Reproduction found a second instance of the same family that the review comment did not name:
`exact_type_violations` interpolates `{value!r}` into its refusal, so refusing a hostile subclass renders it
and runs the hostile method. Round 11 avoided exactly this in `exact_tuple_violations` and did not carry the
reasoning back to the older helper. Same family, same round.

## Boundary decision

**CRD Issue 5d / PR A implementation scope.** Recorded per the standing boundary rule, which fired on the
repeated-hotspot trigger: `representation.py`'s closed-structure surface has now taken rounds 4, 10, 11 and
12.

| Classification | Verdict |
|---|---|
| new mechanical semantic | no |
| schema-content decision | no |
| Known Unknown | no |
| Owner Decision | no |
| general hostile-Python-object hardening project | **no — explicitly out of scope** |
| merge-blocking implementation defect | **yes** |

No ADR amendment. The accepted serialized contract is unchanged: this is runtime structural enforcement
only, so no representation-schema payload change, no manifest row, no schema-4 re-pin, and no movement of
inherited identities. Implementation did not discover any need to change serialized grammar; had it, the
instruction was to stop and report rather than proceed.

## The ownership rule this round establishes

> For every closed serialized authority object:
>
> **parent exact runtime type → held-container exact runtime type → child exact runtime type → semantic
> observation.**
>
> Until the applicable gate succeeds, do not read declared fields, iterate, hash or equality-test, `repr`,
> take length, construct keys, or otherwise observe the rejected value.

Structural admission owns this ordering. Semantic validators may assume admitted structure. One contract,
one choke point; the per-field checks that remain are callers of the shared rule, not parallel spellings of
it.

## Stop condition

Parent-before-container ordering enforced at the shared boundary, every production caller of the generic
walker classified, hostile-parent regressions passing, full gates green, zero movement holding. The sibling
search stops there. PR #159 does not become generalized Python adversarial-object hardening.
