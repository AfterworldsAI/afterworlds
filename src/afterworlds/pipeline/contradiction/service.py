"""Contradiction pass service — CRD Issue 11.

Contradiction pass: receives AssembledContext + writer_output, derives a new
context where the Writer output appears in the PassForwardLedger (rendered
before the volatile suffix), calls the LLM using Anthropic tool use, validates
the flat ContradictionReport, and returns a typed ContradictionResult.

Architectural invariants enforced here:
  - The Contradiction pass does NOT write canon, does NOT persist, and does NOT
    mutate the caller's AssembledContext.
  - Writer output is inserted into a DERIVED PassForwardLedger so it renders
    as "[WRITER OUTPUT]\\n{content}" before the volatile suffix — matching the
    PassForwardLedger.render() format defined in AssembledContext.
  - Verdict is DERIVED at construction time: BLOCKED if violations non-empty,
    CLEAR otherwise.  The model does not model the verdict directly.
  - Extended TTL caching is enabled by default (CRD Item 14 invariant #9).
  - Stable prompt prefix is shared with the Writer pass via cache breakpoint
    on the final stable-prefix block (CRD Item 14 invariant #10).
  - Fail-closed: ContradictionPassError on any provider, parsing, or validation
    failure.  No silent fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from anthropic.types import (
    CacheControlEphemeralParam,
    MessageParam,
    TextBlockParam,
)

from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    _render_retrieval_memory,
    _render_rule_slice,
    _render_story_bible_context,
)
from afterworlds.pipeline.contradiction.caller import (
    REPORT_TOOL_NAME,
    REPORT_TOOL_SPEC,
    AnthropicContradictionCaller,
    ContradictionModelCaller,
    ContradictionPayload,
    parse_tool_input,
    timed_call,
)
from afterworlds.pipeline.contradiction.config import (
    CONTRADICTION_MAX_TOKENS,
    ContradictionConfig,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionPassError,
    ContradictionReport,
    ContradictionResult,
    ContradictionVerdict,
)

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the contradiction prompt file is missing."""


def load_contradiction_prompt() -> str:
    """Load the Contradiction pass system prompt from docs/prompts/contradiction.md."""
    prompt_path = _PROMPT_DIR / "contradiction.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Contradiction prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

_TTL_EXTENDED: Literal["1h"] = "1h"
_TTL_DEFAULT: Literal["5m"] = "5m"


# ---------------------------------------------------------------------------
# ContradictionService
# ---------------------------------------------------------------------------


