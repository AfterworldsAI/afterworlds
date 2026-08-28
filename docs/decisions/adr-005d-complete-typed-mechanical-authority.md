# ADR-005d — Complete Typed Mechanical Authority and Deterministic Rules-Package Binding

**Issue:** CRD Issue 5d  
**Date:** 2026-07-30  
**Status:** Accepted — finalized by Owner 2026-07-30; amended by Owner Decision 2026-07-30 (PR #138
review) so the effective runtime binding also carries an immutable override-set identity, and clarified
in the same review so the contents that identity names are retained as immutable, provenance-exact replay
evidence; further amended by Owner Decision 2026-08-08 so a runtime prose-bound override may resolve
through a first-class authored-authority overlay distinct from 5c source prose, replacing this ADR's
blanket prohibition on a second prose store with the narrower invariant that there is no duplicated store
for what the SRD source says; further amended by Owner Decision 2026-08-09 so that overlay's effective
`handling` is a final classification of each component's own surviving facts and prose, derived once at
final assembly for every component regardless of which override family supplied its authority or which
operation resolved last, rather than remembered as a sticky promotion, correcting this ADR's prior text to
the contrary  
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

**Amended by Owner Decision 2026-08-08.** The many-to-many provenance required above binds the immutable
base projection's prose bindings: those resolve exclusively to 5c leaf subspans and carry no other
provenance. A distinct runtime authored-authority prose overlay, layered over a published record or
component (Decision 10), is not a prose binding under this decision and does not participate in its
many-to-many 5c subspan provenance. Authored prose is never assigned a 5c leaf subspan, a chunk identity,
or an irreducibility claim copied from base-projection authority; its provenance is the authored override
record and the retained override-set version that supplied it (Decision 9).

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

**Amended by Owner Decision 2026-08-24 — duplication is a shape, not only a fact.** "A duplicated-fact
projection must fail" is the general rule that one source statement may not be published twice, and it
binds every element kind the representation carries, not only typed facts. Two forms of it are now stated
explicitly because both were reachable and neither was caught:

- **Sibling components.** Two different components of one record may not hold facts with the same
  `fact_key` when both draw it from the *same* substantive span. Facts equal by content alone are not
  duplication — a rule genuinely restated in two places is two claims — so the rule is fact equivalence
  **plus shared source provenance**, never fact equality alone, and never inferred from parsed target-key
  positions. This is deliberately not global cross-component fact uniqueness.
- **Reference ownership.** Where a record owns a citation directly (Decision 7 as amended), no component
  of that same record may state the same citation. Record ownership *means* no component states it, so the
  pair contradicts its own justification. Two different **components** citing the same wording stay legal:
  each is its own claim and each carries its own provenance edge.

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

**Amended by Owner Decision 2026-08-08.** A runtime authored-authority prose overlay never contributes a
component, fact, or prose binding to this identity. Whether zero or many authored prose overrides are
applied at runtime, the projection they are applied over has exactly one `mechanical_projection_uuid`; the
authored overlay's own complete canonical form participates instead in the override-set identity governed
by Decision 9.

**Amended by Owner Decision 2026-08-24 — explicit verified schema succession, and zero identity movement
across it.** Accepted authority is committed under the representation schema it was reviewed under, and
identity binds that schema (above). A later content batch may need a wider schema, so the two have to
meet. They meet on exactly these terms, and on no others:

1. **Zero movement.** A previously accepted fact key or provenance coordinate may not move. The absence of
   published consumers or overrides does not authorize identity churn. A succession that would move one is
   refused; it is never reconciled, renumbered, or re-derived.

2. **A field added after a schema is omitted from the canonical payload when it carries no meaning.** An
   absent field and a field at its declared default state the same thing, so one canonical form serves
   both. This is what makes zero movement achievable rather than merely required: an element accepted
   under the earlier schema *already has* its later-schema canonical form, so nothing has to be rewritten
   for it to be inherited. The rule is value-keyed, never version-keyed — a fact's canonical form does not
   depend on which schema is declared.

