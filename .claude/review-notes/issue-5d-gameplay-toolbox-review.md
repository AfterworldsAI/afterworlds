# CRD Issue 5d — Gameplay Toolbox packet, offered for review (#132, #137)

**Superseding status (2026-09-27): ACCEPTED and RECORDED.** The Owner accepted this exact proposal and its
one reference resolution; `issue-5d-gameplay-toolbox-ACCEPT.py` recorded both at 09:46:01Z and 09:46:44Z
UTC. See `issue-5d-gameplay-toolbox-recorded-followup.md`. The status below is kept as written at review.

**Status: UNACCEPTED proposal plus one unrecorded resolution draft.** Nothing is accepted, recorded,
committed, pushed, published or activated. `oracles/` is untouched. No shared DB or Chroma was written.
This packet has no Owner decision yet. Codex reviews it independently before any acceptance.

## Remediation (2026-09-27, source-fidelity; no new Owner policy)

Three consolidated findings are corrected under the existing CRD Issue 5d / ADR-005d authority. The
source bytes and the release are unchanged (`source.py` SHA as below).

1. **Net citation (source.py:632).** "Adventuring Gear" cites the Net's statistics, and the Net has no
   record of its own. The citation is now **unresolved in equipment scope**, with its exact printed text. It
   no longer widens to `equipment.adventuring_gear`. This is the only "Adventuring Gear" citation in the
   part. No accepted Equipment record changed.
2. **Troubleshooting is read inside Combat Encounters (PDF pp202–203).** The PDF sets Troubleshooting at the
   level of *Combat Encounter Difficulty*.
   - *Troubleshooting* stays its own `section` review unit over its own release container,
     `gameplay-toolbox/troubleshooting`, with exactly its printed leaves.
   - Its seven components are components of `gameplay_toolbox.combat_encounters`, after `step_3_…`, in
     printed order: `troubleshooting`, `many_creatures`, `adjustments`, `cr_0_creatures`,
     `number_of_stat_blocks`, `powerful_creatures`, `unusual_features`.
   - No record, edge, membership or `SCOPED_WITHIN` is added. The release container is not reinterpreted.
   - **The bounded helper extension** is in `authoring.py` (`build_entry_batch`, where `RepresentationDraft`
     records are built). Two placed entries may share one record key, and the record is emitted once. If
     their kinds differ, it raises. Before this change, the helper emitted one `RecordDraft` per entry, and
     `validate_representation` rejects the duplicate key. So this is not a relaxation: every source,
     span, provenance and review-unit check runs unchanged. Batches with unique keys build byte-identically;
     the sibling byte pins below prove it.
3. **GM latitude by source meaning.** The `\bGM\b` heuristic is gone. `LATITUDE` pins each
   `gamemaster_latitude` component to the printed words that delegate the ruling. The generator asserts
   that the words occur in the component and that every row is used:

   | Record / component | Delegating words |
   |---|---|
   | `curses_and_magical_contagions` / `cursed_creatures` (source.py:136) | "You decide how a spell like _Remove Curse_ affects…" |
   | `curses_and_magical_contagions` / `narrative_curses` (:156) | "…is up to you" |
   | `fear_and_mental_stress` / `fear_and_mental_stress` (:344) | "If you plan to use any of these rules" (rule adoption) |
   | `fear_and_mental_stress` / `fear_effects` (:361) | "At your discretion…" |
   | `fear_and_mental_stress` / `mental_stress_effects` (:374) | "…at your discretion." |
   | `poison` / `poison` (:412) | "You may decide that a partial dose has a reduced effect" |
   | `combat_encounters` / `adjustments` (:947) | "You can adjust an encounter on the fly" |

   The other 74 components are `no_identified_structured_use`. Some address "you" but were checked by
   meaning and are **not** latitude, because they state a procedure or a tabled option:
   - the background design intro and steps (:62, :66): permission to author; the steps state the
     constraints;
   - the traps' "_At Higher Levels._" scaling (:606…:807): the table gives the values;
   - "You can make the pit easier to escape" (:688, :803): a design option, not a ruling;
   - the encounter-budget procedure (:912) and the CR 0 guidance (:952).

   Latitude is written as `irreducibility_reason_code`. Each binding carries its component's reason.

Settled residue, not reopened:
- exact absent named item or part targets stay unresolved;
- Origin Feats is not resolved to the all-feats catalogue;
- `gameplay_tool` stays the kind.

## Artifacts (exact hashes)

