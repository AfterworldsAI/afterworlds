"""Schema 21 ``creature_type`` and ``summoned_creature_type`` (CRD Issue 15c C8).

The intrinsic invariants (manifested, inside the schema hash) and the
relational Find Familiar rule: each named form is a creature profile of the
draft whose own type is the source's ``instead_of``. Shaped on raw candidate
C8's Find Familiar fact and the animal profiles it names.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    ComponentReference,
    CreatureSize,
    CreatureSizeFact,
    CreatureTypeFact,
    CreatureTypeKind,
    FactQualifier,
    MalformedFactPayloadError,
    Phase,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    SummonedCreatureTypeFact,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
)
from afterworlds.ingestion.mechanical.validation import (
    _validate_summoned_creature_types,
    validate_representation,
)
from afterworlds.models.dnd5e_vocabulary import CreatureType
from tests.ingestion.mechanical.conftest import bound_corpus, build_ledger

T = CreatureTypeKind


def test_the_vocabulary_is_the_state_vocabulary() -> None:
    """Declared inside the schema hash, pinned equal to the 2b state enum."""
    assert [m.value for m in CreatureTypeKind] == [m.value for m in CreatureType]
    assert len(CreatureTypeKind) == 14


def _type(payload: dict[str, Any]) -> list[str] | None:
    """The fact's intrinsic findings, or ``None`` when its payload is refused."""
    try:
        fact = fact_from_payload({"family": "creature_type", **payload})
    except MalformedFactPayloadError:
        return None
    return list(fact_invariant_violations(fact))


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "beast", "type_choice": []},
        {"type": None, "type_choice": ["celestial", "fey", "fiend"]},
    ],
)
def test_a_fixed_type_or_a_choice_is_admitted(payload: dict[str, Any]) -> None:
    assert _type(payload) == []


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"type": "beast", "type_choice": ["fey", "fiend"]}, id="both"),
        pytest.param({"type": None, "type_choice": []}, id="neither"),
        pytest.param({"type": None, "type_choice": ["fey"]}, id="single-choice"),
        pytest.param({"type": None, "type_choice": ["fey", "fey"]}, id="duplicate"),
        pytest.param({"type": None, "type_choice": ["fiend", "fey"]}, id="unsorted"),
    ],
)
def test_an_illegal_type_statement_is_refused(payload: dict[str, Any]) -> None:
    assert _type(payload), payload


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"type": "elf", "type_choice": []}, id="tag-not-type"),
        pytest.param({"type": "Beast", "type_choice": []}, id="case"),
        pytest.param({"type": None, "type_choice": ["fey", "elf"]}, id="choice"),
        pytest.param({"type": 3, "type_choice": []}, id="not-a-string"),
        pytest.param({"type": "beast"}, id="missing-field"),
    ],
)
def test_a_malformed_type_value_does_not_build(payload: dict[str, Any]) -> None:
    assert _type(payload) is None


def test_a_hand_built_non_vocabulary_value_is_refused() -> None:
    fact = CreatureTypeFact(type="beast", type_choice=())  # type: ignore[arg-type]
    assert fact_invariant_violations(fact)


def _ref(name: str) -> ComponentReference:
    return ComponentReference(record_key=f"animals.{name}", component_key=name)


def _familiar(**changes: Any) -> SummonedCreatureTypeFact:
    fields: dict[str, Any] = {
        "type_choice": (T.CELESTIAL, T.FEY, T.FIEND),
        "instead_of": T.BEAST,
        "forms": (_ref("bat"), _ref("cat")),
    }
    return SummonedCreatureTypeFact(**{**fields, **changes})


def test_the_c8_familiar_choice_is_admitted() -> None:
    assert fact_invariant_violations(_familiar()) == ()


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"type_choice": (T.FEY,)}, id="single-choice"),
        pytest.param({"type_choice": (T.FEY, T.FEY)}, id="duplicate-choice"),
        pytest.param({"type_choice": (T.FIEND, T.FEY)}, id="unsorted-choice"),
        pytest.param({"type_choice": (T.BEAST, T.FEY)}, id="offers-instead-of"),
        pytest.param({"forms": ()}, id="no-forms"),
        pytest.param({"forms": (_ref("bat"), _ref("bat"))}, id="duplicate-form"),
        pytest.param({"forms": (_ref("cat"), _ref("bat"))}, id="unsorted-forms"),
        pytest.param({"instead_of": "beast"}, id="instead-of-not-vocabulary"),
    ],
)
def test_an_illegal_source_choice_is_refused(changes: dict[str, Any]) -> None:
    assert fact_invariant_violations(_familiar(**changes))


# --- the relational rule ---------------------------------------------------


def _profile(name: str, *facts: object, sized: bool = True) -> ComponentDraft:
    size = (CreatureSizeFact(sizes=(CreatureSize.TINY,)),) if sized else ()
    return ComponentDraft(
        record_key=f"animals.{name}",
        semantic_key=name,
        handling=ComponentHandling.STRUCTURED,
        facts=(*size, *facts),  # type: ignore[arg-type]
    )


def _beast(name: str) -> ComponentDraft:
    return _profile(name, CreatureTypeFact(type=T.BEAST, type_choice=()))


