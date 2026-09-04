# CRD Issue 5d — `hazards-1` accepted

**Owner Decision, 2026-09-03.** Ravenlok accepts `hazards-1` exactly as represented in proposal
`f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417`.

Performed through the repository's real `accept_proposal` path. Nothing is published, activated, or
retired; the branch is not merged; `actions-1` is not begun. Every claim below is executed by
`.claude/review-notes/issue-5d-hazards-1-ACCEPT.py`, which is retained.

**`--verify` re-checks the committed artifact against the frozen prior**, without attempting the
one-time action again. The prior it compares against is
`tests/ingestion/mechanical/data/legacy_conditions_1_unanchored_schema3.json`, asserted at content
SHA-256 `ead1458e…8d81ce` and Git blob `42faeca2…de87` — not the merged file, which would make every
preservation comparison compare the artifact to itself. The comparisons are element-wise and real in
both modes: the conditions-1 batch record, all 185 acceptance records, all 185 spans, every prior
element of each of the six representation collections, and every prior obligation, each reported as
its own Boolean with a count of missing elements beside it. It also asserts the merged artifact
against three pinned identities — **canonical-LF content** SHA-256 `0925d796…73f7`, Git blob
`6e65533f…b59a`, oracle identity `c794bde4…356245` — so an unreviewed edit to the acceptance
**evidence**, which the oracle identity deliberately does not cover, fails there too. All three are
properties of the content, so verification fails on an edited artifact and never on a checkout's line
endings.

**Every SHA-256 in this checkpoint is a canonical-LF content digest**, and every one that decides
anything is checkout-independent. A second corrected claim, recorded rather than replaced: until
2026-09-04 the proposal and merged-artifact assertions in `ACCEPT.py` compared the **raw on-disk**
digest against those canonical pins (`PROPOSAL_SHA256`, `MERGED_SHA256`), and the final
`accepted_artifact_matches_pinned_merged_identity` Boolean carried the raw digest as one of its
terms. On a CRLF checkout that fails for byte-identical JSON — verification would exit before its
acceptance checks and report the checkout as an unreviewed edit. The pins are now named
`PROPOSAL_CONTENT_SHA256` / `MERGED_CONTENT_SHA256`, the assertions read the canonical digest, and
raw digests survive only as `..._raw_sha256_diagnostic` fields in the report, which decide nothing.
The compatibility case was executed, not argued: `--verify` was run in a disposable worktree whose
proposal and accepted JSON had been converted to CRLF, and it passed with the raw digests moved and
the canonical digests and Git blobs unchanged. `test_the_pinned_identities_survive_a_crlf_checkout_and_the_raw_digest_does_not`
keeps that property from regressing. Neither the CRLF worktree nor its files are committed.

A corrected earlier claim, recorded rather than replaced: until 2026-09-03 this section said
`--verify` re-checked *every* post-acceptance assertion. It did not. Its preservation entry was a
dictionary holding one explanatory string, and `all()` over that is `True` for no reason — so the
check reported success while comparing nothing, and it read the merged file as the prior, reporting
`0925d796…73f7` under a "prior" label. Both are closed above.

