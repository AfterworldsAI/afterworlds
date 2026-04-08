# cleanup_backlog.md

Minor cleanup items that are not important enough to justify standalone GitHub
issues right now, but should not disappear. These are candidates for future
low-risk cleanup passes.

## How to Use This File

- Put only **minor**, **non-blocking**, **non-roadmap** items here.
- If an item grows teeth — correctness risk, architectural impact, migration
  work, cross-cutting behavior, or meaningful product consequence — promote it
  to a real GitHub issue.
- When a cleanup pass picks up an item, either:
  - remove it once completed, or
  - replace it with a short note pointing to the PR that resolved it.

---

## Story Bible / Service Cleanup

### `soft_delete` silently succeeds for unknown entity IDs

**Area:** `StoryBibleService.soft_delete()`  
**Type:** Consistency / API behavior

`soft_delete()` currently does nothing when the target entity ID does not exist.
A more consistent API would raise `EntityNotFoundError`.

**Why not a standalone issue:**  
Non-breaking and too small to justify its own issue right now.

**Future handling:**  
Good candidate for a one-line service cleanup pass if the current behavior
starts confusing real callers or tests.

---

### Field validation order in `update_static_field`

**Area:** `StoryBibleService.update_static_field()`  
**Type:** UX / error quality

`update_static_field()` checks `confirmed` before checking whether `field` is a
valid static field name. A caller passing an invalid field with
`confirmed=False` gets `ConfirmationRequiredError` instead of the more
informative `ValueError`.

**Why not a standalone issue:**  
No correctness impact; this is error-quality polish only.

**Future handling:**  
Safe to fix during any small service-layer cleanup pass.

---

### Deterministic ordering for `get_dynamic_field_history()`

**Area:** `StoryBibleService.get_dynamic_field_history()`  
**Type:** Determinism / query hygiene

`get_dynamic_field_history()` currently filters by `entity_type` and
`entity_id` but does not specify explicit ordering. If callers treat the result
as a timeline, database-dependent row order could be confusing.

**Why not a standalone issue:**  
Borderline item, but too small by itself. Better handled as part of a broader
Story Bible history/query cleanup pass.

**Future handling:**  
Consider adding ordering such as `changed_at ASC, history_id ASC`, possibly in
the same pass as any broader `sb_dynamic_field_history` refinement.

---

### Deterministic tie-breaker for locked-fact ordering

**Area:** locked-fact query path  
**Type:** Determinism / cache hygiene

Locked facts are currently ordered by `created_at` only. A secondary tie-breaker
such as `locked_fact_id` would make ordering fully deterministic when
timestamps collide.

**Why not a standalone issue:**  
Minor polish; not worth its own issue.

**Future handling:**  
Batch into a later query-determinism cleanup pass with similar ordering fixes.
