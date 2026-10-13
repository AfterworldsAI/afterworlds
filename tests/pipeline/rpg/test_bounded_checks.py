"""CRD Issue 15c — certified source-fixed-DC checks against accepted G1 authority.

Every number comes from the character's exact binding (``real_index``: the
effective G1 view) and recorded state; every refusal is typed and happens
before any die is rolled.
"""

from __future__ import annotations

import dataclasses
import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    ConditionKind,
    Skill,
)
from afterworlds.models.dnd5e_state import (
    AbilityAdjustment,
    ActiveEffect,
    ClassLevel,
    ConditionInstance,
    Dnd5eCharacterState,
    FeatSelection,
    GrantSource,
    OriginSelection,
    RecordChoice,
    SkillGrant,
    ToolGrant,
    VocabularyChoice,
)
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.models.rpg import DiceResult, RollProposal
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.pipeline.rpg import checks, grants
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import (
    MANIFEST,
    AdjudicationRefusal,
    CapabilityStatus,
    Operation,
    RefusalKind,
    certify,
    governing_fingerprint,
)
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.holdings import Holder, HolderKind, ItemInstance
from afterworlds.services.dnd5e_state.turn import TurnCharacter
from tests.rpg_characters import item, srd_character
from tests.services.dnd5e_state.builders import choice, complete_character, real_index

CLIMB = "glossary.climbing/difficult_climb"


def _proposal(
    identity: str | None = CLIMB,
    operation: str | None = "fixed_dc_check",
    visibility: RollVisibility = RollVisibility.SHOWN,
) -> RollProposal:
    return RollProposal(
        check_label="Athletics Check",
        subsystem_tag="climb",
        visibility=visibility,
        operation=operation,
        check_identity=identity,
    )


def _dice(*raw: int) -> MagicMock:
    dice = MagicMock()
    chosen = raw[0] if len(raw) == 1 else None

    def roll(expression: str) -> DiceResult:
        pick = chosen
        if pick is None:
            pick = max(raw) if expression == "2d20kh1" else min(raw)
        return DiceResult(expression=expression, raw_rolls=raw, chosen=pick)

    dice.roll.side_effect = roll
    return dice


def _state(**update: object) -> Dnd5eCharacterState:
    return complete_character(real_index(), "classes.wizard", 3).model_copy(
        update=update
    )


def _resolve(
    character: TurnCharacter, *raw: int, proposal: RollProposal | None = None
) -> tuple[object, MagicMock]:
    dice = _dice(*raw)
    record = D20RulesSystemAdapter().resolve_roll(
        proposal or _proposal(), character, None, dice, gm_cheating=False
    )
    return record, dice


def _refused(
    kind: RefusalKind, character: TurnCharacter, proposal: RollProposal | None = None
) -> AdjudicationRefusal:
    dice = MagicMock()
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().resolve_roll(
            proposal or _proposal(), character, None, dice, gm_cheating=False
        )
    dice.roll.assert_not_called()
    assert caught.value.kind is kind, caught.value
    return caught.value


# ---------------------------------------------------------------------------
# Positive coverage: numbers from typed authority
# ---------------------------------------------------------------------------


def test_the_dc_ability_and_skill_come_from_the_typed_check_fact() -> None:
    record, dice = _resolve(srd_character(), 10)
    dice.roll.assert_called_once_with("1d20")
    assert record.dc == 15  # Difficult Climb: DC 15 Strength (Athletics)
    assert record.total == 9  # 10 + Str 8 (-1); no Athletics proficiency
    assert record.outcome == "failure"
    provenance = json.loads(record.modifiers_json)
    assert provenance["check_identity"] == CLIMB
    assert provenance["dc_source"] == CLIMB
    assert (provenance["ability"], provenance["skill"]) == ("strength", "athletics")
    assert provenance["breakdown"] == {"strength_modifier": -1}


@pytest.mark.parametrize(
    ("identity", "dc"),
    [
        ("glossary.climbing/difficult_climb", 15),
        ("glossary.long_jump/low_obstacle", 10),
        ("glossary.swimming/rough_water", 15),
    ],
)
def test_every_admitted_identity_resolves_at_its_printed_dc(
    identity: str, dc: int
) -> None:
    record, _ = _resolve(srd_character(), 16, proposal=_proposal(identity))
    assert record.dc == dc
    assert record.outcome == ("success" if dc <= 15 else "failure")


SOLDIER = GrantSource(
    record_key="character_origins.soldier", component_key="skill_proficiencies"
)
ROGUE_TRAITS = GrantSource(record_key="classes.rogue", component_key="core_traits")
ROGUE_EXPERTISE = GrantSource(
    record_key="classes.rogue.expertise", component_key="expertise"
)
WIZARD_TRAITS = GrantSource(record_key="classes.wizard", component_key="core_traits")
ASI = ("feats.ability_score_improvement", "ability_score_improvement")


def _athletics(source: GrantSource, expertise: bool = False) -> SkillGrant:
    return SkillGrant(skill=Skill.ATHLETICS, expertise=expertise, source=source)


def _soldier(**update: object) -> Dnd5eCharacterState:
    return _state(
        background=OriginSelection(record_key="character_origins.soldier"), **update
    )


def _rogue(level: int, *grants: SkillGrant) -> Dnd5eCharacterState:
    return _state(
        classes=(
            ClassLevel(class_record_key="classes.rogue", level=level, hit_die="d8"),
        ),
        level_history=("classes.rogue",) * level,
        skill_proficiencies=grants,
    )


