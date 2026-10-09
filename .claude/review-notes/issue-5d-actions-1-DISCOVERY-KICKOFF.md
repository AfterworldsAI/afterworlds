# CRD Issue 5d: Claude Code kickoff for actions-1

Prepared 2026-09-05. This is a discovery/regeneration brief, not semantic acceptance.

You are the implementing engineer. Codex remains the adversarial reviewer. First complete a hygiene maintenance task in the existing repository at `D:\AI\Claude\afterworlds` to align local tracked files and branch state with verified `origin/main` and account for local-only material. Then begin fresh `actions-1` discovery in that same checkout. Establish whether the current schema can faithfully represent the entire batch before producing an acceptance-ready proposal. If it cannot, finish the bounded gap inventory and return the smallest necessary schema correction as a separate checkpoint; stop before implementing that correction or regenerating an acceptance-ready proposal. Schema remediation and its review are a separate next step.

## 1. Complete repository hygiene in the existing checkout

Owner instruction: work in `D:\AI\Claude\afterworlds`. Do not create a separate worktree or replacement checkout to bypass local misalignment. Hygiene is the first task and a prerequisite to discovery.

Fetch `origin/main` and verify it is exactly `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d`, the merge of #161. Codex verified this remote head on 2026-09-05. If it has advanced, inspect the intervening changes and reconcile the baseline before proceeding; do not silently substitute another accepted authority.

The existing checkout was observed with an older HEAD and many untracked historical proposals and generators. Inspect its current state rather than assuming that observation is unchanged. Complete the following maintenance before authoring `actions-1`:

- Inventory the current branch, upstream, HEAD, local `main`, ahead/behind and divergence state, tracked modifications, and untracked files. Inspect relevant ignored local state as needed to identify stale tooling or artifacts; do not expose credentials.
- Compare local work and historical review artifacts with their committed counterparts. Classify material as merged, unique work to preserve, retained review evidence, local configuration/runtime state, or confirmed disposable output. Preserve unique work and retained evidence, including byte identities and original paths if archival relocation is needed. Do not bulk-delete untracked files, overwrite unique copies, or commit local configuration and runtime data merely to make status clean.
- Bring the existing checkout's tracked files and local `main` to the verified remote baseline using ordinary checkout and fast-forward operations where possible. Inspect and reconcile divergence or obstructing local files first. Preserve unmerged commits and local changes with a named, recoverable disposition; do not use a destructive reset or treat a hidden stash as completed reconciliation. Updating files to their already-merged versions is authorized maintenance, not permission to rewrite accepted authority.
- Verify that the synchronized tracked tree matches the verified baseline, the committed oracle has the identities and totals below, and every remaining local-only item has an explicit disposition. Check that the local Python 3.12 environment can run the required tools; repair stale environment paths if needed. Do not hide unexplained drift with ignore rules.
- Record the before/after branch and commit state, file dispositions, maintenance performed, and verification in `.claude/review-notes/issue-5d-actions-1-HYGIENE-CHECKPOINT.md`. Keep maintenance evidence distinct from action authoring. Only genuinely ambiguous ownership or potential loss of unique work requires an Owner question; carry out routine reversible maintenance autonomously.

Once hygiene is complete, create a new `actions-1` branch from the verified baseline in this same checkout and continue the brief. Do not begin discovery while local alignment remains unresolved. Do not reuse historical payloads as generator input or reopen, regenerate, or alter accepted `hazards-1` or `conditions-1` content.

Read `CLAUDE.md` fully. Implementation authority is #137 and recorded Owner Decisions, accepted ADRs, and the applicable architecture and prompt contracts, in that order. `AGENTS.md` governs Codex's review; do not treat it as implementation authority. Engineering shapes remain your responsibility within the governing contracts.

## 2. Read the authority and bind the source

Read and cross-check:

- GitHub #137: https://github.com/AfterworldsAI/afterworlds/issues/137, including recorded Owner Decisions. It remains open.
- `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`, plus ADR-005c and `adr-005c-operational-reliability-amendment.md` for the downstream source trust boundary.
- The CRD Issue 5c Rev7 specification. Its local archive is `D:\AI\Claude\scratch\AW docs\Issue 5c - Rev7.md`; prefer the GitHub-uploaded version if a duplicate exists. Apply later accepted amendments rather than stale pre-implementation status text.
- `D:\AI\Claude\scratch\AW docs\Issue 5d_Discovery_Report_Rev2.md`. It supersedes Revision 1; use Revision 1 only where Rev2 expressly retains evidence. These reports are historical discovery, not authority to override #137 or current source.
- `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`, the actual bound CRD Issue 5c ledger/corpus, and `docs/architecture/srd-corpus-reproducibility.md`.
- Current `src/afterworlds/ingestion/mechanical/{representation,validation,proposal,accounting,acceptance,oracle,schema_lift,canonical,projection,bound_corpus}.py`, affected serializers/readers, and their tests.
- The committed accepted artifact, `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json`.
- `.claude/review-notes/issue-5d-hazards-1-schema5-REGEN-CHECKPOINT.md`, its executable generator, `issue-5d-hazards-1-ACCEPTANCE-CHECKPOINT.md`, and `issue-5d-schema-evolution-across-batches-CHECKPOINT.md`, for retained-proof and succession constraints. Use their process lessons, not their payloads as new semantic input.

