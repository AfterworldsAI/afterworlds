# CRD Issue 5d — batch `actions-1`, representation schema 6

Proposal preparation checkpoint. **Nothing here is accepted, published, activated,
retired or merged.** `accept_proposal` was not called. The frozen review prior and
the live accepted oracle are unchanged; both were verified before and after the run.

Branch `feature/issue-5d-actions-1`, head at authoring time `2621ef5`.

## 1. Artifacts

| Artifact | SHA-256 |
| --- | --- |
| `.claude/review-notes/issue-5d-actions-1-schema6-PROPOSAL.json` | `88675ae05a9dc336ca5ee46c70aaeee7b01dd820a1d99219bcf98c70fd2fcdbd` |
| `.claude/review-notes/issue-5d-actions-1-schema6-audit.json` | `1588ee515e7b5d77d31d929837647bb2547bf5e47af73e6dc5dc15181844a636` |
| `.claude/review-notes/issue-5d-actions-1-schema6-PROPOSAL-generator.py` | the executable derivation of both |

Proposal identity: **`b7420dae2deea72d75991615cad397881da4929c0d80266a8a20737a8fb660f2`**.

The identity is **not pinned** in the generator. Pinning it would make the script
assert its own output rather than derive it; the generator asserts only that the
identity differs from the superseded schema-1 proposal
`ff30c25a568836b3e44b60b692a713aa8da90cca3ffc8326fbc8adc0ff541bf0`, which it does.

Both files are LF-only (asserted: no CR byte). Regeneration reproducibility is
proved inside the run: the parent re-executes itself in a separate interpreter
under `ACTIONS6_RERUN=1` and compares the final bytes of both artifacts, and the
child's identity line must appear in its stdout. `deterministic True`.

The superseded schema-1 payload was **not** an input. It was neither imported,
edited, translated, restamped, cloned nor read as generator input; its identity is
recorded as historical evidence only. Every span, cut and text in this proposal is
re-derived from the bound source through `build_candidate`.

## 2. Source binding — six values verified live

