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
