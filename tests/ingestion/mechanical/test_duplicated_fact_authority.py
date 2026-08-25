"""One source statement may not become two copies of the same authority.

ADR-005d Decision 5 requires a duplicated-fact projection to fail. The
per-scope duplicate check compares facts *within* one component's scope, so two
sibling components each holding an equivalent fact are two separate scopes and
each looks clean — the whole representation validated while publishing two
accrual claims where the source made one.

The gap was found by building it. Suffocation states a disjunctive trigger and a
single consequence:

    "When a creature runs out of breath or is choking, it gains 1 Exhaustion
    level at the end of each of its turns."

An authoring shape with one component per trigger arm, each carrying its own
copy of the one stated consequence, passed every check. Labelling one provenance
edge ``PRIMARY`` and the other ``CONTEXTUAL`` is what let it through, and that
labelling is itself the defect: the consequence clause *states* both facts, so
calling it merely contextual for one of them is false about where the authority
came from.

Six properties, each of which could break independently — three that must fail
and three that must keep passing. The three that must keep passing are the
reason the rule is narrow rather than a global uniqueness check.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    ComponentOption,
    ConditionKind,
    ConditionLevelFact,
    LevelDirection,
    MovementMode,
    MovementPermissionFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    RepresentationDraft,
    RollActor,
    fact_key,
    fact_target_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import bound_corpus

RECORD_KEY = "hazard.suffocation"
RECORD = RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.GLOSSARY_RULE)

#: The single stated consequence. One fact, whichever component holds it.
GAIN = ConditionLevelFact(
    condition=ConditionKind.EXHAUSTION, direction=LevelDirection.GAIN, amount=1
)
PER_TURN = Recurrence(boundary=RecurrenceBoundary.END_OF_TURN, whose=RollActor.SUBJECT)

LEAF = "leaf-spell"
#: Two disjoint substantive spans of one leaf. ``CONSEQUENCE`` is the clause that
#: states the accrual; ``ELSEWHERE`` stands for a genuinely different rule.
CONSEQUENCE_ID = derive_span_id(LEAF, 0, 20)
ELSEWHERE_ID = derive_span_id(LEAF, 20, 40)
CONSEQUENCE = SemanticSpan(
    span_id=CONSEQUENCE_ID,
    leaf_id=LEAF,
    char_start=0,
    char_end=20,
    disposition=SemanticDisposition.SUBSTANTIVE,
    review_state=ReviewState.ACCEPTED,
)
ELSEWHERE = SemanticSpan(
    span_id=ELSEWHERE_ID,
    leaf_id=LEAF,
    char_start=20,
    char_end=40,
    disposition=SemanticDisposition.SUBSTANTIVE,
    review_state=ReviewState.ACCEPTED,
)


def _ledger() -> ClassificationLedger:
    return ClassificationLedger(
        package_uuid="pkg-5c",
        release_version="rel-5c",
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        spans=(CONSEQUENCE, ELSEWHERE),
        batches=(),
        acceptances=(),
    )


def _duplication_findings(draft: RepresentationDraft) -> list[str]:
    """Only the duplicated-authority findings.

    Isolated deliberately: these drafts are minimal and trip unrelated checks
    (an unclaimed span, a record with no obligation), and a test that asserted
    on the whole report would pass or fail for the wrong reason.
    """
    return [
        f
        for f in validate_representation(draft, _ledger(), bound_corpus())
        if "two copies of the same authority" in f
    ]


def _sibling_draft(role_for_second: ProvenanceRole) -> RepresentationDraft:
    """Shape A: one component per trigger arm, both holding the one consequence."""
    breath = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="accrual_breath",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
        recurs=PER_TURN,
    )
    choking = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="accrual_choking",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
        recurs=PER_TURN,
    )
    return RepresentationDraft(
        records=(RECORD,),
        components=(breath, choking),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "accrual_breath", GAIN),
                CONSEQUENCE_ID,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "accrual_choking", GAIN),
                CONSEQUENCE_ID,
                role_for_second,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# 1-3. What must now fail
# ---------------------------------------------------------------------------


def test_shape_a_fails_as_duplicated_authority() -> None:
    """The defect itself: two sibling components, one stated consequence.

    The ``CONTEXTUAL`` label on the second edge is what made this validate
    before. It is not a mitigation — it is a false claim about where the fact
    came from — so the rule ignores the role entirely.
    """
    (finding,) = _duplication_findings(_sibling_draft(ProvenanceRole.CONTEXTUAL))
    assert RECORD_KEY in finding
    assert fact_key(GAIN) in finding
    assert "accrual_breath" in finding and "accrual_choking" in finding


def test_the_role_label_does_not_change_the_verdict() -> None:
    """Same duplication, both edges ``PRIMARY``: still duplicated authority.

    Asserted separately from the conflicting-primary rule below so the two
    cannot be confused for one another — this is about the fact being copied,
    not about who claims the span.
    """
    assert _duplication_findings(_sibling_draft(ProvenanceRole.PRIMARY))


def test_shape_a_prime_still_fails_for_conflicting_primary_claims() -> None:
    """The pre-existing provenance rule is not weakened by the new one.

    Both findings must be present: a reviewer needs to see that the span is
    doubly claimed *and* that the authority is duplicated, because fixing
    either one alone leaves the other defect standing.
    """
    report = validate_representation(
        _sibling_draft(ProvenanceRole.PRIMARY), _ledger(), bound_corpus()
    )
    assert any("conflicting primary claims" in f for f in report)
    assert any("two copies of the same authority" in f for f in report)


# ---------------------------------------------------------------------------
# 4-6. What must keep passing
# ---------------------------------------------------------------------------


def test_shape_b_passes_with_one_fact_and_honest_provenance() -> None:
    """The adopted shape: one component, one fact, one primary claim.

    The disjunctive trigger is carried as governing prose rather than being
    approximated by a typed predicate, so the source's OR survives unreduced and
    the consequence is stated exactly once.
    """
    component = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="suffocation_accrual",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
        recurs=PER_TURN,
    )
    draft = RepresentationDraft(
        records=(RECORD,),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "suffocation_accrual", GAIN),
                CONSEQUENCE_ID,
                ProvenanceRole.PRIMARY,
            ),
        ),
    )
    assert _duplication_findings(draft) == []


def test_one_mechanic_stated_by_two_different_rules_is_not_duplication() -> None:
    """The same fact from *different* spans is ordinary authority.

    This is why the rule is keyed on shared provenance rather than on fact
    equality. Two rules that each independently impose an Exhaustion level are
    two rules, and a global cross-component uniqueness check would have made the
    corpus unrepresentable.
    """
    first = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="accrual_here",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
    )
    second = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="accrual_there",
        handling=ComponentHandling.STRUCTURED,
        facts=(GAIN,),
    )
    draft = RepresentationDraft(
        records=(RECORD,),
        components=(first, second),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "accrual_here", GAIN),
                CONSEQUENCE_ID,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "accrual_there", GAIN),
                ELSEWHERE_ID,
                ProvenanceRole.PRIMARY,
            ),
        ),
    )
    assert _duplication_findings(draft) == []


def test_mutually_exclusive_options_keep_their_permitted_behaviour() -> None:
    """Two arms of one choice may state the same fact, from the same span.

    ``_validate_components`` already says so — *"the same fact appearing in two
    mutually exclusive options is not a repeat, it is one claim each"* — and the
    new rule must not contradict it. Option facts resolve to their owning
    component, so a choice is never reported as sibling duplication.
    """
    crawl = ComponentOption(
        semantic_key="crawl",
        facts=(GAIN, MovementPermissionFact(mode=MovementMode.WALK)),
    )
    stand = ComponentOption(semantic_key="stand", facts=(GAIN,))
    component = ComponentDraft(
        record_key=RECORD_KEY,
        semantic_key="movement_options",
        handling=ComponentHandling.STRUCTURED,
        options=(crawl, stand),
    )
    draft = RepresentationDraft(
        records=(RECORD,),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "movement_options", GAIN, "crawl"),
                CONSEQUENCE_ID,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD_KEY, "movement_options", GAIN, "stand"),
                CONSEQUENCE_ID,
                ProvenanceRole.CONTEXTUAL,
            ),
        ),
    )
    assert _duplication_findings(draft) == []