| File | SHA-256 |
|---|---|
| `issue-5d-gameplay-toolbox-source.py` (unchanged) | `3289297524d4ff7321a7bc6f033ea6542fc8fc4ef99917ee81bc98a18f74745f` |
| `issue-5d-gameplay-toolbox-generator.py` | `5d236922dbc6e43907b0f7746f46021328c35a5484281c24400dced9733b952a` |
| `issue-5d-gameplay-toolbox-PROPOSAL.json` (499819 bytes) | `3a2751744b6350933f0c0aaec3cbb88761afcfb4f4d35434394bf70537fd49a6` |
| `issue-5d-gameplay-toolbox-resolutions-DRAFTS.json` (unchanged) | `b87e6dcfdb29f4d02317a98e7b868cd12b122c3f5daf99d68ff5b9004a4528dd` |
| `tests/ingestion/mechanical/test_gameplay_toolbox_proposal.py` | `0526f94aff01c2fc20762e590b1e718630d9e3554a94fd74a63d1a9fa6186ef5` |
| `src/afterworlds/ingestion/mechanical/authoring.py` | `41b59e0e2a853c25624d1a8abce330238202439ead5da0abb8808fdcae920ac4` |

- **Proposal identity:** `8d4db7037b167648995d31bef6ad2f47ae31a19a2b48bf42406246517ee719eb`.
  - Superseded: proposal `9b501ea0…` and identity `677b69bb…`.
- **Composed over:** `srd-5-2-1-corpus-574662e9-0ef.json`, SHA
  `b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f`.
  - Release `ebdd9333-eeed-5df1-b3e1-8b97c2f65f80` / `5.2.1-corpus.574662e9-0ef`.
  - Contents: 947 records, 4826 spans, 645 units, 18 batches and 1097 resolutions.
  - Findings: 143 refs, 5621 uncovered, and nothing else.
  - It is read only.
- **Generated with** `.claude/_rc/corr/rel/afterworlds.db`. `main` asserts that its binding equals the
  oracle's.

## Grain and representation

**33 records, all `gameplay_tool`, and 34 review units.**
- Eight section records. *Troubleshooting* is a unit read into `combat_encounters`.
- 25 `CATALOGUE_MEMBER` members, in printed order:
  - 3 contagions;
  - 14 poisons;
  - 8 traps.
- No edge touches `combat_encounters`.

The build has:
- 285 leaves, spans and bindings, each distinct, and no accepted leaf or key;
- 81 components with 0 facts, all prose-bound;
- 513 provenance claims.

Partition and review-unit checks report 0 findings. The representation check reports 170 findings, all
expected:
- 146 are accepted targets the packet alone cannot see;
- 24 are unresolved: equipment 9, feats 1, magic-items 2, monsters 11, playing-the-game 1.

**References (171).** They go to the exact accepted glossary, spell and `equipment.tools.*` records, and
"Travel Pace" goes to its section. These stay unresolved:
- Net, Iron Spike, Poisoner's Kit and the Net's "Adventuring Gear" citation;
- Carpet of Flying and "Magic Items";
- the 11 bold creatures;
- "Equipment", "Playing the Game" and "Origin Feats".

"Vehicles" and "Frigid Water" point inside their own record and are not references.

**Resolution draft (unrecorded, unchanged).** `glossary.challenge_rating` / `""` / "Combat Encounters" →
`gameplay_toolbox.combat_encounters`. Three accepted "Gameplay Toolbox" part pointers stay unresolved.

**Source qualification (unchanged).** The 285 leaves below `# Gameplay Toolbox` (pp192–203) were compared
leaf by leaf with the PDF. The remaining disagreements are harmless and byte-exact:
- *Step 3* prints as a sibling of *Combat Encounter Difficulty*; one record reads the whole subtree in
  order.
- The *Travel Terrain* table sits inside *Vehicles* and is its own `travel_terrain` component.
- Four leaves carry extraction artifacts that lose no meaning: leaf 270 fuses "Example 3", leaf 271 uses
  "•", and leaves 145 and 226 carry a mid-sentence `\n`.

## Native outcomes (test only, in memory)

**Accept then resolve** (`accept_proposal` → `resolve_references`):

| | Before | After |
|---|---|---|
| Records / spans / units / resolutions | 947 / 4826 / 645 / 1097 | 980 / 5111 / 679 / 1098 |
| Uncovered leaves | 5621 | 5336 (exactly the 285 cleared) |
| Reference findings | 143 | 166 = 143 − 1 drafted + 24 packet-own, all unresolved |

