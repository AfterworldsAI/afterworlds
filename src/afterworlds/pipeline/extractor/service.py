"""Extractor service — CRD Issue 10.

Extractor pass: receives AssembledContext + writer_output, calls the LLM using
Anthropic tool use to extract structured narrative proposals, and routes all
proposals through StoryBibleService.route_extractor_proposals() in a single
transactional call.

Architectural invariants enforced here:
  - The Extractor does not commit or manage the DB session.
    StoryBibleService.route_extractor_proposals() owns the transaction.
  - Natural-key resolution failures are fatal: the entire turn is aborted with
    no DB state committed (EntityNotFoundError → ExtractorPassError).
  - Locked-fact proposals are staged as PENDING; they require explicit
    Sojourner confirmation before becoming canon.
  - The Extractor does not create Nodes or Turns; it does not call
    IntentClassifierService, RollingSummaryService, or RulesPackageService.
  - All writes are routed through StoryBibleService; no direct ORM access.
  - ExtractorResult is a typed Pydantic model.  ExtractorPassError is a
    typed exception.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal
from uuid import UUID

from anthropic.types import (
    CacheControlEphemeralParam,
    MessageParam,
    TextBlockParam,
)
from sqlalchemy.orm import Session

from afterworlds.models.context import (
    AssembledContext,
    _render_retrieval_memory,
    _render_rule_slice,
    _render_story_bible_context,
)
from afterworlds.models.extractor import ExtractorProposalSet
from afterworlds.pipeline.extractor.caller import (
    EXTRACT_TOOL_NAME,
    EXTRACT_TOOL_SPEC,
    AnthropicExtractorCaller,
    ExtractorModelCaller,
    ExtractorPayload,
    parse_tool_input,
    timed_call,
)
from afterworlds.pipeline.extractor.config import (
    EXTRACTOR_MAX_TOKENS,
    ExtractorConfig,
)
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.services.story_bible import EntityNotFoundError, StoryBibleService

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the extractor prompt file is missing."""


def load_extractor_prompt() -> str:
    """Load the versioned Extractor system prompt from docs/prompts/extractor.md."""
    prompt_path = _PROMPT_DIR / "extractor.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Extractor prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# TTL constants (mirrors WriterConfig)
# ---------------------------------------------------------------------------

_TTL_EXTENDED: Literal["1h"] = "1h"
_TTL_DEFAULT: Literal["5m"] = "5m"


# ---------------------------------------------------------------------------
# ExtractorService
# ---------------------------------------------------------------------------


