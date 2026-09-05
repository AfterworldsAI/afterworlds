# CRD Issue 5d — bounded sibling audit: stale accepted-scope status

**Defect family.** *A standing description of current production authority that was true of one batch
and was never re-read when a second batch was accepted.*

**Trigger.** Codex flagged five status-authority sites on PR #161 as `[OWNER DECISION]`. It is not
one: the Owner accepted `hazards-1` on 2026-09-03, the committed artifact holds both batches, and the
tests already assert that. What is left is documentation that has not caught up. Correcting a
description to match an authorized acceptance is a specification correction, not a new decision.

**Scope discipline.** This audit controls scope; it does not expand it. Nothing outside the sites
listed here changed, and the accepted-authority JSON, the proposal, the regeneration audit, the
acceptance timestamp and reviewer, the representation schema and the policy were not touched.

## The corrected status, stated once

* accepted batches: **`conditions-1` and `hazards-1`**;
* accepted authority: **22 records over 281 spans** — 15 conditions and 5 hazards, plus the glossary
  entry defining each list;
* the CRD Issue 5d corpus **remains incomplete**;
* batch **`actions-1` has not begun**;
* **nothing is published or activated**;
* the production release still returns **`INCOMPLETE`, not `ABSENT`** — the refusal is about
  coverage, not about absence.

## The search

`grep` over `*.py`, `*.md`, `*.toml`, `*.in`, `*.cfg`, `*.yml`, `*.yaml` for `conditions-1` /
`conditions_1`, and a second pass for the claim shapes that do not name the batch at all:
`only batch`, `16 records`, `185 spans`, `deliberately empty`, `empty of production`, `INCOMPLETE`,
`accepted authority`. Vendored `frontend/node_modules`, `venv/` and `.git/` excluded; the working
review notes under `.claude/review-notes/` for earlier batches are historical drafts, not repository
status claims.

**The distinction applied to every hit:** does this sentence describe *current production authority*,
or does it describe a *past state*, a *frozen fixture*, or *the content of one batch*? Only the first
is stale. A sentence that says "before `conditions-1` was accepted this returned `ABSENT`" is a
correct historical statement and rewriting it would destroy evidence.

## Claims about current production authority — patched

| # | site | stale text | correction |
|---|---|---|---|
| 1 | `docs/architecture/known_unknowns.md` §5d | batch `conditions-1` accepted; oracle "covers 15 conditions and the glossary entry defining them" | both batches, 22 records / 281 spans, `actions-1` not begun |
| 2 | `src/afterworlds/ingestion/mechanical/oracle.py` module docstring | "covering CRD Issue 5d batch ``conditions-1`` only" | both batches, 22 records / 281 spans, corpus still incomplete |
| 3 | `src/afterworlds/ingestion/mechanical/oracles/README.md` | "currently holding **batch `conditions-1` only**" | both batches; records how `hazards-1` extended the file rather than adding one |
| 4 | `src/afterworlds/ingestion/mechanical/publication.py` `publish_from_committed_oracle` | "it covers CRD Issue 5d batch ``conditions-1`` only" | both batches; `INCOMPLETE` for coverage, `actions-1` not begun |
| 5 | `pyproject.toml` `[tool.setuptools.package-data]` | "The directory is deliberately empty of production content today" | one production artifact ships; the glob must carry it or an install refuses `ABSENT` rather than `INCOMPLETE` |
| 6 | `MANIFEST.in` | "Empty of production content today" — the sibling of #5, found by the audit rather than by review | same correction, sdist wording |
| 7 | `tests/…/test_accepted_inputs.py:266` docstring | "batch ``conditions-1`` is accepted; nothing else is" — the summary line contradicted its own body, which already named `hazards-1`, and its own assertion | both batches |
| 8 | `tests/…/test_accepted_inputs.py` publication docstring | incomplete coverage attributed to `conditions-1` alone | both batches, with the counts |
| 9 | `tests/…/test_runtime_production_release.py` module docstring | "CRD Issue 5d batch ``conditions-1``" as the committed authority | both batches |

