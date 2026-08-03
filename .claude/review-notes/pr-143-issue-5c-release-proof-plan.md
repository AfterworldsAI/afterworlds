# CRD Issue 5c — published-release proof boundary: construction plan

Replacement for PR #142, which was frozen and closed as superseded. #142 is
retained as a defect catalogue, a source of adversarial controls, and the record
of two rejected representations. Its implementation history is deliberately not
transplanted: this branch starts from `feature/issue-5d-publication-gate` at
`b35386c` and builds the boundary once.

This is a construction plan, not a chronology.

## Why a replacement rather than a fifth remediation round

Four rounds on #142 replaced the representation and then the closure, and the
same defect family escaped every replacement:

| Round | Representation / closure | Escape |
| --- | --- | --- |
| 1–2 | Hand-maintained key inventories beside a dict-literal builder | Two definitions of one document; each round shut one omission |
| 3 | Frozen Pydantic `BaseModel` | `vars(report)["version_canaries"] = {}` reached past the freeze |
| 4 | Frozen **slotted** Pydantic dataclass | `object.__setattr__(report, "version_canaries", {})` overwrites slot storage |
| 4 | Recorded-release closure at one seam | `finalize_release` reuse never calls it; the audit's unit was the release *row*, not the package/release *pair* |

Both representations were *conventionally* frozen — immutability enforced by a
setter that a lower-level setter bypasses. Both closures were a function one
caller happened to call. The corrections below are structural in the first case
and shared in the second.

## Boundary A — canonical report authority

**Representation: a tuple-based immutable value tree.** Every canonical type is
a `NamedTuple`; arrays are tuples; maps are `Pairs`, a `tuple` subclass holding
sorted `(key, value)` pairs.

Spike results (`object.__setattr__` on an existing field, on a novel field,
`setattr`, `vars`):

