"""Binding Decision 2: route handlers translate HTTP <-> typed service calls only.

Binding Decision 4 explicitly requires the turns route to call
``OrchestratorService.orchestrate_turn`` and the ``EntitlementService`` gate/
settle methods directly ("Issue 19 makes these calls") -- so those two
packages are NOT banned here. What must never leak into route modules is
mode-specific pipeline internals (only the orchestrator itself may invoke
RPG/Branching/Writing pass services) and intent classification (no parallel
intent inference per Binding Decision 3).
"""

from __future__ import annotations

import ast
from pathlib import Path

_ROUTES_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "afterworlds" / "api" / "routes"
)

_DISALLOWED_MODULE_PREFIXES = (
    "afterworlds.pipeline.rpg",
    "afterworlds.pipeline.branching",
    "afterworlds.pipeline.writing",
    "afterworlds.services.intent_classifier",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_route_modules_import_no_disallowed_policy_symbols() -> None:
    route_files = sorted(_ROUTES_DIR.glob("*.py"))
    assert route_files, "expected route modules to exist"
    for path in route_files:
        if path.name == "__init__.py":
            continue
        modules = _imported_modules(path)
        for module in modules:
            for prefix in _DISALLOWED_MODULE_PREFIXES:
                assert not module.startswith(prefix), (
                    f"{path.name} imports {module} directly; route handlers must "
                    "stay thin (Binding Decision 2) -- route through a typed "
                    "seam module (api/access_path.py, api/story_bootstrap.py, "
                    "etc.), not the pipeline/entitlement package directly"
                )


# DoR-E single-choke-point: route modules must never re-derive runnable-path
# status themselves -- only ``api/access_path.py::select_access_path`` reads
# these two fields. A route touching them directly would be reimplementing
# the matrix instead of calling the one tested helper.
_ACCESS_PATH_STATUS_FIELDS = ("hosted_turn_available", "byok_turn_available")


def test_route_modules_never_read_raw_entitlement_status_fields() -> None:
    route_files = sorted(_ROUTES_DIR.glob("*.py"))
    for path in route_files:
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        for field in _ACCESS_PATH_STATUS_FIELDS:
            assert field not in source, (
                f"{path.name} references AccessPathStatus.{field} directly; "
                "the DoR-E runnable-path matrix lives only in "
                "api/access_path.py::select_access_path (single choke point)"
            )
