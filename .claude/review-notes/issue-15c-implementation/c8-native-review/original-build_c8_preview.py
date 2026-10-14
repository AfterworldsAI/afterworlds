"""CRD Issue 15c -- native SIMULATED preview of raw candidate C8 (r2).

REVIEW MATERIAL ONLY: not an Owner acceptance, recording, publication or
activation. Run from the repository root (a worktree works) with the
repository venv; ``afterworlds`` must import from this checkout's ``src``.

Construction (the reviewed C7 method, under schema 21):

* prior: the recorded C7 successor ``srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json``
  (``2853f30a...``), whose real receipts are preserved;
* each C8 fact's owning batch is identified natively from the successor's
  acceptance records -- of the spans the component's existing fact claims
  name (creature profiles) or of its prose-binding spans (species, Find
  Familiar) -- and must equal the correspondence ``batch``;
* each touched batch's accepted proposal (pinned file, identity-matched to the
  successor's anchor) gains its C8 facts: creature profiles keep their mixed
  handling, facts, options, prose, retention reason and bindings and gain one
  ``creature_type`` fact; the nine species ``creature_type`` components and
  ``spells.find_familiar/effect`` go prose_bound -> mixed keeping prose and
  retention reason. One contextual provenance claim per fact, on the one bound
  span holding the fact's quote, and an ExpectedRule in that span's review
  unit. Re-declared at the schema-21 pair; nothing else in it moves;
* in the successor's anchor order each touched batch is excised claim-based
  (``issue-15c-native/scripts/excise.py``) and its new proposal accepted
  natively with SIMULATED evidence. The first acceptance records the
  registered 20 -> 21 lift.

``--dry`` stops after the mapping. ``--twice`` rebuilds and compares bytes.
Proofs, each asserted, are written to ``reports/c8-preview.json``.
"""

from __future__ import annotations

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
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    load_bound_corpus,
)
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
    ComponentHandling,
    ComponentReference,
    CreatureSizeFact,
    CreatureTypeFact,
    CreatureTypeKind,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    SummonedCreatureTypeFact,
    fact_from_payload,
    fact_key,
    fact_payload,
    fact_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    SCHEMA_20_HASH,
    SCHEMA_20_VERSION,
    SCHEMA_21_HASH,
    SCHEMA_21_VERSION,
    lift_accepted_inputs,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402

