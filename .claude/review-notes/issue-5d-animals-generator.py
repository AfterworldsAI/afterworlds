# ruff: noqa: E501  -- patterns are verbatim source text, kept whole to be greppable
"""Author the **Animals** proposal: the 95 stat blocks the SRD prints there.

REVIEW MATERIAL for CRD Issue 5d (#137) over the Monsters-corrected private
release ``67c81736-15fd-5e82-8523-e84922f0a7c6`` / ``5.2.1-corpus.3fe24ff6-4e3``,
composed over the committed twenty-one-batch oracle that records *Monsters*
(``srd-5-2-1-corpus-3fe24ff6-4e3.json``). It emits one *unaccepted*
``5d-proposal-2`` artifact and one file of unrecorded resolution drafts. It
accepts nothing, publishes nothing, writes nothing under ``oracles/`` and
records no resolution.

Scope, 835 leaves (pp344-364 of the official PDF): every leaf of the *Animals*
part below its ``# Animals`` heading; the part heading stays with the other
part headings (shared coverage is deferred). None was accepted before, and no
accepted record holds any of these stat blocks: no *Monsters* stat block, and
no Spell or Item creature, shares an *Animals* name. The qualified leaf texts
are ``issue-5d-animals-source.py``; this file reads them from there.

Record grain: *Animals* prints its stat blocks directly under the part, with
no group heading, so each of the 95 ``##`` stat blocks is a ``creature``
record ``animals.<block>`` of its own. A creature has one prose component per
printed container, as the accepted *Monsters* creatures do: its own leaves
(heading, type line, combat highlights, ability table, details) keyed by its
own slug, then *Traits*, *Actions*, *Bonus Actions* and *Reactions* where
printed, each with its ``###`` heading.

Every component is prose-bound (ADR-005d Decision 4, as *Monsters*). The one
component naming the GM, the *Swarm of Insects*' "Climb or Fly 20 ft. (GM's
choice)", chooses among printed options (``NOT_LATITUDE``, the accepted
*Half-Dragon* precedent); every component states no identified structured use.

References, once per component, by the accepted *Monsters* reading: each
accepted Rules Glossary term the prose depends on, and every spell named in
italics, to its accepted record. *Animals* names no other creature in bold and
prints no quoted pointer.

Governing context: the source treats *Animals* as a section of *Monsters*
(*Wild Shape*: "see "Animals" in "Monsters""; *Polymorph*: "See the "Animals"
section of "Monsters""), so a stat block here is governed by the accepted
*Parts of a Stat Block* rules exactly as a *Monsters A-Z* one is. Each
component reads, ``CONTEXTUAL``, the same exact accepted spans the *Monsters*
generator selects for the same printed text (``header_context`` and
``part_context``). They are an earlier batch's: read in place through
:func:`read_accepted`, from an accepted representation cut to the chosen
spans, so each stays owned (``PRIMARY``) by its accepted rules component; an
override or disable of that owner suppresses it on the animal, and a combined
reading does not repeat it. The release prints *Animals* before *Monsters*, so
a component reads its own text, then the rules governing it.

Run: ``python issue-5d-animals-generator.py <published afterworlds.db>``
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from functools import cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import (
    Built,
    EntryBatch,
    EntryComponent,
    Placement,
    Target,
    accepted_read_findings,
    build_entry_batch,
    emit,
    read_accepted,
    scoped,
)
from afterworlds.ingestion.mechanical.authoring import batch_findings as batch_findings
from afterworlds.ingestion.mechanical.authoring import render as render
from afterworlds.ingestion.mechanical.bound_corpus import published_release_binding
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReleaseBinding,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    RecordKind,
    RepresentationDraft,
)
from afterworlds.persistence.orm.corpus import LedgerLeafORM

ORIGIN = "issue-5d-animals-generator.py"
PROPOSAL_FILE = "issue-5d-animals-PROPOSAL.json"
DRAFTS_FILE = "issue-5d-animals-resolutions-DRAFTS.json"
#: Every record here is placed; the unplaced-entry default is never read.
PARENT = ("Rules Glossary", "Rules Definitions")
PART = "Animals"
ANIMALS = "srd-5.2.1/animals"
#: The release, and the committed oracle recording *Monsters*, composed over.
RELEASE = ("67c81736-15fd-5e82-8523-e84922f0a7c6", "5.2.1-corpus.3fe24ff6-4e3")
CURRENT_SHA256 = "02f3a11b765d1941aedeacc3244ce66f94ae4409a420e6be565aecd07b45dc54"
UNRESOLVED_TARGET = ""
NO_USE = "no_identified_structured_use"
P = ComponentHandling.PROSE_BOUND


def _load(name: str) -> object:
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(f"{name}.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


#: (full label path, exact text) of every scoped leaf, in printed order.
LEAVES: tuple[tuple[tuple[str, ...], str], ...] = _load("issue-5d-animals-source").LEAVES  # type: ignore[attr-defined]
#: The accepted *Monsters* generator: its governing-context selection and its
#: stat-block reference reading, applied here unchanged.
MG = _load("issue-5d-monsters-generator")
MONSTERS: str = MG.MONSTERS  # type: ignore[attr-defined]
slug = MG.slug  # type: ignore[attr-defined]
#: The accepted rules record a stat block is governed by.
RULES_RECORD = "monsters.parts_of_a_stat_block"


def texts_at(path: tuple[str, ...]) -> list[str]:
    """The leaves printed directly in *path*, not in a container below it."""
    return [t for p, t in LEAVES if p == path]


def children(path: tuple[str, ...]) -> list[str]:
    """The labels of *path*'s sub-containers, in printed order."""
    return list(
        dict.fromkeys(
            p[len(path)]
            for p, _ in LEAVES
            if p[: len(path)] == path and len(p) > len(path)
        )
    )