def test_proficiency_comes_from_a_validated_grant_and_the_typed_band() -> None:
    """Soldier's background grants Athletics (``skill_proficiency_grant``)."""
    character = srd_character(_soldier(skill_proficiencies=(_athletics(SOLDIER),)))
    record, _ = _resolve(character, 10)
    assert record.total == 11  # 10 - 1 + PB 2 (levels 1-4)
    breakdown = json.loads(record.modifiers_json)["breakdown"]
    assert breakdown == {"strength_modifier": -1, "proficiency_bonus": 2}


@pytest.mark.parametrize(
    "source",
    [WIZARD_TRAITS, GrantSource(record_key="classes.wizard")],
    ids=["choice-without-athletics", "bare-record"],
)
def test_a_grant_its_source_does_not_give_is_refused(source: GrantSource) -> None:
    """Storage provenance is not entitlement: the Wizard's level-1 skill
    choice does not offer Athletics, and a bare record names no grant."""
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(_state(skill_proficiencies=(_athletics(source),))),
    )


def test_a_grant_from_a_background_the_character_lacks_is_refused() -> None:
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(_state(skill_proficiencies=(_athletics(SOLDIER),))),
    )


def test_a_choice_over_its_count_is_refused() -> None:
    """Rogue level-1 traits: four skills from its list."""
    picks = (
        Skill.ATHLETICS,
        Skill.ACROBATICS,
        Skill.STEALTH,
        Skill.DECEPTION,
        Skill.INSIGHT,
    )
    grants = tuple(
        SkillGrant(skill=k, expertise=False, source=ROGUE_TRAITS) for k in picks
    )
    _refused(RefusalKind.INVALID_SELECTION, srd_character(_rogue(1, *grants)))
    record, _ = _resolve(srd_character(_rogue(1, *grants[:4])), 10)
    assert record.total == 11  # Athletics from a valid Rogue pick: PB 2


def test_expertise_multiplies_by_the_typed_rule_from_an_expertise_source() -> None:
    """Rogue Expertise (gained at level 1) on a skill proficient by Rogue's
    traits; ``glossary.expertise`` doubles the Proficiency Bonus."""
    state = _rogue(5, _athletics(ROGUE_TRAITS), _athletics(ROGUE_EXPERTISE, True))
    record, _ = _resolve(srd_character(state), 10)
    assert record.total == 15  # 10 - 1 + 2 x PB 3 (levels 5-8)
    assert json.loads(record.modifiers_json)["breakdown"]["expertise"] == 6


@pytest.mark.parametrize(
    "grants",
    [
        # Expertise from a source that grants none (the earlier test's Wizard).
        (_athletics(ROGUE_TRAITS), _athletics(WIZARD_TRAITS, True)),
        # Expertise without proficiency by a separate grant.
        (_athletics(ROGUE_EXPERTISE, True),),
        # Expertise recorded twice for one skill.
        (
            _athletics(ROGUE_TRAITS),
            _athletics(ROGUE_EXPERTISE, True),
            _athletics(ROGUE_EXPERTISE, True),
        ),
    ],
    ids=["no-expertise-source", "not-proficient", "duplicate"],
)
def test_invalid_expertise_is_refused(grants: tuple[SkillGrant, ...]) -> None:
    _refused(RefusalKind.INVALID_SELECTION, srd_character(_rogue(5, *grants)))


def _asi_state(level: int, *amounts: tuple[AbilityScore, int]) -> Dnd5eCharacterState:
    """A Wizard holding Ability Score Improvement from its level-4 feature."""
    index = real_index()
    feature = GrantSource(
        record_key="classes.wizard.ability_score_improvement",
        component_key="ability_score_improvement",
    )
    asi = GrantSource(record_key=ASI[0], component_key=ASI[1], choice_id="asi-4")
    base = _state(
        classes=(
            ClassLevel(class_record_key="classes.wizard", level=level, hit_die="d6"),
        ),
        level_history=("classes.wizard",) * level,
    )
    selected = tuple(
        VocabularyChoice(vocabulary="ability", value=a.value) for a, _ in amounts
    )
    return base.model_copy(
        update={
            "feats": (
                *(base.feats or ()),
                FeatSelection(
                    feat_record_key=ASI[0], source=feature, choice_ids=("asi-4",)
                ),
            ),
            "choices": (*(base.choices or ()), choice(index, "asi-4", *ASI, *selected)),
            "ability_adjustments": tuple(
                AbilityAdjustment(ability=a, amount=n, source=asi) for a, n in amounts
            ),
        }
    )


def test_an_ability_score_improvement_applies_its_typed_pattern() -> None:
    """A level-4 Wizard's Ability Score Improvement: +2 to one ability."""
    record, _ = _resolve(srd_character(_asi_state(4, (AbilityScore.STRENGTH, 2))), 10)
    assert record.total == 10  # Str 8 + 2 = 10 (+0)


@pytest.mark.parametrize(
    ("level", "amounts"),
    [
        (4, ((AbilityScore.STRENGTH, 4),)),
        (4, ((AbilityScore.STRENGTH, 30),)),
        (4, ((AbilityScore.STRENGTH, 1), (AbilityScore.STRENGTH, 1))),
        (3, ((AbilityScore.STRENGTH, 2),)),
    ],
    ids=["plus-4", "plus-30", "same-ability-twice", "not-gained-at-level-3"],
)
def test_an_invalid_ability_increase_is_refused(
    level: int, amounts: tuple[tuple[AbilityScore, int], ...]
) -> None:
    """+4 and +30 are not patterns (the earlier test applied both); +1/+1
    must be distinct; a level-3 Wizard has gained no improvement."""
    _refused(RefusalKind.INVALID_SELECTION, srd_character(_asi_state(level, *amounts)))


