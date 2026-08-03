# ADR-005c: Rules Authority Repair

**Issue:** Cross-issue architecture defect — discovered during investigation of the Rules Package,
SRD 5.2.1 ingestion, the bounded d20 adapter, and frozen PR #129 (CRD Issue 15b Phase 2). Not scoped to
a single CRD issue; this ADR establishes the repair order for CRD Issues 5c, 5d, 2b, and 15c below.
**Date:** 2026-07-21
**Status:** Accepted — owner directive dated 2026-07-21 authorizing the seven decisions recorded here.
Repository adoption proceeds through the documentation PR that introduces this ADR.

> **Amendment — operational reliability (2026-08-03).** CRD Issue 5c is judged by **operational
> reliability**, not adversarial or forensic proof. See
> [Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md) and the
> dated section at the end of this ADR. The amendment is **prospective**: it changes what Issue 5c and
> its downstream consumers are required to guarantee from 2026-08-03 forward, and does not alter this
> ADR's historical decision record or what Issue 5c's implementation previously proved.

> **Correction — pre-release clean baseline (2026-07-27, Issue 5c Rev7 / Issue 18 Rev6).** Afterworlds is
> pre-release, so persistence created before Issue 5c gets no upgrade-compatibility or preservation
> guarantee. The owner replaced the earlier *strict legacy quarantine / zero-reachability* contract with a
> breaking clean baseline: (1) migration `0018` deletes the incomplete legacy SQL package and its
> dependent rows; (2) the obsolete structured JSON and every production loader/default/reader for it are
> deleted (kept only in Git history); (3) the configured development Chroma store is reset in full **once**
> — an explicit one-time step (`scripts/reset_corpus_baseline.py`), never automatic startup — before the
> corrected rules corpus is rebuilt from the published SQLite-authoritative package via Issue 18's reindex
> path. No legacy UUID or collection-name handoff, pending-cleanup registry, or publication-time
> legacy-reachability check is used. Historical knowledge is preserved in Git history and this note only.

---

## Central Invariant

> **The architecture does not currently provide an end-to-end authoritative mechanics path from the
> official D&D SRD 5.2.1 source to deterministic adjudication, and no component may claim it does until
> that path is rebuilt.**
>
> Rules Package publication proves source-corpus integrity. Adapter certification proves a named
> adapter version can execute a declared mechanical coverage manifest against a specific package
> version. These are separate, independently provable claims. Semantic retrieval (ChromaDB, embeddings)
> may locate rules prose for explanation and narration; it may never author, infer, or select a
> trust-relevant mechanical value. When advertised authority is missing, the system fails closed with a
> typed error — it does not improvise, does not fall back to a similar mechanic, and does not let
> `outcome="undetermined"` silently stand in for an integration gap.

**Scope of this invariant (2026-08-03).** The Central Invariant above states what *publication* proves —
source-corpus integrity — and what retrieval may never do. It does not, in its own text, prescribe a
proof architecture, a count of release hashes, a derivation graph, or any obligation on a downstream
consumer to re-prove publication. Those requirements were introduced by CRD Issue 5c's Completion
Contract A (GitHub #132), not by this ADR, and are prospectively superseded by the operational
reliability amendment. This invariant's own text is unchanged and remains binding.

## Context

### What triggered this ADR

Investigation of frozen PR #129 (CRD Issue 15b Phase 2, `feature/issue-15b-structured-roll-lifecycle`,
branch head `d8233a4` at the time of this ADR) found that the gap blocking Phase 2 is not local to the
Issue 15b adapter. The PR's own freeze note states the trigger directly:

> "a cross-layer review surfaced unresolved upstream capability questions in the Rules Package schema,
> ingestion pipeline, and bounded-d20 adapter. The currently committed structured SRD artifact and
> adapter do not yet demonstrate production reachability for the complete Issue 15b coverage inventory,
> including authoritative DCs, structured damage and healing terms, saving-throw adjudication,
> multi-step mechanics, and reachable mechanical-decision paths."

