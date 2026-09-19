"""``proficiency-destinations-1`` is the four destinations, proposed — CRD Issue 5d.

``proficiency-1`` prints four pointers: *Challenge Rating*, *Expertise*, the
*Skills table* and *Actions*. This batch is the source review that gives them
somewhere to land, and it is **proposed, not accepted** — nothing here accepts
it, and the in-memory acceptance below is evidence that it is structurally
acceptable through the production path, asserted to write nothing.

Four review units in one batch, because the four destinations are what one
Proficiency reference set needs and reviewing them apart would have meant four
acceptances of one semantic boundary:

* two Rules Glossary entries, ``glossary.challenge_rating`` and
  ``glossary.expertise``, reviewed as ``ENTRY`` units;
* the Skills table, reviewed as a ``TABLE`` unit with **one expected rule per
  printed row** — an omitted row leaves a named span unbound and is reported
  rather than absorbed into a surviving row's evidence; and
* the *Actions* section of Playing the Game, reviewed as a ``SECTION`` unit.
  The Skills table is printed inside 5c's ``Actions`` container, so the table's
  leaves are excluded from this unit and reviewed by the ``TABLE`` unit instead;
  the container placement is 5c's, reported and not repaired here.

What is pinned, and why:

* the bytes derive the identity a reviewer would be shown, under schema 15 and
  the declared policy — no restamp of anything already accepted;
* the exact unit shape: kind, leaf count and expected-rule count for each of
  the four, so a unit that quietly shrank to a greener count fails here;
* the twelve Action-table links resolve to the **same** records the accepted
  ``glossary.action`` entry already cites for the same printed words. That
  comparison is against the committed accepted artifact, which is what makes
  them reviewed destinations rather than plausible keys;
* only two typed facts, both ``ActionAllowanceFact``. The section's other
  clauses are carried as exact governing prose under an
  ``ExpectedRule(fact_family=None)``, because no accepted fact family states
  what they say;
* every explicit citation these units print, including the four whose
  destinations no batch has minted — *Stat Block*, *Combat Encounters*, *Combat*
  and *Opportunity Attack*. Those carry an empty target and are **reported** as
  ``unresolved reference``; a citation the source states cannot become
  undetectable because its destination has not been reviewed yet;
* which reason each prose clause states, and that no clause is labelled
  irreducible for lacking a schema shape; and
* the mutations that matter for a table-shaped review: dropping one Skills row's
  ability cell, and dropping one Action row's name cell, are each reported
  against the component that lost them.

The four destinations this batch mints are not in the committed accepted
artifact, so its own references to ``action.*`` and ``play.proficiency`` are
reported as ``unknown target record`` here. That those close when the accepted
authority, this batch and the revised ``proficiency-1`` are merged is proved in
``test_proficiency_references_resolve.py``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.bound_corpus import (
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.policy import SEMANTIC_POLICY_VERSION
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    PROPOSAL_SCHEMA_VERSION_2,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ActionAllowanceFact,
    ActionCost,
    AllowanceScope,
    ComponentHandling,
    RecordKind,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import validate_representation

REVIEW_NOTES = pathlib.Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
PROPOSAL_PATH = REVIEW_NOTES / "issue-5d-batch-proficiency-destinations-1-PROPOSAL.json"
COMMITTED_ARTIFACT = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"

#: The identity the review packet reports and a reviewer would be shown.
PROPOSAL_IDENTITY = "723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e"  # noqa: E501  # pragma: allowlist secret

CR = "glossary.challenge_rating"
EXP = "glossary.expertise"
SKILLS = "play.skills"
ACTIONS = "play.actions"
PROFICIENCY = "play.proficiency"

GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"
PLAYING_SCOPE = "srd-5.2.1/playing-the-game"
#: Challenge Rating's *"Gameplay Toolbox" ("Combat Encounters")* citation is
#: reviewed in the *Gameplay Toolbox* space, which no accepted batch has used
#: yet. A scope is a review space, not a record key.
TOOLBOX_SCOPE = "srd-5.2.1/gameplay-toolbox"

ACTIONS_UNIT = "proficiency-destinations-1-actions-section"
SKILLS_UNIT = "proficiency-destinations-1-skills-table"

#: ``semantic_key -> kind``. The two glossary entries are glossary rules and the
#: two Playing the Game records are general rules, which is the distinction the
#: Rules Glossary's own entries already draw.
EXPECTED_RECORDS = {
    CR: RecordKind.GLOSSARY_RULE,
    EXP: RecordKind.GLOSSARY_RULE,
    SKILLS: RecordKind.GENERAL_RULE,
    ACTIONS: RecordKind.GENERAL_RULE,
}

#: ``unit_id -> (kind, leaves, expected rules)``. Exact counts rather than "at
#: least": the failure this catches is a unit that dropped a clause or a row and
#: still reported clean, which is indistinguishable from a smaller review.
EXPECTED_UNITS = {
    "proficiency-destinations-1-challenge-rating": (ReviewUnitKind.ENTRY, 7, 3),
    "proficiency-destinations-1-expertise": (ReviewUnitKind.ENTRY, 4, 3),
    SKILLS_UNIT: (ReviewUnitKind.TABLE, 58, 18),
    ACTIONS_UNIT: (ReviewUnitKind.SECTION, 38, 26),
}

#: The twelve action names the table prints, in printed order.
ACTION_NAMES = (
    "Attack",
    "Dash",
    "Disengage",
    "Dodge",
    "Help",
    "Hide",
    "Influence",
    "Magic",
    "Ready",
    "Search",
    "Study",
    "Utilize",
)

#: The four explicit citations in these units whose destinations no batch has
#: minted: ``(from_record, source_text, scope)``. Each is an obligation this
#: batch opens and cannot close — the source names a real heading, and guessing
#: its eventual record key is what an empty target exists to avoid. They are
#: record-owned on the Expertise pointer's terms: the entry or the section states
#: the citation and no one of its rule components does.
OUTSTANDING_CITATIONS = (
    (CR, "Stat Block", GLOSSARY_SCOPE),
    (CR, "Combat Encounters", TOOLBOX_SCOPE),
    (ACTIONS, "Combat", PLAYING_SCOPE),
    (ACTIONS, "Opportunity Attack", PLAYING_SCOPE),
)

#: Every link this batch authors: the table's twelve action names, the
#: *Proficiency* pointer the Expertise entry prints, and the four outstanding
#: citations. The record-owned ones — the entry or section as a whole cites
#: them — have an empty component key, and an outstanding one has an empty
#: target as well.
EXPECTED_REFERENCES = (
    {
        (ACTIONS, "action_table", name, GLOSSARY_SCOPE, f"action.{name.lower()}")
        for name in ACTION_NAMES
    }
    | {(EXP, "", "Proficiency", PLAYING_SCOPE, PROFICIENCY)}
    | {(record, "", text, scope, "") for record, text, scope in OUTSTANDING_CITATIONS}
)

#: The exact standalone report, seventeen findings. Thirteen destinations that
#: exist in accepted or in-flight data but not in *this* draft, and the four
#: citations whose destinations exist nowhere yet. An eighteenth finding of any
#: kind, or a link quietly losing its destination — or an outstanding citation
#: quietly disappearing so the report looks shorter — fails here.
EXPECTED_FINDINGS = tuple(
    sorted(
        [
            f"reference {PLAYING_SCOPE}:'Proficiency': unknown target record "
            f"{PROFICIENCY}"
        ]
        + [
            f"reference {GLOSSARY_SCOPE}:{name!r}: unknown target record "
            f"action.{name.lower()}"
            for name in ACTION_NAMES
        ]
        + [
            f"reference {scope}:{text!r}: unresolved reference"
            for _record, text, scope in OUTSTANDING_CITATIONS
        ]
    )
)


def _proposal():  # type: ignore[no-untyped-def]
    return load_proposal(PROPOSAL_PATH)


def _ledger(proposal) -> ClassificationLedger:  # type: ignore[no-untyped-def]
    """The proposal's own spans, under the release and policy it declares."""
    return ClassificationLedger(
        package_uuid=proposal.binding.package_uuid,
        release_version=proposal.binding.release_version,
        policy_version=proposal.policy_version,
        policy_hash=proposal.policy_hash,
        spans=tuple(p.span for p in proposal.proposed_spans),
        batches=(),
        acceptances=(),
    )


