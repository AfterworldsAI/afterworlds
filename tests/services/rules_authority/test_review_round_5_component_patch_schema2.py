"""Complete component patches carry schema-2 shape — PR #155, round 5.

Codex review round 5, finding 1. Schema 2 made ``applies_when`` and ``options``
part of a component's authoritative shape, but ``ComponentBody`` held neither:
``_build_component_body()`` rejected both keys, ``_component_body_payload()``
omitted them, and ``_component_from_body()`` always built an
``EffectiveComponent`` with their empty defaults. So no complete component patch
— ``APPEND_COMPONENT``, ``REPLACE_COMPONENT``, or a component inside
``REPLACE_RECORD`` — could author a conditioned or choice-bearing component, and
replacing an existing one silently discarded its qualifier and option structure.

Two properties are load-bearing and are each proven here rather than argued:

* **The rules are stated once.** Option-set validity now lives in
  ``representation.option_set_violations`` and is called by both the build-time
  validator and the patch parser, so a patch cannot admit a shape the corpus
  would refuse. Applicability is read through the same two gates the
  accepted-input and persisted-state loaders use.
* **Legacy bytes are unchanged.** The new fields are omitted from the canonical
  payload when they hold their legacy defaults, so an unconditional direct-fact
  component patch keeps exactly the payload and override-set identity it always
  had. The literals below were captured on ``22872cd`` before any edit.
"""

from __future__ import annotations

import json
from uuid import UUID, uuid5

import pytest
from sqlalchemy import select

from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    applicability_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentDraft,
    ComponentHandling,
    MovementAmount,
    MovementCostFact,
    MovementCostKind,
    MovementMode,
    MovementPermissionFact,
    ParticipantRole,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RoundingRule,
    TrackedQuantity,
    fact_key,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.rules_authority import MechanicalOverrideORM
from afterworlds.services.rules_authority import (
    collect_current_override_state,
    load_override_set_version,
    retain_override_set,
)
from afterworlds.services.rules_authority.application import apply_override_set
from afterworlds.services.rules_authority.override_set import (
    EMPTY_OVERRIDE_SET_UUID,
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    override_set_identity,
)
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    patch_from_payload,
    patch_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from afterworlds.services.rules_authority.views import (
    build_gamemaster_view,
    build_typed_view,
)
from tests.services.rules_authority.conftest import (
    DESCRIPTOR_COMPONENT_TARGET,
    DESCRIPTOR_KEY,
    NOW,
    SPELL_KEY,
    RuntimeFixture,
    append_component_payload,
    author_override,
    replace_component_payload,
    replace_record_payload,
)

_SCOPE_UUID = uuid5(UUID("2f2b6d9c-0e2a-5f31-9a44-6b0c1d2e3f40"), "component-patch-s2")

CRAWL = MovementPermissionFact(mode=MovementMode.CRAWL)
STAND = MovementCostFact(
    kind=MovementCostKind.EXPENDITURE,
    amount=MovementAmount.HALF_SPEED,
    payer=ParticipantRole.SUBJECT,
    rounding=RoundingRule.DOWN,
)
SWIM = MovementPermissionFact(mode=MovementMode.SWIM)

NOT_SPEED_ZERO = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    negated=True,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)


def qualifier_payload() -> dict[str, object]:
    built = applicability_payload(NOT_SPEED_ZERO)
    assert built is not None
    return built


def option(key: str, facts: tuple[object, ...], qualified: bool = False):  # type: ignore[no-untyped-def]
    body: dict[str, object] = {
        "semantic_key": key,
        "facts": [fact_payload(f) for f in facts],
    }
    if qualified:
        body["applies_when"] = qualifier_payload()
    return body


def choice_component(keyed: bool = False, **extra: object) -> dict[str, object]:
    body: dict[str, object] = {"handling": "structured", "facts": []}
    if keyed:
        body["semantic_key"] = "movement-choice"
    body["options"] = [
        option("crawl", (CRAWL,)),
        option("stand", (STAND,), qualified=True),
    ]
    body.update(extra)
    return body


# ---------------------------------------------------------------------------
# 1. Canonical parse/payload round trips across all three families
# ---------------------------------------------------------------------------


