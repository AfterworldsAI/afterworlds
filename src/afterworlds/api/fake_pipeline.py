"""Faked provider passes for E2E/CI -- DoR-B: "no real provider calls in
default CI". Activated only via ``AFTERWORLDS_FAKE_PROVIDER=1``
(build_orchestrator wires this in; never used in the product/dev path).

Each pass service already owns its own real parsing logic (tool-call
schemas, text extraction) -- this fake only returns canned, schema-valid
``ProviderCallResult``/model_caller responses so those real code paths
execute end-to-end against deterministic data, never a mocked pass service.
"""

from __future__ import annotations

import json

from afterworlds.entitlement.enums import ModelTier, RuntimeAccessPath
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderContentPart,
    ProviderTextPart,
    ProviderToolCallPart,
)
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)

_FAKE_MODEL = "afterworlds-fake:test-model"


class FakeProviderAdapter:
    """Returns a canned, schema-valid response per pass_id.

    Every real pass service's own parsing/validation logic runs against this
    data -- nothing about Planner/Writer/Extractor/Contradiction/Safety
    itself is faked, only the model call underneath them.
    """

    provider_name = "afterworlds-fake"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        pass_id = request.pass_id.value
        content: list[ProviderContentPart]
        if pass_id == "planner":
            content = [
                ProviderToolCallPart(
                    tool_name="produce_plan",
                    tool_input={
                        "scene_goal": "Move the scene forward.",
                        "next_beat": "Something happens next.",
                        "facts_needed": [],
                    },
                )
            ]
        elif pass_id == "writer":
            content = [
                ProviderTextPart(text="The story continues, faked for E2E testing.")
            ]
        elif pass_id == "extractor":
            content = [
                ProviderToolCallPart(
                    tool_name="propose_canon_updates", tool_input={"proposals": []}
                )
            ]
        elif pass_id == "contradiction":
            content = [
                ProviderToolCallPart(
                    tool_name="report_contradictions", tool_input={"violations": []}
                )
            ]
        elif pass_id in ("input_safety", "output_safety"):
            content = [
                ProviderToolCallPart(
                    tool_name="report_safety_assessment", tool_input={"concerns": []}
                )
            ]
        else:
            # Mode-specific passes (RPG adjudication, Branching writer, OOC
            # extractors) are out of Issue 19's core-path wiring (see
            # Architecture Notes) -- not exercised by the E2E spine.
            raise NotImplementedError(
                f"FakeProviderAdapter has no canned response for pass_id={pass_id!r}"
            )

        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name=self.provider_name,
            model_identifier=_FAKE_MODEL,
            model_tier=ModelTier.HAIKU,
            content_parts=content,
            latency_ms=1,
            input_token_count=100,
            output_token_count=50,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
        )


def fake_intent_model_caller(prompt: str) -> str:
    """Fake ``ModelCallerT`` for the Issue 7 classifier (not a ProviderAdapter
    seam -- see pipeline_wiring.py's docstring)."""
    return json.dumps(
        {
            "intent_type": "in_character_action",
            "confidence": 0.9,
            "ambiguous": False,
            "secondary_intent": None,
        }
    )


class FakeProviderResolver:
    """Drop-in stand-in for ``ProviderResolver.resolve_for_turn`` -- always
    resolves to the fake adapter, regardless of access_path/credentials."""

    def resolve_for_turn(
        self, access_path: RuntimeAccessPath, sojourner_id: object
    ) -> TurnProviderBinding:
        route = EligibleModelRoute(
            provider_name="afterworlds-fake",
            model_identifier=_FAKE_MODEL,
            whitelist_status=SafetyWhitelistStatus.WHITELISTED,
            supports_required_capabilities=True,
        )
        return TurnProviderBinding(
            adapter=FakeProviderAdapter(),
            primary_writer_route=route,
            eligible_writer_routes=(route,),
            access_path=access_path,
        )
