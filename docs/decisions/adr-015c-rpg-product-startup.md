# ADR-015c: RPG Product Startup — World Confirmation, Rules Selection, Character Acceptance, Setup Completion

**Issue:** CRD Issue 21 RPG startup prerequisite ([contract](../architecture/crd-issue-21-rpg-startup-prerequisite.md))
**Date:** 2026-10-16
**Status:** Accepted (the Owner accepted the complete proposal on 2026-10-16 and authorized implementation)
**Addendum to:** [ADR-015](adr-015-rpg-adjudication.md) Decision 9. ADR-015/015b and CRD Issue 15c decisions are unchanged.

---

## Context

ADR-015 Decision 9 gave `RpgSessionState` its `setup_phase` sequence (`world_setup → character_creation → play_configuration → complete`). It also said `play_status` becomes `in_play` once setup completes with an adjudicable sheet. No production path did any of that: setup turns were prose-only, and every RPG proof seeded typed character state and forced `in_play`. The Owner chose **GM-led creation plus completed-sheet entry** and accepted the RPG startup contract. This ADR records how that contract maps onto the existing owners.

## Decision 1: A versioned setup Writer envelope on the existing Writer pass

While an RPG story is in `setup`, its Writer turn uses forced tool `produce_rpg_setup_turn`, with pass id `WRITER`, the same stable prefix and the same settlement. This is the typed-writer pattern of ADR-016 Decision 1, not an extra provider pass. The tool returns `schema_version: 1`, the visible `gm_text`, and one phase-specific `result`:

| Phase | Allowed `result.kind` |
|---|---|
| `world_setup` | `world_confirmation` (the GM's stated understanding) or `clarification` |
| `character_creation` | `character_proposal` (`path`: `gm_led` / `completed_sheet`, `character`: the existing `Dnd5eCharacterState` schema, possibly partial, plus `unresolved` notes) or `clarification` |
| `play_configuration` | `configuration_summary` or `clarification` |

A kind the phase does not allow, or a malformed envelope, fails the turn as a typed `PIPELINE_ERROR` (no Turn, non-billable). The Turn records `gm_text`. Extractor, Contradiction and conditional Safety run on it as for any turn. Setup turns stay ineligible for Rolling Summary (ADR-006b) and keep their `setup_confirmation` retrieval marker. The prompt contract is `docs/prompts/rpg_setup_writer.md`.

## Decision 2: Code-owned setup state in the anchor Node's typed metadata

`RpgNodeMetadata.setup` (`RpgSetupMetadata`, `schema_version: 1`) lives in the existing Node JSON carrier, with no migration. It is written in the same transaction as the delivered setup Turn:

- **World:** every delivered world-setup turn increments `world_revision`.
  - A `world_confirmation` result records a target `{turn_id, world_revision, understanding}`.
  - A clarification clears the target.
  - So a later world edit always invalidates an outstanding confirmation. Readiness is never inferred from prose.
- **Rules package:** `selected_package_uuid` is the Sojourner's explicit choice.
- **Configuration** (Codex whole-candidate review R1, 2026-10-17): configuration is edited through the existing typed `POST /setup` route. Every edit during setup increments `configuration_revision` and clears any outstanding target. A delivered `configuration_summary` records a target `{turn_id, configuration_revision, configuration snapshot, summary}`. Complete setup must name that revision and match the snapshot, so a stale or edited configuration is never confirmed. During setup, an edit through `POST /setup` must also name the `expected_configuration_revision` its form was based on: a stale one is a `409`, so one form cannot silently overwrite a newer save, and a missing one is a `422`. In that RPG edit, an omitted field is unchanged and an explicit `null` clears an optional setting (genre flavor, house rules, content boundaries). In-play configuration edits and other modes are unchanged (Codex R1 re-review, 2026-10-17).
- **Character:** a `character_proposal` mints candidate revision *n+1*.
  - The candidate stores the untrusted proposal, its `path` and `unresolved` notes, and the problems code found.
  - It also stores the exact binding that code validated it under.
  - Problems come from schema parsing, `validate_character`, `character_readiness`, references, and the binding's current status.

The accepted mechanical state lives only in the CRD Issue 2b character service, never in this metadata, in session fields or in the Story Bible.

## Decision 3: Typed setup operations under the story lock

These are thin routes under `/api/stories/{id}/rpg/setup`. Each runs under the existing per-story lock, makes no provider call, does no settlement, and works through the RPG setup owner (`services/rpg_setup.py`):

| Operation | Effect |
|---|---|
| `GET` | Phase, play status, available packages, selection, world target, candidate (readable sheet and problems), accepted character, configuration |
| `POST confirm-world {expected_world_revision}` | `world_setup → character_creation` when the current target matches |
| `POST rules-package {package_uuid}` | Records a selection of an enabled, published, non-quarantined `d20` package whose binding currently resolves |
| `POST accept-character {expected_candidate_revision}` | Revalidates the candidate under the current exact binding. `create_character`, `readiness` and the adapter's `is_adjudicable` must all pass. Then `character_creation → play_configuration`, in one transaction |
| `POST complete {expected_configuration_revision}` | Confirms exactly the configuration the GM's delivered `configuration_summary` presented, at that revision. Rechecks the accepted character and its binding, then sets `setup_phase=complete`, `play_status=in_play` atomically. No scene is generated |

A stale revision, the wrong phase, or a missing or invalid prerequisite gets a typed `409`/`422` and leaves committed state as it was. Repeating a confirmation that already happened returns the current state.

Readiness means the recorded inputs are complete and well formed. It does not certify legality or executability; CRD Issue 15c restrictions still govern play.

## Consequences

- New: `models/node.py` `RpgSetupMetadata` and friends; `pipeline/rpg/setup_writer.py`; `services/rpg_setup.py`; setup routes and DTOs.
- The orchestrator routes RPG setup turns to the setup writer.
- The built app's RPG setup moves from configuration-first to the phase sequence above.
- The test-only RPG seeding route is no longer used by the CRD Issue 21 spine proofs. CRD 15b/15c seeded suites stay valid within their mechanics boundaries.
- Out of scope: a general character builder, new rulesets or mechanics, in-play rebuild or rebinding, package publication or activation.