def test_an_adjustment_from_a_source_with_no_typed_increase_is_refused() -> None:
    alert = AbilityAdjustment(
        ability=AbilityScore.STRENGTH,
        amount=2,
        source=GrantSource(
            record_key="feats.alert", component_key="initiative_proficiency"
        ),
    )
    refusal = _refused(
        RefusalKind.MISSING_AUTHORITY,
        srd_character(_state(ability_adjustments=(alert,))),
    )
    assert "feats.alert" in refusal.detail


def _condition(kind: ConditionKind, level: int | None = None) -> ConditionInstance:
    return ConditionInstance(
        instance_id=str(uuid4()),
        condition=kind,
        visibility=ConditionVisibility.VISIBLE,
        level=level,
    )


def test_poisoned_imposes_disadvantage_from_its_typed_fact() -> None:
    character = srd_character(_state(conditions=(_condition(ConditionKind.POISONED),)))
    record, dice = _resolve(character, 18, 4)
    dice.roll.assert_called_once_with("2d20kl1")
    assert record.total == 3
    provenance = json.loads(record.modifiers_json)
    assert provenance["disadvantage_sources"] == [
        "glossary.poisoned/ability_checks_and_attacks_affected"
    ]


@pytest.mark.parametrize(
    "kind", [ConditionKind.PRONE, ConditionKind.GRAPPLED, ConditionKind.CHARMED]
)
def test_conditions_without_an_effect_on_own_checks_change_nothing(
    kind: ConditionKind,
) -> None:
    record, dice = _resolve(srd_character(_state(conditions=(_condition(kind),))), 10)
    dice.roll.assert_called_once_with("1d20")
    assert record.total == 9


@pytest.mark.parametrize("face", [1, 20])
def test_natural_one_and_twenty_are_not_special_on_an_ability_check(
    face: int,
) -> None:
    state = _rogue(
        1, _athletics(ROGUE_TRAITS), _athletics(ROGUE_EXPERTISE, expertise=True)
    )
    state = state.model_copy(
        update={
            "ability_scores": state.ability_scores.model_copy(  # type: ignore[union-attr]
                update={"strength": 20}
            )
        }
    )
    record, _ = _resolve(srd_character(state), face)
    # 1 + 5 + 4 = 10 vs DC 15 fails; 20 + 9 succeeds -- never "critical".
    assert record.outcome == ("failure" if face == 1 else "success")


def test_gm_cheating_off_is_snapshotted_on_the_immutable_record() -> None:
    record, _ = _resolve(srd_character(), 10)
    assert record.gm_cheating_at_roll is False
    with pytest.raises(Exception):  # noqa: B017, PT011 -- frozen model
        record.outcome = "success"  # type: ignore[misc]


def test_a_hidden_check_reaches_the_writer_scrubbed() -> None:
    adapter = D20RulesSystemAdapter()
    record, _ = _resolve(
        srd_character(), 10, proposal=_proposal(visibility=RollVisibility.HIDDEN)
    )
    view = adapter.to_writer_view(record)
    assert (view.check_label, view.total, view.dc, view.outcome) == (
        "",
        None,
        None,
        None,
    )
    assert record.dc == 15  # kept for the backend audit only


def test_the_certificate_binds_the_exact_release_and_versions() -> None:
    record, _ = _resolve(srd_character(), 10)
    cert = json.loads(record.modifiers_json)["certificate"]
    binding = real_index().binding
    assert cert == {
        "manifest_version": "15c-manifest-2",
        "adapter_version": "15c-d20-2",
        "operation": "fixed_dc_check",
        "package_uuid": str(binding.package_uuid),
        "release_version": binding.release_version,
        "projection_uuid": str(binding.mechanical_projection_uuid),
        "override_set_uuid": str(binding.override_set_uuid),
        "fingerprint": MANIFEST[Operation.FIXED_DC_CHECK].fingerprint,
    }


# ---------------------------------------------------------------------------
# Refusals: typed and distinguishable (AC5), before any die
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "operation",
    [o for o in Operation if MANIFEST[o].status is CapabilityStatus.HELD],
)
def test_held_operations_refuse_as_unsupported_capability(
    operation: Operation,
) -> None:
    """Accepted authority exists; execution does not yet, so the refusal is
    unsupported capability naming what the operation waits on."""
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(),
        _proposal(operation=operation.value),
    )
    assert "waits on" in refusal.detail


def test_a_proposal_naming_no_operation_is_unsupported_not_label_rolled() -> None:
    _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(),
        _proposal(operation=None),
    )


@pytest.mark.parametrize(
    ("operation", "identity"),
    [
        ("contest", CLIMB),
        ("fixed_dc_check", None),
        ("fixed_dc_check", "glossary.hide/hide_check"),
        ("fixed_dc_check", "glossary.long_jump/difficult_landing"),
        ("fixed_dc_check", "play.damage_and_healing/stabilizing"),
        ("fixed_dc_check", "glossary.climbing"),
    ],
)
def test_invalid_selections_are_refused(operation: str, identity: str | None) -> None:
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(),
        _proposal(identity, operation),
    )


