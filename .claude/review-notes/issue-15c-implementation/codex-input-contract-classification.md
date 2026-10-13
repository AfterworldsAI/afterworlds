# CRD Issue 15c input-contract classification

Reviewed 12 October 2026. Read-only classification of `boundary-input-contracts.md` and the complete approved `../issue-15c-preparation/issue-draft.md`. Current-task Library guidance reused: Review 2026-09-25 and Prompting 2026-10-05. Native C5 acceptance/recording is a coordinator-supplied premise (SHA `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69`), not independently reverified here. No candidate acceptance, implementation, tests, imports, stores, Git operations or engineer launch occurred.

## Verdict

Two narrow input-authority choices remain: whether GameMaster assertions can establish spatial context and elapsed fiction time. Storage organization, typed source-bound acquisition records, tool variants and explicit actor-turn edges do not require a fresh Owner Decision merely because they add state. The revised proposal needs the concrete corrections below before implementation.

## Minimum Owner Decision

**Recommended question:** May the GameMaster supply auditable contextual facts for bounded CRD Issue 15c mechanics: (1) operation-specific spatial relationships and movement/area facts selected from code-generated, source-bound options, and (2) explicit elapsed-fiction-time attestations tied to a recorded recovery/condition instance? Code would retain numeric thresholds, dice, eligibility, consequences and atomic mutations; missing or contradictory facts refuse. This would not authorize a general spatial engine, story clock, initiative scheduler or Story Bible writes.

Recommendation: approve this bounded contextual-input role, subject to the corrections below, rather than require a general coordinate/clock system. This is a recommendation, not an approval. The governing issue admits minimum position/timing state and GM selection (`issue-draft.md:18,21,41,45`) but does not explicitly establish model assertions as independent truth for these contextual facts. Defining the input's authority is distinct from choosing its enum or table.

## Spatial input (OD-15c-1)

`boundary-input-contracts.md:36-40` correctly isolates the authority question. Source-threshold enums constrain the assertion's shape; they do not prove geometry. If the Owner authorizes GM contextual assertions, code can validate their source identity and consistency without pretending to independently measure the world.

The contract must cover the complete predicate set in `:27-32`, not just weapon range: Cleave's two relationships involving three subjects, area origin/shape/membership, movement toward a target and the source-required interval, and Push's direction and resulting displacement. Code derives allowed distances and effects; a GM choice cannot directly author a numeric mutation. Preserve the source's permitted choices rather than silently always choosing the maximum.

Bind assertions to the exact subjects, operation, source and current contextual revision. Spatially affected assertions become invalid after movement, including between linked attacks within a delivered turn. Require consistent refreshed facts for downstream operations; an operation-specific audit assertion must not become a reusable hidden position record. These are implementation requirements under `issue-draft.md:18-19,31-35`, not additional product decisions.

## Elapsed time (OD-15c-2)

The input origin in `boundary-input-contracts.md:60-61` is a genuine choice; a new general code-owned story clock is not required by CRD Issue 15c. Recommend explicit, auditable GM attestation bound to the current recovery/condition instance and anchor. Code draws and retains the source-prescribed recovery duration, derives the due condition and HP/condition result, and prevents duplicate consumption or carrying time across an invalidated recovery instance. Do not repeatedly add assertions of cumulative time, infer time from narrative turns/rounds, or allow the GM to select the recovery outcome.

**Correction:** `:62` overstates that knockout is unaffected. Its initial application need not wait for elapsed time, but its required Unconscious-ending consequence includes completion of a Short Rest. The source explicitly says this at `docs/sources/community/dnd-5e-srd-markdown/playing-the-game.md:1203`; a Short Rest is a qualified one-hour period (`rules-glossary.md:1277-1293`). Accepted representation records `starts`, `ends_after` and early-ending events (`src/afterworlds/ingestion/mechanical/representation.py:6281-6293`); the approved issue requires these bounded ending consequences (`issue-draft.md:39`). Include their minimum time/completion authority without admitting general rest recovery.

## Actor edges and round rule

Explicit actor-turn edges are already in scope (`issue-draft.md:18,20,41`). Persisted identity, revision checks, matching begin/end and once-only edge application are ordinary implementation.

**Reject `boundary-input-contracts.md:48` as written.** With only A having begun and ended, every participant who began has ended; beginning A again immediately advances the round. B need never act. This does not enforce the asserted once-per-round bound, and unique request IDs alone do not prevent manufacturing successive fresh turns. Remove the automatic round/scheduling rule; implement only the explicitly authorized actor-edge input and source-timed effects. If actual round scheduling is necessary for a specific admitted rule, identify that rule and its exact authority instead of inventing encounter policy. No automatic round-to-time conversion is authorized (`:54`; issue non-goals `:17,45`).

## Other settled corrections

- **Zero HP:** `boundary-input-contracts.md:17` cannot substitute a Monsters/Animals template location for an explicit resolved subject classification. A pet can use an animal stat block. Record the subject's applicable source-backed treatment and any explicit per-subject exception; unresolved cases refuse (`issue-draft.md:41`). No new pet-treatment policy is approved.
- **Cross-binding:** `:21` now requires agreement and refusal, which is the appropriate in-scope direction. Compare every shared procedure actually contributing to the operation, including saves/effects where relevant; the listed attack/damage examples must not become an exhaustive omission. No precedence rule is approved.
- **Acquisition order/tool variants:** `:74,78` describe ordinary issue-scoped representation of required inputs (`issue-draft.md:17,21,32`), not Owner product choices. Validate identities and acquisition instances under source authority, preserve missingness, and account for persistence/version compatibility. Do not infer a missing chronology; ensure character level alone disambiguates the relevant source grant instance before relying on it. Source-category candidates in `:79` remain a separate semantic-completeness workstream.

## Limits

This note evaluates the proposed contracts, not gameplay completeness or exact-head merge readiness. Source excerpts corroborate the knockout timing dependency; this review did not re-audit the accepted native C5 artifact or all source predicates. Implementation, new semantic acceptance, shared-runtime publication/activation, app launch and merge remain under their existing gates.
