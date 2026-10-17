"""Prerequisite B (ADR-006b): automatic Rolling Summary advancement from real
product turns, through the real app with the production provider resolver;
only the provider transport and credential storage are replaced.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import func, select, text

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.entitlement.policy import TurnCostPolicy
from afterworlds.entitlement.service import EntitlementService
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.rolling_summary import RollingSummaryORM
from afterworlds.services.rolling_summary import (
    ROLLING_SUMMARY_N,
    RollingSummaryService,
)
from scripts.scripted_provider import Reply
from tests.api._spine import Spine


def _summaries(s: Spine, story_id: str) -> list[RollingSummaryORM]:
    with s.session_factory() as session:
        rows = session.scalars(
            select(RollingSummaryORM)
            .where(RollingSummaryORM.story_id == story_id)
            .order_by(RollingSummaryORM.version_number)
        ).all()
        session.expunge_all()
        return list(rows)


def _eligible_ids(s: Spine, story_id: str) -> list[str]:
    with s.session_factory() as session:
        service = RollingSummaryService(session, generator=_never)
        return [r.turn_id for r in service.eligible_turns(UUID(story_id))]


def _never(_p: str | None, _t: list[str]) -> str:
    raise AssertionError("readers never generate")


def _turn_count(s: Spine) -> int:
    with s.session_factory() as session:
        return int(session.scalar(select(func.count()).select_from(TurnORM)) or 0)


def _started(s: Spine, style: str = "freeform_only", rng: str | None = None) -> str:
    story_id = s.create("branching")
    s.setup_branching(story_id, style, rng)
    # A setup-confirmation exchange before Begin is not playable narrative.
    setup_turn = s.turn(story_id, "Make it a stormy harbor town.")
    assert setup_turn["disposition"] == "delivered"
    assert s.begin(story_id)["outcome"] == "started"
    return story_id


@pytest.fixture()
def settled(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Every result hosted settlement received (a spy; settlement runs)."""
    seen: list[Any] = []
    real = EntitlementService.settle_hosted_turn_cost

    def spy(self: EntitlementService, sojourner_id: Any, result: Any, **kw: Any) -> Any:
        seen.append(result)
        return real(self, sojourner_id, result, **kw)

    monkeypatch.setattr(EntitlementService, "settle_hosted_turn_cost", spy)
    return seen


@pytest.mark.parametrize("path", ["hosted", "byok"])
def test_summary_advances_from_eligible_product_turns_and_feeds_later_context(
    spine: Spine, settled: list[Any], path: str
) -> None:
    s = spine
    s.seed_hosted() if path == "hosted" else s.seed_byok()
    story_id = _started(s)  # eligible #1: the opening
    other = _started(s)  # an interleaved story: isolation

    # Eligible #2..#9, interleaved with excluded material.
    for i in range(2, ROLLING_SUMMARY_N):
        assert s.turn(story_id, f"Beat {i}: I search the docks.")["disposition"] == (
            "delivered"
        )
        if i == 4:
            ooc = s.turn(story_id, "[OOC] what does cadence do?")
            assert ooc["disposition"] == "ooc_handled"
        if i == 6:
            s.provider.push("writer", Reply(status=500))
            failed = s.turn(story_id, "A failed beat that never lands.")
            assert failed["disposition"] == "pipeline_error"
        if i == 7:
            assert s.turn(other, "Elsewhere, a lighthouse.")["disposition"] == (
                "delivered"
            )
    assert len(_eligible_ids(s, story_id)) == ROLLING_SUMMARY_N - 1
    assert _summaries(s, story_id) == []
    assert s.provider.calls_for("rolling_summary") == []

    # Eligible #10 crosses the threshold inside its own transaction.
    tenth = s.turn(story_id, "Beat 10: I find the smuggler's ledger.")
    assert tenth["disposition"] == "delivered", tenth
    (v1,) = _summaries(s, story_id)
    eligible = _eligible_ids(s, story_id)
    assert len(eligible) == ROLLING_SUMMARY_N
    assert (v1.version_number, v1.is_current) == (1, True)
    assert v1.compressed_from_turn_id == eligible[0]
    assert v1.compressed_through_turn_id == eligible[-1] == tenth["turn_id"]

    (call,) = s.provider.calls_for("rolling_summary")
    window = next(
        t for t in call.texts if t.startswith("[Rolling Summary Compression]")
    )
    assert "prior_summary:\nnone" in window
    assert window.count("--- turn ") == ROLLING_SUMMARY_N
    assert "[Begin story]" not in window  # the code-owned marker is not source
    for excluded in ("stormy harbor", "cadence", "failed beat", "lighthouse"):
        assert excluded not in window
    assert "smuggler's ledger" in window
    # The pass ran on the turn's selected binding (hosted key or BYOK key).
    writer_key = s.provider.calls_for("writer")[-1].api_key
    assert call.api_key == writer_key
    assert ("byok" in call.api_key.lower()) is (path == "byok")
    # It reused the turn's stable prefix: the Story Bible block the Writer saw.
    assert call.texts[1] in s.provider.calls_for("writer")[-1].texts

    # OOC settles through the same hosted events; BYOK never deducts.
    assert (ooc["turn_id"] in s.deductions()) is (path == "hosted")
    if path == "hosted":
        result = next(r for r in settled if str(r.turn_id) == tenth["turn_id"])
        passes = {snap.pass_id for snap in TurnCostPolicy.extract_snapshots(result)}
        assert PipelinePassId.ROLLING_SUMMARY in passes
        assert tenth["turn_id"] in s.deductions()
    else:
        assert settled == [] and s.deductions() == {}

    # The next turn's context carries the committed summary.
    s.turn(story_id, "Beat 11: I read the ledger.")
    planner = s.provider.calls_for("planner")[-1]
    assert any(v1.text in text for text in planner.texts)
    assert _summaries(s, other) == []  # the other story never compressed

    # A second window compresses the prior summary plus the next N turns.
    for i in range(12, 2 * ROLLING_SUMMARY_N + 1):
        s.turn(story_id, f"Beat {i}: onward.")
    v1_after, v2 = _summaries(s, story_id)
    assert (v1_after.is_current, v2.is_current, v2.version_number) == (False, True, 2)
    second = s.provider.calls_for("rolling_summary")[-1]
    block = next(
        t for t in second.texts if t.startswith("[Rolling Summary Compression]")
    )
    assert f"prior_summary:\n{v1.text}" in block
    assert block.count("--- turn ") == ROLLING_SUMMARY_N
    assert v2.compressed_from_turn_id == _eligible_ids(s, story_id)[ROLLING_SUMMARY_N]