def test_missing_state_is_distinguished() -> None:
    _refused(RefusalKind.MISSING_STATE, srd_character(_state(ability_scores=None)))
    _refused(RefusalKind.MISSING_STATE, srd_character(_state(conditions=None)))


def test_an_unresolved_authority_index_is_missing_authority() -> None:
    character = dataclasses.replace(srd_character(), index=None)
    _refused(RefusalKind.MISSING_AUTHORITY, character)


def test_another_projection_is_an_incompatible_certification() -> None:
    index = real_index()
    other = RulesPackageBinding(
        package_uuid=index.binding.package_uuid,
        release_version=index.binding.release_version,
        mechanical_projection_uuid=uuid4(),
        override_set_uuid=index.binding.override_set_uuid,
    )
    moved = dataclasses.replace(index, binding=other)
    _refused(RefusalKind.INCOMPATIBLE_CERTIFICATION, srd_character(index=moved))


def _with_component(
    index: AuthorityIndex, record_key: str, component_key: str, **change: object
) -> AuthorityIndex:
    record = index.records[record_key]
    components = tuple(
        dataclasses.replace(c, **change) if c.semantic_key == component_key else c
        for c in record.components
    )
    records = dict(index.records)
    records[record_key] = dataclasses.replace(record, components=components)
    return dataclasses.replace(index, records=records)


@pytest.mark.parametrize(
    ("record_key", "component_key"),
    [
        ("glossary.climbing", "difficult_climb"),
        ("play.proficiency.proficiency_bonus", "proficiency_bonus_bands"),
        ("glossary.expertise", "expertise"),
        ("glossary.poisoned", "ability_checks_and_attacks_affected"),
    ],
)
def test_an_override_of_a_governing_component_invalidates_certification(
    record_key: str, component_key: str
) -> None:
    changed = _with_component(
        real_index(), record_key, component_key, supplied_by_override_id="house-rule"
    )
    assert governing_fingerprint(changed) != governing_fingerprint(real_index())
    _refused(RefusalKind.INCOMPATIBLE_CERTIFICATION, srd_character(index=changed))


def test_an_unrelated_override_keeps_certification() -> None:
    changed = _with_component(
        real_index(),
        "equipment.weapons.longsword",
        "longsword",
        supplied_by_override_id="house-rule",
    )
    assert certify(Operation.FIXED_DC_CHECK, changed).fingerprint == (
        MANIFEST[Operation.FIXED_DC_CHECK].fingerprint
    )
    record, _ = _resolve(srd_character(index=changed), 10)
    assert record.outcome == "failure"


def test_a_missing_governing_component_is_missing_authority() -> None:
    index = real_index()
    records = dict(index.records)
    del records["glossary.expertise"]
    _refused(
        RefusalKind.MISSING_AUTHORITY,
        srd_character(index=dataclasses.replace(index, records=records)),
    )


# -- unsupported contributors refuse rather than being ignored --------------


@pytest.mark.parametrize(
    "kind", [ConditionKind.FRIGHTENED, ConditionKind.BLINDED, ConditionKind.DEAFENED]
)
def test_a_condition_whose_effect_needs_judgement_refuses(kind: ConditionKind) -> None:
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(_state(conditions=(_condition(kind),))),
    )
    assert f"glossary.{kind.value}/" in refusal.detail


def test_exhaustion_refuses() -> None:
    _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(_state(conditions=(_condition(ConditionKind.EXHAUSTION, 1),))),
    )


def test_an_active_effect_refuses() -> None:
    effect = ActiveEffect(
        instance_id="guidance",
        source=GrantSource(record_key="spells.guidance"),
        concentration=True,
    )
    _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(_state(active_effects=(effect,))),
    )


def test_a_contributing_class_feature_refuses_once_gained() -> None:
    rogue = ClassLevel(class_record_key="classes.rogue", level=7, hit_die="d8")
    state = _state(classes=(rogue,), level_history=("classes.rogue",) * 7)
    refusal = _refused(RefusalKind.UNSUPPORTED_CAPABILITY, srd_character(state))
    assert "classes.rogue.reliable_talent" in refusal.detail

    earlier = rogue.model_copy(update={"level": 6})
    state = _state(classes=(earlier,), level_history=("classes.rogue",) * 6)
    record, _ = _resolve(srd_character(state), 10)  # not yet gained
    assert record.outcome == "failure"


def test_a_contributing_subclass_feature_refuses() -> None:
    warlock = ClassLevel(class_record_key="classes.warlock", level=3, hit_die="d8")
    state = _state(classes=(warlock,), level_history=("classes.warlock",) * 3)
    record, _ = _resolve(srd_character(state), 10)  # no contributor yet
    assert record.outcome == "failure"

    fiend = warlock.model_copy(
        update={"subclass_record_key": "classes.warlock.fiend_patron"}
    )
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(_state(classes=(fiend,), level_history=state.level_history)),
    )
    assert "classes.warlock.fiend_patron.dark_ones_own_luck" in refusal.detail


def test_a_contributing_species_trait_refuses() -> None:
    halfling = OriginSelection(record_key="character_origins.halfling")
    refusal = _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY, srd_character(_state(species=halfling))
    )
    assert "character_origins.halfling/luck" in refusal.detail


