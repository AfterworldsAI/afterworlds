"""CRD Issue 15c -- native SIMULATED preview of raw candidate C7.

REVIEW MATERIAL ONLY: not an Owner acceptance, recording, publication or
activation. Run from the repository root (a worktree works) with the
repository venv; ``afterworlds`` must import from this checkout's ``src``.

Construction (the reviewed C5/C6 method, under schema 20):

* prior: the recorded native C5 successor ``srd-5-2-1-corpus-8781d4e0-a3b-15c.json``
  (``23e5d8e0...``), whose real receipts are preserved;
* each C7 fact's owning batch is identified natively, from the successor's
  acceptance records of the spans bound to its component;
* each touched batch's accepted proposal (the exact C5 packet proposal,
  identity-matched to the successor's anchor) gains its C7 facts on their
  prose-bound components (handling ``mixed``; prose and retention reason
  kept), a contextual provenance claim per fact on the bound span holding the
  fact's quote, and an ExpectedRule per review unit; it is re-declared at the
  schema-20 pair;
* in the successor's anchor order each touched batch is excised claim-based
  (``issue-15c-native/scripts/excise.py``) and its new proposal accepted
  natively with SIMULATED evidence. The first acceptance records the
  registered 19 -> 20 lift.

Proofs, each asserted and written to ``reports/c7-preview.json``.
"""

from __future__ import annotations

import collections
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent
REPO = NOTES.parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(NOTES / "issue-15c-native/scripts"))

import common as c  # noqa: E402
from excise import excise  # noqa: E402

import afterworlds  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.authoring import render  # noqa: E402
from afterworlds.ingestion.mechanical.bound_corpus import (
    load_bound_corpus,
)  # noqa: E402
from afterworlds.ingestion.mechanical.gate import run_publication_gate  # noqa: E402
from afterworlds.ingestion.mechanical.models import ExpectedRule  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
    projection_payload,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    AmmunitionSupplyFact,
    ComponentHandling,
    ComponentReference,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    fact_from_payload,
    fact_key,
    fact_payload,
    fact_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    SCHEMA_19_HASH,
    SCHEMA_19_VERSION,
    SCHEMA_20_HASH,
    SCHEMA_20_VERSION,
    lift_accepted_inputs,
)
from afterworlds.persistence.database import (
    create_engine,
    create_session_factory,
)  # noqa: E402
from afterworlds.persistence.orm.base import Base  # noqa: E402

assert (
    Path(afterworlds.__file__).resolve().is_relative_to(REPO / "src")
), afterworlds.__file__
assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_20_VERSION
assert representation_schema_hash() == SCHEMA_20_HASH


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def locate(rel: str, digest: str) -> Path:
    """*rel* under this checkout or the nearest ancestor holding it, pinned.

    The accepted C5 packet proposals and the isolated release store are
    git-ignored, so a worktree reads them from the main checkout read-only.
    """
    for root in (REPO, *REPO.parents):
        path = root / rel
        if path.is_file():
            assert sha(path.read_bytes()) == digest, f"pinned input changed: {path}"
            return path
    raise FileNotFoundError(rel)


_store = locate("g1-work/rel/afterworlds.db", c.STORE_SHA256)
c.G1_WORK, c.STORE, c.LEAVES = _store.parent, _store, _store.parent / "leaves.json"

IMPL = NOTES / "issue-15c-implementation"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
SUCCESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c.json"
C7 = IMPL / "candidate-c7/c7.json"
C6R2 = IMPL / "candidate-c6-r2/c6r2.json"
C6 = IMPL / "candidate-c6/c6.json"
PINS = {
    SUCCESSOR: "23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69",
    C7: "bf2a269c6f5446a63d5ce2353c27d5dc75224935cd16960ce79da7e766aefa77",
    C6R2: "699718ff9bac8298c08fc6da706309819b864b604685c88f462669d68e8923f4",
    C6: "eb014b30e685543c435930913d00fe8762963c95b0fdcc9ce470c019bbfb554a",
    **{
        SRC / name: digest
        for name, digest in (
            (
                "feats.md",
                "3894f4a147df40adb8b090825b4c2e3e5ee2c67851aca42305b11f2477bcfbf7",
            ),
            (
                "equipment.md",
                "ba4d96bf7c08a44103b11be1ae5385e6e09f3f5478d56c3a2f38f97bd77d645b",
            ),
            (
                "character-creation.md",
                "1c8f477398cc7ca5721542698d67147f303e4dd5a5dacdad7cb7cec1119f7c42",
            ),
        )
    },
}
#: The accepted proposal each touchable batch was recorded from (C5 packet,
#: rendered digest, identity).
ACCEPTED = {
    "character-origins-feats": (
        "a8928f18d65538d21993e7f94090272bdc7e279c412134ebb8ffc996ada48b89",
        "20716b7dcadd5e1216ff3594c5aa654cb41c2961fe49048b0c853c1eed381838",
    ),
    "equipment": (
        "7f8dadcd28c072cc22965dc36e7e1d7debb99aec3139c9f8b72178be06aff4b6",
        "b01f54b917653f83b7dbeebd6ad54757bdf183f71235d76e9198815f21789c4b",
    ),
}
PREVIEW = HERE / "preview/srd-5-2-1-corpus-8781d4e0-a3b-c7-PREVIEW.json"
ORIGIN = (
    "CRD Issue 15c C7 native preview (review only): the accepted {batch} proposal "
    "{identity} with its raw C7 facts (C6-r2 Origin feat categories and schema-20 "
    "ammunition supplies) on their components, declared at schema 20"
)


