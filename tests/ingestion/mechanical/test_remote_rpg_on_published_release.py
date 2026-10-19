"""Prerequisite #205 (review R4): remote RPG on provisioned shared Rules.

A fresh remote deployment has no Rules data. The supported provisioning path
(``python -m afterworlds.remote.rules_provisioning``) runs the existing
publication owners under the deployment's store locks; this proves it on
disposable stores, then plays an own-account RPG Story through the remote
API -- setup (Rules Package selection), a player-rolled attack, reload and
resume -- while another account is denied every step.

Only the source candidate (the session's real build), the embedding function
(deterministic fake, no model download) and the GameMaster's adjudication
proposals are substituted; publication, routes, sequence service, dice
validation and settlement are the production ones.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
import sqlalchemy as sa

from afterworlds.ingestion.corpus.pipeline import CandidateRelease
from afterworlds.models.enums import DiceHandling, RpgPlayStatus
from afterworlds.persistence.crud.session_state import (
    get_rpg_session_state_by_story,
    update_rpg_session_state,
)
from afterworlds.pipeline.retrieval.embedding import DeterministicFakeEmbeddingFunction
from afterworlds.remote import rules_provisioning
from afterworlds.services.dnd5e_state import service
from tests.api._remote import RemoteHarness, make_remote, remote_settings
from tests.api.test_remote_isolation import _seed_hosted
from tests.ingestion.mechanical.sequence_stack import scripted_dice
from tests.ingestion.mechanical.test_bounded_d20_on_published_release import (
    NOW,
    PACKAGE,
    gm,
)
from tests.ingestion.mechanical.test_rpg_actions_on_published_release import (
    _advanced,
    _attack,
    _begin,
    _pending,
    _resume,
    _roll,
    _turn,
    _wolf,
)
from tests.services.dnd5e_state.builders import complete_character, real_index

__all__ = ["gm"]  # fixture used by pytest


@pytest.fixture()
def provisioned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    source_candidate: CandidateRelease,
    capsys: pytest.CaptureFixture[str],
) -> Path:
    """A fresh remote deployment provisioned through the supported command."""
    settings = remote_settings(tmp_path)
    for name, value in {
        "AFTERWORLDS_DEPLOYMENT": "remote",
        "AFTERWORLDS_DATABASE_URL": settings.database_url,
        "AFTERWORLDS_CONTROL_DATABASE_URL": str(settings.control_database_url),
        "AFTERWORLDS_NOTICE_OUTBOX_DIR": str(settings.notice_outbox_dir),
        "AFTERWORLDS_FRONTEND_DIST": str(tmp_path / "no_frontend"),
        "AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY": str(tmp_path / "chroma"),
        "AFTERWORLDS_FAKE_PROVIDER": "1",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        rules_provisioning, "build_source_candidate", lambda *_a, **_k: source_candidate
    )
    monkeypatch.setattr(
        rules_provisioning, "_embedding_function", DeterministicFakeEmbeddingFunction
    )
    make_remote(tmp_path).close()  # fresh, bound, empty deployment

    # Beside a serving app the command is refused, touching nothing.
    serving = make_remote(tmp_path)
    try:
        assert rules_provisioning.main([]) == 1
        assert "another process" in capsys.readouterr().err
    finally:
        serving.close()

    assert rules_provisioning.main([]) == 0
    first = capsys.readouterr().out
    assert "corpus published, authority published" in first
    assert rules_provisioning.main([]) == 0  # idempotent
    assert "corpus reused, authority already_published" in capsys.readouterr().out
    return tmp_path


def _in_play(remote: RemoteHarness, story: str) -> None:
    """The DB-level character/IN_PLAY seeding the backend product proofs use."""
    with remote.app.state.session_factory() as s:
        state = get_rpg_session_state_by_story(s, UUID(story))
        assert state is not None
        service.create_character(
            s,
            state.character_sheet_id,
            PACKAGE,
            complete_character(real_index(), "classes.wizard", 3),
            now=NOW,
        )
        update_rpg_session_state(
            s,
            state.model_copy(
                update={
                    "play_status": RpgPlayStatus.IN_PLAY,
                    "dice_handling": DiceHandling.PLAYER_ROLLS,
                    "gm_cheating": False,
                }
            ),
        )
        s.commit()


def test_own_account_rpg_runs_on_provisioned_rules_and_stays_isolated(
    provisioned: Path,
    gm: list[list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def faces(expression: str) -> tuple[int, ...]:
        raise AssertionError(f"the backend rolled {expression}")

    scripted_dice(monkeypatch, faces)
    remote = make_remote(provisioned)
    try:
        a = remote.enroll("a@example.test")
        b = remote.enroll("b@example.test")
        _seed_hosted(remote, remote.account_id(a))

        # Setup: the provisioned shared package is offered and selectable.
        setup_story = a.post(
            "/api/stories",
            json={"title": "Setup", "mode": "rpg", "character_name": "Ilse"},
        ).json()["story_id"]
        # The GM's setup turn proposes the world; confirming it opens the
        # character phase, where the provisioned shared package is offered.
        assert (
            _turn(a, setup_story, "A storm-wracked archipelago.")["disposition"]
            == "delivered"
        )
        world = a.get(f"/api/stories/{setup_story}/rpg/setup").json()
        assert world["phase"] == "world_setup", world
        confirmed = a.post(
            f"/api/stories/{setup_story}/rpg/setup/confirm-world",
            json={"expected_world_revision": world["world_target"]["world_revision"]},
        )
        assert confirmed.status_code == 200, confirmed.text
        offered = confirmed.json()["packages"]
        assert [o["package_uuid"] for o in offered] == [str(PACKAGE)]
        chosen = a.post(
            f"/api/stories/{setup_story}/rpg/setup/rules-package",
            json={"package_uuid": str(PACKAGE)},
        )
        assert chosen.status_code == 200, chosen.text
        assert b.get(f"/api/stories/{setup_story}/rpg/setup").status_code == 404
        assert (
            b.post(
                f"/api/stories/{setup_story}/rpg/setup/rules-package",
                json={"package_uuid": str(PACKAGE)},
            ).status_code
            == 404
        )

        # Action: a player-rolled attack becomes a pending interaction.
        story = a.post(
            "/api/stories",
            json={"title": "Play", "mode": "rpg", "character_name": "Ilse"},
        ).json()["story_id"]
        _in_play(remote, story)
        wolf = _wolf(a, story, hp=30)
        gm.append(
            [
                _begin(a, story),
                _attack(a, story, wolf, "equipment.weapons.club", "Club attack"),
            ]
        )
        assert _turn(a, story, "I swing.")["disposition"] == "delivered"
        attack = _pending(a, story)["pending_roll"]
        # B can neither see nor act on it.
        assert b.get(f"/api/stories/{story}/rpg/pending-interaction").status_code == 404
        assert _roll(b, story, attack, 15).status_code == 404
        damage = _advanced(_roll(a, story, attack, 15))["pending_roll"]
        ready = _advanced(_roll(a, story, damage, 3))
        assert ready["interaction_phase"] == "ready_for_narration", ready
        # Recovery: a reload finds the same ready sequence; resume narrates it.
        reloaded = _pending(a, story)
        assert reloaded["sequence_id"] == ready["sequence_id"]
        assert _resume(b, story, ready["sequence_id"]).status_code == 404
        resumed = _resume(a, story, ready["sequence_id"])
        assert resumed.status_code == 200, resumed.text
        assert resumed.json()["disposition"] == "delivered"
        assert _pending(a, story) is None
        # Shared Rules stayed shared: one package, no account ownership row.
        with remote.app.state.session_factory() as s:
            owned = s.execute(
                sa.text(
                    "SELECT COUNT(*) FROM account_resources WHERE resource_id = :p"
                ),
                {"p": str(PACKAGE)},
            ).scalar()
        assert owned == 0
        assert uuid.UUID(remote.account_id(a))  # A's session is intact
    finally:
        remote.close()
