# PR #155 — Codex review round 3 remediation log

CRD Issue #137, ADR-005d Decisions 8–10. Reviewed head
`f6d2813eaf6f9da824fe9382a0fdddbf77eebe09`. Two merge-blocking defect families,
three unresolved threads, all left unresolved for Owner review.

Scope held: the approved conditions-only schema-2 manifest is untouched. No
proposal accepted or published, no partial projection activated, no
`known_unknowns.md` amendment, no legacy authority removed, no 2b/15c work.

---

## Family 1 — incomplete option-scope propagation through typed overrides

**Threads:** `targets.py:77` (P1), `application.py:794` (P1).

`MechanicalTarget.option_key` existed only in memory. The consequence was not a
missing feature but a wrong answer: an override authored against an option fact
either could not be stored, or came back retargeted at the component's
direct-fact scope, and two in-memory targets differing only by option shared one
override-set identity.

### The compatibility constraint

`target_payload()` **omits** `option_key` when it is `None` rather than emitting
it as `None`. Emitting it would have carried the scope correctly *and* reminted
the identity of every override set already authored against a direct fact — the
same authority under a new identifier, no longer naming the retained version it
was recorded against. There is no collision risk: `__post_init__` already
refuses a blank `option_key`, so a present key always names a real option, and a
direct target's payload has four keys where an option target's has five.

The claim is unfalsifiable if both sides are computed by post-change code, so
the pre-change identity was captured by stashing `targets.py` back to the
reviewed head and re-deriving it:

```
one-entry direct-fact override set:  8404b420-e92e-5c5a-968d-5e676de881e6
EMPTY_OVERRIDE_SET_UUID:             521a6242-e6bc-5e76-9564-323c4c0deacb
```

Both are pinned as literals in
`test_review_round_3_option_scope.py::test_legacy_direct_target_identities_are_not_reminted`.

### Seams carried

| Seam | Disposition |
|---|---|
| `targets.py::target_payload()` | **patched** — conditional fifth key |
| `MechanicalOverrideORM.target_option_key` | **patched** — new nullable `String(255)` |
| `OverrideSetEntryORM.target_option_key` | **patched** — new nullable `String(255)` |
| migration `0028` (unmerged) | **patched** — both columns, additive |
| `0024`'s `prevent_rp_override_set_entries_reinsert` | **patched** — dropped and recreated over the new column set |
| `override_set.py::_parse_row()` | **patched** — reads `row.target_option_key` |
| `retention.py::_entry_from_row()` | **patched** — reads `row.target_option_key` |
| `retention.py::retain_override_set()` insert | **patched** — copies `entry.target.option_key` |
| `application.py:782` FACT/DISABLE existence lookup | **patched** — passes `target.option_key` |
| `application.py::_finalize_component()` final `replace()` | **patched** — returns the rebuilt `options` |
| `conftest.py::_ENTRY_CONTENT_COLUMNS` | **patched** — mirrors the migration's guard |
| `conftest.py::author_override()` | **patched** — writes `target_option_key` |
| fixture trigger mirror vs. migrated guard | **patched** — newly asserted; they were two unchecked copies |
| `MechanicalTarget.__post_init__` | already safe — rejects blank and non-FACT `option_key` |
| `MechanicalTarget.describe()` | already safe — renders `[option]` |
| `application.py::_find_fact()` | already safe — already scope-aware |
| `application.py::_suppressed_by()` | already safe — four-element disabled-fact key |
| `application.py::_base_records()` | already safe — builds per-option `EffectiveFact` |
| REPLACE / APPEND fact paths (`application.py:897–986`) | already safe — already resolve `option_key` |
| `_finalize_component()` handling derivation | already safe — `facts_present` already read the filtered options |
| `projection.py::derive_fact_id` / `fact_target_key` | already safe — fourth element already carried |
| `views.py` `structured_context` | already safe — publishes `facts` and `options` separately |
| `patches.py` operation/kind matrix | already safe — no option axis, and none added |

**Boundary, not a defect:** `tests/services/rules_authority/conftest.py::author_override`
is the only `MechanicalOverrideORM` insertion path in the tree. There is no
production override-authoring service yet, so "insertion/copy paths" reduces to
the retention copy plus that test helper.

**Not done, deliberately:** override precedence is unchanged, no `OPTION` target
kind was added, and DISABLE/REPLACE/APPEND semantics are untouched.

### `application.py:782` — the second half of that thread

