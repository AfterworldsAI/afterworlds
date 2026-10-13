# CRD Issue 15c — C8 successor recording

The Owner answered **"Accept exact C8"** (`../issue-15c-c8-native/owner-acceptance-2026-10-13.md`; decision packet `7a29c7cd…`). This directory records that acceptance.

- **What was recorded:** `record_successor.py` recorded `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json`.
  - **Real file SHA-256:** `ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d`, 44,637,018 bytes.
  - **Built on:** the C7 successor, `2853f30a…`, which is unchanged.
  - **Recorded at:** `2026-10-13T17:50:52Z`.
- **Identities that equal the accepted preview:** oracle `70646cd9…`, projection `e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42`, payload `e615d010…`, schema 21 `4499b396…`, and all five proposal identities.
- **What differs from the reviewed SIMULATED preview** (`a2d96264…`, preserved): only the acceptance evidence `reviewer`, `accepted_at` and `rule`, and only on the five touched batches. Rows are matched by identity, and the untouched rows keep their order.
  - Native validation has 0 findings.
  - Persist → reconstruct → re-identify is clean.
  - The read-only gate passes in a private store copy.
  - Full proof: `recorded-followup.json`.
- **Run evidence:**
  - `record.out.txt` and `record.err.txt` (empty) are the run's output.
  - **Ignore `record.exit.txt` as a verdict.** cmd expanded `%errorlevel%` before Python ran.
  - The actual Python exit (0) was observed independently by Codex in `../issue-15c-preparation/c8-recording-exit-observer/result.json`.
- **Rerun:** a rerun from the repository root verifies byte for byte (write-once):
  ```
  PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-c8-recording/record_successor.py
  ```

**Boundary:** recording is not execution certification, publication or activation.
