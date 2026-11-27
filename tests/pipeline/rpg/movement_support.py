"""The accepted SRD 5.2.1 oracle as a movement fact lookup, for tests.

Loading the full runtime authority index takes close to a minute, so tests
read the same accepted oracle the index is built from and rebuild typed facts
with the package's own strict ``fact_from_payload``.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from afterworlds.ingestion.mechanical.representation import fact_from_payload
from afterworlds.pipeline.rpg.movement import MovementRules, load_rules

ORACLE = (
    Path(__file__).resolve().parents[3]
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json"
)
PROSE_DIR = (
    Path(__file__).resolve().parents[3] / "docs/sources/community/dnd-5e-srd-markdown"
)


@cache
def _components() -> dict[tuple[str, str], tuple[object, ...]]:
    data = json.loads(ORACLE.read_text(encoding="utf-8"))
    out: dict[tuple[str, str], tuple[object, ...]] = {}
    for comp in data["representation"]["components"]:
        out[(comp["record_key"], comp["semantic_key"])] = tuple(
            fact_from_payload(f) for f in comp["facts"]
        )
    return out


def oracle_lookup(record: str, component: str) -> tuple[object, ...]:
    return _components().get((record, component), ())


def has_component(record: str, component: str) -> bool:
    return (record, component) in _components()


@cache
def rules() -> MovementRules:
    return load_rules(oracle_lookup)
