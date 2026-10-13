"""RPG Adjudication pass service — CRD Issues 15 and 15c.

Responsibilities:
  1. Normal path (no pending roll being consumed):
       a. Render AssembledContext (the turn's one stable prefix) into a
          ProviderCallRequest.
       b. Call the LLM via forced tool use → AdjudicationProposalOutput. The
          GameMaster's judgement is advisory: it names roster operations and
          code-admitted identities, never numbers.
       c. Refuse (typed, before anything else) proposals beyond
          ADJUDICATION_MAX_ROLLS_PER_TURN and any proposal the story's dice
          handling would hand to the player (CRD Issue 15b/19b's), so no
          pending request is ever created here.
       d. Validate and certify every proposal before any die is rolled.
       e. Resolve each through D20RulesSystemAdapter + DiceService as a
          backend shown/hidden roll → ResolvedAdjudicationRecord.
       f. Return AdjudicationPassResult with resolved records + writer views.

  2. Consume path (pending_roll_request + player_reported_total provided):
       Legacy CRD Issue 15 path, retired by CRD Issue 15b (ADR-015b Group 9).
       Unreachable from production: no pending-roll service is wired.

Architectural invariants enforced here:
  - Roll-authorship is structural: schema forbids result/DC/modifier fields on
    proposals; the adapter holds all resolution logic.
  - gm_cheating=off is honoured at record creation time in the adapter; this
    service never overrides it.
  - Refusals are typed (``AdjudicationRefusal``) and visible; a mechanic is
    never dropped into narration.
  - Fail-closed for LLM/parse failures: AdjudicationPassError on any provider,
    parsing, or schema validation failure.  No silent fallback.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import (
    AdjudicationProposalOutput,
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    SubjectRef,
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
from afterworlds.pipeline.rpg.adapter import PlayerRollValueError
from afterworlds.pipeline.rpg.caller import (
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC,
)
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
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
    from afterworlds.models.rules_package import ActiveRuleSlice
    from afterworlds.models.session import RpgSessionState
    from afterworlds.pipeline.provider._protocol import ProviderAdapter
    from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.services.dnd5e_state.turn import TurnCharacter, TurnSubject

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
        subject_loader: Callable[[UUID, SubjectRef], TurnSubject] | None = None,
    ) -> None:
        self._adapter = adapter
        self._config = config or AdjudicationConfig.from_env()
        #: Reads a character or creature of a story, refusing one of another
        #: story or under a non-current binding (CRD Issue 15c).
        self._subject_loader = subject_loader
        self._system_prompt: str = load_adjudication_prompt()

    def is_adjudicable(self, character: TurnCharacter) -> bool:
        """Delegate to adapter — True if the recorded state is ready."""
        return self._adapter.is_adjudicable(character)

    def adjudicate(
        self,
        built_context: AssembledContext,
        session_state: RpgSessionState,
        sheet: TurnCharacter,
        dice_service: DiceService,
        *,
        provider: ProviderAdapter,
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
            sheet: The active character (typed 2b state) for modifier assembly.
            dice_service: Injected DiceService for roll randomness.
            provider: ProviderAdapter for the LLM call (normal path only).
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
        rule_slice: ActiveRuleSlice | None = (
            built_context.stable_prefix.rules_package_slice
        )

        # -- Consume path --------------------------------------------------------
        if pending_roll is not None and player_reported_total is not None:
            return self._consume(
                pending_roll,
                player_reported_total,
                rule_slice,
                session_state,
            )

        # -- Normal path ---------------------------------------------------------
        return self._normal(
            built_context,
            session_state,
            sheet,
            dice_service,
            provider=provider,
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
        session_state: RpgSessionState,
    ) -> AdjudicationPassResult:
        """Resolve a player-reported roll against the stored PendingRollRequest.

        No LLM call.  Token counts are None (code-only path).
        """
        try:
            record = self._adapter.consume_player_roll(
                pending,
                reported_total,
                rule_slice,
                session_state.gm_cheating,
            )
        except PlayerRollValueError as exc:
            raise AdjudicationPassError(
                f"Player-reported roll rejected: {exc}"
            ) from exc
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
        sheet: TurnCharacter,
        dice_service: DiceService,
        *,
        provider: ProviderAdapter,
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

        # CRD Issue 15c: proposals beyond the per-turn bound are refused, never
        # dropped -- a dropped proposal would let a mechanic pass to narration.
        if len(output.rolls) > ADJUDICATION_MAX_ROLLS_PER_TURN:
            raise AdjudicationRefusal(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{len(output.rolls)} roll proposals exceed the per-turn bound of "
                f"{ADJUDICATION_MAX_ROLLS_PER_TURN}",
            )
        proposals = [
            p.model_copy(
                update={
                    "visibility": _effective_visibility(
                        p.visibility, session_state.dice_handling, False
                    )
                }
            )
            for p in output.rolls
        ]

        # CRD Issue 15c: player-rolled dice are CRD Issue 15b/19b's. Refuse
        # before any proposal is checked, rolled or announced, so no pending
        # request can exist.
        if any(p.visibility is RollVisibility.PLAYER for p in proposals):
            raise AdjudicationRefusal(
                RefusalKind.PLAYER_ROLL_UNSUPPORTED,
                "this story's dice handling asks the player to roll; player-"
                "rolled dice are CRD Issue 15b/19b's and are not resolved here",
            )

        subjects = self._load_subjects(story_id, sheet, proposals)

        # CRD Issue 2b: check every proposal before any has an effect, so a
        # later unsupported check cannot follow an earlier roll.
        for proposal in proposals:
            try:
                self._adapter.require_supported(proposal, sheet, subjects)
            except AdjudicationRefusal:
                raise
            except Exception as exc:
                raise AdjudicationPassError(
                    f"Unsupported proposal {proposal.check_label!r}: {exc}"
                ) from exc

        records: list[ResolvedAdjudicationRecord] = []
        views: list[WriterAdjudicationView] = []
        for proposal in proposals:
            try:
                record = self._adapter.resolve_roll(
                    proposal,
                    sheet,
                    rule_slice,
                    dice_service,
                    session_state.gm_cheating,
                    subjects,
                )
            except AdjudicationRefusal:
                raise
            except Exception as exc:
                raise AdjudicationPassError(
                    f"Adapter failed to resolve proposal "
                    f"{proposal.check_label!r}: {exc}"
                ) from exc
            records.append(record)
            views.append(self._adapter.to_writer_view(record))

        return AdjudicationPassResult(
            proposals=tuple(records),
            writer_views=tuple(views),
            pending_roll_request=None,
            subjects=tuple(subjects.values()),
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )

    def _load_subjects(
        self,
        story_id: UUID,
        sheet: TurnCharacter,
        proposals: list[RollProposal],
    ) -> dict[tuple[str, str], TurnSubject]:
        """Every subject the proposals name besides the acting character, each
        read once with its own binding and revision (CRD Issue 15c)."""
        refs: dict[tuple[str, str], SubjectRef] = {}
        for proposal in proposals:
            if proposal.weapon_attack is not None:
                ref = proposal.weapon_attack.target
                refs[(ref.kind, str(ref.subject_id))] = ref
        refs.pop(("character", str(sheet.sheet_id)), None)
        if not refs:
            return {}
        if self._subject_loader is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_STATE,
                "no subject reader is wired, so a target cannot be read",
            )
        subjects: dict[tuple[str, str], TurnSubject] = {}
        for key, ref in refs.items():
            try:
                subjects[key] = self._subject_loader(story_id, ref)
            except AdjudicationRefusal:
                raise
            except Exception as exc:  # noqa: BLE001
                raise AdjudicationRefusal(
                    RefusalKind.MISSING_STATE,
                    f"{ref.kind} {ref.subject_id} could not be read for this "
                    f"story: {exc}",
                ) from exc
        return subjects

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
