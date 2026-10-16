# ADR-017b — Writing Mode Deferred from the v1 Release

**Date:** 2026-10-16
**Issue:** Release-scope prerequisite to CRD Issue 21; amends the v1 scope of CRD Issue 17
**Status:** Accepted (Owner decision, 2026-10-16 — Option 2)
**Amends:** ADR-017 (release availability only). **Supersedes:** the unmerged
Chiron-only ADR-017a proposal.

## Context

ADR-017 and CRD Issue 17 implemented Writing mode: the Persona Registry with six
profiles, Mentor/Peer orientation, setup and authoring controls, beat
constraints, canon-eligibility rules and minimal version pointers. Design,
Construction Readiness and the CRD Issue 21 draft still required RPG,
Branching and Writing in v1.

A later proposal (ADR-017a, never merged) would have released Writing with
Chiron as the only active persona, collapsed Mentor/Peer and retuned prompts.
The Owner instead chose to release v1 with two modes and defer Writing.

## Owner Decisions

1. v1 has two supported user-facing modes: **RPG and Branching**. Writing is
   unavailable through the released application. No Writing persona is
   offered, including Chiron.
2. There are no current Sojourners and no existing Writing sessions. No
   legacy-session handling, migration, conversion, recovery or
   backward-compatibility workflow is designed. Synthetic fixtures are not
   customer data; local development data is not deleted.
3. The implemented Writing machinery is preserved: registry, six profiles,
   prompt artifacts, internal models, schema, services and useful tests.
4. Writing-specific feature development and persona refinement stop for v1.
   Disabling Writing's product entry points is in scope; shared fixes stay
   with their existing owners.
5. RPG and Branching keep their existing mode-prompt voices. No persona
   profiles, selection, injection, fallback personalities or performance
   controls are added to either mode.
6. The Chiron-only ADR-017a proposal is superseded: no one-active-persona
   compromise, Mentor/Peer collapse, prompt retuning or its open-question slate.
7. v1 and CRD Issue 21 acceptance are revised explicitly to two modes. Writing
   is removed from the release requirement, not silently skipped.

## Implementation (this change)

- **Release policy.** `afterworlds/modes/availability.py` names the released
  subset of `StoryMode` (`RPG`, `BRANCHING`). `StoryMode.WRITING`, its schema
  variants and migrations stay; representation is not availability.
- **Application boundary.** `require_released_mode` (`api/story_bootstrap.py`)
  is the single API refusal: `422` with error code `mode_unavailable` and
  `detail.mode`. It runs first in story creation, structured setup and turn
  submission (which RPG resume shares), so a refused request creates no story,
  session state, anchor or turn, probes no access path, calls no provider and
  reserves or settles nothing. It never maps Writing to another mode.
- **Persona gallery.** `GET /api/personas` keeps its shape and returns empty
  `mentors` and `peers`. Registry data and profile versions are unchanged;
  `HIDDEN` availability is not used as a mode switch.
- **Frontend.** New stories offer Branching (default) and RPG only. A Writing
  story's setup screen shows an unavailable notice instead of persona or setup
  controls. `WritingSetupForm` is retained but not routed.
- **Retained internals.** Orchestrator Writing dispatch, OOC configuration,
  canon-eligibility and Rolling Summary handling, and Retrieval Memory Writing
  eligibility (ADR-018 D6) stay intact and tested. API-level Writing route tests
  run behind a test-only fixture that re-admits Writing; it is not a release or
  deployment flag.

## Consequences

- Hosted and BYOK expose the same two modes. Credit rules, licensing, Cloud
  Services rights, Safety, provider routing and Rules Package authority are
  unchanged; this is release availability, not an entitlement tier.
- ADR-017's decisions remain the accepted contract for the retained Writing
  implementation. Its v1 release availability is replaced by this ADR.
- ADR-020 Decision 5's representative consumption measurement covers the v1
  release modes, RPG and Branching. Measurement ownership is unchanged.
- CRD Issue 21 verifies RPG and Branching and references this change's proof
  that Writing entry points are closed. Its revised draft is
  [`docs/architecture/crd-issue-21-final-narrative-spine.md`](../architecture/crd-issue-21-final-narrative-spine.md).

## Post-v1 Direction (recorded, not implemented)

- Writing becomes a collaborator for creating RPG adventures and Branching
  stories. Structural craft, sentence-level help, sensory detail, consistency
  and player agency remain central; knowledge of supported Afterworlds
  capabilities supplements them.
- The first future goal is a small private create → play → revise loop. Its
  content handoff, author approval, secrets, and separation of authoring state
  from playthrough state are decided in that future scope.
- An authoring Mentor collaborates outside the story; a runtime narrator
  performs within it. They are distinct roles. Implementation may be shared
  where appropriate; this decision does not commit to one universal persona
  architecture.
- Publishing, discovery, ratings, moderation, creator accounts/marketplaces and
  selectable runtime temperaments remain deferred. Availability flags do not
  implement them.
- Chiron's future role, the eventual cast and any orientation/schema changes
  are deferred.

This ADR creates no content-package schema, authoring-to-play converter,
system-knowledge ingestion, publishing service, prompt contract or persona
plumbing.
