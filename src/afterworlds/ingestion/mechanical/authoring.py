"""Assemble an entry-shaped proposal from literal source-review tables.

The step every glossary batch repeats between the shared primitives
(:func:`~.proposal.seed_proposal`, :func:`~.proposal.locate_span`,
:meth:`~.bound_corpus.BoundCorpusSnapshot.unique_chunk_range`) and an
unaccepted ``5d-proposal-2`` artifact: locate each reviewed clause, turn each
proposed component into drafts with one PRIMARY owner per span, and derive one review
unit per printed entry (``ENTRY``) or placed section (``SECTION``).

A batch supplies only review data, held in two independent halves:

* the **source review** -- ``clauses`` (what each printed clause must be read
  as), ``framing`` and each entry's heading (leaves that state no rule), and
  ``supporting`` (spans that identify or illustrate rather than rule); and
* the **representation** -- ``components`` and ``record_references``.

Expected rules are built from ``clauses`` alone, never from ``components``,
so a component a batch drops leaves its expectation standing for
:func:`~.projection.review_unit_violations` to report. Nothing here accepts,
publishes or writes under ``oracles/``; it emits proposals only.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import validate_partition
from afterworlds.ingestion.mechanical.bound_corpus import (
    BoundCorpusSnapshot,
    leaves_under,
    load_bound_corpus,
)
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    ExcludedGroup,
    ExpectedRule,
    ReleaseBinding,
    ReviewState,
    ReviewUnit,
    ReviewUnitKind,
    SemanticDisposition,
    SemanticSpan,
    SupportingGroup,
)
from afterworlds.ingestion.mechanical.policy import (
    IRREDUCIBILITY_REASONS,
    PROSE_RETENTION_REASONS,
)
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    ProposedSpan,
    locate_span,
    proposal_identity,
    proposal_payload,
    seed_proposal,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    Applicability,
    ComponentDraft,
    ComponentOption,
    FactQualifier,
    MechanicalFact,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    Recurrence,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    component_target_key,
    fact_key,
    fact_qualifier_target_key,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    relationship_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_16_HASH,
    SCHEMA_16_VERSION,
    schema_binding_violations,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.orm.corpus import LedgerLeafORM

# An entry is a Rules Glossary entry unless its batch places it elsewhere
# (:class:`Placement`). A single pointer out of the glossary names its target as
# a Target pair.
GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"

#: (entry, component key, expected fact families + ``None`` for governing
#: prose, clause texts).
Clause = tuple[str, str, tuple[str | None, ...], tuple[str, ...]]
#: A glossary entry slug, or the exact (scope key, target record key) of a
#: pointer whose destination lies outside the Rules Glossary.
Target = str | tuple[str, str]
#: (entry, printed text, target, texts of the spans it is read from).
RecordReference = tuple[str, str, Target, tuple[str, ...]]


def rk(slug: str) -> str:
    """Record key of one glossary entry."""
    return f"glossary.{slug}"


def scoped(target: Target) -> tuple[str, str]:
    """The (scope key, target record key) one reference target resolves to."""
    return (GLOSSARY_SCOPE, rk(target)) if isinstance(target, str) else target


@dataclass(frozen=True)
class Placement:
    """Where an entry that is not a Rules Glossary entry sits, and its key.

    A whole printed section is reviewed as one unit under its own heading; the
    glossary default is ``(*parent, label)``, ``rk(slug)``, ``#### {label}``
    and ``ENTRY``.
    """

    record_key: str
    container: tuple[str, ...]
    #: The exact content of the heading leaf that names the section.
    heading: str
    unit_kind: ReviewUnitKind = ReviewUnitKind.SECTION
    #: Sub-containers, as label suffixes, whose leaves another record already
    #: owns and this one therefore leaves out (*Exploration* less its accepted
    #: *Breaking Objects*). Empty by default, which selects the whole container.
    omit: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class EntryComponent:
    """One proposed component, keyed to the clause row it represents."""

    entry: str
    key: str
    handling: ComponentHandling
    reason: str | None
    facts: tuple[MechanicalFact, ...] = ()
    qualifiers: tuple[tuple[MechanicalFact, Applicability], ...] = ()
    options: tuple[ComponentOption, ...] = ()
    applies_when: Applicability | None = None
    #: How often the component's effect repeats; ``None`` states no cadence.
    recurs: Recurrence | None = None
    #: Component-owned references: (printed text, target).
    refs: tuple[tuple[str, Target], ...] = ()
    #: (option key, clause texts): an option read from only some of the
    #: component's clauses claims only those. Unlisted options claim them all.
    option_sources: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: The record that owns the component when it is not the entry's own: an
    #: item or rule the entry prints and a citation names by name. Declared in
    #: :attr:`EntryBatch.records`.
    record: str | None = None
    #: Reviewed texts of the entry read instead of the clause's: a record
    #: owning only part of one (a table row), or a clause read with the section
    #: passages that govern it. Empty reads the clause.
    texts: tuple[str, ...] = ()
    #: Of the texts read, those bound as context rather than owned: a row
    #: reads its table's head, and a named record the rules governing it.
    context: tuple[str, ...] = ()
    #: Of the context texts, (text, entry) for each another entry prints: an
    #: item read with the rules its part's sections print for it. Declared,
    #: never searched for; an unlisted context text is the entry's own.
    context_from: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class EntryBatch:
    """The literal review data of one entry-shaped batch."""

    origin: str
    proposal_origin: str
    unit_prefix: str
    parent: tuple[str, ...]
    #: (slug, printed heading label, record kind), in printed order.
    entries: tuple[tuple[str, str, RecordKind], ...]
    expected_leaves: int
    clauses: tuple[Clause, ...]
    #: (entry, leaf prefix): whole leaves that frame the entry's rules.
    framing: tuple[tuple[str, str], ...]
    components: tuple[EntryComponent, ...]
    #: (entry, text, component key or ``None`` for record-owned references).
    supporting: tuple[tuple[str, str, str | None], ...]
    record_references: tuple[RecordReference, ...]
    #: Texts that also occur in running prose, located on their table cell.
    cell_anchors: Collection[str] = ()
    #: (entry, text) -> a longer text containing it that the entry prints
    #: exactly once: for a text printed more than once there and in no cell of
    #: its own (a table's close, cut from its last row).
    anchors: Mapping[tuple[str, str], str] = field(default_factory=dict)
    #: Entries placed outside the Rules Glossary, by slug.
    placements: Mapping[str, Placement] = field(default_factory=dict)
    #: (entry, exact contents of whole leaves, reason): leaves beside the
    #: entry's own heading that state no rule, excluded as one group.
    excluded: tuple[tuple[str, tuple[str, ...], str], ...] = ()
    #: (entry, section entry): each entry a placed section prints as one of its
    #: own, in printed order. Declared, never inferred from keys, and checked
    #: against the release's containment: it must be exactly the entries whose
    #: leaves all lie in the section's container.
    members: tuple[tuple[str, str], ...] = ()
    #: (record key, kind, entry): records for items or rules an entry prints,
    #: each owning the spans its components claim and a ``CATALOGUE_MEMBER``
    #: of the entry's record (Owner Decision 2026-09-24): the section reaches
    #: the record where it is printed and no longer reads that prose itself.
    #: Unlike :attr:`members`, the list is the cited records, not every entry.
    records: tuple[tuple[str, RecordKind, str], ...] = ()
    #: Declared record key -> the release container, inside its entry, that
    #: prints it (a class feature under its own heading). Its texts are located
    #: exactly once among the entry's leaves in that container, so a leaf the
    #: entry prints twice (*Hunter's Prey* and *Defensive Tactics*) is found
    #: where each record prints it. Unlisted records read the whole entry.
    record_containers: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    #: Declared records wholly contained by their entry's record rather than
    #: printed as one of its catalogue's entries (a spell's own stat block):
    #: their edge is ``SCOPED_WITHIN``, which no consumer expands, in place of
    #: ``CATALOGUE_MEMBER``. Otherwise declared, located and cited alike.
    scoped_records: Collection[str] = ()
    #: (source record key, target record key, kind, entry, text): an edge the
    #: entry's reviewed *text* states between records, which need not be this
    #: batch's own (a class's spell list naming a spell). Cited contextually on
    #: that span; never inferred from keys.
    edges: tuple[tuple[str, str, RelationshipKind, str, str], ...] = ()
    #: The representation schema (version, hash) the batch was reviewed under.
    #: A committed batch keeps the one it was built under when a later schema
    #: is minted, so its bytes still re-derive; acceptance lifts its prior.
    #:
    #: The default is the literal schema-16 pair, not the current contract:
    #: every committed generator that leaves it unset was reviewed under 16,
    #: and following the current contract would restamp them at each mint. A
    #: batch stating schema-17 meaning must declare 17 and is refused otherwise.
    schema: tuple[str, str] = (SCHEMA_16_VERSION, SCHEMA_16_HASH)

    def record_key(self, entry: str) -> str:
        placed = self.placements.get(entry)
        return placed.record_key if placed else rk(entry)


@dataclass
class Built:
    """Everything the proposal was derived from, kept for the checks."""

    binding: ReleaseBinding
    corpus: BoundCorpusSnapshot
    proposal: MechanicalProposal
    ledger: ClassificationLedger
    entry_leaves: dict[str, tuple[str, ...]]
    leaf_rows: dict[str, LedgerLeafORM]
    spans: dict[tuple[str, str], SemanticSpan] = field(default_factory=dict)


def html_table(
    caption: str, header: tuple[str, ...], rows: list[tuple[str, ...]]
) -> str:
    """A 5c table leaf's exact text, written as its rows rather than as markup.

    Only a way to *name* source text: :func:`~.proposal.locate_span` still has
    to find the result verbatim, so a table the corpus renders differently is a
    loud locate failure, never a silently different span.
    """

    def tr(tag: str, cells: tuple[str, ...]) -> str:
        inner = "".join(f"\n      <{tag}>{c}</{tag}>" for c in cells)
        return f"    <tr>{inner}\n    </tr>\n"

    return (
        f"**{caption}**\n\n<table>\n  <thead>\n{tr('th', header)}  </thead>\n"
        f"  <tbody>\n{''.join(tr('td', r) for r in rows)}  </tbody>\n</table>"
    )


def build_entry_batch(
    session: Session, batch: EntryBatch, binding: ReleaseBinding
) -> Built:
    """Derive *batch*'s proposal from the release *binding* names."""
    pkg, rel = binding.package_uuid, binding.release_version
    corpus = load_bound_corpus(session, pkg, rel)

    def selected(slug: str, label: str) -> tuple[str, ...]:
        placed = batch.placements.get(slug)
        if placed is None:
            return leaves_under(session, pkg, rel, (*batch.parent, label))
        owned = {lid for o in placed.omit for lid in leaves_under(session, pkg, rel, o)}
        return tuple(
            lid
            for lid in leaves_under(session, pkg, rel, placed.container)
            if lid not in owned
        )

    entry_leaves = {slug: selected(slug, label) for slug, label, _ in batch.entries}
    all_leaves = [lid for ids in entry_leaves.values() for lid in ids]
    if not len(all_leaves) == len(set(all_leaves)) == batch.expected_leaves:
        raise ValueError(
            f"{len(all_leaves)} leaves ({len(set(all_leaves))} distinct) under "
            f"the entries; the review read {batch.expected_leaves}"
        )
    rows = {
        r.leaf_id: r
        for r in session.execute(
            select(LedgerLeafORM).where(
                LedgerLeafORM.package_uuid == pkg,
                LedgerLeafORM.leaf_id.in_(all_leaves),
            )
        ).scalars()
    }
    order = {lid: rows[lid].occurrence_index for lid in all_leaves}
    entry_leaves = {
        s: tuple(sorted(ids, key=order.__getitem__)) for s, ids in entry_leaves.items()
    }

    seed = seed_proposal(
        corpus,
        all_leaves,
        binding=binding,
        origin=batch.origin,
        rationale="seeded whole-leaf; replaced below by reviewed clauses",
    )

    spans: dict[tuple[str, str], SemanticSpan] = {}
    proposed: list[ProposedSpan] = []

    def locate(
        entry: str,
        text: str,
        disposition: SemanticDisposition,
        why: str,
        record: str | None = None,
    ) -> SemanticSpan:
        key = (record or entry, text)
        if key in spans:
            if spans[key].disposition is not disposition:
                raise ValueError(f"{key} is reviewed as two dispositions")
            return spans[key]
        leaves = entry_leaves[entry]
        if record is not None:
            inside = set(
                leaves_under(session, pkg, rel, batch.record_containers[record])
            )
            leaves = tuple(leaf for leaf in leaves if leaf in inside)
            if not leaves:
                raise ValueError(f"{record} is printed in no leaf of {entry}")
        # A text that is one whole leaf is that leaf, though a longer heading
        # prints it too ("## Barbarian" in "### Barbarian Class Features").
        whole = [leaf for leaf in leaves if rows[leaf].content == text]
        if len(whole) == 1:
            leaves = tuple(whole)
        anchor = batch.anchors.get((entry, text))
        if text in batch.cell_anchors:
            if anchor is not None:
                raise ValueError(f"{(entry, text)} has two anchors")
            anchor = f"<td>{text}</td>"
        span = locate_span(
            {leaf: rows[leaf].content for leaf in leaves},
            text,
            disposition,
            anchor=anchor,
        )
        spans[key] = span
        proposed.append(ProposedSpan(span=span, origin=batch.origin, rationale=why))
        return span

    clause_texts: dict[tuple[str, str], tuple[str, ...]] = {}
    for entry, key, _, texts in batch.clauses:
        if (entry, key) in clause_texts:
            raise ValueError(f"clause {(entry, key)} is reviewed twice")
        clause_texts[(entry, key)] = texts
        for t in texts:
            locate(
                entry,
                t,
                SemanticDisposition.SUBSTANTIVE,
                "states a rule of this entry that the representation carries",
            )
    for entry, text, _ in batch.supporting:
        locate(
            entry,
            text,
            SemanticDisposition.SUPPORTING_AUTHORITY,
            "identifies, enumerates or scopes rules stated in this or another entry",
        )

    def chunk_of(span: SemanticSpan) -> tuple[str, int, int]:
        bound = corpus.unique_chunk_range(span.leaf_id, span.char_start, span.char_end)
        if bound is None:
            raise ValueError(f"span {span.span_id} binds to no single chunk")
        return bound

    def claim(
        kind: ProvenanceTargetKind,
        key: tuple[str, ...],
        span: SemanticSpan,
        role: ProvenanceRole = ProvenanceRole.CONTEXTUAL,
    ) -> ProvenanceClaim:
        return ProvenanceClaim(kind, key, span.span_id, role)

    components: list[ComponentDraft] = []
    bindings: list[ProseBindingDraft] = []
    references: list[ReferenceDraft] = []
    provenance: list[ProvenanceClaim] = []
    irreducible_codes = {r.code for r in IRREDUCIBILITY_REASONS}
    retention_codes = {r.code for r in PROSE_RETENTION_REASONS}

    extra = {key: entry for key, _, entry in batch.records}
    contained = batch.record_containers
    if stray_records := sorted(set(contained) - set(extra)):
        raise ValueError(f"containers name undeclared records {stray_records}")
    if stray_scoped := sorted(set(batch.scoped_records) - set(extra)):
        raise ValueError(f"scoped records name undeclared records {stray_scoped}")

    def at(c: EntryComponent, text: str) -> tuple[str, str]:
        """The key *c* reads *text* under: a contained record's own, or the
        entry printing its context."""
        if (printer := dict(c.context_from).get(text)) is not None:
            return (printer, text)
        if c.record is not None and c.record in contained:
            return (c.record, text)
        return (c.entry, text)

    for c in batch.components:
        record = c.record or batch.record_key(c.entry)
        if c.record is not None and extra.get(c.record) != c.entry:
            raise ValueError(f"{c.record} is not a declared record of {c.entry}")
        irreducible = c.reason if c.reason in irreducible_codes else None
        retention = c.reason if c.reason in retention_codes else None
        entry_key = (c.entry, c.key)
        if any(e not in entry_leaves for _, e in c.context_from):
            raise ValueError(f"component {entry_key} reads context of no entry")
        if {t for t, _ in c.context_from} - set(c.context):
            raise ValueError(f"component {entry_key} reads another entry's text")
        if c.record is not None and c.record in contained:
            if not c.texts:
                raise ValueError(
                    f"component {(c.entry, c.key)} of {c.record} reads nothing"
                )
            for t in c.texts:
                if t in dict(c.context_from):
                    continue  # located where its own entry prints it
                locate(
                    c.entry,
                    t,
                    SemanticDisposition.SUBSTANTIVE,
                    "states a rule of this entry that the representation carries",
                    c.record,
                )
        if c.texts:
            if unreviewed := [t for t in c.texts if at(c, t) not in spans]:
                raise ValueError(f"component {entry_key} reads unreviewed {unreviewed}")
            texts = c.texts
        elif entry_key not in clause_texts:
            raise ValueError(f"component {entry_key} represents no reviewed clause")
        else:
            texts = clause_texts[entry_key]
        if set(c.context) - set(texts):
            raise ValueError(f"component {entry_key} has context it does not read")
        draft = ComponentDraft(
            record_key=record,
            semantic_key=c.key,
            handling=c.handling,
            irreducibility_reason_code=irreducible,
            prose_retention_reason_code=retention,
            facts=c.facts,
            applies_when=c.applies_when,
            options=c.options,
            recurs=c.recurs,
            fact_qualifiers=tuple(
                FactQualifier(fact_key=fact_key(f), applies_when=a)
                for f, a in c.qualifiers
            ),
        )
        components.append(draft)
        cspans = [spans[at(c, t)] for t in texts]
        option_sources = dict(c.option_sources)
        if stray := {t for ts in option_sources.values() for t in ts} - set(texts):
            raise ValueError(f"options of {entry_key} cite unreviewed {sorted(stray)}")
        for text_, span in zip(texts, cspans, strict=True):
            # One PRIMARY owner per span: the governing prose where the
            # component keeps it, else the component itself. A text read as
            # context is owned elsewhere and claimed CONTEXTUAL here.
            role = (
                ProvenanceRole.CONTEXTUAL
                if text_ in c.context
                else ProvenanceRole.PRIMARY
            )
            if c.handling is ComponentHandling.STRUCTURED:
                provenance.append(
                    claim(
                        ProvenanceTargetKind.COMPONENT,
                        component_target_key(draft),
                        span,
                        role,
                    )
                )
            else:
                cid, a, b = chunk_of(span)
                binding_ = ProseBindingDraft(
                    component_key=c.key,
                    record_key=record,
                    chunk_id=cid,
                    span_id=span.span_id,
                    chunk_char_start=a,
                    chunk_char_end=b,
                    irreducibility_reason_code=irreducible,
                    prose_retention_reason_code=retention,
                )
                bindings.append(binding_)
                provenance.append(
                    claim(
                        ProvenanceTargetKind.PROSE_BINDING,
                        prose_binding_target_key(binding_),
                        span,
                        role,
                    )
                )
            for f in c.facts:
                provenance.append(
                    claim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(record, c.key, f),
                        span,
                    )
                )
            for f, _ in c.qualifiers:
                provenance.append(
                    claim(
                        ProvenanceTargetKind.FACT_QUALIFIER,
                        fact_qualifier_target_key(record, c.key, fact_key(f)),
                        span,
                    )
                )
            for o in c.options:
                if text_ not in option_sources.get(o.semantic_key, texts):
                    continue
                for f in o.facts:
                    provenance.append(
                        claim(
                            ProvenanceTargetKind.FACT,
                            fact_target_key(record, c.key, f, o.semantic_key),
                            span,
                        )
                    )
        for text, target in c.refs:
            ref = ReferenceDraft(record, c.key, text, *scoped(target))
            references.append(ref)
            # Cited where the component's own texts print it; only a pointer
            # its own texts do not print is cited from its context.
            # Through the source's bold, which can cover only part of a name
            # ("Giant **Goat**").
            printing = [
                (t, s)
                for t, s in zip(texts, cspans, strict=True)
                if text in t or text in t.replace("**", "")
            ]
            cited = [s for t, s in printing if t not in c.context] or [
                s for _, s in printing
            ]
            if not cited:
                raise ValueError(f"reference {text!r} of {entry_key} cites no clause")
            provenance.extend(
                claim(ProvenanceTargetKind.REFERENCE, reference_target_key(ref), s)
                for s in cited
            )

    def supported(entry: str, component: str) -> str:
        """The record owning the component a supporting text of *entry* names:
        its declared record, else the entry's. A component no record owns is
        claimed on the entry, so review reports the claim; two are refused."""
        owners = {
            c.record or batch.record_key(entry)
            for c in batch.components
            if (c.entry, c.key) == (entry, component)
        }
        if len(owners) > 1:
            raise ValueError(
                f"supporting text of {entry} names component {component!r} "
                f"of {len(owners)} records"
            )
        return owners.pop() if owners else batch.record_key(entry)

    for entry, text, component in batch.supporting:
        if component is not None:
            provenance.append(
                claim(
                    ProvenanceTargetKind.COMPONENT,
                    (supported(entry, component), component),
                    spans[(entry, text)],
                )
            )

    for entry, text, target, texts in batch.record_references:
        # A record owns a reference only where no component of it states the
        # same pointer; otherwise the pointer's spans cite the component's.
        stated = [
            r
            for r in references
            if (r.from_record_key, r.source_text, r.scope_key, r.target_record_key)
            == (batch.record_key(entry), text, *scoped(target))
        ]
        ref = (
            stated[0]
            if stated
            else ReferenceDraft(
                batch.record_key(entry),
                RECORD_OWNED_REFERENCE,
                text,
                *scoped(target),
            )
        )
        if not stated:
            references.append(ref)
        provenance.extend(
            claim(
                ProvenanceTargetKind.REFERENCE,
                reference_target_key(ref),
                spans[(entry, t)],
            )
            for t in texts
        )

    # Membership: each listed entry is a CATALOGUE_MEMBER of its section. The
    # printed containment is the evidence, so the listing must match it both
    # ways, and the edge cites the member's first reviewed clause as
    # contextual source -- which is also the position members are read in.
    relationships: list[RelationshipDraft] = []
    listed: dict[str, str] = {}
    for member, section in batch.members:
        if member in listed:
            raise ValueError(
                f"entry {member} is listed in both {listed[member]} and {section}"
            )
        listed[member] = section
        if section not in batch.placements or member not in entry_leaves:
            raise ValueError(f"membership {member} -> {section} names no placed entry")
    for section in dict.fromkeys(listed.values()):
        container = set(
            leaves_under(session, pkg, rel, batch.placements[section].container)
        )
        within = {
            slug
            for slug, ids in entry_leaves.items()
            if slug != section and ids and container.issuperset(ids)
        }
        declared = {m for m, s in listed.items() if s == section}
        if within != declared:
            raise ValueError(
                f"section {section} prints {sorted(within)}; its membership "
                f"lists {sorted(declared)}"
            )
    for member, section in batch.members:
        clauses = [
            spans[(member, t)]
            for e, _, _, ts in batch.clauses
            if e == member
            for t in ts
        ]
        if not clauses:
            raise ValueError(f"member {member} has no reviewed clause to cite")
        edge = RelationshipDraft(
            batch.record_key(member),
            batch.record_key(section),
            RelationshipKind.CATALOGUE_MEMBER,
        )
        relationships.append(edge)
        provenance.append(
            claim(
                ProvenanceTargetKind.RELATIONSHIP,
                relationship_target_key(edge),
                min(clauses, key=lambda s: (order[s.leaf_id], s.char_start)),
            )
        )

    # Declared records (Owner Decision 2026-09-24): each is a CATALOGUE_MEMBER
    # of its entry's section, which reaches it where it is printed. Declared,
    # never inferred: a component names a record declared for its own entry,
    # and every text it reads -- owned, or read as its table head and group
    # row -- is located among that entry's own leaves (``spans`` is keyed by
    # entry), so it lies in the section by construction. The section must not
    # bind what the record owns as its own; it may read it as context, as a
    # family reads a row an item in another catalogue owns (Owner Decision
    # 2026-09-27). The edge cites the record's first owned span, the position
    # the section reaches it at.
    def read_by(c: EntryComponent) -> tuple[str, ...]:
        return c.texts or clause_texts[(c.entry, c.key)]

    owned: dict[str, list[SemanticSpan]] = {}
    for c in batch.components:
        if c.record is not None:
            owned.setdefault(c.record, []).extend(
                spans[at(c, t)] for t in read_by(c) if t not in c.context
            )
    section_reads = {
        (c.entry, spans[at(c, t)].span_id)
        for c in batch.components
        if c.record is None
        for t in read_by(c)
        if t not in c.context
    }
    for key, _, entry in batch.records:
        if not owned.get(key):
            raise ValueError(f"record {key} owns no reviewed span")
        if reread := sorted(
            {s.span_id for s in owned[key] if (entry, s.span_id) in section_reads}
        ):
            raise ValueError(f"section {entry} rereads {reread} owned by {key}")
        edge = RelationshipDraft(
            key,
            batch.record_key(entry),
            (
                RelationshipKind.SCOPED_WITHIN
                if key in batch.scoped_records
                else RelationshipKind.CATALOGUE_MEMBER
            ),
        )
        relationships.append(edge)
        provenance.append(
            claim(
                ProvenanceTargetKind.RELATIONSHIP,
                relationship_target_key(edge),
                min(owned[key], key=lambda s: (order[s.leaf_id], s.char_start)),
            )
        )

    for source, target, kind, entry, text in batch.edges:
        if (entry, text) not in spans:
            raise ValueError(f"edge {source} -> {target} cites unreviewed {text!r}")
        edge = RelationshipDraft(source, target, kind)
        if edge in relationships:
            raise ValueError(f"edge {source} -> {target} ({kind}) is declared twice")
        relationships.append(edge)
        provenance.append(
            claim(
                ProvenanceTargetKind.RELATIONSHIP,
                relationship_target_key(edge),
                spans[(entry, text)],
            )
        )

    # Two placed entries may share one record: a section the release prints
    # apart from the section the source sets it in (*Troubleshooting* under
    # *Combat Encounters*) stays its own review unit and is read into that
    # record. The record is emitted once, and only if its kind agrees.
    kinds: dict[str, RecordKind] = {}
    for slug, _, record_kind in batch.entries:
        if kinds.setdefault(batch.record_key(slug), record_kind) is not record_kind:
            raise ValueError(f"record {batch.record_key(slug)} is given two kinds")
    representation = RepresentationDraft(
        records=tuple(RecordDraft(semantic_key=k, kind=v) for k, v in kinds.items())
        + tuple(RecordDraft(semantic_key=k, kind=kind) for k, kind, _ in batch.records),
        components=tuple(components),
        prose_bindings=tuple(bindings),
        relationships=tuple(relationships),
        references=tuple(references),
        provenance=tuple(provenance),
    )

    # Review units: one per printed entry. Expected rules come from the source
    # review (clauses), never from the components emitted above, and every
    # other leaf is named: the heading is excluded and framing is supporting.
    # A leaf neither reaches is left unaccounted for review_unit_violations.
    rules: dict[str, list[ExpectedRule]] = {slug: [] for slug, _, _ in batch.entries}
    # A span a declared record owns is expected there, from the components
    # the review declared (never from the output), and not of the section:
    # the families its clause declared follow it to the one component owning
    # it. Declared prose is expected below, on each prose-carrying component.
    member_owners: dict[str, set[tuple[str, str]]] = {}
    for c in batch.components:
        if c.record is not None:
            for t in read_by(c):
                if t not in c.context:
                    member_owners.setdefault(spans[at(c, t)].span_id, set()).add(
                        (c.record, c.key)
                    )
    reviewed: dict[str, set[str | None]] = {}
    for entry, key, expects, texts in batch.clauses:
        ids = tuple(spans[(entry, t)].span_id for t in texts)
        for i in ids:
            reviewed.setdefault(i, set()).update(expects)
        kept = tuple(i for i in ids if i not in member_owners)
        if kept:
            rules[entry].extend(
                ExpectedRule(batch.record_key(entry), key, e, kept) for e in expects
            )
        families = [e for e in expects if e is not None]
        moved: dict[tuple[str, str], list[str]] = {}
        for i in ids:
            if i in member_owners and families:
                if len(member_owners[i]) != 1:
                    raise ValueError(
                        f"clause {(entry, key)} expects {families} of span {i}, "
                        f"which {sorted(member_owners[i])} all own"
                    )
                (owner,) = member_owners[i]
                moved.setdefault(owner, []).append(i)
        for (record, component), moved_ids in moved.items():
            rules[entry].extend(
                ExpectedRule(record, component, e, tuple(moved_ids)) for e in families
            )
    # A declared record's component was read from its host entry's source, so
    # the entry's unit expects its prose there too. A structured one carries
    # no prose, so each span it owns must have been reviewed as typed families
    # alone, which the clauses above now expect of it.
    for c in batch.components:
        if c.record is not None:
            ids = tuple(
                spans[at(c, t)].span_id for t in read_by(c) if t not in c.context
            )
            if c.handling is ComponentHandling.STRUCTURED:
                if any(not reviewed.get(i) or None in reviewed[i] for i in ids):
                    raise ValueError(
                        f"{c.record}/{c.key} must keep its governing prose"
                    )
                continue
            rules[c.entry].append(ExpectedRule(c.record, c.key, None, ids))

    def framing_leaf(entry: str, prefix: str) -> str:
        hits = [
            leaf
            for leaf in entry_leaves[entry]
            if rows[leaf].content.startswith(prefix)
        ]
        if len(hits) != 1:
            raise ValueError(f"framing {entry}/{prefix!r} matches {len(hits)} leaves")
        return hits[0]

    def exact_leaf(entry: str, content: str) -> str:
        # Exact, not a prefix: "#### Range" must not also match "#### Ranged ...".
        hits = [leaf for leaf in entry_leaves[entry] if rows[leaf].content == content]
        if len(hits) != 1:
            raise ValueError(f"leaf {entry}/{content!r} matches {len(hits)} leaves")
        return hits[0]

    def heading_group(slug: str, label: str) -> ExcludedGroup:
        if (placed := batch.placements.get(slug)) is None:
            return ExcludedGroup(
                (framing_leaf(slug, f"#### {label}"),),
                "entry heading: names the entry and states no rule",
            )
        return ExcludedGroup(
            (exact_leaf(slug, placed.heading),),
            "section heading: names the section and states no rule",
        )

    framing: dict[str, list[str]] = {slug: [] for slug, _, _ in batch.entries}
    for entry, prefix in batch.framing:
        framing[entry].append(framing_leaf(entry, prefix))
    # A heading the review reads -- the name, level or category a record is
    # read under -- is authority of that record, not an excluded group.
    read_leaves = {s.leaf_id for s in spans.values()}
    excluded: dict[str, list[ExcludedGroup]] = {
        slug: [
            g for g in (heading_group(slug, label),) if g.leaf_ids[0] not in read_leaves
        ]
        for slug, label, _ in batch.entries
    }
    for entry, contents, reason in batch.excluded:
        # A heading a section prints more than once ("#### Ability Modifier"
        # under each kind of D20 Test) is listed once per printing, and the
        # n-th listing names the n-th printing in source order.
        printed: dict[str, list[str]] = {}
        for heading in contents:
            if heading not in printed:
                printed[heading] = [
                    leaf
                    for leaf in entry_leaves[entry]
                    if rows[leaf].content == heading
                ]
                if len(printed[heading]) != contents.count(heading):
                    raise ValueError(
                        f"leaf {entry}/{heading!r} matches "
                        f"{len(printed[heading])} leaves; "
                        f"the review lists it {contents.count(heading)} times"
                    )
        seen: dict[str, int] = {}
        leaves: list[str] = []
        for heading in contents:
            leaves.append(printed[heading][seen.get(heading, 0)])
            seen[heading] = seen.get(heading, 0) + 1
        excluded[entry].append(ExcludedGroup(tuple(leaves), reason))
    # A section prints whole leaves of example or pointer that no rule's leaf
    # holds; each is named by a group supporting what its spans support. A
    # leaf a rule or framing already reaches gets none, so glossary batches,
    # whose supporting text always shares a clause's leaf, gain no group.
    reached = {
        slug: {
            spans[(slug, t)].leaf_id
            for e, _, _, ts in batch.clauses
            if e == slug
            for t in ts
        }
        | set(framing[slug])
        for slug, _, _ in batch.entries
    }
    loose: dict[str, dict[str, list[str]]] = {slug: {} for slug, _, _ in batch.entries}
    for entry, text, component in batch.supporting:
        leaf = spans[(entry, text)].leaf_id
        held = loose[entry].setdefault(component or "", [])
        if leaf not in reached[entry] and leaf not in held:
            held.append(leaf)

    def supporting_groups(slug: str) -> tuple[SupportingGroup, ...]:
        record = batch.record_key(slug)
        groups = (
            [SupportingGroup(tuple(framing[slug]), record)] if framing[slug] else []
        )
        groups += [
            SupportingGroup(
                tuple(leaves),
                supported(slug, component) if component else record,
                component,
            )
            for component, leaves in loose[slug].items()
            if leaves
        ]
        return tuple(groups)

    units = [
        ReviewUnit(
            unit_id=f"{batch.unit_prefix}/{slug}",
            kind=(
                batch.placements[slug].unit_kind
                if slug in batch.placements
                else ReviewUnitKind.ENTRY
            ),
            leaf_ids=entry_leaves[slug],
            expected_rules=tuple(rules[slug]),
            supporting_groups=supporting_groups(slug),
            excluded_groups=tuple(excluded[slug]),
        )
        for slug, label, _ in batch.entries
    ]

    if illegal := schema_binding_violations(representation, batch.schema):
        raise ValueError(
            f"the batch declares representation schema {batch.schema[0]!r} but "
            "is not admissible under it: " + "; ".join(illegal)
        )
    proposal = replace(
        seed,
        schema_version=batch.schema[0],
        schema_hash=batch.schema[1],
        proposed_spans=tuple(
            sorted(proposed, key=lambda p: (order[p.span.leaf_id], p.span.char_start))
        ),
        proposed_representation=representation,
        proposed_review_units=tuple(units),
        proposal_origin=batch.proposal_origin,
    )
    ledger = ClassificationLedger(
        package_uuid=pkg,
        release_version=rel,
        policy_version=proposal.policy_version,
        policy_hash=proposal.policy_hash,
        spans=tuple(p.span for p in proposal.proposed_spans),
        batches=(),
        acceptances=(),
    )
    return Built(binding, corpus, proposal, ledger, entry_leaves, rows, spans)


