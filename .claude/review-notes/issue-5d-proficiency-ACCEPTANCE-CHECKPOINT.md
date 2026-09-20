# CRD Issue 5d — `proficiency-destinations-1` and `proficiency-1` accepted

**Owner Decision, 2026-09-20 (UTC) / 2026-09-19 (local).** Ravenlok authorized the formal acceptance
of the two independently reviewed Proficiency batches — the exact full proposals, destinations before
Proficiency, with full explicit span scopes and review-unit scopes, not derived from persisted
candidate output. That authorization superseded the standing prohibition on accepting either batch and
on updating the committed accepted authority. It authorized nothing else: **no publication,
activation, retirement, or merge**, no additional source ingestion, no generic supersession, no
resolved-target retargeting, and no movement / 15c / downstream adapter / sheet-execution work. Parent
tracking issue #137 remains in progress.

Performed through the repository's real `accept_proposal` path — two calls, in the authorized order,
the second taking the first's result as `prior`. Every claim below is executed by
`.claude/review-notes/issue-5d-batch-proficiency-destinations-1-and-proficiency-1-ACCEPT.py`, which is
retained. **The Owner made the decision; the script executed the recorded action and reviewed
nothing.** The independent review was a Codex lifecycle-and-exact-artifact review of the reviewed
head that returned a ready verdict; it is named in the recorded rule prose rather than cited as a
repository file, because it is not one and the script does not read it.

| | |
|---|---|
| Batches | `proficiency-destinations-1`, then `proficiency-1` |
| Reviewer (accepting) | Ravenlok (Owner) |
| Accepted at | `2026-09-20T02:50:55Z` (120 destination records) and `2026-09-20T02:50:58Z` (47 Proficiency records) — one timestamp per batch |
| Proposal identities | `723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e` · `f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a` |
| Proposal content SHA-256 | `6a88c886…f035fe1d` · `c4c12fd3…ace85d5d` — the two digests the authorization names, asserted before the merge |
| Proposal Git blob / bytes | `871bda15…2d91` / 139,405 · `ea7e515c…04b7` / 61,375 — unchanged by the acceptance |
| Reviewed head | `88d4ec6d7456c5bf3ec43ed974cf6ad2af13d7b0` |
| Schema | `5d-representation-schema-15` / `e87e0bacdc476b0bef092a04cbedd933e0b57b128651b08ef0ffbd0c94d186fd` |
| Semantic policy | `5d-semantic-policy-2` / `da63b8940c5b3997b44d53e02941389b68e2a2ba35250e73194d38bb1d74cde7` |
| Scope | 167 spans total — 120 + 47 · 5 records · 105 substantive / 61 supporting / **0** unresolved / **1** non-mechanical |
| Review units discharged | 5 — four by the destinations batch, one by `proficiency-1` |
| Accepted oracle identity | `3b8941ce9039a78e72fd3ddf05952d0da4bed18dc4d38fb99b8b80db137fb407` |
| Accepted artifact content SHA-256 | `995976ac1c2b0227d419fc4a7b65a966358e311c7806a1a8f0457a535b4300d7` |
| Accepted artifact Git blob / bytes | `ec645c7e89a126b6ec4778247460449f04da5deb` / 1,083,169 |
| Projection UUID / payload hash | `82c75aad-b294-5b2e-a188-128cdcbada09` / `76f1507bd4b5459219b7d2cfd385e52c304349dc3e2fa1b292379acf7464e080` |

The oracle identity, the proposal identities and the projection identity are four different things and
are reported as four. `723bba62…` and `f0becb8b…` are the content-derived identities of the
*proposals*; `3b8941ce…` is the identity of *accepted authority* after both merges; `82c75aad-…` is
the identity of the projection the accepted artifact derives.

Every SHA-256 here is a **canonical-LF content digest**, so verification fails on an edited artifact
and never on a checkout's line endings.

## The accepted timestamps are observed, and the write is recorded beside them