class ExtractorService:
    """Extractor pass service.

    Responsibilities:
      1. Render an Anthropic Messages payload from AssembledContext + writer_output.
      2. Invoke the provider via the injected caller (forced tool use).
      3. Parse the ToolUseBlock response.
      4. Validate the tool input against ExtractorProposalSet.
      5. Delegate all routing and DB writes to
         StoryBibleService.route_extractor_proposals() — single transactional call.
      6. Return a typed ExtractorResult.

    Args:
        session: SQLAlchemy session (held for compatibility; session management
            is owned by StoryBibleService.route_extractor_proposals).
        story_bible_service: StoryBibleService instance for all Story Bible
            writes.  Injected so tests can pass a real or spy instance.
        config: Extractor configuration.  Defaults to ExtractorConfig.from_env().
        caller: Injectable model caller.  Defaults to AnthropicExtractorCaller.
    """

    def __init__(
        self,
        session: Session,
        story_bible_service: StoryBibleService,
        config: ExtractorConfig | None = None,
        caller: ExtractorModelCaller | None = None,
    ) -> None:
        self._session = session
        self._sbs = story_bible_service
        self._config = config or ExtractorConfig.from_env()
        self._caller: ExtractorModelCaller = caller or AnthropicExtractorCaller(
            self._config
        )
        self._system_prompt: str = load_extractor_prompt()

    def extract(
        self,
        built_context: AssembledContext,
        writer_output: str,
        story_id: UUID,
        turn_id: UUID,
    ) -> ExtractorResult:
        """Execute one Extractor pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Extractor reuses the same stable prefix as the Writer so
                the Anthropic cache breakpoint is in the same position.
            writer_output: The prose produced by the Writer pass this turn.
            story_id: UUID of the story this turn belongs to.
            turn_id: UUID of the persisted Turn, used as provenance on all
                proposals and canon writes created this pass.

        Returns:
            ExtractorResult with the validated proposal set, routing summary,
            and token metrics.

        Raises:
            ExtractorPassError: if the provider call fails, the response
                contains no tool-use block, the tool input fails schema
                validation, or natural-key resolution fails during routing
                (no DB state is committed in the latter case).
        """
        ctx_story_id = built_context.stable_prefix.story_bible_context.story_id
        if ctx_story_id != story_id:
            raise ExtractorPassError(
                f"built_context story_id {ctx_story_id} does not match "
                f"story_id {story_id}."
            )

        payload = self._render(built_context, writer_output)

        try:
            response, _latency_ms = timed_call(self._caller, payload)
        except Exception as exc:
            raise ExtractorPassError(f"Extractor provider call failed: {exc}") from exc

        try:
            tool_input = parse_tool_input(response)
        except ExtractorPassError:
            raise
        except Exception as exc:
            raise ExtractorPassError(
                f"Extractor response parsing failed: {exc}"
            ) from exc

        try:
            proposal_set = ExtractorProposalSet.model_validate(tool_input)
        except Exception as exc:
            raise ExtractorPassError(
                f"Extractor tool input failed schema validation: {exc}"
            ) from exc

        try:
            routed = self._sbs.route_extractor_proposals(
                story_id, turn_id, proposal_set
            )
        except (EntityNotFoundError, ValueError) as exc:
            raise ExtractorPassError(
                f"Extractor routing failed — no DB state committed: {exc}"
            ) from exc

        usage = response.usage
        return ExtractorResult(
            proposal_set=proposal_set,
            routed=routed,
            input_token_count=usage.input_tokens,
            output_token_count=usage.output_tokens,
            cache_read_token_count=usage.cache_read_input_tokens,
            cache_creation_token_count=usage.cache_creation_input_tokens,
        )

    # -----------------------------------------------------------------------
    # Private: prompt rendering
    # -----------------------------------------------------------------------

    def _render(
        self,
        built_context: AssembledContext,
        writer_output: str,
    ) -> ExtractorPayload:
        """Render the AssembledContext + writer_output into an Extractor payload.

        Cache breakpoint placement:
          - The stable-prefix content blocks are rendered in the canonical
            Issue 8 order with the cache_control marker on the last block.
          - The writer output block and volatile suffix blocks carry no marker.
          - This mirrors the Writer renderer so the Anthropic cache can
            potentially share the stable-prefix region across passes.
        """
        cache_control = CacheControlEphemeralParam(
            type="ephemeral",
            ttl=_TTL_EXTENDED if self._config.extended_ttl else _TTL_DEFAULT,
        )

        stable_texts = _collect_stable_texts(built_context)
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

        # Pass-forward ledger from prior passes (empty in Issue 10 standalone).
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

        # Writer output — appended after the volatile suffix so the stable
        # prefix cache breakpoint is not perturbed.
        user_blocks.append(
            TextBlockParam(
                type="text",
                text=f"[WRITER OUTPUT]\n{writer_output}",
            )
        )

        return {
            "model": self._config.model,
            "max_tokens": EXTRACTOR_MAX_TOKENS,
            "system": [TextBlockParam(type="text", text=self._system_prompt)],
            "messages": [MessageParam(role="user", content=user_blocks)],
            "tools": [EXTRACT_TOOL_SPEC],
            "tool_choice": {"type": "tool", "name": EXTRACT_TOOL_NAME},
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _collect_stable_texts(built_context: AssembledContext) -> list[str]:
    """Return stable-prefix section texts in canonical Issue 8 order.

    Mirrors PromptRenderer._collect_stable_prefix_texts() so the Extractor's
    user-message blocks are byte-for-byte identical to the Writer's, maximising
    the chance of cross-pass cache reuse.
    """
    texts: list[str] = []
    sp = built_context.stable_prefix

    texts.append(_render_story_bible_context(sp.story_bible_context))

    if sp.rolling_summary_text is not None:
        texts.append(sp.rolling_summary_text)

    if sp.rules_package_slice is not None:
        texts.append(_render_rule_slice(sp.rules_package_slice))

    retrieval_text = _render_retrieval_memory(sp.retrieval_memory)
    if retrieval_text:
        texts.append(retrieval_text)

    return texts
