# CRD Issue 15c — C8 recertification baseline delta review

Verdict: **pinned delta cleared; no blocking defect found**. Disposition: **already safe / no change**. This supplies bounded evidence for the complete PR review, not a separate Owner milestone, a whole-PR gate result or merge/runtime authority.

Reviewed only immutable `183a664e8645ecadd97c55517e8ba1120e9c5b19` → `555be9aed30e48bd05a469c73092177bb676e400`. Reused the 284-entry C8 and 49-entry C8 recording clearances without repeating them. Read the full governing draft (working SHA-256 `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`) and the whole-PR Owner correction. Applied the installed Review/routing skills with this task's already verified Library Review 2026-09-25 and Prompting 2026-10-05 resolutions.

## Actual delta

All baseline changes concern `recert/governing-components.json`.

| Baseline change | Count |
| --- | ---: |
| New exact filename/detector/hashed-value identities | 12 |
| Removed exact identities | 1 |
| Existing identities changed only in `line_number` | 178 |
| Other existing entries unchanged | 13,751 |
| Audit flags or detector/filter/configuration fields changed | 0 |

The recertification file moves from **248 to 259 total baseline entries**; 259 is not the number of new suppressions. The complete baseline moves from 13,930 to 13,941 entries. Every new entry retains `is_verified: false` and has no `is_secret` field; this metadata is not the basis of harmlessness.

The **12 additions** are ten public mechanical component-schema digests (nine species' `creature_type` components and `spells.find_familiar/effect`) and two public procedure fingerprints (`creature_attack` and the new `creature_species`). The **one removal** is the replaced `creature_attack` fingerprint. Its old value occurs at the expected old fingerprint field, reproduces from the old sorted component list, matches the old manifest constant, and is absent from the new recertification JSON. It is obsolete public hash evidence, not a credential.

The JSON content changes are the projection UUID, ten added governing tuples for `creature_attack`, its replaced fingerprint, and a new `creature_species` operation containing 73 governing tuples and its fingerprint. There are no removed or changed existing component tuples and no other changed operations. Repetition across operations explains why 83 added component occurrences produce only ten newly baselined component identities.

## Content and producer proof

For all 12 new entries, the removed entry, and both old/new locations of the 178 relocated entries, exactly one hex token on the committed recorded line matches the entry's SHA-1 `hashed_secret`. Every anchor reproduces with installed **detect-secrets 1.5.0, Hex entropy limit 3.0**: 369 bounded in-memory line reproductions. Filenames, detector identity and existing entry flags agree. No scan of unrelated files or previously cleared C8 entries was repeated.

Producer inspection used committed source, without importing application code. `recert/governing_components.py:52` obtains component-schema identities and hashes the sorted tuple lists at lines 55–57. `src/afterworlds/services/dnd5e_state/authority.py:81` builds a component identity from mechanical schema/prose/override fields and SHA-256 hashes canonical JSON at lines 109–110. `tests/services/dnd5e_state/builders.py:100` builds the authority index from committed accepted inputs. These are mechanical content identities, not authentication values. The affected old/new procedure fingerprints were independently recomputed directly from committed JSON tuples and matched their manifest constants; the native producer was not rerun. This verifies fingerprint content meaning without claiming a fresh semantic recertification.

The manifest diff also replaces one existing inline `allowlist secret` fingerprint line and adds one inline fingerprint line using the existing pattern. Both exact constants match the independently recomputed public fingerprints. These narrow constant annotations do not introduce a broad detector/filter exemption. Later manifest changes are outside this review.

All non-results baseline fields, plugin settings, thresholds and filters are unchanged. `.pre-commit-config.yaml`, `.github` and `.gitignore` are unchanged over the pinned range. Reused the prior synthetic changed-value baseline-subtraction negative control because its matcher and settings are unchanged; no redundant control run was needed.

## Exact bytes, evidence and limits

| Immutable input | Base SHA-256 | Reviewed SHA-256 |
| --- | --- | --- |
| `.secrets.baseline` | `a8555f69c00b2500357be7e5a79c23eca5e6d174ec0fcdf89bc33e908efdb162` | `80aa17c07541aaa4ccef5fcf380b274b0eae3573b97cd845f95d7d4cf6d2a699` |
| `recert/governing-components.json` | `7348e0b8cef732587ac943a5ec507397818bb993332077593cc5757174a215de` | `a5d4bcc3dab436a41de4e2820d93dd6c25556ef999f1b89da90cd23238e5be50` |

Reproducible evidence is in `c8-baseline-review/recert/check.py` and `results.json`, including exact source/producer hashes, all added/removed/relocated anchors, JSON field locations, classifications and detector/content matches. The script ran successfully with this isolated checkout's `venv/Scripts/python.exe -B`.

At **2026-10-13 20:00:23 UTC**, HEAD had advanced to `d71035d6e2cb5b4ca1f5f0af63b15b4d296cd5e4`. The baseline and recertification JSON still matched the reviewed snapshot (source working comparisons normalize CRLF/LF). The later committed/working `capability.py` differs and is **unreviewed here**. Other later additions and mutable implementation/test/review outputs are likewise outside this immutable delta. This clearance applies to the exact pinned baseline and recertification content; affected later suppressions, producer/content changes or control changes need corresponding review, not automatic inheritance.

No source/baseline/Owner-document/Git change, native builder, private-store access, test/gate run, network operation, installation or runtime action occurred. Writes were restricted to this note and `c8-baseline-review/recert/`. The engineer's active work was untouched. Whole-PR exact-head gates, independent integration review and consolidated Owner acceptance remain due.