def norm(text: str) -> str:
    return " ".join(text.replace("&emsp;", " ").split())


def accepted_path(batch: str) -> Path:
    rel = (
        f".claude/review-notes/issue-15c-native/preview/proposals/{batch}-PROPOSAL.json"
    )
    return locate(rel, ACCEPTED[batch][0])


def owners(
    base: AcceptedInputs, facts: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Each fact's owning batch, read natively from the successor: the batch
    whose accepted records hold every span bound to the fact's component."""
    span_batch = {r.span_id: r.batch_id for r in base.acceptances}
    bound: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for b in base.oracle.representation.prose_bindings:
        bound[(b.record_key, b.component_key)].add(span_batch[b.span_id])
    out: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for f in facts:
        (batch,) = bound[(f["record_key"], f["component_key"])]
        out[batch].append(f)
    return dict(out)


def build_one(
    batch: str, facts: list[dict[str, Any]], leaves: dict[str, str]
) -> tuple[MechanicalProposal, MechanicalProposal, dict[str, Any]]:
    p = load_proposal(accepted_path(batch))
    assert proposal_identity(p) == ACCEPTED[batch][1], batch
    rep = p.proposed_representation
    spans = {x.span.span_id: x.span for x in p.proposed_spans}
    bound: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for b in rep.prose_bindings:
        bound[(b.record_key, b.component_key)].append(b.span_id)
    unit_of_leaf = {
        leaf: u.unit_id for u in p.proposed_review_units for leaf in u.leaf_ids
    }
    added: dict[tuple[str, str], Any] = {}
    claims, rules = [], collections.defaultdict(list)
    chosen_by_fact = {}
    for f in facts:
        key = (f["record_key"], f["component_key"])
        fact = fact_from_payload(f["fact"])
        assert fact_payload(fact) == f["fact"], key
        src = f["source"]
        assert src["quote"] in c.lines(src["file"])[src["line"] - 1], (
            "source line",
            key,
        )
        quote = norm(src["quote"])
        chosen = sorted(
            s
            for s in bound[key]
            if quote
            in norm(leaves[spans[s].leaf_id][spans[s].char_start : spans[s].char_end])
        )
        assert chosen, ("quote on no bound span", key)
        assert key not in added, key
        added[key] = fact
        chosen_by_fact[f"{key[0]}/{key[1]}"] = chosen
        for sid in chosen:
            claims.append(
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT,
                    fact_target_key(*key, fact, ""),
                    sid,
                    ProvenanceRole.CONTEXTUAL,
                )
            )
        per_unit: dict[str, list[str]] = collections.defaultdict(list)
        for sid in chosen:
            per_unit[unit_of_leaf[spans[sid].leaf_id]].append(sid)
        for unit, sids in per_unit.items():
            rules[unit].append(
                ExpectedRule(
                    record_key=key[0],
                    component_key=key[1],
                    fact_family=fact.FAMILY.value,
                    source_span_ids=tuple(sids),
                )
            )
    components = []
    for comp in rep.components:
        key = (comp.record_key, comp.semantic_key)
        if key in added:
            assert (
                comp.handling is ComponentHandling.PROSE_BOUND and not comp.facts
            ), key
            comp = dataclasses.replace(
                comp, handling=ComponentHandling.MIXED, facts=(added[key],)
            )
        components.append(comp)
    changed = sum(1 for a, b in zip(rep.components, components, strict=True) if a != b)
    assert changed == len(facts) == len(added), (batch, changed)
    units = tuple(
        dataclasses.replace(
            u, expected_rules=(*u.expected_rules, *rules.get(u.unit_id, ()))
        )
        for u in p.proposed_review_units
    )
    new = dataclasses.replace(
        p,
        proposed_representation=dataclasses.replace(
            rep, components=tuple(components), provenance=(*rep.provenance, *claims)
        ),
        proposed_review_units=units,
        proposal_origin=ORIGIN.format(batch=batch, identity=ACCEPTED[batch][1]),
        schema_version=SCHEMA_20_VERSION,
        schema_hash=SCHEMA_20_HASH,
    )
    # Nothing else of the proposal moved.
    assert (
        dataclasses.replace(
            new,
            proposed_representation=rep,
            proposed_review_units=p.proposed_review_units,
            proposal_origin=p.proposal_origin,
            schema_version=p.schema_version,
            schema_hash=p.schema_hash,
        )
        == p
    ), batch
    return (
        p,
        new,
        {
            "accepted_proposal_identity": ACCEPTED[batch][1],
            "accepted_rendered_sha256": ACCEPTED[batch][0],
            "facts_added": len(added),
            "claims_added": len(claims),
            "expected_rules_added": sum(len(v) for v in rules.values()),
            "claimed_spans": chosen_by_fact,
            "fact_keys": sorted(
                f"{k[0]}/{k[1]}:{fact_key(v)}" for k, v in added.items()
            ),
        },
    )


