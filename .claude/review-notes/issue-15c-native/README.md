# CRD Issue 15c — native schema-19 review preview (SIMULATION, acceptance held)

This is review material. The preview is not an accepted oracle and lives outside `src/.../oracles/`. Every replacement acceptance in it is visibly simulated. **Start with `OWNER-ACCEPTANCE-PACKET.md`.** It lists the exact identities, the evidence and the blockers.

| Path | What |
| --- | --- |
| `OWNER-ACCEPTANCE-PACKET.md` | Exact identities, semantic deltas, evidence, dependencies |
| `correspondence.md` | C5 → native mapping T, every difference disclosed, and the tool-activity table |
| `adr-005d-schema-19-amendment-DRAFT.md` | Draft amendment text (not applied) |
| `schema-19-src.diff`, `schema-19-tests.diff` | The working-tree src/test change, for review |
| `schema19/` | Schema-19 source blocks; `insert.py HASH` inserts them into `representation.py`, `schema_lift.py` and `projection.py` |
| `scripts/common.py` | Pins, replay and rebind (identity-matched to G1 anchors), and the private store copy |
| `scripts/native_map.py` | Correspondence T and the round-trip check |
| `scripts/build_proposals.py` | The 11 schema-19 proposals; refuses ownerless or unclaimed placements |
| `scripts/excise.py`, `identity_control.py`, `placement.py`, `prechecks.py` | Claim-based excision, singleton reversibility, placement and source prechecks |
| `scripts/lift_check.py`, `scalar_diagnostics.py`, `invariant_exemplars.py` | Schema proofs |
| `scripts/build_candidate.py` | Sequential control, then the changed chain with simulated evidence |
| `scripts/reconcile.py`, `verify_preview.py` | Identity reconciliation; native verification in private store copies |
| `reports/` | JSON results of each script |
| `preview/` | The preview oracle and rendered proposals |

**Re-run order:**
1. `git checkout --` the three src files.
2. `insert.py PIN`.
3. Pin the printed hash in `schema_lift.SCHEMA_19_HASH`.
4. Run Black.
5. Run the scripts: `lift_check`, `scalar_diagnostics`, `invariant_exemplars`, `build_proposals`, `build_candidate`, `verify_preview`, `reconcile`.

Run every script with `PYTHONIOENCODING=utf-8` and the repository `venv`.