`DEST_ACCEPTED_AT` and `PROF_ACCEPTED_AT` are pinned constants, not `datetime.now()`. A wall-clock read
at replay would put new values into the artifact on every run, so the file digest above could never be
reproduced and the "reproduces exactly from retained repository inputs" claim would be false by
construction. Both values are UTC clock reads taken in the same shell session that ran the acceptance,
before the run, three seconds apart and in the acceptance order they are used in, each truncated — not
rounded — to the second. The script carries that basis verbatim in `ACCEPTED_AT_BASIS`.

The local date of that session is **2026-09-19** and the local clock reads were **19:50:55** and
**19:50:58**; the UTC instants are **2026-09-20T02:50:55Z** and **2026-09-20T02:50:58Z**. The two
differ because the workstation runs seven hours behind UTC. Both are stated here rather than one being
passed off as the other. These are the **first acceptances in this corpus whose local and UTC calendar
dates differ**, which is why every document that records them says which of the two it means.

The timestamps are the moments the acceptance actions were *initiated*, not the moment the bytes
landed. The observed write is the accepted artifact's filesystem modification time,
**2026-09-20T02:52:36Z**, reported as a filesystem observation rather than as an instrumented
timestamp. The roughly ninety seconds between the second clock read and the write are not the script's
runtime and are not presented as it.

### A first run was performed and reverted, and is recorded rather than omitted

An earlier pair of reads, **2026-09-20T02:32:04Z** and **02:32:07Z**, timed a first run of this script
that completed and wrote the artifact. It was **reverted**.

The reason was a false sentence in the evidence, not a wrong number. The destination batch's `rule`
prose claimed that thirteen of the seventeen references the destinations batch carries "resolve within
this acceptance to records it mints". That is not where any of them resolve: **twelve** resolve
*backward* to `actions-1` records already in the frozen prior — `action.attack`, `.dash`, `.disengage`,
`.dodge`, `.help`, `.hide`, `.influence`, `.magic`, `.ready`, `.search`, `.study`, `.utilize` — **one**
resolves *forward* to `play.proficiency`, which `proficiency-1` mints next, and **four** carry no
target at all. Rule prose is baked into accepted bytes and cannot be corrected without reverting an
acceptance, so the artifact was restored with `git checkout --` before anything was committed, both
rules were reworded to state where the references actually resolve, a new assertion was added that the
intermediate state carries exactly one obligation more than the finished one, fresh clock reads were
taken, and the run that stands was performed.

The reverted run produced content SHA-256 `8a06c801…`, Git blob `c5331a21…` and 1,082,070 bytes. Those
values are **stale and must not be reused**. The oracle identity was unaffected by the reword — rule
prose is evidence, not identity — which is exactly why the content digest and blob are pinned beside
it and why only they moved.

## Two modes, and what may be run again

| Mode | Prior read | Purpose |
|---|---|---|
| default | the **live** committed artifact | performs the acceptance; a stale rerun fails early rather than double-merging |
| `--probe` | the live artifact, pre-acceptance | computes and prints the pins without writing; only meaningful before the acceptance, and no longer runnable to that end |
| `--verify` | the **frozen seven-batch fixture** | rebuilds both merges in memory from repository inputs and compares to the committed result **byte for byte**; writes nothing |

The default mode ran **twice in total** — once for the reverted run and once for the run that stands —
and **must not be run in acceptance mode again**. `--verify` is the replay path.

```
$ python .claude/review-notes/issue-5d-batch-proficiency-destinations-1-and-proficiency-1-ACCEPT.py --verify
verified proficiency-destinations-1 then proficiency-1: 9 batches, 761 spans, 5 review units,
oracle 3b8941ce9039..., blob ec645c7e89a1..., 14 reference obligations remain.
$ echo $?
0
$ git hash-object src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json
ec645c7e89a126b6ec4778247460449f04da5deb
```

## Merged result