def build(
    base: AcceptedInputs,
) -> dict[str, tuple[MechanicalProposal, MechanicalProposal, dict]]:
    facts = json.loads(C7.read_text("utf-8"))["facts"]
    leaves = c.leaf_texts()
    out = {}
    for batch, fs in owners(base, facts).items():
        (anchor,) = [a for a in base.schema_anchors if a.batch_id == batch]
        assert anchor.proposal_identity == ACCEPTED[batch][1], (
            "successor anchor",
            batch,
        )
        out[batch] = build_one(batch, fs, leaves)
    assert sum(v[2]["facts_added"] for v in out.values()) == len(facts) == 9
    return out


def chain(
    base: AcceptedInputs, built: dict[str, tuple[Any, Any, Any]]
) -> AcceptedInputs:
    state = base
    for batch in [a.batch_id for a in base.schema_anchors if a.batch_id in built]:
        accepted, new, _ = built[batch]
        (old,) = [b for b in state.batches if b.batch_id == batch]
        excised, _ = excise(state, {batch: accepted.proposed_representation})
        state = accept_proposal(
            new,
            batch_id=batch,
            resolved_scope=old.resolved_scope,
            resolved_review_units=tuple(u.unit_id for u in new.proposed_review_units),
            prior=excised,
            rule=c.SIMULATED_RULE,
            reviewer=c.SIMULATED_REVIEWER,
            accepted_at=c.SIMULATED_AT,
        )
    return state