def _round_trip(raw: dict[str, object], operation, target):  # type: ignore[no-untyped-def]
    once = patch_payload(patch_from_payload(raw, operation=operation, target=target))
    twice = patch_payload(patch_from_payload(once, operation=operation, target=target))
    assert once == twice, "emitter and parser disagree"
    return once


APPEND_TARGET = MechanicalTarget(kind=MechanicalTargetKind.RECORD, record_key=SPELL_KEY)


def test_append_component_carries_qualifier_and_options() -> None:
    payload = _round_trip(
        {
            "patch": "append_component",
            "component": choice_component(keyed=True, applies_when=qualifier_payload()),
        },
        OverrideOperationEnum.APPEND,
        APPEND_TARGET,
    )
    body = payload["component"]
    assert isinstance(body, dict)
    assert body["applies_when"] == qualifier_payload()
    assert [o["semantic_key"] for o in body["options"]] == ["crawl", "stand"]
    assert body["options"][1]["applies_when"] == qualifier_payload()


def test_replace_component_carries_qualifier_and_options() -> None:
    payload = _round_trip(
        {
            "patch": "replace_component",
            "component": choice_component(applies_when=qualifier_payload()),
        },
        OverrideOperationEnum.REPLACE,
        DESCRIPTOR_COMPONENT_TARGET,
    )
    body = payload["component"]
    assert isinstance(body, dict)
    assert body["applies_when"] == qualifier_payload()
    assert len(body["options"]) == 2


def test_replace_record_carries_them_on_every_component() -> None:
    payload = _round_trip(
        {
            "patch": "replace_record",
            "record_kind": "spell",
            "components": [
                choice_component(keyed=True, applies_when=qualifier_payload())
            ],
        },
        OverrideOperationEnum.REPLACE,
        APPEND_TARGET,
    )
    (body,) = payload["components"]
    assert body["applies_when"] == qualifier_payload()
    assert len(body["options"]) == 2


# ---------------------------------------------------------------------------
# 2. Legacy payload bytes and identities are unmoved
# ---------------------------------------------------------------------------

#: Captured on `22872cd` before any round-5 edit, by running the pre-change
#: emitter. Recomputing them with post-change code would make the claim
#: unfalsifiable.
LEGACY = {
    "REPLACE_COMPONENT": "e71ba996-4bc3-5ed3-8f2f-10ac83009a8f",
    "APPEND_COMPONENT": "95b4f149-8ce4-5a4b-98be-209c924907e2",
    "REPLACE_RECORD": "eaf62f89-5582-5fdf-ba74-8e94918f5bb3",
}


def _identity(payload: dict[str, object], operation, target) -> str:  # type: ignore[no-untyped-def]
    entry = EffectiveOverrideEntry(
        override_id="ov-1",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=target,
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=patch_payload(
            patch_from_payload(payload, operation=operation, target=target)
        ),
    )
    return override_set_identity((entry,))


@pytest.mark.parametrize(
    ("label", "raw", "operation", "target"),
    [
        (
            "REPLACE_COMPONENT",
            replace_component_payload(),
            OverrideOperationEnum.REPLACE,
            DESCRIPTOR_COMPONENT_TARGET,
        ),
        (
            "APPEND_COMPONENT",
            append_component_payload(),
            OverrideOperationEnum.APPEND,
            APPEND_TARGET,
        ),
        (
            "REPLACE_RECORD",
            replace_record_payload(),
            OverrideOperationEnum.REPLACE,
            APPEND_TARGET,
        ),
    ],
)
def test_legacy_component_patch_identity_is_unmoved(
    label: str, raw: dict[str, object], operation, target
) -> None:  # type: ignore[no-untyped-def]
    assert _identity(raw, operation, target) == LEGACY[label]


def test_a_legacy_component_payload_gains_no_new_keys() -> None:
    payload = patch_payload(
        patch_from_payload(
            replace_component_payload(),
            operation=OverrideOperationEnum.REPLACE,
            target=DESCRIPTOR_COMPONENT_TARGET,
        )
    )
    body = payload["component"]
    assert isinstance(body, dict)
    assert set(body) == {"handling", "facts", "authored_prose"}