def _held(record_key: str, *, equipped: bool) -> ItemInstance:
    return ItemInstance(
        item_id=uuid4(),
        story_id=uuid4(),
        record_key=record_key,
        component_key=None,
        quantity=1,
        holder=Holder(HolderKind.CHARACTER, uuid4()),
        equipped=equipped,
        attuned_subject_id=None,
        charges_remaining=None,
        applied_poison_record_key=None,
        revision=1,
    )


def test_worn_armor_holds_strength_and_dexterity_checks_on_c1c() -> None:
    refusal = _refused(
        RefusalKind.MISSING_AUTHORITY,
        srd_character(items=(_held("equipment.armor.chain_mail", equipped=True),)),
    )
    assert "C1-C" in refusal.detail
    # carried, not worn: nothing to apply
    record, _ = _resolve(
        srd_character(items=(_held("equipment.armor.chain_mail", equipped=False),)), 10
    )
    assert record.outcome == "failure"


def test_an_equipped_magic_item_refuses() -> None:
    _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        srd_character(items=(_held("magic_items.cloak_of_protection", equipped=True),)),
    )


def test_a_player_roll_is_refused_before_preparation() -> None:
    with pytest.raises(AdjudicationRefusal) as caught:
        D20RulesSystemAdapter().require_supported(
            _proposal(visibility=RollVisibility.PLAYER), srd_character()
        )
    assert caught.value.kind is RefusalKind.PLAYER_ROLL_UNSUPPORTED


def test_prepare_is_pure_and_matches_the_rolled_record() -> None:
    character = srd_character()
    prepared = checks.prepare(_proposal(), character)
    assert (prepared.dc, prepared.modifier, prepared.expression) == (15, -1, "1d20")
    rolled = checks.roll(prepared, _dice(12))
    assert (rolled.total, rolled.outcome) == (11, "failure")


# ---------------------------------------------------------------------------
# Earned instances and shared choices (Codex grant review, three P1 findings)
# ---------------------------------------------------------------------------

ACOLYTE = "character_origins.acolyte"
SKILLED = GrantSource(record_key="feats.skilled", component_key="skilled")


def _acolyte_increases(*choice_ids: str) -> Dnd5eCharacterState:
    """A level-1 Acolyte recording its one background increase under each of
    *choice_ids*: +2 Intelligence and +1 Wisdom each time."""
    index = real_index()
    choices = tuple(
        choice(
            index,
            cid,
            ACOLYTE,
            "ability_scores",
            VocabularyChoice(vocabulary="ability", value="intelligence"),
            VocabularyChoice(vocabulary="ability", value="wisdom"),
        )
        for cid in choice_ids
    )
    adjustments = tuple(
        AbilityAdjustment(
            ability=a,
            amount=n,
            source=GrantSource(
                record_key=ACOLYTE, component_key="ability_scores", choice_id=cid
            ),
        )
        for cid in choice_ids
        for a, n in ((AbilityScore.INTELLIGENCE, 2), (AbilityScore.WISDOM, 1))
    )
    base = _state(background=OriginSelection(record_key=ACOLYTE))
    return base.model_copy(
        update={
            "choices": (*(base.choices or ()), *choices),
            "ability_adjustments": adjustments,
        }
    )


