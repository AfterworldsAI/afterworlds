"""CRD Issue 5d — batch `attitudes-1`, representation schema 8.

Executable generator for the attitudes-1 proposal and its audit. It reads the
committed SRD through the 5c pipeline, re-derives the attitude boundary from
the source's own entry class, cuts every represented leaf into an exact
partition, assigns each cut to the element that states it, and writes two
deterministic LF artifacts. It accepts nothing, publishes nothing, activates
nothing, retires nothing and touches no database.

Why this batch, and what its membership is
------------------------------------------
The batch is chosen by **complete source membership**, on the shape the three
accepted batches already established: a source-tagged entry class *plus* the
untagged umbrella glossary rule that defines the tag. conditions-1 was the 15
``[Condition]`` entries plus ``Condition``; hazards-1 the 5 ``[Hazard]``
entries plus ``Hazard``; actions-1 the 12 ``[Action]`` entries plus ``Action``.

``[Attitude]`` is the next complete class under that rule and the smallest one
left: three entries — Friendly, Hostile, Indifferent — plus the umbrella
``Attitude``. Four records, sixteen leaves, sixteen represented, **zero policy
exclusions**. The boundary is re-derived below from the tag itself and checked
against the names the umbrella's own "See also" prints, so an attitude added or
renamed upstream fails this run rather than silently dropping out.

The one remaining unaccepted tagged class, ``[Area of Effect]`` (Cone, Cube,
Cylinder, Emanation, Line, Sphere, plus its umbrella), is deliberately **not**
this batch: it needs an entire spatial-geometry family — point of origin, shape
dimensions, origin inclusion, line of effect blocked by Total Cover — that no
current fact carries, and that sits against the settled "no general rules
engine" boundary. It stays the next candidate, not this one.

That three of the five reference targets accepted authority is currently
missing happen to be ``attitude.friendly``, ``attitude.hostile`` and
``attitude.indifferent`` is a **consequence** of picking a complete source
class, not the reason for it. ``glossary.concentration`` and ``glossary.speed``
are untagged entries in other source groups and stay unresolved after this
batch; the audit states that, rather than implying the blocker is cleared.

What this run is, and is not
----------------------------
* It is *proposal preparation*. Zero validator findings is necessary and
  explicitly insufficient; this is material for semantic review.
* Nothing here is accepted, activated, published or retired. The publication
  gate is not executed by this run at all — there is no persisted projection to
  run it over.
* The accepted three-batch prior is read **only** as a frozen review prior, by
  content identity, and asserted unchanged afterwards. The live oracle is read
  as a mutation sentinel and is never an input.

Schema
------
**One extension, registered and minimal.** Every mechanic in this batch but one
has an admissible shape under representation schema 7 as accepted. The
exception is schema stop ``S-2``, and schema 8 closes it with a single fact
family, ``DefaultAttitudeFact``, over a single closed vocabulary, ``Attitude``
(see ``SCHEMA_STOPS``). The crossing is the registered transition
``5d-lift-schema-7-to-8``, exercised below against the frozen accepted prior.

The load-bearing precedent is ``condition.charmed``'s ``social_advantage``,
already accepted: *"The charmer has Advantage on any ability check to interact
with you socially"* is a ``MIXED`` component carrying an ``AdvantageFact`` over
``RollSpec(actor=AGAINST_SUBJECT, context=ABILITY_CHECK, ability=None)`` plus a
``contextual_applicability`` binding for the purpose restriction. ``RollActor``
says so verbatim in its own docstring: that case's "actor restriction is
applicability prose on a ``MIXED`` component, and admitting a member for it
would have widened the union on speculation." Friendly and Hostile are the same
sentence with the polarity flipped and "to influence" in place of "to interact
socially", so they take the same shape and add nothing to any vocabulary.

Schema stop S-2, and how it is closed
-------------------------------------
``S-2``: *"Indifferent is the default attitude of a monster."* states a
determinate rule — absent any other specification a monster's attitude is
Indifferent, which then feeds ``action.influence``'s check — and schema 7
carried no fact family for "this record is the default member of its class".

The governing rule is **#137 contract 3**: if a substantive family cannot be
represented by the current union, *add a specific typed family or classify the
affected component honestly as prose-bound*. Its prose-bound branch is
unavailable here — none of the six closed irreducibility reasons is true of the
clause (nothing about it is contextual, subjective, unbounded, delegated to the
GM, an exception, or fiction-dependent), and binding it anyway would record a
vocabulary gap as an irreducibility. That leaves the typed branch, so schema 8
adds ``DefaultAttitudeFact`` over ``Attitude`` and nothing else, and ``I2`` is
emitted ``SUBSTANTIVE``.

**Sibling count is not an admission gate.** An earlier revision of this file
asserted that "the typed vocabularies are evidence-bound, admitting a member
only with siblings in more than one section". That rule was explicitly
*withdrawn* by ``issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md`` §6, and the
union itself records the counterexample: ``MovementPermissionFact`` is "the
thinnest family admitted here", two instances, and its own docstring says "its
vocabulary is stronger than its sibling count." ``BenefitUseLimit`` has one
member. Sibling count is evidence a reviewer weighs; contract 3 and ADR-005d
Decision 4 state the gate.

``SIBLING_SWEEP`` is retained as what it actually measures: an exact-phrase
count of ``is the default`` over the represented leaves. It is *not* evidence
that no semantically related default exists elsewhere in the corpus — a
paraphrase would not match it — and it is not an admission test. It is
re-executed by this run so the figure quoted is measured rather than asserted.

Emission rule
-------------
Every represented leaf of every attitude entry is partitioned end to end. A
segment's first element is the text the segment **ends with**; ``None`` means
"to the end of the leaf". Cuts are found in the bound leaf content at run time
and fail loudly if the source moved. Separator runs are absorbed as the
*leading* text of the next segment, so the partition reconstructs each leaf
byte for byte.

Reference siting
----------------
A source-authored reference is emitted where the source **cites a record as a
defined term**, not at every place it says the word. That is the rule the
accepted batches already follow: ``glossary.hazard`` emits its five references
from its quoted "See also" list and classifies *"A hazard is an environmental
danger."* as supporting authority; ``action.dash`` emits ``Speed`` from its
"See also" leaf while its body's four other mentions of Speed carry facts;
``glossary.condition`` and ``glossary.action`` emit from their printed
enumerations, which are the only place they cite their members.

So ``glossary.attitude``'s four references come from its "See also" leaf, and
its body sentence — *"A monster has a starting attitude toward a player
character: Friendly, Hostile, or Indifferent."* — is the record's own
definitional framing, exactly as *"A hazard is an environmental danger."* is.
Siting them at both places would also have collided: ``reference_target_key``
keys on ``source_text``, and the term is spelled the same in both leaves.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

#: The repository this run reads everything from, derived from where this file
#: actually lives: `<repo>/.claude/review-notes/<this file>`.
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
assert OUT.name == "review-notes" and OUT.parent.name == ".claude", OUT
sys.path.insert(0, str(REPO / "src"))

SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"

#: **The frozen review prior.** Accepted authority as it stands for this batch's
#: review: conditions-1, hazards-1 and actions-1, representation schema 7. Read
#: only, by content identity, and asserted unchanged at the end of the run.
REVIEW_PRIOR_PATH = (
    REPO
    / "tests/ingestion/mechanical/data"
    / "accepted_prior_conditions_1_hazards_1_actions_1.json"
)

#: **A mutation sentinel, never an input.** Bytes captured before generation and
#: asserted identical afterwards. Never loaded, lifted, merged, or recorded.
LIVE_ORACLE_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)
PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (SOURCE_PDF, REVIEW_PRIOR_PATH, LIVE_ORACLE_PATH, PACKAGE_ROOT):
    assert (
        _required.exists()
    ), f"missing beneath the derived repository root: {_required}"
for _module in (
    "ingestion/mechanical/representation.py",
    "ingestion/mechanical/schema_lift.py",
    "ingestion/mechanical/validation.py",
    "ingestion/mechanical/oracle.py",
    "ingestion/mechanical/acceptance.py",
    "ingestion/mechanical/projection.py",
    "ingestion/mechanical/policy.py",
    "ingestion/corpus/pipeline.py",
):
    assert (PACKAGE_ROOT / _module).exists(), f"missing module: {_module}"

#: The frozen review prior, identified by **content** rather than by whatever
#: bytes a working copy holds. `.gitattributes` declares `* text=auto eol=lf`,
#: so a raw digest is a property of a checkout; the canonical (CRLF -> LF)
#: SHA-256 and the Git blob id are properties of the authority.
REVIEW_PRIOR_CONTENT_SHA256 = "87864b6ac81e4f8baf57eddf9524dade1b2045a5fc804c79b3d57412c87f46fc"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BLOB = (
    "a729a797594e1156b279fac76c3073c733707a2f"  # pragma: allowlist secret
)
REVIEW_PRIOR_IDENTITY = "8c41b01e92878c614fad5c039c006c66221a4cc55cfab68698ef9302865a6eee"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_BATCH_IDS = ["actions-1", "conditions-1", "hazards-1"]
REVIEW_PRIOR_SCHEMA_VERSION = "5d-representation-schema-7"
REVIEW_PRIOR_SCHEMA_HASH = "80e853ef9433ba2e7232c384a7192235692463c9954f5ff766be1fafade6f43d"  # noqa: E501  # pragma: allowlist secret
REVIEW_PRIOR_RECORDS = 35
REVIEW_PRIOR_SPANS = 463

# --- Retained-evidence guard ------------------------------------------------
# Every artifact of the three accepted batches records authority or the
# discovery this run derives its brief from. Refuse to run if this file would
# overwrite one, and assert afterwards that none of them moved.
PROPOSAL_FILE = "issue-5d-batch-attitudes-1-PROPOSAL.json"
AUDIT_FILE = "issue-5d-batch-attitudes-1-audit.json"
WRITES = {PROPOSAL_FILE, AUDIT_FILE}
#: This run's own two outputs are excluded, and only those two: on the
#: determinism rerun they already exist from the parent, and a rerun that
#: refused to overwrite them could not prove anything about reproducibility.
RETAINED = tuple(
    sorted(
        p.name
        for p in OUT.iterdir()
        if p.is_file()
        and p.name != Path(__file__).name
        and p.name not in WRITES
        and p.suffix != ".tmp"
    )
)
assert not (WRITES & set(RETAINED)), "would overwrite retained evidence"
_RETAINED_BEFORE = {
    n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in RETAINED
}

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import _full_coverage_edges  # noqa: E402
from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    _merge_representation,
)
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    derive_span_id,
    validate_partition,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    _representation,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    IRREDUCIBILITY_REASONS,
    SEMANTIC_POLICY_VERSION,
    irreducibility_reason_for,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ProjectionCandidate,
    ReleaseBinding,
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    AdvantageFact,
    AdvantageState,
    Attitude,
    ComponentDraft,
    DefaultAttitudeFact,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    component_damage_composition_violations,
    component_roll_outcome_violations,
    fact_invariant_violations,
    fact_key,
    fact_target_key,
    held_structure_violations,
    option_set_violations,
    prose_binding_target_key,
    reference_target_key,
    representation_draft_violations,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (  # noqa: E402
    lift_path,
    verify_lift_path,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402
from afterworlds.services.rules_authority.application import (  # noqa: E402
    _base_records,
)

import afterworlds  # noqa: E402  # isort: skip

IMPORTED_FROM = Path(afterworlds.__file__).resolve().parent
assert PACKAGE_ROOT.resolve() == IMPORTED_FROM, (IMPORTED_FROM, PACKAGE_ROOT)
INPUT_PATHS = {
    "repository_root_derived_from": "Path(__file__).resolve().parents[2]",
    "source_pdf": SOURCE_PDF.relative_to(REPO).as_posix(),
    "review_prior": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
    "afterworlds_package": IMPORTED_FROM.relative_to(REPO).as_posix(),
    "output_directory": OUT.relative_to(REPO).as_posix(),
    "note": (
        "Recorded relative to the derived root on purpose: an absolute path "
        "would make this artifact differ between two checkouts that produced "
        "identical content. The live accepted-authority oracle is deliberately "
        "absent: it is not an input. This run reads it only as a mutation "
        "sentinel and records neither its path nor its digest, because an "
        "accumulating artifact's identity goes stale at the next acceptance."
    ),
}

SCHEMA = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
assert SCHEMA[0] == "5d-representation-schema-8", SCHEMA
assert SCHEMA[1] == (
    "8a125f6c4c9929109879ad98a8f14a4ec1d0c7f5fe56fe4f894dafbdf707afff"  # noqa: E501  # pragma: allowlist secret
), SCHEMA

# ---------------------------------------------------------------------------
# Bound release - derived from the committed PDF, asserted against production
# ---------------------------------------------------------------------------

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret
TRANSFORM_CONFIG_HASH = "77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e"  # noqa: E501  # pragma: allowlist secret
BUNDLE_ROOT_HASH = "03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685"  # noqa: E501  # pragma: allowlist secret

#: The only binding value NOT independently derivable here: a function of the
#: persisted `rp_sources` rows and verified Chroma state, so reproducing it
#: requires an actual publish, which this generator must not do. Taken from the
#: published CRD Issue 5c release record and disclosed as such.
PERSISTED_CORPUS_DIGEST = "c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b"  # noqa: E501  # pragma: allowlist secret

CAND = build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())
assert CAND.package_uuid == PACKAGE_UUID, CAND.package_uuid
assert CAND.release_version == RELEASE_VERSION, CAND.release_version
assert CAND.authoritative_source_hash == SOURCE_SHA256, CAND.authoritative_source_hash
assert CAND.transform_config_hash == TRANSFORM_CONFIG_HASH, CAND.transform_config_hash
assert CAND.bundle.bundle_root_hash == BUNDLE_ROOT_HASH, CAND.bundle.bundle_root_hash

LEDGER_OBJ = CAND.ledger
LABELS = {c.container_id: c.label for c in LEDGER_OBJ.containers}
CONTAINERS = {c.container_id: c for c in LEDGER_OBJ.containers}
LEAF_BY_ID = {leaf.leaf_id: leaf for leaf in LEDGER_OBJ.leaves}
REPRESENTED = {
    leaf.leaf_id
    for leaf in LEDGER_OBJ.leaves
    if exclusion_reason_for(leaf, LABELS) is None
}
EDGES = _full_coverage_edges(CAND.members.chunks, LEAF_BY_ID)

BINDING = ReleaseBinding(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    authoritative_source_hash=CAND.authoritative_source_hash,
    transform_config_hash=CAND.transform_config_hash,
    bundle_root_hash=CAND.bundle.bundle_root_hash,
    persisted_corpus_digest=PERSISTED_CORPUS_DIGEST,
)
CORPUS = BoundCorpusSnapshot(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    leaf_lengths={lid: len(LEAF_BY_ID[lid].content) for lid in REPRESENTED},
    chunk_coverage=tuple(
        ChunkCoverage(
            chunk_id=e.chunk_id,
            leaf_id=e.leaf_id,
            cover_start=e.cover_start,
            cover_end=e.cover_end,
            role=e.role,
            projection_id=e.projection_id,
        )
        for e in EDGES
    ),
)
chunk_of_leaf = {e.leaf_id: e.chunk_id for e in EDGES}


def _ancestry(cid: str) -> list[str]:
    out, cur = [], CONTAINERS.get(cid)
    while cur:
        out.append(cur.container_id)
        cur = CONTAINERS.get(cur.parent_id) if cur.parent_id else None
    return out


RULES_DEFINITIONS = next(
    c.container_id for c in LEDGER_OBJ.containers if c.label == "Rules Definitions"
)
ENTRY_BY_LABEL = {
    c.label: c.container_id
    for c in LEDGER_OBJ.containers
    if c.container_type == "entry" and RULES_DEFINITIONS in _ancestry(c.container_id)
}

by_container: dict[str, list] = defaultdict(list)
for _leaf in LEDGER_OBJ.leaves:
    if _leaf.leaf_id not in REPRESENTED:
        continue
    for _cid in _leaf.container_path:
        by_container[_cid].append(_leaf)
for _group in by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

LSQ = "“"  # left double quotation mark
RSQ = "”"  # right double quotation mark

# --- Boundary, re-derived from the source rather than asserted --------------
# The source's own entry class: `[Attitude]`-tagged entries under Rules
# Definitions, plus the umbrella `Attitude` glossary rule. Derived by scanning
# the labels, then checked against the names the umbrella's own "See also"
# prints, so an attitude added or renamed upstream fails here rather than
# silently dropping out of the batch.
ATTITUDE_LABELS = sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Attitude]"))
NAMED = ["Friendly", "Hostile", "Indifferent"]
assert [f"{n} [Attitude]" for n in sorted(NAMED)] == ATTITUDE_LABELS, ATTITUDE_LABELS
assert len(ATTITUDE_LABELS) == 3, ATTITUDE_LABELS
UMBRELLA_SEE_ALSO = by_container[ENTRY_BY_LABEL["Attitude"]][3].content
for _n in NAMED:
    assert f"{LSQ}{_n}," in UMBRELLA_SEE_ALSO, f"{_n} is not cited by the umbrella"

#: The class this batch is a complete member of, derived rather than narrated:
#: the five tag values the Rules Glossary's own preamble names, and which of
#: them accepted authority already carries.
TAG_CLASSES = {
    tag: sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(f" [{tag}]"))
    for tag in ("Action", "Area of Effect", "Attitude", "Condition", "Hazard")
}
assert {t: len(v) for t, v in TAG_CLASSES.items()} == {
    "Action": 12,
    "Area of Effect": 6,
    "Attitude": 3,
    "Condition": 15,
    "Hazard": 5,
}, {t: len(v) for t, v in TAG_CLASSES.items()}

BATCH_LABELS = ["Attitude", *ATTITUDE_LABELS]

#: Policy exclusions inside this boundary. There are none — every leaf of every
#: attitude entry is represented — and that is asserted rather than assumed,
#: because a batch that silently lost a body leaf would look the same as one
#: that lost a running header.
POLICY_EXCLUDED = sorted(
    leaf.leaf_id
    for lab in BATCH_LABELS
    for cid in [ENTRY_BY_LABEL[lab]]
    for leaf in LEDGER_OBJ.leaves
    if cid in leaf.container_path and leaf.leaf_id not in REPRESENTED
)
assert POLICY_EXCLUDED == [], POLICY_EXCLUDED

SCOPE_KEY = "srd-5.2.1/rules-glossary"

RECORD_KEY: dict[str, str] = {"Attitude": "glossary.attitude"}
for lab in ATTITUDE_LABELS:
    RECORD_KEY[lab] = "attitude." + lab.split(" [")[0].lower()
#: `RecordKind` is a closed vocabulary and has no attitude member. The umbrella
#: and its three entries are all Rules Glossary definitions, which is what
#: `GLOSSARY_RULE` means, and it is the kind actions-1 gave both its umbrella
#: and its twelve entries. Minting a kind for a three-member class would widen
#: a closed vocabulary for one batch's convenience.
RECORD_KIND = {k: RecordKind.GLOSSARY_RULE for k in RECORD_KEY.values()}

ATT = "glossary.attitude"
FRI = "attitude.friendly"
HOS = "attitude.hostile"
IND = "attitude.indifferent"
INFL = "action.influence"

CTX = "contextual_applicability"
assert irreducibility_reason_for(CTX) is not None, CTX

# ---------------------------------------------------------------------------
# The typed facts
# ---------------------------------------------------------------------------
#
# One shape, twice, with the polarity flipped — and it is `condition.charmed`'s
# accepted `social_advantage` shape, not a new one. "You have Advantage on an
# ability check to influence a Friendly creature" is a roll DIRECTED AT the
# subject of the record (the Friendly creature), which is exactly what
# `AGAINST_SUBJECT` means, and the purpose restriction — *which* ability check,
# the one made to influence — is applicability prose on a `MIXED` component
# rather than a new `RollContext` or a new `RollActor`.

INFLUENCE_ROLL = RollSpec(
    actor=RollActor.AGAINST_SUBJECT,
    context=RollContext.ABILITY_CHECK,
)
FRIENDLY_ADV = AdvantageFact(state=AdvantageState.ADVANTAGE, roll=INFLUENCE_ROLL)
HOSTILE_DIS = AdvantageFact(state=AdvantageState.DISADVANTAGE, roll=INFLUENCE_ROLL)

# The schema-8 family, stating the value rather than inferring it from the
# record it sits on. `attitude.indifferent` is a semantic key, not evidence:
# reading the member off the key is the by-convention inference the union
# already refuses elsewhere, so the fact names INDIFFERENT outright. The
# component is STRUCTURED - the whole clause is typed, and nothing is left over
# for governing prose to carry.
DEFAULT_ATTITUDE = DefaultAttitudeFact(attitude=Attitude.INDIFFERENT)

COMPONENTS: dict[tuple[str, str], dict] = {
    (FRI, "influence_advantage"): dict(handling=ComponentHandling.MIXED, reason=CTX),
    (HOS, "influence_disadvantage"): dict(handling=ComponentHandling.MIXED, reason=CTX),
    (IND, "default_attitude"): dict(handling=ComponentHandling.STRUCTURED),
}

# ---------------------------------------------------------------------------
# The proposed batch, as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Segment shape: (marker, kind, arg, obligation).
#
#   R  supporting authority, claimed CONTEXTUAL by the record          arg=None
#   X  supporting authority, claimed CONTEXTUAL by a reference
#                                     arg=(source_text, target[, from_component])
#   F  substantive, claimed PRIMARY by a typed fact              arg=(comp, fact)
#   P  substantive, claimed PRIMARY by a prose binding         arg=(comp, reason)
#   U  unresolved: read, but not classifiable safely under this schema. Claimed
#      by nothing, because `UNRESOLVED` admits no provenance claim at all, and
#      it blocks publication.                                          arg=None

W = [(None, "R", None, None)]  # whole leaf, supporting authority, owned by the record

SPEC: dict[str, list] = {}

# --- Attitude (umbrella glossary rule) -------------------------------------
# No components. The umbrella states what an attitude is and cites its three
# members plus the action they feed; it states no mechanic of its own. That is
# `glossary.hazard`'s accepted shape exactly — record-owned references, no
# component, no binding — and it is what the source prints.
SPEC["Attitude"] = [
    W,  # 'Attitude'
    W,  # 'A monster has a starting attitude toward a player character: ...'
    W,  # 'See also'
    [
        (f"{LSQ}Friendly,{RSQ}", "X", ("Friendly", FRI), "T3"),
        (f"{LSQ}Hostile,{RSQ}", "X", ("Hostile", HOS), "T3"),
        (f"{LSQ}Indifferent,{RSQ}", "X", ("Indifferent", IND), "T3"),
        (None, "X", ("Influence", INFL), "T4"),
    ],
]

# --- Friendly --------------------------------------------------------------
SPEC["Friendly [Attitude]"] = [
    W,  # 'Friendly [Attitude]'
    [
        ("views you favorably.", "R", None, "F1"),
        (
            " You have Advantage on an ability check",
            "F",
            ("influence_advantage", FRIENDLY_ADV),
            "F2",
        ),
        (None, "P", ("influence_advantage", CTX), "F3"),
    ],
    W,  # 'See also'
    [(None, "X", ("Influence", INFL), "F4")],
]

# --- Hostile ---------------------------------------------------------------
SPEC["Hostile [Attitude]"] = [
    W,  # 'Hostile [Attitude]'
    [
        ("views you unfavorably.", "R", None, "H1"),
        (
            " You have Disadvantage on an ability check",
            "F",
            ("influence_disadvantage", HOSTILE_DIS),
            "H2",
        ),
        (None, "P", ("influence_disadvantage", CTX), "H3"),
    ],
    W,  # 'See also'
    [(None, "X", ("Influence", INFL), "H4")],
]

# --- Indifferent -----------------------------------------------------------
# One component, carrying the default. The definitional sentence stays the
# record's own supporting authority; the default statement is the schema-8
# family, so I2 is claimed by a typed fact rather than left UNRESOLVED.
SPEC["Indifferent [Attitude]"] = [
    W,  # 'Indifferent [Attitude]'
    [
        ("help or hinder you.", "R", None, "I1"),
        (None, "F", ("default_attitude", DEFAULT_ATTITUDE), "I2"),
    ],
    W,  # 'See also'
    [(None, "X", ("Influence", INFL), "I3")],
]

#: Every source clause this batch must account for, named once. Every id must be
#: discharged by at least one span, and no span may name an id that is not here.
OBLIGATION_IDS = [
    "T1",
    "T2",
    "T3",
    "T4",
    "F1",
    "F2",
    "F3",
    "F4",
    "H1",
    "H2",
    "H3",
    "H4",
    "I1",
    "I2",
    "I3",
]
OBLIGATION_TEXT = {
    "T1": "the umbrella names the term",
    "T2": "a monster has a starting attitude, drawn from exactly three",
    "T3": "the umbrella cites its three members",
    "T4": "the umbrella cites the action its members affect",
    "F1": "what a Friendly creature is",
    "F2": "Advantage on the check",
    "F3": "which check: the one made to influence a Friendly creature",
    "F4": "Friendly cites the action it affects",
    "H1": "what a Hostile creature is",
    "H2": "Disadvantage on the check",
    "H3": "which check: the one made to influence a Hostile creature",
    "H4": "Hostile cites the action it affects",
    "I1": "what an Indifferent creature is",
    "I2": "Indifferent is the default attitude of a monster",
    "I3": "Indifferent cites the action it affects",
}
assert len(OBLIGATION_IDS) == len(set(OBLIGATION_IDS)) == 15, len(OBLIGATION_IDS)
assert sorted(OBLIGATION_TEXT) == sorted(OBLIGATION_IDS)

#: `W` carries no obligation id, so the three whole-leaf umbrella spans and the
#: eight heading/"See also" spans are attributed here rather than left blank.
#: Keyed by (record, leaf index) so the attribution is checkable against the
#: partition below.
WHOLE_LEAF_OBLIGATION = {
    (ATT, 0): "T1",
    (ATT, 1): "T2",
    (ATT, 2): "T3",
    (FRI, 0): "F1",
    (FRI, 2): "F4",
    (HOS, 0): "H1",
    (HOS, 2): "H4",
    (IND, 0): "I1",
    (IND, 2): "I3",
}

# ---------------------------------------------------------------------------
# Emission
# ---------------------------------------------------------------------------

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
references: list[ReferenceDraft] = []
prose_bindings: list[ProseBindingDraft] = []
comp_facts: dict[tuple[str, str], list] = defaultdict(list)
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "X": SemanticDisposition.SUPPORTING_AUTHORITY,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
    "U": SemanticDisposition.UNRESOLVED,
}
RATIONALE = {
    "R": (
        "identifies, frames, or defines the mechanic; preserved as supporting "
        "authority owned by the record rather than discarded"
    ),
    "X": (
        "a source-authored mechanical reference, resolved at build time within a "
        "committed scope to an exact target record; supporting authority, because "
        "naming a rule is not stating one"
    ),
    "F": (
        "states a mechanic the closed typed union carries exactly, with every "
        "qualifier that narrows or multiplies it carried by a structure of this "
        "schema rather than left implicit"
    ),
    "P": (
        "affirmatively irreducible under a closed reason code: the predicate "
        "ranges over fiction the projection cannot enumerate, and the mechanic "
        "it governs is typed beside it"
    ),
    "U": (
        "states a determinate mechanic this schema has no structure for, so no "
        "admissible composition carries it: typing it would assert it beyond its "
        "printed scope, and prose-binding it would record a vocabulary gap as an "
        "irreducibility. Read, unclaimed, and publication-blocking until the "
        "schema can express it"
    ),
}
CLAIMANT_KIND = {
    "R": "record",
    "X": "reference",
    "F": "fact",
    "P": "prose_binding",
    "U": "none",
}

ORIGIN = "issue-5d-batch-attitudes-1-generator.py"
leaf_content: dict[str, str] = {}
obligation_spans: dict[str, list[str]] = defaultdict(list)

for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(
        leafspecs
    ), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for leaf_index, (lf, segs) in enumerate(zip(lvs, leafspecs, strict=True)):
        content, lid = lf.content, lf.leaf_id
        leaf_content[lid] = content
        cursor = 0
        for marker, kind, arg, obligation in segs:
            if obligation is None:
                obligation = WHOLE_LEAF_OBLIGATION[(rkey, leaf_index)]
            if marker is None:
                end = len(content)
            else:
                found = content.find(marker, cursor)
                assert found >= 0, f"{label}: marker {marker!r} not in {content!r}"
                end = found + len(marker)
            assert end > cursor, f"{label}: empty segment for marker {marker!r}"
            start, cursor = cursor, end
            sid = derive_span_id(lid, start, end)
            disp = DISP[kind]
            span = SemanticSpan(
                span_id=sid,
                leaf_id=lid,
                char_start=start,
                char_end=end,
                disposition=disp,
                review_state=ReviewState.PROPOSED,
            )
            spans.append(span)
            proposed.append(
                ProposedSpan(span=span, origin=ORIGIN, rationale=RATIONALE[kind])
            )
            assert obligation in OBLIGATION_IDS, obligation
            obligation_spans[obligation].append(sid)

            if kind == "F":
                comp, fact = arg
                claimant = f"{rkey}/{comp}/{fact_key(fact)}"
            elif kind == "P":
                claimant = f"{rkey}/{arg[0]} ({arg[1]})"
            elif kind == "X":
                claimant = f"{rkey} -> {arg[1]}"
            elif kind == "U":
                claimant = ""
            else:
                claimant = rkey
            audit.append(
                {
                    "record": rkey,
                    "obligation": obligation,
                    "obligation_text": OBLIGATION_TEXT[obligation],
                    "leaf": lid,
                    "span_id": sid,
                    "range": [start, end],
                    "text": content[start:end],
                    "disposition": disp.value,
                    "kind": kind,
                    "claimant_kind": CLAIMANT_KIND[kind],
                    "claimant": claimant,
                    "role": (
                        "primary"
                        if disp is SemanticDisposition.SUBSTANTIVE
                        else (
                            "none"
                            if disp is SemanticDisposition.UNRESOLVED
                            else "contextual"
                        )
                    ),
                    "rationale": RATIONALE[kind],
                }
            )

            if kind == "R":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.RECORD,
                        (rkey,),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
            elif kind == "X":
                text, target = arg[0], arg[1]
                owner = arg[2] if len(arg) > 2 else RECORD_OWNED_REFERENCE
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key=owner,
                    source_text=text,
                    scope_key=SCOPE_KEY,
                    target_record_key=target,
                )
                references.append(ref)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.REFERENCE,
                        reference_target_key(ref),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
            elif kind == "F":
                comp, fact = arg
                bucket = comp_facts[(rkey, comp)]
                if all(fact_key(f) != fact_key(fact) for f in bucket):
                    bucket.append(fact)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact, ""),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "P":
                comp, reason = arg
                assert irreducibility_reason_for(reason) is not None, reason
                extent = CORPUS.chunk_relative_range(
                    chunk_of_leaf[lid], lid, start, end
                )
                assert extent is not None, f"{label}: no chunk extent for {sid}"
                pb = ProseBindingDraft(
                    component_key=comp,
                    record_key=rkey,
                    chunk_id=chunk_of_leaf[lid],
                    span_id=sid,
                    chunk_char_start=extent[0],
                    chunk_char_end=extent[1],
                    irreducibility_reason_code=reason,
                )
                prose_bindings.append(pb)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.PROSE_BINDING,
                        prose_binding_target_key(pb),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )

records = tuple(
    RecordDraft(semantic_key=k, kind=RECORD_KIND[k])
    for k in sorted(set(RECORD_KEY.values()))
)
components = tuple(
    ComponentDraft(
        record_key=rkey,
        semantic_key=ckey,
        handling=spec["handling"],
        irreducibility_reason_code=spec.get("reason"),
        facts=tuple(comp_facts[(rkey, ckey)]),
    )
    for (rkey, ckey), spec in COMPONENTS.items()
)
for _c in components:
    assert _c.facts or _c.handling is ComponentHandling.PROSE_BOUND, _c
    for _f in _c.facts:
        assert not fact_invariant_violations(_f), (
            f"{_c.record_key}/{_c.semantic_key}",
            type(_f).__name__,
            fact_invariant_violations(_f),
        )

DRAFT = RepresentationDraft(
    records=records,
    components=components,
    prose_bindings=tuple(prose_bindings),
    relationships=(),
    references=tuple(references),
    provenance=tuple(provenance),
)
LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(spans),
    batches=(),
    acceptances=(),
)

# ---------------------------------------------------------------------------
# Self-checks: pure validators only. No persistence, no gate, no acceptance.
# ---------------------------------------------------------------------------

touched = sorted({s.leaf_id for s in spans})
partition: list[str] = []
for lid in touched:
    partition.extend(validate_partition(lid, CORPUS.leaf_lengths[lid], tuple(spans)))
reason_codes = validate_reason_codes(tuple(spans))
standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))

# --- Source canaries: derived, then compared. A mismatch is stop-and-explain -
CANARIES = {
    "records": (len(records), 4),
    "represented_leaves": (len(touched), 16),
    "policy_exclusions": (len(POLICY_EXCLUDED), 0),
    "container_leaves": (len(touched) + len(POLICY_EXCLUDED), 16),
}
CANARY_MISMATCH = {k: v for k, v in CANARIES.items() if v[0] != v[1]}
assert not CANARY_MISMATCH, (
    "the bound source no longer yields the recorded boundary; stop and explain "
    f"rather than adjusting the batch: {CANARY_MISMATCH}"
)

# --- The classification partition, reconstructed rather than trusted --------
PARTITIONS: dict[str, list[dict]] = {}
for lid in touched:
    ordered = sorted((s for s in spans if s.leaf_id == lid), key=lambda s: s.char_start)
    rebuilt = "".join(leaf_content[lid][s.char_start : s.char_end] for s in ordered)
    assert rebuilt == leaf_content[lid], f"{lid}: partition does not reproduce the leaf"
    prev = 0
    for s in ordered:
        assert s.char_start == prev, f"{lid}: gap or overlap at {s.char_start}"
        prev = s.char_end
    assert prev == CORPUS.leaf_lengths[lid], f"{lid}: partition stops short"
    PARTITIONS[lid] = [
        {
            "range": [s.char_start, s.char_end],
            "text": leaf_content[lid][s.char_start : s.char_end],
            "disposition": s.disposition.value,
        }
        for s in ordered
    ]

# --- Obligation closure, derived from the emitted spans ---------------------
OBLIGATION_CLOSURE = {
    oid: {
        "clause": OBLIGATION_TEXT[oid],
        "spans": obligation_spans[oid],
        "claimants": sorted({a["claimant"] for a in audit if a["obligation"] == oid}),
        "dispositions": sorted(
            {a["disposition"] for a in audit if a["obligation"] == oid}
        ),
        "text": [a["text"] for a in audit if a["obligation"] == oid],
    }
    for oid in OBLIGATION_IDS
}
_open_obligations = [oid for oid in OBLIGATION_IDS if not obligation_spans[oid]]
assert not _open_obligations, f"obligations with no span: {_open_obligations}"
_unknown = sorted(set(obligation_spans) - set(OBLIGATION_IDS))
assert not _unknown, f"spans naming an obligation the ledger does not have: {_unknown}"

#: "All 15 discharged" is true and, alone, misleading: it counts a clause whose
#: text was handed to a supporting-authority span the same as one whose mechanic
#: entered the typed vocabulary. Classified by CARRIAGE — what the span
#: contributes — not by which element happens to own it.
_CARRIAGE = {"F": "typed", "P": "prose_bound", "U": "unresolved"}
OBLIGATION_ACCOUNTING: dict[str, list[str] | dict[str, int]] = {}
for oid in OBLIGATION_IDS:
    kinds = {a["kind"] for a in audit if a["obligation"] == oid}
    bucket = (
        "typed"
        if "F" in kinds
        else (
            "prose_bound"
            if "P" in kinds
            else ("unresolved" if "U" in kinds else "supporting_authority_only")
        )
    )
    OBLIGATION_ACCOUNTING.setdefault(bucket, []).append(oid)  # type: ignore[union-attr]
OBLIGATION_ACCOUNTING["tally"] = {
    k: len(v) for k, v in sorted(OBLIGATION_ACCOUNTING.items()) if isinstance(v, list)
}
assert sum(
    v for v in OBLIGATION_ACCOUNTING["tally"].values()  # type: ignore[union-attr]
) == len(OBLIGATION_IDS), OBLIGATION_ACCOUNTING

# --- The schema stop, measured rather than asserted -------------------------
#
# Two things a reader should not have to take on trust are executed here. The
# closed irreducibility catalog is printed in full with a per-code disposition,
# which is what makes contract 3's prose-bound branch demonstrably unavailable
# rather than merely declined. And the exact-phrase sweep is re-run over the
# source, so the "one statement, one section" figure quoted in the disclosure
# is measured. The sweep is context for a reviewer, NOT an admission test: the
# gate is #137 contract 3, and a sibling-count precondition on typed families
# was withdrawn by issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md section 6.
_DEFAULT_RX = re.compile(r"\bis the default\b", re.IGNORECASE)


def _section_of(leaf: object) -> str:
    path = getattr(leaf, "container_path", ())
    return LABELS.get(path[0], "?") if path else "?"


_default_hits = [
    leaf
    for leaf in LEDGER_OBJ.leaves
    if leaf.leaf_id in REPRESENTED and _DEFAULT_RX.search(leaf.content)
]
_default_sections = sorted({_section_of(leaf) for leaf in _default_hits})
SIBLING_SWEEP = {
    "pattern": _DEFAULT_RX.pattern,
    "represented_leaves_scanned": len(REPRESENTED),
    "matching_leaves": len(_default_hits),
    "sections": _default_sections,
    "matches": [
        {"printed_page": leaf.page_index + 1, "text": leaf.content}
        for leaf in _default_hits
    ],
    "what_this_measures": (
        "an exact-phrase count of 'is the default' over the represented leaves, "
        "and nothing more. It shows this clause is the only leaf that states a "
        "default IN THOSE WORDS; a paraphrase would not match, so it is not "
        "evidence that no semantically related default exists elsewhere in the "
        "corpus."
    ),
    "what_this_is_not": (
        "an admission test. #137 contract 3 states the gate - add a specific "
        "typed family or classify honestly as prose-bound - and ADR-005d "
        "Decision 4 constrains its shape. A universal cross-section "
        "sibling-count precondition was explicitly WITHDRAWN by "
        "issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md section 6, and the "
        "accepted union records the counterexample: MovementPermissionFact is "
        "'the thinnest family admitted here', two instances, and its docstring "
        "says 'its vocabulary is stronger than its sibling count.' "
        "BenefitUseLimit has one member. Sibling count is evidence a reviewer "
        "weighs; it is not a barrier and it is not an Owner Decision."
    ),
}
assert SIBLING_SWEEP["matching_leaves"] == 1, SIBLING_SWEEP
assert _default_sections == ["Rules Glossary"], SIBLING_SWEEP
assert "Indifferent is the default attitude of a monster." in _default_hits[0].content

#: The closed irreducibility catalog, one line each, saying why *that* code is
#: false of this clause rather than asserting a blanket "none of them fit". The
#: keys are checked against the live catalog, so a reason code added or renamed
#: makes this disclosure fail rather than quietly go stale.
REASON_DISPOSITION = {
    "contextual_applicability": (
        "false: the rule has no predicate. It does not apply *when* anything — "
        "it states the value a monster's attitude takes absent other "
        "specification, which is the opposite of a condition on applicability."
    ),
    "subjective_judgment": (
        "false: nothing is left to anyone's judgment. 'Indifferent' is a named "
        "member of a closed three-member class, not an assessment."
    ),
    "open_ended_effect": (
        "false: the effect is closed and singular — one attitude, chosen from "
        "three. There is nothing unbounded to enumerate."
    ),
    "gamemaster_latitude": (
        "false: the source delegates nothing here. It states the default "
        "rather than inviting the GM to pick one."
    ),
    "natural_language_exception": (
        "false: this is the rule, not an exception carved out of one. Nothing "
        "in the batch it could be an exception to states a different default."
    ),
    "fiction_dependent_consequence": (
        "false: the consequence is mechanical and immediate — which attitude "
        "feeds action.influence's check — and depends on no fiction at all."
    ),
}
assert sorted(REASON_DISPOSITION) == sorted(
    reason.code for reason in IRREDUCIBILITY_REASONS
), sorted(REASON_DISPOSITION)

SCHEMA_STOPS = [
    {
        "id": "S-2",
        "status": "closed by representation schema 8",
        "obligation": "I2",
        "record": IND,
        "text": "Indifferent is the default attitude of a monster.",
        "what_it_states": (
            "a determinate rule: absent any other specification a monster's "
            "attitude is Indifferent, which then feeds action.influence's check "
            "with neither Advantage nor Disadvantage."
        ),
        "what_was_missing_under_schema_7": (
            "no fact family carried 'this record is the default member of its "
            "class'. No composition of existing families stated it either: a "
            "default is not an effect, a duration, an allowance, a roll, or a "
            "state transition."
        ),
        "why_not_prose_bound": dict(REASON_DISPOSITION)
        | {
            "conclusion": (
                "none of the six closed reasons is true of it, so binding it "
                "under one anyway would record a vocabulary gap as an "
                "irreducibility — which is exactly the misfiling the closed "
                "catalog exists to prevent."
            )
        },
        "how_it_is_closed": {
            "governing_rule": (
                "#137 contract 3: if a substantive family cannot be represented "
                "by the current union, add a specific typed family or classify "
                "the affected component honestly as prose-bound. The "
                "prose-bound branch is unavailable (see why_not_prose_bound), "
                "so the typed branch is the only one left open."
            ),
            "schema": SCHEMA[0],
            "fact_family": "default_attitude",
            "vocabulary": {"Attitude": [m.value for m in Attitude]},
            "vocabulary_scope": (
                "admitted at its printed closure - 'A monster has a starting "
                "attitude toward a player character: Friendly, Hostile, or "
                "Indifferent.' enumerates the class in one line - rather than "
                "at the single member this batch uses, which is MovementMode's "
                "accepted reasoning."
            ),
            "registered_transition": "5d-lift-schema-7-to-8",
            "adr_005d_decision_4": (
                "satisfied: a specific typed family with a closed vocabulary, "
                "schema and tests. No generic numeric or key-value escape "
                "hatch, no runtime-interpreted script, no general rules DSL."
            ),
            "not_widened": (
                "the fact states a DEFAULT, not an attitude a creature "
                "currently has, and adjudicates nothing at runtime. Friendly "
                "and Hostile keep condition.charmed's accepted AdvantageFact "
                "shape on a MIXED component and gain nothing from this family."
            ),
            "sibling_count_disclosure": SIBLING_SWEEP,
        },
        "disposition": "SUBSTANTIVE, typed under schema 8",
    }
]
assert [s["id"] for s in SCHEMA_STOPS] == ["S-2"]
assert not [s for s in SCHEMA_STOPS if s["status"] == "open"], SCHEMA_STOPS
assert sum(1 for s in spans if s.disposition is SemanticDisposition.UNRESOLVED) == 0

# ---------------------------------------------------------------------------
# The frozen review prior, and the merge acceptance would validate
# ---------------------------------------------------------------------------


def _review_prior_identifiers() -> tuple[str, str, str]:
    """The review prior's raw, canonical, and Git identities."""
    raw = REVIEW_PRIOR_PATH.read_bytes()
    canonical = raw.replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(canonical).hexdigest(),
        blob,
    )