| | prior (7 batches) | after both | delta |
|---|---|---|---|
| batches | 7 | **9** | +2 |
| spans | 594 | **761** | +167 |
| records | 48 | **53** | +5 |
| components | 145 | **177** | +32 |
| facts | 190 | **210** | +20 |
| prose bindings | 49 | **142** | +93 |
| relationships | 0 | **0** | 0 |
| references | 62 | **83** | +21 |
| provenance | 627 | **828** | +201 |
| obligations | 48 | **53** | +5 |
| review units | 0 | **5** | +5 |
| review-unit acceptances | 0 | **5** | +5 |
| schema anchors | 7 | **9** | +2 |
| registered lifts | 8 | **12** | +4 |
| policy transitions | 0 | **1** | +1 |
| reference resolutions | 0 | **0** | 0 |

The five new records are `play.actions`, `play.skills`, `glossary.challenge_rating` and
`glossary.expertise` — the four reviewed destinations — plus `play.proficiency`. None opens a typed
record family.

Schema succession: the eight crossings already recorded, plus `5d-lift-schema-11-to-12` → `12-to-13`
→ `13-to-14` → `14-to-15`. Policy succession: one crossing, `5d-policy-1-to-2`, from
`5d-semantic-policy-1` to `5d-semantic-policy-2`. The prior was **lifted, never restamped**, and every
earlier anchor stays where its batch was reviewed: `conditions-1` at schema 3, `hazards-1` at 5,
`actions-1` at 7, `attitudes-1` at 8, `areas-of-effect-1` at 9, `cover-1` at 10, `speed-1` at 11.

For the first time since `conditions-1`, the committed artifact declares **current** authority:
schema 15 is the schema this build implements, so `validate_schema_binding` over the committed
candidate returns `()` and no lift stands between the file and current authority.

## The four Proficiency links resolve; the residue moved by exactly four empties

All four references `proficiency-1` prints resolve **uniquely** against the destinations batch
accepted immediately before it. That is why the two were authorized in that order and accepted in it,
and the intermediate state is the proof rather than the claim: after the destinations merge and before
the Proficiency merge the artifact reports **15** outward reference obligations, the fifteenth being

```
reference srd-5.2.1/playing-the-game:'Proficiency': unknown target record play.proficiency
```

and the second merge closes exactly that one, leaving **14**. The ACCEPT script asserts this in code,
and `test_proficiency_acceptance_reproduction` asserts it in CI.

### The ten named-but-unminted targets are unchanged

`glossary.burrow_speed`, `glossary.climb_speed`, `glossary.climbing`, `glossary.concentration`,
`glossary.crawling`, `glossary.fly_speed`, `glossary.flying`, `glossary.jumping`,
`glossary.swim_speed`, `glossary.swimming`. The Proficiency batches closed none of them and opened
none. Each closes the moment some batch mints the record, with no decision and no key change.

### The four empty-target citations, and that no resolution was invoked

| scope | citation | target |
|---|---|---|
| `srd-5.2.1/rules-glossary` | *Stat Block* | *(empty)* |
| `srd-5.2.1/gameplay-toolbox` | *Combat Encounters* | *(empty)* |
| `srd-5.2.1/playing-the-game` | *Combat* | *(empty)* |
| `srd-5.2.1/playing-the-game` | *Opportunity Attack* | *(empty)* |

Review read each citation the source plainly makes and could state no destination key. **No
destination was ingested for any of them and no target was invented.** These four **must remain
unresolved**: `reference_resolutions` is empty in the committed artifact, so no reviewed reference
resolution was invoked for any of the fourteen obligations. They close only through an explicit
reviewed resolution under ADR-005d Decision 7 as amended, never by a later batch minting a plausible
target — a reference's key includes its target, so a later authored destination states a *different*
key and the accepted empty edge would survive beside it.

### The fourteen reported obligations, verbatim

