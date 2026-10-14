# CRD Issue 15b — Owner acceptance of PR #194 and native packet

Recorded by Codex on 2026-10-14 from the Owner's direct message:

> I accept PR #194 and the native review packet, including the proposed combat Action cost. Check CI and prepare the next whole 15b PR. Preserve #129’s explicit resume gate; no merges or shared-runtime operations.

Accepted PR: https://github.com/AfterworldsAI/afterworlds/pull/194 at `5d05f4732c41a527dddd5e40dbd0ac045aaceb75`.

This accepts the whole proposal, including ADR-015b Group 17 (15b-37), S1 and C9 r2, and the initiating-participant Action cost during an active combat turn. The resisting check costs no additional Action. Outside active combat no per-turn use is recorded. The described off-turn/Bonus Action/Reaction/free-effort refusals remain binding.

Exact accepted artifacts:

- S1 SHA-256 `c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a`.
- C9 r2 raw SHA-256 `a3d40545d1a0ea1b4a1e24a1e3831b12b972f50ea26981b0edf1b578fd0648db`.
- Supporting preview branch head `002de94d04d26fbcfbbf3d5872696c13bc90f5ae`.
- Native bundle `C9-NATIVE-OWNER-REVIEW.zip`, SHA-256 `acbee2ed44b3795614f2b0d5e08982b8cf9cac57bffa5d50cc5b306d5ca1c22d`.
- Native preview SHA-256 `3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3`.
- Native oracle identity `924321dff5ab1821de3a4cdf464e3db1aa28859238458ddd6a58663ddf15ab0c`.
- Projection `3703faf5-8b51-5c3f-b28c-b378b005f7bf`; payload hash `c7a52d551823917a8def153396262a816eb51c60a5c6b5a58cdb8d009902b82f`.
- Composite native report SHA-256 `d61ed1b435e539da7127373d387d2124167581b9df9b5fcc9afb146049e096d4`.

CI run `38555377777` completed SUCCESS at the exact accepted PR head: all 11 jobs passed. `pr-194-accepted-head-ci.json` and `ci-38555377777-completed.json` preserve the live check.

The next whole PR records the accepted C9 successor, lands schema 22 with it and recertifies affected 15c authority. Acceptance permits that controlled local repository work. The native simulation stays preserved as simulation; real Owner recording must use the native acceptance mechanism and show the permitted evidence-only delta.

PR #129 remains OPEN/FROZEN at `d8233a435b6b7bf11cc043786570063027ccec57`. This receipt does not release its explicit resume gate. No dependent lifecycle implementation or Phase 3 begins in this upstream PR. No merge, shared-runtime migration, publication or activation is authorized. C8 bytes, all unaffected source/proofs and earlier acceptance receipts remain preserved.
