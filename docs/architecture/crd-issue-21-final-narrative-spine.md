# CRD Issue 21 — Final Narrative Spine Demo

**Status:** Accepted by the Owner on 2026-10-16 with its [Integration Prerequisite Contracts](crd-issue-21-integration-prerequisites.md); implementation authorized. GitHub publication, merge, auto-merge, deployment, shared-runtime operations and Rules Package publication/activation remain unauthorized.  
**Governing issue:** the Owner authorized publication of this governing issue on 2026-10-17; it is published as [#203](https://github.com/AfterworldsAI/afterworlds/issues/203), with the three accepted prerequisite contracts linked as its comments (exact body and AC1–11 readback verified 2026-10-17). That publication authorized no implementation push, PR or merge. Later on 2026-10-17 the Owner conditionally authorized commit, push and a PR for the reviewed candidate after satisfactory Codex review and local verification, holding at merge; merge, auto-merge, deployment, shared-runtime operations and Rules Package publication/activation remain unauthorized.  
**Prepared against:** main `a08f7aac88748c39464ddc86b6115a90dd7b6cd0`, including accepted PR #200.  
**Revised:** 2026-10-16 to the two-mode v1 scope of [ADR-017b](../decisions/adr-017b-writing-v1-deferral.md) (Writing deferred). Its separate release-scope prerequisite merged as PR #202. Startup was rechecked against main `3f638667512be1a7c1a885d566724ba827c09258`; merging the prerequisite did not accept this draft. The Owner accepted this draft and the prerequisite contracts on 2026-10-16; the readiness prerequisites below are implemented as accepted prerequisite scope (ADR-016b, ADR-006b) and are verified by the CRD Issue 21 evidence, not by that acceptance.

## Goal

Verify that Branching and RPG operate coherently through the user-facing Afterworlds application on both hosted and BYOK access paths. Writing is deferred from v1 (ADR-017b) and is not demonstrated here.

Demonstrate cooperation among the existing narrative pipeline, persistence, memory layers, Rules Package integration, entitlements and frontend/API. Correct only narrow integration defects whose contracts and ownership are already settled.

CRD Issue 21 is the narrative-spine gate. Passing it does not establish public-launch readiness.

## Background and Architectural Position

The governing scope is defined in the Construction Readiness Document’s CRD Issue 21 section and Items 16–17.

Existing services retain their responsibilities:

- Core pipeline and transaction behavior: CRD Issues 7–12c.
- Runtime entitlements and settlement: CRD Issue 13 and ADR-013.
- Credentials, provider selection and refusal fallback: CRD Issues 14a/14b and their ADRs.
- Mode behavior: CRD Issues 15–17, including accepted RPG follow-ups and ADR-015b.
- Retrieval Memory: CRD Issue 18 and ADR-018.
- Frontend/API and account configuration: CRD Issues 19/19b/20.
- v1 mode availability (RPG and Branching; Writing deferred): ADR-017b and its release-scope change.

Accepted component and integration proofs remain valid within their demonstrated boundaries. They do not, by themselves, establish that the complete product path works.

Current main exposes several verification gaps:

- Browser tests demonstrate Freeform Branching; Hybrid and True CYOA remain disabled pending product integration.
- The product path reads Rolling Summary, but its supplied generator returns empty text and no production compression caller was found.
- Existing canned fake-provider tests bypass credential-based provider resolution and generally return empty canon proposals, Safety concerns and contradiction violations.

These are starting findings for verification and boundary classification, not an instruction to redesign those systems.

## Readiness Prerequisites — Recorded Decisions and Bounded Dependencies

The two integration gaps have been traced and their required product choices recorded. Their complete proposed contracts are in [Integration Prerequisite Contracts](crd-issue-21-integration-prerequisites.md). Those contract extensions required Owner acceptance and separate implementation authorization, both given on 2026-10-16; they are not silently absorbed into CRD Issue 21's narrow wiring allowance.

### Branching product integration

**Recorded Owner Decision (2026-10-16):** setup saves configuration; a separate **Begin story** action generates the first playable scene and, for card styles, the first selectable cards. Setup confirmation does not automatically generate the opening.

The prerequisite defines the saved-setup/start/play transition, explicit start operation, pipeline and access behavior, atomic delivery, failed/repeated-start handling and persisted reload state. It preserves True CYOA's ordinary-play selection guard; startup must not be disguised as a choice against an empty card set. Reconcile the accepted extension with ADR-016 before implementation.

Already-settled corrections remain narrow integration work: inject the owning Branching writer, selection and OOC services; supply valid persisted card-count configuration; and expose authoritative committed cards in turn responses and reload reads. Preserve code-owned affordances, cadence, selection/annotation validation, OOC behavior, the paraphrase-classifier limitation and deferred graph traversal.

Proof starts from fresh built-app stories without seeded cards and covers setup, distinct Begin, opening, selection/continuation and reload across all styles and hosted/BYOK. Include invalid selection, OOC changes and failed/repeated Begin. AC1, AC2 and AC5 cannot pass merely because the controls are enabled.

### Automatic Rolling Summary advancement

**Recorded Owner Decisions (2026-10-16):** a due Rolling Summary and the narrative Turn/canon commit atomically on the selected hosted/BYOK path; generation failure blocks delivery and rolls back the turn under existing non-billable failure rules. Only delivered ordinary Branching/RPG narrative counts toward provisional N = 10, including the first playable opening. Setup-only, OOC, pending roll/decision steps and blocked/refused/errored attempts are excluded.

The prerequisite defines delivery-time eligibility/provenance, ordered incremental input, generic generation/non-empty output validation, lightweight provider pass and usage accounting, transaction placement, typed failures, retry/idempotency and later context consumption under existing owners. Context Builder remains a reader. Reconcile this production contract in accepted authority before implementation; replacing its empty generator alone cannot establish advancement.

Proof uses actual product turns crossing the eligible threshold, persisted summary versions/coverage and later production-context use. Cover exclusion, isolation, refusal/error/rollback, retry, hosted usage and BYOK non-deduction. Manual compression or seeded summaries do not satisfy AC5; affected AC4/AC6 guarantees must also be demonstrated.

Retain ADR-0010's provisional threshold, GitHub #65's concurrent-generation cost deferral and Writing's ADR-017b deferral. No summary UI, calibration program, new database migration, shared-data reclassification or Writing semantics belong here.

### RPG product startup

**Accepted 2026-10-16** ([RPG Startup Prerequisite](crd-issue-21-rpg-startup-prerequisite.md), [ADR-015c](../decisions/adr-015c-rpg-product-startup.md)): fresh RPG stories complete world-first setup, choose a supported published Rules Package, create a character through GM-led conversation or a pasted completed sheet, accept a typed, adjudicable sheet under its exact binding, confirm configuration and enter play through the product path. Seeded character state does not satisfy AC1/AC2.

Both dependencies remain necessary for a passing spine verdict. Continue unaffected verification; splitting prerequisite work does not waive AC1–11. The Owner's 2026-10-16 acceptance authorizes implementation only; it creates no publication or merge authority.

## Owner Decisions and Deferred Questions

Preserve all accepted mode, access, credential, settlement and Rules Package contracts.

Existing deferrals remain deferred, including:

- True CYOA paraphrase-classification policy.
- Pending-roll cancellation, expiration and rewind.
- Writing mode and selectable personas, deferred from v1 by ADR-017b: Writing setup, Chiron/persona behavior, Writing generation and other Writing positive-use scenarios.
- Writing prose parity, automatic canon promotion and full version history.
- Writing-specific Rolling Summary eligibility semantics.
- Empirical finalization of the provisional summary interval.
- Unverified OpenRouter cache behavior.
- Commercial prices, allowances, additional-usage mechanism and numeric burn estimates.

CRD Issue 21 does not resolve these questions merely because a demo encounters them.

## In Scope

- Reproducible end-to-end verification of Branching and RPG on hosted and BYOK paths.
- Reference to ADR-017b's focused proof that Writing and persona entry points are closed (reused, not re-implemented).
- Built-app browser and API integration tests using isolated disposable stores.
- Observable checks of persisted outcomes, cross-turn continuity, access selection and settlement.
- Targeted failure-path verification across participating systems.
- Narrow wiring, dependency-injection, DTO, fixture or orchestration-seam corrections under settled contracts.
- A concise findings and acceptance-evidence record.

## Out of Scope

- Changes to architecture, ownership, schemas, prompt contracts, mode semantics, provider behavior, retrieval design or entitlement policy.
- New user-facing feature scope or broad refactoring.
- Rules corpus regeneration, acceptance, publication or activation in shared environments.
- Support/compliance workflows owned by CRD Issue 22.
- Trial lifecycle and payment integration owned by CRD Issue 23.
- Pricing calibration, consumption-measurement infrastructure or numeric estimates.
- Real provider credentials, paid provider calls, shared-runtime operations or deployment.

## Required Behavior

### 1. Product-path demonstration

Demonstrate a representative complete interaction for each combination:

| Mode | Hosted | BYOK |
|---|---|---|
| Branching | Required | Required |
| RPG | Required | Required |
| Writing | Deferred (ADR-017b) | Deferred (ADR-017b) |

Each demonstration must exercise the built frontend, existing API and owning backend services. Verify setup, submission, authoritative outcome display and recovery of persisted state after reload.

Across the matrix and focused supporting tests, cover:

- **Branching:** Freeform-only, Hybrid and True CYOA; typed options and explicit selection; persisted interaction style and cadence; invalid-input handling and OOC behavior. Preserve the known classifier limitation.
- **RPG:** accepted setup and character binding, a supported deterministic mechanical interaction, player-roll or decision handling where required, and narration through the existing sequence/resume path. Preserve hidden-information and roll-result guarantees.
- **Writing:** deferred by ADR-017b — not demonstrated, passed, failed or skipped. Its persona and Mentor/Peer configuration, setup confirmation, prose/support interactions and provenance are not v1 release requirements. Reference ADR-017b's proof that Writing is unavailable: the API refuses Writing creation, setup and turns with `mode_unavailable` before any write, access-path selection, provider call or settlement, on hosted and BYOK (`tests/api/test_mode_availability.py`); the persona gallery is empty; the built app offers only Branching and RPG, defaulting to Branching (`frontend/src/StoryList.test.tsx`, `frontend/e2e/spine.spec.ts`). Retained Writing canon/non-canon protections stay covered by their internal tests and are not re-verified here.

A canned delivery response or a setup-only interaction is insufficient proof of an entire mode.

### 2. Access paths and settlement

Verify actual access-path selection and provider binding under the existing contracts.

Demonstrate:

- Hosted delivery and OOC settlement through approved entitlement events.
- No hosted-credit deduction for BYOK turns.
- Existing BYOK-first selection when both paths are runnable.
- Local BYOK operation independently of Cloud Services renewal.
- Typed refusal when no runnable path exists.
- No silent hosted/BYOK crossing during provider fallback.

Provider-routing proof must retain the production resolver, readiness and binding logic. Test doubles may replace external provider transport and credential storage; a resolver that always returns one fake adapter cannot prove those decisions.

### 3. Persistence and continuity

Verify meaningful state changes and later consumption, rather than only successful responses.

Demonstrate:

- Delivered Turn and eligible Story Bible changes persist through the approved transaction path.
- Later context uses committed canon and appropriate recent history.
- Rolling Summary advances under its approved contract and is consumed by later context.
- Eligible delivered material enters local ChromaDB Retrieval Memory and can be retrieved on a later turn.
- Story isolation and exclusion of ineligible, blocked or rolled-back material remain intact.
- RPG context and adjudication use the correct published Rules Package binding and supported Rules System Adapter capabilities.

Use isolated published Rules Package fixtures through existing supported mechanisms. Preserve accepted authority and unaffected native proofs.

Do not introduce summary-generation, eligibility, billing or transaction semantics to conceal a missing integration contract.

### 4. Pipeline and failure behavior

Verify the ordinary narrative path preserves classification before context assembly, Planner → Writer → Extractor → Contradiction, conditional Safety checks and stable-prefix reuse.

Use targeted product-path scenarios to demonstrate:

- Input and output Safety blocks.
- Contradiction blocking.
- Typed provider refusal and permitted bounded fallback.
- Malformed provider output or operational failure.
- Applicable transaction rollback and retrieval-ingestion exclusion.
- Truthful frontend outcomes without displaying undelivered candidate prose.

Preserve existing non-billable outcomes and the distinction between provider refusal and Safety verdict.

### 5. Integration boundary

A correction belongs in CRD Issue 21 only when the required behavior, owner and failure semantics are already clear.

If completion requires a new contract, policy, schema, prompt change or broader feature implementation:

1. Record the observed failure and affected acceptance criterion.
2. Classify the boundary and identify the owning follow-up.
3. Surface any required Owner Decision before implementation.

Splitting a follow-up does not turn an unmet spine requirement into a pass. Continue unaffected verification, but keep the overall spine verdict blocked until required dependencies are satisfied.

Repeated hotspot review or feedback about ownership and semantics triggers the established boundary check before further patches.

## Testing

Use deterministic scripted provider responses and synthetic credentials with disposable SQLite, ChromaDB and credential stores. Preserve real participating service, parser, routing and transaction behavior.

The evidence must distinguish:

- Built-app browser coverage.
- API/service integration coverage.
- Reused accepted component or native proofs.
- External behavior replaced by test doubles.
- Remaining limitations or blocked criteria.

Default verification requires no real provider contact. Scripted responses establish integration behavior; they do not establish live-model narrative quality, cache performance or commercial consumption estimates.

Reuse unaffected proofs. Rerun checks when changes invalidate them or binding delivery gates require them. Preserve failed and interrupted verdicts alongside their corrections and reruns.

## Acceptance Criteria

1. Branching and RPG complete representative built-app interactions on both hosted and BYOK paths. Writing is deferred by ADR-017b; the evidence references that change's proof that Writing entry points are closed.
2. Accepted mode-specific behaviors are covered, including Branching styles and RPG mechanical lifecycle. Writing authorship/canon boundaries are deferred with Writing (ADR-017b).
3. Production access selection and provider binding are verified without bypassing the decisions under test.
4. Hosted settlement, BYOK non-deduction, unavailable-access behavior and fallback boundaries match existing contracts.
5. Persistence, Story Bible, Rolling Summary, Retrieval Memory and Rules Package interactions are demonstrated through observable cross-turn behavior.
6. Safety, contradiction, refusal and operational-failure scenarios preserve transaction, delivery and billing guarantees.
7. Tests use isolated stores and synthetic credentials; secrets and hidden RPG information remain protected.
8. Findings are classified and narrowly corrected or assigned to explicit follow-ups. No required criterion is silently waived.
9. Evidence identifies the reviewed revision, commands/results, substitutions, reused proofs and unresolved limitations.
10. Applicable repository gates, required final-head CI and Codex review pass without weakening tests, coverage, audits or secret detection.
11. The final report states whether the narrative-spine gate passed or remains blocked, separately from public-launch readiness.

## Documentation and Architecture Notes

Provide a reproducible demo guide and concise acceptance-evidence matrix.

Record material integration findings, their owning contracts, corrections and follow-up dispositions. Reconcile documentation where necessary without rewriting accepted history or declaring deferred questions resolved.

PR Architecture Notes must state either **“No drift from design principles”** or describe the exact authorized deviation and remaining risk.

Public launch continues to require CRD Issues 22/23, applicable security/compliance gates and Owner approval.

## Branch and Merge

Claude Code implements under the Owner's explicit 2026-10-16 authorization; Codex reviews.

Use a clean isolated checkout from refreshed main. Preserve the protected dirty checkout, accepted artifacts and unaffected proofs.

Acceptance authorizes implementation only: no GitHub publication, merge, auto-merge, shared-runtime operation or Rules Package publication/activation.
