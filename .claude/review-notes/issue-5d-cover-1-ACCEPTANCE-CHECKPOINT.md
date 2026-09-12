# CRD Issue 5d — `cover-1` accepted

**Owner Decision, 2026-09-11.** Ravenlok accepts all 28 spans and the complete representation of
proposal `1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01` as batch `cover-1`,
extending the preserved five-batch prior through the registered schema transitions. That
authorization superseded the standing prohibition on accepting this batch and on updating the
committed accepted authority. It authorized nothing else: **no publication, activation, retirement,
or merge**, and no further corpus batch or runtime geometry. Parent tracking issue #137 remains in
progress.

Performed through the repository's real `accept_proposal` path. Every claim below is executed by
`.claude/review-notes/issue-5d-cover-1-ACCEPT.py`, which is retained. **The Owner made the decision;
the script executed the recorded action and reviewed nothing** — the report says so in a field of its
own rather than leaving the distinction to a reader. The final independent review is
`cover-1-final-owner-review.md` in the Codex task folder; it is named in the report rather than
cited, because it is not a repository file and the script does not read it.

| | |
|---|---|
| Batch | `cover-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-11T17:14:44Z` — one timestamp across all 28 records |
| Proposal identity | `1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `132bbc9f…3d07e` / `cbf0b530…2899` — unchanged by the acceptance |
| Reviewed head | `717e6b10aa0cd355e3d2e354b4b0a9c38ed443b2` |
| Schema | `5d-representation-schema-10` / `c39e3a35e197a1d1db5c2c2b3445ff0cbf03395c91e3426353a4bce589be4be0` |
| Scope | 28 spans · 16 leaves · 1 record · 16 substantive / 12 supporting / **0** unresolved / **0** non-mechanical |
| Source sites | `combat` and `glossary` — both printings of the entry, in one batch |
| Accepted oracle identity | `86cd11c2be330f5962982d8d87dfc1847815710868223257529f30bef8cdb500` |
| Accepted artifact content SHA-256 | `391c71b72d7fa9406890c74eed9a505278ea4f8f4536a01cd3db1edf403f6407` |
| Accepted artifact Git blob | `b7c0149432072d4a3b151d0f9b2c458252e584da` |

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings. Raw on-disk digests survive only as `..._raw_sha256_diagnostic`
fields in the report and decide nothing.

## The accepted timestamp is observed, and the write window is recorded beside it

`ACCEPTED_AT` is a pinned constant, not `datetime.now()`. A wall-clock read at replay would put a new
value into the artifact on every run, so the file digest above could never be reproduced and the
"reproduces exactly from retained repository inputs" claim would be false by construction. The value
is a UTC clock read taken in the same shell session that ran the acceptance, before the run, truncated
— not rounded — to the second. The report carries that basis in `accepted_at_basis` rather than
leaving a reader to assume it.

The local date of that session is **2026-09-11** and the local clock read was **10:14:44**; the UTC
instant is **2026-09-11T17:14:44Z**. The two differ because the workstation runs seven hours behind
UTC. Both are stated here rather than one being passed off as the other.

`ACCEPTED_AT` is the moment the acceptance was *initiated*, not the moment the bytes landed. The
acceptance run's own banners record the write window:

| | |
|---|---|
| `WRITE_STARTED` | `2026-09-11T17:31:20Z` |
| `WRITE_FINISHED` | `2026-09-11T17:32:23Z` |

The sixteen minutes between the clock read and the write are not the script's runtime and are not
presented as it. The clock was read once and then **held fixed** while the script itself was
corrected: its recorded `rule` prose was rewritten and the three merged identity pins re-derived to
match. The pins that correction superseded came from `_cover1_pin_probe.py`, a truncated copy of the
script that stops before the write section and never calls `_write_artifact` — so **no earlier
attempt wrote the artifact**, and the run log holds exactly one `WRITE_STARTED`. The artifact was
written once, by the run whose banners are quoted above. Both banners are in the retained run log;
neither is reported as `ACCEPTED_AT`.

## The acceptance authority, and what was retained beside it

The authorization sentence is carried verbatim in the script's `AUTHORIZATION` constant and echoed in
the report's `authorization` field, so the recorded action and the text that authorized it travel
together.

### The cross-check subject is the committed audit, not a review probe

`attitudes-1` cross-checked its acceptance against a review probe committed to the repository,
`.claude/review-notes/issue-5d-attitudes-1-final-independent-probe.json`. **This acceptance script
consumes no committed repository review probe**, and none was synthesized. Deriving the expected
counts from the artifact being checked would make the cross-check a restatement of its own subject,
so the reproduction is retained from tracked repository inputs alone.

What exists instead is the batch's committed audit,
`.claude/review-notes/issue-5d-batch-cover-1-audit.json`, written by the generator as the in-repo
evidence of the proposal, and pinned by canonical-LF digest
`927ca2d9985efce3fdcc2c851cff1f4a88d8c7021d15c2cd87f8f9d9abcd97ab` as `AUDIT_CONTENT_SHA256`. The
script cross-checks the merge against it on **27 named fields**, each reported separately in
`matches_retained_audit` so an audit that had drifted fails by name rather than by total:

`proposal_identity` · `schema` · `prior_sha256` · `prior_blob` · `prior_identity` ·
`prior_batch_ids` · `prior_spans` · `prior_collections` · `spans` · `records` · `components` ·
`facts` · `prose_bindings` · `references` · `relationships` · `provenance` · `leaves` ·
`source_sites` · `dispositions` · `obligation_tally` · `emits_no_reference` ·
`unresolved_before` · `unresolved_after` · `resolved_by_this_batch` · `resolving_citation` ·
`succession_step` · `no_open_schema_stop` — **all `true`**.

The claim that carries is the weaker one: an audit written by the generator is in-repo evidence of
what was proposed, not an independent second observation of it. That weaker claim is the true one,
and it is stated in the script's module docstring as well as here.

The rule prose the artifact now carries permanently is bound to that audit rather than trusted. The
six representation gaps it names — G1 the three-degree closure, G2 the defensive bonus, G3 the
direct-targeting prohibition, G4 the provision polarity, G5 the opposite-side requirement and G6
most-protective selection — are asserted against `gaps_closed`, every one is asserted to have at
least one witness in `gap_witnesses`, and `schema_stops` is asserted **empty**, which is why the rule
says the gaps were *closed* rather than that stops were found. The obligation split the rule states
in prose is asserted against `obligation_accounting.tally` for the same reason: prose baked into
accepted bytes cannot be corrected without reverting an acceptance.

Every input `--verify` requires is a tracked repository file: the proposal, the audit, the discovery
source manifest (canonical-LF `f82163ee…0cdcad`, the same digest the generator pins), the frozen
five-batch prior, the committed SRD PDF and the `afterworlds` package. Nothing is read from a private
workstation path, so the reproduction below runs in any checkout.

The semantic diff is retained in full inside the batch record, 28 entries, tallying
`none → substantive: 16` and `none → supporting_authority: 12`. Nothing was previously judged, so no
prior disposition moved.

## Two modes, and why the default one cannot pass twice

| Mode | Prior read | Purpose |
|---|---|---|
| default | the **live** committed artifact | performs the acceptance; a stale rerun fails early rather than double-merging |
| `--verify` | the **frozen five-batch fixture** | rebuilds the whole merge in memory from repository inputs and compares it to the committed result **byte for byte**; writes nothing |

`--verify` does not run the generator — the generator writes the proposal and the audit, and a
verification that writes has verified nothing about the bytes that were already there. Instead it
reconstructs the reviewed `MechanicalProposal` from the committed proposal JSON through the loader's
own field parsers, and proves it *is* that proposal by round-tripping the result back through
`proposal_payload` to those exact bytes and re-deriving the pinned proposal identity. It then hands
that object to the same `accept_proposal` seam the acceptance used.

The accepted scope is handed over **in its recorded order**, re-derived from the digest-pinned
discovery manifest. `resolved_scope` is the one field acceptance retains verbatim — spans, diffs and
every representation collection are canonicalized on serialization — and the generator emitted it in
manifest clause order, which the canonically sorted proposal JSON does not preserve. The two orders
are measurably different over the same 28-span set, so reading the order back from the artifact would
make the comparison test nothing; it is rebuilt from the inventory instead and the acceptance run
asserts the two derivations agree.

The comparison is total and is stated **before** the three identity pins, so it cannot be read as a
consequence of them: a difference anywhere in the merged file fails, including in fields no sampled
assertion covers. `test_cover_1_acceptance_reproduction.py` is the regression coverage, written as a
second independent implementation that imports nothing from the ACCEPT script, and its third test
demonstrates the gap the byte comparison closes — accepting the identical span set in the proposal's
canonical order yields an artifact with the same `oracle_identity`, the same counts, the same
dispositions, the same unresolved citations and no acceptance findings, and different bytes.

The frozen prior is
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1.json`
— content `9f380251…c1e738`, blob `467fcc62…9eef7`, `oracle_identity` `8e08ac48…c82d44b40`. It was
**not** written by this change: the report field `frozen_five_batch_prior_untouched` is `true`, and
the fixture's blob is unchanged in the commit diff. No six-batch freeze was created.

