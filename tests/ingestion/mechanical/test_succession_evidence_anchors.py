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

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    OracleLoadError,
    accepted_inputs_payload,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_4_HASH,
    SCHEMA_4_VERSION,
    BatchSchemaAnchor,
    lift_accepted_inputs,
    succession_evidence_violations,
)

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
SCHEMA_3 = (SCHEMA_3_VERSION, SCHEMA_3_HASH)
SCHEMA_4 = (SCHEMA_4_VERSION, SCHEMA_4_HASH)
BATCH_ID = "conditions-1"


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


def _schema_4_artifact(anchors: list[dict[str, str]], lifts: list[dict] | None = None) -> dict:  # type: ignore[type-arg]
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
def test_corrupted_succession_evidence_is_refused(tmp_path, build, expected: str) -> None:  # type: ignore[no-untyped-def]
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
