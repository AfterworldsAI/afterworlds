# CRD Issue 15c — implementation status

- **Branch and head:** `codex/issue-15c-bounded-d20` at baseline `e83018ccee66101da56e612c9e48719e1a50f51c`. That baseline is also remote main. No commits yet.
- **Scope:** #191 as posted (draft SHA-256 `e7dfbcbd…b3d5`). The G1 oracle `2ccbaeba…1258` is verified and unchanged.
- **Orientation:** Graphify refreshed and queried. The Advisor was consulted on the approach and on the candidate's scope.

## Finding: semantic candidate required

Accepted G1 types weapon category and mastery identity only. Every creature record (336) carries zero facts, and character AC is unimplemented. The roster depends on new structured authority. See `gap-inventory.md`.

Candidate C1, under `candidate/`, has three separately hashed parts:

| Part | Content | Holds |
| --- | --- | --- |
| C1-A | Rules, the 38 weapon rows, 13 tools | Weapons, masteries, zero-HP lifecycle, initiative, tool checks, GameMaster-difficulty checks |
| C1-B | Creature defensive profile | Attacks on creatures |
| C1-C | Armor and character AC | Attacks on characters |

## Progress

| Item | State |
| --- | --- |
| Gap inventory | Written |
| C1-A derivation | Written: 223 facts, every one anchored to an accepted component |
| C1-B and C1-C derivation | Open |
| Packet README | Open |
| Independent track: wiring, manifest/certification, refusal taxonomy, player-roll refusal, prompt, fixed-DC checks and saves | Not started |

## Blockers

Dependent work waits on Codex independent review and explicit Owner semantic acceptance of C1.
