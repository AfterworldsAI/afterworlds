"""The Monsters-corrected replacement chain and the Monsters proposal over it.

CRD Issue 5d, bounded Monsters source correction (#132, #137). REVIEW MATERIAL:
nothing here is accepted, recorded, published or activated, and no Owner
approval exists for it. There is deliberately no recording step: one is added
only after the Owner's exact semantic acceptance of this packet, not before.

The private release ``67c81736-15fd-5e82-8523-e84922f0a7c6`` /
``5.2.1-corpus.3fe24ff6-4e3`` is built from the controlled source with three
reviewed corrections in *Monsters A-Z* (the Succubus's Initiative moved into its
AC line, the Owner's *Veteran Warrior* heading, the official-source-backed
Young White Dragon SAVE ``−2``) and the *Monsters* part read before *Monsters
A-Z* (``issue-5d-monsters-source-correction-candidate.diff``). The cross-release
check refuses to extend the accepted ``srd-5-2-1-corpus-574662e9-0ef.json``
(SHA-256 :data:`ACCEPTED_SHA256`, left byte-unchanged) onto it, so this script
composes a *fresh* chain over no prior from the twenty regenerated
``issue-5d-<batch>-REGEN-3fe24ff6-PROPOSAL.json`` files, through the same native
seams, in the same order and with the same serial steps as the scripts that
recorded the accepted chain:

* ``accept_proposal`` once per batch, each over the previous result, whole scope
  and every review unit;
* ``resolve_references`` after ``checks-actions-rests``,
  ``character-creation-foundations`` and ``character-origins-feats`` (six
  reference drafts), ``equipment`` (43), ``spellcasting`` (1),
  ``class-option-catalogues`` (1), ``spell-descriptions`` (1,046),
  ``gameplay-toolbox`` (1) and ``magic-items`` (1): 1,099 resolutions, each
  step's payload held to its ``-REGEN-3fe24ff6-DRAFTS.json``. The last three
  are drafted over the chain before their batch, as they were recorded.

``--simulate`` runs the chain in memory under an explicit simulated reviewer and
writes nothing. It pins the simulated bytes, compares them against the accepted
artifact (:func:`against_accepted`), validates them against the corrected build
in the private scratch store, then composes the unaccepted Monsters proposal and
its drafts over it, in memory, and reports the totals.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.corpus.hashing import content_id  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.canonical import canonical_order  # noqa: E402
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    accepted_inputs_payload,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    load_proposal,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    reference_resolution_payload,
    reference_resolution_violations,
)

RELEASE = ("67c81736-15fd-5e82-8523-e84922f0a7c6", "5.2.1-corpus.3fe24ff6-4e3")
TAG = "REGEN-3fe24ff6"
SCRATCH_DB = REPO / ".claude" / "_rc" / "msc" / "rel" / "afterworlds.db"
ACCEPTED_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-574662e9-0ef.json"
ACCEPTED_SHA256 = "fc62c47cde83cd341f714b7e51660354a22b69dc59f214c0a6e5ec379dee5a62"

#: (batch, proposal_identity, file SHA-256), in the accepted chain's order.
BATCHES = (
    (
        "conditions-pilot",
        "b6447a9348cd4be1f7072b80dbdbc5b9e8b876b4db4553101e095455f436e4cd",
        "f142f4886af7d006b3a993839aedd04f23d5b528812e9cd40e32d8734959ac71",
    ),
    (
        "actions-pilot",
        "86d51bf772cb977aded2b43beeee6c34f3bd91816b9af0d05bee8c5a904401d2",
        "52e27e59cbd577fa504fa7cc7d5cd880bbc9a4662a581d03e55d7d57bd183186",
    ),
    (
        "reference-closure",
        "50f1dfb23c558ee13207bd9b34b2d19ca4ee6a71641c23373a593d739cf228b1",
        "916ebb077ff54b30a01b6edd73225a2e434c4840546b37fd4d2c7c8ea89e60fe",
    ),
    (
        "movement-closure",
        "5af32afc358558eae7e420b44eb72fac4ccfd8fea52b02cdd0dfe1b1d9352c6c",
        "c8d55fdd5997fc54ce3627d975c48e570c1ad461be00ce461e0dc215631fe05d",
    ),
    (
        "combat-turn-1",
        "07368f439df7b33910d8311b3074dd05dbe0afacf673318830fc3f9e8fa1f5ed",
        "a19c134d15da05450836532cb49522b3f9bde7f20788621c227e39acf22a1ba7",
    ),
    (
        "damage-and-hit-points",
        "c2303ddca53dd01a37bc989bc3aaf140b9fa9a519fbb145cb0ea0bbab1261473",
        "9d27e3fe5b47e055228b68d82017d6bcb1524cf56843e88899ee88eb4f2b74f6",
    ),
    (
        "combat-damage-breaking",
        "ce7a80ff95d8ae361d2a76612b85d7f5d546c57755588d3084a6a41a4f8a7de2",
        "92a936cafc49cfef0c62ddc2afe8891082c24c925d294d338dc22aa23e1c2508",
    ),
    (
        "checks-actions-rests",
        "bc984667ac0d7a0b3eadf0ce53d16f5be94a1fcf005abc03ca1325f58c3d6be0",
        "9ae8519578fa9a727716ff5bd8fa2d500c191b11e8fb500180e6285fa83cdf82",
    ),
    (
        "core-play-completion",
        "147a50f468dad8741b2892c018df549ff2bfe5b39861d62c4e4dfce7cbe5d9e8",
        "3faee5fc525aab542ec8993ac95f1b035085597ad74d7b7b2f17df1b96ff603e",
    ),
    (
        "core-play-dependencies",
        "71db9bfc255617677ea27efc29931fa7a35f7905a53eff8e1d6a7489c0ef7c84",
        "87c1f5418ee22d092cdf73931107048d495e50132f303ba7857161da9454aa20",
    ),
    (
        "character-creation-foundations",
        "00a4abd9d427ed678c66218c4a87cc97ee743e8859c7fae3487c3b3aa768d25c",
        "bf7f3c955413de03151aa67b1f0143731d705eec0cc22287fd6a422f40d11467",
    ),
    (
        "character-origins-feats",
        "8ce962407320ee246ec6d07ad51cddbff5b57d87fe966b3e73fc115f06bcd051",
        "bb85ca76fa6cd1c781d86389c72653ddd76e2c7bb1926e1625cdb698d1fd61d6",
    ),
    (
        "equipment",
        "f97f2449518e8eb30d8fd5c05237fcfee17a89d55da1feee8d9d8880bcd9154c",
        "12a124ce2b09f32a2d3d9d41256b4d0501692a7574a781e97c6ca9e61bd426f3",
    ),
    (
        "spellcasting",
        "7d0c8966f9fcbce41a0e80ae77626e84a216844db221649c51de0f7499888648",
        "cb0b1f97ed7a64f8ac59722bd3e51efb200d6beb6a33f6c77e4a79c82e456124",
    ),
    (
        "rules-glossary-completion",
        "e777201803ce1dbadc753ec0da38f385edf23628ba1a45a3bac20c5999cca367",
        "f16160d9523e2b43a3c2eb310104849e6a758c88d566683c90dbb579155aa473",
    ),
    (
        "classes",
        "c98ed194f954eeec7c9005788192edba893512b1064ff6b38a4280812b9a2b03",
        "5df314c3c8bd282c9ca72dc2048d9b30ba7131b7d1d464d21530a9e169788839",
    ),
    (
        "class-option-catalogues",
        "ba5e78d5fe9e6c7fd69247fdefb734158d635e707d3898f31ee4147cc06e5d4f",
        "64e4b9fc3094a620fdacc9795757a3abf156793c874a0fd109cfd0ca5017f695",
    ),
    (
        "spell-descriptions",
        "737040bbd065f97f37f2438f23fe8827ebc31b2fa446a545f99be96ce9e6fafc",
        "21d61891618928683ddb6f06f57a9d9dac0db2805dc9b5f66badbf61f611fe33",
    ),
    (
        "gameplay-toolbox",
        "22c3c6f80155d7e804fdae5edac9b9962363d85553ca737d5e402ff1d33fad8f",
        "644d7ebf8f06dd19fc81a02fb8af89a9e95aea55240a11d6daf936ffab936542",
    ),
    (
        "magic-items",
        "dd6d191b5b3fe7d2705f71ba8ccf7b24c430c04a2a28dbe22cb6c9ac6003901b",
        "7107c4897ae10609298927a100558ec9fe3c77a52194df8c89d2660176896be0",
    ),
)
#: The resolution step after each batch that has one: (generator, draft functions).
RESOLUTIONS = {
    "checks-actions-rests": ("checks-actions-rests", ("draft_attack_roll_resolution",)),
    "character-creation-foundations": (
        "character-creation-foundations",
        ("draft_armor_class_resolution", "draft_proficiency_bonus_resolution"),
    ),
    "character-origins-feats": (
        "character-origins-feats",
        (
            "draft_choose_background_resolution",
            "draft_choose_species_resolution",
            "draft_background_feat_resolution",
        ),
    ),
    "equipment": ("equipment", ("draft_resolutions",)),
    "spellcasting": ("spellcasting", ("draft_resolutions",)),
    "class-option-catalogues": ("classes", ("draft_resolutions",)),
    "spell-descriptions": ("spell-descriptions", ("draft_resolutions",)),
    "gameplay-toolbox": ("gameplay-toolbox", ("draft_resolutions",)),
    "magic-items": ("magic-items", ("draft_resolutions",)),
}
#: Batches whose drafts are drafted over the chain before them (``prior=``).
OVER_PRIOR = ("spell-descriptions", "gameplay-toolbox", "magic-items")
#: Drafts file -> (SHA-256, the batches whose steps it holds).
DRAFTS = {
    "reference": (
        "7892d71ff3d873bff1c7451b03ef01d5d424b754e81b04407501f6a51d367668",
        (
            "checks-actions-rests",
            "character-creation-foundations",
            "character-origins-feats",
        ),
    ),
    "equipment": (
        "a672c7606aaf77af47ebbf7ee2c978f57c8a0c89f7f8d2d9e2406e33b10647ba",
        ("equipment",),
    ),
    "spellcasting": (
        "fd45ef74d3f1b34eb715bcac1711123d6524ba322349638c69eb51392ec5587c",
        ("spellcasting",),
    ),
    "classes": (
        "819eacf602bd670a62e9c25ad7028b465db0f6a21b2acac2d5d8847e94c5f00e",
        ("class-option-catalogues",),
    ),
    "spell-descriptions": (
        "d85523852b036c80c73ff8d170622eaef3cf7f18bb2c6a95a402c45ae0bc29dd",
        ("spell-descriptions",),
    ),
    "gameplay-toolbox": (
        "c499cd7f36a26e02ed9b44c52326b0dac07c3518bf528e51bc7ccd046515f3f8",
        ("gameplay-toolbox",),
    ),
    "magic-items": (
        "c5bcd92e5235b8a3e86970e1a1a10e48daa84d5c119e1e5a8f8f92d1a60d9621",
        ("magic-items",),
    ),
}

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_RULE = "SIMULATION ONLY: in-memory composition check; records no acceptance"
SIMULATED_AT = "2026-09-26T00:00:00Z"
#: The simulated chain's bytes: a composition check, not an accepted artifact.
SIMULATED_SHA256 = "caad48afb76183296a4e8936efda93fa215f5837d21bb9894d39d65dbf88c3ae"

MONSTERS_BATCH_ID = "monsters"
MONSTERS_FILE = HERE / "issue-5d-monsters-PROPOSAL.json"
MONSTERS_FILE_SHA256 = (
    "cdf06f4307bd09786f73cc16e4cf75c6609595c9a041ef4d1f47c9dbcf9a4336"
)
MONSTERS_IDENTITY = "0fd9e1698985748b81499def620a37b89c52a6b8cdc5a4ead69a1b57911239df"
MONSTERS_DRAFTS_FILE = HERE / "issue-5d-monsters-resolutions-DRAFTS.json"
MONSTERS_DRAFTS_SHA256 = (
    "1733d78c91f56092b163732e0fc354cf5d21e6fd907f32fe33f7c440f74dc792"
)

#: What each state must hold: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED = {
    "chain": ((20, 1250, 6450, 950, 1099), (315, 4003)),
    "monsters": ((21, 1664, 9589, 1364, 1182), (317, 864)),
}


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


def generator(batch: str) -> ModuleType:
    return _load(
        f"gen_{batch.replace('-', '_')}", HERE / f"issue-5d-{batch}-generator.py"
    )


def proposal_path(batch: str) -> Path:
    return HERE / f"issue-5d-{batch}-{TAG}-PROPOSAL.json"


def drafts_path(name: str) -> Path:
    return HERE / f"issue-5d-{name}-resolutions-{TAG}-DRAFTS.json"


def _drafts(
    out: ReferenceResolution | tuple[ReferenceResolution, ...],
) -> tuple[ReferenceResolution, ...]:
    return (out,) if isinstance(out, ReferenceResolution) else tuple(out)


def chain(
    reviewer: str, rule: str, reference: str, at: str, through: str | None = None
) -> AcceptedInputs:
    """The fresh twenty-batch chain and its 1,099 resolutions, over no prior.

    ``through`` stops after that batch and its resolutions: the state each later
    batch is composed over.
    """
    inputs: AcceptedInputs | None = None
    steps: dict[str, tuple[ReferenceResolution, ...]] = {}
    for batch, identity, sha in BATCHES:
        path = proposal_path(batch)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, batch
        proposal = load_proposal(path, expected_identity=identity)
        assert (
            proposal.binding.package_uuid,
            proposal.binding.release_version,
        ) == RELEASE
        before = inputs
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
            prior=before,
        )
        if batch in RESOLUTIONS:
            name, functions = RESOLUTIONS[batch]
            gen = generator(name)
            binding = inputs.oracle.binding
            steps[batch] = tuple(
                d
                for f in functions
                for d in _drafts(
                    getattr(gen, f)(binding, prior=before)
                    if batch in OVER_PRIOR
                    else getattr(gen, f)(binding)
                )
            )
            inputs = resolve_references(
                inputs,
                resolutions=steps[batch],
                authorized_by=reviewer,
                authorization_reference=reference,
                reviewer=reviewer,
                resolved_at=at,
            )
        if batch == through:
            return inputs
    assert through is None, f"unknown batch {through!r}"
    assert inputs is not None
    for name, (sha, batches) in DRAFTS.items():
        data = drafts_path(name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha, name
        assert json.loads(data) == list(
            reference_resolution_payload(tuple(d for b in batches for d in steps[b]))
        ), f"{name} drafts are not the regenerated drafts"
    assert len(inputs.oracle.reference_resolutions) == 1099
    return inputs


def simulated() -> AcceptedInputs:
    """The chain under the simulated reviewer, held to its pinned bytes."""
    inputs = chain(SIMULATED_REVIEWER, SIMULATED_RULE, SIMULATED_RULE, SIMULATED_AT)
    data = serialize_accepted_inputs(inputs)
    assert hashlib.sha256(data).hexdigest() == SIMULATED_SHA256, "drifted"
    return inputs


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def monsters(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """The unaccepted Monsters proposal, accepted whole over ``base`` and then
    resolved with its drafts (drafted over ``base``), in memory only."""
    assert _sha(MONSTERS_FILE.read_bytes()) == MONSTERS_FILE_SHA256, MONSTERS_FILE.name
    proposal = load_proposal(MONSTERS_FILE, expected_identity=MONSTERS_IDENTITY)
    assert proposal.binding == base.oracle.binding
    accepted = accept_proposal(
        proposal,
        batch_id=MONSTERS_BATCH_ID,
        rule=SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=reviewer,
        accepted_at=at,
        prior=base,
    )
    drafts = generator("monsters").draft_resolutions(base.oracle.binding, prior=base)
    raw = MONSTERS_DRAFTS_FILE.read_bytes()
    assert _sha(raw) == MONSTERS_DRAFTS_SHA256, MONSTERS_DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the committed drafts"
    return resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by=reviewer,
        authorization_reference=SIMULATED_RULE,
        reviewer=reviewer,
        resolved_at=at,
    )


def _preserved(old: object, new: object, where: str = "") -> list[str]:
    """Where ``new`` drops or changes anything ``old`` holds (lists as multisets)."""
    if isinstance(old, dict) and isinstance(new, dict):
        return [
            p
            for k in old
            for p in (
                _preserved(old[k], new[k], f"{where}.{k}")
                if k in new
                else [f"{where}.{k} missing"]
            )
        ]
    if isinstance(old, list) and isinstance(new, list):
        key = lambda x: json.dumps(x, sort_keys=True)  # noqa: E731
        lost = Counter(map(key, old)) - Counter(map(key, new))
        return [f"{where} lost {sum(lost.values())} of {len(old)}"] if lost else []
    return [] if old == new else [f"{where} changed"]


#: Acceptance evidence: who, when and under which rule. Blanked in the
#: comparison and reported by value instead.
EVIDENCE = frozenset(
    {
        "reviewer",
        "accepted_at",
        "resolved_at",
        "rule",
        "authorized_by",
        "authorization_reference",
    }
)
#: The collections ``canonical_order`` sorts by whole content (ADR-005d
#: Decision 6): re-minted ids and acceptance times reorder them.
CANONICAL = (
    ("acceptance", "records"),
    ("acceptance", "review_unit_records"),
    ("representation", "prose_bindings"),
    ("representation", "provenance"),
)


def against_accepted(inputs: AcceptedInputs) -> list[str]:
    """Every difference from the accepted artifact, position by position.

    Only release-derived identities are mapped, accepted -> replacement: the
    release binding values, chunk ids (``content_id`` over package and leaf),
    span ids (paired by leaf and extent) and proposal identities. Acceptance
    evidence is blanked. The :data:`CANONICAL` collections must be in
    ``canonical_order`` in both artifacts and are then compared as multisets;
    every other list is compared in order. Returns the differences, untruncated.
    """
    raw = ACCEPTED_PATH.read_bytes()
    assert _sha(raw) == ACCEPTED_SHA256, "the accepted artifact changed"
    old = json.loads(raw)
    new = json.loads(serialize_accepted_inputs(inputs))
    ob, nb = old["release_binding"], new["release_binding"]
    mapping = {ob[k]: nb[k] for k in ob if ob[k] != nb[k]}

    def extent(s: dict[str, Any]) -> tuple[str, int, int]:
        return (s["leaf_id"], s["char_start"], s["char_end"])

    spans = {extent(s): s["span_id"] for s in new["spans"]}
    assert len(spans) == len(new["spans"])
    for s in old["spans"]:
        mapping[s["span_id"]] = spans[extent(s)]
        mapping[content_id("chunk", ob["package_uuid"], s["leaf_id"])] = content_id(
            "chunk", nb["package_uuid"], s["leaf_id"]
        )
    batches = {b["batch_id"]: b for b in new["acceptance"]["batches"]}
    for b in old["acceptance"]["batches"]:
        mapping[b["proposal_identity"]] = batches[b["batch_id"]]["proposal_identity"]
    assert len(set(mapping.values())) == len(mapping), "the id map is not one-to-one"

    def norm(x: object) -> object:
        if isinstance(x, dict):
            return {k: "<evidence>" if k in EVIDENCE else norm(v) for k, v in x.items()}
        if isinstance(x, list):
            return [norm(v) for v in x]
        return mapping.get(x, x) if isinstance(x, str) else x

    out: list[str] = []
    for side in (old, new):
        for path in CANONICAL:
            items = side[path[0]][path[1]]
            if items != canonical_order(items):
                out.append(f"{'.'.join(path)} not in canonical order")

    def diff(a: object, b: object, where: str) -> None:
        if type(a) is not type(b):
            out.append(f"{where}: {json.dumps(a)} -> {json.dumps(b)}")
        elif isinstance(a, dict) and isinstance(b, dict):
            if list(a) != list(b):
                out.append(f"{where}: keys {list(a)} -> {list(b)}")
            for k in a:
                if k in b:
                    diff(a[k], b[k], f"{where}.{k}")
        elif isinstance(a, list) and isinstance(b, list):
            if tuple(where.strip(".").split(".")) in CANONICAL:
                a = sorted(a, key=lambda x: json.dumps(x, sort_keys=True))
                b = sorted(b, key=lambda x: json.dumps(x, sort_keys=True))
            if len(a) != len(b):
                out.append(f"{where}: length {len(a)} -> {len(b)}")
            for i, (x, y) in enumerate(zip(a, b, strict=False)):
                diff(x, y, f"{where}[{i}]")
        elif a != b:
            out.append(f"{where}: {json.dumps(a)} -> {json.dumps(b)}")

    diff(norm(old), norm(new), "")
    return out


def _counts(inputs: AcceptedInputs) -> tuple[int, int, int, int, int]:
    oracle = inputs.oracle
    return (
        len(inputs.batches),
        len(oracle.representation.records),
        len(oracle.spans),
        len(oracle.review_units),
        len(oracle.reference_resolutions),
    )


def _findings(inputs: AcceptedInputs) -> tuple[int, int]:
    """Reference and uncovered-leaf findings against a private DB copy."""
    from afterworlds.ingestion.mechanical.bound_corpus import load_bound_corpus
    from afterworlds.ingestion.mechanical.oracle import candidate_from_accepted_inputs
    from afterworlds.ingestion.mechanical.projection import validate_candidate
    from afterworlds.persistence.database import create_engine, create_session_factory

    candidate = candidate_from_accepted_inputs(inputs)
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        with create_session_factory(engine)() as session:
            corpus = load_bound_corpus(session, *RELEASE)
            findings = validate_candidate(candidate, corpus)
        engine.dispose()
    leaf = [f for f in findings if f.startswith("leaf ")]
    refs = [f for f in findings if f.startswith("reference ")]
    other = [f for f in findings if f not in leaf and f not in refs]
    print("  reference findings", len(refs), "leaf/uncovered", len(leaf))
    print("  other findings", len(other), other[:5])
    assert not other, other
    return len(refs), len(leaf)


def _check(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    """Counts, violations, chain preservation and findings for ``state``."""
    oracle = inputs.oracle
    violations = reference_resolution_violations(
        oracle.representation, oracle.reference_resolutions, oracle.binding
    )
    lost = _preserved(accepted_inputs_payload(base), accepted_inputs_payload(inputs))
    print(state)
    print("  counts (batches, records, spans, units, resolutions)", _counts(inputs))
    print("  resolution violations", len(violations))
    print("  twenty-batch chain preserved", not lost, _counts(base))
    assert not violations, violations
    assert not lost, lost
    assert _counts(base) == EXPECTED["chain"][0], _counts(base)
    counts, findings = EXPECTED[state]
    assert _counts(inputs) == counts, _counts(inputs)
    got = _findings(inputs)
    assert got == findings, got


def simulate() -> None:
    inputs = simulated()
    print("SIMULATED (in memory; nothing written; not an acceptance)")
    print("  reviewer", repr(SIMULATED_REVIEWER))
    print("  bytes sha256", SIMULATED_SHA256)
    print("  batches", [b.batch_id for b in inputs.batches])
    delta = against_accepted(inputs)
    print("  differences from the accepted artifact", len(delta))
    for line in delta:
        print("   ", line)
    assert not delta
    _check("chain", inputs, inputs)
    _check("monsters", inputs, monsters(inputs, SIMULATED_REVIEWER, SIMULATED_AT))


def main(argv: list[str]) -> None:
    if argv != ["--simulate"]:
        raise SystemExit("usage: --simulate (no recording step exists)")
    simulate()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