def batch_findings(built: Built) -> dict[str, list[str]]:
    """The three batch-scoped checks, keyed by name."""
    p, ledger = built.proposal, built.ledger
    partition: list[str] = []
    for lid in sorted({s.leaf_id for s in ledger.spans}):
        partition.extend(
            validate_partition(
                lid,
                built.corpus.leaf_lengths[lid],
                tuple(s for s in ledger.spans if s.leaf_id == lid),
                require_complete=False,
            )
        )
    return {
        "partition": partition,
        "review_units": review_unit_violations(
            p.proposed_review_units,
            p.proposed_representation,
            p.policy_version,
            ledger.spans,
        ),
        "representation": sorted(
            validate_representation(p.proposed_representation, ledger, built.corpus)
        ),
    }


#: (reader record, reader component) -> the accepted (record, component) whose
#: governing prose it reads as context.
AcceptedReads = Mapping[tuple[str, str], tuple[tuple[str, str], ...]]


def read_accepted(
    built: Built, accepted: RepresentationDraft, reads: AcceptedReads
) -> Built:
    """*built* with its components reading accepted prose of an earlier batch.

    Each read copies the accepted owner's bindings -- same chunk, span and
    extent -- under the reader's own keys and reasons, claimed CONTEXTUAL. The
    owner keeps the span; this batch neither proposes nor re-accounts it, so
    a proposal validated alone cannot see it (:func:`accepted_read_findings`)
    and a merged candidate can.
    """
    rep = built.proposal.proposed_representation
    own = {
        (b.record_key, b.component_key): b
        for b in reversed(rep.prose_bindings)
        if not b.option_key
    }
    proposed = {p.span.span_id for p in built.proposal.proposed_spans}
    bindings, claims = list(rep.prose_bindings), list(rep.provenance)
    for reader, owners in reads.items():
        if reader not in own:
            raise ValueError(f"{reader}: no component-wide binding to read with")
        for owner in owners:
            source = [
                b
                for b in accepted.prose_bindings
                if (b.record_key, b.component_key) == owner
            ]
            if not source:
                raise ValueError(f"{reader} reads unaccepted {owner}")
            for b in source:
                if b.span_id in proposed:
                    raise ValueError(f"{reader} reads proposed span {b.span_id}")
                copy = replace(
                    b,
                    record_key=reader[0],
                    component_key=reader[1],
                    option_key="",
                    irreducibility_reason_code=own[reader].irreducibility_reason_code,
                    prose_retention_reason_code=own[reader].prose_retention_reason_code,
                )
                bindings.append(copy)
                claims.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.PROSE_BINDING,
                        prose_binding_target_key(copy),
                        b.span_id,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
    rep = replace(rep, prose_bindings=tuple(bindings), provenance=tuple(claims))
    return replace(built, proposal=replace(built.proposal, proposed_representation=rep))


