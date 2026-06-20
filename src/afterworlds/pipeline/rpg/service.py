"""RPG Adjudication pass service — CRD Issue 15.

Responsibilities:
  1. Normal path (no pending roll being consumed):
       a. Render AssembledContext + character state into a ProviderCallRequest.
       b. Call the LLM via forced tool use → AdjudicationProposalOutput.
       c. Enforce multi-roll bound (ADJUDICATION_MAX_ROLLS_PER_TURN).
       d. For each SHOWN/HIDDEN proposal: resolve via D20RulesSystemAdapter +
          DiceService → ResolvedAdjudicationRecord.
       e. For each PLAYER proposal: prepare announce via adapter →
          PendingRollRequest + announce WriterAdjudicationView.  Only the
          first PLAYER proposal is accepted per turn; extras are dropped.
       f. Return AdjudicationPassResult with resolved records + writer views
          + optional pending_roll_request.

  2. Consume path (pending_roll_request + player_reported_total provided):
       No LLM call.  Delegate to adapter.consume_player_roll(); return
       AdjudicationPassResult with the single resolved record and no token
       counts (consume path is code-only).

Architectural invariants enforced here:
  - Roll-authorship is structural: schema forbids result/DC/modifier fields on
    proposals; the adapter holds all resolution logic.
  - gm_cheating=off is honoured at record creation time in the adapter; this
    service never overrides it.
  - PLAYER proposals on the normal path produce a PendingRollRequest — no
    DiceService call.
  - Multi-roll bound: proposals beyond ADJUDICATION_MAX_ROLLS_PER_TURN are
    dropped (fail-safe, not fail-closed — partial adjudication is better than
    a hard failure on narrative turns with many simultaneous checks).
  - Fail-closed for LLM/parse failures: AdjudicationPassError on any provider,
    parsing, or schema validation failure.  No silent fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import RollVisibility
from afterworlds.models.rpg import (
    AdjudicationProposalOutput,
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    WriterAdjudicationView,
)
from afterworlds.pipeline._refusal import ProviderRefusalError
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
from afterworlds.pipeline.rpg.caller import (
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC,
)
from afterworlds.pipeline.rpg.config import (
    ADJUDICATION_MAX_ROLLS_PER_TURN,
    ADJUDICATION_MAX_TOKENS,
    AdjudicationConfig,
)
from afterworlds.pipeline.rpg.models import (
    AdjudicationPassError,
    AdjudicationPassResult,
)

if TYPE_CHECKING:
    from afterworlds.models.character_sheet import Dnd5eCharacterSheet
    from afterworlds.models.rules_package import ActiveRuleSlice, RuleOverride
    from afterworlds.models.session import RpgSessionState
    from afterworlds.pipeline.provider._protocol import ProviderAdapter
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.dice import DiceService

# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


class UnknownPromptError(ValueError):
    """Raised when the adjudication prompt file is missing."""


def load_adjudication_prompt() -> str:
    """Load the RPG Adjudication pass system prompt from docs/prompts/."""
    prompt_path = _PROMPT_DIR / "rpg_adjudication.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UnknownPromptError(
            f"Adjudication prompt file not found at {prompt_path}"
        ) from exc


# ---------------------------------------------------------------------------
# Module-level tool definition (built once)
# ---------------------------------------------------------------------------

_ADJUDICATION_TOOL_DEF = ProviderToolDefinition(
    name=PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
    description=PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC["description"],
    input_schema=PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC["input_schema"],
)


# ---------------------------------------------------------------------------
# RpgAdjudicationPassService
# ---------------------------------------------------------------------------


class RpgAdjudicationPassService:
    """RPG Adjudication pass service.

    Normal path: LLM → proposals → adapter resolution → AdjudicationPassResult.
    Consume path: no LLM; adapter.consume_player_roll() → single resolved record.

    Args:
        adapter: D20RulesSystemAdapter instance.
        config: Adjudication config.  Defaults to AdjudicationConfig.from_env().
    """

    def __init__(
        self,
        adapter: D20RulesSystemAdapter,
        config: AdjudicationConfig | None = None,
    ) -> None:
        self._adapter = adapter
        self._config = config or AdjudicationConfig.from_env()
        self._system_prompt: str = load_adjudication_prompt()

    def adjudicate(
        self,
        built_context: AssembledContext,
        session_state: RpgSessionState,
        sheet: Dnd5eCharacterSheet,
        dice_service: DiceService,
        *,
        provider: ProviderAdapter,
        overrides: list[RuleOverride] | None = None,
        story_id: UUID,
        originating_turn_id: UUID,
        pending_roll: PendingRollRequest | None = None,
        player_reported_total: int | None = None,
    ) -> AdjudicationPassResult:
        """Execute one adjudication pass and return a typed result.

        Args:
            built_context: AssembledContext from the Context Builder.  The
                rules_package_slice on its stable_prefix is the active rule slice.
            session_state: Current RpgSessionState (provides gm_cheating flag).
            sheet: Active Dnd5eCharacterSheet for modifier assembly.
            dice_service: Injected DiceService for roll randomness.
            provider: ProviderAdapter for the LLM call (normal path only).
            overrides: Active RuleOverrides for the session.  Defaults to [].
            story_id: Story UUID, forwarded to PendingRollRequest.
            originating_turn_id: Turn UUID for audit and PendingRollRequest.
            pending_roll: Non-None on the consume path — the PendingRollRequest
                being consumed this turn.
            player_reported_total: Non-None on the consume path — the integer
                total the player reported.

        Returns:
            AdjudicationPassResult with resolved records, writer views, and
            optional pending_roll_request.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER.
            AdjudicationPassError: LLM call failure, missing tool block, schema
                validation failure, or adapter error on normal path.
        """
        _overrides: list[RuleOverride] = overrides or []
        rule_slice: ActiveRuleSlice | None = (
            built_context.stable_prefix.rules_package_slice
        )

        # -- Consume path --------------------------------------------------------
        if pending_roll is not None and player_reported_total is not None:
            return self._consume(
                pending_roll,
                player_reported_total,
                rule_slice,
                _overrides,
                session_state,
            )

        # -- Normal path ---------------------------------------------------------
        return self._normal(
            built_context,
            session_state,
            sheet,
            dice_service,
            provider=provider,
            overrides=_overrides,
            rule_slice=rule_slice,
            story_id=story_id,
            originating_turn_id=originating_turn_id,
        )

    # -----------------------------------------------------------------------
    # Consume path
    # -----------------------------------------------------------------------

    def _consume(
        self,
        pending: PendingRollRequest,
        reported_total: int,
        rule_slice: ActiveRuleSlice | None,
        overrides: list[RuleOverride],
        session_state: RpgSessionState,
    ) -> AdjudicationPassResult:
        """Resolve a player-reported roll against the stored PendingRollRequest.

        No LLM call.  Token counts are None (code-only path).
        """
        record = self._adapter.consume_player_roll(
            pending,
            reported_total,
            rule_slice,
            overrides,
            session_state.gm_cheating,
        )
        writer_view = self._adapter.to_writer_view(record)
        return AdjudicationPassResult(
            proposals=(record,),
            writer_views=(writer_view,),
            pending_roll_request=None,
        )

    # -----------------------------------------------------------------------
    # Normal path
    # -----------------------------------------------------------------------

    def _normal(
        self,
        built_context: AssembledContext,
        session_state: RpgSessionState,
        sheet: Dnd5eCharacterSheet,
        dice_service: DiceService,
        *,
        provider: ProviderAdapter,
        overrides: list[RuleOverride],
        rule_slice: ActiveRuleSlice | None,
        story_id: UUID,
        originating_turn_id: UUID,
    ) -> AdjudicationPassResult:
        request = self._render(built_context)

        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise AdjudicationPassError(
                f"Adjudication provider call failed: {exc}"
            ) from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise AdjudicationPassError("Adjudication response missing tool-use block")
        if tool_parts[0].tool_name != PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME:
            raise AdjudicationPassError(
                f"Adjudication unexpected tool name: {tool_parts[0].tool_name!r}; "
                f"expected {PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME!r}"
            )

        try:
            output = AdjudicationProposalOutput.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise AdjudicationPassError(
                f"Adjudication tool input failed schema validation: {exc}"
            ) from exc

        # Enforce multi-roll bound
        proposals: list[RollProposal] = output.rolls[:ADJUDICATION_MAX_ROLLS_PER_TURN]

        records: list[ResolvedAdjudicationRecord] = []
        views: list[WriterAdjudicationView] = []
        pending_roll_request: PendingRollRequest | None = None

        for proposal in proposals:
            if proposal.visibility is RollVisibility.PLAYER:
                if pending_roll_request is not None:
                    # Only one PLAYER roll announce per turn.
                    continue
                pending, view = self._adapter.prepare_player_roll_announce(
                    proposal,
                    sheet,
                    rule_slice,
                    overrides,
                    story_id=story_id,
                    session_id=session_state.session_id,
                    originating_turn_id=originating_turn_id,
                )
                pending_roll_request = pending
                views.append(view)
            else:
                try:
                    record = self._adapter.resolve_roll(
                        proposal,
                        sheet,
                        rule_slice,
                        overrides,
                        dice_service,
                        session_state.gm_cheating,
                    )
                except Exception as exc:
                    raise AdjudicationPassError(
                        f"Adapter failed to resolve proposal "
                        f"{proposal.check_label!r}: {exc}"
                    ) from exc
                view = self._adapter.to_writer_view(record)
                records.append(record)
                views.append(view)

        return AdjudicationPassResult(
            proposals=tuple(records),
            writer_views=tuple(views),
            pending_roll_request=pending_roll_request,
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )

    # -----------------------------------------------------------------------
    # Prompt rendering
    # -----------------------------------------------------------------------

    def _render(self, built_context: AssembledContext) -> ProviderCallRequest:
        """Render AssembledContext into a ProviderCallRequest.

        Stable-prefix blocks are shared with the Planner/Writer for cache reuse.
        System blocks: adjudication pass contract + active mode contract.
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

        return ProviderCallRequest(
            pass_id=PipelinePassId.RPG_ADJUDICATION,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=built_context.stable_prefix.system_prompt),
            ],
            rendered_blocks=rendered_blocks,
            max_output_tokens=ADJUDICATION_MAX_TOKENS,
            tool_definitions=[_ADJUDICATION_TOOL_DEF],
            forced_tool_name=PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
        )
