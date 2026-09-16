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
additive splice (`.claude/review-notes/_conditions1_baseline_splice.py`):
scan a copy, add only that one file's block, leave every other entry and
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
`86cd11c2…` (47 records / 558 spans) passes on this head.**

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
* `excluded_group_reasons` remain free prose rather than a closed catalog —
  deliberate, and revisitable if the vocabulary settles.
* `bounded_oracle.json` does not round-trip through `accepted_inputs_payload`.
  Pre-existing and unrelated: the fixture is hand-authored, not writer-produced.
  The released artifact round-trips exactly.
* CI has not run on this head, by trigger design.
