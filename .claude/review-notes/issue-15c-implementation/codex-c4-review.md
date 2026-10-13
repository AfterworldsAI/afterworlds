# CRD Issue 15c — final C4 independent review

**Verdict: source-family corrections required before native preparation.** Reviewed final C4-A `901083ec3c8c25e9cd95a638a537cf3db41d8277420e07f0fc2b5d023cd15e62`, B `f679b06c7e8e3513b9886716754db78b5a28c8cf254cb09d1e195b4f30765c08`, C `2c34a6f03fc081a0adbe3abf8f9e50f0dcad55e9c07469cf3204ccb36e68fb5f`, capability `2d884ffbb254af6849a8bd0b61cc5f2f2c4a84dd568f664e3606fb02cb783a8e`. These remain unaccepted raw evidence. Head `1473426762970dd532a01924dcfcb6183ccdf603`; no tests or regeneration by Codex.

## Boundary assessment

Repeated source completeness and source/capability separation findings triggered the boundary-over-patch check. The approved #191 contract decides the ordinary bounded families below. Their disposition is **issue-scoped source correction**, not new Owner policy, universal execution or another handful of parser examples. Genuine different engines remain named unsupported boundaries. Complete a coherent family assessment before another readiness claim or costly native generation.

## Required corrections

### 1. P1 — ordinary admitted source families remain untyped

The 103 `missing_source_authority` assignments are mixed. Neither making all permanent exclusions nor promising all as executable is correct. Representative broken contracts:

| Family | C4-B example (zero-based JSON paths) | Source |
| --- | --- | --- |
| Equivalent ordinary wording | `creatures[254].entries[0].attack.reach_ft = null` for “reach 5 feet” | animals.md:1428 |
| Grapple, size, occupied appendages and linked conditions | `[250].entries[1]` lacks Medium-or-smaller grapple DC12 and linked Restrained | animals.md:1145 |
| Conditional replacement/additional damage | `[43].entries[1]` leaves Advantage-dependent replacement damage untyped | monsters-A-Z.md:3627 |
| Forced movement and charge consequences | `[141].entries[4]` lacks Large-or-smaller pull15 | monsters-A-Z.md:11718 |
| Timed modifiers and combined conditions | `[72].entries[2]` lacks next-attack Disadvantage; `[224].entries[6]` lacks timed Speed0 | monsters-A-Z.md:6048,18731 |
| Source-defined parameter choices | `[108].entries[2]` lacks 7(2d6) damage using Draconic Origin's selected type | monsters-A-Z.md:8964,8972–8974 |
| Admitted check contributors | Sphinx Inscrutable `[193/194].entries[0]` describes its Insight Disadvantage only in prose/capability | monsters-A-Z.md:16046,16142 |

Assess the parallel source families, including repeat saves, bounded durations, temporary source-specific immunity and save-degree branches. Runtime position/visibility/actor clocks/selected values are legitimate prerequisites **after** the source facts and predicates exist. Formatting-only residue (for example `. <br>`) requires normalization. Ghost Possession is a different body-control/stat-substitution mechanic and must be a named unsupported boundary, not “ordinary missing source authority.”

Mixed clauses need individual dispositions. In particular, timed Poisoned/no-HP-regain clauses on Bearded/Bone Devil matter to approved zero-HP recovery; a blanket “healing” label cannot erase their admitted effects. Actual general healing, swallowing, possession, curses, armor degradation or maximum-HP engines remain outside this bounded contract. Preserve complete clauses and refuse applicable unsupported contributing mechanics.

### 2. P1 — logical source entries lose continuation lines

Adult Bronze Dragon Thunderclap `[36].entries[10]` retains only `10 (3d6)` from monsters-A-Z.md:3041; physical line 3042 supplies Thunder damage and Deafened until end of the target's next turn. Neither is preserved in its raw entry. Ghost Possession also omits continuation lines 6844–6845, including termination and immunity. Thus the “every clause preserved” and numeric-set checks do not establish logical entry completeness.

Correct the logical-entry extraction family across the admitted source files and preserve complete source spans before classifying or typing. Retain unsupported entries' full meaning too. Verify source-to-entry conservation independently of the same clause parser; counting numbers or source headings is insufficient.

### 3. P1 — source payload still invents capability qualifications

Seven Swarm contributors put `applies_when.zero_hp_treatment = character_style` in source. The source prohibition on regaining HP or gaining Temporary HP is unconditional (animals.md:5965 and siblings; monsters-A-Z.md:4631). Keep it unconditional in authority; put present roster relevance in capability. Its interaction with the approved natural-20/stable recovery follows the source exception rule and requires no general healing engine.

The full-file scope-word sweep also misses semantic policy: Half-Dragon `profile.resistance[0].selection.recorded_as` says “ChoiceRecord on the creature (existing 2b contract).” That is runtime storage policy, not an SRD fact. Source may supply the choice vocabulary and dependent formula; storage, applicability and certification belong outside minted source. Check representative parallel source fields for the same boundary, rather than extending a vocabulary blacklist alone.

### 4. P1 — new subclass skill grant lacks typed eligibility

C4-A College of Lore Bonus Proficiencies (c4a.json:5721–5743) types three chosen skills but omits the selected College of Lore/Level 3 requirement (classes.md:1688–1696). G1 has no exact progression entry for this feature to supply that missing predicate. Type the eligibility before using the grant. Barbarian Primal Knowledge can use its existing exact G1 progression entry; make the relationship explicit where needed. This remains validation of contributing grants, not a general build-legality sweep.

The prior feat prerequisites, multiclass skill counts, class ASI/Epic Boon feat-choice links and boon anchors are repaired. Reuse that evidence and the unaffected numeric/reused-family checks.

### 5. Source qualification clarification — Vampire Familiar

The source says “except from its vampire master” (monsters-A-Z.md:17503). An exact template restriction is not supplied, but the word **vampire** must not disappear. A same-story creature reference by itself does not make an arbitrary creature a qualified vampire master. Preserve the source qualification and a validated relation/role prerequisite; missing or unvalidated qualification holds the affected Charmed determination. Do not invent an exact-template policy or a general relationship framework.

## Next action and proof

Claude prepares a separately identified raw successor, preserving final C1–C4 byte-for-byte. Supply source-family dispositions and complete logical source spans, source-only facts/formulas/predicates, capability-only judgments, and exact new hashes. Report any actual unresolved policy separately; do not manufacture one for the settled corrections above. Counts alone cannot establish readiness. Native preparation remains held until the corrected raw contract independently clears; exact native review and explicit Owner acceptance remain mandatory before dependent execution.

All existing merge, runtime, publication/activation, app-launch and issue freeze boundaries remain. No full suite/CI rerun for this correction pass.