(
    _prior_raw_before,
    _prior_content_before,
    _prior_blob_before,
) = _review_prior_identifiers()
assert _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256, _prior_content_before
assert _prior_blob_before == REVIEW_PRIOR_BLOB, _prior_blob_before

_LIVE_ORACLE_BYTES_BEFORE = LIVE_ORACLE_PATH.read_bytes()

PRIOR = load_accepted_inputs(REVIEW_PRIOR_PATH)
assert [b.batch_id for b in PRIOR.batches] == REVIEW_PRIOR_BATCH_IDS, PRIOR.batches
assert {a.batch_id for a in PRIOR.acceptances} == set(REVIEW_PRIOR_BATCH_IDS)
assert (
    PRIOR.oracle.schema_version == REVIEW_PRIOR_SCHEMA_VERSION
), PRIOR.oracle.schema_version
assert PRIOR.oracle.schema_hash == REVIEW_PRIOR_SCHEMA_HASH, PRIOR.oracle.schema_hash
assert (PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash) != SCHEMA
assert len(PRIOR.oracle.representation.records) == REVIEW_PRIOR_RECORDS
assert len(PRIOR.oracle.spans) == REVIEW_PRIOR_SPANS

#: **One registered crossing.** The prior is anchored at schema 7; this batch
#: proposes under schema 8, which S-2 required. The step is looked up in the
#: registry rather than named, and `verify_lift_path` re-proves the accepted
#: content element by element under the new contract instead of asserting it.
#: Accepted bytes are never restamped: the frozen prior still declares schema 7
#: after this run, and is asserted unchanged below.
STEPS = lift_path((PRIOR.oracle.schema_version, PRIOR.oracle.schema_hash), SCHEMA)
LIFT_RECORDS = verify_lift_path(STEPS, PRIOR.oracle.representation)
assert [r.lift_id for r in LIFT_RECORDS] == ["5d-lift-schema-7-to-8"], LIFT_RECORDS
SUCCESSION = {
    "prior_schema": PRIOR.oracle.schema_version,
    "batch_schema": SCHEMA[0],
    "lift_required": True,
    "steps": [r.lift_id for r in LIFT_RECORDS],
    "verified_collections": [list(r.verified_collections) for r in LIFT_RECORDS],
    "note": (
        "the accepted prior is anchored at 5d-representation-schema-7 and this "
        "batch proposes under 5d-representation-schema-8, which schema stop "
        "S-2 required. Exactly one registered transition separates them and it "
        "is exercised here rather than described. The transition adds a fact "
        "family and a vocabulary; it adds no field to an accepted family, no "
        "ownership form, no nullable field and no required field, so every "
        "accepted fact key, component key and provenance coordinate has the "
        "same canonical form under both contracts."
    ),
}