def _corpus(proposal) -> BoundCorpusSnapshot:  # type: ignore[no-untyped-def]
    """A snapshot of the bound release over exactly the leaves this batch reads.

    Derived from the proposal rather than re-parsed from the PDF: 5c's own
    ``build_candidate`` is a full release parse, far too heavy for a test. Every
    binding of this batch covers the whole of the leaf it binds and each bound
    leaf is its own chunk — true of the generated artifact, asserted below —
    so giving each chunk the whole leaf reproduces the real extent rather than
    manufacturing one. That the untampered draft yields exactly
    :data:`EXPECTED_FINDINGS` is what shows the snapshot is neither inventing
    nor hiding a finding.
    """
    spans = [p.span for p in proposal.proposed_spans]
    leaf_lengths: dict[str, int] = {}
    for span in spans:
        leaf_lengths[span.leaf_id] = max(
            leaf_lengths.get(span.leaf_id, 0), span.char_end
        )
    leaf_of = {span.span_id: span.leaf_id for span in spans}
    edges = {
        (binding.chunk_id, leaf_of[binding.span_id]): ChunkCoverage(
            chunk_id=binding.chunk_id,
            leaf_id=leaf_of[binding.span_id],
            cover_start=0,
            cover_end=leaf_lengths[leaf_of[binding.span_id]],
            role="authoritative",
            projection_id="proficiency-destinations-1-proposal-test",
        )
        for binding in proposal.proposed_representation.prose_bindings
    }
    return BoundCorpusSnapshot(
        package_uuid=proposal.binding.package_uuid,
        release_version=proposal.binding.release_version,
        leaf_lengths=leaf_lengths,
        chunk_coverage=tuple(edges.values()),
    )