Tracing that gap upstream — through Rules Package ingestion (CRD Issue 5b / GitHub #57), the Rules
Package models and query service (CRD Issue 5a / GitHub #54), the live orchestration path, and the
bounded d20 adapter as it exists on `main` (pre-Issue-15b) — confirms this is a cross-issue defect in
the mechanical-authority chain, not another local Issue 15b patch.

### Confirmed defect family

Each item below is verified against current repository state, not inherited from prior planning
documents:

1. **Issue 5b's full-corpus contract was not met.** GitHub #57's spec is explicit and repeated:
   *"'fully ingested' means the full D&D SRD 5.2.1 corpus, not a bounded representative subset,"*
   and, on the term "curated": *"It does not authorize partial-corpus ingestion."* The committed
   artifact, `data/srd/srd_5_2_1_structured.json` (58,686 bytes, 1,102 lines), contains 54 sections and
   50 entities (17 spells, 15 conditions, 10 items, 5 actions, 3 stat blocks) — a small, hand-curated
   subset. This is a deviation from an already-accepted contract, discovered later during Issue 15b
   review, not a decision anyone made at Issue 5b's acceptance time.
2. **Source-version fidelity has not been established; the absence of explicit older-version labels
   does not prove concordance.** The artifact's `_meta` block carries one consistent tag
   (`"source_version": "5.2.1"`) and no other version string (`5.1`, `2014`, `OGL 1.0a`) appears
   anywhere in the file — but that negative check rules out only one narrow contamination mode (an
   explicit wrong version label) and proves nothing about the others: obsolete rule wording; rules that
   differ from SRD 5.2.1's actual text; page citations that do not correspond to SRD 5.2.1; material
   copied or paraphrased from an older rules source; a mixture of content from different source
   versions; or source text that cannot be reconciled to the authoritative PDF at all. None of these
   have been checked. This ADR does not assert contamination is either proven or disproven — see the
   Verification Note below for the governing statement and CRD Issue 5c's required verification scope.
3. **The ingestion parser accepts preconstructed JSON only.** `src/afterworlds/ingestion/srd_parser.py`
   validates a JSON document's shape against typed Pydantic models; it contains no code path that reads
   or derives content from `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`. `scripts/ingest_srd.py` is a CLI
   wrapper that loads the same committed JSON and calls `IngestionService.ingest(...)` — the PDF is
   never touched by any ingestion code.
4. **The publication gate proves internal consistency, not source completeness.** `IngestionService.
   publish` checks package/manifest existence, `manifest.sql_ingest_complete`, `manifest.
   vector_write_complete`, and SQL-row-count-equals-vector-count — five checks that compare the
   pipeline's own outputs to each other. `sql_ingest_complete` is set `True` once `sql_chunk_count > 0`
   (i.e., "at least one chunk exists"), not "the corpus is complete." No check compares ingested content
   to the source PDF or any independent completeness reference.
5. **Ingestion tests use deliberately minimal, independently constructed fixtures — not the committed
   production artifact.** `tests/ingestion/test_ingestion.py` (2,216 lines, 63 tests) defines its own
   in-memory `srd_data_fixture` (a hand-constructed minimal dict covering all 8 subsystems: 3 spells, 3
   conditions, 2 items, 1 stat block, 1 action) to prove provenance non-nullity, manifest gating,
   idempotency, and publish/draft visibility. This fixture is not `data/srd/srd_5_2_1_structured.json` —
   the test suite never loads or validates the committed production corpus against the official SRD
   inventory, and therefore cannot prove production-corpus completeness. This is a distinct gap from the
   fixture's own minimality: even a much larger hand-constructed fixture would not close it, because
   nothing in the suite checks the *committed artifact* at all.
6. **Rules Package entities lack typed numeric/relational mechanical data.**
   `src/afterworlds/models/rules_package.py`: `SpellEntity.effect_description`, `ConditionEntity.
   effects`, `ActionEntity.effect`, and `StatBlockEntity.actions` are all plain `str`/`tuple[str, ...]`
   prose fields. No entity carries a `dc`/`difficulty_class` field or a structured dice-term
   representation — *non-binding illustrative example, not a support commitment:* Fireball's `8d6` and
   the Young Red Dragon's `2d10+6` bite currently exist only as prose substrings in the committed
   artifact; this is cited only as evidence of the current data shape, not as a decision that these
   specific spells or stat blocks are or will be supported. `RuleOverride` is a non-mutating
   content-patch channel for chunks/entities, not a per-call numeric-DC channel.
7. **An empty `RuleSliceRequest` produces an empty slice.** `RulesPackageService.
   get_active_rule_slice` only populates `applied_chunks` when `subsystem_tags` is non-empty and only
   iterates `entity_refs` when it is non-empty; with both left at their model defaults (`[]`), the
   method returns `ActiveRuleSlice(chunks=(), entities=())` — not an error, not a fallback to "all
   content."
8. **Two independent live paths reach adjudication with no usable rule slice — not one.** Direct
   repository verification (prompted by Codex review; an earlier draft of this ADR audited only Path B
   and incorrectly stated the slug path was not live) confirms both:

   **Path A — non-UUID binding is silently omitted.** `RpgCharacterSheetBase.rules_package_id` is a plain
   `str` (`src/afterworlds/models/character_sheet.py`). The live story-bootstrap path,
   `ensure_mode_session_state` in `src/afterworlds/api/story_bootstrap.py:153`, hardcodes
   `rules_package_id="dnd5e"` for every RPG character sheet it creates. This function is called directly
   from the production `POST /api/stories` route (`src/afterworlds/api/routes/stories.py:66`) for every
   new RPG story — confirmed by direct inspection, not inferred. No production code path subsequently
   rewrites `rules_package_id` to a UUID before play. At turn time,
   `src/afterworlds/pipeline/orchestrator/service.py:645-651` is:
   ```python
   try:
       _pkg_uuid = UUID(pre_sheet.rules_package_id)
       rule_slice_request = RuleSliceRequest(package_id=_pkg_uuid)
   except ValueError:
       # Non-UUID binding (slug) — omit request; adjudication
       # proceeds without a rule slice and produces "undetermined".
       rule_slice_request = None
   ```
   For the bootstrap value `"dnd5e"`, `UUID(...)` raises `ValueError`; the `except` clause catches it and
   sets `rule_slice_request = None`, and adjudication continues without a Rules Package slice. **This is
   a live, currently-reachable fail-open path, not a forward-looking risk.**

   **Path B — a valid UUID still produces an empty request.** When `rules_package_id` does hold a
   syntactically valid UUID, the same call site (`service.py:647`) builds
   `RuleSliceRequest(package_id=_pkg_uuid)` with `subsystem_tags`/`entity_refs` left at their model
   defaults (`[]`); per item 7 above, this always resolves to an empty `ActiveRuleSlice` — not an error.

   Both paths converge on the same downstream consequence (items 9–10 below): adjudication proceeds with
   no Rules Package authority, and missing authority can surface as `outcome="undetermined"`
   indistinguishably from a genuinely unsupported mechanic.
9. **The bounded d20 adapter cannot verify real DCs or generate non-1d20-family instructions from
   production data.** On `main` (`src/afterworlds/pipeline/rpg/adapter.py`, pre-Issue-15b),
   `_verify_dc` unconditionally `return`s `None`, with an inline comment stating DC verification is
   "deferred to Issue 18." Because `_compute_outcome` always receives `dc=None`, the adapter can never
   return anything but `"undetermined"` for any roll. `compute_sheet_effects` passes through whatever
   `sheet_effects` the record already carries rather than computing damage/healing/duration effects from
   Rules Package data, and roll generation is limited to three hardcoded expressions (`1d20`,
   `2d20kh1`, `2d20kl1`).
10. **`outcome="undetermined"` has served both as valid fail-safe and as a mask for missing upstream
    authority.** ADR-015 Decision 7 designed `undetermined` as the correct fallback when a mechanic is
    outside the supported boundary. Because DC is unconditionally `None` on `main`, every DC-gated roll
    resolves to `undetermined` regardless of whether the underlying mechanic is genuinely unsupported or
    the authority chain is simply empty — the same output code currently means two different things.
11. **ADR-018 Decision 10 already forecloses semantic retrieval as mechanical authority.** ADR-018's
    Central Invariant and Decision 10 state, in nearly the words this ADR would otherwise need to
    introduce: *"No Context Builder, RPG adjudication loop, Writer, Planner, pass service, or runtime
    mechanical decision may consume semantic rules retrieval as authority. Runtime rule inclusion
    remains exclusively through `get_active_rule_slice`."* This ADR's Decision 4 restates and binds this
    boundary at the Rules Authority layer; it does not reopen or amend ADR-018.
12. **PR #129 contains plausibly reusable lifecycle machinery whose production mechanical reachability
    is unproven.** Sequence/persistence/resume/event-ledger/transaction/audit machinery exists and is
    unit-tested against hand-constructed instructions (per ADR-015b), but nothing in PR #129 or its
    prerequisites demonstrates that this machinery can be driven end-to-end from real Rules Package
    content once items 6–9 above are fixed.

### Verification note — source-version fidelity is unresolved, not cleared

The investigation prompt that led to this ADR described the committed SRD artifact as containing
"source-version contamination and invalid or obsolete source references." Checking for explicit
older-version strings (item 2 above) found none — but that is not a sufficient fidelity test, and this
ADR does not treat it as one.

> **Source-version fidelity has not yet been established. The absence of explicit older-version labels
> does not prove concordance with SRD 5.2.1.** Contamination or source mismatch can appear as obsolete
> rule wording; rules that differ from SRD 5.2.1; page citations that do not correspond to SRD 5.2.1;
> material copied or paraphrased from an older rules source; a mixture of content from different source
> versions; or source text that cannot be reconciled to the authoritative PDF. None of these have been
> checked against `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`. **CRD Issue 5c must perform source-hash,
> citation-level, and rule-level concordance verification** before the corpus can be considered
> fidelity-checked.

The previously alleged contamination remains **unverified pending CRD Issue 5c** — this ADR asserts
neither that it is proven nor that it is disproven. The corpus-scale defect (item 1) stands independently
of this open question and is sufficient on its own to justify Decision 1 and Decision 2 below.

A second material observation, not a contradiction of any required decision: `adapter.py`'s `_verify_dc`
comment on `main` says DC verification is "deferred to Issue 18." Issue 18 is retrieval memory
(ADR-018), and ADR-018 Decision 10 already forbids semantic retrieval from supplying mechanical
authority. That comment reflects a superseded plan overturned by Decisions 4 and 6 below. This ADR does
not edit that comment — it is application code, out of scope for a documentation-only change — but flags
it as remediation work for CRD Issue 5d / 15c.

---

## Decisions of Record

### Decision 1 — Rules Package publication and adapter certification are separate

A Rules Package can be published as a complete and trustworthy source corpus without implying that
every mechanic in it is deterministically executable. Two distinct states are defined:

**Corpus-published:** the package has passed authoritative-source identity verification, complete
source-unit accounting, provenance validation, persistence/queryability checks, and source-to-artifact
concordance checks.

**Adapter-certified:** a named Rules System Adapter version has passed a declared compatibility suite
against a particular package version and mechanical coverage manifest. Certification binds, at minimum:
Rules Package identity and version, authoritative-source or corpus-transform hash, adapter identity and
version, and capability-manifest version. Changing any certification component invalidates the prior
certification until compatibility tests pass again.

Package publication must never imply universal adapter support. Item 4 above (`sql_ingest_complete` at
`sql_chunk_count > 0`) is the concrete evidence that today's publication gate proves neither corpus
completeness nor adapter reachability — it proves only "the pipeline ran to completion on whatever
input it was given."

### Decision 2 — The complete source corpus and executable mechanical projection are distinct layers

A Rules Package contains two related but non-identical layers. The **authoritative source corpus** is
the complete source text, tables, stat blocks, entities, provenance, and indexing required by the
package contract. The **executable mechanical projection** is a bounded set of normalized,
machine-readable mechanical facts linked to exact authoritative source records. Not every sentence in
the source corpus must become executable.

Every executable fact must resolve to authoritative source provenance, use an approved typed mechanical
representation, remain distinguishable from source prose, and be covered by the adapter capability
manifest. The project preserves complete source authority without pretending to compile every source
sentence into executable mechanics. This directly targets defect items 1 and 6: full-corpus ingestion
(the source-corpus layer) and typed mechanical authority (the executable-projection layer) are separate
repair efforts with separate acceptance criteria — conflating them is what let a 50-entity subset with
prose-only mechanics stand in for both at once.

**Forward reference (ADR-005d, 2026-07-30):** the executable mechanical projection layer is specified by
[ADR-005d](adr-005d-complete-typed-mechanical-authority.md), which settles complete 5d scope as the full
mechanically substantive SRD 5.2.1 corpus represented as typed facts, exact prose-bound GameMaster
authority, or both. This decision's text is unchanged.

### Decision 3 — Ingestion does not generate a rules engine

The ingestion pipeline may produce declarative, typed mechanical facts. It must not produce or execute
generated application code, arbitrary executable expressions, dynamic scripts, model-authored mechanical
logic, or an inferred universal rules engine. Each supported adjudicated game system requires a
hand-authored Rules System Adapter that interprets only approved and bounded typed mechanic shapes. The
model may interpret supplied rules for advisory reasoning and narration; it does not author
trust-relevant numbers, outcomes, or mutations.

### Decision 4 — Semantic retrieval is never trust-relevant mechanical authority

ChromaDB, embeddings, full-text search, or other semantic retrieval systems may locate relevant source
prose for context, explanation, and model reasoning. They may not author, infer, or select authoritative
difficulty classes, Armor Classes, dice pools, numeric modifiers, resource costs, targeting rules,
success/failure branches, conditions/durations, sheet mutations, or other trust-relevant mechanical
values. Trust-relevant mechanics come from deterministic identifiers and typed persisted records.
Retrieved prose may support explanation but cannot substitute for missing deterministic mechanical
authority.

This preserves and restates the Issue 18 boundary already established in ADR-018 (Central Invariant and
Decision 10, quoted in Context item 11) rather than introducing a new one. It also forecloses the stale
`_verify_dc` "deferred to Issue 18" plan noted in the Verification Note: DC authority must come from
typed, persisted, source-linked Rules Package mechanical authority defined by Issue 5d — whether that
takes the shape of a field on an existing entity, a linked mechanical-projection record, or another typed
persisted structure is an Issue 5d implementation choice this ADR does not make — never from retrieval.

### Decision 5 — Canonical Rules Package binding uses deterministic package identity, not an unverified slug

The runtime path must bind a character and session to one deterministically resolved Rules Package
identity. A human-readable package key or slug may remain available as metadata or an external
convenience, but it must resolve through one code-owned and tested service before context construction
or adjudication. The canonical internal binding uses either the Rules Package UUID or a typed package
reference that resolves unambiguously to the UUID and version.

The architecture must not allow silently omitted rule slices because a slug was placed where a UUID was
expected, valid package identifiers that produce an entirely empty adjudication request, or
model-authored labels substituting for deterministic package, entity, action, ability, effect, or
mechanic identities. Any adjudicating request must contain sufficient deterministic selectors to
retrieve its required authority.

**Confirmed against current code (Context item 8):** both prohibited failure modes are live. The current
bootstrap path supplies the non-UUID identifier `dnd5e`; the orchestrator catches the resulting UUID
parse failure, omits the `RuleSliceRequest`, and continues without a rule slice (Path A). Separately,
when the stored identifier is a valid UUID, the orchestrator constructs a request with no subsystem or
entity selectors, which resolves to an empty slice without error (Path B). CRD Issue 5d owns
deterministic package-reference resolution and authoritative selector construction — closing both gaps,
either by requiring non-default selectors before a slice request is honored, or by a documented, explicit
"whole-package slice" request shape distinguishable from an accidentally-empty one. CRD Issue 15c owns
ensuring adjudication fails closed when the resolved authority is absent or empty.

**Forward reference (ADR-005d, 2026-07-30):** [ADR-005d](adr-005d-complete-typed-mechanical-authority.md)
Decision 9 supplies the deterministic binding this decision requires and extends it: the effective runtime
binding is package UUID, release version, immutable mechanical-projection UUID, and an immutable
override-set UUID identifying the exact applied override state. This decision's text is unchanged.

### Decision 6 — Advertised supported mechanics fail closed when authority is missing

For a mechanic declared supported by an adapter capability manifest, the following must produce a typed
error or explicit unsupported/configuration result: missing package authority; empty or unresolved rule
binding; incompatible package and adapter versions; missing required character state; unresolved action,
ability, item, spell, condition, target, or mechanic identity; unsupported effect shape; invalid or
incomplete provenance; failure to construct an authoritative instruction.

The system must not silently improvise a mechanical value from prose, accept a model-proposed number as
authority, fall back to a semantically similar mechanic, treat missing authority as an ordinary
successful adjudication, or reduce an unsupported mechanic to a simpler supported mechanic.

`outcome="undetermined"` remains valid only where indeterminacy is the explicitly designed behavior — for
example, a roll with no compare-outcome, or a deliberately deferred difficulty decision. It must not mask
empty integration, absent authority, or a mechanic advertised as deterministically supported. This
directly resolves the double meaning identified in Context item 10: after CRD Issue 15c, an
`undetermined` outcome and a fail-closed typed error must be distinguishable failure modes, not the same
code path standing in for both.

### Decision 7 — PR #129 remains frozen pending Rules Authority remediation

PR #129 is provisionally classified as: *"Issue 15b Phase 2 lifecycle foundation — compatibility pending
Rules Authority remediation."* Do not merge it. Do not resume general fix-and-review cycling on its
adapter. Do not begin Issue 15b Phase 3 product or HTTP wiring.

The following portions may remain candidate foundation: structured roll-instruction contracts,
action-resolution sequences, pending-roll and pending-decision lifecycle, resume handling, event-ledger
records, transaction and idempotency boundaries, and sheet-effect and audit projections. Their final
disposition depends on the corrected upstream contracts.

After the Rules Package, character-state, deterministic binding, and adapter-compatibility work is
complete, PR #129 must be evaluated under one of three dispositions: **rebase and amend** if its
lifecycle architecture remains compatible; **split** if lifecycle and obsolete adapter work need
independent review; or **replace** only if the repaired contracts materially invalidate the lifecycle
architecture itself. The current investigation does not justify discarding the lifecycle foundation, but
it also does not establish production mechanical reachability.

---

## Scope Note — `Dnd5eCharacterSheet` Is Not a Reproduction of an Official Character Sheet

`Dnd5eCharacterSheet` (`src/afterworlds/models/character_sheet.py`) is an Afterworlds-owned internal
representation of character state — confirmed by direct inspection: it extends `RpgCharacterSheetBase`
(structural identity/ruleset-binding fields only: `sheet_id`, `story_id`, `rules_package_id`,
`character_name`, timestamps) and adds D&D-5e-specific typed fields (`ability_scores`, `skills`,
`equipment`, `current_hp`/`maximum_hp`, `spell_slots`, `active_conditions`) — this field list describes
the **current** implementation as evidence of ownership, not a finalized or complete future inventory;
completing the D&D 5e character-state model is out of scope for this ADR (see Scope Boundaries). The
module docstring already states this ownership boundary: rules meaning belongs to the active Rules
Package and adjudication layer, not this model.

Its fields must be derived from three sources: SRD 5.2.1 mechanics; the state required by Afterworlds'
supported deterministic adjudication; and product persistence/display requirements. An official D&D
character sheet may later be consulted as a non-authoritative completeness and usability reference — its
layout does not define this internal schema. This ADR does not address a future visual or printable
character-sheet UI; that remains explicitly out of scope (see Scope Boundaries below).

---

## Consequences

### Positive consequences

- Source-corpus completeness can be proven independently of adapter breadth (Decision 1).
- Afterworlds can ingest complete systems without claiming universal deterministic support (Decision 1,
  Decision 2).
- Supported-mechanics claims become versioned and testable (Decision 1).
- Mechanical provenance becomes auditable (Decision 2).
- Semantic retrieval remains useful without entering the trust boundary (Decision 4, consistent with
  ADR-018 Decision 10).
- Missing authority becomes visible rather than hidden by `undetermined` (Decision 6).
- PR #129 can be evaluated against stable upstream contracts rather than patched repeatedly (Decision 7).

### Costs and tradeoffs

- Additional schema and migration work will be required (Rules Package DC/dice-term mechanical authority,
  deterministic binding) — exact shape is an Issue 5d decision, not fixed here.
- Full-corpus ingestion and executable projection need separate tests and manifests.
- Every supported adapter/package combination requires explicit certification.
- Some SRD mechanics will remain present in the corpus but unsupported by deterministic adjudication.
- The existing curated package artifact was replaced by the authoritative PDF-derived corpus and then,
  under the R18 pre-release clean baseline (see the correction note below), deleted outright rather than
  rebuilt (Issue 5c Rev7).
- Existing tests and acceptance claims for Issues 5b, 15, and 15b will require reevaluation — not because
  those issues were decided incorrectly at the time, but because a later-discovered gap changes what
  "acceptance" now requires downstream.
- Character-state completeness and Rules Package authority will require separate ownership and
  implementation work (CRD Issue 2b, CRD Issue 5d).

---

## Alternatives Considered

1. **Continue patching the Issue 15b adapter against the current package.** Rejected — the adapter's
   `_verify_dc` returns `None` unconditionally on `main` because no DC authority exists anywhere
   upstream; no adapter-local patch can manufacture data the Rules Package does not carry.
2. **Treat model interpretation of source prose as deterministic authority.** Rejected — this directly
   violates CLAUDE.md invariant 10 and ADR-015 Decision 7; the model is not code-owned and cannot be the
   trust boundary for mechanical values.
3. **Parse arbitrary dice and effect prose at runtime.** Rejected — turns ingestion into an inferred
   rules engine (Decision 3), reintroducing exactly the "generated mechanical logic" risk this ADR
   forecloses, and offers no provenance guarantee that typed, source-linked mechanical authority does.
4. **Treat ChromaDB or semantic retrieval as the missing rules engine.** Rejected — already foreclosed by
   ADR-018 Decision 10; retrieval is a discovery aid, never authority (Decision 4).
5. **Mark the curated subset as the intended v1 package and silently weaken Issue 5b's full-corpus
   contract.** Rejected — Issue 5b's spec is explicit that "curated... does not authorize partial-corpus
   ingestion." Retroactively redefining "v1 scope" to match what was actually shipped would rewrite an
   already-accepted contract to erase a defect rather than fix it, and would contradict CLAUDE.md's rule
   against silently resolving Known Unknowns and scope drift.
6. **Attempt to compile the entire SRD into executable mechanics.** Rejected — Decision 2 explicitly
   separates the source-corpus layer from the executable-projection layer; not every sentence needs to
   become executable, and attempting this would be unbounded scope with no stopping criterion.
7. **Discard all of PR #129 before testing its lifecycle structures against the repaired contracts.**
   Rejected — Decision 7: the lifecycle machinery (sequences, event ledger, transaction/idempotency
   boundaries) is independently unit-tested and plausibly reusable; discarding it before evaluating it
   against corrected upstream contracts would be premature and wasteful.
8. **Put all D&D-specific mechanical state into the generic `RpgCharacterSheetBase`.** Rejected —
   `RpgCharacterSheetBase` is documented as structural identity/ruleset-binding fields only, shared
   across future ruleset-specific sheets; collapsing D&D 5e specifics into it would make the base
   unusable for any other supported ruleset and contradicts the existing `Dnd5eCharacterSheet` subclass
   design (Scope Note above).

---

## Scope Boundaries

This ADR establishes architecture and repair order. It does not itself define the final implementation
schema. Explicitly out of scope: implementing full-corpus ingestion; selecting the exact PDF extraction
library; defining the complete source-unit taxonomy; writing the final mechanical discriminated union;
completing the D&D 5e character-state model; implementing deterministic binding; repairing the adapter;
deciding support for every SRD mechanic; implementing parameterized upcasting; implementing arbitrary
reaction handling; implementing a visual or printable character-sheet UI; modifying PR #129; resuming
Issue 15b Phase 3; frontend dice work under Issue 19b. Those details belong to the subsequent repair
issues below and their associated ADR amendments where necessary.

---

## Amendment — Issue 5c Operational Reliability (2026-08-03)

**Status:** Accepted — owner approval dated 2026-08-03. Governing text:
[Issue 5c Operational Reliability Amendment](adr-005c-operational-reliability-amendment.md).
**Effect:** Prospective. Nothing above this section is rewritten, and no historical decision record or
prior implementation claim is altered.

**The standard.** CRD Issue 5c exists to make the SRD 5.2.1 corpus **operationally reliable** for
dependable gameplay and downstream Rules Package construction. It does not provide adversarial,
forensic, or chain-of-custody proof. The required standard is reliable source material for Issue 5d —
not proof that a malicious actor could not coherently rewrite the database and every dependent value.

**Preserved as binding outcomes.** Exact source identification (document, version, license, and a
checksum sufficient to detect a different document); complete and faithful representation, with silent
omission unacceptable and every deliberate exclusion made under an explicit reviewable policy; citable
provenance with stable source locations; authoritative/derivative separation; stable immutable
publication with no silent in-place mutation; meaningful-change versioning; accidental mismatch and
corruption detection at publication, verified reuse, and the downstream seam; fail-closed publication
leaving no usable partial release; rebuildability and diagnosis from committed source, declared
configuration, approved logical corpus, and diagnostic evidence; legacy quarantine of the incomplete
prior corpus from every active path; and the typed-mechanics boundary — Issue 5c does not certify that
source prose was correctly interpreted as typed mechanics, which remains Issue 5d's responsibility.

**Prospectively superseded as governing requirements.** An exact mandatory count of top-level release
hashes or proof artifacts; a complete mathematical genealogy connecting every stored identity to every
other; byte-identical regeneration of every report, serialization, database representation, or
incidental artifact when the approved logical corpus is unchanged; and coherent-rewrite resistance —
resistance to a malicious actor rewriting the database together with every related checksum or
reference. Downstream reconstruction and re-proof of the entire historical publication process on every
load of an approved release is superseded by the trust boundary in §5 of the amendment.

Superseding these as *requirements* does not delete the corresponding implementation. Existing ledgers,
reconciliation records, hashes, reports, manifests, and validators may remain where the bounded
contract-to-code audit shows them to be a low-cost way to satisfy a retained outcome; their present
existence simply no longer makes their exact topology mandatory.

**Attribution.** These superseded requirements originate in CRD Issue 5c's Completion Contract A
(GitHub #132), not in this ADR's Decisions of Record. Decisions 1–7 above are unchanged and remain
binding, as does the 2026-07-27 pre-release clean-baseline correction.

**Release identity.** Release identity tracks the authoritative source and the approved logical corpus,
not every byte of every implementation file. An incidental code, annotation, comment, logging, or
plumbing change that leaves the approved logical corpus and its compatibility unchanged does not require
reminting solely because a whole source file changed. Choosing the least complicated implementation of
that rule belongs to the contract-to-code audit.

**Chroma.** The Owner Decision of 2026-08-01 is preserved exactly; see §6 of the amendment and ADR-005d
Decision 8.

---

## Repair-Order Consequence

1. ADR-005c — Rules Authority Repair (this document).
2. CRD Issue 5c — SRD Corpus Integrity and Reproducible Full-Corpus Ingestion.
3. CRD Issue 5d — Structured Mechanical Authority and Deterministic Rule Binding.
4. CRD Issue 2b — D&D 5e Character State Completeness for Deterministic Adjudication.
5. CRD Issue 15c — Bounded d20 Production Reachability.
6. PR #129 disposition (Decision 7).
7. Resume Issue 15b Phase 3 and Issue 19b only after the vertical mechanics gate passes.

CRD Issues 5d and 2b may proceed in parallel after CRD Issue 5c establishes the authoritative corpus
contract, provided their shared interfaces (Rules Package identity/version binding consumed by both the
character-state model and the mechanical-authority layer) are fixed first. None of these repair issues
has a GitHub issue number yet; they are referenced here only by CRD issue label, per CLAUDE.md's
CRD-issue-vs-GitHub-issue namespace distinction — do not invent GitHub numbers for them.

---

## `known_unknowns.md` Resolution Text

Neither entry below existed in canonical `known_unknowns.md` on `main` before this ADR's documentation
PR. Both were first surfaced and documented on frozen, unmerged PR #129 (Issue 15b Phase 2); because that
PR never merged, neither entry ever reached the canonical record. This ADR's documentation change adds
both entries to `known_unknowns.md` for the first time on `main`, with corrected dispositions rather than
an import of PR #129's text as-is:

- **"Rules Package carries no structured numeric/mechanical data (DC, dice formulas)"** (new entry, Open
  section): the architectural question — how DC and dice-term authority should be modeled and bound so
  the adapter can execute against real Rules Package content, and how that authority must never silently
  fall back to prose, retrieval, or model inference — is resolved by ADR-005c (Decisions 1, 2, 4, 5, 6).
  Implementation remains pending CRD Issues 5c (corpus), 5d (structured mechanical authority and
  deterministic binding), 2b (character-state completeness), and 15c (adapter production reachability).
- **"Parameterized adjustments (spell-slot-level upcasting, variable-amount resource recovery)"** (new
  entry, Open section): added as a distinct, still-open mechanic-shape question that ADR-005c does not
  resolve. Any production-coverage or production-reachability claims present in PR #129's version of this
  question are not imported — see Context items 1, 5, and 12 above.

---

## Cross-Reference: ADR-015b Seams Table

ADR-015b's Seams table (row "5a / 5b") states *"Rules Package remains mechanical canon; ingestion is
unchanged."* That statement was accurate at ADR-015b's acceptance time and is not rewritten here — see
the note below on why. It is now qualified by this ADR: ingestion output is confirmed short of Issue 5b's
full-corpus contract (Context item 1), and the Issue 15b coverage inventory's production reachability
against that output was never demonstrated (PR #129's own freeze note). CRD Issue 15c inherits this
qualification when it resumes work on adapter production reachability.

**Why ADR-015b itself is not edited:** no existing ADR in `/docs/decisions/` carries a forward
cross-reference note added by a *later, separate* ADR — the one precedent found (ADR-015b's own "Group
12 Addendum") is an intra-document addendum added during that ADR's own remediation rounds, not a
cross-ADR annotation. Absent a repository convention for this, and because ADR-015b's file is currently
part of PR #129's unmerged diff (editing it here would create an unnecessary merge conflict when #129
resumes), this ADR records the cross-reference on its own side rather than editing ADR-015b. This
follows the task's explicit fallback: leave ADR-015b unchanged and explain why.
