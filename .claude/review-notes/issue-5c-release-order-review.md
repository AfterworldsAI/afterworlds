# CRD Issues 5c and 5d release order review

Prepared for the Owner on 6 October 2026. **Verdict: one bounded correction is
needed before publication or activation.** The official SRD supplies the full
14-file order. The recorded Owner Decision already authorizes this consolidated
correction after the content packets; no new chapter-order policy is needed.
This review proposes that correction and identifies its consequences. It does
not change the corpus, record new acceptance, or lift the publication block.

## Authority and reviewed state

The [21 September restart decision](../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md)
governs CRD Issue 5c (#132) and CRD Issue 5d (#137). The exact
[release-order Owner Decision](issue-5c-release-order-review/owner-order-decision.md)
was recovered from the earlier review workspace and matches its recorded
SHA-256 `8854e1bc03692ea9601080e2319d291ccad291982d0ff8024b687be7e5548fce`.
Its instruction is:

> Furthermore, we will finish the packets, tracking the known cross-file ordering defects explicitly, then correct the release order in one bounded pass before publication or activation.

The [current recording review](issue-5d-final-ten-references-recording-codex-review.md)
establishes 24 accepted batches, 1,835 records, 1,486 reference resolutions and
real approvals, and zero reference, uncovered-leaf or other findings. The live
oracle is still SHA-256
`e6f5f36aa3af13807bbff721797d971dcf0d8e588a97483c7d769cf88cbd1308`,
bound to `67c81736-15fd-5e82-8523-e84922f0a7c6` /
`5.2.1-corpus.3fe24ff6-4e3`, representation schema 17.
These are accepted semantics over the present release, not acceptance of a
future replacement binding.

Review guidance reuses the versions already verified current in this task:
Review Afterworlds Issues 2026-09-25 and Prompting Claude Code 2026-10-05.
Their Library selection and download evidence remain in
`../_sp/final-ten/codex-coordination.md`; no newer source was reported.

## Official order compared with the current release

The [official PDF](../../docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf) retains SHA-256
`8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87`.
Its printed Contents on page 2 establishes this sequence. The Monsters rules
on page 254 and the Animals transition on page 344 were also inspected visually:
Animals follows the final Monsters A-Z material, including the Ogre Zombie on
the same page. The stat-block index is an index, not the chapter reading order.

| Proposed position | Source file | Official start page | Current position |
| --- | --- | --- | --- |
| 1 | `legal-information.md` | 1 | 1 |
| 2 | `playing-the-game.md` | 5 | 12 |
| 3 | `character-creation.md` | 19 | 3 |
| 4 | `classes.md` | 28 | 5 |
| 5 | `character-origins.md` | 83 | 4 |
| 6 | `feats.md` | 87 | 7 |
| 7 | `equipment.md` | 89 | 6 |
| 8 | `spells.md` | 104 | 14 |
| 9 | `rules-glossary.md` | 176 | 13 |
| 10 | `gameplay-toolbox.md` | 192 | 8 |
| 11 | `magic-items.md` | 204 | 9 |
| 12 | `monsters.md` | 254 | 10 |
| 13 | `monsters-A-Z.md` | 258 | 11 |
| 14 | `animals.md` | 344 | 2 |

**RO-1: verified release-blocking implementation defect.** Animals appears
before its governing Monsters rules. The first broken contract is
`CORPUS_FILES` in `source_units.py:56-71`; its sequence becomes persisted global
reading order. Runtime readers use that order, so the known contextual Animals
read places its own passages before governing rules. Disposition: correct the
cross-file permutation under the existing Owner Decision.

**RO-2: now characterized; the same defect family needs the same correction.**
The bounded comparison covers every corpus file. Beyond Animals, the present
sequence puts Playing the Game after Monsters, Origins before Classes,
Equipment before Feats, Spells after Monsters, and the Glossary after the
Toolbox and Magic Items. Monsters rules already precede Monsters A-Z, and Legal
Information remains first. Disposition: apply the complete table above once,
rather than repeatedly moving individual files. No within-file correction is
proposed, and no new semantic or ownership judgment was made.

## What the correction changes

A read-only in-memory permutation of the pinned source verified exactly
**10,464 units and 2,877 containers** on both sides. Matching units by file and
compact character range preserves every field except `file_index`; content,
headings, offsets, leaf types and container relationships are identical.
Containers match exactly by identity and payload. Of the units, 10,459 move to
a different global position, and 10,292 change file index. Source units are not
the oracle's classification spans or review units; these counts have different
meanings. No release was built, no citations recomputed, and no oracle recorded.

| Surface | Consequence and evidence |
| --- | --- |
| Qualified source bytes and manifest | Preserve exactly. The 14-file membership stays the same; only build order changes. Existing PDF qualification remains reusable. |
| Unit content and boundaries | Verified unchanged by the permutation probe. Within-rule, table and stat-block order is preserved. |
| Leaf/container/span identities | Container equality is verified. Leaf identity derives from file and compact offsets (`source_units.py:412-415`); span identity derives from leaf and range (`accounting.py:66-72`). Their preservation is expected and must be compared in the replacement build. |
| Official locators | Expected unchanged, not yet verified on a rebuilt release. Citation partitioning is per file (`source_citations.py:114-145`); compare old/new pages and locators keyed by stable source extent. |
| Release identity and persisted corpus | Must change. Ordered extraction files feed transform identity (`source_ledger.py:211-260`); `pipeline.py:216-224` derives a new config hash, package UUID and version. Global occurrence and file indices change, so ledger/bundle/persisted digests must be recomputed. |
| Chunk identities and retrieval | Every represented chunk is release-scoped (`transform.py:88-110`), so chunk IDs change with the package UUID. Replacement retrieval state must use that binding; old state cannot be relabeled or used as fallback. |
| 5d representation and references | Prose bindings name exact chunks; reference resolutions carry all six release-binding coordinates. These payloads need controlled rebinding and new identities even when semantic content is unchanged. |
| Acceptance | Current approvals remain evidence for the old release. Native acceptance refuses extending a different release (`acceptance.py:371-375`); publication also checks binding. Prepare and review an exact replacement candidate, then obtain exact Owner acceptance before recording it. Do not copy old approvals as if they authorize the new binding. |
| Runtime readers | Use the replacement release's persisted `occurrence_index` (`service.py:629-693`, `application.py:400-432`). Preserve selection, ownership, reference destinations and all deferred reader behavior. |

The previous [class spell-table replacement](issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py)
is evidence that this repository already handles changed-release proposals
through native acceptance. It is not a requirement to replay every historical
generator or reconstruct superseded intermediates. Claude should choose the
smallest native approach that preserves the accepted semantic payload and makes
all identity changes explicit and reviewable.

## Bounded implementation and proof

The next engineering deliverable is an **isolated order-only replacement
candidate**, with new release identity and an exact delta from the current
accepted artifact. Existing source qualification, semantic decisions, packet
reviews and unchanged regression assertions remain useful evidence. New
release-specific pins and changed-binding checks need fresh evidence.

The correction invalidates order-dependent identity and persistence evidence,
not the entire substantive source review. Required focused proof is:

- The full 14-file order matches the official sequence, without omitted or
  duplicated files. Existing consecutive-index tests do not prove this; add a
  focused chapter-order regression.
- Source bytes, unit membership, within-file order, leaf extents, ownership,
  semantic records, reference routes and destinations remain unchanged; compare
  locators explicitly. Explain every difference outside release binding,
  release-scoped chunk identity, reading coordinates and resulting hashes.
- The replacement stays schema 17 unless a concrete independent requirement
  appears. Compare the expected 24 batches, 1,835 records, 1,486 resolutions and
  zero findings through native validation; do not manufacture green counts.
- Fresh replacement persistence/reconstruction binds the new order and chunks,
  and rejects stale/mixed old-release state. Show an Animals contextual read with
  governing rules before its own passages, plus Monsters and representative
  cross-file controls. Reuse unaffected reader assertions rather than rerunning
  all historical packets.
- Publishability can be checked in isolated stores only as authorized by the
  candidate scope. Production publication/activation and the normal final
  delivery gates remain separate boundaries. Broad suites, coverage, expanded
  mypy and dependency repairs are not automatically started by this review.

The current oracle, approvals, candidate histories and evidence remain intact.
No corpus byte edits, hierarchy rewrite, semantic rereview campaign, reader
policy change, house-rule installation, shared-store write, staging, commit,
push, merge, publication or activation is part of preparing this review.

## Claude-ready candidate brief

Prepare an isolated order-only replacement candidate for CRD Issues 5c (#132)
and 5d (#137), under the 21 September restart decision and the exact retained
release-order Owner Decision linked above. Use the full official file sequence
in this review. The current accepted oracle is pinned above and must remain
unchanged until exact replacement acceptance and recording are authorized.

Preserve source bytes, all accepted semantics, scope, ownership, reference
routes/destinations and deferred policies. Reuse unaffected reviewed material.
Use native release and acceptance contracts to derive the replacement binding
and candidate; do not relabel the old release or treat its approvals as approval
of the new binding. Provide the exact old/new release pins, a concise delta,
semantic/locator equality evidence, zero-findings native validation, focused
persisted reader/order proof, and honest gate results. Stop with the exact
candidate ready for Codex review and Owner acceptance. No live recording,
publication, activation, shared-store write or unrelated cleanup.

## Evidence and limits

The [retained inspection evidence](issue-5c-release-order-review/evidence.json)
pins the actual source files, PDF, current oracle, HEAD and index, and includes
the permutation result. Inspection scripts, extracted PDF pages and three
rendered page images are under `../_sp/release-order-review/`. This is a source
order and binding-impact review, not new CI, a replacement build, or runtime
reverification. The existing final-ten runtime evidence remains as reported in
its recording review; it is not claimed as proof of the proposed new release.

Architecture Notes: **No drift from design principles.** The proposal implements
the existing consolidated-order decision; exact replacement acceptance and
publication/activation boundaries remain intact.
