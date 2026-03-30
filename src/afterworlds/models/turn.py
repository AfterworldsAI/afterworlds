"""Turn — one interaction unit (one user input + one AI response).

Turn and Node are intentionally distinct types.  They often correspond 1:1
but are not the same concept.  Collapsing them is architectural debt.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from afterworlds.models.enums import IntentType


class Turn(BaseModel):
    """One interaction unit: one user input and one AI response.

    Minimal field contract required to preserve Turn's distinction from Node:
    - ``turn_id`` — own identity, not reused from the associated Node
    - ``user_input`` — the raw user submission
    - ``assistant_output`` — the raw AI response
    - ``timestamp`` — when the interaction occurred
    - ``intent_classification`` — classified intent for this Turn
    - ``node_id`` — optional link to the associated Node (may be None when the
      Turn does not yet correspond to a persisted Node, e.g. during pre-play)
    """

    turn_id: UUID = Field(default_factory=uuid4)
    user_input: str
    assistant_output: str
    timestamp: datetime
    intent_classification: IntentType
    node_id: UUID | None = None