> **Erratum against the acceptance commit message.** The body of `1f3117d` says "all three frozen
> prior fixtures are untouched". The count is wrong: `tests/ingestion/mechanical/data/` holds
> **four** `accepted_prior_*.json` fixtures — `…hazards_1`, `…actions_1`, `…attitudes_1` and the
> five-batch `…areas_of_effect_1` pinned above. The untouchedness claim is correct for every one of
> them: the commit's 21 changed paths contain no `tests/ingestion/mechanical/data/` entry at all.
> Only the number is wrong. The message is left as written rather than amended, because the gate
> results recorded under `## Gates` were run on `1f3117d` itself.

## Merged result

| | conditions-1 | hazards-1 | actions-1 | attitudes-1 | areas-of-effect-1 | cover-1 | **merged** |
|---|---|---|---|---|---|---|---|
| spans | 185 | 96 | 182 | 24 | 43 | 28 | **558** |
| acceptance records | 185 | 96 | 182 | 24 | 43 | 28 | **558** |
| records | 16 | 6 | 13 | 4 | 7 | 1 | **47** |
| components | 54 | 15 | 37 | 3 | 23 | 4 | **136** |
| facts | 70 | 21 | 48 | 3 | 23 | 8 | **173** |
| prose bindings | 15 | 5 | 27 | 2 | 0 | 0 | **49** |
| relationships | 0 | 0 | 0 | 0 | 0 | 0 | **0** |
| references | 15 | 7 | 17 | 7 | 7 | 0 | **53** |
| provenance edges | 185 | 96 | 199 | 24 | 43 | 28 | **575** |

