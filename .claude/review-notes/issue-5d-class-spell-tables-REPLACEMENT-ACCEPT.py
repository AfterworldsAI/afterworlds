"""Owner acceptance of the corrected-release replacement and Spell Descriptions.

CRD Issue 5d, class spell-table Owner correction (#132, #137). The Owner answered
:data:`OWNER_REVIEW` (SHA-256 :data:`OWNER_REVIEW_SHA256`), whose exact packet is
:data:`MANIFEST` (SHA-256 :data:`MANIFEST_SHA256`), with :data:`APPROVAL`.

That decision authorizes exactly three native actions, in this order, each over
the previous result, and each reading the UTC clock when it runs:

1. ``record``: the fresh seventeen-batch chain and its 51 resolutions below,
   over no prior (603 records, 2776 spans, 305 review units).
2. ``accept-spells``: :func:`accept_proposal` of the whole Spell Descriptions
   proposal (:data:`SD_FILE_SHA256`, :data:`SD_IDENTITY`) over step 1.
3. ``resolve-spells``: :func:`resolve_references` with its 1,046 drafts, drafted
   over step 1's chain and held to :data:`SD_DRAFTS_SHA256`.

The other 143 reference findings stay; nothing here publishes or activates.
``--verify`` reads the step times back from the artifact and rebuilds it, so
the recorded bytes reproduce. Any artifact state other than absent or one of
the three step results fails closed. The executed times and the bytes after
each step are pinned in :data:`RECORDED_AT` and :data:`RECORDED_SHA256`;
:func:`recorded` rebuilds the seventeen-batch chain from them.

The release ``ebdd9333-eeed-5df1-b3e1-8b97c2f65f80`` / ``5.2.1-corpus.574662e9-0ef``
is built from the controlled source with the Owner's seven-edit correction of the
Level 2 Bard, Druid, Sorcerer and Wizard spell tables
(``issue-5d-class-spell-tables-owner-correction.diff``). The cross-release check
refuses to extend the accepted ``srd-5-2-1-corpus-626c83f8-209.json`` onto it,
so this script composes a *fresh* chain over no prior from the seventeen
regenerated ``issue-5d-<batch>-REGEN-574662e9-PROPOSAL.json`` files, through the
same native seams, in the same order and with the same serial steps as the
scripts that recorded the accepted chain:

* ``accept_proposal`` once per batch, each over the previous result, whole scope
  and every review unit;
* ``resolve_references`` after ``checks-actions-rests``,
  ``character-creation-foundations`` and ``character-origins-feats`` (the six
  reference drafts), ``equipment`` (43), ``spellcasting`` (1) and
  ``class-option-catalogues`` (1): 51 resolutions, each step's payload held to
  its reviewed ``-REGEN-574662e9-DRAFTS.json``.

The Spell Descriptions batch is **not** in this chain: it is proposed over it,
separately, by ``issue-5d-spell-descriptions-generator.py``.

``--simulate`` runs the chain in memory under an explicit simulated reviewer and
writes nothing. It pins the simulated bytes, validates the candidate against the
corrected build in the private scratch store, then composes the Spell
Descriptions proposal and its drafts over it, in memory, and reports the totals.

``record``, ``accept-spells`` and ``resolve-spells`` each refuse unless the
artifact is in the state before them, and first run the remaining steps in
memory under the simulated reviewer so a drafts mismatch surfaces before bytes
are written.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    load_proposal,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    ReferenceResolution,
    reference_resolution_payload,
    reference_resolution_violations,
)

RELEASE = ("ebdd9333-eeed-5df1-b3e1-8b97c2f65f80", "5.2.1-corpus.574662e9-0ef")
TAG = "REGEN-574662e9"
SCRATCH_DB = REPO / ".claude" / "_rc" / "corr" / "rel" / "afterworlds.db"
ACCEPTED_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-574662e9-0ef.json"

#: (batch, proposal_identity, file SHA-256), in the accepted chain's order.
BATCHES = (
    (
        "conditions-pilot",
        "7d3a876e993e143a131e28168bc7ccc820e339b5d218315089042e33f3e7bbb0",
        "71c0884c33aee77ad8638ab72ff47e1879b2d702d274706e31d86c70ce0b4b68",
    ),
    (
        "actions-pilot",
        "62594095afb7eefbaaab0b36bc600eafd40001b78eba3145ee75f4f96ce88da0",
        "c6a9102d406eaf3c3ad68000a1dfd029ac26834fa3219532e79a200953292e03",
    ),
    (
        "reference-closure",
        "018196bb3992a884c3e356be462d67b41911a73997acc6c89314e6673a474192",
        "160d2184a7faada136fc3ade4eff1d8743a29139a00e69046c05db56ab988f27",
    ),
    (
        "movement-closure",
        "ac589d20e3ef69fdde3a7424fed19fbaba10f6e642a07042d8d6ced91783857f",
        "6c37e11b61e51b5c52fa19fe5b1dd7ba5addf6c627a3846e591e9bde22a696e9",
    ),
    (
        "combat-turn-1",
        "97031db290b4cfb74e83818607282865d1f41fdad92c6a356759d09b60a6e8b8",
        "81aff159e5c5ad526c42b49376aa21d75a58012c7b2dab001ee0961e8eeb789b",
    ),
    (
        "damage-and-hit-points",
        "5d5f1b66d6d4f8f4beff17538384f3cf023384d43abaefec4fb330bafaddcbed",
        "5ea9aeba2065b01b08044256c2132e2dcf12cdc657a16dfda1d6958a5d9edbf8",
    ),
    (
        "combat-damage-breaking",
        "52d318f6b6e96e96792ca82bcc09b7a1af34c8101aa258dda1ec73a1c7b082a2",
        "2d4c4dffbe79aabbdf69617e9e3c8a991385342d266f5e1282fe257f4ca93fef",
    ),
    (
        "checks-actions-rests",
        "c4b60669266035c0bea4d271594c8cb420014d420a28082c9184ef96b0bbeb57",
        "ff267664e450d0a7b57d526cc427a4c1cdc1423dd8d3ea6295cb8430dcb5dc1c",
    ),
    (
        "core-play-completion",
        "bb711fa7874b68ebbc906c8cce4fb02980e69a46104f99edcf8f07833abb9240",
        "7f62217b06525c5a5ca6b14278d752ff590af320eb19d4f4cf7927f9579ec4fc",
    ),
    (
        "core-play-dependencies",
        "2d882bf17ab8be76affdc917f66f038514f17974c3cde479fb0ed906b2bc7278",
        "781cb7ead0d281ef66882c2e57a8bc3f774a5561b42a472be4fe93715e6105b3",
    ),
    (
        "character-creation-foundations",
        "6344d4e4d071b024788a228eaf735751c0fea4ade2503545bbb9db84570cb127",
        "288bad428508c57fd343efffdb3d93ebd4b7bca5351dab31e3e7a9db0e37f2ea",
    ),
    (
        "character-origins-feats",
        "60b4422e464b8ffbddab27564aa1c1bea1c3f5cac20faf8fdc3e01bcbb1521e6",
        "9672b2ab6bfa3f669cb691cd7139b11b637027866bb69452c536a94a62994e53",
    ),
    (
        "equipment",
        "3fb78d8c427a566633d5a98656a29995551e808706d8a0a2165f36a343b8c671",
        "3b1c6c0154861c6d2a401b7ce05b839177f26f4720de03128f636b5c770789bb",
    ),
    (
        "spellcasting",
        "c98e02b0f7164f7293a4e6316cdf3a3903428cd030426dbd941d2a210fce167a",
        "64f9121cae8d5a02c5e3972d8e2c45866366a2250f151f6f3741f35c84b4e7bd",
    ),
    (
        "rules-glossary-completion",
        "99f85c48a92f841fd7fcf1b351f94236b8ed9f0457d1b2f888285856afe0ac65",
        "27d38af3349ecabd81026a5d6d1c8ec836dda7c7bf415b5a6a89d4320bcff01e",
    ),
    (
        "classes",
        "062f4246bdfa3f5def4c47a99fe7319de5580a0675c8b22763a06b3431c92608",
        "e8e74e3f1bd2f5fb4b1b682912967833fad803c79db77310fb895c8a1597971d",
    ),
    (
        "class-option-catalogues",
        "dd7e7e3d5fc47fe6b891f6c0b3ba5ce5492d90c7871d83243e707d7db9b229c1",
        "446282730d21a604ec1410999bdd4b180dd3a6f8a860025d91773b1ecf1df060",
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
}
#: Reviewed drafts file -> (SHA-256, the batches whose steps it holds).
DRAFTS = {
    "reference": (
        "251e5def6b313dc95791f0984a55728cbd42d92763f86d9b264f471acddfba2d",
        (
            "checks-actions-rests",
            "character-creation-foundations",
            "character-origins-feats",
        ),
    ),
    "equipment": (
        "c3bfc73257de1532701fd4a282765faa654fc5edfec62a5550a240b2f2aa3978",
        ("equipment",),
    ),
    "spellcasting": (
        "9d4d8221d099e47a187722925c7b6524414e4adf418023ac31ab726ce7835018",
        ("spellcasting",),
    ),
    "classes": (
        "81e6b1702dc14f77eda4600341f930bca2a73eaa6ef3e1dcc6dbb1af498af782",
        ("class-option-catalogues",),
    ),
}

SIMULATED_REVIEWER = "SIMULATION - not an Owner approval"
SIMULATED_RULE = "SIMULATION ONLY: in-memory composition check; records no acceptance"
SIMULATED_AT = "2026-09-26T00:00:00Z"
#: The simulated chain's bytes: a composition check, not an accepted artifact.
SIMULATED_SHA256 = "4aaa37b04c61fdc182a7fed60478ff02dc5b45a952f9bd1bfef5f392887d2e2d"

SD_BATCH_ID = "spell-descriptions"
SD_FILE = HERE / "issue-5d-spell-descriptions-PROPOSAL.json"
SD_FILE_SHA256 = "acf1965acebb8ee1e8c1801cddea4ce8d55bfd586659fecb40c30ce9bc13e4b2"
SD_IDENTITY = "6361cf7f6f5015cc43a2870df50647d76589fd4d0d68f93327804aa890049783"
SD_DRAFTS_FILE = HERE / "issue-5d-spell-descriptions-resolutions-DRAFTS.json"
SD_DRAFTS_SHA256 = "5c4373a30a34b74d17a02be2cf3eadebe659e284e1cb7d63962dd3e0aeb75c3a"

#: The Owner is the reviewer, the authorizer and the executor.
OWNER = "Ravenlok (Owner)"
OWNER_REVIEW = "spell-corrections-and-descriptions-owner-review.md"
OWNER_REVIEW_SHA256 = "fb0bf796ef255186771ad8869a073f6ac2ff15ccc72bb656a4d079f1079e2e6e"
MANIFEST = "spell-corrections-owner-manifest.json"
MANIFEST_SHA256 = "dd31842edb21cee90263e736a8c960177ed9b69dde0fcd1cf008331cd084d16b"
#: The Owner's decision, verbatim; the rule of every batch it accepts.
APPROVAL = (
    "I accept both exact items in this packet, approve their reference "
    "resolutions, and retain the 143 reference findings and partial-publication "
    "block."
)
AUTHORIZATION_REFERENCE = (
    f"Owner decision on {OWNER_REVIEW} (SHA-256 {OWNER_REVIEW_SHA256}), "
    f"exact packet {MANIFEST} (SHA-256 {MANIFEST_SHA256}): {APPROVAL!r}"
)

#: What each step must produce: batches, records, spans, review units,
#: resolutions; then reference and uncovered-leaf findings on the release.
EXPECTED = {
    "chain": ((17, 603, 2776, 305, 51), (1157, 7657)),
    "spells-accepted": ((18, 947, 4826, 645, 51), None),
    "resolved": ((18, 947, 4826, 645, 1097), (143, 5621)),
}

#: The executed step times (chain, spells accepted, spells resolved), as the
#: recording wrote them, and the artifact bytes after each step.
RECORDED_AT = ("2026-09-27T03:34:02Z", "2026-09-27T03:34:46Z", "2026-09-27T03:35:13Z")
#: The chain step's time: each of its seventeen acceptances and 51 resolutions.
ACCEPTED_AT = RECORDED_AT[0]
RECORDED_SHA256 = {
    "chain": "4f78fa80f6c28f5c5569581ad8fc9e0ce7a8e87c5df66aefdef8f75d75c2d35e",
    "spells-accepted": (
        "c13c33ba446d93f50405cd01b39e25502e5bdc963faa39278078d331f0ca6907"
    ),
    "resolved": "b1f8718fe5fccf3bd36e8331a29150a6119efca83877934cdf1245cd096d639f",
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


def chain(
    reviewer: str, rule: str, reference: str, at: str, through: str | None = None
) -> AcceptedInputs:
    """The fresh seventeen-batch chain and its 51 resolutions, over no prior.

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
        if batch in RESOLUTIONS:
            name, functions = RESOLUTIONS[batch]
            gen = generator(name)
            binding = inputs.oracle.binding
            steps[batch] = tuple(
                d for f in functions for d in _drafts(getattr(gen, f)(binding))
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
        ), f"{name} drafts are not the reviewed drafts"
    assert len(inputs.oracle.reference_resolutions) == 51
    return inputs


