<!-- markdownlint-disable -->
> **Recorded Owner Decision — 21 September 2026.** Authority rung 1 under
> `CLAUDE.md` ("The governing CRD issue and recorded Owner Decisions"), above the
> ADRs it amends. Captured verbatim from the Owner's handoff to Codex Desktop so
> the decision is reviewable in the repository without a local-only dependency.
> The body below is unmodified; only this banner and the clarification note were
> added.
>
> **Owner wording clarification (20 September 2026, applies to Step 2).** The
> corrected Markdown need not match the official PDF word for word. Its *meaning
> and relationships* must be faithful. Where wording differs, either restore the
> official wording or retain the Markdown when meaning is preserved. Do not force
> cosmetic identity and do not waive substantive differences.
>
> **Documents this decision amends** (each carries a banner citing this file):
> `docs/decisions/adr-005c-rules-authority-repair.md`,
> `docs/decisions/adr-005c-operational-reliability-amendment.md`,
> `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`,
> `docs/architecture/srd-corpus-reproducibility.md`,
> `docs/architecture/issue-5d-practical-reliability-draft.md`.
> Implementation state lives in
> `docs/architecture/issue-5c-5d-clean-restart.md`.

# Afterworlds — clean source and fresh 5c/5d construction

Owner handoff to Codex Desktop · 21 September 2026

## Assignment

Carry out the clean restart described below. Codex coordinates the work and independently reviews it; Claude implements through the established workflow. Use the automation already understood in this environment. The Owner should not have to relay routine implementation/review messages between agents.

This is an implementation handoff, superseding the earlier investigation-only assignment. Begin with repository discovery and a concrete first implementation phase; do not stop at another general recommendation. Work in reviewable stages and observe existing merge, publication, activation, and Owner-required acceptance boundaries. Do not invent additional approval gates for decisions already made here.

## Settled Owner decision

Quarantine the existing 5c corpus and 5d authority products. Verify and correct a pinned local copy of `downfallx/dnd-5e-srd-markdown` against the official WotC SRD 5.2.1 PDF. Build a fresh source corpus from that clean information, then construct 5d anew under practical, iterative improvement principles.

The Owner expressly prefers the confidence and reduced frustration of fresh construction, even if it eventually costs more tokens. Do not reopen this decision through migration-cost arguments, sunk-cost arguments, or existing document conventions. No one has played a game in RPG or Branching mode or written a sentence in Writing mode; do not invent a user compatibility obligation to preserve these authority products.

Useful knowledge and implementation may be salvaged. Existing acceptance, source identities, batch boundaries, provenance, and typed content are not inherited authority. There is no requirement to migrate old 5d provenance, preserve old leaf IDs, reproduce historical batch counts, or retain schemas solely for compatibility with the discarded products.

The investigation report's recommendations to retain accepted semantics through provenance regeneration are superseded. Any similar preservation recommendation in earlier retrospectives is also superseded. Their evidence and useful lessons remain available.

Quarantine is temporary reference material, not a second supported authority system. Retain it only while it provides concrete guidance. Remove obsolete working artifacts and paths once their useful lessons have been captured and dependencies addressed; normal Git history is sufficient historical retention. Do not conduct a general salvage audit before beginning clean work.

## Governing outcomes

The official WotC SRD 5.2.1 remains ultimate source authority. Community Markdown is a candidate transformation until verified. Its corrected local version can become Afterworlds' canonical machine-readable representation without becoming an independent rules authority.

Apply the August 3 operational-reliability standard and the September practical-reliability decisions to both 5c and 5d: complete in-scope coverage, faithful content and relationships, useful machine-readable structure, explainable and correctable mechanics, official-source citations, stable release identities, and detection of consequential omissions, stale reuse, corruption, and partial publication.

Full mechanically substantive SRD coverage remains the destination. It does not require encoding every grammatical distinction as a typed fact or implementing every rule as deterministic execution. Preserve faithful prose where a structured representation has no identified consumer benefit. Keep specified deterministic consequences and trust-relevant mechanics code-owned. Do not use this reset to transfer existing code-owned responsibilities to an LLM.

Avoid forensic proof topology, exhaustive leaf genealogy, duplicated validation implementations, per-batch infrastructure, or schema expansion without an actual gameplay, authoring, maintenance, or diagnostic benefit. Do not promise acceleration or token savings without measuring them.

## Starting evidence and inputs

These identify the investigation snapshot, not necessarily the current desktop checkout:

| Input | Investigated identity |
|---|---|
| Afterworlds main | `cf26e25b9a8392640e0e2912dbed715541c294e2` |
| Official source | `docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf`; 364 pages |
| Official PDF SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| Community repository | <https://github.com/downfallx/dnd-5e-srd-markdown> |
| Investigated community commit | `1b4b99dcb786cdd1a2fb26f8acec1551191f1ca4` |

