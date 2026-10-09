"""The remaining-references target-scope candidate, composed in memory.

CRD Issue 5d remaining-references packet (#132, #137). REVIEW MATERIAL:
nothing here is accepted, recorded, published or activated, and no Owner
approval exists for it. There is deliberately no recording step.

Under ADR-005d Decision 7 as amended 2026-09-24 ("A citation of a named item
resolves to that item's one record, not to the section that prints it") each
cited rule printed inside a wider accepted section needs its own record.
:data:`CANDIDATES` declares them through the native seams
(``EntryBatch.records`` and ``EntryComponent.record``) on the accepted
generators' own batches, rebuilt from the release in memory: *Proficiency
Bonus*, *Skill Proficiencies*, *Travel Pace*, *Extreme Cold*, *Magic Item
Values by Rarity* and *Challenge Rating* (six). Each moved component keeps
every expectation its source review stated, typed families included, on its
new record; :func:`main` checks that per span against the accepted
inventory. The same batches
also narrow five pointers to the exact texts that print each occurrence
(:data:`RETEXT`, :data:`RECORD_RETEXT`), declare the nine sections printed
under ``## Casting Spells`` its members
(:data:`CASTING_SPELLS_MEMBERS`, through ``EntryBatch.edges``), and re-author
the consecutive schema-15 batches from *Checks, Actions and Rests* up to the
existing schema-16 transition under schema 16 (:data:`SCHEMA_16`), so the
recorded lift moves earlier and no batch or rule is added.

Three moved components carry a recorded resolution, whose reference identity
therefore changes. Each is dropped from its recorded step and drafted afresh
by ``REKEYED`` in the generator; none is carried over (:func:`chain`).

The acceptance module has no supersession, so the changed batches are shown as
one fresh chain over no prior, as the accepted Equipment chain was recorded
(``issue-5d-equipment-cited-targets-ACCEPT.py``): the twenty-two recorded
proposals, eight rebuilt under the simulated reviewer and fourteen read from
their recorded bytes; every other recorded resolution re-applied verbatim with
its recorded evidence; then the reviewed drafts, simulated. A control run with
no candidate must rebuild the accepted artifact byte for byte.

Run: ``python issue-5d-remaining-references-REPLACEMENT.py [--delta PATH]``.
Writes nothing but ``--delta PATH`` when asked.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from uuid import UUID

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.authoring import (  # noqa: E402
    EntryBatch,
    EntryComponent,
    build_entry_batch,
    read_accepted,
    render,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    published_release_binding,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    ProvenanceRole,
    ProvenanceTargetKind,
    RelationshipKind,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    SCHEMA_16_HASH,
    SCHEMA_16_VERSION,
)
from afterworlds.models.enums import (  # noqa: E402
    OverrideOperationEnum,
    OverrideOriginEnum,
)
from afterworlds.models.rules_package import RulesPackageBinding  # noqa: E402
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.services.rules_authority.application import (  # noqa: E402
    SourceProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.override_set import (  # noqa: E402
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import (  # noqa: E402
    source_leaf_order,
)
from afterworlds.services.rules_authority.targets import (  # noqa: E402
    MechanicalTarget,
    MechanicalTargetKind,
)


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The accepted chain's composition (proposals, evidence, resolution steps).
REPL = _load(
    "equipment_cited_targets_replacement",
    HERE / "issue-5d-equipment-cited-targets-REPLACEMENT.py",
)
GEN = _load(
    "remaining_references_generator",
    HERE / "issue-5d-remaining-references-generator.py",
)

ACCEPTED_PATH: Path = GEN.ORACLE
ACCEPTED_SHA256 = "76a16103a08db564ee00b9c8d493d2f5dd48b05e312c77780dd3a74639da86ac"
CITED_SUFFIX: str = REPL.CITED_SUFFIX
SCRATCH_DB: Path = REPL.SCRATCH_DB

#: batch -> ((record key, host entry, components it owns in printed order), ...).
#: Each record takes its host entry's record kind.
CANDIDATES: dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]] = {
    "checks-actions-rests": (
        (
            "play.proficiency.proficiency_bonus",
            "proficiency",
            (
                "proficiency_bonus",
                "proficiency_bonus_bands",
                "d20_test_application",
                "spell_uses",
                "bonus_operation_limits",
            ),
        ),
        (
            "play.proficiency.skill_proficiencies",
            "proficiency",
            ("skills", "skill_proficiency", "skill_list", "determining_skills"),
        ),
    ),
    "core-play-completion": (
        (
            "play.exploration.travel_pace",
            "exploration",
            ("travel_pace", "pace_effects"),
        ),
    ),
    "gameplay-toolbox": (
        (
            "gameplay_toolbox.environmental_effects.extreme_cold",
            "environmental_effects",
            ("extreme_cold",),
        ),
    ),
    "magic-items": (
        (
            "magic_items.magic_item_rarity.magic_item_values_by_rarity",
            "magic_item_rarity",
            ("magic_item_values_by_rarity",),
        ),
    ),
    "monsters": (
        (
            "monsters.parts_of_a_stat_block.challenge_rating",
            "parts_of_a_stat_block",
            ("challenge_rating", "experience_points", "proficiency_bonus"),
        ),
    ),
}

#: batch -> (entry, component) -> (printed pointer, the exact texts printing
#: its occurrences, in its place). Each keeps the pointer's unresolved scope;
#: the review grades each text.
RETEXT: dict[str, dict[tuple[str, str], tuple[str, tuple[str, ...]]]] = {
    "core-play-completion": {
        ("exploration", "weapons_beyond_battle"): (
            "Equipment",
            ('The weapons in "Equipment"',),
        ),
    },
    "spellcasting": {
        # Its other occurrence qualifies "Component Pouch", which is resolved.
        ("components", "component_pouch_and_focus"): (
            "Equipment",
            ('see "Equipment" for descriptions',),
        ),
    },
    "magic-items": {
        ("time_and_cost", "time_and_cost"): (
            "Equipment",
            (
                'whose crafting time and cost are given in "Equipment."',
                'craft that item using the rules in "Equipment."',
            ),
        ),
        # Its other occurrence qualifies "Scribing Spell Scrolls", resolved.
        ("magic_item_rarity", "magic_item_values_by_rarity"): (
            "Equipment",
            ('a purchase cost in "Equipment"',),
        ),
        ("magic_items_a_z", "magic_items_a_z"): (
            "Monsters",
            (
                'the stat block is in "Monsters."',
                'How to read and use a stat block is explained in "Monsters."',
            ),
        ),
    },
}

#: batch -> (entry, printed pointer) -> the exact text of its record-owned
#: occurrence, which read the component's pointer while the texts were one.
RECORD_RETEXT: dict[str, dict[tuple[str, str], str]] = {
    "core-play-completion": {
        ("exploration", "Equipment"): 'See "Equipment" for rules on many items',
    },
}

#: The sections the release prints under ``## Casting Spells`` (pp. 104-106:
#: its 14pt Casting Time, Range, Components, Duration and Effects, and the 12pt
#: Targets, Saving Throws, Attack Rolls and Combining Spell Effects under
#: Effects), each a flat CATALOGUE_MEMBER citing its first reviewed clause, as
#: :func:`build_entry_batch` cites a listed member's.
CASTING_SPELLS_MEMBERS = (
    "casting_time",
    "range",
    "components",
    "duration",
    "effects",
    "targets",
    "saving_throws",
    "attack_rolls",
    "combining_spell_effects",
)

#: The consecutive schema-15 batches from the first one a candidate changes up
#: to the existing schema-16 transition, re-authored under schema 16.
SCHEMA_16 = (
    "checks-actions-rests",
    "core-play-completion",
    "core-play-dependencies",
    "character-creation-foundations",
)

CHANGED = (*SCHEMA_16, "spellcasting", "gameplay-toolbox", "magic-items", "monsters")
GENERATORS = {b: HERE / f"issue-5d-{b}-generator.py" for b in CHANGED}

SIMULATED_REVIEWER: str = REPL.SIMULATED_REVIEWER
SIMULATED_RULE: str = REPL.SIMULATED_RULE
SIMULATED_AT: str = REPL.SIMULATED_AT

#: Batches, records, spans, review units, resolutions; then reference and
#: uncovered-leaf findings on the release.
EXPECTED_ACCEPTED = ((22, 1826, 10484, 1459, 1408), (91, 29))
EXPECTED = {
    "candidate": ((22, 1832, 10484, 1459, 1408 - len(GEN.REKEYED)), (97, 29)),
    "drafted": ((22, 1832, 10484, 1459, 1408 + len(GEN.DRAFTS)), None),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def accepted() -> AcceptedInputs:
    assert _sha(ACCEPTED_PATH.read_bytes()) == ACCEPTED_SHA256, "accepted changed"
    return load_accepted_inputs(ACCEPTED_PATH)


def candidate_batch(batch: str, base: EntryBatch) -> EntryBatch:
    """*base* with its candidate records declared and their components moved,
    its pointers split, its members declared and its schema lifted."""
    kinds = {slug: kind for slug, _, kind in base.entries}
    declared = CANDIDATES.get(batch, ())
    moved = {(entry, key): record for record, entry, keys in declared for key in keys}
    retext = RETEXT.get(batch, {})
    present = {(c.entry, c.key) for c in base.components}
    assert set(moved) | set(retext) <= present, f"{batch}: absent components"

    def refs(c: EntryComponent) -> tuple[tuple[str, Any], ...]:
        if (c.entry, c.key) not in retext:
            return c.refs
        pointer, texts = retext[(c.entry, c.key)]
        (target,) = [t for x, t in c.refs if x == pointer]
        assert isinstance(target, tuple) and target[1] == "", target
        return tuple(
            r
            for x, t in c.refs
            for r in ([(text, t) for text in texts] if x == pointer else [(x, t)])
        )

    record_retext = RECORD_RETEXT.get(batch, {})
    record_references = tuple(
        (entry, record_retext.get((entry, text), text), target, texts)
        for entry, text, target, texts in base.record_references
    )
    assert len(set(record_references) - set(base.record_references)) == len(
        record_retext
    ), f"{batch}: absent record references"
    edges = base.edges
    if batch == "spellcasting":
        assert not edges
        edges = tuple(
            (
                base.record_key(member),
                base.record_key("casting_spells"),
                RelationshipKind.CATALOGUE_MEMBER,
                member,
                next(ts[0] for e, _, _, ts in base.clauses if e == member),
            )
            for member in CASTING_SPELLS_MEMBERS
        )
    return dataclasses.replace(
        base,
        records=(
            *base.records,
            *((record, kinds[entry], entry) for record, entry, _ in declared),
        ),
        components=tuple(
            dataclasses.replace(
                c, record=moved.get((c.entry, c.key), c.record), refs=refs(c)
            )
            for c in base.components
        ),
        record_references=record_references,
        edges=edges,
        schema=(
            (SCHEMA_16_VERSION, SCHEMA_16_HASH) if batch in SCHEMA_16 else base.schema
        ),
    )


def rebuilt(
    rec: AcceptedInputs, with_candidates: bool
) -> dict[str, MechanicalProposal]:
    """Each changed batch rebuilt from the release and read back from its
    rendered bytes, as a recorded proposal file is; unchanged, those bytes are
    the recorded file's (the control in :func:`main` holds the chain to it).
    Magic items reads the accepted Equipment attunement rules, as its own
    ``build`` does; Equipment is unchanged, so from *rec*."""
    out: dict[str, MechanicalProposal] = {}
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                for batch, path in GENERATORS.items():
                    module = _load(f"rr_{batch.replace('-', '_')}", path)
                    base = module.batch()
                    if with_candidates:
                        base = candidate_batch(batch, base)
                    whole = build_entry_batch(session, base, binding)
                    if batch == "magic-items":
                        whole = read_accepted(
                            whole, rec.oracle.representation, module.CROSS_READS
                        )
                    built = whole.proposal
                    file = Path(tmp) / f"{batch}.json"
                    file.write_bytes(render(built).encode("utf-8"))
                    print(batch, "proposal bytes sha256", _sha(file.read_bytes()))
                    out[batch] = load_proposal(
                        file, expected_identity=proposal_identity(built)
                    )
        finally:
            engine.dispose()
    return out


def _steps(rec: AcceptedInputs, rekeyed: bool) -> dict[str, tuple[Any, ...]]:
    """The recorded resolutions by the step they followed: the 1,247 of the
    recorded manifest, then the 161 cited ones after the last batch; less,
    when *rekeyed*, the three whose reference the candidate re-keys."""
    cited = tuple(
        r
        for r in rec.oracle.reference_resolutions
        if r.resolution_id.endswith(CITED_SUFFIX)
    )
    rest = [
        r
        for r in rec.oracle.reference_resolutions
        if not r.resolution_id.endswith(CITED_SUFFIX)
    ]
    steps: dict[str, tuple[Any, ...]] = REPL._steps(
        SimpleNamespace(oracle=SimpleNamespace(reference_resolutions=rest))
    )
    assert len(cited) == 161 and sum(map(len, steps.values())) == 1247
    out = {**steps, "equipment-cited": cited}
    if not rekeyed:
        return out
    kept = {
        b: tuple(r for r in step if r.resolution_id not in GEN.REKEYED)
        for b, step in out.items()
    }
    dropped = [b for b in out if len(kept[b]) != len(out[b])]
    print("re-keyed recorded resolutions dropped from steps", dropped)
    assert sum(map(len, out.values())) - sum(map(len, kept.values())) == len(
        GEN.REKEYED
    )
    return kept


def chain(
    rec: AcceptedInputs, proposals: dict[str, MechanicalProposal], rekeyed: bool
) -> AcceptedInputs:
    """The recorded chain over no prior, with *proposals* substituted."""
    per, res = REPL._evidence(rec)
    steps = _steps(rec, rekeyed)
    recorded = {b.batch_id: b.proposal_identity for b in rec.batches}
    inputs: AcceptedInputs | None = None

    def resolve(step: tuple[Any, ...]) -> AcceptedInputs:
        assert inputs is not None
        (ev,) = {
            (
                res[r.resolution_id].authorized_by,
                res[r.resolution_id].authorization_reference,
                res[r.resolution_id].reviewer,
                res[r.resolution_id].resolved_at,
            )
            for r in step
        }
        return resolve_references(
            inputs,
            resolutions=step,
            authorized_by=ev[0],
            authorization_reference=ev[1],
            reviewer=ev[2],
            resolved_at=ev[3],
        )

    for batch, proposal in REPL._proposals():
        assert proposal.binding == rec.oracle.binding, batch
        rule, reviewer, at = per[batch]
        if batch in proposals:
            proposal = proposals[batch]
            if proposal_identity(proposal) != recorded[batch]:
                rule, reviewer, at = SIMULATED_RULE, SIMULATED_REVIEWER, SIMULATED_AT
        inputs = accept_proposal(
            proposal,
            batch_id=batch,
            rule=rule,
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            resolved_review_units=tuple(
                u.unit_id for u in proposal.proposed_review_units
            ),
            reviewer=reviewer,
            accepted_at=at,
            prior=inputs,
        )
        if steps.get(batch):
            inputs = resolve(steps[batch])
    inputs = resolve(steps["equipment-cited"])
    return inputs


def drafted(base: AcceptedInputs) -> AcceptedInputs:
    """The reviewed drafts over *base*, simulated."""
    drafts = GEN.draft_resolutions(base.oracle.binding)
    raw = (HERE / GEN.DRAFTS_FILE).read_bytes()
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "drafts drifted"
    return resolve_references(
        base,
        resolutions=drafts,
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    return REPL._counts(inputs)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Consumer check: the rules-authority service's own reading.
# ---------------------------------------------------------------------------
def _disable(kind: MechanicalTargetKind, record: str, component: str | None) -> Any:
    return EffectiveOverrideEntry(
        override_id=f"disable-{record}-{component or 'record'}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(kind=kind, record_key=record, component_key=component),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )


#: Real, non-empty overrides on the candidate: one new record disabled whole,
#: one moved component disabled.
OVERRIDES = (
    _disable(MechanicalTargetKind.RECORD, "play.exploration.travel_pace", None),
    _disable(
        MechanicalTargetKind.COMPONENT,
        "monsters.parts_of_a_stat_block.challenge_rating",
        "experience_points",
    ),
)


def consumer(
    inputs: AcceptedInputs, overrides: tuple[Any, ...] = ()
) -> tuple[dict[str, tuple[str, ...]], dict[str, list[str]], dict[str, list[str]]]:
    """(section -> members, section -> its reading as span ids in reading order,
    record -> its direct read as span ids), from :func:`apply_override_set`
    under *overrides*."""
    candidate = candidate_from_accepted_inputs(inputs)
    binding = inputs.oracle.binding
    state = EffectiveOverrideSet(
        binding.package_uuid, binding.release_version, overrides
    )
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                authority = apply_override_set(
                    candidate,
                    state,
                    RulesPackageBinding(
                        package_uuid=UUID(binding.package_uuid),
                        release_version=binding.release_version,
                        mechanical_projection_uuid=UUID(
                            identify_projection(candidate).projection_uuid
                        ),
                        override_set_uuid=UUID(state.override_set_uuid),
                    ),
                    leaf_order=source_leaf_order(session, candidate),
                )
        finally:
            engine.dispose()
    records = {r.semantic_key: r for r in authority.records}

    def prose(record: str, component: str, ix: tuple[int, ...] | None) -> list[str]:
        (c,) = [c for c in records[record].components if c.semantic_key == component]
        entries = (
            c.governing_prose if ix is None else [c.governing_prose[i] for i in ix]
        )
        return [e.span_id for e in entries if isinstance(e, SourceProse)]

    readings = {
        section: [s for r, c, ix in runs for s in prose(r, c, ix)]
        for section, runs in authority.readings
    }
    direct = {
        key: [s for c in rec.components for s in prose(key, c.semantic_key, None)]
        for key, rec in records.items()
    }
    return dict(authority.members), readings, direct


def owned(inputs: AcceptedInputs) -> dict[str, set[str]]:
    """record -> the spans its components' prose bindings claim PRIMARY."""
    return {r: {s for _, s in cs} for r, cs in owned_by_component(inputs).items()}


