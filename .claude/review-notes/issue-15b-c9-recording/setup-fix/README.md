# Collection-dependent ORM registration at fixture setup — sibling audit

**Defect family.** A test fixture calls `Base.metadata.create_all` while the set of models registered on `Base` depends on which modules pytest happened to collect first. `persistence/orm/dnd5e_state.py` (and `character_sheet.py`) declare story-scoped tables with FKs to `stories.story_id`. When an RPG module is collected first, those tables are registered but `stories` is not. `create_all` then raises `NoReferencedTableError: dnd5e_character_states.story_id -> stories`.

**Trigger.** The combined focused runs, in which `tests/pipeline/rpg/test_certification.py` was collected before the ingestion persistence modules:
- first run: 1,050 passed, 1 failed, 42 setup errors;
- repeat run: 1,049 passed, 1 failed, 16 setup errors.

Codex reduced it to two nodes: 1 passed and 1 error in 32.34 s (`CODEX-C9-SETUP-ERROR-DISPOSITION.md`). The same error reproduced with `test_bloodied.py`, which is unchanged since main, so this was not caused by C9.

**Fix (in scope).** `tests/ingestion/conftest.py` explicitly imports `afterworlds.persistence.orm.node` and `.story`. This is the convention `tests/services/dnd5e_state/conftest.py` already uses: Story registers Node, and the pair is self-contained. That conftest is the parent of every ingestion `create_all` site, including:
- the mechanical `session` fixture;
- `source_release_db` and the fresh/durable finalization helpers.

The FKs are retained. There is no production, model or migration change, and no test split.

**Evidence** (this directory; focused diagnostics only, full output and real exit codes):

| Run | Result |
| --- | --- |
| `two-node.*`: Codex's exact reproduction | 2 passed, 34.86 s, exit 0 |
| `affected.*`: `test_bloodied.py` first, then `test_accepted_inputs.py`, the subclass persistence node and `test_representation_schema_identity.py`. Covers all 16 nodes that errored in the repeat run | 140 passed, exit 0 |
| `siblings.*` | 432 passed. Run **with** the three sibling patches that were later reverted (see below), so it is **not** evidence for this head |

**Reused publication proof.** The isolated publication module passed 27 before this change, when `stories` was not registered in its process. The question is whether registering Story/Node in `source_release_db` could change that. The earlier 26-pass run of `test_bounded_d20_on_published_release.py` and `test_srd_state_on_published_release.py` answers it:
- in that run, the API module imports `create_app`, which registers Story/Node at collection;
- `test_srd_state_on_published_release.py` builds its store from `source_release_db`.

So `source_release_db` has already been exercised with exactly this registration, and passed. The publication module's own fixtures copy that store and add no `create_all`. Its 27 passes are reused, not rerun.

**Sibling dispositions.** Determined by a fresh-interpreter probe per module (importing the module and its conftest chain), not by grep:

| Site | Disposition |
| --- | --- |
| All `tests/ingestion/**` `create_all` sites (17) | **patched**, through the parent conftest |
| `tests/services/dnd5e_state/conftest.py`, `tests/services/conftest.py`, `tests/services/rules_authority/**`, `tests/persistence/**`, `tests/pipeline/{orchestrator,retrieval,writer,extractor}/**`, `tests/pipeline/rpg/test_sheet_effects.py`, `tests/api/**`, scripts tests | **already safe**: importing each module on its own registers `stories` and `dnd5e_character_states`, so its own imports admit the graph whatever was collected first |
| `tests/entitlement/conftest.py`, `tests/pipeline/provider/conftest.py`, `tests/test_quarantine_5c_5d.py` | **out of scope, deferred**: their standalone registration lacks `stories`, a latent gap. Codex's scope disposition (`../CODEX-SCOPE-DISPOSITION.md`) keeps them out of this authority PR, so the patches tried here were reverted. Not observed failing |

Probe: `registration_probe.py`; output at this head: `probe.out.txt` (45 sites). `"True …"` means the site registers `stories` on its own, which ingestion sites now do via the parent conftest. The only `"False False"` sites are the four deferred ones above. Nothing else in the family was found.
