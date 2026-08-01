"""The accepted completeness oracle — CRD Issue 5d, Decision 5.

Two things are proven here: that a committed oracle file is read strictly
enough to be authority, and that the oracle cannot be produced from the thing
it judges.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical import oracle as oracle_module
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedOracle,
    OracleLoadError,
    _resolve_committed_oracle,
    derive_obligations,
    load_oracle,
    oracle_identity,
    oracle_payload,
)
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    PACKAGE_UUID,
    RELEASE_VERSION,
    accepted_oracle,
)


def _payload() -> dict[str, object]:
    return json.loads(BOUNDED_ORACLE_PATH.read_text(encoding="utf-8"))


def _write(tmp_path: Path, payload: object, name: str = "o.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Self-attestation prevention
# ---------------------------------------------------------------------------


def test_oracle_module_cannot_reach_the_state_it_judges() -> None:
    """No import path from the oracle to persistence, the ORM, or the gate.

    The structural half of independence: an oracle that could read a persisted
    projection could be *derived* from one, and a later refactor that adds such
    an import would silently turn the completeness proof into self-attestation.
    This fails on the import, before anyone has to notice the semantics.
    """
    source = Path(oracle_module.__file__).read_text(encoding="utf-8")
    imported = {
        node.module or ""
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    forbidden = ("sqlalchemy", "persistence", "raw_state", "gate", "publication", "orm")
    offending = sorted(m for m in imported if any(f in m for f in forbidden))
    assert offending == [], f"oracle must not import {offending}"


def test_no_committed_oracle_is_generated_into_the_source_tree() -> None:
    """The committed oracle directory holds no production authority yet.

    The production SRD release therefore resolves to no accepted authority and
    cannot be published. When a later content PR commits one, this test is the
    place that says so out loud.
    """
    assert sorted(p.name for p in COMMITTED_ORACLE_DIR.glob("*.json")) == []


def test_declared_policy_comes_from_the_file_not_current_code(tmp_path: Path) -> None:
    """A file declaring a different policy loads with *that* policy.

    Substituting the current constants here would let a policy change re-bless
    an oracle nobody re-reviewed. The gate is what rejects the mismatch; the
    loader's job is to report honestly what the file says.
    """
    payload = _payload()
    payload["semantic_policy_version"] = "5d-semantic-policy-0"
    loaded = load_oracle(_write(tmp_path, payload))
    assert loaded.policy_version == "5d-semantic-policy-0"


# ---------------------------------------------------------------------------
# Committed-file loading
# ---------------------------------------------------------------------------


def test_committed_file_states_the_accepted_authority() -> None:
    """The committed JSON and the accepted content are the same authority.

    Regenerate ``data/bounded_oracle.json`` when the fixture's accepted content
    or the frozen semantic policy changes — a policy change legitimately
    invalidates a committed oracle until it is re-accepted.
    """
    assert oracle_payload(load_oracle(BOUNDED_ORACLE_PATH)) == oracle_payload(
        accepted_oracle()
    )


def test_loaded_oracle_carries_every_accepted_element() -> None:
    loaded = load_oracle(BOUNDED_ORACLE_PATH)
    assert isinstance(loaded, AcceptedOracle)
    assert loaded.binding.package_uuid == PACKAGE_UUID
    assert len(loaded.spans) == 3
    assert len(loaded.representation.records) == 2
    assert len(loaded.representation.provenance) == 4
    assert {o.record_key for o in loaded.obligations} == {
        "spell:wish",
        "creature:wish-scoped-servant",
    }


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda p: p.pop("obligations"), "missing ['obligations']"),
        (lambda p: p.update(extra=1), "unexpected ['extra']"),
        (
            lambda p: p["spans"][0].update(disposition="mostly_substantive"),
            "not a declared SemanticDisposition",
        ),
        (
            lambda p: p["spans"][0].update(disposition=3),
            "expected a string SemanticDisposition",
        ),
        (
            lambda p: p["representation"]["records"][0].update(kind="artifact"),
            "not a declared RecordKind",
        ),
        (
            lambda p: p["representation"]["components"][0]["facts"][0].update(
                family="vibes"
            ),
            "not a member of the closed typed-fact union",
        ),
        (
            lambda p: p["representation"]["components"][0]["facts"][0].pop("level"),
            "missing ['level']",
        ),
        (
            lambda p: p["obligations"][0].update(
                structured_fact_families=["telepathy"]
            ),
            "not a declared FactFamily",
        ),
    ],
)
def test_a_malformed_oracle_is_rejected_not_defaulted(
    tmp_path: Path, mutate, fragment: str  # type: ignore[no-untyped-def]
) -> None:
    """Every rejection is a raise, never a quietly narrower oracle.

    An oracle that silently dropped an unreadable element would be *weaker*
    authority than the one a reviewer accepted, and publication would be judged
    against the difference.
    """
    payload = _payload()
    mutate(payload)
    with pytest.raises(OracleLoadError) as exc:
        load_oracle(_write(tmp_path, payload))
    assert fragment in str(exc.value)


def test_unreadable_file_is_a_load_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(OracleLoadError):
        load_oracle(path)


def test_review_state_is_not_a_field_a_file_may_set(tmp_path: Path) -> None:
    """A committed oracle is accepted authority by construction."""
    payload = _payload()
    payload["spans"][0]["review_state"] = "proposed"
    with pytest.raises(OracleLoadError) as exc:
        load_oracle(_write(tmp_path, payload))
    assert "unexpected ['review_state']" in str(exc.value)


# ---------------------------------------------------------------------------
# Release resolution and identity
# ---------------------------------------------------------------------------


def test_release_with_no_committed_oracle_resolves_to_none(tmp_path: Path) -> None:
    assert _resolve_committed_oracle("other-pkg", "rel-9", tmp_path) is None


def test_committed_oracle_resolves_by_exact_release(tmp_path: Path) -> None:
    _write(tmp_path, _payload(), "bounded.json")
    resolved = _resolve_committed_oracle(PACKAGE_UUID, RELEASE_VERSION, tmp_path)
    assert resolved is not None
    assert resolved.binding.release_version == RELEASE_VERSION
    assert _resolve_committed_oracle(PACKAGE_UUID, "rel-other", tmp_path) is None


def test_two_oracles_for_one_release_is_rejected(tmp_path: Path) -> None:
    """Picking one would make publication depend on filesystem ordering."""
    _write(tmp_path, _payload(), "a.json")
    _write(tmp_path, _payload(), "b.json")
    with pytest.raises(OracleLoadError) as exc:
        _resolve_committed_oracle(PACKAGE_UUID, RELEASE_VERSION, tmp_path)
    assert "2 committed oracles" in str(exc.value)


# ---------------------------------------------------------------------------
# The obligation relation must be total and exact
# ---------------------------------------------------------------------------
#
# Shape validation cannot see any of this. Every payload below parses perfectly
# and describes a real accepted representation; what is wrong is the *relation*
# between the declared obligations and that representation, which is where a
# per-record completeness control silently loses its teeth.

SPELL_OBLIGATION = {
    "record_key": "spell:wish",
    "kind": "spell",
    "structured_fact_families": ["spell_descriptor"],
    "prose_bound_components": ["open-ended-clause"],
}


def _with_obligations(obligations: list[dict[str, object]]) -> dict[str, object]:
    payload = _payload()
    payload["obligations"] = obligations
    return payload


def test_the_bounded_oracle_declares_exactly_what_it_represents() -> None:
    """The committed file's obligations are the derived ones, not a subset."""
    oracle = load_oracle(BOUNDED_ORACLE_PATH)
    assert set(oracle.obligations) == set(derive_obligations(oracle.representation))


