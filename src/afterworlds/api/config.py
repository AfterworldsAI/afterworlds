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
    """Load settings from environment, falling back to product defaults."""
    return ApiSettings(
        database_url=os.environ.get("AFTERWORLDS_DATABASE_URL", _DEFAULT_DB_URL),
        frontend_dist_dir=Path(
            os.environ.get("AFTERWORLDS_FRONTEND_DIST", str(_DEFAULT_FRONTEND_DIST))
        ),
    )
