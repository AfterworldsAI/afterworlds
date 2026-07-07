"""Binding Decision 2: route handlers translate HTTP <-> typed service calls only.

No orchestration, provider, entitlement, mode, intent, or option-resolution
policy may live in route modules. This is enforced by asserting route
modules import no symbols from the disallowed subpackages except through the
narrow, named allowlist (helpers Issue 19 itself owns).
"""

from __future__ import annotations

import ast
from pathlib import Path

_ROUTES_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "afterworlds" / "api" / "routes"
)

_DISALLOWED_MODULE_PREFIXES = (
    "afterworlds.pipeline.orchestrator",
    "afterworlds.pipeline.rpg",
    "afterworlds.pipeline.branching",
    "afterworlds.pipeline.writing",
    "afterworlds.entitlement",
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
