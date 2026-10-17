"""CRD Issue 21 AC3-AC6 on the product path: committed canon and Retrieval
Memory feed later turns; access, fallback, Safety, contradiction and
malformed-output failures keep their transaction, delivery and billing
guarantees. Production provider resolver; only transport and credential
storage replaced (``tests/api/_spine.py``).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import func, select

from afterworlds.entitlement.enums import EntitlementEventType
from afterworlds.entitlement.payloads import CloudServicesActivatedPayload
from afterworlds.persistence.orm.node import TurnORM
from scripts.scripted_provider import Reply
from tests.api._spine import Spine

_KEY_LINE = "The lighthouse keeper hides a brass key beneath the third step."
_EVENT = {
    "kind": "event",
    "event_kind": "plot_reveal",
    "description": "The harbormaster is secretly the smuggler.",
    "significance": "major_plot_turn",
}
_CONCERN = {
    "category": "OTHER",
    "description": "scripted concern",
    "evidence_summary": "scripted",
}


def _turns(s: Spine) -> int:
    with s.session_factory() as session:
        return int(session.scalar(select(func.count()).select_from(TurnORM)) or 0)


def _started(s: Spine) -> str:
    story_id = s.create("branching")
    s.setup_branching(story_id, "freeform_only")
    assert s.begin(story_id)["outcome"] == "started"
    return story_id


def _stable_texts(call: Any) -> str:
    return "\n".join(call.texts)


def test_canon_and_retrieval_memory_feed_later_turns_per_story(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    other = _started(s)

    s.provider.push("writer", Reply(text=_KEY_LINE))
    s.provider.push("extractor", Reply(tool_input={"proposals": [_EVENT]}))
    assert s.turn(story_id, "I question the lighthouse keeper.")["disposition"] == (
        "delivered"
    )

    s.turn(story_id, "Where did the lighthouse keeper hide the brass key?")
    planner = _stable_texts(s.provider.calls_for("planner")[-1])
    # Story Bible canon committed by the Extractor's approved path.
    assert "secretly the smuggler" in planner
    # Retrieval Memory: the delivered narration was ingested into ChromaDB and
    # retrieved into the rendered stable-prefix block. Asserted on that block,
    # not the joined request: the 10-turn Immediate window still holds the
    # same turn verbatim.
    retrieved = [
        text
        for text in s.provider.calls_for("planner")[-1].texts
        if text.startswith("## Retrieved Context")
    ]
    assert len(retrieved) == 1
    assert f"- {_KEY_LINE}" in retrieved[0].splitlines()

    # Isolation: the other story asks the same question and sees neither.
    s.turn(other, "Where did the lighthouse keeper hide the brass key?")
    elsewhere = _stable_texts(s.provider.calls_for("planner")[-1])
    assert _KEY_LINE not in elsewhere  # neither retrieved nor recent
    assert "secretly the smuggler" not in elsewhere


def test_contradiction_block_rolls_back_unbilled_and_unretrievable(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    turns, deductions = _turns(s), s.deductions()
    s.provider.push(
        "writer", Reply(text="A forbidden candidate the reader never sees.")
    )
    s.provider.push("extractor", Reply(tool_input={"proposals": [_EVENT]}))
    s.provider.push(
        "contradiction",
        Reply(
            tool_input={
                "violations": [
                    {
                        "category": "other",
                        "description": "contradicts canon",
                        "canon_reference": "scripted",
                    }
                ]
            }
        ),
    )
    blocked = s.turn(story_id, "I do the impossible.")
    assert blocked["disposition"] == "blocked_contradiction"
    assert blocked["delivered_output"] is None
    assert (_turns(s), s.deductions()) == (turns, deductions)

    s.turn(story_id, "Was that impossible deed recorded anywhere?")
    later = _stable_texts(s.provider.calls_for("planner")[-1])
    assert "the reader never sees" not in later  # no turn, no memory
    assert "secretly the smuggler" not in later  # canon rolled back


def test_byok_safety_blocks_and_same_path_fallback(spine: Spine) -> None:
    """BYOK with Anthropic and OpenRouter: the OpenRouter route is not on the
    Safety whitelist, so both Safety checks run; a refusal falls back within
    BYOK only; a blocked or refused turn is never delivered or billed."""
    s = spine
    s.seed_byok(openrouter=True)
    story_id = _started(s)
    turns = _turns(s)

    s.provider.push("safety", Reply(tool_input={"concerns": [_CONCERN]}))
    assert s.turn(story_id, "Something unsafe.")["disposition"] == (
        "blocked_input_safety"
    )
    s.provider.push(
        "safety",
        Reply(tool_input={"concerns": []}),
        Reply(tool_input={"concerns": [_CONCERN]}),
    )
    out = s.turn(story_id, "Something that turns unsafe.")
    assert out["disposition"] == "blocked_output_safety"
    assert out["delivered_output"] is None
    assert _turns(s) == turns

    before = len(s.provider.calls)
    s.provider.push("writer", Reply(refusal=True))  # the primary refuses
    fell_back = s.turn(story_id, "I keep going.")
    assert fell_back["disposition"] == "delivered", fell_back
    writers = [c for c in s.provider.calls[before:] if c.pass_name == "writer"]
    assert [c.api for c in writers] == ["anthropic", "openrouter"]
    assert all("byok" in c.api_key.lower() for c in s.provider.calls[before:])
    assert s.deductions() == {}


def test_hosted_exhausted_refusal_and_malformed_output_are_typed_and_unbilled(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    story_id = _started(s)
    turns, deductions = _turns(s), s.deductions()

    s.provider.push("writer", Reply(refusal=True))
    refused = s.turn(story_id, "Write something refusable.")
    assert refused["disposition"] == "refused_by_provider"
    assert refused["provider_refusal"]["provider"] == "anthropic"
    # Hosted has no configured fallback route; nothing crosses to BYOK.
    assert {c.api for c in s.provider.calls_for("writer")} == {"anthropic"}

    s.provider.push("extractor", Reply(tool_input={"not": "a proposal list"}))
    malformed = s.turn(story_id, "Make the extractor stumble.")
    assert malformed["disposition"] == "pipeline_error"
    assert (_turns(s), s.deductions()) == (turns, deductions)


def test_unavailable_access_is_typed_before_any_work(
    spine: Spine,
) -> None:
    s = spine
    story_id = s.create("branching")
    s.setup_branching(story_id, "hybrid", "2-3")
    resp = s.client.post(f"/api/stories/{story_id}/begin")
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "entitlement_blocked"
    resp = s.client.post(f"/api/stories/{story_id}/turns", json={"user_input": "Hi"})
    assert resp.status_code == 403
    assert s.provider.calls == []
    assert s.visible(story_id)["play_status"] == "setup"


def test_one_stable_prefix_serves_every_pass_of_a_card_turn(
    spine: Spine,
) -> None:
    """Invariant 7: the turn's stable prefix is assembled once and rendered
    identically for Planner, the Branching writer, Extractor, Contradiction
    and the due Rolling Summary pass."""
    s = spine
    s.seed_hosted()
    story_id = s.create("branching")
    s.setup_branching(story_id, "hybrid", "2-3")
    s.begin(story_id)
    for i in range(8):
        s.turn(story_id, f"I choose option {1 + i % 2}")
    before = len(s.provider.calls)
    assert s.turn(story_id, "I choose option 1")["disposition"] == "delivered"
    turn_calls = s.provider.calls[before:]
    by_pass = {c.pass_name: c for c in turn_calls}
    assert {
        "planner",
        "branching_writer",
        "extractor",
        "contradiction",
        "rolling_summary",
    } <= set(by_pass)

    def story_bible_block(call: Any) -> str:
        blocks = call.body["messages"][0]["content"]
        cached = [b["text"] for b in blocks if b.get("cache_control")]
        assert len(cached) == 1  # one cache breakpoint: the stable prefix end
        return str(blocks[0]["text"])

    first = {name: story_bible_block(c) for name, c in by_pass.items()
             if name in ("planner", "branching_writer", "extractor",
                         "contradiction", "rolling_summary")}  # fmt: skip
    assert len(set(first.values())) == 1


def test_byok_runs_without_cloud_services_renewal(spine: Spine) -> None:
    """Spine section 2: local BYOK operation is independent of Cloud
    Services; a lapsed subscription gates hosted cloud features only."""
    s = spine
    s.seed_byok()
    s._events(
        (
            EntitlementEventType.CLOUD_SERVICES_ACTIVATED,
            CloudServicesActivatedPayload(
                expires_at=datetime.now(UTC) - timedelta(days=1)
            ),
        )
    )
    account = s.client.get("/api/account").json()
    assert account["selected_access_path"] == "byok"
    story_id = _started(s)
    assert s.turn(story_id, "I keep my own lantern lit.")["disposition"] == (
        "delivered"
    )
    assert s.deductions() == {}
    assert all("byok" in c.api_key.lower() for c in s.provider.calls)


def _ooc_style(s: Spine, story_id: str, style: str, rng: str | None) -> str:
    s.provider.push(
        "branching_ooc_config_extractor",
        Reply(
            tool_input={
                "interaction_style": style,
                "branching_cadence": None,
                "branch_count_range": rng,
                "length_preference": None,
            }
        ),
    )
    ooc = s.turn(story_id, f"[OOC] switch me to {style} {rng or 'as is'}")
    assert ooc["disposition"] == "ooc_handled"
    return str(ooc["delivered_output"])


def _started_with(s: Spine, style: str, rng: str | None) -> str:
    story_id = s.create("branching")
    s.setup_branching(story_id, style, rng)
    assert s.begin(story_id)["outcome"] == "started"
    return story_id


@pytest.mark.parametrize("rng", [None, "2-3"])
def test_ooc_cannot_strand_true_cyoa_without_committed_cards(
    spine: Spine, rng: str | None
) -> None:
    """ADR-016b: in play, True CYOA always has a selectable committed card
    set. After Freeform-only play there is none, and configuration does not
    generate cards, so the switch is refused with a truthful code-owned note
    and the story stays playable (no new OOC narrative path)."""
    s = spine
    s.seed_hosted()
    story_id = _started_with(s, "freeform_only", None)
    s.turn(story_id, "I walk the pier.")
    note = _ooc_style(s, story_id, "true_cyoa", rng)
    assert "not changed" in note
    assert s.visible(story_id)["interaction_style"] == "freeform_only"
    assert s.turn(story_id, "I walk on.")["disposition"] == "delivered"


def test_a_mixed_ooc_request_keeps_its_independently_valid_fields(
    spine: Spine,
) -> None:
    """The guard suppresses only the style/range change it refuses; a valid
    cadence change in the same request still applies, and the note names
    only what did not change."""
    s = spine
    s.seed_hosted()
    story_id = _started_with(s, "freeform_only", None)
    s.provider.push(
        "branching_ooc_config_extractor",
        Reply(
            tool_input={
                "interaction_style": "true_cyoa",
                "branching_cadence": "immersive",
                "branch_count_range": "2-3",
                "length_preference": None,
            }
        ),
    )
    ooc = s.turn(story_id, "[OOC] true cyoa 2-3, and more immersive please")
    assert "Interaction style and branch-count range not changed" in (
        ooc["delivered_output"]
    )
    vs = s.visible(story_id)
    assert (vs["interaction_style"], vs["branching_cadence"]) == (
        "freeform_only",
        "immersive",
    )


def test_ooc_to_true_cyoa_applies_only_when_committed_cards_fit(
    spine: Spine,
) -> None:
    s = spine
    s.seed_hosted()
    one_card = _started_with(s, "hybrid", "1-2")  # the opening shows 1 card
    note = _ooc_style(s, one_card, "true_cyoa", "2-3")
    assert "do not fit the True CYOA range 2-3" in note
    assert s.visible(one_card)["interaction_style"] == "hybrid"

    two_cards = _started_with(s, "hybrid", "2-3")
    _ooc_style(s, two_cards, "true_cyoa", "2-4")
    vs = s.visible(two_cards)
    assert (vs["interaction_style"], vs["branch_count_range"]) == (
        "true_cyoa",
        "2-4",
    )
    assert [c["option_id"] for c in vs["last_branch_options"]] == ["opt_1", "opt_2"]
    assert s.turn(two_cards, "I choose option 2")["disposition"] == "delivered"


def test_in_play_setup_cannot_strand_true_cyoa(spine: Spine) -> None:
    s = spine
    s.seed_hosted()
    body = {
        "mode": "branching",
        "interaction_style": "true_cyoa",
        "branch_count_range": "2-3",
    }
    freeform = _started_with(s, "freeform_only", None)
    resp = s.client.post(f"/api/stories/{freeform}/setup", json=body)
    assert resp.status_code == 422
    assert "True CYOA needs a current set of branch cards" in resp.json()["message"]
    one_card = _started_with(s, "hybrid", "1-2")
    resp = s.client.post(f"/api/stories/{one_card}/setup", json=body)
    assert resp.status_code == 422
    assert s.visible(one_card)["interaction_style"] == "hybrid"
    two_cards = _started_with(s, "hybrid", "2-3")
    resp = s.client.post(f"/api/stories/{two_cards}/setup", json=body)
    assert resp.status_code == 200, resp.text
    assert s.turn(two_cards, "I choose option 1")["disposition"] == "delivered"


def test_a_freeform_beat_replaces_the_committed_cards(spine: Spine) -> None:
    """ADR-016: each beat replaces the choices on offer. Cards survive an
    immediate switch away and back (no narrative in between), but a
    delivered Freeform-only beat leaves none to show or select."""
    s = spine
    s.seed_hosted()
    story_id = _started_with(s, "hybrid", "2-3")
    _ooc_style(s, story_id, "freeform_only", None)
    _ooc_style(s, story_id, "hybrid", "2-3")
    assert s.visible(story_id)["last_branch_options"]  # no beat in between

    _ooc_style(s, story_id, "freeform_only", None)
    assert s.turn(story_id, "I swim to the buoy.")["disposition"] == "delivered"
    _ooc_style(s, story_id, "hybrid", "2-3")
    vs = s.visible(story_id)
    assert vs["interaction_style"] == "hybrid"
    assert vs["last_branch_options"] is None
    stale = s.turn(story_id, "I choose option 1")
    assert stale["disposition"] == "interaction_rejected"
    assert stale["interaction_rejection_reason"] == "invalid_branch_selection"
    # Hybrid still accepts freeform input; its beat commits fresh cards.
    assert s.turn(story_id, "I climb the mast.")["disposition"] == "delivered"
    assert s.visible(story_id)["last_branch_options"]


def test_a_setup_write_during_begin_cannot_pair_with_the_opening(
    spine: Spine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3: an opening generated for one configuration never commits with
    another. The write is injected while the opening is being generated."""
    from uuid import UUID

    from afterworlds.models.enums import BranchCountRange
    from afterworlds.persistence.crud.session_state import (
        apply_branching_config_update,
    )
    from afterworlds.pipeline.branching.service import BranchingWriterService

    s = spine
    s.seed_hosted()
    story_id = s.create("branching")
    s.setup_branching(story_id, "true_cyoa", "2-3")
    real = BranchingWriterService.write
    fired: list[bool] = []

    def racing(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not fired:
            fired.append(True)
            with s.session_factory() as other:
                apply_branching_config_update(
                    other,
                    UUID(story_id),
                    branch_count_range=BranchCountRange.TWO_TO_FIVE,
                )
                other.commit()
        return real(self, *args, **kwargs)

    monkeypatch.setattr(BranchingWriterService, "write", racing)
    turns = _turns(s)
    raced = s.begin(story_id)
    assert raced["outcome"] == "not_started"
    assert raced["turn"]["disposition"] == "pipeline_error"
    assert _turns(s) == turns and s.deductions() == {}
    assert s.visible(story_id)["play_status"] == "setup"
    assert s.visible(story_id)["branch_count_range"] == "2-5"
    # A retry opens for the configuration now persisted.
    assert s.begin(story_id)["outcome"] == "started"
    assert s.visible(story_id)["branch_count_range"] == "2-5"


def test_setup_shares_the_story_turn_lock(spine: Spine) -> None:
    import asyncio
    from uuid import UUID

    s = spine
    story_id = s.create("branching")
    lock = s.client.app.state.story_locks[UUID(story_id)]  # type: ignore[attr-defined]
    asyncio.run(lock.acquire())
    try:
        resp = s.client.post(
            f"/api/stories/{story_id}/setup",
            json={"mode": "branching", "interaction_style": "hybrid"},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "turn_in_flight"
    finally:
        lock.release()


HOSTED_OPENROUTER_KEY = "sk-or-SYNTHETIC-hosted-0000000000"  # pragma: allowlist secret


@pytest.fixture()
def hosted_fallback_spine(
    app_settings: Any, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Spine]:
    """The factory-built app with the hosted OpenRouter fallback configured
    the way an operator does: OPENROUTER_API_KEY plus the explicit
    OPENROUTER_FALLBACK_MODEL (no default exists)."""
    import keyring
    from fastapi.testclient import TestClient

    from afterworlds.api.app import create_app
    from scripts.e2e_memory_keyring import install as install_memory_keyring
    from scripts.scripted_provider import SYNTHETIC_HOSTED_KEY, ScriptedProvider

    for name in ("AFTERWORLDS_FAKE_PROVIDER", "AFTERWORLDS_CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", SYNTHETIC_HOSTED_KEY)
    monkeypatch.setenv("OPENROUTER_API_KEY", HOSTED_OPENROUTER_KEY)
    monkeypatch.setenv("OPENROUTER_FALLBACK_MODEL", "anthropic/claude-sonnet-4-5")
    previous = keyring.get_keyring()
    install_memory_keyring()
    provider = ScriptedProvider().install()
    try:
        with TestClient(create_app(app_settings)) as client:
            yield Spine(client, provider)
    finally:
        provider.uninstall()
        keyring.set_keyring(previous)


def test_hosted_refusal_falls_back_within_hosted_through_factory_wiring(
    hosted_fallback_spine: Spine,
) -> None:
    s = hosted_fallback_spine
    s.seed_hosted()
    story_id = _started(s)
    before = len(s.provider.calls)
    s.provider.push("writer", Reply(refusal=True))  # hosted Anthropic refuses
    turn = s.turn(story_id, "I keep going.")
    assert turn["disposition"] == "delivered", turn
    writers = [c for c in s.provider.calls[before:] if c.pass_name == "writer"]
    assert [c.api for c in writers] == ["anthropic", "openrouter"]
    assert writers[1].api_key == HOSTED_OPENROUTER_KEY  # hosted, never BYOK
    assert writers[1].body["model"] == "anthropic/claude-sonnet-4-5"
    assert turn["turn_id"] in s.deductions()  # settled as hosted


def test_hosted_fallback_key_without_model_fails_closed(
    app_settings: Any, monkeypatch: pytest.MonkeyPatch, spine: Spine
) -> None:
    monkeypatch.delenv("OPENROUTER_FALLBACK_MODEL", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", HOSTED_OPENROUTER_KEY)
    from fastapi.testclient import TestClient

    from afterworlds.api.app import create_app

    with TestClient(create_app(app_settings)) as client:
        s = Spine(client, spine.provider)
        s.seed_hosted()
        story_id = s.create("branching")
        s.setup_branching(story_id, "freeform_only")
        begun = s.begin(story_id)
        assert begun["outcome"] == "not_started"
        assert "openrouter_fallback_model is missing" in (
            begun["turn"]["pipeline_error_summary"]
        )
