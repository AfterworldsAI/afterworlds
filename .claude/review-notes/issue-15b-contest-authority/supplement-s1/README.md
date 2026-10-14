# CRD Issue 15b — candidate S1: the SRD 5.1 contest supplement

> **Accepted 2026-10-14.** The Owner accepted S1 (`c232a786…`) with PR #194 (`../../issue-15b-c9-recording/owner-acceptance-2026-10-14.md`). It stays a release-bound authored override applied only to isolated in-memory fixtures: not authored into any store, not published, not activated. Activation remains a separately authorized operational gate. The text below is the pre-acceptance record.

**This is a candidate only.** It is not accepted, not authored into any store, not published and not activated. What the Owner accepted on 2026-10-14 is the policy and source choice ([Owner Decision](../../../../docs/decisions/owner-decision-2026-10-14-contest-supplement.md)). That acceptance does not cover this artifact. S1 needs independent review and exact semantic acceptance. After that, putting it into a package's override state is a separately authorized shared-runtime operation.

| File | SHA-256 |
| --- | --- |
| `s1.json` | `c232a7863d3a31144ebb7fcdd2f7af6591b68b4f3cb096bf65ad6e6d3372c64a` |
| `page-77-extract.txt` (pypdf text of PDF page index 76) | `ed129b55cb0dccf9446dff29e89475c23fc626fa58034a1907432d11e87e80fa` |
| `validation.json` (28 checks, all true) | `22bd4d12d0ac43e27226c82e42efc7abe980840460db32f302aff7cc8ed80b66` |

**Historical C8 evidence.** `validation.json` is the accepted report, produced while C8 was the selected authority (PR #194 at `5d05f473`). `validate_s1.py` reads whichever authority `committed_inputs_for` selects, but it labels that authority C8 and rewrites `validation.json`. On a branch where C9 is recorded, running it unchanged would mix C9 data with C8 labels and overwrite the accepted report. Reproduce it on a checkout of `5d05f473`, or run only `derive_s1.py` here, which does not read the corpus. The current C9 compatibility of the accepted S1 is a separate in-memory proof, `../../issue-15b-c9-recording/s1-on-c9/` (`s1-on-c9.json`).

**Reproduce (at `5d05f473`).** Run from the repository root, with the worktree venv plus `pypdf`, which is a review-tool dependency, not a project one. Two runs produce byte-identical output.

```
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15b-contest-authority/supplement-s1/derive_s1.py [--pdf PATH]
PYTHONIOENCODING=utf-8 venv/Scripts/python.exe .claude/review-notes/issue-15b-contest-authority/supplement-s1/validate_s1.py [--pdf PATH]
```

**Pinned inputs.** All are digest-checked.

| Input | Digest or location |
| --- | --- |
| Official SRD 5.1 CC PDF | `2504d2a0…f1f0`, 3,158,713 bytes. "Contests" is on printed page 77 (index 76). Its CC-BY-4.0 attribution statement is on index 0 |
| Reviewed proposal | `6e708e77…8a20` |
| Owner policy receipt | `fcc30b1b…af03` |
| PDF location | the Codex scratch folder. It is not committed; the repository keeps the raw page text and its digest |

## What S1 is

S1 is one typed mechanical override. It uses the existing authored-authority mechanism of ADR-005d Decision 10, as amended by Owner Decision 2026-08-08.

| Field | Value |
| --- | --- |
| `override_id` | `b9134dea-52c3-546a-b13c-795fe16bfe90`, which is `uuid5(URL, "afterworlds:afterworlds.supplement.srd-5-1-contests:v1")`. It is deterministic, so identities can be computed in advance |
| Release | authored against package `1299484e…` release `5.2.1-corpus.8781d4e0-a3b`. A cross-release use fails as `INVALID_OVERRIDE` |
| Origin | `package_patch`. **Disclosed:** the enum documents it as an "administrative correction to packaged content". `house_rule` means a Sojourner-configured override, which this is not. No new origin value was added, because that would be an enum and identity change |
| Operation and target | `APPEND` on the record `play.d20_tests` |
| Patch | `append_component` with `semantic_key` `contest`, `handling` `prose_bound`, no facts. `authored_prose` is the supplement text |

**The authored prose** has four parts:
- an identifying header that states it is not SRD 5.2.1 content;
- the verbatim SRD 5.1 excerpt, from "Sometimes one character's…" to "…a tie means that the door remains shut.";
- the Owner's three adopted points, verbatim from the receipt;
- the source's own CC-BY-4.0 attribution statement, verbatim.

**Extraction.** Every run of tab, CR, LF, NBSP or space becomes one space. Three words that the PDF text layer splits are corrected, and each correction is asserted to occur exactly once:
- `e fforts` → `efforts`
- `th e action` → `the action`
- `of f` → `off`

Nothing else changes. Typographic apostrophes (U+2019), the dash (U+2014) and the attribution's quotes (U+201C/D) are extracted as they are. No U+FFFD appears.

## What the validator proves (`validation.json`)

**Source:**
- The PDF is pinned.
- The page text reproduces byte for byte.
- The excerpt reproduces and sits exactly between the "Contests" heading and the "Skills" heading.
- All 12 sentences are contained in the normalized source text.
- The corrections are listed exactly.
- The attribution is the PDF's own statement.
- The three points are verbatim in the receipt.

**The patch:**
- The payload is the canonical `patch_payload`.
- These malformed variants are refused by `patch_from_payload`:
  - structured handling carrying prose;
  - prose-bound handling without prose;
  - an unkeyed addition.

**Simulated application.** S1 is applied in memory to the committed C8 inputs (`ead7fa9d…`, projection `e4f8f4fb…`, equal to `capability.CERTIFIED_RELEASE`):

| Binding | Result |
| --- | --- |
| No overrides (`EMPTY_OVERRIDE_SET_UUID`) | no `play.d20_tests/contest` component |
| S1 present but disabled | no `play.d20_tests/contest` component |
| S1 applied | one prose-bound component. It has exactly one authored passage equal to the authored prose, `supplied_by_override_id` `b9134dea…`, and no irreducibility reason. `component_schema_id` is `802ea03805060bb6d590a1d5a2d7343d4e6c672e8fe4659b2b5aaaf7cbd54ccb` |

- The supplement-only override set is `ffcb9a48-901a-5fe7-9e80-9054b05a9097`. A package with other overrides has a different set identity, but the same component schema id.
- One added space in the text moves the schema id. A future contest certification therefore binds the exact text.
- Only that one component is added. The schema id of every other component in the release is unchanged, and `overridden` is `{play.d20_tests}`.
- **All 15 manifest operations:** each governing fingerprint is identical with and without S1 and equals its manifest pin. Every executable operation certifies under the supplemented binding; `saving_throw` stays held. S1 changes no 15c operation.

## Not done

- No store write.
- No override authored into a package.
- No publication or activation.
- No contest operation or certification code; that is dependent 15b Phase 2 work, held until acceptance.