**#5 and #6 were stale before this PR.** "Deliberately empty of production content" expired when
`conditions-1` was accepted on 2026-08-23, not when `hazards-1` was. Recorded as *patched
(pre-existing, not introduced here)* rather than folded in with the `hazards-1` siblings, because a
disposition that misdates a defect is the same species of error this audit exists to catch.

## Claims about batch *content* that a reader would now check and find false — patched

The committed artifact carries **two** `ability_check` facts today, both from `hazards-1`. Two
sentences asserted the artifact holds none — and both are load-bearing, because "no element of that
family" is the legality condition for the registered schema 4 → 5 succession.

| # | site | disposition |
|---|---|---|
| 10 | `src/afterworlds/ingestion/mechanical/schema_lift.py` module docstring | **patched** — scoped to the content the lift was proved against, naming the frozen specimen, and stating that a later batch adding such a fact is not retroactive: a lift's legality is a claim about what it carried across |
| 11 | `src/afterworlds/ingestion/mechanical/representation.py` `AbilityCheckFact.context` | **patched** — "nothing already accepted moved when this axis was added"; `hazards-1`, reviewed under schema 5, states the axis outright |

A one-word `artifact` → `batch` swap would have under-fixed these. The sentence is an argument for
the registry row's legality, so a reader who checks the file today and finds an ability-check fact
must be able to see *why* that does not invalidate the succession.

## Inspected and left alone

| site | why it is not stale |
|---|---|
| `tests/…/test_oracle.py:79` | explicitly historical: "This asserted an empty directory **until** the Owner accepted `conditions-1`" |
| `tests/…/test_production_release.py:265` | explicitly historical, and already updated for both batches: "**Before** `conditions-1` was accepted this returned `ABSENT`… covers 22 records (15 conditions and 5 hazards…)" |
| `tests/…/test_committed_accepted_authority.py` | already describes two batches throughout |
| the eleven modules holding `legacy_conditions_1_unanchored_schema3.json` | frozen-fixture descriptions. The specimen *is* the single-batch, schema-3, unanchored form; saying so is accurate and must not be "corrected" |
| `projection.py:200,327`, `representation.py:5266`, `representation.py:6200,6334`, `acceptance.py:345`, `schema_lift.py:238,442` | claims about the **`conditions-1` content**'s identities — `"applies_when": null`, the fifteen references, the schema-3 review anchor, the empty lift evidence. All still true of that batch, and all are about identity stability rather than coverage |
| `representation.py:790,1433(scope),4942,4946` | schema-history statements about which version admitted what |

## Surfaced, not changed

**`docs/decisions/adr-005d-complete-typed-mechanical-authority.md:205-208`** — *"the committed
`conditions-1` artifact declares schema 3 and reaches schema 5 across two recorded crossings"*, with
the zero-movement figures 185 spans / 185 acceptances / 16 obligations. Present tense, and the
committed file now declares schema 5.

Left as it stands, deliberately. The sentence is the **legality argument for the registered
succession, evaluated at lift time**, not a claim about today's production coverage — the same shape
as #10 and #11, but sited in an accepted ADR. `CLAUDE.md` puts accepted ADRs above standing
repository guidance, and amending an accepted Decision's text is a reconciliation requiring its own
authority, not a documentation cleanup folded into a Codex remediation. **Disposition: out of scope —
surfaced here rather than silently resolved.** If the Owner wants the ADR to carry a
post-acceptance note, that is a one-line amendment in its own change.

## Dispositions

**11 patched · 7 inspected and already accurate · 1 out of scope (surfaced) · 0 Known Unknowns ·
0 owner decisions needed.**

No test assertion was weakened or deleted, no pinned identity moved, and no runtime behaviour
changed: every patch in this audit is documentation, comment, or docstring text. The accepted
artifact, the proposal, the regeneration audit and the frozen fixture are byte-identical throughout.

**No Owner Decision was required.** `hazards-1` acceptance was already authorized and already
performed; these sites were describing a state the repository had left behind.
