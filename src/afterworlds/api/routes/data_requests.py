"""/api/data-requests -- CRD Issue 22 Story and account-wide export/deletion.

The requester's own paths, in both deployments: remote requests are scoped
to the authenticated hosted account (a submitted ID never selects a subject
-- another account's request is the same 404 as a missing one); local
requests use the local owner boundary and need no cloud account. Remote
requests are approved and executed by the Owner administrator
(``/api/admin/data-requests``); a local owner executes their own.

``POST /api/data-requests/receipt`` is the post-closure status path: it
needs the one-time credential issued at account-deletion confirmation,
never a guessable request ID alone.
"""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from afterworlds.api.deps import AdmittedWorkerRoute
from afterworlds.api.dto import (
    ConfirmDeletionRequest,
    ConfirmDeletionResponse,
    CreateDataRequest,
    DataRequestDTO,
    DataRequestListResponse,
    DataRequestStepRequest,
    DeletionPreviewResponse,
    ReceiptLookupRequest,
)
from afterworlds.api.errors import ApiError
from afterworlds.api.operations import preview_dto, request_dto, run_operation
from afterworlds.api.remote_access import get_actor
from afterworlds.operations.requests import RequestKind, RequestScope
from afterworlds.operations.service import DataRequestService
from afterworlds.remote.identity import Actor

router = APIRouter(
    prefix="/api/data-requests", tags=["data-requests"], route_class=AdmittedWorkerRoute
)

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ApiError} for status in (401, 403, 404, 409, 422, 503)
}


def _service(request: Request) -> DataRequestService:
    return request.app.state.data_requests  # type: ignore[no-any-return]


@router.post("", response_model=DataRequestDTO, status_code=201, responses=_RESPONSES)
def create_data_request(
    body: CreateDataRequest, request: Request, actor: Actor = Depends(get_actor)
) -> DataRequestDTO:
    view = run_operation(
        lambda: _service(request).create(
            actor, RequestKind(body.kind), RequestScope(body.scope), body.story_id
        )
    )
    return request_dto(view, administrator=False)


@router.get("", response_model=DataRequestListResponse, responses=_RESPONSES)
def list_data_requests(
    request: Request, actor: Actor = Depends(get_actor)
) -> DataRequestListResponse:
    views = run_operation(lambda: _service(request).list_own(actor))
    return DataRequestListResponse(
        requests=[request_dto(v, administrator=False) for v in views]
    )


@router.post("/receipt", response_model=DataRequestDTO, responses=_RESPONSES)
def read_receipt(body: ReceiptLookupRequest, request: Request) -> DataRequestDTO:
    view = run_operation(
        lambda: _service(request).receipt(
            body.request_id, body.credential.get_secret_value()
        )
    )
    return request_dto(view, administrator=False)


@router.get("/{request_id}", response_model=DataRequestDTO, responses=_RESPONSES)
def get_data_request(
    request_id: UUID, request: Request, actor: Actor = Depends(get_actor)
) -> DataRequestDTO:
    view = run_operation(lambda: _service(request).get_own(actor, str(request_id)))
    return request_dto(view, administrator=False)


@router.get(
    "/{request_id}/deletion-preview",
    response_model=DeletionPreviewResponse,
    responses=_RESPONSES,
)
def get_deletion_preview(
    request_id: UUID, request: Request, actor: Actor = Depends(get_actor)
) -> DeletionPreviewResponse:
    return preview_dto(
        run_operation(lambda: _service(request).preview(actor, str(request_id)))
    )


@router.post(
    "/{request_id}/confirm",
    response_model=ConfirmDeletionResponse,
    responses=_RESPONSES,
)
def confirm_deletion(
    request_id: UUID,
    body: ConfirmDeletionRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> ConfirmDeletionResponse:
    view, credential = run_operation(
        lambda: _service(request).confirm(
            actor,
            str(request_id),
            expected_revision=body.expected_revision,
            confirmed_scope_revision=body.scope_revision,
            password=body.password.get_secret_value() if body.password else None,
        )
    )
    return ConfirmDeletionResponse(
        request=request_dto(view, administrator=False), receipt_credential=credential
    )


@router.post(
    "/{request_id}/execute", response_model=DataRequestDTO, responses=_RESPONSES
)
async def execute_local_request(
    request_id: UUID,
    body: DataRequestStepRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> DataRequestDTO:
    """Local owner only. A deletion first takes the per-Story turn locks of
    every Story in scope, so no in-flight turn can land after it."""
    service = _service(request)
    view = await run_in_threadpool(
        lambda: run_operation(lambda: service.get_own(actor, str(request_id)))
    )
    locks: list[asyncio.Lock] = []
    if view.kind == "deletion":
        story_ids = await run_in_threadpool(
            lambda: run_operation(lambda: service.preview(actor, str(request_id)))
        )
        registry = request.app.state.story_locks
        locks = [registry[UUID(sid)] for sid in sorted(story_ids["story_ids"])]
    async with AsyncExitStack() as stack:
        for lock in locks:
            await stack.enter_async_context(lock)
        result = await run_in_threadpool(
            lambda: run_operation(
                lambda: service.execute_local(
                    actor, str(request_id), expected_revision=body.expected_revision
                )
            )
        )
    return request_dto(result, administrator=False)


@router.get(
    "/{request_id}/artifact",
    response_class=FileResponse,
    responses={**_RESPONSES, 200: {"content": {"application/zip": {}}}},
)
def download_artifact(
    request_id: UUID, request: Request, actor: Actor = Depends(get_actor)
) -> FileResponse:
    path = run_operation(
        lambda: _service(request).artifact_path(actor, str(request_id))
    )
    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"afterworlds-export-{request_id}.zip",
        headers={"Cache-Control": "no-store"},
    )