- `REPLACEMENT._preserved` finds no dropped or changed accepted byte, so the actual approvals are exact.
- The first 18 batches are identical.
- The `oracles/` directory is byte-identical before and after.

**Production rules-authority service** (one persisted draft on a private DB copy):
- Selecting `combat_encounters` reads *Combat Encounters* and then *Troubleshooting*, text for text in
  printed order.
- A `(combat_encounters, adjustments)` component selector reads only the *Adjustments* leaves. With the
  record also selected, each component is read once.
- REPLACE of `adjustments` reads `AuthoredProse` in its place (third after Step 3). The other 11
  components are unchanged.
- The existing section, member, disable and replace behaviour still passes.

## Gates (changed only; raw, attached, logs in `.claude/_sp/gt/`)

| Gate | Result | Log |
|---|---|---|
| `pytest tests/ingestion/mechanical/test_gameplay_toolbox_proposal.py` plus the `committed_bytes` tests of `character_origins_feats`, `conditions_pilot` and `combat_damage_breaking` (shared-helper byte pins) | 18 passed (199.2 s) | `pytest-final.log` |
| Black `--check`: generator, test, `authoring.py` | clean | `lint-final.log` |
| Ruff: same three files | all checks passed | `lint-final.log` |
| `mypy src/` | no issues in 235 files | `lint-final.log` |

Not run:
- No full or near-full suite, per the task.
- pip-audit stays deferred.

## Secrets baseline (scoped, remediation)

| | |
|---|---|
| Before | `ed7803764de722e292ce5e02656df0f4e393f34c95a8b49f889ee47d729eb125` (asserted before writing) |
| After | `7d1e44bf2fff2247258d64bec90b823eed8194ddb6b65ccd45c6402c5ef2a9d9` (staged; index = worktree) |
| Added / pruned / line-refreshed | 2 / 2 / 9 (2 in the test; 7 on the generator's and PROPOSAL's surviving entries) |
| Entries / files | 3281 → 3281 / 75 → 75 |
| Preserved | top-level settings, filters, version and `generated_at`; hashes and types identical across all 75 files; line numbers refreshed on 3 files (test, generator, PROPOSAL), all other entries byte-identical; existing key order; `is_verified` false on added entries |

The six changed files were rescanned under the baseline's own plugins and filters: the generator,
PROPOSAL, DRAFTS, this note, the test and `authoring.py`. Only the test changed findings:
- **Added:** the new `IDENTITY` (the recomputed `proposal_identity` of the PROPOSAL) and `PROPOSAL_SHA256`
  (the recomputed SHA-256 of the PROPOSAL). Both were recovered from their lines and verified public
  (`verify.log`, `verify.json`).
- **Pruned:** the superseded `677b69bb…` identity and `9b501ea0…` SHA. The rescan no longer finds either.

Probing:
- **Scanner probe:** it used a baseline copy in `.claude/_sp/gt/`, which was deleted afterwards.
- **Hook:** `detect-secrets-hook --baseline .secrets.baseline` ran on the six files plus the baseline,
  twice. Both runs exited 0 with the SHA stable (`hook.log`). The final rescan (`scan-final.json`) and
  hook run (`hook-final.log`) found no new or obsolete finding, matched every line number, and left the
  SHA at `7d1e44bf…`.
- **A first hook run was rejected, not accepted.** The first apply step, `ed780376…` → `cafd9b53…`, added
  and pruned entries but did not refresh the line numbers of files with no new findings. The hook then
  rewrote the baseline: it refreshed those 7 lines, but it also dropped 16 other files' live entries and
  wrote CRLF. That rewrite was discarded with `git checkout -- .secrets.baseline`, which restored the
  staged `cafd9b53…`. A second scoped step, `cafd9b53…` → `7d1e44bf…`, refreshed only those 7 line
  numbers.
- **Deltas:** `baseline-delta-1.json` and `baseline-delta.json`.
- **Not done:** no `scan --baseline` was run and no allowlist pragma was added.


## Boundaries

- Nothing was committed, pushed, merged, published or activated. Partial publication stays blocked.
- Left untouched:
  - the quarantined `36b786d8-fa2` oracle;
  - the protected `issue-5d-source-correction-REPLACEMENT-PACKET.md`;
  - the 36 pre-existing staged deletions;
  - the unrelated modified files;
  - the four stashes.
- pip-audit 31/11 stays deferred and non-green.
- The broad accepted review, Casting Spells and shared coverage come after 5d.