def test_one_earned_background_increase_applies_once() -> None:
    index = real_index()
    once = grants.ability_score(
        index, _acolyte_increases("bg-1"), AbilityScore.INTELLIGENCE
    )
    assert once[0] == 17  # Int 15 + 2
    with pytest.raises(AdjudicationRefusal) as caught:
        grants.ability_score(
            index, _acolyte_increases("bg-1", "bg-2"), AbilityScore.INTELLIGENCE
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


def test_one_ability_score_improvement_selection_applies_once() -> None:
    """Two +2 groups under different choice ids, one earned selection."""
    state = _asi_state(4, (AbilityScore.STRENGTH, 2))
    second = AbilityAdjustment(
        ability=AbilityScore.DEXTERITY,
        amount=2,
        source=GrantSource(record_key=ASI[0], component_key=ASI[1], choice_id="asi-x"),
    )
    index = real_index()
    state = state.model_copy(
        update={
            "choices": (
                *(state.choices or ()),
                choice(
                    index,
                    "asi-x",
                    *ASI,
                    VocabularyChoice(vocabulary="ability", value="dexterity"),
                ),
            ),
            "ability_adjustments": (*(state.ability_adjustments or ()), second),
        }
    )
    _refused(RefusalKind.INVALID_SELECTION, srd_character(state))


def _wizard_with_feat(
    feat: str, *adjustments: AbilityAdjustment
) -> Dnd5eCharacterState:
    """A level-4 Wizard who took *feat* with its Ability Score Improvement
    feature's "or another feat for which you qualify"."""
    feature = GrantSource(
        record_key="classes.wizard.ability_score_improvement",
        component_key="ability_score_improvement",
    )
    base = _state(
        classes=(ClassLevel(class_record_key="classes.wizard", level=4, hit_die="d6"),),
        level_history=("classes.wizard",) * 4,
        ability_adjustments=adjustments,
    )
    return base.model_copy(
        update={
            "feats": (
                *(base.feats or ()),
                FeatSelection(feat_record_key=feat, source=feature),
            )
        }
    )


def test_a_class_feat_choice_admits_a_qualifying_feat() -> None:
    """Grappler (General, level 4+, Strength or Dexterity 13+): typed
    prerequisites met by the Wizard's base Dexterity 14; its +1 Dexterity
    (cap 20) applies."""
    plus_one = AbilityAdjustment(
        ability=AbilityScore.DEXTERITY,
        amount=1,
        source=GrantSource(
            record_key="feats.grappler", component_key="ability_score_increase"
        ),
    )
    state = _wizard_with_feat("feats.grappler", plus_one)
    assert grants.ability_score(real_index(), state, AbilityScore.DEXTERITY)[0] == 15


def test_a_feat_with_no_typed_category_cannot_be_certified_by_a_choice() -> None:
    """Skilled's Origin category is prose in the accepted authority, so its
    eligibility under a category or qualifying-feat choice is refused as
    missing authority, naming the feat."""
    state = _wizard_with_feat("feats.skilled")
    state = state.model_copy(update={"skill_proficiencies": (_athletics(SKILLED),)})
    refusal = _refused(RefusalKind.MISSING_AUTHORITY, srd_character(state))
    assert "feats.skilled" in refusal.detail


@pytest.fixture
def skilled_entitled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Treat every feat selection as entitled, to exercise Skilled's shared
    skill/tool allowance on its own: no Skilled path is certifiable from the
    accepted authority (see the test above)."""
    monkeypatch.setattr(grants, "_check_feat_source", lambda *a, **k: None)


def _human_with_skilled(skills: tuple[Skill, ...], tools: int) -> Dnd5eCharacterState:
    """A Human whose Versatile trait gave Skilled, spending its three picks on
    *skills* and *tools* Thieves' Tools-like tool entries."""
    tool_targets = [
        ("equipment.tools.thieves_tools", "thieves_tools"),
        ("equipment.tools.herbalism_kit", "herbalism_kit"),
    ][:tools]
    base = _state(species=OriginSelection(record_key="character_origins.human"))
    return base.model_copy(
        update={
            "choices": tuple(
                c for c in base.choices or () if c.choice_id != "elf-lineage"
            ),
            "feats": (
                *(base.feats or ()),
                FeatSelection(
                    feat_record_key="feats.skilled",
                    source=GrantSource(
                        record_key="character_origins.human",
                        component_key="versatile",
                    ),
                ),
            ),
            "skill_proficiencies": tuple(
                SkillGrant(skill=k, expertise=False, source=SKILLED) for k in skills
            ),
            "tool_proficiencies": tuple(
                ToolGrant(
                    record_key=r, component_key=c, expertise=False, source=SKILLED
                )
                for r, c in tool_targets
            ),
        }
    )


def test_skilled_shares_one_allowance_between_skills_and_tools(
    skilled_entitled: None,
) -> None:
    within = _human_with_skilled((Skill.ATHLETICS, Skill.STEALTH), tools=1)
    record, _ = _resolve(srd_character(within), 10)
    assert record.total == 11
    index = real_index()
    assert grants.tool_proficiency(
        index, within, "equipment.tools.thieves_tools", "thieves_tools"
    )
    over = _human_with_skilled((Skill.ATHLETICS, Skill.STEALTH, Skill.ARCANA), tools=1)
    _refused(RefusalKind.INVALID_SELECTION, srd_character(over))


# ---------------------------------------------------------------------------
# A grant must agree with the choice it cites (Codex grant review, round 2)
# ---------------------------------------------------------------------------


def _with(state: Dnd5eCharacterState, **update: object) -> Dnd5eCharacterState:
    return state.model_copy(update=update)


def test_an_increase_to_an_ability_its_choice_did_not_select_is_refused() -> None:
    """The ASI choice ``asi-4`` selected Strength; a +2 Dexterity citing it
    is not the increase that choice made."""
    state = _asi_state(4, (AbilityScore.STRENGTH, 2))
    moved = tuple(
        a.model_copy(update={"ability": AbilityScore.DEXTERITY})
        for a in state.ability_adjustments or ()
    )
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(_with(state, ability_adjustments=moved)),
    )


def test_a_grant_citing_another_sources_choice_is_refused() -> None:
    """``asi-4`` was made under the ASI feat; a background increase cannot
    cite it."""
    state = _asi_state(4, (AbilityScore.STRENGTH, 2))
    borrowed = AbilityAdjustment(
        ability=AbilityScore.STRENGTH,
        amount=2,
        source=GrantSource(
            record_key="character_origins.sage",
            component_key="ability_scores",
            choice_id="asi-4",
        ),
    )
    refusal = _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(_with(state, ability_adjustments=(borrowed,))),
    )
    assert "made under" in refusal.detail


def test_a_skill_grant_its_choice_did_not_select_is_refused() -> None:
    index = real_index()
    picked = choice(
        index,
        "rogue-skills",
        "classes.rogue",
        "core_traits",
        VocabularyChoice(vocabulary="skill", value="stealth"),
    )
    linked = ROGUE_TRAITS.model_copy(update={"choice_id": "rogue-skills"})
    state = _rogue(1, _athletics(linked))
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(_with(state, choices=(*(state.choices or ()), picked))),
    )
    agreeing = _with(
        state,
        choices=(
            *(state.choices or ()),
            picked.model_copy(
                update={
                    "selected": (
                        VocabularyChoice(vocabulary="skill", value="athletics"),
                    )
                }
            ),
        ),
    )
    record, _ = _resolve(srd_character(agreeing), 10)
    assert record.total == 11