def _drafts(
    out: ReferenceResolution | tuple[ReferenceResolution, ...],
) -> tuple[ReferenceResolution, ...]:
    return (out,) if isinstance(out, ReferenceResolution) else tuple(out)


def simulated() -> AcceptedInputs:
    """The chain under the simulated reviewer, held to its pinned bytes."""
    inputs = chain(SIMULATED_REVIEWER, SIMULATED_RULE, SIMULATED_RULE, SIMULATED_AT)
    data = serialize_accepted_inputs(inputs)
    assert hashlib.sha256(data).hexdigest() == SIMULATED_SHA256, "drifted"
    return inputs


def recorded() -> AcceptedInputs:
    """The recorded seventeen-batch chain, rebuilt from its recorded time.

    It is the prior the Spell Descriptions step composed over, and is never read
    back from the artifact, which now also holds that step.
    """
    inputs = owner_chain(RECORDED_AT[0])
    data = serialize_accepted_inputs(inputs)
    assert hashlib.sha256(data).hexdigest() == RECORDED_SHA256["chain"], "drifted"
    return inputs


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def spells_accepted(base: AcceptedInputs, reviewer: str, at: str) -> AcceptedInputs:
    """Step 2: the Spell Descriptions proposal, accepted whole, over the chain."""
    assert _sha(SD_FILE.read_bytes()) == SD_FILE_SHA256, SD_FILE.name
    proposal = load_proposal(SD_FILE, expected_identity=SD_IDENTITY)
    assert proposal.binding == base.oracle.binding
    return accept_proposal(
        proposal,
        batch_id=SD_BATCH_ID,
        rule=APPROVAL if reviewer == OWNER else SIMULATED_RULE,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=reviewer,
        accepted_at=at,
        prior=base,
    )


