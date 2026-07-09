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
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from afterworlds.api.config import ApiSettings, load_settings
from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.api.deps import provision_sojourner_id
from afterworlds.api.errors import ApiError, ApiErrorCode, ApiErrorResponse
from afterworlds.api.pipeline_wiring import build_orchestrator
from afterworlds.api.routes.health import router as health_router
from afterworlds.api.routes.personas import router as personas_router
from afterworlds.api.routes.setup import router as setup_router
from afterworlds.api.routes.stories import router as stories_router
from afterworlds.api.routes.turns import router as turns_router
from afterworlds.api.routes.visible_state import router as visible_state_router
from afterworlds.persistence.database import create_engine, create_session_factory
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

    # P1 remediation (PR #126 review round 1): apply the real Alembic
    # migrations rather than Base.metadata.create_all(), which silently
    # skipped Alembic-only DDL (append-only audit triggers) and, on a fresh
    # DB, any table whose ORM module app.py did not happen to import. See
    # db_bootstrap.py's docstring for the full defect writeup.
    upgrade_to_head(settings.database_url)
    engine = create_engine(settings.database_url)
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
    app.include_router(visible_state_router)
    app.include_router(setup_router)
    app.include_router(personas_router)

    @app.exception_handler(ApiErrorResponse)
    async def _api_error_handler(
        request: Request, exc: ApiErrorResponse
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.error.model_dump())

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # P2 remediation (PR #126 review round 1): FastAPI/Pydantic
        # validation failures (extra="forbid" rejections, invalid setup
        # enums, malformed UUID path params, a non-integer transcript
        # limit) previously fell through to FastAPI's default {"detail":
        # [...]} 422 body instead of the single ApiError envelope (Binding
        # Decision 10). detail carries only the dotted field path and a
        # human-safe message per offending field -- never exc.errors()'s
        # raw "input" value, which can echo back client-supplied data.
        detail = {
            ".".join(str(part) for part in error["loc"]): str(error["msg"])
            for error in exc.errors()
        }
        error = ApiError(
            error_code=ApiErrorCode.VALIDATION_FAILED,
            message="Request validation failed.",
            detail=detail or None,
        )
        return JSONResponse(status_code=422, content=error.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # P2 remediation (PR #126): framework-raised HTTP errors -- an
        # unmatched /api/... route, a wrong-method 405, or the StaticFiles
        # mount's own 404 for an unknown asset path -- previously returned
        # FastAPI's default {"detail": ...} body instead of the single
        # ApiError envelope (Binding Decision 10). FastAPI's own
        # HTTPException subclasses Starlette's, so this one registration
        # catches both. Nothing in this codebase raises HTTPException
        # directly (grepped); every in-app failure already raises
        # ApiErrorResponse, so exc.detail here is always framework text,
        # never client- or handler-supplied.
        if exc.status_code == 404:
            error = ApiError(error_code=ApiErrorCode.NOT_FOUND, message="Not found.")
        elif exc.status_code == 405:
            error = ApiError(
                error_code=ApiErrorCode.VALIDATION_FAILED,
                message="Method not allowed.",
            )
        elif 400 <= exc.status_code < 500:
            message = str(exc.detail) if exc.detail else "Request failed."
            error = ApiError(error_code=ApiErrorCode.VALIDATION_FAILED, message=message)
        else:
            error = ApiError(
                error_code=ApiErrorCode.INTERNAL_ERROR,
                message="An internal error occurred.",
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=error.model_dump(),
            headers=dict(exc.headers) if exc.headers else None,
        )

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