class ContradictionService:
    """Contradiction pass service.

    Responsibilities:
      1. Derive a new AssembledContext where writer_output is inserted into the
         PassForwardLedger (renders as "[WRITER OUTPUT]\\n..." before the
         volatile suffix).  The caller's context is never mutated.
      2. Render an Anthropic Messages payload from the derived context.
      3. Invoke the provider via the injected caller (forced tool use).
      4. Parse the ToolUseBlock response.
      5. Validate the tool input against ContradictionReport.
      6. Derive the verdict from the violations list.
      7. Return a typed ContradictionResult.

    Args:
        config: Contradiction configuration.  Defaults to
            ContradictionConfig.from_env().
        caller: Injectable model caller.  Defaults to
            AnthropicContradictionCaller.
    """

    def __init__(
        self,
        config: ContradictionConfig | None = None,
        caller: ContradictionModelCaller | None = None,
    ) -> None:
        self._config = config or ContradictionConfig.from_env()
        self._caller: ContradictionModelCaller = caller or AnthropicContradictionCaller(
            self._config
        )
        self._system_prompt: str = load_contradiction_prompt()

    def check(
        self,
        built_context: AssembledContext,
        writer_output: str,
    ) -> ContradictionResult:
        """Execute one Contradiction pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Contradiction pass derives a new context from this without
                mutating it.
            writer_output: The prose produced by the Writer pass this turn.

        Returns:
            ContradictionResult with the derived verdict, violations, and
            token metrics.

        Raises:
            ContradictionPassError: if the provider call fails, the response
                contains no tool-use block, or the tool input fails schema
                validation.
        """
        derived = _derive_context(built_context, writer_output)
        payload = self._render(derived)

        try:
            response, latency_ms = timed_call(self._caller, payload)
        except Exception as exc:
            raise ContradictionPassError(
                f"Contradiction provider call failed: {exc}"
            ) from exc

        try:
            tool_input = parse_tool_input(response)
        except ContradictionPassError:
            raise
        except Exception as exc:
            raise ContradictionPassError(
                f"Contradiction response parsing failed: {exc}"
            ) from exc

        try:
            report = ContradictionReport.model_validate(tool_input)
        except Exception as exc:
            raise ContradictionPassError(
                f"Contradiction tool input failed schema validation: {exc}"
            ) from exc

        verdict = (
            ContradictionVerdict.BLOCKED
            if report.violations
            else ContradictionVerdict.CLEAR
        )

        usage = response.usage
        return ContradictionResult(
            verdict=verdict,
            violations=report.violations,
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

    def _render(self, derived_context: AssembledContext) -> ContradictionPayload:
        """Render the derived AssembledContext into a Contradiction payload.

        Cache breakpoint placement:
          - Stable-prefix blocks carry the cache_control marker on the last
            block, matching the Writer renderer so the Anthropic cache can
            share the stable-prefix region across passes.
          - PassForwardLedger (containing the Writer output) renders after the
            stable prefix with no cache marker.
          - Volatile suffix blocks carry no marker.
        """
        cache_control = CacheControlEphemeralParam(
            type="ephemeral",
            ttl=_TTL_EXTENDED if self._config.extended_ttl else _TTL_DEFAULT,
        )

        stable_texts = _collect_stable_texts(derived_context)
        user_blocks: list[TextBlockParam] = []

        if stable_texts:
            for text in stable_texts[:-1]:
                user_blocks.append(TextBlockParam(type="text", text=text))
            user_blocks.append(
                TextBlockParam(
                    type="text",
                    text=stable_texts[-1],
                    cache_control=cache_control,
                )
            )

        # PassForwardLedger includes the Writer output (added by _derive_context).
        ledger_text = derived_context.pass_forward_ledger.render()
        if ledger_text:
            user_blocks.append(TextBlockParam(type="text", text=ledger_text))

        # Volatile suffix: recent turns + current input + intent.
        vs = derived_context.volatile_suffix
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
            "max_tokens": CONTRADICTION_MAX_TOKENS,
            "system": [TextBlockParam(type="text", text=self._system_prompt)],
            "messages": [MessageParam(role="user", content=user_blocks)],
            "tools": [REPORT_TOOL_SPEC],
            "tool_choice": {"type": "tool", "name": REPORT_TOOL_NAME},
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _derive_context(
    built_context: AssembledContext, writer_output: str
) -> AssembledContext:
    """Return a new AssembledContext with writer_output in the ledger.

    Idempotent around Writer output so that Issue 12 can pre-populate the
    ledger without accidentally duplicating evidence in the Contradiction
    prompt.  Rules:

    - No existing ``writer`` entry → append ``writer_output``.
    - Exactly one ``writer`` entry whose content matches ``writer_output``
      → return derived context as-is (no duplicate appended).
    - Exactly one ``writer`` entry whose content differs → raise
      ``ContradictionPassError`` (stale or conflicting ledger).
    - Multiple ``writer`` entries → raise ``ContradictionPassError``.

    The caller's original context is never mutated.
    """
    writer_entries = [
        e for e in built_context.pass_forward_ledger.entries if e.pass_name == "writer"
    ]

    if len(writer_entries) > 1:
        raise ContradictionPassError(
            f"PassForwardLedger contains {len(writer_entries)} 'writer' entries; "
            "expected at most one."
        )

    if len(writer_entries) == 1:
        existing = writer_entries[0].content
        if existing == writer_output:
            # Already present and consistent — return a copy without appending.
            new_ledger = PassForwardLedger(
                entries=list(built_context.pass_forward_ledger.entries)
            )
            return AssembledContext(
                stable_prefix=built_context.stable_prefix,
                volatile_suffix=built_context.volatile_suffix,
                pass_forward_ledger=new_ledger,
            )
        raise ContradictionPassError(
            "PassForwardLedger already contains a 'writer' entry whose content "
            "differs from the supplied writer_output.  Refusing to overwrite."
        )

    new_ledger = PassForwardLedger(
        entries=list(built_context.pass_forward_ledger.entries)
    )
    new_ledger.add("writer", writer_output)
    return AssembledContext(
        stable_prefix=built_context.stable_prefix,
        volatile_suffix=built_context.volatile_suffix,
        pass_forward_ledger=new_ledger,
    )


def _collect_stable_texts(built_context: AssembledContext) -> list[str]:
    """Return stable-prefix section texts in canonical Issue 8 order.

    Mirrors the Writer and Extractor renderers so the Contradiction pass's
    user-message blocks are byte-for-byte identical to the prior passes',
    maximising the chance of cross-pass cache reuse.

    Order:
      1. Mode contract (system_prompt) — POV/tense/agency/mode-specific rules
      2. Story Bible active context
      3. Rolling Summary (omitted if None)
      4. Rules Package slice (omitted if None)
      5. Retrieval Memory (omitted when empty)
    """
    texts: list[str] = []
    sp = built_context.stable_prefix

    texts.append(sp.system_prompt)
    texts.append(_render_story_bible_context(sp.story_bible_context))

    if sp.rolling_summary_text is not None:
        texts.append(sp.rolling_summary_text)

    if sp.rules_package_slice is not None:
        texts.append(_render_rule_slice(sp.rules_package_slice))

    retrieval_text = _render_retrieval_memory(sp.retrieval_memory)
    if retrieval_text:
        texts.append(retrieval_text)

    return texts