def spells_resolved(
    base: AcceptedInputs, accepted: AcceptedInputs, reviewer: str, at: str
) -> AcceptedInputs:
    """Step 3: the reviewed drafts, drafted over the chain ``base``, over step 2."""
    drafts = generator("spell-descriptions").draft_resolutions(
        base.oracle.binding, prior=base
    )
    raw = SD_DRAFTS_FILE.read_bytes()
    assert _sha(raw) == SD_DRAFTS_SHA256, SD_DRAFTS_FILE.name
    assert json.loads(raw) == list(
        reference_resolution_payload(drafts)
    ), "the drafts are not the reviewed drafts"
    assert len(drafts) == 1046, len(drafts)
    reference = AUTHORIZATION_REFERENCE if reviewer == OWNER else SIMULATED_RULE
    return resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by=reviewer,
        authorization_reference=reference,
        reviewer=reviewer,
        resolved_at=at,
    )


def owner_chain(at: str) -> AcceptedInputs:
    """Step 1 under the Owner's decision at ``at``."""
    return chain(OWNER, APPROVAL, AUTHORIZATION_REFERENCE, at)


def _one(values: set[str], what: str) -> str:
    assert len(values) == 1, f"{what}: {sorted(values)}"
    return next(iter(values))


def _is_spell_resolution(resolution_id: str) -> bool:
    return resolution_id.endswith("-spell-descriptions-1")


