# CRD Issue 15c — C8 native SIMULATED preview (review packet)

**SIMULATION ONLY.** This is not an Owner acceptance, recording, publication, activation or supersession. The preview oracle and the five rendered proposals live in the git-ignored `preview/`. `build_c8_preview.py` regenerates them byte for byte. Codex cleared exactly raw C8 r2 (`7e7d5b43…`) for this step (`../issue-15c-implementation/codex-c8-raw-correction-review.md`, `9e80f93a…`).

**Branch:** `codex/issue-15c-c8-preview` (worktree `.claude/worktrees/agent-aa5b1ea6bf4ee4f39`), from `1d4193c`. Schema 21 exists only there. Main stays on accepted C7 / schema 20.

**Reproduce:** from the repository root (a worktree works), using the repository venv with this checkout's `src` first on `PYTHONPATH`:

```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15c-c8-native/build_c8_preview.py --twice
```

It writes `reports/c8-preview.json` (`--dry` stops after the mapping). The builder asserts `afterworlds.__file__` is under this checkout's `src`. It reads git-ignored inputs read-only, from this checkout or the nearest ancestor that holds them; each is digest-pinned:
- the accepted C5 packet proposals `issue-15c-native/preview/proposals/{spell-descriptions,magic-items,monsters,animals}-PROPOSAL.json`;
- the accepted C7 preview proposal `character-origins-feats-C7-PROPOSAL.json` in the preserved C7 preview worktree `agent-afb6123d0b7851456`;
- the isolated release store `g1-work/rel/afterworlds.db`, which is only ever copied privately;
- the Codex correction review (untracked in the main checkout).

**Run of record:** 2026-10-13, head `056d3d4`, `--twice`, launcher PID 61644 (Python PID 696), exit 0, 849 s (committed `reports/c8-build.log.out` and `.log.err`; the supervisor log `reports/c8-build.log` and `reports/focused-tests-1.log` are `*.log`, so git-ignored and kept locally in the worktree). One build; no rebuild was needed.

## Exact identities

| Item | Identity |
| --- | --- |
| Raw candidate C8 r2 | `7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628`; correspondence `43589153…0ce24`; inventory `3f05591e…7ce55d`; schema plan `1c33046c…3b1b5` |
| Prior: recorded C7 successor | `srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json`, `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373` (read only) |
| Schema | `5d-representation-schema-21` / `4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55`; lift `5d-lift-schema-20-to-21`. Schema 20 `759dcc1f…e77a` reproduces from the frozen code at `1d4193c` and stays the registered lift source |
| Preview oracle file | `a2d96264dd18605680358393270e1f9f4fc27da144fda09da06e31cbd5250016` (44,788,438 bytes) |
| Oracle identity | `70646cd987dcf75adc7b57b6271e38c6ca8cc9b508584dac89c5acefafa3e8d9` |
| Projection | `e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42`, payload hash `e615d0106996466b8ab72dacd481934b7982e4c421a661eb2cc0e3fcdfad5d87` |
| C7 successor lifted to 21 (cross checks) | projection `7ea06d93-74cc-5e33-9d2f-38892fe3d106`, payload hash `99380ddf694fbd934f05f46ebeef62faa0355648cd91d8f5a97a0ae61da2b122` |
| Builder | `build_c8_preview.py` as run: `bf4e57b0362e3fa6c51c56fc9d78bffc6e0b818f329e710197e1bd3a8af3aa09`; `common.py` `20761dc0…9b07`, `excise.py` `80a177b3…62a3` |

| Batch (C7 anchor order) | Accepted proposal → preview proposal | Rendered SHA-256 | Facts / claims / rules |
| --- | --- | --- | --- |
| spell-descriptions | `dce22fbd…bbdc9` → `1c01d1e4f603acebf8baa14b909b7b07406e0e3f0c27330a305363f923d527c7` | `68c7526213cf976963e9408b0063140c70af38ef7a671c23c4144e00dfcc4377` | 5 / 5 / 5 (4 `creature_type`, 1 `summoned_creature_type`) |
| magic-items | `bc4979d7…e712` → `d88713097ad106b5e645b35cf1e0f1bffaa6408a8cd7af2faa4da68331f6996b` | `f6a8b41281de0023a493803c934bf906ed8ee5909a544a9800743f0e9c63a2cd` | 2 / 2 / 2 |
| monsters | `ff24d9da…c617` → `bec1bedc4097a7b42c6acbf64c6131688caa2c86cc85616006b2de1a85c886be` | `c12dad2846359cd35823c48c36e7dbca6fc6553a37c65ac5764a571173289984` | 235 / 235 / 235 |
| animals | `efa248a9…21c9` → `db3f0d2dd9c997f4f2edc1f8fd361244becf7720ab80834c7e2828d971e92014` | `6c2cd65751bdbefbb48ac042c0a201af087f8aca0cd9229a0e53bf48d95b8bbf` | 95 / 95 / 95 |
| character-origins-feats | `1e7b63d3…bfd28` → `301572d46bc655125bc45ad8d08b53d044c0d28014c2ea0340bedd08d2a20f5f` | `9705cf1d223db4395311f23215bd12e451a1115a65b1ee6b3aa8bcd88674f1fe` | 9 / 9 / 9 |