#: The stat blocks, in printed order.
NAMES = tuple(children((PART,)))
assert len(NAMES) == 95 and not texts_at((PART,))
BLOCK_PARTS = ("Traits", "Actions", "Bonus Actions", "Reactions")
for _n in NAMES:
    _h, _type, *_ = texts_at((PART, _n))
    assert _h == f"## {_n}" and MG.TYPE_LINE.fullmatch(_type), _n  # type: ignore[attr-defined]
    assert [c for c in BLOCK_PARTS if c in children((PART, _n))] == children(
        (PART, _n)
    ), _n
    for _c in children((PART, _n)):
        assert not children((PART, _n, _c)) and texts_at((PART, _n, _c))[0] == (
            f"### {_c}"
        )
    _own = [t for p, t in LEAVES if p[:2] == (PART, _n)]
    assert len(_own) == len(set(_own)), _n


def animal_key(name: str) -> str:
    return f"animals.{slug(name)}"


#: Each stat block by its printed name: every name is printed once, and no
#: accepted *Monsters* stat block shares one.
ANIMAL_KEY = {n: animal_key(n) for n in NAMES}
assert len(set(ANIMAL_KEY.values())) == len(NAMES)
assert not set(MG.BLOCK_KEY) & set(NAMES)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Latitude
# ---------------------------------------------------------------------------
#: (entry, component key) -> the printed words naming the GM that only choose
#: among printed options, and so are reducible.
NOT_LATITUDE: dict[tuple[str, str], str] = {
    (
        slug("Swarm of Insects"),
        slug("Swarm of Insects"),
    ): "Climb or Fly 20 ft. (GM's choice)",
}
READ_AS_OPTIONS: set[tuple[str, str]] = set()


def reason(entry: str, key: str, texts: tuple[str, ...]) -> str:
    if (words := NOT_LATITUDE.get((entry, key))) is not None:
        assert any(words in t for t in texts), (entry, key)
        READ_AS_OPTIONS.add((entry, key))
    else:
        assert not any(MG.DELEGATING.search(t) for t in texts), (entry, key)  # type: ignore[attr-defined]
    return NO_USE