# ---------------------------------------------------------------------------
# 3. Alternate spellings cannot mint two identities for one meaning
# ---------------------------------------------------------------------------


def _payload_of(component: dict[str, object]) -> str:
    return json.dumps(
        patch_payload(
            patch_from_payload(
                {"patch": "replace_component", "component": component},
                operation=OverrideOperationEnum.REPLACE,
                target=DESCRIPTOR_COMPONENT_TARGET,
            )
        ),
        sort_keys=True,
    )


DIRECT = {"handling": "structured", "facts": [fact_payload(SWIM)]}


@pytest.mark.parametrize(
    ("label", "left", "right"),
    [
        (
            "absent vs explicit-null applies_when",
            DIRECT,
            {**DIRECT, "applies_when": None},
        ),
        ("absent vs empty options", DIRECT, {**DIRECT, "options": []}),
        (
            "options in reversed order",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("crawl", (CRAWL,)), option("stand", (STAND,))],
            },
            {
                "handling": "structured",
                "facts": [],
                "options": [option("stand", (STAND,)), option("crawl", (CRAWL,))],
            },
        ),
        (
            "option facts in reversed order",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (CRAWL, SWIM)), option("b", (STAND,))],
            },
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (SWIM, CRAWL)), option("b", (STAND,))],
            },
        ),
    ],
)
def test_one_meaning_canonicalizes_to_one_payload(
    label: str, left: dict[str, object], right: dict[str, object]
) -> None:
    assert _payload_of(left) == _payload_of(right)


def test_a_genuine_difference_still_moves_the_payload() -> None:
    """The dedup above must not have flattened real content."""
    assert _payload_of(DIRECT) != _payload_of(
        {**DIRECT, "applies_when": qualifier_payload()}
    )
    assert _payload_of(choice_component()) != _payload_of(
        choice_component(applies_when=qualifier_payload())
    )


# ---------------------------------------------------------------------------
# 4. Malformed shapes fail closed, with the representation's own rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "component", "expected"),
    [
        (
            "singleton choice",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("only", (CRAWL,))],
            },
            "choice of one",
        ),
        (
            "duplicate option keys",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("same", (CRAWL,)), option("same", (STAND,))],
            },
            "duplicate option key",
        ),
        (
            "two options stating the same facts",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (CRAWL,)), option("b", (CRAWL,))],
            },
            "same typed facts",
        ),
        (
            "an option with no facts",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (CRAWL,)), option("empty", ())],
            },
            "states no typed facts",
        ),
        (
            "a blank option key",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (CRAWL,)), option("   ", (STAND,))],
            },
            "non-blank string",
        ),
        (
            "direct facts alongside options",
            {
                "handling": "structured",
                "facts": [fact_payload(SWIM)],
                "options": [option("a", (CRAWL,)), option("b", (STAND,))],
            },
            "conjunction or a choice",
        ),
        (
            "prose_bound handling with options",
            {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "x",
                "options": [option("a", (CRAWL,)), option("b", (STAND,))],
            },
            "prose_bound handling with typed facts",
        ),
        (
            "structured handling with neither facts nor options",
            {"handling": "structured", "facts": []},
            "no facts",
        ),
        (
            "a malformed applicability key",
            {**DIRECT, "applies_when": {**qualifier_payload(), "extra": 1}},
            "unexpected",
        ),
        (
            "a missing applicability key",
            {
                **DIRECT,
                "applies_when": {
                    k: v for k, v in qualifier_payload().items() if k != "phase"
                },
            },
            "missing",
        ),
        (
            "a coerced applicability boolean",
            {**DIRECT, "applies_when": {**qualifier_payload(), "negated": "false"}},
            "not a boolean",
        ),
        (
            "an option-level malformed applicability",
            {
                "handling": "structured",
                "facts": [],
                "options": [
                    option("a", (CRAWL,)),
                    {
                        **option("b", (STAND,)),
                        "applies_when": {**qualifier_payload(), "negated": "false"},
                    },
                ],
            },
            "not a boolean",
        ),
        (
            "an option with an unexpected key",
            {
                "handling": "structured",
                "facts": [],
                "options": [
                    option("a", (CRAWL,)),
                    {**option("b", (STAND,)), "junk": 1},
                ],
            },
            "carries extra",
        ),
        (
            "an option repeating one fact",
            {
                "handling": "structured",
                "facts": [],
                "options": [option("a", (CRAWL, CRAWL)), option("b", (STAND,))],
            },
            "repeats the same typed fact",
        ),
        (
            "options that are not a list",
            {"handling": "structured", "facts": [], "options": "crawl"},
            "options must be a list",
        ),
    ],
)
def test_a_malformed_component_patch_fails_closed(
    label: str, component: dict[str, object], expected: str
) -> None:
    with pytest.raises(InvalidPatchError, match=expected):
        patch_from_payload(
            {"patch": "replace_component", "component": component},
            operation=OverrideOperationEnum.REPLACE,
            target=DESCRIPTOR_COMPONENT_TARGET,
        )


