"""Writer service — CRD Issue 9 / 14a.

Single Writer pass: accepts a BuiltContext (AssembledContext), builds a
ProviderCallRequest, invokes the provider via the injected ProviderAdapter,
parses the response, persists a Turn via Issue 3's CRUD layer, and returns
a typed WriterResult.

No Planner.  No Extractor.  No Contradiction.  No Safety.  No orchestration.

Architectural invariants enforced here:
  - The Writer does not call StoryBibleService, RollingSummaryService,
    RulesPackageService, or IntentClassifierService directly.  AssembledContext
    is the sole input contract.
  - Turn persistence uses Issue 3's CRUD service.  No direct ORM access.
  - WriterResult is a typed Pydantic model.  WriterPassError is a typed
    exception.  Raw strings and dicts are not returned.
  - No Turn is persisted when the provider call fails or produces empty output.
  - The Writer does not create Nodes; the caller supplies node_id.
  - node_id lineage is verified against story_id before any provider call or
    Turn persistence; a mismatched or nonexistent node raises WriterPassError.
  - built_context.stable_prefix.story_bible_context.story_id is verified
    against story_id before rendering; a mismatch raises WriterPassError so
    cross-story context contamination is caught before any provider call.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import IntentType
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_turn, node_belongs_to_story
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderTextPart,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter
from afterworlds.pipeline.writer.config import WRITER_MAX_TOKENS, WriterConfig
from afterworlds.pipeline.writer.models import WriterPassError, WriterResult

# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _render_intent_block(assembled: AssembledContext) -> str:
    """Render the intent classification as a compact structured block."""
    icr = assembled.volatile_suffix.classified_intent
    lines = [
        "[INTENT CLASSIFICATION]",
        f"intent_type: {icr.intent_type.value}",
        f"confidence: {icr.confidence:.3f}",
        f"ambiguous: {icr.ambiguous}",
    ]
    if icr.secondary_intent is not None:
        lines.append(f"secondary_intent: {icr.secondary_intent.value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# WriterService
# ---------------------------------------------------------------------------


class WriterService:
    """Single-pass Writer service.

    Responsibilities:
      1. Render the AssembledContext into a ProviderCallRequest.
      2. Invoke the provider via the injected ProviderAdapter.
      3. Parse the response (plain text concatenation; fail-closed on empty or
         malformed output).
      4. Persist the resulting Turn via Issue 3 CRUD services.
      5. Return a typed WriterResult.

    Args:
        session: SQLAlchemy session used for Turn persistence.
        config: Writer configuration (model, API key source, TTL mode).
    """

    def __init__(
        self,
        session: Session,
        config: WriterConfig | None = None,
    ) -> None:
        self._session = session
        self._config = config or WriterConfig.from_env()

    def write(
        self,
        built_context: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        *,
        provider: ProviderAdapter,
        session: Session | None = None,
    ) -> WriterResult:
        """Execute one Writer pass and return a typed result with a persisted Turn.

        Args:
            built_context: AssembledContext produced by Issue 8's
                ContextBuilderService.  The Writer does not assemble context
                itself; AssembledContext is the input contract.
            story_id: UUID of the story this turn belongs to.  Validated
                against the node_id lineage (Node → Chapter → Arc → Story)
                before any provider call or Turn persistence.
            node_id: UUID of the already-seeded Node to link the Turn to.
                The Writer does not create Nodes — the caller is responsible for
                having seeded a valid Arc/Chapter/Node chain.
            provider: ProviderAdapter for this turn.
            session: optional orchestrator-owned SQLAlchemy session (Issue
                12c).  When supplied the Turn write joins the caller's outer
                transaction and the Writer does NOT call ``commit``; the
                orchestrator commits or rolls back at the gate boundary.
                When ``None`` the standalone Issue 3 / 9 behavior is
                preserved: the constructor-injected session is used and the
                Writer commits at the end of a successful write.

        Returns:
            WriterResult with the persisted turn_id, assistant_output, model
            identifier, latency, and token/cache metrics.

        Raises:
            WriterPassError: if built_context was assembled for a different
                story_id, if node_id does not belong to story_id, the provider
                call fails, the response is malformed, or the parsed output is
                empty after trimming.  No Turn is persisted in any error case.
            ProviderRefusalError: if the provider explicitly refuses the
                call.  Propagated unchanged so the Issue 12c orchestrator can
                route the turn to REFUSED_BY_PROVIDER and roll back the
                outer transaction.  The Writer does NOT downgrade refusals
                into WriterPassError.
        """
        target_session: Session = session if session is not None else self._session

        if not node_belongs_to_story(target_session, node_id, story_id):
            raise WriterPassError(
                f"node {node_id} does not belong to story {story_id}; "
                "no Turn persisted"
            )

        context_story_id = built_context.stable_prefix.story_bible_context.story_id
        if context_story_id != story_id:
            raise WriterPassError(
                f"built_context was assembled for story {context_story_id}, "
                f"not story {story_id}; no Turn persisted"
            )

        request = self._render(built_context)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise WriterPassError(f"Writer provider call failed: {exc}") from exc

        try:
            prose = self._parse_result(result)
        except WriterPassError:
            raise
        except Exception as exc:
            raise WriterPassError(f"Writer response parsing failed: {exc}") from exc

        icr = built_context.volatile_suffix.classified_intent
        turn = Turn(
            user_input=built_context.volatile_suffix.current_input,
            assistant_output=prose,
            timestamp=datetime.now(UTC),
            intent_classification=IntentType(icr.intent_type.value),
            node_id=node_id,
            intent_classification_result=icr,
        )
        create_turn(target_session, turn)
        if session is None:
            target_session.commit()

        return WriterResult(
            turn_id=turn.turn_id,
            assistant_output=prose,
            model_identifier=result.model_identifier,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
            provider=result.provider_name,
            model_tier=result.model_tier.value,
        )

    # ---------------------------------------------------------------------------
    # Private: rendering
    # ---------------------------------------------------------------------------

    def _render(self, assembled: AssembledContext) -> ProviderCallRequest:
        """Render an AssembledContext into a ProviderCallRequest.

        Cache breakpoint sits on the final stable-prefix content block.
        PassForwardLedger blocks (when non-empty) appear after the breakpoint.
        VolatileSuffix blocks appear last with no cache marker.

        System parameter: one block — the active mode contract.  The Writer
        has no separate pass-contract file; the mode contract is the full
        system instruction.
        """
        ttl = TTL_EXTENDED if self._config.extended_ttl else TTL_DEFAULT
        rendered_blocks: list[RenderedBlock] = list(
            render_stable_prefix_blocks(assembled.stable_prefix, ttl)
        )

        ledger_text = assembled.pass_forward_ledger.render()
        if ledger_text:
            rendered_blocks.append(RenderedBlock(text=ledger_text))

        for turn in assembled.volatile_suffix.recent_turns:
            rendered_blocks.append(
                RenderedBlock(
                    text=(
                        f"Player: {turn.user_input}\n"
                        f"Narrator: {turn.assistant_output}"
                    )
                )
            )
        rendered_blocks.append(
            RenderedBlock(text=assembled.volatile_suffix.current_input)
        )
        rendered_blocks.append(RenderedBlock(text=_render_intent_block(assembled)))

        return ProviderCallRequest(
            pass_id=PipelinePassId.WRITER,
            system_blocks=[RenderedBlock(text=assembled.stable_prefix.system_prompt)],
            rendered_blocks=rendered_blocks,
            max_output_tokens=WRITER_MAX_TOKENS,
        )

    # ---------------------------------------------------------------------------
    # Private: response parsing
    # ---------------------------------------------------------------------------

    def _parse_result(self, result: object) -> str:
        """Parse a ProviderCallResult and return trimmed prose.

        Parsing rules (explicit, no silent fallback):
          1. Iterate content_parts in order.
          2. Concatenate the text field of every ProviderTextPart.
          3. Trim leading and trailing whitespace.
          4. If the result is empty, raise WriterPassError.
          5. If the envelope is malformed (missing required fields), raise
             WriterPassError with the underlying AttributeError preserved.

        Args:
            result: The ProviderCallResult from the adapter.

        Returns:
            Trimmed prose string (non-empty).

        Raises:
            WriterPassError: on empty output or malformed result envelope.
        """
        from afterworlds.pipeline.provider._models import ProviderCallResult

        if not isinstance(result, ProviderCallResult):
            raise WriterPassError(
                f"Unexpected result type from provider: {type(result).__name__}"
            )

        parts: list[str] = []
        for part in result.content_parts:
            if isinstance(part, ProviderTextPart):
                parts.append(part.text)

        prose = "".join(parts).strip()
        if not prose:
            raise WriterPassError(
                "Writer produced empty output after trimming whitespace. "
                "No Turn persisted."
            )
        return prose