def test_a_tool_grant_its_choice_did_not_select_is_refused(
    skilled_entitled: None,
) -> None:
    index = real_index()
    state = _human_with_skilled((Skill.ATHLETICS, Skill.STEALTH), tools=1)
    picked = choice(
        index,
        "skilled-picks",
        "feats.skilled",
        "skilled",
        RecordChoice(record_key="equipment.tools.herbalism_kit"),
    )
    tools = tuple(
        t.model_copy(
            update={"source": SKILLED.model_copy(update={"choice_id": "skilled-picks"})}
        )
        for t in state.tool_proficiencies or ()
    )
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(
            _with(
                state,
                choices=(*(state.choices or ()), picked),
                tool_proficiencies=tools,
            )
        ),
    )


# ---------------------------------------------------------------------------
# Difficulty checks, tool checks and Initiative (native C5 authority)
# ---------------------------------------------------------------------------


def _op(operation: str, **selection: str | None) -> RollProposal:
    return RollProposal(
        check_label="check",
        subsystem_tag="check",
        visibility=RollVisibility.SHOWN,
        operation=operation,
        **selection,
    )


def test_a_difficulty_check_reads_its_dc_from_the_selected_typical_dc() -> None:
    proposal = _op(
        "difficulty_check", ability="strength", skill="athletics", difficulty="hard"
    )
    record, dice = _resolve(srd_character(), 10, proposal=proposal)
    dice.roll.assert_called_once_with("1d20")
    assert (record.dc, record.total, record.outcome) == (20, 9, "failure")
    provenance = json.loads(record.modifiers_json)
    assert provenance["dc_source"] == "play.d20_tests/typical_dcs#hard"
    assert provenance["operation"] == "difficulty_check"


@pytest.mark.parametrize(
    "selection",
    [
        {"ability": "dexterity", "skill": "athletics", "difficulty": "easy"},
        {"ability": "strength", "difficulty": "trivial"},
        {"ability": "strength"},
        {"ability": "brawn", "difficulty": "easy"},
    ],
    ids=["skill-not-governed", "unknown-difficulty", "no-difficulty", "no-ability"],
)
def test_an_invalid_difficulty_selection_is_refused(selection: dict[str, str]) -> None:
    _refused(
        RefusalKind.INVALID_SELECTION,
        srd_character(),
        _op("difficulty_check", **selection),
    )


THIEVES = ("equipment.tools.thieves_tools", "thieves_tools")


def _holding(*targets: tuple[str, str]) -> tuple[ItemInstance, ...]:
    return tuple(
        dataclasses.replace(item(record), component_key=component)
        for record, component in targets
    )


def _rogue_with_tools() -> Dnd5eCharacterState:
    return _rogue(1).model_copy(
        update={
            "tool_proficiencies": (
                ToolGrant(
                    record_key=THIEVES[0],
                    component_key=THIEVES[1],
                    expertise=False,
                    source=ROGUE_TRAITS,
                ),
            )
        }
    )


def test_a_tool_check_uses_the_activitys_printed_dc_and_validated_proficiency() -> None:
    proposal = _op(
        "tool_check", check_identity="/".join(THIEVES), tool_activity="pick_a_lock"
    )
    character = srd_character(_rogue_with_tools(), items=_holding(THIEVES))
    record, _ = _resolve(character, 10, proposal=proposal)
    assert (record.dc, record.total) == (15, 14)  # 10 + Dex 14 (+2) + PB 2
    provenance = json.loads(record.modifiers_json)
    assert provenance["dc_source"] == f"{'/'.join(THIEVES)}#pick_a_lock"
    unproficient = srd_character(items=_holding(THIEVES))
    record, _ = _resolve(unproficient, 10, proposal=proposal)
    assert record.total == 12  # no proficiency: Dex only


@pytest.mark.parametrize(
    ("kind", "identity", "activity", "held"),
    [
        (RefusalKind.MISSING_STATE, "/".join(THIEVES), "pick_a_lock", False),
        (RefusalKind.INVALID_SELECTION, "/".join(THIEVES), "start_a_fire", True),
        (
            RefusalKind.MISSING_STATE,
            "equipment.tools.gaming_set/gaming_set",
            "win_the_game",
            True,
        ),
        (RefusalKind.INVALID_SELECTION, "equipment.armor/armor", "pick_a_lock", True),
    ],
    ids=["tool-not-held", "other-tools-activity", "kind-not-recorded", "not-a-tool"],
)
def test_an_unusable_tool_check_is_refused(
    kind: RefusalKind, identity: str, activity: str, held: bool
) -> None:
    record, _, component = identity.partition("/")
    character = srd_character(
        _rogue_with_tools(), items=_holding((record, component)) if held else ()
    )
    _refused(
        kind,
        character,
        _op("tool_check", check_identity=identity, tool_activity=activity),
    )


def test_initiative_is_a_dexterity_check_with_an_undetermined_outcome() -> None:
    record, dice = _resolve(srd_character(), 12, proposal=_op("initiative"))
    dice.roll.assert_called_once_with("1d20")
    assert (record.dc, record.total, record.outcome) == (None, 14, "undetermined")


def test_invisible_has_advantage_on_initiative_from_its_typed_fact() -> None:
    invisible = _condition(ConditionKind.INVISIBLE)
    character = srd_character(_state(conditions=(invisible,)))
    record, dice = _resolve(character, 5, 15, proposal=_op("initiative"))
    dice.roll.assert_called_once_with("2d20kh1")
    assert record.total == 17
    sources = json.loads(record.modifiers_json)["advantage_sources"]
    assert sources == ["glossary.invisible/surprise"]