`cover-1` emits **no reference of its own** — it is the definition another batch cites, not a citer —
which is asserted as `emits_no_reference` rather than left to the reference total not moving.

Preservation is asserted element-wise rather than by total: `prior_batch_records_identical`,
`prior_acceptance_records_identical`, `prior_spans_identical`, `prior_obligations_preserved`,
`prior_schema_anchors_identical`, `prior_facts_still_present`, `prior_references_identical` — all
`true` — and `missing_prior_elements` is `0` for every one of the six representation collections.
`round_trip` is `true` and `validate_acceptance` is empty.

The succession is one row per crossing, through the single registered `5d-lift-schema-9-to-10`:
3 → 4 → 5 → 6 → 7 → 8 → 9 → 10. Each batch keeps the anchor it was reviewed under —
`conditions-1`→3, `hazards-1`→5, `actions-1`→7, `attitudes-1`→8, `areas-of-effect-1`→9, `cover-1`→10
— and no earlier anchor moved.

The four schema-10 components are probed by value rather than by count, so a merge that carried the
right number of the wrong facts fails:

| component | handling | facts |
|---|---|---|
| `glossary.cover/degree_benefit` | structured | `CoverDefensiveBonusFact` ×2, `CoverTargetingProhibitionFact` |
| `glossary.cover/degree_provision` | structured | `CoverProvisionFact` ×3 |
| `glossary.cover/degree_selection` | structured | `CoverDegreeSelectionFact` |
| `glossary.cover/benefit_origin` | structured | `CoverBenefitOriginFact` |