def _findings(proposal, draft) -> tuple[str, ...]:  # type: ignore[no-untyped-def]
    return tuple(
        sorted(validate_representation(draft, _ledger(proposal), _corpus(proposal)))
    )


def _unit(proposal, unit_id: str):  # type: ignore[no-untyped-def]
    (unit,) = [u for u in proposal.proposed_review_units if u.unit_id == unit_id]
    return unit


def _unit_findings(proposal, draft) -> list[str]:  # type: ignore[no-untyped-def]
    return review_unit_violations(
        proposal.proposed_review_units,
        draft,
        proposal.policy_version,
        tuple(p.span for p in proposal.proposed_spans),
    )


def _without_binding(draft, span_id: str):  # type: ignore[no-untyped-def]
    return dataclasses.replace(
        draft,
        prose_bindings=tuple(b for b in draft.prose_bindings if b.span_id != span_id),
    )


def test_the_proposal_derives_its_reviewed_identity_under_schema_fifteen() -> None:
    """A proposal nobody can reproduce is not evidence of what was reviewed."""
    proposal = _proposal()
    assert proposal_identity(proposal) == PROPOSAL_IDENTITY
    assert proposal.proposal_schema_version == PROPOSAL_SCHEMA_VERSION_2
    assert proposal.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert proposal.schema_hash == representation_schema_hash()
    assert proposal.policy_version == SEMANTIC_POLICY_VERSION
    # No schema change was needed for these four destinations: this batch
    # declares the current schema as-is, and reads the same bound release the
    # accepted authority was accepted against.
    prior = load_accepted_inputs(COMMITTED_ARTIFACT)
    assert proposal.binding == prior.oracle.binding


def test_nothing_in_this_proposal_is_accepted() -> None:
    """It is a proposal, and the records it mints are new to the corpus."""
    proposal = _proposal()
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    prior = load_accepted_inputs(COMMITTED_ARTIFACT)
    assert PROPOSAL_IDENTITY not in {b.proposal_identity for b in prior.batches}
    accepted_records = {r.semantic_key for r in prior.oracle.representation.records}
    assert accepted_records.isdisjoint(EXPECTED_RECORDS)
    # And nothing already accepted is restated: the spans are disjoint too, so
    # this batch cannot be re-reviewing source another batch owns.
    assert {p.span.span_id for p in proposal.proposed_spans}.isdisjoint(
        {s.span_id for s in prior.oracle.spans}
    )


