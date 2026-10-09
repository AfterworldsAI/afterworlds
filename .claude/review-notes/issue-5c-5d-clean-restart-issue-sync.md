# External issue synchronization text — CRD Issue 5c/5d clean restart

**NOT POSTED.** Prepared locally under the operating boundary of the 21 September
2026 increment ("Prepare exact external issue synchronization text locally; do
not post it yet"). Post only on explicit Owner instruction. Two comments, one per
issue, verbatim below.

---

## Comment to post on #132 (CRD Issue 5c)

> **Owner Decision 2026-09-21 — clean restart. This issue's delivered corpus is quarantined.**
>
> The Owner has directed a clean restart of CRD Issues 5c and 5d rather than
> migration of the existing products. The decision is recorded in-repo at
> `docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md` so it is
> reviewable without a local-only dependency.
>
> What this means for this issue:
>
> - The delivered corpus release (`package_uuid 4458fa10-4a66-5e0e-9ecc-ea37530ad2b4`,
>   `release_version 5.2.1-corpus.36b786d8-fa2`) is **quarantined**. It is refused
>   at every seam that could make it active authority: slice selection,
>   `get_active_rule_slice`, package-reference resolution, release finalization,
>   the publication gate, verified operational load, vector publication and
>   verification, retrieval reindex, retrieval diagnostic fallback, generic
>   package ingestion, publication and by-id reads, the obsolete ingestion
>   command (`scripts/ingest_srd.py`), and the baseline reset
>   (`scripts/reset_corpus_baseline.py`), which refuse before they migrate a
>   database, open a store or delete a collection. The reset stays usable for the
>   replacement corpus; only quarantined releases are refused.
>   Finalization is additionally keyed on the retired PDF-geometric transform
>   recipe, so reconfiguring an incidental input such as the embedding model label
>   mints a different package identity but does not reopen the path. Refusal
>   raises a typed error rather than returning an empty result, so no caller can
>   read it as "nothing configured" and fall back.
> - Existing acceptance, source identities, batch boundaries, provenance and typed
>   content are **not inherited authority** for the replacement. The earlier
>   recommendation to retain accepted semantics through provenance regeneration is
>   superseded.
> - Nothing is deleted. Git history is the retention mechanism; retirement of the
>   superseded work is a later increment, sequenced after the replacement exists.
> - ADR-005c and its 2026-08-03 operational-reliability amendment now carry
>   supersession banners pointing at the Owner Decision. The architectural
>   requirements they state are not withdrawn; the products built under them are.
>
> Replacement work in progress: one pinned Afterworlds-controlled copy of
> `downfallx/dnd-5e-srd-markdown` at commit `1b4b99dc`, held **provisional**, is
> being qualified against the official WotC SRD 5.2.1 PDF (sha256
> `8974902d…bc5e3d87`, 364 pages), which remains the ultimate source authority.
> A full-document comparison pass has run: 96.4% character-window coverage over
> all 364 pages, 99.1% excluding the licence page and the table of contents, with
> 269 of 364 pages matching completely. Coverage, every discrepancy excerpt, and
> the explicit list of what was **not** checked are committed at
> `docs/architecture/issue-5c-5d-community-source-coverage.json`, with the
> implementation state at `docs/architecture/issue-5c-5d-clean-restart.md`.
>
> **This is not qualification.** Table row and column association — including
> `colspan` cells, empty cells and repeated ability-grid headers — is not checked
> by that pass at all, and no region is cleared by it. The structural pass is the
> gating work before the Markdown can become the canonical machine-readable
> representation of the document, and it would not thereby become an independent
> rules authority in any case.

---

## Comment to post on #137 (CRD Issue 5d)

> **Owner Decision 2026-09-21 — clean restart. The accepted 5d authority is quarantined.**
>
> The Owner has directed that 5d be constructed anew rather than extended. The
> decision is recorded in-repo at
> `docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md`.
>
> What this means for this issue:
>
> - The committed accepted authority (`projection_uuid
>   82c75aad-b294-5b2e-a188-128cdcbada09`, artifact
>   `oracles/srd-5-2-1-corpus-36b786d8-fa2.json`) is **quarantined**: committed
>   accepted-inputs resolution, active-projection resolution, activation, and
>   publication all refuse it, as does the bound view of the 5c corpus it depends
>   on.
> - The nine accepted batches (`conditions-1`, `hazards-1`, `actions-1`,
>   `attitudes-1`, `areas-of-effect-1`, `cover-1`, `speed-1`,
>   `proficiency-destinations-1`, `proficiency-1`) are **not preserved as
>   inherited authority**. The 2026-09-16 practical-reliability amendment's
>   statement that the accepted batches are preserved is superseded on that point;
>   its review policy — section/entry/table review, use-driven field selection,
>   exact governing prose, shared batch tooling — is not withdrawn.
> - The old accepted 5d meaning was **not** independently proved universally
>   wrong. It is being replaced because the Owner prefers the confidence of fresh
>   construction, not because a defect was demonstrated in it.
> - Reading the committed artifact by path is still permitted; it is reference
>   material. Only authority paths refuse. `load_accepted_inputs` and
>   `candidate_from_accepted_inputs` are deliberately unguarded and the boundary
>   is covered by inverted tests.
>
> Code-owned deterministic and trust-relevant responsibilities are unchanged:
> dice generation, hidden/backend-visible rolls, roll-result preservation and
> `gm_cheating = off` enforcement stay code-owned (invariant 10), and the Rules
> Package remains mechanical canon distinct from the Story Bible (invariant 8).
> Campaign version stability, house-rule precedence, and the separation of source
> from interpretation are preserved by the restart, not relaxed by it. Unrelated
> custom Rules Packages and story-memory functionality are untouched: refusal is
> keyed to the specific quarantined identities and content digests.
>
> No fresh semantic content has been accepted, and none will be authored until
> the source qualification the restart depends on is complete. Implementation
> state: `docs/architecture/issue-5c-5d-clean-restart.md`.

---

## Not included, deliberately

- No issue is closed, and neither comment requests closure.
- Neither comment claims the community source is qualified, or that table
  structure was verified.
- No PR is referenced, because none is open for this work.
