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
