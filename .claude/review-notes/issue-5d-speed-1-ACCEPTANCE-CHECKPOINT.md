# CRD Issue 5d — `speed-1` accepted

**Owner Decision, 2026-09-12.** Ravenlok accepts all 36 spans and the complete representation of
proposal `bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8` as batch `speed-1`,
extending the preserved prior through the registered schema transitions. That authorization
superseded the standing prohibition on accepting this batch and on updating the committed accepted
authority. It authorized nothing else: **no publication, activation, retirement, or merge**, and no
further corpus batch or runtime movement geometry. Parent tracking issue #137 remains in progress.

Performed through the repository's real `accept_proposal` path. Every claim below is executed by
`.claude/review-notes/issue-5d-batch-speed-1-ACCEPT.py`, which is retained. **The Owner made the
decision; the script executed the recorded action and reviewed nothing** — the report says so in a
field of its own (`reviewer_is_the_decision_maker`) rather than leaving the distinction to a reader.
The final independent review was a Codex semantic review of the reviewed head that returned no
blocking finding; it is named in the report rather than cited, because it is not a repository file
and the script does not read it.

| | |
|---|---|
| Batch | `speed-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-12T18:26:58Z` — one timestamp across all 36 records |
| Proposal identity | `bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `78e6dc72…f111188a` / `5bc15a8b…fe56` — unchanged by the acceptance |
| Reviewed head | `7a38b1619e7725c5b531d7b52bd06a2789d84eb2` |
| Schema | `5d-representation-schema-11` / `605e8b4cfdaf0cb6d4f0b65fcf0d23f3e45c4734404c9568f41dc4261eefd037` |
| Scope | 36 spans · 16 leaves · 1 record · 16 substantive / 20 supporting / **0** unresolved / **0** non-mechanical |
| Source sites | `combat` and `glossary` — both printings of the entry, in one batch |
| Accepted oracle identity | `d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f` |
| Accepted artifact content SHA-256 | `eed7df0476445fc6e5d1d9cd6bdd67977f72372bc67b01808eaa240b69a7e619` |
| Accepted artifact Git blob | `4fcfab6f667923acbaa98345b56a405061287643` |

The oracle identity and the proposal identity are two different things and are reported as two.
`bd9d4942…` is the content-derived identity of the *proposal* (`proposal.py:161`); `d395e4ed…` is
the identity of *accepted authority* after the merge. Neither is a projection identity.

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings. Raw on-disk digests survive only as `..._raw_sha256_diagnostic`
fields in the report and decide nothing.

## The accepted timestamp is observed, and the write is recorded beside it

`ACCEPTED_AT` is a pinned constant, not `datetime.now()`. A wall-clock read at replay would put a new
value into the artifact on every run, so the file digest above could never be reproduced and the
"reproduces exactly from retained repository inputs" claim would be false by construction. The value
is a UTC clock read taken in the same shell session that ran the acceptance, before the run,
truncated — not rounded — to the second. The report carries that basis in `accepted_at_basis` rather
than leaving a reader to assume it.

The local date of that session is **2026-09-12** and the local clock read was **11:26:58**; the UTC
instant is **2026-09-12T18:26:58Z**. The two differ because the workstation runs seven hours behind
UTC. Both are stated here rather than one being passed off as the other.

`ACCEPTED_AT` is the moment the acceptance was *initiated*, not the moment the bytes landed. This
script emits no write banner, so no banner is quoted: the observed write is the accepted artifact's
filesystem modification time, **2026-09-12 11:41:19 local = 18:41:19Z**, and it is reported as a
filesystem observation rather than as an instrumented timestamp. The roughly fourteen minutes between
the clock read and the write are not the script's runtime and are not presented as it; the clock was
read once and then held fixed while the script was assembled and run. The pins reported before that
run came from `.claude/review-notes/_speed1_pin_probe.py`, a probe that stops before the write section
and never calls `_write_artifact`, so **no earlier attempt wrote the artifact**.

## The acceptance authority, and what was retained beside it

The authorization sentence is carried verbatim in the script's `AUTHORIZATION` constant and echoed in
the report's `authorization` field, so the recorded action and the text that authorized it travel
together.

### The cross-check subject is the committed audit, not a review probe

**This acceptance script consumes no committed repository review probe**, and none was synthesized.
Deriving the expected counts from the artifact being checked would make the cross-check a restatement
of its own subject, so the reproduction is retained from tracked repository inputs alone.

What exists instead is the batch's committed audit,
`.claude/review-notes/issue-5d-batch-speed-1-audit.json`, written by the generator as the in-repo
evidence of the proposal, and pinned by canonical-LF digest
`15c1cf300d7a656b1d42c705b7b63407b1669f976912e39b9a31d6c43abd679a` as `AUDIT_CONTENT_SHA256`. The
script cross-checks the merge against it on **31 named fields**, each reported separately in
`matches_retained_audit` so an audit that had drifted fails by name rather than by total:

`proposal_identity` · `schema` · `prior_sha256` · `prior_blob` · `prior_identity` ·
`prior_batch_ids` · `prior_spans` · `prior_obligations` · `prior_unchanged_by_the_review_run` ·
`spans` · `clauses` · `records` · `components` · `facts` · `prose_bindings` · `references` ·
`relationships` · `provenance` · `leaves` · `source_sites` · `dispositions` · `obligation_tally` ·
`unresolved_before` · `unresolved_after` · `resolved_by_this_batch` · `resolving_citation` ·
`emits_nine_record_owned_references` · `the_split_reference` · `not_publishable_alone` ·
`succession_step` · `no_open_schema_stop` — **all `true`**.

The claim that carries is the weaker one: an audit written by the generator is in-repo evidence of
what was proposed, not an independent second observation of it. That weaker claim is the true one,
and it is stated in the script's module docstring as well as here.

The rule prose the artifact now carries permanently is bound to that audit rather than trusted. The
six representation gaps it names — G1 what a Speed *is*, G2 the per-turn movement allowance, G3
depletion, G4 multi-speed selection and mid-move switching, G5 propagation of a Speed change to the
special speeds, and G6 *special speed* as a category with its printed mode list — are asserted against
`gaps_closed`, and `schema_stops` is asserted **empty**, which is why the rule says the gaps were
*closed* rather than that stops were found. The obligation split the rule states in prose is asserted
against `obligation_accounting` for the same reason: prose baked into accepted bytes cannot be
corrected without reverting an acceptance.

Every input `--verify` requires is a tracked repository file: the proposal, the audit, the discovery
source manifest (canonical-LF `8c8ea8eed38feaeb28d74386690b5ee28e43872b1316517b922fb89afa016b20`, the
same digest the generator pins), the frozen six-batch prior, the committed SRD PDF and the
`afterworlds` package. Nothing is read from a private workstation path, so the reproduction below runs
in any checkout.

The semantic diff is retained in full inside the batch record, 36 entries, tallying
`none → substantive: 16` and `none → supporting_authority: 20`. Nothing was previously judged, so no
prior disposition moved.

## Two modes, and why the default one cannot pass twice

| Mode | Prior read | Purpose |
|---|---|---|
| default | the **live** committed artifact | performs the acceptance; a stale rerun fails early rather than double-merging |
| `--verify` | the **frozen six-batch fixture** | rebuilds the whole merge in memory from repository inputs and compares it to the committed result **byte for byte**; writes nothing |

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
are measurably different over the same 36-span set, so reading the order back from the artifact would
make the comparison test nothing; it is rebuilt from the inventory instead and the acceptance run
asserts the two derivations agree.

The comparison is total and is stated **before** the three identity pins, so it cannot be read as a
consequence of them: a difference anywhere in the merged file fails, including in fields no sampled
assertion covers. `test_speed_1_acceptance_reproduction.py` is the regression coverage, written as a
second independent implementation that imports nothing from the ACCEPT script, and its third test
demonstrates the gap the byte comparison closes — accepting the identical span set in the proposal's
canonical order yields an artifact with the same `oracle_identity`, the same counts, the same
dispositions, the same unresolved citations and no acceptance findings, and different bytes.

The frozen prior is
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1_cover_1.json`
— content `391c71b7…f6407`, blob `b7c01494…84da`, `oracle_identity` `86cd11c2…0bef8cdb500`. It was
**not** written by this change: the report field `frozen_six_batch_prior_untouched` is `true`, and the
fixture's blob is unchanged in the commit diff. `tests/ingestion/mechanical/data/` holds **four**
`accepted_prior_*.json` fixtures and this commit changes none of them. No seven-batch freeze was
created.