MERGED = _merge_representation(PRIOR.oracle.representation, DRAFT)
MERGED_LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(PRIOR.oracle.spans) + tuple(spans),
    batches=(),
    acceptances=(),
)
merged_findings = list(validate_representation(MERGED, MERGED_LEDGER, CORPUS))

# --- Reference scope, enumerated exactly ------------------------------------
#
# What this batch cites, what it resolves, and what is still missing after the
# merge. The last column is the honest one and it is not empty.
_batch_records = {rec.semantic_key for rec in records}
_prior_records = {r.semantic_key for r in PRIOR.oracle.representation.records}
_cross_batch = sorted(
    {
        (r.from_record_key, r.target_record_key)
        for r in references
        if r.target_record_key not in _batch_records
    }
)
assert _cross_batch == [
    (FRI, INFL),
    (HOS, INFL),
    (IND, INFL),
    (ATT, INFL),
], _cross_batch
#: Every cross-batch citation this batch makes resolves into the accepted prior.
assert all(t in _prior_records for _f, t in _cross_batch), _cross_batch

#: What the prior could not resolve before this batch, and what it can after.
_prior_missing = sorted(
    {
        r.target_record_key
        for r in PRIOR.oracle.representation.references
        if r.target_record_key not in _prior_records
    }
)
_merged_records = {r.semantic_key for r in MERGED.records}
_merged_missing = sorted(
    {
        r.target_record_key
        for r in MERGED.references
        if r.target_record_key not in _merged_records
    }
)
assert _prior_missing == [
    "attitude.friendly",
    "attitude.hostile",
    "attitude.indifferent",
    "glossary.concentration",
    "glossary.speed",
], _prior_missing
assert _merged_missing == ["glossary.concentration", "glossary.speed"], _merged_missing

