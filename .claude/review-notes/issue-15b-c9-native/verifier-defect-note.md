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