## Merged result

| | conditions-1 | hazards-1 | actions-1 | attitudes-1 | areas-of-effect-1 | cover-1 | speed-1 | **merged** |
|---|---|---|---|---|---|---|---|---|
| spans | 185 | 96 | 182 | 24 | 43 | 28 | 36 | **594** |
| acceptance records | 185 | 96 | 182 | 24 | 43 | 28 | 36 | **594** |
| records | 16 | 6 | 13 | 4 | 7 | 1 | 1 | **48** |
| components | 54 | 15 | 37 | 3 | 23 | 4 | 9 | **145** |
| facts | 70 | 21 | 48 | 3 | 23 | 8 | 17 | **190** |
| prose bindings | 15 | 5 | 27 | 2 | 0 | 0 | 0 | **49** |
| relationships | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |
| references | 15 | 7 | 17 | 7 | 7 | 0 | 9 | **62** |
| provenance edges | 185 | 96 | 199 | 24 | 43 | 28 | 52 | **627** |

`speed-1` emits **nine record-owned references** of its own — it is a definition that is also a citer
— which is asserted as `emits_nine_record_owned_references` rather than inferred from the reference
total moving by nine.

Preservation is asserted element-wise rather than by total: `prior_batch_records_identical`,
`prior_acceptance_records_identical`, `prior_spans_identical`, `prior_obligations_preserved`,
`prior_schema_anchors_identical`, `prior_facts_still_present`, `prior_references_preserved`,
`merged_references_are_prior_plus_this_batch` — all `true` — and `missing_prior_elements` is `0` for
every one of the six representation collections. `round_trip` is `true` and `validate_acceptance` is
empty.

