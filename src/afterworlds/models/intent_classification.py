"""Intent classification models — CRD Issue 7.

These models form the typed contract between the IntentClassifierService and
all downstream consumers (Context Builder, pipeline passes).  Downstream issues
depend on this contract being stable and typed — never a raw string or dict.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from afterworlds.models.enums import IntentType


class ClassificationHints(BaseModel):
    """Optional hints from the UI layer to assist classification.

    This is a typed stub.  Neither field is required to affect classification
    logic in Issue 7.  The model is defined now so Issue 8 (Context Builder)
    has a stable contract to pass hints through.

    Future use:
        ``mode`` may allow the classifier to weight intent types that are more
        or less likely in a given mode (e.g., ``branch_choice`` is only
        relevant in branching mode).
        ``recent_intents`` may allow the classifier to use short-term pattern
        context to disambiguate boundary cases.
    """

    mode: Literal["rpg", "branching", "writing"] | None = None
    recent_intents: list[IntentType] | None = None


class IntentClassificationResult(BaseModel):
    """Typed result returned by IntentClassifierService.classify().

    This is the contract that Context Builder (Issue 8) and pipeline passes
    consume.  It must never be returned as a raw string, dict, or bare enum.

    Attributes:
        intent_type: The primary classified intent.
        confidence: Model confidence in the primary classification, 0.0–1.0.
            Advisory in v1 — not consumed by any routing logic in this issue.
        raw_input: The original player input string, set by the service (not
            echoed from the model) to guarantee it matches the actual input.
        ambiguous: True when the input could reasonably classify as more than
            one intent type.  A classifier that never returns True here has
            hidden its edge cases rather than handled them.
        secondary_intent: Populated when ambiguous is True; the next most
            likely intent type.  None when ambiguous is False.
    """

    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    raw_input: str
    ambiguous: bool
    secondary_intent: IntentType | None = None

    @model_validator(mode="after")
    def _check_ambiguous_secondary_intent(self) -> IntentClassificationResult:
        if self.ambiguous and self.secondary_intent is None:
            raise ValueError("secondary_intent must be set when ambiguous is True")
        if not self.ambiguous and self.secondary_intent is not None:
            raise ValueError("secondary_intent must be None when ambiguous is False")
        return self


class IntentClassificationError(Exception):
    """Raised when model output cannot be parsed as IntentClassificationResult.

    Fail-closed: no silent fallback to a default intent type.  Swallowing a
    parse failure and returning ``in_character_action`` by default would mask a
    real failure mode and allow malformed turns into the pipeline.
    """
