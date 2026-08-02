# ADR-005d — Complete Typed Mechanical Authority and Deterministic Rules-Package Binding

**Issue:** CRD Issue 5d  
**Date:** 2026-07-30  
**Status:** Accepted — finalized by Owner 2026-07-30; amended by Owner Decision 2026-07-30 (PR #138
review) so the effective runtime binding also carries an immutable override-set identity, and clarified
in the same review so the contents that identity names are retained as immutable, provenance-exact replay
evidence; amended by Owner Decision 2026-08-01 (PR #141 review) to fix how a downstream 5d consumer
verifies an already-published 5c release's `persisted_corpus_digest` — see Decisions 6 and 8  
**Amends/clarifies:** ADR-005c, ADR-0007, ADR-015, ADR-018

---

## Context

ADR-005c established the Rules Authority repair sequence:

```text
5c source-corpus integrity
→ 5d typed mechanical authority and deterministic binding
→ 2b package-bound character state
→ 15c repaired bounded-d20 execution and certification
```

CRD Issue 5c now publishes the complete authoritative SRD 5.2.1 source corpus with deterministic
identity, exact source accounting, provenance, persisted-state verification, and a publication gate. It
deliberately does not decide which text is mechanically substantive or produce typed mechanical
authority.

Discovery against the real 5c pipeline found:

- 28,109 represented leaves in the measured release, including rules, headings, legal text, examples,
  explanatory prose, and other non-mechanical material;
- 2,422 `ENTRY` containers, whose geometry-derived boundaries are reliable for some categories but not
  for composite stat blocks, non-entry general rules, nested creature records, or many tables;
- 683 logical tables, including stat-block prose fragmented across cells;
- 1,533 represented leaves with at least two lexical mechanical-signal families;
- multiple mechanical facts spanning several leaves/table cells; and
- 203 colliding names among 1,893 distinct container names.

Therefore:

1. 5c `REPRESENTED` cannot mean "mechanically substantive."
2. One record per `ENTRY` and one component per leaf are unsound.
3. Reference coverage alone cannot prove faithful mechanical representation.
4. A projection identity that omits actual facts and relationships can reuse stale authority.
5. Aggregate extraction floors or prose percentages cannot prove per-record completeness.
6. Complete representation must not be confused with how much the bounded-d20 adapter executes.

The Owner has settled completed 5d scope as the full mechanically substantive SRD 5.2.1 corpus.

---

## Central Decision

Afterworlds will publish one complete typed mechanical-authority projection for an exact published 5c
release. Every mechanically substantive source component is represented:

- through typed declarative facts where meaning can be preserved faithfully;
- through exact governing prose where contextual, subjective, or open-ended GameMaster judgment remains
  necessary; or
- through both.

This projection is complete mechanical **representation**, not universal deterministic **execution**.
The hand-authored Rules System Adapter separately declares and proves the component shapes it can execute.

---

## Decisions

### Decision 1 — Complete source accounting, selective execution

The completed first projection accounts for the full mechanically substantive content of SRD 5.2.1.
Implementation phasing cannot redefine a partial projection as completed 5d.

Structured/prose-bound handling follows representability of source meaning. No owner-selected extraction
percentage, prose ceiling, or adapter-coverage target determines that classification.

### Decision 2 — Span-exact semantic classification

Every 5c `REPRESENTED` leaf is partitioned into accepted semantic spans classified as:

- substantive mechanical authority;
- supporting authority;
- non-mechanical material under a closed reason;
- or unresolved.

Unreviewed/proposed and unresolved spans block publication. `PROSE_BOUND` is not a classification default;
it is an affirmative component-handling judgment requiring a closed irreducibility reason.

Supporting authority is first-class. Headings, examples, cross-references, explanatory clauses, and
GameMaster guidance may identify, limit, explain, or exemplify mechanics even when they are not
independent structured facts.

### Decision 3 — Semantic records and many-to-many provenance

Mechanical records are assembled from a committed accepted inventory. A 5c `ENTRY` is structural evidence,
not universal semantic authority.

Records and components use stable semantic keys rather than positional ordinals. Facts, prose bindings,
and relationships carry exact many-to-many provenance to 5c leaf subspans. Primary and contextual roles
are distinct; contextual overlap is permitted while conflicting primary claims fail.

### Decision 4 — Closed typed facts, no generated rules engine

Structured authority uses a closed, versioned discriminated union of fact families. A new mechanical
family requires a typed schema and tests or an honest prose-bound classification.

The projection cannot contain:

- arbitrary executable expressions;
- runtime-interpreted scripts or a general rules DSL;
- model-authored mechanical logic;
- generic numeric/key-value escape hatches; or
- mechanically authoritative values inferred from source prose at runtime.

The projection is declarative data consumed by hand-authored code.

### Decision 5 — Exact completeness, not aggregate thresholds

Publication is proven through exact full-corpus accounting and accepted per-record/component obligations.
Every expected record, component, fact family, prose-bound claim, provenance edge, and reference must be
present exactly as required.

Counts, extraction floors, prose percentages, and category ceilings may detect regressions but cannot
prove completeness. An all-prose projection and a duplicated-fact projection must both fail.

### Decision 6 — Complete meaning-bearing identity

Mechanical projection identity binds:

- the exact published 5c source release;
- semantic classification;
- record assembly and membership;
- actual components and handling;
- actual structured facts and relationships;
- prose bindings and exact provenance;
- reference resolutions;
- representation schema and semantic policy; and
- normalization/canonicalization rules.

Reviewer names, timestamps, proposal origins, and comments are audit metadata and do not change semantic
identity unless the accepted semantic content changes.

Identity derivation is acyclic. Stable record/component/fact IDs derive from the projection UUID and
committed semantic keys, never local ordinals.

This identity covers the immutable base projection only. `RuleOverride` state is deliberately outside it
and carries its own separate identity under Decisions 9 and 10, so an override change never mutates or
remints the base projection UUID.

**Owner Decision 2026-08-01 (PR #141) — the 5c `persisted_corpus_digest` in the 5d binding.** The exact
`persisted_corpus_digest` recorded by a successfully published 5c release remains part of the immutable
5d source binding and of mechanical projection identity. Its meaning is unchanged: it is the 5c
cross-store proof identity, and it still covers the vector logical state 5c bound into it. What this
amendment fixes is how a *downstream* 5d consumer verifies an already-published release — the digest is
consumed as immutable release identity and historical publication evidence, verified for exact equality
against the authoritative 5c release record and its recorded evidence report. 5d does not redefine,
narrow, or recompute the value.

### Decision 7 — Build-time reference resolution

Mechanical references resolve at build time through committed source scope, aliases, and exact target
semantic keys. Unique destination names alone do not establish source intent. Bare strings, runtime
similarity, and model selection are never authoritative references.

Ambiguous, unresolved, invalid, or cross-release references block publication.

### Decision 8 — Persist, reconstruct, prove, then publish

5d follows:

```text
build candidate
→ persist draft
→ reconstruct from persisted state
→ compute persisted-state digest
→ run exact completeness gate
→ atomically publish
```

Draft/partial projections are not active authority. Published projections are immutable. Meaning-changing
corrections *to the projection itself* mint a new projection UUID; changes to override state do not (see
Decision 9).

**Owner Decision 2026-08-01 (PR #141) — what the 5d publication gate proves about the bound 5c release.**
Before publishing a mechanical projection the gate must, through the 5c-owned verification seam:

- verify exact equality of the six-value binding — including `persisted_corpus_digest` — with the
  authoritative 5c release record;
- verify that release's recorded evidence payload and proof identities;
- reconstruct and re-prove all SQLite-authoritative corpus state that seam exposes; and
- reject missing, mismatched, unpublished, or SQL-inconsistent release state.

The 5d gate **does not** open or depend on ChromaDB to recompute the vector-backed portion of the 5c
persisted-corpus digest. Chroma remains an informational, rebuildable projection and is not mechanical
authority (ADR-018 D4/D10). Loss, corruption, or absence of the live rules-corpus vector collection after
successful 5c publication is a CRD Issue 18 operational/reindex defect; it does not make the 5c source
authority stale for 5d publication.

This does not weaken CRD Issue 5c. Fresh 5c publication and 5c's own verified-reuse path must continue to
write, read back, and verify the required vector projection before declaring a 5c release published or
reusable.

### Decision 9 — Deterministic effective binding and selector ownership

5d supplies a typed, immutable **effective** binding of:

- package UUID;
- release version;
- mechanical projection UUID — the immutable base projection; and
- override-set UUID — the exact applied effective override set.

Base-projection identity and override-set identity remain distinct and are never collapsed into one
value. The effective binding is **provenance-exact**, not merely mechanically equivalent: the override-set
identity names both the exact effective mechanical state applied and the exact authoritative override
records that supplied it. The canonical identity-bearing representation of every override entry therefore
carries:

- stable override identity (`override_id` or its repository-native successor);
- override origin (`house_rule`, `package_patch`, or its typed successor);
- exact typed target identity;
- operation;
- precedence/order;
- enablement state; and
- complete validated payload.

The override-set UUID is derived deterministically at binding-resolution time from that canonical ordered
state. Adding, removing, enabling, disabling, reprioritizing, retargeting, or changing the payload of an
applicable override yields a different override-set UUID, and so does deleting and recreating an otherwise
identical override under a different identity or origin: a house rule and a package patch with identical
mechanical contents are not the same provenance-exact authority. The no-overrides state has its own
deterministic override-set UUID; it is not the absence of one.

Identity is not silently broadened to incidental audit metadata. Creation timestamps, authors, comments,
and proposal history remain non-identity audit metadata unless they participate in override applicability,
ordering, or resolution. The enclosing package UUID already supplies package scope.

Each override-set UUID is the content-derived identity of one immutable, replayable override-set
**version**. That version preserves — or is deterministically reconstructable from append-only retained
evidence that preserves — the exact canonical ordered override state enumerated above. Historical
override-set versions remain retrievable after the source `RuleOverride` rows are edited, disabled,
reprioritized, retargeted, or deleted. Recording the override-set UUID while retaining only mutable
current override rows is insufficient. Current override rows remain the authoring surface; they are not
historical replay evidence. That version may be retained as a content-addressed snapshot, as append-only
version records, or as append-only events that deterministically reconstruct the canonical version; an
event log need not itself be content-addressed, but its reconstructed canonical version must reproduce and
verify the recorded override-set UUID. Which of those shapes a repository uses is an implementation choice
this ADR does not make. Override-set version retention is runtime state and is separate from the
Decision 8 projection publication lifecycle.

Rule slices, deterministic-consumer views, GameMaster authority views, applied-override provenance,
stale/mismatch validation, and replay/audit evidence identify the exact effective binding — all four
components — that produced them. Two operations follow, and they are distinct:

- **Runtime resolution and adjudication.** A recorded binding whose override-set UUID no longer matches
  the override-set UUID recomputed from current override state is `STALE` and fails explicitly; it is
  never silently re-resolved against current overrides.
- **Audit, replay, and provenance reads.** These resolve against the retained immutable override-set
  version and must succeed, reconstructing the exact effective mechanical authority originally applied
  rather than merely reporting that it differs from current override state. `STALE` is not a valid answer
  here; a failure to reconstruct is a retention defect, not a divergence signal.

Overrides never mutate or remint the base projection UUID.

A human-facing slug may resolve through one code-owned service but cannot serve as canonical authority.
Every rule-slice request carries the exact effective binding plus deterministic selectors or an explicit
whole-package flag. Invalid slugs, accidentally empty selectors, stale bindings, and mismatched releases
fail explicitly.

### Decision 10 — Typed override completion

ADR-0007's entity-targeting override deferral is discharged by 5d.

5d defines typed patch shapes for the new record/component/fact representation and applies them in the
effective mechanical view. Existing override precedence and `DISABLE` / `REPLACE` / `APPEND` semantics
remain unchanged. Overrides never mutate the immutable base projection and never remint its identity;
the applied ordered override state is identified instead by the override-set UUID of the effective
binding (Decision 9), and applied-override provenance is reported against that binding.

Applied-override provenance resolves through the retained immutable override-set version, not through
current override rows, so an effective view recorded earlier remains reconstructable after the source
overrides are edited, disabled, reprioritized, retargeted, or deleted. That provenance is
provenance-exact: it reports the stable override identity and origin of each applied override alongside
its target, operation, order, enablement, and payload, so an audit can name which authoritative override
record supplied each change rather than only what the change was. The base projection and its identity are
unaffected either way.

`DISABLE` suppresses an exact typed target; `REPLACE` supplies a complete validated replacement for a
component or fact; and `APPEND` adds a complete typed component or fact only where the owning schema
permits multiplicity. A whole-record replacement requires an explicit record-kind-specific patch and is
never a generic JSON overwrite.

The obsolete prose-only `MechanicalEntity` target is removed under ADR-005c's pre-release clean-baseline
authority. Unmappable development targets are not guessed into new identities.

### Decision 11 — Downstream ownership remains downstream

5d does not decide:

- Character Sheet Model completeness or storage and revalidation of the typed effective binding (2b);
- adapter capability, certification, or execution (15c);
- how GameMaster-adjudicated outcomes become trusted mechanical state or narrative canon (15c and the
  applicable canon/state owners); or
- frozen #129 / CRD Issue 15b Phase 3 / CRD Issue 19b disposition.

5d exposes exact authority seams for those later decisions.

---

## ADR Reconciliation

### ADR-005c

ADR-005c remains authoritative and is not superseded.

| ADR-005c decision | Reconciliation |
|---|---|
| **D1 — Corpus publication and adapter certification are separate** | Preserved. 5d adds a third explicit state: mechanical-projection publication, which still does not imply adapter certification. |
| **D2 — Source corpus and executable mechanical projection are distinct** | Clarified. "Executable projection" means typed executable-facing authority, not that every represented component is code-executable. Complete 5d scope includes prose-bound GameMaster authority as part of the mechanical projection. |
| **D3 — Ingestion does not generate a rules engine** | Preserved. Typed facts are declarative; execution remains hand-authored adapter code. |
| **D4 — Semantic retrieval is never mechanical authority** | Preserved. GameMaster prose retrieval resolves to exact source-bound authority; retrieval never supplies a trust-relevant value. |
| **D5 — Deterministic binding** | Implemented by 5d's package/release/base-projection/override-set effective binding and selector contract. |
| **D6 — Advertised mechanics fail closed** | Preserved for 15c. 5d supplies typed absence/ambiguity/stale/mismatch failures but does not certify adapter capability. |
| **D7 — #129 remains frozen** | Unchanged. |
| **Pre-release clean-baseline correction** | Governs 5d legacy removal. Obsolete mechanical entities and development rows receive no compatibility guarantee. |

No historical ADR-005c text is deleted. ADR-005c Decisions 2 and 5 carry forward references to this ADR
as of this change.

### ADR-0007

ADR-0007 remains a correct historical deferral for CRD Issue 5a. This ADR records that CRD Issue 5d is
the first issue requiring typed entity/component/fact override application and therefore **discharges**
the deferral.

ADR-0007 carries this status note as of this change — followed there by a link to Decisions 9 and 10 and
a statement that its historical Context, Decision, and Consequences text is preserved:

> **Discharged by ADR-005d / CRD Issue 5d.** The typed mechanical projection now defines the concrete
> record/component/fact patch families and applies them while preserving existing override precedence and
> operations.

### ADR-015

ADR-015 remains authoritative.

- Decision 3's roll-authorship invariant is unchanged.
- Decision 7's hand-authored bounded-d20 boundary is unchanged.
- 5d supplies the typed Rules Package authority from which later 15c code may verify DCs, modifiers,
  actions, costs, and effects.
- 5d projection publication does not convert ADR-015's `undetermined` behavior into adapter support.
- 15c still distinguishes truly unsupported mechanics from missing/incomplete authority.

ADR-015 Decision 7 carries a forward reference to this ADR as of this change; its historical text and
`Accepted` status are otherwise unchanged.

### ADR-018

ADR-018's semantic-retrieval boundary remains unchanged. Exact governing prose may be located for
GameMaster context, but no semantic retrieval path may author, infer, or select a trust-relevant
mechanical value. No amendment beyond a cross-reference is required, and ADR-018 Decision 10 carries that
narrowly scoped cross-reference as of this change.

---

## Consequences

### Positive

- The shipped SRD Rules Package can support complete basic-game authority without pretending every rule
  is algorithmically resolvable.
- Open-ended mechanics such as Wish and illusion effects remain playable through exact GameMaster
  authority.
- Deterministic consumers receive typed, source-linked facts instead of parsing prose.
- Missing or ambiguous authority becomes visible and typed.
- Mechanical corrections mint new immutable identity rather than silently reusing stale releases.
- Replay and audit reconstruct the exact effective authority — base projection plus the retained
  override-set version — instead of an ambiguous package/release pair that could resolve to different
  trust-relevant values over time, and they keep working after the current override rows are edited or
  deleted. Because the binding is provenance-exact, they also name which override record and origin
  supplied each applied change. Runtime stale detection remains a separate fail-closed check against
  current override state.
- 2b and 15c receive stable upstream contracts.

### Costs

- The accepted classification and mechanical declaration artifacts are substantial.
- Full semantic review cannot be replaced by a corpus count or unattended classifier.
- Table/stat-block reconstruction and scoped reference resolution require committed domain work.
- Typed fact and override families require maintenance as new authorized Rules Packages add mechanics.
- Every effective override change mints a new override-set identity, so consumers that record or cache an
  effective binding must revalidate it rather than assume stability across override edits.
- Retained override-set versions accumulate alongside override authoring, and pruning them forfeits the
  replay and audit reconstruction they exist to provide.
- Because identity is provenance-exact, recreating an override under a new identity or changing its origin
  mints a new override-set identity even when the mechanical result is unchanged, so authoring churn is
  visible in the binding rather than hidden by it.
- Delivery requires multiple PRs before 5d is complete.

### Rejected alternatives

1. **Treat all 5c represented text as mechanical.** Rejected: 5c includes legal, navigational, flavor, and
   explanatory material.
2. **Default unreviewed text to prose-bound.** Rejected: an empty extraction could pass.
3. **One record per `ENTRY`.** Rejected: real stat blocks, general rules, tables, and nested records
   contradict it.
4. **One component per leaf.** Rejected: real mechanics are many-to-many across spans and cells.
5. **Use extraction floors or prose ceilings as completeness proof.** Rejected: duplicates and omissions
   can satisfy aggregates.
6. **Hash only schema/classification manifests.** Rejected: actual facts could change under stale identity.
7. **Let adapter breadth decide representation breadth.** Rejected: representation and execution are
   independent.
8. **Resolve references by bare name or retrieval.** Rejected: source scope and name collisions make the
   result ambiguous.
9. **Preserve the old `MechanicalEntity` for compatibility.** Rejected: it is obsolete, prose-only, and
   authorized for removal under the pre-release clean baseline.
10. **Compile the SRD into a universal rules engine.** Rejected: many mechanics are contextual or
    open-ended, and execution remains hand-authored.
11. **Bind runtime authority to package, release, and base projection alone.** Rejected by Owner Decision
    2026-07-30 (PR #138): overrides change the effective mechanical view, so one such binding could
    resolve to different DCs, effects, or disabled mechanics over time and neither stale detection nor
    replay could reconstruct the authority actually used.
12. **Record the override-set identity but retain only current override rows.** Rejected in the same
    review: the identifier would name state that no longer exists once an override is edited, disabled,
    reprioritized, retargeted, or deleted, leaving audit and replay able to detect divergence but not to
    reconstruct the authority actually applied. This is the standing auditability invariant — operational
    state must be reconstructable from explicit retained evidence, not inferred from mutable current
    state — applied to override sets.
13. **Identify a retained override-set version by its mechanical contents alone.** Rejected in the same
    review: deleting and recreating an otherwise identical override, or changing only its origin, would
    reuse the same identity and leave no evidence of which authoritative record actually applied, which is
    the applied-override provenance Decision 10 promises. The retained state carries stable override
    identity and origin as well. Identity is not broadened past that: creation timestamps, authors,
    comments, and proposal history stay non-identity audit metadata unless they participate in
    applicability, ordering, or resolution.
14. **Recompute the vector-backed half of the 5c `persisted_corpus_digest` during 5d publication.**
    Rejected by Owner Decision 2026-08-01 (PR #141): it would make mechanical authority depend on live
    Chroma health, contradicting ADR-018 D4/D10 — an informational, rebuildable projection would become a
    precondition for publishing mechanical canon, so a reindex-able vector defect would present as stale
    source authority. 5d verifies the recorded digest against the authoritative release record and its
    evidence report and re-proves the SQLite-authoritative state; proving the live vector projection stays
    with 5c publication and 5c verified reuse, and its operational health with CRD Issue 18.

---

## Implementation Authority

The construction-ready CRD Issue 5d specification governs required outcomes, scope, architectural
boundaries, failure behavior, and acceptance evidence. Repository-native schema, module organization,
internal decomposition, implementation phases, migration design, and test organization remain engineering
decisions unless this ADR or the Issue explicitly makes a particular choice contractual.

If implementation discovers a materially better architecture that contradicts this ADR, amend the ADR and
the affected specification in advance of, or in the same PR as, the implementation. Do not merge a quiet
contradiction.