None is prose-bound, which is the point the schema-10 amendment turns on: no clause in this
population matches any closed reason code in `policy.IRREDUCIBILITY_REASONS`, so typed families were
required rather than chosen.

`primary_spans_per_fact` is `[1, 2, 2, 2, 2, 2, 2, 2]`. Seven of the eight facts are printed twice
and are claimed `PRIMARY` by the spans at **both** printings. Only **four** of those seven pairs
cross both sites, which is what the audit's `facts_printed_at_both_sites` counts: `half_benefit`
(`glossary/1/2` + `combat/6/0`), `three_quarters_benefit` (`glossary/1/3` + `combat/8/0`),
`total_prohibition` (`glossary/1/4` + `combat/11/0`) and `most_protective` (`glossary/1/5` +
`combat/1/3`). The remaining three pair two clauses inside `combat` alone — `half_provision`
(`combat/5/0` + `combat/6/1`), `three_quarters_provision` (`combat/7/0` + `combat/9/0`) and
`total_provision` (`combat/10/0` + `combat/11/1`) — and `opposite_side` (`combat/1/2`) is printed
once. Each is one fact claimed as `PRIMARY` by every span that prints it, because the source stated
one rule; `validation.py:622-623` rejects a *span* with more than one primary owner, not a fact with
more than one primary span, so this is shared authority with exact provenance rather than a
duplicate. The accepted `rule` prose states the same two counts.

## The blocker set moved **down**, and is asserted in both directions

`attitudes-1` closed three targets by accepting the complete source-defined Attitude class, as
`docs/architecture/known_unknowns.md` records. `areas-of-effect-1` closed none and added
`glossary.cover`. `cover-1` closes that one and adds none.

| | |
|---|---|
| unresolved before | `glossary.concentration`, `glossary.cover`, `glossary.speed` |
| resolved by this batch | `glossary.cover` |
| added by this batch | *(none)* |
| unresolved after | `glossary.concentration`, `glossary.speed` |

The arithmetic is pinned before the merge runs — `(before − resolved) | added == after` — and both
directions are asserted against the merged artifact afterwards, so a batch that resolved something it
did not claim to resolve fails just as loudly as one that failed to resolve something it did.

The citation this batch resolves is named exactly, not inferred from a count going down:
`resolving_citation` is `("glossary.area_of_effect", "", "srd-5.2.1/rules-glossary", "Cover")` — the
reference `areas-of-effect-1` recorded because the source states it. It now has a target.

`validate_representation` returns exactly **two** findings, and the script asserts the set is
**non-empty**: a blocker set that emptied here would be fabricated closure.

```
reference srd-5.2.1/rules-glossary:'Speed': unknown target record glossary.speed
reference srd-5.2.1/rules-glossary:'Concentration': unknown target record glossary.concentration
```

`still_blocked` is `true`. Speed and Concentration remain explicit unresolved targets, no target was
invented for either, and no batch for either is begun here.

## Reproduction

From the repository root, on this branch, with no private files and no network:

```bash
python .claude/review-notes/issue-5d-cover-1-ACCEPT.py --verify
pytest -q --no-cov tests/ingestion/mechanical/
```

`--verify` reads only tracked repository inputs, rebuilds the complete merged artifact in memory from
the frozen five-batch prior, the retained proposal and the pinned source manifest, and compares it to
the committed file byte for byte. It ends with
`reconstructed_artifact_byte_identical_to_committed: true`,
`accepted_artifact_matches_pinned_merged_identity: true` and
`frozen_five_batch_prior_untouched: true`. It **writes nothing**.

The default mode still refuses a stale rerun, and refuses it first: with the acceptance in place it
fails on the live artifact's pinned prior digest at
`assert _prior_content_sha == PRIOR_CONTENT_SHA256` (`issue-5d-cover-1-ACCEPT.py:548`), before the
generator executes and before anything is written. The captured refusal's stdout is **0 lines long**,
which is the evidence that nothing ran ahead of the guard.

The full stdout of the acceptance run itself is retained untracked under
`.claude/review-notes/accept-run/` as `cover1-acceptance-run.log`, with the JSON report split out as
`cover1-acceptance-report.json`; the pre-commit verifications are `cover1-verify-pre-commit.json`
and `cover1-verify-final.json` — the second run after the baseline splice and this checkpoint
existed, exit 0 with empty stderr — and the refusal is `cover1-stale-rerun-refused.err` / `.out`. The acceptance run's stdout is not pure
JSON because the script executes the generator through `runpy` first — that is why the log and the
report are two files rather than one. Those captures are untracked scratch, following the
`areas-of-effect-1` precedent; the **committed, replayable** evidence is `--verify`.

## Which committed checks changed, and why each had to

None was weakened or deleted. Every one below asserted something true of the five-batch artifact and
now asserts the same property of the six-batch one.

| Module | What moved |
|---|---|
| `test_committed_accepted_authority.py` | sixth batch id and proposal identity; oracle identity, content digest, blob, projection uuid and payload hash re-pinned; `COVER` count dict added and `MERGED` re-summed; sixth anchor, the `9-to-10` lift and the sixth `accepted_at` added to their lists; the record-key partition gained `glossary.cover`; two test names widened from *five* to *six* |
| `test_committed_accepted_authority.py::test_accepted_authority_is_lifted_rather_than_restamped` | restored to its *declares-current-authority* form, as the `areas-of-effect-1` acceptance restored it before schema 10 superseded it. The artifact now declares schema 10, which this build implements, so `validate_schema_binding` returns `()`, `records == ()` and `lifted is inputs`. The frozen schema-3 specimen still carries the other half of the rule, unchanged |
| `test_cover_1_frozen_prior.py` | `test_the_committed_artifact_is_still_these_bytes` → `test_the_committed_artifact_extends_this_copy_by_exactly_one_batch`. This is the replacement that module's own docstring promised when it was written: *"when that happens it is replaced by the extends-by-exactly-one-batch claim, as its predecessors were, rather than deleted"* |
| `test_areas_of_effect_1_frozen_prior.py` | its extends-by-**one** claim generalized to extends-by-**the-batches-since**, following the `test_attitudes_1_frozen_prior` precedent rather than being re-pinned to a single batch name |
| `test_attitudes_1_frozen_prior.py` | the same claim, now naming three batches since its freeze |
| `test_areas_of_effect_1_acceptance_reproduction.py` | its comparison target retargeted from the live artifact to the frozen five-batch fixture, which **is** the bytes that acceptance wrote (blob `467fcc62…`). All four tests keep their force; the attachment between fixture and live artifact is what `test_cover_1_frozen_prior` now proves |
| `test_cover_1_acceptance_reproduction.py` | **new**, following the `areas-of-effect-1` module clause for clause: a second independent rebuild of this merge, a proof the two scope orders differ, the discrimination test, and the out-of-scope refusal |
| `test_accepted_inputs.py` | batch-id and anchor-order lists; the 46/530 sentence → 47/558 |
| `test_production_release.py` | 46 → 47 records, 530 → 558 spans, and the record breakdown corrected to name Cover as a glossary rule that defines no list |
| `test_schema_6_succession.py` | `COMMITTED_CONTENT_SHA256` re-pinned. The frozen two-batch copy's own digest is untouched — the sentinel exists to be able to fail for one and pass for the other |

