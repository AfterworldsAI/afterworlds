"""Single config source shared by ``create_app()`` and the uvicorn entry point.

Binding Decision 12: one config source, not one per construction site.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DB_URL = "sqlite:///./afterworlds.db"
_DEFAULT_FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


@dataclass(frozen=True)
class ApiSettings:
    """Runtime configuration for the Afterworlds API."""

    database_url: str
    frontend_dist_dir: Path
    schema_version: int = 1


def load_settings() -> ApiSettings:
    """Load settings from environment, falling back to product defaults.

    Round 6 P2 remediation (PR #126): ``_DEFAULT_FRONTEND_DIST`` is a
    repo-relative path (``parents[3]``) that does not exist in a
    wheel/site-packages install -- ``app.py``'s mount is a bare
    ``if dist.is_dir(): mount(...)`` with no ``else``, so an installed
    package would previously boot an API-only server while silently never
    serving the Issue 19 product UI. Packaging the built frontend under the
    Python package (``importlib.resources``) is deferred -- see
    Architecture Notes -- so this fails loudly instead: a production launch
    (no ``AFTERWORLDS_FRONTEND_DIST`` override, and the default repo path
    absent) raises here rather than starting a UI-less server that claims
    to serve the frontend. An explicit override is trusted as-is -- an
    operator who sets it has made a deliberate choice, even if the path
    does not exist yet at load time.
    """
    override = os.environ.get("AFTERWORLDS_FRONTEND_DIST")
    if override is None and not _DEFAULT_FRONTEND_DIST.is_dir():
        raise RuntimeError(
            "No frontend build found at the default location "
            f"({_DEFAULT_FRONTEND_DIST}) and AFTERWORLDS_FRONTEND_DIST is not "
            "set. Build the frontend (npm run build in frontend/) or set "
            "AFTERWORLDS_FRONTEND_DIST to a built frontend/dist directory."
        )
    return ApiSettings(
        database_url=os.environ.get("AFTERWORLDS_DATABASE_URL", _DEFAULT_DB_URL),
        frontend_dist_dir=Path(override) if override else _DEFAULT_FRONTEND_DIST,
    )
