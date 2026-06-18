"""Contradiction pass service — CRD Issue 11 / 14a.

Contradiction pass: receives AssembledContext + writer_output, derives a new
context where the Writer output appears in the PassForwardLedger (rendered
before the volatile suffix), builds a ProviderCallRequest, calls the LLM via
the injected ProviderAdapter using forced tool use, validates the flat
ContradictionReport, and returns a typed ContradictionResult.

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

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
)
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.contradiction.caller import (
    REPORT_TOOL_NAME,
    REPORT_TOOL_SPEC,
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
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_CONTRADICTION_TOOL_DEF = ProviderToolDefinition(
    name=REPORT_TOOL_NAME,
    description=REPORT_TOOL_SPEC["description"],
    input_schema=REPORT_TOOL_SPEC["input_schema"],
)


# ---------------------------------------------------------------------------
# ContradictionService
# ---------------------------------------------------------------------------


class ContradictionService:
    """Contradiction pass service.

    Responsibilities:
      1. Derive a new AssembledContext where writer_output is inserted into the
         PassForwardLedger (renders as "[WRITER OUTPUT]\\n..." before the
         volatile suffix).  The caller's context is never mutated.
      2. Render a ProviderCallRequest from the derived context.
      3. Invoke the provider via the injected ProviderAdapter (forced tool use).
      4. Parse the ProviderToolCallPart response.
      5. Validate the tool input against ContradictionReport.
      6. Derive the verdict from the violations list.
      7. Return a typed ContradictionResult.

    Args:
        config: Contradiction configuration.  Defaults to
            ContradictionConfig.from_env().
    """

    def __init__(
        self,
        config: ContradictionConfig | None = None,
    ) -> None:
        self._config = config or ContradictionConfig.from_env()
        self._system_prompt: str = load_contradiction_prompt()

    def check(
        self,
        built_context: AssembledContext,
        writer_output: str,
        *,
        provider: ProviderAdapter,
    ) -> ContradictionResult:
        """Execute one Contradiction pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Contradiction pass derives a new context from this without
                mutating it.
            writer_output: The prose produced by the Writer pass this turn.
            provider: ProviderAdapter for this turn.

        Returns:
            ContradictionResult with the derived verdict, violations, and
            token metrics.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER routing.
            ContradictionPassError: if the provider call fails, the response
                contains no tool-use block, or the tool input fails schema
                validation.
        """
        derived = _derive_context(built_context, writer_output)
        request = self._render(derived)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise ContradictionPassError(
                f"Contradiction provider call failed: {exc}"
            ) from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise ContradictionPassError(
                "Contradiction response missing tool-use block"
            )
        if tool_parts[0].tool_name != REPORT_TOOL_NAME:
            raise ContradictionPassError(
                f"Contradiction unexpected tool name: {tool_parts[0].tool_name!r}; "
                f"expected {REPORT_TOOL_NAME!r}"
            )

        try:
            report = ContradictionReport.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise ContradictionPassError(
                f"Contradiction tool input failed schema validation: {exc}"
            ) from exc

        verdict = (
            ContradictionVerdict.BLOCKED
            if report.violations
            else ContradictionVerdict.CLEAR
        )

        return ContradictionResult(
            verdict=verdict,
            violations=report.violations,
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

    def _render(self, derived_context: AssembledContext) -> ProviderCallRequest:
        """Render the derived AssembledContext into a ProviderCallRequest.

        Cache breakpoint placement:
          - Stable-prefix blocks come from the shared Issue 12c renderer
            with the cache_control marker on the last block.  All six
            provider-backed passes render the same stable region in the
            same order so the cache breakpoint is in the same position
            across passes (CRD Item 14 invariant #10).
          - The active mode contract (``stable_prefix.system_prompt``) sits
            in the ``system`` parameter as the second block (matching the
            Planner / Safety convention).  It is no longer included in the
            user-message stable region.
          - PassForwardLedger (containing the Writer output) renders after
            the stable prefix with no cache marker.
          - Volatile suffix blocks carry no marker.
        """
        ttl = TTL_EXTENDED if self._config.extended_ttl else TTL_DEFAULT
        rendered_blocks: list[RenderedBlock] = list(
            render_stable_prefix_blocks(derived_context.stable_prefix, ttl)
        )

        ledger_text = derived_context.pass_forward_ledger.render()
        if ledger_text:
            rendered_blocks.append(RenderedBlock(text=ledger_text))

        vs = derived_context.volatile_suffix
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
            pass_id=PipelinePassId.CONTRADICTION,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=derived_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=CONTRADICTION_MAX_TOKENS,
            tool_definitions=[_CONTRADICTION_TOOL_DEF],
            forced_tool_name=REPORT_TOOL_NAME,
        )


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
