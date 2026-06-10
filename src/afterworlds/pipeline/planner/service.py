"""Planner pass service — CRD Issue 12a / 14a.

Planner pass: receives AssembledContext, builds a ProviderCallRequest,
calls the LLM via the injected ProviderAdapter using forced tool use,
validates the PlannerOutput, and returns a typed PlannerResult.

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

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.planner.caller import (
    PRODUCE_PLAN_TOOL_NAME,
    PRODUCE_PLAN_TOOL_SPEC,
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
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter

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
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_PLANNER_TOOL_DEF = ProviderToolDefinition(
    name=PRODUCE_PLAN_TOOL_NAME,
    description=PRODUCE_PLAN_TOOL_SPEC["description"],
    input_schema=PRODUCE_PLAN_TOOL_SPEC["input_schema"],
)


# ---------------------------------------------------------------------------
# PlannerService
# ---------------------------------------------------------------------------


class PlannerService:
    """Planner pass service.

    Responsibilities:
      1. Render the AssembledContext into a ProviderCallRequest.
         System parameter: two blocks — Planner pass contract and active mode
         contract.  User-message stable-prefix blocks start with Story Bible
         (Writer-aligned for cache reuse).
      2. Invoke the provider via the injected ProviderAdapter (forced tool use).
      3. Parse the ProviderToolCallPart response.
      4. Validate the tool input against PlannerOutput.
      5. Return a typed PlannerResult.

    Args:
        config: Planner configuration.  Defaults to PlannerConfig.from_env().
    """

    def __init__(
        self,
        config: PlannerConfig | None = None,
    ) -> None:
        self._config = config or PlannerConfig.from_env()
        self._system_prompt: str = load_planner_prompt()

    def plan(
        self,
        built_context: AssembledContext,
        *,
        provider: ProviderAdapter,
    ) -> PlannerResult:
        """Execute one Planner pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Planner pass renders from this without mutating it.
            provider: ProviderAdapter for this turn.

        Returns:
            PlannerResult with scene_goal, next_beat, facts_needed, notes, and
            token metrics.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER routing.
            PlannerPassError: if the provider call fails, the response contains
                no tool-use block, or the tool input fails schema validation.
        """
        request = self._render(built_context)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise PlannerPassError(f"Planner provider call failed: {exc}") from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise PlannerPassError("Planner response missing tool-use block")
        if tool_parts[0].tool_name != PRODUCE_PLAN_TOOL_NAME:
            raise PlannerPassError(
                f"Planner unexpected tool name: {tool_parts[0].tool_name!r}; "
                f"expected {PRODUCE_PLAN_TOOL_NAME!r}"
            )

        try:
            output = PlannerOutput.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise PlannerPassError(
                f"Planner tool input failed schema validation: {exc}"
            ) from exc

        return PlannerResult(
            plan=output,
            model_identifier=result.model_identifier,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
            provider=result.provider_name,
            model_tier=result.model_tier.value,
        )

    # -----------------------------------------------------------------------
    # Private: prompt rendering
    # -----------------------------------------------------------------------

    def _render(self, built_context: AssembledContext) -> ProviderCallRequest:
        """Render the AssembledContext into a ProviderCallRequest.

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
        rendered_blocks: list[RenderedBlock] = list(
            render_stable_prefix_blocks(built_context.stable_prefix, ttl)
        )

        ledger_text = built_context.pass_forward_ledger.render()
        if ledger_text:
            rendered_blocks.append(RenderedBlock(text=ledger_text))

        vs = built_context.volatile_suffix
        for turn in vs.recent_turns:
            rendered_blocks.append(
                RenderedBlock(
                    text=(
                        f"Player: {turn.user_input}\n"
                        f"Narrator: {turn.assistant_output}"
                    )
                )
            )
        rendered_blocks.append(
            RenderedBlock(
                text=(
                    f"Player: {vs.current_input}\n"
                    f"[Intent: {vs.classified_intent.intent_type.value}]"
                )
            )
        )

        return ProviderCallRequest(
            pass_id=PipelinePassId.PLANNER,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=built_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=PLANNER_MAX_TOKENS,
            tool_definitions=[_PLANNER_TOOL_DEF],
            forced_tool_name=PRODUCE_PLAN_TOOL_NAME,
        )
