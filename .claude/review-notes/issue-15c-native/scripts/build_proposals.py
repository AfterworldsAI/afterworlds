"""Build the eleven schema-19 replacement proposals.

Each is its batch's identity-matched accepted proposal (``common.replayed``)
with, on each component it owns, the C5 native facts mapped by
``native_map``; that component's handling becomes ``mixed`` where it was
``prose_bound`` (its prose and retention reason are kept, as G1 kept its row
prose); a provenance claim per fact on the spans its source covers, only
inside the batch's own scope; one ``ExpectedRule`` per review unit, component
and new family naming exactly the spans those facts claim; and the schema-19
declaration. Nothing else in a proposal changes -- spans, units' leaves,
prose bindings, references, records and relationships are the accepted ones.

Writes ``../preview/proposals/<batch>-PROPOSAL.json`` (rendered) and
``../reports/proposals.json``.
"""

from __future__ import annotations

import collections
import dataclasses
import json
import re
from typing import Any

import common as c
import native_map as m

from afterworlds.ingestion.mechanical.authoring import render
from afterworlds.ingestion.mechanical.models import ExpectedRule
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, proposal_identity
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentHandling,
    ComponentOption,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    fact_from_payload,
    fact_key,
    fact_target_key,
    representation_schema_hash,
)

ORIGIN = ("CRD Issue 15c native preview (review only): the accepted {batch} proposal "
          "{identity}, mechanically rebound where recorded at the prior release, with "
          "the independently reviewed C5 schema-19 source facts on the components it "
          "owns")


