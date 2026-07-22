"""RPG Adjudication pass service — CRD Issue 15. Revised by CRD Issue 15b.

Responsibilities:
  1. Render AssembledContext + character state into a ProviderCallRequest.
  2. Call the LLM via forced tool use → AdjudicationProposalOutput.
  3. Enforce multi-roll bound (ADJUDICATION_MAX_ROLLS_PER_TURN).
  4. For each HIDDEN proposal (and SHOWN in AI_ROLLS mode): resolve via
     D20RulesSystemAdapter + DiceService → ResolvedAdjudicationRecord.
  5. For the first visible (SHOWN→PLAYER or PLAYER) proposal in PLAYER_ROLLS
     mode: return it as ``player_proposal`` for the orchestrator to hand to
     ``ActionResolutionService.start_sequence`` inside its own transaction —
     this service no longer builds pending-roll state itself (CRD Issue 15b;
     sequence identity/persistence is ``ActionResolutionService``'s job, not
     the adjudication pass service's). Overflow visible proposals are
     deferred (not AI-resolved, not a second pending roll).
  6. Return AdjudicationPassResult with resolved records + writer views +
     optional player_proposal.

Per 15b-25, the retired total-only consume path (pending_roll_request +
player_reported_total kwargs, ``_consume()``) no longer exists here —
consuming a player roll result is exclusively
``ActionResolutionService.consume_roll``, reached through
``orchestrate_rpg_resume``, not this service.

Architectural invariants enforced here:
  - Roll-authorship is structural: schema forbids result/DC/modifier fields on
    proposals; the adapter holds all resolution logic.
  - gm_cheating=off is honoured at record creation time in the adapter; this
    service never overrides it.
  - Multi-roll bound: proposals beyond ADJUDICATION_MAX_ROLLS_PER_TURN are
    dropped (fail-safe, not fail-closed — partial adjudication is better than
    a hard failure on narrative turns with many simultaneous checks).
  - Fail-closed for LLM/parse failures: AdjudicationPassError on any provider,
    parsing, or schema validation failure.  No silent fallback.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import (
    AdjudicationProposalOutput,
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
# Dice-handling enforcement
# ---------------------------------------------------------------------------


def _effective_visibility(
    proposal_vis: RollVisibility,
    dice_handling: DiceHandling,
    has_pending: bool,
) -> RollVisibility:
    """Return the code-enforced visibility for a proposal.

    Model-emitted visibility is advisory; dice_handling mode is authoritative.
    AI_ROLLS: PLAYER proposals are coerced to SHOWN (AI resolves all rolls).
    PLAYER_ROLLS: all visible proposals (SHOWN or PLAYER) become PLAYER.
      The caller's has_pending guard drops overflow visible proposals without
      calling DiceService.  Returning PLAYER for overflow means "deferred",
      not "create a second pending roll".  HIDDEN stays HIDDEN.
    """
    if dice_handling is DiceHandling.AI_ROLLS:
        return (
            RollVisibility.SHOWN
            if proposal_vis is RollVisibility.PLAYER
            else proposal_vis
        )
    # PLAYER_ROLLS: hidden is always code-resolved; all visible proposals → PLAYER.
    # When has_pending=True the loop guard drops the overflow (no DiceService call).
    if proposal_vis is RollVisibility.HIDDEN:
        return RollVisibility.HIDDEN
    return RollVisibility.PLAYER


# ---------------------------------------------------------------------------
# RpgAdjudicationPassService
# ---------------------------------------------------------------------------


class RpgAdjudicationPassService:
    """RPG Adjudication pass service.

    LLM → proposals → adapter resolution (AI/hidden) or raw proposal handoff
    (player) → AdjudicationPassResult. CRD Issue 15b: the retired consume
    path (no LLM; ``adapter.consume_player_roll()``) no longer exists here —
    see ``ActionResolutionService.consume_roll``.

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

    def is_adjudicable(self, sheet: Dnd5eCharacterSheet) -> bool:
        """Delegate to adapter — True if the sheet has enough data to adjudicate."""
        return self._adapter.is_adjudicable(sheet)

    def adjudicate(
        self,
        built_context: AssembledContext,
        session_state: RpgSessionState,
        sheet: Dnd5eCharacterSheet,
        dice_service: DiceService,
        *,
        provider: ProviderAdapter,
        overrides: list[RuleOverride] | None = None,
    ) -> AdjudicationPassResult:
        """Execute one adjudication pass and return a typed result.

        CRD Issue 15b: no longer takes ``story_id``/``originating_turn_id`` —
        this service returns a raw ``player_proposal`` for PLAYER rolls; the
        orchestrator (which already has both IDs) is the one that calls
        ``ActionResolutionService.start_sequence`` with them, inside its own
        transaction.

        Args:
            built_context: AssembledContext from the Context Builder.  The
                rules_package_slice on its stable_prefix is the active rule slice.
            session_state: Current RpgSessionState (provides gm_cheating flag).
            sheet: Active Dnd5eCharacterSheet for modifier assembly.
            dice_service: Injected DiceService for roll randomness.
            provider: ProviderAdapter for the LLM call.
            overrides: Active RuleOverrides for the session.  Defaults to [].

        Returns:
            AdjudicationPassResult with resolved records, writer views, and
            optional player_proposal.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER.
            AdjudicationPassError: LLM call failure, missing tool block, schema
                validation failure, or adapter error.
        """
        _overrides: list[RuleOverride] = overrides or []
        rule_slice: ActiveRuleSlice | None = (
            built_context.stable_prefix.rules_package_slice
        )
        return self._normal(
            built_context,
            session_state,
            sheet,
            dice_service,
            provider=provider,
            overrides=_overrides,
            rule_slice=rule_slice,
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
        player_proposal: RollProposal | None = None

        for proposal in proposals:
            effective_vis = _effective_visibility(
                proposal.visibility,
                session_state.dice_handling,
                player_proposal is not None,
            )
            coerced = (
                proposal.model_copy(update={"visibility": effective_vis})
                if effective_vis is not proposal.visibility
                else proposal
            )

            if effective_vis is RollVisibility.PLAYER:
                if player_proposal is not None:
                    # Overflow visible proposal deferred — not AI-resolved, not
                    # a second pending. CRD Issue 15b: the orchestrator builds
                    # the structured instruction and announce view via
                    # ActionResolutionService.start_sequence, not this service.
                    continue
                player_proposal = coerced
                views.append(
                    WriterAdjudicationView(
                        check_label=coerced.check_label,
                        visibility=RollVisibility.PLAYER,
                        player_facing_summary=(f"Roll needed: {coerced.check_label}"),
                        total=None,
                        dc=None,
                        outcome=None,
                    )
                )
            else:
                try:
                    record = self._adapter.resolve_roll(
                        coerced,
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
            player_proposal=player_proposal,
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