REFERENCE_SCOPE = {
    "references_emitted": len(references),
    "record_owned": sum(
        1 for r in references if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "targets_defined_by_this_batch": sorted(
        {
            r.target_record_key
            for r in references
            if r.target_record_key in _batch_records
        }
    ),
    "cross_batch_citations": [f"{f} -> {t}" for f, t in _cross_batch],
    "cross_batch_citations_all_resolve_into_the_accepted_prior": True,
    "unresolved_targets_before_this_batch": _prior_missing,
    "unresolved_targets_after_the_merge": _merged_missing,
    "resolved_by_this_batch": sorted(set(_prior_missing) - set(_merged_missing)),
    "publishable_alone": False,
    "note": (
        "This batch adds no unresolved citation of its own: all four of its "
        "cross-batch references target action.influence, which accepted "
        "authority already carries. It resolves three of the prior's five "
        "unresolved targets as a CONSEQUENCE of representing a complete source "
        "class. glossary.concentration and glossary.speed are untagged entries "
        "in other source groups and remain unresolved, so the merged validator "
        "still reports exactly two. Schema stop S-2 leaves no UNRESOLVED span: "
        "schema 8 closes it with a typed family. Nothing here is accepted, "
        "activated or published, and the publication gate is not executed by "
        "this run at all."
    ),
}

#: Both columns checked against a count DERIVED from the drafts rather than a
#: number chosen in advance: the validator reports one finding per unresolved
#: reference, not one per unresolved target, so the standalone column is this
#: batch's four See-also citations of `action.influence` and the merged column
#: is however many prior references still point at the two glossary entries no
#: accepted batch defines.
UNRESOLVED_FINDINGS = {}
for _column, _found, _refs, _known in (
    ("standalone", standalone, references, _batch_records),
    ("merged", merged_findings, MERGED.references, _merged_records),
):
    _dangling = [r for r in _refs if r.target_record_key not in _known]
    assert len(_found) == len(_dangling), (_column, len(_found), len(_dangling))
    for _t in {r.target_record_key for r in _dangling}:
        assert any(_t in f for f in _found), (_column, _t, _found)
    UNRESOLVED_FINDINGS[_column] = {
        "findings": len(_found),
        "distinct_targets": sorted({r.target_record_key for r in _dangling}),
        "citations_per_target": {
            _t: sum(1 for r in _dangling if r.target_record_key == _t)
            for _t in sorted({r.target_record_key for r in _dangling})
        },
    }
assert UNRESOLVED_FINDINGS["standalone"]["distinct_targets"] == [
    INFL
], UNRESOLVED_FINDINGS
assert (
    UNRESOLVED_FINDINGS["merged"]["distinct_targets"] == _merged_missing
), UNRESOLVED_FINDINGS
REFERENCE_SCOPE["validator_findings"] = UNRESOLVED_FINDINGS

# --- Disjointness and zero movement, over all six collections ---------------
SIX = (
    "records",
    "components",
    "prose_bindings",
    "relationships",
    "references",
    "provenance",
)


def _identity(collection: str, element: object) -> object:
    if collection == "records":
        return element.semantic_key
    if collection == "components":
        return (element.record_key, element.semantic_key)
    if collection == "prose_bindings":
        return prose_binding_target_key(element)
    if collection == "references":
        return reference_target_key(element)
    if collection == "relationships":
        return (element.from_record_key, element.to_record_key, element.kind.value)
    return (
        element.target_kind.value,
        element.target_key,
        element.span_id,
        element.role.value,
    )


OVERLAP = {}
ZERO_MOVEMENT = {}
for _coll in SIX:
    _prior_c = getattr(PRIOR.oracle.representation, _coll)
    _new = getattr(DRAFT, _coll)
    _merged_c = getattr(MERGED, _coll)
    OVERLAP[_coll] = sorted(
        str(k)
        for k in (
            {_identity(_coll, e) for e in _prior_c}
            & {_identity(_coll, e) for e in _new}
        )
    )
    _prior_payload = representation_payload(PRIOR.oracle.representation)[_coll]
    _new_payload = representation_payload(DRAFT)[_coll]
    _merged_payload = representation_payload(MERGED)[_coll]
    ZERO_MOVEMENT[_coll] = {
        "prior_elements": len(_prior_c),
        "prefix_is_byte_identical": _merged_c[: len(_prior_c)] == _prior_c,
        "prior_payloads_absent_from_the_merge": [
            str(x) for x in _prior_payload if x not in _merged_payload
        ],
        "payload_element_count": {
            "prior": len(_prior_payload),
            "new": len(_new_payload),
            "merged": len(_merged_payload),
            "sums": len(_merged_payload) == len(_prior_payload) + len(_new_payload),
        },
    }
    assert not OVERLAP[_coll], (_coll, OVERLAP[_coll])
    assert ZERO_MOVEMENT[_coll]["prefix_is_byte_identical"], _coll
    assert not ZERO_MOVEMENT[_coll]["prior_payloads_absent_from_the_merge"], _coll
    assert ZERO_MOVEMENT[_coll]["payload_element_count"]["sums"], _coll

prior_spans = {s.span_id for s in PRIOR.oracle.spans}
prior_leaves = {s.leaf_id for s in PRIOR.oracle.spans}
DISJOINT = {
    "span_overlap": sorted(prior_spans & {s.span_id for s in spans}),
    "leaf_overlap": sorted(prior_leaves & set(touched)),
    "collection_overlap": OVERLAP,
    "prior_spans_retained": len(prior_spans),
    "zero_movement": ZERO_MOVEMENT,
}
assert not DISJOINT["span_overlap"], DISJOINT["span_overlap"]
assert not DISJOINT["leaf_overlap"], DISJOINT["leaf_overlap"]

# --- Schema legality at every authority-bearing seam ------------------------
STRUCTURAL = [
    *representation_draft_violations(DRAFT),
    *held_structure_violations(DRAFT),
]
_component_rules: list[str] = []
for _c in components:
    _tag = f"{_c.record_key}/{_c.semantic_key}"
    _component_rules.extend(
        component_damage_composition_violations(_c.facts, _c.options, _tag)
    )
    _component_rules.extend(
        component_roll_outcome_violations(
            _c.facts, _c.options, _c.applies_when, _tag, _c.fact_qualifiers
        )
    )
    _component_rules.extend(option_set_violations(_c.facts, _c.options, _tag))

_WIRE_OUT = representation_payload(DRAFT)
_WIRE_BACK = representation_payload(_representation(json.loads(json.dumps(_WIRE_OUT))))
WIRE_ROUND_TRIP = _WIRE_OUT == _WIRE_BACK
assert WIRE_ROUND_TRIP, "the emitted draft does not survive the wire"

SEAMS = {
    "build-time draft shape (representation_draft_violations)": len(
        representation_draft_violations(DRAFT)
    ),
    "held authority shape (held_structure_violations)": len(
        held_structure_violations(DRAFT)
    ),
    "component rules (damage + roll outcome + option sets)": len(_component_rules),
    "representation gate, standalone (validate_representation)": len(standalone),
    "representation gate, merged with the accepted three-batch prior": len(
        merged_findings
    ),
    "committed-loader round trip (representation_payload -> _representation)": (
        0 if WIRE_ROUND_TRIP else 1
    ),
    "partition accounting (validate_partition)": len(partition),
    "reason codes (validate_reason_codes)": len(reason_codes),
}
#: Derived from the reference scope above, not pinned: the only findings either
#: gate is permitted to report are unresolved reference targets, and exactly as
#: many as there are dangling citations.
_EXPECTED_NONZERO = {
    "representation gate, standalone (validate_representation)": (
        UNRESOLVED_FINDINGS["standalone"]["findings"]
    ),
    "representation gate, merged with the accepted three-batch prior": (
        UNRESOLVED_FINDINGS["merged"]["findings"]
    ),
}
for _seam, _n in _EXPECTED_NONZERO.items():
    assert SEAMS[_seam] == _n, (SEAMS, _seam)
assert all(v == 0 for k, v in SEAMS.items() if k not in _EXPECTED_NONZERO), SEAMS
assert not _component_rules, _component_rules

# --- The consumer boundary: what a reader of this authority actually sees ----
#
# `_base_records` is the function every consumer of mechanical authority goes
# through. It is applied to the merged candidate IN MEMORY — nothing is
# persisted, published or activated — and the values are read back off the
# resulting objects rather than off this run's own dictionaries.
CANDIDATE = ProjectionCandidate(
    binding=BINDING,
    classification=MERGED_LEDGER,
    representation=MERGED,
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
)
_span_text = {a["span_id"]: a["text"] for a in audit}
BASE = _base_records(CANDIDATE)
for _k in (ATT, FRI, HOS, IND):
    assert _k in BASE, sorted(BASE)

CONSUMER_VIEW: dict[str, object] = {
    _k: {
        "kind": BASE[_k].kind.value,
        "component_keys": sorted(c.semantic_key for c in BASE[_k].components),
        "span_ids": len(BASE[_k].span_ids),
    }
    for _k in (ATT, FRI, HOS, IND)
}

#: The three attitude records the accepted actions-1 authority cites are now
#: present in the projection, which is the whole consumer-visible effect of
#: this batch. References live on the representation rather than the effective
#: record, so the reachability claim is made where the citations actually are
#: and checked against what the projection assembles.
_influence_targets = sorted(
    {r.target_record_key for r in MERGED.references if r.from_record_key == INFL}
)
assert _influence_targets == [FRI, HOS, IND], _influence_targets
assert all(t in BASE for t in _influence_targets), _influence_targets
CONSUMER_VIEW["action.influence -> attitudes now resolve"] = {
    "cited": _influence_targets,
    "all_assembled_by_the_projection": True,
    "note": (
        "accepted actions-1 authority cites all three by name; before this "
        "batch none of them existed as a record, so the citation dangled."
    ),
}

#: The polarity a consumer reads back off the two typed components, taken off
#: the assembled effective view rather than off this run's own objects.
#: Advantage and Disadvantage on the same roll spec is the entire mechanical
#: content of the batch, so it is asserted, not narrated.
_polarity: dict[str, dict] = {}
for _k, _ck in ((FRI, "influence_advantage"), (HOS, "influence_disadvantage")):
    _comp = next(c for c in BASE[_k].components if c.semantic_key == _ck)
    _efacts = list(_comp.facts)
    assert len(_efacts) == 1, (_k, _efacts)
    _f = _efacts[0].fact
    _polarity[_k] = {
        "component": _ck,
        "handling": _comp.handling.value,
        "irreducibility_reason_code": _comp.irreducibility_reason_code,
        "state": _f.state.value,
        "roll_actor": _f.roll.actor.value,
        "roll_context": _f.roll.context.value,
        "roll_ability": _f.roll.ability,
        "fact_span_ids": list(_efacts[0].span_ids),
        "fact_span_text": [_span_text.get(x, "<prior>") for x in _efacts[0].span_ids],
        "governing_prose_extents": len(_comp.governing_prose),
    }
assert _polarity[FRI]["state"] == "advantage", _polarity
assert _polarity[HOS]["state"] == "disadvantage", _polarity
assert _polarity[FRI]["roll_actor"] == _polarity[HOS]["roll_actor"] == "against_subject"
assert (
    _polarity[FRI]["roll_context"] == _polarity[HOS]["roll_context"] == "ability_check"
)
assert _polarity[FRI]["roll_ability"] is _polarity[HOS]["roll_ability"] is None
#: Each typed fact carries exactly the span that states it, and each component
#: carries exactly the prose extent that says which check it applies to.
for _k in (FRI, HOS):
    assert len(_polarity[_k]["fact_span_ids"]) == 1, _polarity
    assert "You have" in _polarity[_k]["fact_span_text"][0], _polarity
    assert _polarity[_k]["governing_prose_extents"] == 1, _polarity
CONSUMER_VIEW["polarity_read_back_off_the_projection"] = _polarity

#: The schema-8 family read back off the same projection. This is the whole
#: point of the extension: a consumer asking what a monster's attitude is
#: absent other specification gets a closed vocabulary member off the typed
#: component, not prose to parse and not an inference off the record key.
_default_comp = next(
    c for c in BASE[IND].components if c.semantic_key == "default_attitude"
)
_default_efacts = list(_default_comp.facts)
assert len(_default_efacts) == 1, _default_efacts
_default_fact = _default_efacts[0].fact
assert isinstance(_default_fact, DefaultAttitudeFact), type(_default_fact)
assert _default_fact.attitude is Attitude.INDIFFERENT, _default_fact
assert _default_comp.handling is ComponentHandling.STRUCTURED, _default_comp
assert _default_comp.irreducibility_reason_code is None, _default_comp
assert len(_default_comp.governing_prose) == 0, _default_comp
assert len(_default_efacts[0].span_ids) == 1, _default_efacts
CONSUMER_VIEW["default_attitude_read_back_off_the_projection"] = {
    "record": IND,
    "component": "default_attitude",
    "handling": _default_comp.handling.value,
    "fact_family": _default_fact.FAMILY.value,
    "attitude": _default_fact.attitude.value,
    "fact_key": fact_key(_default_fact),
    "fact_span_text": [
        _span_text.get(x, "<prior>") for x in _default_efacts[0].span_ids
    ],
    "governing_prose_extents": len(_default_comp.governing_prose),
    "note": (
        "the value is stated by the fact, not inferred from the record key "
        "attitude.indifferent, and it is a default rather than an attitude any "
        "creature currently holds - the projection models no runtime state."
    ),
}

#: The accepted `condition.charmed` shape this batch reuses, read off the same
#: projection so "same shape, flipped polarity" is comparable rather than
#: asserted.
_charmed = next(
    c
    for c in BASE["condition.charmed"].components
    if c.semantic_key == "social_advantage"
)
_charmed_fact = next(iter(_charmed.facts)).fact
PRECEDENT = {
    "accepted": {
        "component": "condition.charmed/social_advantage",
        "handling": _charmed.handling.value,
        "state": _charmed_fact.state.value,
        "roll_actor": _charmed_fact.roll.actor.value,
        "roll_context": _charmed_fact.roll.context.value,
        "irreducibility_reason_code": _charmed.irreducibility_reason_code,
    },
    "this_batch": _polarity,
    "identical_axes": [
        "handling",
        "roll_actor",
        "roll_context",
        "roll.ability is None",
        "irreducibility_reason_code",
    ],
    "differing_axis": "state (advantage vs disadvantage)",
    "note": (
        "RollActor's own docstring names this case: the charmer's actor "
        "restriction 'is applicability prose on a MIXED component, and "
        "admitting a member for it would have widened the union on "
        "speculation'. Friendly and Hostile are the same sentence with the "
        "polarity flipped, so they take the same shape and widen nothing."
    ),
}
assert PRECEDENT["accepted"]["roll_actor"] == _polarity[FRI]["roll_actor"], PRECEDENT
assert (
    PRECEDENT["accepted"]["roll_context"] == _polarity[FRI]["roll_context"]
), PRECEDENT
assert PRECEDENT["accepted"]["handling"] == _polarity[FRI]["handling"], PRECEDENT
assert PRECEDENT["accepted"]["irreducibility_reason_code"] == CTX, PRECEDENT
assert _charmed_fact.roll.ability is None, PRECEDENT

# ---------------------------------------------------------------------------
# Proposal, identity, counts
# ---------------------------------------------------------------------------

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=SCHEMA[0],
    schema_hash=SCHEMA[1],
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin=(
        f"{ORIGIN} (CRD Issue 5d batch attitudes-1, representation schema 8)"
    ),
)
payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)
#: No pinned expectation: this is a fresh proposal, so its identity is reported
#: for review rather than asserted against a value chosen in advance.
assert ident != REVIEW_PRIOR_IDENTITY, "the proposal is not the accepted prior"