@pytest.mark.parametrize(
    ("obligations", "expected"),
    [
        pytest.param([], "carry no obligation", id="none-at-all"),
        pytest.param(
            [SPELL_OBLIGATION],
            "carry no obligation",
            id="one-record-uncovered",
        ),
        pytest.param(
            [SPELL_OBLIGATION, SPELL_OBLIGATION],
            "duplicate obligation",
            id="duplicate",
        ),
        pytest.param(
            [
                SPELL_OBLIGATION,
                {
                    "record_key": "spell:invented",
                    "kind": "spell",
                    "structured_fact_families": [],
                    "prose_bound_components": [],
                },
            ],
            "does not declare",
            id="targets-a-nonexistent-record",
        ),
        pytest.param(
            [{**SPELL_OBLIGATION, "kind": "creature"}],
            "does not reconcile",
            id="wrong-record-kind",
        ),
        pytest.param(
            [{**SPELL_OBLIGATION, "structured_fact_families": []}],
            "does not reconcile",
            id="understated-fact-family",
        ),
        pytest.param(
            [
                {
                    **SPELL_OBLIGATION,
                    "structured_fact_families": ["spell_descriptor", "ability_check"],
                }
            ],
            "does not reconcile",
            id="overstated-fact-family",
        ),
        pytest.param(
            [{**SPELL_OBLIGATION, "prose_bound_components": []}],
            "does not reconcile",
            id="understated-prose-bound-set",
        ),
        pytest.param(
            [{**SPELL_OBLIGATION, "prose_bound_components": ["descriptor"]}],
            "does not reconcile",
            id="prose-bound-names-a-structured-component",
        ),
        pytest.param(
            [{**SPELL_OBLIGATION, "prose_bound_components": ["no-such-component"]}],
            "does not reconcile",
            id="prose-bound-names-a-nonexistent-component",
        ),
    ],
)
def test_an_unclosed_obligation_relation_fails_to_load(
    tmp_path: Path, obligations: list[dict[str, object]], expected: str
) -> None:
    """Malformed accepted authority is no oracle, never a weaker one."""
    with pytest.raises(OracleLoadError) as exc:
        load_oracle(_write(tmp_path, _with_obligations(obligations)))
    assert expected in str(exc.value)


def test_identity_changes_with_accepted_meaning(tmp_path: Path) -> None:
    base = load_oracle(BOUNDED_ORACLE_PATH)
    payload = _payload()
    payload["representation"]["components"][0]["facts"][0]["level"] = 8
    assert oracle_identity(load_oracle(_write(tmp_path, payload))) != oracle_identity(
        base
    )


def test_identity_is_stable_across_authoring_order(tmp_path: Path) -> None:
    """Two files stating the same authority in different orders are one oracle."""
    payload = _payload()
    payload["spans"].reverse()
    payload["representation"]["records"].reverse()
    payload["obligations"].reverse()
    assert oracle_identity(load_oracle(_write(tmp_path, payload))) == oracle_identity(
        load_oracle(BOUNDED_ORACLE_PATH)
    )
