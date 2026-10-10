"""A malformed source-owner key refuses a citation instead of crashing the reader.

``_citation_in_effect`` (ADR-005d Decision 7) keeps an unbound SUBSTANTIVE
citing span in effect through its unique PRIMARY ``COMPONENT`` provenance owner,
whose target key is ``(record, component)``. Persisted-state closure admits any
list of strings as a target key, so a malformed owner key can reach the reader;
it must be refused through the typed contract (the caller reports
``INVALID_REFERENCE``), not raise from tuple unpacking.

The fixture is the minimum shape the predicate reads, modelled on the accepted
``glossary.dodge`` / ``benefits_lost`` "Incapacitated" citation.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from afterworlds.ingestion.mechanical.models import SemanticDisposition
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceRole,
    ProvenanceTargetKind,
)
from afterworlds.services.rules_authority.service import _citation_in_effect

CITATION = (
    "glossary.dodge",
    "benefits_lost",
    "Incapacitated",
    "srd-5.2.1/rules-glossary",
)
SPAN = "c4ff6396-1e05-5508-9087-ecffe419fcf3"
REFERENCE_KEY = ("reference-key",)


def _inputs(owner_key: tuple[str, ...]) -> tuple[Any, Any, Any]:
    stated = [SimpleNamespace(target_record_key="glossary.incapacitated")]
    provenance = (
        SimpleNamespace(
            target_kind=ProvenanceTargetKind.REFERENCE,
            target_key=REFERENCE_KEY,
            span_id=SPAN,
            role=ProvenanceRole.CONTEXTUAL,
        ),
        SimpleNamespace(
            target_kind=ProvenanceTargetKind.COMPONENT,
            target_key=owner_key,
            span_id=SPAN,
            role=ProvenanceRole.PRIMARY,
        ),
    )
    candidate = SimpleNamespace(
        representation=SimpleNamespace(provenance=provenance, prose_bindings=()),
        classification=SimpleNamespace(
            spans=(
                SimpleNamespace(
                    span_id=SPAN, disposition=SemanticDisposition.SUBSTANTIVE
                ),
            )
        ),
    )
    component = SimpleNamespace(
        semantic_key="benefits_lost",
        governing_prose=(),
        supplied_by_override_id=None,
        span_ids=(SPAN,),
    )
    authority = SimpleNamespace(
        records=(
            SimpleNamespace(
                semantic_key="glossary.dodge",
                supplied_by_override_id=None,
                components=(component,),
            ),
        )
    )
    return stated, candidate, authority


@pytest.fixture(autouse=True)
def _reference_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every stated reference maps to the one REFERENCE provenance key."""
    monkeypatch.setattr(
        "afterworlds.services.rules_authority.service.reference_target_key",
        lambda _ref: REFERENCE_KEY,
    )


def test_a_well_formed_owner_keeps_the_citation() -> None:
    """The control: the same shape with a two-part owner key is admitted."""
    stated, candidate, authority = _inputs(("glossary.dodge", "benefits_lost"))
    assert _citation_in_effect(CITATION, stated, candidate, authority) is True


@pytest.mark.parametrize(
    "owner_key",
    [
        ("glossary.dodge",),
        ("glossary.dodge", "benefits_lost", "extra"),
        (),
    ],
    ids=["one-part", "three-part", "empty"],
)
def test_a_malformed_owner_key_refuses_rather_than_raises(
    owner_key: tuple[str, ...],
) -> None:
    stated, candidate, authority = _inputs(owner_key)
    assert _citation_in_effect(CITATION, stated, candidate, authority) is False