counts: dict[str, int] = defaultdict(int)
for s in spans:
    counts[s.disposition.value] += 1
per_record: dict[str, dict] = defaultdict(lambda: {"leaves": set(), "spans": 0})
for a in audit:
    rec = per_record[a["record"]]
    rec["leaves"].add(a["leaf"])
    rec["spans"] += 1

COUNTS = {
    "records": len(records),
    "represented_leaves": len(touched),
    "policy_exclusions": len(POLICY_EXCLUDED),
    "spans": len(spans),
    "substantive": counts["substantive"],
    "supporting_authority": counts["supporting_authority"],
    "non_mechanical": counts["non_mechanical"],
    "unresolved": counts["unresolved"],
    "components": len(components),
    "components_structured": sum(
        1 for c in components if c.handling is ComponentHandling.STRUCTURED
    ),
    "components_mixed": sum(
        1 for c in components if c.handling is ComponentHandling.MIXED
    ),
    "components_prose_bound": sum(
        1 for c in components if c.handling is ComponentHandling.PROSE_BOUND
    ),
    "facts": sum(len(c.facts) for c in components),
    "prose_bindings": len(prose_bindings),
    "references": len(references),
    "record_owned_references": sum(
        1 for r in references if r.from_component_key == RECORD_OWNED_REFERENCE
    ),
    "relationships": 0,
    "provenance_edges": len(provenance),
    "obligations": len(OBLIGATION_IDS),
}
assert COUNTS["spans"] == len(audit) == len(proposed) == 24, COUNTS
assert COUNTS["provenance_edges"] == len(spans) - COUNTS["unresolved"], COUNTS
assert (
    COUNTS["substantive"]
    + COUNTS["supporting_authority"]
    + COUNTS["non_mechanical"]
    + COUNTS["unresolved"]
    == COUNTS["spans"]
), COUNTS
assert COUNTS["references"] == 7, COUNTS
assert COUNTS["record_owned_references"] == 7, COUNTS
assert COUNTS["facts"] == 3 and COUNTS["prose_bindings"] == 2, COUNTS
assert COUNTS["components"] == 3, COUNTS
assert COUNTS["components_structured"] == 1, COUNTS
assert COUNTS["components_mixed"] == 2, COUNTS
assert COUNTS["components_prose_bound"] == 0, COUNTS
assert COUNTS["unresolved"] == 0, COUNTS
assert COUNTS["substantive"] == 5, COUNTS