The scope-blind existence check rejected *every* valid option-fact disable as
`INVALID_OVERRIDE`, because a choice component is required to have no direct
facts. Fixing only the lookup would still have left the fact visible:
`_finalize_component()` computed filtered `options` and then discarded them in
its final `replace()`. Both halves are patched, and both are proven separately
(`test_an_option_fact_disable_is_accepted_at_all`,
`test_the_filtered_options_reach_the_assembled_view`).

---

## Family 2 — applicability payloads did not fail closed on primitive types

**Thread:** `oracle.py:430` (P1).

`bool("false")` is `True`. Both loaders coerced `negated`, so a malformed
accepted-input file reconstructed as the *opposite* applicability, was
canonicalized in that form, and could pass publication against an identically
coerced oracle. `value` and the nested `at_least` had no exact integer check
either: `bool` is an `int` subclass, so `True` satisfied `value < 0` and
`at_least < 1` silently as `1`, and a string raised an incidental `TypeError`
from the comparison rather than a stated finding.

### Where the rule lives

Stated once, on the build side, because both loaders already call the invariant
functions after construction:

* `representation.py::applicability_violations` — exact `bool` for `negated`,
  exact `int`-or-`None` for `value` (excluding `bool`), `isinstance` for each
  enum field, and `any_of` as a tuple of `SizeComparison`. Placed **before**
  `_is_set` and the range comparisons, with its own early return.
* `representation.py::size_comparison_violations` — the same treatment for
  `category`, `relation`, and `at_least`, also with an early return, so one
  defect produces one finding rather than a second misleading opinion about a
  range the value never had.
* `projection.py::applicability_payload_violations` — **new**. The typed
  invariants cannot see a missing or misspelled JSON key, which was the real
  gap: extra keys were silently ignored in both loaders. Closed 8-key top level,
  closed 3-key `any_of` member. Placed next to `applicability_payload` so the
  emitted shape and the accepted shape are declared together; both loaders
  already import that module, so no cycle.

### Loader changes

* `oracle.py::_applicability` — `bool(raw["negated"])` → `raw["negated"]`; runs
  `applicability_payload_violations` first; raises `OracleLoadError`.
* `persistence.py::_applicability_from_row` — same de-coercion; dropped
  `cast("int | None", raw["value"])` and `cast("list[dict[str, Any]]", …)`,
  which asserted types the checker was about to test; raises
  `PersistedStateReconstructionError`.

Nothing is normalized, coerced, defaulted, or reinterpreted.

**Already safe:** enum *values* were already fail-closed —
`CreatureSize(0)` raises `ValueError`, which both loaders already wrap in their
own error type. No redundant guard was added for those.

---

## Regression coverage

`tests/services/rules_authority/test_review_round_3_option_scope.py` — 13 tests.

1. Direct-target canonical payload and pre-change identity literals unchanged;
   `EMPTY_OVERRIDE_SET_UUID` unchanged; the same fact key direct / in option A /
   in option B yields three distinct override-set identities.
2. Authoring rows store the scope and `collect_current_override_state` reads it
   back exactly; retained replay round-trips it and still re-derives its own
   identity **after the current row has been retargeted to another option and
   then deleted**; two options retain as two versions; a stored option scope on
   a RECORD target fails closed with `OverrideStateError`.
3. Disabling an option fact removes only that fact: the sibling fact of the same
   option survives, the identical fact in the sibling option survives, and the
   identical fact held directly on another component survives. The inverse
   direction holds too, the disable is accepted at all, and a disable naming a
   fact absent from the named option still fails.

Built as a standalone `ProjectionCandidate` rather than by growing the shared
runtime fixture, whose element counts are asserted across the suite.

`tests/ingestion/mechanical/test_review_round_3_applicability_types.py` — 54 tests.

4–5. One corruption table of 20 malformed payloads run through **both** doors:
`"false"`, `"true"`, `0`, `1`, `null` for `negated`; `True`/`False`/`"0"`/`0.0`
for `value`; `True`/`"2"`/`2.0` for the nested `at_least`; missing key,
misspelled key, extra key, missing/extra `any_of` member key, `any_of` as a
string, `any_of` holding a scalar, and a non-object payload — asserting
`OracleLoadError` on the accepted-input side and
`PersistedStateReconstructionError` on the stored-state side. Plus build-side
proofs that in-memory construction is rejected deterministically rather than
passing or raising `TypeError`, and two end-to-end tests corrupting
`rp_mech_components.applies_when` and `rp_mech_component_options.applies_when`
in the database and asserting `reconstruct_candidate` refuses — the
component- and option-level scopes the task names.

---

## Notes

* The `5d-representation-schema-2` structural hash `ca27a746…` is **untouched**.
  Override target columns are runtime authority, not representation shape.