```
reference srd-5.2.1/gameplay-toolbox:'Combat Encounters': unresolved reference
reference srd-5.2.1/playing-the-game:'Combat': unresolved reference
reference srd-5.2.1/playing-the-game:'Opportunity Attack': unresolved reference
reference srd-5.2.1/rules-glossary:'Burrow Speed': unknown target record glossary.burrow_speed
reference srd-5.2.1/rules-glossary:'Climb Speed': unknown target record glossary.climb_speed
reference srd-5.2.1/rules-glossary:'Climbing': unknown target record glossary.climbing
reference srd-5.2.1/rules-glossary:'Concentration': unknown target record glossary.concentration
reference srd-5.2.1/rules-glossary:'Crawling': unknown target record glossary.crawling
reference srd-5.2.1/rules-glossary:'Fly Speed': unknown target record glossary.fly_speed
reference srd-5.2.1/rules-glossary:'Flying': unknown target record glossary.flying
reference srd-5.2.1/rules-glossary:'Jumping': unknown target record glossary.jumping
reference srd-5.2.1/rules-glossary:'Stat Block': unresolved reference
reference srd-5.2.1/rules-glossary:'Swim Speed': unknown target record glossary.swim_speed
reference srd-5.2.1/rules-glossary:'Swimming': unknown target record glossary.swimming
```

## The original seven acceptances are preserved

The pre-acceptance artifact was copied byte-for-byte to
`tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1_areas_of_effect_1_cover_1_speed_1.json`
before the acceptance ran — 785,687 bytes, canonical-LF SHA-256
`eed7df0476445fc6e5d1d9cd6bdd67977f72372bc67b01808eaa240b69a7e619`, Git blob
`4fcfab6f667923acbaa98345b56a405061287643`, oracle identity
`d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f`. It is the
`--verify` prior and the CI fixture for five properties.

`test_proficiency_acceptance_reproduction::test_the_seven_earlier_acceptances_are_carried_in_unchanged`
compares the live artifact against it element by element — every batch, acceptance record and span
keyed by id, and the anchors and lifts by position, so `speed-1` must still be the seventh anchor.
Nothing in the seven earlier acceptances moved.

## Reproduction

`--verify` rebuilds both merges from tracked repository inputs alone — the two committed proposals, the
frozen seven-batch prior and the `afterworlds` package — and compares the result to the committed
artifact byte for byte. Nothing is read from a private workstation path, so the reproduction runs in
any checkout.

`tests/ingestion/mechanical/test_proficiency_acceptance_reproduction.py` is the CI half of that claim
and is **deliberately independent of the ACCEPT script**: it imports nothing from it, re-derives both
scopes from the proposal JSON, and calls `accept_proposal` twice on its own. Two independent paths
arriving at the same bytes is evidence; one shared helper agreeing with itself is not. Unlike the five
earlier batches there is no source manifest here — the Owner authorized explicit span scopes "not
derived from persisted candidate output", and the explicit scopes are the reviewed proposals' own
order — so there is no second scope order to discriminate against. That property stays covered once,
over `cover-1` and `areas-of-effect-1`, and is not restated.

## Which committed checks changed, and why each had to

| Module | Why |
|---|---|
| `test_committed_accepted_authority` | the nine-batch artifact: batch/anchor/lift/stamp lists, the five moved pins, the `non_mechanical` column, the policy transition and review-unit records, and the empty-target half of the residue |
| `test_proficiency_acceptance_reproduction` | **new** — byte reproduction, the seven preserved acceptances, and the intermediate 15-obligation state |
| `test_proficiency_destinations_1_proposal`, `test_proficiency_1_proposal` | `test_nothing_in_this_proposal_is_accepted` inverted into `test_the_accepted_batch_names_exactly_this_proposal`; rehearsal priors repointed to the frozen prior |
| `test_proficiency_references_resolve` | rehearsal now starts from the frozen prior, and the rehearsal and the accepted artifact are asserted to report the same thing |
| `test_policy_versioning` | the first accepted policy crossing, asserted on the live artifact |
| `test_speed_1_frozen_prior`, `test_cover_1_frozen_prior`, `test_attitudes_1_frozen_prior`, `test_areas_of_effect_1_frozen_prior` | each extends its frozen copy by the batches since, which is now two more |
| `test_speed_1_acceptance_reproduction` | its comparison target is the frozen seven-batch fixture, not the live file, which has moved on by two batches |
| `test_accepted_inputs`, `test_retained_proposals`, `test_schema_6_succession`, `test_reference_resolution` | batch/anchor/proposal lists and the committed content and oracle pins |
| `test_schema_14_proficiency_inputs` | the pre-widening authority specimen is now the frozen prior |
| `test_production_release` | 53 records over 761 spans, still `INCOMPLETE`, now `POPULATION_MISMATCH` rather than `POLICY_MISMATCH` |