Accepted inputs (rendered SHA-256): spell-descriptions `e8830765…957d`, magic-items `28a7f4d5…0e31`, monsters `9f30cf57…474f`, animals `7186c42a…8631` (C5 packet), character-origins-feats `58706886…178e` (accepted C7).

## Construction

- **Ownership:** each fact's batch is read natively from the successor's acceptance records. For profiles it uses the spans that the component's existing fact claims name. For species and Find Familiar, which have no fact, it uses the prose-binding spans. All 346 equal the correspondence `batch`. Animals profiles also bind monsters-scoped spans, so binding spans alone do not decide ownership.
- **Claim:** one contextual claim per fact on the **one** bound span whose leaf text holds the fact's quote. Exactly one such span exists for every fact, and it is always one of the correspondence's `claim_spans`; the correspondence lists the component's full claim set, 5–6 spans. One ExpectedRule goes in that span's review unit.
- **Components:** the 336 creature profiles stay `mixed`. Each keeps its handling, facts, options, prose, retention reason and bindings, and gains one `creature_type` fact appended after its existing facts. The nine species `creature_type` components and `spells.find_familiar/effect` go from `prose_bound` to `mixed` and keep their prose and retention reason. Nothing else in any proposal moves (asserted).
- **Chain:** in C7 anchor order, each batch is excised claim-based and re-accepted with SIMULATED evidence. The first acceptance records `20→21`.

## Proofs (all true in `reports/c8-preview.json`)

- **Pins:** before and after.
- **The 19 untouched batches:** batch, record, review-unit and anchor rows are byte-identical in their own order, matched by filtering, because evidence rows serialize in canonical order. The five touched batches move by construction. Re-acceptance appends their anchors after the 19 untouched ones, in the C7 order, so `equipment` now precedes them. This is asserted exactly. The batch set is unchanged.
- **Unchanged:** spans, reference resolutions and records, release binding, policy and policy transitions.
- **Lifts:** C7's plus exactly `20→21`.
- **Representation:**
  - exactly 346 components changed, each by one appended type fact;
  - the only handling changes are the 10 `prose_bound→mixed`;
  - 346 provenance claims added, 0 removed;
  - records, prose bindings, relationships and references are identical sets;
  - every collection's delta equals the proposal delta.
- **Review units:** touched units change only by the 346 added rules; other units are identical.
- **Obligations:** they change only on fact records.
- **Native:**
  - `validate_candidate` returns 0 findings;
  - five malformed variants are each refused through `validate_candidate`: Familiar form whose type is not Beast, unknown form, non-profile form, duplicate choice, and Find Steed single choice;
  - persist → reconstruct → re-identify is clean in a private store copy, for the preview and for the lifted successor;
  - the gate passes against the preview oracle;
  - the lifted C7 successor is refused against the preview, and the reverse.
- **Successor lift:** lifting C7 to 21 records `5d-lift-schema-20-to-21` and leaves its representation unchanged.
- **Determinism:** `--twice` gives a byte-identical oracle and proposals.

## Schema 21

- `CreatureTypeKind`: the 14 types, declared in `representation.py` (inside the hash). `test_creature_type_facts` pins it equal to `models.dnd5e_vocabulary.CreatureType`.
- `CreatureTypeFact` (`creature_type`): `type: CreatureTypeKind | None`, `type_choice: tuple[CreatureTypeKind, ...]`. Manifested invariant: exactly one of a fixed type with an empty choice, or `None` with at least two distinct, sorted choices.
- `SummonedCreatureTypeFact` (`summoned_creature_type`): `type_choice`, `instead_of`, `forms: tuple[ComponentReference, ...]`. Manifested invariants:
  - the choice has at least two types, distinct and sorted, and does **not** contain `instead_of`. A choice "instead of a Beast" that offers Beast is ill-formed; this is the engineer's judgment;
  - `forms` is non-empty, distinct and sorted.
- **Relational rule** (`validation._validate_summoned_creature_types`, inside `validate_representation`). Each form must be a component of the draft that is a creature profile: a `creature` record carrying `creature_size`. Its own `creature_type` facts must be exactly `[instead_of]`. Facts refused by their own invariants are not read, and forms whose own size or type facts are refused are skipped; their refusal is the finding.
- **Lift:** `5d-lift-schema-20-to-21` moves nothing. No field was added to an accepted family and no component key was added.

**Focused diagnostics** (not acceptance or full-gate evidence): `scripts/run_focused_tests.py` over 18 schema, oracle and succession test files: 2993 passed, 0 failed, 642 s (`reports/focused-tests-1.log`). Black, Ruff and mypy are clean on the changed files. The full suite was not run.

## Not done (held)

Not done:
- real acceptance or recording, a committed oracle, supersession, or a change to `oracle.py`;
- type-dependent execution: Ghast/Ghoul rider saves, familiar target typing and `creature_attack` recertification;
- the creature-species input proposal;
- main integration, push/PR/merge, publication/activation, runtime migration and app launch.
