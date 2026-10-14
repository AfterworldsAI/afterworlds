# CRD Issue 15b — C9 successor recording and 15c recertification

The Owner accepted PR #194 and the native C9 packet, including the combat Action cost (`owner-acceptance-2026-10-14.md`, a byte copy of Codex's receipt, `30b50a3e…`; `owner-acceptance.json`). PR #194's accepted head `5d05f473` passed all 11 CI jobs in run `38555377777` (`pr-194-accepted-head-ci.json`, `ci-38555377777-completed.json`).

## Recording

`record_successor.py` recorded `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json`:

- **Real file:** SHA-256 `01729b532a0ff46047608d9e46d539851ba2c9a32aaa9e0468ae0babb902ec7b`, 44,914,191 bytes, recorded `2026-10-14T18:54:11Z`.
- **Built on:** the C8 successor `ead7fa9d…2d0d`, unchanged and now superseded by digest.
- **Method:** nothing rebuilt. The four accepted C9 proposals are the reviewed preview's rendered files (copied from the preserved preview checkout with matching SHA-256, pinned by rendered digest and proposal identity). In C8's anchor order each touched batch is excised against the C8 proposal it was accepted from (pinned private copy) and its C9 proposal accepted with native `accept_proposal`; the first records the `21 → 22` lift.
- **Identities equal to the accepted packet:** oracle `924321df…ab0c`, projection `3703faf5-8b51-5c3f-b28c-b378b005f7bf`, payload `c7a52d55…2f`, schema 22 `b073cd4f…414f`, and the four proposal identities (`2f296a37…`, `b5412d4b…`, `6445a5b1…`, `3c6fa542…`).
- **Only difference from the reviewed SIMULATED preview** (`3ad7bdcb…`, preserved): `reviewer`, `accepted_at` and `rule`, only on the four touched batches (4 batch rules, 7,364 record rows, 1,121 review-unit rows), matched by row identity. Lifts, schema anchors and resolution records are equal; no SIMULATION residue.
- **The 20 untouched batches:** their batch, record, review-unit and anchor rows equal the C8 successor's, in order.
- **Native, rerun on the recording:** `validate_candidate` 0 findings; persist → reconstruct → re-identify clean; its own read-only publication gate passes in a private store copy.
- **Carried from the accepted packet** (`reports/c9-packet.json`, `d61ed1b4…`), because the representation and projection payload are identical: the five malformed-input refusals, the cross-oracle refusals, the preservation proof and the sequencing proof.
- **Run:** `record.out.txt`, `record.err.txt` (empty), `record.exit.txt` (`exit 0`, 360 s; PowerShell `$LASTEXITCODE`).

Rerun (write-once; an existing successor is rebuilt from its own recording time and must match byte for byte):

```
$env:PYTHONPATH = "src"; $env:PYTHONIOENCODING = "utf-8"
venv\Scripts\python.exe .claude/review-notes/issue-15b-c9-recording/record_successor.py --inputs <private copy of c9-native-work/inputs>
```

The private inputs (`proposals/*-C8-PROPOSAL.json`, `rel/afterworlds.db`, `rel/leaves.json`) are pinned by the packet builder; the store is only ever copied again into a temporary directory.

## Selection

`oracle.SUPERSEDED_ORACLE_SHA256` adds C8's digest, so C9 is the release's one claimant; MANIFEST.in and pyproject exclude C8 from distributions and ship C9. Oracle, packaging, succession, committed-authority and publication tests follow, and the resolution test asserts the four C9 proposal identities, schema 22, the lift and the 336 skills facts.

## Recertification

`recert/governing_components.py` computes every executable operation's governing components on the production-selected C9 and diffs them, component by component, against the superseded C8 file (`recert/governing-components.json`; the C8 evidence in `issue-15c-implementation/recert/` is untouched).

- **14 executable operations; no governing set moved;** every manifest fingerprint equals the C9 evidence.
- **Changed records:** 336, all creature profiles (330 under `monsters.`/`animals.`, six in spells and magic items: Giant Fly, Avatar of Death, Animated Object, Otherworldly Steed, Giant Insect, Draconic Spirit). Templates are certified per subject (`certify_template`), so C8-era template digests are stale on C9.
- **`CERTIFIED_RELEASE`** moves to `3703faf5-…`. Adapter `15c-d20-4` and manifest `15c-manifest-4` stay: neither adapter code nor any manifest entry changed, the versions are recorded but never compared, and a certificate's projection distinguishes C8 from C9.
- **Tests** (`tests/pipeline/rpg/test_certification.py`): all 14 certify on the production-selected index; the superseded C8 file, loaded and identified natively, refuses each with `incompatible_certification` although its fingerprints match; a changed template's digest differs and an untouched one's does not.

## Boundary

Recording installs local repository authority only. S1 is not recorded and stays a release-bound authored override applied only to isolated in-memory fixtures. No contest operation, lifecycle, #129 code, migration, Phase 3 or 19b work. PR #129 stays frozen at `d8233a43`; its explicit resume gate is not released. No publication, activation, merge, shared-runtime operation or app launch.