Inspect the actual branch, worktree, current decisions, and runtime entry points before editing. Preserve unrelated work. A different source checksum requires resolving the discrepancy, not silently updating the expected checksum. Pin the community snapshot; do not silently follow upstream changes.

The community source contains Markdown **and embedded HTML tables**, including `colspan`, empty cells, and repeated ability-grid headers. Do not assume a pipe-table-only parser. Preserve required source attribution and licensing material.

The bounded investigation already established enough to justify this direction:

- Twelve representative cases exposed false tables, wrong ancestry, lost creature ownership, detached headers, fragmented prose, and incorrect cross-page spell-list assembly.
- Replaying 25 PDF pages reproduced 67 table inventory records, including false tables, while both concordance checks passed. Agreement with a detector-generated baseline did not establish correct source structure.
- Skills/Perception p.9; Armor/Chain Shirt p.92; Always-Prepared Spells p.104; Carpet of Flying p.215; Vulture Pack Tactics p.364; Archelon/Baboon pp.344–345; Barbarian progression p.28; Sorcerer lists pp.67–68; rarity/value and Command Word p.206 provide concrete regression families. Actions pp.9–10 and Multiclass Spellcaster p.26 are positive controls.
- Community tables passed 449 sampled header/data-cell comparisons plus visual and prose checks. **This was not full-source verification.** Completeness and fidelity remain work to perform.
- Word improved many passages but retained split tables, displaced rows, reordered spell-list fragments, and messy stat blocks. Do not start a Word normalizer. The DOCX is optional comparison material.
- Old accepted 5d meaning was not independently proved universally wrong. Its exclusion is the Owner's clean-start decision, not a fabricated claim that every old rule is false.

The earlier report is titled `Afterworlds-5c-source-structure-investigation-2026-09-21.md`. Use it if accessible, but this handoff is sufficient to begin; do not require the Owner to shuttle it before proceeding.

## Implementation sequence

### 1. Record the decision and establish quarantine

Record this Owner decision in the repository and reconcile conflicting authority in the same workstream. Inspect these known documents and their current successors:

- `docs/decisions/adr-005c-rules-authority-repair.md`
- `docs/decisions/adr-005c-operational-reliability-amendment.md`
- `docs/architecture/srd-corpus-reproducibility.md`
- `docs/decisions/adr-005d-complete-typed-mechanical-authority.md`
- `docs/architecture/issue-5d-practical-reliability-draft.md`
- Governing CRD Issue 5c/5d text and associated live issue authority.

Amend requirements that prescribe PDF-geometric atoms as the canonical interface, require downstream reconstruction of page layout, or require preserving old accepted products and their formats solely for historical compatibility. Retain operational outcomes, source/interpretation separation, meaningful release versioning, campaign version stability, and deliberate house-rule precedence. Cite this handoff as the Owner decision rather than requesting the same decision again. Prepare any required external authority synchronization through the established workflow.

Identify old ingestion, corpus selection, accepted-artifact loading, fallback, Rules Package, and retrieval/projection paths. Define the smallest practical quarantine that makes old products unavailable as active authority. Archiving files alone is insufficient if a selector or fallback still loads them. Do not destroy shared databases or unrelated data. Implement and test the isolation on the working branch; coordinate any shared-state operation under existing permissions.

### 2. Verify and correct the local Markdown source

Maintain one pinned, Afterworlds-controlled source copy. Add missing official content, remove community additions that are not official content, and correct altered wording or relationships. Separate harmless formatting normalization from content corrections. Record corrections economically with their official source locations; no elaborate chain-of-custody system.

Cover the entire document, not only the earlier samples. Use full-source comparison and an intelligible coverage inventory to account for sections, entries, prose, lists, and table contents. Resolve missing/extra text and unexplained differences against the PDF. Legitimate non-content differences such as repeated page furniture need a documented normalization policy. Do not silently exclude substantive material to obtain a passing comparison.

Text comparison alone is insufficient. Check relationships and boundaries: headings, row/column associations, categories, table continuations, footnotes, spell levels and legends, class progression, creature ownership, traits/actions, item prose, and cross-reference wording. Visually inspect the official PDF wherever extraction is ambiguous or a structural judgment matters. Cover every structural family and investigate discrepancies across the full source; use representative independent checks where repetition genuinely makes them sufficient. Repeated failures trigger a bounded sibling check of that family, not endless isolated patches or an unrelated corpus audit.

Codex reviews against the PDF independently of Claude's corrected output and comparison script. Another transform can help diagnose a disagreement but cannot settle it by majority vote.

Keep the corrected source provisional until substantive discrepancies are resolved. Report coverage and remaining uncertainty honestly; passing the old 449 spot checks is not qualification. If the community source proves materially different from the promising sample, present concrete evidence and the smallest alternative before changing the chosen approach.