The succession is one row per crossing, through the single registered `5d-lift-schema-10-to-11`:
3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11. Each batch keeps the anchor it was reviewed under —
`conditions-1`→3, `hazards-1`→5, `actions-1`→7, `attitudes-1`→8, `areas-of-effect-1`→9,
`cover-1`→10, `speed-1`→11 — and no earlier anchor moved.

The nine schema-11 components are probed by value rather than by count, so a merge that carried the
right number of the wrong facts fails. None is prose-bound: no clause in this population matches any
closed reason code in `policy.IRREDUCIBILITY_REASONS`, so typed families were required rather than
chosen.

| component | handling | facts |
|---|---|---|
| `glossary.speed/speed_definition` | structured | `SpeedDefinitionFact` |
| `glossary.speed/movement_allowance` | structured | `MovementAllowanceFact` |
| `glossary.speed/movement_composition` | structured | `MovementCompositionFact` ×2 |
| `glossary.speed/movement_depletion` | structured | `MovementDepletionFact` |
| `glossary.speed/movement_modes` | structured | `MovementPermissionFact` ×4 |
| `glossary.speed/special_speeds` | structured | `SpecialSpeedFact` ×4 |
| `glossary.speed/speed_selection` | structured | `SpeedSelectionFact` ×2 |
| `glossary.speed/speed_switch_limit` | structured | `SpeedSwitchLimitFact` |
| `glossary.speed/speed_change_propagation` | structured | `SpeedChangePropagationFact` |

Seven distinct facts carry a `PRIMARY` provenance claim and `primary_spans_per_fact` is
`[1, 1, 1, 1, 1, 3, 3]` — five printed once, two printed three times and claimed `PRIMARY` by the
spans at every printing. Each is one fact claimed by every span that prints it, because the source
stated one rule; `validation.py:622-623` rejects a *span* with more than one primary owner, not a fact
with more than one primary span, so this is shared authority with exact provenance rather than a
duplicate. Five of those `PRIMARY` edges are component-scoped, over exactly three components
(`movement_modes`, `special_speeds` ×3, `movement_composition`), reported by span id in
`component_scoped_primary_spans`.

