# Recorded release-order live-pin review

Codex independently confirms recorded oracle SHA-256 `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`: all accepted candidate semantics and proposal identities are exact, only the six approval fields and native evidence sorting change, and full native projection/acceptance-evidence reconstruction passes with zero findings. No rerecording is needed.

## Bounded correction

**P2 — implementation work, current inventory pin omitted.** `tests/ingestion/mechanical/test_packaging.py::test_the_production_oracle_directory_ships_only_reviewed_content` still expects three files. The source directory now correctly has four. Add exactly `srd-5-2-1-corpus-8781d4e0-a3b.json` to the sorted expected list; preserve all historical names, exact equality and the sentinel negative assertion. No wheel/sdist rebuild or broad package suite is needed.

The focused pre-correction diagnostic is retained as `run/codex-packaging-pin-before.log` / `.exit`, raw exit 1 with one failed inventory assertion. Codex's invocation also inherited repository default coverage flags, producing a separate 80-percent coverage failure; this is not coverage success or a broad-suite run. Use `-o addopts= --no-cov` for the bounded correction diagnostic, preserving the failed raw log.

**P2 — implementation work, accepted proposal-identity inventory omitted.** `tests/ingestion/mechanical/test_committed_accepted_authority.py::test_no_refused_candidate_is_selectable` unions all committed batch identities but its exact expected set omits the 24 new bound identities. The bounded reviewer directly observed this assertion failing. Identities stayed fixed from the accepted NEW candidate to the NEW recording; all 24 rebound proposal identities differ from the OLD live binding. Add the 24 exact identities extracted from the independently reviewed immutable accepted candidate, preserving the entire historical expected set, exact equality and refused-ID assertions. The sibling `accepted-new-proposal-identities.json` gives the candidate pin and exact batch/identity mapping for review. Do not derive expected values from the same current oracle being tested, use a subset assertion, rederive accepted proposals or change generators.

Both findings are stale current-inventory pins within the now-authorized recording scope. They require no new Owner Decision, rerecording, changed semantic approval, source rebuild or broad suite.