def test_an_honest_option_bearing_component_is_accepted() -> None:
    """The negative controls above must not be rejecting everything."""
    patch = patch_from_payload(
        {"patch": "replace_component", "component": choice_component()},
        operation=OverrideOperationEnum.REPLACE,
        target=DESCRIPTOR_COMPONENT_TARGET,
    )
    assert len(patch.body.options) == 2  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# 5. Application, views, and mutual exclusivity
# ---------------------------------------------------------------------------

_BINDING = ReleaseBinding(
    package_uuid=str(_SCOPE_UUID),
    release_version="5.2.1-component-patch.fixture",
    authoritative_source_hash="a" * 64,
    transform_config_hash="b" * 64,
    bundle_root_hash="c" * 64,
    persisted_corpus_digest="d" * 64,
)
_CLASSIFICATION = ClassificationLedger(
    package_uuid=_BINDING.package_uuid,
    release_version=_BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=(),
    batches=(),
    acceptances=(),
)
_PACKAGE_BINDING = RulesPackageBinding(
    package_uuid=_SCOPE_UUID,
    release_version=_BINDING.release_version,
    mechanical_projection_uuid=_SCOPE_UUID,
    override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
)


def _candidate() -> ProjectionCandidate:
    """A base component that already carries a qualifier and options.

    Replacing it is what proves omission *removes* rather than inherits.
    """
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=SPELL_KEY, kind=RecordKind.SPELL),),
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=DESCRIPTOR_KEY,
                handling=ComponentHandling.STRUCTURED,
                applies_when=NOT_SPEED_ZERO,
                options=(),
                facts=(SWIM,),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    return ProjectionCandidate(
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
        binding=_BINDING,
        classification=_CLASSIFICATION,
        representation=draft,
    )


def _resolve(raw: dict[str, object]):  # type: ignore[no-untyped-def]
    entry = EffectiveOverrideEntry(
        override_id="ov-1",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=patch_payload(
            patch_from_payload(
                raw,
                operation=OverrideOperationEnum.REPLACE,
                target=DESCRIPTOR_COMPONENT_TARGET,
            )
        ),
    )
    state = EffectiveOverrideSet(
        package_uuid=_BINDING.package_uuid,
        release_version=_BINDING.release_version,
        entries=(entry,),
    )
    return apply_override_set(_candidate(), state, _PACKAGE_BINDING)


def _component(view):  # type: ignore[no-untyped-def]
    (record,) = view.records
    (component,) = record.components
    return component


def test_a_replacement_installs_its_qualifier_and_options() -> None:
    component = _component(
        _resolve(
            {
                "patch": "replace_component",
                "component": choice_component(applies_when=qualifier_payload()),
            }
        )
    )
    assert component.applies_when == NOT_SPEED_ZERO
    assert [o.semantic_key for o in component.options] == ["crawl", "stand"]
    stand = next(o for o in component.options if o.semantic_key == "stand")
    assert stand.applies_when == NOT_SPEED_ZERO
    assert component.facts == ()


def test_every_override_supplied_option_fact_names_its_override() -> None:
    component = _component(
        _resolve({"patch": "replace_component", "component": choice_component()})
    )
    for opt in component.options:
        for fact in opt.facts:
            assert fact.supplied_by_override_id == "ov-1"
            assert fact.supplied_by_origin is OverrideOriginEnum.HOUSE_RULE
            assert fact.option_key == opt.semantic_key
            assert fact.span_ids == ()