The schema extension is reported as what it is: seven new fact families
(`movement_composition`, `movement_depletion`, `special_speed`, `speed_change_propagation`,
`speed_definition`, `speed_selection`, `speed_switch_limit`), eleven new vocabularies, one accepted
vocabulary **widened** (`MovementMode` gains `jump`, witness clause `combat/3/0`), one optional field
added to an accepted family (`movement_allowance.window`), `accepted_families_changed` **empty**, and
two intrinsic invariants declared (`movement_depletion.until.at-least-one` and `…no-repeats`). The
one addition to an accepted family is optional and additive, and no existing field of an accepted
family changed — which is what `accepted_families_changed` being empty states, and why the prior
lifts rather than being rewritten.

## The blocker set moved **both ways**, and is asserted in both directions

`attitudes-1` closed three targets by accepting the complete source-defined Attitude class.
`areas-of-effect-1` closed none and added `glossary.cover`. `cover-1` closed that one and added none.
`speed-1` does both in one acceptance, and the total goes **up**.

| | |
|---|---|
| unresolved before | `glossary.concentration`, `glossary.speed` |
| resolved by this batch | `glossary.speed` |
| added by this batch | `glossary.burrow_speed`, `glossary.climb_speed`, `glossary.climbing`, `glossary.crawling`, `glossary.fly_speed`, `glossary.flying`, `glossary.jumping`, `glossary.swim_speed`, `glossary.swimming` |
| inherited residue, untouched | `glossary.concentration` |
| unresolved after | the nine above plus `glossary.concentration` — **ten** |

The arithmetic is pinned before the merge runs — `(before − resolved) | added == after` — and both
directions are asserted against the merged artifact afterwards, so a batch that resolved something it
did not claim to resolve fails just as loudly as one that failed to resolve something it did.

The citation this batch resolves is named exactly, not inferred from a count moving:
`resolving_citation` is `("action.dash", "", "srd-5.2.1/rules-glossary", "Speed")` — the reference
`actions-1` recorded because the source prints it in Dash. It now has a target, and it resolves
because a record arrived, not because a citation was rewritten. That resolution is a property of the
**combined** representation: neither the accepted prior alone nor this batch's draft alone exhibits
it.

The nine outgoing citations are **cited, not ingested**: no record, component, fact or span was
created for any of the nine glossary entries, and no target was invented. `Fly Speed` is the one split
reference — the source prints it at two clauses, `glossary/5/0` and `glossary/6/0`, so it carries two
provenance edges against one reference; the other eight carry one each, which is why
`reference/contextual` provenance is ten over nine references.

`validate_representation` returns exactly **ten** findings, and the script asserts **set equality on
target keys in both directions** against a pinned ten-element set rather than a count: a run showing
the set shrunk to one would mean the nine printed citations had been dropped, and a run showing
`glossary.concentration` gone would mean a prior citation had been rewritten. A blocker set that
emptied here would be fabricated closure.

```
reference srd-5.2.1/rules-glossary:'Concentration': unknown target record glossary.concentration
reference srd-5.2.1/rules-glossary:'Burrow Speed': unknown target record glossary.burrow_speed
reference srd-5.2.1/rules-glossary:'Climb Speed': unknown target record glossary.climb_speed
reference srd-5.2.1/rules-glossary:'Climbing': unknown target record glossary.climbing
reference srd-5.2.1/rules-glossary:'Crawling': unknown target record glossary.crawling
reference srd-5.2.1/rules-glossary:'Fly Speed': unknown target record glossary.fly_speed
reference srd-5.2.1/rules-glossary:'Flying': unknown target record glossary.flying
reference srd-5.2.1/rules-glossary:'Jumping': unknown target record glossary.jumping
reference srd-5.2.1/rules-glossary:'Swim Speed': unknown target record glossary.swim_speed
reference srd-5.2.1/rules-glossary:'Swimming': unknown target record glossary.swimming
```

