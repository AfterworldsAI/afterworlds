# ADR-017: Writing Mode Integration — Persona Registry, Authoring Controls, Beat Constraints, and Minimal Draft Provenance

**Issue:** CRD Issue 17 — Writing Mode Integration
**Date:** 2026-06-29
**Status:** Accepted

---

## Context

CRD Issue 17 ships the Writing Mode persona registry, persisted setup/configuration,
typing for work-product kind and canon eligibility, beat constraints, minimal version
pointers, transaction-scoped OOC configuration updates, and backend UI-facing Writing
state.

The central invariant:

> **The model may write, critique, brainstorm, teach, and propose revisions; it may
> never seize authorship or make durable writing configuration, persona identity,
> canon status, beat constraints, or version-history state authoritative.**

Thirteen decisions were made during Issue 17. They are recorded here.

---

## Decision 1: Persona selection is registry-backed

**Decision:** Issue 17 implements a static, versioned Persona Registry. The v1
registry contains six active Writing personas: Chiron, Merlin, Vidura, Odin, Athena,
and Thoth. Future personas can be added without schema change.

**Rationale:** The v1 persona roster is intentionally small and must not be implemented
as if the six are the permanent closed universe. A registry allows expansion by adding
data, not by changing enum definitions or schema.

**Consequence:** `PersonaProfile` typed model and `PersonaRegistryProvider` protocol
added to `src/afterworlds/modes/personas/registry.py`. Initial v1 Writing profiles
stored in `src/afterworlds/modes/personas/profiles/writing_personas.v1.json`. Registry
loaded and validated at startup/test time.

---

## Decision 2: Persona identity is persisted by stable registry ID

**Decision:** `WritingSessionState` stores `persona_id`, `persona_registry_version`,
`persona_profile_version`, and `persona_prompt_fingerprint`. The selected profile is
resolved from the registry during setup, prompt rendering, and visible-state assembly.

**Rationale:** Stable slug + provenance fields allow registry evolution without
requiring session data migration for the common case. Profile version and fingerprint
are provenance-only in v1; historical lookup and mismatch handling are deferred.

**Consequence:** `WritingPersona` closed enum removed. `WritingSessionState.persona_id: str | None`
replaces `persona: WritingPersona | None`. ORM and CRUD updated accordingly. Migration 0013
adds the provenance columns and all setup/config fields.

---

## Decision 3: Mentor/Peer orientation is resolved from the Persona Registry

**Decision:** Orientation (MENTOR / PEER) is a validated field on the resolved
`PersonaProfile`. `WritingSessionState` persists persona provenance only; it does not
duplicate orientation. `WritingModeMetadata` snapshots resolved orientation for
historical provenance.

**Consequence:** No `orientation` field on `WritingSessionState`. `WritingModeMetadata`
snapshots `relationship_orientation` resolved from the profile active at turn time.

---

## Decision 4: The Persona Registry is mode-aware

**Decision:** Issue 17 enables Writing-mode personas only, but `PersonaProfile.supported_modes`
allows future RPG or Branching availability without redesigning the registry.

**Consequence:** `SupportedMode` enum added with `WRITING`, `RPG`, `BRANCHING` values.
`PersonaRegistryProvider.get_profile()` and `list_active()` accept `SupportedMode` as
a filter.

---

## Decision 5: Persona source anchors and UI descriptions are registry data

**Decision:** Each active persona has source tradition, source anchors, UI description,
signature move, demeanor tags, prompt fragment, and negative constraints as registry
fields. This supports future UI choice surfaces and guards against all personas
collapsing into generic wise-person soup.

**Consequence:** `PersonaProfile` Pydantic model includes all these fields with
`extra="forbid"`. Validated at load time.

---

## Decision 6: The registry is static and repo-owned in Issue 17

**Decision:** No database-backed persona CMS, admin surface, marketplace, hosted
persona catalog, or user-defined persona authoring system in this issue.

**Consequence:** Registry lives at
`src/afterworlds/modes/personas/profiles/writing_personas.v1.json`. The static
`JsonPersonaRegistry` implementation loads and validates it at startup.

---

## Decision 7: Writing mode extends the existing WritingSessionState / writing_session_states persistence surface

**Decision:** Do not create a parallel WritingConfig table.

**Rationale:** One persisted session state per story per mode is the correct
granularity. A separate config table adds a join and new transaction boundary without
adding semantic value.

**Consequence:** Migration 0013 adds all new fields to `writing_session_states`.

---

## Decision 8: Writing output uses the ordinary Writer path with Writing-mode prompt injection

**Decision:** Unlike Issue 16's `BranchingWriterService`, Writing mode produces
ordinary prose and reuses the plain Writer path. No sibling writer service.
`WriterService.write()` and `WriterResult` are not widened. The existing
`load_mode_contract(StoryMode.WRITING)` already loads `writing_mode.md` into
`StablePrefix.system_prompt`.

