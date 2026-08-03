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
names off `NamedTuple._asdict()` and `Pairs`, so the serializer cannot drift from
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

## Scope

Unchanged: 5c digest identity semantics, the payload's canonical shape, the
2026-08-01 Owner Decision on the persisted-corpus digest (Chroma is not
reopened), and CI workflow configuration. No Owner Decision, ADR amendment,
Issue amendment, or schema-version decision is required — every invariant above
is one `run_gate` already defines; the implementation is being brought into
agreement with it.
