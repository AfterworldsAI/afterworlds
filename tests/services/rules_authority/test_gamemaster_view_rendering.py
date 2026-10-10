"""``render_gamemaster_view`` — the stable-prefix text of a rule slice.

Final CRD Issue 5d cutover. The production rule slice states its authority as
this rendering, so every element of a GameMaster component must reach the text
exactly, in the view's own order: the binding; handling and reasons; an
override-supplied component; applicability and recurrence; source prose,
an absent bound passage (never a substitute), option-scoped prose and authored
prose with its supplying override; facts with their own qualifiers and
suppliers; options; and the ordered applied overrides.
"""

from __future__ import annotations

import json
from uuid import UUID

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.projection import (
    applicability_payload,
    recurrence_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Phase,
    RecordKind,
    Recurrence,
    RecurrenceBoundary,
    fact_payload,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.application import (
    AppliedOverride,
    AuthoredProse,
    EffectiveFact,
    EffectiveFactQualifier,
    EffectiveOption,
    SourceProse,
)
from afterworlds.services.rules_authority.views import (
    GameMasterAuthorityView,
    GameMasterComponent,
    render_gamemaster_view,
)
from tests.services.rules_authority.conftest import (
    CHECK_FACT,
    DESCRIPTOR_COMPONENT_TARGET,
    DESCRIPTOR_FACT,
)

_BINDING = RulesPackageBinding(
    package_uuid=UUID("11111111-1111-5111-8111-111111111111"),
    release_version="5.2.1-render",
    mechanical_projection_uuid=UUID("22222222-2222-5222-8222-222222222222"),
    override_set_uuid=UUID("33333333-3333-5333-8333-333333333333"),
)
_WHEN = Applicability(kind=ApplicabilityKind.PHASE, phase=next(iter(Phase)))
_RECURS = Recurrence(boundary=RecurrenceBoundary.START_OF_TURN)


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _view() -> GameMasterAuthorityView:
    qualified = EffectiveFact(
        fact_key="fact-qualified",
        fact=DESCRIPTOR_FACT,
        qualifier=EffectiveFactQualifier(applies_when=_WHEN),
    )
    supplied = EffectiveFact(
        fact_key="fact-supplied",
        fact=CHECK_FACT,
        supplied_by_override_id="ov-fact",
        supplied_by_origin=OverrideOriginEnum.PACKAGE_PATCH,
    )
    rich = GameMasterComponent(
        record_key="spell:wish",
        record_kind=RecordKind.SPELL,
        component_key="open-ended-clause",
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_outcome",
        prose_retention_reason_code="no_identified_structured_use",
        governing_prose=(
            SourceProse(
                chunk_id="chunk-a",
                span_id="span-a",
                char_start=0,
                char_end=5,
                text="Exact",
            ),
            SourceProse(
                chunk_id="chunk-gone",
                span_id="span-gone",
                char_start=0,
                char_end=5,
                text=None,
                option_key="arm",
            ),
            SourceProse(
                chunk_id="chunk-b",
                span_id="span-b",
                char_start=0,
                char_end=6,
                text="Scoped",
                option_key="arm",
            ),
            AuthoredProse(
                text="House addendum.",
                supplied_by_override_id="ov-prose",
                supplied_by_origin=OverrideOriginEnum.HOUSE_RULE,
            ),
        ),
        structured_context=(qualified, supplied),
        span_ids=("span-a",),
        supplied_by_override_id="ov-component",
        options=(
            EffectiveOption(semantic_key="arm", facts=(qualified,), applies_when=_WHEN),
            EffectiveOption(semantic_key="other-arm", facts=()),
        ),
        applies_when=_WHEN,
        recurs=_RECURS,
    )
    plain = GameMasterComponent(
        record_key="spell:wish",
        record_kind=RecordKind.SPELL,
        component_key="descriptor",
        handling=ComponentHandling.STRUCTURED,
        irreducibility_reason_code=None,
        prose_retention_reason_code=None,
        governing_prose=(),
        structured_context=(),
        span_ids=(),
        supplied_by_override_id=None,
    )
    applied = tuple(
        AppliedOverride(
            override_id=override_id,
            origin=OverrideOriginEnum.HOUSE_RULE,
            target=DESCRIPTOR_COMPONENT_TARGET,
            operation=OverrideOperationEnum.DISABLE,
            precedence=order,
            apply_order=order,
            is_enabled=True,
            payload={"patch": "disable"},
            applied=was_applied,
        )
        for order, (override_id, was_applied) in enumerate(
            (("ov-applied", True), ("ov-reached", False))
        )
    )
    return GameMasterAuthorityView(
        binding=_BINDING, components=(rich, plain), applied_overrides=applied
    )


def test_every_element_of_the_view_reaches_the_text_in_order() -> None:
    text = render_gamemaster_view(_view())
    when = _canonical(applicability_payload(_WHEN))
    lines = text.split("\n")
    assert lines[:2] == [
        "## Rules authority",
        f"Binding: package {_BINDING.package_uuid}; release 5.2.1-render; "
        f"projection {_BINDING.mechanical_projection_uuid}; "
        f"override set {_BINDING.override_set_uuid}",
    ]
    expected_in_order = [
        "### spell:wish / open-ended-clause",
        "Kind: spell; handling: mixed",
        "Judgement reason: open_ended_outcome",
        "Prose retained: no_identified_structured_use",
        "Supplied by override ov-component",
        f"Applies when: {when}",
        f"Recurs: {_canonical(recurrence_payload(_RECURS))}",
        "Exact",
        "[governing passage absent: chunk chunk-gone, span span-gone] [option arm]",
        "Scoped [option arm]",
        "House addendum. [authored: override ov-prose (house_rule)]",
        f"Fact fact-qualified: {_canonical(fact_payload(DESCRIPTOR_FACT))} when {when}",
        f"Fact fact-supplied: {_canonical(fact_payload(CHECK_FACT))} "
        "[override ov-fact (package_patch)]",
        f"Option arm when {when}",
        f"  Fact fact-qualified: {_canonical(fact_payload(DESCRIPTOR_FACT))} "
        f"when {when}",
        "Option other-arm",
        "### spell:wish / descriptor",
        "Kind: spell; handling: structured",
        "Applied overrides, in order:",
        "- ov-applied (house_rule; disable; applied)",
        "- ov-reached (house_rule; disable; not applied)",
    ]
    positions = [lines.index(line) for line in expected_in_order]
    assert positions == sorted(positions)
    # The structured component states no reason it does not have.
    plain = lines[lines.index("### spell:wish / descriptor") :]
    assert not any(line.startswith("Judgement reason") for line in plain)


def test_the_rendering_is_deterministic() -> None:
    assert render_gamemaster_view(_view()) == render_gamemaster_view(_view())
