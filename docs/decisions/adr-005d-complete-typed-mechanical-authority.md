# ADR-005d — Complete Typed Mechanical Authority and Deterministic Rules-Package Binding

**Issue:** CRD Issue 5d  
**Date:** 2026-07-30  
**Status:** Accepted — finalized by Owner 2026-07-30  
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
corrections mint a new projection UUID.

### Decision 9 — Deterministic binding and selector ownership

5d supplies a typed binding of:

- package UUID;
- release version; and
- mechanical projection UUID.

A human-facing slug may resolve through one code-owned service but cannot serve as canonical authority.
Every rule-slice request carries deterministic selectors or an explicit whole-package flag. Invalid slugs,
accidentally empty selectors, stale bindings, and mismatched releases fail explicitly.

### Decision 10 — Typed override completion

ADR-0007's entity-targeting override deferral is discharged by 5d.

5d defines typed patch shapes for the new record/component/fact representation and applies them in the
effective mechanical view. Existing override precedence and `DISABLE` / `REPLACE` / `APPEND` semantics
remain unchanged. Overrides never mutate the immutable base projection.

`DISABLE` suppresses an exact typed target; `REPLACE` supplies a complete validated replacement for a
component or fact; and `APPEND` adds a complete typed component or fact only where the owning schema
permits multiplicity. A whole-record replacement requires an explicit record-kind-specific patch and is
never a generic JSON overwrite.

The obsolete prose-only `MechanicalEntity` target is removed under ADR-005c's pre-release clean-baseline
authority. Unmappable development targets are not guessed into new identities.

### Decision 11 — Downstream ownership remains downstream

5d does not decide:

- Character Sheet Model completeness or storage of the typed binding (2b);
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
| **D5 — Deterministic binding** | Implemented by 5d's package/release/projection binding and selector contract. |
| **D6 — Advertised mechanics fail closed** | Preserved for 15c. 5d supplies typed absence/ambiguity/stale/mismatch failures but does not certify adapter capability. |
| **D7 — #129 remains frozen** | Unchanged. |
| **Pre-release clean-baseline correction** | Governs 5d legacy removal. Obsolete mechanical entities and development rows receive no compatibility guarantee. |

No historical ADR-005c text is deleted. Add a forward reference from ADR-005c Decisions 2 and 5 to this
ADR when repository documentation is updated.

### ADR-0007

ADR-0007 remains a correct historical deferral for CRD Issue 5a. This ADR records that CRD Issue 5d is
the first issue requiring typed entity/component/fact override application and therefore **discharges**
the deferral.

Add a status note to ADR-0007:

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

Add a forward reference to ADR-005d from ADR-015 Decision 7 when repository documentation is updated.

### ADR-018

ADR-018's semantic-retrieval boundary remains unchanged. Exact governing prose may be located for
GameMaster context, but no semantic retrieval path may author, infer, or select a trust-relevant
mechanical value. No amendment beyond a cross-reference is required.

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
- 2b and 15c receive stable upstream contracts.

### Costs

- The accepted classification and mechanical declaration artifacts are substantial.
- Full semantic review cannot be replaced by a corpus count or unattended classifier.
- Table/stat-block reconstruction and scoped reference resolution require committed domain work.
- Typed fact and override families require maintenance as new authorized Rules Packages add mechanics.
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

---

## Implementation Authority

The construction-ready CRD Issue 5d specification governs required outcomes, scope, architectural
boundaries, failure behavior, and acceptance evidence. Repository-native schema, module organization,
internal decomposition, implementation phases, migration design, and test organization remain engineering
decisions unless this ADR or the Issue explicitly makes a particular choice contractual.

If implementation discovers a materially better architecture that contradicts this ADR, amend the ADR and
the affected specification in advance of, or in the same PR as, the implementation. Do not merge a quiet
contradiction.
