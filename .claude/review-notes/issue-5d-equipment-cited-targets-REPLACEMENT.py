"""The Equipment cited-targets candidate, composed in memory over no prior.

CRD Issue 5d Equipment cited-targets packet (#132, #137). REVIEW MATERIAL:
nothing here is accepted, recorded, published or activated, and no Owner
approval exists for it. There is deliberately no recording step.

The acceptance module has no supersession, so a changed Equipment batch can
only be shown as a fresh chain over no prior. This script composes the recorded
twenty-two batches of ``srd-5-2-1-corpus-3fe24ff6-4e3.json`` (read, never
written) through the native seams in their recorded order, with:

* every batch's recorded proposal file (SHA-256 pinned) and recorded rule,
  reviewer and time, except ``equipment``, which takes the candidate
  ``issue-5d-equipment-cited-targets-PROPOSAL.json`` under the simulated
  reviewer;
* every recorded resolution re-applied **verbatim from the recorded artifact**
  (not re-drafted: the name-matching generators would now see the new records),
  after the batch it was recorded after, with its recorded evidence;
* then the 161 unrecorded cited-target drafts, simulated.

It proves every non-Equipment claim is kept, prints the Equipment semantic
delta in printed order with full text, and reports counts, violations and
findings. Writes nothing but ``--delta PATH`` when asked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal  # noqa: E402
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_payload,
    reference_resolution_violations,
)

RECORDED_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-3fe24ff6-4e3.json"
RECORDED_SHA256 = "4ad85dab4ec9e5967779a0bb24f22c099e0aafdc9762088e340f7796b86290ba"
SCRATCH_DB = REPO / ".claude" / "_rc" / "msc" / "rel" / "afterworlds.db"


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


#: The recorded manifest: batch order, identities and file SHA-256s.
REPLACEMENT = _load(
    "monsters_corrections_replacement",
    HERE / "issue-5d-monsters-corrections-REPLACEMENT.py",
)
LATER = (
    (
        "monsters",
        REPLACEMENT.MONSTERS_IDENTITY,
        REPLACEMENT.MONSTERS_FILE_SHA256,
        REPLACEMENT.MONSTERS_FILE,
    ),
    (
        "animals",
        "19685bc2b3c9a22d484b0435ba78950185dab00590a58bae36c8f41ca2fb53cd",
        "a3057b73ec23db2bf169286446e25047ef7d54ebc96061083e3c9a2d48045ebb",
        HERE / "issue-5d-animals-PROPOSAL.json",
    ),
)
#: Recorded batches after which a resolution step was recorded, and the drafts
#: file (as REPLACEMENT.DRAFTS pins it) that lists that step's resolution ids.
#: The shared ``reference`` file (sorted by id) holds three steps: id -> batch,
#: as REPLACEMENT.RESOLUTIONS names their draft functions.
REFERENCE_SPLIT = {
    "resolve-attack-roll-playing-the-game-1": "checks-actions-rests",
    "resolve-armor-class-character-creation-1": "character-creation-foundations",
    "resolve-proficiency-bonus-character-creation-1": (
        "character-creation-foundations"
    ),
    "resolve-choose-background-character-origins-1": "character-origins-feats",
    "resolve-choose-species-character-origins-1": "character-origins-feats",
    "resolve-background-feat-feats-1": "character-origins-feats",
}

CANDIDATE = HERE / "issue-5d-equipment-cited-targets-PROPOSAL.json"
CANDIDATE_SHA256 = "13271e035f76316a6f78cf90ccca1f68ec233738ce31a93c7303052bc5bb02e0"
CANDIDATE_IDENTITY = "309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680"
CITED_DRAFTS = HERE / "issue-5d-equipment-cited-targets-resolutions-DRAFTS.json"
CITED_DRAFTS_SHA256 = "bfbf5a7ac78fa96fd568148d26bd2690415a4add9196d8ca393ef7b4f0c139eb"
CITED_SUFFIX = "-equipment-cited-1"

SIMULATED_REVIEWER: str = REPLACEMENT.SIMULATED_REVIEWER
SIMULATED_RULE: str = REPLACEMENT.SIMULATED_RULE
SIMULATED_AT: str = REPLACEMENT.SIMULATED_AT

#: Batches, records, spans, review units, resolutions; reference and
#: uncovered-leaf findings on the release.
EXPECTED_RECORDED = ((22, 1759, 10424, 1459, 1247), (252, 29))
EXPECTED = {
    "replayed": ((22, 1826, 10484, 1459, 1247), None),
    "cited": ((22, 1826, 10484, 1459, 1408), (91, 29)),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def recorded() -> AcceptedInputs:
    assert _sha(RECORDED_PATH.read_bytes()) == RECORDED_SHA256, "recorded changed"
    return load_accepted_inputs(RECORDED_PATH)


def _steps(rec: AcceptedInputs) -> dict[str, tuple[ReferenceResolution, ...]]:
    """The recorded resolutions, verbatim, keyed by the batch they followed."""
    by_id = {r.resolution_id: r for r in rec.oracle.reference_resolutions}
    ids: dict[str, list[str]] = {}
    for name, (sha, batches) in REPLACEMENT.DRAFTS.items():
        raw = REPLACEMENT.drafts_path(name).read_bytes()
        assert _sha(raw) == sha, name
        listed = [d["resolution_id"] for d in json.loads(raw)]
        if name == "reference":
            assert sorted(listed) == sorted(REFERENCE_SPLIT), listed
            for i in listed:
                ids.setdefault(REFERENCE_SPLIT[i], []).append(i)
        else:
            (batch,) = batches
            ids[batch] = listed
    for batch, suffix in (("monsters", "-monsters-1"), ("animals", "-animals-1")):
        ids[batch] = [i for i in by_id if i.endswith(suffix)]
    placed = [i for v in ids.values() for i in v]
    assert len(placed) == len(set(placed)) == len(by_id), "not a partition"
    return {b: tuple(by_id[i] for i in v) for b, v in ids.items()}


def _evidence(rec: AcceptedInputs) -> tuple[dict[str, tuple[str, str, str]], Any]:
    """Recorded (rule, reviewer, time) per batch; resolution evidence per id."""
    rules = {b.batch_id: b.rule for b in rec.batches}
    who = {(a.batch_id, a.reviewer, a.accepted_at) for a in rec.acceptances}
    per: dict[str, tuple[str, str, str]] = {}
    for batch, reviewer, at in who:
        assert batch not in per, batch
        per[batch] = (rules[batch], reviewer, at)
    res = {a.resolution_id: a for a in rec.reference_resolution_acceptances}
    return per, res


def _proposals() -> list[tuple[str, Any]]:
    out = []
    for batch, identity, sha in REPLACEMENT.BATCHES:
        path = HERE / f"issue-5d-{batch}-{REPLACEMENT.TAG}-PROPOSAL.json"
        if batch == "equipment":
            path, identity, sha = CANDIDATE, CANDIDATE_IDENTITY, CANDIDATE_SHA256
        assert _sha(path.read_bytes()) == sha, path.name
        out.append((batch, load_proposal(path, expected_identity=identity)))
    for batch, identity, sha, path in LATER:
        assert _sha(path.read_bytes()) == sha, path.name
        out.append((batch, load_proposal(path, expected_identity=identity)))
    return out


def replayed(rec: AcceptedInputs) -> AcceptedInputs:
    """The recorded chain with the candidate Equipment batch, over no prior."""
    per, res = _evidence(rec)
    steps = _steps(rec)
    inputs: AcceptedInputs | None = None
    for batch, proposal in _proposals():
        assert proposal.binding == rec.oracle.binding, batch
        rule, reviewer, at = per[batch]
        if batch == "equipment":
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
        if batch in steps:
            step = steps[batch]
            (ev,) = {
                (
                    res[r.resolution_id].authorized_by,
                    res[r.resolution_id].authorization_reference,
                    res[r.resolution_id].reviewer,
                    res[r.resolution_id].resolved_at,
                )
                for r in step
            }
            inputs = resolve_references(
                inputs,
                resolutions=step,
                authorized_by=ev[0],
                authorization_reference=ev[1],
                reviewer=ev[2],
                resolved_at=ev[3],
            )
    assert inputs is not None
    return inputs


def cited(base: AcceptedInputs) -> AcceptedInputs:
    """The 161 unrecorded cited-target drafts over the replayed chain."""
    gen = _load(
        "equipment_cited_targets_generator",
        HERE / "issue-5d-equipment-cited-targets-generator.py",
    )
    drafts = gen.draft_cited_resolutions(base.oracle.binding)
    raw = CITED_DRAFTS.read_bytes()
    assert _sha(raw) == CITED_DRAFTS_SHA256, CITED_DRAFTS.name
    assert json.loads(raw) == list(reference_resolution_payload(drafts))
    assert len(drafts) == 161 and all(
        d.resolution_id.endswith(CITED_SUFFIX) for d in drafts
    )
    return resolve_references(
        base,
        resolutions=drafts,
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    o = inputs.oracle
    return (
        len(inputs.batches),
        len(o.representation.records),
        len(o.spans),
        len(o.review_units),
        len(o.reference_resolutions),
    )


def _findings(inputs: AcceptedInputs) -> tuple[int, int]:
    from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus
    from afterworlds.ingestion.mechanical.oracle import candidate_from_accepted_inputs
    from afterworlds.ingestion.mechanical.projection import validate_candidate
    from afterworlds.persistence.database import create_engine, create_session_factory

    candidate = candidate_from_accepted_inputs(inputs)
    binding = inputs.oracle.binding
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        with create_session_factory(engine)() as session:
            corpus = load_bound_corpus(
                session, binding.package_uuid, binding.release_version
            )
            findings = validate_candidate(candidate, corpus)
        engine.dispose()
    leaf = [f for f in findings if f.startswith("leaf ")]
    refs = [f for f in findings if f.startswith("reference ")]
    other = [f for f in findings if f not in leaf and f not in refs]
    assert not other, other[:5]
    return len(refs), len(leaf)


# ---------------------------------------------------------------------------
# The delta: every recorded claim kept outside Equipment; Equipment in full.
# ---------------------------------------------------------------------------
EVIDENCE = ("reviewer", "accepted_at", "resolved_at", "rule")
#: Payload collections compared as multisets.
COLLECTIONS = (
    ("spans",),
    ("review_units",),
    ("obligations",),
    ("reference_resolutions",),
    ("representation", "records"),
    ("representation", "components"),
    ("representation", "references"),
    ("representation", "relationships"),
    ("representation", "prose_bindings"),
    ("representation", "provenance"),
    ("acceptance", "batches"),
    ("acceptance", "records"),
    ("acceptance", "review_unit_records"),
    ("acceptance", "reference_resolution_records"),
    ("acceptance", "schema_anchors"),
    ("acceptance", "lifts"),
)


def _at(payload: dict[str, Any], path: tuple[str, ...]) -> list[Any]:
    value: Any = payload
    for k in path:
        value = value[k]
    assert isinstance(value, list), path
    return value


def _key(item: object) -> str:
    return json.dumps(item, sort_keys=True)


def _texts(binding: Any) -> dict[str, tuple[int, str]]:
    """leaf_id -> (occurrence_index, content), from the release store."""
    con = sqlite3.connect(f"file:{SCRATCH_DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "select leaf_id, occurrence_index, content from rp_ledger_leaves "
            "where package_uuid = ?",
            (binding.package_uuid,),
        ).fetchall()
    finally:
        con.close()
    return {leaf: (row, text) for leaf, row, text in rows}


class Delta:
    def __init__(self, old: AcceptedInputs, new: AcceptedInputs) -> None:
        self.old = accepted_inputs_payload(old)
        self.new = accepted_inputs_payload(new)
        self.leaves = _texts(new.oracle.binding)
        spans = {s["span_id"]: s for s in (*self.old["spans"], *self.new["spans"])}
        self.spans = spans
        self.eq_old = {a.span_id for a in old.acceptances if a.batch_id == "equipment"}
        self.eq_new = {a.span_id for a in new.acceptances if a.batch_id == "equipment"}

    def text(self, span_id: str) -> str:
        s = self.spans[span_id]
        return self.leaves[s["leaf_id"]][1][s["char_start"] : s["char_end"]]

    def position(self, span_id: str) -> tuple[int, int]:
        s = self.spans[span_id]
        return (self.leaves[s["leaf_id"]][0], s["char_start"])

    def equipment(self, item: object) -> bool:
        """Whether ``item`` is Equipment's own, by its owning field: a record,
        component, binding, provenance or obligation of an ``equipment.``
        record, an Equipment span or review unit, the Equipment batch, or one
        of the cited drafts. A mention of an Equipment key elsewhere is not."""
        assert isinstance(item, dict), item
        owner = (
            item.get("record_key")
            or (item.get("semantic_key") if "parent_key" in item else None)
            or (item.get("from_record_key") if "resolution_id" not in item else None)
            or item.get("source_record_key")
            or (item.get("target_key") or [None])[0]
        )
        eq = self.eq_old | self.eq_new
        rules = item.get("expected_rules") or ()
        return (
            (isinstance(owner, str) and owner.startswith("equipment."))
            or item.get("batch_id") == "equipment"
            or item.get("span_id") in eq
            or str(item.get("resolution_id", "")).endswith(CITED_SUFFIX)
            or bool(rules)
            and all(r["record_key"].startswith("equipment.") for r in rules)
        )

    def blank(self, path: tuple[str, ...], item: Any) -> Any:
        if path[0] == "acceptance" and isinstance(item, dict):
            return {k: ("<evidence>" if k in EVIDENCE else v) for k, v in item.items()}
        return item

    def collections(self) -> dict[tuple[str, ...], tuple[list[Any], list[Any]]]:
        out = {}
        for path in COLLECTIONS:
            a = Counter(_key(self.blank(path, x)) for x in _at(self.old, path))
            b = Counter(_key(self.blank(path, x)) for x in _at(self.new, path))
            out[path] = (
                [json.loads(k) for k in (a - b).elements()],
                [json.loads(k) for k in (b - a).elements()],
            )
        return out

    def kept_outside_equipment(self) -> list[str]:
        """Every non-Equipment claim that is lost or added (must be none)."""
        return [
            f"{'.'.join(p)} {side}: {_key(x)[:300]}"
            for p, (lost, added) in self.collections().items()
            for side, items in (("lost", lost), ("added", added))
            for x in items
            if not self.equipment(x)
        ]

    def coverage(self) -> tuple[str, str]:
        """Equipment's accepted text, in printed order, before and after."""

        def joined(ids: set[str]) -> str:
            return "".join(self.text(i) for i in sorted(ids, key=self.position))

        return joined(self.eq_old), joined(self.eq_new)

    def report(self) -> list[str]:
        """The Equipment semantic delta, every item, in printed order."""
        lines: list[str] = []
        for path, (lost, added) in self.collections().items():
            if not lost and not added:
                continue
            lines.append(f"## {'.'.join(path)}: -{len(lost)} +{len(added)}")
            for sign, items in (("-", lost), ("+", added)):
                for x in sorted(items, key=self._order):
                    lines.append(f"{sign} {_key(x)}")
                    for sid in self._span_ids(x):
                        lines.append(f"    {sid[:8]} {self.text(sid)!r}")
        return lines

    def _span_ids(self, item: Any) -> list[str]:
        if not isinstance(item, dict):
            return []
        ids = [item[k] for k in ("span_id",) if isinstance(item.get(k), str)]
        for k in ("provenance_span_ids", "source_span_ids"):
            ids += [i for i in item.get(k) or () if isinstance(i, str)]
        return [i for i in ids if i in self.spans]

    def _order(self, item: Any) -> tuple[Any, ...]:
        ids = self._span_ids(item)
        first = min((self.position(i) for i in ids), default=(1 << 30, 0))
        return (first, _key(item))


