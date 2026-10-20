"""``create_app()`` -- the single FastAPI construction choke point.

Binding Decision 12: one factory owning service wiring/DI, one config
source, one static-serving mount. Constructing services/clients/base URLs
anywhere else is a defect.
"""

from __future__ import annotations

import asyncio
import contextlib
import gc
import logging
import tempfile
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from chromadb.api.shared_system_client import SharedSystemClient
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from afterworlds.api.access_path import ServerHostedByokUnavailable
from afterworlds.api.account import ACCOUNT_PATH_PREFIX, account_validation_location
from afterworlds.api.config import ApiSettings, load_settings
from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.api.deps import provision_sojourner_id
from afterworlds.api.errors import ApiError, ApiErrorCode, ApiErrorResponse
from afterworlds.api.fake_pipeline import fake_credential_check
from afterworlds.api.pipeline_wiring import build_pipeline, fake_provider_enabled
from afterworlds.api.remote_access import authorize_story, enforce_access
from afterworlds.api.routes.account import router as account_router
from afterworlds.api.routes.admin import router as admin_router
from afterworlds.api.routes.auth import router as auth_router
from afterworlds.api.routes.data_requests import router as data_requests_router
from afterworlds.api.routes.health import router as health_router
from afterworlds.api.routes.personas import router as personas_router
from afterworlds.api.routes.rpg_actions import router as rpg_actions_router
from afterworlds.api.routes.rpg_setup import router as rpg_setup_router
from afterworlds.api.routes.setup import router as setup_router
from afterworlds.api.routes.stories import router as stories_router
from afterworlds.api.routes.stories import story_router
from afterworlds.api.routes.turns import router as turns_router
from afterworlds.api.routes.visible_state import router as visible_state_router
from afterworlds.api.rpg_actions import RpgActions
from afterworlds.operations.anomalies import AnomalyService
from afterworlds.operations.service import DataRequestService
from afterworlds.operations.support import SupportService
from afterworlds.operations.vectors import story_chunk_deleter
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.pipeline.provider import (
    ByokCredentialReadinessProvider,
    ByokSettingsService,
)
from afterworlds.pipeline.provider.credentials import make_credential_store
from afterworlds.pipeline.retrieval.client import build_chroma_client
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig
from afterworlds.remote.access import AccessPolicy, IdentityUnavailable, ScopedSeam
from afterworlds.remote.control_store import open_control_store, utc_now
from afterworlds.remote.fence import AccountFence
from afterworlds.remote.identity import IdentityService
from afterworlds.remote.notices import OutboxDirectoryTransport
from afterworlds.remote.storage import (
    StoreRefused,
    acquire_control_lock,
    acquire_store_lock,
    acquire_vector_lock,
    bind_vector_store,
    check_content_store_before_migration,
    check_vector_store,
    complete_remote_initialization,
    initialize_remote_content_store,
    pending_restores,
    refuse_multiply_linked,
    refuse_notice_store_exposure,
    refuse_public_backups,
    refuse_public_overlap,
    refuse_store_aliasing,
    sqlite_path,
)
from afterworlds.services.dnd5e_state.leases import (
    clear_orphans as clear_orphan_turn_leases,
)

