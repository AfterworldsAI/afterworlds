# CRD Issue 5d — Animals recorded: follow-up (#132, #137)

The Owner-approved Animals packet is recorded natively over the Monsters authority. Only Animals is new. No prior
batch was replaced, no source or release was regenerated, and no cross-file reorder was made. Nothing was
committed, pushed, published or activated. This is not an all-green claim.

## Authorization recorded

The Owner's statement, verbatim:

> "I accept the exact Animals proposal and its 65 reference resolutions, retaining 252 reference findings and the
> partial-publication block. Furthermore, we will finish the packets, tracking the known cross-file ordering
> defects explicitly, then correct the release order in one bounded pass before publication or activation."

| Owner file (prompt directory) | SHA-256 | Written (UTC) |
|---|---|---|
| `animals-owner-review.md` | `bb7a341bc6e3ca70f6d5afe911e961188613d8f045a6baff6710245cdf9e231a` | 2026-09-28T14:06:55Z |
| `release-order-owner-decision.md` | `8854e1bc03692ea9601080e2319d291ccad291982d0ff8024b687be7e5548fce` | 2026-09-28T17:19:47Z |

Both files predate the recording, which started at 2026-09-28T17:27:17Z.

- **Batch rule (`APPROVAL`)** is the first sentence, verbatim. It is exactly the owner review's suggested response,
  and it is the acceptance.
- **The whole statement (`OWNER_STATEMENT`)**, including the "Furthermore" sentence, is carried verbatim inside
  `AUTHORIZATION_REFERENCE` on every Animals resolution. The release-order file quotes that second sentence as a
  separate decision. The split does not truncate the Owner's words: both are recorded.
- **`AUTHORIZATION_REFERENCE`** names:
  - both Owner files and their SHA-256;
  - the proposal: `a3057b73ec23db2bf169286446e25047ef7d54ebc96061083e3c9a2d48045ebb`, identity
    `19685bc2b3c9a22d484b0435ba78950185dab00590a58bae36c8f41ca2fb53cd`;
  - the drafts: `924ef579a879f73c1281d1263ba8c49f166302a11578808814a3d05f776766ac`;
  - the prior oracle: `02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54`.