def accepted_read_findings(
    accepted: RepresentationDraft,
    reads: AcceptedReads,
    reasons: Mapping[tuple[str, str], str],
) -> list[str]:
    """The findings :func:`read_accepted` leaves on a proposal validated alone.

    Three per copied binding, all "that span is not this batch's": the binding
    names no span of the proposal, nor does its claim, so nothing traces it.
    Each vanishes when the proposal is validated with the accepted batch.
    *reasons* is each reader's own binding reason, which the copy states.
    """
    found: list[str] = []
    for reader, owners in reads.items():
        for owner in owners:
            for b in accepted.prose_bindings:
                if (b.record_key, b.component_key) != owner:
                    continue
                copy = replace(
                    b,
                    record_key=reader[0],
                    component_key=reader[1],
                    option_key="",
                    irreducibility_reason_code=reasons[reader],
                    prose_retention_reason_code=None,
                )
                key = list(prose_binding_target_key(copy))
                found += [
                    f"prose binding {reader[0]}/{reader[1]}: unknown accepted span "
                    f"{b.span_id!r}",
                    f"prose_binding {key}: no provenance to a 5c leaf subspan",
                    f"provenance prose_binding{key}: unknown span {b.span_id}",
                ]
    return found


def unknown_target_findings(
    record_references: tuple[RecordReference, ...],
    components: tuple[EntryComponent, ...],
    targets: Collection[Target],
) -> list[str]:
    """The ``unknown target record`` findings *targets* leave, and only those.

    One finding per reference :func:`build_entry_batch` drafts: each
    component's own pointer, and a record's pointer only where no component of
    that record states it -- so one pointer held by several records is several.
    """
    stated = {(c.entry, c.key, text, t) for c in components for text, t in c.refs}
    owned = {
        (e, text, t)
        for e, text, t, _ in record_references
        if not any((e, text, t) == (s[0], s[2], s[3]) for s in stated)
    }
    pointers = [(text, t) for *_, text, t in (*stated, *owned)]
    return sorted(
        f"reference {scoped(target)[0]}:{text!r}: unknown target record "
        f"{scoped(target)[1]}"
        for text, target in pointers
        if target in targets
    )


