# CRD Issue 15b — C9 native SIMULATED preview (review packet)

> **Accepted and recorded (14 October 2026).** The Owner accepted PR #194 and this native packet
> (`../issue-15b-c9-recording/owner-acceptance-2026-10-14.md`). The C9 successor is recorded natively
> from the four exact proposals below (`../issue-15b-c9-recording/`), schema 22 lands with it and the
> 15c operations are recertified. This packet, its preview and its reports stay as they were reviewed:
> a simulation. The "Not done (held)" list at the end is the pre-acceptance state.

**This is a simulation only.** It is not an Owner acceptance, recording, publication, activation or supersession. This is the local preview branch `codex/issue-15b-c9-schema-preview`, not the proposed PR. Schema 22 exists only here, and main stays on accepted C8 at schema 21. The preview oracle and the four rendered proposals live in the git-ignored `preview/`; their digests are pinned below and in the builder (`CONSTRUCTED`).

| Item | Identity |
| --- | --- |
| Raw candidate C9 r2 | `c9.json` `a3d40545…48db`; correspondence `285ee055…f1e4`; inventory `daab6ac2…3d9b` (`issue-15b-contest-authority/candidate-c9/`) |
| Prior: recorded C8 successor | `srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json`, `ead7fa9d…2d0d`, read only |
| Schema | `5d-representation-schema-22`, `b073cd4f429631826efd628ed164a5ad680050c7e957e74680777922affb414f`; lift `5d-lift-schema-21-to-22` from schema 21, `4499b396…` |
| Preview oracle file | `3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3` (45,062,133 bytes) |
| Oracle identity | `924321dff5ab1821de3a4cdf464e3db1aa28859238458ddd6a58663ddf15ab0c` |
| Projection | `3703faf5-8b51-5c3f-b28c-b378b005f7bf`, payload hash `c7a52d551823917a8def153396262a816eb51c60a5c6b5a58cdb8d009902b82f` |
| Packet report | `reports/c9-packet.json`, `d61ed1b435e539da7127373d387d2124167581b9df9b5fcc9afb146049e096d4` |

| Batch | Accepted C8 proposal (rendered) → C9 proposal identity | Rendered SHA-256 | Facts / claims / rules |
| --- | --- | --- | --- |
| spell-descriptions | `68c75262…` → `2f296a37e843fc408a0b8cdab542d651364345c04d74cf36154a3e2479d3897b` | `48f1ba1291c2cba7aacc99e80a5552e49249467f9c6bf85c65cf2f64d4650848` | 4 / 4 / 4 |
| magic-items | `f6a8b412…` → `b5412d4bde82e7153f119783da126ac1251fcaa106cbe094f2416bd3400f9bc6` | `5255c82699780573c27905898720666d930abaf7d98f41e3524ea011a0e44168` | 2 / 2 / 2 |
| monsters | `c12dad28…` → `6445a5b1433ec73f9972c78f7d4f9edfd1bf204debc588ce55272effae3824ab` | `5b726871e6aa5b64120a1c01d33cd20764b6937e4ecce99102bac7a6456000a0` | 235 / 235 / 235 |
| animals | `6c2cd657…` → `3c6fa54203a5412d1d93b524d52ddb4fe80eb8627152c7761e14ac211c7305f3` | `c3dbcc7184f9167b356ec39bee9afbdb0c8bf22822f54d7951878f311275bc37` | 95 / 95 / 95 |

## Inputs: read-only reuse, private copies

These are copied to `../c9-native-work/inputs/`, digest-checked before use, and checked again after the copy:
- the four accepted C8 rebuilt proposals, from the preserved C8 preview worktree `agent-aa5b1ea6bf4ee4f39`. The C8 recording proved they render identically to the accepted ones;
- the isolated release store `g1-work/rel/afterworlds.db` (`9b427fff…`) and `leaves.json` (`700b502b…`). The store is only ever copied again into a temporary directory and never opened in place;
- `scripts/common.py` (`20761dc0…`) and `excise.py` (`80a177b3…`), copied unchanged from the C5/C8 native scripts.

All originals were unchanged after copying.

## Evidence, by revision

| Revision | What ran | Result |
| --- | --- | --- |
| `2121a50e`, builder `b68ae789` | Construction (Codex-supervised): four proposals built, chained with SIMULATED evidence, recording the `21→22` lift | `built 107 s`, `twice identical 201 s` (byte-identical), `preserved 230 s`, then **exit 1** in the malformed-input verifier (round 1 in `verifier-defect-note.md`) |
| `31810c08`, builder `c4a9a8bf` | `--verify-existing` (Codex-supervised, 714 s) | All native and sequencing proofs passed (below). **Exit 1** on one conservation boolean, the raw-vs-assembled component delta (round 2). Report preserved at `308b65ad` |
| finishing revision (this commit) | `--finish-report` (43 s, foreground) | The corrected `preserved()` is all true, with alignment counterexample, three negative controls and direct invariant findings. Native and sequencing results are carried under source-segment identity guards. `PACKET PROOFS PASSED` |

**Native proofs** (carried from `31810c08`):
- `validate_candidate` returns 0 findings;
- all five malformed variants are refused:
  - an unsorted skills list;
  - a duplicated skill;
  - Strength (Acrobatics) for the Assassin;
  - two facts on one profile;
  - a skills fact on a weapon component;
- persist → reconstruct → re-identify is clean for the preview and for lifted C8, in a private store copy;
- the preview's own publication gate passes with no failures;
- lifted C8 is refused against the preview, and the reverse.

**Sequencing proofs** (carried):
- main still selects C8;
- the 14 executable 15c operations still certify on C8 under the schema-22 build;
- the preview projection is not `CERTIFIED_RELEASE`, and every operation refuses `incompatible_certification` on it.

This is why schema 22 lands only with a recorded C9 successor and recertification.

**Preservation** (recomputed):
- untouched acceptance, review-unit and anchor rows are identical in order;
- the lift prefix is unchanged and exactly `21→22` is added;
- spans, bindings, policy, references and resolutions are unchanged;
- the touched review units change only by 336 added rules;
- 336 components each gain one `creature_skills` fact and nothing else;
- 336 provenance claims are added and none removed;
- no handling changes;
- every collection delta equals the proposal delta, with components aligned by assembled fact order only.

## Reproduce

Run from this checkout, with `src` first on `PYTHONPATH`:

```
venv/Scripts/python.exe .claude/review-notes/issue-15b-c9-native/build_c9_preview.py --inputs ../c9-native-work/inputs --twice            # construction
venv/Scripts/python.exe .claude/review-notes/issue-15b-c9-native/build_c9_preview.py --inputs ../c9-native-work/inputs --verify-existing  # native proofs
venv/Scripts/python.exe .claude/review-notes/issue-15b-c9-native/build_c9_preview.py --inputs ../c9-native-work/inputs --finish-report    # packet report
```

## Not done (held)

- Owner acceptance of this exact packet.
- Recording the C9 successor.
- Landing schema 22 on main.
- 15c recertification.
- S1 activation.
- Contest execution.
- Any publication, push, PR, merge or shared-runtime operation.
