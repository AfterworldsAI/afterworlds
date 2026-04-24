"""Turn — one interaction unit (one user input + one AI response).

Turn and Node are intentionally distinct types.  They often correspond 1:1
but are not the same concept.  Collapsing them is architectural debt.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from afterworlds.models.enums import IntentType, normalize_legacy_intent_type
from afterworlds.models.intent_classification import IntentClassificationResult


class Turn(BaseModel):
    """One interaction unit: one user input and one AI response.

    Minimal field contract required to preserve Turn's distinction from Node:
    - ``turn_id`` — own identity, not reused from the associated Node
    - ``user_input`` — the raw user submission
    - ``assistant_output`` — the raw AI response
    - ``timestamp`` — when the interaction occurred
    - ``intent_classification`` — classified intent enum for this Turn
    - ``intent_classification_result`` — full typed ICR from the pipeline;
      populated by the Writer pass (Issue 9) and nullable for pre-pipeline
      Turns written before the Writer existed.
    - ``node_id`` — optional link to the associated Node (may be None when the
      Turn does not yet correspond to a persisted Node, e.g. during pre-play)
    """

    turn_id: UUID = Field(default_factory=uuid4)
    user_input: str
    assistant_output: str
    timestamp: datetime
    intent_classification: IntentType
    node_id: UUID | None = None
    intent_classification_result: IntentClassificationResult | None = None

    @field_validator("intent_classification", mode="before")
    @classmethod
    def _coerce_legacy_intent_classification(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_legacy_intent_type(v)
        return v
