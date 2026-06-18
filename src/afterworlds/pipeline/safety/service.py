"""Safety pass service — CRD Issue 12b / 14a.

Safety envelope: receives AssembledContext + text + SafetyTarget, builds a
ProviderCallRequest, calls the LLM via the injected ProviderAdapter using forced
tool use, validates the SafetyReport, and returns a typed SafetyResult.

Architectural invariants enforced here:
  - The Safety pass is a guardrail envelope, NOT a narrative pass.  It does
    NOT call the Writer, does NOT persist, and does NOT mutate the caller's
    AssembledContext or PassForwardLedger.
  - Every pass receives both a pass contract and an active mode contract.  The
    Safety ``system`` parameter contains two blocks in order:
      1. Safety pass contract (loaded from docs/prompts/safety.md) — defines
         evaluation posture, categories, and ambiguity rules.
      2. Active mode contract (built_context.stable_prefix.system_prompt) —
         behavioural constraints that determine what is acceptable for the
         current story mode.
  - The mode contract is placed in the ``system`` parameter (not user blocks),
    following the Planner pattern (not the Contradiction pattern).
  - Stable-prefix user blocks follow canonical Writer order:
    Story Bible → Rolling Summary → Rules Package slice → Retrieval Memory.
    The mode contract (system_prompt) is NOT repeated in the user blocks.
  - Cache breakpoint is placed on the last stable-prefix block.
  - Extended TTL caching is enabled by default (CRD Item 14 invariant #9).
  - The evaluated text is placed in the volatile suffix, labelled by target.
  - PassForwardLedger is NOT rendered into the Safety payload and is NOT
    mutated by the Safety pass.
  - Verdict is computed from the concerns list — the model never supplies it.
  - Fail-closed: SafetyPassError on ANY provider, parsing, or validation
    failure — including ProviderRefusalError.  No silent ALLOW on any failure
    path.  Provider refusals must not silently grant a safety ALLOW.
"""

from __future__ import annotations

from pathlib import Path

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter
from afterworlds.pipeline.safety.caller import (
    REPORT_SAFETY_TOOL_NAME,
    REPORT_SAFETY_TOOL_SPEC,
)
from afterworlds.pipeline.safety.config import (
    SAFETY_MAX_TOKENS,
    SafetyConfig,
)
from afterworlds.pipeline.safety.models import (
    SafetyPassError,
    SafetyReport,
    SafetyResult,
    SafetyTarget,
)

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the safety prompt file is missing."""


def load_safety_prompt() -> str:
    """Load the Safety pass system prompt from docs/prompts/safety.md."""
    prompt_path = _PROMPT_DIR / "safety.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Safety prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# Target labels
# ---------------------------------------------------------------------------

_LABEL_INPUT: str = "[SOJOURNER INPUT FOR SAFETY EVALUATION]"
_LABEL_OUTPUT: str = "[WRITER OUTPUT FOR SAFETY EVALUATION]"

# ---------------------------------------------------------------------------
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_SAFETY_TOOL_DEF = ProviderToolDefinition(
    name=REPORT_SAFETY_TOOL_NAME,
    description=REPORT_SAFETY_TOOL_SPEC["description"],
    input_schema=REPORT_SAFETY_TOOL_SPEC["input_schema"],
)

# ---------------------------------------------------------------------------
# SafetyService
# ---------------------------------------------------------------------------


class SafetyService:
    """Safety pass service.

    Responsibilities:
      1. Render the AssembledContext + evaluated text into a ProviderCallRequest.
         System parameter: two blocks — Safety pass contract and active mode
         contract.  User-message stable-prefix blocks start with Story Bible.
      2. Invoke the provider via the injected ProviderAdapter (forced tool use).
      3. Parse the ProviderToolCallPart response.
      4. Validate the tool input against SafetyReport.
      5. Return a typed SafetyResult with a computed verdict.

    The caller's AssembledContext and PassForwardLedger are NEVER mutated.

    Fail-closed: ALL exceptions — including ProviderRefusalError — are wrapped
    in SafetyPassError.  A provider refusal on a Safety call must never silently
    grant a safety ALLOW.

    Args:
        config: Safety configuration.  Defaults to SafetyConfig.from_env().
    """

    def __init__(
        self,
        config: SafetyConfig | None = None,
    ) -> None:
        self._config = config or SafetyConfig.from_env()
        self._system_prompt: str = load_safety_prompt()

    def check(
        self,
        built_context: AssembledContext,
        text: str,
        target: SafetyTarget,
        *,
        provider: ProviderAdapter,
    ) -> SafetyResult:
        """Execute one Safety pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                Never mutated by this call.
            text: The text to evaluate — either the Sojourner's raw input
                (INPUT target) or the Writer's output prose (OUTPUT target).
            target: Which target is being evaluated; determines the label
                placed around the text in the volatile suffix.
            provider: ProviderAdapter for this turn.

        Returns:
            SafetyResult with report (concerns list), target, token counts, and
            computed verdict (ALLOW when concerns is empty, BLOCK otherwise).

        Raises:
            SafetyPassError: on any failure — provider call, parsing, validation,
                or ProviderRefusalError.  Never returns ALLOW on failure.
        """
        request = self._render(built_context, text, target)

        try:
            result = provider.call(request)
        except Exception as exc:
            raise SafetyPassError(
                f"Safety provider call failed: {exc}", cause=exc
            ) from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise SafetyPassError(
                "Safety response missing tool-use block",
                cause=None,
            )
        if tool_parts[0].tool_name != REPORT_SAFETY_TOOL_NAME:
            raise SafetyPassError(
                f"Safety unexpected tool name: {tool_parts[0].tool_name!r}; "
                f"expected {REPORT_SAFETY_TOOL_NAME!r}",
                cause=None,
            )

        try:
            report = SafetyReport.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise SafetyPassError(
                f"Safety tool input failed schema validation: {exc}", cause=exc
            ) from exc

        return SafetyResult(
            report=report,
            target=target,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value,
        )

    # -----------------------------------------------------------------------
    # Private: prompt rendering
    # -----------------------------------------------------------------------

    def _render(
        self,
        built_context: AssembledContext,
        text: str,
        target: SafetyTarget,
    ) -> ProviderCallRequest:
        """Render the AssembledContext + text into a ProviderCallRequest."""
        pass_id = (
            PipelinePassId.INPUT_SAFETY
            if target is SafetyTarget.INPUT
            else PipelinePassId.OUTPUT_SAFETY
        )
        ttl = TTL_EXTENDED if self._config.extended_ttl else TTL_DEFAULT
        rendered_blocks: list[RenderedBlock] = list(
            render_stable_prefix_blocks(built_context.stable_prefix, ttl)
        )

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

        label = _LABEL_INPUT if target is SafetyTarget.INPUT else _LABEL_OUTPUT
        rendered_blocks.append(
            RenderedBlock(
                text=(
                    f"{label}\n{text}\n\n"
                    f"[Intent: {vs.classified_intent.intent_type.value}]"
                )
            )
        )

        return ProviderCallRequest(
            pass_id=pass_id,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=built_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=SAFETY_MAX_TOKENS,
            tool_definitions=[_SAFETY_TOOL_DEF],
            forced_tool_name=REPORT_SAFETY_TOOL_NAME,
        )
