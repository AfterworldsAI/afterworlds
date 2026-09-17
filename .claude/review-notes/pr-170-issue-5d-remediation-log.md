# PR #170 — CRD Issue 5d practical reliability: independent-review remediation

Remediation of the first independent review of the runtime implementation. Two
defects, one evidence gap, and four reporting corrections. Nothing here reopens
the Owner's 2026-09-16 adoption, and no corpus content is accepted, published or
activated.

Head at time of writing: **`5cce971`**, stacked on **#169** at `668ae84`.

---

## Finding 1 — review-unit acceptance was outside the recorded contract

**The defect.** `MechanicalProposal` stated no review inventory, and
`accept_proposal` took the units as a separate argument. A batch's
`proposal_identity`, resolved scope and semantic diff therefore described the
spans and nothing else. Probed with `tests.ingestion.mechanical.
test_accepted_inputs._accept` and `conftest.REVIEW_UNITS`: accepting the two
units, versus accepting the same two with the first unit's `expected_rules`
replaced by `()`, produced **different oracle identities but identical batches
and identical acceptance evidence**. Retained evidence could not say which
expectation inventory the reviewer accepted, nor attribute a unit to the action
that accepted it.

A second, separate defect in the same seam: a legitimate support-only review
unit — a section read and found to state no mechanical rule, so there is nothing
to classify — was refused with *"an acceptance action must name at least one
span"*. That retained exactly the obligation the amendment removed.

**The fix, as the smallest versioned extension of the existing contract.**

* **`5d-proposal-2`** states `proposed_review_units` inside `proposal_payload`,
  so the inventory a reviewer was asked to read is inside the identity an
  acceptance records. `_ENVELOPE` maps each version to its exact top-level key
  set. `5d-proposal-1` states none and writes the exact payload the seven
  retained proposals are identified from; carrying an inventory under it is
  refused at both the writer and the reader rather than silently dropped.
* **`accept_proposal(..., resolved_review_units=...)`** names which proposed
  units this action accepts. Silence over a proposed unit is not acceptance of
  it. A unit no proposal proposed, a repeated id, or an id a prior batch already
  recorded are each refused.
* **`ReviewUnitAcceptance(unit_id, batch_id, reviewer, accepted_at)`** is
  retained as the exact sibling of `AcceptanceRecord`, including a **nullable
  `batch_id`** on the same terms — `None` for an individually reviewed unit,
  named for one taken as part of a batch. `accept_proposal` always names the
  batch it is taking, so every unit accepted through the production path carries
  its attribution, and the demonstration tests assert it there.
* It is **emitted only when nonempty**, in `acceptance_evidence_payload` and in
  `accepted_inputs_payload`, so the seven committed artifacts keep their exact
  bytes and every recorded `persisted_state_digest` is unchanged.
* **An acceptance may name no span when it names a review unit.** `_validate_batch`
  treats a unit-only batch as complete evidence; naming neither a span nor a
  unit is still refused.