# ---------------------------------------------------------------------------
# The chunk
# ---------------------------------------------------------------------------
class Chunk:
    """The literal review data of the packet, gathered in printed order."""

    def __init__(self) -> None:
        self.entries: list[tuple[str, str, RecordKind]] = []
        self.placements: dict[str, Placement] = {}
        self.clauses: list[tuple[str, str, tuple[str | None, ...], tuple[str, ...]]] = (
            []
        )
        self.components: list[EntryComponent] = []
        #: (record key, component key) -> the exact accepted rules texts that
        #: govern it, in source order.
        self.context: dict[tuple[str, str], tuple[str, ...]] = {}

    def section(
        self,
        entry: str,
        own: str,
        key: str,
        texts: tuple[str, ...],
        refs: tuple[tuple[str, Target], ...],
        context: tuple[tuple[str, str], ...],
    ) -> None:
        assert texts, (entry, key)
        self.clauses.append((entry, key, (None,), texts))
        self.components.append(
            EntryComponent(entry, key, P, reason(entry, key, texts), refs=refs)
        )
        self.context[(own, key)] = tuple(t for t, _ in context)

    def batch(self) -> EntryBatch:
        return EntryBatch(
            origin=ORIGIN,
            proposal_origin=f"{ORIGIN} (CRD Issue 5d animals; unaccepted)",
            unit_prefix="animals",
            parent=PARENT,
            entries=tuple(self.entries),
            expected_leaves=len(LEAVES),
            clauses=tuple(self.clauses),
            framing=(),
            components=tuple(self.components),
            supporting=(),
            record_references=(),
            placements=self.placements,
            members=(),
            edges=(),
        )

    def record_keys(self) -> set[str]:
        return {p.record_key for p in self.placements.values()}


#: Every component that names a spell, and every one that casts one.
NAMING: set[tuple[str, str]] = set()
CASTING: set[tuple[str, str]] = set()


def animals_chunk() -> Chunk:
    chunk = Chunk()
    for name in NAMES:
        path = (PART, name)
        entry, own = slug(name), animal_key(name)
        chunk.entries.append((entry, name, RecordKind.CREATURE))
        chunk.placements[entry] = Placement(
            own, path, f"## {name}", ReviewUnitKind.ENTRY
        )
        ts = tuple(texts_at(path))
        refs, names_spell = MG.creature_refs(own, ts)  # type: ignore[attr-defined]
        assert not names_spell, name
        chunk.section(entry, own, slug(name), ts, refs, MG.header_context(ts))  # type: ignore[attr-defined]
        for part in children(path):
            ts = tuple(texts_at((*path, part)))
            at = (entry, slug(part))
            refs, names_spell = MG.creature_refs(own, ts)  # type: ignore[attr-defined]
            casts = MG._casts_spells(ts)  # type: ignore[attr-defined]
            # Every spell an animal names is one it casts.
            assert casts == names_spell, at
            if names_spell:
                NAMING.add(at)
            if casts:
                CASTING.add(at)
            chunk.section(
                entry, own, slug(part), ts, refs, MG.part_context(part, ts, casts)  # type: ignore[attr-defined]
            )
    return chunk


ANIMALS_CHUNK = animals_chunk()
assert set(NOT_LATITUDE) == READ_AS_OPTIONS
# The *Giant Owl* alone casts: _Detect Evil and Good_, _Detect Magic_,
# _Clairvoyance_.
assert CASTING == NAMING == {(slug("Giant Owl"), "actions")}
# Every reference is to an accepted record: none names this packet's own.
assert (
    not {scoped(t)[1] for c in ANIMALS_CHUNK.components for _, t in c.refs}
    & ANIMALS_CHUNK.record_keys()
)


def batch() -> EntryBatch:
    return ANIMALS_CHUNK.batch()


# ---------------------------------------------------------------------------
# The accepted rules read in place
# ---------------------------------------------------------------------------
@cache
def current() -> AcceptedInputs:
    """The oracle this packet composes over: the twenty-one batches as the
    Owner's *Monsters* acceptance recorded them, rebuilt from its recorded
    times, since the committed file now also records *Animals*."""
    rec = _load("issue-5d-monsters-corrections-ACCEPT")
    base = rec.recorded()  # type: ignore[attr-defined]
    at = rec.RECORDED_AT  # type: ignore[attr-defined]
    inputs: AcceptedInputs = rec.monsters_resolved(  # type: ignore[attr-defined]
        base,
        rec.monsters_accepted(base, rec.OWNER, at[1]),  # type: ignore[attr-defined]
        rec.OWNER,  # type: ignore[attr-defined]
        at[2],
    )
    assert (
        hashlib.sha256(serialize_accepted_inputs(inputs)).hexdigest() == CURRENT_SHA256
    )
    assert not {
        r.semantic_key
        for r in inputs.oracle.representation.records
        if r.semantic_key.startswith("animals.")
    }
    return inputs


