"""Branching Writer pass service — CRD Issue 16.

Responsibilities:
  1. Load the branching mode prompt contract at init time.
  2. Render AssembledContext + BranchingSessionState into a ProviderCallRequest
     with forced tool use (``produce_branch_output``).
  3. Call the LLM → ``BranchingWriterProposal``.
  4. Validate branch option count against the session's ``branch_count_range``.
     Fail-closed: out-of-range count raises ``BranchingPassError`` (never
     clamp, pad, or truncate).
  5. Code-stamp all affordance fields from session state:
     - ``interaction_style`` (from session state)
     - ``branching_cadence`` (from session state)
     - ``freeform_available`` (derived: True iff style is not TRUE_CYOA)
     - ``branch_count_range`` (from session state)
     - ``option_id`` for each branch option (sequential: opt_1, opt_2, …)
  6. Return ``BranchingPassResult`` with validated, code-stamped output.

Architectural invariants:
  - This service is called ONLY for HYBRID and TRUE_CYOA modes.
    FREEFORM_ONLY stays on the prose WriterService (no branch cards).
  - Code owns all affordances; the model proposes prose + labels only.
  - Schema shape enforces the invariant: option_id / interaction_style /
    branching_cadence / freeform_available / branch_count_range are all
    absent from the tool input_schema.
  - Fail-closed: BranchingPassError on any provider, parse, schema, or
    range-validation failure.  No silent fallback.
  - ProviderRefusalError is propagated unchanged (orchestrator routes to
    REFUSED_BY_PROVIDER).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import InteractionStyle
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.branching.caller import (
    PRODUCE_BRANCH_OUTPUT_TOOL_NAME,
    PRODUCE_BRANCH_OUTPUT_TOOL_SPEC,
)
from afterworlds.pipeline.branching.config import (
    BRANCH_COUNT_RANGE_BOUNDS,
    BRANCHING_WRITER_MAX_TOKENS,
    BranchingWriterConfig,
)
from afterworlds.pipeline.branching.models import (
    BranchingPassError,
    BranchingPassResult,
    BranchingWriterProposal,
    BranchOption,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)

if TYPE_CHECKING:
    from afterworlds.models.session import BranchingSessionState
    from afterworlds.pipeline.provider._protocol import ProviderAdapter

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the branching writer prompt file is missing."""


def load_branching_writer_prompt() -> str:
    """Load the Branching Writer pass system prompt from docs/prompts/."""
    prompt_path = _PROMPT_DIR / "branching_mode.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Branching writer prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_BRANCHING_TOOL_DEF = ProviderToolDefinition(
    name=PRODUCE_BRANCH_OUTPUT_TOOL_NAME,
    description=PRODUCE_BRANCH_OUTPUT_TOOL_SPEC["description"],
    input_schema=PRODUCE_BRANCH_OUTPUT_TOOL_SPEC["input_schema"],
)


# ---------------------------------------------------------------------------
# Branch-count range validation helper
# ---------------------------------------------------------------------------


def _validate_branch_count(
    branch_options_text: list[str],
    branch_count_range: str | None,
) -> None:
    """Validate proposed branch option count against the session's range.

    Raises ``BranchingPassError`` when:
    - ``branch_count_range`` is set and the count is outside [min, max].
    - ``branch_count_range`` is set but unknown (not in BRANCH_COUNT_RANGE_BOUNDS).

    Never clamps, pads, or truncates.  Out-of-range is a hard fail-closed error.
    """
    if branch_count_range is None:
        return
    bounds = BRANCH_COUNT_RANGE_BOUNDS.get(branch_count_range)
    if bounds is None:
        raise BranchingPassError(f"Unknown branch_count_range {branch_count_range!r}")
    min_opts, max_opts = bounds
    n = len(branch_options_text)
    if n < min_opts or n > max_opts:
        raise BranchingPassError(
            f"Model proposed {n} branch option(s) but session branch_count_range"
            f" {branch_count_range!r} requires between {min_opts} and {max_opts}."
            " Never clamp or pad — model output violates the range contract."
        )


# ---------------------------------------------------------------------------
# BranchingWriterService
# ---------------------------------------------------------------------------


