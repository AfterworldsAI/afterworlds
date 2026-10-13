# CRD Issue 15c — native transition review requirements

Read-only preparation on head `1473426762970dd532a01924dcfcb6183ccdf603`. No native generation, schema authoring, tests or store writes by Codex. This note grants no semantic acceptance.

Current C4 transition covers 11 of 24 batches. Recompute only if the final reviewed successor changes source placements. Replace the affected batches; preserve the other 13, rather than rerunning unaffected authoring.

## Required identity and preservation proof

- Schema 19 needs a real closed-family/field/vocabulary/invariant contract and exact 18→19 registry lift, not a version restamp. Existing G1 representation payloads must remain canonical-byte equivalent under the lift in every collection; original batch anchors and replay schemas remain historical identities. See `representation.py:8801,9016–9099`, `schema_lift.py:738–793,916–966`, `projection.py:917–935`, and `persistence.py:640–667`.
- Identity-match each prior affected batch's replayed proposal before provenance-aware excision. The G1 `issue-2b-g1-candidate/scripts/excise.py` precedent removes an element only if that batch stated it and it has no provenance outside the removed scope. Preserve shared elements, reference resolutions, release binding/semantic policy and prior lift history. See `acceptance.py:439–519,665–677`.
- Native source payloads must equal the independently reviewed raw source facts/formulas/predicates exactly, with complete component/provenance correspondence. Capability/storage/certification metadata must not be minted as SRD authority. Native qualifiers/options must survive serialization without silently dropping or adding semantics.
- Preserve untouched batch acceptance, review-unit and schema-anchor rows byte-identically; account for intended changes in affected batches and retain shared provenance. Pin all source files and prior G1/predecessor bytes. The G1 candidate `scripts/build_candidate.py` and `verify_candidate.py` supply prior native construction/verification precedent; reuse the invariant, not a blind script invocation against its default store.
- Use a private copy of the isolated G1 database. Simulated reviewer/time/rule receipts must be visibly labeled SIMULATION in a review-only preview outside committed accepted-oracle locations. Validation, persistence → reconstruction → identical projection payload/UUID, persisted digest and a read-only publication-gate check against that preview are appropriate isolated proofs. Verify cross-oracle refusal and unchanged prior bytes. Do not publish, activate, migrate a shared runtime or write real acceptance/recording/supersession evidence.

## Exact Owner acceptance packet

Pin prior G1 SHA; reviewed raw source-part hashes; schema-19 version/hash and lift ID; every replacement batch's rendered proposal SHA, proposal identity, scope and review-unit inventory; serialized preview SHA; oracle identity and projection UUID; preservation evidence; and the explicitly simulated receipt identity. An eventual real Owner receipt may replace only designated acceptance metadata after explicit acceptance, with the native semantic/proposal/projection identities remaining identical. G1 `issue-2b-g1-recording/record_successor.py:176–194` is the prior comparison precedent, not permission to run it.

Raw review readiness and native preview completion are review gates, not completion of CRD Issue 15c. Gameplay/state execution remains held until the exact native identity has independent review and explicit Owner semantic acceptance. Required final exact-head repository/CI gates, merge and runtime boundaries remain unchanged.
