# CRD Issue 5d — `areas-of-effect-1` accepted

**Owner Decision, 2026-09-11.** Ravenlok accepts all 43 spans and the complete representation of
proposal `d602f4e59ab90dbb04852661f78f03e2e311025e80be03f39f4b324f2c6d6878` as batch
`areas-of-effect-1`, extending the preserved
`conditions-1`/`hazards-1`/`actions-1`/`attitudes-1` prior through the registered schema
transitions. That authorization superseded the standing prohibition on accepting this batch and on
updating the committed accepted authority. It authorized nothing else: **no publication, activation,
retirement, or merge**, and no further corpus batch or runtime geometry. Parent tracking issue #137
remains in progress.

Performed through the repository's real `accept_proposal` path. Every claim below is executed by
`.claude/review-notes/issue-5d-areas-of-effect-1-ACCEPT.py`, which is retained. **The Owner made the
decision; the script executed the recorded action and reviewed nothing** — the report says so in a
field of its own rather than leaving the distinction to a reader.

| | |
|---|---|
| Batch | `areas-of-effect-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-11T05:30:17Z` — one timestamp across all 43 records |
| Proposal identity | `d602f4e59ab90dbb04852661f78f03e2e311025e80be03f39f4b324f2c6d6878` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `f18f909c…184b9` / `b66283f8…bedb` — unchanged by the acceptance |
| Reviewed head | `210623fae0fd799f93e3767474e4b1e0f91888f7` |
| Schema | `5d-representation-schema-9` / `f5a5e30817e64f019e31aa7f4692d72611215e4294e7da36242e492bca6b336e` |
| Scope | 43 spans · 20 leaves · 7 records · 24 substantive / 19 supporting / **0** unresolved / **0** non-mechanical |
| Accepted oracle identity | `8e08ac48f2a57a4498557990a07270f9abd855b246c1039da68cc9ec82d44b40` |
| Accepted artifact content SHA-256 | `9f3802514298f519120680db4a9a20805f5dcb8a4b00dd8686ed6faddec1e738` |
| Accepted artifact Git blob | `467fcc62c8fb64e54cf74e73a6f55c384129eef7` |

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings. Raw on-disk digests survive only as `..._raw_sha256_diagnostic`
fields in the report and decide nothing.

## The accepted timestamp is observed, not invented

`ACCEPTED_AT` is a pinned constant, not `datetime.now()`. A wall-clock read at replay would put a new
value into the artifact on every run, so the file digest above could never be reproduced and the
"reproduces exactly from retained repository inputs" claim would be false by construction. The value
is a UTC clock read taken in the same shell session that ran the acceptance, before the run, truncated
— not rounded — to the second. The report carries that basis in `accepted_at_basis` rather than
leaving a reader to assume it.

The local date of that session is **2026-09-10**; the UTC instant is **2026-09-11T05:30:17Z**. The two
differ because the workstation runs behind UTC. Both are stated here rather than one being passed off
as the other.

`ACCEPTED_AT` is the moment the acceptance was *initiated*, not the moment the bytes landed. The
observed write time of the accepted artifact was `2026-09-11T05:36:00.4501496Z` (`LastWriteTimeUtc`).
That is recorded here, beside the pinned value, instead of being reported as it.

## The acceptance authority, and what was retained beside it

The authorization sentence is carried verbatim in the script's `AUTHORIZATION` constant and echoed in
the report's `authorization` field, so the recorded action and the text that authorized it travel
together.

### There is no review probe for this batch, and the checkpoint says so

`attitudes-1` cross-checked its acceptance against a retained review probe. **No probe exists for
`areas-of-effect-1`**, and none was synthesized. Inventing one — or deriving the expected counts from
the artifact being checked — would make the cross-check a restatement of its own subject.

What exists instead is the batch's committed audit,
`.claude/review-notes/issue-5d-batch-areas-of-effect-1-audit.json`, written by the generator as the
in-repo evidence of the proposal, and pinned by canonical-LF digest
`2b7f0dedff5216bff5083f3adfbce70573fb6a4f678a3321b7e45c2ff605cd32` as `AUDIT_CONTENT_SHA256`. The
script cross-checks the merge against it on **21 named fields**, each reported separately in
`matches_retained_audit` so an audit that had drifted fails by name rather than by total:

`proposal_identity` · `schema` · `prior_sha256` · `prior_blob` · `prior_identity` ·
`prior_batch_ids` · `prior_spans` · `spans` · `records` · `components` · `facts` ·
`prose_bindings` · `references` · `provenance` · `leaves` · `dispositions` ·
`unresolved_before` · `unresolved_after` · `resolved_by_this_batch` · `succession_step` ·
`no_open_schema_stop` — **all `true`**.

This is the one process deviation from the `attitudes-1` precedent, and it is a weaker claim than that
one made: an audit written by the generator is in-repo evidence of what was proposed, not an
independent second observation of it. The weaker claim is the true one and is stated in the script's
module docstring as well as here.

Every input `--verify` requires is a tracked repository file: the proposal, the audit, the generator,
the frozen four-batch prior and the `afterworlds` package. Nothing is read from a private workstation
path, so the reproduction below runs in any checkout.

The semantic diff is retained in full inside the batch record, 43 entries, tallying
`none → substantive: 24` and `none → supporting_authority: 19`. Nothing was previously judged, so no
prior disposition moved.

## Two modes, and why the default one cannot pass twice

| Mode | Prior read | Purpose |
|---|---|---|
| default | the **live** committed artifact | performs the acceptance; a stale rerun fails early rather than double-merging |
| `--verify` | the **frozen four-batch fixture** | re-derives the whole merge from repository inputs and compares it to the committed result |