def main(argv: list[str]) -> None:
    if argv not in ([], ["--delta"]) and not (len(argv) == 2 and argv[0] == "--delta"):
        raise SystemExit("usage: [--delta PATH]")
    rec = recorded()
    assert (_counts(rec), None) == (EXPECTED_RECORDED[0], None), _counts(rec)
    base = replayed(rec)
    final = cited(base)
    print("SIMULATED (in memory; nothing accepted or recorded)")
    for state, inputs in (("replayed", base), ("cited", final)):
        o = inputs.oracle
        violations = reference_resolution_violations(
            o.representation, o.reference_resolutions, o.binding
        )
        print(state, "counts", _counts(inputs), "violations", len(violations))
        assert not violations, violations[:5]
        counts, findings = EXPECTED[state]
        assert _counts(inputs) == counts, _counts(inputs)
        if findings is not None:
            got = _findings(inputs)
            print(state, "reference, uncovered-leaf findings", got)
            assert got == findings, got
    print("simulated bytes sha256", _sha(serialize_accepted_inputs(final)))
    delta = Delta(rec, final)
    outside = delta.kept_outside_equipment()
    print("non-Equipment claims lost or added", len(outside))
    for line in outside[:20]:
        print("  ", line)
    before, after = delta.coverage()
    print(
        "Equipment accepted text, printed order: identical",
        before == after,
        len(before),
        _sha(before.encode("utf-8")),
    )
    assert before == after, "Equipment's accepted text changed"
    summary = {
        ".".join(p): (len(lost), len(added))
        for p, (lost, added) in delta.collections().items()
        if lost or added
    }
    print("delta by collection (-, +)", json.dumps(summary, indent=1))
    lines = delta.report()
    if len(argv) == 2:
        Path(argv[1]).write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
        print("delta written", argv[1], len(lines), "lines")
    assert not outside
    assert before == after


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