def owned_by_component(inputs: AcceptedInputs) -> dict[str, set[tuple[str, str]]]:
    """record -> (component, span) its prose bindings claim PRIMARY."""
    rep = inputs.oracle.representation
    out: dict[str, set[tuple[str, str]]] = {}
    for p in rep.provenance:
        if (
            p.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and p.role is ProvenanceRole.PRIMARY
        ):
            out.setdefault(p.target_key[0], set()).add((p.target_key[1], p.span_id))
    return out


def expectations(inputs: AcceptedInputs) -> Counter[tuple[str, str, str, str, str]]:
    """(unit, record, component, family, span) per span of every reviewed
    expected rule; the family ``""`` is governing prose."""
    return Counter(
        (u.unit_id, r.record_key, r.component_key, r.fact_family or "", s)
        for u in inputs.oracle.review_units
        for r in u.expected_rules
        for s in r.source_span_ids
    )


def dangling_component_claims(inputs: AcceptedInputs) -> list[tuple[str, ...]]:
    """COMPONENT provenance naming no component the representation states."""
    rep = inputs.oracle.representation
    stated = {(c.record_key, c.semantic_key) for c in rep.components}
    return [
        tuple(p.target_key)
        for p in rep.provenance
        if p.target_kind is ProvenanceTargetKind.COMPONENT
        and tuple(p.target_key[:2]) not in stated
    ]


