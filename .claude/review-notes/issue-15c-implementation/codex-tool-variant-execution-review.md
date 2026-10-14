# CRD Issue 15c — tool-variant execution family review

**Bounded family clearance at `b92493eae56ca839e027f3c7919febf0d3646a4d`. No concrete merge-blocking defect found in this family.** This is not whole-PR readiness, source acceptance, a configured-coverage gate, or permission to merge/publish/activate.

Authority: full `../issue-15c-preparation/issue-draft.md`, SHA-256 `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`; `owner-whole-pr-review-2026-10-13.md`; the parent-adopted tool addendum in `whole-pr-coverage-review/codex-whole-pr-coverage-check.md` and `codex-whole-pr-coverage-remediation.md`. Installed Review/routing skills read; reuse task-verified Library Review 2026-09-25 / Prompting 2026-10-05. Accepted C5/C7/C8 source/native/recording/selection evidence reused. No new product policy or source candidate is required for these settled tool checks.

## Revision and evidence

The initial core pin `fd7c9771db8440525d794558efe62de79cf30ef4` was amended into `b92493e...`. The exact difference adds only scene tool identities, the corresponding scene test, and prompt/architecture completion (four files, 40 insertions/3 deletions). Core model, grant, check, holding, validation, migration, and core tests are unchanged by that amendment.

Independent programs `tool-variant-review/probe.py` and `tool-variant-review/seams.py` import **all project and test Python from immutable Git blobs at b92493e**, not the concurrently changing checkout. `results.json` and `seam-results.json` retain module SHA-256s and the before/after-checked accepted C8 oracle SHA-256 `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`. Both completed exit 0 with the selected checkout's `venv/Scripts/python.exe`. These are direct bounded assertions/probes, not pytest suite counts or full gates.

## Contract disposition

| Seam | Verified behavior and evidence | Disposition |
| --- | --- | --- |
| Exact kind and component grain | `ToolGrant.variant` (`models/dnd5e_state.py:365`), `RollProposal.tool_variant`, and `ItemInstance.tool_variant` retain typed accepted identities. `validation.py:120,139` resolves variants from the actual tool component/options. `_tool_spec` (`checks.py:336`) requires the selected activity and kind, matches a held item of that exact kind, and derives ability/DC from source facts. | Already safe. |
| Per-kind proficiency | Soldier Dice gives +2; a Playing Cards grant with held Dice gives +0; Bard Lute gives +2 and a different held instrument gives +0. The committed positive tests also assert the exact source DC, ability, and kind-bearing provenance identity. All 8 Gaming Set activity/kind combinations and all 20 Musical Instrument combinations resolve through the real adapter using accepted facts. | Already safe; no blanket kind hold remains. |
| Source entitlement and counts | Actual accepted facts were inspected for Soldier (1 gaming kind), Bard (3 instruments), Monk (1 artisan tool or instrument), and Skilled (3 shared skill/tool picks). Frozen probes accept the entitled picks and refuse Soldier 2-over-1, duplicate Soldier grants, Bard 4-over-3, Monk 2-over-1, and Skilled 3 skills plus 1 tool before dice. `grants.py:861,883,966` validates source, category/family, kind, and shared counts. | Already safe. |
| Duplicates and legacy state | A duplicated Bard Lute grant does not stack proficiency (+2 remains +2); duplicate entries still consume the source's finite budget. This does not justify expanding into character-build legality. A matching legacy grant whose variant is null refuses `missing_state` before dice. Missing held kind, missing selected kind, wrong-family kind, and a kind on a tool without variants are refused by seven committed negative controls executed directly. | Already safe; no silent legacy per-kind proficiency. |
| State/item persistence | Character JSON round-trip preserves `ToolVariant.DICE`. ORM/migration 0042 add one nullable item column without inferring old kinds; the committed migration test checks up/down shape, FKs and constraints. `holdings.py:335,358,442,468` reads/persists the field and retains it through use and transfer; transfer validates it against the destination's exact binding before CAS. Existing holdings revisions and delivery rechecks remain the concurrency mechanism. | Already safe by code inspection, direct round-trip, and reused focused persistence diagnostics. |
| Adoption and holds | `adoption.py:197` validates every held kind under the target index before the existing guarded rebind. A pure frozen-helper control accepts Dice under the original index and rejects the same held identity under an in-memory target with Dice removed. It uses a fake holdings read, not a new store. Pending/shared-change holds, current-target checks, and revision-guarded rebind remain before successful adoption; no hold bypass was added. | Already safe. |
| Caller, scene, audit and visibility | Caller enum schema includes `tool_variant` (`caller.py:380`); scene lists held tool identity/kind (`scene.py:111`), and prompt explains the selection. The committed scene assertion passes. Real caller/service probes parse shown and hidden Dice proposals, roll once, retain the kind in audit provenance, and filter the hidden Writer view's numbers/outcome/kind. No new general inventory or input-policy behavior was introduced. | Already safe. |

The prior representation-grain failure warranted this bounded family/sibling check. Disposition is **implementation gap closed / already safe** for the reviewed tool seams. No further patch loop, new Owner policy vote, source census, or native rebuild is indicated by these results.

## Reused public engineer diagnostics

Read the actual public commands/results in `../issue-15c-preparation/tool-variant-public-diagnostics.json` and inspected committed `scripts/run_focused_tests.py`: it runs Black checks, then pytest with `--no-cov`, reports the actual pytest exit, and explicitly labels the result diagnostic-only. Failed/malformed earlier invocations are not counted as successes.

- `toolu_01HK2SxqbBsYBRnC6YmsjQB5`: **283 passed, 66.79s, diagnostic exit 0** across bounded checks/before-dice, holding/state/adoption/selection/readiness, and migrations 0041/0042/Alembic.
- `toolu_01QwfoTpiwayNz9BmA4U74xy`: **22 passed, 353.51s, diagnostic exit 0**, existing complete published-release API file.
- `toolu_01VCD2oParPyCQ2psZnd8SLA`: **118 passed, 354.43s, diagnostic exit 0**, scene + bounded checks + published-release API file before the coherent amendment was committed.

The API file supplies application wiring/delivery/hidden/rollback proof; it does **not** separately execute a Gaming Set/Musical Instrument API scenario. New tool-specific proof composes the unchanged application delivery seam with the independent frozen real caller/service cases, per-kind adapter cases, state/holding evidence, and the scene/schema/prompt review. No repeated disposable publication/store setup was run by this review.

## Invalidation and remaining parent work

Later changes to any imported module in the saved hashes, source identity/certification, persistence schema, caller/scene, grant validation, or delivery plumbing require the parent to assess their actual effect. The active C8 changes to shared adapter/service paths mean these immutable service probes remain historical at b92493e until the final change comparison/gates establish applicability. Do not silently relabel them exact-final-head proof.

Parent retains the complete PR acceptance map, final stable-head source/file comparison, configured 80% coverage, unchanged repository gates and exact-head CI. Other weapon, Multiattack, lifecycle and C8 execution findings are outside this worker's verdict. No implementation/source/baseline/Git/network/runtime mutation was made; only the named review note and `tool-variant-review/` evidence files were written.