logger = logging.getLogger("afterworlds.api")


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Build and wire the FastAPI app.

    Product configuration: single uvicorn worker (Binding Decision 8), no
    CORS middleware (DoR-C), built frontend served via StaticFiles.

    A construction that fails at any step releases everything it acquired
    (store locks, the content engine, embedded Chroma's clients) and
    re-raises the original error, so the same process can retry.
    """
    settings = settings or load_settings()
    # Prerequisite #205: every /api route passes the one access choke point.
    app = FastAPI(title="Afterworlds API", dependencies=[Depends(enforce_access)])
    app.state.store_lock = None
    app.state.vector_lock = None
    app.state.control_lock = None
    app.state.engine = None
    # Chroma clients that already exist in this process (and their refcounts)
    # are not this construction's: only systems it creates are its own.
    chroma_before = {
        ident: SharedSystemClient._identifier_to_refcount.get(ident, 0)
        for ident in SharedSystemClient._identifier_to_system
    }
    try:
        _wire_app(app, settings)
    except BaseException:
        _release_construction(app, chroma_before)
        raise
    return app


def _release_construction(app: FastAPI, chroma_before: dict[str, int]) -> None:
    """Best-effort release after a failed construction; never masks it.

    Releases only what this construction acquired or created: the locks and
    engines it holds (a failed acquisition grants none) and the Chroma systems
    that appeared during it. Pre-existing clients keep running, with their
    refcounts restored."""
    control = getattr(app.state, "control_factory", None)
    for engine in (app.state.engine, control.kw["bind"] if control else None):
        if engine is not None:
            with contextlib.suppress(Exception):
                engine.dispose()
    app.state.orchestrator = None
    app.state.rpg_actions = None
    with contextlib.suppress(Exception):
        # Stop (not merely forget) the embedded Chroma systems this
        # construction created, and undo its refcounts on existing ones.
        # shortcut: reads chromadb's private registries, verified on the
        # exact pin chromadb==1.5.9 (pyproject.toml); any pin change needs a
        # deliberate compatibility review here.
        systems = SharedSystemClient._identifier_to_system
        refcounts = SharedSystemClient._identifier_to_refcount
        for ident in [i for i in systems if i not in chroma_before]:
            refcounts.pop(ident, None)
            systems.pop(ident).stop()
        for ident, count in chroma_before.items():
            if ident in refcounts:
                refcounts[ident] = count
    gc.collect()
    for name in ("control_lock", "vector_lock", "store_lock"):
        handle = getattr(app.state, name)
        if handle is not None:
            with contextlib.suppress(Exception):
                handle.close()


def export_dir(settings: ApiSettings) -> Path:
    """Where service-managed export artifacts live (CRD Issue 22)."""
    if settings.export_dir is not None:
        return settings.export_dir
    try:
        db = sqlite_path(settings.database_url)
    except StoreRefused:  # an in-memory test store has no directory
        return Path(tempfile.gettempdir()) / "afterworlds-exports"
    return db.with_name(db.name + ".exports")


def _wire_app(app: FastAPI, settings: ApiSettings) -> None:
    remote = settings.deployment == "remote"

    if remote:
        # ADR-021 D6/D7: one writer process, and only a fresh or this
        # deployment's own store -- checked before any migration touches it.
        assert settings.control_database_url is not None
        outbox = settings.notice_outbox_dir
        assert outbox is not None
        # A refused or failed start keeps neither store locked or open
        # (create_app releases whatever was acquired).
        vector_dir = Path(RetrievalMemoryConfig.from_env().persist_directory)
        refuse_notice_store_exposure(outbox, vector_dir, settings.frontend_dist_dir)
        # The public static root is served unauthenticated: no live store may
        # be in or around it (checked before any store is created).
        private: list[tuple[Path | str, str]] = [
            (export_dir(settings), "the export artifact directory"),
            (sqlite_path(settings.database_url), "the content store"),
            (vector_dir, "the live vector store"),
            (outbox, "the notice outbox"),
        ]
        with contextlib.suppress(StoreRefused):  # a non-file control store
            private.append(
                (sqlite_path(settings.control_database_url), "the control store")
            )
        refuse_public_overlap(settings.frontend_dist_dir, private)
        # One physical file as both stores is refused first (a path check).
        refuse_store_aliasing(settings.database_url, settings.control_database_url)
        refuse_multiply_linked(sqlite_path(settings.database_url), "the content store")
        control_path: Path | None = None
        with contextlib.suppress(StoreRefused):  # a non-file control store
            control_path = sqlite_path(settings.control_database_url)
        if control_path is not None:
            refuse_multiply_linked(control_path, "the control store")
        app.state.store_lock = acquire_store_lock(settings.database_url)
        app.state.vector_lock = acquire_vector_lock(vector_dir)
        app.state.control_lock = acquire_control_lock(settings.control_database_url)
        control_factory = open_control_store(settings.control_database_url)
        app.state.control_factory = control_factory
        # ...nor any undisposed backup, before anything is mounted.
        refuse_public_backups(control_factory, settings.frontend_dist_dir)
        # A fresh deployment's identity is recorded before anything is
        # created; an interrupted initialization resumes that identity.
        initializing = check_content_store_before_migration(
            settings.database_url, vector_dir, control_factory, now=utc_now()
        )
        if pending_restores(control_factory):
            raise StoreRefused(
                "a restored content store is awaiting deletion-suppression "
                "enforcement and verification; it cannot be served yet"
            )
        check_vector_store(vector_dir, control_factory)
        upgrade_to_head(settings.database_url)
        engine = app.state.engine = create_engine(settings.database_url)
        if initializing is not None:
            initialize_remote_content_store(
                create_session_factory(engine), initializing, now=utc_now()
            )
            bind_vector_store(vector_dir, initializing)
            complete_remote_initialization(control_factory, initializing)
    else:
        # P1 remediation (PR #126 review round 1): apply the real Alembic
        # migrations rather than Base.metadata.create_all(), which silently
        # skipped Alembic-only DDL (append-only audit triggers) and, on a
        # fresh DB, any table whose ORM module app.py did not happen to
        # import. See db_bootstrap.py's docstring for the full defect writeup.
        upgrade_to_head(settings.database_url)
        engine = app.state.engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    # CRD Issue 2b: recover turn leases whose owning process is proven dead
    # (its OS owner lock is free). A live or unprovable lease is kept, so a
    # second app or process on the same store cannot erase an in-flight turn.
    clear_orphan_turn_leases(session_factory)

    app.state.settings = settings
    app.state.session_factory = session_factory
    if remote:
        assert outbox is not None
        fence = AccountFence()
        identity = IdentityService(
            control_factory, OutboxDirectoryTransport(outbox), fence=fence
        )
        app.state.identity = identity
        app.state.control_factory = control_factory
        app.state.access_policy = AccessPolicy(identity, control_factory)
        app.state.account_fence = fence
        # CRD Issue 22: remote operational records live in the control store.
        app.state.support = SupportService(control_factory, session_factory, identity)
        # ADR-021 D4: no shared subject -- each request's account is its own.
    else:
        app.state.identity = None
        app.state.access_policy = AccessPolicy()
        app.state.sojourner_id = provision_sojourner_id(session_factory)
    # Per-story turn-submission lock registry (Binding Decision 8). A single
    # choke point created once here, not per-request.
    story_locks: dict[UUID, asyncio.Lock] = defaultdict(asyncio.Lock)
    app.state.story_locks = story_locks
    orchestrator, rpg_sequences = build_pipeline(
        session_factory, app.state.access_policy
    )
    app.state.orchestrator = orchestrator
    # CRD Issue 15b: the RPG action routes reach the orchestrator's own
    # ActionResolutionService through the typed seam, never a second one.
    app.state.rpg_actions = RpgActions(rpg_sequences)
    if remote:
        # #205: the routes' owning-service seams refuse unscoped remote calls.
        app.state.orchestrator = ScopedSeam(
            orchestrator,
            app.state.access_policy,
            session_factory,
            frozenset(
                {
                    "orchestrate_turn",
                    "orchestrate_rpg_resume",
                    "orchestrate_branching_start",
                }
            ),
            app.state.account_fence,
        )
        app.state.rpg_actions = ScopedSeam(
            app.state.rpg_actions,
            app.state.access_policy,
            session_factory,
            frozenset(
                {"current", "submit_roll", "adjust", "decide", "refuse_settled_resume"}
            ),
            app.state.account_fence,
        )
    # CRD Issue 22: Story and account-wide data requests, both deployments.
    retrieval_config = RetrievalMemoryConfig.from_env()
    app.state.data_requests = DataRequestService(
        ops=control_factory if remote else session_factory,
        content=session_factory,
        environment="remote" if remote else "local",
        policy=app.state.access_policy,
        delete_story_chunks=story_chunk_deleter(
            lambda: build_chroma_client(retrieval_config)
        ),
        export_dir=export_dir(settings),
        identity=app.state.identity,
        fence=app.state.account_fence if remote else None,
        support=app.state.support if remote else None,
    )
    app.state.anomalies = AnomalyService(
        control_factory if remote else session_factory,
        session_factory,
        app.state.data_requests.store,
        control=control_factory if remote else None,
        now=utc_now,
    )
    app.state.ops_factory = control_factory if remote else session_factory
    # DoR-E: the readiness seam is constructed once here and consumed only
    # inside the access-path selection helper (api/access_path.py callers) --
    # never in a route handler directly.
    if remote:
        # ADR-021 D9: no credential store exists server-side; BYOK readiness
        # is never probed, so no hosted BYOK execution model can arise.
        app.state.byok_readiness_provider = ServerHostedByokUnavailable()
        app.state.byok_settings = None
    else:
        credential_store = make_credential_store()
        app.state.byok_readiness_provider = ByokCredentialReadinessProvider(
            credential_store, session_factory
        )
        # CRD Issue 20: settings write the same store the readiness probe
        # reads. Fake-provider mode never contacts a real provider,
        # validation included.
        app.state.byok_settings = ByokSettingsService(
            credential_store,
            session_factory,
            checker=fake_credential_check if fake_provider_enabled() else None,
        )

    # Both deployments mount every router (one OpenAPI document); behavior
    # is gated by enforce_access. Every /api/stories/{story_id} route passes
    # the one Story ownership guard.
    story_guard = [Depends(authorize_story)]
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(stories_router)
    app.include_router(story_router, dependencies=story_guard)
    app.include_router(turns_router, dependencies=story_guard)
    app.include_router(rpg_actions_router, dependencies=story_guard)
    app.include_router(visible_state_router, dependencies=story_guard)
    app.include_router(setup_router, dependencies=story_guard)
    app.include_router(rpg_setup_router, dependencies=story_guard)
    app.include_router(personas_router)
    app.include_router(account_router)
    app.include_router(data_requests_router)

    @app.exception_handler(ApiErrorResponse)
    async def _api_error_handler(
        request: Request, exc: ApiErrorResponse
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.error.model_dump())

    @app.exception_handler(IdentityUnavailable)
    async def _identity_unavailable_handler(
        request: Request, exc: IdentityUnavailable
    ) -> JSONResponse:
        # A control-authority read failed after admission (#205): the same
        # sanitized answer as an unreachable identity store at admission.
        error = ApiError(
            error_code=ApiErrorCode.IDENTITY_UNAVAILABLE,
            message="Sign-in is temporarily unavailable.",
        )
        return JSONResponse(status_code=503, content=error.model_dump())

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
        # CRD Issue 20: on the account/credential surface an unknown property
        # name is client-chosen (it could carry a key), so locations there
        # name only known fields.
        account = request.url.path.startswith(ACCOUNT_PATH_PREFIX)
        detail = {
            (
                account_validation_location(tuple(error["loc"]))
                if account
                else ".".join(str(part) for part in error["loc"])
            ): str(error["msg"])
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