`still_blocked` is `true`. Concentration and the nine movement entries remain explicit unresolved
targets, no target was invented for any of them, and no batch for any of them is begun here.

## Reproduction

From the repository root, on this branch, with no private files and no network:

```bash
python .claude/review-notes/issue-5d-batch-speed-1-ACCEPT.py --verify
pytest -q --no-cov tests/ingestion/mechanical/
```

`--verify` reads only tracked repository inputs, rebuilds the complete merged artifact in memory from
the frozen six-batch prior, the retained proposal and the pinned source manifest, and compares it to
the committed file byte for byte. It ends with
`reconstructed_artifact_byte_identical_to_committed: true`,
`accepted_artifact_matches_pinned_merged_identity: true` and
`frozen_six_batch_prior_untouched: true`. It **writes nothing**, and exits 0.

The default mode still refuses a stale rerun, and refuses it first: with the acceptance in place the
live artifact's pinned prior digest no longer matches `PRIOR_CONTENT_SHA256`, so the run stops before
the generator executes and before anything is written. That guard was not re-exercised after the
acceptance and no refusal capture is presented for it; what is presented is the guard itself and the
`--verify` mode that does not need it.

The stdout of the acceptance run and of `--verify` are retained untracked as
`.claude/review-notes/_speed1_accept_run.json` and `_speed1_verify_run.json` (with `_speed1_verify_run.err`
empty). The acceptance run's stdout is not pure JSON because the script executes the generator through
`runpy` first. Those captures are untracked scratch, following the `cover-1` precedent; the
**committed, replayable** evidence is `--verify`.

## Which committed checks changed, and why each had to

None was weakened or deleted. Every one below asserted something true of the six-batch artifact and
now asserts the same property of the seven-batch one.

| Module | What moved |
|---|---|
| `test_committed_accepted_authority.py` | seventh batch id and proposal identity; oracle identity, content digest, blob, projection uuid and payload hash re-pinned; `SPEED` count dict added and `MERGED` re-summed; seventh anchor, the `10-to-11` lift and the seventh `accepted_at` added to their lists; the record-key partition gained `glossary.speed`; one test name widened from *six* to *seven* |
| `test_committed_accepted_authority.py::test_accepted_authority_is_lifted_rather_than_restamped` | restored to its *declares-current-authority* form, as the `cover-1` acceptance restored it before schema 11 superseded it. The artifact now declares schema 11, which this build implements, so `validate_schema_binding` returns `()`, `records == ()` and `lifted is inputs`. This is the stronger assertion, not a weaker one |
| `test_committed_accepted_authority.py::test_the_unresolved_cross_batch_citations_are_exactly_these_ten` | **new**. Ten is now read off committed authority — the dangling targets of the artifact's own references — rather than computed as arithmetic over two sets, and the resolved `action.dash` → `glossary.speed` citation is asserted by name |
| `test_speed_1_frozen_prior.py` | `test_the_committed_artifact_is_still_this_copy_byte_for_byte` → `test_the_committed_artifact_extends_this_copy_by_exactly_one_batch`, the replacement that module's own docstring promised when it was written |
| `test_cover_1_frozen_prior.py` · `test_attitudes_1_frozen_prior.py` · `test_areas_of_effect_1_frozen_prior.py` | their extends-by-**one** claims generalized to extends-by-**the-batches-since**, following the `attitudes-1` precedent rather than being re-pinned to a single batch name |
| `test_cover_1_acceptance_reproduction.py` | its comparison target retargeted from the live artifact to the frozen six-batch fixture, which **is** the bytes that acceptance wrote (blob `b7c01494…`). All four tests keep their force; the attachment between fixture and live artifact is what `test_speed_1_frozen_prior` now proves |
| `test_speed_1_acceptance_reproduction.py` | **new**, following the `cover-1` module clause for clause: a second independent rebuild of this merge, a proof the two scope orders differ, the discrimination test, and the out-of-scope refusal |
| `test_accepted_inputs.py` | batch-id and anchor-order lists; the 47/558 sentence → 48/594 |
| `test_production_release.py` | 47 → 48 records, 558 → 594 spans, and the record breakdown corrected to name Cover **and Speed** as glossary rules that define no list |
| `test_schema_6_succession.py` | `COMMITTED_CONTENT_SHA256` re-pinned. The frozen two-batch copy's own `ACCEPTED_ORACLE_IDENTITY` is untouched — the sentinel exists to be able to fail for one and pass for the other |