## Acceptance status reconciled at every site

| Site | Change |
|---|---|
| both `REVIEW-PACKET.md` status lines | `PROPOSED. Not accepted.` → accepted 2026-09-20 UTC, with the packets' own claims left as the reviewer read them |
| `oracles/README.md` | nine batches, 53 records over 761 spans, the two new acceptances and the policy crossing, and the four empty citations beside the ten |
| `oracle.py` `review_unit_acceptances` docstring | "Empty for all seven accepted batches" was true when written and is not now |
| `adr-005d-…md` | appended a superseding historical note in the `speed-1` format; the schema-14/15 paragraph's "No semantic acceptance was granted" is kept as written and marked superseded |
| `docs/architecture/known_unknowns.md` | appended a correction: nine batches, the moved counts, and the expiry of "**None is accepted today**" for the empty-target kind |

Nothing in the historical records was rewritten. Both are append-and-mark, which is the pattern every
earlier acceptance in this issue used.

## Gates

Run on the working tree that became this commit. The only file changed after the full suite is this
checkpoint — these two sections — and no test reads it, which was checked rather than assumed
(`grep -rn` over the three reproduction modules matches three docstring mentions and no read).
`.secrets.baseline` was spliced and staged **before** the suite ran, not after. The staged diff the
suite ran against hashes to
`4b242ed2201b099bc23b0801e9f955bf769b0c41db0f95f4f9a18c41594d2523`.

