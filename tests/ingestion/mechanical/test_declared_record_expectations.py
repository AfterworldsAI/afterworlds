"""Reviewed expectations and supporting claims follow a component to its
declared record -- CRD Issue 5d (#132, #137).

A component moved to a record its batch declares (``EntryComponent.record``)
keeps what the source review said of its spans: each expected fact family,
on exactly its spans, now on the declared record, beside the governing prose
it keeps. Nothing is inferred from the output, so dropping the typed facts
still fails. A STRUCTURED component moves only when every span it owns was
reviewed with families alone; a supporting text lands on the record owning the
component it names, and one naming no component stays on the entry, where
review reports it. Batches that
declare nothing keep their recorded identities; the current release's build of
them is a different release's, so that cross-release equality is retired
(``correction-followup.md``).
"""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    batch_findings,
    build_entry_batch,
)
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import ProvenanceTargetKind
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_16_HASH,
    SCHEMA_16_VERSION,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from tests.ingestion.mechanical._replacement_chain import (
    current,
    identity,
    proposal_path,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"

PACE = "play.exploration.travel_pace"
BONUS = "play.proficiency.proficiency_bonus"
SKILLS = "play.proficiency.skill_proficiencies"
BONUS_KEYS = (
    "proficiency_bonus",
    "proficiency_bonus_bands",
    "d20_test_application",
    "spell_uses",
    "bonus_operation_limits",
)
SKILL_KEYS = ("skills", "skill_proficiency", "skill_list", "determining_skills")


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKS = _load(
    "checks_actions_rests", NOTES / "issue-5d-checks-actions-rests-generator.py"
)
PLAY = _load(
    "core_play_completion", NOTES / "issue-5d-core-play-completion-generator.py"
)


def declare(
    base: EntryBatch, entry: str, records: dict[str, tuple[str, ...]]
) -> EntryBatch:
    """*base* with *records* declared under *entry*, each owning its components,
    under schema 16, which states their membership of *entry*'s record."""
    kind = {slug: k for slug, _, k in base.entries}[entry]
    owner = {(entry, k): r for r, keys in records.items() for k in keys}
    return dataclasses.replace(
        base,
        records=(*base.records, *((r, kind, entry) for r in records)),
        components=tuple(
            dataclasses.replace(c, record=owner.get((c.entry, c.key), c.record))
            for c in base.components
        ),
        schema=(SCHEMA_16_VERSION, SCHEMA_16_HASH),
    )


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


def _build(session, batch: EntryBatch) -> Built:  # type: ignore[no-untyped-def]
    return build_entry_batch(session, batch, published_release_binding(session))


@pytest.fixture(scope="module")
def play(session):  # type: ignore[no-untyped-def]
    base = PLAY.batch()
    return _build(session, base), _build(
        session, declare(base, "exploration", {PACE: ("travel_pace", "pace_effects")})
    )


@pytest.fixture(scope="module")
def checks(session):  # type: ignore[no-untyped-def]
    base = CHECKS.batch()
    moved = declare(base, "proficiency", {BONUS: BONUS_KEYS, SKILLS: SKILL_KEYS})
    return _build(session, base), _build(session, moved)


def _rules(built: Built) -> set[tuple[str, str, str | None, tuple[str, ...]]]:
    return {
        (r.record_key, r.component_key, r.fact_family, r.source_span_ids)
        for u in built.proposal.proposed_review_units
        for r in u.expected_rules
    }


def _per_span(built: Built, owners: dict[str, str]) -> set[tuple[str, ...]]:
    """(record after the move, component, family, span) of every expectation."""
    return {
        (owners.get(c, r), c, f or "", s)
        for r, c, f, spans in _rules(built)
        for s in spans
    }


def _same_findings(before: Built, after: Built) -> None:
    """The move adds no finding: review coverage stays complete and the
    out-of-batch reference findings are the unmoved batch's own."""
    was, now = batch_findings(before), batch_findings(after)
    assert not now["partition"] and not now["review_units"]
    assert sorted(now["representation"]) == sorted(was["representation"])


def _stripped(built: Built, record: str, key: str) -> list[str]:
    """Review findings once *record*/*key* loses every fact it carries."""
    p = built.proposal
    rep = p.proposed_representation
    bare = dataclasses.replace(
        rep,
        components=tuple(
            (
                dataclasses.replace(
                    c,
                    facts=(),
                    options=tuple(dataclasses.replace(o, facts=()) for o in c.options),
                )
                if (c.record_key, c.semantic_key) == (record, key)
                else c
            )
            for c in rep.components
        ),
    )
    return review_unit_violations(
        p.proposed_review_units, bare, p.policy_version, built.ledger.spans
    )


def test_batches_declaring_nothing_keep_their_recorded_identity(
    play: tuple[Built, Built], checks: tuple[Built, Built]
) -> None:
    # The identities the Owner approved in the replacement chain, at their
    # recorded bytes; the committed file has since recorded these batches'
    # declaring replacements. The builds here are the current release's.
    for batch, (base, _) in (
        ("core-play-completion", play),
        ("checks-actions-rests", checks),
    ):
        recorded = load_proposal(
            proposal_path(batch), expected_identity=identity(batch)
        )
        assert proposal_identity(recorded) == identity(batch)
        assert recorded.binding != base.binding == current().oracle.binding


def test_a_mixed_component_keeps_its_reviewed_family_and_prose(play) -> None:  # type: ignore[no-untyped-def]
    before, after = play
    (spans,) = {
        s
        for r, c, f, s in _rules(before)
        if (r, c, f) == ("play.exploration", "pace_effects", "advantage")
    }
    assert (PACE, "pace_effects", "advantage", spans) in _rules(after)
    assert any(
        (r, c, f) == (PACE, "pace_effects", None) and set(spans) <= set(s)
        for r, c, f, s in _rules(after)
    )
    owners = {"travel_pace": PACE, "pace_effects": PACE}
    assert _per_span(before, owners) == _per_span(after, {})
    _same_findings(before, after)


def test_a_structured_component_keeps_its_typed_expectations(checks) -> None:  # type: ignore[no-untyped-def]
    before, after = checks
    owners = {**dict.fromkeys(BONUS_KEYS, BONUS), **dict.fromkeys(SKILL_KEYS, SKILLS)}
    assert _per_span(before, owners) == _per_span(after, {})
    families = {(r, c, f) for r, c, f, _ in _rules(after) if f}
    assert {
        (BONUS, "proficiency_bonus_bands", "proficiency_bonus_band"),
        (BONUS, "bonus_operation_limits", "proficiency_bonus_operation_limit"),
        (SKILLS, "skill_proficiency", "proficiency_application"),
    } <= families
    assert not any(
        (r, c) == (BONUS, "proficiency_bonus_bands") and f is None
        for r, c, f, _ in _rules(after)
    )
    _same_findings(before, after)


@pytest.mark.parametrize(
    ("which", "record", "key", "family"),
    [
        ("play", PACE, "pace_effects", "advantage"),
        ("checks", BONUS, "proficiency_bonus_bands", "proficiency_bonus_band"),
        ("checks", SKILLS, "skill_proficiency", "proficiency_application"),
    ],
)
def test_a_moved_component_without_its_facts_fails_review(
    request: pytest.FixtureRequest, which: str, record: str, key: str, family: str
) -> None:
    _, after = request.getfixturevalue(which)
    assert any(
        f"expected rule {record}/{key} requires fact family {family!r}" in v
        for v in _stripped(after, record, key)
    )


def test_a_structured_component_reviewed_as_prose_is_refused(session) -> None:  # type: ignore[no-untyped-def]
    base = CHECKS.batch()
    prose = dataclasses.replace(
        base,
        clauses=tuple(
            (
                (e, k, (*x, None), t)
                if (e, k) == ("proficiency", "spell_uses")
                else (e, k, x, t)
            )
            for e, k, x, t in base.clauses
        ),
    )
    with pytest.raises(
        ValueError, match=f"{BONUS}/spell_uses must keep its governing prose"
    ):
        _build(session, declare(prose, "proficiency", {BONUS: BONUS_KEYS}))


def test_supporting_text_is_claimed_on_its_components_declared_record(checks) -> None:  # type: ignore[no-untyped-def]
    before, after = checks

    def claims(built: Built) -> set[tuple[str, str]]:
        return {
            (p.target_key[0], p.target_key[1])
            for p in built.proposal.proposed_representation.provenance
            if p.target_kind is ProvenanceTargetKind.COMPONENT
            and p.target_key[1] in ("skill_proficiency", "bonus_operation_limits")
        }

    assert claims(before) == {
        ("play.proficiency", "skill_proficiency"),
        ("play.proficiency", "bonus_operation_limits"),
    }
    assert claims(after) == {
        (SKILLS, "skill_proficiency"),
        (BONUS, "bonus_operation_limits"),
    }


def test_a_supporting_leaf_is_grouped_on_its_components_declared_record(
    session: Session,
) -> None:
    # No candidate moves a component a whole supporting leaf names, so this
    # declares one: the d20_tests rerolls example.
    record = "play.d20_tests.rerolls"
    built = _build(
        session, declare(CHECKS.batch(), "d20_tests", {record: ("rerolls",)})
    )
    groups = {
        (g.supports_record_key, g.supports_component_key)
        for u in built.proposal.proposed_review_units
        for g in u.supporting_groups
        if g.supports_component_key
    }
    assert (record, "rerolls") in groups
    assert ("play.d20_tests", "rerolls") not in groups
    assert not batch_findings(built)["review_units"]


def test_supporting_text_naming_no_component_is_reported(session) -> None:  # type: ignore[no-untyped-def]
    # No record owns it, so it is claimed on the entry as before the move and
    # review reports it; it never lands on a declared record.
    base = CHECKS.batch()
    stray = dataclasses.replace(
        base,
        supporting=tuple(
            (e, t, "no_such_component" if c == "skill_proficiency" else c)
            for e, t, c in base.supporting
        ),
    )
    built = _build(session, declare(stray, "proficiency", {SKILLS: SKILL_KEYS}))
    found = [x for v in batch_findings(built).values() for x in v]
    assert any("no_such_component" in x for x in found), found
    assert not any(
        p.target_key[:2] == (SKILLS, "no_such_component")
        for p in built.proposal.proposed_representation.provenance
    )
