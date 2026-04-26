"""Extractor service — CRD Issue 10.

Extractor pass: receives AssembledContext + writer_output, calls the LLM using
Anthropic tool use to extract structured narrative proposals, stages every
proposal through StoryBibleService, auto-commits soft facts, transient states,
events, and unresolved threads, and stages locked-fact proposals as PENDING for
Sojourner confirmation.

Architectural invariants enforced here:
  - The Extractor NEVER writes to the Story Bible without first calling
    StoryBibleService.stage_proposed_update().  Every canon write is preceded
    by a staged proposal; ratification and application happen after staging.
  - Locked-fact proposals remain PENDING; they are never ratified without
    explicit Sojourner confirmation (confirmed=True).
  - Soft facts, transient states, unresolved threads, and events are auto-
    ratified immediately after staging.
  - Soft-fact and transient-state proposals that resolve to a known cast
    entry are applied to the live dynamic field via StoryBibleService.
    Unresolvable proposals remain RATIFIED but unapplied (logged, not raised).
  - The Extractor does not create Nodes or Turns; it does not call
    IntentClassifierService, RollingSummaryService, or RulesPackageService.
  - All writes are routed through StoryBibleService; no direct ORM access.
  - ExtractorResult is a typed Pydantic model.  ExtractorPassError is a
    typed exception.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
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
from afterworlds.models.enums import EventSignificance, ProposalType
from afterworlds.models.story_bible import ProvisionalProposal
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
      4. Stage all proposals via StoryBibleService.stage_proposed_update().
      5. Auto-ratify soft facts, transient states, unresolved threads, and events.
      6. Apply soft-fact and transient-state updates to live cast fields where
         the character name resolves to a known cast entry.
      7. Leave locked-fact proposals as PENDING for Sojourner confirmation.
      8. Return a typed ExtractorResult.

    Args:
        session: SQLAlchemy session (used indirectly via StoryBibleService).
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
        story_id: UUID,
        writer_output: str,
        source_turn_id: str | None = None,
    ) -> ExtractorResult:
        """Execute one Extractor pass and return a typed result.

        Args:
            built_context: AssembledContext produced by the Context Builder.
                The Extractor reuses the same stable prefix as the Writer so
                the Anthropic cache breakpoint is in the same position.
            story_id: UUID of the story this turn belongs to.
            writer_output: The prose produced by the Writer pass this turn.
            source_turn_id: Optional string UUID of the persisted Turn, used as
                provenance on all proposals created this pass.

        Returns:
            ExtractorResult with all staged proposals, token metrics, and a
            pass_forward_content summary for downstream pipeline passes.

        Raises:
            ExtractorPassError: if the provider call fails, the response
                contains no tool-use block, or the tool input is malformed.
        """
        payload = self._render(built_context, writer_output)

        try:
            response, latency_ms = timed_call(self._caller, payload)
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

        cast_name_map = _build_cast_name_map(built_context)

        all_proposals: list[ProvisionalProposal] = []
        pending: list[ProvisionalProposal] = []
        auto_committed: list[ProvisionalProposal] = []

        # ── Locked facts — stage only, leave PENDING ──────────────────────
        for item in _iter_list(tool_input, "locked_facts"):
            fact_text = str(item.get("fact_text", "")).strip()
            if not fact_text:
                continue
            proposal = ProvisionalProposal(
                story_id=story_id,
                proposal_type=ProposalType.LOCKED_FACT,
                proposed_value={"fact_text": fact_text},
                source_turn_id=source_turn_id,
                created_at=datetime.now(UTC),
            )
            staged = self._sbs.stage_proposed_update(story_id, proposal)
            all_proposals.append(staged)
            pending.append(staged)

        # ── Soft facts — stage + ratify + apply ───────────────────────────
        for item in _iter_list(tool_input, "soft_facts"):
            staged_ratified = self._stage_and_ratify_cast_update(
                story_id,
                item,
                ProposalType.SOFT_FACT,
                cast_name_map,
                source_turn_id,
            )
            if staged_ratified is not None:
                all_proposals.append(staged_ratified)
                auto_committed.append(staged_ratified)

        # ── Transient states — stage + ratify + apply ─────────────────────
        for item in _iter_list(tool_input, "transient_states"):
            staged_ratified = self._stage_and_ratify_cast_update(
                story_id,
                item,
                ProposalType.TRANSIENT_STATE,
                cast_name_map,
                source_turn_id,
            )
            if staged_ratified is not None:
                all_proposals.append(staged_ratified)
                auto_committed.append(staged_ratified)

        # ── Unresolved threads — stage + ratify (creates thread row) ──────
        for item in _iter_list(tool_input, "unresolved_threads"):
            description = str(item.get("description", "")).strip()
            if not description:
                continue
            proposal = ProvisionalProposal(
                story_id=story_id,
                proposal_type=ProposalType.UNRESOLVED_THREAD,
                proposed_value={"description": description},
                source_turn_id=source_turn_id,
                created_at=datetime.now(UTC),
            )
            staged = self._sbs.stage_proposed_update(story_id, proposal)
            ratified = self._sbs.ratify_update(staged.proposal_id)
            all_proposals.append(ratified)
            auto_committed.append(ratified)

        # ── Events — stage + ratify (creates event row) ───────────────────
        for item in _iter_list(tool_input, "events"):
            description = str(item.get("description", "")).strip()
            significance_raw = str(
                item.get("significance", EventSignificance.ROUTINE.value)
            ).strip()
            if not description:
                continue
            # Coerce unknown significance values to ROUTINE rather than failing.
            try:
                EventSignificance(significance_raw)
            except ValueError:
                significance_raw = EventSignificance.ROUTINE.value
            proposal = ProvisionalProposal(
                story_id=story_id,
                proposal_type=ProposalType.EVENT,
                proposed_value={
                    "description": description,
                    "significance": significance_raw,
                },
                source_turn_id=source_turn_id,
                created_at=datetime.now(UTC),
            )
            staged = self._sbs.stage_proposed_update(story_id, proposal)
            ratified = self._sbs.ratify_update(staged.proposal_id)
            all_proposals.append(ratified)
            auto_committed.append(ratified)

        self._session.commit()

        pass_forward = _render_pass_forward(pending, auto_committed)

        usage = response.usage
        return ExtractorResult(
            proposals=all_proposals,
            pending_proposals=pending,
            auto_committed=auto_committed,
            pass_forward_content=pass_forward,
            model_identifier=f"anthropic:{response.model}",
            latency_ms=latency_ms,
            input_token_count=usage.input_tokens,
            output_token_count=usage.output_tokens,
            cache_read_token_count=usage.cache_read_input_tokens,
            cache_creation_token_count=usage.cache_creation_input_tokens,
        )

    # -----------------------------------------------------------------------
    # Private: staging helpers
    # -----------------------------------------------------------------------

    def _stage_and_ratify_cast_update(
        self,
        story_id: UUID,
        item: dict[str, Any],
        proposal_type: ProposalType,
        cast_name_map: dict[str, UUID],
        source_turn_id: str | None,
    ) -> ProvisionalProposal | None:
        """Stage a cast-field update proposal, ratify it, and apply the change.

        Returns the ratified ProvisionalProposal, or None if the item was empty
        or had no fact_text / description.  Never raises; unresolvable proposals
        are staged and ratified without applying the field update.
        """
        char_name = str(item.get("character_name", "")).strip()
        field_name = str(item.get("field_name", "")).strip()
        new_value: Any = item.get("new_value")
        if not char_name or not field_name:
            return None

        cast_id = cast_name_map.get(char_name.lower())
        proposed_value: dict[str, Any] = {
            "entity_type": "cast_entry",
            "character_name": char_name,
            "entity_id": str(cast_id) if cast_id is not None else None,
            "field_name": field_name,
            "new_value": new_value,
        }
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=proposal_type,
            target_entity_type="cast_entry",
            target_entity_id=str(cast_id) if cast_id is not None else None,
            proposed_value=proposed_value,
            source_turn_id=source_turn_id,
            created_at=datetime.now(UTC),
        )
        staged = self._sbs.stage_proposed_update(story_id, proposal)
        ratified = self._sbs.ratify_update(staged.proposal_id)

        # Apply the field update to live canon if the entity is resolvable.
        if cast_id is not None:
            with contextlib.suppress(ValueError, EntityNotFoundError):
                self._sbs.update_dynamic_field(
                    story_id,
                    cast_id,
                    field_name,
                    new_value,
                    source_turn_id=source_turn_id,
                )

        return ratified

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
                text=vs.current_input,
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


def _build_cast_name_map(built_context: AssembledContext) -> dict[str, UUID]:
    """Build a lowercase-name → cast_id map from the assembled context.

    Case-insensitive so the LLM's name capitalisation doesn't prevent matching.
    """
    return {
        entry.name.lower(): entry.cast_id
        for entry in built_context.stable_prefix.story_bible_context.cast
    }


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


def _iter_list(tool_input: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Safely extract a list of dicts from the tool input under ``key``."""
    raw = tool_input.get(key, [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _render_pass_forward(
    pending: list[ProvisionalProposal],
    auto_committed: list[ProvisionalProposal],
) -> str:
    """Render the Extractor's pass-forward summary for downstream passes."""
    lines: list[str] = ["[EXTRACTOR SUMMARY]"]

    if pending:
        lines.append(f"Locked-fact proposals pending confirmation: {len(pending)}")
        for p in pending:
            fact = p.proposed_value.get("fact_text", "<unknown>")
            lines.append(f"  - {fact}")

    if auto_committed:
        lines.append(f"Auto-committed proposals: {len(auto_committed)}")
        for p in auto_committed:
            lines.append(f"  - [{p.proposal_type.value}] {_proposal_summary(p)}")

    if not pending and not auto_committed:
        lines.append("No narrative updates extracted this turn.")

    return "\n".join(lines)


def _proposal_summary(proposal: ProvisionalProposal) -> str:
    """Return a one-line summary of a proposal for pass-forward output."""
    pv = proposal.proposed_value
    ptype = proposal.proposal_type

    if ptype == ProposalType.UNRESOLVED_THREAD:
        return str(pv.get("description", "<no description>"))
    if ptype == ProposalType.EVENT:
        sig = str(pv.get("significance", "?"))
        return f"{pv.get('description', '<no description>')} [{sig}]"
    if ptype in (ProposalType.SOFT_FACT, ProposalType.TRANSIENT_STATE):
        char = str(pv.get("character_name", "?"))
        field = str(pv.get("field_name", "?"))
        val = pv.get("new_value", "?")
        return f"{char}.{field} = {val!r}"
    return str(pv)