* The suite's trigger mirror (`conftest.py::_ENTRY_CONTENT_COLUMNS`) and the
  migration are two hand-maintained copies of one guard, and the pre-existing
  trigger-set test compares only *names*. A new assertion reads the migrated
  trigger's own SQL and requires every mirrored column to appear in it; it was
  verified to fail on an injected drift. Without it, drift would leave every
  retention and override-set test passing against a guard the production schema
  does not have.
* The two end-to-end persistence corruptions were checked for vacuity rather
  than assumed non-vacuous: the persisted fixture carries a stored qualifier on
  3 of 3 component rows and 2 of 2 option rows, and the component-scope failure
  is attributed to `rp_mech_components spell:wish/descriptor`. (SQLAlchemy's
  `sa.JSON` stores Python `None` as a JSON `null` literal rather than SQL NULL,
  which is why the component rows are non-NULL despite the draft declaring no
  component-level qualifier.)
* Black reformatted 11 unrelated `alembic/versions/*.py` files when run outside
  the repository's stated `src/ tests/` gate scope; those were reverted and only
  `0028` carries a formatting change.

---

# Round 4 — three P1 findings

Reviewed head `3eeda482cbd2b0cbbc20fcc9624066f60538953d`, verified unmoved before
starting. Three threads, all left **unresolved** for Owner review. Scope held as
in round 3: no proposal accepted or published, no partial projection activated,
`known_unknowns.md` unchanged, no legacy authority removed, override precedence
untouched, and no Issue 2b / 15c / #129 / production-authoring work.

## Finding 1 — retained-entry triggers lost on downgrade

**Thread:** `0028:163` (P1).

**Root cause.** SQLite implements `ALTER TABLE … DROP COLUMN` by rebuilding the
table, and a rebuild drops every trigger attached to the old one. `downgrade()`
restored only `prevent_rp_override_set_entries_reinsert`, so after rolling 0028
back to 0027 the retained evidence was updatable, deletable, and extendable past
its seal.

**Measured before fixing**, rather than reasoned about:

| Direction | Triggers present after |
|---|---|
| 0027 → 0028 (`ADD COLUMN`) | all four — **already preserved** |
| 0028 → 0027 (`DROP COLUMN`) | `reinsert` only — **three lost** |

| Trigger | 0027→0028 | 0028→0027 |
|---|---|---|
| `prevent_rp_override_set_entries_update` | already preserved | **patched** |
| `prevent_rp_override_set_entries_delete` | already preserved | **patched** |
| `prevent_rp_override_set_entries_reinsert` | patched in round 3 (column set) | already restored |
| `seal_rp_override_set_entries` | already preserved | **patched** |

`_entry_triggers(columns)` now returns all four, with the update/delete/seal SQL
copied from `0024` verbatim so the two cannot drift, and **both** directions call
it — upgrade recreates the family too, so neither direction has to be reasoned
about separately. `seal_` is emitted last; it reads `rp_override_set_versions`,
which both directions leave in place.

**Tests.** A direct 0028↔0027 boundary test (the existing downgrade test walks to
0023, where the table no longer exists — which is why this was invisible), plus
behavioural injection of update, delete, conflicting reinsert, and post-seal
extension against a genuinely rolled-back database: presence in `sqlite_master`
is not the claim, refusal is. A third test proves the restored 0027 guard sheds
`target_option_key` and keeps every other column. All were verified to fail
against the reinstated defect.

## Finding 2 — closed schema-2 structures accepted subclasses

**Thread:** `representation.py:3986` (P1).

**Defect family: closed-structure identity leak.** `applicability_violations()`
never required `type(applicability) is Applicability`, and the `any_of` loop used
`isinstance`. A dataclass subclass carrying an undeclared meaning-bearing field
validated cleanly while `applicability_payload()` emitted only the declared keys
— so two structures asserting *different* conditions received one canonical
payload, one persisted form, and one identity. A subclass may also redefine
equality, letting a duplicate slip past the `seen` set in the size-comparison
dedup check.

The rule already existed as `_vo_field`, used by the fact-family validators. It
is now published as `exact_type_violations` and applied at the three leaking
sites.

| Structure | Disposition |
|---|---|
| `Applicability` | **patched** — gate is the first statement, before `kind` is read (a subclass could shadow it) |
| `SizeComparison` (top level) | **patched** — gate first, before any field read |
| `SizeComparison` (inside `any_of`) | **patched** — `isinstance` → exact type |
| `ComponentOption` | **patched** — `validation.py::_validate_options`, before the key/fact reads and dedup checks it would evade |
| six new schema-2 fact families | **already safe** — `fact_invariant_violations` already tests `_FACT_TYPES[family] is not type(fact)` |
| `ComponentDraft`, `RecordDraft`, `ProseBindingDraft`, `ProvenanceClaim` | **out of scope** — same latent exposure, but pre-existing top-level draft structures, not newly introduced by schema 2. Guarding one and not the rest would be arbitrary, and guarding all of them is the repository-wide dataclass refactor this task forbids. **Surfaced, not silently fixed.** |