def _to_threshold(s: Spine, story_id: str) -> None:
    for i in range(2, ROLLING_SUMMARY_N):
        s.turn(story_id, f"Beat {i}.")


@pytest.mark.parametrize(
    ("reply", "disposition"),
    [
        (Reply(refusal=True), "refused_by_provider"),
        (Reply(tool_input={"summary": "   "}), "pipeline_error"),
        (Reply(status=500), "pipeline_error"),
    ],
)
def test_a_failed_due_summary_rolls_the_turn_back_unbilled_and_retries(
    spine: Spine, reply: Reply, disposition: str
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    _to_threshold(s, story_id)
    turns, deductions = _turn_count(s), s.deductions()
    ingested: list[Any] = []
    service = s.client.app.state.orchestrator._retrieval_write_service  # type: ignore[attr-defined]
    real_ingest = service.ingest_turn
    service.ingest_turn = lambda **kw: (ingested.append(kw), real_ingest(**kw))[1]

    s.provider.push("rolling_summary", reply)
    failed = s.turn(story_id, "Beat 10: the due turn.")
    assert failed["disposition"] == disposition, failed
    assert failed["delivered_output"] is None and failed["turn_id"] is None
    assert _turn_count(s) == turns  # Turn and canon rolled back
    assert _summaries(s, story_id) == []
    assert len(_eligible_ids(s, story_id)) == ROLLING_SUMMARY_N - 1
    assert s.deductions() == deductions  # non-billable
    assert ingested == []  # never reached Retrieval Memory

    retried = s.turn(story_id, "Beat 10: the due turn.")
    assert retried["disposition"] == "delivered"
    (row,) = _summaries(s, story_id)
    assert row.compressed_through_turn_id == retried["turn_id"]
    assert [k["turn_id"] for k in ingested] == [UUID(retried["turn_id"])]


def test_summary_persistence_failure_rolls_back(
    spine: Spine, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    _to_threshold(s, story_id)
    turns, deductions = _turn_count(s), s.deductions()
    real = RollingSummaryService.compress

    def broken(self: RollingSummaryService, *a: Any, **kw: Any) -> Any:
        real(self, *a, **kw)
        raise RuntimeError("disk full")

    monkeypatch.setattr(RollingSummaryService, "compress", broken)
    failed = s.turn(story_id, "Beat 10.")
    assert failed["disposition"] == "pipeline_error"
    assert "rolling summary persistence failed: disk full" in (
        failed["pipeline_error_summary"]
    )
    assert (_turn_count(s), s.deductions(), _summaries(s, story_id)) == (
        turns,
        deductions,
        [],
    )


def test_compression_is_idempotent_on_persisted_coverage(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    _to_threshold(s, story_id)
    s.turn(story_id, "Beat 10.")
    (row,) = _summaries(s, story_id)
    with s.session_factory() as session:
        service = RollingSummaryService(session, generator=_never)
        # Covered: nothing is due until N more eligible turns land.
        assert service.advance_if_due(UUID(story_id)) is None
        # Re-compressing the persisted window returns its row, ungenerated.
        again = service.compress(
            UUID(story_id),
            UUID(row.compressed_from_turn_id),
            UUID(row.compressed_through_turn_id),
            ["duplicate work"],
        )
        assert str(again.summary_id) == row.summary_id
    assert len(s.provider.calls_for("rolling_summary")) == 1


@pytest.fixture()
def results(spine: Spine, monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Every OrchestrationResult the app's orchestrator returns (a spy)."""
    orchestrator = spine.client.app.state.orchestrator  # type: ignore[attr-defined]
    seen: list[Any] = []
    real = orchestrator.orchestrate_turn

    def spy(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        seen.append(result)
        return result

    monkeypatch.setattr(orchestrator, "orchestrate_turn", spy)
    return seen


def _assert_rolled_back_with_audit(
    s: Spine, story_id: str, before: tuple[int, Any], result: Any
) -> None:
    turns, deductions = before
    assert result.disposition.value == "pipeline_error"
    assert result.turn_id is None and result.delivered_output is None
    # Completed passes stay on the non-delivered result for audit.
    assert result.extractor_result is not None
    assert result.contradiction_result is not None
    assert (_turn_count(s), s.deductions(), _summaries(s, story_id)) == (
        turns,
        deductions,
        [],
    )
    assert len(_eligible_ids(s, story_id)) == ROLLING_SUMMARY_N - 1


def test_a_malformed_summary_tool_call_rolls_back_with_audit(
    spine: Spine, results: list[Any]
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    _to_threshold(s, story_id)
    before = (_turn_count(s), s.deductions())
    # The model ignores the forced tool and answers in prose.
    s.provider.push("rolling_summary", Reply(text="A prose answer, no tool call."))
    failed = s.turn(story_id, "Beat 10: the due turn.")
    assert failed["disposition"] == "pipeline_error"
    assert "missing record_rolling_summary tool call" in (
        failed["pipeline_error_summary"]
    )
    result = results[-1]
    _assert_rolled_back_with_audit(s, story_id, before, result)
    # The failed call's usage is kept for audit, never settled.
    assert result.rolling_summary_result is not None
    assert result.rolling_summary_result.input_token_count


def test_outer_commit_failure_after_due_compression_rolls_everything_back(
    spine: Spine, results: list[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The due summary is generated and flushed, then the owning outer
    transaction's commit fails: no Turn, canon, summary, count, ingestion or
    deduction survives, and the completed passes' usage stays on the typed
    error."""
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    _to_threshold(s, story_id)
    before = (_turn_count(s), s.deductions())
    orchestrator = s.client.app.state.orchestrator  # type: ignore[attr-defined]
    ingested: list[Any] = []
    service = orchestrator._retrieval_write_service
    real_ingest = service.ingest_turn
    service.ingest_turn = lambda **kw: (ingested.append(kw), real_ingest(**kw))[1]

    compressed: list[Any] = []
    real_advance = RollingSummaryService.advance_if_due

    def advance(self: RollingSummaryService, *a: Any, **kw: Any) -> Any:
        row = real_advance(self, *a, **kw)
        compressed.append(row)
        return row

    monkeypatch.setattr(RollingSummaryService, "advance_if_due", advance)
    real_factory = orchestrator._session_factory

    def factory() -> Any:
        session = real_factory()
        real_commit = session.commit

        def commit() -> None:
            if compressed and compressed[-1] is not None:
                raise RuntimeError("disk I/O error during commit")
            real_commit()

        session.commit = commit
        return session

    monkeypatch.setattr(orchestrator, "_session_factory", factory)
    # A valid canon proposal on the due turn: it must not survive either.
    s.provider.push(
        "extractor",
        Reply(
            tool_input={
                "proposals": [
                    {
                        "kind": "event",
                        "event_kind": "plot_reveal",
                        "description": "The tide gate was sabotaged.",
                        "significance": "major_plot_turn",
                    }
                ]
            }
        ),
    )
    failed = s.turn(story_id, "Beat 10: the due turn.")
    assert compressed and compressed[-1] is not None  # it was due and ran
    assert "transaction commit failed" in failed["pipeline_error_summary"]
    result = results[-1]
    _assert_rolled_back_with_audit(s, story_id, before, result)
    assert result.rolling_summary_result is not None
    assert result.extractor_result.proposal_set.proposals  # proposed...
    with s.session_factory() as session:  # ...and no canon persisted
        events = session.execute(
            text("SELECT description FROM sb_events WHERE story_id = :s"),
            {"s": story_id},
        ).all()
    assert all("tide gate" not in row.description for row in events)
    assert ingested == []