The frozen prior is
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1.json`
— content `fd390d95…b787ab`, blob `2346404005…b200f`, `oracle_identity` `c3b4d4b7…5b74fa`. It was
**not** written by this change: the report field `frozen_four_batch_prior_untouched` is `true`, and
the fixture's blob is unchanged in the commit diff. No five-batch freeze was created.

## Merged result

| | conditions-1 | hazards-1 | actions-1 | attitudes-1 | areas-of-effect-1 | **merged** |
|---|---|---|---|---|---|---|
| spans | 185 | 96 | 182 | 24 | 43 | **530** |
| acceptance records | 185 | 96 | 182 | 24 | 43 | **530** |
| records | 16 | 6 | 13 | 4 | 7 | **46** |
| components | 54 | 15 | 37 | 3 | 23 | **132** |
| facts | 70 | 21 | 48 | 3 | 23 | **165** |
| prose bindings | 15 | 5 | 27 | 2 | 0 | **49** |
| relationships | 0 | 0 | 0 | 0 | 0 | **0** |
| references | 15 | 7 | 17 | 7 | 7 | **53** |
| provenance edges | 185 | 96 | 199 | 24 | 43 | **547** |

Preservation is asserted element-wise rather than by total: `prior_batch_records_identical`,
`prior_acceptance_records_identical`, `prior_spans_identical`, `prior_obligations_preserved`,
`prior_schema_anchors_identical`, `prior_facts_still_present` — all `true` — and
`missing_prior_elements` is `0` for every one of the six representation collections. `round_trip` is
`true` and `validate_acceptance` is empty.

The succession is one row per crossing, through the single registered `5d-lift-schema-8-to-9`:
3 → 4 → 5 → 6 → 7 → 8 → 9. Each batch keeps the anchor it was reviewed under — `conditions-1`→3,
`hazards-1`→5, `actions-1`→7, `attitudes-1`→8, `areas-of-effect-1`→9 — and no earlier anchor moved.

Four schema-9 components are probed by value rather than by count, so a merge that carried the right
number of the wrong facts fails:
`BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN` with `CoverDegree.TOTAL`;
`AreaMovementSuspension.(INSTANTANEOUS_EFFECT, STATIONARY_EFFECT)` as an ordered pair;
`AreaWidthRelation.EQUAL_TO_THAT_POINTS_DISTANCE_FROM_THE_POINT_OF_ORIGIN`; and
`AreaOriginInclusion.EXCLUDED_UNLESS_ITS_CREATOR_DECIDES_OTHERWISE`. Whole-batch shape is asserted
beside them: every one of the 23 new components is `STRUCTURED`, carries exactly one fact, and binds
no coordinate the prior already bound.

## The blocker set moved **up**, and is asserted in both directions

`attitudes-1` closed three reference targets. `areas-of-effect-1` closes **none** and adds one.

| | |
|---|---|
| unresolved before | `glossary.concentration`, `glossary.speed` |
| resolved by this batch | *(none)* |
| added by this batch | `glossary.cover` |
| unresolved after | `glossary.concentration`, `glossary.cover`, `glossary.speed` |

The arithmetic is pinned before the merge runs —
`(before − resolved) | added == after` — and both directions are asserted against the merged artifact
afterwards, so a batch that resolved something it did not claim to resolve fails just as loudly as one
that failed to resolve something it did. `validate_representation` returns exactly three findings, one
per missing target, and the script asserts the set is **non-empty**: a blocker set that emptied here
would be fabricated closure.

The seventh reference `areas-of-effect-1` states is `glossary.area_of_effect → glossary.cover`. It is
recorded because the source states it, not to imply a `cover-1` batch exists. None does, and none is
begun here.

## Reproduction

From the repository root, on this branch, with no private files and no network:

```bash
python .claude/review-notes/issue-5d-areas-of-effect-1-ACCEPT.py --verify
pytest -q --no-cov tests/ingestion/mechanical/
```

`--verify` reads only tracked repository inputs, re-derives the merge from the frozen four-batch prior
and the retained proposal, and compares it to the committed artifact. It ends with
`accepted_artifact_matches_pinned_merged_identity: true` and
`frozen_four_batch_prior_untouched: true`. It **writes nothing**: run after the reconciliation above,
`git status --porcelain -- src/` showed no working-tree modification, and the report parsed equal to
the one taken at acceptance.

The full stdout of the acceptance run itself is retained untracked under
`.claude/review-notes/accept-run/` as `areasofeffect1-acceptance-run.log`, with the JSON report split
out as `areasofeffect1-acceptance-report.json`; the pre-commit verification is
`areasofeffect1-verify-pre-commit.json`. The acceptance run's stdout is not pure JSON because the
script executes the generator through `runpy` first — that is why the log and the report are two
files rather than one.

## Which committed checks changed, and why each had to

None was weakened or deleted. Every one below asserted something true of the four-batch artifact and
now asserts the same property of the five-batch one.

| Module | What moved |
|---|---|
| `test_committed_accepted_authority.py` | fifth batch id and proposal identity; oracle identity, content digest, blob, projection uuid and payload hash re-pinned; `AREAS` count dict added and `MERGED` re-summed; fifth anchor and the `8-to-9` lift added to the anchor/lift/`accepted_at` lists; the record-key partition gained the six `area_of_effect.*` keys and `glossary.area_of_effect` |
| `test_committed_accepted_authority.py::test_accepted_authority_is_lifted_rather_than_restamped` | restored to its *declares-current-authority* form. The artifact now declares schema 9, which this build implements, so `validate_schema_binding` returns `()` and the succession is a no-op. The frozen schema-3 specimen still carries the other half of the rule, unchanged |
| `test_areas_of_effect_1_frozen_prior.py` | `test_the_committed_artifact_is_still_these_exact_bytes` → `test_the_committed_artifact_extends_this_copy_by_exactly_one_batch`. This is the replacement that module's own docstring promised when it was written: *"it is then replaced by the extends-by-exactly-one-batch claim, not deleted"* |
| `test_attitudes_1_frozen_prior.py` | its extends-by-**one** claim generalized to extends-by-**the-batches-since**, rather than being re-pinned to a single batch name or narrowed |
| `test_accepted_inputs.py` | batch-id and anchor-order lists; the 46/530 sentence |
| `test_production_release.py` | 39 → 46 records, 487 → 530 spans, and the record breakdown corrected to name all five lists |
| `test_schema_6_succession.py` | `COMMITTED_CONTENT_SHA256` re-pinned. The frozen two-batch copy's own digest is untouched — the sentinel exists to be able to fail for one and pass for the other |
| `test_runtime_production_release.py` | module docstring: five batches |

## Acceptance status reconciled at every site

| Site | What it now says |
|---|---|
| `docs/architecture/known_unknowns.md` §5d | five batches, 46 records / 530 spans, three remaining unresolved targets, and that this batch added one |
| `docs/decisions/adr-005d-…md` | a dated historical block beneath the schema-9 amendment. The amendment paragraphs are **kept as written** — they record the state at registration — and the block records what the acceptance changed and what it did not |
| `src/afterworlds/ingestion/mechanical/oracle.py` module docstring | five batches, 46 records / 530 spans |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | five batches; records the schema-8→9 crossing as a lift; states that the residue went **up** |
| `src/afterworlds/ingestion/mechanical/publication.py` | five batches, 46 records over 530 spans |
| `pyproject.toml` package-data comment · `MANIFEST.in` | five batches |
| `issue-5d-areas-of-effect-1-DISCOVERY-CHECKPOINT.md` | a superseded banner at the top. Every status line beneath it is preserved: they are the evidence of what was put in front of the Owner |

## The required secrets gate

`detect-secrets` was run exactly as `.pre-commit-config.yaml` configures it —
`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>` — against the
staged set, and exits **0** with no output.

The baseline gained **19** `Hex High Entropy String` entries for the extended artifact and re-numbered
the existing ones for that file, through a single-file rescan spliced into the existing baseline.
Nothing else moved: the diff touches exactly one `filename` — the oracle JSON — plus `generated_at`.
No plugin, filter, version, or other file block changed, and no previously baselined hash for that
file disappeared (asserted, not assumed). The running `detect-secrets` carries two detectors this
baseline's plugin block does not list; neither fired on this file, which is asserted rather than
hoped, so **no detector setting was changed** to make the gate pass.

## Gates

Run on the final branch head.

| Gate | Result |
|---|---|
| `black --check src/ tests/` | pass — 466 files unchanged |
| `ruff check src/ tests/` | pass |
| `mypy src/` | pass — no issues in 225 source files |
| `pytest -q` (full suite, attached to completion) | pass - **5502 passed, 10 skipped** in 1369.79s; total coverage 94.14%, above the 80% floor |
| `detect-secrets` pre-commit hook on the staged set | pass, exit 0 |
| `pip-audit` | **nonzero — 22 known vulnerabilities across 9 packages** |

`pip-audit` exits 1 and is reported as it ran, not as green: `chromadb 1.5.8` (PYSEC-2026-311, -3813,
-3814, -3815, no fix version published), `cryptography 49.0.0` (PYSEC-2026-3552 → 50.0.0),
`idna 3.11` (PYSEC-2026-215 → 3.15), `mako 1.3.10` (PYSEC-2026-2617 → 1.3.12),
`msgpack 1.1.2` (PYSEC-2026-3625 → 1.2.1), `pip 26.1.2` (PYSEC-2026-3721 → 26.2),
`pydantic-settings 2.14.0` (CVE-2026-58203 → 2.14.2), `pytest 9.0.2` (PYSEC-2026-1845 → 9.0.3),
`urllib3 2.6.3` (PYSEC-2026-141, -142 → 2.7.0). `afterworlds 0.1.0` is skipped as not on PyPI.

**Disposition: pre-existing, untouched, and out of this change's scope.** This change edits no
dependency: `pyproject.toml`'s only modification is a package-data *comment*. Every finding predates
it and is unrelated to CRD Issue 5d. No audit suppression, no `npm`/`pip` audit fix, no version bump
and no environment maintenance was performed, and the gate was not weakened to accommodate them.
Dependency remediation is separate work with its own review.

## Architecture Notes

`No drift from design principles`, with two disclosures that are properties of the accepted content
rather than deviations from the contract:

1. **The publication blocker set grew.** Accepting a complete source class resolved nothing and added
   `glossary.cover`. That is a consequence of representing what `[Area of Effect]` prints, not a
   reason to have represented it, and it is asserted in both directions rather than described.
   Sequencing a batch that states `Cover` is ordinary engineering under #137, not an Owner Decision.
2. **The cross-check is an in-repo audit, not an independent probe.** `attitudes-1` had a probe;
   this batch does not, and none was synthesized. The claim made here is the weaker, true one.

No parameter value, unit, coordinate or grid semantic is represented anywhere. Runtime geometry, grid
simulation, adapter execution and downstream adjudication stay outside, where ADR-005d Decision 11 and
#137's Out of scope leave them. No table, settled classification, rules engine or downstream adapter
ownership is reopened.

## Stop conditions honoured

Accepting is not publishing. This change **published, activated and retired nothing**; the release
still resolves to a committed oracle and still refuses as `INCOMPLETE`, and the runtime binding still
reports `UNPUBLISHED`. No five-batch frozen prior fixture was created and the four-batch one is
untouched. No further batch and no runtime geometry was begun. Nothing was merged — the Owner merges.
Parent tracking issue #137 remains in progress.
