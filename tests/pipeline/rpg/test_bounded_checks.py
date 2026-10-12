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
    GrantSource,
    OriginSelection,
    SkillGrant,
)
from afterworlds.models.enums import ConditionVisibility, RollVisibility
from afterworlds.models.rpg import DiceResult, RollProposal
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.pipeline.rpg import checks
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
from tests.rpg_characters import srd_character
from tests.services.dnd5e_state.builders import complete_character, real_index

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


def test_proficiency_comes_from_the_typed_band_for_total_level() -> None:
    athletics = SkillGrant(
        skill=Skill.ATHLETICS,
        expertise=False,
        source=GrantSource(record_key="classes.wizard"),
    )
    character = srd_character(_state(skill_proficiencies=(athletics,)))
    record, _ = _resolve(character, 10)
    assert record.total == 11  # 10 - 1 + PB 2 (levels 1-4)
    breakdown = json.loads(record.modifiers_json)["breakdown"]
    assert breakdown == {"strength_modifier": -1, "proficiency_bonus": 2}


def test_expertise_doubles_the_proficiency_bonus() -> None:
    expert = SkillGrant(
        skill=Skill.ATHLETICS,
        expertise=True,
        source=GrantSource(record_key="classes.wizard"),
    )
    state = _state(
        skill_proficiencies=(expert,),
        classes=(ClassLevel(class_record_key="classes.wizard", level=5, hit_die="d6"),),
        level_history=("classes.wizard",) * 5,
    )
    record, _ = _resolve(srd_character(state), 10)
    assert record.total == 15  # 10 - 1 + 2 x PB 3 (levels 5-8)
    assert json.loads(record.modifiers_json)["breakdown"]["expertise"] == 6


def test_adjustments_are_totalled_and_capped() -> None:
    raise_str = AbilityAdjustment(
        ability=AbilityScore.STRENGTH,
        amount=4,
        source=GrantSource(record_key="feats.ability_score_improvement"),
    )
    record, _ = _resolve(srd_character(_state(ability_adjustments=(raise_str,))), 10)
    assert record.total == 11  # Str 8 + 4 = 12 (+1)

    capped = raise_str.model_copy(update={"amount": 30, "maximum": None})
    record, _ = _resolve(srd_character(_state(ability_adjustments=(capped,))), 10)
    assert record.total == 15  # capped at 20 (+5)


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
    expert = SkillGrant(
        skill=Skill.ATHLETICS, expertise=True, source=GrantSource(record_key="x.y")
    )
    state = _state(
        skill_proficiencies=(expert,),
        ability_scores=_state().ability_scores.model_copy(update={"strength": 20}),
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
        "manifest_version": "15c-manifest-1",
        "adapter_version": "15c-d20-1",
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
def test_held_operations_refuse_as_missing_authority(operation: Operation) -> None:
    refusal = _refused(
        RefusalKind.MISSING_AUTHORITY,
        srd_character(),
        _proposal(operation=operation.value),
    )
    assert "candidate C1" in refusal.detail


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
