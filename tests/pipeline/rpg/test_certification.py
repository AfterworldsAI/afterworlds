"""CRD Issue 15c — certification scope (AC2): an operation's pinned shared
procedure covers only what it reads, and each creature an operation reads is
certified per subject against its own binding's template."""

from __future__ import annotations

import dataclasses
import json
from functools import cache
from typing import Any
from uuid import UUID, uuid4

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.capability import (
    CERTIFIED_RELEASE,
    MANIFEST,
    AdjudicationRefusal,
    CapabilityStatus,
    Operation,
    RefusalKind,
    certify,
    certify_template,
    governing_fingerprint,
)
from afterworlds.services.dnd5e_state.turn import TurnCreature
from tests.pipeline.rpg.test_bounded_checks import _with_component
from tests.pipeline.rpg.test_creature_attacks import (
    _bite,
    _medium_wizard,
    _resolve,
    _subjects,
)
from tests.pipeline.rpg.test_weapon_attacks import (
    CLUB,
    _attacker,
    _creature,
    _dice,
    _proposal,
    _run,
)
from tests.services.dnd5e_state.builders import index_for, real_index

WOLF = "animals.wolf"
#: The accepted CRD Issue 15b C9 successor's projection (recorded 2026-10-14)
#: and the C8 successor it superseded by digest.
C9_PROJECTION = "3703faf5-8b51-5c3f-b28c-b378b005f7bf"
C8_PROJECTION = "e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42"
C8_FILE = "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
C8_ORACLE_IDENTITY = "70646cd987dcf75adc7b57b6271e38c6ca8cc9b508584dac89c5acefafa3e8d9"  # noqa: E501  # pragma: allowlist secret


def _with_index(creature: TurnCreature, index: Any) -> TurnCreature:
    return dataclasses.replace(creature, index=index)


def test_an_unrelated_fixed_dc_override_leaves_other_operations_certified() -> None:
    climb = _with_component(
        real_index(),
        "glossary.climbing",
        "difficult_climb",
        supplied_by_override_id="house-rule",
    )
    base = real_index()
    assert governing_fingerprint(climb, Operation.FIXED_DC_CHECK) != (
        governing_fingerprint(base, Operation.FIXED_DC_CHECK)
    )
    for operation in (Operation.WEAPON_ATTACK, Operation.CREATURE_ATTACK):
        assert governing_fingerprint(climb, operation) == governing_fingerprint(
            base, operation
        )


@pytest.mark.parametrize("how", ["supplied", "suppressed"])
def test_an_overridden_creature_template_is_not_certified(how: str) -> None:
    index = real_index()
    if how == "supplied":
        changed = _with_component(
            index, WOLF, "wolf", supplied_by_override_id="house-rule"
        )
    else:  # a suppression leaves no supplied_by marker on what remains
        changed = dataclasses.replace(index, overridden=frozenset({WOLF}))
    wolf = _with_index(_creature(hp=40), changed)
    wizard = _medium_wizard()
    for proposal, actor in (
        (_bite(wolf, wizard), wizard),  # the template's own attack
        (_proposal(wolf), _attacker(CLUB)),  # its AC and defenses as a target
    ):
        with pytest.raises(AdjudicationRefusal) as caught:
            D20RulesSystemAdapter().require_supported(proposal, actor, _subjects(wolf))
        assert caught.value.kind is RefusalKind.INCOMPATIBLE_CERTIFICATION


@cache
def _superseded_c8_index() -> Any:
    """The superseded C8 successor, loaded from its committed file and bound
    under the projection it derives (not a hand-made identity)."""
    inputs = load_accepted_inputs(COMMITTED_ORACLE_DIR / C8_FILE)
    assert oracle_identity(inputs.oracle) == C8_ORACLE_IDENTITY
    return index_for(inputs)


EXECUTABLE = [
    op for op, cap in MANIFEST.items() if cap.status is CapabilityStatus.EXECUTABLE
]


def test_every_executable_operation_certifies_on_the_selected_c9_successor() -> None:
    index = real_index()
    assert len(EXECUTABLE) == 14
    assert (
        index.binding.package_uuid,
        index.binding.release_version,
        index.binding.mechanical_projection_uuid,
    ) == CERTIFIED_RELEASE
    assert CERTIFIED_RELEASE[2] == UUID(C9_PROJECTION)
    for operation in EXECUTABLE:
        certificate = certify(operation, index)
        assert certificate.projection_uuid == UUID(C9_PROJECTION)
        assert certificate.fingerprint == MANIFEST[operation].fingerprint


@pytest.mark.parametrize("operation", EXECUTABLE, ids=lambda op: op.value)
def test_the_superseded_c8_successor_is_refused(operation: Operation) -> None:
    index = _superseded_c8_index()
    assert index.binding.mechanical_projection_uuid == UUID(C8_PROJECTION)
    # C9 typed no governing component: only the certified release differs.
    assert governing_fingerprint(index, operation) == (MANIFEST[operation].fingerprint)
    with pytest.raises(AdjudicationRefusal) as caught:
        certify(operation, index)
    assert caught.value.kind is RefusalKind.INCOMPATIBLE_CERTIFICATION


def test_a_c8_template_certificate_is_stale_on_c9() -> None:
    """A creature profile gained its Skills entry, so the template digest a C8
    certificate recorded differs; one C9 left untouched keeps its digest."""
    old, new = _superseded_c8_index(), real_index()
    assert certify_template(old, WOLF) != certify_template(new, WOLF)
    untouched = "monsters.parts_of_a_stat_block"
    assert certify_template(old, untouched) == certify_template(new, untouched)


def test_an_unchanged_template_is_certified_across_bindings() -> None:
    # Another override set that touches nothing the attack reads.
    other = real_index().binding.model_copy(update={"override_set_uuid": uuid4()})
    wolf = _with_index(
        _creature(hp=40), dataclasses.replace(real_index(), binding=other)
    )
    wizard = _medium_wizard()
    record = _resolve(_bite(wolf, wizard), wizard, _subjects(wolf), _dice((18,), (3,)))
    templates = json.loads(record.modifiers_json)["templates"]
    assert list(templates) == [f"creature:{wolf.subject_id}"]
    # A weapon attack against it records the target's template too.
    record = _run(_attacker(CLUB), wolf, _proposal(wolf), _dice((15,), (3,)))
    assert json.loads(record.modifiers_json)["templates"]
