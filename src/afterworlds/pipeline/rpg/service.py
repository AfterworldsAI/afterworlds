"""RPG Adjudication pass service — CRD Issues 15, 15c and 15b.

Responsibilities:
  a. Render AssembledContext (the turn's one stable prefix) into a
     ProviderCallRequest.
  b. Call the LLM via forced tool use → AdjudicationProposalOutput. The
     GameMaster's judgement is advisory: it names roster operations and
     code-admitted identities, never numbers.
  c. Refuse (typed, before anything else) proposals beyond
     ADJUDICATION_MAX_ROLLS_PER_TURN.
  d. Validate and certify every proposal before any die is rolled
     (:meth:`RpgAdjudicationPassService.prepare_turn`).
  e. Resolve each through D20RulesSystemAdapter
     (:meth:`RpgAdjudicationPassService.resolve_turn`) with the turn's
     :class:`~.steps.SequenceDice`. Who rolls each die follows the story's
     dice handling (CRD Issue 15b): a player-rolled die of the acting
     character, or a result-triggered decision, pauses the turn into an
     action-resolution sequence; otherwise every die is a backend roll.
  f. Return AdjudicationPassResult with resolved records + writer views, or
     the sequence start of a paused turn.

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

import json
from collections import Counter
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.ingestion.mechanical.representation import ConditionKind
from afterworlds.models.context import AssembledContext
from afterworlds.models.dnd5e_state import SubjectReference, TurnCoordination
from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.models.rpg import (
    AdjudicationProposalOutput,
    DiceResult,
    ResolvedAdjudicationRecord,
    RollProposal,
    SubjectRef,
    TurnUseRef,
    WeaponAttackSelection,
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
from afterworlds.pipeline.rpg import (
    bystanders,
    creature_attacks,
    creature_effects,
    economy,
)
from afterworlds.pipeline.rpg.caller import (
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
    PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC,
)
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Operation,
    RefusalKind,
)
from afterworlds.pipeline.rpg.config import (
    ADJUDICATION_MAX_ROLLS_PER_TURN,
    ADJUDICATION_MAX_TOKENS,
    AdjudicationConfig,
)
from afterworlds.pipeline.rpg.dice import DecisionRequest, RollRequest
from afterworlds.pipeline.rpg.dice import decide as dice_decide
from afterworlds.pipeline.rpg.dice import request as dice_request
from afterworlds.pipeline.rpg.models import (
    ActionResolutionError,
    AdjudicationPassError,
    AdjudicationPassResult,
    PlayerInputRequired,
    PreflightGapError,
)
from afterworlds.pipeline.rpg.steps import SequenceDice, SequenceStart
from afterworlds.services.dnd5e_state.coordination import (
    EdgeRefused,
    StoredCoordination,
    apply_edge,
    take_use,
)
from afterworlds.services.dnd5e_state.turn import (
    TurnCharacter,
    TurnCreature,
    TurnSubject,
    advanced,
    with_possible,
)

if TYPE_CHECKING:
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


_EDGE_OPERATIONS = ("begin_turn", "end_turn")


def _ledger(
    document: TurnCoordination,
    proposals: list[RollProposal],
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    openers: dict[int, tuple[SubjectReference, str]],
) -> TurnCoordination:
    """*document* after the proposals' actor-turn edges and action/once-per-
    turn uses, in order, or a typed refusal for the first that is not legal
    (contract G1; :mod:`.economy`). Checked before any die."""
    begun = False
    for index, proposal in enumerate(proposals):
        sel = proposal.weapon_attack
        if sel is not None and sel.cleave:
            _cleave_follows(proposals, index)
        creature = proposal.creature_attack
        if creature is not None and creature.follows_up:
            creature_attacks.check_follow_up(proposals, index, actor, subjects)
        document = _spend(document, proposal, actor, subjects, index, openers)
        if proposal.operation not in _EDGE_OPERATIONS or proposal.subject is None:
            continue
        kind = "begin" if proposal.operation == "begin_turn" else "end"
        subject = SubjectReference(
            kind=proposal.subject.kind, subject_id=proposal.subject.subject_id
        )
        try:
            document, _ = apply_edge(document, kind, subject, begun_this_turn=begun)
        except EdgeRefused as exc:
            raise AdjudicationRefusal(RefusalKind.INVALID_SELECTION, str(exc)) from exc
        begun = begun or kind == "begin"
    return document


def _uses(
    document: TurnCoordination,
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    index: int,
    openers: dict[int, tuple[SubjectReference, str]],
) -> list[economy.Use]:
    attack = proposal.creature_attack
    return economy.costs(
        proposal,
        actor,
        subjects,
        document,
        in_multiattack=attack is not None and attack.multiattack,
        opens_multiattack=openers[index][1] if index in openers else None,
    )


def _spend(
    document: TurnCoordination,
    proposal: RollProposal,
    actor: TurnCharacter,
    subjects: dict[tuple[str, str], TurnSubject],
    index: int,
    openers: dict[int, tuple[SubjectReference, str]],
) -> TurnCoordination:
    for use in _uses(document, proposal, actor, subjects, index, openers):
        try:
            document = take_use(document, use.by, use.key)
        except EdgeRefused as exc:
            raise AdjudicationRefusal(RefusalKind.INVALID_SELECTION, str(exc)) from exc
    return document


class _CountingDice:
    """The turn's dice, counting what one operation drew: a refusal after its
    own first die is a preflight gap, not an ordinary refusal."""

    def __init__(self, inner: DiceService) -> None:
        self._inner = inner
        self.rolled = 0

    def roll(self, expression: str) -> DiceResult:
        self.rolled += 1
        return self._inner.roll(expression)

    def roll_described(self, expression: str, request: RollRequest) -> DiceResult:
        self.rolled += 1
        return dice_request(self._inner, expression, request)

    def decide(self, request: DecisionRequest) -> str | None:
        return dice_decide(self._inner, request)


def _ammunition_supply(proposals: list[RollProposal], actor: TurnCharacter) -> None:
    """Refuse, before any die, attacks that together fire more of a held
    ammunition item than the actor holds: each attack expends one, hit or
    miss (CRD Issue 15c C7)."""
    fired = Counter(
        p.weapon_attack.ammunition_item_id
        for p in proposals
        if p.weapon_attack is not None and p.weapon_attack.ammunition_item_id
    )
    held = {i.item_id: i.quantity for i in actor.items}
    for item_id, count in fired.items():
        if count > held.get(item_id, 0):
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                f"the turn fires {count} of ammunition item {item_id}, which "
                f"holds {held.get(item_id, 0)}",
            )


def _species_once(proposals: list[RollProposal]) -> None:
    """Refuse, before any die, a turn recording a creature's species twice:
    each is checked against the state the turn read, so a second would pass
    the preflight and fail only after the first had an effect (C8)."""
    named = Counter(
        str(p.subject.subject_id)
        for p in proposals
        if p.operation == Operation.CREATURE_SPECIES.value and p.subject is not None
    )
    for subject_id, count in named.items():
        if count > 1:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                f"the turn records creature {subject_id}'s species {count} times; "
                "an individual's species is recorded once",
            )


def _cleaves(records: list[ResolvedAdjudicationRecord]) -> bool:
    """Whether the attack just resolved hit and may Cleave."""
    if not records:
        return False
    provenance = json.loads(records[-1].modifiers_json)
    return (provenance.get("mastery") or {}).get("result") == "may_cleave"


def _follows_up(records: list[ResolvedAdjudicationRecord]) -> bool:
    """Whether the creature attack just resolved hit and allows its
    follow-up attack."""
    if not records:
        return False
    provenance = json.loads(records[-1].modifiers_json)
    return (provenance.get("clauses") or {}).get("follow_up") == "may_follow_up"


def _cleave_follows(proposals: list[RollProposal], index: int) -> None:
    """Cleave's extra attack directly follows a weapon attack with the same
    weapon that selects its mastery, against another creature."""
    sel = proposals[index].weapon_attack
    before = proposals[index - 1].weapon_attack if index else None
    if (
        sel is None
        or before is None
        or before.weapon_item_id != sel.weapon_item_id
        or not before.mastery
        or before.target == sel.target
    ):
        raise AdjudicationRefusal(
            RefusalKind.INVALID_SELECTION,
            "Cleave's extra attack follows an attack with the same weapon that "
            "selects Cleave, against another creature",
        )


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
    proposal_vis: RollVisibility, dice_handling: DiceHandling
) -> RollVisibility:
    """The code-enforced visibility of a proposal; the model's is advisory.

    AI_ROLLS: a PLAYER proposal is coerced to SHOWN (the backend rolls).
    PLAYER_ROLLS: a visible proposal (SHOWN or PLAYER) becomes PLAYER, whose
    acting character's dice the Sojourner rolls (CRD Issue 15b); HIDDEN stays
    HIDDEN and is always rolled by the backend.
    """
    if dice_handling is DiceHandling.AI_ROLLS:
        return (
            RollVisibility.SHOWN
            if proposal_vis is RollVisibility.PLAYER
            else proposal_vis
        )
    if proposal_vis is RollVisibility.HIDDEN:
        return RollVisibility.HIDDEN
    return RollVisibility.PLAYER


def _decisions_offered(proposals: list[RollProposal]) -> None:
    """Refuse, before any die, what would take a result-triggered decision
    away from the Sojourner (CRD Issue 15b): knocking a target out instead of
    reducing it to 0 Hit Points is the acting character's own decision when
    its melee hit would do so, so the GameMaster never preselects it, and a
    hidden melee attack, whose decision could not be offered without
    revealing the hit, is refused."""
    for proposal in proposals:
        sel = proposal.weapon_attack
        if sel is None:
            continue
        if sel.knock_out:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                "knocking a target out is the Sojourner's decision when a hit "
                "would reduce it to 0 Hit Points; it is offered then, never "
                "preselected",
            )
        if _melee(sel) and proposal.visibility is RollVisibility.HIDDEN:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                "a hidden melee attack by the acting character could not offer its "
                "knockout decision without revealing the hit",
            )


def _melee(sel: WeaponAttackSelection) -> bool:
    """A melee attack: made within reach and not thrown (a ranged weapon is
    never within reach)."""
    return sel.range == "within_reach" and not sel.thrown


@dataclass
class PreparedTurn:
    """A turn's proposals with everything read and checked before any die
    (:meth:`RpgAdjudicationPassService.prepare_turn`)."""

    proposals: list[RollProposal]
    sheet: TurnCharacter
    subjects: dict[tuple[str, str], TurnSubject]
    coordination: StoredCoordination | None
    discovery: tuple[UUID, frozenset[tuple[str, str, int]]] | None
    openers: dict[int, tuple[SubjectReference, str]]

    def reads(self) -> dict[str, Any]:
        """What the turn's work rests on, canonically: every subject's
        revision, exact binding and holdings, the coordination and the
        discovery snapshot. An action-resolution sequence requires it
        unchanged at every advancement (CRD Issue 15b)."""

        def subject(s: TurnSubject) -> dict[str, Any]:
            return {
                "revision": s.stored.revision,
                "binding": s.stored.binding.model_dump(mode="json"),
                "items": sorted([str(i.item_id), i.revision] for i in s.items),
            }

        coordination = self.coordination
        return {
            "actor": subject(self.sheet),
            "subjects": {
                f"{kind}:{sid}": subject(s)
                for (kind, sid), s in sorted(self.subjects.items())
            },
            "coordination": (
                None
                if coordination is None
                else {
                    "revision": coordination.revision,
                    "document": coordination.document.model_dump(mode="json"),
                }
            ),
            "discovery": (
                None if self.discovery is None else sorted(self.discovery[1])
            ),
        }


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
        coordination_loader: Callable[[UUID], StoredCoordination] | None = None,
        bounded_loader: Callable[[UUID, SubjectRef], list[TurnSubject]] | None = None,
        scene_loader: Callable[[UUID, TurnCharacter], str] | None = None,
        aura_loader: Callable[[UUID], list[TurnCharacter]] | None = None,
        discovery_reader: (
            Callable[[UUID], frozenset[tuple[str, str, int]]] | None
        ) = None,
    ) -> None:
        self._adapter = adapter
        self._config = config or AdjudicationConfig.from_env()
        #: Reads a character or creature of a story, refusing one of another
        #: story or under a non-current binding (CRD Issue 15c).
        self._subject_loader = subject_loader
        self._coordination_loader = coordination_loader
        self._bounded_loader = bounded_loader
        self._scene_loader = scene_loader
        self._aura_loader = aura_loader
        #: Snapshots the story before a discovery scan (production wiring
        #: supplies it; the orchestrator rechecks it at commit).
        self._discovery_reader = discovery_reader
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
        sequences: bool = False,
    ) -> AdjudicationPassResult:
        """Execute one adjudication pass and return a typed result.

        Every operation is validated and certified before any die. The turn's
        operations then resolve in order with the turn's dice. When the
        resolution needs the Sojourner (their own die in a player-rolled
        story, or a result-triggered decision), it pauses: the result carries
        the sequence start (:class:`~.steps.SequenceStart`) instead of
        records, and nothing has an effect until the sequence is narrated
        (CRD Issue 15b). A turn needing no player input resolves as in 15c.
        ``originating_turn_id`` is recorded by the sequence when persisted.

        *sequences* says whether the caller can persist a sequence (its
        action-resolution service is wired). Without one the pass behaves as
        in CRD Issue 15c: a proposal the dice handling hands to the player is
        refused before anything is checked or rolled, and a knockout stays the
        GameMaster's selection; nothing can pend.

        Raises:
            ProviderRefusalError: propagated unchanged for REFUSED_BY_PROVIDER.
            AdjudicationPassError: LLM call failure, missing tool block, schema
                validation failure, a typed refusal, or adapter error.
        """
        # CRD Issue 15c: the identities a proposal may name, GameMaster-only.
        scene = (
            self._scene_loader(story_id, sheet)
            if self._scene_loader is not None
            else None
        )
        request = self._render(built_context, scene)

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
                        p.visibility, session_state.dice_handling
                    )
                }
            )
            for p in output.rolls
        ]
        if not sequences and any(
            p.visibility is RollVisibility.PLAYER for p in proposals
        ):
            raise AdjudicationRefusal(
                RefusalKind.PLAYER_ROLL_UNSUPPORTED,
                "this story's dice handling asks the player to roll, and no "
                "action-resolution sequence can be persisted here",
            )
        usage = AdjudicationPassResult(
            proposals=(),
            writer_views=(),
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )
        prepared = self.prepare_turn(story_id, sheet, proposals, decisions=sequences)
        if not sequences:
            records: list[ResolvedAdjudicationRecord] = []
            views = self.resolve_turn(
                prepared, session_state.gm_cheating, dice_service, records
            )
            return usage.model_copy(
                update={
                    "subjects": tuple(prepared.subjects.values()),
                    "coordination": prepared.coordination,
                    "discovery": prepared.discovery,
                    "proposals": tuple(records),
                    "writer_views": tuple(views),
                }
            )
        dice = SequenceDice(
            backend=dice_service,
            sequence_id=uuid4(),
            actor=("character", str(sheet.subject_id)),
            player_rolls=session_state.dice_handling is DiceHandling.PLAYER_ROLLS,
        )
        records = []
        read = {
            "subjects": tuple(prepared.subjects.values()),
            "coordination": prepared.coordination,
            "discovery": prepared.discovery,
        }
        try:
            views = self.resolve_turn(
                prepared, session_state.gm_cheating, dice, records
            )
        except PlayerInputRequired as pause:
            start = SequenceStart(
                sequence_id=dice.sequence_id,
                proposals=tuple(prepared.proposals),
                reads=prepared.reads(),
                gm_cheating=session_state.gm_cheating,
                player_rolls=dice.player_rolls,
                records=tuple(records),
                steps=tuple(dice.new_steps),
                pause=pause,
            )
            return usage.model_copy(
                update={
                    **read,
                    "writer_views": (start.announcement(),),
                    "sequence": start,
                }
            )
        return usage.model_copy(
            update={**read, "proposals": tuple(records), "writer_views": tuple(views)}
        )

    def prepare_turn(
        self,
        story_id: UUID,
        sheet: TurnCharacter,
        proposals: list[RollProposal],
        *,
        decisions: bool = True,
    ) -> PreparedTurn:
        """Read every subject the proposals name and check every proposal
        before any die is rolled (CRD Issues 2b, 15c). Dice-free and
        deterministic for the same stored state, so an action-resolution
        sequence repeats it to verify its reads (CRD Issue 15b).

        *decisions*: the Sojourner's result-triggered decisions can be
        offered (an action-resolution sequence can persist them). The
        knockout is then theirs, never preselected, and a melee hit may leave
        its target Unconscious whatever was selected."""
        subjects = self._load_subjects(story_id, sheet, proposals)
        coordination = self._load_coordination(story_id, proposals)
        discovery = None
        scans = any(p.operation in _EDGE_OPERATIONS for p in proposals) or any(
            self._adapter.savers(p, sheet, subjects) for p in proposals
        )
        if scans and self._discovery_reader is not None:
            # Taken before the scans: a change after it fails the commit.
            discovery = (story_id, self._discovery_reader(story_id))
        self._load_bounded(story_id, sheet, proposals, subjects)
        # Contract G1: every actor-turn edge is a legal transition, checked in
        # order before any die is rolled.
        openers = self._multiattacks(proposals, subjects)
        if coordination is None and any(
            p.operation in _EDGE_OPERATIONS
            or _uses(TurnCoordination(), p, sheet, subjects, i, openers)
            for i, p in enumerate(proposals)
        ):
            raise AdjudicationRefusal(
                RefusalKind.MISSING_STATE,
                "these operations spend the actor's turn, and no turn "
                "coordination is read",
            )
        if coordination is not None:
            _ledger(coordination.document, proposals, sheet, subjects, openers)
        self._limited_uses(proposals, subjects)
        _ammunition_supply(proposals, sheet)
        _species_once(proposals)
        if decisions:
            _decisions_offered(proposals)
        aura_holders = self._auras(story_id, sheet, proposals, subjects)
        # One subject's hand facts agree across the turn's operations: none
        # changes grip, so a difference is a contradiction.
        hands = {
            p.weapon_attack.hands
            for p in proposals
            if p.weapon_attack is not None and p.weapon_attack.hands is not None
        }
        if len(hands) > 1:
            raise AdjudicationRefusal(
                RefusalKind.INVALID_SELECTION,
                "the attacker's hand facts differ between operations of this turn",
            )

        # CRD Issue 2b: check every proposal before any has an effect, so a
        # later unsupported check cannot follow an earlier roll. CRD Issue
        # 15c: each is checked with every condition the turn's earlier
        # operations could apply already present. Refusal paths only grow
        # with a subject's conditions, so passing that state covers whichever
        # outcome the dice give.
        possible: dict[tuple[str, str], set[ConditionKind]] = {}
        moved: set[tuple[str, str]] = set()
        changed: set[tuple[str, str]] = set()
        for proposal in proposals:
            # Whether a subject is dying, knocked out or has a recovery
            # instance is not monotone like conditions: an earlier operation
            # of this turn can falsify it after its dice. Such an operation
            # needs a later turn.
            unsettled = changed & self._adapter.lifecycle_reads(proposal)
            if unsettled:
                kind, subject_id = sorted(unsettled)[0]
                raise AdjudicationRefusal(
                    RefusalKind.INVALID_SELECTION,
                    f"{proposal.check_label!r} turns on {kind} {subject_id}'s "
                    "zero-HP state, which an earlier operation of this turn can "
                    "change; it needs a later turn",
                )
            changed |= self._adapter.lifecycle_changes(proposal)
            spatial = self._adapter.spatial_subjects(proposal, sheet)
            if self._adapter.savers(proposal, sheet, subjects):
                # "Out of range" of each aura holder is consumed too.
                spatial |= aura_holders
            stale = moved & spatial
            if stale:
                raise AdjudicationRefusal(
                    RefusalKind.INVALID_SELECTION,
                    f"{proposal.check_label!r} states spatial facts about "
                    f"{sorted(stale)[0][0]} {sorted(stale)[0][1]}, which an earlier "
                    "operation of this turn can move; they need a later turn",
                )
            moved |= self._adapter.moved_subjects(proposal)
            view, view_subjects = with_possible(sheet, subjects, possible)
            try:
                self._adapter.require_supported(proposal, view, view_subjects)
            except AdjudicationRefusal:
                raise
            except Exception as exc:
                raise AdjudicationPassError(
                    f"Unsupported proposal {proposal.check_label!r}: {exc}"
                ) from exc
            for key, kinds in self._adapter.possible_conditions(
                proposal, view, view_subjects
            ).items():
                possible.setdefault(key, set()).update(kinds)
            sel = proposal.weapon_attack
            if decisions and sel is not None and _melee(sel):
                # The knockout decision may leave the target Unconscious.
                key = (sel.target.kind, str(sel.target.subject_id))
                possible.setdefault(key, set()).add(ConditionKind.UNCONSCIOUS)
        return PreparedTurn(
            proposals=proposals,
            sheet=sheet,
            subjects=subjects,
            coordination=coordination,
            discovery=discovery,
            openers=openers,
        )

    def resolve_turn(
        self,
        prepared: PreparedTurn,
        gm_cheating: bool,
        dice_service: DiceService,
        records: list[ResolvedAdjudicationRecord],
    ) -> list[WriterAdjudicationView]:
        """Resolve the prepared operations in order; return their Writer
        views. *records* holds what is already resolved: those operations are
        folded from their records, never resolved again, and every newly
        resolved one is appended. A sequence pause
        (:class:`~.models.PlayerInputRequired`) passes through, leaving
        *records* as resolved so far."""
        proposals, sheet = prepared.proposals, prepared.sheet
        subjects, openers = prepared.subjects, prepared.openers
        coordination = prepared.coordination
        done = len(records)
        views: list[WriterAdjudicationView] = []
        # Each operation reads the state the turn's earlier operations left
        # (CRD Issue 15c): two hits on one target compound. The snapshots the
        # turn read stay in the result, unadvanced: the orchestrator rechecks
        # their revisions and applies every effect to them in order.
        current, current_subjects = sheet, dict(subjects)
        document = coordination.document if coordination is not None else None
        begun = False
        method = getattr(type(dice_service), "operation", None)
        operation = None if method is None else lambda i, h: method(dice_service, i, h)
        for index, proposal in enumerate(proposals):
            if index < done:
                record = records[index]
            else:
                record, skipped = self._resolve_one(
                    proposal,
                    index,
                    records,
                    current,
                    current_subjects,
                    document,
                    gm_cheating,
                    dice_service,
                    operation,
                )
                if document is not None and not skipped:
                    # A Cleave or follow-up attack that is not triggered takes
                    # no use.
                    spent = _uses(document, proposal, current, subjects, index, openers)
                    if spent:
                        record = record.model_copy(
                            update={
                                "turn_uses": tuple(
                                    TurnUseRef(
                                        by=SubjectRef(
                                            kind=u.by.kind,  # type: ignore[arg-type]
                                            subject_id=u.by.subject_id,
                                        ),
                                        key=u.key,
                                    )
                                    for u in spent
                                )
                            }
                        )
                records.append(record)
            views.append(self._adapter.to_writer_view(record))
            if document is not None:
                for use in record.turn_uses:
                    document = take_use(
                        document,
                        SubjectReference(
                            kind=use.by.kind, subject_id=use.by.subject_id
                        ),
                        use.key,
                    )
            if record.turn_edge is not None and document is not None:
                ref = record.turn_edge.subject
                document, _ = apply_edge(
                    document,
                    record.turn_edge.kind,
                    SubjectReference(kind=ref.kind, subject_id=ref.subject_id),
                    begun_this_turn=begun,
                )
                begun = begun or record.turn_edge.kind == "begin"
            current, current_subjects = advanced(
                current, current_subjects, record.sheet_effects
            )
        return views

    def _resolve_one(
        self,
        proposal: RollProposal,
        index: int,
        records: list[ResolvedAdjudicationRecord],
        current: TurnCharacter,
        current_subjects: dict[tuple[str, str], TurnSubject],
        document: TurnCoordination | None,
        gm_cheating: bool,
        dice_service: DiceService,
        operation: Callable[[int, bool], AbstractContextManager[None]] | None,
    ) -> tuple[ResolvedAdjudicationRecord, bool]:
        """One operation's record, and whether it was skipped (an extra
        attack whose trigger did not happen)."""
        sel = proposal.weapon_attack
        creature = proposal.creature_attack
        skipped = (sel is not None and sel.cleave and not _cleaves(records)) or (
            creature is not None and creature.follows_up and not _follows_up(records)
        )
        if skipped:
            record = self._adapter.not_triggered(
                proposal, gm_cheating, "cleave" if sel is not None else "follow_up"
            )
            return record, True
        counted = _CountingDice(dice_service)
        hidden = proposal.visibility is RollVisibility.HIDDEN
        scope = operation(index, hidden) if operation is not None else nullcontext()
        try:
            with scope:
                resolved = self._adapter.resolve_roll(
                    proposal,
                    current,
                    None,
                    counted,
                    gm_cheating,
                    current_subjects,
                    document,
                )
            return resolved, False
        except PlayerInputRequired:
            raise
        except AdjudicationRefusal as exc:
            if records or counted.rolled:
                # Dice were rolled; discarding them would let a retry reroll
                # (Architecture Invariant 10). The preflight should have
                # refused this before any die: a defect, not a refusal.
                raise PreflightGapError(
                    f"{proposal.check_label!r} refused after earlier dice "
                    f"were rolled, which the preflight missed: {exc}"
                ) from exc
            raise
        except ActionResolutionError:
            raise
        except Exception as exc:
            raise AdjudicationPassError(
                f"Adapter failed to resolve proposal {proposal.check_label!r}: {exc}"
            ) from exc

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
            named = [proposal.subject]
            weapon, creature = proposal.weapon_attack, proposal.creature_attack
            area = proposal.creature_save_effect
            if weapon is not None:
                named += [weapon.target, *(weapon.hostiles_within_5_feet or ())]
            if creature is not None:
                named += [
                    creature.attacker,
                    creature.target,
                    *(creature.hostiles_within_5_feet or ()),
                    *(creature.allies_within_5_feet_of_target or ()),
                ]
            if area is not None:
                named += [area.source, *area.targets]
            for ref in named:
                if ref is not None:
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

    @staticmethod
    def _multiattacks(
        proposals: list[RollProposal],
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> dict[int, tuple[SubjectReference, str]]:
        """Each Multiattack (consecutive ``creature_attack`` proposals by one
        creature marked ``multiattack``), validated against the creature's
        printed alternatives before any die; keyed by its opening proposal,
        with the once-per-turn use it takes."""
        uses: dict[int, tuple[SubjectReference, str]] = {}
        index = 0
        while index < len(proposals):
            sel = proposals[index].creature_attack
            if sel is None or not sel.multiattack:
                index += 1
                continue
            end = index
            while end < len(proposals):
                nxt = proposals[end].creature_attack
                if nxt is None or not nxt.multiattack or nxt.attacker != sel.attacker:
                    break
                end += 1
            attacker = subjects.get((sel.attacker.kind, str(sel.attacker.subject_id)))
            if not isinstance(attacker, TurnCreature):
                raise AdjudicationRefusal(
                    RefusalKind.MISSING_STATE, "the Multiattack's creature was not read"
                )
            entries = [
                p.creature_attack.entry
                for p in proposals[index:end]
                if p.creature_attack is not None
            ]
            creature_attacks.check_multiattack(attacker, entries)
            uses[index] = (
                SubjectReference(kind="creature", subject_id=attacker.subject_id),
                creature_attacks.multiattack_key(attacker),
            )
            index = end
        return uses

    @staticmethod
    def _limited_uses(
        proposals: list[RollProposal],
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> None:
        """Refuse, before any die, proposals that together spend a creature's
        limited entry (Recharge, X/Day) beyond what it has left: each use is
        spent whether or not it hits or is saved against."""
        wanted: Counter[tuple[tuple[str, str], str]] = Counter()
        for proposal in proposals:
            for key, entry in creature_effects.limited_entries(proposal):
                wanted[(key, entry)] += 1
        for (key, entry), count in wanted.items():
            creature = subjects.get(key)
            if not isinstance(creature, TurnCreature):
                continue
            left = creature_effects.remaining(creature, entry)
            if left is not None and count > left:
                raise AdjudicationRefusal(
                    RefusalKind.INVALID_SELECTION,
                    f"{entry} is used {count} times this turn; {left} use(s) left",
                )

    def _auras(
        self,
        story_id: UUID,
        sheet: TurnCharacter,
        proposals: list[RollProposal],
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> set[tuple[str, str]]:
        """Refuse, before any die, a save another creature's aura could
        change (:mod:`.bystanders`). Holders are found in the whole story and
        read like any other subject, so their revisions are rechecked."""
        forcing = [(p, self._adapter.savers(p, sheet, subjects)) for p in proposals]
        if not any(savers for _, savers in forcing):
            return set()
        if self._aura_loader is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_STATE,
                "no reader of the story's aura holders is wired",
            )
        holders = bystanders.aura_holders(self._aura_loader(story_id))
        for holder in holders:
            if holder.sheet_id != sheet.sheet_id:
                subjects.setdefault(("character", str(holder.sheet_id)), holder)
        for proposal, savers in forcing:
            selection = (
                proposal.weapon_attack
                or proposal.creature_attack
                or proposal.creature_save_effect
            )
            bystanders.check_auras(
                holders,
                savers,
                selection.auras_in_range if selection is not None else None,
            )
        return {("character", str(h.subject_id)) for h in holders}

    def _load_bounded(
        self,
        story_id: UUID,
        sheet: TurnCharacter,
        proposals: list[RollProposal],
        subjects: dict[tuple[str, str], TurnSubject],
    ) -> None:
        """Add every subject of the story holding an effect bounded by an
        edge subject's turn (contract G2), so the edge can end it with the
        same recheck as any other subject."""
        for proposal in proposals:
            if proposal.operation not in _EDGE_OPERATIONS or proposal.subject is None:
                continue
            if self._bounded_loader is None:
                raise AdjudicationRefusal(
                    RefusalKind.MISSING_STATE,
                    "no reader of turn-bounded effects is wired, so an edge cannot "
                    "end them",
                )
            for holder in self._bounded_loader(story_id, proposal.subject):
                key = (
                    "creature" if isinstance(holder, TurnCreature) else "character",
                    str(holder.subject_id),
                )
                if key != ("character", str(sheet.sheet_id)):
                    subjects.setdefault(key, holder)

    def _load_coordination(
        self, story_id: UUID, proposals: list[RollProposal]
    ) -> StoredCoordination | None:
        """The story's actor-turn coordination, read once when a proposal is
        an actor-turn edge (contract G1)."""
        if not proposals:
            return None
        if not any(p.operation in _EDGE_OPERATIONS for p in proposals):
            if self._coordination_loader is not None:
                return self._coordination_loader(story_id)
            return None
        if self._coordination_loader is None:
            raise AdjudicationRefusal(
                RefusalKind.MISSING_STATE,
                "no turn-coordination reader is wired, so an actor-turn edge "
                "cannot be applied",
            )
        return self._coordination_loader(story_id)

    # -----------------------------------------------------------------------
    # Prompt rendering
    # -----------------------------------------------------------------------

    def _render(
        self, built_context: AssembledContext, scene: str | None = None
    ) -> ProviderCallRequest:
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
        if scene:
            # After the shared stable prefix, which it never changes.
            rendered_blocks.append(RenderedBlock(text=scene))

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