## Acceptance status reconciled at every site

| Site | What it now says |
|---|---|
| `docs/architecture/known_unknowns.md` §5d | six batches, 47 records / 558 spans, **two** remaining unresolved targets, and that this batch closed the one `areas-of-effect-1` added. The schema-10 paragraph's "still three" sentence is marked expired in place rather than rewritten |
| `docs/decisions/adr-005d-…md` | a dated historical block beneath the schema-10 amendment. The amendment paragraphs are **kept as written** — they record the state at registration — and the block records what the acceptance changed and what it did not |
| `src/afterworlds/ingestion/mechanical/oracle.py` module docstring | six batches, 47 records / 558 spans |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | six batches; records the schema-9→10 crossing as a lift; states that the residue went **down** and that it moves in both directions |
| `src/afterworlds/ingestion/mechanical/publication.py` | six batches, 47 records over 558 spans |
| `pyproject.toml` package-data comment · `MANIFEST.in` | six batches |
| `issue-5d-cover-1-DISCOVERY-CHECKPOINT.md` | a superseded banner beneath its existing partial-supersession banner. Every status line beneath both is preserved: they are the evidence of what was put in front of the Owner |

## The required secrets gate

`detect-secrets` was run exactly as `.pre-commit-config.yaml` configures it —
`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>` — against the
staged set, and exits **0** with no output.

The artifact's own baseline block had to be re-spliced: the acceptance added 28 spans, so the JSON's
64-hex literals moved and new ones appeared, and a JSON file cannot carry an inline
`pragma: allowlist secret`. The block was produced by scanning **that one file** into a **copy** of
the existing baseline and taking only `results[<the oracle path>]` from the copy — a bare
`detect-secrets scan --baseline` against the real file was measured to drop the blocks for thirteen
other files, which is exactly what the copy avoids. `version`, `plugins_used`, `filters_used`,
`generated_at` and the key order are byte-identical to `HEAD`, no file block was added or removed,
and the oracle block is the only one that changed (114 → 123 entries). Every hash the baseline
already carried for that file is asserted to still be present — the file was extended, not rewritten
— and nothing was added to the baseline to silence a live hit.

## Gates

Run attached, on the working tree that became this commit. The only files changed after the run were
`.secrets.baseline` and this checkpoint; no test reads either, which was checked rather than
assumed.

| Gate | Result |
|---|---|
| `black --check src/ tests/` | pass — 470 files unchanged |
| `ruff check src/ tests/` | pass |
| `mypy src/` | pass — no issues in 225 source files |
| `pytest -q --no-cov tests/ingestion/mechanical/` | pass — **2637 passed** in 154.41s |
| `detect-secrets` pre-commit hook on the staged set | pass, exit 0 |
| `pip-audit` | **nonzero — 29 known vulnerabilities across 10 packages** |
| full default coverage suite | **not run in this invocation** — Codex supervises it after the acceptance changes settle, and a duplicate run is not started here |

`.claude/review-notes/` sits outside the `black src/ tests/` and `ruff check src/ tests/` gate paths,
so `issue-5d-cover-1-ACCEPT.py` is not reformatted to satisfy a gate that does not read it — the same
disposition the `actions-1` schema-stop checkpoint records, and the same one the accepted
`areas-of-effect-1` generator sits under.

