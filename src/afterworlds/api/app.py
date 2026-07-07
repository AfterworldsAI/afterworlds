"""``create_app()`` -- the single FastAPI construction choke point.

Binding Decision 12: one factory owning service wiring/DI, one config
source, one static-serving mount. Constructing services/clients/base URLs
anywhere else is a defect.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import every ORM module so its tables register on Base.metadata before
# create_all/health-check touches the engine.
import afterworlds.persistence.orm.character_sheet  # noqa: F401
import afterworlds.persistence.orm.identity  # noqa: F401
import afterworlds.persistence.orm.node  # noqa: F401
import afterworlds.persistence.orm.retrieval  # noqa: F401
import afterworlds.persistence.orm.session_state  # noqa: F401
import afterworlds.persistence.orm.state  # noqa: F401
import afterworlds.persistence.orm.story  # noqa: F401
from afterworlds.api.config import ApiSettings, load_settings
from afterworlds.api.deps import provision_sojourner_id
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.pipeline_wiring import build_orchestrator
from afterworlds.api.routes.health import router as health_router
from afterworlds.api.routes.stories import router as stories_router
from afterworlds.api.routes.turns import router as turns_router
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.provider import ByokCredentialReadinessProvider
from afterworlds.pipeline.provider.credentials import make_credential_store

logger = logging.getLogger("afterworlds.api")


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Build and wire the FastAPI app.

    Product configuration: single uvicorn worker (Binding Decision 8), no
    CORS middleware (DoR-C), built frontend served via StaticFiles.
    """
    settings = settings or load_settings()
    app = FastAPI(title="Afterworlds API")

    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.sojourner_id = provision_sojourner_id(session_factory)
    # Per-story turn-submission lock registry (Binding Decision 8). A single
    # choke point created once here, not per-request.
    story_locks: dict[UUID, asyncio.Lock] = defaultdict(asyncio.Lock)
    app.state.story_locks = story_locks
    app.state.orchestrator = build_orchestrator(session_factory)
    # DoR-E: the readiness seam is constructed once here and consumed only
    # inside the access-path selection helper (api/access_path.py callers) --
    # never in a route handler directly.
    app.state.byok_readiness_provider = ByokCredentialReadinessProvider(
        make_credential_store(), session_factory
    )

    app.include_router(health_router)
    app.include_router(stories_router)
    app.include_router(turns_router)

    @app.exception_handler(ApiErrorResponse)
    async def _api_error_handler(
        request: Request, exc: ApiErrorResponse
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.error.model_dump())

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception in %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error_code": ApiErrorCode.INTERNAL_ERROR.value,
                "message": "An internal error occurred.",
                "detail": None,
                "schema_version": 1,
            },
        )

    if settings.frontend_dist_dir.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(settings.frontend_dist_dir), html=True),
            name="frontend",
        )

    return app
