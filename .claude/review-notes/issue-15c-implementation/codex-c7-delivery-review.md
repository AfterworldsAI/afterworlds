# CRD Issue 15c — delivery/read-set review

Reviewed statically at `00b822471d9658ad34d79de929736558883f342b`, against #191 body SHA `979889e7a42ef8673f1b4f99d3849545b6091025f08a7a7fcd3d37d0bb5f3173`. No tests, imports, store changes or implementation. These are issue-scoped P1 corrections, not Owner policy choices.

## P1 — recheck the holdings contributing to adjudication

`turn.py:223` / `RpgTurnHold.recheck` recheck only a subject's state revision and binding. `TurnCharacter`/`TurnCreature` also snapshot `items`; weapon and armor calculations use those holdings. `holdings.py:399` updates an item's own revision, and `transfer_item`/`update_item_use` do not bump the holder's state revision or acquire a turn-blocking hold. No item-to-subject revision trigger exists in migration 0038. A weapon can be transferred or unequipped, armor changed, or a new equipped contributor inserted after adjudication's read while the subject state recheck still passes. The delivery then applies mechanics computed from obsolete holdings.

Recheck the relevant holdings read set, including changes in collection membership, ownership and item revisions, in the delivery transaction; retain CAS for actual expenditure. Source-state CAS alone is insufficient. Cover a held weapon transfer/change, an added/changed target defense item and the eventual ammunition depletion race, with no partial Turn/audit/effects. This is #191 AC6 implementation, not a new inventory product policy.

## P1 — validate coordination reads even without coordination writes

`coordination.py:145` returns immediately when there are no edges and the resulting document equals the snapshot. `_load_coordination` reads coordination for weapon/creature attacks; mastery and rider expiry derive timing from it. `_commit_turn_edges` calls `commit` with that snapshot even when an attack takes no once-per-turn use. A concurrent delivered actor edge can change the coordination while the attack's subject state remains unchanged; the early return skips the revision check and commits effects based on stale timing.

Every mechanically consumed coordination read needs a commit-time revision check, including an initially absent row and read-only/no-effect paths. Do not manufacture a coordination mutation merely to force the check. Cover an attack whose timing snapshot changes mid-turn, with atomic refusal.

## P1 — record once-per-turn uses as reconstructable events

`ResolvedAdjudicationRecord.turn_use` / `turn_use_by` and the active instance drive `take_use`. Multiattack attaches those fields only after resolution (`service.py:583`); Cleave attaches its use in `adapter.py:629`. `_write_rpg_audit` serializes the existing roll/provenance/effects but not those fields. `coordination.commit` appends only begin/end rows; a use-only update writes the document without any coordination event. The ORM explicitly claims the complete document is reconstructable by replaying `rpg_turn_edges`, but replaying begin/end cannot recreate its non-empty use set. The current reconstruction test exercises edges without uses; the use-only test only checks the stored revision.

Record each applied use explicitly with its subject, source key and actor-turn instance in the same delivered transaction, through an appropriate durable event/audit path, and prove reconstruction including a use-only delivery and rollback. Do not rely on inferring hidden in-memory fields from current state or a changed template. This is the existing reconstructability invariant and bounded actor-turn contract, not an encounter-engine expansion.

## Boundary disposition

The recurring family is an incomplete mechanical read set and incomplete delivery event recording. Representative sibling seams inspected: subject revision/binding checks, independent item CAS/collection snapshots, coordination CAS/no-op path, edge logging, Cleave and Multiattack use threading, and effect/audit delivery transaction. Subject-addressed writes already run within the outer delivery transaction and use state/binding CAS. That existing safe structure should be retained while the missing read/event dependencies are added. No general inventory cleanup, scheduler, pending-action sequence model, cancellation or retry behavior is authorized by this review.
