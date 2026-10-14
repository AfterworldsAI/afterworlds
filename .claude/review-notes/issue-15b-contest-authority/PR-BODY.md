## CRD Issue 15b — contest authority and contract amendment (#127 AC8)

**This PR proposes; it does not activate.** Codex reviews it and presents the whole PR to the Owner for acceptance or rejection. It contains:
- no runtime contest execution;
- no #129 change, no Phase 3 route and no UI;
- no publication, activation or migration;
- no recorded authority.

PR #129 stays frozen at `d8233a43`. The Owner's adoption of the SRD 5.1 contest policy is recorded. That adoption is separate from exact native semantic acceptance of S1 and C9, which has not been given.

### What was built

- **Owner policy record:** `docs/decisions/owner-decision-2026-10-14-contest-supplement.md`. The SRD 5.1 "Contests" procedure is an explicit v1 supplement:
  - the greater final total wins;
  - equal totals preserve the prior situation;
  - specific SRD 5.2.1 mechanics are unchanged.
- **Contract: ADR-015b Group 17 (15b-37, proposed).** It defines how generic two-participant contests run through the 15b lifecycle:
  - **Distinct forms are not converted:** recorded-total, passive, fixed or formula DC, and attacks and saves.
  - **Authority for each participant's check.** A creature's printed skill total applies to its usual ability pairing only. An atypical pairing refuses, as a bounded adapter exclusion.
  - **Timing:** backend dice are generated only after the player's result is accepted.
  - **Representation:**
    - each participant's check is an ordinary roll event (`CONTESTED`, `dc = None`, `"undetermined"`);
    - one immutable resolution (win or tie) is committed with the completing roll event;
    - a tie changes nothing.
  - **No effects**, so a contest cannot stand in for Hide, Influence or Grapple/Shove.
  - **Combat action accounting:**
    - the comparison spends nothing;
    - the initiating effort is accounted by SRD 5.2.1 and the 15c economy;
    - an off-turn initiation, or a Bonus Action, Reaction or free effort, refuses.
  - **Hidden-participant projection:** a known opponent with a hidden roll is distinct from a counterpart whose existence is hidden; the latter projects as an ordinary check.
  - **The proof matrix.**
  - **Ordered gates:** acceptance and the #129 gate, then the recording landing gate, then later activation, which is not a prerequisite for dependent code.

  AC8's text is unchanged, and it stays positive execution.
- **15b-36 pointers.** Recorded Owner Decision 15b-36 (empty-table cutover, fail before destruction) is marked as governing over ADR-015b's older nullable-preservation migration text. No migration change.
- **S1 supplement candidate** (`.claude/review-notes/issue-15b-contest-authority/supplement-s1/`):
  - the verbatim SRD 5.1 excerpt, from the pinned PDF `2504d2a0…`, page 77, with three listed word-split extraction corrections;
  - the Owner's three points and the CC-BY-4.0 attribution;
  - all of it as one deterministic `package_patch` override, `b9134dea…`, appending `play.d20_tests/contest`.
- **C9 creature-skill candidate (r2)** (`.../candidate-c9/`):
  - one `creature_skills` fact per accepted creature profile, 336 in all: 216 printed lists and 120 positively empty;
  - printed totals bound to the usual ability;
  - the schema-22 delta.
- **Forward references** in the 15c traceability and in Known Unknowns. The history is preserved.

### Native review packet (local preview branch, not in this PR)

`codex/issue-15b-c9-schema-preview` @ `002de94d` contains two things.

**The schema-22 preview code** (`b073cd4f…`):
- `CreatureSkillBonus(skill, ability, bonus)` and `CreatureSkillsFact`;
- manifested invariants, including the usual-ability pairing;
- the relational profile rule;
- the no-movement `21→22` lift;
- its tests.

**The C9 native SIMULATED packet** (`.claude/review-notes/issue-15b-c9-native/`):