class BranchingWriterService:
    """Branching Writer pass service.

    Produces narrative text + code-stamped branch options via forced tool use.
    Called ONLY for HYBRID and TRUE_CYOA interaction styles; FREEFORM_ONLY
    turns bypass this service entirely and use the prose WriterService.

    Args:
        config: Branching writer config.  Defaults to BranchingWriterConfig.from_env().
    """

    def __init__(
        self,
        config: BranchingWriterConfig | None = None,
    ) -> None:
        self._config = config or BranchingWriterConfig.from_env()
        self._system_prompt: str = load_branching_writer_prompt()

    def write(
        self,
        built_context: AssembledContext,
        session_state: BranchingSessionState,
        *,
        provider: ProviderAdapter,
    ) -> BranchingPassResult:
        """Execute one branching writer pass and return a typed result.

        Args:
            built_context: AssembledContext from the Context Builder.
            session_state: Current BranchingSessionState with interaction config.
            provider: ProviderAdapter for the LLM call.

        Returns:
            BranchingPassResult with code-stamped affordances and validated options.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER.
            BranchingPassError: LLM call failure, missing tool block, schema
                validation failure, or branch-count range violation.
        """
        request = self._render(built_context, session_state)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise BranchingPassError(
                f"Branching writer provider call failed: {exc}"
            ) from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise BranchingPassError("Branching writer response missing tool-use block")
        if tool_parts[0].tool_name != PRODUCE_BRANCH_OUTPUT_TOOL_NAME:
            raise BranchingPassError(
                f"Branching writer unexpected tool name: {tool_parts[0].tool_name!r};"
                f" expected {PRODUCE_BRANCH_OUTPUT_TOOL_NAME!r}"
            )

        try:
            proposal = BranchingWriterProposal.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise BranchingPassError(
                f"Branching writer tool input failed schema validation: {exc}"
            ) from exc

        # Validate branch option count before stamping — fail-closed.
        branch_count_range_val = (
            session_state.branch_count_range.value
            if session_state.branch_count_range is not None
            else None
        )
        _validate_branch_count(proposal.branch_options_text, branch_count_range_val)

        # Code stamps: option_id assigned sequentially.
        branch_options = [
            BranchOption(option_id=f"opt_{i + 1}", action_text=text)
            for i, text in enumerate(proposal.branch_options_text)
        ]

        # Code derives freeform_available from interaction_style.
        interaction_style = session_state.interaction_style
        if interaction_style is None:
            raise BranchingPassError(
                "BranchingWriterService called with interaction_style=None;"
                " cannot produce branch output without a configured style."
            )
        freeform_available = interaction_style is not InteractionStyle.TRUE_CYOA

        branching_cadence = session_state.branching_cadence
        if branching_cadence is None:
            raise BranchingPassError(
                "BranchingWriterService called with branching_cadence=None;"
                " cannot produce branch output without a configured cadence."
            )

        return BranchingPassResult(
            narrative_text=proposal.narrative_text,
            interaction_style=interaction_style,
            branching_cadence=branching_cadence,
            length_preference=session_state.length_preference,
            freeform_available=freeform_available,
            branch_count_range=session_state.branch_count_range,
            branch_options=branch_options,
            branch_presentation_state=proposal.branch_presentation_state,
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value if result.model_tier else None,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )

    # -----------------------------------------------------------------------
    # Prompt rendering
    # -----------------------------------------------------------------------

    def _render(
        self,
        built_context: AssembledContext,
        session_state: BranchingSessionState,
    ) -> ProviderCallRequest:
        """Render AssembledContext into a ProviderCallRequest.

        Stable-prefix blocks are shared with the Planner for cache reuse.
        A session-state summary is appended to the volatile suffix so the model
        knows the active interaction style, cadence, and branch count range
        without those values appearing in the tool schema (they are code-owned).
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

        # Session-state context block: informs the model of active configuration
        # so it can calibrate density/length/branch count — but code validates all.
        _ss = session_state
        _style_v = _ss.interaction_style.value if _ss.interaction_style else "not_set"
        _cadence_v = _ss.branching_cadence.value if _ss.branching_cadence else "not_set"
        _len_v = _ss.length_preference.value if _ss.length_preference else "not_set"
        _range_v = _ss.branch_count_range.value if _ss.branch_count_range else "none"
        _free_v = (
            str(_ss.interaction_style is not InteractionStyle.TRUE_CYOA)
            if _ss.interaction_style
            else "unknown"
        )
        session_context_lines = [
            "[Branching Session Configuration]",
            f"interaction_style: {_style_v}",
            f"branching_cadence: {_cadence_v}",
            f"length_preference: {_len_v}",
            f"branch_count_range: {_range_v}",
            f"freeform_available: {_free_v}",
        ]
        rendered_blocks.append(RenderedBlock(text="\n".join(session_context_lines)))

        rendered_blocks.append(
            RenderedBlock(
                text=(
                    f"Player: {vs.current_input}\n"
                    f"[Intent: {vs.classified_intent.intent_type.value}]"
                )
            )
        )

        return ProviderCallRequest(
            pass_id=PipelinePassId.BRANCHING_WRITER,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=built_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=BRANCHING_WRITER_MAX_TOKENS,
            tool_definitions=[_BRANCHING_TOOL_DEF],
            forced_tool_name=PRODUCE_BRANCH_OUTPUT_TOOL_NAME,
        )


__all__ = [
    "BranchingWriterService",
    "UnknownPromptError",
    "load_branching_writer_prompt",
]
