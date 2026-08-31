"""A batch states the schema it was reviewed under — CRD Issue 5d, #137 round 7.

Changing one field of the committed artifact — its declared ``(version, hash)``
pair, and nothing else — turned schema-3-reviewed authority into committed
schema-4 accepted authority. Every other check passed, because every other check
was satisfied: the representation is legal under schema 4, the batches and their
proposal identities are untouched and reconcile, the obligations close, and an
empty lift history has nothing to contradict.

The gap was in the evidence, not in the checks. Acceptance evidence never
recorded *which schema each batch was reviewed under*, so an empty lift history
had two readings that could not be told apart:

* authority genuinely first accepted under the declared schema; and
* authority reviewed under an earlier schema and re-declared.

``BatchSchemaAnchor`` states the one thing the batch never said, beside the batch
rather than inside it: an ``AcceptanceBatch`` records what a human accepted, and
a batch accepted before this existed does not acquire a field because a later
succession needed one.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical.acceptance import AcceptanceError, accept_proposal
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    OracleLoadError,
    accepted_inputs_payload,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentDraft,
    ConditionKind,
    ConditionLevelFact,
    EffectTerminationFact,
    LevelDirection,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    BatchSchemaAnchor,
    SchemaLiftError,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
    lift_for,
    succession_evidence_violations,
)

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
SCHEMA_3 = (SCHEMA_3_VERSION, SCHEMA_3_HASH)
SCHEMA_4 = (SCHEMA_4_VERSION, SCHEMA_4_HASH)
BATCH_ID = "conditions-1"
COMMITTED_ORACLE_IDENTITY = "a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda"  # noqa: E501  # pragma: allowlist secret


def _committed() -> dict:  # type: ignore[type-arg]
    return json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))


def _proposal_identity() -> str:
    (batch,) = load_accepted_inputs(ARTIFACT_PATH).batches
    return batch.proposal_identity


def _write(raw: dict, tmp_path: pathlib.Path, name: str = "probe.json") -> pathlib.Path:  # type: ignore[type-arg]
    path = tmp_path / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def _anchor(**overrides: str) -> dict[str, str]:
    base = {
        "batch_id": BATCH_ID,
        "proposal_identity": _proposal_identity(),
        "schema_version": SCHEMA_3_VERSION,
        "schema_hash": SCHEMA_3_HASH,
    }
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# The attack, exactly as reported
# ---------------------------------------------------------------------------


def test_a_declaration_only_restamp_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """One field changed, and nothing else — the whole finding.

    The batches, their semantic diff, their diff hash and their proposal
    identity are the committed ones, byte for byte. That is what makes this a
    restamp rather than a forgery, and what made it invisible: nothing in the
    file disagrees with anything else in the file.
    """
    raw = _committed()
    raw["representation_schema"] = {
        "version": REPRESENTATION_SCHEMA_VERSION,
        "hash": representation_schema_hash(),
    }
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(_write(raw, pathlib.Path(tmp_path)))
    message = str(raised.value)
    assert "no batch states the representation schema it was reviewed under" in message


def test_the_committed_artifact_still_loads_and_is_byte_identical() -> None:
    """The legacy form, and the one reading it can have.

    A pre-schema-4 declaration with no lift evidence can only mean its batches
    were reviewed under the schema it declares — there was no other schema for
    them to have been reviewed under. That default is what keeps the committed
    file loadable without editing it, and it is exactly the default the test
    above proves is unavailable to a schema-4 declaration.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.schema_anchors == ()
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == SCHEMA_3
    assert accepted_inputs_payload(inputs) == _committed()


# ---------------------------------------------------------------------------
# The two shapes that must stay legal
# ---------------------------------------------------------------------------