**Tests.** Subclasses carrying extra meaning-bearing fields at each site; a
`kind`-shadowing subclass proving the gate precedes every field read; an
`eq=False` subclass whose two distinct instances collide as one set member,
proving the dedup-evasion vector and that the gate fires before dedup runs; a
property test showing two differing subclass instances emit byte-identical
canonical payloads (the leak itself); and component-level and option-level
applicability both failing deterministically for the same stated reason.

## Finding 3 — option-scoped fact appends were unreachable

**Thread:** `targets.py:105` (P1). Owner Decision 2026-08-19 approved.

**Root cause.** Schema 2 added option-aware append code to `_apply_entry()` that
nothing could reach. `(APPEND, FACT)` is unsupported, `(APPEND, COMPONENT)` was
the only fact addition, and `MechanicalTarget` rejected `option_key` on every
non-`FACT` target — so appending a fact to either arm of a choice always fell
into the *"must be appended to one of its options, not beside them"* refusal. A
schema-permitted operation had no encoding.

`MechanicalTargetKind.OPTION` is that encoding, and only that:
`record_key` + `component_key` + nonblank `option_key`, `fact_key` forbidden.
`(APPEND, OPTION) → FactAdditionPatch` is the sole permitted pairing.

`DISABLE` and `REPLACE` on `OPTION` stay unsupported, and deliberately for a
*different* reason than `(APPEND, FACT)`: an option does have content that could
be suppressed or replaced, but the source states the choice as **exhaustive**, so
removing or rewriting one arm would publish a choice the source never states.
`required_patch_family` now says so rather than reusing the "no multiplicity"
message, which would have been inaccurate for this grain.

| Seam | Disposition |
|---|---|
| `MechanicalTargetKind.OPTION` | **patched** |
| `__post_init__` shape rules | **patched** — third branch, not the `else` that forbids `option_key` |
| `_REQUIRED_FAMILY[(APPEND, OPTION)]` | **patched** |
| `required_patch_family` refusal message | **patched** — states exhaustiveness, not absent multiplicity |
| `_suppressed_by` | **patched** — OPTION branch before the `assert … is FACT`; record and component disables suppress it, an individual fact disable does not |
| `target_payload()` | **already safe** — the round-3 conditional already emits the fifth key, and `kind` differs |
| `describe()` | **already safe** — already renders `[option]` |
| `_parse_row` / `_entry_from_row` | **already safe** — `MechanicalTargetKind(row.target_kind)` and the existing `target_option_key` column |
| `retain_override_set` insert | **already safe** — copies `target.option_key` regardless of kind |
| `_apply_entry` fact dispatch | **already safe** — an OPTION target arrives with non-`None` `option_key` and no `fact_key`, exactly the shape the addition path wants |
| migration / ORM | **already safe** — reuses `target_option_key`; **no new migration**, no second scope field |
| `views.py`, `service.py` | **already safe** — neither switches on target kind |

**Tests.** Append into each named option; the appended fact naming its override
rather than a 5c span; both options appended independently; duplicate detection
scoped per option; a fact a *sibling* option already holds still appending (the
isolation case a scope-blind check would refuse); missing option, missing
component, and option-target-on-a-non-choice failures; `DISABLE`/`REPLACE` on
OPTION and `APPEND` on FACT all refused; suppression by an earlier record and
component disable; a prose-bound component still refusing; authoring-row and
retained-replay round trips verified after the mutable row is retargeted and
deleted; a stored OPTION row carrying a `fact_key` failing closed; and the
round-3 pinned direct-target identity re-asserted unmoved.

## Authority reconciliation

ADR-005d Decision 10 and #137's typed-target/APPEND contract are reconciled in
`targets.py`'s module docstring and `patches.py`'s matrix comment: **OPTION is an
APPEND-only container grain, not a generally suppressible or replaceable
choice-arm target.**

The representation schema version and hash are **unchanged** —
`5d-representation-schema-2` /
`ca27a7468abb84db43781e96ac48fbc55e166c3e410fe33d80f03a263a8d002c`, re-derived
and asserted after the change. OPTION is a runtime override target kind; it does
not participate in representation identity, and repository evidence confirms that
rather than the claim resting on inspection.
