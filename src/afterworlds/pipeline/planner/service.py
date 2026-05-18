"""Planner pass service — CRD Issue 12a.

Planner pass: receives AssembledContext, renders an Anthropic Messages payload,
calls the LLM using Anthropic tool use, validates the PlannerOutput, and returns
a typed PlannerResult.

Architectural invariants enforced here:
  - Every pass receives both a pass contract and an active mode contract.  The
    Planner ``system`` parameter contains two blocks in order:
      1. Planner pass contract (loaded from docs/prompts/planner.md) — defines
         the Planner's job.
      2. Active mode contract (built_context.stable_prefix.system_prompt) —
         defines RPG / Branching / Writing behavioural constraints so planning
         is conditioned on the current story mode.
  - The Planner pass does NOT call the Writer, does NOT persist, and does NOT
    mutate the caller's AssembledContext.
  - PassForwardLedger is empty when Planner renders (it is the first pass in
    pipeline order); empty ledger produces zero extra user blocks.
  - Planner user-message stable-prefix blocks match the Writer renderer order:
    Story Bible → Rolling Summary → Rules Package slice → Retrieval Memory.
    This alignment allows Planner to warm the stable-prefix cache for Writer
    (CRD Item 14 invariant #10; Issue 12c wires the handoff).
  - Cache breakpoint is placed on the last stable-prefix block.
  - Extended TTL caching is enabled by default (CRD Item 14 invariant #9).
  - Fail-closed: PlannerPassError on any provider, parsing, or validation failure.
    No silent fallback.
"""

from __future__ import annotations

from pathlib import Path

from anthropic.types import (
    MessageParam,
    TextBlockParam,
)

from afterworlds.models.context import AssembledContext
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.planner.caller import (
    PRODUCE_PLAN_TOOL_NAME,
    PRODUCE_PLAN_TOOL_SPEC,
    AnthropicPlannerCaller,
    PlannerModelCaller,
    PlannerPayload,
    parse_tool_input,
    timed_call,
)
from afterworlds.pipeline.planner.config import (
    PLANNER_MAX_TOKENS,
    PlannerConfig,
)
from afterworlds.pipeline.planner.models import (
    PlannerOutput,
    PlannerPassError,
    PlannerResult,
)

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the planner prompt file is missing."""


def load_planner_prompt() -> str:
    """Load the Planner pass system prompt from docs/prompts/planner.md."""
    prompt_path = _PROMPT_DIR / "planner.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Planner prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# PlannerService
# ---------------------------------------------------------------------------


class PlannerService:
    """Planner pass service.

    Responsibilities:
      1. Render the AssembledContext into an Anthropic Messages payload.
         System parameter: two blocks — Planner pass contract and active mode
         contract.  User-message stable-prefix blocks start with Story Bible
         (Writer-aligned for cache reuse).
      2. Invoke the provider via the injected caller (forced tool use).
      3. Parse the ToolUseBlock response.
      4. Validate the tool input against PlannerOutput.
      5. Return a typed PlannerResult.

    Args:
        config: Planner configuration.  Defaults to PlannerConfig.from_env().
        caller: Injectable model caller.  Defaults to AnthropicPlannerCaller.
    """

    def __init__(
        self,
        config: PlannerConfig | None = None,
        caller: PlannerModelCaller | None = None,
    ) -> None:
        self._config = config or PlannerConfig.from_env()
        self._caller: PlannerModelCaller = caller or AnthropicPlannerCaller(
            self._config
        )
        self._system_prompt: str = load_planner_prompt()

    def plan(
        self,
        built_context: AssembledContext,
    ) -> PlannerResult:
        """Execute one Planner pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Planner pass renders from this without mutating it.

        Returns:
            PlannerResult with scene_goal, next_beat, facts_needed, notes, and
            token metrics.

        Raises:
            PlannerPassError: if the provider call fails, the response contains
                no tool-use block, or the tool input fails schema validation.
        """
        payload = self._render(built_context)

        try:
            response, latency_ms = timed_call(self._caller, payload)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise PlannerPassError(f"Planner provider call failed: {exc}") from exc

        try:
            tool_input = parse_tool_input(response)
        except PlannerPassError:
            raise
        except Exception as exc:
            raise PlannerPassError(f"Planner response parsing failed: {exc}") from exc

        try:
            output = PlannerOutput.model_validate(tool_input)
        except Exception as exc:
            raise PlannerPassError(
                f"Planner tool input failed schema validation: {exc}"
            ) from exc

        usage = response.usage
        return PlannerResult(
            plan=output,
            model_identifier=f"anthropic:{self._config.model}",
            latency_ms=latency_ms,
            input_token_count=usage.input_tokens,
            output_token_count=usage.output_tokens,
            cache_read_token_count=usage.cache_read_input_tokens,
            cache_creation_token_count=usage.cache_creation_input_tokens,
        )

    # -----------------------------------------------------------------------
    # Private: prompt rendering
    # -----------------------------------------------------------------------

    def _render(self, built_context: AssembledContext) -> PlannerPayload:
        """Render the AssembledContext into a Planner payload.

        Cache breakpoint placement:
          - Stable-prefix blocks carry the cache_control marker on the last
            block via the shared renderer (CRD Item 14 invariant #10).  All
            provider-backed passes go through the same utility so the cache
            region is structurally identical across passes (Issue 12c).
          - PassForwardLedger is empty for the Planner pass (it is first in
            pipeline order) — produces zero extra blocks.
          - Volatile suffix blocks carry no marker.
        """
        ttl = TTL_EXTENDED if self._config.extended_ttl else TTL_DEFAULT
        user_blocks: list[TextBlockParam] = list(
            render_stable_prefix_blocks(built_context.stable_prefix, ttl)
        )

        # PassForwardLedger: renders any content from earlier passes.
        # Empty when Planner is first in pipeline — produces no block.
        ledger_text = built_context.pass_forward_ledger.render()
        if ledger_text:
            user_blocks.append(TextBlockParam(type="text", text=ledger_text))

        # Volatile suffix: recent turns + current input + intent.
        vs = built_context.volatile_suffix
        for turn in vs.recent_turns:
            user_blocks.append(
                TextBlockParam(
                    type="text",
                    text=(
                        f"Player: {turn.user_input}\n"
                        f"Narrator: {turn.assistant_output}"
                    ),
                )
            )
        user_blocks.append(
            TextBlockParam(
                type="text",
                text=(
                    f"Player: {vs.current_input}\n"
                    f"[Intent: {vs.classified_intent.intent_type.value}]"
                ),
            )
        )

        return {
            "model": self._config.model,
            "max_tokens": PLANNER_MAX_TOKENS,
            "system": [
                TextBlockParam(type="text", text=self._system_prompt),
                TextBlockParam(
                    type="text",
                    text=built_context.stable_prefix.system_prompt,
                ),
            ],
            "messages": [MessageParam(role="user", content=user_blocks)],
            "tools": [PRODUCE_PLAN_TOOL_SPEC],
            "tool_choice": {"type": "tool", "name": PRODUCE_PLAN_TOOL_NAME},
        }