def test_a_fresh_schema_4_artifact_needs_no_lift(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Genuinely first accepted under schema 4, with the anchor to say so.

    This is the case the restamp is trying to impersonate, and the reason the
    fix cannot simply be "a schema-4 artifact must carry lifts".
    """
    raw = _committed()
    raw["representation_schema"] = {"version": SCHEMA_4_VERSION, "hash": SCHEMA_4_HASH}
    raw["acceptance"]["schema_anchors"] = [
        _anchor(schema_version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH)
    ]
    loaded = load_accepted_inputs(_write(raw, pathlib.Path(tmp_path)))
    assert loaded.lifts == ()
    assert loaded.schema_anchors[0].schema_version == SCHEMA_4_VERSION


def test_a_genuinely_lifted_history_loads(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Reviewed under schema 3, carried across the registered succession.

    Built by the real lift rather than by hand: the anchor stays at schema 3 —
    which is the whole point, since that is where the review happened — and the
    declaration and the lift evidence agree on where it ended up.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    lifted, record = lift_accepted_inputs(inputs, SCHEMA_4)
    anchored = replace(
        lifted,
        schema_anchors=tuple(
            BatchSchemaAnchor(b.batch_id, b.proposal_identity, *SCHEMA_3)
            for b in lifted.batches
        ),
        lifts=(record,),
    )
    path = _write(
        accepted_inputs_payload(anchored), pathlib.Path(tmp_path), "lifted.json"
    )

    loaded = load_accepted_inputs(path)
    assert (loaded.oracle.schema_version, loaded.oracle.schema_hash) == SCHEMA_4
    assert loaded.schema_anchors == anchored.schema_anchors
    assert loaded.batches == inputs.batches, "the retained review is untouched"


# ---------------------------------------------------------------------------
# Every way the evidence can be wrong
# ---------------------------------------------------------------------------


def _schema_4_artifact(  # type: ignore[type-arg]
    anchors: list[dict[str, str]], lifts: list[dict] | None = None
) -> dict:
    """A schema-4 declaration carrying whatever evidence a case wants to test."""
    raw = _committed()
    raw["representation_schema"] = {"version": SCHEMA_4_VERSION, "hash": SCHEMA_4_HASH}
    raw["acceptance"]["schema_anchors"] = anchors
    if lifts is not None:
        raw["acceptance"]["lifts"] = lifts
    return raw


def _registered_lift() -> dict:  # type: ignore[type-arg]
    from afterworlds.ingestion.mechanical.representation import (
        REPRESENTATION_COLLECTIONS,
    )

    return {
        "lift_id": "5d-lift-schema-3-to-4",
        "from_version": SCHEMA_3_VERSION,
        "from_hash": SCHEMA_3_HASH,
        "to_version": SCHEMA_4_VERSION,
        "to_hash": SCHEMA_4_HASH,
        "verified_collections": sorted(REPRESENTATION_COLLECTIONS),
    }


CORRUPTIONS = [
    pytest.param(
        lambda: _schema_4_artifact([]),
        "no batch states the representation schema",
        id="missing-every-anchor",
    ),
    pytest.param(
        lambda: _schema_4_artifact([_anchor(), _anchor()], [_registered_lift()]),
        "anchored more than once",
        id="duplicate-anchor",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(batch_id="a-batch-that-is-not-here")], [_registered_lift()]
        ),
        "no retained batch has this id",
        id="dangling-anchor",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(proposal_identity="0" * 64)], [_registered_lift()]
        ),
        "anchored to proposal",
        id="rewritten-proposal-identity",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(schema_version="5d-representation-schema-99")],
            [_registered_lift()],
        ),
        "not a contract this build accepts authority under",
        id="unrecognized-anchored-version",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(schema_hash="f" * 64)], [_registered_lift()]
        ),
        "not a contract this build accepts authority under",
        id="invented-anchored-hash",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(schema_hash=SCHEMA_4_HASH)], [_registered_lift()]
        ),
        "not a contract this build accepts authority under",
        id="mismatched-known-anchor-pair",
    ),
    pytest.param(
        lambda: _schema_4_artifact([_anchor()], []),
        "without a registered succession carrying it there",
        id="inherited-authority-with-no-lift",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor(schema_version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH)],
            [_registered_lift()],
        ),
        "which no retained batch was reviewed under",
        id="decorative-lift",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor()],
            [{**_registered_lift(), "to_version": "5d-representation-schema-9"}],
        ),
        "the registered lift from",
        id="hash-mismatched-transition",
    ),
    pytest.param(
        lambda: _schema_4_artifact(
            [_anchor()],
            [
                {
                    **_registered_lift(),
                    "from_version": SCHEMA_4_VERSION,
                    "from_hash": SCHEMA_4_HASH,
                    "to_version": SCHEMA_3_VERSION,
                    "to_hash": SCHEMA_3_HASH,
                }
            ],
        ),
        "no lift is registered",
        id="reversed-transition",
    ),
]


@pytest.mark.parametrize(("build", "expected"), CORRUPTIONS)
def test_corrupted_succession_evidence_is_refused(  # type: ignore[no-untyped-def]
    tmp_path, build, expected: str
) -> None:
    """Through ``load_accepted_inputs``, not only through the validator."""
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(_write(build(), pathlib.Path(tmp_path)))
    message = str(raised.value)
    assert "acceptance evidence does not describe an authorized succession" in message
    assert expected in message, message


def test_an_unanchored_batch_beside_an_anchored_one_is_refused() -> None:
    """Partial evidence is not evidence.

    Asserted on the validator directly because it needs two batches, and the
    committed artifact has one — the loader cases above cover the file path.
    """
    from afterworlds.ingestion.mechanical.models import AcceptanceBatch

    batches = [
        AcceptanceBatch(
            batch_id=name,
            rule="r",
            resolved_scope=(),
            diff=(),
            semantic_diff_hash="d" * 64,
            proposal_identity=f"{index}" * 64,
        )
        for index, name in enumerate(("first", "second"))
    ]
    anchors = [BatchSchemaAnchor(batches[0].batch_id, "0" * 64, *SCHEMA_4)]
    findings = succession_evidence_violations(batches, anchors, (), SCHEMA_4)
    assert any("retained with no schema anchor" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Round 8 — evidence is validated before it is carried, not after it is written
# ---------------------------------------------------------------------------
#
# The loader's check was satisfiable by an artifact ``accept_proposal`` had just
# manufactured. Given an in-memory prior whose declared pair had been overwritten
# and whose evidence said nothing, the acceptance seam read that declaration to
# synthesize anchors — so the schema-3 review acquired schema-4 anchors, and the
# resulting file loaded clean because the transformation wrote exactly the
# evidence the loader would check.
#
# The fix validates the prior through the same contract the loader uses, before
# anything is computed from it. Malformed evidence is refused, never repaired.

PROBE_LEAF = "leaf-laundering-probe"
PROBE_SPAN = derive_span_id(PROBE_LEAF, 0, 28)
PROBE_RECORD = "hazard.laundering-probe"


def _proposal(prior, *, version: str, schema_hash: str) -> MechanicalProposal:  # type: ignore[no-untyped-def]
    span = SemanticSpan(
        span_id=PROBE_SPAN,
        leaf_id=PROBE_LEAF,
        char_start=0,
        char_end=28,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    return MechanicalProposal(
        binding=prior.oracle.binding,
        policy_version=prior.oracle.policy_version,
        policy_hash=prior.oracle.policy_hash,
        schema_version=version,
        schema_hash=schema_hash,
        proposed_spans=(
            ProposedSpan(span=span, origin="laundering-probe", rationale="probe"),
        ),
        proposed_representation=RepresentationDraft(
            records=(
                RecordDraft(semantic_key=PROBE_RECORD, kind=RecordKind.GLOSSARY_RULE),
            ),
            components=(
                ComponentDraft(
                    record_key=PROBE_RECORD,
                    semantic_key="accrual",
                    handling=ComponentHandling.STRUCTURED,
                    facts=(
                        ConditionLevelFact(
                            condition=ConditionKind.EXHAUSTION,
                            direction=LevelDirection.GAIN,
                            amount=1,
                        ),
                    ),
                ),
            ),
            prose_bindings=(),
            relationships=(),
            references=(),
            provenance=(),
        ),
        proposal_origin="test_succession_evidence_anchors",
    )


def _accept(prior, *, version: str, schema_hash: str):  # type: ignore[no-untyped-def]
    return accept_proposal(
        _proposal(prior, version=version, schema_hash=schema_hash),
        batch_id="laundering-probe-1",
        rule="the probe span",
        resolved_scope=(PROBE_SPAN,),
        reviewer="Test",
        accepted_at="2026-08-30T00:00:00Z",
        prior=prior,
    )


def _restamped_in_memory():  # type: ignore[no-untyped-def]
    """The committed artifact with its declared pair overwritten, nothing else."""
    real = load_accepted_inputs(ARTIFACT_PATH)
    return replace(
        real,
        oracle=replace(
            real.oracle, schema_version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH
        ),
    )


def test_an_in_memory_restamped_prior_cannot_be_extended() -> None:
    """The laundering, refused at the seam that used to perform it.

    The prior is the committed artifact with one field changed. Its batches,
    diffs and proposal identities are the real ones — which is exactly why
    reading its *declaration* to fill in its missing anchors produced evidence
    that looked genuine.
    """
    with pytest.raises(AcceptanceError) as raised:
        _accept(
            _restamped_in_memory(),
            version=SCHEMA_4_VERSION,
            schema_hash=SCHEMA_4_HASH,
        )
    message = str(raised.value)
    assert "succession evidence does not hold" in message
    assert "no batch states the representation schema it was reviewed under" in message


def test_the_refused_prior_never_becomes_loadable_evidence(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Refusal means no artifact, and the prior itself is still unloadable.

    Stated as two facts rather than one: acceptance produced nothing to write,
    and writing the restamped prior directly is refused by the loader for the
    same reason. There is no path from that in-memory value to a committed file.
    """
    restamped = _restamped_in_memory()
    with pytest.raises(AcceptanceError):
        _accept(restamped, version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH)

    path = _write(accepted_inputs_payload(restamped), pathlib.Path(tmp_path))
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(path)


def test_a_lift_cannot_launder_it_either() -> None:
    """The sibling seam, through the same shared rule.

    ``lift_accepted_inputs`` re-declares an artifact and synthesizes its anchors
    from the pair being lifted *from*. Given incoherent evidence it would carry
    that incoherence into the destination artifact, so it validates first — the
    same function, not a second implementation of it.
    """
    real = load_accepted_inputs(ARTIFACT_PATH)
    dangling = replace(
        real,
        schema_anchors=(
            BatchSchemaAnchor("a-batch-that-is-not-here", "0" * 64, *SCHEMA_3),
        ),
    )
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(dangling, SCHEMA_4)
    assert "does not hold" in str(raised.value)


MALFORMED_PRIORS = [
    pytest.param(
        lambda real: replace(
            real,
            schema_anchors=tuple(
                BatchSchemaAnchor(b.batch_id, b.proposal_identity, *SCHEMA_3)
                for b in real.batches
            )
            * 2,
        ),
        "anchored more than once",
        id="duplicate",
    ),
    pytest.param(
        lambda real: replace(
            real,
            schema_anchors=(BatchSchemaAnchor("not-a-batch", "0" * 64, *SCHEMA_3),),
        ),
        "no retained batch has this id",
        id="dangling",
    ),
    pytest.param(
        lambda real: replace(
            real,
            schema_anchors=tuple(
                BatchSchemaAnchor(b.batch_id, "0" * 64, *SCHEMA_3) for b in real.batches
            ),
        ),
        "anchored to proposal",
        id="proposal-mismatched",
    ),
    pytest.param(
        lambda real: replace(
            real,
            schema_anchors=tuple(
                BatchSchemaAnchor(
                    b.batch_id,
                    b.proposal_identity,
                    "5d-representation-schema-99",
                    "f" * 64,
                )
                for b in real.batches
            ),
        ),
        "not a contract this build accepts authority under",
        id="unknown-pair",
    ),
    pytest.param(
        lambda real: replace(real, schema_anchors=()),
        "no batch states the representation schema",
        id="incomplete-under-schema-4",
    ),
    pytest.param(
        lambda real: replace(
            real,
            schema_anchors=tuple(
                BatchSchemaAnchor(b.batch_id, b.proposal_identity, *SCHEMA_3)
                for b in real.batches
            ),
            lifts=(),
        ),
        "without a registered succession carrying it there",
        id="lift-inconsistent",
    ),
]


@pytest.mark.parametrize(("corrupt", "expected"), MALFORMED_PRIORS)
def test_malformed_prior_evidence_cannot_be_laundered_through_acceptance(
    corrupt, expected: str
) -> None:  # type: ignore[no-untyped-def]
    """Every corruption, on a prior that declares schema 4 and is extended.

    None of these is repaired, deleted, or worked around: the shared rule reports
    what is wrong with the prior and acceptance stops.
    """
    real = load_accepted_inputs(ARTIFACT_PATH)
    schema_4_prior = replace(
        real,
        oracle=replace(
            real.oracle, schema_version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH
        ),
    )
    with pytest.raises(AcceptanceError) as raised:
        _accept(
            corrupt(schema_4_prior),
            version=SCHEMA_4_VERSION,
            schema_hash=SCHEMA_4_HASH,
        )
    assert expected in str(raised.value)


# ---------------------------------------------------------------------------
# Everything that must stay acceptable
# ---------------------------------------------------------------------------


def test_the_legacy_artifact_is_still_extendable_and_anchored_at_schema_3() -> None:
    """The sole compatibility default, exercised through a real acceptance.

    The committed artifact states no anchors and no lifts and declares the
    recognized legacy pair, so its batches are anchored at *that* pair — schema 3,
    where the review happened — while the new batch is anchored at the schema the
    proposal declares.
    """
    prior = load_accepted_inputs(ARTIFACT_PATH)
    result = _accept(prior, version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH)

    anchored = {a.batch_id: a.schema_version for a in result.schema_anchors}
    assert anchored == {
        "conditions-1": SCHEMA_3_VERSION,
        "laundering-probe-1": SCHEMA_4_VERSION,
    }
    assert len(result.lifts) == 1, "the crossing the schema-3 anchor requires"
    assert result.batches[0] == prior.batches[0], "the retained review is untouched"


def test_a_validly_anchored_schema_4_prior_is_still_extendable() -> None:
    """Authority genuinely accepted under schema 4, extended again under it."""
    real = load_accepted_inputs(ARTIFACT_PATH)
    prior = replace(
        real,
        oracle=replace(
            real.oracle, schema_version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH
        ),
        schema_anchors=tuple(
            BatchSchemaAnchor(b.batch_id, b.proposal_identity, *SCHEMA_4)
            for b in real.batches
        ),
    )
    result = _accept(prior, version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH)
    assert result.lifts == (), "same contract, so no succession was crossed"
    assert {a.schema_version for a in result.schema_anchors} == {SCHEMA_4_VERSION}


def test_acceptance_with_no_prior_is_unaffected() -> None:
    """Nothing to validate, and nothing to carry."""
    real = load_accepted_inputs(ARTIFACT_PATH)
    result = accept_proposal(
        _proposal(real, version=SCHEMA_4_VERSION, schema_hash=SCHEMA_4_HASH),
        batch_id="laundering-probe-1",
        rule="the probe span",
        resolved_scope=(PROBE_SPAN,),
        reviewer="Test",
        accepted_at="2026-08-30T00:00:00Z",
        prior=None,
    )
    (anchor,) = result.schema_anchors
    assert (anchor.batch_id, anchor.schema_version) == (
        "laundering-probe-1",
        SCHEMA_4_VERSION,
    )
    assert result.lifts == ()


# ---------------------------------------------------------------------------
# Round 10 — lifting to the schema an artifact already declares is a no-op
# ---------------------------------------------------------------------------
#
# Checkpoint T-7 requires that carrying accepted authority to a schema it
# already declares neither changes its bytes nor records a second
# ``SchemaLiftRecord``. ``lift_accepted_inputs`` called ``lift_for``
# unconditionally, so schema-4 to schema-4 raised ``UnknownSchemaLiftError``
# instead — correct of ``lift_for``, which is keyed by real transitions, and
# wrong of the caller, which was asking a different question.
#
# The no-op lives in the caller for that reason. ``lift_for`` stays exact: an
# equal pair is not a registered succession, and teaching the registry to answer
# for one would merge "is this authorized?" with "is there anything to do?".


def _fully_evidenced_schema_4() -> AcceptedInputs:
    """The committed artifact carried to schema 4, with the evidence to say so.

    The record ``lift_accepted_inputs`` returns is deliberately *not* appended
    to ``lifts`` by that function — ``accept_proposal`` assembles the evidence
    half — so the artifact straight out of a lift declares schema 4 while
    holding a schema-3 anchor and no crossing. That is incomplete evidence, and
    the test below asserts it is refused rather than papering over it here.
    """
    lifted, record = lift_accepted_inputs(load_accepted_inputs(ARTIFACT_PATH), SCHEMA_4)
    return replace(lifted, lifts=(record,))


def test_the_genuine_succession_still_happens_exactly_once() -> None:
    """The crossing path, unchanged: one real record, anchored where reviewed."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    lifted, record = lift_accepted_inputs(inputs, SCHEMA_4)

    assert record is not None
    assert record.lift_id == "5d-lift-schema-3-to-4"
    assert (record.from_version, record.to_version) == (
        SCHEMA_3_VERSION,
        SCHEMA_4_VERSION,
    )
    assert (lifted.oracle.schema_version, lifted.oracle.schema_hash) == SCHEMA_4
    assert [(a.batch_id, a.schema_version) for a in lifted.schema_anchors] == [
        (BATCH_ID, SCHEMA_3_VERSION)
    ]

    # The other half of T-7: deterministic as well as idempotent. Lifting the
    # same artifact again produces the same bytes, so "once" is a property of
    # the evidence rather than of when the function happened to be called.
    twice, record_again = lift_accepted_inputs(
        load_accepted_inputs(ARTIFACT_PATH), SCHEMA_4
    )
    assert accepted_inputs_payload(twice) == accepted_inputs_payload(lifted)
    assert record_again == record


def test_retrying_a_fully_evidenced_artifact_is_a_byte_identical_no_op() -> None:
    """T-7, stated as the three things it actually requires.

    No new record; the same bytes; and no second crossing in the evidence. The
    returned object *is* the one passed in, so byte-identity holds by
    construction rather than by a comparison that could be satisfied loosely.
    """
    full = _fully_evidenced_schema_4()
    again, record = lift_accepted_inputs(full, SCHEMA_4)

    assert record is None
    assert again is full
    assert accepted_inputs_payload(again) == accepted_inputs_payload(full)
    assert len(again.lifts) == 1, "no duplicate lift evidence"
    assert again.schema_anchors == full.schema_anchors, "nothing synthesized"


def test_a_lift_is_still_needed_before_the_no_op_can_certify_anything() -> None:
    """The incomplete middle state, refused.

    An artifact declaring schema 4 while anchored at schema 3 with no recorded
    crossing has not arrived anywhere. The no-op certifies "already at target",
    which is a claim about the artifact, so it may not be made about this one.
    """
    lifted, _ = lift_accepted_inputs(load_accepted_inputs(ARTIFACT_PATH), SCHEMA_4)
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(lifted, SCHEMA_4)
    assert "without a registered succession carrying it there" in str(raised.value)


def test_lift_for_still_has_no_row_for_an_equal_pair() -> None:
    """``lift_for`` is unchanged, and the no-op is not a registry entry.

    If the equal pair were registered, "authorized succession" would include
    transitions nobody authorized because nothing happens in them, and every
    future schema would acquire one for free.
    """
    with pytest.raises(UnknownSchemaLiftError):
        lift_for(SCHEMA_4, SCHEMA_4)
    with pytest.raises(UnknownSchemaLiftError):
        lift_for(SCHEMA_3, SCHEMA_3)


def test_the_legacy_artifact_no_ops_at_the_schema_it_declares() -> None:
    """The other valid equal pair: schema 3, unanchored, exactly as committed."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    same, record = lift_accepted_inputs(inputs, SCHEMA_3)
    assert record is None
    assert same is inputs
    assert same.schema_anchors == (), "the committed artifact states no anchors"


def test_an_unknown_equal_pair_does_not_escape_through_the_no_op() -> None:
    """Idempotent is not unconditional. A pair nobody recognizes is still refused."""
    full = _fully_evidenced_schema_4()
    unknown = ("5d-representation-schema-99", "f" * 64)
    restamped = replace(
        full,
        oracle=replace(full.oracle, schema_version=unknown[0], schema_hash=unknown[1]),
    )
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(restamped, unknown)
    assert "not a contract this build accepts authority under" in str(raised.value)


def test_malformed_succession_evidence_does_not_escape_through_the_no_op() -> None:
    """A dangling anchor is refused on the equal-pair path as on the crossing one."""
    full = _fully_evidenced_schema_4()
    dangling = replace(
        full,
        schema_anchors=(BatchSchemaAnchor("not-a-batch", "0" * 64, *SCHEMA_4),),
    )
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(dangling, SCHEMA_4)
    assert "no retained batch has this id" in str(raised.value)


def test_an_illegal_representation_does_not_escape_through_the_no_op() -> None:
    """The legality half, the one an equal pair looks least likely to need.

    A schema-3 artifact holding a schema-4 fact family declares a contract that
    cannot state what it carries. Source equals target, the pair is recognized,
    and the evidence is the committed artifact's own — so nothing but
    ``declared_meaning_violations`` refuses this, and it must.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    draft = inputs.oracle.representation
    tampered = replace(
        draft,
        components=(
            replace(draft.components[0], facts=(EffectTerminationFact(),), options=()),
            *draft.components[1:],
        ),
    )
    illegal = replace(inputs, oracle=replace(inputs.oracle, representation=tampered))
    with pytest.raises(SchemaLiftError) as raised:
        lift_accepted_inputs(illegal, SCHEMA_3)
    assert "not admissible together" in str(raised.value)
    assert "effect_termination" in str(raised.value)


def test_the_committed_artifact_is_unmoved_by_any_of_this() -> None:
    """Zero movement, asserted where a no-op path could have reached it."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    lift_accepted_inputs(inputs, SCHEMA_3)
    lift_accepted_inputs(inputs, SCHEMA_4)
    assert accepted_inputs_payload(load_accepted_inputs(ARTIFACT_PATH)) == _committed()
    assert (inputs.oracle.schema_version, inputs.oracle.schema_hash) == SCHEMA_3
    assert oracle_identity(inputs.oracle) == COMMITTED_ORACLE_IDENTITY
    assert (
        len(inputs.oracle.representation.provenance),
        len(inputs.oracle.representation.references),
    ) == (185, 15)