def _read_back(inputs: AcceptedInputs) -> tuple[str, str | None, str | None]:
    """The executed step times recorded in ``inputs``: chain, spells, resolved."""
    ids = {b for b, _, _ in BATCHES}
    chain_at = _one(
        {a.accepted_at for a in inputs.acceptances if a.batch_id in ids}
        | {
            a.resolved_at
            for a in inputs.reference_resolution_acceptances
            if not _is_spell_resolution(a.resolution_id)
        },
        "chain times",
    )
    sd = {a.accepted_at for a in inputs.acceptances if a.batch_id == SD_BATCH_ID}
    resolved = {
        a.resolved_at
        for a in inputs.reference_resolution_acceptances
        if _is_spell_resolution(a.resolution_id)
    }
    return (
        chain_at,
        _one(sd, "spell-descriptions accepted_at") if sd else None,
        _one(resolved, "spell-descriptions resolved_at") if resolved else None,
    )


def _state() -> tuple[str, AcceptedInputs | None, AcceptedInputs | None]:
    """(state, chain, result) of the artifact, after checking it rebuilds.

    Fails closed on anything but absent or one of the three step results.
    """
    if not ACCEPTED_PATH.exists():
        return "absent", None, None
    data = ACCEPTED_PATH.read_bytes()
    inputs = load_accepted_inputs(ACCEPTED_PATH)
    got = {b.batch_id for b in inputs.batches}
    ids = {b for b, _, _ in BATCHES}
    if got not in (ids, ids | {SD_BATCH_ID}):
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized batches {sorted(got)}")
    chain_at, sd_at, resolved_at = _read_back(inputs)
    base = owner_chain(chain_at)
    result: AcceptedInputs
    if got == ids and not sd_at and not resolved_at:
        state, result = "chain", base
    elif got != ids and sd_at and not resolved_at:
        state, result = "spells-accepted", spells_accepted(base, OWNER, sd_at)
    elif got != ids and sd_at and resolved_at:
        state = "resolved"
        result = spells_resolved(
            base, spells_accepted(base, OWNER, sd_at), OWNER, resolved_at
        )
    else:
        raise SystemExit(f"{ACCEPTED_PATH.name}: unrecognized step times")
    assert data == serialize_accepted_inputs(result), f"{state} artifact drifted"
    return state, base, result


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
    print("  seventeen-batch chain preserved", not lost, _counts(base))
    assert not violations, violations
    assert not lost, lost
    assert _counts(base) == EXPECTED["chain"][0], _counts(base)
    counts, findings = EXPECTED[state]
    assert _counts(inputs) == counts, _counts(inputs)
    if findings is not None:
        assert _findings(inputs) == findings