SPELL = ComponentDraft(
    record_key="spells.find_familiar",
    semantic_key="note",
    handling=ComponentHandling.STRUCTURED,
    facts=(CreatureTypeFact(type=T.BEAST, type_choice=()),),
)


def _draft(source: SummonedCreatureTypeFact, *profiles: ComponentDraft) -> Any:
    effect = ComponentDraft(
        record_key="spells.find_familiar",
        semantic_key="effect",
        handling=ComponentHandling.STRUCTURED,
        facts=(source,),
    )
    components = (*profiles, effect, SPELL)
    keys = sorted({c.record_key for c in components})
    return RepresentationDraft(
        records=tuple(
            RecordDraft(
                semantic_key=k,
                kind=(
                    RecordKind.SPELL if k.startswith("spells.") else RecordKind.CREATURE
                ),
            )
            for k in keys
        ),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


def test_c8_shaped_forms_validate() -> None:
    assert (
        _validate_summoned_creature_types(
            _draft(_familiar(), _beast("bat"), _beast("cat"))
        )
        == []
    )


def test_an_unknown_form_is_refused() -> None:
    draft = _draft(_familiar(), _beast("bat"))
    (finding,) = _validate_summoned_creature_types(draft)
    assert "animals.cat/cat" in finding and "not a component of this draft" in finding


def test_a_form_that_is_not_a_creature_profile_is_refused() -> None:
    unsized = _profile(
        "cat", CreatureTypeFact(type=T.BEAST, type_choice=()), sized=False
    )
    (finding,) = _validate_summoned_creature_types(
        _draft(_familiar(), _beast("bat"), unsized)
    )
    assert "not a creature profile" in finding
    spell_form = _familiar(
        forms=(
            ComponentReference(record_key="spells.find_familiar", component_key="note"),
        )
    )
    (finding,) = _validate_summoned_creature_types(_draft(spell_form))
    assert "not a creature profile" in finding


@pytest.mark.parametrize(
    "cat",
    [
        pytest.param(
            _profile("cat", CreatureTypeFact(type=T.FEY, type_choice=())), id="fey"
        ),
        pytest.param(_profile("cat"), id="untyped"),
        pytest.param(
            _profile("cat", CreatureTypeFact(type=None, type_choice=(T.BEAST, T.FEY))),
            id="choice",
        ),
    ],
)
def test_a_form_whose_own_type_is_not_instead_of_is_refused(
    cat: ComponentDraft,
) -> None:
    (finding,) = _validate_summoned_creature_types(
        _draft(_familiar(), _beast("bat"), cat)
    )
    assert "animals.cat/cat" in finding and "not exactly beast" in finding


_WHILE_ACTIVE = Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE)
_TINY = CreatureSizeFact(sizes=(CreatureSize.TINY,))
_IS_BEAST = CreatureTypeFact(type=T.BEAST, type_choice=())


def _conditional_cat(case: str) -> ComponentDraft:
    if case == "option-arms":
        return ComponentDraft(
            record_key="animals.cat",
            semantic_key="cat",
            handling=ComponentHandling.STRUCTURED,
            options=(
                ComponentOption(semantic_key="a", facts=(_TINY, _IS_BEAST)),
                ComponentOption(
                    semantic_key="b",
                    facts=(CreatureSizeFact(sizes=(CreatureSize.SMALL,)),),
                ),
            ),
        )
    if case == "component-applies-when":
        return replace(_beast("cat"), applies_when=_WHILE_ACTIVE)
    qualified = _TINY if case == "qualified-size" else _IS_BEAST
    return replace(
        _beast("cat"),
        fact_qualifiers=(
            FactQualifier(fact_key=fact_key(qualified), applies_when=_WHILE_ACTIVE),
        ),
    )


@pytest.mark.parametrize(
    "case",
    ["option-arms", "component-applies-when", "qualified-type", "qualified-size"],
)
def test_conditional_profile_authority_is_not_a_fixed_form(case: str) -> None:
    """codex-c8-schema-code-review P2: a component reference selects no option
    or condition, so a size or type held conditionally never establishes the
    fixed ``instead_of`` form."""
    (finding,) = _validate_summoned_creature_types(
        _draft(_familiar(), _beast("bat"), _conditional_cat(case))
    )
    assert "animals.cat/cat" in finding and "no fixed profile" in finding


def test_refused_structure_is_never_read_relationally() -> None:
    """A refused form type is its own finding; a refused source is not read."""
    bad_cat = _profile("cat", CreatureTypeFact(type=T.FEY, type_choice=(T.FEY,)))
    assert (
        _validate_summoned_creature_types(_draft(_familiar(), _beast("bat"), bad_cat))
        == []
    )
    bad_source = _familiar(forms=(_ref("cat"), _ref("bat"), _ref("rat")))
    assert _validate_summoned_creature_types(_draft(bad_source, _beast("bat"))) == []


def test_the_rule_runs_inside_validate_representation() -> None:
    """Wired into the candidate validation path, not only callable."""

    def findings(draft: RepresentationDraft) -> list[str]:
        found = validate_representation(draft, build_ledger(), bound_corpus())
        return [f for f in found if "summoned_creature_type names" in f]

    assert findings(_draft(_familiar(), _beast("bat"), _beast("cat"))) == []
    assert findings(_draft(_familiar(), _beast("bat")))