def main(argv: list[str]) -> None:
    if not (argv == [] or (len(argv) == 2 and argv[0] == "--delta")):
        raise SystemExit("usage: [--delta PATH]")
    rec = accepted()
    assert _counts(rec) == EXPECTED_ACCEPTED[0], _counts(rec)
    print("SIMULATED (in memory; nothing accepted or recorded)")

    control = chain(rec, rebuilt(rec, with_candidates=False), rekeyed=False)
    same = serialize_accepted_inputs(control) == ACCEPTED_PATH.read_bytes()
    print(
        "control: chain with the rebuilt, unchanged batches is the accepted artifact",
        same,
    )
    assert same, "the control does not rebuild the accepted artifact"

    proposals = rebuilt(rec, with_candidates=True)
    recorded = {b.batch_id: b.proposal_identity for b in rec.batches}
    for batch, p in proposals.items():
        print(
            "candidate",
            batch,
            p.schema_version,
            "identity",
            proposal_identity(p),
            "changed",
            proposal_identity(p) != recorded[batch],
        )
        assert proposal_identity(p) != recorded[batch], batch
    base = chain(rec, proposals, rekeyed=True)
    final = drafted(base)
    for state, inputs in (("candidate", base), ("drafted", final)):
        o = inputs.oracle
        violations = reference_resolution_violations(
            o.representation, o.reference_resolutions, o.binding
        )
        print(state, "counts", _counts(inputs), "violations", len(violations))
        assert not violations, violations[:5]
        counts, findings = EXPECTED[state]
        assert _counts(inputs) == counts, _counts(inputs)
        got = REPL._findings(inputs)
        print(state, "reference, uncovered-leaf findings", got)
        if findings is not None:
            assert got == findings, got
        dangling = dangling_component_claims(inputs)
        print(state, "component claims naming no stated component", dangling)
        assert not dangling
    print("simulated bytes sha256", _sha(serialize_accepted_inputs(final)))

    # Source review: every reviewed expectation, per span, is carried with its
    # family, unit and component; only its record may change, and then only to
    # the record the candidate declares that component's owner.
    owner = {
        (host, key): record
        for batch, declared in CANDIDATES.items()
        for record, entry, keys in declared
        for host in [
            _load(f"rr_{batch.replace('-', '_')}", GENERATORS[batch])
            .batch()
            .record_key(entry)
        ]
        for key in keys
    }
    reviewed, derived = expectations(rec), expectations(base)
    moved = Counter(
        (u, owner.get((r, c), r), c, f, s)
        for (u, r, c, f, s), n in reviewed.items()
        for _ in range(n)
    )
    rehomed = Counter(k for k in reviewed.elements() if (k[1], k[2]) in owner)
    print(
        "reviewed expectations (per span)",
        sum(reviewed.values()),
        "->",
        sum(derived.values()),
        "| re-owned",
        sum(rehomed.values()),
        "| typed re-owned",
        sum(n for k, n in rehomed.items() if k[3]),
        "| lost",
        sum((moved - derived).values()),
        "| added",
        sum((derived - moved).values()),
    )
    assert moved == derived, (
        list((moved - derived).items())[:5],
        list((derived - moved).items())[:5],
    )
    for record, component, family in (
        ("play.exploration.travel_pace", "pace_effects", "advantage"),
        (
            "play.proficiency.proficiency_bonus",
            "proficiency_bonus_bands",
            "proficiency_bonus_band",
        ),
        (
            "play.proficiency.skill_proficiencies",
            "skill_proficiency",
            "proficiency_application",
        ),
    ):
        spans = sorted(
            s for _, r, c, f, s in derived if (r, c, f) == (record, component, family)
        )
        print("  typed expectation", record, component, family, len(spans), "spans")
        assert spans

    # Preservation: every accepted resolution is kept verbatim, but the three
    # re-keyed, each drafted afresh with only its identity and record changed.
    old = {r.resolution_id: r for r in rec.oracle.reference_resolutions}
    new = {r.resolution_id: r for r in final.oracle.reference_resolutions}
    old_res = Counter(
        json.dumps(r, sort_keys=True)
        for r in reference_resolution_payload(
            tuple(r for i, r in old.items() if i not in GEN.REKEYED)
        )
    )
    new_res = Counter(
        json.dumps(r, sort_keys=True)
        for r in reference_resolution_payload(final.oracle.reference_resolutions)
    )
    print(
        "accepted resolutions kept verbatim",
        not (old_res - new_res),
        sum(old_res.values()),
        "of",
        len(old),
    )
    assert not old_res - new_res
    drafts = {
        (d.from_record_key, d.source_text): d
        for d in GEN.draft_resolutions(rec.oracle.binding)
    }
    for old_id, (record, component, text, scope, target, spans) in GEN.REKEYED.items():
        was, now = old[old_id], drafts[(record, text)]
        assert old_id not in new and now.resolution_id in new
        assert (
            (
                was.from_component_key,
                was.source_text,
                was.scope_key,
                was.target_record_key,
                was.provenance_span_ids,
            )
            == (now.from_component_key, text, scope, target, spans)
            == (
                component,
                text,
                scope,
                target,
                now.provenance_span_ids,
            )
        )
        print(
            f"re-keyed {old_id} ({was.from_record_key}) -> {now.resolution_id}"
            f" ({now.from_record_key}); text, scope, target, spans unchanged"
        )

    # Full text, order-aware: each host keeps its printed text across itself
    # and its new members; each member owns exactly its moved components' spans.
    before, after = owned(rec), owned(base)
    texts = REPL.Delta(rec, final)
    old_members, old_readings, old_direct = consumer(rec)
    members, readings, direct = consumer(base)
    hosts: dict[str, str] = {}
    for batch, declared in CANDIDATES.items():
        gen = _load(f"rr_{batch.replace('-', '_')}", GENERATORS[batch]).batch()
        for record, entry, _ in declared:
            host = hosts[record] = gen.record_key(entry)
            whole = before[host]
            parts = [after[host], *(after[r] for r, e, _ in declared if e == entry)]
            assert set().union(*parts) == whole and sum(map(len, parts)) == len(whole)
            order = sorted(whole, key=texts.position)
            joined = "".join(texts.text(s) for s in order)
            read = readings[host]
            print(
                f"{record}: owns {len(after[record])} of {host}'s {len(whole)} spans;",
                "member of",
                host,
                record in members.get(host, ()),
                "| host reading = accepted text in printed order",
                read == order,
                len(joined),
                _sha(joined.encode("utf-8"))[:16],
            )
            assert record in members[host] and record not in old_members.get(host, ())
            assert read == order, (read[:5], order[:5])
            assert set(direct[record]) >= after[record]
            print(
                "   direct read",
                [texts.text(s)[:60] for s in direct[record]][:3],
                "...",
            )

    # Casting Spells: its printed sections are its members; its reading is its
    # own prose and theirs in printed order, and each still reads directly.
    cs = "spells.casting_spells"
    kids = tuple(f"spells.{m}" for m in CASTING_SPELLS_MEMBERS)
    union = before[cs].union(*(before[k] for k in kids))
    order = sorted(union, key=texts.position)
    print(
        cs,
        "members before",
        old_members.get(cs, ()),
        "after",
        members.get(cs, ()),
        "| catalogue reading before",
        cs in old_readings,
        "| direct read before",
        len(old_direct[cs]),
        "| reading after",
        len(readings[cs]),
        "= own + members in printed order",
        readings[cs] == order,
    )
    assert set(members[cs]) == set(kids) and not old_members.get(cs)
    assert cs not in old_readings
    assert old_direct[cs] == sorted(before[cs], key=texts.position)
    assert direct[cs] == old_direct[cs]
    assert readings[cs] == order
    assert all(before[k] == after[k] for k in (cs, *kids))
    for k in kids[:1] + kids[-1:]:
        print(
            "  ",
            k,
            "direct read",
            len(direct[k]),
            [texts.text(s)[:50] for s in direct[k]][:1],
        )

    # Real overrides: a disabled record leaves its host's reading; a disabled
    # component leaves its record's direct read and its host's reading.
    o_members, o_readings, o_direct = consumer(base, OVERRIDES)
    pace = "play.exploration.travel_pace"
    cr = "monsters.parts_of_a_stat_block.challenge_rating"
    xp = {s for c, s in owned_by_component(base)[cr] if c == "experience_points"}
    still_read = set().union(*o_readings.values(), *o_direct.values())
    gone = set(after[pace]) & still_read
    print(
        "override disable record",
        pace,
        "| in direct reads",
        pace in o_direct,
        "|",
        hosts[pace],
        "still a catalogue",
        hosts[pace] in o_readings,
        "| its spans left in any reading or direct read",
        len(gone),
        "of",
        len(after[pace]),
    )
    print(
        "override disable component",
        f"{cr}/experience_points ({len(xp)} spans)",
        "| left in direct read",
        len(xp & set(o_direct[cr])),
        "| left in",
        hosts[cr],
        "reading",
        len(xp & set(o_readings[hosts[cr]])),
        "| rest of the record still read",
        set(direct[cr]) - xp <= set(o_direct[cr]),
    )
    assert xp and pace not in o_direct and not gone
    assert hosts[pace] not in o_readings and hosts[pace] in o_direct
    assert not xp & set(o_direct[cr])
    assert not xp & set(o_readings[hosts[cr]])
    assert set(direct[cr]) - xp <= set(o_direct[cr])

    summary = {
        ".".join(p): (len(lost), len(added))
        for p, (lost, added) in texts.collections().items()
        if lost or added
    }
    print("candidate delta by collection (-, +)", json.dumps(summary))
    if len(argv) == 2:
        report = texts.report()
        Path(argv[1]).write_bytes(("\n".join(report) + "\n").encode("utf-8"))
        print("delta written", argv[1], len(report), "lines")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
