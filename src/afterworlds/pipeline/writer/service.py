"""Writer service — CRD Issue 9.

Single Writer pass: accepts a BuiltContext (AssembledContext), renders it to
an Anthropic Messages API payload, invokes the provider, parses the response,
persists a Turn via Issue 3's CRUD layer, and returns a typed WriterResult.

No Planner.  No Extractor.  No Contradiction.  No Safety.  No orchestration.
This is proof-of-life for the first real provider call in the system.

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

from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import IntentType
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import create_turn, node_belongs_to_story
from afterworlds.pipeline.writer.caller import (
    AnthropicModelCaller,
    WriterModelCaller,
    timed_call,
)
from afterworlds.pipeline.writer.config import WriterConfig
from afterworlds.pipeline.writer.models import WriterPassError, WriterResult
from afterworlds.pipeline.writer.renderer import PromptRenderer


class WriterService:
    """Single-pass Writer service.

    Responsibilities:
      1. Render the AssembledContext into an Anthropic Messages payload.
      2. Invoke the provider via the injected caller.
      3. Parse the response (plain text concatenation; fail-closed on empty or
         malformed output).
      4. Persist the resulting Turn via Issue 3 CRUD services.
      5. Return a typed WriterResult.

    Args:
        session: SQLAlchemy session used for Turn persistence.
        config: Writer configuration (model, API key source, TTL mode).
        caller: Injectable model caller.  Defaults to AnthropicModelCaller.
            Tests substitute a fake; no real network call occurs in unit tests.
    """

    def __init__(
        self,
        session: Session,
        config: WriterConfig | None = None,
        caller: WriterModelCaller | None = None,
    ) -> None:
        self._session = session
        self._config = config or WriterConfig.from_env()
        self._renderer = PromptRenderer(self._config)
        self._caller: WriterModelCaller = caller or AnthropicModelCaller(self._config)

    def write(
        self,
        built_context: AssembledContext,
        story_id: UUID,
        node_id: UUID,
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

        Returns:
            WriterResult with the persisted turn_id, assistant_output, model
            identifier, latency, and token/cache metrics.

        Raises:
            WriterPassError: if built_context was assembled for a different
                story_id, if node_id does not belong to story_id, the provider
                call fails, the response is malformed, or the parsed output is
                empty after trimming.  No Turn is persisted in any error case.
        """
        if not node_belongs_to_story(self._session, node_id, story_id):
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

        payload = self._renderer.render(built_context)

        try:
            response, latency_ms = timed_call(self._caller, payload)
        except Exception as exc:
            raise WriterPassError(f"Writer provider call failed: {exc}") from exc

        try:
            prose = self._parse_response(response)
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
        create_turn(self._session, turn)
        self._session.commit()

        usage = response.usage
        return WriterResult(
            turn_id=turn.turn_id,
            assistant_output=prose,
            model_identifier=f"anthropic:{response.model}",
            latency_ms=latency_ms,
            input_token_count=usage.input_tokens or None,
            output_token_count=usage.output_tokens or None,
            cache_read_token_count=usage.cache_read_input_tokens,
            cache_creation_token_count=usage.cache_creation_input_tokens,
        )

    # ---------------------------------------------------------------------------
    # Response parsing
    # ---------------------------------------------------------------------------

    def _parse_response(self, response: object) -> str:
        """Parse the Anthropic Messages response and return trimmed prose.

        Parsing rules (explicit, no silent fallback):
          1. Iterate the content array in order.
          2. Concatenate the text field of every block whose type == "text".
          3. Trim leading and trailing whitespace.
          4. If the result is empty, raise WriterPassError.
          5. If the envelope is malformed (missing required fields), raise
             WriterPassError with the underlying AttributeError preserved.

        Args:
            response: The raw response from the model caller.

        Returns:
            Trimmed prose string (non-empty).

        Raises:
            WriterPassError: on empty output or malformed response envelope.
        """
        from anthropic.types import Message, TextBlock

        if not isinstance(response, Message):
            raise WriterPassError(
                f"Unexpected response type from provider: {type(response).__name__}"
            )

        parts: list[str] = []
        for block in response.content:
            if isinstance(block, TextBlock):
                parts.append(block.text)

        prose = "".join(parts).strip()
        if not prose:
            raise WriterPassError(
                "Writer produced empty output after trimming whitespace. "
                "No Turn persisted."
            )
        return prose
