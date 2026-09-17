# CRD Issue 5d — Complete Typed Mechanical Authority and Deterministic Rules-Package Binding

> **Status:** Accepted — practical reliability amendment adopted by Owner 2026-09-16.
> Owner decision: “I approve adopting this policy in CRD Issue 5d and ADR-005d.”
> This complete issue text is coordinated with the amended [ADR-005d](../decisions/adr-005d-complete-typed-mechanical-authority.md).
> Implementation remains in progress. Policy adoption does not accept new corpus content or authorize
> publication, activation, or merge. The original issue was finalized on 2026-07-30;
> the adopted changes are incorporated directly below and into ADR-005d.
> See the [Speed comparison and delivery sequence](issue-5d-speed-comparison.md).
>
> **Amended by Owner Decision 2026-07-30 (PR #138 review):** the effective runtime `RulesPackageBinding`
> also carries an immutable, versioned override-set identity for the exact applied override set, distinct
> from the immutable base mechanical-projection identity. See ADR-005d Decisions 6, 8, 9, and 10. No other
> 5d architecture is reopened.
>
> **Clarified in the same review (2026-07-30):** each `override_set_uuid` is the content-derived identity
> of one immutable, replayable override-set version whose exact canonical ordered contents are retained as
> replay evidence. Recording the identity while retaining only mutable current override rows is
> insufficient. The effective binding is **provenance-exact**: the retained version identifies both the
> exact effective mechanical state applied and the exact authoritative override records — identity and
> origin included — that supplied it. This clarifies the correction above and the standing auditability
> invariant; it is not a further architecture decision.
>
> **Amended by Owner Decision 2026-08-08:** a runtime prose-bound override now resolves through a
> first-class authored-authority prose overlay — a distinct runtime authority layer with its own
> provenance — rather than through the legacy `rp_overrides` chunk-targeting path. This narrows contracts 3
> and 6 and ADR-005d Decisions 3, 6, 9, and 10 from a blanket prohibition on a second prose store to the
> narrower invariant that there is no duplicated store for what the SRD source says: 5c source prose
> remains immutable and resolves only from its exact `RuleChunk`. No other 5d architecture is reopened;
> this is not the production-corpus authoring PR or the final activation/legacy-retirement PR, and the
> legacy chunk-targeting path remains scheduled for removal there, not here.
>
> **Depends on:** completed CRD Issue 5c; ADR-005c; ADR-0007; ADR-015; ADR-018.\
> **Unblocks:** CRD Issue 2b, then CRD Issue 15c.\
> **Remains frozen:** #129 disposition, CRD Issue 15b Phase 3, and CRD Issue 19b until their controlling
> prerequisites are complete.

---

## Outcome

For one exact published CRD Issue 5c Rules Package release, build and publish one immutable,
provenance-exact mechanical-authority projection that accounts for the complete mechanically substantive
SRD 5.2.1 corpus.

Every substantive rule component must be represented by:

- typed declarative facts required by an identified code-owned use in play, explanation, or correction;
- exact governing prose for remaining rule meaning, including judgment and reducible meaning without
  an identified need for separate fields; or
- both.

The resulting projection must be deterministic to build, persist, reconstruct, identify, publish, query,
and audit. Missing required review, uncovered rules, unresolved ambiguity, stale identity, incomplete
persistence, unresolved references, or mismatched releases fail explicitly.

Publication proves **complete mechanical representation**. It does not certify that every represented
component is executable by the bounded-d20 Rules System Adapter.

---

## Governing Authority

[ADR-005d](../decisions/adr-005d-complete-typed-mechanical-authority.md) governs this issue.
The Owner-adopted 2026-09-16 policy is incorporated directly into this complete issue text and the
corresponding ADR decisions; no separate policy overlay is required.

The core authority split is:

- the **Rules Package projection** represents the complete mechanically substantive source;
- the **Rules System Adapter** executes only component shapes it explicitly supports; and
- the **GameMaster** uses exact governing prose and structured context to explain rules and adjudicate
  contextual or open-ended components from the Sojourner's declared use. Choosing prose representation
  does not make a fixed rule discretionary or certify its execution.

Free-form GameMaster output never becomes authoritative mechanical state. A later adjudicated outcome may
cause a mechanical mutation only through a typed, code-validated path owned downstream.

---

## Scope

### In scope

- Semantic accounting over one exact published 5c release.
- Accepted record assembly and component classification.
- Closed typed declarative fact families and exact prose-bound authority.
- Exact many-to-many provenance from records, components, facts, prose bindings, and references to 5c
  leaf subspans.
- Immutable projection identity, persistence, reconstruction, completeness proof, and atomic publication.
- Build-time reference resolution.
- Deterministic Rules Package binding and rule-slice selector construction.
- Typed deterministic-consumer and GameMaster-facing authority views.
- Typed record/component/fact `RuleOverride` application with existing precedence semantics.
- A first-class typed prose-authority override target, scoped by stable record and component identity,
  carrying authored text as a distinct runtime authority layer (Owner Decision 2026-08-08).
- Removal of the obsolete prose-only `MechanicalEntity` authority path.

### Out of scope

- Changes to 5c extraction, leaf segmentation, containers, reconciliation, publication, or identity.
- Generated executable mechanics, a runtime rules language, a generic rules engine, or a cross-system
  plugin framework.
- Bounded-d20 adapter implementation, capability declaration, or certification.
- Character Sheet Model completion or binding-storage decisions.
- Downstream application of a GameMaster-selected mechanical effect.
- ChromaDB, embeddings, semantic retrieval, model recollection, or similarity ranking as mechanical
  authority.
- Changes to `RuleOverride` precedence or the meanings of `DISABLE`, `REPLACE`, and `APPEND`.
- Any work on the frozen #129 / CRD Issue 15b Phase 3 / CRD Issue 19b paths.

Mechanical canon remains structurally separate from Story Bible canon, character/session state,
resolution events, retrieval indexes, and adapter behavior.

---

## Required Contracts

### 1. Exact source binding and population

A projection binds to reconstructed published 5c state, including at minimum:

- `package_uuid`;
- `release_version`;
- authoritative-source hash;
- transform/configuration hash;
- canonical corpus-bundle root hash; and
- persisted-corpus digest.

A matching slug, display name, source label, or filename is insufficient.

**Amended by Owner Decision 2026-08-01, as further amended 2026-08-03 (CRD Issue 5c Operational
Reliability Amendment).** The persisted-corpus digest stays part of the exact binding, with its 5c
meaning unchanged. Downstream 5d verification establishes, through the narrow 5c-owned operational
trust seam: that the requested release exists and is marked published; that the release identifier and
package/release relationship are internally consistent; that the release identifies the expected
authoritative source and corpus; that the authoritative SQLite corpus state being supplied matches the
approved release's recorded persisted-corpus identity through a **direct operational integrity
check** — not merely because an evidence-report hash matches; that the corpus records 5d needs are
present and reachable through the approved authoritative seam; and that the release uses a corpus
contract or schema version supported by the 5d transformation. 5d fails closed on any failure.

5d does **not**, merely because it loads an approved release, reconstruct and re-hash the full source
ledger, reconciliation member, policy chain, canonical bundle, or evidence report; prove that every
historical identity was derived from every recorded predecessor; compare diagnostic report summaries
against a newly reconstructed publication history; or rerun coherent-rewrite or adversarial mutation
controls. The requirement to prove "the reconstructable SQLite-authoritative corpus state exposed by
the 5c-owned verification seam" is prospectively superseded.

The live Chroma collection is **not** reopened as a prerequisite for publishing mechanical authority:
Chroma is an informational, rebuildable projection, not mechanical authority (ADR-018 D4/D10). Missing
or corrupt Chroma after a successful 5c publication is a CRD Issue 18 rebuild/operations defect, not
stale mechanical source authority. 5c publication and 5c verified reuse retain their own cross-store
verification obligation. See ADR-005d Decision 8 and
`docs/decisions/adr-005c-operational-reliability-amendment.md` §5.

The source population is the complete set of 5c leaves whose final disposition is `REPRESENTED`.
Derive it from the bound release. The review inventory groups this source into meaningful sections,
entries, and tables with exact source membership; it must not omit source regions. Discovery counts
are regression canaries, not hard-coded authority. 5c exclusions remain governed by 5c and are not
reclassified here. Source membership does not require separate human classification of every fragment.

### 2. Reviewed rule coverage and handling

Review meaningful sections, entries, or tables against an inventory covering the bound source.
Expected entries, table rows, rules, qualifications, and exceptions come from source review, not from
whatever a generator emitted. Inventory gaps, unreviewed units, unresolved rules, and missing expected
rules block publication. A review unit need not become a record or component.

Each reviewed unit distinguishes actual rules, useful supporting text, and material excluded from
mechanical authority. Every actual rule has an accepted home in structured data, exact governing prose,
or both. Supporting text links to the rules it explains. Non-mechanical material may be excluded in
coherent groups with an accepted reason, without separate rows for each word or extracted fragment.
This supersedes mandatory gap-free semantic partitioning of every represented leaf. Existing accepted
partitions remain valid; they are not rewritten to match the new review method.

Review state is separate from meaning. Proposals remain unaccepted until an explicit, reviewable
acceptance action records the actual proposal, resolved scope, and meaning changes. Silence and a
successful tool run are not acceptance. Source references remain exact and resolvable.

Licensing, navigation, pure flavor, and non-rule guidance can be excluded from mechanical authority.
Headings, examples, cross-references, advice, and repeated wording are not blanket exclusions: preserve
any rule, qualification, exception, or useful explanation they carry. Repeated statements may share a
rule representation with their relevant source links; preserve differences in scope and effect.

Every publishable component has one handling disposition:

- `STRUCTURED` — represented by closed typed facts and relationships;
- `PROSE_BOUND` — exact governing prose preserves the rule meaning;
- `MIXED` — both coexist.

A new field or family requires an identified code-owned use in play, explanation, or correction and
a concrete consequence of omission. Planned v1 uses count even before their consumers are implemented.
Reducibility alone, speculative extensibility, and the adapter's current capability are insufficient.
Apply the Owner's three questions to kinds of work; do not create a form for every passage or row.

A prose choice must record its actual reason: judgment required, or no identified need for a separate
structured representation. These reasons require an explicit versioned policy/schema transition where
necessary. Never label reducible meaning with an old irreducibility code. Preserve old reason meanings
and accepted inputs. Prose is governing authority, not merely citation; it cannot be a default for
unreviewed content or conceal a missing field needed by an identified operation.

Choosing prose does not authorize runtime interpretation into trusted values. Required numeric or
other mechanical inputs still reach consumers through typed, code-validated paths. 15c retains
ownership of any validated application path for GameMaster-selected effects.

### 3. Mechanical records, components, facts, and provenance

The projection must support stable semantic records assembled from accepted source membership rather than
assuming one 5c `ENTRY` equals one mechanical entity. It must handle:

- simple entry-backed records;
- composite records such as stat blocks assembled from anchors, sibling sections, and table cells;
- non-entry rules and free-standing tables; and
- nested records, including complete creature stat blocks embedded in spell authority.

Record membership is declared by accepted semantic assembly; runtime heuristics do not become authority.
Records, components, and facts use stable semantic keys and release-scoped identities. Positional ordinals
must not determine identity; inserting an unrelated sibling must not churn existing identities.

The closed record vocabulary must cover the mechanically substantive SRD domains, including general and
glossary rules, character creation/advancement, classes/features, species/backgrounds/feats, equipment,
spells, conditions, gameplay tools/tables, magic items, and creature stat blocks using `CREATURE` as the
record kind. `Animals` and `Monsters A–Z` remain source ancestry, not separate record kinds; rules-defined
creature type remains a distinct descriptor.

Structured authority uses a closed discriminated union. Source review and identified consumer uses
jointly determine which fields are required. Review the following domains for those needs; this list
is not a mandate to create every conceivable distinction or field in advance:

- **identity and relationships:** typed references, membership/classification, prerequisites,
  eligibility, choices, sequencing, dependencies, scaling, and progression;
- **roll and resolution:** dice, attacks, saves, checks, contests, DC sources, advantage/disadvantage,
  critical changes, explicit probability, and random-table selection;
- **timing, targeting, and space:** action economy, triggers, reactions, range/reach/area/origin,
  targeting restrictions, duration/concentration, recurrence, and movement;
- **effects and state:** damage, healing, resistances/immunities/vulnerabilities, conditions, resources,
  recharge/rest cadence, and typed state effects;
- **domain descriptors:** spell, creature/stat-block, equipment, class, species, background, feat, and
  level-progression authority.

If an identified structured use cannot be represented by the current union, add a specific typed
family before that use relies on it. Otherwise preserve the rule as exact governing prose with an
honest reason under contract 2. Do not use untyped dictionaries, generic numeric/key-value attributes,
arbitrary expressions, or free text while claiming structured coverage.
Missing source values are never invented.

Every component, fact, prose binding, relationship, and resolved reference must trace through exact 5c
leaf/subspan provenance. Primary claims and contextual support are distinct. Contextual overlap is
allowed; conflicting primary claims fail unless an explicit closed policy permits them. Exact governing
prose resolves through the authoritative 5c `RuleChunk` source rather than creating a second store for what
the SRD source says.

**Amended by Owner Decision 2026-08-08.** This prohibition binds the base projection's own prose bindings:
they resolve exclusively to 5c leaf subspans, never to a fabricated chunk, and are never duplicated into a
second copy of source authority. It does not prohibit a distinct runtime authored-authority prose overlay
(contract 6) that carries its own override-identity provenance and never claims 5c provenance, span
identity, or an irreducibility reason copied from the base source.

### 4. Accepted semantic inputs, reference resolution, and identity

The production build consumes committed, accepted, meaning-bearing inputs that cover:

1. semantic policy and canonicalization;
2. the accepted source-review inventory and rule/support/exclusion decisions, including retained
   historical classification ledgers;
3. accepted record assembly and membership;
4. accepted components, facts, prose bindings, obligations, and provenance claims; and
5. accepted source-reference scope, aliases, and exact targets.

Tools may propose these inputs, but publication must compare persisted output against accepted
expectations reviewed independently against the source. Expectations must never be regenerated from
the output they check. Independence does not require a second handwritten acceptance implementation
per batch. Reuse common loaders and validators; test concrete failures rather than a helper's
agreement with itself. The entire build must be reproducible from a clean checkout without local-only
files, unrecorded model output, or manual database edits.

Projection identity binds the exact 5c release and the complete accepted meaning-bearing payload:
review inventory and coverage decisions, classification, record assembly, components, facts, prose
bindings, provenance, relationships, resolved references, schemas, policies, normalization, and
canonicalization. Meaning changes mint a new projection UUID. Reviewer names, timestamps, comments,
and proposal origins remain audit metadata and do not change
semantic identity unless accepted meaning changes.

Source-authored mechanical references resolve at build time through committed source scope, aliases, and
exact target semantic keys. Bare names, runtime similarity, or model selection are never authoritative.
Ambiguous, unresolved, invalid, or cross-release references block publication.

### 5. Persistence, completeness proof, and publication

The lifecycle is:

```text
build candidate
→ persist draft
→ reconstruct from persisted state
→ compute persisted-state digest
→ run exact completeness gate
→ atomically publish
```

Persist enough typed or canonically validated state to reconstruct the complete projection and its proof.
An opaque JSON blob alone is insufficient. Active readers must never observe a partial draft. Published
projections are immutable; meaning-changing corrections *to the projection itself* mint a new projection
UUID, while override changes mint a new override-set identity and leave the projection UUID untouched
(contract 6). Concurrent identical builds are idempotent, and activation cannot split between competing
projections.

**Amended by Owner Decision 2026-08-01, as further amended 2026-08-03 (CRD Issue 5c Operational
Reliability Amendment).** Before publishing, the completeness gate must establish the bound 5c release
through the narrow 5c-owned operational trust seam: the release exists and is marked published; its
identifier and package/release relationship are internally consistent; it identifies the expected
authoritative source and corpus; the authoritative SQLite corpus state matches the approved release's
recorded persisted-corpus identity through a direct operational integrity check; the corpus records 5d
needs are present and reachable; and the corpus contract/schema version is supported by the 5d
transformation. Missing, mismatched, unpublished, or corpus-inconsistent release state is rejected and
the gate fails closed.

The former requirement of "reconstruction and re-proof of all SQLite-authoritative corpus state that
seam exposes" is prospectively superseded — it made every downstream load a re-execution of 5c's
historical publication proof, which CRD Issue 5c no longer promises. Fresh 5c publication and 5c verified
reuse may perform stronger internal checks; those do not become downstream obligations.

The gate does not open ChromaDB or recompute the vector-backed portion of the digest. See ADR-005d
Decision 8 and `docs/decisions/adr-005c-operational-reliability-amendment.md` §5.

Override-set versions are retained separately from this projection lifecycle and are not part of the
publication gate. Each `override_set_uuid` is the content-derived identity of one immutable, replayable
override-set version that preserves — or is deterministically reconstructable from append-only retained
evidence that preserves — the exact canonical ordered override state it was derived from. That state is
provenance-exact and includes, per override entry:

- stable override identity (`override_id` or its repository-native successor);
- override origin (`house_rule`, `package_patch`, or its typed successor);
- exact typed target identity;
- operation;
- precedence/order;
- enablement state; and
- complete validated payload.

Historical override-set versions remain retrievable after the source `RuleOverride` rows are edited,
disabled, reprioritized, retargeted, or deleted. The version may be retained as a content-addressed
snapshot, as append-only version records, or as append-only events that deterministically reconstruct the
canonical version; an event log need not itself be content-addressed, but its reconstructed canonical
version must reproduce and verify the recorded `override_set_uuid`. The repository-native design is an
implementation choice.

Identity is not broadened to incidental audit metadata: creation timestamps, authors, comments, and
proposal history remain non-identity audit metadata unless they participate in override applicability,
ordering, or resolution. The enclosing package UUID already supplies package scope.

The publication gate must prove, against reconstructed persisted state and independent accepted inputs:

- exact 5c binding and source-inventory membership covering the source population;
- accepted review of every inventory unit, with no unresolved or missing expected rule;
- no proposed or incomplete authority represented as accepted;
- every expected rule, qualification, and exception represented in accepted fields or governing prose;
- retained supporting material context-linked and excluded groups given an accepted reason;
- every prose-bound portion supplied with exact prose and an honest accepted handling reason;
- every accepted per-record/component obligation satisfied exactly;
- no unexpected record, component, fact, edge, prose binding, or reference outside accepted inputs;
- exact record assembly;
- valid provenance, overlap, reverse links, and reference closure;
- conformance to the closed typed fact union;
- matching semantic root, derived identities, and persisted digest; and
- one atomic active publication with no reachable partial state.

Aggregate counts, extraction floors, percentages, and prose ceilings may detect drift but never prove
completion. Focused failure tests must reject omitted rules/exceptions, missing fields required by a
named operation, invalid source links, reference-only substitutes for rule content, duplication used
as coverage, changed source or stored payload under unchanged identity, unaccepted input, and partial
publication. Prose is not under-extraction merely because it could be structured. Use shared tests for
shared behavior and content-specific tests for actual exceptions. Further negative controls must prove that:

1. deleting and recreating the same semantic patch under a different `override_id` changes the
   override-set identity;
2. changing only `override_origin` — for example from `house_rule` to `package_patch` — changes the
   override-set identity;
3. a previously recorded effective binding reconstructs the exact identities, origins, order, targets,
   operations, enablement state, and payloads originally applied, after the underlying current override
   rows are modified or deleted; and
4. mutable current override rows cannot substitute for retained provenance evidence — an implementation
   that retains only the `override_set_uuid` and re-derives from current rows fails.

Mechanical authority operations must distinguish at least:

`ABSENT`, `AMBIGUOUS`, `UNRESOLVED`, `UNREVIEWED`, `INCOMPLETE`, `STALE`,
`MISMATCHED_RELEASE`, `INVALID_SELECTOR`, `INVALID_REFERENCE`, `INVALID_OVERRIDE`, and `UNPUBLISHED`.

These states must not collapse to `None`, empty results, generic exceptions, retrieval fallback, or model
inference. In runtime resolution and adjudication, `STALE` and `MISMATCHED_RELEASE` cover divergence of
the complete effective binding, including an override-set identity that no longer matches the identity
recomputed from current override state — not release mismatch alone. Audit, replay, and provenance reads
are the distinct case: they resolve against the retained override-set version and must succeed, so
`STALE` is not a valid result there and a failure to reconstruct is a retention defect.

### 6. Runtime binding, authority views, overrides, and legacy retirement

Expose an immutable effective binding equivalent to:

```text
RulesPackageBinding(package_uuid, release_version, mechanical_projection_uuid, override_set_uuid)
```

Base-projection identity and override-set identity are distinct and are never collapsed into one value.
The binding is provenance-exact: `override_set_uuid` identifies both the exact effective mechanical state
applied and the exact authoritative override records that supplied it. It is derived deterministically at
binding-resolution time from the canonical ordered effective override state that will be applied — per
entry, stable override identity, override origin, exact typed target identity, operation, precedence/order,
enablement state, and complete validated payload (contract 5). Adding, removing, enabling, disabling,
reprioritizing, retargeting, or changing an override payload must yield a different `override_set_uuid`,
and so must deleting and recreating an otherwise identical override under a different `override_id` or
changing only its `override_origin`: a house rule and a package patch with identical mechanical contents
are not the same provenance-exact authority. The no-overrides state has its own deterministic identity
rather than the absence of one. Overrides never mutate or remint `mechanical_projection_uuid`.

Each `override_set_uuid` is the content-derived identity of one immutable, replayable override-set version
whose exact canonical ordered contents are retained as replay evidence under contract 5. Current
`RuleOverride` rows may remain the authoring surface, but they are not historical replay evidence, and
recording the identifier while retaining only those mutable rows is insufficient.

Human-facing slugs may resolve through one code-owned service, but runtime authority uses the exact typed
effective binding.

Extend the existing `RuleSliceRequest` / `get_active_rule_slice` production path rather than replacing it
without cause. Every request must carry the exact effective binding plus deterministic record/component
selectors, or explicitly set `whole_package=True`. An empty selector set without that flag is
`INVALID_SELECTOR`. The existing fail-open slug/UUID and accidentally-empty selector paths must have no
surviving caller.

Provide two exact source-linked read surfaces:

1. a typed mechanical view for deterministic consumers, including applied override provenance; and
2. a GameMaster authority view combining exact governing prose with structured context and handling.

Both views, every rule slice, and all replay/audit evidence must identify the exact effective binding —
all four components — that produced them. Neither view implies adapter capability. Retrieval may locate
candidates for the GameMaster view, but the returned authority must resolve to exact bound identities and
cannot supply or select a mechanical value.

Complete typed `RuleOverride` application while preserving existing precedence and operation semantics:

- `DISABLE` targets a record, component, or fact, suppresses that exact target, and stops later applicable
  processing under the existing precedence rule without deleting base authority;
- `REPLACE` supplies a complete schema-valid component or fact replacement;
- `APPEND` adds a complete typed component or fact through an allowed record/component multiplicity seam.

Patch payloads must be closed and target-family-specific. Generic JSON paths, key/value patches, arbitrary
expressions, or raw strings cannot patch structured authority. Record-level replacement is allowed only
through an explicit record-kind-specific patch contract, never a generic whole-record overwrite. Existing
chunk-targeting prose overrides remain distinct from typed mechanical patches. Invalid, stale, ambiguous,
cross-release, or type-incompatible patches fail explicitly. The effective view records ordered override
provenance against the `override_set_uuid` that produced it, resolved through the retained override-set
version rather than current override rows; the immutable base projection and its identity do not change.
At runtime, a recorded binding whose `override_set_uuid` no longer matches the identity recomputed from
current override state is `STALE` and fails explicitly rather than being silently re-resolved against
current overrides. For audit and replay, that same recorded binding must instead reconstruct the exact
effective mechanical authority originally applied — including after the source override rows are edited,
disabled, reprioritized, retargeted, or deleted — not merely report that it differs from current state.
That provenance is provenance-exact: it names the stable identity and origin of each applied override, not
only the mechanical change it produced.

**Amended by Owner Decision 2026-08-08 — a first-class authored-authority prose overlay.** `DISABLE`,
`REPLACE`, and `APPEND` now also apply to prose authority: a typed target grain scoped by stable record and
component identity, never a raw chunk, a JSON path, or an unscoped selector. `REPLACE` on prose authority
replaces the target's effective governing prose with exact authored prose; `APPEND` preserves the existing
effective prose and adds authored prose in deterministic precedence order; `DISABLE` suppresses the exact
targeted prose authority without deleting base state. On a `MIXED` component, prose operations do not
silently alter its typed facts. Adding authored prose to a component the base projection classified
`STRUCTURED` must produce an honest effective `MIXED`/prose-bearing view rather than smuggling prose into a
typed fact; the base projection's own `STRUCTURED` classification and identity are untouched.
As settled by ADR-005d on 2026-08-09, effective handling is derived once at final assembly from each
component's own surviving facts and prose, for every component and regardless of the last operation.
It is not a sticky promotion; removal of effective prose can leave a structured component again.
Complete component additions or replacements may contain authored prose where their closed schema
permits it. Blank, malformed, ambiguous, missing-target, cross-release, type-incompatible, or unsupported
prose patches fail explicitly as invalid overrides, exactly like any other typed override.

Represent effective governing prose as a closed discriminated form distinguishing at least: source prose
(exact `chunk_id` and resolved source text) and authored prose (exact text plus supplying override identity
and origin). Authored prose is never given a fake `chunk_id`, 5c span provenance, or an irreducibility
claim copied from the base source; its provenance is the authored override and the retained override-set
version. Runtime stale detection, applied-override provenance, and replay from a recorded binding continue
to work after the current prose override is edited, disabled, reprioritized, retargeted, or deleted — the
same replay guarantee contract 5 already requires of every other override.

The pre-existing free-form session `house_rules` string is not silently promoted into trusted mechanical
authority by this contract. Any future UI or conversion into an authored overlay must use an explicit
validated authoring path through this typed override system, not an implicit one.

This narrows the second-prose-store prohibition above and in contract 3 to the invariant that there is no
duplicated store for what the SRD source says. Legacy chunk-targeting prose overrides remain an obsolete
pre-release path, not a second concurrent mechanical truth, and remain scheduled for removal at final
cutover, not in the PR that introduces this overlay.

**Amended by Owner Decision 2026-08-19 — an APPEND-only `OPTION` container target.** Representation
schema 2 admits a component whose meaning is an exhaustive actor choice: a set of mutually exclusive
`options`, each holding its own typed facts. Adding a typed fact to one arm of such a choice had no valid
encoding — a component-scoped `APPEND` adds a fact beside the options, which a choice component's schema
forbids, and `APPEND` on a `FACT` target has never been permitted. This amendment supplies exactly that
encoding:

- `OPTION` is a fifth exact typed target grain, shaped by `record_key`, `component_key`, and a nonblank
  `option_key`, with `fact_key` forbidden. Scoped by stable semantic identity like every other grain,
  never a JSON path, an index, or an unscoped selector.
- It targets an option only as the owning container for fact addition, never as a general handle on a
  choice arm.
- Only `(APPEND, OPTION) → FactAdditionPatch` is permitted. Every other operation/`OPTION` pairing fails
  explicitly as an invalid override, exactly like any other unsupported typed pairing.
- `DISABLE` and `REPLACE` on `OPTION` remain unsupported, and not for the reason `APPEND` on `FACT` is.
  An option is not missing multiplicity; it holds content that could in principle be suppressed or
  replaced. It is the exhaustiveness of the choice that forbids it: the source states these options as the
  complete set of what the actor may do, so removing or rewriting one arm would publish a choice the
  source never authored — a falsification of source authority rather than a permitted narrowing.
- `APPEND` on `FACT` remains unsupported on its original grounds: a fact has no multiplicity to append
  into.

An option is therefore addressable as a fact container and in no other way.

Runtime-only and identity-narrow. `OPTION` reuses the existing `target_option_key` column that already
carries an option-qualified `FACT` target's scope, introducing no second scope field. Because exact typed
target identity participates in the override-set payload (contract 5), an `OPTION` target changes the
override-set identity of any state containing one, as any new authority must; it leaves every existing
direct-target canonical payload and every already-derived override-set identity unchanged, so no recorded
binding is reminted or orphaned from the retained version it names. It does not change representation
schema identity — `OPTION` is an override target grain, not a representation structure.

Remove the obsolete prose-only mechanical-authority family and its production paths, including
`MechanicalEntity`, `SpellEntity`, `ConditionEntity`, `StatBlockEntity`, `ActionEntity`, `ItemEntity`,
`EntityData`, the associated ORM/table, and legacy-only constructors/callers. Retain the authoritative
source-corpus surfaces (`RuleChunk`, `RuleSource`, `RulesPackage`, and manifest) and existing override
precedence. Unmappable pre-release development rows or targets are rejected or deleted under the accepted
clean-baseline policy; they are never guessed into new authority. Diagnostic source-corpus query surfaces
may remain only as explicitly informational/admin tools and never as mechanical authority.

---

## Required Real-Corpus Proof

The first publication must use the complete production 5c release, not a substitute fixture or geometry
approximation, and must handle at least:

- rules outside `ENTRY` containers;
- spells and spell-list tables;
- class progression tables;
- equipment, random, lookup, and reference tables;
- composite creature stat blocks with sibling containers and fragmented table-cell prose;
- complete spell-scoped creature records and references to globally defined creatures without duplicate
  records;
- scoped name collisions; and
- records containing structured, prose-bound, and mixed authority.

Required canaries:

1. **Wish:** structured spell descriptors and fixed consequences coexist with the prose-bound open-ended
   clause; no free-form outcome becomes executable.
2. **Illusion:** typed check/DC-source authority coexists with contextual GameMaster judgment.
3. **Composite creature:** one creature record assembles its anchor, traits/actions, ability grid, and
   table-cell prose.
4. **Spell-scoped creature:** an embedded complete stat block becomes a scoped creature record with the
   correct typed relationship; an external creature reference reuses the existing record.
5. **Progression table:** level-indexed entitlements and feature references reconstruct correctly.
6. **Scoped collision:** a repeated feature/rule name resolves to the committed intended target.
7. **Supporting authority:** at least one heading, example, cross-reference, or explanatory clause is
   preserved as supporting authority rather than discarded.

Canaries prove difficult shapes; they do not replace the full-corpus gate.

---

## Acceptance Criteria

1. The projection binds exactly one reconstructed, published 5c release and rejects stale or mismatched
   bindings.
2. The review inventory covers the bound source with exact membership. Every unit is accepted, with
   no unreviewed unit, unresolved rule, or missing expected rule at publication.
3. Every expected rule, qualification, and exception has accepted structured or exact governing-prose
   authority; supporting material is linked and non-mechanical exclusions have accepted group reasons.
4. Every publishable component is structured, prose-bound with an honest accepted reason, or mixed.
   New fields have identified uses, including planned v1 uses. Reducibility alone and current adapter
   support do not determine handling; prose cannot conceal a field required by such a use.
5. Records assemble from accepted semantic membership and correctly handle simple, composite, non-entry,
   and nested source structures.
6. Stable record/component/fact identities do not depend on local ordinals and do not churn from unrelated
   sibling insertion.
7. Every fact, prose binding, relationship, and reference has exact source subspan provenance; overlap
   policy is enforced.
8. The closed typed fact union covers the fields required by identified uses; generic escape hatches
   and invented absence values are rejected. Versioned policy changes preserve historical meanings.
9. Reviewed per-record/component expectations reject omitted rules/exceptions, duplicate-as-coverage,
   missing required structured inputs, reference-only substitutes, and aggregate-count inflation.
   Exact governing prose is valid where no identified use requires separate fields.
10. Every source-authored mechanical reference resolves uniquely at build time through committed scope,
    alias, and target data.
11. The complete meaning-bearing payload changes projection identity; audit-only metadata does not; and
    override state changes the override-set identity without reminting the base projection identity.
12. A clean rebuild with identical inputs reproduces semantic hashes, projection UUID, stable
    subidentities, and persisted-state digest.
13. Persisted-state reconstruction detects tamper, omission, stale reuse, and partial state before
    publication.
14. Publication is atomic, published projections are immutable, and active queries never expose drafts.
15. Concurrent identical builds are idempotent and competing activation cannot split the active binding.
16. Typed failure states remain distinct and never authorize fallback inference.
17. The seven real-corpus canaries pass through the production 5c path, and the full-corpus gate—not the
    canaries—proves completion.
18. Slug and UUID inputs resolve to the same exact effective binding when valid; ambiguous/non-resolving
    inputs and accidentally empty selectors fail explicitly.
19. Typed and GameMaster authority views resolve consistent exact authority and provenance, identify the
    exact effective binding used, and do so without implying adapter capability or allowing retrieval to
    choose mechanical values.
20. Typed overrides preserve existing precedence, report ordered provenance, reject invalid/stale/
    cross-release/type-incompatible patches, and leave base projection rows unchanged.
21. Every distinct effective override state — including the empty one — has a deterministic override-set
    identity; adding, removing, enabling, disabling, reprioritizing, retargeting, or repayloading an
    applicable override mints a different one, as does recreating an otherwise identical override under a
    different `override_id` or changing only its `override_origin`; and at runtime a binding recorded
    against a superseded override set is reported `STALE` rather than re-resolved. Each identity is the
    content-derived identity of an immutable, replayable override-set version that preserves — or is
    deterministically reconstructable from append-only retained evidence preserving — the exact canonical
    ordered override identities, origins, typed targets, operations, precedence/order, enablement state,
    and complete validated payloads, so audit and replay of a previously recorded binding reconstruct all
    of them exactly as originally applied after the current override rows are edited, disabled,
    reprioritized, retargeted, or deleted. Retaining only the identifier plus current rows fails this
    criterion and its negative controls. Incidental audit metadata — creation timestamp, author, comments,
    proposal history — does not participate in the identity unless it participates in applicability,
    ordering, or resolution.
22. A clean-checkout migration succeeds, and no obsolete `MechanicalEntity` model, table, constructor,
    seed, fixture, fallback, or production caller remains.
23. CRD Issue 2b can consume the four-component effective binding without 5d deciding sheet storage, and
    CRD Issue 15c can consume authority without 5d claiming execution capability or implementing
    adjudicated-effect mutation.
24. Full default CI passes on the exact branch head, including production-path full-corpus acceptance and
    negative controls.
25. **(Owner Decision 2026-08-08)** A prose-authority override target, scoped by stable record and
    component identity, supports `DISABLE`/`REPLACE`/`APPEND` with the effective behavior contract 6
    defines; changing authored text, target, origin, operation, or order changes `override_set_uuid` while
    the base projection UUID is unaffected; the GameMaster view returns exact ordered source/authored
    authority and provenance; deterministic consumers' typed fact-bearing surface is unchanged by an
    authored prose overlay; replay reconstructs exact authored prose after mutable override rows change or
    disappear; invalid, blank, ambiguous, missing-target, cross-release, and type-incompatible prose
    patches fail closed; and legacy chunk-targeting overrides cannot alter the new effective
    mechanical/GameMaster authority views.

---

## Delivery and Engineering Discretion

This issue will require multiple reviewable PRs, but the internal design and PR boundaries are engineering
choices. Claude Code should inspect the current merged repository, choose the lowest-complexity
repository-native architecture that satisfies ADR-005d and this contract, and state any proposed PR split
in the first PR's Architecture Notes.

Claude Code owns ordinary choices such as schema normalization, module/class organization, helper
boundaries, migration decomposition, proposal/authoring tooling, test/fixture organization, and use of
Graphify, subagents, or advisor tools.

Apply the practical reliability delivery sequence: preserve accepted Speed and the other six batches;
consolidate common proposal loading, acceptance, and verification around existing production services;
make any necessary policy/schema transition explicit; then demonstrate one coherent regular section,
including exceptions, before scaling further. Retain historical replay evidence. No per-batch copied
acceptance program or second reproduction implementation is required merely for independence.

The pilot reports actual source scope, reused/new fields, governing/supporting prose, exceptions,
review findings, authoring/review effort, and batch-specific code. It has no preset throughput target
and changes no final coverage obligation. If large custom programs are still necessary, identify why
before beginning further batches. See the companion Speed comparison for the concrete first step.

The following are not engineering-discretion items:

- exact 5c release binding;
- complete mechanically substantive accounting;
- explicit acceptance of semantic authority;
- closed typed representation and exact provenance;
- source-reviewed expectations independent of the output they check;
- meaning-bearing immutable identity;
- distinct immutable base-projection and effective override-set identities in the runtime binding;
- retained immutable, provenance-exact override-set versions as replay evidence — override identity and
  origin included — separate from mutable current override rows;
- build-time reference resolution;
- reconstruct-before-publish and atomic activation;
- fail-closed binding/selectors/overrides;
- separation of representation, adapter execution, and GameMaster judgment; and
- removal of obsolete mechanical authority.

No partial PR or category batch constitutes completed 5d, and no partial projection may become active.

Every PR must report:

- the exact 5c release used for production-corpus verification;
- meaning-bearing inputs or identities changed;
- persisted reconstruction/publication behavior affected;
- completeness obligations and negative controls exercised;
- legacy paths removed or still pending;
- downstream seams touched; and
- any deviation from ADR-005d or this issue.

---

## Downstream Seams and Deferred Work

- **5c / ADR-005c:** read-only authoritative source corpus and identity. 5d does not alter it.
- **5a / ADR-0007:** retain source models, read path, and override precedence; discharge the typed-target
  override deferral and remove obsolete mechanical entities.
- **2b:** consumes the four-component `RulesPackageBinding` (package, release, mechanical projection,
  override set); owns Character Sheet Model fields and persistence, including how a recorded binding is
  revalidated when the effective override set changes.
- **15 / ADR-015:** roll-authorship and hand-authored adapter boundaries remain unchanged.
- **15c:** owns capability manifest, deterministic execution/certification, adjudication failure behavior,
  and any typed application path for GameMaster-selected effects.
- **18 / ADR-018:** retrieval remains informational/contextual, never trust-relevant authority.
- **15b Phase 3 / 19b / #129:** remain frozen.

Still deferred:

- complete Character Sheet Model and binding-storage design;
- adapter capability manifest and certified executable coverage;
- cancellation, rewind, expiration, retry/regenerate, and supersession semantics; and
- cross-system adapters or a generic plugin framework.

Update `known_unknowns.md` to show typed Rules Package authority as in progress until the complete issue
lands, preserve 15c ownership, and avoid equating projection publication with adapter coverage.

---

## Boundary Stop

Stop and surface the conflict rather than patching through it if implementation would:

- alter 5c source-corpus behavior or identity;
- narrow completed 5d below the complete mechanically substantive SRD;
- use adapter coverage to choose representation scope;
- accept machine proposals implicitly;
- replace reviewed rule-coverage expectations with aggregate thresholds;
- generate executable mechanics from prose or introduce a runtime rules language;
- use retrieval or model interpretation as trust-relevant authority;
- change override precedence or operation semantics;
- decide Character Sheet Model policy owned by 2b;
- implement or certify adapter behavior or adjudicated-effect mutation owned by 15c;
- authorize free-form GameMaster output as mechanical state;
- resume frozen work;
- preserve obsolete mechanical authority for compatibility;
- give authored prose a fake `chunk_id`, 5c span provenance, or an irreducibility claim copied from the
  base source;
- let deterministic consumers interpret authored prose as executable mechanics, or introduce model
  interpretation, a rules DSL, or retrieval-selected authority through the prose overlay;
- silently promote the free-form session `house_rules` string into trusted mechanical authority; or
- begin production-corpus authoring/acceptance, activate a partial mechanical projection, remove
  `MechanicalEntity` or the legacy runtime path, or decide downstream adjudicated-effect mutation owned by
  15c, in the PR that introduces the authored-authority prose overlay.

If implementation discovers a materially better architecture that conflicts with ADR-005d or this issue,
amend the governing document before or in the same PR. Do not merge a quiet contradiction.

If repeated review rounds concentrate on the same schema/service or shift from concrete defects into
ownership or semantics, apply the project boundary-over-patch rule before another remediation cycle.

---

## Claude Code Task

Implement the outcome and contracts above against current merged `main` and the real CRD Issue 5c
production release. Treat ADR-005d as governing authority. Inspect repository reality before choosing the
schema, decomposition, migrations, tooling, PR boundaries, or test layout.

Preserve the named issue boundaries, prove the acceptance criteria with production-path and negative
verification, and surface any genuine ownership conflict or Known Unknown instead of improvising it.
Follow normal repository branch, CI, review, and owner-merge rules.
