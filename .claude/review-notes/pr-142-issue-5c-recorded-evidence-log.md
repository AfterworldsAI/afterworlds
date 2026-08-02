# PR #142 Remediation Log — CRD Issue 5c recorded-evidence schema

Archive of detailed investigation and negative-control evidence for the stacked
5c recorded-evidence hardening. Kept out of the PR body so that body stays a
one-screen statement of what changed and why it is separately reviewable.

**Why this PR exists.** PR #141 round 4 produced a fourth consecutive finding in
the same 5c recorded-evidence verification seam. Its renewed stop condition
required escalation rather than a fifth local patch, so the hardening is
delivered here, reviewed on its own, and merged into
`feature/issue-5d-publication-gate`. It is based on that branch and not on
`main` because `verify_published_release` and the round-3 report helpers are
introduced by #141 and do not exist upstream yet.

---

## The finding, and the family behind it

Codex (PR #141, thread on `report.py:158`) is correct. `VERSION_CANARIES`
defines six required checks; round 3's `verdict_violations` iterated whatever
`version_canaries` happened to contain and required each present entry to be
`True`. It never required the map to *be* the canonical population. Once
`report_payload` and `evidence_report_hash` are edited together, `{}`,
`{"invented": true}`, or a partial map all satisfy recorded verdict validation,
and `verify_published_release` accepts evidence recording none of the required
version checks. `{}` is the sharpest case: `all(...)` over nothing is vacuously
true.

**Defect family:** *the recorded evidence validator checks required values but
does not prove the exact population of every closed schema inventory.*
`version_canaries` is one instance, and the fix is not a canary check.

## Inventory audit — every map classified explicitly

Audited before editing: the top-level report key set, `version_canaries`,
`findings`, `accounting`, every other nested map, `REQUIRED_REPORT_KEYS`,
`EVIDENCE_REPORT_SCHEMA_VERSION`, `VERSION_CANARIES`, `build_report`,
`verdict_violations`, `recorded_success_violations`, `run_gate`,
`verify_published_release`, fresh finalization, and verified reuse.

| Map | Classification | Population fixed by |
| --- | --- | --- |
| top-level report keys | **closed** | `REQUIRED_REPORT_KEYS` |
| `version_canaries` | **closed, verdict-bearing** | `VERSION_CANARIES` (derived) |
| `findings` | **closed, verdict-bearing** | `_ZERO_FINDINGS` |
| `accounting` | **closed, verdict-bearing** | `_ACCOUNTING_KEYS` |
| `reproduction_target` | **closed, structural** | `build_report` literal |
| `reconciliation_policy_reference` | **closed, structural** | `build_report` literal |
| `source_ledger_leaf_totals` | **open** | leaf types occurring in the corpus |
| `represented_totals` | **open** | leaf types occurring in the corpus |
| `excluded_totals_by_reason` | **open** | exclusion reasons actually applied |
| `transform_identity` | **open** | the recorded transform config's own identity payload |
| `rules_corpus_vector_identity` | **open** | the vector-identity builder |

The open maps are `Counter` results and config passthroughs: a release with no
table cells legitimately has no `table_cell` total, so demanding an exact
population would be demanding a particular corpus. That distinction is now
declared in code — `OPEN_REPORT_MAPS` — rather than left implicit, so nobody
later "hardens" it into a false failure.

## The correction

One canonical 5c-owned validator, as before; no second canary check anywhere, no
5d-side check, no parallel validator in `corpus.persistence`, no schema
framework.

- `CANONICAL_CANARY_NAMES = frozenset(c.name for c in VERSION_CANARIES)` —
  **derived**, so adding or retiring a canary moves the required population with
  no second list to remember.
- `_CLOSED_VERDICT_MAPS` and `_CLOSED_STRUCTURAL_MAPS` declare the closed
  inventories; `OPEN_REPORT_MAPS` declares the open ones.
- `_closed_map_violations` reports missing and unexpected entries separately —
  an omission and a foreign key are different findings.
- `verdict_violations` now checks **population before values** for the
  verdict-bearing maps. That runs on both sides of the boundary, which closes
  the same omission in `build_report`: `all(c.passed for c in ())` was vacuously
  true, so a report built from a partial canary run would have recorded `"pass"`.
  It cannot now.
- `recorded_success_violations` additionally requires the top-level key set to
  match **exactly** — previously only missing keys were reported, so an
  edited-and-rehashed payload could carry an unknown field under the same schema
  version — and closes the two structural maps.

**No schema-version bump.** The canonical payload shape is unchanged; this
enforces semantics every honestly built report already satisfies. Verified: the
real full-SRD report and the bounded fixture report both pass unchanged, and
`EVIDENCE_REPORT_SCHEMA_VERSION` is bound into the transform identity, so a bump
would mint a new 5c release identity for no shape change.

**Test-fixture consequence.** The bounded mechanical fixture built its report
with `canaries=()`. That is now refused, correctly, so it supplies the complete
canonical population via `BOUND_CANARIES`, derived from `VERSION_CANARIES` —
standing in for a real canary run exactly as the rest of that synthetic release
stands in for a real corpus. The bounded oracle needed no regeneration: the
report is not a bundle member and the six binding values are untouched.

## Negative controls

**Canary population** — `tests/ingestion/corpus/test_recorded_evidence.py`:
`{}`, invented-only, missing one canonical name, canonical plus one invented,
a canonical canary `False`, a canonical canary non-boolean; and the positive
control, the exact six all `True`, passing. Plus
`test_the_canonical_canary_set_is_derived_not_restated`, which holds the
constant to `VERSION_CANARIES` so a hand-written duplicate cannot creep back.

**Sibling inventories** — `findings` partial and with an extra key; `accounting`
with an extra key; `reproduction_target` empty and with an extra key;
`reconciliation_policy_reference` with wrong keys; an unknown top-level key.
And the counter-control: each of the five open maps accepts an arbitrary
content-derived key.

**Writing side** —
`test_build_report_refuses_to_claim_success_over_an_incomplete_canary_run`.

**End-to-end** — the mechanical bound-release matrix gained six cases that
rewrite the release's recorded report **and rehash it**, so the payload still
hashes to its recorded hash and all five proof identities are untouched: no
canaries, invented-only canary, one canonical canary omitted, an invented canary
added, an incomplete `findings` population, and an unknown top-level key. Each
returns `STALE` with exactly `{BOUND_RELEASE}` from
`publish_from_committed_oracle` — publication refused, not merely a validator
returning a string.

## Verification

`black` clean · `ruff check` clean · `mypy --strict` clean (210 files) ·
5c corpus + mechanical suites **764 passed** (includes the real-SRD production
control and the full 5c report/gate/persistence/finalization/reuse suites) ·
recorded-evidence module **49 passed** · mechanical publication **55 passed** ·
full default suite **3141 passed, 10 skipped** (93.42%).

No Chroma dependency, no Owner Decision, no ADR or Issue amendment, and nothing
outside the recorded-evidence schema was touched.

## Further stop condition

If review of this PR finds another omitted closed inventory in the same report
schema after this audit, the hand-maintained validation is replaced by an
explicit typed canonical report schema whose construction, hashing, persistence,
and recorded verification all use one object — not another field-by-field patch.

During this audit no part of `report.py` was found reconstructing the canonical
schema independently: `build_report` assembles the payload, and the declared
constants above are the single source for every population check. That is why a
typed schema object is not yet justified.

---

## Round 2 — the stop condition fired: hand-maintained validation replaced

**Both P1s are valid.**

- `transform_identity` and `rules_corpus_vector_identity` were classified as
  open. They are not: `extraction_config()`, `transform_identity()`, and
  `rules_corpus_vector_identity()` all return fixed production schemas. An
  edited-and-rehashed stored report could replace either identity with `{}` or
  arbitrary keys and still be accepted, so canonical evidence was removable.
- The remaining open maps were classified by key-population variability and then
  given **no runtime enforcement at all**: `OPEN_REPORT_MAPS` was consumed only
  by tests. `transform_identity="deleted"`, `rules_corpus_vector_identity=None`,
  and `source_ledger_leaf_totals=[]` all passed. "Open" had come to mean
  unvalidated rather than variably populated.

Together these invalidate the claim that round 1's hand-maintained sibling audit
closed the report schema. The PR's explicit stop condition therefore applies: an
executable typed canonical schema, not another inventory patch.

Four rounds each shut one hole and left the next, and the reason is structural —
`build_report` held the real shape in a dict literal while the validator held a
second, partial description of it. Two definitions of one document is the
defect; the individual omissions were symptoms.

### Why more `_CLOSED_STRUCTURAL_MAPS` entries were rejected

The obvious patch was two more rows in the closed-map table plus a shape loop
over `OPEN_REPORT_MAPS`. Rejected for three reasons, and the PR's stop condition
already required the alternative:

1. **It repeats the failure mode.** Rounds 1–4 each added an inventory entry and
   each left the next omission. The table can only ever describe the fields
   somebody remembered; the builder's dict literal is what actually defines the
   document. A fifth entry would have closed `transform_identity` and left its
   *nested* extractor, manifest, and invocation structures open — which is
   precisely what Codex would have found next.
2. **It cannot express nesting.** `_closed_map_violations` compares one key set.
   Closing `transform_identity` properly needs four levels of key sets and value
   types; expressing that as constants is a schema language, written badly.
3. **It leaves two definitions.** The defect named in the stop condition is not
   any individual omission — it is that `build_report` and the validator each
   describe the document separately. Adding entries preserves that.

A typed model removes the class of defect rather than its current instance: a
field that is not on the model does not exist, and one that is on it cannot be
omitted, retyped, or shadowed.

### Final integration audit

Verified by code search at `05c4e7e`, before requesting review:

| Path | Result |
| --- | --- |
| `build_report` | constructs `CorpusEvidenceReport.model_validate` directly — twice, the first only to read the verdict off the assembled document |
| `EvidenceReport.payload` | typed `CorpusEvidenceReport`; it cannot hold an unparsed dict |
| `report_hash` | `hash_obj(report.dump())`, nothing else |
| SQL write | `persist_release` → `artifacts.report.dump()`; `finalize` → `report.dump()` |
| SQL reconstruction | `_reconstruct_artifacts` → `parse_recorded_report(release_row.report_payload)` |
| `verify_published_release` | consumes the parsed report for identities, verdict, and recomputation |
| 5c verified reuse | reaches the same parsed report through `_reconstruct_artifacts` |
| fixtures | no 5c `EvidenceReport` is built from a raw dict |
| duplicate key inventories | none remain in 5c |
| alternate serialization | none; `model_dump` appears only in `dump()` and in the identity comparisons |

Two findings recorded rather than "fixed", because neither is a competing 5c
schema:

* `mechanical/publication.py::_REQUIRED_REPORT_KEYS` is the **5d** mechanical
  evidence report's key set — a different document with its own schema and its
  own hash. Out of scope here; if it deserves the same treatment that is a 5d
  change, not this one.
* `_report_schema_ok` survives and still reads the stored dict, because it is a
  *contextual* check the model cannot make: it compares the report's recorded
  version with the version recorded in `transform_config`. It duplicates no key
  list.

### What replaced it

`report_schema.py`: strict, frozen Pydantic v2 models with `extra="forbid"`.
`CorpusEvidenceReport` **is** the payload. `build_report` constructs it,
`report_hash` hashes its canonical dump, SQL persists that same dump,
reconstruction and `verify_published_release` parse stored bytes back through
it, and fixtures build it the same way. There is no second rendering.

Modelled explicitly: the top-level document; `TransformIdentity` with nested
`ExtractorConfig`, `SourceManifestEntry`, and `ComponentBInvocation`;
`RulesCorpusVectorIdentity`; `ReproductionTarget`; `PolicyReference`;
`Accounting`; `Findings`. `version_canaries` is a `dict[str, bool]` whose key
set must equal names derived from `VERSION_CANARIES` — no duplicated list.

`strict=True` is what makes `true` fail an integer field (`bool` is an `int`
subclass), `"0"` fail an integer, and `0.0` fail an integer. Arrays are declared
`list` with `strict=False` on those fields only: the identity builders return
tuples in memory and JSON round-trips them to lists, and both canonicalize to
the same bytes — so this admits the two encodings of one value while lax mode
still refuses a bare string.

**Variable-population maps are typed, not untyped.** The three totals maps are
`dict[str, Count]` with `Count = int >= 0`. The two leaf-total maps additionally
restrict keys to the `LeafType` universe, derived from the enum: any subset is
legitimate, an invented type name is not. `excluded_totals_by_reason` keeps free
string keys deliberately — the frozen policy is not available at parse time, and
reaching for it would create the second policy definition this refactor exists
to remove. Reason validity is proven contextually instead.

### Intrinsic versus contextual

The model owns shape, types, closed populations, value domains, and the
cross-field semantics of a successful verdict. `verify_published_release` now
owns agreement with the release and with reconstructed state:

- five proof identities against the release row (unchanged);
- `transform_identity.extractor` against recorded `transform_config.extraction_config`;
- the rest of the transform identity against recorded `transform_config.transform_identity`;
- `rules_corpus_vector_identity` against the recorded config;
- policy reference, leaf totals, represented totals, excluded totals, declared
  projection count, accounting, and findings all **recomputed** from the
  reconstructed ledger, reconciliation, and policy.

Not recomputed, and stated as such: concordance and canary results would require
reopening the authoritative PDF, and the vector half of the persisted-corpus
digest would require Chroma (Owner Decision 2026-08-01 unchanged). Those are
verified through their closed successful recorded form.

### `5c-evidence-3` retained — parity proven, not asserted

Run at parent `cfade0d` and at head with identical inputs (`build_candidate`
over the committed PDF; `build_report` with a fixed placeholder digest; no
Chroma, no finalize), dumping payload plus every release identity to JSON:

```
python parity.py parity_parent.json <PDF>   # at cfade0d
python parity.py parity_head.json <PDF>     # at 05c4e7e
diff parity_parent.json parity_head.json
→ (no output; files identical)

report_hash             1b1c26ec4385d034bfb75c8e166ed95f78aa327a74d4b8e95ddb48284079f336
package_uuid            4458fa10-4a66-5e0e-9ecc-ea37530ad2b4
release_version         5.2.1-corpus.36b786d8-fa2
transform_config_hash   77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e
bundle_root_hash        03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685
```

That covers `report_hash`, `package_uuid`, `release_version`,
`transform_config_hash`, `bundle_root_hash`, and the complete payload. The typed
model accepts the honestly generated full-SRD report unmodified and its dump is
byte-identical to the pre-refactor payload, so the version constant stands and
no release is reminted. The three identity builders were **not** touched:
normalizing a tuple in a builder would have moved `transform_config_hash` and
reminted the package.

### Obsolete machinery removed, not kept beside it

`REQUIRED_REPORT_KEYS`, `_CLOSED_VERDICT_MAPS`, `_CLOSED_STRUCTURAL_MAPS`,
`OPEN_REPORT_MAPS`, `_closed_map_violations`, `_ZERO_COUNTERS`,
`_ZERO_FINDINGS`, `_ACCOUNTING_KEYS`, and the standalone `verdict_violations`
walker are gone. `CANONICAL_CANARY_NAMES` survives because it expresses domain
semantics and is consumed by the model. Two competing schema definitions were
the defect; leaving the old validator for defence in depth would have preserved
it.

### Consequences worth naming

- `EvidenceReport.payload` is the typed object; `EvidenceReport.dump()` is the
  one serialization. Every 5c consumer was moved onto it.
- Reconstruction raises `PersistedReportError` on an unparseable stored report,
  and `_finalize_core`'s reuse path converts that to an ordinary failed result —
  a parse error never propagates out of publication.
- The bounded mechanical fixture's `transform_config` carried only a policy, so
  its report had `transform_identity={"extractor": None}` and no vector
  identity. It now uses the real production builders. `transform_config_hash` is
  a fixture constant rather than a hash of that config, so the six binding
  values are untouched and `bounded_oracle.json` needed no regeneration; only
  `BOUND_EVIDENCE_REPORT_HASH` moved.

### Controls

`tests/ingestion/corpus/test_recorded_evidence.py` (89) replaces the
field-by-field inventory tests: malformed identity maps at every nesting level
(empty, scalar, null, array, extra key, wrong nested shape, incomplete manifest
entry, wrongly typed component-B invocation, string where an array is declared);
every variable map as null/string/array/scalar and with boolean, float, string,
null, negative, and object counts; invented leaf-type names rejected while every
declared subset is accepted; empty, invented, partial, extended, and
non-boolean canary populations; missing and extra top-level fields; obsolete
schema version; invalid status; and the verdict controls. Positive controls: the
honest report parses, its dump round-trips exactly, and the canary set is
derived rather than restated.

Mechanical bound-release controls drive the contextual path through real
publication: each tampered-and-rehashed stored payload returns `STALE` with
exactly `{BOUND_RELEASE}` rather than an uncaught validation exception.

### Escalation rule now standing

If review finds a report field still constructed, serialized, persisted, or
verified outside the canonical typed object, that competing path is reported as
an architectural defect in the typed-schema conversion — not patched locally.

### Verification

`black` clean · `ruff check` clean · `mypy --strict` clean (211 files) ·
typed-schema module **89 passed** · mechanical suites **521 passed** ·
5c corpus + production control + packaging **285 passed** · full default suite
**3181 passed, 10 skipped** (93.43%) · parent-versus-head parity **identical**,
re-run after the final `_finalize_core` edit and again at the committed head.

No test was skipped, weakened, or xfailed to accommodate the conversion. Two
existing tests changed because they hashed a deliberately-unparseable payload
through `EvidenceReport`: both now hash the stored dict with `hash_obj`, which
is what the verifier itself does, so they assert more precisely than before.

No CI runs on this stacked PR: `.github/workflows/ci.yml` triggers only on
`pull_request` targeting `main`. Left unchanged deliberately — widening it is a
repository-workflow decision and a separate infrastructure follow-up after
Issue 5d, not part of this defect. CI covers the merged result when #141 runs
against `main`.

---

## Round 3 — final escalation: the value object was incomplete

**All three P1s are valid, and the final escalation condition fired.** Round 2's
audit concluded that nothing met that rule. **That conclusion is superseded.**
The audit asked whether every path *reached* the typed object and answered yes;
it did not ask whether the object was a *value* — deeply immutable, canonically
serialized, and the only thing hashed. On that question the honest answer was
no, and the third finding names it exactly: after parsing the stored payload
into `CorpusEvidenceReport`, `verify_published_release` still hashed the
original ORM dictionary. A report was still being verified outside the canonical
serializer.

**One defect, not three.** `CorpusEvidenceReport` validated a value at entry but
did not yet *constitute* the single deeply immutable canonical value used for
construction, serialization, hashing, persistence, and verification. The three
symptoms are the same boundary being incomplete in three directions:

- a canonical semantic constant (`reproduction_target.python_target`) modelled
  as an unrestricted string, so an edited-and-rehashed report could record a
  false reproduction target and pass every check;
- `ConfigDict(frozen=True)` preventing attribute rebinding while nested `dict`
  and `list` values stayed mutable — `report.version_canaries.clear()` after
  parsing left `success_violations()` returning nothing and `dump()` emitting
  the mutated state without revalidation, reopening the exact schema hole the
  conversion closed;
- a second serialization route on the read side.

The reproduction-target and shallow-freeze findings are sibling evidence for the
third: all three are places where the model is a validator that ran once rather
than a value that cannot be wrong.

**The correction is a deeply immutable canonical report value**, not more
validators wrapped around mutable Pydantic containers. Revalidating before
hashing would have been the fifth iteration of "remember to check" — the class
of fix this PR exists to stop.

### What replaced it, in three directions

**Deep immutability.** Canonical arrays are `tuple` — source manifest, Component
B steps, metadata fields — so an element cannot be appended or replaced.
Content-derived maps and the canary map are validated and then wrapped in a
`MappingProxyType` over a **copy** of the validated dict: the report owns its
own value, so a caller mutating the dictionary it passed in cannot reach inside
the parsed report. The proxy has no `__setitem__`, `__delitem__`, or `clear`.
Nested models stay frozen; every collection they hold is now immutable too.
Deliberately not chosen: revalidating before hashing. That is "remember to
check" again, the class of fix this PR exists to end.

**A canonical constant, bound not defaulted.** `PYTHON_TARGET` moved into the
schema layer, and `ReproductionTarget` rejects anything else during parsing.
`"99.0"` now fails intrinsically rather than surviving to a contextual
comparison that did not exist.

**One serializer, one hash.** `verify_published_release` no longer hashes the
ORM dictionary. The raw payload is input to `parse_recorded_report` and nothing
else; the stored hash is then checked with `report_hash` over the parsed value —
the same call publication makes. `_report_schema_ok` was the last raw-dictionary
report verifier and now takes the parsed report, so its remaining job is purely
contextual: comparing the report's version with the one recorded in the stored
transform configuration.

### Integration audit, re-run

- no production `hash_obj` over a report payload remains (the one match is
  `mechanical/projection.py`, hashing a projection, unrelated);
- one `report_hash` implementation, over `EvidenceReport.dump()`;
- SQL writes, stored verification, and reuse reconstruction all use it;
- `_report_schema_ok` no longer reads raw report fields;
- no `dict[...]`/`list[...]` field annotations remain in the schema;
- no duplicate top-level or nested inventory has returned.

`mechanical/publication.py::_REQUIRED_REPORT_KEYS` remains the 5d mechanical
report's own key set and is out of scope here, as stated in round 2.

### Controls added

Thirteen mutation attempts — canary `clear`, insert, and delete; totals insert
of an invented key and of a negative count; totals delete and clear; metadata
fields assign and append; source manifest assign and append; Component B steps
append; attribute rebind — each asserting the operation raises **and** that the
canonical dump and hash are unchanged afterwards. Plus: parsing does not alias
the caller's dictionaries; the canonical collection types are `MappingProxyType`
and `tuple`; five non-canonical reproduction targets and an extra-keyed target
fail; and the read-side hash equals the write-side hash over the same dump.

Existing malformed-shape, identity-map, variable-map, canary-population,
contextual-tamper, and honest-report controls are retained unchanged.

### Identity parity, re-run after the conversion

```
diff parity_parent.json parity_head3.json
→ (no output; files identical)
```

Same payload, `report_hash`, `package_uuid`, `release_version`,
`transform_config_hash`, `bundle_root_hash`, and persisted-corpus digest as
`cfade0d`. Immutability and the bound constant changed how the document is
*held*, not what it *is*, so `5c-evidence-3` stands.

### One existing test rewritten, and why

`test_report_schema_ok_fails_closed_on_bad_schema` called `_report_schema_ok`
with raw dictionaries — its whole premise was the raw-dictionary report verifier
this round removes. It is now
`test_report_schema_ok_compares_the_parsed_report_with_the_transform_config`,
passing a parsed report and exercising the one question the model cannot answer:
agreement with the version recorded in the stored transform configuration. The
cases it dropped — obsolete, missing, and malformed report versions — did not
lose coverage; they moved to the parse boundary, where
`test_recorded_evidence`'s `obsolete-schema-version` control already proves
them. The docstring says so, so the migration is visible rather than a quiet
deletion.

### Verification (round 3)

`black` clean · `ruff check` clean · `mypy --strict` clean (211 files) ·
typed-schema module **112 passed** · mechanical suites **521 passed** ·
5c persistence/quarantine **55 passed** · full default suite **3204 passed,
10 skipped** (93.43%) · parity **identical**, re-run after the conversion.