def test_the_four_destinations_are_the_records_this_batch_mints() -> None:
    """Four records, two glossary entries and two Playing the Game rules."""
    proposal = _proposal()
    assert {
        r.semantic_key: r.kind for r in proposal.proposed_representation.records
    } == EXPECTED_RECORDS


def test_the_four_units_are_the_shape_the_source_was_reviewed_in() -> None:
    """Exact kind, membership and rule count, and coverage the draft satisfies."""
    proposal = _proposal()
    assert {
        u.unit_id: (u.kind, len(u.leaf_ids), len(u.expected_rules))
        for u in proposal.proposed_review_units
    } == EXPECTED_UNITS
    for unit in proposal.proposed_review_units:
        assert len(set(unit.leaf_ids)) == len(unit.leaf_ids)
    assert _unit_findings(proposal, proposal.proposed_representation) == []


def test_the_skills_table_is_reviewed_one_printed_row_at_a_time() -> None:
    """Eighteen rows, each naming the two cells that state the row's rule.

    A single rule over the whole table would let a dropped row be certified on
    a surviving row's evidence. The *Example Uses* column is illustrative, so it
    is accounted for as supporting authority rather than as a rule.
    """
    proposal = _proposal()
    unit = _unit(proposal, SKILLS_UNIT)
    assert unit.kind is ReviewUnitKind.TABLE
    assert len(unit.expected_rules) == 18
    assert {(r.record_key, r.component_key) for r in unit.expected_rules} == {
        (SKILLS, "skills_table")
    }
    assert {len(r.source_span_ids) for r in unit.expected_rules} == {2}
    assert {r.fact_family for r in unit.expected_rules} == {None}
    (supporting,) = unit.supporting_groups
    assert supporting.supports_record_key == SKILLS
    assert supporting.supports_component_key == "skills_table"
    # Caption, three header cells and one Example Uses cell per row.
    assert len(supporting.leaf_ids) == 1 + 3 + 18


def test_the_actions_section_types_only_the_two_allowances_it_states() -> None:
    """One Bonus Action and one Reaction per turn. Everything else is prose.

    The rest of the section is judgment, latitude, and reducible meaning with no
    identified code-owned use, so each is carried as exact governing prose under
    a rule with no family. Typing them would have invented a rule the source does
    not state; see
    :func:`test_the_prose_reasons_say_why_each_clause_is_prose` for why "no shape
    fits" is never recorded as irreducibility.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    facts = [
        (c.record_key, c.semantic_key, f)
        for c in draft.components
        for f in c.all_facts()
    ]
    assert [(rec, key, type(f)) for rec, key, f in facts] == [
        (ACTIONS, "bonus_action_allowance", ActionAllowanceFact),
        (ACTIONS, "reaction_allowance", ActionAllowanceFact),
    ]
    assert [(f.count, f.per, f.cost) for _r, _k, f in facts] == [
        (1, AllowanceScope.TURN, ActionCost.BONUS_ACTION),
        (1, AllowanceScope.TURN, ActionCost.REACTION),
    ]
    typed = {c.semantic_key for c in draft.components if c.all_facts()}
    assert {c.handling for c in draft.components if c.semantic_key in typed} == {
        ComponentHandling.MIXED
    }
    assert {c.handling for c in draft.components if c.semantic_key not in typed} == {
        ComponentHandling.PROSE_BOUND
    }


def test_the_prose_reasons_say_why_each_clause_is_prose() -> None:
    """Irreducible means irreducible, not "this schema has no shape for it".

    The closed catalog defines ``natural_language_exception`` as an exception that
    cannot be reduced without executable interpretation. A clause that states its
    exception's condition and consequence outright — Expertise's *"unless the
    bonus is doubled by another feature"* — or that defers to another rule's own
    text — *"unless the Reaction's description says otherwise"* — is reducible,
    and labelling it irreducible would make the catalog say something false about
    the source. Those keep the whole clause and the honest retention reason
    instead, which is also what the sibling ``act.bonus_timing`` already carried,
    so one shape does not get two reasons.

    The four irreducibility codes this batch does use each name a property of the
    printed sentence rather than a gap in the schema.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation

    assert {
        c.semantic_key: c.irreducibility_reason_code
        for c in draft.components
        if c.irreducibility_reason_code
    } == {
        "threat_comparison": "subjective_judgment",
        "encounter_circumstances": "contextual_applicability",
        "improvised_action_options": "open_ended_effect",
        "improvised_action_judgment": "gamemaster_latitude",
    }
    # Every other component states the retention reason, and no component and no
    # binding states both or neither.
    for c in draft.components:
        if c.handling is ComponentHandling.PROSE_BOUND or c.all_facts():
            assert bool(c.irreducibility_reason_code) != bool(
                c.prose_retention_reason_code
            ), c.semantic_key
    for b in draft.prose_bindings:
        assert bool(b.irreducibility_reason_code) != bool(
            b.prose_retention_reason_code
        ), b.span_id

    # The two corrected components: whole clause, one binding each, no facts
    # extracted from either, and the retention reason rather than a legacy code.
    corrected = {
        c.semantic_key: c
        for c in draft.components
        if c.semantic_key in ("expertise_doubling", "reaction_timing")
    }
    assert len(corrected) == 2
    for key, component in corrected.items():
        assert component.handling is ComponentHandling.PROSE_BOUND, key
        assert component.all_facts() == (), key
        assert component.irreducibility_reason_code is None, key
        assert component.prose_retention_reason_code == "no_identified_structured_use"
        bindings = [b for b in draft.prose_bindings if b.component_key == key]
        assert len(bindings) == 1, key