COUNT_DERIVATION = {
    "records": (
        "one per source entry in the boundary: the Attitude umbrella plus the "
        "three [Attitude] entries"
    ),
    "represented_leaves": (
        "distinct leaf ids the spans cover; all 16 of the boundary's 16 "
        "container leaves, because this boundary has no policy exclusion"
    ),
    "spans": (
        "the partition cells: 4 leaves x 4 records, cut where an element's "
        "claim starts or stops"
    ),
    "references": (
        "the umbrella's four See-also citations plus one per entry; every one "
        "record-owned, because no component of this batch is the thing doing "
        "the citing"
    ),
    "components": (
        "three: Friendly's and Hostile's influence modifiers, MIXED, plus "
        "Indifferent's default_attitude, STRUCTURED. The umbrella holds none, "
        "which is glossary.hazard's accepted shape"
    ),
    "unresolved": (
        "none. Schema stop S-2 was the only candidate and schema 8 closes it "
        "with a typed family, so no span is emitted UNRESOLVED"
    ),
}

# ---------------------------------------------------------------------------
# Audit document
# ---------------------------------------------------------------------------

AUDIT_DOC: dict[str, object] = {
    "_": (
        "DISPOSABLE REVIEW MATERIAL for CRD Issue 5d batch attitudes-1. Emitted "
        "by "
        + ORIGIN
        + ". This run accepts nothing, publishes nothing, activates nothing, "
        "retires nothing, writes no database and never executes the publication "
        "gate. It is material for semantic review."
    ),
    "proposal_identity": ident,
    "batch_selection": {
        "batch_id": "attitudes-1",
        "chosen_by": "complete source membership",
        "rule": (
            "the shape the three accepted batches established: a source-tagged "
            "entry class plus the untagged umbrella glossary rule that defines "
            "the tag. conditions-1 = 15 + Condition; hazards-1 = 5 + Hazard; "
            "actions-1 = 12 + Action; attitudes-1 = 3 + Attitude."
        ),
        "membership": {lab: RECORD_KEY[lab] for lab in BATCH_LABELS},
        "tag_classes_in_the_source": {t: len(v) for t, v in TAG_CLASSES.items()},
        "accepted_classes": ["Condition", "Hazard", "Action"],
        "this_class": "Attitude",
        "remaining_unaccepted_class": {
            "tag": "Area of Effect",
            "entries": TAG_CLASSES["Area of Effect"],
            "why_not_this_batch": (
                "it needs an entire spatial-geometry family — point of origin, "
                "shape dimensions, origin inclusion, line of effect blocked by "
                "Total Cover — that no current fact carries, and that sits "
                "against the settled 'no general rules engine' boundary. Next "
                "candidate, not this one."
            ),
        },
        "relationship_to_the_five_missing_targets": (
            "That three of accepted authority's five unresolved reference "
            "targets are attitude.friendly, attitude.hostile and "
            "attitude.indifferent is a CONSEQUENCE of representing a complete "
            "source class, not the reason for choosing it. The batch was not "
            "assembled to close a list: glossary.concentration and "
            "glossary.speed are untagged entries in other source groups and "
            "stay unresolved after this batch."
        ),
    },
    "representation_schema": {"version": SCHEMA[0], "hash": SCHEMA[1]},
    "schema_extension": {
        "extends_the_schema": True,
        "from_schema": REVIEW_PRIOR_SCHEMA_VERSION,
        "to_schema": SCHEMA[0],
        "new_vocabularies": {"Attitude": [m.value for m in Attitude]},
        "new_fact_families": ["default_attitude"],
        "registered_transitions_touched": ["5d-lift-schema-7-to-8"],
        "accepted_families_changed": [],
        "note": (
            "One extension, and only what schema stop S-2 requires: the fact "
            "family default_attitude over the closed vocabulary Attitude, "
            "admitted at its printed closure. Every other mechanic in this "
            "batch has an admissible shape under schema 7 as accepted. No "
            "field is added to, made required on, or made nullable on any "
            "accepted family and no ownership form changes, which is what "
            "makes the crossing a re-declaration rather than a rewrite."
        ),
    },
    "semantic_policy": {
        "version": SEMANTIC_POLICY_VERSION,
        "hash": semantic_policy_hash(),
    },
    "release_binding": {
        "package_uuid": BINDING.package_uuid,
        "release_version": BINDING.release_version,
        "authoritative_source_hash": BINDING.authoritative_source_hash,
        "transform_config_hash": BINDING.transform_config_hash,
        "bundle_root_hash": BINDING.bundle_root_hash,
        "persisted_corpus_digest": BINDING.persisted_corpus_digest,
        "derivation": (
            "five of six values re-derived from the committed PDF by the 5c "
            "pipeline and asserted; persisted_corpus_digest is a function of "
            "persisted rows and verified vector state, so it is carried from "
            "the published CRD Issue 5c release record and disclosed as such."
        ),
    },
    "boundary": {
        "derived_from": (
            "'[Attitude]'-tagged entries under Rules Definitions, plus the "
            "untagged 'Attitude' umbrella, checked against the names the "
            "umbrella's own See-also prints"
        ),
        "labels": BATCH_LABELS,
        "printed_pages": sorted({LEAF_BY_ID[lid].page_index + 1 for lid in touched}),
        "policy_exclusions": POLICY_EXCLUDED,
        "canaries": {
            k: {"derived": v[0], "expected": v[1]} for k, v in CANARIES.items()
        },
    },
    "counts": COUNTS,
    "count_derivation": COUNT_DERIVATION,
    "per_record": {
        r: {"leaves": len(d["leaves"]), "spans": d["spans"]}
        for r, d in sorted(per_record.items())
    },
    "record_shapes": {
        rec.semantic_key: {
            "kind": rec.kind.value,
            "components": sorted(
                c.semantic_key for c in components if c.record_key == rec.semantic_key
            ),
            "prose_bindings": sum(
                1 for b in prose_bindings if b.record_key == rec.semantic_key
            ),
            "references": sum(
                1 for r in references if r.from_record_key == rec.semantic_key
            ),
        }
        for rec in records
    },
    "validation": {
        "seams_reporting_findings": SEAMS,
        "expected_nonzero": _EXPECTED_NONZERO,
        "wire_round_trip": WIRE_ROUND_TRIP,
        "partition": partition,
        "reason_codes": reason_codes,
        "structural": STRUCTURAL,
        "component_rules": _component_rules,
        "standalone_findings": standalone,
        "merged_findings": merged_findings,
    },
    "classification_partitions": {
        lid: {
            "record": next(a["record"] for a in audit if a["leaf"] == lid),
            "printed_page": LEAF_BY_ID[lid].page_index + 1,
            "content": leaf_content[lid],
            "cells": PARTITIONS[lid],
        }
        for lid in touched
    },
    "reference_scope": REFERENCE_SCOPE,
    "reference_siting": {
        "rule": (
            "a reference is emitted where the source cites a record as a "
            "defined term, not at every place it says the word"
        ),
        "accepted_precedent": [
            "glossary.hazard emits its five references from its quoted See-also "
            "list; 'A hazard is an environmental danger.' is supporting authority",
            "action.dash emits 'Speed' from its See-also leaf while its body's "
            "other mentions of Speed carry facts",
            "glossary.condition and glossary.action emit from their printed "
            "enumerations, the only place they cite their members",
        ],
        "applied_here": (
            "glossary.attitude's four references come from its See-also leaf; "
            "its body sentence is the record's own definitional framing. "
            "Siting them at both places would also have collided: "
            "reference_target_key keys on source_text and the term is spelled "
            "the same in both leaves."
        ),
        "reference_keys_are_distinct": len(
            {reference_target_key(r) for r in references}
        )
        == len(references),
    },
    "schema_stops": SCHEMA_STOPS,
    "typed_prose_dispositions": {
        "typed": [
            {
                "record": FRI,
                "component": "influence_advantage",
                "fact": fact_key(FRIENDLY_ADV),
                "text": "You have Advantage on an ability check",
            },
            {
                "record": HOS,
                "component": "influence_disadvantage",
                "fact": fact_key(HOSTILE_DIS),
                "text": "You have Disadvantage on an ability check",
            },
            {
                "record": IND,
                "component": "default_attitude",
                "fact": fact_key(DEFAULT_ATTITUDE),
                "text": "Indifferent is the default attitude of a monster.",
                "schema": SCHEMA[0],
                "why": (
                    "schema stop S-2, closed by the schema-8 family rather "
                    "than left UNRESOLVED or misfiled under an irreducibility "
                    "reason none of whose six codes is true of it."
                ),
            },
        ],
        "prose_bound": [
            {
                "record": b.record_key,
                "component": b.component_key,
                "reason": b.irreducibility_reason_code,
                "text": _span_text[b.span_id],
                "why": (
                    "which ability check the modifier applies to — the one made "
                    "to influence this creature — ranges over fiction the "
                    "projection cannot enumerate. Widening RollContext or "
                    "RollActor for it is what RollActor's docstring explicitly "
                    "declined to do for the identical Charmed clause."
                ),
            }
            for b in prose_bindings
        ],
        "supporting_authority": [
            {"record": a["record"], "text": a["text"]}
            for a in audit
            if a["kind"] == "R"
        ],
        "unresolved": [
            {"record": a["record"], "text": a["text"], "schema_stop": "S-2"}
            for a in audit
            if a["kind"] == "U"
        ],
    },
    "precedent": PRECEDENT,
    "consumer_boundary_proofs": CONSUMER_VIEW,
    "schema_succession": SUCCESSION,
    "accepted_prior": {
        "path": REVIEW_PRIOR_PATH.relative_to(REPO).as_posix(),
        "content_sha256": _prior_content_before,
        "blob": _prior_blob_before,
        "identity": REVIEW_PRIOR_IDENTITY,
        "batch_ids": REVIEW_PRIOR_BATCH_IDS,
        "records": REVIEW_PRIOR_RECORDS,
        "spans": REVIEW_PRIOR_SPANS,
        "schema_version": PRIOR.oracle.schema_version,
        "read_only": True,
    },
    "disjointness_from_the_accepted_prior": DISJOINT,
    "obligation_closure": OBLIGATION_CLOSURE,
    "obligation_accounting": OBLIGATION_ACCOUNTING,
    "evidence_classes": [
        {
            "class": "source extraction and partition reconstruction",
            "executed_here": True,
            "strength": (
                "strong for coverage and span boundaries; says nothing about "
                "whether the meaning assigned to a span is right — that is what "
                "semantic review is for"
            ),
        },
        {
            "class": "structural validation",
            "executed_here": True,
            "strength": (
                "the repository's own checkers over the emitted draft and over "
                "the merge acceptance would validate. Zero findings is "
                "explicitly insufficient: these judge shape, not fidelity"
            ),
        },
        {
            "class": "consumer projection assertion",
            "executed_here": True,
            "strength": (
                "_base_records is applied to the merged candidate in memory and "
                "values are read back off those objects. Nothing is persisted"
            ),
        },
        {
            "class": "sibling sweep for a new fact family",
            "executed_here": True,
            "strength": (
                "measured over all represented leaves of the bound source, not "
                "recalled: one match, one section"
            ),
        },
        {
            "class": "publication gate",
            "executed_here": False,
            "strength": (
                "NOT run. There is no persisted projection to run it over, and "
                "this generator must not create one"
            ),
        },
        {
            "class": "acceptance",
            "executed_here": False,
            "strength": (
                "NOT run. accept_proposal is never called; the live oracle is "
                "read as a mutation sentinel only"
            ),
        },
    ],
    "review_disposition": {
        "open_schema_stops": [s["id"] for s in SCHEMA_STOPS if s["status"] == "open"],
        "residues": [
            "no UNRESOLVED span remains; S-2 is closed by schema 8 and the "
            "registered transition 5d-lift-schema-7-to-8 is exercised above",
            "glossary.concentration and glossary.speed remain unresolved after "
            "the merge; they belong to a later glossary batch",
        ],
        "requires_owner_authorization_before": [
            "any acceptance of this batch into committed authority",
            "any acceptance is also what would carry the accepted prior across "
            "5d-lift-schema-7-to-8; this run proves the crossing and performs "
            "none of it",
        ],
    },
    "repository_inputs": INPUT_PATHS,
    "spans": audit,
}
assert AUDIT_DOC["proposal_identity"] == ident
assert AUDIT_DOC["review_disposition"]["open_schema_stops"] == [], AUDIT_DOC[
    "review_disposition"
]