Resolve repository-relative paths inside the synchronized existing checkout. Generators must derive their repository root from their own location and use committed inputs there. Local archive documents may inform review, but clean-checkout reproduction must not depend on that archive or other untracked files. Use CI for the independent clean-checkout reproduction check; this requirement does not authorize moving implementation into another worktree.

Verify the exact source binding:

| Field | Expected value |
|---|---|
| package UUID | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
| release | `5.2.1-corpus.36b786d8-fa2` |
| source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| transform/configuration hash | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` |
| bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` |
| persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` |

Use the real CRD Issue 5c pipeline and authoritative seam, not a geometry approximation or historical source-cut payload. Distinguish values independently re-derived during discovery from retained published-release evidence. Do not describe `build_candidate` as persisted-state verification, republish the source, or turn downstream discovery into a second CRD Issue 5c publication proof.

## 3. Freeze the two-batch review prior

Before generation, preserve the exact committed two-batch artifact as an immutable review fixture outside the production oracle directory, for example under `tests/ingestion/mechanical/data/`. Include that fixture in the eventual branch so retained proofs can run from a clean checkout after later acceptance. Pin it by content and Git blob, not an absolute path or platform-specific raw digest.

| Identity | Expected value |
|---|---|
| representation schema | `5d-representation-schema-5` |
| schema hash | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` |
| accepted file content SHA-256, LF-normalized | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` |
| accepted file Git blob | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` |
| oracle identity | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` |

The prior contains exactly `conditions-1` and `hazards-1`: 22 records, 281 spans, 69 components, 20 prose bindings, 0 relationships, 22 references, 281 provenance edges, and 281 acceptance records. Preserve obligations, acceptance batches and full diffs, proposal identities, schema anchors, and lift evidence too. `conditions-1` was reviewed under schema 3; `hazards-1` under schema 5. Existing succession is `3 -> 4 -> 5`, with `5d-lift-schema-3-to-4` and `5d-lift-schema-4-to-5`.

The frozen fixture is the sole accepted-prior input for combined validation and preservation proofs. Read the live oracle only as an unchanged-byte sentinel before and after the run. Do not couple retained artifacts to its future accumulating identity. All identities above must remain unchanged during this stage.

## 4. Discovery first: prove representability

Derive the batch boundary afresh from the source-tagged `[Action]` entries under Rules Definitions and the umbrella `Action` entry, then cross-check actual source membership. Inspect complete entries, continuation leaves, tables, qualifiers, examples, references, and relevant source outside the cut where it governs interpretation. Structural containers are evidence, not automatic semantic boundaries.

Produce a per-record obligation ledger mapping every source meaning to exact leaf/subspan coordinates, proposed claimant, typed shape or affirmative governing prose, and rationale. Identify any unsupported meaning explicitly. Classify substantive and supporting material honestly; do not hide a schema gap as supporting prose or use a prose-bound reason merely because the union lacks a field.

Directly examine these pressure points:

1. **Dash, SRD p.180:** extra movement for the current turn, equal to the selected Speed after modifiers, with special-speed selection on each use. `SpeedModificationFact` changes Speed; `MovementPermissionFact` grants a locomotion mode; neither description itself states this movement grant. Show whether any existing composition faithfully captures the amount, duration, and per-use selection. Do not encode Dash as doubling Speed, a movement cost, a fixed number copied from an example, or an unconditional permanent grant.
2. **Influence, p.184:** inspect the full willing/unwilling/hesitant branches, GM-selected check, suggested table, default DC, results, and retry restriction. The attitude effect is not globally unspecified: this entry points to the attitude entries, and Friendly (p.182) explicitly grants Advantage while Hostile (p.183) explicitly grants Disadvantage; Indifferent is on p.184. Follow those exact references. Do not invent a numeric modifier, select a suggested check as mandatory, or silently import new attitude records into the batch. If required reference targets or source ownership exceed the cut, expose the scope boundary separately from a representation defect.
3. **Attack, p.177:** distinguish the basic attack entitlement, per-attack equip/unequip choice and before/after timing, and conditional movement between multiple attacks. Show how the prerequisites and interleaving survive without inventing an attack bonus, granting extra movement or attacks, treating component order as execution order, or constructing a general rules engine.

These are minimum checks, not the full gap inventory. For every representability gap, state the mechanically distinct source meanings the current shape would collapse, the existing types considered, the smallest proposed closed typed correction, and representative sibling rules. Distinguish issue-scoped schema work, specification correction, scope leak, Known Unknown, and `[OWNER DECISION]:` residue. Do not decide new game semantics or downstream ownership in code.

Historical August canaries are 13 records, 92 leaves, 149 classification spans, 19 components, 16 facts, 7 prose bindings, 12 references, and 39 obligations. They predate schema 5. Derive fresh counts independently and explain each difference from the bound source; do not force these totals or reuse the old proposal/generator's semantic payload. Label diagnostic comparisons as historical.

If any required meaning remains unrepresentable or any governing boundary unresolved, return the discovery ledger and schema/scope checkpoint now. Do not produce an acceptance-ready proposal or silently widen schema 5. Complete the bounded sibling map before recommending patches so review does not become another sequence of one-clause schema changes. Any later schema step must separately address version/hash succession, old-declaration legality, wire identity, persistence and overrides where affected, and unchanged accepted evidence.

## 5. Regenerate only if the schema gate is clear

If fresh discovery proves that schema 5 already suffices and no blocking boundary remains, author a fresh proposal, audit, executable generator, and checkpoint under `.claude/review-notes/`, with names beginning `issue-5d-actions-1-schema5-REGEN-`. Preserve earlier artifacts. Cut spans from bound source at run time and fail on source drift. Keep proposal review state `PROPOSED`.

Required executable evidence:

- Exact per-leaf partition and text reconstruction; closed reason codes; complete primary/contextual provenance and per-record obligations; no lost qualifiers or duplicate consequences.
- Standalone shape, schema, and representation validation. Enumerate any cross-batch missing-target findings by exact source and target and assert that exact set, rather than demanding a misleading standalone zero or allowing a broad exception.
- Combined validation beside the frozen accepted `conditions-1` plus `hazards-1`, without recording acceptance. A missing target outside those batches is a disclosed blocker, not permission to add authority silently. Combined representation findings must be zero before claiming readiness.
- Zero overlap using canonical collection keys for all six representation collections and accepted span scope. Every prior element must survive unchanged, with no movement, loss, replacement, coalescing, or reordering in the combined in-memory representation. Also preserve all accepted spans, obligations, batches, diffs, acceptance records, schema anchors, and existing lift evidence.
- Declared-schema wire round trips and semantic identity checks. Do not relabel prior review anchors to schema 5 or rewrite historical evidence.
- Before/after byte preservation of the frozen fixture, live oracle, and retained accepted evidence.
- Explicit UTF-8/LF outputs, no embedded absolute checkout paths or volatile data, and identical final artifact bytes from independent processes with different hash seeds and a clean checkout. Report commands, input identities, resulting proposal identity, and artifact content hashes/Git blobs.

Passing validators proves admissibility, not semantic truth. The checkpoint must explain source-to-representation fidelity and disclose every remaining limitation; do not claim Owner acceptance.

## 6. Gates and return package

Use the repository's Python 3.12 toolchain. Establish the deterministic `detect-secrets` baseline at the beginning and individually inspect new findings as artifacts appear, including hash literals. Record justified false-positive treatment; do not disable scanning or broadly exclude generated artifacts. Run applicable repository gates and report exact commands, results, and branch head. Preserve any failures as evidence rather than presenting unrun checks as passed.

Separate whole-PR measurements (`verified base...final head`) from individual-commit measurements and runtime measurements. State which comparison every file/line/test/timing total describes. Include Architecture Notes: `No drift from design principles` only when accurate; otherwise state the boundary, authority, and deferred risk.

Include the completed hygiene checkpoint in the return package. If hygiene encounters an unresolved risk to unique work, report that specific blocker and do not begin discovery. Otherwise return either:

- **Schema/boundary stop:** branch/base, exact source binding, frozen prior proof, complete discovery/obligation ledger, smallest schema correction or ownership question, representative sibling evidence, and explicit reasons regeneration has not begun; or
- **Reviewable proposal:** all of the above with a clear schema sufficiency argument, proposal/audit/generator/checkpoint paths, identity and determinism evidence, exact standalone/combined findings, preservation proof, and applicable gate results.

Do not call `accept_proposal`, alter accepted authority, publish, activate, retire, merge the branch, or close #137. Completing `actions-1` completes this batch worklist, not by itself the full-corpus or activation obligations of CRD Issue 5d. Stop for Codex's inspection of the actual artifacts and an independent semantic review before any recommendation of Owner acceptance.
