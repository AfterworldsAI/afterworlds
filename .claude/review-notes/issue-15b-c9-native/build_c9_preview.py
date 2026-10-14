"""CRD Issue 15b -- native SIMULATED preview of raw candidate C9 (r2).

REVIEW MATERIAL ONLY: not an Owner acceptance, recording, publication or
activation. Run from this preview checkout's root with the venv and this
checkout's ``src`` first on ``PYTHONPATH``:

    PYTHONIOENCODING=utf-8 PYTHONPATH=src venv/Scripts/python.exe \
        .claude/review-notes/issue-15b-c9-native/build_c9_preview.py \
        --inputs PRIVATE_DIR [--twice]

Construction (the reviewed C8 method, under schema 22):

* prior: the recorded C8 successor ``srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json``
  (``ead7fa9d...``), whose real receipts are preserved;
* the four touched batches' accepted proposals are the C8 packet's rebuilt
  proposals (the C8 recording proved they render byte-identical to the
  accepted preview's), read from a private copy (``--inputs``) whose files
  are pinned to the C8 packet's rendered digests and identity-matched to the
  successor's schema anchors;
* each profile component (kept mixed: facts, options, prose, retention reason
  and bindings unchanged) gains one ``creature_skills`` fact. One contextual
  provenance claim per fact on the one bound span holding the fact's quote --
  the printed Skills line, or for an empty list (interpretation S1) the
  details line where the entry would appear -- and an ExpectedRule in that
  span's review unit. Re-declared at the schema-22 pair; nothing else moves;
* in the successor's anchor order each touched batch is excised claim-based
  (``scripts/excise.py``, copied unchanged from the C5/C8 native scripts) and
  its new proposal accepted natively with SIMULATED evidence. The first
  acceptance records the registered 21 -> 22 lift.

The isolated release store is only ever copied privately. ``--dry`` stops
after the mapping; ``--twice`` rebuilds and compares bytes. Proofs, each
asserted, go to ``reports/c9-preview.json``; the preview oracle and proposals
go to the git-ignored ``preview/``.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from uuid import UUID

HERE = Path(__file__).resolve().parent
NOTES = HERE.parent
REPO = NOTES.parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE / "scripts"))

import common as c  # noqa: E402
from excise import excise  # noqa: E402

import afterworlds  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import accept_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.authoring import render  # noqa: E402
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
)
from afterworlds.ingestion.mechanical.gate import run_publication_gate  # noqa: E402
from afterworlds.ingestion.mechanical.models import ExpectedRule  # noqa: E402
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    candidate_from_accepted_inputs,
    committed_inputs_for,
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
    AbilityScore,
    ComponentHandling,
    CreatureSizeFact,
    CreatureSkillBonus,
    CreatureSkillsFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    Skill,
    fact_from_payload,
    fact_payload,
    fact_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    SCHEMA_21_HASH,
    SCHEMA_21_VERSION,
    SCHEMA_22_HASH,
    SCHEMA_22_VERSION,
    lift_accepted_inputs,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

AFTERWORLDS_FILE = Path(afterworlds.__file__).resolve()
assert AFTERWORLDS_FILE.is_relative_to(REPO / "src"), AFTERWORLDS_FILE
assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_22_VERSION
assert representation_schema_hash() == SCHEMA_22_HASH
#: The accepted schema 21 is the registered lift source.
assert SCHEMA_21_HASH == (
    "4499b3964aac338e10c7b6d1f67a5eb37570878600e0c5f04bd4464d58f1df55"  # pragma: allowlist secret  # noqa: E501
)

CAND = NOTES / "issue-15b-contest-authority" / "candidate-c9"
SUCCESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json"
C9 = CAND / "c9.json"
CORRESPONDENCE = CAND / "correspondence.json"
INVENTORY = CAND / "inventory.json"
#: Pinned: the accepted C8 successor and the raw C9 r2 candidate files.
PINS: dict[Path, str] = {
    SUCCESSOR: "ead7fa9d4fde484098f71221ca5ef82dfb2c82229d8fca80ab5feeb4e4d62d0d",  # noqa: E501  # pragma: allowlist secret
    C9: "a3d40545d1a0ea1b4a1e24a1e3831b12b972f50ea26981b0edf1b578fd0648db",  # noqa: E501  # pragma: allowlist secret
    CORRESPONDENCE: "285ee055374edbcf75383b00e755aca2daa2d5f0363f57b6af368a27efeaf1e4",  # noqa: E501  # pragma: allowlist secret
    INVENTORY: "daab6ac2acd13d3b273995baff64e4ba8e0242f9817e7edf62b4965ea8de3d9b",  # noqa: E501  # pragma: allowlist secret
    HERE
    / "scripts/common.py": "20761dc0f9e13007cbb7270dae6fad7ba6d122899aa2e30ea03e0153369d9b07",  # noqa: E501  # pragma: allowlist secret
    HERE
    / "scripts/excise.py": "80a177b3787ba563156bf7994759729c91af8fe699a429ce9ec2fbe29f0162a3",  # noqa: E501  # pragma: allowlist secret
}
for _rel, _digest in json.loads(C9.read_bytes())["pins"].items():
    PINS.setdefault(REPO / _rel, _digest)

#: The accepted proposal each touched batch was last recorded from (the C8
#: packet's rebuilt proposals): (file name, rendered SHA-256, identity).
ACCEPTED: dict[str, tuple[str, str]] = {
    "spell-descriptions": (
        "spell-descriptions-C8-PROPOSAL.json",
        "68c7526213cf976963e9408b0063140c70af38ef7a671c23c4144e00dfcc4377",  # pragma: allowlist secret  # noqa: E501
    ),
    "magic-items": (
        "magic-items-C8-PROPOSAL.json",
        "f6a8b41281de0023a493803c934bf906ed8ee5909a544a9800743f0e9c63a2cd",  # pragma: allowlist secret  # noqa: E501
    ),
    "monsters": (
        "monsters-C8-PROPOSAL.json",
        "c12dad2846359cd35823c48c36e7dbca6fc6553a37c65ac5764a571173289984",  # pragma: allowlist secret  # noqa: E501
    ),
    "animals": (
        "animals-C8-PROPOSAL.json",
        "6c2cd65751bdbefbb48ac042c0a201af087f8aca0cd9229a0e53bf48d95b8bbf",  # pragma: allowlist secret  # noqa: E501
    ),
}
STORE_LEAVES_SHA256 = "700b502bfd8091350677eb2ff8fe9263839829dc73638e0180ec2207c0f542f7"  # pragma: allowlist secret  # noqa: E501
PREVIEW = HERE / "preview/srd-5-2-1-corpus-8781d4e0-a3b-c9-PREVIEW.json"
ORIGIN = (
    "CRD Issue 15b C9 native preview (review only): the accepted {batch} proposal "
    "{identity} with its raw C9 r2 creature_skills facts on their profile "
    "components, declared at schema 22"
)
COLLECTIONS = (
    "records",
    "components",
    "prose_bindings",
    "relationships",
    "references",
    "provenance",
)
SIMULATED_AT = "2026-10-14T00:00:00Z"
SIMULATED_RULE = (
    "SIMULATION ONLY - CRD Issue 15b C9 native preview; not an Owner acceptance "
    "or authorization"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(text: str) -> str:
    return " ".join(text.replace("&emsp;", " ").split())


def private_inputs(root: Path) -> dict[str, Path]:
    """The private copies, each pinned; the store is pointed at by ``common``."""
    store = root / "rel/afterworlds.db"
    assert sha(store.read_bytes()) == c.STORE_SHA256, store
    leaves = root / "rel/leaves.json"
    assert sha(leaves.read_bytes()) == STORE_LEAVES_SHA256, leaves
    c.G1_WORK, c.STORE, c.LEAVES = store.parent, store, leaves
    out = {}
    for batch, (name, rendered) in ACCEPTED.items():
        path = root / "proposals" / name
        assert sha(path.read_bytes()) == rendered, path
        out[batch] = path
    return out


def rows() -> list[dict[str, Any]]:
    """The 336 candidate facts, each joined to its correspondence row."""
    raw = json.loads(C9.read_bytes())
    corr = {
        (r["record_key"], r["component_key"]): r
        for r in json.loads(CORRESPONDENCE.read_bytes())
    }
    assert len(raw["facts"]) == len(corr) == 336
    out = []
    for f in raw["facts"]:
        r = corr[(f["record_key"], f["component_key"])]
        quote = f["source"].get("quote") or f["source"]["details_quote"]
        line = f["source"].get("line") or f["source"]["details_line"]
        assert r["file"] == f["source"]["file"], r
        out.append(
            {
                **f,
                "quote": quote,
                "line": line,
                "batch": r["batch"],
                "claim_spans": r["claim_spans"],
            }
        )
    return out


def build_one(
    batch: str,
    path: Path,
    identity: str,
    facts: list[dict[str, Any]],
    leaves: dict[str, str],
) -> tuple[MechanicalProposal, MechanicalProposal, dict[str, Any]]:
    p = load_proposal(path)
    assert proposal_identity(p) == identity, batch
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
    chosen_by_fact: dict[str, str] = {}
    for f in facts:
        key = (f["record_key"], f["component_key"])
        fact = fact_from_payload(f["fact"])
        assert type(fact) is CreatureSkillsFact and fact_payload(fact) == f["fact"]
        assert f["quote"] in c.lines(f["source"]["file"])[f["line"] - 1], key
        quote = norm(f["quote"])
        chosen = sorted(
            s
            for s in bound[key]
            if s in spans
            and quote
            in norm(leaves[spans[s].leaf_id][spans[s].char_start : spans[s].char_end])
        )
        assert len(chosen) == 1, ("quote on exactly one bound span", key, chosen)
        (sid,) = chosen
        assert sid in f["claim_spans"], ("claim span in correspondence", key)
        assert key not in added, key
        added[key] = fact
        chosen_by_fact[f"{key[0]}/{key[1]}"] = sid
        claims.append(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(*key, fact, ""),
                sid,
                ProvenanceRole.CONTEXTUAL,
            )
        )
        rules[unit_of_leaf[spans[sid].leaf_id]].append(
            ExpectedRule(
                record_key=key[0],
                component_key=key[1],
                fact_family=fact.FAMILY.value,
                source_span_ids=(sid,),
            )
        )
    components = []
    for comp in rep.components:
        key = (comp.record_key, comp.semantic_key)
        if key in added:
            # A creature profile: everything kept, one fact appended.
            assert comp.handling is ComponentHandling.MIXED, key
            assert any(type(x) is CreatureSizeFact for x in comp.facts), key
            comp = dataclasses.replace(comp, facts=(*comp.facts, added[key]))
        components.append(comp)
    changed = [
        (a, b) for a, b in zip(rep.components, components, strict=True) if a != b
    ]
    assert len(changed) == len(facts) == len(added), (batch, len(changed))
    for a, b in changed:
        assert b.facts[:-1] == a.facts and dataclasses.replace(b, facts=a.facts) == a
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
        proposal_origin=ORIGIN.format(batch=batch, identity=identity),
        schema_version=SCHEMA_22_VERSION,
        schema_hash=SCHEMA_22_HASH,
    )
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
    empty = sum(1 for f in added.values() if not f.skills)
    return (
        p,
        new,
        {
            "accepted_proposal_identity": identity,
            "accepted_rendered_sha256": ACCEPTED[batch][1],
            "accepted_from_schema": p.schema_version,
            "facts_added": len(added),
            "empty_skill_lists": empty,
            "claims_added": len(claims),
            "expected_rules_added": sum(len(v) for v in rules.values()),
            "claimed_span": chosen_by_fact,
        },
    )


def build(
    base: AcceptedInputs, paths: dict[str, Path]
) -> dict[str, tuple[MechanicalProposal, MechanicalProposal, dict[str, Any]]]:
    facts = rows()
    leaves = c.leaf_texts()
    inventory = json.loads(INVENTORY.read_bytes())["touched_batches"]
    by_batch: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    span_batch = {r.span_id: r.batch_id for r in base.acceptances}
    claimed: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for cl in base.oracle.representation.provenance:
        if cl.target_kind is ProvenanceTargetKind.FACT:
            claimed[(cl.target_key[0], cl.target_key[1])].add(cl.span_id)
    for f in facts:
        (batch,) = {
            span_batch[s] for s in claimed[(f["record_key"], f["component_key"])]
        }
        assert batch == f["batch"], f["record_key"]
        by_batch[batch].append(f)
    out = {}
    for batch, fs in by_batch.items():
        (anchor,) = [a for a in base.schema_anchors if a.batch_id == batch]
        out[batch] = build_one(
            batch, paths[batch], anchor.proposal_identity, fs, leaves
        )
        assert out[batch][2]["facts_added"] == inventory[batch]["facts"], batch
    assert set(out) == set(inventory) == set(ACCEPTED)
    assert sum(v[2]["facts_added"] for v in out.values()) == len(facts) == 336
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
            rule=SIMULATED_RULE,
            reviewer=c.SIMULATED_REVIEWER,
            accepted_at=SIMULATED_AT,
        )
    return state


def preserved(
    base: AcceptedInputs, data: bytes, built: dict[str, Any], preview: AcceptedInputs
) -> dict[str, Any]:
    """The C8 builder's preservation proofs, at 21 -> 22."""
    touched = set(built)
    G, P = json.loads(serialize_accepted_inputs(base)), json.loads(data)

    def keep(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [r for r in rows if r["batch_id"] not in touched]

    out: dict[str, Any] = {
        f"acceptance.{f}.untouched_rows_identical_in_order": keep(G["acceptance"][f])
        == keep(P["acceptance"][f])
        for f in ("batches", "records", "review_unit_records", "schema_anchors")
    }
    g_anchor = [a["batch_id"] for a in G["acceptance"]["schema_anchors"]]
    p_anchor = [a["batch_id"] for a in P["acceptance"]["schema_anchors"]]
    out["acceptance.schema_anchors.order_is_untouched_then_touched_in_c8_order"] = (
        p_anchor
        == [b for b in g_anchor if b not in touched]
        + [b for b in g_anchor if b in touched]
    )
    out["acceptance.batch_set_unchanged"] = sorted(g_anchor) == sorted(p_anchor)
    (lift,) = P["acceptance"]["lifts"][len(G["acceptance"]["lifts"]) :]
    out["lifts.prefix_unchanged"] = (
        P["acceptance"]["lifts"][:-1] == G["acceptance"]["lifts"]
    )
    out["lifts.added_exactly_21_to_22"] = (
        lift["lift_id"] == "5d-lift-schema-21-to-22"
        and (lift["from_version"], lift["from_hash"])
        == (SCHEMA_21_VERSION, SCHEMA_21_HASH)
        and (lift["to_version"], lift["to_hash"]) == (SCHEMA_22_VERSION, SCHEMA_22_HASH)
    )
    out["representation_schema.was_21_now_22"] = G["representation_schema"] == {
        "version": SCHEMA_21_VERSION,
        "hash": SCHEMA_21_HASH,
    } and P["representation_schema"] == {
        "version": SCHEMA_22_VERSION,
        "hash": SCHEMA_22_HASH,
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
    out["resolution_records"] = G["acceptance"].get(
        "reference_resolution_records"
    ) == P["acceptance"].get("reference_resolution_records")
    out["policy_transitions"] = G["acceptance"].get("policy_transitions") == P[
        "acceptance"
    ].get("policy_transitions")
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
    gu = {u["unit_id"]: u for u in G["review_units"] if u["unit_id"] in touched_units}
    pu = {u["unit_id"]: u for u in P["review_units"] if u["unit_id"] in touched_units}
    added_rules = 0
    only_rules = gu.keys() == pu.keys()
    for uid in gu:
        a, b = dict(gu[uid]), dict(pu.get(uid, {}))
        ra, rb = a.pop("expected_rules", []), b.pop("expected_rules", [])
        only_rules &= a == b and all(r in rb for r in ra)
        added_rules += len(rb) - len(ra)
    out["review_units.touched_changed_only_by_added_rules"] = only_rules
    out["review_units.expected_rules_added"] = added_rules
    fact_records = {
        k.split("/")[0] for v in built.values() for k in v[2]["claimed_span"]
    }
    gob = {o["record_key"]: o for o in G["obligations"]}
    pob = {o["record_key"]: o for o in P["obligations"]}
    out["obligations.changed_only_on_fact_records"] = (
        gob.keys() == pob.keys()
        and {k for k in gob if gob[k] != pob[k]} <= fact_records
    )
    gr, pr = base.oracle.representation, preview.oracle.representation
    for f in COLLECTIONS:
        before, after = set(getattr(gr, f)), set(getattr(pr, f))
        old = set().union(
            *(getattr(v[0].proposed_representation, f) for v in built.values())
        )
        new = set().union(
            *(getattr(v[1].proposed_representation, f) for v in built.values())
        )
        out[f"representation.{f}.delta_is_the_proposal_delta"] = (
            before - after == old - new
        ) and (after - before == new - old)
        out[f"representation.{f}.count_before_after"] = [len(before), len(after)]
    gc = {(x.record_key, x.semantic_key): x for x in gr.components}
    pc = {(x.record_key, x.semantic_key): x for x in pr.components}
    moved = {k for k in gc if gc[k] != pc.get(k)}
    out["components.same_keys"] = gc.keys() == pc.keys()
    out["components.changed"] = len(moved)
    # Assembled components are canonical, so the added fact need not be last:
    # select it semantically and compare the rest in their canonical order.
    out["components.changed_only_by_one_added_skills_fact"] = all(
        [type(f) for f in pc[k].facts].count(CreatureSkillsFact) == 1
        and CreatureSkillsFact not in [type(f) for f in gc[k].facts]
        and [f for f in pc[k].facts if type(f) is not CreatureSkillsFact]
        == list(gc[k].facts)
        and dataclasses.replace(pc[k], facts=gc[k].facts) == gc[k]
        for k in moved
    )
    out["components.handling_changes"] = sorted(
        f"{k[0]}/{k[1]}" for k in moved if gc[k].handling != pc[k].handling
    )
    out["provenance.removed"] = len(set(gr.provenance) - set(pr.provenance))
    out["provenance.added"] = len(set(pr.provenance) - set(gr.provenance))
    for f in ("records", "prose_bindings", "relationships", "references"):
        out[f"representation.{f}.identical_set"] = set(getattr(gr, f)) == set(
            getattr(pr, f)
        )
    return out


GOBLIN = ("monsters.goblins.goblin_warrior", "goblin_warrior")
ASSASSIN = ("monsters.assassin.assassin", "assassin")


def _skills_at(comp: Any) -> int:
    """The position of the component's one ``creature_skills`` fact. Assembled
    components are canonical, so position is never assumed; absent or
    duplicated is a defect in the verifier's input, not a variant."""
    at = [i for i, f in enumerate(comp.facts) if type(f) is CreatureSkillsFact]
    assert len(at) == 1, (comp.record_key, comp.semantic_key, len(at))
    return at[0]


def _replace_skills(rep: Any, key: tuple[str, str], fn: Any) -> Any:
    """*rep* with component *key*'s skills fact replaced by ``fn(fact)``'s
    facts, in its place; every other fact untouched."""
    comps, hit = [], 0
    for comp in rep.components:
        if (comp.record_key, comp.semantic_key) == key:
            i = _skills_at(comp)
            comp = dataclasses.replace(
                comp, facts=(*comp.facts[:i], *fn(comp.facts[i]), *comp.facts[i + 1 :])
            )
            hit += 1
        comps.append(comp)
    assert hit == 1, (key, hit)
    return dataclasses.replace(rep, components=tuple(comps))


def _onto_non_profile(rep: Any, key: tuple[str, str], fn: Any) -> Any:
    """Move the profile's skills fact onto a non-creature component."""
    del key, fn
    profile = next(
        x for x in rep.components if (x.record_key, x.semantic_key) == GOBLIN
    )
    target = next(
        x
        for x in rep.components
        if x.record_key.startswith("equipment.weapons.")
        and x.handling is ComponentHandling.MIXED
    )
    skills = profile.facts[_skills_at(profile)]
    assert CreatureSkillsFact not in [type(f) for f in target.facts], target
    comps = []
    for comp in rep.components:
        if comp is target:
            comp = dataclasses.replace(comp, facts=(*comp.facts, skills))
        comps.append(comp)
    return dataclasses.replace(rep, components=tuple(comps))


def _bonus(skill: Skill, ability: AbilityScore, bonus: int) -> CreatureSkillBonus:
    return CreatureSkillBonus(skill=skill, ability=ability, bonus=bonus)


#: Malformed variants of the preview: (component, editor, fn, finding substring).
MALFORMED: dict[str, tuple[tuple[str, str], Any, Any, str]] = {
    "unsorted_skills": (
        ASSASSIN,
        _replace_skills,
        lambda f: (dataclasses.replace(f, skills=tuple(reversed(f.skills))),),
        "creature_skills",
    ),
    "duplicate_skill": (
        GOBLIN,
        _replace_skills,
        lambda f: (dataclasses.replace(f, skills=(*f.skills, *f.skills)),),
        "creature_skills",
    ),
    "atypical_pairing_strength_acrobatics": (
        ASSASSIN,
        _replace_skills,
        lambda f: (
            dataclasses.replace(
                f,
                skills=tuple(
                    (
                        _bonus(Skill.ACROBATICS, AbilityScore.STRENGTH, s.bonus)
                        if s.skill is Skill.ACROBATICS
                        else s
                    )
                    for s in f.skills
                ),
            ),
        ),
        "creature_skills",
    ),
    "two_facts_on_one_profile": (
        GOBLIN,
        _replace_skills,
        lambda f: (f, CreatureSkillsFact(skills=())),
        "at most one",
    ),
    "on_a_non_profile_component": (
        GOBLIN,
        _onto_non_profile,
        None,
        "only on a creature profile",
    ),
}


def native(
    inputs: AcceptedInputs, other: AcceptedInputs, paths: dict[str, Path]
) -> dict[str, Any]:
    del paths
    out: dict[str, Any] = {}
    with c.private_store() as db:
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as s:
                b = inputs.oracle.binding
                corpus = load_bound_corpus(s, b.package_uuid, b.release_version)
                candidate = candidate_from_accepted_inputs(inputs)
                t0 = time.monotonic()
                out["validate_candidate_findings"] = list(
                    validate_candidate(candidate, corpus)
                )
                out["validate_candidate_seconds"] = round(time.monotonic() - t0)
                malformed = {}
                for name, (key, editor, fn, needle) in MALFORMED.items():
                    bad = dataclasses.replace(
                        candidate,
                        representation=editor(candidate.representation, key, fn),
                    )
                    malformed[name] = [
                        x for x in validate_candidate(bad, corpus) if needle in x
                    ][:3]
                out["malformed_variants_refused"] = malformed
                ids = {}
                for tag, x in (("preview", inputs), ("successor_lifted", other)):
                    identified = identify_projection(candidate_from_accepted_inputs(x))
                    persist_draft(s, identified, now=SIMULATED_AT)
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
                    own_gate_failures=[f.detail for f in own.failures][:5],
                    successor_refused_against_preview=not cross.passed,
                    preview_refused_against_successor=not back.passed,
                )
        finally:
            engine.dispose()
    return out


def sequencing(preview: AcceptedInputs) -> dict[str, Any]:
    """Why schema 22 cannot land before a recorded C9 successor: evidence."""
    from afterworlds.models.rules_package import RulesPackageBinding
    from afterworlds.pipeline.rpg.capability import (
        CERTIFIED_RELEASE,
        MANIFEST,
        AdjudicationRefusal,
        CapabilityStatus,
        certify,
    )
    from afterworlds.services.dnd5e_state.authority import AuthorityIndex
    from afterworlds.services.rules_authority.application import apply_override_set
    from afterworlds.services.rules_authority.override_set import (
        EMPTY_OVERRIDE_SET_UUID,
        EffectiveOverrideSet,
    )

    package, release = str(CERTIFIED_RELEASE[0]), CERTIFIED_RELEASE[1]
    selected = committed_inputs_for(package, release)
    assert selected is not None
    out: dict[str, Any] = {
        "production_selection_is_still_c8": selected.oracle.schema_version
        == SCHEMA_21_VERSION
        and oracle_identity(selected.oracle)
        == oracle_identity(load_accepted_inputs(SUCCESSOR).oracle),
        "preview_not_in_committed_oracles": not PREVIEW.resolve().is_relative_to(
            COMMITTED_ORACLE_DIR.resolve()
        ),
    }
    candidate = candidate_from_accepted_inputs(selected)
    out["c8_declares_schema_21_under_a_schema_22_build"] = (
        candidate.schema_version == SCHEMA_21_VERSION
    )
    for tag, cand in (
        ("c8_as_committed", candidate),
        ("preview", candidate_from_accepted_inputs(preview)),
    ):
        projection = identify_projection(cand).projection_uuid
        binding = RulesPackageBinding(
            package_uuid=UUID(package),
            release_version=release,
            mechanical_projection_uuid=UUID(projection),
            override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
        )
        leaves = {sp.leaf_id: i for i, sp in enumerate(cand.classification.spans)}
        index = AuthorityIndex.from_authority(
            apply_override_set(
                cand,
                EffectiveOverrideSet(package, release, ()),
                binding,
                leaf_order=leaves,
            )
        )
        results = {}
        for operation, capability in MANIFEST.items():
            if capability.status is not CapabilityStatus.EXECUTABLE:
                continue
            try:
                certify(operation, index)
                results[operation.value] = "certified"
            except AdjudicationRefusal as exc:
                results[operation.value] = exc.kind.value
        out[tag] = {
            "projection": str(projection),
            "equals_certified_release": UUID(projection) == CERTIFIED_RELEASE[2],
            "certify": dict(sorted(results.items())),
        }
    return out


#: The construction this verifier completes: built twice with identical bytes
#: at preview commit 2121a50e by builder b68ae789 (Codex supervised run,
#: 2026-10-14: built 107 s, twice identical 201 s, preserved 230 s, then exit 1
#: in the malformed-input verifier, a positional fact-selection defect).
CONSTRUCTION = {
    "preview_commit": "2121a50ebbf79434c16eac176890a42e0f027142",
    "builder_sha256": "b68ae78960e4b7d1f2db3b7c61923b69e034457824f33d875019a839675596ee",  # noqa: E501  # pragma: allowlist secret
    "supervised_stdout": ["built 107 s", "twice identical 201 s", "preserved 230 s"],
    "supervised_exit": 1,
    "failure": "AttributeError: 'CreatureTypeFact' object has no attribute "
    "'skills' in _replace_last (malformed-input editor took facts[-1] of a "
    "canonically assembled component)",
}
#: The bytes that construction wrote, pinned for --verify-existing.
CONSTRUCTED: dict[str, str] = {
    "srd-5-2-1-corpus-8781d4e0-a3b-c9-PREVIEW.json": "3ad7bdcb7aa926e38eca6c4019f7c77119427076a1639b2aa1f81cbfd25f59a3",  # noqa: E501  # pragma: allowlist secret
    "animals-C9-PROPOSAL.json": "c3dbcc7184f9167b356ec39bee9afbdb0c8bf22822f54d7951878f311275bc37",  # noqa: E501  # pragma: allowlist secret
    "magic-items-C9-PROPOSAL.json": "5255c82699780573c27905898720666d930abaf7d98f41e3524ea011a0e44168",  # noqa: E501  # pragma: allowlist secret
    "monsters-C9-PROPOSAL.json": "5b726871e6aa5b64120a1c01d33cd20764b6937e4ecce99102bac7a6456000a0",  # noqa: E501  # pragma: allowlist secret
    "spell-descriptions-C9-PROPOSAL.json": "48f1ba1291c2cba7aacc99e80a5552e49249467f9c6bf85c65cf2f64d4650848",  # noqa: E501  # pragma: allowlist secret
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--twice", action="store_true")
    parser.add_argument("--dry", action="store_true")
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="do not chain or write the preview: read the pinned constructed "
        "bytes, re-derive the proposals (no acceptance chain) and prove they "
        "render identically, then run the preservation, native and sequencing "
        "proofs",
    )
    args = parser.parse_args()
    started = datetime.datetime.now(datetime.UTC)
    t0 = time.monotonic()
    for path, digest in PINS.items():
        assert sha(path.read_bytes()) == digest, path
    paths = private_inputs(args.inputs)
    base = load_accepted_inputs(SUCCESSOR)
    built = build(base, paths)
    if args.dry:
        print(
            json.dumps(
                {
                    b: {k: v for k, v in x[2].items() if k != "claimed_span"}
                    for b, x in built.items()
                },
                indent=1,
            )
        )
        return
    rendered = {b: render(v[1]).encode("utf-8") for b, v in built.items()}
    reused: dict[str, Any] | None = None
    if args.verify_existing:
        on_disk = {n: (PREVIEW.parent / n).read_bytes() for n in CONSTRUCTED}
        assert {n: sha(b) for n, b in on_disk.items()} == CONSTRUCTED, "constructed"
        assert all(
            on_disk[f"{b}-C9-PROPOSAL.json"] == text for b, text in rendered.items()
        ), "re-derived proposals differ from the constructed ones"
        data = on_disk[PREVIEW.name]
        reused = {
            "construction": CONSTRUCTION,
            "constructed_sha256": CONSTRUCTED,
            "proposals_rederived_identical": True,
            "acceptance_chain_rerun": False,
        }
        print("verified existing construction", round(time.monotonic() - t0), "s")
    else:
        preview = chain(base, built)
        data = serialize_accepted_inputs(preview)
        print("built", round(time.monotonic() - t0), "s", flush=True)
    if args.twice and not args.verify_existing:
        again = build(base, paths)
        assert serialize_accepted_inputs(chain(base, again)) == data, "determinism"
        assert {b: render(v[1]).encode("utf-8") for b, v in again.items()} == rendered
        print("twice identical", round(time.monotonic() - t0), "s", flush=True)
    if not args.verify_existing:
        PREVIEW.parent.mkdir(parents=True, exist_ok=True)
        PREVIEW.write_bytes(data)
        for batch, text in rendered.items():
            (PREVIEW.parent / f"{batch}-C9-PROPOSAL.json").write_bytes(text)
    back = load_accepted_inputs(PREVIEW)
    assert serialize_accepted_inputs(back) == data
    for batch in rendered:
        reread = load_proposal(PREVIEW.parent / f"{batch}-C9-PROPOSAL.json")
        assert proposal_identity(reread) == proposal_identity(built[batch][1]), batch
    pres = preserved(base, data, built, back)
    lifted, lift_records = lift_accepted_inputs(
        base, (SCHEMA_22_VERSION, SCHEMA_22_HASH)
    )
    lifted_unchanged = all(
        getattr(lifted.oracle.representation, f)
        == getattr(base.oracle.representation, f)
        for f in COLLECTIONS
    )
    print("preserved", round(time.monotonic() - t0), "s", flush=True)
    nat = native(back, lifted, paths)
    seq = sequencing(back)
    print("native", round(time.monotonic() - t0), "s", flush=True)
    report = {
        "label": "SIMULATION - review-only native preview; not an Owner acceptance",
        "afterworlds_file": str(AFTERWORLDS_FILE),
        "builder_sha256": sha(Path(__file__).read_bytes()),
        "pins": {
            str(p.relative_to(REPO)).replace("\\", "/"): d for p, d in PINS.items()
        },
        "private_inputs": {
            "root": str(args.inputs),
            "proposals": {b: ACCEPTED[b] for b in built},
            "store_sha256": c.STORE_SHA256,
            "leaves_sha256": STORE_LEAVES_SHA256,
        },
        "touched_batches": sorted(built),
        "batches": {
            b: {
                **{k: v for k, v in x[2].items() if k != "claimed_span"},
                "proposal_identity": proposal_identity(x[1]),
                "rendered_proposal_sha256": sha(rendered[b]),
            }
            for b, x in built.items()
        },
        "claimed_spans": {
            k: v for x in built.values() for k, v in x[2]["claimed_span"].items()
        },
        "preview_sha256": sha(data),
        "preview_bytes": len(data),
        "oracle_identity": oracle_identity(back.oracle),
        "schema": [back.oracle.schema_version, back.oracle.schema_hash],
        "lifts": [lf.lift_id for lf in back.lifts],
        "successor_lift": {
            "lift_ids": [r.lift_id for r in lift_records],
            "representation_unchanged": lifted_unchanged,
        },
        "preservation": pres,
        "native": nat,
        "sequencing": seq,
        "deterministic_twice": args.twice or bool(reused),
        "verified_existing": reused,
        "pins_after": all(sha(p.read_bytes()) == d for p, d in PINS.items()),
        "run": {
            "pid": os.getpid(),
            "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "seconds": round(time.monotonic() - t0),
            "argv": sys.argv[1:],
        },
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (
        HERE / "reports" / ("c9-verification.json" if reused else "c9-preview.json")
    ).write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k not in ("preservation", "batches", "claimed_spans", "pins")
            },
            indent=1,
        )
    )
    assert all(v is True for v in pres.values() if isinstance(v, bool)), pres
    assert pres["components.changed"] == 336 and pres["provenance.added"] == 336
    assert pres["provenance.removed"] == 0 and not pres["components.handling_changes"]
    assert pres["review_units.expected_rules_added"] == 336
    assert lifted_unchanged and [r.lift_id for r in lift_records] == [
        "5d-lift-schema-21-to-22"
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
    assert seq["production_selection_is_still_c8"]
    assert report["pins_after"]
    print("ALL PROOFS PASSED", round(time.monotonic() - t0), "s")


if __name__ == "__main__":
    main()