## Acceptance status reconciled at every site

| Site | What it now says |
|---|---|
| `docs/architecture/known_unknowns.md` §5d | seven batches, 48 records / 594 spans, **ten** remaining unresolved targets named individually, and that this batch closed one while opening nine. The schema-11 paragraph's "still two" clause is marked expired in place rather than rewritten |
| `docs/decisions/adr-005d-…md` | a dated historical block beneath the schema-11 amendment and its correction. Those paragraphs are **kept as written** — they record the state at registration and at the proposal — and the block records what the acceptance changed and what it did not |
| `src/afterworlds/ingestion/mechanical/oracle.py` module docstring | seven batches, 48 records / 594 spans |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | seven batches; records the schema-10→11 crossing as a lift; names all ten unresolved targets and states that the residue moved **both ways at once** |
| `src/afterworlds/ingestion/mechanical/publication.py` | seven batches, 48 records over 594 spans |
| `pyproject.toml` package-data comment · `MANIFEST.in` | seven batches |
| `issue-5d-speed-1-DISCOVERY-CHECKPOINT.md` | a superseded banner beneath its existing status line. Every status line beneath it is preserved: they are the evidence of what was put in front of the Owner, in the order it was put there |

## Gates

Run on the working tree that became this commit. The only files changed after the full suite were
`.secrets.baseline` and this section; no test reads either, which was checked rather than assumed
(`grep -rl 'secrets.baseline\|ACCEPTANCE-CHECKPOINT' tests/` matches two docstring mentions and no
read). The staged diff the suite ran against hashes to
`22553c2c0d15a6b5d8fb189a6a6864f7931d2bc7c050867f2133fe90f5b14d39`, with no unstaged tracked changes.

| Gate | Result |
|---|---|
| `black --check src/ tests/` | 473 files would be left unchanged |
| `ruff check src/ tests/` | All checks passed |
| `mypy src/` | Success: no issues found in 225 source files |
| detect-secrets, invoked as `.pre-commit-config.yaml` configures it (`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>`) | exit 0 |
| `pytest -q` (full suite, coverage enforced) | **5784 passed, 10 skipped, 241 warnings in 1178.24s**, total coverage 94.21% against the 80% floor, exit 0 |
| `pip-audit` | **exit 1** — see below |
| `issue-5d-batch-speed-1-ACCEPT.py --verify` | exit 0, stderr empty (0 bytes), report retained at `_speed1_verify_final.json` |

**Who ran the suite, and why that is stated here.** Two CLI-owned full-suite runs were launched in
this session and both were killed on turn exit — the first stopped at 3% of collection, the second at
6%, and neither produced a result. Those runs are **not** evidence of anything and no pass is claimed
for them. The result in the table above was produced by an independent Codex-executed
`pytest -q` over the same staged tree, retained at
`~/.codex/visualizations/2026/09/05/01a07071-8e0c-7502-b149-77574cc34096/speed-1-codex-full-suite.txt`.
The identity of the tree is what ties the two together: the staged diff hash above is the tree that
run measured. Every other gate in the table was executed in this session and attached to its own
call.

**Formatting and lint reached three docstrings, not the acceptance.** `ruff` flagged three E501s
introduced by this batch's docstring retargets — in `publication.py`, `test_committed_accepted_authority.py`
and `test_production_release.py` — each a line that grew past 88 columns when "six batches / 47
records / 558 spans" became "seven batches / 48 records / 594 spans". All three were rewrapped; no
assertion, pin or count was changed to satisfy a linter.

