# CRD Issue 15c — final C8 evidence baseline review

Verdict: **delta cleared; no blocking defect found**. Disposition: **already safe / no change**. Reviewed immutable `555be9a` → `6caa63e`, reusing the earlier 333 C8 entries and recertification proof. This is whole-PR supporting evidence, not a new Owner milestone or full-gate/merge clearance.

The baseline adds **1,693 exact filename/detector/hashed-value entries across 29 committed evidence files**: 1,502 Hex and 191 Secret Keyword findings. There are **zero removals, existing-entry changes, line-number changes, audit-flag changes or non-results settings changes**. All 13,941 prior entries remain identical; the new total is 15,634. New entries have `is_verified: false` and no `is_secret` field. No previous true-secret or nonpublic entry was deleted or broadened.

| Actual added value meaning | Entries |
| --- | ---: |
| Source/artifact SHA-256 pins | 1,236 |
| Copied public baseline SHA-1 digests | 382 |
| Git revision pins | 33 |
| Mechanical proposal identities | 15 |
| Mechanical corpus-binding digests | 10 |
| Mechanical schema digests | 9 |
| Mechanical oracle identities | 4 |
| Mechanical projection digests | 4 |

All 1,693 entries have an exact source token whose SHA-1 equals the baseline value, and all reproduce using their actual detector under detect-secrets 1.5.0: Hex limit 3.0 and the unchanged empty Keyword exclusion. The 191 Keyword findings and 191 corresponding Hex findings concern the same public `hashed_secret` values copied into the recertification audit. Each traces to an exact previously cleared baseline key, not a credential. Thus there are 1,502 distinct file/token pairs.

Producer inspection confirms the source/module inventories are SHA-256 hashes of recorded file/Git-blob bytes; even entries under provider-credential module paths hash public source code rather than credentials. Recorder and acceptance snapshots match their previously reviewed source copies. Mechanical identities come from the retained typed identity/schema/binding fields and reviewed canonical-hash producers. All Git pins resolve to commit objects. No new credential was found or newly masked.

Detector plugins, thresholds, filters, metadata, pre-commit configuration, CI and `.gitignore` are unchanged. No production inline secret-allowlist annotation changed in this delta. The prior changed-value baseline-subtraction negative control remains applicable and was reused.

Full immutable revision/source hashes, the reproducible audit script, per-entry classifications and detector results are retained outside the publication evidence tree at `../issue-15c-preparation/c8-evidence-baseline-final-review/`. At 20:34 UTC on 13 October 2026, HEAD was `696c0de`; none of the reviewed baseline/source/control inputs had changed since the pinned review, including normalized working-file checks.

No application import, native/store operation, broad scan, test run, network access, Git mutation, baseline edit or implementation change was performed. Later report/evidence suppressions require their own actual narrow delta review. Gameplay corrections, full repository gates, stable-head CI and consolidated Owner acceptance remain separate parent-coordinated requirements.