def preserved(
    base: AcceptedInputs, data: bytes, built: dict[str, Any], preview: AcceptedInputs
) -> dict[str, bool]:
    touched = set(built)
    G, P = json.loads(serialize_accepted_inputs(base)), json.loads(data)
    keep = lambda rows: [r for r in rows if r["batch_id"] not in touched]  # noqa: E731
    out = {
        f"acceptance.{f}": keep(G["acceptance"][f]) == keep(P["acceptance"][f])
        for f in ("batches", "records", "review_unit_records", "schema_anchors")
    }
    out["acceptance.batches.order"] = [
        b["batch_id"] for b in G["acceptance"]["batches"]
    ] == [b["batch_id"] for b in P["acceptance"]["batches"]]
    (lift,) = P["acceptance"]["lifts"][len(G["acceptance"]["lifts"]) :]
    out["lifts.prefix_unchanged"] = (
        P["acceptance"]["lifts"][:-1] == G["acceptance"]["lifts"]
    )
    out["lifts.added_exactly_19_to_20"] = (
        lift["lift_id"] == "5d-lift-schema-19-to-20"
        and (lift["from_version"], lift["from_hash"])
        == (SCHEMA_19_VERSION, SCHEMA_19_HASH)
        and (lift["to_version"], lift["to_hash"]) == (SCHEMA_20_VERSION, SCHEMA_20_HASH)
    )
    out["representation_schema.was_19_now_20"] = G["representation_schema"] == {
        "version": SCHEMA_19_VERSION,
        "hash": SCHEMA_19_HASH,
    } and P["representation_schema"] == {
        "version": SCHEMA_20_VERSION,
        "hash": SCHEMA_20_HASH,
    }
    for k in (
        "reference_resolutions",
        "spans",
        "release_binding",
        "semantic_policy_hash",
        "semantic_policy_version",
        "artifact_kind",
    ):
        out[k] = G[k] == P[k]
    out["resolution_records"] = (
        G["acceptance"]["reference_resolution_records"]
        == P["acceptance"]["reference_resolution_records"]
    )
    touched_units = {
        r["unit_id"]
        for r in G["acceptance"]["review_unit_records"]
        if r["batch_id"] in touched
    }
    g_units, p_units = (
        [u for u in X["review_units"] if u["unit_id"] not in touched_units]
        for X in (G, P)
    )
    out["review_units.other_batches"] = g_units == p_units
    fact_records = {
        k.split("/")[0] for v in built.values() for k in v[2]["claimed_spans"]
    }
    gob = {o["record_key"]: o for o in G["obligations"]}
    pob = {o["record_key"]: o for o in P["obligations"]}
    out["obligations.changed_only_on_fact_records"] = (
        gob.keys() == pob.keys()
        and {k for k in gob if gob[k] != pob[k]} <= fact_records
    )
    gr, pr = base.oracle.representation, preview.oracle.representation
    for f in (
        "records",
        "components",
        "prose_bindings",
        "relationships",
        "references",
        "provenance",
    ):
        before, after = set(getattr(gr, f)), set(getattr(pr, f))
        old = set().union(
            *(getattr(v[0].proposed_representation, f) for v in built.values())
        )
        new = set().union(
            *(getattr(v[1].proposed_representation, f) for v in built.values())
        )
        out[f"representation.{f}"] = (before - after == old - new) and (
            after - before == new - old
        )
    return out


def _supply(rep: Any, record: str, **changes: Any) -> Any:
    """*rep* with the ammunition_supply on *record* changed."""
    comps = []
    for comp in rep.components:
        if comp.record_key == record:
            (fact,) = comp.facts
            assert type(fact) is AmmunitionSupplyFact
            comp = dataclasses.replace(
                comp, facts=(dataclasses.replace(fact, **changes),)
            )
        comps.append(comp)
    return dataclasses.replace(rep, components=tuple(comps))


def _ref(record: str) -> tuple[ComponentReference, ...]:
    return (
        ComponentReference(record_key=record, component_key=record.rsplit(".", 1)[1]),
    )


#: Malformed variants of the preview, each of which must not validate.
MALFORMED = {
    "sling_bullets_also_claim_musket": (
        "equipment.adventuring_gear.bullets_sling",
        {"for_weapons": _ref("equipment.weapons.musket")},
    ),
    "arrows_for_a_weapon_without_ammunition": (
        "equipment.adventuring_gear.arrows",
        {"for_weapons": _ref("equipment.weapons.dagger")},
    ),
    "bolts_for_an_arrow_weapon": (
        "equipment.adventuring_gear.bolts",
        {"for_weapons": _ref("equipment.weapons.shortbow")},
    ),
    "needles_for_an_unknown_component": (
        "equipment.adventuring_gear.needles",
        {"for_weapons": _ref("equipment.weapons.no_such_weapon")},
    ),
}


