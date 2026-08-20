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
| `service.py` | **already safe** — does not switch on target kind |
| `views.py` | **already safe, asserted** — grep proved no kind-branching, which is not the same as correct published output. Driven end to end instead: `build_gamemaster_view` publishes an appended option fact inside its own option, absent from `structured_context` and from the sibling option, so mutual exclusivity survives the new grain. |

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

---

# Round 5 — authority-consistency remediation

Reviewed head `9608a80373a15f35a6e5aa29cbc2cd282de4a348`, verified unmoved before
starting. Bounded to reconciling governing texts and correcting stale
implementation documentation. No implementation reopened, no OPTION redesign, no
review thread resolved, `known_unknowns.md` unchanged.

## Finding 1 — governing authorities were not actually reconciled

**This was an overclaim in my own round-4 PR body**, and the correction is
recorded here rather than quietly fixed. That body stated the Owner Decision was
"reconciled" with ADR-005d Decision 10 and Issue #137. What was actually
reconciled was the *implementing code's* self-description —
`targets.py`'s module docstring and `patches.py`'s matrix comment. Neither
authoritative text was touched, and the round-4 commit range contains no ADR
change. Under CLAUDE.md's authority order the ADR and the governing issue rank
above source code, so describing a docstring edit as an authority reconciliation
inverted that order.

Both texts are now amended narrowly, in each document's established
"**Amended by Owner Decision …**" voice:

