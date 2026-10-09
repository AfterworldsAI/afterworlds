# CRD Issues 5c/5d — final-ten candidate: Codex review

Reviewed 6 October 2026 local time (7 October UTC). **Ready for exact Owner
acceptance of the local candidate. No blocking candidate finding remains.**
No Owner acceptance or recording has occurred. The live oracle still has ten
reference findings. The detailed [Owner packet](issue-5d-final-ten-references-candidate.md)
and the pins below identify the reviewed result.

## Exact result

| Artifact | SHA-256 |
|---|---|
| Proposal: `.claude/_sp/final-ten/candidate/issue-5d-final-ten-references-PROPOSAL.json` | `46808846b0ad6712393b0f058a71e03d6e664a2ffdf8734de7d046bf4b4d68e3` |
| Construction script: `CANDIDATE.py` | `2f84d877037b865121bd502a9c92ae365f44cf82dc6d312d814759200433fd57` |
| Delta: `issue-5d-final-ten-references-DELTA.txt` | `465a17f7d749c512aed45848874576a6c2a839e1eaf0ea595da6a6c11c827851` |
| Simulated complete oracle | `6302adbe7b09fab0a26d60e5526d72fa5269214e3911b0362486ad9e705d85ff` |
| Reader test | `fec853b8ed1d84146248aa19d5f92b1c60b14aea226cf281a31dba6a07ba3dbe` |
| Live accepted oracle, unchanged | `5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d` |

The proposal adds exactly ten resolutions, with 201 destinations, under schema
17. Native simulation clears ten findings to zero, with no new finding. There
is no production reader, contract, schema, record, component or source change.
Simulated approval metadata is review evidence only; any later authorized
recording must use real approval metadata and reproduce these exact proposed
resolutions, rather than copying the simulated approvals.

## Independent review and proof

Authority reviewed includes the governing CRD Issues 5c (#132) and 5d (#137),
the restart Owner Decision, ADR-005d Decision 7, and the October 6 directions
linked in the Owner packet. Current Library guidance was verified separately
in `codex-coordination.md`: Review September 25 and Prompting October 5.

Codex inspected the native resolution validation and acceptance paths, the
persisted projection reconstruction, and the affected citation/GameMaster
reader paths. The immutable citation scope is retained as source identity;
native validation does not enforce a destination namespace from that scope.
The named exceptions for Wizard Spellbook, local Giant Fly, local Avatar of
Death and supporting item prose are explicit and asserted. They retain their
existing owners and follow the settled Owner/source directions. No new
ownership decision was silently implemented.

Source coverage review confirms the conditional priced-Equipment route,
including Food, Drink, and Lodging's intact table/context; 45 Gear entries
normalized to 39 names; Wizard-owned spellbook text; 25 normal familiar forms
and the Pact's seven additional forms; 42 item/creature routes preserving
bestiary blocks with source modifications; Awaken's two SRD examples; bounded
ability-modifier glossary coverage; and the general Cantrip/Ritual rules.
The official PDF was visually checked for material creature cues and local
blocks. The wider inventory does not justify duplicating the separate,
already-resolved unbold table references into reference 54.

`codex_payload_check.py` passed on the final script and proposal. Its durable
`codex-payload-verification.json` independently compares complete primitive
payloads, including order: all 1,476 prior resolutions and approvals, all
batches and every other payload are preserved. Exactly ten original held
citation coordinates match the additions. Only the ten resolutions and ten
SIMULATION approvals are added. Nine resolutions are identical to the first
independently reviewed draft; the sole revision is reference 34's additional
priced-Equipment destination. This refreshed proof supersedes the earlier
200-destination proof for final candidate identity. The retained first-draft
`codex-simulation.log` remains historical evidence.

Final `bound-gates.log` records input hashes and raw commands/exits: native
simulation, deterministic reload, isolated persistence, Black, Ruff and
strict mypy on the two changed Python files all pass. `reader-focused.log`
binds the final script/test hashes and reports **33 passed, exit 0**. It uses
private test stores and the native reader, with controlled binding resolution.
Controls refuse all ten unresolved citations and a disabled destination, while
an unrelated disable and a representative class selection remain correct.
Concrete content checks cover prices, spellbook prose, creature ownership,
local modifications and general casting rules. Codex also inspected captured
native glossary prose, including ability selection and modifier application.

The Awakened Plant integration is **drafted and tested only as isolated
house-rule prose presentation**: the supplied full block has HP 3 (1d6),
unchanged SRD prose precedes the exact authored addition, and HOUSE_RULE
provenance and override identity remain distinct. It adds no SRD record or
destination and is not installed or activated.

The interrupted reader attempt and the first completed run's five corrected
test-expectation failures are retained and do not count as passing evidence.
The separate Opus 5.5 advisor was consulted through the explicitly approved
Anthropic session. Its follow-up improved evidence binding and documented the
test's private-constructor dependency; Codex retains final judgment.

## Preservation and limits

`codex-preservation.json` independently checks all 3,922 pre-existing
Git-visible files and the protected external settings/guidance/launcher. Only
the authorized restart opening changes. HEAD, branch, full index, four
stashes, live oracle, historical evidence and `.secrets.baseline` are preserved.
`codex-final-verification.json` checks the historical body byte-for-byte and
pins the final packet and opening. Final document content checks are recorded
in `codex-final-hook.log`: real unstaged hook exit **1**, private-copy content
check exit **0**. Those outcomes do not establish a green staged/full gate.

The test currently loads its construction script from private `.claude/_sp`.
Before committing or delivering that test, the authorized recording/delivery
work must preserve a reproducible constructor or adapt it to the recorded
oracle. This is a delivery prerequisite, not an unresolved semantic decision
for these ten proposed resolutions.

The broad suite, coverage, expanded mypy, pip-audit, dependency repairs,
pre-existing reader-retention residue and bounded Owner release-order pass
remain deferred or outstanding. Publication remains blocked. No staging,
commit, push, merge, publication, activation or shared-store write occurred.

## Architecture Notes

No drift from design principles. The declared scope exceptions and separate
house-rule presentation follow existing ownership and recorded directions.

**Stop point: present this exact candidate for Owner acceptance before any
recording. Acceptance alone grants no publication or activation authority.**
