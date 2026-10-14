# C9 native verifier: positional fact selection after canonical assembly

**Trigger.** Codex ran a supervised foreground run of `build_c9_preview.py` at preview commit `2121a50e` (builder `b68ae789…`). It printed `built 107 s`, `twice identical 201 s` and `preserved 230 s`, then exited 1:

```
AttributeError: 'CreatureTypeFact' object has no attribute 'skills'
```

The error came from `_replace_last`. Codex keeps the logs in `native-c9-supervised-run/`. An earlier background run of the same builder was killed when its CLI exited. It wrote no output and is not evidence.

**Defect family.** Code assumed `facts[-1]` is the added `creature_skills` fact on a component read back from accepted inputs. Accepted components are canonically assembled, and on the constructed preview the skills fact is last in **0 of 336** profiles (`c9-native-work/quick_check.py`).

| Site | Stage | Disposition |
| --- | --- | --- |
| `_replace_last` (malformed-input editor) | assembled preview | **patched**: `_replace_skills` selects the one `CreatureSkillsFact` semantically, replaces it in place, and asserts exactly one per component and exactly one component |
| `_onto_non_profile` | assembled preview | **patched**: reads the Goblin's skills fact semantically, and asserts the target holds none |
| `preserved()` `components.changed_only_by_one_appended_skills_fact` | assembled base and preview | **patched**. It had not yet failed visibly, because the bool asserts run after `native()`, but it would have reported false for every changed component. Now `components.changed_only_by_one_added_skills_fact` requires exactly one skills fact, none in the base, the other facts equal in canonical order, and nothing else changed. The quick check is true for all 336 |
| `build_one` `b.facts[:-1] == a.facts` | raw proposal construction | **already safe**: that stage appends the fact itself (`facts=(*comp.facts, added[key])`) before any assembly |

**Construction reused, not repeated.** `--verify-existing` re-derives the four proposals without running the acceptance chain (about 20 s) and proves they render byte-identical to the pinned constructed files. It then reads the pinned preview (`3ad7bdcb…`) instead of chaining. The producer path (`build`, `build_one`, `chain`) is unchanged from `2121a50e`, so no new construction is justified. The report goes to `reports/c9-verification.json`, which records `CONSTRUCTION` (`2121a50e`, `b68ae789`, the supervised timings and the failure) separately from the verifier revision's own builder digest.

## Round 2: the generic component delta

**Trigger.** Codex ran `--verify-existing` at `31810c08` (builder `c4a9a8bf…`, 714 s), and it exited 1. Every native and sequencing proof had passed. Exactly one conservation boolean was false: `representation.components.delta_is_the_proposal_delta`. That report is preserved byte for byte at `308b65ad` (`reports/c9-verification.json`, `b9f66c92…`).

**Cause.** This is the same family as round 1: a mismatch between the proof stage and the order. The generic collection delta compared the built proposals' raw component objects against the oracle's assembled ones:
- the raw construction appends the skills fact last;
- assembly puts it before `creature_type`.

**The counterexample**, Goblin Warrior, from `reports/c9-packet.json` → `alignment_controls`:

| Component | Order of the last three facts | Notes |
| --- | --- | --- |
| Raw | `… CreatureSizeFact, CreatureTypeFact, CreatureSkillsFact` | the same fact multiset as the assembled component |
| Assembled | `… CreatureSizeFact, CreatureSkillsFact, CreatureTypeFact` | equal to the raw component apart from fact order |

The C8 proposals as loaded already match their assembled components (0 of 948 monster components differ), so only the in-memory built C9 objects carry construction order.

| Site | Disposition |
| --- | --- |
| `preserved()` component delta | **Patched with `aligned_components`.** A raw component takes its assembled twin's fact order only when the twins hold the same `fact_key` multiset and every other field is equal. Options and nested orders are untouched. Any other difference keeps the raw form, so the delta still fails. **Negative controls (all hold):** a changed non-skill fact (Goblin size) is not aligned; a changed field (`handling`) is not aligned; and the delta proof returns **false** when the built monsters proposal carries that changed Goblin |
| `records`, `prose_bindings`, `relationships`, `references`, `provenance` deltas | **Already safe.** These are flat value objects with no reordered nested sequence, and all were true in the `31810c08` report. Provenance is compared as a set of claims |

**Supplementary.** The native report's excerpt for the three fact-invariant variants (unsorted, duplicate, atypical pairing) shows the review-unit rule mismatch, which is the first matching validation finding. `invariant_findings_direct` records each variant's own invariant finding:
- "skills is distinct by skill and sorted by skill" (unsorted and duplicate);
- "each printed skill bonus is for the skill's usual ability" (atypical pairing).

## Carried, not rerun

`--finish-report` does the following:
- checks that the producer, pins, malformed variants, `native` and `sequencing` are unchanged from `31810c08`, by AST source-segment SHA-256 (`CARRIED_CODE`);
- checks the carried report's digest, the input pins, the private copies and the constructed bytes;
- re-derives the proposals without the acceptance chain and proves byte identity;
- recomputes only `preserved()`, the alignment controls and the direct invariant findings;
- writes `reports/c9-packet.json`.

The native and sequencing results are carried with their original identity:
- verifier `31810c08`, builder `c4a9a8bf`;
- Codex run, PID 40888, 714 s.

The construction is recorded as `2121a50e`, builder `b68ae789`, built twice identically. Neither the construction nor the native block was rerun.