def test_an_initiative_contributor_refuses() -> None:
    """Alert adds the Proficiency Bonus to Initiative; not executed here."""
    state = _state(
        feats=(
            FeatSelection(
                feat_record_key="feats.alert",
                source=GrantSource(
                    record_key="character_origins.criminal", component_key="feat"
                ),
            ),
        )
    )
    _refused(
        RefusalKind.UNSUPPORTED_CAPABILITY, srd_character(state), _op("initiative")
    )


def test_increases_apply_only_when_their_order_cannot_matter() -> None:
    """Caps make increases non-commuting: from 19, a +1 to 30 then a +2 to 20
    gives 20, the other order 21. Acquisition order is not recorded, so that
    refuses; increases that agree in every order apply."""
    with pytest.raises(AdjudicationRefusal) as caught:
        grants._order_independent(
            19, [(20, "asi", 2), (30, "boon", 1)], AbilityScore.STRENGTH
        )
    assert caught.value.kind is RefusalKind.MISSING_STATE
    assert (
        grants._order_independent(
            10, [(20, "asi", 2), (30, "boon", 1)], AbilityScore.STRENGTH
        )
        == 13
    )
    assert (
        grants._order_independent(
            19, [(20, "asi", 2), (20, "background", 1)], AbilityScore.STRENGTH
        )
        == 20
    )


# ---------------------------------------------------------------------------
# Earned feat entitlement (Codex feat-entitlement boundary audit)
# ---------------------------------------------------------------------------

WIZARD_ASI = GrantSource(
    record_key="classes.wizard.ability_score_improvement",
    component_key="ability_score_improvement",
)


def _wizard(level: int, *feats: FeatSelection, **update: object) -> Dnd5eCharacterState:
    base = _state(
        classes=(
            ClassLevel(class_record_key="classes.wizard", level=level, hit_die="d6"),
        ),
        level_history=("classes.wizard",) * level,
        **update,
    )
    return base.model_copy(update={"feats": (*(base.feats or ()), *feats)})


def test_a_feat_without_typed_repeatability_cannot_be_counted_twice() -> None:
    """Two Grappler selections from two earned ASI gains: Grappler states no
    Repeatable rule, and unstated repeatability is not permission."""
    grappler = FeatSelection(feat_record_key="feats.grappler", source=WIZARD_ASI)
    increase = AbilityAdjustment(
        ability=AbilityScore.DEXTERITY,
        amount=1,
        source=GrantSource(
            record_key="feats.grappler", component_key="ability_score_increase"
        ),
    )
    state = _wizard(8, grappler, grappler, ability_adjustments=(increase,))
    with pytest.raises(AdjudicationRefusal) as caught:
        grants.ability_score(real_index(), state, AbilityScore.DEXTERITY)
    assert caught.value.kind is RefusalKind.MISSING_AUTHORITY


def test_a_feat_selection_must_be_the_feat_its_choice_selected() -> None:
    """The ASI feature's choice selected Grappler; a selection of Ability
    Score Improvement citing it is not that choice."""
    index = real_index()
    picked = choice(
        index,
        "asi-gain-4",
        WIZARD_ASI.record_key,
        WIZARD_ASI.component_key or "",
        RecordChoice(record_key="feats.grappler"),
    )
    cited = FeatSelection(
        feat_record_key=ASI[0],
        source=WIZARD_ASI.model_copy(update={"choice_id": "asi-gain-4"}),
    )
    state = _wizard(4, cited)
    state = state.model_copy(update={"choices": (*(state.choices or ()), picked)})
    with pytest.raises(AdjudicationRefusal) as caught:
        grants.ability_score(
            real_index(),
            _with(
                state,
                ability_adjustments=(
                    AbilityAdjustment(
                        ability=AbilityScore.STRENGTH,
                        amount=2,
                        source=GrantSource(record_key=ASI[0], component_key=ASI[1]),
                    ),
                ),
            ),
            AbilityScore.STRENGTH,
        )
    assert caught.value.kind is RefusalKind.INVALID_SELECTION


def test_the_epic_boon_alternative_admits_a_qualifying_feat_of_any_category() -> None:
    """Wizard 19's Epic Boon: an Epic Boon feat *or* any feat it qualifies for
    -- here the General Ability Score Improvement."""
    boon = FeatSelection(
        feat_record_key=ASI[0],
        source=GrantSource(
            record_key="classes.wizard.epic_boon", component_key="epic_boon"
        ),
    )
    increase = AbilityAdjustment(
        ability=AbilityScore.STRENGTH,
        amount=2,
        source=GrantSource(record_key=ASI[0], component_key=ASI[1]),
    )
    state = _wizard(19, boon, ability_adjustments=(increase,))
    assert grants.ability_score(real_index(), state, AbilityScore.STRENGTH)[0] == 10


def test_the_prompt_contract_lists_exactly_the_manifest_roster() -> None:
    """The GameMaster is told the roster the engine runs (prompt contract,
    authority level 4): every manifest operation and selection field is
    described, and nothing else is offered."""
    from afterworlds.pipeline.rpg.caller import PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC
    from afterworlds.pipeline.rpg.service import load_adjudication_prompt

    prompt = load_adjudication_prompt()
    for operation in MANIFEST:
        assert f"`{operation.value}`" in prompt, operation
    item = PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC["input_schema"]["properties"][
        "rolls"
    ]["items"]
    for field in item["properties"]:
        assert f"`{field}`" in prompt, field
    assert item["properties"]["operation"]["enum"] == [o.value for o in Operation]
