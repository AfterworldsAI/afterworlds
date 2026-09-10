"""Ready's choice, provenance-mapped to its own printed coordinates.

``test_schema_6_source_compositions`` composes ``Ready`` on the **fixture**
record: a 40-character spell leaf partitioned as many ways as the composition
needs, and a 30-character prose leaf split into clauses. That demonstrates the
*shape* — an exhaustive choice, its option-scoped prose, and the views it
reaches — and it deliberately says nothing about where any of it is printed.

This module answers the different question: **what does the real source
actually support?** Every leaf id, leaf length, character extent and printed
string below is transcribed from the committed evidence artifact
``.claude/review-notes/issue-5d-actions-1-obligation-coordinates.json``, which
``issue-5d-actions-1-OBLIGATION-COORDINATES.py`` derives from the pinned SRD
5.2.1 PDF. Nothing here is sized to make a count come out.

``test_the_transcription_equals_the_pinned_source_evidence`` reads that artifact
back and compares every literal to it — leaf ids, leaf lengths, extents and
printed strings — and checks the artifact's own
``authoritative_source_hash`` against the pinned source digest, so the
comparison is tied to the pinned PDF rather than to any regeneration. Length
checks alone were not enough: they pass for any same-length paraphrase.

What the source states, and where:

* **L2** ``af20f466…[125:200)`` — *"which lets you act by taking a Reaction
  before the start of your next turn."*
* **L4** ``af20f466…[277:405)`` — *"Then, you choose the action you will take
  in response to that trigger, or you choose to move up to your Speed in
  response to it."*
* **L6** ``1022361f…[97:211)`` — *"When the trigger occurs, you can either
  take your Reaction right after the trigger finishes or ignore the trigger."*

**Why the two arms' cost edges are contextual on L2.** ``ProvenanceRole``
distinguishes whether a span *states* a claim or *merely supports* it, so the
role has to follow from the cited span's own content — L2's — and not from what
some other clause omits. L2 says *"lets you act by taking a Reaction"*: it
states the slot **once, for the whole readied response**, and
``ActionAllowanceFact(count=1, per=OWNING_EFFECT, cost=REACTION)`` is that
statement with its count and its owning-effect scope intact. That is L2's
primary owner.

``ActionEconomyFact(REACTION)`` on an arm asserts something L2 never scopes:
that *this alternative* is what spends the slot. L2 makes each arm's copy true
without stating it — the docstring's "merely supports it" — so the two copies
carry contextual edges to the span that supports them. They are two copies of
one printed cost, restated per arm only because a component is a conjunction or
a choice and never both, and so has no position for a cost the arms share.

The rest of the contract is what it has always been: every authoritative
element carries at least one admissible edge *of any role*, and every
substantive span carries exactly one **primary** owner. Nothing direct is
relabelled — L4's own two statements keep primary ownership of the text that
prints them, and L2's grant keeps primary ownership of L2. (L4 also happens to
print no Reaction at all; that is a true observation about the source, and it is
not what decides the role.)

The one partition is at the printed ``or``, computed from the sentence rather
than written down, so it cannot drift into an arbitrary offset chosen to make
a claim fit:

* **L4a** ``af20f466…[277:348)`` — *"Then, you choose the action you will take
  in response to that trigger, "*. Primary owner: arm 1's option-scoped prose
  binding.
* **L4b** ``af20f466…[348:405)`` — *"or you choose to move up to your Speed in
  response to it."* Primary owner: arm 2's ``MovementAllowanceFact(OWN_SPEED)``.

Four spans, four primary owners, two contextual edges. Arm 2 carries no prose
binding, because nothing in its clause is left untyped.

**Limits of this proof, stated so it is not read for more than it proves.**

* Leaf ids, leaf lengths, extents and printed text are checked against the
  pinned artifact. **Chunk ids are local to this module**: a prose binding
  resolves through ``covers_span``, which needs a projection edge, and the real
  5c chunk ids for these leaves are not in the artifact — deriving them means
  rebuilding the corpus from the PDF, which is outside a unit test. Coverage is
  stated as one chunk per whole leaf, which is what the SRD 5.2.1 projection
  does everywhere, but the identifiers are not the release's own. Codex
  substituted the release's real projection chunks out of band and validation
  and the GameMaster view still passed; that corroboration is external to this
  module and is recorded rather than reproduced here.
* The ledger carries the **four spans this demonstration claims**, not
  ``Ready``'s whole partition. Both leaves are fully enumerated in the artifact
  (11 obligation spans, 9 single-character gaps, 451 + 639 characters); every
  substantive span needs a primary owner, so a ledger holding all of them would
  require the whole record encoded. That is the eventual proposal's work.
* This module is still a **demonstration against the existing contract**, not
  a proposal and not an acceptance. ``actions-1`` has since been accepted, from
  a proposal reviewed under schema 7 — nothing here was any part of that review,
  and the fixtures below are local to this module rather than read out of the
  committed artifact.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.representation import (
    ActionCost,
    ActionEconomyFact,
    AllowanceScope,
    ComponentDraft,
    ComponentOption,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    fact_key,
    option_set_violations,
    prose_binding_target_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    _base_records,
)
from afterworlds.services.rules_authority.binding import RulesPackageBinding
from afterworlds.services.rules_authority.views import (
    build_gamemaster_view,
    build_typed_view,
)
from tests.ingestion.mechanical.conftest import (
    PACKAGE_UUID,
    RELEASE_BINDING,
    RELEASE_VERSION,
    bound_corpus,
    build_ledger,
    candidate_of,
    coverage,
)
from tests.ingestion.mechanical.test_schema_6_actions_1_source_cases import CASES

# ---------------------------------------------------------------------------
# The accepted source coordinates, and the pinned evidence they are checked at
# ---------------------------------------------------------------------------

#: The committed discovery evidence.
#: ``issue-5d-actions-1-OBLIGATION-COORDINATES.py`` derives it from the pinned
#: SRD PDF through the real 5c pipeline, and fails loudly if a quoted phrase is
#: not present verbatim in the leaf it claims — so it is independent of the
#: literals transcribed below.
EVIDENCE_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-actions-1-obligation-coordinates.json"
)

#: The pinned source the artifact must have been derived from. Without this the
#: comparison would only prove the transcription matches *some* regeneration.
#: Not a credential: it is the published SRD 5.2.1 PDF's content digest, the
#: same literal `issue-5d-actions-1-OBLIGATION-COORDINATES.py` pins.
PINNED_SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret


def pinned_evidence() -> dict[str, object]:
    """The committed artifact, read as UTF-8 and never skipped past.

    A missing artifact fails rather than skips: a guard that quietly stops
    running is the exact defect family this module exists to close.
    """
    assert EVIDENCE_PATH.exists(), (
        f"pinned source evidence is missing: {EVIDENCE_PATH}. Re-derive it with "
        "`venv/Scripts/python .claude/review-notes/"
        "issue-5d-actions-1-OBLIGATION-COORDINATES.py`."
    )
    with open(EVIDENCE_PATH, encoding="utf-8") as handle:
        payload: dict[str, object] = json.load(handle)
    return payload


#: ``Ready [Action]``, leaf 1 of 2 — printed page 186.
FIRST_LEAF = "af20f466-ce0c-5790-9912-0c93dae7211a"
FIRST_LEAF_LENGTH = 451
#: ``Ready [Action]``, leaf 2 of 2 — printed page 187.
SECOND_LEAF = "1022361f-12cf-5e93-93d5-f290c6640282"
SECOND_LEAF_LENGTH = 639

L2_START, L2_END = 125, 200
L2_TEXT = "which lets you act by taking a Reaction before the start of your next turn."

L4_START, L4_END = 277, 405
L4_TEXT = (
    "Then, you choose the action you will take in response to that trigger, "
    "or you choose to move up to your Speed in response to it."
)

L6_START, L6_END = 97, 211
L6_TEXT = (
    "When the trigger occurs, you can either take your Reaction right after "
    "the trigger finishes or ignore the trigger."
)

#: The one boundary this module draws, derived from the printed sentence. The
#: alternation is printed with an ``or``, and that is the only place a two-arm
#: choice can be split without the split itself being an assertion.
L4_BOUNDARY = L4_START + L4_TEXT.index("or you choose")
L4A_TEXT = L4_TEXT[: L4_BOUNDARY - L4_START]
L4B_TEXT = L4_TEXT[L4_BOUNDARY - L4_START :]

L2_SPAN = derive_span_id(FIRST_LEAF, L2_START, L2_END)
L4A_SPAN = derive_span_id(FIRST_LEAF, L4_START, L4_BOUNDARY)
L4B_SPAN = derive_span_id(FIRST_LEAF, L4_BOUNDARY, L4_END)
L6_SPAN = derive_span_id(SECOND_LEAF, L6_START, L6_END)

#: Local to this module — see the docstring's second limit. One chunk per whole
#: leaf, which is the shape ``chunk_relative_range`` requires and the shape the
#: production projection has, with identifiers that are this module's own.
FIRST_CHUNK = "chunk-ready-p186"
SECOND_CHUNK = "chunk-ready-p187"

READY_CORPUS = bound_corpus(
    leaf_lengths={FIRST_LEAF: FIRST_LEAF_LENGTH, SECOND_LEAF: SECOND_LEAF_LENGTH},
    chunk_coverage=(
        coverage(FIRST_CHUNK, FIRST_LEAF, 0, FIRST_LEAF_LENGTH),
        coverage(SECOND_CHUNK, SECOND_LEAF, 0, SECOND_LEAF_LENGTH),
    ),
)


def _leaf_text(length: int, *placed: tuple[int, str]) -> str:
    """A leaf of *length* carrying each printed extent at its own offset.

    Only the extents this demonstration claims are reconstructed; the rest of
    the leaf is filler, because the other obligations' text is not what any
    binding here resolves to. The offsets are real, so a binding whose extent
    disagreed with its span would slice the filler and fail visibly.
    """
    body = [" "] * length
    for start, text in placed:
        body[start : start + len(text)] = text
    return "".join(body)


FIRST_LEAF_TEXT = _leaf_text(
    FIRST_LEAF_LENGTH, (L2_START, L2_TEXT), (L4_START, L4_TEXT)
)
SECOND_LEAF_TEXT = _leaf_text(SECOND_LEAF_LENGTH, (L6_START, L6_TEXT))


# ---------------------------------------------------------------------------
# The representation, keyed to those coordinates
# ---------------------------------------------------------------------------

READY_KEY = "gameplay_tool:ready"
RESPONSE_KEY = "ready-response"
CHOICE_KEY = "readied-choice"
ACTION_ARM = "take-the-chosen-action"
MOVE_ARM = "move-up-to-your-speed"

#: That *this arm* is what spends the readied Reaction. One printed cost
#: restated per arm, because a choice has no position for a cost its arms
#: share. L2 states the slot once for the whole response and so supports each
#: copy without stating it — which is why these edges are contextual on L2.
READIED_REACTION = ActionEconomyFact(cost=ActionCost.REACTION)

#: ``ActionAllowanceFact(1, OWNING_EFFECT, REACTION)`` — L2's grant.
READY_GRANT = CASES["L2"][1]
#: ``MovementAllowanceFact(OWN_SPEED)`` — L4's second clause.
OWN_SPEED = CASES["L4"][1]
#: ``TriggeredResolutionFact(IMMEDIATELY_AFTER_TRIGGER, optional=True)`` — L6.
TRIGGER_RESOLUTION = CASES["L6"][1]

_ARM_ONE_PROSE = ProseBindingDraft(
    component_key=CHOICE_KEY,
    record_key=READY_KEY,
    chunk_id=FIRST_CHUNK,
    span_id=L4A_SPAN,
    # The chunk covers the whole leaf from offset 0, so the chunk-relative
    # extent *is* the printed leaf extent. `_validate_prose_extent` recomputes
    # exactly this from the bound release and refuses a disagreement.
    chunk_char_start=L4_START,
    chunk_char_end=L4_BOUNDARY,
    irreducibility_reason_code="open_ended_effect",
    option_key=ACTION_ARM,
)


def _components() -> tuple[ComponentDraft, ComponentDraft]:
    return (
        ComponentDraft(
            record_key=READY_KEY,
            semantic_key=RESPONSE_KEY,
            handling=ComponentHandling.STRUCTURED,
            facts=(READY_GRANT, TRIGGER_RESOLUTION),
        ),
        ComponentDraft(
            record_key=READY_KEY,
            semantic_key=CHOICE_KEY,
            handling=ComponentHandling.MIXED,
            irreducibility_reason_code="open_ended_effect",
            options=(
                ComponentOption(semantic_key=ACTION_ARM, facts=(READIED_REACTION,)),
                ComponentOption(
                    semantic_key=MOVE_ARM, facts=(READIED_REACTION, OWN_SPEED)
                ),
            ),
        ),
    )


def _fact_edge(
    component_key: str,
    fact: object,
    span_id: str,
    role: ProvenanceRole,
    option_key: str = "",
) -> ProvenanceClaim:
    key = (READY_KEY, component_key, fact_key(fact))
    if option_key:
        key += (option_key,)
    return ProvenanceClaim(ProvenanceTargetKind.FACT, key, span_id, role)


#: The mapping this module exists to state, as data rather than as prose: one
#: row per authoritative element, naming the span its evidence comes from and
#: the role that evidence carries.
READY_PROVENANCE = (
    # L2 states the grant. It is the span's one primary owner.
    _fact_edge(RESPONSE_KEY, READY_GRANT, L2_SPAN, ProvenanceRole.PRIMARY),
    # L6 states when the response resolves and that it may be declined.
    _fact_edge(RESPONSE_KEY, TRIGGER_RESOLUTION, L6_SPAN, ProvenanceRole.PRIMARY),
    # Each arm's copy of the one printed cost, evidenced on the span that
    # grants the slot. Contextual: L2 scopes the Reaction to the whole readied
    # response, never to an alternative, so it supports these without stating
    # them.
    _fact_edge(
        CHOICE_KEY, READIED_REACTION, L2_SPAN, ProvenanceRole.CONTEXTUAL, ACTION_ARM
    ),
    _fact_edge(
        CHOICE_KEY, READIED_REACTION, L2_SPAN, ProvenanceRole.CONTEXTUAL, MOVE_ARM
    ),
    # L4's own two statements keep primary ownership of the text printing them.
    _fact_edge(CHOICE_KEY, OWN_SPEED, L4B_SPAN, ProvenanceRole.PRIMARY, MOVE_ARM),
    ProvenanceClaim(
        ProvenanceTargetKind.PROSE_BINDING,
        prose_binding_target_key(_ARM_ONE_PROSE),
        L4A_SPAN,
        ProvenanceRole.PRIMARY,
    ),
)


def ready_draft(
    provenance: tuple[ProvenanceClaim, ...] = READY_PROVENANCE,
) -> RepresentationDraft:
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=READY_KEY, kind=RecordKind.GAMEPLAY_TOOL),),
        components=_components(),
        prose_bindings=(_ARM_ONE_PROSE,),
        relationships=(),
        references=(),
        provenance=provenance,
    )


def _span(span_id: str, leaf: str, start: int, end: int) -> SemanticSpan:
    return SemanticSpan(
        span_id=span_id,
        leaf_id=leaf,
        char_start=start,
        char_end=end,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.ACCEPTED,
    )


READY_SPANS = (
    _span(L2_SPAN, FIRST_LEAF, L2_START, L2_END),
    _span(L4A_SPAN, FIRST_LEAF, L4_START, L4_BOUNDARY),
    _span(L4B_SPAN, FIRST_LEAF, L4_BOUNDARY, L4_END),
    _span(L6_SPAN, SECOND_LEAF, L6_START, L6_END),
)


def ready_ledger() -> ClassificationLedger:
    """The four accepted spans this demonstration claims — see the limits above."""
    return build_ledger(spans=READY_SPANS)


def _authority() -> EffectiveAuthority:
    records = _base_records(
        candidate_of(RELEASE_BINDING, ready_ledger(), ready_draft())
    )
    return EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, PACKAGE_UUID),
            release_version=RELEASE_VERSION,
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )


# ---------------------------------------------------------------------------
# The partition, and that it is the printed one
# ---------------------------------------------------------------------------


def test_the_split_is_the_printed_or_and_nothing_else() -> None:
    """The one boundary, checked against the sentence it came from.

    A partition chosen to make a count come out is exactly what this module is
    written to avoid, so the offset is derived rather than declared, the two
    halves must reassemble into the printed sentence, and both must lie inside
    the extent the artifact records for L4.
    """
    assert L4A_TEXT + L4B_TEXT == L4_TEXT
    assert L4_START < L4_BOUNDARY < L4_END
    assert L4B_TEXT.startswith("or ")
    # And both halves fall inside the leaf the artifact says they are printed
    # on, which is what makes them addressable at all.
    assert L4_END <= FIRST_LEAF_LENGTH
    assert L6_END <= SECOND_LEAF_LENGTH


def test_the_transcription_equals_the_pinned_source_evidence() -> None:
    """Every literal in this module, against evidence it did not produce.

    Comparing hand-entered strings with hand-entered extents proves nothing: a
    same-length paraphrase — *"saving a Reaction"* for *"taking a Reaction"* —
    passes every other check in this file, because the reconstructed leaf is
    built from the same literals. This is the check that fails.

    The artifact is derived from the pinned SRD PDF by a committed script, and
    its recorded ``authoritative_source_hash`` is asserted too, so equality here
    is equality to the pinned source and not to whatever a regeneration made.
    """
    evidence = pinned_evidence()
    assert evidence["authoritative_source_hash"] == PINNED_SOURCE_SHA256

    rows = {
        row["obligation"]: row
        for row in evidence["coordinates"]  # type: ignore[union-attr]
        if row["entry"] == "Ready [Action]"
    }
    for name, leaf, start, end, text in (
        ("L2", FIRST_LEAF, L2_START, L2_END, L2_TEXT),
        ("L4", FIRST_LEAF, L4_START, L4_END, L4_TEXT),
        ("L6", SECOND_LEAF, L6_START, L6_END, L6_TEXT),
    ):
        row = rows[name]
        assert row["leaf_id"] == leaf
        assert (row["char_start"], row["char_end"]) == (start, end)
        assert row["source_text"] == text

    lengths = {
        row["leaf_id"]: row["length"]
        for row in evidence["leaf_partition"]  # type: ignore[union-attr]
    }
    assert lengths[FIRST_LEAF] == FIRST_LEAF_LENGTH
    assert lengths[SECOND_LEAF] == SECOND_LEAF_LENGTH

    # The reconstruction is built from strings now proven, so the leaf it
    # assembles is the right length and carries each clause at its own offset.
    # ``_leaf_text`` assigns into a list slice, so a length disagreement would
    # resize the leaf and shift every offset after it.
    assert len(FIRST_LEAF_TEXT) == FIRST_LEAF_LENGTH
    assert len(SECOND_LEAF_TEXT) == SECOND_LEAF_LENGTH
    assert FIRST_LEAF_TEXT[L2_START:L2_END] == L2_TEXT
    assert FIRST_LEAF_TEXT[L4_START:L4_END] == L4_TEXT
    assert SECOND_LEAF_TEXT[L6_START:L6_END] == L6_TEXT


def test_the_cost_edges_are_contextual_because_of_what_l2_scopes() -> None:
    """The role argument, in checkable form.

    ``ProvenanceRole`` asks whether the cited span *states* the claim or merely
    supports it, so the answer has to come from L2 — the span these edges cite —
    and not from L4's silence. L2 states the slot once for the whole readied
    response: the grant is scoped to the owning effect, and its cost names the
    same slot each arm's fact spends. The arms' copies are therefore not
    independent authority. They assert what L2 never scopes — that *this
    alternative* is what spends it — and L2 makes them true without saying it.
    """
    assert READIED_REACTION.cost is READY_GRANT.cost
    assert READY_GRANT.per is AllowanceScope.OWNING_EFFECT
    assert READY_GRANT.count == 1
    # L4 prints no Reaction. True of the source, and deliberately *not* the
    # reason for the role: an edge citing L2 cannot be justified by L4.
    assert "Reaction" not in L4_TEXT
    assert "Reaction" in L2_TEXT


# ---------------------------------------------------------------------------
# The contract, exercised rather than described
# ---------------------------------------------------------------------------


def test_readys_choice_validates_against_its_own_source_coordinates() -> None:
    """The whole mapping, through the real validator, on the real extents."""
    assert validate_representation(ready_draft(), ready_ledger(), READY_CORPUS) == ()


def test_the_choice_is_an_exhaustive_actor_choice() -> None:
    """Authorability is asked of the rule that decides it, not asserted around."""
    _, choice = _components()
    assert option_set_violations(choice.facts, choice.options, "ready/choice") == []


def test_each_span_carries_exactly_one_primary_owner() -> None:
    """Half the contract, stated over the real spans.

    Four substantive spans, four primary owners, and the owner of each is the
    element whose meaning that text prints.
    """
    primary = {
        claim.span_id: claim.target_key
        for claim in READY_PROVENANCE
        if claim.role is ProvenanceRole.PRIMARY
    }
    assert set(primary) == {L2_SPAN, L4A_SPAN, L4B_SPAN, L6_SPAN}
    assert len(
        [c for c in READY_PROVENANCE if c.role is ProvenanceRole.PRIMARY]
    ) == len(primary)
    assert primary[L2_SPAN] == (READY_KEY, RESPONSE_KEY, fact_key(READY_GRANT))
    assert primary[L6_SPAN] == (READY_KEY, RESPONSE_KEY, fact_key(TRIGGER_RESOLUTION))
    assert primary[L4B_SPAN] == (
        READY_KEY,
        CHOICE_KEY,
        fact_key(OWN_SPEED),
        MOVE_ARM,
    )
    assert primary[L4A_SPAN] == prose_binding_target_key(_ARM_ONE_PROSE)


def test_every_element_carries_evidence_and_a_contextual_only_fact_is_enough() -> None:
    """The other half, and the point the checkpoint had backwards.

    ``_validate_provenance`` requires every authoritative element to carry at
    least one admissible edge *of any role*. Both arms' consumption facts carry
    a contextual edge and nothing else, and the representation validates — so a
    fact whose only evidence is contextual is admitted. Why those two are
    contextual is decided by what L2 scopes, and is checked in
    ``test_the_cost_edges_are_contextual_because_of_what_l2_scopes``.
    """
    elements = {
        (READY_KEY, RESPONSE_KEY, fact_key(READY_GRANT)),
        (READY_KEY, RESPONSE_KEY, fact_key(TRIGGER_RESOLUTION)),
        (READY_KEY, CHOICE_KEY, fact_key(READIED_REACTION), ACTION_ARM),
        (READY_KEY, CHOICE_KEY, fact_key(READIED_REACTION), MOVE_ARM),
        (READY_KEY, CHOICE_KEY, fact_key(OWN_SPEED), MOVE_ARM),
        prose_binding_target_key(_ARM_ONE_PROSE),
    }
    assert {claim.target_key for claim in READY_PROVENANCE} == elements

    contextual_only = {
        claim.target_key
        for claim in READY_PROVENANCE
        if claim.role is ProvenanceRole.CONTEXTUAL
    }
    assert contextual_only == {
        (READY_KEY, CHOICE_KEY, fact_key(READIED_REACTION), ACTION_ARM),
        (READY_KEY, CHOICE_KEY, fact_key(READIED_REACTION), MOVE_ARM),
    }
    assert not contextual_only & {
        claim.target_key
        for claim in READY_PROVENANCE
        if claim.role is ProvenanceRole.PRIMARY
    }
    assert validate_representation(ready_draft(), ready_ledger(), READY_CORPUS) == ()


def test_the_shared_consumption_is_not_duplicated_authority() -> None:
    """One printed statement carried by two arms is one claim each.

    ADR-005d Decision 5 refuses the same fact drawn from the same span by two
    sibling *components*. Two arms of one choice are mutually exclusive
    alternatives, not a repeat — and this is the live case, since both arms cite
    L2 for the same consumption.
    """
    findings = validate_representation(ready_draft(), ready_ledger(), READY_CORPUS)
    assert not [f for f in findings if "duplicat" in f]


def test_only_the_clause_that_needs_binding_is_bound() -> None:
    """One prose binding, on the arm whose content is open.

    *Which* action the subject readies is not stated by any closed vocabulary,
    so arm 1's clause is bound. Arm 2's clause is fully typed by the own-Speed
    allowance, so binding it as well would carry text the record already states
    and would put a second primary claim on L4b.
    """
    draft = ready_draft()
    assert [b.option_key for b in draft.prose_bindings] == [ACTION_ARM]
    _, choice = _components()
    # The component is MIXED, and one option-scoped binding satisfies it: the
    # handling rule reads the component's prose, not each arm's.
    assert choice.handling is ComponentHandling.MIXED
    assert validate_representation(draft, ready_ledger(), READY_CORPUS) == ()


# ---------------------------------------------------------------------------
# The effective views, carrying the printed text
# ---------------------------------------------------------------------------


def test_the_gamemaster_reads_the_printed_clause_against_the_printed_arm() -> None:
    """The binding's offsets, resolved against the leaf they were taken from.

    The view slices the chunk with the extent the binding declares, so this
    returns the printed clause only if the extent is the real one. It is the
    check that fails if an offset is ever nudged.
    """
    view = build_gamemaster_view(
        _authority(),
        {FIRST_CHUNK: FIRST_LEAF_TEXT, SECOND_CHUNK: SECOND_LEAF_TEXT},
    )
    choice = next(c for c in view.components if c.component_key == CHOICE_KEY)
    assert [e.text for e in choice.governing_prose] == [L4A_TEXT]
    assert [
        e.option_key for e in choice.governing_prose  # type: ignore[union-attr]
    ] == [ACTION_ARM]
    assert [o.semantic_key for o in choice.options] == [ACTION_ARM, MOVE_ARM]


def test_the_typed_view_carries_both_arms_and_the_grant_that_precedes_them() -> None:
    """A typed consumer gets the choice and the allowance it spends."""
    typed = build_typed_view(_authority())
    components = {c.semantic_key: c for c in typed.records[0].components}
    choice = components[CHOICE_KEY]
    by_arm = {o.semantic_key: [f.fact for f in o.facts] for o in choice.options}
    assert by_arm[ACTION_ARM] == [READIED_REACTION]
    assert by_arm[MOVE_ARM] == [READIED_REACTION, OWN_SPEED]
    assert [f.fact for f in components[RESPONSE_KEY].facts] == [
        READY_GRANT,
        TRIGGER_RESOLUTION,
    ]


def test_every_fact_reaches_a_consumer_under_its_own_span() -> None:
    """Provenance survives to the effective record, keyed per arm."""
    records = _base_records(
        candidate_of(RELEASE_BINDING, ready_ledger(), ready_draft())
    )
    choice = next(
        c for c in records[READY_KEY].components if c.semantic_key == CHOICE_KEY
    )
    by_arm = {
        o.semantic_key: {f.fact: set(f.span_ids) for f in o.facts}
        for o in choice.options
    }
    assert by_arm[ACTION_ARM][READIED_REACTION] == {L2_SPAN}
    assert by_arm[MOVE_ARM][READIED_REACTION] == {L2_SPAN}
    assert by_arm[MOVE_ARM][OWN_SPEED] == {L4B_SPAN}
    response = next(
        c for c in records[READY_KEY].components if c.semantic_key == RESPONSE_KEY
    )
    assert {f.fact: set(f.span_ids) for f in response.facts} == {
        READY_GRANT: {L2_SPAN},
        TRIGGER_RESOLUTION: {L6_SPAN},
    }


# ---------------------------------------------------------------------------
# The refusals, as one-edit perturbations of the same real-coordinate draft
# ---------------------------------------------------------------------------


def test_dropping_the_movement_claim_leaves_l4s_second_clause_unowned() -> None:
    """A substantive span with no primary owner is refused by name."""
    without = tuple(c for c in READY_PROVENANCE if c.span_id != L4B_SPAN)
    findings = validate_representation(
        ready_draft(without), ready_ledger(), READY_CORPUS
    )
    assert f"span {L4B_SPAN}: substantive but unclaimed" in findings


def test_a_second_primary_owner_on_one_span_is_refused() -> None:
    """Two elements cannot both own the text that prints one of them.

    Arm 1's binding is pointed at L4b beside the movement allowance — the exact
    shape a five-claims-over-one-sentence encoding would need, and the reason
    it cannot simply be asserted.
    """
    moved = tuple(
        replace(c, span_id=L4B_SPAN) if c.span_id == L4A_SPAN else c
        for c in READY_PROVENANCE
    )
    findings = validate_representation(ready_draft(moved), ready_ledger(), READY_CORPUS)
    assert any(
        f.startswith(f"span {L4B_SPAN}: conflicting primary claims by")
        for f in findings
    )
    # And L4a, no longer owned by anything, is reported too.
    assert f"span {L4A_SPAN}: substantive but unclaimed" in findings


def test_promoting_a_cost_edge_makes_l2_say_two_things_at_once() -> None:
    """The role is refused, not merely preferred.

    Arm 1's consumption is promoted to PRIMARY on the span it already cites.
    Nothing about the fact or the span changes — only the claim that L2 *states*
    this arm spends the slot, beside L2's grant already stating that the readied
    response has one. ``_validate_provenance`` refuses exactly that: two
    structures both asserting they are what one sentence says.
    """
    promoted = tuple(
        (
            replace(c, role=ProvenanceRole.PRIMARY)
            if c.span_id == L2_SPAN and c.role is ProvenanceRole.CONTEXTUAL
            else c
        )
        for c in READY_PROVENANCE
    )
    findings = validate_representation(
        ready_draft(promoted), ready_ledger(), READY_CORPUS
    )
    assert any(
        f.startswith(f"span {L2_SPAN}: conflicting primary claims by") for f in findings
    )


def test_the_same_edge_twice_is_one_claim_recorded_twice() -> None:
    """Duplicate authority is rejected rather than counted as two."""
    doubled = (*READY_PROVENANCE, READY_PROVENANCE[0])
    findings = validate_representation(
        ready_draft(doubled), ready_ledger(), READY_CORPUS
    )
    assert any("duplicate provenance edge for span" in f for f in findings)


def test_a_binding_may_not_claim_a_span_its_chunk_does_not_cover() -> None:
    """Chunk locality, on the real two-leaf split.

    ``Ready`` prints across two leaves, so the case is genuine here rather than
    constructed: L6 is on page 187's leaf, and page 186's chunk does not
    contain it.
    """
    elsewhere = tuple(
        (
            replace(c, span_id=L6_SPAN)
            if c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            else c
        )
        for c in READY_PROVENANCE
    )
    findings = validate_representation(
        ready_draft(elsewhere), ready_ledger(), READY_CORPUS
    )
    assert any(f"is not covered by bound chunk {FIRST_CHUNK}" in f for f in findings)
