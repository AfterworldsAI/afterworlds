"""Extractor service — CRD Issue 10 / 14a.

Extractor pass: receives AssembledContext + writer_output, builds a
ProviderCallRequest, calls the LLM via the injected ProviderAdapter using
forced tool use, extracts structured narrative proposals, and routes all
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
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.extractor import ExtractorProposalSet
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.extractor.caller import (
    EXTRACT_TOOL_NAME,
    EXTRACT_TOOL_SPEC,
)
from afterworlds.pipeline.extractor.config import (
    EXTRACTOR_MAX_TOKENS,
    ExtractorConfig,
)
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter
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
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_EXTRACTOR_TOOL_DEF = ProviderToolDefinition(
    name=EXTRACT_TOOL_NAME,
    description=EXTRACT_TOOL_SPEC["description"],
    input_schema=EXTRACT_TOOL_SPEC["input_schema"],
)


# ---------------------------------------------------------------------------
# ExtractorService
# ---------------------------------------------------------------------------


class ExtractorService:
    """Extractor pass service.

    Responsibilities:
      1. Render a ProviderCallRequest from AssembledContext + writer_output.
      2. Invoke the provider via the injected ProviderAdapter (forced tool use).
      3. Parse the ProviderToolCallPart response.
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
    """

    def __init__(
        self,
        session: Session,
        story_bible_service: StoryBibleService,
        config: ExtractorConfig | None = None,
    ) -> None:
        self._session = session
        self._sbs = story_bible_service
        self._config = config or ExtractorConfig.from_env()
        self._system_prompt: str = load_extractor_prompt()

    def extract(
        self,
        built_context: AssembledContext,
        writer_output: str,
        story_id: UUID,
        turn_id: UUID,
        *,
        provider: ProviderAdapter,
        session: Session | None = None,
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
            provider: ProviderAdapter for this turn.
            session: optional orchestrator-owned SQLAlchemy session (Issue
                12c).  Forwarded to ``StoryBibleService.route_extractor_proposals``
                so the Extractor's writes nest as a SAVEPOINT inside the
                outer transaction.  When ``None`` the standalone Issue 10
                behavior is preserved.

        Returns:
            ExtractorResult with the validated proposal set, routing summary,
            and token metrics.

        Raises:
            ExtractorPassError: if the provider call fails, the response
                contains no tool-use block, the tool input fails schema
                validation, or natural-key resolution fails during routing
                (no DB state is committed in the latter case).
            ProviderRefusalError: if the provider explicitly refuses the
                Extractor call.  Propagated unchanged so the Issue 12c
                orchestrator can route the turn to REFUSED_BY_PROVIDER and
                roll back the outer transaction.
        """
        ctx_story_id = built_context.stable_prefix.story_bible_context.story_id
        if ctx_story_id != story_id:
            raise ExtractorPassError(
                f"built_context story_id {ctx_story_id} does not match "
                f"story_id {story_id}."
            )

        request = self._render(built_context, writer_output)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise ExtractorPassError(f"Extractor provider call failed: {exc}") from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise ExtractorPassError("Extractor response missing tool-use block")
        if tool_parts[0].tool_name != EXTRACT_TOOL_NAME:
            raise ExtractorPassError(
                f"Extractor unexpected tool name: {tool_parts[0].tool_name!r}; "
                f"expected {EXTRACT_TOOL_NAME!r}"
            )

        try:
            proposal_set = ExtractorProposalSet.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise ExtractorPassError(
                f"Extractor tool input failed schema validation: {exc}"
            ) from exc

        try:
            routed = self._sbs.route_extractor_proposals(
                story_id, turn_id, proposal_set, session=session
            )
        except (EntityNotFoundError, ValueError) as exc:
            raise ExtractorPassError(
                f"Extractor routing failed — no DB state committed: {exc}"
            ) from exc

        return ExtractorResult(
            proposal_set=proposal_set,
            routed=routed,
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
        writer_output: str,
    ) -> ProviderCallRequest:
        """Render the AssembledContext + writer_output into a ProviderCallRequest.

        Cache breakpoint placement:
          - The stable-prefix content blocks come from the shared Issue 12c
            renderer with the cache_control marker on the last block.  This
            is byte-for-byte identical across all six provider-backed passes
            so the cache breakpoint is in the same position regardless of
            which pass renders first.
          - The active mode contract (``stable_prefix.system_prompt``) sits
            in the ``system`` parameter as the second block (matching the
            Planner / Safety convention).  It is no longer included in the
            user-message stable region.
          - The writer-output block and volatile-suffix blocks carry no
            cache marker.
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

        # Writer output — appended after the volatile suffix so the stable
        # prefix cache breakpoint is not perturbed.
        rendered_blocks.append(RenderedBlock(text=f"[WRITER OUTPUT]\n{writer_output}"))

        return ProviderCallRequest(
            pass_id=PipelinePassId.EXTRACTOR,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=built_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=EXTRACTOR_MAX_TOKENS,
            tool_definitions=[_EXTRACTOR_TOOL_DEF],
            forced_tool_name=EXTRACT_TOOL_NAME,
        )