AFTERWORLDS_FILE = Path(afterworlds.__file__).resolve()
assert AFTERWORLDS_FILE.is_relative_to(REPO / "src"), AFTERWORLDS_FILE
assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_21_VERSION
assert representation_schema_hash() == SCHEMA_21_HASH
#: The frozen accepted schema 20 is still the registered lift source.
assert SCHEMA_20_HASH == (
    "759dcc1f9de2cac9254be108ca8a83433ca30854061276a9c349a370e1c6e77a"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def locate(rel: str, digest: str) -> Path:
    """*rel* under this checkout or the nearest ancestor holding it, pinned.

    The accepted proposals and the isolated release store are git-ignored, so
    a worktree reads them from the main checkout read-only.
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
CAND = IMPL / "candidate-c8"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"
SUCCESSOR = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json"
C8 = CAND / "c8.json"
CORRESPONDENCE = CAND / "correspondence.json"
INVENTORY = CAND / "inventory.json"
DELTA = CAND / "schema-21-delta.md"
CORRECTION_REVIEW = locate(
    ".claude/review-notes/issue-15c-implementation/codex-c8-raw-correction-review.md",
    "9e80f93aef59e99f5385c335f2176ca78d02061b89482a6c236f59bb91ba48aa",
)
PINS: dict[Path, str] = {
    SUCCESSOR: "2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373",
    C8: "7e7d5b43ccd7bd877e0764643e57df1270419dd758a6ae5fcf52422081e42628",
    CORRESPONDENCE: "43589153ee7befe4e46052f0e7fe7db053b5a9a22c3ff8a6b4468e41c9e0ce24",
    INVENTORY: "3f05591efa78656132db3a179f174b560ca3e8f3d3ebfd525e56b400e87ce55d",
    DELTA: "1c33046c692692f48e63766e61fa6f2b7785b9118f50db241503f5868223b1b5",
    CORRECTION_REVIEW: (
        "9e80f93aef59e99f5385c335f2176ca78d02061b89482a6c236f59bb91ba48aa"
    ),
}
# The source files the C8 candidate pins (its own pin table names C7 too).
for _rel, _digest in json.loads(C8.read_bytes())["pins"].items():
    PINS.setdefault(REPO / _rel, _digest)

_C5 = ".claude/review-notes/issue-15c-native/preview/proposals/{}-PROPOSAL.json"
_C7 = (
    ".claude/worktrees/agent-afb6123d0b7851456/.claude/review-notes/"
    "issue-15c-c7-native/preview/{}-C7-PROPOSAL.json"
)
#: The accepted proposal each touched batch was last recorded from: the C5
#: packet (four) and the accepted C7 preview (character-origins-feats);
#: (relative path, rendered SHA-256, proposal identity).
ACCEPTED: dict[str, tuple[str, str, str]] = {
    "spell-descriptions": (
        _C5.format("spell-descriptions"),
        "e8830765f3e8a728b810627bd4f58de86d37ed3ba9c447756ade368cf027957d",
        "dce22fbd6f89a61cbd7ab5efa0be75f81eec87840ae91731e8162c8fabfbbdc9",
    ),
    "magic-items": (
        _C5.format("magic-items"),
        "28a7f4d5ceeaa8a2a19bb4d09313dc97cdc9b9263a2b37230f4ac882eb3c0e31",
        "bc4979d74a841065af99502e0cf20d157ab4bedd1fd7a9724a2130ffa092e712",
    ),
    "monsters": (
        _C5.format("monsters"),
        "9f30cf57619ceca946444a331644b90c1f7af6720962cb936abc0faa20b1474f",
        "ff24d9daf6dd81a760778865a011a5da236b56514a32753c2a8034f5f3eec617",
    ),
    "animals": (
        _C5.format("animals"),
        "7186c42a3c731b805a3adce43ca5d2af91a46833e70295872193a1c71dc68631",
        "efa248a979c21d293701253cda86b561b876bec332667437769abebbb06221c9",
    ),
    "character-origins-feats": (
        _C7.format("character-origins-feats"),
        "587068868bbcbc05cb881f3ae4b2e68cb2c47c257192671470bdf792c17f178e",
        "1e7b63d3800154eee539297b0ae5d4f9efbfe21c1776986db133e3cc046bfd28",
    ),
}
PREVIEW = HERE / "preview/srd-5-2-1-corpus-8781d4e0-a3b-c8-PREVIEW.json"
ORIGIN = (
    "CRD Issue 15c C8 native preview (review only): the accepted {batch} proposal "
    "{identity} with its raw C8 r2 facts (schema-21 creature types and the Find "
    "Familiar source choice) on their components, declared at schema 21"
)
COLLECTIONS = (
    "records",
    "components",
    "prose_bindings",
    "relationships",
    "references",
    "provenance",
)


def norm(text: str) -> str:
    return " ".join(text.replace("&emsp;", " ").split())


def rows() -> list[dict[str, Any]]:
    """The 346 candidate facts, each joined to its correspondence row."""
    raw = json.loads(C8.read_bytes())
    facts = [*raw["facts"], *raw["source_type_choices"]]
    corr = {(r["record_key"], r["component_key"]): r for r in json.loads(
        CORRESPONDENCE.read_bytes()
    )}
    assert len(facts) == len(corr) == 346
    out = []
    for f in facts:
        r = corr[(f["record_key"], f["component_key"])]
        assert (r["file"], r["line"], r["quote"]) == (
            f["source"]["file"],
            f["source"]["line"],
            f["source"]["quote"],
        ), r
        out.append({**f, "batch": r["batch"], "claim_spans": r["claim_spans"]})
    return out


def owners(
    base: AcceptedInputs, facts: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Each fact's owning batch, read natively from the successor's acceptance
    records: of the spans the component's existing fact claims name, or, for a
    component with no fact, of its prose-binding spans."""
    span_batch = {r.span_id: r.batch_id for r in base.acceptances}
    rep = base.oracle.representation
    bound: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for b in rep.prose_bindings:
        bound[(b.record_key, b.component_key)].add(b.span_id)
    claimed: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for cl in rep.provenance:
        if cl.target_kind is ProvenanceTargetKind.FACT:
            claimed[(cl.target_key[0], cl.target_key[1])].add(cl.span_id)
    out: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for f in facts:
        key = (f["record_key"], f["component_key"])
        (batch,) = {span_batch[s] for s in claimed.get(key) or bound[key]}
        assert batch == f["batch"], ("correspondence batch", key, batch)
        out[batch].append(f)
    return dict(out)


def build_one(
    batch: str, facts: list[dict[str, Any]], leaves: dict[str, str]
) -> tuple[MechanicalProposal, MechanicalProposal, dict[str, Any]]:
    rel, rendered, identity = ACCEPTED[batch]
    p = load_proposal(locate(rel, rendered))
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
        assert fact_payload(fact) == f["fact"], key
        src = f["source"]
        assert src["quote"] in c.lines(src["file"])[src["line"] - 1], ("line", key)
        quote = norm(src["quote"])
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
    components, handling_changes = [], []
    for comp in rep.components:
        key = (comp.record_key, comp.semantic_key)
        if key in added:
            if comp.handling is ComponentHandling.MIXED:
                # A creature profile: everything kept, one fact added.
                assert type(added[key]) is CreatureTypeFact, key
                assert any(type(x) is CreatureSizeFact for x in comp.facts), key
                comp = dataclasses.replace(comp, facts=(*comp.facts, added[key]))
            else:
                assert (
                    comp.handling is ComponentHandling.PROSE_BOUND
                    and not comp.facts
                    and not comp.options
                    and comp.prose_retention_reason_code is not None
                ), key
                handling_changes.append(f"{key[0]}/{key[1]}")
                comp = dataclasses.replace(
                    comp, handling=ComponentHandling.MIXED, facts=(added[key],)
                )
        components.append(comp)
    changed = [
        (a, b) for a, b in zip(rep.components, components, strict=True) if a != b
    ]
    assert len(changed) == len(facts) == len(added), (batch, len(changed))
    for a, b in changed:
        # Only handling (prose_bound -> mixed) and the one appended fact moved.
        assert dataclasses.replace(b, handling=a.handling, facts=a.facts) == a
        assert b.facts[: len(a.facts)] == a.facts and len(b.facts) == len(a.facts) + 1
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
        schema_version=SCHEMA_21_VERSION,
        schema_hash=SCHEMA_21_HASH,
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
            "accepted_proposal_identity": identity,
            "accepted_rendered_sha256": rendered,
            "accepted_from_schema": p.schema_version,
            "facts_added": len(added),
            "claims_added": len(claims),
            "expected_rules_added": sum(len(v) for v in rules.values()),
            "handling_prose_bound_to_mixed": sorted(handling_changes),
            "claimed_span": chosen_by_fact,
            "fact_families": dict(
                collections.Counter(f.FAMILY.value for f in added.values())
            ),
        },
    )


