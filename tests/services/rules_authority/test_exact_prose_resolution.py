"""The GameMaster view returns the governing clause, not its paragraph.

CRD Issue 5d, #137 contract 3. A prose-bound component's authority is its
accepted span. The 5c ``RuleChunk`` remains the only store of what the source
says — nothing here copies it — but what the view *returns* is sliced to the
extent the projection accepted, because the surrounding sentences are other
components' authority or nobody's.

Built directly from an :class:`EffectiveAuthority` rather than through the
service, so the assertions are about resolution itself and cannot pass by
accident because a fixture's chunk happens to be one sentence long.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.models.enums import OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.application import (
    AuthoredProse,
    EffectiveAuthority,
    EffectiveComponent,
    EffectiveRecord,
    GoverningProseEntry,
    SourceProse,
)
from afterworlds.services.rules_authority.views import build_gamemaster_view

CHUNK = "chunk-wish-open-ended"
SPAN = "span-reshape-reality"

#: One chunk, two clauses. The component below governs only the second.
CHUNK_TEXT = (
    "You create one object of up to 25,000 GP in value. "
    "You may wish for something not included in any of the other effects."
)
GOVERNING = "You may wish for something not included in any of the other effects."
NEIGHBOUR = "You create one object of up to 25,000 GP in value."

START = CHUNK_TEXT.index(GOVERNING)
END = START + len(GOVERNING)


def _authority(*prose: GoverningProseEntry) -> EffectiveAuthority:
    return EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, "pkg-5c"),
            release_version="rel-5c",
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-1"),
        ),
        records=(
            EffectiveRecord(
                semantic_key="spell:wish",
                kind=RecordKind.SPELL,
                parent_key=None,
                components=(
                    EffectiveComponent(
                        record_key="spell:wish",
                        semantic_key="open-ended-clause",
                        handling=ComponentHandling.PROSE_BOUND,
                        irreducibility_reason_code="open_ended_effect",
                        facts=(),
                        governing_prose=prose,
                        span_ids=(SPAN,),
                    ),
                ),
            ),
        ),
        applied_overrides=(),
    )


def _resolved(
    *prose: GoverningProseEntry, text: str = CHUNK_TEXT
) -> tuple[object, ...]:
    view = build_gamemaster_view(_authority(*prose), {CHUNK: text})
    return view.components[0].governing_prose


def test_resolution_returns_only_the_accepted_span() -> None:
    (entry,) = _resolved(SourceProse(CHUNK, SPAN, START, END))
    assert entry.text == GOVERNING


def test_resolution_excludes_unrelated_text_from_the_same_chunk() -> None:
    """The neighbouring clause is in the same chunk and must not come back.

    This is the whole point of the extent: returning the paragraph would
    overstate what governs this component, and a GameMaster reading it would
    adjudicate against authority the projection never accepted here.
    """
    (entry,) = _resolved(SourceProse(CHUNK, SPAN, START, END))
    assert NEIGHBOUR not in (entry.text or "")
    assert entry.text != CHUNK_TEXT


def test_resolution_retains_exact_5c_provenance() -> None:
    """Narrowing the text does not turn source authority into something else.

    The entry stays :class:`SourceProse`, still names the exact chunk and the
    accepted span, and carries no override identity — a slice is not an authored
    overlay.
    """
    (entry,) = _resolved(SourceProse(CHUNK, SPAN, START, END))
    assert isinstance(entry, SourceProse)
    assert (entry.chunk_id, entry.span_id) == (CHUNK, SPAN)
    assert (entry.char_start, entry.char_end) == (START, END)
    assert not hasattr(entry, "supplied_by_override_id")


def test_an_absent_chunk_is_reported_absent_not_empty() -> None:
    view = build_gamemaster_view(_authority(SourceProse(CHUNK, SPAN, START, END)), {})
    assert view.components[0].governing_prose[0].text is None


def test_an_extent_past_the_stored_text_resolves_to_absent() -> None:
    """A short chunk yields no passage rather than a truncated one.

    Python would silently slice to whatever is there. A partial sentence
    presented as exact governing authority is worse than a reported absence.
    """
    (entry,) = _resolved(SourceProse(CHUNK, SPAN, START, END), text=CHUNK_TEXT[:60])
    assert entry.text is None


def test_authored_prose_passes_through_unsliced() -> None:
    """An authored overlay already carries exact text and is never chunk-bound."""
    authored = AuthoredProse(
        text="House rule: the GM may veto any wish that ends the campaign.",
        supplied_by_override_id="ovr-1",
        supplied_by_origin=OverrideOriginEnum.HOUSE_RULE,
    )
    entries = _resolved(SourceProse(CHUNK, SPAN, START, END), authored)
    assert entries[0].text == GOVERNING
    assert entries[1] == authored
