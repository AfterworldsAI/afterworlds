# Issue 5c Operational Reliability Amendment

**Date:** 2026-08-03
**Status:** Accepted — owner approval dated 2026-08-03. This document is the governing amendment; it
supersedes the earlier assistant-authored draft, which was rejected and is not part of the record.
Repository authority (ADR-005c, ADR-005d, `docs/architecture/srd-corpus-reproducibility.md`) is
reconciled by the pull request that introduces this document. The live GitHub issue bodies for
Issue #132 and Issue #137 are synchronized as post-merge authority synchronization; the exact
proposed text is carried in that pull request.
**Scope:** The governing contract for CRD Issue 5c and the boundary by which CRD Issue 5d consumes an
approved Issue 5c corpus release.

---

## 1. Purpose and governing standard

CRD Issue 5c exists to make the SRD 5.2.1 corpus operationally reliable for dependable gameplay and downstream Rules Package construction. It does not provide adversarial, forensic, or chain-of-custody proof.

Operational reliability means that Afterworlds can:

1. extract the identified authoritative source completely and faithfully into durable, machine-usable, citable source material;
2. detect silent omissions, stale reuse, wrong-source ingestion, accidental corruption, mismatched artifacts, and partial publication;
3. publish an immutable, stably identified corpus release;
4. assign a new release identity when the authoritative source or the meaningful corpus output changes;
5. trace supported source material back to the relevant source passage;
6. refuse publication visibly and atomically when completeness or consistency checks fail; and
7. rebuild, diagnose, or correct the approved corpus without depending on Chroma or an opaque legacy artifact.

The required standard is reliable source material for Issue 5d—not proof that a malicious actor could not coherently rewrite the database and every dependent value.

This amendment is prospective. It supersedes conflicting requirements in Issue #132, Issue #137, ADR-005c, and ADR-005d once incorporated into those authorities. It does not alter the historical record of what Issue 5c originally required or what its implementation previously proved.

---

## 2. Issue 5c guarantees

### 2.1 Binding operational outcomes

Issue 5c must continue to guarantee all of the following outcomes:

- **Exact source identification.** The corpus identifies the authoritative SRD document, source version, license, and a checksum sufficient to detect use of a different document.
- **Complete and faithful representation.** The complete in-scope source is represented or deliberately excluded under an explicit, reviewable policy. Silent omission is not acceptable.
- **Citable provenance.** Authoritative corpus records retain stable source locations and enough source context for downstream explanation and citation.
- **Authoritative/derivative separation.** Extracted source material remains distinguishable from summaries, indexes, embeddings, typed interpretations, and other derived material.
- **Stable immutable publication.** A published corpus release is never silently mutated or replaced in place.
- **Meaningful-change versioning.** A change to the authoritative source or to the approved logical corpus output produces a new release. Incidental implementation changes that leave the approved logical corpus unchanged do not, by themselves, require a new release.
- **Accidental mismatch and corruption detection.** Publication, verified reuse, and the downstream trust seam reject inconsistent release metadata, mismatched corpus state, stale artifacts, and accidental corruption relevant to the material being consumed.
- **Fail-closed publication.** A failed completeness, consistency, persistence, or required projection check leaves no usable partial release.
- **Rebuildability and diagnosis.** The committed source, declared process/configuration, approved logical corpus, and diagnostic evidence are sufficient to reproduce the meaningful corpus result and investigate defects.
- **Legacy quarantine.** The incomplete prior corpus and its obsolete mechanics cannot remain reachable through active ingestion, selection, fallback, or runtime paths.
- **Typed-mechanics boundary.** Issue 5c does not certify that source prose has been correctly interpreted as typed mechanics. That is Issue 5d's responsibility.

### 2.2 What Issue 5c does not promise

Issue 5c does not promise:

1. resistance to a malicious actor coherently rewriting the database and every related checksum or reference;
2. cryptographic nonrepudiation, chain-of-custody proof, or courtroom-grade historical evidence;
3. a complete mathematical genealogy connecting every stored identity to every other identity;
4. an exact mandatory count of top-level hashes or proof artifacts;
5. byte-identical regeneration of every report, serialization, database representation, or incidental artifact when the approved logical corpus is unchanged;
6. downstream reconstruction and re-proof of the entire historical publication process whenever an approved release is loaded; or
7. certification of typed mechanical correctness, adapter support, or gameplay adjudication.

Hashes and immutable records remain useful where they cheaply prevent wrong-source ingestion, stale reuse, accidental corruption, mismatched state, or silent mutation. They are not independent product goals.

---

## 3. Prospective supersession of the original Issue 5c contract

The original Completion Contract A in Issue #132 prescribed both operational outcomes and a specific forensic proof architecture. This amendment preserves the operational outcomes in §2.1 but supersedes the following as governing requirements:

- exactly five top-level immutable release hashes;
- the requirement that every identity participate in a complete acyclic derivation graph;
- byte-for-byte regeneration of the entire build and every generated proof artifact;
- exhaustive atomic-leaf accounting as the uniquely required method of proving completeness;
- a canonical bundle topology whose principal purpose is proof genealogy;
- a frozen evidence report as an independently authoritative proof object;
- coherent-rewrite controls intended to detect a database and all dependent identities being rewritten together;
- downstream reconstruction of ledgers, policies, reconciliations, bundle roots, report summaries, and runtime membership merely to re-prove historical publication; and
- any mechanism-heavy acceptance criterion that does not materially prevent one of the operational failures named in §1.

This supersession does **not** automatically delete the corresponding implementation. Existing ledgers, reconciliation records, hashes, reports, manifests, or validators may remain when the later contract-to-code audit shows that they are a low-cost way to satisfy a retained operational outcome. Their present existence no longer makes their exact topology or derivation mandatory.

The evidence report remains a diagnostic record of what publication checked and what release was produced. It is not a second authority that downstream consumers must reconcile against a reconstructed history.

---

## 4. Mechanism disposition

The contract-to-code audit must classify each current mechanism by the concrete failure it prevents, not merely by whether the check runs during publication or downstream loading.

### 4.1 Retain as binding outcomes

| Outcome | Operational failure prevented |
|---|---|
| Authoritative document identity and source checksum | Wrong-source ingestion |
| Complete in-scope coverage or explicit policy-approved exclusion | Silent omission |
| Source-to-corpus concordance sufficient to catch stale, misplaced, or fabricated source text | Wrong or stale corpus content |
| Stable per-record provenance and locators | Uncitable or undiagnosable rules |
| Authoritative/derivative separation | Derived material masquerading as source authority |
| Immutable published release identity | Silent mutation of an existing release |
| New identity for a meaningfully changed source or logical corpus | Corrected content masquerading as an old release |
| Direct integrity validation of the authoritative corpus state | Accidental corruption or mismatched persisted content |
| Atomic publication and rollback/refusal | Usable partial release |
| Clean active-path quarantine of the incomplete legacy corpus | Obsolete corpus reuse |
| Required live Chroma projection verification during fresh publication and verified reuse | Declaring publication/reuse before the required retrieval projection exists |
| A diagnostic publication record | Inability to explain or investigate a failed or suspect release |

### 4.2 Simplify or retain only when justified

The following mechanisms are not binding in their current shape. The later audit may keep, simplify, combine, or remove them according to the operational outcome they serve:

- frozen source ledger and its exact segmentation model;
- reconciliation member and exact identity-level leaf accounting;
- reconciliation-policy hash and frozen-policy topology;
- canonical bundle and bundle-member manifest;
- evidence-report schema, hash, and report reference;
- transform source/configuration hashing;
- persisted-corpus digest composition;
- package UUID and release-version derivation formula;
- report-versus-state validators;
- single-source, chunk-membership, and runtime-membership validators; and
- adversarial mutation and coherent-rewrite tests.

The audit must prefer the smallest structure that preserves complete, faithful, citable ingestion; stable releases; meaningful-change versioning; accidental-corruption and stale-reuse detection; atomic publication; and rebuildability.

### 4.3 Settled identity semantics

Release identity tracks the authoritative source and the approved logical corpus, not every byte of every implementation file.

Therefore:

- a source change or meaningful change to corpus content, structure, provenance, or compatibility requires a new release;
- a correction that changes the approved logical corpus requires a new release;
- an incidental code, annotation, comment, logging, or plumbing change that leaves the approved logical corpus and its compatibility unchanged does not require reminting solely because a whole source file changed; and
- choosing the least complicated implementation of this rule belongs to the contract-to-code audit. It is not an unresolved Owner Decision.

---

## 5. Downstream Issue 5d trust boundary

Issue 5d consumes an approved Issue 5c release. It does not become a second Issue 5c publication system.

Before binding or transforming a release, the 5c-owned downstream seam must establish:

1. the requested release exists and is marked published;
2. the release identifier and package/release relationship are internally consistent;
3. the release identifies the expected authoritative source and corpus;
4. the authoritative SQLite corpus state being supplied matches the approved release's recorded persisted-corpus identity through a direct operational integrity check—not merely because an evidence-report hash matches;
5. the corpus records needed by 5d are present and reachable through the approved authoritative seam; and
6. the release uses a corpus contract or schema version supported by the 5d transformation.

"Compatible with the 5d transformation" means only that 5d recognizes and supports the published corpus contract/schema it is about to consume. The authority does not prescribe whether engineering represents that support through a version field, capability declaration, or equivalent low-cost mechanism.

Issue 5d must fail closed when any of these checks fails. It may record the 5c release identity, source identity, corpus identity, and compatibility version as provenance for its own deterministic Rules Package.

Issue 5d must not, merely because it loads an approved release:

- reconstruct and re-hash the full source ledger, reconciliation member, policy chain, canonical bundle, or evidence report;
- prove that every historical identity was mathematically derived from every recorded predecessor;
- compare diagnostic report summaries against a newly reconstructed publication history;
- rerun coherent-rewrite or adversarial mutation controls; or
- reopen or recompute Chroma.

Fresh 5c publication and 5c verified reuse may perform stronger internal checks when they cheaply support an operational outcome. Those checks do not automatically become downstream obligations.

---

