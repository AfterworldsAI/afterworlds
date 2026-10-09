"""Machine proposal generator — CRD Issue 5d content batch candidate `conditions-1`.

DISPOSABLE REVIEW MATERIAL. Emits a `MechanicalProposal` payload only. Never
writes to `oracles/`, never calls `accept_proposal`, never touches the database.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(r"D:\AI\Claude\afterworlds")
sys.path.insert(0, str(REPO / "src"))
OUT = Path(__file__).parent

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
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import ReleaseBinding  # noqa: E402
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.models import ReviewState  # noqa: E402
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    AbilityScore,
    ActionCost,
    ActionRestrictionFact,
    AdvantageFact,
    AdvantageState,
    AutomaticOutcome,
    AutomaticOutcomeFact,
    CriticalHitChange,
    CriticalHitRuleFact,
    DamageResponseFact,
    DamageResponseKind,
    DamageScope,
    RollActor,
    RollSpec,
    ScalingBasis,
    ScalingDirection,
    ScalingEffect,
    ScalingFact,
    SpeedChange,
    SpeedModificationFact,
    StateEffectFact,
    StateEffectKind,
    ComponentDraft,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    RollContext,
    component_target_key,
    fact_target_key,
    prose_binding_target_key,
    record_target_key,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)

# ---------------------------------------------------------------------------
# Bound release, reconstructed from the dumped production build
# ---------------------------------------------------------------------------

leaves = json.loads((OUT / "leaves.json").read_text(encoding="utf-8"))
containers = json.loads((OUT / "containers.json").read_text(encoding="utf-8"))
edges = json.loads((OUT / "edges.json").read_text(encoding="utf-8"))
binding_json = json.loads((OUT / "binding.json").read_text(encoding="utf-8"))

BINDING = ReleaseBinding(**binding_json)

CORPUS = BoundCorpusSnapshot(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    leaf_lengths={
        lf["leaf_id"]: len(lf["content"])
        for lf in leaves
        if lf["disposition"] == "represented"
    },
    chunk_coverage=tuple(
        ChunkCoverage(
            chunk_id=e["chunk_id"],
            leaf_id=e["leaf_id"],
            cover_start=e["cover_start"],
            cover_end=e["cover_end"],
            role=e["role"],
            projection_id=e["projection_id"],
        )
        for e in edges
    ),
)

leaf_by_id = {lf["leaf_id"]: lf for lf in leaves}
chunk_of_leaf = {e["leaf_id"]: e["chunk_id"] for e in edges}

by_container = defaultdict(list)
for lf in leaves:
    if lf["disposition"] != "represented":
        continue
    for cid in lf["container_path"]:
        by_container[cid].append(lf)
for v in by_container.values():
    v.sort(key=lambda x: (x["page_index"], x["char_start"]))

GLOSSARY = "5436892a-8f86-5774-8f2b-09553e1e4fb0"


def ancestry(cid):
    out, c = [], containers[cid]
    while c:
        out.append(c["container_id"])
        c = containers.get(c["parent_id"]) if c["parent_id"] else None
    return out


ENTRY_BY_LABEL = {
    c["label"]: cid
    for cid, c in containers.items()
    if c["container_type"] == "entry" and GLOSSARY in ancestry(cid)
}

# ---------------------------------------------------------------------------
# The proposed batch, stated as an explicit reviewable clause table
# ---------------------------------------------------------------------------
#
# Per entry: one list of leaf specs, in document order, one per leaf.
# Each leaf spec is a list of segments: (cut_marker | None, kind, arg).
#   "R"  SUPPORTING_AUTHORITY, contextually linked to the record
#   "C"  SUPPORTING_AUTHORITY, contextually linked to component `arg`
#   "U"  UNRESOLVED           — the closed typed union cannot carry this
#                               mechanic and it is not affirmatively prose-bound
#   "F"  SUBSTANTIVE, primary-claimed by fact  arg = (component, fact)
#   "P"  SUBSTANTIVE, primary-claimed by prose binding  arg = (component, reason)
# `cut_marker` ends the segment right after that substring; None runs to the
# end of the leaf.

A, D = AdvantageState.ADVANTAGE, AdvantageState.DISADVANTAGE
ATK, CHK, SAV, INI = (
    RollContext.ATTACK_ROLL,
    RollContext.ABILITY_CHECK,
    RollContext.SAVING_THROW,
    RollContext.INITIATIVE,
)
MINE, THEIRS = RollActor.SUBJECT, RollActor.AGAINST_SUBJECT
APPLIES, IMMUNITY = ConditionEffectKind.APPLIES, ConditionEffectKind.IMMUNITY
CTX = "contextual_applicability"
NLE = "natural_language_exception"
OPEN = "open_ended_effect"


def ADV(state, actor, context, ability=None):
    return AdvantageFact(state=state, roll=RollSpec(actor, context, ability))


def AUTOFAIL(ability=None, context=SAV):
    return AutomaticOutcomeFact(
        roll=RollSpec(MINE, context, ability), outcome=AutomaticOutcome.FAILURE
    )


def COND(kind, effect=APPLIES):
    return ConditionEffectFact(kind, effect)


SPEED_ZERO = SpeedModificationFact(
    change=SpeedChange.SET_TO, feet=0, can_increase=False
)
AUTO_CRIT = CriticalHitRuleFact(CriticalHitChange.AUTOMATIC_ON_HIT)
ALL_DAMAGE_RESIST = DamageResponseFact(DamageResponseKind.RESISTANCE, DamageScope.ALL)


def EXHAUST(effect, amount):
    return ScalingFact(
        basis=ScalingBasis.CONDITION_LEVEL,
        threshold=0,
        effect=effect,
        direction=ScalingDirection.DECREASE,
        amount=amount,
    )


def STATE(kind):
    return StateEffectFact(kind)

W = [(None, "R", None)]  # whole leaf, supporting, linked to the record
U = [(None, "U", None)]  # whole leaf, unresolved


def C(comp):
    return [(None, "C", comp)]


def F(comp, fact):
    return [(None, "F", (comp, fact))]


def P(comp, reason=CTX):
    return [(None, "P", (comp, reason))]


SPEC: dict[str, list] = {
    "Condition": [
        W,
        W,
        [  # 'Blinded Charmed Deafened Exhaustion Frightened'
            ("Blinded", "REF", "condition.blinded"),
            ("Charmed", "REF", "condition.charmed"),
            ("Deafened", "REF", "condition.deafened"),
            ("Exhaustion", "REF", "condition.exhaustion"),
            (None, "REF", "condition.frightened"),
        ],
        [
            ("Grappled", "REF", "condition.grappled"),
            ("Incapacitated", "REF", "condition.incapacitated"),
            ("Invisible", "REF", "condition.invisible"),
            ("Paralyzed", "REF", "condition.paralyzed"),
            (None, "REF", "condition.petrified"),
        ],
        [
            ("Poisoned", "REF", "condition.poisoned"),
            ("Prone", "REF", "condition.prone"),
            ("Restrained", "REF", "condition.restrained"),
            ("Stunned", "REF", "condition.stunned"),
            (None, "REF", "condition.unconscious"),
        ],
        P("condition_definition", NLE),
    ],
    "Blinded [Condition]": [
        W,
        W,
        C("cant_see"),
        [
            # "You can't see" as an imposed sensory state has exactly one other
            # instance corpus-wide (Deafened's parallel). Every other blinding
            # effect says "has the Blinded condition", which ConditionEffectFact
            # already carries, so a StateEffectKind member here would be
            # condition-specific. Honest residue, not a new enum member.
            ("see", "U", None),
            ("any ability check", "F", ("cant_see", AUTOFAIL(context=CHK))),
            (None, "P", ("cant_see", CTX)),
        ],
        C("attacks_affected"),
        [
            ("have Advantage,", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            (None, "F", ("attacks_affected", ADV(D, MINE, ATK))),
        ],
    ],
    "Charmed [Condition]": [
        W,
        W,
        C("cant_harm_the_charmer"),
        # Targeting restriction. The corpus sweep found restriction referents
        # ranging over distances, creature relationships, spell schools, spatial
        # areas, and effect properties; a closed referent vocabulary spanning
        # those is a predicate language. Affirmatively prose-bound.
        P("cant_harm_the_charmer", CTX),
        C("social_advantage"),
        [
            ("any ability check", "F", ("social_advantage", ADV(A, THEIRS, CHK))),
            (None, "P", ("social_advantage", CTX)),
        ],
    ],
    "Deafened [Condition]": [
        W,
        W,
        C("cant_hear"),
        [
            ("hear", "U", None),
            ("any ability check", "F", ("cant_hear", AUTOFAIL(context=CHK))),
            (None, "P", ("cant_hear", CTX)),
        ],
    ],
    "Exhaustion [Condition]": [
        W,
        W,
        W,
        # Cumulative level accrual and the death threshold. A condition-level
        # state machine is singular machinery - the source itself calls
        # Exhaustion "an exception to that rule" - so it is reported as residue
        # rather than typed on one instance.
        U,
        C("d20_tests_affected"),
        F("d20_tests_affected", EXHAUST(ScalingEffect.D20_TEST, 2)),
        C("speed_reduced"),
        F("speed_reduced", EXHAUST(ScalingEffect.SPEED, 5)),
        W,
        # Removal of one condition level by a Long Rest. ResourceRecoveryFact
        # states resource cadence; a condition-level decrement is not a resource,
        # and forcing it through resource_key would be the string escape hatch
        # ADR-005d Decision 4 forbids.
        U,
    ],
    "Frightened [Condition]": [
        W,
        W,
        C("checks_and_attacks"),
        [
            ("on ability checks", "F", ("checks_and_attacks", ADV(D, MINE, CHK))),
            ("and attack rolls", "F", ("checks_and_attacks", ADV(D, MINE, ATK))),
            (None, "P", ("checks_and_attacks", CTX)),
        ],
        C("cant_approach"),
        P("cant_approach", CTX),
    ],
    "Grappled [Condition]": [
        W,
        W,
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        [
            ("on attack rolls", "F", ("attacks_affected", ADV(D, MINE, ATK))),
            (None, "P", ("attacks_affected", CTX)),
        ],
        W,
        # Per-foot movement cost plus a size-comparative eligibility predicate.
        # Movement cost and creature size are both untyped, and eligibility is a
        # deferred family this batch does not force on its own.
        U,
    ],
    "Incapacitated [Condition]": [
        W,
        W,
        C("inactive"),
        [
            (
                "any action,",
                "F",
                ("inactive", ActionRestrictionFact(ActionCost.ACTION)),
            ),
            (
                "Bonus Action,",
                "F",
                ("inactive", ActionRestrictionFact(ActionCost.BONUS_ACTION)),
            ),
            (None, "F", ("inactive", ActionRestrictionFact(ActionCost.REACTION))),
        ],
        C("no_concentration"),
        F("no_concentration", STATE(StateEffectKind.CONCENTRATION_BROKEN)),
        C("speechless"),
        F("speechless", STATE(StateEffectKind.CANNOT_SPEAK)),
        C("surprised"),
        C("surprised"),
        F("surprised", ADV(D, MINE, INI)),
    ],
    "Invisible [Condition]": [
        W,
        W,
        C("surprise"),
        F("surprise", ADV(A, MINE, INI)),
        C("concealed"),
        # Targeting restriction, same sweep-backed judgement as Charmed.
        P("concealed", CTX),
        C("attacks_affected"),
        [
            ("have Disadvantage,", "F", ("attacks_affected", ADV(D, THEIRS, ATK))),
            ("have Advantage.", "F", ("attacks_affected", ADV(A, MINE, ATK))),
            (None, "P", ("attacks_affected", CTX)),
        ],
    ],
    "Paralyzed [Condition]": [
        W,
        W,
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("automatic_critical_hits"),
        [
            ("is a Critical Hit", "F", ("automatic_critical_hits", AUTO_CRIT)),
            (None, "P", ("automatic_critical_hits", CTX)),
        ],
    ],
    "Petrified [Condition]": [
        W,
        W,
        W,
        # Transformation to an inanimate substance, a tenfold weight change, and
        # ceased aging: three singular claims with no typed home.
        U,
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("resist_damage"),
        F("resist_damage", ALL_DAMAGE_RESIST),
        C("poison_immunity"),
        F("poison_immunity", COND(ConditionKind.POISONED, IMMUNITY)),
    ],
    "Poisoned [Condition]": [
        W,
        W,
        C("checks_and_attacks"),
        [
            ("on attack rolls", "F", ("checks_and_attacks", ADV(D, MINE, ATK))),
            (None, "F", ("checks_and_attacks", ADV(D, MINE, CHK))),
        ],
    ],
    "Prone [Condition]": [
        W,
        W,
        W,
        # Movement options and their cost: crawling and the half-Speed stand-up
        # cost have no typed home, and the sentence continues into the next leaf.
        U,
        U,
        C("attacks_affected"),
        [
            ("on attack rolls.", "F", ("attacks_affected", ADV(D, MINE, ATK))),
            ("has Advantage", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            # The branch selector - the distance test and the "Otherwise"
            # default - is governing prose, exactly as the identical "within 5
            # feet" qualifier is on Paralyzed's and Unconscious's automatic
            # Critical Hit. Without it the typed surface would assert both
            # Advantage and Disadvantage against the subject unconditionally,
            # and a deterministic consumer could not tell which applies.
            ("Otherwise,", "P", ("attacks_affected", CTX)),
            (None, "F", ("attacks_affected", ADV(D, THEIRS, ATK))),
        ],
    ],
    "Restrained [Condition]": [
        W,
        W,
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        [
            ("have Advantage,", "F", ("attacks_affected", ADV(A, THEIRS, ATK))),
            (None, "F", ("attacks_affected", ADV(D, MINE, ATK))),
        ],
        C("saving_throws_affected"),
        F("saving_throws_affected", ADV(D, MINE, SAV, AbilityScore.DEXTERITY)),
    ],
    "Stunned [Condition]": [
        W,
        W,
        C("incapacitated"),
        F("incapacitated", COND(ConditionKind.INCAPACITATED)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
    ],
    "Unconscious [Condition]": [
        W,
        W,
        C("inert"),
        [
            ("the Incapacitated", "F", ("inert", COND(ConditionKind.INCAPACITATED))),
            ("and Prone conditions,", "F", ("inert", COND(ConditionKind.PRONE))),
            ("holding.", "F", ("inert", STATE(StateEffectKind.DROPS_HELD_OBJECTS))),
            # "When this condition ends, you remain Prone." - sequencing, a
            # deferred family this clause alone does not force.
            (None, "U", None),
        ],
        C("speed_zero"),
        F("speed_zero", SPEED_ZERO),
        C("attacks_affected"),
        F("attacks_affected", ADV(A, THEIRS, ATK)),
        C("saving_throws_affected"),
        [
            (
                "fail Strength",
                "F",
                ("saving_throws_affected", AUTOFAIL(AbilityScore.STRENGTH)),
            ),
            (None, "F", ("saving_throws_affected", AUTOFAIL(AbilityScore.DEXTERITY))),
        ],
        C("automatic_critical_hits"),
        [
            ("is a Critical Hit", "F", ("automatic_critical_hits", AUTO_CRIT)),
            (None, "P", ("automatic_critical_hits", CTX)),
        ],
        C("unaware"),
        F("unaware", STATE(StateEffectKind.UNAWARE_OF_SURROUNDINGS)),
    ],
}

RECORD_KEY = {
    "Condition": "glossary.condition",
    **{
        lbl: "condition." + lbl.split(" [")[0].lower()
        for lbl in SPEC
        if lbl.endswith("[Condition]")
    },
}
RECORD_KIND = {
    "glossary.condition": RecordKind.GLOSSARY_RULE,
    **{v: RecordKind.CONDITION for k, v in RECORD_KEY.items() if k != "Condition"},
}
SCOPE_KEY = "srd-5.2.1/rules-glossary"

# ---------------------------------------------------------------------------
# Expansion
# ---------------------------------------------------------------------------

spans: list[SemanticSpan] = []
proposed: list[ProposedSpan] = []
provenance: list[ProvenanceClaim] = []
references: list[ReferenceDraft] = []
prose_bindings: list[ProseBindingDraft] = []
comp_facts: dict[tuple[str, str], list] = defaultdict(list)
comp_reason: dict[tuple[str, str], str] = {}
audit: list[dict] = []

DISP = {
    "R": SemanticDisposition.SUPPORTING_AUTHORITY,
    "C": SemanticDisposition.SUPPORTING_AUTHORITY,
    "REF": SemanticDisposition.SUPPORTING_AUTHORITY,
    "U": SemanticDisposition.UNRESOLVED,
    "F": SemanticDisposition.SUBSTANTIVE,
    "P": SemanticDisposition.SUBSTANTIVE,
}
RATIONALE = {
    "R": "identifies or frames the mechanic; preserved as supporting authority rather than discarded",
    "C": "sub-heading naming the effect it labels; preserved as supporting authority",
    "REF": "names one condition this glossary defines; source-authored reference target",
    "U": "no member of the closed typed fact union faithfully carries this mechanic, and it is "
    "not affirmatively irreducible; classifying it PROSE_BOUND would be a backlog state",
    "F": "states a mechanic the closed typed union carries exactly",
    "P": "applicability qualifier that cannot be reduced without executable interpretation",
}

for label, leafspecs in SPEC.items():
    entry_id = ENTRY_BY_LABEL[label]
    rkey = RECORD_KEY[label]
    lvs = by_container[entry_id]
    assert len(lvs) == len(leafspecs), f"{label}: {len(lvs)} leaves vs {len(leafspecs)} specs"

    for lf, segs in zip(lvs, leafspecs):
        content, lid = lf["content"], lf["leaf_id"]
        cursor = 0
        for i, (marker, kind, arg) in enumerate(segs):
            if marker is None:
                end = len(content)
            else:
                found = content.find(marker, cursor)
                assert found >= 0, f"{label}: marker {marker!r} not in {content!r}"
                end = found + len(marker)
            assert end > cursor, f"{label}: empty segment {marker!r}"
            start = cursor
            cursor = end
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
                ProposedSpan(span=span, origin="propose_conditions.py", rationale=RATIONALE[kind])
            )
            audit.append(
                {
                    "record": rkey,
                    "leaf": lid,
                    "span_id": sid,
                    "range": [start, end],
                    "text": content[start:end],
                    "disposition": disp.value,
                    "kind": kind,
                }
            )

            if kind == "R":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.RECORD, (rkey,), sid, ProvenanceRole.CONTEXTUAL
                    )
                )
            elif kind == "C":
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.COMPONENT,
                        (rkey, arg),
                        sid,
                        ProvenanceRole.CONTEXTUAL,
                    )
                )
            elif kind == "REF":
                ref = ReferenceDraft(
                    from_record_key=rkey,
                    from_component_key="condition_definition",
                    source_text=content[start:end].strip(),
                    scope_key=SCOPE_KEY,
                    target_record_key=arg,
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
                comp_facts[(rkey, comp)].append(fact)
                provenance.append(
                    ProvenanceClaim(
                        ProvenanceTargetKind.FACT,
                        fact_target_key(rkey, comp, fact),
                        sid,
                        ProvenanceRole.PRIMARY,
                    )
                )
            elif kind == "P":
                comp, reason = arg
                comp_reason[(rkey, comp)] = reason
                comp_facts.setdefault((rkey, comp), [])
                extent = CORPUS.chunk_relative_range(chunk_of_leaf[lid], lid, start, end)
                assert extent is not None, f"{label}: no unambiguous chunk extent for {sid}"
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
    RecordDraft(semantic_key=k, kind=RECORD_KIND[k]) for k in sorted(set(RECORD_KEY.values()))
)
components = []
for (rkey, ckey), facts in sorted(comp_facts.items()):
    reason = comp_reason.get((rkey, ckey))
    if facts and reason:
        handling = ComponentHandling.MIXED
    elif facts:
        handling = ComponentHandling.STRUCTURED
    else:
        handling = ComponentHandling.PROSE_BOUND
    components.append(
        ComponentDraft(
            record_key=rkey,
            semantic_key=ckey,
            handling=handling,
            irreducibility_reason_code=reason,
            facts=tuple(facts),
        )
    )

DRAFT = RepresentationDraft(
    records=records,
    components=tuple(components),
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

findings: list[str] = []
touched = sorted({s.leaf_id for s in spans})
for lid in touched:
    findings.extend(validate_partition(lid, CORPUS.leaf_lengths[lid], tuple(spans)))
findings.extend(validate_reason_codes(tuple(spans)))
findings.extend(validate_representation(DRAFT, LEDGER, CORPUS))

PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    proposed_spans=tuple(proposed),
    proposed_representation=DRAFT,
    proposal_origin="propose_conditions.py (CRD Issue 5d batch candidate conditions-1)",
)

payload = proposal_payload(PROPOSAL)
ident = proposal_identity(PROPOSAL)

(OUT / "proposal_conditions_1.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
)
(OUT / "proposal_audit.json").write_text(
    json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
)

unresolved = [s for s in spans if s.disposition is SemanticDisposition.UNRESOLVED]
print(f"leaves touched      : {len(touched)}")
print(f"spans               : {len(spans)}")
print(f"  substantive       : {sum(1 for s in spans if s.disposition is SemanticDisposition.SUBSTANTIVE)}")
print(f"  supporting        : {sum(1 for s in spans if s.disposition is SemanticDisposition.SUPPORTING_AUTHORITY)}")
print(f"  unresolved        : {len(unresolved)}")
print(f"  non_mechanical    : {sum(1 for s in spans if s.disposition is SemanticDisposition.NON_MECHANICAL)}")
print(f"records             : {len(records)}")
print(f"components          : {len(components)}  "
      f"(structured {sum(1 for c in components if c.handling is ComponentHandling.STRUCTURED)}, "
      f"mixed {sum(1 for c in components if c.handling is ComponentHandling.MIXED)}, "
      f"prose_bound {sum(1 for c in components if c.handling is ComponentHandling.PROSE_BOUND)})")
print(f"facts               : {sum(len(c.facts) for c in components)}")
print(f"prose bindings      : {len(prose_bindings)}")
print(f"relationships       : {len(DRAFT.relationships)}")
print(f"references          : {len(references)}")
print(f"provenance edges    : {len(provenance)}")
print(f"proposal identity   : {ident}")
print(f"\nVALIDATION FINDINGS  : {len(findings)}")
for f in findings:
    print("   -", f)