def render(proposal: MechanicalProposal) -> str:
    return (
        json.dumps(
            proposal_payload(proposal), indent=1, sort_keys=True, ensure_ascii=False
        )
        + "\n"
    )


def emit(
    db: str,
    build: Callable[[Session], Built],
    out: Path,
    expected_representation: list[str],
) -> int:
    """Build against the published release in *db*, check, and write *out*."""
    from afterworlds.persistence.database import (
        create_engine,
        create_session_factory,
    )

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        built = build(session)
        found = batch_findings(built)
    engine.dispose()
    if found["partition"] or found["review_units"]:
        raise ValueError(found)
    if found["representation"] != expected_representation:
        raise ValueError(found["representation"])
    if {p.span.review_state for p in built.proposal.proposed_spans} != {
        ReviewState.PROPOSED
    }:
        raise ValueError("a proposal holds only PROPOSED spans")

    data = render(built.proposal).encode("utf-8")
    out.write_bytes(data)
    rep = built.proposal.proposed_representation
    units = built.proposal.proposed_review_units
    b = built.binding
    print(f"release           {b.package_uuid} / {b.release_version}")
    print(f"proposal          {out.name} ({len(data)} bytes)")
    print(f"proposal_identity {proposal_identity(built.proposal)}")
    print(f"file_sha256       {hashlib.sha256(data).hexdigest()}")
    print(
        f"leaves {sum(map(len, built.entry_leaves.values()))}  "
        f"spans {len(built.proposal.proposed_spans)}"
    )
    print(
        f"records {len(rep.records)}  components {len(rep.components)}  "
        f"facts {sum(len(c.all_facts()) for c in rep.components)}  "
        f"bindings {len(rep.prose_bindings)}  references {len(rep.references)}  "
        f"provenance {len(rep.provenance)}"
    )
    print(
        f"units {len(units)}  expected rules "
        f"{sum(len(u.expected_rules) for u in units)}"
    )
    for k, v in found.items():
        print(f"{k:15s}  {len(v)} findings")
        for f in v:
            print(f"   - {f}")
    return 0