| Candidate | `object.__setattr__` | `vars()` | `__dict__` |
| --- | --- | --- | --- |
| Pydantic frozen `BaseModel` | writes | writes | present |
| Pydantic frozen + slotted dataclass (#142 head) | **writes** | raises | absent |
| `NamedTuple` | raises | raises | absent |
| `tuple` subclass | raises | raises | absent |

A `NamedTuple` stores its values in the tuple itself. There is no instance
dictionary and no slot descriptor, so there is nothing for the base setter to
write — immutability is a property of the storage rather than of a guard.

`Pairs` is chosen over `MappingProxyType` for the same reason. A proxy is a view
onto a real dict, which remains reachable through `gc.get_referents`; a pair
tuple has no backing dict at all. This is the difference between "no mutable
dictionary is *exposed*" and the required "no mutable dictionary is
*reachable*".

**One parser.** A single `TypeAdapter` over the value tree. Pydantic validates
ingress and never holds the value: strict per-scalar aliases (`true` is not an
integer, `"0"` is not an integer), `BeforeValidator` requiring a JSON *object*
at every node (pydantic's native `NamedTuple` handling would otherwise accept a
positional array), `AfterValidator` for closed populations, the canonical
`report_version`, and the canonical `python_target`. Extra, missing, and
wrongly-typed keys are refused by the adapter.

**One construction path.** `build_report` assembles a plain dict and hands it to
`canonical_report(...)`. A `NamedTuple` constructor runs no validators, so
direct construction of the canonical types is never a production path; a
build-time negative control asserts a non-canonical canary population, an
unsupported `report_version`, and a non-canonical `python_target` each fail at
*build* time, not only at parse time.

**One serializer.** `CorpusEvidenceReport.dump()` walks the tree and reads field
names off `NamedTuple._fields` and renders `Pairs` as objects, so it cannot drift from
the declaration. It is the only rendering: `report_hash`, the SQL column, stored-
hash verification, contextual comparison, and reuse reconstruction all read it.

**New hazard this representation introduces.** `json.dumps` raised `TypeError`
on a dataclass but *succeeds* on a `NamedTuple`, emitting a positional array —
so `canonical_bytes(report)` would silently mint a wrong-but-plausible hash. A
control asserts `report_hash` equals `sha256_hex(canonical_bytes(report.dump()))`
and that the raw object's canonical bytes differ from the payload's, so any
accidental direct serialization fails loudly.

## Boundary B — published-release authority

**One 5c-owned seam:** `load_published_release(session, pkg)`, returning the
proven package/release pair or the violations that refuse it. Its unit is the
**pair**, not either row — that is precisely what the #142 field audit got wrong.

Invariants stated in the seam:

- package row exists; is `published`; is enabled; has `published_at`
- release row exists; is `published`
- `package.version == release.release_version`
- identity, report, and reference columns present as a set
- `hash_obj(release.transform_config) == release.transform_config_hash`
- canonical report hashes to `evidence_report_hash`
- `corpus_report_reference == evidence_report_hash`
- report proof identities equal their release columns
- report schema version agrees with the recorded transform configuration

Reconstruction keeps what it already owns and the seam does not duplicate:
ledger, policy, reconciliation, bundle, source, chunk membership, page coverage,
and every recomputable report total.

**Every caller of the seam:**

| Caller | Site | Why |
| --- | --- | --- |
| `verify_published_release` | `persistence.py` — downstream 5d entry, called by `mechanical/gate.py:run_gate` step 0 | Proves the pair before comparing 5d's six declared values against it |
| `_finalize_core` verified reuse | `persistence.py` reuse branch, replacing the `package_state_ok` inline check | A release refused downstream must not be returned as `published=True, reused=True` |
| `_finalize_core` fresh publication | `persistence.py`, after the status writes and before `session.commit()` | The same row-level invariants gate a *fresh* success; failing rolls back rather than committing a release the seam would later refuse |

Three call sites, one definition. `policy_hash` is deliberately not re-verified
in the seam: `_load_policy` already validates a closed cross-reference chain
across the policy, reconciliation, and release rows and fails closed, and a
second statement of it would reintroduce the two-definitions defect.

## Package / release field disposition

`rp_packages` (for `rules_package_id == pkg`):

| Field | Disposition |
| --- | --- |
| `rules_package_id` | Seam — the lookup key; absence is a violation |
| `version` | **Seam — must equal `release.release_version`** (the #142 omission) |
| `publication_status` | Seam — must be `published` |
| `is_enabled` | Seam — must be true |
| `published_at` | Seam — must be present |
| `name`, `system` | Not proof-bearing; fixed descriptive values, no identity binds them |
| `created_at`, `updated_at` | Wall-clock; excluded from every hashed artifact by construction |

`rp_corpus_releases` (for `package_uuid == pkg`):

| Field | Disposition |
| --- | --- |
| `package_uuid` | Seam — the lookup key |
| `release_version` | Seam — must equal `package.version`; also a 5d declared value |
| `publication_status` | Seam — must be `published` |
| `authoritative_source_hash` | Seam — must equal the report's identity; also a 5d declared value |
| `transform_config` | Seam — must be an object hashing to `transform_config_hash` |
| `transform_config_hash` | Seam — recomputed from `transform_config`, and equal to the report's |
| `ledger_hash` | Reconstruction — recomputed from persisted leaves |
| `policy_hash` | Reconstruction — `_load_policy` proves the closed chain and fails closed |
| `reconciliation_hash` | Reconstruction — recomputed from persisted reconciliation |
| `bundle_root_hash` | Both — seam compares the report's; reconstruction recomputes the bundle |
| `persisted_corpus_digest` | Seam (recorded equality only) — its cross-store half is provable solely by `finalize_release`, which holds a Chroma client; unchanged by the 2026-08-01 Owner Decision |
| `report_payload` | Seam — parsed by the one parser; unparseable is a refusal, not an exception |
| `evidence_report_hash` | Seam — the canonical report must hash to it |
| `corpus_report_reference` | Seam — must equal `evidence_report_hash` |
| `created_at` | Wall-clock; excluded from hashed artifacts |

## Identity parity

Compared against clean base `b35386c` — the untyped dict-based report — from an
explicit worktree at that commit, on identical deterministic inputs. Unchanged
canonical payload, `evidence_report_hash`, `transform_config_hash`,
`package_uuid`, `release_version`, `bundle_root_hash`, `persisted_corpus_digest`,
and every other release identity. `5c-evidence-3` is retained only if that
comparison is empty.

The bounded mechanical fixture declared `transform_config_hash = "b" * 64`,
which is not the hash of its own configuration — it was a synthetic constant
chosen before any check recomputed it, so nothing had ever required it to be
honestly derived. It is derived here and `bounded_oracle.json` regenerated,
because a fixture that cannot pass the proof it is used to test is not evidence.

## What was built

Both boundaries as planned, with three findings worth recording because the
construction changed them.

**The serializer could not come from Pydantic.** `TypeAdapter.dump_python` over
a `NamedTuple` emits a *positional array*, not an object, so the canonical
payload had to be rendered by a small recursive walk. It reads field names off
`NamedTuple._fields`, so there is still one declaration — but the same fact
creates a hazard the dataclass did not have: `json.dumps` *succeeds* on a
`NamedTuple`. `canonical_bytes(report)` therefore mints a wrong-but-plausible
hash instead of raising, and a control asserts the raw object's bytes differ
from the payload's.

**Positional input had to be refused explicitly.** Pydantic's native
`NamedTuple` handling accepts a sequence, so a stored report could have arrived
as a JSON array and parsed. `BeforeValidator(_object_only)` is applied at the
root and at every nested node.

**Reuse proves the pair before reconstructing, not after.** The plan said reuse
must call the seam; putting the call after `_reconstruct_artifacts` — where the
old inline package check lived — meant artifacts were assembled around rows
nothing had accepted yet, and `_reconstruct_artifacts` asserted on the
post-persistence columns rather than refusing. The seam now runs first, and
those `assert`s are a `PersistedReportError` (an `assert` disappears under `-O`).

Two invariants proved to belong intrinsically to the document rather than
contextually, so they moved onto their own fields: the canonical
`report_version` and the canonical `python_target`. `_report_schema_ok` keeps
only the genuinely contextual half — agreement with the persisted transform
configuration, which the document cannot know about itself.

**Fresh publication needed fault injection, not a positive assertion.** Both
other callers can be driven by editing rows after publication; the fresh path
has to be made to write a bad pair while it runs, or its refusal branch never
executes. A monkeypatched `_persist_package_and_source` writes a package version
the release does not carry, and the control asserts the refusal *and* that no
published package or release row survives — the rollback, not just the verdict.

Two `PersistedReportError` raises inside `_reconstruct_artifacts` became
unreachable once reuse proved the pair first. They are kept as backstops and
marked `# pragma: no cover`, because assembling artifacts around a half-written
or unparseable release would produce something that looks whole. The
`PolicyReconstructionError` half of the surrounding `except` stays live: the
seam does not call `_load_policy`, so a deleted policy row still lands there.

## Verification

Parity against clean base `b35386c`, identical deterministic inputs, generated
before any edit and again at the final head: `diff` produced **no output**
across the complete payload, `report_hash`, `package_uuid`, `release_version`,
`transform_config_hash`, `bundle_root_hash`, and the persisted-corpus digest.
`5c-evidence-3` therefore stands.

Black, Ruff, and `mypy --strict` (211 source files) clean. 75 tests in the
typed-schema module, 24 in the new published-release seam module; 875 across
ingestion. Coverage on the changed modules: `report_schema.py` 100%,
`report.py` 100%, `persistence.py` 99% — its three remaining lines are
pre-existing, `delete_release` among them.

## Scope

Unchanged: 5c digest identity semantics, the payload's canonical shape, the
2026-08-01 Owner Decision on the persisted-corpus digest (Chroma is not
reopened), and CI workflow configuration. No Owner Decision, ADR amendment,
Issue amendment, or schema-version decision is required — every invariant above
is one `run_gate` already defines; the implementation is being brought into
agreement with it.

---

# Round 1 — boundary reassessment

Two P1 findings, both valid, both firing this PR's standing condition. They are
not patched where they were reported: the accepted construction plan above is
revised first, because each names a boundary that was drawn in the wrong place
rather than a check that was left out.

**The tuple tree held.** `CorpusEvidenceReport` and every nested value remain
structurally immutable; no finding reaches them. That is worth stating plainly,
because it means the representation decision was right and the mistake was in
what the boundary was drawn *around*.

**Boundary A was drawn around the payload; the authority was the wrapper.**
`build_report` returns `EvidenceReport`, a frozen dataclass holding the
canonical value, and everything that matters consumes *that* —
`report_hash`, SQL persistence, the gate. So
`object.__setattr__(report, "payload", forged)` replaces the whole document
after construction. Making the payload unforgeable while the object carrying it
to the hash function stays writable protects the wrong thing. The correction is
to delete the wrapper, not to freeze a second one.

The wrapper also carried `persisted`, a caller-supplied boolean outside the
hashed payload that gate condition 18 trusted as proof the report postdates
persistence. `build_report`'s `persisted` parameter is the same trust one layer
down: it is the sole input deciding whether the hashed
`prepublication_validation_status` may be `"pass"`, and the single production
call site passes a hardcoded `True` under a comment arguing that this particular
caller is trustworthy. Both go.

**Boundary B was drawn around recorded-row closure; published authority is
more.** `load_published_release` proves the package/release rows are internally
coherent and then stops. It never asks whether the report *describes the
persisted corpus*. Rewrite `declared_projection_count`, the totals, and the
accounting to different but internally consistent values, rehash, and update the
reference: the pair is accepted, and neither downstream reconstruction nor the
reuse gate compares those fields with the reconstructed ledger and
reconciliation. The name overclaims what the function proves, which is how the
gap survived a field audit.

**Authority disposition.** Neither finding requires an Owner Decision, ADR
amendment, Issue amendment, or schema-version change. Both are invariants
already implied by `run_gate` and by Component K's ordering; the implementation
is being brought into agreement with them. Removing a non-payload wrapper and a
non-payload constructor parameter must not move a single byte of the canonical
document — if parity is non-empty afterwards, that is a behavioural change to
report and not a fixture to adjust.

## Revised Boundary A — the canonical report is the authority

`build_report(...) -> CorpusEvidenceReport` and
`report_hash(report: CorpusEvidenceReport)`. No wrapper type remains in
production; `ReleaseArtifacts.report` carries the canonical value. Construction,
hashing, persistence, parsing, stored-hash verification, contextual comparison,
gate evaluation, and reuse reconstruction all consume it directly.

The name `EvidenceReport` is kept in `report.py` as a runtime alias of the
canonical class — `EvidenceReport is CorpusEvidenceReport` — so that
`pipeline.py`, whose bytes are bound into the transform identity, stays
byte-identical. It is vocabulary, not a type: no `payload`, no `persisted`, no
second serializer, nothing to construct or unwrap.

No runtime type guard is added at the hash boundary. A guard is the shape the
last two rounds killed: the answer is that there is no wrapper type to pass, so
the control asserts the *absence* of the production type rather than the
rejection of imposters.

**Where "postdates persistence" is now structurally enforced,** replacing the
deleted `report.persisted` check:

1. `persisted_corpus_digest` is a required argument to `build_report` and cannot
   be computed before persistence — it digests reconstructed SQL rows and the
   read-back vector state. A pre-persistence caller has nothing to pass.
2. `ReleaseArtifacts` — the only thing `run_gate` accepts — has exactly two
   construction sites, both in `persistence.py`: the fresh path after the digest
   is computed, and reconstruction from an already-proven published release.
   None in tests.
3. `PublicationEvidence.sql_persist_ok` is derived from comparing reconstructed
   rows against the candidate, never defaulted.

Gate condition 18 keeps its other two checks: the report carries a
persisted-corpus digest, and its recorded status is `"pass"`.

## Revised Boundary B — row closure is a prerequisite, not authority

Two named concepts instead of one overclaiming name:

- **`load_recorded_release_pair`** — recorded-row closure only. Existence,
  statuses, enablement, `published_at`, version equality, required
  post-persistence fields, transform-config hash, report parse and hash, report
  reference, proof-column equality, schema version, self-contained verdict.
  Necessary, explicitly not sufficient.
- **`load_verified_published_release`** — the one published-authority seam:
  recorded closure, then policy/ledger/reconciliation/members/source
  reconstruction, reconstruction identity checks, report-versus-reconstructed-
  state verification, and membership verification. Returns the proven state
  bundle, so callers do not reconstruct a second independent copy.

**One report-context verifier.** `report_state_violations(report, *, release,
transform_config, ledger, reconciliation, policy, members)` is the single
definition of "the report agrees with the persisted corpus". It takes one
`report.dump()` and never serializes a nested fragment independently. The
summary fields are recomputed through the same derivation `build_report` uses
rather than a second implementation of how totals are counted.

Called from the seam (reuse, downstream) and from `run_gate` (fresh publication,
which has no seam call before the rows exist). Reuse runs both and may report a
violation twice; that redundancy is accepted deliberately rather than resolved
by giving one of them its own copy of the comparison.

**Recorded-only fields.** Concordance against the authoritative PDF, canary
execution, and the live vector half of the persisted-corpus digest are not
recomputable from SQL alone. They keep their existing treatment — required in
closed successful recorded form under the 2026-08-01 Owner Decision — while
fresh publication and reuse, which hold pages and vector state, continue to
rerun the real checks.

A drift guard makes the completeness claim executable rather than asserted: the
21 declared fields partition exactly into 10 recomputed from reconstructed
state, 5 compared against release columns, and 6 that are neither, with no
remainder. A field added to the document and not routed anywhere fails that
test rather than silently ceasing to be compared.

## Exact identity parity, and the intermediate implementation that lost it

The first implementation of this round edited `pipeline.py` for one reason: to
retype `ReleaseArtifacts.report` from the deleted wrapper to
`CorpusEvidenceReport`. `pipeline.py` is one of the eleven modules whose source
bytes are bound into the transform identity, so that annotation change reminted
`transform_source_hash`, `transform_config_hash`, `package_uuid`,
`release_version`, `bundle_root_hash`, and `report_hash`.

That remint was a whole-file-hash side effect, not a transform change.
`pipeline.py` is audited because `build_candidate` owns the candidate-affecting
steps a0–b; `ReleaseArtifacts.report` is post-persistence plumbing for steps
c–g. No candidate corpus, canonical bundle member, or report schema moved — the
canonical payload was byte-identical throughout, which was proven by restoring
`pipeline.py` alone and observing an empty diff.

**The architecture was adjusted rather than the identity accepted.**
`EvidenceReport` is retained in `report.py` as a runtime alias of
`CorpusEvidenceReport` — the same class object, not a wrapper, adapter, or
second report type. It has no `payload` member and no `persisted` member,
introduces no alternate serializer, and cannot be constructed as anything other
than the canonical report. `pipeline.py` is byte-identical to `b35386c` and was
not reformatted, re-annotated, or re-imported.

The intermediate reminting head was never pushed.

**Verified after the amendment:**

- `git diff --exit-code b35386c -- src/afterworlds/ingestion/corpus/pipeline.py`
  is clean, and a direct SHA-256 over newline-normalized bytes matches
  (`f0af4fdb…`, the same value the base manifest records);
- all **eleven** `TRANSFORM_SOURCE_MODULES` entries hash identically to
  `b35386c`, and `transform_source_hash` is `6332f201…` as before;
- full parity `diff` against `b35386c` is **empty** — canonical payload,
  `report_hash`, `transform_config_hash`, `package_uuid`, `release_version`,
  and `bundle_root_hash`;
- `bounded_oracle.json` is back to its pre-remint committed value, and the
  fixture derives the same hash.

Modules outside the manifest — `report.py`, `report_schema.py`, `persistence.py`,
`gate.py` — changed substantially and do not move transform identity, which is
the intended separation: verification and post-persistence code is not
candidate-affecting.

**`5c-evidence-3` is retained.** It versions the canonical shape, which is
unchanged, and every release identity is now exactly as it was.
