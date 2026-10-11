"""Shared helpers for the CRD Issue 2b G1 candidate scripts.

REVIEW MATERIAL. Nothing here accepts, records, publishes or activates
anything. Run every script from the repository root with the clone's own venv.
The isolated release store is built by
``issue-5c-release-order-candidate/scripts/build.py`` into ``G1_WORK/rel``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import os
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

REPO = Path.cwd()
sys.path.insert(0, str(REPO / "src"))

NOTES = REPO / ".claude/review-notes"
HERE = NOTES / "issue-2b-g1-candidate"
G1_WORK = Path(os.environ.get("G1_WORK", REPO.parent / "g1-work"))
STORE = G1_WORK / "rel/afterworlds.db"

PRIOR_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b.json"
)
PRIOR_SHA256 = "def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c"
GENERATOR_PATH = NOTES / "issue-5d-equipment-cited-targets-generator.py"
BATCH = "equipment"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def generator() -> ModuleType:
    """The recorded Equipment generator, unmodified."""
    return load_module("equipment_cited_targets_generator", GENERATOR_PATH)


#: The three references the accepted class-eligibility replacement removed
#: (``issue-5d-equipment-class-eligibility-REPLACEMENT.py``, ``REMOVED``),
#: restated here so the control does not load that script's whole chain.
CLASS_ELIGIBILITY_REMOVED = (
    ("equipment.adventuring_gear.holy_symbol", "holy_symbol", "Cleric or Paladin"),
    ("equipment.adventuring_gear.druidic_focus", "druidic_focus", "Druid or Ranger"),
    (
        "equipment.adventuring_gear.arcane_focus",
        "arcane_focus",
        "Sorcerer, Warlock, or Wizard",
    ),
)


def class_eligibility_edited(base: Any) -> Any:
    """*base* without the three removed references, as the accepted edit."""
    removed = {(r, c): p for r, c, p in CLASS_ELIGIBILITY_REMOVED}
    seen: Counter[tuple[str, str]] = Counter()

    def refs(c: Any) -> tuple[tuple[str, Any], ...]:
        where = (c.record or base.record_key(c.entry), c.key)
        if where not in removed:
            return tuple(c.refs)
        seen[where] += 1
        return tuple((x, t) for x, t in c.refs if x != removed[where])

    components = tuple(dataclasses.replace(c, refs=refs(c)) for c in base.components)
    assert seen == Counter(removed.keys()), seen
    return dataclasses.replace(base, components=components)


def build_proposal(entry_batch: Any) -> Any:
    """Build *entry_batch* natively against the isolated release store."""
    from afterworlds.ingestion.mechanical.authoring import build_entry_batch
    from afterworlds.ingestion.mechanical.bound_corpus import (
        published_release_binding,
    )
    from afterworlds.persistence.database import (
        create_engine,
        create_session_factory,
    )

    engine = create_engine(f"sqlite:///{STORE}")
    try:
        with create_session_factory(engine)() as session:
            binding = published_release_binding(session)
            return build_entry_batch(session, entry_batch, binding)
    finally:
        engine.dispose()


G1_GENERATOR_PATH = HERE / "issue-2b-g1-equipment-generator.py"


def g1_generator() -> ModuleType:
    """The G1 candidate generator (the recorded one plus the G1 changes)."""
    return load_module("issue_2b_g1_equipment_generator", G1_GENERATOR_PATH)