| Item | Identity |
| --- | --- |
| Preview oracle | `3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3` |
| Projection | `3703faf5-8b51-5c3f-b28c-b378b005f7bf` |
| Payload hash | `c7a52d551823917a8def153396262a816eb51c60a5c6b5a58cdb8d009902b82f` |
| Packet report | `c9-packet.json` `d61ed1b4…` |

Its inputs are private, pinned copies of:
- the accepted C8 proposals;
- the isolated release store;
- the C5/C8 native scripts.

The originals are unchanged.

**Evidence by revision:**

| Revision | Run | Result |
| --- | --- | --- |
| `2121a50e` | construction | built twice byte-identically |
| `31810c08` | Codex-supervised, 714 s | **native:** zero validation findings; five malformed variants refused; clean store reconstruction for preview and lifted C8; own publication gate passed; cross gates refused both ways. **Sequencing:** main still selects C8 and its 14 executable 15c operations certify; the preview refuses `incompatible_certification` |
| `002de94d` | `--finish-report` | the corrected preservation proof passes, with a raw-vs-assembled order counterexample and negative controls; the native and sequencing results are carried under source-segment identity guards |

Two earlier verifier failures had one cause, positional and canonical-order assumptions in proof code. They are preserved and documented in `verifier-defect-note.md`.

### Acceptance coverage

| Requirement | Evidence |
| --- | --- |
| AC8 positive execution | contract and proof matrix in Group 17. Execution follows acceptance and recording |
| The supplement matches the rule and the pinned source | S1 `validation.json`, 28 of 28 |
| Explicit, versioned, bound and auditable | deterministic override; release-bound; the component schema id moves on any text change; absent under empty or disabled sets; all 15 manifest fingerprints unchanged |
| Creature-skill completeness, exact modifiers, absence versus missing, qualifiers and provenance | C9 `validation.json`, 19 of 19: bijection of 216 lines onto 216 profiles; positive absences; no qualified entries; usual-ability pairing on all 429 entries, including the Assassin case; quotes on their cited lines |
| Typed serialization, lift, round trip and publication identities | the preview-branch schema tests and the native packet |
| Accepted artifacts unchanged | C8 `ead7fa9d…` read only; main's selection is still C8 |

### Test evidence

- **This branch** changes no `src`, `tests`, migrations or dependencies.
  - `black --check src tests`, `ruff check src tests` and `mypy src/` (strict) are clean.
  - The review scripts pass black and ruff, and the detect-secrets hook passes.
  - The S1 and C9 validators pass deterministically.
  - **pytest and pip-audit were not run.** Nothing they cover changed. Exact-head CI is required.
- **Preview branch:**
  - black, ruff and mypy are clean;
  - focused schema diagnostics: 3,630 passed and 1 failed (a class-name string in the schema contract); after the fix, the affected 1,417 passed;
  - the native packet passes as above;
  - the full suite was not run.

### Owner Decision proposed for whole-PR review

- **Contest action cost in an active turn.** The source says efforts "typically" take an action.
  - Proposed: v1 always charges the initiator's one action in an active turn, and refuses a GameMaster-declared costless contest.
  - This is not implemented.

### Architecture Notes

The deviations are bounded and disclosed.

1. **New authority from a second source.** The SRD 5.1 contest procedure enters as an authored override, which is the existing ADR-005d Decision 10 mechanism. It never carries SRD 5.2.1 provenance and never enters the accepted oracle.
2. **The override origin is `package_patch`.** The enum documents it as a "correction". No new origin was minted.
3. **Schema 22 is not in this PR.** It would move the active projection away from `CERTIFIED_RELEASE`, which the preview's sequencing proof shows. It lands with C9's recording and recertification, as C8's did.
4. **Observed, not changed:**
   - admitted 15c checks record no action use in an active turn;
   - the GameMaster prompt routing of Hide, Influence, Grapple and Shove is Phase 2 work.

There is otherwise no drift from the design principles. Known Unknowns touched: contests, as a dated status line; the history is unchanged.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