### 3. Establish coherent source units and official citations

After qualification, implement the simplest deterministic ingestion path from the corrected source to a fresh 5c corpus. Preserve coherent paragraphs, lists, logical tables with headers/categories/notes, and record boundaries. 5c owns faithful document structure; 5d owns interpretation of rule meaning. 5d should not repair page layout before it can reason about a rule.

Choose unit sizes for useful consumption and citation; do not mechanically reproduce one chunk per geometric leaf. Keep implementation and schema changes proportional to actual needs. New identities and replacement fixtures are allowed; compatibility scaffolding for discarded products is not a goal.

Map normalized units to official PDF pages and contextual source locators. Scope matches by section/record before matching text; repeated passages must not silently attach to the first occurrence. Normalize typography and line wrapping without erasing rule-bearing distinctions. Use multiple page locators when needed and manually resolve ambiguous mappings where cheaper. Word page numbers are never official citations. A simple deterministic mapping with reviewable exceptions is preferable to a general proof engine.

Demonstrate reproducible logical output, wrong-source/stale-input detection, meaningful-change versioning, and rejection of incomplete or inconsistent publication. Build and verify in isolation before any production activation. Derived retrieval state, including Chroma where applicable, must refer to the new release and must not fall back to old authority.

### 4. Construct 5d freshly from the qualified source

Begin fresh semantic authoring only after the source qualification and coherent-unit boundary are established. Use the existing practical-reliability principles to determine useful structured inputs, faithful prose, and references. No old record becomes accepted because its predecessor was accepted.

Old material may suggest edge cases, terminology, consumer needs, or implementation approaches. Any reused content must earn its place through fresh comparison and acceptance against the clean source. Do not import the old artifact as a baseline and call that a restart. Retain helpers/types only where they solve an actual present requirement economically.

First exercise the shared authoring/review process on a coherent ordinary section with representative tricky siblings. Measure preparation effort, review rounds, custom code required, and unresolved interpretation work. Correct a recurring boundary problem before multiplying batches. Then proceed iteratively toward full scope; do not turn the initial section into a permanent reduced MVP or require the Owner to relay each batch.

Use shared tooling and source-backed regression tests. Avoid a new validator or schema vocabulary for each passage unless the actual consumer requires it. Preserve distinctions between source meaning, structured representation, implementation capability, and runtime activation.

### 5. Retire superseded work

As replacement paths become ready, remove obsolete corpus artifacts, acceptance scaffolding, geometric reconstruction code, tests that merely enshrine defective output, and old projection/loading paths where no longer needed. Check references and active reachability before removal. Do not recreate a permanent legacy subsystem or rewrite Git history. Preserve a concise account of useful lessons and unresolved product decisions; retain old working artifacts only while they still serve a concrete purpose.

## Review and operating boundaries

Use current repository instructions and required gates. Claude follows its implementation guidance; Codex applies the adversarial review guidance. Group related findings by defect family and inspect relevant siblings before proposing patches. Separate correctness blockers from genuine Owner decisions and optional improvements. Once a concrete risk is resolved and required gates pass, stop optional testing and redesign loops.

The reset, local source correction, new identities, fresh construction, and necessary replacement of obsolete implementation are authorized directions. Routine engineering choices do not require renewed Owner approval. This does not authorize bypassing established merge or semantic-acceptance requirements, publishing/activating partial authority, destructive shared-state operations, or changing unrelated character, adapter, or gameplay policy.

Escalate only an actual unresolved product/semantic decision, a materially different source architecture, unavailable required access/input, or an action outside existing permissions. State the exact decision needed, evidence, recommendation, and consequence. Continue independent useful work while that boundary is unresolved. Do not manufacture an approval request merely because an older document disagrees with this settled decision; reconcile that document explicitly.

## Expected deliverables and reporting

Produce reviewable implementation increments, with the first covering the recorded reset, quarantine boundary, pinned source, and a concrete verification pass. Continue through the sequence rather than ending after writing a plan.

The completed work should provide:

- Reconciled governing decision/specification and a clear quarantine/retirement disposition.
- Corrected, pinned canonical source with economical correction notes, full coverage accounting, and official-PDF locators.
- Fresh coherent 5c ingestion and release handling with source-backed regression coverage for the known structural families.
- A practical, repeatable fresh 5d authoring/review path and progress toward the complete agreed scope, with acceptance status explicit.
- Evidence that stale corpus/package/retrieval products cannot become active through selection or fallback; required gate results on the final relevant heads.

Report progress by verified sections/records, unresolved discrepancies, fresh semantic coverage, and working consumer behavior—not legacy leaf percentages. Keep the Owner informed with concise consolidated updates and concrete decisions needing attention. Distinguish implemented, reviewed, accepted, merged, published, and active states. Never describe a partial stage as the completed restart.