| Value | |
| --- | --- |
| package UUID | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
| release | `5.2.1-corpus.36b786d8-fa2` |
| authoritative source SHA-256 | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| transform/config hash | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` |
| bundle root hash | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` |
| persisted-corpus digest | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` |

The first five are re-derived from the PDF by the run and asserted. The sixth is
carried from the 5c release record; it is not re-derivable from the candidate and
is recorded as a carried value, not as a computed one.

Schema pin: `5d-representation-schema-6` /
`0e4b4378bf1409ed3ffbbec61a279430689ce4a0d3b70b1b3e9d886f66ae20b7`, asserted
against `representation_schema_hash()` at run time.
Policy: `5d-semantic-policy-1` /
`e6363968d6ee8ec288e6c7e3382907a1afd8bf2aad0b18e153aec439b5aa9454`.

## 3. The action boundary, in full

13 records · **94** container leaves · **92** represented · **2** policy exclusions.

The two exclusions are the running header/footer leaves, not the headings:

- `056d861c…` p187 `System Reference Document 5.2.1 187` (Ready)
- `891e92d8…` p183 `System Reference Document 5.2.1 183` (Help)

The 13 heading leaves **are** represented, each carrying whole-leaf supporting
authority, exactly as in the accepted hazards-1 batch. Each entry's leaf set is
reconstructed byte-for-byte from its span partition and asserted; no leaf is
partially claimed and none is silently dropped.

Records: `glossary.action`, `action.attack`, `action.dash`, `action.disengage`,
`action.dodge`, `action.help`, `action.hide`, `action.influence`, `action.magic`,
`action.ready`, `action.search`, `action.study`, `action.utilize` — all
`GLOSSARY_RULE`, the twelve named actions parented to the umbrella.

Emitted: **177 spans** (78 substantive, 99 supporting authority, 0 non-mechanical,
0 unresolved) · **37 components** · **47 facts** (34 component-grain + 13
option-grain) · **24 prose bindings** (5 option-grain) · **17 references**
(2 record-owned) · **191 provenance edges** (14 contextual extras) ·
0 relationships.

## 4. Obligation closure

78 distinct obligation IDs from `issue-5d-actions-1-obligation-coordinates.json`,
**all discharged, 0 open, 0 unknown**. The I-series runs I1–I7, I9, I10 — there is
no I8 in the source ledger, and the generator asserts the count is 78 so a silent
renumbering would fail the run.

## 5. Substantive judgment changes from discovery

Stated as reasons. The discovery ledger was a first pass over the source and is
evidence, not a target; its counts are not treated as quotas.

- **JC-1 — reference `source_text` is the bare name.** The checkpoint wrote
  `"Speed."` / `"Concentration."`. Every one of the accepted prior's 22 references
  carries a bare name; a citation names a rule, and the punctuation belongs to the
  sentence.
- **JC-2 — the Influence/Search/Study table cells are supporting authority,** not
  prose bindings. The Owner's clarification that suggested skill/ability tables are
  exemplars and guidance, read against SUPPORTING_AUTHORITY's own definition. The
  governing sentences J7, J8, M3, N2 keep their bindings, so nothing that governs
  play was demoted; what moved is the exemplar rows those sentences point at.
- **JC-3 — J10 is prose-bound,** not a typed ROLL_OUTCOME gate. A ROLL_OUTCOME
  applicability requires exactly one roll-establishing fact in scope; a component
  that publishes no fact establishes none, so the gate would name the outcome of
  nothing. The effect — a monster doing as urged — is unbounded anyway.
- **JC-4 — B2 is supporting authority, not a cross-reference.** "with a weapon or an
  Unarmed Strike" names no glossary record this batch can resolve; it identifies and
  limits the instrument of the attack the component already grants.
- **JC-5 — Help carries one reason for both arms** (see residue R-help-reason).
- **JC-6 — Dodge is three components, including a standalone duration.** One
  duration governs two benefits; duplicating the duration fact across both would put
  an equivalent fact of two components on one substantive span, which
  `_validate_duplicated_fact_authority` refuses. Only the attack benefit carries a
  prose condition, and a component holds one reason.
- **JC-7 — Study splits into `study_check` and `study_areas`.** N1's effect space is
  unbounded (`open_ended_effect`); N2 is a judgement call about which skill applies
  (`subjective_judgment`). Two reasons cannot live in one component.
- **JC-8 — Utilize is fully STRUCTURED.** "when an object requires an action for its
  use" is exactly `ActivationCostEligibilityFact` and "you take the Utilize action"
  is exactly `ActionEconomyFact`. Nothing in the entry is irreducible; a reason code
  invented to justify a binding would be false.
- **JC-9 — the 13 headings are represented, not policy-excluded.** Re-derived from
  `exclusion_reason_for` against the bound ledger; the exclusions are the two
  running header/footer leaves named in §3.

## 6. Disclosed limits and residue

**L-1 — `action.attack/attack_equipment_change`, the equipment cross product.**
`EquipmentChangeFact` carries change and timing in one fact, while the source states
the two axes in two separate sentences, so the option set is the cross product
(equip/unequip × before/after) and no single span states any one of the four
combinations. Accounted for by claiming each axis sentence PRIMARY by the owning
component — the element that holds the choice — and giving each of the four option
facts a CONTEXTUAL edge on both axis spans. Nothing invented, nothing dropped; what
is disclosed is that the typed shape is more specific than any one span. Not a stop:
the cross product is entailed by the two sentences read together, so no schema
meaning is changed.

**R-help-reason — `action.help/help_choice`.** H5 ("The GM has final say on whether
your assistance is possible") would take `gamemaster_latitude` on its own; the
component carries `contextual_applicability`, which both other bindings need. An
option set cannot span components and a component holds exactly one reason. The two
alternatives were rejected on the merits: demoting H5 to supporting authority would
be false (it is substantive), and a sibling PROSE_BOUND component would falsely
claim to govern both arms, since no `ApplicabilityKind` can scope a component to one
arm of a choice. Carried as residue. `contextual_applicability` is true of H5 and
only less specific — a coarsening of a label, not a false statement about the rule,
so the stop clause does not apply.

## 7. Validation

Standalone and merged were both run with the registered lift
(`5d-lift-schema-5-to-6`, one step 5→6, 6 collections verified).

| Column | Findings |
| --- | --- |
| partition | 0 |
| structural | 0 |
| schema-6 component rules | 0 |
| reason codes | 0 |
| schema binding | 0 |
| representation (standalone) | 5 |
| representation (merged with accepted prior) | 5 |

The 5 findings are identical in both columns and are exactly the expected
cross-batch missing targets, each asserted by set equality against a declared
expectation rather than by count:

- `glossary.speed` — cited by `action.dash` (record-owned, `Speed`)
- `glossary.concentration` — cited by `action.magic` (record-owned, `Concentration`)
- `attitude.indifferent`, `attitude.friendly`, `attitude.hostile` — cited by
  `action.influence/influence_check`

None of the five exists in the 22-record prior.

> **This batch is not publishable on its own.** `publishable_alone: false` in the
> audit. Zero validator findings would be necessary and insufficient — and this
> batch does not even have zero. It is a complete, internally consistent actions-1
> proposal whose five outbound citations await the batches that define their
> targets. It must not be described as a publishable partial batch.

## 8. Preservation evidence

- **Frozen review prior** `tests/ingestion/mechanical/data/accepted_prior_conditions_1_hazards_1.json`
  — content SHA-256 `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7`
  and Git blob `6e65533f4a3523aba3d60cfc3c274ab22e66b59a`, identical before and
  after the run. Batches `['conditions-1','hazards-1']`, schema
  `5d-representation-schema-5`, 22 records, 281 spans, 69 components — all asserted.
- **Live accepted oracle** — read as a sentinel only, never as an input; digest
  unchanged across the run.
- **Zero overlap** with the accepted collections: span overlap `[]`, leaf overlap
  `[]`, and collection overlap 0 for records, components, prose bindings,
  relationships, references and provenance.
- **Zero movement** — every accepted record, span and edge is byte-identical in the
  merged view; the merge adds and never rewrites.
- **Retained artifacts** — the 9 pre-existing untracked actions-1 review notes were
  hashed before and after the run and are unchanged. The run writes exactly two
  files, both named for actions-1 and schema 6.
- **Ownership** — 78 substantive spans, each with exactly one primary claimant
  (component 9, fact 43, fact qualifier 2, prose binding 24); 99 supporting spans,
  none carrying a primary claim; 0 prose bindings over supporting text; 0 spans with
  no claim at all.

## 9. Source and semantic proof limits

What is machine-proved: the cuts, the partition, the six binding values, the schema
pin, the structural and component rules, obligation closure, disjointness from the
accepted prior, and byte-level regeneration.

What is **not** machine-proved and remains for independent review: that each typed
fact means what the sentence it is bound to means, that each irreducibility reason is
the right member of the six-code catalog, and that the component seams cut the
entries where the source cuts them. `fact_invariant_violations` proves a fact is
well-formed, never that it is the correct reading. The exemplar tables (JC-2) and the
Help reason (R-help-reason) are the two places where a reviewer disagreeing with the
reading would change the artifact, and both are named here rather than buried.

## 10. Architecture Notes

No drift from design principles. This is proposal preparation under CRD Issue 5d and
ADR-005d against the bound CRD Issue 5c source; it adds no production code path,
changes no accepted contract, and touches no runtime module. The representation
schema is consumed at its pinned version and hash — no schema meaning was changed to
make the batch author cleanly. Where the schema was more specific than the source
(L-1) or less specific than the source (R-help-reason), the gap is disclosed rather
than closed by editing the schema or the reading.

Rules Package / Story Bible separation is untouched: this is mechanical canon
authored through the mechanical ingestion path only.

## 11. Stop

Stopping at the completed engineering handoff for independent review, as instructed.
Not done, and not to be done without a further Owner authorization: `accept_proposal`,
publish, activate, retire, merge, closing #137, changing 5c or downstream ownership.
The branch stays local — no push, no PR.
