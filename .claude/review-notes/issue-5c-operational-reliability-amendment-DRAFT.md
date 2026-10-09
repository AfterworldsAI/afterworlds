# Issue 5c Operational Reliability Amendment — DRAFT for owner review

**Date:** 2026-08-03
**Status:** Draft. Not applied. No ADR, issue body, or code changed.
**Scope:** Governing authority for CRD Issue 5c and its downstream consumption by CRD Issue 5d.

---

## 1. The amendment

### 1.1 Purpose

CRD Issue 5c provides **operational reliability** for the SRD 5.2.1 source corpus. It does not
provide adversarial or forensic proof. This amendment states that distinction as governing
authority, supersedes the specific downstream re-proof obligation recorded on 2026-08-01, and
leaves every practical safeguard binding.

### 1.2 What Issue 5c guarantees

1. The identified authoritative source is extracted **completely and faithfully** into durable,
   machine-usable, citable source material.
2. Silent omissions, stale artifacts, wrong-source ingestion, and accidental corruption or
   mismatch are **detected**.
3. Published corpus releases are **immutable and stably identified**.
4. A materially changed source or meaningfully changed corpus receives a **new release identity**.
5. Supported source material remains **traceable to its source passage**.
6. Publication **fails visibly** and leaves no usable partial release when completeness or
   consistency checks fail.
7. An approved release can be **rebuilt, diagnosed, or corrected** without depending on Chroma or
   an opaque legacy artifact.

### 1.3 What Issue 5c does not promise

1. Protection against a malicious actor coherently rewriting the database and all dependent
   hashes.
2. Cryptographic nonrepudiation or chain-of-custody proof.
3. A complete mathematical genealogy connecting every stored identity.
4. Re-proof of the entire historical publication process whenever CRD Issue 5d or another
   downstream consumer loads an approved release.
5. Certification that extracted prose has been correctly interpreted as typed mechanics — that
   remains CRD Issue 5d's responsibility.

### 1.4 Guarantees superseded