#: reader (record, component) -> {owner (record, component): accepted span ids}.
Reads = dict[tuple[str, str], dict[tuple[str, str], tuple[str, ...]]]


def reads(session: Session) -> Reads:
    """Each component's chosen governing texts, as the accepted spans of
    *Parts of a Stat Block* that print them. A text is one whole leaf, bound
    once by one rules component; one that is not fails here, loudly."""
    accepted = current().oracle
    located = {s.span_id: s for s in accepted.spans}
    bindings = [
        b
        for b in accepted.representation.prose_bindings
        if b.record_key == RULES_RECORD
    ]
    content = dict(
        session.execute(
            select(LedgerLeafORM.leaf_id, LedgerLeafORM.content).where(
                LedgerLeafORM.package_uuid == accepted.binding.package_uuid,
                LedgerLeafORM.leaf_id.in_(
                    {located[b.span_id].leaf_id for b in bindings}
                ),
            )
        ).all()
    )
    at: dict[str, list[tuple[str, str]]] = {}
    for b in bindings:
        span = located[b.span_id]
        leaf = content[span.leaf_id]
        assert (span.char_start, span.char_end) == (0, len(leaf)), b.span_id
        at.setdefault(leaf, []).append((b.component_key, b.span_id))
    out: Reads = {}
    for reader, texts in ANIMALS_CHUNK.context.items():
        owners: dict[tuple[str, str], list[str]] = {}
        for t in texts:
            ((component, span_id),) = at[t]
            owners.setdefault((RULES_RECORD, component), []).append(span_id)
        out[reader] = {o: tuple(s) for o, s in owners.items()}
    return out


def _cut(accepted: RepresentationDraft, span_ids: set[str]) -> RepresentationDraft:
    """*accepted* with only the rules bindings of *span_ids*."""
    return replace(
        accepted,
        prose_bindings=tuple(
            b
            for b in accepted.prose_bindings
            if b.record_key == RULES_RECORD and b.span_id in span_ids
        ),
    )


def _each_read(
    session_reads: Reads,
) -> list[
    tuple[RepresentationDraft, dict[tuple[str, str], tuple[tuple[str, str], ...]]]
]:
    accepted = current().oracle.representation
    return [
        (
            _cut(accepted, {s for ss in owners.values() for s in ss}),
            {reader: tuple(owners)},
        )
        for reader, owners in session_reads.items()
    ]


def build(session: Session) -> Built:
    """Derive the animals proposal from the release *session* published, each
    component reading the accepted rules governing it."""
    built = build_entry_batch(session, batch(), published_release_binding(session))
    for cut, read in _each_read(reads(session)):
        built = read_accepted(built, cut, read)
    return built


def unresolved(chunk: Chunk) -> list[tuple[str, str]]:
    """Printed pointers whose destination has no record yet, as (scope, text)."""
    return sorted(
        (scoped(t)[0], text)
        for c in chunk.components
        for text, t in c.refs
        if scoped(t)[1] == UNRESOLVED_TARGET
    )