- The Owner is the reviewer, authorizer and executor (`Ravenlok (Owner)`, the Monsters recording's `OWNER`).

Before any write, the following were rechecked:

- proposal, drafts and identity;
- the oracle at `02f3a11b…dc54`: 21 batches, 1664 records, 1182 resolutions;
- the baseline at `e7580932b7e6766a6a02872454a54415ef066eb12ce0d55ac19d3c86e4d9d3ff`.

None of the approved proposal or draft bytes changed.

## Recording

**Script:** `.claude/review-notes/issue-5d-animals-ACCEPT.py` (new). It follows the Monsters and Magic Items ACCEPT
pattern.

**Prior:** the 21 batches, rebuilt from the Monsters recording's times through
`issue-5d-monsters-corrections-ACCEPT.py` (`recorded()`, then `monsters_accepted` and `monsters_resolved` at
`RECORDED_AT`). It is pinned to `02f3a11b…dc54` and is never read back from the artifact.

**Steps.** Each step:

- refuses unless the artifact is in the preceding state;
- reads the UTC clock when it runs;
- writes with `serialize_accepted_inputs`;
- reads the result back through `_state()`.

`_state()` fails closed on unrecognized batch sets or step times. It recognizes and replays exact intermediates, so
nothing is recorded twice.

| Step | Native seam | Executed (UTC) | Artifact SHA-256 | (batches, records, spans, units, resolutions) |
|---|---|---|---|---|
| prior | — (Monsters recording) | — | `02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54` | (21, 1664, 9589, 1364, 1182) |
| `accept-animals` | `accept_proposal`, batch `animals` | 2026-09-28T17:28:00Z | `bc11be6ee4dbc56d7f90d9d06d220cfc7ab4e31bcaaafaf84a27d78c15894f16` | (22, 1759, 10424, 1459, 1182) |
| `resolve-animals` | `resolve_references`, 65 drafts | 2026-09-28T17:28:58Z | `4ad85dab4ec9e5967779a0bb24f22c099e0aafdc9762088e340f7796b86290ba` | (22, 1759, 10424, 1459, 1247) |

- **Simulation first.** `--simulate` ran in memory under the simulated reviewer and exited 0 with the same counts
  and findings.
- **Precheck.** `accept-animals` reran both steps in memory before writing.
- **Drafts check.** `resolve-animals` checks the drafts against their reviewed bytes, their payload equality and the
  count of 65 before writing.
- **Pins.** The executed times and bytes are pinned in `RECORDED_AT` and `RECORDED_SHA256`.
- **Rebuild.** `recorded()` rebuilds the 22-batch file from them.

**Final findings:** 252 reference, 29 uncovered leaf, 0 other, 0 resolution violations. The 19 chapter pointers
(Animals ×2, Monsters ×17) stay within the 252.

### Preservation

The prior's evidence is held by two checks:

- The prior is a sha-pinned native rebuild.
- `_check` runs `REPLACEMENT._preserved` over the raw `accepted_inputs_payload` of the prior and the result. Nothing
  is blanked, so reviewer, `accepted_at`, rule, `resolved_at`, `authorized_by` and `authorization_reference` are
  compared by value, along with every record, span, unit, resolution, obligation and all 21 batch payloads.

Result: nothing lost.

`_check` also asserts:

- the 21 prior batches are an exact prefix;
- the acceptance and resolution-acceptance counts outside Animals equal the prior's, so nothing is duplicated.

`_approvals` is scoped to Animals. Every Animals batch, span and unit acceptance names the Owner, and the rule is
`APPROVAL`. Every `-animals-1` resolution carries (`OWNER`, `OWNER`, `AUTHORIZATION_REFERENCE`). The prior batches
keep the Monsters rule, and that is held by the preservation check above.

No obligation delta arose: raw preservation passes with obligations included.

### Replay

- **`--verify`** (exit 0):
  - state `resolved`;
  - the recorded bytes `4ad85dab…90ba` and the recorded times;
  - every Animals acceptance names the Owner and this decision;
  - counts, findings, preservation;
  - reloads to the same bytes.
- **Full replay:** `recorded()` rebuilt the prior through the Monsters chain from its times, then both Animals steps
  from theirs. It serialized to `4ad85dab…90ba`, byte-identical to disk.
- **Fresh-checkout caveat:** `--verify`'s findings step uses the REPLACEMENT helper's `SCRATCH_DB`
  (`.claude/_rc/msc/rel/afterworlds.db`), which is under `.claude/_*` and never committed. A fresh checkout can
  replay bytes, times and preservation, but not `_findings`, without that DB. The live tests compute findings from
  the `source_release_db` fixture instead. This is a boundary, not a gap in this run.

## Dependency moves (settled tests to the 22-batch authority)

No assertion was weakened; each pin moved to the authority it describes.

- **`issue-5d-animals-generator.py` `current()`:**
  - **Before:** it read the committed file. That read is now 22 batches and fails its own no-animals assertion.
  - **Now:** it rebuilds the Monsters-recorded prior from the Monsters recording's times, pinned to the same
    `CURRENT_SHA256` (`02f3a11b…`), with the no-animals assertion kept. This follows the Monsters generator's own
    `current()` pattern.
  - The unused `committed_inputs_for` import was removed.
  - The proposal and drafts are unchanged; the `test_the_committed_bytes…` test re-derives both.
- **`tests/ingestion/mechanical/_replacement_chain.py`:**
  - loads the Animals recording (`ANIMALS`);
  - `COMMITTED_SHA256` is now its `RECORDED_SHA256["resolved"]`, the last recorded bytes as the docstring defines
    them;
  - adds the cached `monsters_recorded()` (the rebuilt 21-batch prior).
- **`test_animals_proposal.py`:**
  - The `prior` fixture now uses `monsters_recorded()`. It is the same object as `GEN.current()`, since `GEN` is the
    recording's own generator. It asserts `02f3a11b…` against both the generator and the Monsters recording pin.
  - The disk-bytes assertion moved to a new `test_the_committed_oracle_records_the_owner_acceptance`, which asserts:
    - disk equals `COMMITTED_SHA256` and `ACCEPT.recorded()`;
    - the prior is kept whole, and Animals is the one added batch;
    - identity and rule;
    - 835 + 95 acceptances at the recorded time;
    - 65 resolutions with the Owner and reference at the recorded time;
    - counts (22, 1759, 10424, 1459, 1247) and findings (252, 29).
  - The docstring is updated.
- **`test_monsters_proposal.py::test_the_committed_oracle_records_the_owner_acceptance`:**
  - disk equals `COMMITTED_SHA256`;
  - the Monsters recording, rebuilt at `02f3a11b…`, is kept whole on disk;
  - all prior assertions, including (21, 1664, 9589, 1364, 1182) and (317, 864), now run on that rebuilt recording.
- **`test_gameplay_toolbox_proposal.py`** and **`test_magic_items_proposal.py`:** the disk-SHA pins moved from the
  Monsters `RECORDED_SHA256["resolved"]` to `COMMITTED_SHA256`. Gameplay's committed batch set adds `"animals"`.
- **`test_source_release_readiness.py`:** the committed batch set adds `"animals"`. Spans and resolutions are now
  10424 and 1247, and the docstring is updated.
- **`test_committed_accepted_authority.py::test_no_refused_candidate_is_selectable`:** the Animals proposal identity,
  recomputed from `issue-5d-animals-PROPOSAL.json`, is added to the named set, as for every earlier recording.
  - I first skipped this file on the wrong reasoning that only file names mattered. The test enumerates the batch
    identities of the committed file, so it needed the new identity.
  - This was caught in pre-handoff review, before the file was run.
- **`test_character_origins_feats_acceptance.py`:** unchanged. It reads `COMMITTED_SHA256`, whose value moved.
- **`oracles/README.md`:** the "Current" section now states 22 batches, 1759 records, 1247 resolutions,
  `4ad85dab…` and 252 findings. It also records the Animals recording and the tracked order defect.

### Animals test-comment correction

The REPLACE comment in `test_suppressing_a_governing_rule_suppresses_it_on_the_animal` said "A house rule replacing
the owner replaces what the animal reads." That was inaccurate. It now says:

- the printed rule is suppressed on the animal;
- the house text stays with the rules owner, read when the owner is selected;
- the house text is not propagated into the animal's contextual read.

The module docstring was aligned the same way. The assertion, which checks disappearance, is unchanged. The existing
contract is unchanged, and no new propagation behavior or policy is implied. The absence of the house text from the
animal's read is still not separately pinned.

## Tracked cross-file release-order defects (Owner decision, carried forward)

Under `release-order-owner-decision.md`, the known cross-file order defects are tracked here and in every subsequent
5d handoff. They are corrected in one bounded pass after the packets and before publication or activation. Content
acceptance does not declare the current release order correct.

| # | Defect | Observable effect | Status |
|---|---|---|---|
| RO-1 | `CORPUS_FILES` is largely alphabetical: Animals precedes its governing Monsters rules, unlike the official chapter order. | A direct Animals read shows the animal's own passages, then the governing *Parts of a Stat Block* rules. Monsters direct reads show the rules first. Animals text and mechanics are verified and retained. | Deferred to the consolidated release-order pass, which needs a bounded official-source comparison. |
| RO-2 | The remaining chapter order beyond Monsters rules/A–Z (already corrected relative to each other) is unverified against the official order. | Not yet characterized. | Same pass. |

The deferral does not cover within-rule, table or statblock order defects that change meaning or ownership. Such a
defect would go to immediate scoped review under `source-error-policy.md`. None was found in this recording run,
which made no source review.

## Secrets baseline

This was a scoped update from the starting bytes only. It used a private-settings scan under the baseline's own
plugins and filters. `detect-secrets scan --baseline` was never run, and no `pragma: allowlist secret` was added.

- **Before:** `e7580932b7e6766a6a02872454a54415ef066eb12ce0d55ac19d3c86e4d9d3ff` (117 files, 5518 entries).
- **After:** `2d7854786839ff799eef31d91989b9df4151e9cd5b72e00e7e16dff5ddf8347b` (118 files, 5527 entries).
- **Preserved** (asserted before writing):
  - settings, plugins, filters, version and `generated_at`;
  - every untouched file's entries;
  - the key order of the existing files.
- **Added entries:** all have `is_verified: false`.
- **Line endings:** LF.
- **Staged:** `.secrets.baseline`, by name.

| File | Added | Moved | Pruned |
|---|---|---|---|
| `src/…/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json` | 2 | 1005 | 0 |
| `.claude/review-notes/issue-5d-animals-ACCEPT.py` (new file) | 7 | 0 | 0 |
| `.claude/review-notes/issue-5d-animals-generator.py` | 0 | 1 | 0 |
| `tests/ingestion/mechanical/test_animals_proposal.py` | 0 | 3 | 0 |
| `tests/ingestion/mechanical/test_monsters_proposal.py` | 0 | 3 | 0 |
| Other scanned files: `_replacement_chain.py`, gameplay/magic-items/source-release/committed-authority tests, oracles `README.md`, this doc | 0 | 0 | 0 |

**Size of the staged diff.** `START` (`e7580932…`) is the index bytes before this run, and they already carry the
earlier uncommitted recordings. As a result, `git diff --cached -- .secrets.baseline` against HEAD is about 32k lines,
while this run's own delta is only 9 added, 1012 moved and 0 pruned.

**The authority test.** `test_committed_accepted_authority.py` was scanned after its edit and has 0 findings, so the
baseline was unchanged by it.

**The 9 additions.** Each was recovered from its line and checked against its SHA-1 before being accepted as a
public literal (`.claude/_sp/ani/rec/verify.json`, 0 unverified):

- **Oracle `proposal_identity` (line 6463):** recomputed from the PROPOSAL.
- **Oracle `semantic_diff_hash` (line 7302):** `batch_diff_hash` of the rebuilt Animals batch, equal to the stored
  field.
- **ACCEPT:**
  - PROPOSAL SHA-256 (line 88), identity (line 89) and DRAFTS SHA-256 (line 91);
  - both Owner-file SHA-256s (lines 102 and 105);
  - the rebuilt `animals-accepted` bytes (line 141) and the recorded oracle bytes (line 143).

The machine-readable delta is `.claude/_sp/ani/rec/baseline-delta.json`, with pruned entries listed and none
present.

**Hook.** Run twice on the final bytes of all 12 affected files, including both changed generators/recorders, the
oracle and this doc (PowerShell):

```
$f=Get-Content .claude/_sp/ani/rec/files.txt
rtk proxy .\venv\Scripts\detect-secrets-hook.exe --baseline .secrets.baseline @f; "exit=$LASTEXITCODE"
```

Runs in order:

- **Runs 1–2 (11 files, before staging):** each exited 1. The hook's only output was "Your baseline file
  (.secrets.baseline) is unstaged". No secret was reported. `.secrets.baseline` was then staged by name.
- **Runs 3–4 (11 files):** each exited 0.
- **Gate pair (12 files):** run after the authority-test edit and this doc's final edits. Both runs exited 0.
  `git diff --quiet -- .secrets.baseline` exited 0, so nothing is left unstaged.
- **Stability:** `.secrets.baseline` stayed byte-identical at `2d785478…347b` across all runs, so the hook rewrote
  nothing.

## Gates (raw)

This is not an all-green claim.

PowerShell, repo root, explicit venv via `rtk proxy`:

| Gate | Command | Result |
|---|---|---|
| Simulate | `python .claude/review-notes/issue-5d-animals-ACCEPT.py --simulate` | exit 0 (49.6 s); expected counts and findings |
| Record step 1 | `… issue-5d-animals-ACCEPT.py accept-animals` | exit 0; `bc11be6e…4f16` |
| Record step 2 | `… issue-5d-animals-ACCEPT.py resolve-animals` | exit 0; `4ad85dab…90ba` |
| Verify | `… issue-5d-animals-ACCEPT.py --verify` | exit 0 |
| Independent replay | `recorded()` rebuilt and hashed | exit 0; `4ad85dab…90ba` |
| Collect | `python -m pytest tests/ingestion/mechanical --collect-only -q -p no:cacheprovider --no-cov` | exit 0; 4016 collected |
| Changed tests | `python -m pytest <test_animals_proposal.py, monsters/gameplay committed, magic_items in-memory + committed, source_release_readiness pilot-authorities, character_origins_feats recorded-bytes> -q -p no:cacheprovider --no-cov` | exit 0; 18 passed in 715.70 s |
| Black | `python -m black --check <8 changed .py>` | exit 0 |
| Ruff | `python -m ruff check <8 changed .py>` | exit 0 |
| detect-secrets hook | see Secrets baseline | see Secrets baseline |
| mypy (`src/`) | not run: no `src/` Python changed (README only) | — |
| Expanded mypy | deferred | non-green |
| pip-audit | deferred | non-green |
| Committed-oracle loaders | `python -m pytest "$m/test_committed_accepted_authority.py" "$m/test_accepted_inputs.py" "$m/test_oracle.py" "$m/test_packaging.py" -q -p no:cacheprovider --no-cov` (`$m='tests/ingestion/mechanical'`) | exit 0; 152 passed in 89.23 s (`.claude/_sp/ani/rec-grp.log`) |
| Black / Ruff (authority test) | `python -m black --check` / `python -m ruff check` on `test_committed_accepted_authority.py` | exit 0 / exit 0 |
| Full suite | not run: only the changed gates were in scope | — |

**Scope of the edited pins.** Each edited pin is local to a test that ran:

- `test_source_release_readiness.py:379–395`: the pilot-authorities test.
- `test_gameplay_toolbox_proposal.py:628–631`: the committed test.
- `test_magic_items_proposal.py:906` and `:929`: the committed and in-memory tests.

`COMMITTED_SHA256` is read by the tests that ran, including `test_character_origins_feats_acceptance`. A grep of
`tests/ingestion/mechanical` for the prior pins found no stale value outside the moved tests. The pins searched were
`1664`, `9589`, `1364`, `1182`, `317`, `864` and `02f3a11b`.

## Retention (current purpose only)

Nothing was deleted.

- **`issue-5d-animals-ACCEPT.py`**, the Animals PROPOSAL/DRAFTS, `-source.py`, `-generator.py` and `-review.md`:
  replay and review evidence for the recorded batch. `--verify` and the live tests read them.
- **`issue-5d-monsters-corrections-ACCEPT.py`** and its REPLACEMENT: the prior's authority. The Animals prior,
  generator and tests rebuild through them.
- **`.claude/_rc/msc/rel/afterworlds.db`** (`SCRATCH_DB`): retained while ACCEPT `--verify` and replay need
  `_findings`. See the fresh-checkout caveat above.
- **`.claude/_sp/ani/`** (scratch, never committed):
  - `rec/` holds this run's baseline scan/verify/apply and its delta;
  - the earlier packet scratch stays while Codex's independent verification may reread it.
- **Untouched:**
  - quarantined `srd-5-2-1-corpus-36b786d8-fa2.json`;
  - protected `issue-5d-source-correction-REPLACEMENT-PACKET.md`;
  - the 574662e9 oracle (`fc62c47c…5a62`);
  - root `afterworlds.db`;
  - the 4 stashes;
  - the pre-existing staged deletions and unrelated changes.

## Blockers and deferrals

- **Partial publication:** blocked. There are 252 reference findings and 29 uncovered leaves, and the release-order
  pass (RO-1, RO-2) is still pending.
- **Deferred, non-green:** pip-audit and expanded mypy.
- **Later work, not expanded here:**
  - the remaining 5d packets;
  - broad accepted review;
  - Casting Spells;
  - shared coverage (including the `# Animals` part heading);
  - the one bounded release-order correction.
- **Source errors:** `source-error-policy.md` applies: official errata first, then the official resource, then
  notify the Owner.
- **Codex:** independently verifies before the remaining 5d work.

## Process disclosures

- **Nothing committed.** Nothing was committed, pushed, merged, published or activated. There was no shared DB and
  no Chroma write. The only change this run staged is `.secrets.baseline`, staged by name. The pre-existing staged deletions are
untouched.
- **Alias collision.** A PowerShell helper named `R` collided with the `Invoke-History` alias. The multi-replace
  script it ran was a no-op: the file was rewritten with identical bytes, and the SHA-256 was rechecked before
  proceeding with the Edit tool.
- **Connectors.** Context7, Expedia, Google Calendar, Intuit TurboTax and Shopify need authorization in claude.ai
  connector settings. They were not used.

## Sources

- https://www.dndbeyond.com/srd
- https://media.dndbeyond.com/compendium-images/errata/MM-25/MM-2025_v1.pdf
- https://www.dndbeyond.com/sources/dnd/sae/monster-manual
- https://www.dndbeyond.com/posts/1950-sage-advice-and-errata-for-the-new-core-rules-is
