"""GET /api/health — boot/config check."""

from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.deps import get_session
from afterworlds.api.dto import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)) -> HealthResponse:
    session.execute(sa.text("SELECT 1"))
    return HealthResponse(status="ok", db_reachable=True)