| Gate | Result |
|---|---|
| `black src/ tests/` | 2 files reformatted (the two proposal modules' inverted tests), 484 unchanged; `--check` clean afterwards |
| `ruff check src/ tests/` | All checks passed |
| `mypy src/` | Success: no issues found in 226 source files |
| detect-secrets, invoked as `.pre-commit-config.yaml` configures it (`python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline <staged files>`) | exit 1 before the splice, **exit 0** after |
| `pytest tests/ingestion -q -p no:randomly` | **3436 passed**, 2 warnings, 912.11s, exit 0 |
| `pytest tests --ignore=tests/ingestion -q -p no:randomly --cov-append` | **2776 passed, 10 skipped**, 246 warnings, 351.88s, **total coverage 94.36%** against the 80% floor, exit 0 |
| `pip-audit` | **exit 1** — see below |
| `…-and-proficiency-1-ACCEPT.py --verify` | exit 0 |

The suite is split because `pytest-xdist` and `pytest-timeout` are not installed and the ingestion
tree alone runs for a quarter of an hour; `--cov-append` makes the two halves one coverage figure, and
the 94.36% above is that combined figure. **6212 tests passed and none failed.** Both halves were run
attached in this session.

**The baseline grew by the additive splice, not by a rewrite.** Two JSON files fired, and neither can
carry an inline `pragma: allowlist secret`: the artifact gained 167 spans, so its registered 64-hex
identity literals moved (a rescan, 24 hits), and the frozen seven-batch prior is newly tracked, so its
literals are new keys (a registration, 139 hits). `_p172_baseline_splice_accept.py` scanned both files
into a **copy** of the baseline — a bare `detect-secrets scan --baseline` against the real file drops
every other file's entries — and took only those two blocks from the copy. `version`, `plugins_used`,
`filters_used`, `generated_at`, and every other file's block were each asserted identical before the
write, the real baseline was asserted not to have moved during the scan, and every hash the artifact
already carried was asserted to survive. `git diff .secrets.baseline` touches exactly those two
`filename` keys. The baseline was **not** grown to silence a hit anywhere else: the 64-hex pins in the
ACCEPT script and in the new test module carry inline pragmas, because Python can.

**`.claude/review-notes/` is outside the gate paths.** `black src/ tests/` and `ruff check src/ tests/`
do not reach it, so the ACCEPT script and the checkpoints beside it are neither formatted nor linted
by those gates, and `pytest` never collects from there (`testpaths = ["tests"]`). detect-secrets does
scan it. This is the existing repository disposition and this batch does not change it.

**`pip-audit` is nonzero, and is reported as an environment advisory finding.** It reports 24 known
vulnerabilities across 10 installed packages — `anyio`, `chromadb`, `cryptography`, `idna`, `mako`,
`msgpack`, `pip`, `pydantic-settings`, `pytest` and `urllib3`. This branch changes no dependency
declaration: the only `pyproject.toml` edit is a comment inside the `package-data` block naming the
accepted batches. The local failure and the configured clean CI audit are **distinct evidence, not
permission to change dependencies**; dependency maintenance is out of scope here and was not
performed, nothing was suppressed, and no audit ignore was added.

## Architecture Notes

`No drift from design principles`, with three disclosures that are properties of the accepted content
rather than deviations from the contract:

1. **The committed artifact declares current authority for the first time since `conditions-1`.** It
   is accepted at schema 15, which is the schema this build implements, so the "committed authority is
   one or more lifts behind the build" property that every earlier acceptance exhibited is no longer
   true of the live file. The property has not been deleted: it now reads the frozen seven-batch
   prior, which still needs four crossings, beside the legacy schema-3 specimen. `crossings_from` over
   schema 15 raises, and is never called.
2. **This is the first acceptance to cross a semantic policy and the first to record a review
   inventory.** One `5d-policy-1-to-2` transition and five review-unit acceptances — four discharged
   by the destinations batch, one by `proficiency-1` — are accepted content, not new machinery; both
   seams already existed and were empty. `oracle.py`'s docstring saying the field is empty for all
   accepted batches was true when written and is corrected rather than reinterpreted.
3. **The reference residue moved in both directions and is asserted in both.** Twelve of the
   destinations batch's seventeen citations resolve *backward* into `actions-1`, one resolves
   *forward* into a record `proficiency-1` mints next, and four name no target at all. The obligation
   count therefore goes 10 → 15 → 14 across the two merges, and the intermediate 15 is asserted rather
   than described: it is the only evidence that the four Proficiency links resolve because of the
   destinations batch and not in spite of it.

No target was invented for the four empty-target citations and no destination was ingested for them;
`reference_resolutions` is empty, so no reviewed resolution was invoked for any of the fourteen
obligations. The accepted content declaratively records what the source prints. Nothing adjudicates a
check, computes a bonus, applies proficiency to a roll or touches sheet execution — runtime
adjudication and downstream adapters stay where ADR-005d Decision 11 and #137's Out of scope leave
them. No table, settled classification or downstream ownership is reopened.

## Stop conditions honoured

Nothing was published, activated, retired or merged, and PR #172 stays a draft. No additional source
was ingested and no destination was authored for the four empty citations. No reference resolution was
invoked for any real citation. No generic supersession was built and no resolved target was
retargeted. No 5c edit, no accepted-Action uniformity rewrite, no movement / 15c / downstream adapter /
sheet-execution work, no progress accounting. No dependency, audit-exclusion or Python-environment
change — the local `pip-audit` failure and the configured clean CI audit remain distinct evidence, not
permission to change dependencies. The four stashes and all untracked scratch are intact and
uncommitted; no `git gc`, `prune` or `reflog expire` was run. No old ACCEPT script was re-run in
acceptance mode, and this one will not be either.