def norm(text: str) -> str:
    text = text.replace("&emsp;", " ")
    text = re.sub(r"\s*<br>\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def source_lines(file: str, first: int, last: int) -> str:
    return norm(" ".join(c.lines(file)[first - 1:last]))


def owner_map() -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for batch in c.AFFECTED:
        for comp in c.replayed(batch).proposed_representation.components:
            key = (comp.record_key, comp.semantic_key)
            assert key not in out or out[key] == batch, key
            out.setdefault(key, batch)
    return out


def claim_spans(hint: dict[str, Any], candidates: dict[str, str]) -> list[str]:
    """The owned, bound spans this fact's source covers (``candidates`` maps
    span id -> normalized span text)."""
    if hint["kind"] == "quote":
        q = norm(hint["source"]["quote"])
        return sorted(s for s, t in candidates.items() if q and q in t)
    r = hint["record"]
    if hint["kind"] == "entry":
        sp = hint["entry"]["source_span"]
        text = source_lines(sp["file"], sp["first_line"], sp["last_line"])
    else:  # the stat block's profile region, heading through CR
        src = r["source"]
        lines = c.lines(src["file"])
        first = src["block_first_line"]
        cr = next(n for n in range(first, src["block_last_line"] + 1)
                  if lines[n - 1].startswith("**CR**"))
        text = source_lines(src["file"], first, cr)
    return sorted(s for s, t in candidates.items() if t and t in text)


def build() -> tuple[dict[str, MechanicalProposal], dict[str, Any]]:
    leaves = c.leaf_texts()
    owners = owner_map()
    schema = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    by_component: dict[tuple[str, str], list[tuple[Any, dict[str, Any]]]] = (
        collections.defaultdict(list))
    for rk, ck, payload, hint in m.items():
        by_component[(rk, ck)].append((fact_from_payload(payload), hint))
    ownerless = sorted(k for k in by_component if k not in owners)
    assert not ownerless, ("mapped C5 components no affected batch owns", ownerless)
    proposals, report = {}, {"batches": {}, "unresolved_claims": []}
    for batch in c.AFFECTED:
        p = c.replayed(batch)
        rep = p.proposed_representation
        spans = {x.span.span_id: x.span for x in p.proposed_spans}
        texts = {sid: norm(leaves[s.leaf_id][s.char_start:s.char_end]) for sid, s in spans.items()}
        bound: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for b in rep.prose_bindings:
            if b.span_id in spans:
                bound[(b.record_key, b.component_key)].add(b.span_id)
        # Relocation: a quoted fact whose sentence no span of its anchored
        # component binds moves to the one sibling component of this batch
        # that binds it (correspondence.md, placement corrections); anything
        # else stays an unresolved claim.
        placed: dict[tuple[str, str], list[tuple[Any, dict[str, Any]]]] = (
            collections.defaultdict(list))
        for key, entries in by_component.items():
            if owners.get(key) != batch:
                continue
            for fact, hint in entries:
                target = key
                own = {s_: texts[s_] for s_ in bound[key]}
                if hint["kind"] == "quote" and not claim_spans(hint, own):
                    homes = sorted(k for k, sids in bound.items() if k != key and claim_spans(
                        hint, {s_: texts[s_] for s_ in sids}))
                    if len(homes) == 1:
                        target = homes[0]
                        report.setdefault("relocations", []).append(
                            {"batch": batch, "family": fact.FAMILY.value,
                             "c5_component": list(key), "native_component": list(target),
                             "quote": hint["source"]["quote"]})
                placed[target].append((fact, hint))
        components, claims = [], []
        family_spans: dict[tuple[str, str, str], set[str]] = collections.defaultdict(set)
        added = 0
        for comp in rep.components:
            key = (comp.record_key, comp.semantic_key)
            new = placed.get(key, [])
            if not new:
                components.append(comp)
                continue
            candidates = {s: texts[s] for s in bound[key]}
            assert not comp.options or not any(h.get("option") for _, h in new), key
            gathered = []  # (fact, chosen spans, option)
            for fact, hint in new:
                chosen = claim_spans(hint, candidates)
                if not chosen:
                    report["unresolved_claims"].append(
                        {"batch": batch, "record": key[0], "component": key[1],
                         "family": fact.FAMILY.value, "hint": hint["kind"]})
                    continue
                gathered.append((fact, chosen, hint.get("option", "")))
            # A component is a conjunction or a choice. One printed activity is
            # not a choice: its facts are direct. Several are a choice, and each
            # option is complete: it also carries the component's direct facts
            # (a tool's tool_entry), which the component then no longer states
            # directly (correspondence.md, tool activities).
            option_keys = sorted({o for _, _, o in gathered if o})
            if len(option_keys) == 1:
                gathered = [(f, ch, "") for f, ch, _ in gathered]
                option_keys = []
            if option_keys:
                assert not comp.facts, key
                direct = [(f, ch) for f, ch, o in gathered if not o]
                gathered = [(f, ch, o) for f, ch, o in gathered if o] + [
                    (f, ch, o) for o in option_keys for f, ch in direct]
            facts = list(comp.facts) + [f for f, _, o in gathered if not o]
            options: dict[str, list[Any]] = {o.semantic_key: list(o.facts) for o in comp.options}
            for fact, chosen, option in gathered:
                if option:
                    options.setdefault(option, []).append(fact)
                for sid in chosen:
                    claims.append(ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(key[0], key[1], fact, option), sid,
                        ProvenanceRole.CONTEXTUAL))
                    family_spans[(key[0], key[1], fact.FAMILY.value)].add(sid)
            added += len({id(f) for f, _, _ in gathered})
            keys = [fact_key(f) for f in facts]
            assert len(keys) == len(set(keys)), ("fact key collision", key)
            for o, ofacts in options.items():
                okeys = [fact_key(f) for f in ofacts]
                assert len(okeys) == len(set(okeys)), ("option fact key collision", key, o)
            existing = {o.semantic_key: o for o in comp.options}
            new_options = tuple(
                dataclasses.replace(existing[o], facts=tuple(sorted(f, key=fact_key)))
                if o in existing else ComponentOption(semantic_key=o,
                                                      facts=tuple(sorted(f, key=fact_key)))
                for o, f in sorted(options.items()))
            handling = (ComponentHandling.MIXED if comp.handling is ComponentHandling.PROSE_BOUND
                        else comp.handling)
            components.append(dataclasses.replace(
                comp, handling=handling, facts=tuple(sorted(facts, key=fact_key)),
                options=new_options))
        unit_of_leaf = {leaf: u.unit_id for u in p.proposed_review_units for leaf in u.leaf_ids}
        rules: dict[str, list[ExpectedRule]] = collections.defaultdict(list)
        for (rk, ck, family), sids in sorted(family_spans.items()):
            per_unit: dict[str, list[str]] = collections.defaultdict(list)
            for sid in sorted(sids):
                unit = unit_of_leaf.get(spans[sid].leaf_id)
                assert unit is not None, ("claimed span outside every unit", batch, rk, ck, sid)
                per_unit[unit].append(sid)
            for unit, unit_sids in per_unit.items():
                rules[unit].append(ExpectedRule(record_key=rk, component_key=ck,
                                                fact_family=family,
                                                source_span_ids=tuple(unit_sids)))
        units = tuple(dataclasses.replace(u, expected_rules=(*u.expected_rules,
                                                                  *rules.get(u.unit_id, ())))
                      for u in p.proposed_review_units)
        new_rep = dataclasses.replace(rep, components=tuple(components),
                                      provenance=(*rep.provenance, *claims))
        proposal = dataclasses.replace(
            p, schema_version=schema[0], schema_hash=schema[1], proposed_representation=new_rep,
            proposed_review_units=units,
            proposal_origin=ORIGIN.format(batch=batch, identity=proposal_identity(p)))
        proposals[batch] = proposal
        report["batches"][batch] = {
            "replayed_identity": proposal_identity(p), "facts_added": added,
            "claims_added": len(claims),
            "expected_rules_added": sum(len(v) for v in rules.values()),
            "components_given_facts": sum(1 for a, b in zip(rep.components, components,
                                                            strict=True) if a is not b)}
    # Every mapped fact is claimed somewhere; placement is checked item by item
    # in reconcile.py.
    assert not report["unresolved_claims"], report["unresolved_claims"][:5]
    return proposals, report


def main() -> None:
    proposals, report = build()
    out = c.NATIVE / "preview" / "proposals"
    out.mkdir(parents=True, exist_ok=True)
    for batch, p in proposals.items():
        data = render(p)
        (out / f"{batch}-PROPOSAL.json").write_text(data, "utf-8", newline="\n")
        report["batches"][batch].update(
            proposal_identity=proposal_identity(p),
            rendered_sha256=c.hashlib.sha256(data.encode()).hexdigest())
    (c.NATIVE / "reports" / "proposals.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "unresolved_claims"}, indent=1))
    print("unresolved", len(report["unresolved_claims"]))
    for u in report["unresolved_claims"][:20]:
        print(u)


if __name__ == "__main__":
    main()
