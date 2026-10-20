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

import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

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
    ReissueReceiptCredentialRequest,
)
from afterworlds.api.errors import ApiError
from afterworlds.api.operations import preview_dto, request_dto, run_operation
from afterworlds.api.remote_access import get_actor
from afterworlds.operations.requests import RequestKind, RequestScope
from afterworlds.operations.service import DataRequestService
from afterworlds.remote.identity import Actor

logger = logging.getLogger("afterworlds.api.data_requests")

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
def execute_local_request(
    request_id: UUID,
    body: DataRequestStepRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> DataRequestDTO:
    """Local owner only. A deletion holds the local owner fence exclusive for
    its whole run (``DataRequestService.execute_local``)."""
    result = run_operation(
        lambda: _service(request).execute_local(
            actor, str(request_id), expected_revision=body.expected_revision
        )
    )
    return request_dto(result, administrator=False)


#: Bytes per streamed chunk of an export download.
DOWNLOAD_CHUNK = 64 * 1024


def _stream_artifact(path: Path, on_complete: Callable[[], None]) -> Iterator[bytes]:
    """The whole artifact, in order, then ``on_complete``: the server asks for
    the next chunk only after the previous send completed, so reaching the
    end proves every byte was handed to the transport. A disconnect or send
    failure stops the iteration and nothing is recorded (review round 2,
    F3). There is no Range service: every response is the full artifact."""
    with path.open("rb") as handle:
        while chunk := handle.read(DOWNLOAD_CHUNK):
            yield chunk
    try:
        on_complete()
    except (
        Exception
    ):  # noqa: BLE001 -- an unrecorded delivery only keeps erasure waiting
        logger.error("export delivery not recorded: category=delivery_unrecorded")


@router.get(
    "/{request_id}/artifact",
    response_class=StreamingResponse,
    responses={**_RESPONSES, 200: {"content": {"application/zip": {}}}},
)
def download_artifact(
    request_id: UUID, request: Request, actor: Actor = Depends(get_actor)
) -> StreamingResponse:
    service = _service(request)
    path, artifact_id = run_operation(
        lambda: service.artifact_path(actor, str(request_id))
    )
    return StreamingResponse(
        _stream_artifact(path, lambda: service.mark_delivered(artifact_id)),
        media_type="application/zip",
        headers={
            "Cache-Control": "no-store",
            "Content-Length": str(path.stat().st_size),
            "Content-Disposition": (
                f'attachment; filename="afterworlds-export-{request_id}.zip"'
            ),
        },
    )


@router.post(
    "/{request_id}/receipt-credential",
    response_model=ConfirmDeletionResponse,
    responses=_RESPONSES,
)
def reissue_receipt_credential(
    request_id: UUID,
    body: ReissueReceiptCredentialRequest,
    request: Request,
    actor: Actor = Depends(get_actor),
) -> ConfirmDeletionResponse:
    """Replace a receipt credential whose confirmation response was lost --
    before closure only, with the owner's session and password."""
    view, credential = run_operation(
        lambda: _service(request).reissue_credential(
            actor, str(request_id), body.password.get_secret_value()
        )
    )
    return ConfirmDeletionResponse(
        request=request_dto(view, administrator=False), receipt_credential=credential
    )