def test_the_action_table_links_resolve_where_the_accepted_glossary_says() -> None:
    """The twelve destinations are the accepted ones, not plausible keys.

    The Rules Glossary's ``Action`` entry is already accepted and already cites
    these twelve words. Reading its targets from the committed artifact, rather
    than writing twelve keys that look right, is what makes this batch's links
    reviewed destinations — and is why merging the two cannot make one printed
    word in one scope resolve two ways.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    assert {
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in draft.references
    } == EXPECTED_REFERENCES

    prior = load_accepted_inputs(COMMITTED_ARTIFACT)
    accepted = {
        (r.source_text, r.scope_key): r.target_record_key
        for r in prior.oracle.representation.references
        if r.from_record_key == "glossary.action"
        and r.from_component_key == "action_choice"
    }
    assert len(accepted) == len(ACTION_NAMES)
    assert {
        (r.source_text, r.scope_key): r.target_record_key
        for r in draft.references
        if r.from_record_key == ACTIONS and r.from_component_key == "action_table"
    } == accepted


def test_the_four_outstanding_citations_are_authored_as_unresolved() -> None:
    """A citation the source states, with no destination to name yet.

    The rule this replaces was "mint a reference only where the record already
    exists", which silently turned four printed citations into prose nobody could
    detect. What makes an obligation honest is that it is *reported*: exact scope,
    exact printed wording, provenance on the clause it is printed in, and an empty
    target until an explicit reviewed resolution supplies one — a later batch
    authoring the destination cannot close it, because a reference's key includes
    its target (``reference_resolution``, Owner Decision 2026-09-19). Guessing a
    key would be the other failure — a link that resolves by spelling coincidence.
    """
    proposal = _proposal()
    draft = proposal.proposed_representation
    outstanding = {
        (r.from_record_key, r.source_text, r.scope_key)
        for r in draft.references
        if not r.target_record_key
    }
    assert outstanding == set(OUTSTANDING_CITATIONS)

    by_citation = {(r.from_record_key, r.source_text): r for r in draft.references}
    spans = {p.span.span_id: p.span for p in proposal.proposed_spans}
    for record, text, _scope in OUTSTANDING_CITATIONS:
        ref = by_citation[(record, text)]
        # Record-owned, exactly like the Expertise pointer: no rule component of
        # the entry or section states the citation, the whole record does.
        assert ref.from_component_key == ""
        # And it carries provenance to the 5c subspan the citation is printed
        # in, so a reviewer can read the sentence the obligation came from.
        claims = [
            c
            for c in draft.provenance
            if c.target_kind.value == "reference"
            and c.target_key[2] == text
            and c.target_key[0] == record
        ]
        assert len(claims) == 1, (record, text, claims)
        assert claims[0].span_id in spans


def test_the_untampered_report_is_exactly_the_seventeen_open_obligations() -> None:
    """Thirteen links this draft does not carry, four with no destination yet."""
    proposal = _proposal()
    assert _findings(proposal, proposal.proposed_representation) == EXPECTED_FINDINGS
    assert sum("unresolved reference" in f for f in EXPECTED_FINDINGS) == 4
    # The premise of the fake snapshot: one chunk per bound leaf, covering the
    # whole leaf. If that stopped holding, the report above would be extent
    # noise rather than the reference report.
    draft = proposal.proposed_representation
    leaf_of = {p.span.span_id: p.span.leaf_id for p in proposal.proposed_spans}
    chunk_leaves: dict[str, set[str]] = {}
    for binding in draft.prose_bindings:
        chunk_leaves.setdefault(binding.chunk_id, set()).add(leaf_of[binding.span_id])
    assert all(len(leaves) == 1 for leaves in chunk_leaves.values())


def test_dropping_one_skills_row_is_reported_against_the_table() -> None:
    """A row's ability cell is a named passage, not an optional one."""
    proposal = _proposal()
    draft = proposal.proposed_representation
    rule = _unit(proposal, SKILLS_UNIT).expected_rules[-1]
    _name_span, ability_span = rule.source_span_ids
    findings = _unit_findings(proposal, _without_binding(draft, ability_span))
    assert findings
    assert all(f"{SKILLS}/skills_table" in f for f in findings)
    assert all("binds no prose from" in f for f in findings)
    assert any(ability_span in f for f in findings)