def test_replacement_is_complete_and_removes_omitted_fields() -> None:
    """The base carries a qualifier; a replacement that omits one must not
    inherit it. Component replacement is complete by contract."""
    component = _component(
        _resolve({"patch": "replace_component", "component": DIRECT})
    )
    assert component.applies_when is None
    assert component.options == ()
    assert [f.fact_key for f in component.facts] == [fact_key(SWIM)]


def test_the_gamemaster_view_keeps_the_options_mutually_exclusive() -> None:
    """Flattening would publish both arms as jointly applicable."""
    view = build_gamemaster_view(
        _resolve(
            {
                "patch": "replace_component",
                "component": choice_component(applies_when=qualifier_payload()),
            }
        ),
        {},
    )
    (component,) = view.components
    assert component.applies_when == NOT_SPEED_ZERO
    assert component.structured_context == ()
    scopes = {o.semantic_key: [f.fact_key for f in o.facts] for o in component.options}
    assert scopes == {"crawl": [fact_key(CRAWL)], "stand": [fact_key(STAND)]}
    stand = next(o for o in component.options if o.semantic_key == "stand")
    assert stand.applies_when == NOT_SPEED_ZERO


def test_the_typed_view_carries_the_same_structure() -> None:
    view = build_typed_view(
        _resolve({"patch": "replace_component", "component": choice_component()})
    )
    (record,) = view.records
    (component,) = record.components
    assert [o.semantic_key for o in component.options] == ["crawl", "stand"]


# ---------------------------------------------------------------------------
# 6. Retained replay reconstructs the same component
# ---------------------------------------------------------------------------


def test_retained_replay_survives_editing_and_deleting_the_authoring_row(
    runtime: RuntimeFixture,
) -> None:
    raw = {
        "patch": "replace_component",
        "component": choice_component(applies_when=qualifier_payload()),
    }
    canonical = patch_payload(
        patch_from_payload(
            raw,
            operation=OverrideOperationEnum.REPLACE,
            target=DESCRIPTOR_COMPONENT_TARGET,
        )
    )
    author_override(
        runtime.session,
        override_id="ov-choice",
        target=DESCRIPTOR_COMPONENT_TARGET,
        operation=OverrideOperationEnum.REPLACE,
        payload=canonical,
    )
    state = collect_current_override_state(
        runtime.session, str(runtime.package_uuid), runtime.release_version
    )
    identity = retain_override_set(runtime.session, state, now=NOW)

    row = runtime.session.get(MechanicalOverrideORM, "ov-choice")
    assert row is not None
    row.payload = patch_payload(
        patch_from_payload(
            {"patch": "replace_component", "component": DIRECT},
            operation=OverrideOperationEnum.REPLACE,
            target=DESCRIPTOR_COMPONENT_TARGET,
        )
    )
    runtime.session.flush()
    runtime.session.delete(row)
    runtime.session.flush()
    assert runtime.session.execute(select(MechanicalOverrideORM)).scalars().all() == []

    replayed = load_override_set_version(
        runtime.session,
        identity,
        package_uuid=str(runtime.package_uuid),
        release_version=runtime.release_version,
    )
    (entry,) = replayed.entries
    assert entry.payload == canonical
    assert replayed.override_set_uuid == identity

    # And it still rebuilds as the same typed patch.
    rebuilt = patch_from_payload(
        entry.payload,
        operation=OverrideOperationEnum.REPLACE,
        target=DESCRIPTOR_COMPONENT_TARGET,
    )
    assert rebuilt.body.applies_when == NOT_SPEED_ZERO  # type: ignore[union-attr]
    assert len(rebuilt.body.options) == 2  # type: ignore[union-attr]


def test_the_representation_schema_hash_is_untouched() -> None:
    """``ComponentBody`` is patch-layer shape, not representation shape.

    The literal moved to schema 3's hash because schema 3 changed the
    representation contract deliberately. What this test asserts is unchanged:
    the *patch layer* does not participate in representation identity, so this
    canary may only move when the representation itself does.
    """
    assert representation_schema_hash() == (
        "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"
    )