`pip-audit` exits 1 and is reported as it ran, not as green: `chromadb 1.5.7` (PYSEC-2026-311, -3813,
-3814, -3815, no fix version published), `click 8.3.1` (PYSEC-2026-2132 → 8.3.3),
`cryptography 49.0.0` (PYSEC-2026-3552 → 50.0.0), `idna 3.11` (PYSEC-2026-215 → 3.15),
`mako 1.3.10` (PYSEC-2026-2617 → 1.3.12), `msgpack 1.1.2` (PYSEC-2026-3625 → 1.2.1),
`pip 26.0.1` (PYSEC-2026-196, -2875, -2876, -3721 → 26.2), `pydantic-settings 2.13.1`
(CVE-2026-58203 → 2.14.2), `setuptools 82.0.1` (PYSEC-2026-3447 → 83.0.0), `urllib3 2.6.3`
(PYSEC-2026-141, -142 → 2.7.0). `afterworlds 0.1.0` is skipped as not on PyPI.

**Disposition: untouched by this change, and out of its scope.** Stated as what was actually
verified, not as a chronology:

* the audit exits **1** locally, with the 29 findings above, and is reported at that value;
* this branch changes **no dependency**. `git diff origin/main...HEAD` touches no lock file, no
  requirements file and no dependency specification; `pyproject.toml`'s only modification is a
  package-data *comment*;
* no audit configuration, ignore list or suppression was added or changed, and the gate was not
  weakened.

Unchanged dependency files do not establish when an advisory was first published, so no claim is made
that these findings predate the change; the three verified facts above are what is asserted instead.
The counts differ from the `areas-of-effect-1` checkpoint's because the local environment's installed
versions differ, which is a property of the environment and not of this branch. No audit suppression,
no `npm`/`pip` audit fix, no version bump and no environment maintenance was performed. Dependency
remediation is separate work with its own review.

## Architecture Notes

`No drift from design principles`, with three disclosures that are properties of the accepted content
rather than deviations from the contract:

1. **The publication blocker set shrank.** That is a consequence of defining the entry another batch
   already cited, not evidence of completion, and not the first such narrowing — `attitudes-1`
   closed three targets, as `known_unknowns.md` records. Two targets remain, the corpus is still
   incomplete, and the residue is asserted in both directions so a fabricated closure would fail.
2. **The cross-check is an in-repo audit, not a review probe.** `attitudes-1` consumed a committed
   probe file; this script consumes no committed repository review probe, and none was synthesized.
   The claim made here is the weaker, true one.
3. **Seven of the eight facts carry two `PRIMARY` provenance claims, four of them across both
   sites.** Each doubly-printed rule is one fact claimed by every span that prints it — four pairs
   spanning `glossary` and `combat`, three pairing two `combat` clauses. That is ADR-005d
   Decision 3's many-to-many provenance used as intended, not a duplicate the validator failed to
   catch — `validation.py:622-623` constrains spans, not facts.

No parameter value, unit, coordinate or grid semantic is represented anywhere. Cover declaratively
records what the source prints; it does not measure geometry, choose a degree for a scene, execute an
attack or change adapter ownership. Runtime geometry, grid simulation, adapter execution and
downstream adjudication stay outside, where ADR-005d Decision 11 and #137's Out of scope leave them.
No table, settled classification, rules engine or downstream adapter ownership is reopened.

## Stop conditions honoured

Accepting is not publishing. This change **published, activated and retired nothing**; the release
still resolves to a committed oracle and still refuses as `INCOMPLETE`, and the runtime binding still
reports `UNPUBLISHED`. This is a **sixth accepted batch and not full-corpus completion** — the
full-corpus work ADR-005d Decision 5 requires remains undischarged. No six-batch frozen prior fixture
was created and the five-batch one is untouched. No further batch, no runtime geometry, no unrelated
batch and no dependency maintenance was begun. Nothing was pushed and nothing was merged — the Owner
merges. Parent tracking issue #137 remains in progress, its state unchanged.