def _write_artifact(name: str, document: object, *, sort_keys: bool = False) -> bytes:
    """Write one artifact as UTF-8 with **LF** newlines, and return its bytes.

    ``newline="\n"`` is the whole point. Left to the default, Python translates
    ``\n`` to ``os.linesep`` on write, so the same generator emitted CRLF on
    Windows and LF on Linux - two files, two digests, one computation.
    """
    text = json.dumps(document, indent=1, sort_keys=sort_keys, ensure_ascii=False)
    path = OUT / name
    path.write_text(text, encoding="utf-8", newline="\n")
    written = path.read_bytes()
    assert b"\r\n" not in written, f"{name} was written with CRLF"
    assert b"\r" not in written, f"{name} contains a carriage return"
    return written


_proposal_bytes = _write_artifact(PROPOSAL_FILE, payload, sort_keys=True)

DETERMINISM_SECTION = {
    "procedure": (
        "The parent writes both artifacts in their final form, then re-executes "
        "this generator in a separate process, then compares the final bytes of "
        "both files and asserts the child minted the same proposal identity."
    ),
    "newlines": "LF, written explicitly, on every platform",
    "proposal_sha256": hashlib.sha256(_proposal_bytes).hexdigest(),
    "audit_self_hash": (
        "omitted: an audit cannot state its own final digest without changing "
        "the bytes that digest describes. The run asserts instead that the "
        "parent's and the child's final audits are byte-identical, and reports "
        "the resulting digest to stdout."
    ),
}

