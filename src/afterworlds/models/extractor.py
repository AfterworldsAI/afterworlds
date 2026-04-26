"""Extractor proposal types and result types — CRD Issue 10."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from afterworlds.models.enums import EventKind, EventSignificance, TargetDomain


class LockedFactProposal(BaseModel):
    kind: Literal["locked_fact"] = "locked_fact"
    fact_text: str
    rationale: str | None = None


class SoftFactProposal(BaseModel):
    kind: Literal["soft_fact"] = "soft_fact"
    target_domain: TargetDomain
    target_natural_key: str
    target_field: str
    proposed_value: str
    rationale: str | None = None


class TransientStateProposal(BaseModel):
    kind: Literal["transient_state"] = "transient_state"
    target_domain: TargetDomain
    target_natural_key: str
    target_field: str
    proposed_value: str
    rationale: str | None = None


class UnresolvedThreadProposal(BaseModel):
    kind: Literal["unresolved_thread"] = "unresolved_thread"
    description: str
    rationale: str | None = None


class EventProposal(BaseModel):
    kind: Literal["event"] = "event"
    event_kind: EventKind
    description: str
    significance: EventSignificance
    related_entity_natural_keys: list[str] = Field(default_factory=list)
    rationale: str | None = None


ExtractorProposal = Annotated[
    LockedFactProposal
    | SoftFactProposal
    | TransientStateProposal
    | UnresolvedThreadProposal
    | EventProposal,
    Field(discriminator="kind"),
]


class ExtractorProposalSet(BaseModel):
    proposals: list[ExtractorProposal] = Field(default_factory=list)


class ExtractorRoutingSummary(BaseModel):
    locked_fact_staged_ids: list[UUID]
    soft_fact_staged_ids: list[UUID]
    transient_state_staged_ids: list[UUID]
    unresolved_thread_staged_ids: list[UUID]
    event_ids: list[UUID]


__all__ = [
    "LockedFactProposal",
    "SoftFactProposal",
    "TransientStateProposal",
    "UnresolvedThreadProposal",
    "EventProposal",
    "ExtractorProposal",
    "ExtractorProposalSet",
    "ExtractorRoutingSummary",
]
