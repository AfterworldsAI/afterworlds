"""RPG product startup routes (ADR-015c).

Typed phase confirmations against the displayed revision. Each runs under the
story's turn lock (a held lock is ``409 turn_in_flight``), makes no provider
call and settles nothing. Setup conversation itself goes through ordinary
``POST .../turns``.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from afterworlds.api.deps import get_story_lock, run_under_story_lock
from afterworlds.api.dto import (
    RpgAcceptCharacterRequest,
    RpgCompleteSetupRequest,
    RpgConfirmWorldRequest,
    RpgSelectRulesPackageRequest,
    RpgSetupViewDTO,
)
from afterworlds.api.errors import API_ERROR_RESPONSES
from afterworlds.api.rpg_setup import now, read_setup_view, run_setup_operation
from afterworlds.services import rpg_setup

router = APIRouter(prefix="/api/stories", tags=["rpg-setup"])


@router.get(
    "/{story_id}/rpg/setup",
    response_model=RpgSetupViewDTO,
    responses=API_ERROR_RESPONSES,
)
async def get_rpg_setup(story_id: UUID, request: Request) -> RpgSetupViewDTO:
    return await asyncio.to_thread(
        read_setup_view, request.app.state.session_factory, story_id
    )


@router.post(
    "/{story_id}/rpg/setup/confirm-world",
    response_model=RpgSetupViewDTO,
    responses=API_ERROR_RESPONSES,
)
async def confirm_world(
    story_id: UUID,
    body: RpgConfirmWorldRequest,
    request: Request,
    lock: asyncio.Lock = Depends(get_story_lock),
) -> RpgSetupViewDTO:
    return await run_under_story_lock(
        lock,
        run_setup_operation,
        request.app.state.session_factory,
        story_id,
        lambda s: rpg_setup.confirm_world(s, story_id, body.expected_world_revision),
    )


@router.post(
    "/{story_id}/rpg/setup/rules-package",
    response_model=RpgSetupViewDTO,
    responses=API_ERROR_RESPONSES,
)
async def select_rules_package(
    story_id: UUID,
    body: RpgSelectRulesPackageRequest,
    request: Request,
    lock: asyncio.Lock = Depends(get_story_lock),
) -> RpgSetupViewDTO:
    return await run_under_story_lock(
        lock,
        run_setup_operation,
        request.app.state.session_factory,
        story_id,
        lambda s: rpg_setup.select_package(s, story_id, body.package_uuid, now=now()),
    )


@router.post(
    "/{story_id}/rpg/setup/accept-character",
    response_model=RpgSetupViewDTO,
    responses=API_ERROR_RESPONSES,
)
async def accept_character(
    story_id: UUID,
    body: RpgAcceptCharacterRequest,
    request: Request,
    lock: asyncio.Lock = Depends(get_story_lock),
) -> RpgSetupViewDTO:
    return await run_under_story_lock(
        lock,
        run_setup_operation,
        request.app.state.session_factory,
        story_id,
        lambda s: rpg_setup.accept_character(
            s, story_id, body.expected_candidate_revision, now=now()
        ),
    )


@router.post(
    "/{story_id}/rpg/setup/complete",
    response_model=RpgSetupViewDTO,
    responses=API_ERROR_RESPONSES,
)
async def complete_setup(
    story_id: UUID,
    body: RpgCompleteSetupRequest,
    request: Request,
    lock: asyncio.Lock = Depends(get_story_lock),
) -> RpgSetupViewDTO:
    return await run_under_story_lock(
        lock,
        run_setup_operation,
        request.app.state.session_factory,
        story_id,
        lambda s: rpg_setup.complete_setup(
            s, story_id, body.expected_configuration_revision, now=now()
        ),
    )