## 6. Chroma boundary preserved

The Owner Decision of 2026-08-01 remains unchanged:

- The persisted-corpus digest remains immutable historical identity for the published corpus.
- Fresh Issue 5c publication and Issue 5c verified reuse check the live Chroma projection, including the required write/read-back and SQL-versus-projection verification before declaring a release published or reusable.
- Downstream Issue 5d verification does not reopen or recompute Chroma.
- Chroma remains rebuildable, non-authoritative retrieval infrastructure owned by CRD Issue 18. Loss or corruption of the live collection after successful Issue 5c publication is an Issue 18 operational defect, not a change to 5c source authority.

This amendment does not turn Chroma into mechanical authority and does not make its implementation-dependent embedding bytes part of the canonical source corpus.

---

## 7. Authority reconciliation

| Authority | Retain | Amend or supersede |
|---|---|---|
| **Issue #132 / approved Issue 5c** | Exact-source ingestion; full-corpus scope; faithful and citable source records; provenance; immutable publication; fail-closed publication; legacy quarantine; separation from typed mechanics | Add a prominent prospective supersession note. Replace Completion Contract A's proof architecture as governing authority with §§1–4 of this amendment. Do not silently rewrite the historical body. |
| **ADR-005c** | Source corpus and typed mechanics remain separate; vector retrieval is non-authoritative; deterministic package/release binding remains required at the level of meaningful operational identity; advertised mechanics remain outside 5c | Add a dated operational-reliability amendment. Correctly distinguish ADR-005c's architectural decisions from the detailed proof machinery introduced by Issue #132. Any wording that makes exact proof topology or byte-identical artifact regeneration binding is prospectively superseded. |
| **Issue #137 / final Issue 5d** | Complete typed-mechanics authority; deterministic Rules Package identity; binding to one approved 5c corpus release; fail-closed publication; provenance; Chroma exclusion | Replace requirements to reconstruct and re-prove all SQLite-authoritative 5c state and evidence identities with the §5 downstream trust boundary. |
| **ADR-005d** | Issue 5d owns typed interpretation and deterministic Rules Package construction; 5c owns authoritative source-corpus publication; Chroma remains outside downstream authority | Amend Decision 8 and its 2026-08-01 block so 5d verifies the operational trust seam in §5 rather than the complete historical 5c proof graph. Preserve the Chroma decision. |

ADR-005c's existing Central Invariant must not be described as the source of Issue #132's entire Completion Contract unless its text actually contains those guarantees. The repository amendment must quote and reconcile the exact current language rather than importing Issue #132's detailed proof architecture into ADR-005c by implication.

---

## 8. Required implementation topology after owner approval

Apply this authority change before modifying the frozen PR stack:

1. Create a small, main-based authority amendment PR that:
   - adds the dated ADR-005c amendment;
   - adds the prospective supersession note to Issue #132;
   - reconciles Issue #137's 5c-consumption requirements; and
   - amends ADR-005d's corresponding decision while preserving the Chroma boundary.
2. Create a new main-based **Issue 5c operational correction** issue. It owns:
   - the bounded contract-to-code audit;
   - classification of current machinery against §§2–5;
   - the smallest code and test changes needed to implement the amended contract; and
   - explicit preservation of honest existing release identity wherever the approved logical corpus is unchanged.
3. Implement and independently review that Issue 5c correction.
4. Close or supersede PR #143 if its replacement verification architecture no longer matches the amended boundary.
5. Restack PR #141 onto the accepted 5c correction, then reassess only its Issue 5d-owned work under the reconciled Issue #137 and ADR-005d contracts.

The authority amendment must not itself choose tables, validators, report schemas, hash counts, or migration details. Those are engineering decisions bounded by the operational outcomes above.

---

## 9. Frozen PR disposition

Until the authority amendment and 5c operational-correction plan are approved:

| PR | Required state |
|---|---|
| **#141** | Open, draft, frozen at `b35386c`; do not patch, rebase, merge, or request further review. |
| **#142** | Closed and unmerged; retain only as historical evidence. |
| **#143** | Open, draft, frozen at `5a6b6f7`; do not patch the two P1 findings or resolve their threads. |

No further Codex review round should be requested on #141 or #143 until the governing contract is approved and the replacement 5c boundary is implemented. The unresolved P1s in #143 are evidence that the superseded forensic contract remains incomplete; they are not instructions for another local patch.

---

## 10. Approval effect

Owner approval of this amendment settles the following:

- Issue 5c is judged by operational reliability, not adversarial historical proof.
- Practical completeness, provenance, immutability, meaningful-change versioning, accidental-corruption detection, atomic publication, and rebuildability remain mandatory.
- Exact proof-object count, proof genealogy, and byte-identical incidental artifacts are no longer governing outcomes.
- Issue 5d trusts a narrow 5c-owned operational verification seam and does not reconstruct 5c's publication history.
- Incidental implementation-byte changes do not remint an unchanged approved logical corpus solely because they alter a whole-file hash.
- Chroma remains non-authoritative and outside downstream 5d verification.
- Code simplification begins only through the separately scoped 5c contract-to-code audit.
