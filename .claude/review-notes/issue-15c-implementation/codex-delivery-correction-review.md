# CRD Issue 15c — delivery correction review

**Verdict: the delivery correction family is ready at `4a39f27becb1ae265ba549727e72846fbce83ae8`. All four original findings are closed; no new finding or Owner residue was identified in this bounded follow-up.** This is not whole-PR acceptance: independent creature capability work and supervised final repository gates remain separate.

Reused the full governing issue, current-task verified Library guidance, accepted C7 identity, and the approved spatial/hand contracts from the original review. Inspected immutable committed source for `2570029`, `a7160eb`, `f15c175`, and `4a39f27`. Current HEAD advanced to `3accd1b400a91366b7ac8c6bc4184737504ccbb5` during the review; its creature-effect/capability changes were excluded from the pinned runtime probe and are not approved by this verdict. Relevant delivery code remained unchanged.

## Closure

| Original finding | Disposition and evidence |
| --- | --- |
| P1 negative discovery reads and membership | **Closed.** `services/dnd5e_state/turn.py:297–329` snapshots every character/creature identity and revision. `pipeline/rpg/service.py:542–548` captures it before aura and turn-bounded-effect scans; the result carries it to `pipeline/orchestrator/service.py:2165–2170`, which rechecks before audit and mechanical application. `api/pipeline_wiring.py:394–407,658` supplies the production reader. |
| P1 spatial bystanders | **Closed.** `pipeline/rpg/attacks.py:1467–1480` and `adapter.py:467–492` include named hostile/ally/aura subjects. `service.py:603–607,881` additionally retains discovered aura holders even when the GM says none are in range. Independent real-service Pack Tactics, close-combat, and discovered-out-of-range-aura probes each refuse `invalid_selection` with **zero dice calls**. |
| P2 Light/Nick item identity | **Closed.** `economy.py:147,157–167` retains source record and individual item UUID; the different-weapon check uses the UUID while source properties remain authoritative. Reused the matching independent principal check in `codex-identity-loading-correction-check.md`; inspected committed same-item and distinct-Dagger Light/Nick regression coverage. |
| P1 source hand classification | **Closed.** `hands.py:107` applies one-handed loading requirements from the absence of the source Two-Handed property, independently of asserted grip. Reused the principal explicit-bypassing-grip probe and valid free-hand control after matching the source hash. |

## Discovery completeness and transaction check

- A nonmatching subject changing into an aura/effect holder increments its state revision; insertion or removal changes membership. Both state saves and rebinding route through `store._cas`, which increments the revision (`store.py:244–272,275–331`), so bindings are not an unguarded dependency of the negative query.
- Positive subjects retain their exact binding/state/holdings checks. The new story guard supplements those checks rather than replacing them.
- Current aura discovery consumes the character's state and exact authority through `_held_keys`; timed-effect discovery consumes the state document. Independent item changes remain guarded for participating holders. No unsupported claim that all future discovery predicates are automatically covered is made.
- The production turn lease is acquired before binding reads (`orchestrator/service.py:490–537`). Shared-change activation considers all story character/creature bindings, and adoption is held by the same story events; rebind also increments revision. Those existing guards preserve effective authority during this operation.
- The story query uses current scalar database columns, not cached ORM snapshots. Its delivery recheck follows provisional Turn creation and precedes mechanical writes in the same outer transaction. A mismatch produces pipeline failure; the existing non-delivery rollback removes provisional work. SQLite's writer transaction prevents a later concurrent writer from slipping between this check and commit.

Read the actual committed discovery tests and their public tool results in `.claude/review-notes/issue-15c-preparation/implementation-c7-run/stream.jsonl` (only `tool_use`/`tool_result` blocks):

- `toolu_01TVEfKyJVQUidvsniBtSt3a`: **2 passed**, 9 warnings, 343.17s.
- `toolu_01Lm7uB6gTXEUiX16KGrWDsP`: disabling only the guard gives **2 failed**, 11 warnings, 349.34s; the guard was restored. The immutable `4a39f27` source independently confirms restoration.

These cases cover changed previously unnamed state and added membership through actual API delivery. They inject the change in the transaction, respecting SQLite's single-writer behavior, and demonstrate rollback of audit/subject changes. Reused this evidence without rerunning its expensive setup or negative control.

## Independent probe provenance

`delivery-review/recheck_spatial_4a39f27.py` loads every `afterworlds.pipeline.rpg.*` module it executes from `git show 4a39f27:<path>` using an import loader. This prevents concurrent creature/capability edits from contaminating the reviewed runtime. Supporting state/model and test-helper inputs were checked unchanged against `4a39f27` (`git diff --quiet`, exit 0).

- Script SHA-256: `0c23b3e2d32654fa3b02db3977c5121fb75f520d3f6581450aa0c9f2d64357b4`.
- Final evidence: `delivery-review/spatial-4a39f27-frozen-results.jsonl`, SHA-256 `bcd6e7d4c07357477502d301927e59e7a7e485e3a8ef25ec148a98d7691d18d9`; exit 0, empty stderr. It records all imported RPG source hashes and all three zero-dice refusals. The earlier non-fully-frozen spatial run is preserved but not used for final-head evidence.
- Reused identity/loading hashes: `economy.py` `eccc6825b8f6a047f9e26e1e576378ca10ba0aa4d27fbec49d3cb7156085e4bb`; `hands.py` `74da351abc2753ca6f241615ac1dec73e768fe3caf0d8cb41fac78978c214a0e`.
- Additional checked delivery hashes: `service.py` `19410903645809b6f1f900997b7586a2f1c36ece1c34bb2669acc93ef5d3da82`; state `turn.py` `a58ea3b48225b3cf3fbc8d1883c2e8adc7972272a7dbd36b4e5b00606aafa679`; `pipeline_wiring.py` `c32a7753d6d3f7da8a85ebc23adde35eb23023b4565dd477a4ba75b139907b68`; orchestrator `service.py` `ebf922b93507eaee61fd01e35de0bace707ed6caeeb792d476253d3e5e40064b`.

The adjacent per-operation counting-dice guard (`service.py:657–675`) now distinguishes refusal after an operation's own first die, including the first operation. Its presence is verified; complete creature before-dice behavior and current positive capability coverage remain the independent creature review's responsibility.

No implementation, store/authority, Git, network, or shared-runtime changes were performed. No full-suite verdict is claimed; the interrupted optional E2E file is not a pass, and final supervised full pytest and required repository gates remain mandatory.