**`.claude/review-notes/` is outside the gate paths.** `black src/ tests/` and
`ruff check src/ tests/` do not reach it, so `issue-5d-batch-speed-1-ACCEPT.py` and the checkpoints
beside it are neither formatted nor linted by those gates, and `pytest` never collects from there
(`testpaths = ["tests"]`). This is the existing repository disposition and this batch does not change
it.

**The baseline grew by the additive splice, not by a rewrite.** The oracle JSON gained 36 spans, so
its 64-hex literals moved and new ones appeared, and a JSON artifact cannot carry an inline
`pragma: allowlist secret`. `_speed1_baseline_splice_accept.py` scanned that one file into a **copy**
of the baseline and took only `results[<oracle path>]` from the copy: 123 → 139 entries with none
dropped. `version`, `plugins_used`, `filters_used`, `generated_at`, the set and order of file blocks,
and every other file's block were each asserted byte-identical to `HEAD:.secrets.baseline` before the
write. `git diff .secrets.baseline` touches one `filename`. The baseline was not grown to silence a
hit anywhere else: the four 64-hex pins in the ACCEPT script carry inline pragmas, because it is
Python and can.

**`pip-audit` is nonzero, and is reported as an environment advisory finding.** It reports 29 known
vulnerabilities across 10 installed packages — `chromadb`, `click`, `cryptography`, `idna`, `mako`,
`msgpack`, `pip`, `pydantic-settings`, `setuptools` and `urllib3`. This branch changes no dependency
declaration: the only `pyproject.toml` edit is a comment inside the `package-data` block. An
unchanged dependency file does not by itself establish when an advisory first appeared, so no
chronology is claimed. Dependency maintenance is out of scope for this batch and was not performed;
nothing was suppressed and no audit ignore was added.

## Architecture Notes

`No drift from design principles`, with three disclosures that are properties of the accepted content
rather than deviations from the contract:

1. **The publication blocker set grew, from two to ten.** That is a consequence of representing what
   the source prints — the Speed entry names nine other glossary entries — not evidence of a defect,
   and it is the first batch in the series to move the residue in both directions at once. The nine
   are cited, not ingested. Growth is not a reason to withhold a batch any more than narrowing was a
   reason to accept one; both are consequences of accepting complete source classes.
2. **The resolved Dash-to-Speed citation is a property of the combined representation.** Neither the
   accepted prior nor this batch's draft exhibits it alone: the prior cites a record it cannot
   resolve, the draft defines a record nothing in it cites. Ten is asserted against the merged
   artifact rather than derived, which is why the new committed test reads it off the artifact.
3. **Seven distinct facts carry `PRIMARY` provenance and two of them carry three such claims each.**
   Each doubly- or triply-printed rule is one fact claimed by every span that prints it. That is
   ADR-005d Decision 3's many-to-many provenance used as intended, not a duplicate the validator
   failed to catch — `validation.py:622-623` constrains spans, not facts.

No parameter value, unit, coordinate or grid semantic is invented anywhere. `DistanceUnit.FOOT` is
the unit the source prints; no number of feet, no square, no segment and no corner rule is
represented. Speed declaratively records what the source prints; it does not measure geometry, plan a
route, execute a move or change adapter ownership. Runtime movement, grid simulation, adapter
execution and downstream adjudication stay outside, where ADR-005d Decision 11 and #137's Out of
scope leave them. No table, settled classification, rules engine or downstream adapter ownership is
reopened.

## Stop conditions honoured

Accepting is not publishing. This change **published, activated and retired nothing**; the release
still resolves to a committed oracle and still refuses as `INCOMPLETE`, and the runtime binding still
reports `UNPUBLISHED`. This is a **seventh accepted batch and not full-corpus completion** — the
full-corpus work ADR-005d Decision 5 requires remains undischarged. No seven-batch frozen prior
fixture was created and the six-batch one is untouched. No further batch, no runtime movement
geometry, no unrelated batch and no dependency maintenance was begun. Parent tracking issue #137
remains in progress, its state unchanged, and the Owner merges.