def expected_representation_findings(chunk: Chunk, session_reads: Reads) -> list[str]:
    """What the packet alone cannot see: accepted targets and accepted reads.

    One finding per component reference to an accepted record, and three per
    accepted rules binding a component reads -- each valid once the packet is
    read over the accepted oracle, which the composition check shows.
    """
    assert not unresolved(chunk)
    reasons = {
        (chunk.placements[c.entry].record_key, c.key): c.reason
        for c in chunk.components
    }
    return sorted(
        [
            *(
                f"reference {scoped(t)[0]}:{text!r}: unknown target record {scoped(t)[1]}"
                for c in chunk.components
                for text, t in c.refs
            ),
            *(
                f
                for cut, read in _each_read(session_reads)
                for f in accepted_read_findings(cut, read, reasons)  # type: ignore[arg-type]
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Unrecorded resolution drafts for the same Owner packet
# ---------------------------------------------------------------------------
_BUDGET = ("gameplay_toolbox.combat_encounters", "step_3_spend_your_budget")
#: Accepted plural pointers, reviewed one by one, to the stat block their own
#: source names: the encounter example's "2 **Giant Wasps** (100 XP each)" and
#: "6 **Giant Rats** (25 XP each)", at their stat blocks' XP, and the *Robe of
#: Useful Items* patch "2 Mastiffs".
PLURAL_DRAFTS: dict[tuple[str, str, str], str] = {
    (*_BUDGET, "Giant Wasps"): "Giant Wasp",
    (*_BUDGET, "Giant Rats"): "Giant Rat",
    ("magic_items.robe_of_useful_items", "robe_of_useful_items", "Mastiffs"): "Mastiff",
}
#: The chapter pointers left unresolved: *Wild Shape* and *Polymorph*'s
#: "Animals", and every "Monsters".
CHAPTERS = frozenset({"Animals", "Monsters"})


def draft_targets(
    prior: AcceptedInputs,
) -> tuple[
    list[tuple[str, str, str, str, str, tuple[str, ...]]],
    list[tuple[str, str, str, str]],
]:
    """(drafts, left): each accepted unresolved *Monsters* or *Animals* pointer
    whose printed text is exactly one *Animals* stat block's name, or a
    reviewed plural of one (``PLURAL_DRAFTS``), to that creature in the
    pointer's own scope, with the spans the oracle cites it from; and every
    other one (a chapter pointer), left unresolved as printed."""
    from afterworlds.ingestion.mechanical.representation import (
        ProvenanceTargetKind,
        reference_target_key,
    )

    rep = prior.oracle.representation
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in rep.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    resolved = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in prior.oracle.reference_resolutions
    }
    drafts, left = [], []
    for ref in rep.references:
        if ref.scope_key not in (MONSTERS, ANIMALS) or ref.target_record_key:
            continue
        where = (ref.from_record_key, ref.from_component_key, ref.source_text)
        if (*where, ref.scope_key) in resolved:
            continue
        name = PLURAL_DRAFTS.get(where, ref.source_text)
        if name in ANIMAL_KEY:
            spans = tuple(cited[reference_target_key(ref)])
            assert spans, where
            drafts.append((*where, ref.scope_key, ANIMAL_KEY[name], spans))
        else:
            assert ref.source_text in CHAPTERS, where
            left.append((*where, ref.scope_key))
    assert set(PLURAL_DRAFTS) <= {d[:3] for d in drafts}
    return drafts, left


def draft_resolutions(
    binding: ReleaseBinding, prior: AcceptedInputs
) -> tuple[ReferenceResolution, ...]:
    drafts, _ = draft_targets(prior)
    out = tuple(
        ReferenceResolution(
            resolution_id=f"resolve-{MG._slug(record)}-{MG._slug(component) or 'record'}-{MG._slug(text)}-animals-1",  # type: ignore[attr-defined]
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=scope,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, scope, target, spans in drafts
    )
    ids = {r.resolution_id for r in out}
    assert len(ids) == len(out)
    assert not ids & {r.resolution_id for r in prior.oracle.reference_resolutions}
    return out


def main(db: str) -> int:
    here = Path(__file__).resolve().parent
    from afterworlds.persistence.database import create_engine, create_session_factory

    engine = create_engine(f"sqlite:///{db}")
    with create_session_factory(engine)() as session:
        binding = published_release_binding(session)
        session_reads = reads(session)
    engine.dispose()
    prior = current()
    # Only the release the committed oracle is bound to.
    assert binding == prior.oracle.binding, binding
    emit(
        db,
        build,
        here / PROPOSAL_FILE,
        expected_representation_findings(ANIMALS_CHUNK, session_reads),
    )
    drafts = draft_resolutions(binding, prior=prior)
    payload = reference_resolution_payload(drafts)
    (here / DRAFTS_FILE).write_bytes(
        (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    )
    print(f"drafts            {DRAFTS_FILE} ({len(drafts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