| | |
|---|---|
| Batch | `hazards-1` |
| Reviewer | Ravenlok (Owner) |
| Accepted at | `2026-09-03T10:58:59Z` — one timestamp across all 96 records |
| Proposal identity | `f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417` |
| Proposal payload hash | identical to the identity, asserted |
| Proposal content SHA-256 / Git blob | `6d0e0566…753f` / `3018bce5…ee3b` — unchanged by the acceptance |
| Schema | `5d-representation-schema-5` / `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` |
| Scope | 96 spans · 43 leaves · 6 records · 65 substantive / 31 supporting / **0** unresolved / **0** non-mechanical |
| Accepted oracle identity | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` |
| Accepted artifact content SHA-256 | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` |
| Accepted artifact Git blob | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` |

## How the proposal was supplied

Not hand-converted, not renamed, not reproduced. The reviewed `MechanicalProposal` is rebuilt by
**executing the reviewed generator**, and the run asserts its identity, its payload hash, that its
payload equals the committed proposal JSON byte for byte, and that the proposal file's own canonical
content SHA-256 and Git blob are unchanged across the run — so the acceptance cannot be a covert
regeneration.

The prior is the committed `conditions-1` artifact, asserted **first** by the two identities that do
not depend on a checkout — Git blob `42faeca2486117cd1ea518f8b679d036d6fcde87` and content SHA-256
`ead1458e…8d81ce` — and asserted to hold that one batch and nothing else.

## Merged result

| collection | conditions-1 | hazards-1 | committed |
|---|---|---|---|
| spans | 185 | 96 | **281** |
| acceptance records | 185 | 96 | **281** |
| records | 16 | 6 | **22** |
| components | 54 | 15 | **69** |
| prose bindings | 15 | 5 | **20** |
| relationships | 0 | 0 | **0** |
| references | 15 | 7 | **22** |
| provenance edges | 185 | 96 | **281** |

Every conditions-1 batch record, acceptance record, span, representation element and obligation is
preserved unchanged — asserted as a byte-identical prefix on the in-memory merge, and as
element-wise presence plus exact counts on the file that was written. The two scopes are disjoint.

**Schema anchors** keep `conditions-1` at schema 3, where its review happened, and record `hazards-1`
at schema 5. The file now *declares* schema 5, and the **registered succession** that connects them
is retained in full: `5d-lift-schema-3-to-4` → `5d-lift-schema-4-to-5`, six collections verified at
each step, never collapsed into a transition the registry has no row for.

**Both Exhaustion references now resolve** inside accepted authority — `hazard.dehydration →
condition.exhaustion` and `hazard.malnutrition → condition.exhaustion` — and no accepted reference
points outside it.

`validate_acceptance` and `validate_representation` both return **no findings**; the written artifact
round-trips exactly; it is written through `accepted_inputs_payload` in the same
indent-2 / sort-keys / LF form the file was already committed in. **One oracle file, extended** —
never a second.

## The accepted-scope status the repository now states

Accepting `hazards-1` made every standing "batch `conditions-1` only" description false. Nine such
sites — `known_unknowns.md`, `oracle.py`, `oracles/README.md`, `publication.py`, `pyproject.toml`,
`MANIFEST.in`, and three test docstrings — now say: accepted batches `conditions-1` **and**
`hazards-1`, 22 records over 281 spans, the corpus still incomplete, `actions-1` not begun, nothing
published or activated, and the production release refusing as `INCOMPLETE` rather than `ABSENT`.
Two further sentences claiming the committed artifact holds no ability-check fact were corrected to
the content the schema-5 lift was proved against, because the artifact now carries two such facts
from `hazards-1` and a reader checking the file would otherwise read the succession as illegally
registered. Recorded in `issue-5d-accepted-status-sibling-AUDIT.md`, with the one site deliberately
left alone and why. **No Owner Decision was needed** — the acceptance itself was the authorization,
and this is documentation catching up to it.

## Publication is still refused, and that is unchanged

The gate compares accepted authority against the *whole* persisted projection. The artifact now
judges 22 records where it judged 16; the SRD has far more than 22. `test_production_release` and
`test_runtime_production_release` still refuse, and their refusal was re-run rather than assumed.

## The consequence this acceptance had, stated plainly

Accepting a second batch into the one artifact **ended the repository's only specimen of the legacy
form** — a single-batch, schema-3, unanchored accepted artifact. Thirteen test modules were using the
production artifact as that specimen, because until now it *was* one, and 118 tests failed the moment
it stopped being one.

The failures split into two classes, and the two got different treatment:

* **Fixture failures (105).** Modules whose subject is the legacy form — succession evidence,
  subclass refusal at authority seams, schema-version legality, lift evidence, declared-schema
  canonicalization, acceptance across a succession, and four schema-3 zero-movement statements. The
  pre-acceptance bytes are frozen at
  `tests/ingestion/mechanical/data/legacy_conditions_1_unanchored_schema3.json` — **byte-identical**
  to what the repository committed, Git blob `42faeca2…`, so every identity those modules pin is
  unchanged — and they read it there. **No assertion was weakened or deleted**; only the input moved.
  The specimen lives under `data/`, never in the oracle directory, because two artifacts claiming one
  release is exactly what the resolver refuses — and a test asserts it stays out.
* **Semantic failures (13).** Statements that were true about the world and are now false:
  `test_conditions_1_accepted_authority.py` (renamed `test_committed_accepted_authority.py`, since
  its subject is now both batches), the production-release record and span counts, and the committed
  batch list. These were rewritten to describe what the Owner actually accepted — per-batch counts
  kept separate from the totals, so a merged count that is right for the wrong reason still fails.

Two tests changed meaning rather than numbers, and both are recorded here rather than quietly
adjusted:

* the artifact no longer declares schema 3, so *"the declared schema is the one it was accepted
  under"* became *"each batch states the schema it was reviewed under"* — the declaration follows the
  newest acceptance, the `conditions-1` anchor does not move, and the lifts connect them;
* the artifact is now buildable as current authority, which is what accepting a batch reviewed under
  the current schema means. The fail-closed refusal it used to demonstrate is **not weakened** — it
  is asserted against the specimen in the same test.

## Stop conditions honoured

`accept_proposal` called exactly once, for exactly the authorized batch and scope · the proposal,
audit and semantic representation unchanged · no schema, policy, or `src/` change other than the one
accepted-authority artifact this acceptance is authorized to extend · no partial acceptance: all 96
spans or none · conditions-1 evidence neither altered nor discarded · nothing published, activated,
or retired · branch not merged · `actions-1` not begun.