def test_dropping_one_action_row_is_reported_against_the_table() -> None:
    """Twelve row rules, so an omitted action name cannot be absorbed."""
    proposal = _proposal()
    draft = proposal.proposed_representation
    rows = [
        r
        for r in _unit(proposal, ACTIONS_UNIT).expected_rules
        if r.component_key == "action_table" and len(r.source_span_ids) == 1
    ]
    # Twelve printed rows plus the clause that points at the table.
    assert len(rows) == 13
    (span_id,) = rows[0].source_span_ids
    findings = _unit_findings(proposal, _without_binding(draft, span_id))
    assert findings
    assert all(f"{ACTIONS}/action_table" in f for f in findings)
    assert any(span_id in f for f in findings)


def test_in_memory_acceptance_is_evidence_and_writes_nothing() -> None:
    """Structurally acceptable through the production path. Not an acceptance.

    ``accept_proposal`` returns an in-memory :class:`AcceptedInputs`; it has no
    output path and persists nothing. The digest comparison makes that claim
    checkable rather than trusted, and the obligation count is what a later gate
    would have to satisfy: four new per-record claims, none of the accepted
    forty-eight disturbed.
    """
    before = hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest()
    proposal = _proposal()
    prior = load_accepted_inputs(COMMITTED_ARTIFACT)

    accepted = accept_proposal(
        proposal,
        batch_id="proficiency-destinations-1-test-evidence-only",
        rule="every span and the four review units this proposal proposes",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="test-evidence-only",
        accepted_at="2026-09-17T00:00:00Z",
        prior=prior,
        resolved_review_units=tuple(sorted(EXPECTED_UNITS)),
    )

    assert accepted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert accepted.oracle.schema_hash == representation_schema_hash()
    assert len(accepted.batches) == len(prior.batches) + 1
    assert {u.unit_id for u in accepted.oracle.review_units} == set(EXPECTED_UNITS)

    before_obligations = {o.record_key for o in prior.oracle.obligations}
    after_obligations = {o.record_key for o in accepted.oracle.obligations}
    assert after_obligations - before_obligations == set(EXPECTED_RECORDS)
    assert before_obligations <= after_obligations
    assert {
        o.record_key: sorted(f.value for f in o.structured_fact_families)
        for o in accepted.oracle.obligations
        if o.record_key in EXPECTED_RECORDS
    } == {
        ACTIONS: [ActionAllowanceFact.FAMILY.value],
        SKILLS: [],
        CR: [],
        EXP: [],
    }

    assert hashlib.sha256(COMMITTED_ARTIFACT.read_bytes()).hexdigest() == before