def _precheck(base: AcceptedInputs) -> None:
    """The later steps, in memory under the simulated reviewer, over ``base``."""
    spells_resolved(
        base,
        spells_accepted(base, SIMULATED_REVIEWER, SIMULATED_AT),
        SIMULATED_REVIEWER,
        SIMULATED_AT,
    )


def simulate() -> None:
    inputs = simulated()
    print("SIMULATED (in memory; nothing written; not an acceptance)")
    print("  reviewer", repr(SIMULATED_REVIEWER))
    print("  bytes sha256", SIMULATED_SHA256)
    print("  batches", [b.batch_id for b in inputs.batches])
    composed = spells_resolved(
        inputs,
        spells_accepted(inputs, SIMULATED_REVIEWER, SIMULATED_AT),
        SIMULATED_REVIEWER,
        SIMULATED_AT,
    )
    _check("chain", inputs, inputs)
    _check("resolved", inputs, composed)


def verify(state: str, base: AcceptedInputs, inputs: AcceptedInputs) -> None:
    data = ACCEPTED_PATH.read_bytes()
    print("state", state, _sha(data))
    assert _sha(data) == RECORDED_SHA256[state], "not the recorded bytes"
    assert _read_back(inputs) == tuple(
        t if i <= list(RECORDED_SHA256).index(state) else None
        for i, t in enumerate(RECORDED_AT)
    ), "not the recorded times"
    assert _sha(serialize_accepted_inputs(base)) == RECORDED_SHA256["chain"]
    print("  times (chain, spells, resolved)", _read_back(inputs))
    _check(state, base, inputs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ACCEPTED_PATH.name
        path.write_bytes(data)
        assert serialize_accepted_inputs(load_accepted_inputs(path)) == data
    print("  reloads to the same bytes True")


def main(argv: list[str]) -> None:
    if argv == ["--simulate"]:
        simulate()
        return
    state, base, inputs = _state()
    if argv == ["--verify"]:
        if base is None or inputs is None:
            raise SystemExit(f"{ACCEPTED_PATH.name} is {state}")
        verify(state, base, inputs)
        return
    steps = {
        "record": "absent",
        "accept-spells": "chain",
        "resolve-spells": "spells-accepted",
    }
    if len(argv) != 1 or argv[0] not in steps:
        raise SystemExit(
            "usage: --simulate | record | accept-spells | resolve-spells | --verify"
        )
    if state != steps[argv[0]]:
        raise SystemExit(f"{ACCEPTED_PATH.name} is {state}, not {steps[argv[0]]}")
    if argv == ["record"]:
        _precheck(simulated())
        result = owner_chain(_now())
    elif argv == ["accept-spells"]:
        assert base is not None
        _precheck(base)
        result = spells_accepted(base, OWNER, _now())
    else:
        assert base is not None and inputs is not None
        result = spells_resolved(base, inputs, OWNER, _now())
    data = serialize_accepted_inputs(result)
    ACCEPTED_PATH.write_bytes(data)
    print(argv[0], ACCEPTED_PATH.name, _sha(data))
    # Read the written artifact back: it must rebuild from its recorded times.
    after, base, inputs = _state()
    assert after == {"record": "chain", "accept-spells": "spells-accepted"}.get(
        argv[0], "resolved"
    ), after
    assert base is not None and inputs is not None
    verify(after, base, inputs)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
