# CRD Issue 15c — C7 correction review

The two bounded corrections from `codex-c7-native-review.md` are closed. Reviewed preview-worktree commit `3166f2285c4951ffba8cb190d4a89a098d50a89a`, following `ed23cb77fbd4e561b20c718fcb068df15b4de797`.

The new relational reader calls `fact_invariant_violations` before observing an exact weapon-property or ammunition-supply fact. It skips refused structure and retains its existing structural finding. Refused target weapon structure is likewise excluded from relational observations. This addresses the reproduced malformed member crash and the container/weapon-kind siblings.

Existing public run logs show **9 passed in 0.04s** for the corrected validation file and **2,107 passed in 9.88s** for focused schema diagnostics. These are passing regression tests, not nine unresolved defects. Earlier one-failed/eight-passed output was superseded by the corrected run. Codex ran no tests in this recheck.

The corrected Owner packet presents one consolidated decision including the disclosed firearm inference, exact changes/preservation, and settled execution boundaries. Packet SHA `4912928fcfe58d0612ea908d21ad59988d6649b1e5b31be35b776d178948eb2c`.

Preview SHA remains `d661cc3be22aa6aca996a4e67cac4f8ebbd2dfa1908dd29a0c7ae2e38177ef6d`; no schema or semantic content changed. Schema hash, oracle identity, projection and payload remain as independently reviewed. No additional mint/store/recording was required. C5 SHA remains `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69`.

Verdict: the exact consolidated C7 packet is ready for explicit Owner semantic acceptance. This closes candidate-review findings only, not execution certification, repository full gates, CI or merge readiness.