This amendment supersedes exactly one contract clause, recorded in three places by the Owner
Decision of 2026-08-01 (PR #141 review):

> "…and reconstruction and re-proof of all SQLite-authoritative corpus state that seam exposes."

- **GitHub Issue #137, Required Contract 1** — the sentence "Downstream 5d verification proves the
  authoritative published 5c release record, its recorded evidence payload and proof identities,
  exact equality of all six binding values, and *the reconstructable SQLite-authoritative corpus
  state exposed by the 5c-owned verification seam*."
- **GitHub Issue #137, Required Contract 5** — "…and *reconstruction and re-proof of all
  SQLite-authoritative corpus state that seam exposes*."
- **ADR-005d, Decision 8** — the third bullet of the 2026-08-01 owner-decision block,
  "*reconstruct and re-prove all SQLite-authoritative corpus state that seam exposes*."

Superseded because it makes every downstream load a re-execution of 5c's historical publication
proof. That is guarantee 4 of §1.3, and it is the source of the escalating verification surface
seen across PRs #141, #142, and #143.

**Nothing else in the 2026-08-01 Owner Decision is superseded.** In particular its Chroma
provisions are re-affirmed verbatim in §1.6.

### 1.5 Safeguards that remain binding

Unchanged and still required:

- Completion Contract A components **A–G** and **J–L** in their entirety: source identity and the
  five immutable release identities; reproducible transform identity and the frozen reconciliation
  policy; the frozen pre-transform source ledger; the reconciliation member with identity-level
  leaf accounting, zero unresolved leaves, and gap-free declared projection; source-to-corpus
  concordance; authoritative/derivative separation; per-record provenance and locators; version
  canaries; the acyclic canonical bundle with byte-for-byte reproducibility; and the pre-release
  clean baseline.
- Completion Contract A component **I** (publication gate) at **fresh publication and verified
  reuse**. Publication still fails visibly and atomically, and leaves no usable partial release.
- Completion Contract A component **H** (evidence report) as the **operational diagnostic record**
  of a publication.
- ADR-005c Decisions 1–7, and its Central Invariant, unchanged.
- ADR-005c's pre-release clean-baseline correction (2026-07-27), unchanged.

The distinction this amendment draws is **lifecycle position, not mechanism**. A check that
detects accidental corruption *at the moment state is written* is operational and is retained. The
same check re-executed by a downstream consumer *on every load of an already-approved release* is
re-proof of history and is retired.

### 1.6 Chroma decision preserved (2026-08-01)

Re-affirmed without change:

- The persisted-corpus digest remains **immutable historical identity** for the published corpus.
- **Fresh 5c publication and 5c verified reuse check the live Chroma projection**, and must
  continue to write, read back, and verify the required vector projection before declaring a
  release published or reusable.
- **Downstream 5d verification does not reopen or recompute Chroma.**
- Chroma remains **rebuildable, non-authoritative infrastructure owned by CRD Issue 18**
  (ADR-018 D4/D10). Loss or corruption of the live collection after successful 5c publication is
  an Issue 18 operational defect, not stale 5c source authority.

### 1.7 Authority status

No change to ADR-005c's Central Invariant is required: it states what *publication* proves
("Rules Package publication proves source-corpus integrity"), and never claimed that a downstream
consumer must re-prove it. This amendment annotates that invariant's scope rather than amending its
text.

---

## 2. Downstream 5d trust boundary

### 2.1 What 5d must verify

For a release it intends to bind:

| # | Obligation |
|---|---|
| 1 | The requested release **exists** and is **published**. |
| 2 | Its **stable release identity** is correct. |
| 3 | It identifies the **expected source/corpus**. |
| 4 | The **stored corpus checksum matches** the approved release. |
| 5 | The release is **compatible with the 5d transformation**. |

### 2.2 What 5d must not do

5d does not reconstruct and re-prove 5c's complete historical evidence graph. Specifically, and by
name against the current implementation, the following fall **outside** the boundary when reached
from a downstream load:

- reconstruction identity checks (recomputing ledger, reconciliation, and bundle-root hashes from
  persisted rows);
- report-versus-reconstructed-state verification of the evidence report's contextual summaries;
- single-source and chunk-runtime membership verification;
- recomputation of the recorded transform configuration's own hash.

Each remains correct and required **inside 5c's own publication and verified-reuse lifecycle**.

### 2.3 Mapping the shipped seam onto the boundary

`load_verified_published_release` (PR #143, `5a6b6f7`) has five stages. Against §2.1:

| Stage | Boundary disposition |
|---|---|
| 1. Recorded package/release pair closure — existence, publication status, enablement, `published_at`, `package.version == release.release_version` | **Inside** — satisfies obligations 1 and 2 |
| 1 (cont). Report parses; report hash matches `evidence_report_hash`; `corpus_report_reference` agrees; proof identities equal their columns; schema version agrees | **Inside** — satisfies obligation 4 |
| Declared six-value binding comparison (in `verify_published_release`) | **Inside** — satisfies obligations 2 and 3 |
| 2. Policy/ledger/reconciliation/member/source reconstruction | **Outside** |
| 3. Reconstruction identity checks | **Outside** |
| 4. `report_state_violations` | **Outside** |
| 5. Single-source and chunk-runtime membership | **Outside** |

**Obligation 5 has no counterpart in the shipped implementation.** "Compatible with the 5d
transformation" is new contract surface. It is not satisfied today by anything named above, and it
requires definition — at minimum whether compatibility is expressed as an evidence-report schema
version, a corpus-shape predicate, or a declared capability. Flagged, not designed.

---

## 3. Obligation classification

Classified by **lifecycle position**, per §1.5. "Retire" classifies the *obligation*; the
disposition of any specific code is deferred to the bounded contract-to-code audit.

### 3.1 Retain for operational reliability

| Obligation | Source | Reliability guarantee served |
|---|---|---|
| Authoritative source identity (path, version, size, SHA-256) | CC-A **A** | Wrong-source ingestion detected |
| Five immutable top-level release identities | CC-A **A** | Immutable, stably identified releases |
| New identity on changed source or transform inputs; no mutation of a published release | CC-A **A** | Materially changed corpus gets a new identity |
| Frozen reconciliation policy committed before output | CC-A **B** | Faithful, reviewable extraction |
| Byte-for-byte reproducible transform from committed inputs | CC-A **B**, **K** | Rebuild, diagnose, correct |
| Frozen pre-transform source ledger, exhaustive over every page | CC-A **C** | Complete extraction; silent omission detected |
| Identity-level leaf accounting; zero unresolved leaves | CC-A **D** | Silent omission detected |
| Gap-free declared projection; orphan and duplicate detection | CC-A **D** | Complete and faithful representation |
| Source-to-corpus concordance | CC-A **E** | Stale artifacts and wrong-source content detected |
| Authoritative vs. derivative layer separation | CC-A **F** | Faithful source material |
| Per-record provenance and locators | CC-A **G** | Traceable to source passage |
| Version canaries | CC-A **J** | Wrong-source / obsolete-version detected |
| Publication gate at **fresh publication and verified reuse**; atomic failure, no partial release | CC-A **I** | Publication fails visibly |
| Acyclic canonical bundle; no artifact covered by a hash it contains | CC-A **K** | Rebuildable, diagnosable |
| Pre-release clean baseline | CC-A **L** | No opaque legacy artifact |
| Cross-store vector verification at fresh publication and verified reuse | Owner Decision 2026-08-01 | Detects a corpus that did not fully persist |
| Package/release **pair** consistency, including version equality | PR #143 | Accidental mismatch detected |
| Report-versus-state verification **at fresh publication** | PR #143 | Accidental corruption detected as it is written |
| Canonical report as a single immutable value with one parser and one serializer | PR #142/#143 | Prevents accidental in-process corruption; near-zero cost |

### 3.2 Simplify or make diagnostic

| Obligation | Source | Disposition |
|---|---|---|
| Corpus evidence report | CC-A **H** | Retain as the **operational diagnostic record** of a publication. Its role as a downstream-re-verified proof artifact ends. Its content is unchanged by this amendment. |
| Recorded package/release row closure at downstream load | PR #143 `load_recorded_release_pair` | Simplify to the §2.1 obligations. It is already the closest existing analogue of the thin boundary. |
| Recorded-report parse and hash check at downstream load | PR #141/#143 | Retain in simplified form as obligation 4 (stored checksum matches), not as an evidence-graph proof. |

### 3.3 Retire as forensic / tamper-proof machinery

| Obligation | Source | Why it retires |
|---|---|---|
| Downstream reconstruction and re-proof of all SQLite-authoritative corpus state | Issue #137 Contracts 1 and 5; ADR-005d D8 | The clause this amendment supersedes (§1.4) |
| Reconstruction identity checks on a downstream load | PR #141/#143 | Re-proof of history |
| `report_state_violations` **on a downstream load** | PR #143 | Re-proof of history. Retained at fresh publication (§3.1) |
| Single-source and chunk-runtime membership verification on a downstream load | PR #141/#143 | Re-proof of history |
| Transform-configuration hash recomputation on a downstream load | PR #143 | Re-proof of history |
| The nine coherent-rewrite controls — a rewritten report plus recomputed `evidence_report_hash` and `corpus_report_reference` | PR #143 | Models exactly "a malicious actor coherently rewriting the database and all dependent hashes", which §1.3(1) says 5c does not defend against |
| The adversarial mutation suite (`object.__setattr__`, `vars()`, container-write controls) | PR #142/#143 | Forensic framing. The *immutable value* is retained under §3.1 as accidental-corruption hygiene; the adversarial control surface is not a 5c promise |

**Stated plainly:** the machinery retired here is machinery this session built. `report_state_violations`
and its coherent-rewrite controls were the correct answer to the contract as it stood on 2026-08-01 and
are the wrong shape for the contract as amended — at the downstream boundary only.

### 3.4 Reassess during the contract-to-code audit

| Item | Question deferred |
|---|---|
| `TRANSFORM_SOURCE_MODULES` whole-file hashing over eleven modules | See §5 — an unresolved owner choice, not an engineering call |
| Which retired obligations correspond to deletable code versus code that stays and is called from fewer places | Explicitly out of scope here |
| Whether `load_verified_published_release` splits into a thin downstream entry plus a full 5c-internal proof, or the downstream entry calls `load_recorded_release_pair` directly | Implementation shape, after authority is approved |
| Test-suite disposition for the retired controls | After the audit |
| Definition of trust-boundary obligation 5 ("compatible with the 5d transformation") | New contract surface (§2.3) |

---

## 4. Proposed authority topology

Four documents, smallest set. **Not applied.**

| # | Document | Change | Rationale |
|---|---|---|---|
| 1 | **ADR-005c** | Add one dated section, "Issue 5c Operational Reliability Amendment (2026-08-03)", carrying §1 of this draft. Add a one-line scope annotation beneath the Central Invariant pointing to it. **Do not amend the Central Invariant text.** | ADR-005c is the accepted authority that owns 5c's scope, and it is the only 5c authority still open to amendment. Its Central Invariant states what *publication* proves and never claimed downstream re-proof, so it needs annotation, not amendment. |
| 2 | **GitHub Issue #132** | Prominent prospective supersession note at the top of the body. No edit to Completion Contract A or any historical text. | #132 is **CLOSED**; it is a historical record of a completed contract. §2 of the instruction requires a prospective note rather than a silent rewrite. |
| 3 | **GitHub Issue #137** | Amend the two 2026-08-01 amendment blocks — Required Contract 1 and Required Contract 5 — replacing the superseded clause with the §2.1 trust boundary. Leave the Chroma paragraphs verbatim. | #137 is **OPEN** and is where 5d's consumption contract is normative. |
| 4 | **ADR-005d** | Amend Decision 8's 2026-08-01 owner-decision block: replace the third bullet with the §2.1 boundary; add a dated note referencing the ADR-005c amendment. Leave the Chroma paragraph and the closing "does not weaken CRD Issue 5c" paragraph unchanged. | Decision 8 is the ADR-level statement of the superseded clause. |

**Conditional fifth:** if the §5 decision is deferred rather than answered, record it in
`docs/architecture/known_unknowns.md` as a named Known Unknown rather than leaving it implicit.

Not proposed: no new ADR (this is an amendment to accepted authority, not a new architectural
decision); no change to ADR-018; no change to Issue #57; no code, test, or schema change.

---

## 5. Isolated owner decision

One genuine choice remains, and it is not an engineering call.

**Does "a materially changed source or meaningfully changed corpus receives a new release
identity" (§1.2, guarantee 4) bind to file bytes or to candidate-affecting behaviour?**

Today `TRANSFORM_SOURCE_MODULES` hashes eleven whole module files into the transform identity, so
*any* byte change in a covered file mints a new package UUID and release version. This session
produced a concrete instance: retyping one annotation in `pipeline.py` — post-persistence plumbing
that changed no candidate corpus, no bundle member, and no report schema — reminted the release,
and the owner ruled that remint unacceptable and required it reverted.

The ruling therefore implies that byte-equality is *not* the intended meaning of "materially
changed", but the amendment above does not settle what replaces it. The two answers differ
materially:

- **(a) Keep whole-file hashing.** Conservative and simple: no behavioural analysis is ever needed,
  and false remints are handled case by case as they arise (as this one was, by preserving a
  compatibility alias).
- **(b) Narrow the manifest to candidate-affecting code.** Matches the stated guarantee, but
  requires a defensible rule for what "candidate-affecting" means and moves a release-identity
  input, which is itself a reminting change.

Recommendation withheld deliberately: option (b) changes the meaning of an identity that published
releases already carry, which is an owner call rather than an implementation preference.

---

## 6. PR state at the time of drafting

| PR | State | Head | Notes |
|---|---|---|---|
| **#141** | OPEN, **draft** | `b35386c` | Converted to draft as instructed; frozen |
| **#142** | **CLOSED**, unmerged | `31be484` | Left closed; branch retained as evidence |
| **#143** | OPEN, **draft** | `5a6b6f7` | Frozen; 2 review threads unresolved, unanswered |

No code was patched, no thread replied to or resolved, no review requested, no rebase, merge,
close, or push performed.
