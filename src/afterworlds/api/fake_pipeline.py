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
import re

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
from afterworlds.pipeline.provider.credentials import ValidationStatus

_FAKE_MODEL = "afterworlds-fake:test-model"
_FAKE_RANGE_MINIMUM = {"1-2": 1, "2-3": 2, "3-4": 3, "2-4": 2, "2-5": 2}


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
        if pass_id == "intent_classifier":
            # Round 6 remediation (PR #126 P1): classification is now
            # provider-routed in the product path, so fake mode's
            # FakeProviderResolver-supplied adapter must answer this pass_id
            # too. Reuses fake_intent_model_caller's canned JSON body rather
            # than duplicating it -- "fake-provider CI mode may continue to
            # use fake_intent_model_caller".
            prompt = "\n".join(block.text for block in request.rendered_blocks)
            content = [ProviderTextPart(text=fake_intent_model_caller(prompt))]
        elif pass_id == "planner":
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
        elif (
            pass_id == "writer" and request.forced_tool_name == "produce_rpg_setup_turn"
        ):
            # ADR-015c: an RPG setup turn's envelope. The fake confirms the
            # world and otherwise clarifies; it never proposes a character.
            world = any(
                "phase: world_setup" in block.text for block in request.rendered_blocks
            )
            content = [
                ProviderToolCallPart(
                    tool_name="produce_rpg_setup_turn",
                    tool_input={
                        "schema_version": 1,
                        "gm_text": "The setup continues, faked for E2E testing.",
                        "result": (
                            {
                                "kind": "world_confirmation",
                                "understanding": "A world, faked for E2E.",
                            }
                            if world
                            else {"kind": "clarification", "questions": []}
                        ),
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
        elif pass_id == "rpg_adjudication":
            # CRD Issue 15c wires RPG adjudication: the canned turn is
            # non-mechanical (no roll proposed), so the spine is unchanged.
            content = [
                ProviderToolCallPart(
                    tool_name="produce_adjudication_proposals",
                    tool_input={"rolls": []},
                )
            ]
        elif pass_id in ("input_safety", "output_safety"):
            content = [
                ProviderToolCallPart(
                    tool_name="report_safety_assessment", tool_input={"concerns": []}
                )
            ]
        elif pass_id == "branching_writer":
            # CRD Issue 21: the Branching writer is wired; propose the minimum
            # count the session's code-owned range allows (validated by code).
            rendered = "\n".join(block.text for block in request.rendered_blocks)
            match = re.search(r"branch_count_range: (\S+)", rendered)
            count = _FAKE_RANGE_MINIMUM.get(match.group(1), 2) if match else 2
            content = [
                ProviderToolCallPart(
                    tool_name="produce_branch_output",
                    tool_input={
                        "narrative_text": "The story branches, faked for E2E.",
                        "branch_options_text": [
                            f"Fake path {i + 1}" for i in range(count)
                        ],
                        "branch_presentation_state": "shown",
                    },
                )
            ]
        elif pass_id == "branching_ooc_config_extractor":
            content = [
                ProviderToolCallPart(
                    tool_name="extract_branching_config_update",
                    tool_input={
                        "interaction_style": None,
                        "branching_cadence": None,
                        "branch_count_range": None,
                        "length_preference": None,
                    },
                )
            ]
        elif pass_id == "rolling_summary":
            content = [
                ProviderToolCallPart(
                    tool_name="record_rolling_summary",
                    tool_input={"summary": "The story so far, faked for E2E."},
                )
            ]
        else:
            # Writing's OOC extractor is out of v1 scope (ADR-017b).
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


def fake_credential_check(
    provider_name: str, raw_key: str
) -> tuple[ValidationStatus, None]:
    """Fake-provider-mode stand-in for the live credential check (CRD Issue
    20): never contacts a provider. A key containing ``"invalid"`` is
    rejected, anything else accepted, so built-app tests can exercise both
    verdicts."""
    if "invalid" in raw_key:
        return ValidationStatus.INVALID, None
    return ValidationStatus.VALID, None