**Consequence:** No `WritingWriterService`. Writing configuration and persona profile
are rendered into the stable prefix context by `WritingContextRenderer`. Issue 9
`WriterService` is unchanged.

---

## Decision 9: Writing setup confirmation is an ordinary DELIVERED turn

**Decision:** No setup-specific disposition. Setup turns are `DELIVERED` turns with
`WritingWorkProductKind.SETUP_CONFIRMATION` recorded in `WritingModeMetadata`.

**Rationale:** Setup narrative is canon-trackable; setup turns create Nodes and persist
like any other delivered turn.

**Consequence:** No new `PipelineDisposition`. Setup gating enforced by code checking
`play_status` and required field presence.

---

## Decision 10: Durable OOC Writing configuration updates are transaction-scoped

**Decision:** OOC updates to persona, critique intensity, authoring controls, beat
constraints, version pointers, and play status are written inside the existing OOC
orchestration transaction and commit only with `OOC_HANDLED`.

**Rationale:** Decoupling config write from OOC Turn persistence would create a
two-phase-commit problem — same invariant as ADR-016 Decision 4.

**Consequence:** `WritingOocConfigExtractorService` added to
`pipeline/writing/ooc_config_extractor.py`. `apply_writing_config_update` CRUD
helper added. Writing OOC extraction is best-effort; failure skips config persistence
without blocking `OOC_HANDLED` delivery.

---

## Decision 11: Writing canon eligibility is code-owned and explicit

**Decision:** In v1, no turn is automatically promoted to `EXTRACTOR_ELIGIBLE`.
Classifier output, prompt wording, Writer prose, frontend implication, and heuristic
detection do not promote eligibility. `WritingTurnRequest.canon_eligibility_override`
is the only v1 promoter.

**Rationale:** Writing mode has the highest risk of accidental canon pollution —
critique, alternate approaches, brainstorming, exercises, and beat plans are not
story events.

**Consequence:** `WritingCanonEligibility` enum: `EXTRACTOR_ELIGIBLE` /
`NON_CANON_SUPPORT`. Cross-field validator enforces `EXTRACTOR_ELIGIBLE` only for
`PROSE_CONTINUATION`, `DRAFT_PROSE`, and `REVISION`.

---

## Decision 12: Non-canon Writing support output discards Extractor proposals

**Decision:** For `NON_CANON_SUPPORT` turns, Extractor proposals are discarded before
Story Bible routing. The Extractor LLM call runs; proposals are discarded rather than
the pass being skipped entirely.

**Rationale:** Running-and-discarding preserves 12c pipeline ordering and maintains
observability. `skip_story_bible_routing: bool = False` parameter added to
`ExtractorService.extract()`.

**Consequence:** When `skip_story_bible_routing=True`, `route_extractor_proposals()`
is not called. Orchestrator passes this flag for `NON_CANON_SUPPORT` Writing turns.

---

## Decision 13: Minimal version pointers are provenance references, not version history

**Decision:** `WritingVersionPointer` may point to prior Turns, Nodes, draft labels,
current working segments, or generated candidates. They must not imply snapshot trees,
restore workflows, compare views, branch management, or manuscript-versioning UI.

**Consequence:** `WritingVersionPointer` model enforces non-empty label, at least one
source reference, and prohibits version-graph semantics.

---

## Mode-Specific OOC Handler — Known Unknown Resolution

ADR-016 noted that Writing mode OOC handler remained OPEN. Issue 17 resolves this:

- `docs/prompts/writing_ooc_handler.md` created.
- `OrchestratorService._run_ooc()` extended for `StoryMode.WRITING`.
- `load_writing_ooc_handler_prompt()` loader added.
- `known_unknowns.md` updated: Writing OOC handler, persona behavioral details,
  and prose parity constraint marked RESOLVED.

---

## Deferral Set

Deferred explicitly: dynamic persona catalog, persona marketplace, user-created
personas, historical registry/profile-version lookup, fingerprint mismatch handling,
automatic canon-eligibility promotion, full version history, draft branching, snapshot
trees, restore/rollback, compare views, manuscript evolution tooling, ChromaDB
retrieval memory (Issue 18), frontend/HTTP rendering (Issue 19),
`work_product_kind` trust-boundary enforcement for non-backend callers (Issue 19),
Rolling Summary mode-awareness for Writing canon vs. non-canon output.

---

## Architecture Notes

No drift from design principles for Decisions 1–13.

**Rolling Summary limitation (Decision 6 seam):** Rolling Summary is not mode-aware
in v1. `WritingModeMetadata.canon_eligibility` and `work_product_kind` are persisted
on each Turn/Node so a future issue can retroactively filter non-canon output from
the Rolling Summary window.

**`work_product_kind` trust boundary (Issue 19 note):** In v1, `work_product_kind`
is caller-trusted because the caller is backend-only. When Issue 19 introduces a
non-backend caller, the request's self-asserted kind becomes the trust boundary gating
canon eligibility. This must be enforced at the HTTP/entry-point layer in Issue 19.