def build(
    base: AcceptedInputs,
) -> dict[str, tuple[MechanicalProposal, MechanicalProposal, dict[str, Any]]]:
    facts = rows()
    leaves = c.leaf_texts()
    inventory = json.loads(INVENTORY.read_bytes())["touched_batches"]
    out = {}
    for batch, fs in owners(base, facts).items():
        (anchor,) = [a for a in base.schema_anchors if a.batch_id == batch]
        assert anchor.proposal_identity == ACCEPTED[batch][2], ("anchor", batch)
        out[batch] = build_one(batch, fs, leaves)
        assert out[batch][2]["facts_added"] == inventory[batch]["facts"], batch
    assert set(out) == set(inventory) == set(ACCEPTED)
    assert sum(v[2]["facts_added"] for v in out.values()) == len(facts) == 346
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
) -> dict[str, Any]:
    """Untouched rows are compared in their own relative order: evidence rows
    serialize in canonical order (``canonical_order`` reads ``accepted_at``),
    so the re-accepted rows may sit elsewhere (C7 recording ``compare()``)."""
    touched = set(built)
    G, P = json.loads(serialize_accepted_inputs(base)), json.loads(data)
    keep = lambda rows: [r for r in rows if r["batch_id"] not in touched]  # noqa: E731
    out: dict[str, Any] = {
        f"acceptance.{f}.untouched_rows_identical_in_order": keep(G["acceptance"][f])
        == keep(P["acceptance"][f])
        for f in ("batches", "records", "review_unit_records", "schema_anchors")
    }
    g_anchor = [a["batch_id"] for a in G["acceptance"]["schema_anchors"]]
    p_anchor = [a["batch_id"] for a in P["acceptance"]["schema_anchors"]]
    # Re-acceptance appends: the untouched anchors keep their order and the
    # five touched follow in the C7 anchor order.
    out["acceptance.schema_anchors.order_is_untouched_then_touched_in_c7_order"] = (
        p_anchor
        == [b for b in g_anchor if b not in touched]
        + [b for b in g_anchor if b in touched]
    )
    out["acceptance.batch_set_unchanged"] = sorted(g_anchor) == sorted(p_anchor)
    (lift,) = P["acceptance"]["lifts"][len(G["acceptance"]["lifts"]) :]
    out["lifts.prefix_unchanged"] = (
        P["acceptance"]["lifts"][:-1] == G["acceptance"]["lifts"]
    )
    out["lifts.added_exactly_20_to_21"] = (
        lift["lift_id"] == "5d-lift-schema-20-to-21"
        and (lift["from_version"], lift["from_hash"])
        == (SCHEMA_20_VERSION, SCHEMA_20_HASH)
        and (lift["to_version"], lift["to_hash"]) == (SCHEMA_21_VERSION, SCHEMA_21_HASH)
    )
    out["representation_schema.was_20_now_21"] = G["representation_schema"] == {
        "version": SCHEMA_20_VERSION,
        "hash": SCHEMA_20_HASH,
    } and P["representation_schema"] == {
        "version": SCHEMA_21_VERSION,
        "hash": SCHEMA_21_HASH,
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
    # Exact shape of the change: 346 components gain one fact each; ten of
    # them change prose_bound -> mixed; 346 claims added, none removed;
    # records, bindings, relationships and references identical.
    gc = {(x.record_key, x.semantic_key): x for x in gr.components}
    pc = {(x.record_key, x.semantic_key): x for x in pr.components}
    moved = {k for k in gc if gc[k] != pc.get(k)}
    out["components.same_keys"] = gc.keys() == pc.keys()
    out["components.changed"] = len(moved)
    out["components.changed_only_by_one_appended_type_fact"] = all(
        pc[k].facts[:-1] == gc[k].facts
        and type(pc[k].facts[-1]) in (CreatureTypeFact, SummonedCreatureTypeFact)
        and dataclasses.replace(pc[k], handling=gc[k].handling, facts=gc[k].facts)
        == gc[k]
        for k in moved
    )
    out["components.handling_changes"] = sorted(
        f"{k[0]}/{k[1]}:{gc[k].handling.value}->{pc[k].handling.value}"
        for k in moved
        if gc[k].handling != pc[k].handling
    )
    out["provenance.removed"] = len(set(gr.provenance) - set(pr.provenance))
    out["provenance.added"] = len(set(pr.provenance) - set(gr.provenance))
    for f in ("records", "prose_bindings", "relationships", "references"):
        out[f"representation.{f}.identical_set"] = set(getattr(gr, f)) == set(
            getattr(pr, f)
        )
    return out


FAMILIAR = ("spells.find_familiar", "effect")


def _with_fact(rep: Any, key: tuple[str, str], fn: Any) -> Any:
    """*rep* with the last fact of component *key* replaced by ``fn(fact)``."""
    comps = []
    for comp in rep.components:
        if (comp.record_key, comp.semantic_key) == key:
            comp = dataclasses.replace(comp, facts=(*comp.facts[:-1], fn(comp.facts[-1])))
        comps.append(comp)
    return dataclasses.replace(rep, components=tuple(comps))


T = CreatureTypeKind
#: Malformed variants of the preview: (component, change, finding substring).
MALFORMED: dict[str, tuple[tuple[str, str], Any, str]] = {
    "familiar_form_whose_type_is_not_beast": (
        ("animals.cat", "cat"),
        lambda f: dataclasses.replace(f, type=T.FEY),
        "summoned_creature_type names animals.cat/cat",
    ),
    "familiar_unknown_form": (
        FAMILIAR,
        lambda f: dataclasses.replace(
            f,
            forms=tuple(
                sorted(
                    (
                        *f.forms,
                        ComponentReference(
                            record_key="animals.no_such_beast",
                            component_key="no_such_beast",
                        ),
                    ),
                    key=lambda r: (r.record_key, r.component_key),
                )
            ),
        ),
        "not a component of this draft",
    ),
    "familiar_non_profile_form": (
        FAMILIAR,
        lambda f: dataclasses.replace(
            f,
            forms=tuple(
                sorted(
                    (*f.forms, ComponentReference(record_key=FAMILIAR[0], component_key=FAMILIAR[1])),
                    key=lambda r: (r.record_key, r.component_key),
                )
            ),
        ),
        "not a creature profile",
    ),
    "familiar_duplicate_choice": (
        FAMILIAR,
        lambda f: dataclasses.replace(f, type_choice=(T.CELESTIAL, T.CELESTIAL, T.FEY)),
        "type_choice is at least two types",
    ),
    "steed_single_choice": (
        ("spells.find_steed.otherworldly_steed", "otherworldly_steed"),
        lambda f: dataclasses.replace(f, type_choice=(T.FEY,)),
        "type_choice is at least two types",
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
                t0 = time.monotonic()
                out["validate_candidate_findings"] = list(
                    validate_candidate(candidate, corpus)
                )
                out["validate_candidate_seconds"] = round(time.monotonic() - t0)
                comps = {
                    (x.record_key, x.semantic_key)
                    for x in candidate.representation.components
                }
                malformed = {}
                for name, (key, fn, needle) in MALFORMED.items():
                    if key not in comps:
                        malformed[name] = [f"component {key} absent"]
                        continue
                    bad = dataclasses.replace(
                        candidate,
                        representation=_with_fact(candidate.representation, key, fn),
                    )
                    malformed[name] = [
                        x for x in validate_candidate(bad, corpus) if needle in x
                    ][:3]
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
                    own_gate_failures=[f.detail for f in own.failures][:5],
                    successor_refused_against_preview=not cross.passed,
                    preview_refused_against_successor=not back.passed,
                )
        finally:
            engine.dispose()
    return out


def main() -> None:
    started = datetime.datetime.now(datetime.UTC)
    t0 = time.monotonic()
    for path, digest in PINS.items():
        assert sha(path.read_bytes()) == digest, path
    base = load_accepted_inputs(SUCCESSOR)
    built = build(base)
    if "--dry" in sys.argv:
        print(json.dumps({b: {k: v for k, v in x[2].items() if k != "claimed_span"}
                          for b, x in built.items()}, indent=1))
        return
    preview = chain(base, built)
    data = serialize_accepted_inputs(preview)
    rendered = {b: render(v[1]).encode("utf-8") for b, v in built.items()}
    print("built", round(time.monotonic() - t0), "s", flush=True)
    if "--twice" in sys.argv:
        again = build(base)
        assert serialize_accepted_inputs(chain(base, again)) == data, "determinism"
        assert {b: render(v[1]).encode("utf-8") for b, v in again.items()} == rendered
        print("twice identical", round(time.monotonic() - t0), "s", flush=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.write_bytes(data)
    for batch, text in rendered.items():
        (PREVIEW.parent / f"{batch}-C8-PROPOSAL.json").write_bytes(text)
    back = load_accepted_inputs(PREVIEW)
    assert serialize_accepted_inputs(back) == data
    for batch, text in rendered.items():
        reread = load_proposal(PREVIEW.parent / f"{batch}-C8-PROPOSAL.json")
        assert proposal_identity(reread) == proposal_identity(built[batch][1]), batch
    pres = preserved(base, data, built, back)
    # The successor at the live contract: the registered lift, data unchanged.
    lifted, lift_records = lift_accepted_inputs(
        base, (SCHEMA_21_VERSION, SCHEMA_21_HASH)
    )
    lifted_unchanged = all(
        getattr(lifted.oracle.representation, f)
        == getattr(base.oracle.representation, f)
        for f in COLLECTIONS
    )
    print("preserved", round(time.monotonic() - t0), "s", flush=True)
    nat = native(back, lifted)
    report = {
        "label": "SIMULATION - review-only native preview; not an Owner acceptance",
        "afterworlds_file": str(AFTERWORLDS_FILE),
        "builder_sha256": sha(Path(__file__).read_bytes()),
        "scripts_sha256": {
            n: sha((NOTES / "issue-15c-native/scripts" / n).read_bytes())
            for n in ("common.py", "excise.py")
        },
        "pins": {
            (
                str(p.relative_to(REPO)) if p.is_relative_to(REPO) else str(p)
            ).replace("\\", "/"): d
            for p, d in PINS.items()
        },
        "accepted_inputs_located": {b: ACCEPTED[b][:2] for b in built},
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
        "deterministic_twice": "--twice" in sys.argv,
        "pins_after": all(sha(p.read_bytes()) == d for p, d in PINS.items()),
        "run": {
            "pid": os.getpid(),
            "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "seconds": round(time.monotonic() - t0),
            "argv": sys.argv[1:],
        },
    }
    (HERE / "reports").mkdir(exist_ok=True)
    (HERE / "reports/c8-preview.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in ("preservation", "batches")},
            indent=1,
        )
    )
    assert all(v is True for k, v in pres.items() if isinstance(v, bool)), pres
    assert pres["components.changed"] == 346 and pres["provenance.added"] == 346
    assert pres["provenance.removed"] == 0
    assert pres["review_units.expected_rules_added"] == 346
    assert len(pres["components.handling_changes"]) == 10
    assert lifted_unchanged and [r.lift_id for r in lift_records] == [
        "5d-lift-schema-20-to-21"
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
    print("ALL PROOFS PASSED", round(time.monotonic() - t0), "s")


if __name__ == "__main__":
    main()
