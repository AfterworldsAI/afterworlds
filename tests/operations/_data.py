"""Shared CRD Issue 22 fixtures: real Stories with delivered turns, planted
content-bearing history in the orphan-prone and trigger-protected tables,
and raw-store probes (row counts and byte scans) for deletion proofs."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.operations.vectors import story_chunk_counter
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig

SECRET = "sk-ant-SYNTHETIC-CRD22-SECRET-91b2"  # pragma: allowlist secret


def play_branching(c: TestClient, title: str, turn: str) -> str:
    """A Branching Story in play with one delivered (fake-provider) turn."""
    created = c.post("/api/stories", json={"title": title, "mode": "branching"})
    assert created.status_code == 201, created.text
    sid = str(created.json()["story_id"])
    resp = c.post(
        f"/api/stories/{sid}/setup",
        json={
            "mode": "branching",
            "interaction_style": "freeform_only",
            "branching_cadence": "balanced",
        },
    )
    assert resp.status_code == 200, resp.text
    assert c.post(f"/api/stories/{sid}/begin").status_code == 200
    resp = c.post(f"/api/stories/{sid}/turns", json={"user_input": turn})
    assert resp.status_code == 200, resp.text
    return sid


def plant(content: sessionmaker[Session], story_id: str, marker: str) -> dict[str, str]:
    """Content-bearing rows the generic Story CRUD would not remove: an old
    canon value (no FK), a hidden roll and an action event (triggers), a
    refusal row keyed only by Turn, and an orphan Turn (``node_id`` NULL)
    reachable only through a Story-scoped edge."""
    engine = content.kw["bind"]
    orphan = str(uuid.uuid4())
    with engine.begin() as conn:
        turn = conn.execute(
            sa.text(
                "SELECT t.turn_id FROM turns t JOIN nodes n ON n.node_id = t.node_id "
                "JOIN chapters c ON c.chapter_id = n.chapter_id "
                "JOIN arcs a ON a.arc_id = c.arc_id WHERE a.story_id = :s LIMIT 1"
            ),
            {"s": story_id},
        ).scalar_one()
        conn.execute(
            sa.text(
                "INSERT INTO sb_dynamic_field_history (history_id, entity_type,"
                " entity_id, field_name, old_value, changed_at, source_turn_id,"
                " story_id) VALUES (:h, 'cast', :e, 'description', :v,"
                " '2026-01-01T00:00:00+00:00', :t, :s)"
            ),
            {
                "h": str(uuid.uuid4()),
                "e": str(uuid.uuid4()),
                "v": json.dumps(f"old canon {marker}"),
                "t": turn,
                "s": story_id,
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO rpg_roll_audit (turn_id, story_id, session_id,"
                " character_id, check_label, visibility, expression, raw_rolls_json,"
                " modifiers_json, total, outcome, source, gm_cheating_at_roll,"
                " sheet_effects_json, created_at) VALUES (:t, :s, :x, :x, :label,"
                " 'hidden', '1d20', '[17]', '[]', 17, 'success', 'backend', 0, '[]',"
                " '2026-01-01T00:00:00+00:00')"
            ),
            {
                "t": turn,
                "s": story_id,
                "x": str(uuid.uuid4()),
                "label": f"hidden {marker}",
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO action_resolution_events (event_id, sequence_id, step_id,"
                " story_id, session_id, character_id, event_order, kind,"
                " mechanical_provenance, provisional_effects_json, created_at,"
                " payload_json, schema_version) VALUES (:e, :x, :x, :s, :x, :x, 1,"
                " 'roll', '{}', '[]', '2026-01-01T00:00:00+00:00', :p, 1)"
            ),
            {
                "e": str(uuid.uuid4()),
                "x": str(uuid.uuid4()),
                "s": story_id,
                "p": json.dumps({"hidden": marker}),
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO provider_refusal_log (turn_id, sojourner_id, pass_id,"
                " primary_provider_name, primary_model_identifier, refusal_category,"
                " fallback_outcome, created_at) VALUES (:t, NULL, 'writer', 'x', 'm',"
                " 'policy', 'none', '2026-01-01 00:00:00')"
            ),
            {"t": turn},
        )
        conn.execute(
            sa.text(
                "INSERT INTO turns (turn_id, node_id, user_input, assistant_output,"
                " timestamp, intent_classification) VALUES (:t, NULL, :u, :o,"
                " '2026-01-01T00:00:00+00:00', 'in_world_action')"
            ),
            {"t": orphan, "u": f"orphan {marker}", "o": f"orphan prose {marker}"},
        )
        conn.execute(
            sa.text(
                "INSERT INTO rpg_turn_edges (edge_id, story_id, sequence, turn_id,"
                " kind, subject_kind, subject_id, turn_instance,"
                " coordination_revision, recorded_at) VALUES (:e, :s, 1, :t, 'begin',"
                " 'character', :x, 1, 1, '2026-01-01T00:00:00+00:00')"
            ),
            {
                "e": str(uuid.uuid4()),
                "s": story_id,
                "t": orphan,
                "x": str(uuid.uuid4()),
            },
        )
    return {"turn": str(turn), "orphan": orphan}


def chunk_count(story_id: str) -> int:
    config = RetrievalMemoryConfig.from_env()
    return story_chunk_counter(lambda: build_chroma_client(config))(story_id)


def rows_with(content: sessionmaker[Session], needle: str) -> list[str]:
    """Tables whose rows still contain *needle* anywhere (logical scan)."""
    hits = []
    engine = content.kw["bind"]
    inspector = sa.inspect(engine)
    with engine.connect() as conn:
        for table in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns(table)]
            expr = " || '|' || ".join(
                f"coalesce(CAST(\"{c}\" AS TEXT), '')" for c in cols
            )
            if conn.execute(
                sa.text(f"SELECT count(*) FROM {table} WHERE ({expr}) LIKE :n"),
                {"n": f"%{needle}%"},
            ).scalar():
                hits.append(table)
    return hits


def files_with(root: Path, needle: str) -> list[str]:
    """Raw byte scan of every file under *root* (journals, free pages,
    vector segments)."""
    data = needle.encode()
    hits = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            body = p.read_bytes()
        except PermissionError:  # an OS-locked lock file holds no content
            continue
        if data in body:
            hits.append(str(p.relative_to(root)))
    return sorted(hits)


def unzip(body: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        return {
            name: (
                json.loads(archive.read(name))
                if name.endswith(".json")
                else archive.read(name).decode()
            )
            for name in archive.namelist()
        }
