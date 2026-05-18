"""Safety pass service — CRD Issue 12b.

Safety envelope: receives AssembledContext + text + SafetyTarget, renders an
Anthropic Messages payload, calls the LLM using Anthropic tool use, validates
the SafetyReport, and returns a typed SafetyResult.

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
  - Fail-closed: SafetyPassError on any provider, parsing, or validation
    failure.  No silent ALLOW.
"""

from __future__ import annotations

from pathlib import Path

from anthropic.types import (
    MessageParam,
    TextBlockParam,
)

from afterworlds.models.context import AssembledContext
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.safety.caller import (
    REPORT_SAFETY_TOOL_NAME,
    REPORT_SAFETY_TOOL_SPEC,
    AnthropicSafetyCaller,
    SafetyModelCaller,
    SafetyPayload,
    parse_tool_input,
    timed_call,
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
    TokenUsage,
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
# SafetyService
# ---------------------------------------------------------------------------


class SafetyService:
    """Safety pass service.

    Responsibilities:
      1. Render the AssembledContext + evaluated text into an Anthropic
         Messages payload.
         System parameter: two blocks — Safety pass contract and active mode
         contract.  User-message stable-prefix blocks start with Story Bible.
      2. Invoke the provider via the injected caller (forced tool use).
      3. Parse the ToolUseBlock response.
      4. Validate the tool input against SafetyReport.
      5. Return a typed SafetyResult with a computed verdict.

    The caller's AssembledContext and PassForwardLedger are NEVER mutated.

    Args:
        config: Safety configuration.  Defaults to SafetyConfig.from_env().
        caller: Injectable model caller.  Defaults to AnthropicSafetyCaller.
    """

    def __init__(
        self,
        config: SafetyConfig | None = None,
        caller: SafetyModelCaller | None = None,
    ) -> None:
        self._config = config or SafetyConfig.from_env()
        self._caller: SafetyModelCaller = caller or AnthropicSafetyCaller(self._config)
        self._system_prompt: str = load_safety_prompt()

    def check(
        self,
        built_context: AssembledContext,
        text: str,
        target: SafetyTarget,
    ) -> SafetyResult:
        """Execute one Safety pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                Never mutated by this call.
            text: The text to evaluate — either the Sojourner's raw input
                (INPUT target) or the Writer's output prose (OUTPUT target).
            target: Which target is being evaluated; determines the label
                placed around the text in the volatile suffix.

        Returns:
            SafetyResult with report (concerns list), target, usage, and
            computed verdict (ALLOW when concerns is empty, BLOCK otherwise).

        Raises:
            SafetyPassError: if the provider call fails, the response contains
                no tool-use block, or the tool input fails schema validation.
                Never returns ALLOW on failure — always raises.
        """
        payload = self._render(built_context, text, target)

        try:
            response, _latency_ms = timed_call(self._caller, payload)
        except SafetyPassError:
            raise
        except Exception as exc:
            raise SafetyPassError(
                f"Safety provider call failed: {exc}", cause=exc
            ) from exc

        try:
            tool_input = parse_tool_input(response)
        except SafetyPassError:
            raise
        except Exception as exc:
            raise SafetyPassError(
                f"Safety response parsing failed: {exc}", cause=exc
            ) from exc

        try:
            report = SafetyReport.model_validate(tool_input)
        except Exception as exc:
            raise SafetyPassError(
                f"Safety tool input failed schema validation: {exc}", cause=exc
            ) from exc

        raw_usage = response.usage
        usage = TokenUsage(
            input_tokens=raw_usage.input_tokens,
            output_tokens=raw_usage.output_tokens,
            cache_read_input_tokens=raw_usage.cache_read_input_tokens,
            cache_creation_input_tokens=raw_usage.cache_creation_input_tokens,
        )

        return SafetyResult(report=report, target=target, usage=usage)

    # -----------------------------------------------------------------------
    # Private: prompt rendering
    # -----------------------------------------------------------------------

    def _render(
        self,
        built_context: AssembledContext,
        text: str,
        target: SafetyTarget,
    ) -> SafetyPayload:
        """Render the AssembledContext + text into a Safety payload."""
        ttl = TTL_EXTENDED if self._config.extended_ttl else TTL_DEFAULT
        user_blocks: list[TextBlockParam] = list(
            render_stable_prefix_blocks(built_context.stable_prefix, ttl)
        )

        # Volatile suffix: recent turns + evaluated text with target label.
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

        label = _LABEL_INPUT if target == SafetyTarget.INPUT else _LABEL_OUTPUT
        user_blocks.append(
            TextBlockParam(
                type="text",
                text=(
                    f"{label}\n{text}\n\n"
                    f"[Intent: {vs.classified_intent.intent_type.value}]"
                ),
            )
        )

        return {
            "model": self._config.model,
            "max_tokens": SAFETY_MAX_TOKENS,
            "system": [
                TextBlockParam(type="text", text=self._system_prompt),
                TextBlockParam(
                    type="text",
                    text=built_context.stable_prefix.system_prompt,
                ),
            ],
            "messages": [MessageParam(role="user", content=user_blocks)],
            "tools": [REPORT_SAFETY_TOOL_SPEC],
            "tool_choice": {
                "type": "tool",
                "name": REPORT_SAFETY_TOOL_NAME,
            },
        }