_, _prior_content_after, _prior_blob_after = _review_prior_identifiers()
assert _prior_content_after == _prior_content_before, "the review prior changed"
assert _prior_blob_after == _prior_blob_before, "the review prior's blob id moved"
AUDIT_DOC["accepted_prior"]["content_sha256_after"] = _prior_content_after  # type: ignore[index]
AUDIT_DOC["accepted_prior"]["unchanged"] = (  # type: ignore[index]
    _prior_content_after == _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256
    and _prior_blob_after == REVIEW_PRIOR_BLOB
)

AUDIT_DOC["determinism"] = DETERMINISM_SECTION
_audit_bytes = _write_artifact(AUDIT_FILE, AUDIT_DOC)

# Retained evidence, the review prior, and the live oracle must all be
# untouched by this run.
for _n, _before in _RETAINED_BEFORE.items():
    _after = hashlib.sha256((OUT / _n).read_bytes()).hexdigest()
    assert _after == _before, f"retained evidence {_n} changed"
_raw_end, _prior_end, _blob_end = _review_prior_identifiers()
assert _prior_end == _prior_content_before == REVIEW_PRIOR_CONTENT_SHA256, _prior_end
assert _blob_end == _prior_blob_before == REVIEW_PRIOR_BLOB, _blob_end
assert _raw_end == _prior_raw_before, "the review prior's bytes changed"
assert AUDIT_DOC["accepted_prior"]["unchanged"], AUDIT_DOC["accepted_prior"]  # type: ignore[index]

LIVE_ORACLE_UNCHANGED = LIVE_ORACLE_PATH.read_bytes() == _LIVE_ORACLE_BYTES_BEFORE
assert LIVE_ORACLE_UNCHANGED, "this run modified the live accepted-authority oracle"

# ---------------------------------------------------------------------------
# Determinism: a clean rerun must reproduce identical bytes and identity
# ---------------------------------------------------------------------------
RERUN = os.environ.get("ATTITUDES1_RERUN") == "1"
FINAL_SHA256 = {
    PROPOSAL_FILE: hashlib.sha256(_proposal_bytes).hexdigest(),
    AUDIT_FILE: hashlib.sha256(_audit_bytes).hexdigest(),
}
DETERMINISTIC: bool | None = None
if not RERUN:
    _child = subprocess.run(
        [sys.executable, str(Path(__file__).resolve())],
        env={**os.environ, "ATTITUDES1_RERUN": "1"},
        capture_output=True,
        text=True,
    )
    assert _child.returncode == 0, _child.stderr[-4000:]
    _after_bytes = {
        n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in sorted(WRITES)
    }
    DETERMINISTIC = _after_bytes == FINAL_SHA256
    assert DETERMINISTIC, (FINAL_SHA256, _after_bytes)
    assert ident in _child.stdout, "the rerun minted a different proposal identity"
    for _name in sorted(WRITES):
        assert b"\r" not in (OUT / _name).read_bytes(), f"{_name} came back with CR"

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

# Absolute paths go to stdout, never into an artifact.
print(f"repo root      {REPO}")
print(f"imported from  {IMPORTED_FROM}")
print(f"source pdf     {SOURCE_PDF}")
print(f"review prior   {REVIEW_PRIOR_PATH}")
print(f"live oracle    {LIVE_ORACLE_PATH}  (sentinel only, not an input)")
print(f"output dir     {OUT}")
print(f"schema         {SCHEMA[0]} / {SCHEMA[1]}")
print(f"policy         {SEMANTIC_POLICY_VERSION} / {semantic_policy_hash()}")
print(f"identity       {ident}")
print()
print(f"batch          attitudes-1: {', '.join(BATCH_LABELS)}")
print(f"tag classes    {json.dumps({t: len(v) for t, v in TAG_CLASSES.items()})}")
print(f"records        {len(records)}")
print(
    f"leaves         {len(touched)} represented + {len(POLICY_EXCLUDED)} policy "
    f"exclusions = {len(touched) + len(POLICY_EXCLUDED)} container leaves"
)
print(f"spans          {len(spans)}")
for k in ("substantive", "supporting_authority", "non_mechanical", "unresolved"):
    print(f"  {k:22} {counts[k]}")
print(f"components     {len(components)}")
for c in components:
    print(
        f"  {c.record_key}/{c.semantic_key}: {c.handling.value}, "
        f"{len(c.facts)} facts, reason={c.irreducibility_reason_code}"
    )
print(f"facts          {COUNTS['facts']}")
print(f"prose bindings {len(prose_bindings)}")
print(
    f"references     {len(references)} "
    f"({COUNTS['record_owned_references']} record owned)"
)
print(f"provenance     {len(provenance)}")
print("relationships  0")
print()
print(f"{'record':24} {'leaves':>6} {'spans':>6}")
for r in sorted(per_record):
    d = per_record[r]
    print(f"{r:24} {len(d['leaves']):6} {d['spans']:6}")
print()
for name, found in (
    ("partition", partition),
    ("structural", STRUCTURAL),
    ("component rules", _component_rules),
    ("reason codes", reason_codes),
    ("representation (standalone)", standalone),
    ("representation (merged w/ accepted prior)", merged_findings),
):
    print(f"{name:44} {len(found)}")
    for f in found:
        print("   -", f)
print()
print(f"wire trip      {WIRE_ROUND_TRIP}")
print(
    f"obligations    {len(OBLIGATION_IDS)} accounted for; "
    + ", ".join(f"{k}={v}" for k, v in OBLIGATION_ACCOUNTING["tally"].items())  # type: ignore[union-attr]
)
print(f"schema change  {SCHEMA[0]} (+1 family, +1 vocabulary)")
print(
    f"succession     {REVIEW_PRIOR_SCHEMA_VERSION} -> {SCHEMA[0]} via "
    f"{SUCCESSION['steps']}, verified element by element"
)
print(
    f"schema stop    S-2 {SCHEMA_STOPS[0]['status']}; exact-phrase sweep "
    f"{SIBLING_SWEEP['matching_leaves']} leaf in "
    f"{len(SIBLING_SWEEP['sections'])} section over "
    f"{SIBLING_SWEEP['represented_leaves_scanned']} represented leaves "
    "(disclosure, not an admission test)"
)
print(f"refs cited     {REFERENCE_SCOPE['cross_batch_citations']}")
print(f"unresolved before  {REFERENCE_SCOPE['unresolved_targets_before_this_batch']}")
print(f"unresolved after   {REFERENCE_SCOPE['unresolved_targets_after_the_merge']}")
print(f"resolved by this   {REFERENCE_SCOPE['resolved_by_this_batch']}")
print(
    "publishable    False  (proposed only; not accepted, not activated, "
    "publication gate not executed)"
)
print(
    f"precedent      charmed={PRECEDENT['accepted']['state']}/"
    f"{PRECEDENT['accepted']['roll_actor']} vs "
    f"friendly={_polarity[FRI]['state']} hostile={_polarity[HOS]['state']}"
)
print(f"consumer       action.influence -> {_influence_targets} all present")
print(f"prior content sha    {_prior_content_before} -> {_prior_content_after}")
print(f"prior blob id        {_prior_blob_before} -> {_prior_blob_after}")
print(f"prior raw sha        {_prior_raw_before}")
print(f"live oracle unchanged {LIVE_ORACLE_UNCHANGED}  (read as a sentinel only)")
print(
    "disjointness   "
    + json.dumps(
        {
            "span_overlap": DISJOINT["span_overlap"],
            "leaf_overlap": DISJOINT["leaf_overlap"],
            "collection_overlap": {k: len(v) for k, v in OVERLAP.items()},
        }
    )
)
_inputs_line = json.dumps({k: v for k, v in INPUT_PATHS.items() if k != "note"})
print(f"inputs         {_inputs_line}")
print(f"final proposal sha256  {FINAL_SHA256[PROPOSAL_FILE]}")
print(f"final audit    sha256  {FINAL_SHA256[AUDIT_FILE]}")
print("newlines       LF (asserted: no CR byte in either artifact)")
if DETERMINISTIC is not None:
    print(f"deterministic  {DETERMINISTIC}  (final bytes, parent vs separate process)")