def native(inputs: AcceptedInputs, other: AcceptedInputs) -> dict[str, Any]:
    out: dict[str, Any] = {}
    with c.private_store() as db:
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as s:
                b = inputs.oracle.binding
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                candidate = candidate_from_accepted_inputs(inputs)
                out["validate_candidate_findings"] = list(
                    validate_candidate(candidate, corpus)
                )
                malformed = {}
                for name, (record, changes) in MALFORMED.items():
                    bad = dataclasses.replace(
                        candidate,
                        representation=_supply(
                            candidate.representation, record, **changes
                        ),
                    )
                    malformed[name] = [
                        x
                        for x in validate_candidate(bad, corpus)
                        if "ammunition_supply names" in x
                    ]
                out["malformed_variants_refused"] = malformed
                ids = {}
                for tag, x in (("preview", inputs), ("successor_lifted", other)):
                    identified = identify_projection(candidate_from_accepted_inputs(x))
                    persist_draft(s, identified, now=c.SIMULATED_AT)
                    s.commit()
                    rebuilt = reconstruct_candidate(s, identified.projection_uuid)
                    out[f"{tag}_reconstruction_clean"] = (
                        verify_reconstruction(s, identified) == ()
                        and projection_payload(rebuilt)
                        == projection_payload(identified.candidate)
                        and identify_projection(rebuilt).projection_uuid
                        == identified.projection_uuid
                    )
                    record_persisted_state_digest(s, identified.projection_uuid)
                    s.commit()
                    ids[tag] = identified
                own = run_publication_gate(
                    s, ids["preview"].projection_uuid, inputs.oracle
                )
                cross = run_publication_gate(
                    s, ids["successor_lifted"].projection_uuid, inputs.oracle
                )
                back = run_publication_gate(
                    s, ids["preview"].projection_uuid, other.oracle
                )
                out.update(
                    projection=str(ids["preview"].projection_uuid),
                    payload_hash=ids["preview"].payload_hash,
                    successor_lifted_projection=str(
                        ids["successor_lifted"].projection_uuid
                    ),
                    successor_lifted_payload_hash=ids["successor_lifted"].payload_hash,
                    own_gate_passed=own.passed and not own.failures,
                    successor_refused_against_preview=not cross.passed,
                    preview_refused_against_successor=not back.passed,
                )
        finally:
            engine.dispose()
    return out


def main() -> None:
    for path, digest in PINS.items():
        assert sha(path.read_bytes()) == digest, path
    base = load_accepted_inputs(SUCCESSOR)
    built = build(base)
    preview = chain(base, built)
    data = serialize_accepted_inputs(preview)
    rendered = {b: render(v[1]).encode("utf-8") for b, v in built.items()}
    if "--twice" in sys.argv:
        again = build(base)
        assert serialize_accepted_inputs(chain(base, again)) == data, "determinism"
        assert {b: render(v[1]).encode("utf-8") for b, v in again.items()} == rendered
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_bytes(data)
    for batch, text in rendered.items():
        (PREVIEW.parent / f"{batch}-C7-PROPOSAL.json").write_bytes(text)
    back = load_accepted_inputs(PREVIEW)
    assert serialize_accepted_inputs(back) == data
    pres = preserved(base, data, built, back)
    # The successor at the live contract: the registered lift, data unchanged.
    lifted, lift_records = lift_accepted_inputs(
        base, (SCHEMA_20_VERSION, SCHEMA_20_HASH)
    )
    lifted_unchanged = all(
        getattr(lifted.oracle.representation, f)
        == getattr(base.oracle.representation, f)
        for f in (
            "records",
            "components",
            "prose_bindings",
            "relationships",
            "references",
            "provenance",
        )
    )
    nat = native(back, lifted)
    report = {
        "label": "SIMULATION - review-only native preview; not an Owner acceptance",
        "pins": {
            str(p.relative_to(REPO)).replace("\\", "/"): d for p, d in PINS.items()
        },
        "accepted_inputs_located": {b: ACCEPTED[b][0] for b in built},
        "touched_batches": sorted(built),
        "batches": {
            b: {
                **v[2],
                "proposal_identity": proposal_identity(v[1]),
                "rendered_proposal_sha256": sha(rendered[b]),
            }
            for b, v in built.items()
        },
        "preview_sha256": sha(data),
        "oracle_identity": oracle_identity(back.oracle),
        "schema": [back.oracle.schema_version, back.oracle.schema_hash],
        "lifts": [lf.lift_id for lf in back.lifts],
        "successor_lift": {
            "lift_ids": [r.lift_id for r in lift_records],
            "representation_unchanged": lifted_unchanged,
        },
        "preservation": pres,
        "native": nat,
        "deterministic_twice": "--twice" in sys.argv,
        "pins_after": all(sha(p.read_bytes()) == d for p, d in PINS.items()),
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/c7-preview.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("preservation", "batches")},
            indent=1,
        )
    )
    assert all(pres.values()), pres
    assert lifted_unchanged and [r.lift_id for r in lift_records] == [
        "5d-lift-schema-19-to-20"
    ]
    assert not nat["validate_candidate_findings"], nat["validate_candidate_findings"][
        :5
    ]
    assert all(nat["malformed_variants_refused"].values()), nat[
        "malformed_variants_refused"
    ]
    assert nat["own_gate_passed"] and nat["successor_refused_against_preview"]
    assert nat["preview_refused_against_successor"]
    assert (
        nat["preview_reconstruction_clean"]
        and nat["successor_lifted_reconstruction_clean"]
    )
    assert report["pins_after"]


if __name__ == "__main__":
    main()