* **Closed in both directions at the loader** (`oracle.py`): an acceptance record
  naming a unit the artifact does not state is refused, and a stated unit no
  action accepted is refused (*"an inventory nobody accepted is not review
  evidence"*). **And in persisted state**: `rp_mech_review_unit_acceptances`
  (Alembic `0034`), with the same two-way closure in `validate_raw_closure` and a
  downgrade that refuses rather than invents once a row exists.

**Not done, deliberately:** no new framework, no per-fragment paperwork, no field
on `AcceptanceBatch`. Putting reviewer and timestamp on the batch would have
moved the committed bytes of the seven accepted artifacts; a sibling ledger does
not.

**Demonstrated** in `test_accepted_inputs.py` through production acceptance and
gate paths: exact reviewed scope; per-unit batch attribution across two batches;
artifact round-trip and persistence/reconstruction; refusal of an altered
inventory (different `proposal_identity`, and `load_proposal` refuses when the
reviewed identity is supplied); refusal of an unaccepted inventory at the loader
and in reconstruction; and a span-free support unit accepted, persisted,
reconstructed and run through `run_publication_gate`.

## Finding 2 — `load_proposal` ignored `proposal_schema_version`

**The defect.** A retained file declaring a version this build cannot read was
rebuilt under current rules and restamped with the current constant. Because the
restamped payload re-derived the old identity, supplying the recorded
`expected_identity` **confirmed** the substitution instead of catching it.

**The fix.** The declared version is checked against the closed set of shapes
this build reads, and the envelope against exactly what that version declares —
both before reconstruction and before the identity comparison. Unsupported,
missing, mistyped and undeclared envelope content are all `ProposalLoadError`.

**Demonstrated** in `test_retained_proposals.py` on copies of the retained Speed
JSON, each with the recorded Speed identity supplied: `unsupported-proposal-999`;
missing, int and list versions; a foreign envelope key; an inventory carried
under `5d-proposal-1`. A readable version still reaches the shape checks, and
`test_a_loaded_proposal_is_proposed_not_accepted` shows PROPOSED-state
normalization unchanged. All seven retained proposals still load and still derive
their recorded identity.

## Evidence gap — conditions-1 is committed

`.claude/review-notes/issue-5d-conditions-1-schema3-REMEDIATION-PROPOSAL.json`,
the exact reviewed file, sha256
`d9ad121c833265042f43d137c376265ddee61adbc3c4867023d8db8d5794968d`, 166,038
bytes, is committed at `d44ace5`. `git show :<path> | sha256sum` matches the
working-tree sha exactly — no line-ending normalization moved it. It
independently re-derives the proposal identity the accepted seven-batch artifact
records for conditions-1, and the `NOT_COMMITTED` skip in
`test_retained_proposals.py` is removed: **all seven batches are now checked
unconditionally.**

Its high-entropy strings are content hashes — release binding pins, declared
policy and schema hashes, derived span ids — not credentials. A JSON artifact
cannot carry an inline allowlist pragma, so its baseline block was added by the
additive splice (`.claude/review-notes/_conditions1_baseline_splice.py`,
untracked scratch, like every other `_*_baseline_splice*.py`): scan a copy, add only that one file's block, leave every other entry and
`generated_at` untouched.

Superseded conditions-1 drafts are deliberately not committed: retained review
history nobody accepted, several of which no longer load under the current
closed representation union.

---

## Reporting corrections

**`.secrets.baseline` did change.** `git diff 668ae84..d38a162 -- .secrets.baseline`
is **11 insertions / 4 deletions** — the `bounded_oracle` fixture's restamped
fingerprints and line numbers. The earlier report called it unchanged; it was
not. `d44ace5` adds a further **275 insertions / 0 deletions**, the conditions-1
block. Both are justified fingerprint updates, and both are now stated.

**The pip-audit number was not the configured gate's.** The earlier "29 findings"
came from a raw `pip-audit` with none of CI's exclusions. The configured gate is
reported below.

**cover-1's stale live output path needs no Owner decision.** `issue-5d-cover-1-
ACCEPT.py` pins `ACCEPTED_PATH` to the live release path, which speed-1's later
acceptance overwrote with the seven-batch merge, so `--verify` compares a
six-batch rebuild to a seven-batch file. The script is retained acceptance
evidence and is left unchanged for that reason — an ordinary engineering choice,
not an Owner item. **cover-1's reproduction against its frozen six-batch prior
`86cd11c2…` (47 records / 558 spans) passes on this head**, in
`tests/ingestion/mechanical/test_cover_1_acceptance_reproduction.py` alongside
`test_speed_1_frozen_prior.py` — 12 tests, inside the ingestion chunk and rerun
directly on the current tree. The retained ACCEPT scripts were not re-executed.

**`application.py` / `views.py` carry the retention reason; they do not branch on
it.** `EffectiveComponent` and `GameMasterComponent` expose
`prose_retention_reason_code` beside `irreducibility_reason_code` so a consumer
can tell which of the two reasons retained the prose. **Neither downgrades the
prose to explanatory-only on that basis, and both reasons may preserve governing
rule meaning.** The intended consumer is a GameMaster-authority view that says
which reason applies; the field is exposure, not a semantic switch.

**CI has not run on this implementation head.** `.github/workflows/ci.yml`
triggers only on `pull_request` targeting `main`; this PR targets
`docs/issue-5d-practical-reliability`. Documentation CI on #169 is not runtime
CI. The gates below were run locally and are reported as such.

---

## Finding 3 — a review unit could decide nothing and certify everything

Reported on the `d38a162` review as comments 4026372087, 4026398077 (expected-
rule precision and source links), 4026372100 (supporting linkage) and 4026398066
(empty-unit accounting). One defect family, one correction, one patch round;
duplicate bot comments were not treated as separate rounds. Comment 4026398055
(acceptance evidence) was closed by `96c620b` and stays closed.

**Verified at `34da498`, before the fix.**

1. A `ReviewUnit` naming every leaf of the fixture, with no expectations, no
   exclusions, an empty `RepresentationDraft`, zero spans and a unit acceptance
   record, produced `validate_candidate(..., bound_corpus()) == ()`. The unit
   relaxed the complete-partition rule for every leaf it named and gave nothing
   back. `excluded_group_reasons` was a bare tuple of strings with no membership,
   so a reason could not say which text it excused, and `ReviewUnit` carried no
   source-scoped link from supporting material to the authority it explains.
2. Replacing `REVIEW_UNITS[0].leaf_ids` with `(SUPPORT_LEAF,)` while keeping its
   original expected rules produced **no** `review_unit_violations`.
   `ExpectedRule` stored `record_key` / `component_key` / `fact_family` only, so a
   family-presence check could not tell two rules or two exceptions of one family
   apart: drop one of two exceptions and the survivor answered for both.

**What was already sufficient, and is unchanged.** The exact accepted-oracle /
output comparison still catches a changed build against an unchanged good
oracle. The missing contract was source-reviewed expectations specific enough to
detect omission or substitution, and group coverage of the text a unit reviewed.

**The correction.**

* `ExpectedRule.source_span_ids` names the accepted spans the rule was read from.
  Costs the reviewer nothing to state — every fact and prose binding already
  carries at least one admissible provenance edge (`PROVENANCE_REQUIRED_KINDS`),
  and the check accepts any admissible role, so a shared representation claimed
  `PRIMARY` from one span and `CONTEXTUAL` from another still passes.
* `SupportingGroup(leaf_ids, supports_record_key, supports_component_key="")` and
  `ExcludedGroup(leaf_ids, reason)` replace `excluded_group_reasons`. Exact
  membership plus one decision, at **group** granularity — no row per character,
  no row per extraction fragment, no automatic semantic classifier, no second
  copy of the prose.
* Every leaf a unit names must be reached by some decision — a rule read from a
  span of that leaf, a supporting group, or an excluded group. `_accounted_leaves`
  is the single definition, used both to report an unaccounted leaf and to decide
  whether the unit earns the partition relaxation there, so the two can never
  disagree.
* Carried through proposal identity, explicit acceptance, the accepted artifact,
  persistence and reconstruction, projection identity, raw-state closure and the
  publication gate. Alembic `0035` adds `source_span_ids`, creates
  `rp_mech_review_groups`, drops `excluded_group_reasons`, and refuses in both
  directions rather than inventing a source span or a membership no reviewer
  recorded.

**Precision claimed, and its bound.** Component + family + source spans tells
apart two exceptions of one family read from **different** spans, and catches a
rule or passage substituted from the wrong source text. Two facts of one family
read from the **same** span are not distinguished by the expectation check; that
is the exact oracle comparison's job and no attempt is made to duplicate it.

**The shapes that changed are this branch's own.** `review_unit_payload`, the
artifact's `_review_unit` required keys and `5d-proposal-2` all changed without a
further version bump, for the same reason `0033` and `0034` are edited in place
rather than superseded: proposal shape 2 was introduced on this branch, nothing
has ever been written under it, and every retained proposal and accepted artifact
declares `5d-proposal-1`, which states no review inventory. A shape no recorded
document uses is not yet a contract with anything.

**A batch must accept the source its units' rules cite.** New observable
constraint, and the reason two `test_accepted_inputs` batch tests were re-split:
`accept_proposal` refuses a unit whose expected rules name spans outside the
merged accepted scope of this acceptance and its priors. That is the intended
reading — an expectation read from text no acceptance holds is not coverage of
anything accepted — but it constrains how a multi-batch acceptance is cut, and
the regular-section pilot should cut batches along unit boundaries because of it.

**Nothing recorded moved.** No committed JSON artifact contains `review_units`;
all seven accepted artifacts declare `5d-proposal-1`, and `projection_payload`
omits the key when empty. No recorded projection identity and no recorded
`persisted_state_digest` changes. `0033` and `0034` are this branch's own and
unreleased. The Speed data and its recorded scope order, the four-part bindings
and override/replay behaviour are untouched.

**Proof** — `tests/ingestion/mechanical/test_review_units.py`, 58 tests:
round-trip of all three decision kinds through persistence and the committed
artifact; a blank unit reporting both its unaccounted leaves and the uncovered
text it used to excuse; rules left behind by narrowed membership; two
`movement_permission` exceptions read from two sentences passing together and
failing exactly the dropped one's expectation; wrong-source rule and prose
substitution; unlinked, unreasoned, empty and out-of-unit groups; valid
all-supporting and all-excluded units and a shared representation passing; and
the group rows inside both `identify_projection` and
`compute_persisted_state_digest`. `test_gate.py`'s support-section unit now
states the supporting decision that makes its leaf reviewed — a unit that named
the leaf and decided nothing is refused, which is the fix observed at the gate.

---

## Gate results — head `5cce971` unless stated

| Gate | Scope | Result |
|---|---|---|
| `black --check src/ tests/` | whole gate path | clean, 477 files |
| `ruff check src/ tests/` | whole gate path | All checks passed |
| `mypy src/` | whole gate path | Success, 225 source files |
| `pytest tests/ingestion` | 3179 tests | **3179 passed**, 854s |
| `pytest tests --ignore=tests/ingestion` | 2785 tests | **2775 passed, 10 skipped**, 317s |
| combined coverage | both chunks, `--cov-append` | **94.12%**, `--fail-under=80` met |
| detect-secrets (pre-commit hook form) | staged files of each commit | clean |
| `pip-audit` (CI flags verbatim) | installed venv | **22 findings, 7 ignored, 9 packages**; exit 1 |

Per-file coverage of the changed modules: `acceptance.py` 95, `accounting.py` 95,
`models.py` 100, `oracle.py` 95, `persistence.py` 98, `proposal.py` 96,
`raw_state.py` 97, `orm/mechanical.py` 100.

`tests/ingestion` was also run at `96c620b` (3179 passed, 478s) before the
`5cce971` registry commit, which touches only `tests/services`. The coverage run
above is the one on the final head.

**pip-audit, configured gate.** `pip-audit --ignore-vuln CVE-2026-4539
--ignore-vuln CVE-2026-3219 --ignore-vuln CVE-2026-45829 --ignore-vuln
CVE-2026-45830 --ignore-vuln CVE-2026-45831 --ignore-vuln CVE-2026-45833`
reports **22 findings across 9 packages** at the versions installed in the local
venv: click 8.3.1, cryptography 49.0.0, idna 3.11, mako 1.3.10, msgpack 1.1.2,
pip 26.0.1, pydantic-settings 2.13.1, setuptools 82.0.1, urllib3 2.6.3. The six
configured exclusions accounted for 7 of the 29 raw findings, including every
chromadb advisory.

**These are installed local versions, not repository dependency changes.**
`git diff 668ae84..HEAD -- pyproject.toml` is **empty**: this branch declares no
new dependency and changes no pin. None of the nine packages is pinned by
`pyproject.toml` at a version this branch chose. That says what changed here; it
does **not** establish when each advisory first existed, and no such claim is
made. Remediation is dependency maintenance outside this phase. No exclusion was
added, no policy changed, no upgrade performed.

---

## Regular-section pilot — identified, not authored

`.claude/review-notes/issue-5d-regular-section-pilot-IDENTIFICATION.md` names
**`Playing the Game > Proficiency`** (container `1fb4fa49-571f-5c36-8540-
595aba2d643f`): 30 represented leaves, one policy-excluded interloper, one owned
table container, zero overlap with any accepted batch. It lists the six
exceptions a source-reviewed expectation must catch and the membership questions
the acceptance — not engineering — must settle. **No draft, proposal, acceptance,
lift or publication is produced, and no candidate record key is proposed.**

## Remaining boundaries

* **Corpus publication is incomplete.** Seven batches are accepted; the corpus is
  not finished, and nothing here publishes or activates.
* Ten cross-batch targets remain unresolved: `glossary.burrow_speed`,
  `climb_speed`, `climbing`, `concentration`, `crawling`, `fly_speed`, `flying`,
  `jumping`, `swim_speed`, `swimming`.
* An excluded group's `reason` remains free prose rather than a closed catalog
  — deliberate, and revisitable if the vocabulary settles.
* An expectation cannot tell apart two facts of one family read from the same
  span. The exact accepted-oracle comparison covers that case.
* `bounded_oracle.json` does not round-trip through `accepted_inputs_payload`.
  Pre-existing and unrelated: the fixture is hand-authored, not writer-produced.
  The released artifact round-trips exactly.
* Publication of this work is the Owner's; #170 stays draft until independent
  review and the required gates are complete.

---

## Gate results — head `0cb696c` (coverage-decision round)

| Gate | Scope | Result |
| --- | --- | --- |
| `black src/ tests/` | gate paths | clean (3 files reformatted, then clean) |
| `ruff check src/ tests/` | gate paths | clean (3 `I001` autofixed) |
| `mypy src/` | 225 files | **Success** |
| `pytest tests/ingestion` | 3205 tests | **3205 passed** (857s) |
| `pytest tests --ignore=tests/ingestion` | 2785 tests | **2775 passed, 10 skipped** (336s) |
| combined coverage | both chunks, `--cov-append` | **94.15%** |
| detect-secrets (pre-commit hook form) | staged files | clean; baseline unchanged |
| `pip-audit` | installed venv | same pre-existing findings as above; no upgrade, no exclusion |

CI now runs on this PR: it targets `main`, and the head is `0cb696c`.

---

## Finding 4 — a multi-source expectation verified one source and certified all of them

Second independent review, on `0cb696c`. The correction that closed Finding 3
gave `ExpectedRule` a `source_span_ids` list and explicitly allowed several
spans, because a rule stated across two sentences is one rule. The checks read
that list as *alternatives*.

**Verified symptoms at `0cb696c`.**

* One `ExpectedRule(SPELL_KEY, EXCEPTIONS_KEY, MOVEMENT_FAMILY, (CRAWL_SENTENCE,
  CLIMB_SENTENCE))` against `_exceptions_draft(CRAWL_EXCEPTION)` returned no
  violations, although the second expected source had no surviving authority.
* One `ExpectedRule(SPELL_KEY, OPEN_ENDED_KEY, None, (SPELL_SPAN, PROSE_SPAN))`
  returned no violations against the normal fixture, which binds prose for that
  component from `PROSE_SPAN` only.

`_expected_rule_violations` accepted governing prose if *any one* named source
was bound; `_family_carried_from` likewise accepted a matching family fact read
from any one named source. Meanwhile `_accounted_leaves` credited *every* named
source leaf. So an expectation bought the partition relaxation on source
material it never verified — the same source-expectation completeness family as
Finding 3, with the multiple-source input the single-source tests of that round
did not cover.

**The correction.** Each named span is a required constituent, not an
alternative.

* Prose: the set of spans this component actually binds is computed once, and
  the finding names `sorted(sources - bound)` — exactly the passages with no
  home, not the whole list.
* Structured: `_family_carried_from` (a bool) becomes
  `_family_sources_without_authority`, which collects the target keys of the
  component's facts of the expected family and returns the named spans no
  provenance claim on those keys reaches. Same `fact_target_key`, same option
  handling; only the direction of the question changed.
* `_accounted_leaves` is unchanged and now honest: once every named source must
  be verified, crediting every named source leaf credits nothing unverified.
  `validate_candidate` runs `review_unit_violations` over the same candidate in
  the same pass that grants the relaxation, so an unmet constituent fails the
  gate rather than quietly widening coverage.
* `ExpectedRule.source_span_ids` says so in the model, which is where the
  ambiguity was.

**No duplicate facts and no per-fragment classification.** One shared structure
carrying a provenance claim to each passage that states it satisfies all of
them — proven, with one fact, in
`test_one_shared_fact_answers_for_both_sentences_it_was_read_from`. Nothing
counts facts; source repetition is repetition, not duplication.

**Proof.** Both of the independent review's reproductions are used literally as
negative controls, and each asserts that the finding names *only* the
unsupported span — which is what distinguishes "each source required" from
"list rejected wholesale":
`test_a_rule_read_from_two_passages_needs_a_home_for_both`,
`test_one_rule_read_from_two_sentences_needs_authority_for_both`. Positive
controls: `test_a_rule_read_from_two_passages_passes_when_both_are_bound` and
the shared-authority test above. The production seam is exercised by
`test_a_multi_source_rule_is_refused_at_the_gate`, which runs
`validate_candidate(reviewed_candidate((unit,)), bound_corpus())` and asserts
the honest inventory still returns no findings. The structured controls stay at
`review_unit_violations` level for the reason recorded in Finding 3: their
sub-leaf sentence spans overlap the fixture's leaf-wide span, which is
`validate_partition`'s question, not this one.

**Nothing recorded moved.** No stored shape changed, no migration was needed,
and no accepted artifact, proposal identity, scope order, binding or digest is
touched. The change is entirely in what the validator requires before an
expectation becomes trusted coverage.

Three of the previous round's assertions were reworded with the finding text:
"carries that family from other source text only" was false once a *partial*
list could fail, and is now "carries no fact of that family read from there".

---

## Gate results — head `fe66ff4` (multi-source expectation correction)

| Gate | Scope | Result |
| --- | --- | --- |
| `black src/ tests/` | gate paths | clean (1 file reformatted, then clean) |
| `ruff check src/ tests/` | gate paths | **All checks passed** |
| `mypy src/` | 225 files | **Success** |
| `pytest tests/ingestion/mechanical tests/services` | 3718 tests | **3718 passed** (240s) |
| detect-secrets (pre-commit hook form) | staged files | clean; baseline unchanged |

Targeted, not a full suite: the full local run belongs to `0cb696c` (5980
passed, 10 skipped, 94.15% coverage) and is not re-attributed to this head. CI
on the final pushed head is the full-suite evidence for this correction.

---

## Finding 5 — a proposal could state one id twice and have one definition silently discarded

Raised as comment `4032773536` after #170 was marked ready; Codex returned the
PR to draft for this correction.

**The defect.** `accept_proposal` built `proposed_units_by_id = {u.unit_id: u
for u in proposal.proposed_review_units}` before anything looked for repeats.
Two units sharing one `unit_id` and stating different kinds were reduced to
whichever came last. Resolving that id then accepted one definition while the
`proposal_identity` the batch retains as evidence — derived from the ordered
list — names both, and the discarded definition never reached the
accepted-candidate duplicate validator, which only ever sees what survived the
dictionary.

This is not a hash collision. Reversing the two definitions derives a different
`proposal_identity`, so the identity distinguishes them perfectly; what failed
was an invalid duplicate identifier getting past the uniqueness contract at the
acceptance boundary.

**The sibling.** `proposed_by_id = {p.span.span_id: p.span for p in
proposal.proposed_spans}` loses an entry the same way. A four-entry proposal
containing one repeated span id accepts as three spans whenever the resolved
scope is unique, and the batch retains an identity naming four.

**The correction.** One `_repeated` helper — a `Counter` over ids — and two
refusals placed immediately before either dictionary is built, so neither
conversion can discard an entry that was never refused:

* `this proposal proposes spans more than once: [...]`
* `this proposal proposes review units more than once: [...]`

Identical repeats are refused on the same terms as conflicting ones: resolving
the id still names an entry no reader can point at, and a proposal stating one
unit twice has said nothing the second statement adds. The check counts ids
only, so rejecting an invalid identifier never depends on what the duplicate
definition contains, nor on whether this acceptance names it — which is why no
unaccepted unit is asked for valid semantic coverage in order to be refused for
a duplicate id. The two pre-existing `.count()` duplicate checks over
`resolved_scope` and `resolved_review_units` now call the same helper;
behaviour and messages are unchanged.

Ordered resolved scope, legitimate representation merging and shared authority,
the declared proposal formats and the seven historical proposal identities are
all untouched: nothing here changes what a valid proposal derives.

**Bounded sibling dispositions.** Codex checked the neighbouring selection paths
before handing this off; one more was found while placing the fix.

| Path | Disposition |
| --- | --- |
| proposed review units, duplicate `unit_id` | **patched** |
| proposed spans, duplicate `span_id` | **patched** (verified sibling) |
| repeated resolved span / unit ids | already rejected |
| re-accepting an id a prior batch accepted | already rejected |
| accepted-inventory and raw-state duplicates | already rejected |
| `_merged_collection` keyed union across representation collections | **out of scope** — intentional contract, rejects conflicting contents, unchanged |
| `proposal_payload`'s `by_span` origin/rationale lookup | **already safe** — the same last-wins shape, but acceptance now refuses before any identity is recorded as evidence, and an unaccepted proposal's identity attests to nothing |

All seven retained production proposals were loaded and checked: zero duplicate
proposed span ids, zero duplicate unit ids. No Owner Decision, no new
framework, no policy expansion.

**Proof.** Four new tests at the public `accept_proposal` boundary in
`test_accepted_inputs.py`:
`test_a_proposal_stating_one_unit_id_twice_is_refused` (conflicting kinds, and
this action resolves *no* unit, so the refusal cannot be coming from coverage),
`test_a_repeated_unit_definition_is_refused_even_when_it_is_identical`,
`test_a_proposal_stating_one_span_id_twice_is_refused` (asserts the four-entry /
three-unique-id shape explicitly) and
`test_a_repeated_span_definition_is_refused_even_when_it_is_identical`. The span
tests resolve the *deduplicated* ids on purpose: passing the raw list would trip
the pre-existing "resolved scope repeats spans" refusal and the tests would pass
for the wrong reason.

Ordinary valid proposals are the existing controls rather than a new one:
`test_retained_proposals.py` loads all seven through the production loader, and
`test_cover_1_acceptance_reproduction.py`,
`test_speed_1_acceptance_reproduction.py` and
`test_areas_of_effect_1_acceptance_reproduction.py` re-run real
`accept_proposal` calls end to end. All pass on this head.

Regression check, on the same terms as Finding 4: the new tests were run against
`git show HEAD:...acceptance.py` — **4 failed, 51 passed**, the failures being
exactly the four new tests, each "DID NOT RAISE". The file was restored and
`git diff --stat` confirmed the change intact. No stash was used.

**Nothing recorded moved.** No stored shape, migration, accepted artifact,
proposal identity, scope order, binding or digest is touched.

---

## Gate results — head `171ac6c` (duplicate proposed id refusal)

| Gate | Scope | Result |
| --- | --- | --- |
| `black --check src/ tests/` | gate paths | clean, 477 files |
| `ruff check src/ tests/` | gate paths | **All checks passed** |
| `mypy src/` | 225 files | **Success** |
| `pytest tests/ingestion/mechanical` | 2974 tests | **2974 passed** (177s) |
| detect-secrets (pre-commit hook form) | staged files | clean; baseline unchanged |

Focused, not a full suite. Prior evidence keeps its own heads: the full local
run (5980 passed, 10 skipped, 94.15%) is `0cb696c`'s, and CI run `35174458362`
(5985 passed, 10 skipped, 94.15%, audit clean) is `b6eddfe`'s. CI on this
head is the full-suite evidence for this correction.