3. **The declared version decides legality, never canonical form.** A post-succession field holding
   meaning under an earlier declaration is refused, and refused *as a restamp* — an artifact whose declared
   schema and content disagree — rather than silently emptied to reproduce a legacy identity. Fields
   introduced at or before the last-accepted schema keep unconditional emission; switching one to
   omit-when-empty would move exactly the identities this rule exists to hold still.

   *Amended 2026-08-28 (#137 round 4) — legality is checked wherever authority is created or admitted, not
   only where the schema changes.* A representation and the schema identity it declares are admissible
   together only when its meaning is legal under that version **and** its exact `(version, hash)` pair is a
   contract this build accepts authority under — the live pair, or an endpoint of the registered succession
   graph. Unknown versions, invented hashes, and known versions paired with another version's hash are one
   refusal: the union that decides what these facts may mean cannot be established. An empty lift history
   exempts neither half — an artifact that crossed no succession has said nothing about whether it was
   built under the schema it names. The rule is enforced at committed-artifact loading, at acceptance for
   both the proposed and the prior half, inside a verified lift, and at publication, which holds the strict
   end of the same rule: a projection about to become *current* authority must declare the live pair
   exactly. Being *serializable* under a version is deliberately not sufficient — schema 1 and schema 2
   payloads remain reproducible for historical reconstruction, and reproducing an identity is not admitting
   new accepted authority under it.

4. **Compatibility is declared, never inferred.** Each authorized succession is registered by its exact
   `(version, hash)` source **and** destination pair, with its destination hash written literally rather
   than derived from whatever the type surface currently is. Version ordering is not evidence: "schema 4
   is newer than schema 3" says nothing about whether schema 4 can carry schema 3's accepted content, and
   a rule that reasoned that way would authorize every future succession in advance. An unregistered,
   reversed, skipped, or hash-mismatched transition fails closed.

5. **A succession proves, it does not transform.** Before any re-declaration, every inherited element is
   proved byte-identical under both schemas, collection by collection. Nothing is normalized, reshaped, or
   defaulted on the way through: a difference is a semantic change the reviewer never saw. This is a
   stronger guarantee than a transforming lift could give — a transforming lift has to *argue* that its
   mapping preserved meaning; this one demonstrates that nothing moved.

6. **The crossing is evidence, never identity.** That an artifact was carried across a succession is
   recorded beside its acceptance batches, on the evidence half of accepted inputs, and never on the
   accepted oracle. Which schema an artifact was carried across is review and migration process, and
   process is not identity-bearing. The combined artifact declares the destination schema and takes the
   new oracle identity that follows from declaring it.

   *Amended 2026-08-28 (#137 round 3) — the recorded evidence is exactly what a loader can check.* Loaded
   evidence is read from a file, so it proves nothing about itself. Each record is therefore validated
   against the registry and the artifact's own declaration: the transition is registered by its exact
   source and destination pair under the registered lift ID, the records form a continuous oldest-first
   chain, the last destination is the schema the artifact declares, no transition repeats, and the proof
   extent names exactly the representation's collections, each of them once. What a record may **not**
   carry is a per-collection element count. The count a lift produces is true when it is produced and
   unverifiable ever after: one committed artifact supersedes its predecessor, later batches merge into
   the same collections, and no record anchors the crossing to a point in the batch sequence — so the
   pre-lift extent cannot be re-derived, and a fabricated number would validate exactly as well as a true
   one. Evidence a reader cannot check is not evidence, and an audit surface may not state more than the
   build can support.

### Decision 7 — Build-time reference resolution

Mechanical references resolve at build time through committed source scope, aliases, and exact target
semantic keys. Unique destination names alone do not establish source intent. Bare strings, runtime
similarity, and model selection are never authoritative references.

Ambiguous, unresolved, invalid, or cross-release references block publication.

**Amended by Owner Decision 2026-08-24 — a record may own the references it authors.** Some records cite
other records in their own right: a hazard umbrella names the five hazards it collects, and no component
of that umbrella states the naming. A reference therefore has exactly one owner, and it is either the
source **record** or one named **component** of that record.

- A component-owned reference must name a component that really exists within its source record —
  unchanged, and every previously accepted reference is one.
- A record-owned reference must name a real source record and must not carry a fabricated or dangling
  component. It does not license inventing a component to hang a citation on, and a component invented for
  that purpose publishes a component the source never states.
- Everything else about a reference is unchanged and remains fail-closed: ambiguity, scope resolution,
  target existence, per-element provenance, canonical ordering, persistence reconstruction, and digest
  coverage.
- An earlier schema continues to reject record-owned reference meaning. Serializing it under a schema that
  has no such form would produce bytes an earlier reviewer would read as a component-owned reference to a
  component with an empty key, which is the restamp Decision 6 as amended refuses.

This ownership widening is a *domain* widening of the existing owner field rather than a new ownership
field beside it, precisely so that no accepted reference's canonical payload or provenance coordinate
moves.

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

**Owner Decision 2026-08-01, as amended 2026-08-03 — what the 5d publication gate proves about the
bound 5c release.**

*Preservation note.* This block is recorded on `main` for the first time here. The 2026-08-01 Owner
Decision was drafted on PR #141, which remains open, draft, and unmerged; its Chroma provisions are
carried below **unchanged**, and its downstream re-proof requirement is carried in its amended form.

CRD Issue 5d owns typed interpretation and deterministic Rules Package construction. It consumes an
approved CRD Issue 5c release; it does not become a second 5c publication system. Before publishing a
mechanical projection, the gate must establish, through the narrow 5c-owned operational trust seam:

- the requested release exists and is marked published;
- the release identifier and package/release relationship are internally consistent;
- the release identifies the expected authoritative source and corpus;
- the authoritative SQLite corpus state being supplied matches the approved release's recorded
  persisted-corpus identity through a **direct operational integrity check** — not merely because an
  evidence-report hash matches;
- the corpus records 5d needs are present and reachable through the approved authoritative seam; and
- the release uses a corpus contract or schema version supported by the 5d transformation.

"Compatible with the 5d transformation" means only that 5d recognizes and supports the published corpus
contract/schema it is about to consume. This ADR does not prescribe whether engineering represents that
support through a version field, a capability declaration, or an equivalent low-cost mechanism.

The gate **fails closed** when any of these checks fails. It may record the 5c release identity, source
identity, corpus identity, and compatibility version as provenance for its own deterministic Rules
Package.

Merely because it loads an approved release, 5d must **not** reconstruct and re-hash the full source
ledger, reconciliation member, policy chain, canonical bundle, or evidence report; prove that every
historical identity was mathematically derived from every recorded predecessor; compare diagnostic
report summaries against a newly reconstructed publication history; or rerun coherent-rewrite or
adversarial mutation controls.

*Amended 2026-08-03.* The 2026-08-01 decision as drafted also required the gate to "reconstruct and
re-prove all SQLite-authoritative corpus state that seam exposes." That requirement is prospectively
superseded: it made every downstream load a re-execution of 5c's historical publication proof, which
CRD Issue 5c no longer promises. Fresh 5c publication and 5c verified reuse may still perform stronger
internal checks where they cheaply support an operational outcome; those checks do not automatically
become downstream obligations. See
[CRD Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md) §5.

**Chroma — preserved exactly (2026-08-01).** The 5d gate **does not** open or depend on ChromaDB to
recompute the vector-backed portion of the 5c persisted-corpus digest. Chroma remains an informational,
rebuildable projection and is not mechanical authority (ADR-018 D4/D10). Loss, corruption, or absence of
the live rules-corpus vector collection after successful 5c publication is a CRD Issue 18
operational/reindex defect; it does not make the 5c source authority stale for 5d publication.

This does not weaken CRD Issue 5c. Fresh 5c publication and 5c's own verified-reuse path must continue
to write, read back, and verify the required vector projection before declaring a 5c release published
or reusable.

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

**Amended by Owner Decision 2026-08-08.** The "complete validated payload" every canonical override entry
already carries explicitly covers a prose-authority payload: the complete authored text of a `REPLACE` or
`APPEND` against prose authority, or the empty payload of a `DISABLE`. Changing that authored text changes
the override-set UUID exactly as changing any other enumerated field does; it never changes
`mechanical_projection_uuid`. Prose authority is targeted at the same grain as a component — stable record
and component identity — but is a distinct target kind (Decision 10), so a prose operation and a component
operation against the same record/component pair are two different targets and never collide.

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

**Amended by Owner Decision 2026-08-08 — a first-class authored-authority prose overlay.** `DISABLE`,
`REPLACE`, and `APPEND` now also apply to prose authority: a fourth typed target grain scoped by stable
record and component identity, never a raw chunk, a JSON path, or an unscoped selector. Their existing
meanings extend without changing:

- `DISABLE` on prose authority suppresses that exact component's effective governing prose without
  deleting its base state or altering its typed facts. What that leaves the component's *effective*
  handling as depends on what survives — see the effective-content classification below — not on what the
  component's handling was before the disable.
- `REPLACE` on prose authority replaces the target's complete effective governing prose with exact
  authored prose, superseding both the base projection's 5c-bound prose and any previously applied
  authored prose for that target, resolved in the same ascending `(precedence, override_id)` order every
  other override uses. It also clears any source-derived irreducibility reason the component carried: that
  reason was the base corpus's judgement about the source prose this operation just discarded, and keeping
  it would be exactly the copied irreducibility claim the non-fabricated-provenance rule below forbids.
  `APPEND` and `DISABLE` leave the reason untouched — `APPEND` only adds to existing governing prose, so
  any source prose the reason describes remains effective, and `DISABLE`'s reason-preserving behavior on a
  now-empty `PROSE_BOUND` component is the named exception directly below.
- `APPEND` on prose authority preserves the target's existing effective governing prose — 5c-bound,
  previously authored, or both — and adds one more authored passage after it, in that same order.

Effective governing prose is represented as a closed discriminated form distinguishing at least:

- **source prose** — an exact `chunk_id` and its resolved 5c text; and
- **authored prose** — exact text plus the supplying override's stable identity and origin.

Authored prose is never assigned a fake `chunk_id`, 5c span provenance, or an irreducibility claim copied
from the base source; its provenance is the authored override and the retained override-set version
(Decision 9). Attaching authored prose to a component the base projection classified `STRUCTURED` — which
by definition carries no prose binding — makes that component's *effective* handling `MIXED` in every view
built from it, honestly reflecting that structured facts and authored prose now coexist; the immutable base
projection's own `STRUCTURED` classification and identity are untouched. Complete component additions or
replacements (this decision's existing `REPLACE`/`APPEND` component and record patches) may declare
`PROSE_BOUND` or `MIXED` handling and carry authored prose where their own closed schema permits it, under
the same non-fabricated-provenance rule.

**Amended by Owner Decision 2026-08-09 — final effective-state classification, not historical/sticky or
path-dependent.** An earlier draft of this decision stated that a `DISABLE` of prose authority "does not
demote" an effective `PROSE_BOUND` or `MIXED` component's handling, including a `MIXED` promotion an
earlier override in the same resolved set produced. That was wrong and is superseded:
`EffectiveComponent.handling` describes the authority surviving *after* ordered override application, not
authority that existed earlier in the sequence. It is a classification of each component's own final
`facts` and `governing_prose`, computed once at final assembly, for every component alike — whether its
authority came from a prose operation, a whole-component or whole-record `REPLACE`/`APPEND` declaring
`handling` directly, or the immutable base projection — never remembered as a sticky flag and never
dependent on which of those override families supplied the authority or which operation resolved last.
Concretely, for every component with surviving facts or surviving prose after override application:

- effective facts plus effective prose → `MIXED`;
- effective facts without effective prose → `STRUCTURED`;
- effective prose without effective facts → `PROSE_BOUND`.

A component left with neither is not content-bearing; classifying that state is out of this decision's
scope. The one settled exception is a prose-only component whose sole prose authority is suppressed: it
remains `PROSE_BOUND`, with an empty effective prose surface, because no other category honestly describes
a component with no typed facts — this is the component's already-declared handling, unmutated by the
suppression itself, so it is unaffected by whether the prose or a sibling fact was suppressed first.

So `STRUCTURED → authored prose → MIXED → DISABLE prose` finishes `STRUCTURED`, and a `MIXED` component —
however its facts and prose were supplied — whose prose is suppressed while its facts survive finishes
`STRUCTURED` the same way; a `MIXED` component whose facts are removed while its prose survives finishes
`PROSE_BOUND` the same way. A promotion to `MIXED` is never sticky, and none of this depends on the order in
which the surviving facts and prose were established. This classification affects only the effective
runtime view: the immutable base projection's own classification and identity, and every applied-override's
provenance, are unaffected either way. It does not loosen the unchanged suppression rule directly above — a
later override aimed at the *exact same* already-disabled prose target still does not apply; re-promotion
after a suppression can only come from a different target (a whole-component or whole-record replacement
clears the stale suppression for the semantic key it replaces, exactly as it already does for facts and
components).

This discharges ADR-005d's blanket prohibition on a second prose store (recorded in this ADR's implementing
code — `patches.py`'s prior docstring — and in #137 contract 3, rather than as a prior Decision clause in
this document). The narrower invariant is: there is
no duplicated store for what the SRD source says. 5c source prose remains immutable, resolves only from its
exact `RuleChunk`, and is never copied and relabeled as source authority. A separately identified
authored-authority overlay — carrying its own distinct provenance and never claiming 5c provenance — is
intentional and is exactly what this amendment adds.

Legacy chunk-targeting overrides (the pre-existing `rp_overrides` prose path) remain a distinct, obsolete
pre-release mechanism. They are not a second concurrent mechanical or GameMaster truth: the typed authority
path and views this ADR governs never read them, and their removal remains scheduled for the final
activation/legacy-retirement PR, not the PR that introduces this overlay.

**Amended by Owner Decision 2026-08-19 — an APPEND-only `OPTION` container target.** Representation
schema 2 admits a component that states an exhaustive actor choice: one whose meaning is a set of mutually
exclusive `options`, each holding its own typed facts. That structure created a multiplicity seam this
decision's `APPEND` clause above could not address. A component-scoped `APPEND` adds a fact *beside* the
options, which a choice component's schema forbids, and `(APPEND, FACT)` has never been permitted — so
adding a typed fact to one arm of a choice was a schema-permitted operation with no valid encoding. This
amendment supplies exactly that encoding and nothing more:

- `OPTION` is a **fifth exact typed target grain**, shaped by `record_key`, `component_key`, and a
  nonblank `option_key`, with `fact_key` **forbidden**. It is scoped by stable semantic identity like
  every other grain — never a JSON path, an index, or an unscoped selector — and a container together
  with one of its members is two targets, not one.
- It targets an option **only as the owning container for fact addition**. `OPTION` is not a general
  handle on a choice arm.
- Only `(APPEND, OPTION) → FactAdditionPatch` is permitted. Every other operation/`OPTION` pairing fails
  explicitly as an invalid override, exactly like any other unsupported typed pairing.
- `DISABLE` and `REPLACE` on `OPTION` remain **unsupported**, and deliberately not for the same reason
  `(APPEND, FACT)` is. An option is not missing multiplicity — it holds content that could in principle
  be suppressed or replaced. It is the **exhaustiveness** of the choice that forbids it: the source states
  these options as the complete set of what the actor may do, so removing or rewriting one arm would
  publish a choice the source never authored. That is a falsification of source authority, not a
  permitted narrowing of it.
- `APPEND` on `FACT` remains unsupported on its original grounds, unchanged by this amendment: a fact has
  no multiplicity to append into.

An option is therefore addressable as a fact container and in no other way.

This amendment is **runtime-only and identity-narrow**. `OPTION` reuses the existing `target_option_key`
column that already carries an option-qualified `FACT` target's scope; it introduces no second scope
field. Because a target's exact identity participates in the override-set payload (Decision 9), an
`OPTION` target changes the override-set identity of any state containing one — as any new authority
must. It leaves **every existing direct-target canonical payload and every already-derived override-set
identity unchanged**, so no previously recorded binding is reminted or orphaned from the retained version
it names. It does **not** change representation schema identity: `OPTION` is an override target grain, not
a representation structure, and the representation schema version and hash are unaffected.

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

**Operational reliability amendment (2026-08-03).** ADR-005c is amended prospectively so that CRD Issue
5c is judged by operational reliability rather than adversarial or forensic proof. For 5d this changes
one thing only: the downstream trust boundary in Decision 8, which now verifies the narrow 5c-owned
operational seam instead of reconstructing 5c's complete publication-proof graph. 5d's own ownership is
unchanged — typed interpretation, deterministic Rules Package construction, fail-closed publication, and
provenance all stand. See
[CRD Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md).

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
- A house rule or package-patch author can supply exact authored governing prose through the same typed,
  provenance-exact override path as any other mechanical patch, without corrupting or duplicating 5c
  source authority (Owner Decision 2026-08-08).

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
- An effective component's governing prose can now be a mix of immutable 5c-bound passages and
  mutable-until-retained authored passages, ordered by the same precedence rule as every other override;
  operators and auditors reason about one more provenance-exact case (Owner Decision 2026-08-08).

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
14. **Integrate authored prose through the legacy `rp_overrides` chunk-targeting path.** Rejected by Owner
    Decision 2026-08-08: that path targets a raw chunk directly, which is exactly the raw-chunk/unscoped-
    selector targeting this ADR's typed override system exists to replace, and it would leave two
    concurrent, differently-shaped override mechanisms both claiming to patch mechanical authority.
    Authored prose extends the same typed record/component/fact target system instead, at a fourth grain
    scoped by stable record and component identity.
15. **Give authored prose its own irreducibility reason from the closed 5c catalog.** Rejected: that
    catalog exists for 5c's build-time semantic classification of *source* text (Decision 2), a judgment an
    override author is not making. An override-supplied component's `irreducibility_reason_code` stays
    `None`, so it can never be confused with, or copied from, a base-projection classification.

---

## Implementation Authority

The construction-ready CRD Issue 5d specification governs required outcomes, scope, architectural
boundaries, failure behavior, and acceptance evidence. Repository-native schema, module organization,
internal decomposition, implementation phases, migration design, and test organization remain engineering
decisions unless this ADR or the Issue explicitly makes a particular choice contractual.

If implementation discovers a materially better architecture that contradicts this ADR, amend the ADR and
the affected specification in advance of, or in the same PR as, the implementation. Do not merge a quiet
contradiction.