| Document | Change | Preservation |
|---|---|---|
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`, end of Decision 10 | +36 lines, 0 removed | pure insertion; rest byte-for-byte |
| GitHub Issue #137, contract 6, after the 2026-08-08 prose-overlay amendment | +2505 chars | rest byte-for-byte apart from one trailing newline GitHub appends |

Each records the same six points: `OPTION` as a fifth exact typed target grain
(`record_key` + `component_key` + nonblank `option_key`, `fact_key` forbidden);
the option targeted only as the owning container for fact addition; only
`(APPEND, OPTION) → FactAdditionPatch` permitted; `DISABLE`/`REPLACE` on
`OPTION` unsupported because altering an arm would falsify an exhaustive
source-authored choice; `APPEND` on `FACT` unsupported because a fact has no
multiplicity; and the identity envelope — reuses `target_option_key`, changes
override-set identity where an `OPTION` target is present, leaves existing
direct-target canonical payloads and identities unchanged, does not change
representation schema identity.

**Verified against the live Issue after editing** rather than trusting the
command's exit status: the amendment is present once, all six points are
present, and a normalised diff of the live body minus the amendment against the
pre-edit body is identical across all 700 lines.

## Finding 2 — stale implementation documentation

`MechanicalTarget.option_key`'s comment still asserted *"there is no OPTION
target kind"* — true when written, false since round 4. It now describes the
actual split: on `FACT` the field is an optional qualifier naming an existing
fact's owning option; on `OPTION` it is required and is the target itself,
naming an APPEND-only fact container. The closing sentence keeps the rule both
forms share — neither makes an option suppressible or replaceable.

Comment-only: the diff contains no non-comment lines, and behaviour is unchanged.

## Deferred residue — top-level draft closure

`ComponentDraft`, `RecordDraft`, `ProseBindingDraft`, and `ProvenanceClaim`
accept subclasses in the same general closed-structure family round 4 closed for
`Applicability`, `SizeComparison`, and `ComponentOption`. **Deliberately not
closed here, and not partially closed.** Exact-gating `ComponentDraft` alone
would leave its siblings open while implying the family was handled, which is
worse than leaving all four visibly open.

This is separate 5d implementation work that must be closed coherently across
the whole top-level draft boundary **before any proposal is accepted or
published**, since acceptance is the point at which an unclosed structure could
persist undeclared state under a canonical identity. Recorded in the PR summary
as deferred residue. `known_unknowns.md` is unchanged — this is scheduled
implementation work with a known shape, not an undecided question.

---

# Round 6 — two P1 findings

Reviewed head `22872cd9ef8f02269289073a756d6e2f5aeab156`, verified unmoved before
starting. Both threads left **unresolved**; eight threads now stand open. Scope
held: no schema hash change, no OPTION decision reopened, no ADR or Issue
amendment, no acceptance/publication/activation, `known_unknowns.md` unchanged,
no legacy removal or 2b / 15c / #129 / production-authoring work.

## Finding 1 — complete component patches dropped schema-2 shape

**Thread:** `representation.py:3694` (P1).

**Root cause.** Schema 2 made `applies_when` and `options` part of a component's
authoritative shape, but the patch layer never learned them: `ComponentBody`
held neither field, `_build_component_body()` rejected both keys as unexpected,
`_component_body_payload()` emitted neither, and `_component_from_body()` always
constructed `EffectiveComponent` with their empty defaults. No complete
component patch could author a conditioned or choice-bearing component, and
replacing an existing one silently discarded whatever qualifier and option
structure the base projection gave it.

### The rules are stated once, not copied

The task forbids "a looser runtime copy of the schema", and the largest risk
here was exactly that — six option-set rules restated in `patches.py`.

* **Option-set validity** moved from `validation.py::_validate_options` to
  `representation.option_set_violations(facts, options, tag)`, stated over the
  two fields rather than over a whole `ComponentDraft` (which a replacement body
  cannot supply — it has no `record_key`). `_validate_options` now delegates, so
  its existing callers and tests are unchanged, and the patch parser calls the
  same function. Exhaustiveness, duplicate keys, duplicate fact sets, empty
  options, the exact `ComponentOption` type, direct-facts-versus-options, and
  per-option applicability are therefore one rule with two callers.
* **Applicability** is read in `patches.py` through the same two gates the
  accepted-input and persisted-state loaders already use —
  `applicability_payload_violations` for the closed key set, then
  `applicability_violations` for the typed contract — raising
  `InvalidPatchError`. That is a third *reader* of the rules, not a third copy;
  collapsing all three constructions into one builder would have rewritten two
  loaders that passed review last round, which this finding does not ask for.

### Seam dispositions

| Seam | Disposition |
|---|---|
| `ComponentBody` | **patched** — `applies_when`, `options`, reusing the representation's own types |
| `_build_component_body()` | **patched** — both keys optional on the way in; applicability and options parsed strictly |
| handling-honesty predicate | **patched** — counts option facts. A choice component has **no direct facts by contract**, so the old `if not facts` refusal would have rejected every honest option-bearing component. Same predicate as `_finalize_component`'s `facts_present`. |
| `_component_body_payload()` | **patched** — omits both when they hold legacy defaults; options sorted by `semantic_key`, each option's facts by `fact_key` |
| `_build_replace_record` / `_build_replace_component` / `_build_append_component` | **already safe** — all three route through `_build_component_body`, so one change closes all three families |
| `application.py::_component_from_body()` | **patched** — builds `applies_when` and `EffectiveOption` entries; every option fact carries `option_key` plus the supplying override's identity and origin |
| completeness of replacement | **already safe, asserted** — builds a fresh `EffectiveComponent` rather than `replace()`-ing the base, so omission removes rather than inherits. Proven against a base component that *does* carry a qualifier. |
| `_finalize_component`, `disabled_facts.difference_update` | **already safe** — both handle options generically since round 3 |
| `views.py::_gamemaster_component` | **already safe, asserted** — passes `options`/`applies_when` through generically; driven end to end rather than dispositioned by inspection, per the round-4 correction |
| `_REQUIRED_FAMILY` | **untouched** — an OPTION-target append (one fact into an existing option) and a component patch carrying options are different operations that coexist; conflating them would reopen the settled decision |
| top-level draft subclass closure | **still deferred** — unchanged from round 5, not expanded into here |

### Legacy compatibility

Captured on `22872cd` **before any edit**, by running the pre-change emitter —
the claim is unfalsifiable if computed with post-change code:

| Family | Override-set identity |
|---|---|
| `REPLACE_COMPONENT` | `e71ba996-4bc3-5ed3-8f2f-10ac83009a8f` |
| `APPEND_COMPONENT` | `95b4f149-8ce4-5a4b-98be-209c924907e2` |
| `REPLACE_RECORD` | `eaf62f89-5582-5fdf-ba74-8e94918f5bb3` |

All three payloads are byte-identical after the change and all three identities
are unmoved, pinned as literals. A legacy component payload still carries
exactly `{handling, facts, authored_prose}` and gains no new keys.

### Alternate spellings

Four pairs proven to canonicalize to one payload: absent versus explicit-`null`
`applies_when`; absent versus `[]` `options`; options supplied in reversed
order; option facts supplied in reversed order. A negative control proves the
dedup did not flatten real content — a qualifier being present or absent still
moves the payload. A round-trip property
(`payload(parse(payload(p))) == payload(p)`) catches emitter/parser divergence
in one assertion across all three families.

## Finding 2 — `MovementCostFact`'s legal value matrix

**Thread:** `representation.py:2263` (P1).

**Root cause.** `_check_movement_cost()` validated `feet` against `amount` but
never `kind` against `amount`, so `PER_FOOT_SURCHARGE` + `HALF_SPEED` passed
with no findings — a declared per-foot *rate* stated in the lump form, naming no
computable cost, publishable as mechanical canon.

**One rule, not two, and the arithmetic was checked before choosing.** Both
prohibitions the task names — `PER_FOOT_SURCHARGE` requires `FEET`, and
`HALF_SPEED` requires `EXPENDITURE` — forbid the *same single cell* with both
vocabularies at two members. Stating them separately would report one malformed
fact as two defects, contradicting the one-defect-one-finding discipline round 4
established. `_MOVEMENT_COST_MATRIX` is therefore the allowed set, which also
stays correct if either vocabulary grows: a new pairing is refused until
deliberately admitted.

**Fixed-feet expenditures preserved.** `(EXPENDITURE, FEET, n>0)` remains valid;
nothing in the repository disproves it. Every committed instance was checked
first — the exemplars and the closure proof use `(PER_FOOT_SURCHARGE, FEET, 1)`
and `(EXPENDITURE, HALF_SPEED)`, neither of which is the forbidden cell.

### Sibling audit — the other five schema-2 families

| Family | Discriminator/payload pair | Disposition |
|---|---|---|
| `sensory_capability` | `can_perceive` vs `range_feet` | **already safe** — a removed capability carrying a range is already refused |
| `condition_level` | `all_levels` vs `amount`; `cumulative` vs `direction` | **already safe** — both cross-checks present |
| `movement_permission` | none — a single enum | **already safe** by shape |
| `quantity_multiplier` | none — `factor` is not conditioned on `quantity` | **already safe** by shape |
| `transformation` | none — the bool is independent of `becomes` | **already safe** by shape |

**Boundary, reported not fixed:** the advisor flagged a possible `bool`-as-`int`
gap in `_optional_int_field`. It does not exist — `_is_int` already excludes
`bool` — so it is reported as already safe rather than patched. Had it existed
it would have been a primitive-type gap, not the discriminator-mismatch family
this finding names.

## Regression evidence

`tests/services/rules_authority/test_review_round_5_component_patch_schema2.py`
(35) and `tests/ingestion/mechanical/test_review_round_5_movement_cost_matrix.py`
(18). Both were verified to **fail against their reinstated defects** before
being kept: disabling the matrix check fails 5 movement tests; disabling the
payload omission fails 7 component tests. The matrix test carries an
exhaustiveness guard that fails if either vocabulary grows without the table.

## Note

`git stash pop` reported success while leaving `validation.py` unrestored, which
was caught by the file's absence from `git status` rather than by the command's
exit status. Restored from the stash entry explicitly and re-verified before
committing.

---

# Round 7 — two P1 findings

Reviewed head `8091ec5d192a9411500d88f37fa2dccf73e81ab9`, verified unmoved
before starting. Both threads left **unresolved**; ten threads now stand open.
Scope held: schema-2 hash unchanged, OPTION decision not reopened, no ADR or
Issue amendment, no acceptance/publication/activation, `known_unknowns.md`
unchanged, override precedence untouched, deferred top-level draft closure not
expanded into, and no legacy removal or 2b / 15c / #129 work.

## Finding 1 — final effective option invariants

**Thread:** `application.py:965` (P1). Defect class: effective-state /
schema-invariant gap. The sibling gate had fired.

**Root cause.** Every existing check is *per-scope*. An `APPEND` or `REPLACE`
inside one option sees only that option's facts; a fact-scoped `DISABLE` is not
resolved into removal until `_finalize_component()`. None of them can observe
that two arms have become indistinguishable, or that an arm has been emptied —
those are component-wide properties of the **final** state. So options `{A}` and
`{A, B}` become two identical arms once `B` is appended to the first, and
`option_set_violations()` rejects exactly that shape at build time while nothing
asked it after override application.

**Where the check runs, and why there.** `_verify_final_option_sets` runs once,
after `surviving` is assembled — after the whole ordered set has been applied
*and* suppression resolved. That is what makes it final-state rather than
intermediate-state validation: a shape one entry creates and a later entry
legitimately repairs is never rejected, which is proven by a positive control
whose intermediate state is invalid and whose final state is valid.

**The rule is reused, not restated.** The effective view is projected back into
the representation's own types — `EffectiveFact.fact`, and `ComponentOption`
rebuilt from `EffectiveOption` — and handed to
`representation.option_set_violations`, the same function the corpus is built
under and the same one the patch parser calls since round 6. The projection
deliberately discards provenance: the contract is about what the facts *say*,
not which override supplied them. Provenance on the published view is untouched,
and asserted so.

**Attribution.** A final-state violation has no single culprit; an earlier entry
may create the shape a later one completes. `_blame_for` names the last applied
override that targeted that record and component — the one whose application
produced the invalid state — and the detail string says that is the rule, so a
reader is not misled into thinking it is the only cause.

### Sibling dispositions

| Seam | Disposition |
|---|---|
| option-scoped `APPEND` / `REPLACE` / `DISABLE` | **patched** — all three covered by one final-state check |
| facts removed only in `_finalize_component()` | **patched** — the check runs after finalization, which is the whole point |
| complete component addition / replacement | **already safe** — `_build_component_body` validates the option set at parse time (round 6), *and* the final check covers whatever they install |
| `REPLACE_RECORD` components | **already safe** — same parse-time path, same final check |
| record- and component-level `DISABLE` | **already safe, asserted** — a suppressed component publishes nothing, so it states no invalid choice; both proven not to raise spuriously |
| direct-fact operations on a component with no options | **already safe, asserted** — the check early-returns on `not component.options` |
| base projection with no overrides | **already safe, asserted** — the check must not reject authority the corpus already accepted |
| GameMaster and typed views | **already safe** — both build from the validated `EffectiveAuthority`; an invalid set now fails before either is constructed |
| fact provenance | **already safe, asserted** — validation reads the view, never rewrites it |

## Finding 2 — schema-1 identity across migration 0028

**Thread:** `projection.py:144` (P1). **Owner Decision 2026-08-20, Option A.**

**Root cause.** Schema 2 added `applies_when` and `options` to the canonical
component payload. A schema-1 projection has neither in its stored rows, so
reconstruction supplies the new fields' defaults — and the serializer emitted
them as `null` and `[]`. Those keys were absent from the original
identity-bearing payload, so `identify_projection(reconstruct_candidate(...))`
derived a different UUID and payload hash, and `verify_persisted_state` rejected
otherwise unchanged historical state.

**The decision, and its exact bounds.** A schema-1 projection persisted under
0027 must reconstruct after the upgrade with its original projection UUID,
payload hash, derived IDs, and recorded persisted-state digest. **Narrow to the
`0027 -> 0028` boundary.** It does not revoke #137's clean-baseline policy, does
not establish general legacy compatibility, and does not make a schema-1
projection activatable.

**Feasibility was checked before building.** The question that decided the whole
design was whether historical verification routes through
`validate_schema_binding`, which refuses any candidate not declaring the current
schema. It does not: `verify_persisted_state` calls `reconstruct_candidate` and
`identify_projection`, both of which are free of that gate, which lives only in
`validate_candidate` and `gate.py`. So no gate had to be weakened — and a test
asserts a schema-1 candidate is *still* refused as current authority, which is
what keeps Option A narrow.

**Implementation.** `representation_payload(draft, *, schema_version=...)`
defaults to the current schema, so every existing caller is byte-identical
without passing anything, and `projection_payload` passes
`candidate.schema_version` — the same reasoning the schema block itself already
follows: substituting current code there would re-identify history.
`_component_schema_2_payload` holds the omission and the fail-closed check
**together on purpose**: the branch that decides to drop a field is the branch
that proves the field is empty, so the two cannot drift into silently discarding
meaning. A schema-1 declaration carrying a real qualifier or option set raises
`LegacySchemaPayloadError` rather than being quietly serialized without it.

**Literals captured from real pre-change code.** A detached worktree at
`f6d2813~1` produced every schema-1 value; computing both sides with post-change
code would make the claim unfalsifiable.

| | |
|---|---|
| schema-1 version / hash | `5d-representation-schema-1` / `44bf8519…` |
| projection UUID | `5925934a-3692-551d-babe-2df5a6fa6752` |
| payload hash | `0df49dee…` |
| record / component / fact id | `96de01e9…` / `3377d6db…` / `919810ef…` |

**One correction to my own first reading.** An initial comparison reported the
fact ids as changed. They had not: the derived id value is identical, and what
gained an option slot is the *in-memory dict key* of `IdentifiedProjection.
fact_ids` — a lookup shape, not an identity. The test asserts the id values and
says why.

## Regression evidence

`tests/services/rules_authority/test_review_round_6_final_option_invariants.py`
(12) and `tests/ingestion/mechanical/test_review_round_6_schema1_identity.py`
(15). Both verified to **fail against their reinstated defects** — disabling the
two guards fails 15 of the 27. The schema-1 suite persists into a database built
by the real migration chain through `head` (past 0028), reconstructs, and checks
the recorded digest and `verify_persisted_state`, so it exercises the actual
post-upgrade state rather than a serializer in isolation.
