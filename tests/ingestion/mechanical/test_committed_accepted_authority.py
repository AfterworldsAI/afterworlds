"""The committed accepted authority — CRD Issue 5d, batches 1 through 9.

Nine Owner authorizations, one file. 2026-08-23 accepted ``conditions-1``
(proposal ``14587d5b…``, reviewed under representation schema 3); 2026-09-03
accepted ``hazards-1`` (proposal ``f7ce4491…``, reviewed under schema 5);
2026-09-09 accepted ``actions-1`` (proposal ``62202e9a…``, reviewed under
schema 7); 2026-09-10 accepted ``attitudes-1`` (proposal ``c571dfd6…``,
reviewed under schema 8); 2026-09-11 accepted ``areas-of-effect-1`` (proposal
``d602f4e5…``, reviewed under schema 9); 2026-09-11 accepted ``cover-1``
(proposal ``1d8a5116…``, reviewed under schema 10); 2026-09-12 accepted
``speed-1`` (proposal ``bd9d4942…``, reviewed under schema 11); and
2026-09-20 UTC — 2026-09-19 local, the first acceptances whose two calendar
dates differ — accepted ``proficiency-destinations-1`` (proposal
``723bba62…``) and then ``proficiency-1`` (proposal ``f0becb8b…``), both
reviewed under schema 15 and both recorded under ``5d-semantic-policy-2``,
the first crossing of the semantic policy this corpus has made. The artifact
that records all nine actions is committed under the oracle directory, and this
module keeps it honest: the file is the acceptance action of record, so a
change to it that no one reviewed must fail here.

Seven properties, each of which could break independently:

* the release resolves to **this** artifact and only this one;
* each batch's proposal identity, reviewer, scope, and counts are exact, and the
  scopes are pairwise disjoint;
* the schema each batch was *reviewed* under is retained beside it, and the
  registered succession that carried the older ones forward is recorded;
* the one registered semantic-policy crossing, and the review units each
  batch discharged, are recorded beside the batches that caused them;
* the committed bytes round-trip strictly and reproduce every derived identity;
* the refused candidates cannot be selected; and
* the corpus is still incomplete, so nothing here can publish.

The end-to-end publication refusal lives in ``test_production_release`` and
``test_runtime_production_release``, which carry the real SRD fixture. What is
asserted here is the reason it refuses: this artifact judges 15 conditions, the
glossary entry that defines them, 5 hazards and the glossary entry that defines
*those*, 12 actions plus the glossary entry that defines *those*, the three
attitudes with the glossary entry that defines *those*, and the six areas of
effect with the glossary entry that defines *those*, the ``Cover`` and
``Speed`` glossary rules, neither of which defines a list of its own, and the
four reviewed Proficiency destinations — ``play.actions``, ``play.skills``,
``glossary.challenge_rating`` and ``glossary.expertise`` — beside the
``play.proficiency`` rule the last of them cites — 53 records, not the
release.

``batches`` is keyed rather than ordered: ``load_accepted_inputs`` returns it in
canonical id order, so every assertion below looks a batch up by id. Acceptance
order is asserted where the artifact actually records it — ``schema_anchors``.

**The legacy form is no longer here.** Until ``hazards-1`` was accepted, this
file was also the repository's only specimen of a single-batch, schema-3,
unanchored artifact, and a dozen succession and subclass-refusal modules used it
as one. That shape is frozen at
``data/legacy_conditions_1_unanchored_schema3.json`` — byte-identical to what
this file was, Git blob ``42faeca2…`` — and those modules read it there. This
module is about the artifact the release actually resolves to.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import replace

import pytest

from afterworlds.ingestion.mechanical.models import ReviewState, SemanticDisposition
from afterworlds.ingestion.mechanical.oracle import (
    ACCEPTED_ARTIFACT_KIND,
    COMMITTED_ORACLE_DIR,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
    load_oracle,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.proposal import (
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
    REPRESENTATION_SCHEMA_VERSION,
    fact_qualifier_target_key,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_3_HASH,
    SCHEMA_3_VERSION,
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    SCHEMA_7_HASH,
    SCHEMA_7_VERSION,
    SCHEMA_8_HASH,
    SCHEMA_8_VERSION,
    SCHEMA_9_HASH,
    SCHEMA_9_VERSION,
    SCHEMA_10_HASH,
    SCHEMA_10_VERSION,
    SCHEMA_11_HASH,
    SCHEMA_11_VERSION,
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
    lift_accepted_inputs,
)
from afterworlds.quarantine import QuarantinedAuthorityError
from tests.ingestion.mechanical._replacement_chain import (
    ANIMALS_CATALOGUE,
    BATCHES,
    CHARACTER_CREATION,
    EQUIPMENT_CLASS_ELIGIBILITY,
    FINITE_REFERENCE,
    FINITE_REFERENCE_ROUTES,
    FRAMING,
    NOTES,
    PLAYING_THE_GAME,
    REMAINING,
    proposal_path,
)
from tests.ingestion.mechanical._schema_pins import crossings_from

PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"

ARTIFACT_NAME = "srd-5-2-1-corpus-36b786d8-fa2.json"
ARTIFACT_PATH = COMMITTED_ORACLE_DIR / ARTIFACT_NAME
CONDITIONS_PILOT_PROPOSAL = proposal_path("conditions-pilot")
ACTIONS_PILOT_PROPOSAL = proposal_path("actions-pilot")
REFERENCE_CLOSURE_PROPOSAL = proposal_path("reference-closure")
MOVEMENT_CLOSURE_PROPOSAL = proposal_path("movement-closure")
COMBAT_TURN_1_PROPOSAL = proposal_path("combat-turn-1")
DAMAGE_AND_HIT_POINTS_PROPOSAL = proposal_path("damage-and-hit-points")
COMBAT_DAMAGE_BREAKING_PROPOSAL = proposal_path("combat-damage-breaking")
CHECKS_ACTIONS_RESTS_PROPOSAL = proposal_path("checks-actions-rests")
CORE_PLAY_COMPLETION_PROPOSAL = proposal_path("core-play-completion")
CORE_PLAY_DEPENDENCIES_PROPOSAL = proposal_path("core-play-dependencies")
CHARACTER_CREATION_FOUNDATIONS_PROPOSAL = proposal_path(
    "character-creation-foundations"
)
CHARACTER_ORIGINS_FEATS_PROPOSAL = proposal_path("character-origins-feats")
SPELLCASTING_PROPOSAL = proposal_path("spellcasting")
RULES_GLOSSARY_COMPLETION_PROPOSAL = proposal_path("rules-glossary-completion")
CLASSES_PROPOSAL = proposal_path("classes")
CLASS_OPTION_CATALOGUES_PROPOSAL = proposal_path("class-option-catalogues")
#: Accepted over the replacement chain, not part of it.
SPELL_DESCRIPTIONS_PROPOSAL = NOTES / "issue-5d-spell-descriptions-PROPOSAL.json"
GAMEPLAY_TOOLBOX_PROPOSAL = NOTES / "issue-5d-gameplay-toolbox-PROPOSAL.json"
MAGIC_ITEMS_PROPOSAL = NOTES / "issue-5d-magic-items-PROPOSAL.json"

REVIEWER = "Ravenlok (Owner)"

#: The legacy specimen: what this file was before ``hazards-1`` was accepted
#: into it. The succession tests below carry *that* content across the
#: registered lifts, because that is the content a lift exists to carry.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)

#: The seven-batch artifact this file was before the two Proficiency batches
#: were accepted into it, frozen byte-for-byte. It is this module's specimen
#: of a *superseded* declaration now that the committed artifact declares
#: current authority: schema 11 under ``5d-semantic-policy-1``, four
#: registered crossings behind the schema this build implements.
FROZEN_PRIOR = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1_attitudes_1"
        "_areas_of_effect_1_cover_1_speed_1.json"
    )
)

BATCH_ID = "conditions-1"
PROPOSAL_IDENTITY = "14587d5b5d51ad282f3d16510e015cd7116adcbd3877964bf034eef96780b0eb"  # noqa: E501  # pragma: allowlist secret
HAZARDS_BATCH_ID = "hazards-1"
HAZARDS_PROPOSAL_IDENTITY = "f7ce449174102f1cdb7087a806d1f594add384282e54fb17181c4f5168c40417"  # noqa: E501  # pragma: allowlist secret
ACTIONS_BATCH_ID = "actions-1"
ACTIONS_PROPOSAL_IDENTITY = "62202e9a4b9e0cb539c770e1244b3aa322d8f988e82a544991998fd8fb363b5c"  # noqa: E501  # pragma: allowlist secret
ATTITUDES_BATCH_ID = "attitudes-1"
ATTITUDES_PROPOSAL_IDENTITY = "c571dfd6b829852e58ca066f8735b6d5944cb51c0f4b42c82052d876392bff22"  # noqa: E501  # pragma: allowlist secret
AREAS_BATCH_ID = "areas-of-effect-1"
AREAS_PROPOSAL_IDENTITY = "d602f4e59ab90dbb04852661f78f03e2e311025e80be03f39f4b324f2c6d6878"  # noqa: E501  # pragma: allowlist secret
COVER_BATCH_ID = "cover-1"
COVER_PROPOSAL_IDENTITY = "1d8a51164f9be0a1559aba93fb076ee0e8c262dda183791491bc339e3ebfec01"  # noqa: E501  # pragma: allowlist secret
SPEED_BATCH_ID = "speed-1"
SPEED_PROPOSAL_IDENTITY = "bd9d49427b7f2d996269e4e30a74abc26dacb7804e9176d8ca7f908b6c6a2bf8"  # noqa: E501  # pragma: allowlist secret
PROFICIENCY_DESTINATIONS_BATCH_ID = "proficiency-destinations-1"
PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY = "723bba6246e3a325141705be984c6c28fb016d36a7a6ff1b78fb7b0e21aeac3e"  # noqa: E501  # pragma: allowlist secret
PROFICIENCY_BATCH_ID = "proficiency-1"
PROFICIENCY_PROPOSAL_IDENTITY = "f0becb8bd87fcbb41aced983c55f59beb3f25b52d4eca549257d51d9b86d345a"  # noqa: E501  # pragma: allowlist secret

ORACLE_IDENTITY = "3b8941ce9039a78e72fd3ddf05952d0da4bed18dc4d38fb99b8b80db137fb407"  # noqa: E501  # pragma: allowlist secret
#: The same identity for the frozen seven-batch prior, so the specimen the
#: succession half of this module reads is pinned as exactly as the live file.
PRIOR_ORACLE_IDENTITY = "d395e4ed79045d0b3ef015240d61fd91445a4b38a77a5f75b0e537ca74eaa29f"  # noqa: E501  # pragma: allowlist secret

#: The whole committed file, by two identities the oracle identity does not
#: cover. ``oracle_identity`` is content-only **by design** — reviewer and
#: timestamp are evidence, not identity, so re-reviewing an unchanged
#: classification must not remint a projection (#137 acceptance criterion 11).
#: The consequence is that an unreviewed edit to the acceptance *evidence* —
#: reviewer, timestamp, batch rule, resolved scope, anchors, lifts — leaves the
#: oracle identity untouched. These two pin the file itself, so it does not.
#:
#: The content digest normalizes CRLF to LF, which is what ``.gitattributes``
#: declares this file is stored as; the blob id is Git's own content identity,
#: computed from those same bytes rather than read out of ``.git``.
ARTIFACT_CONTENT_SHA256 = "995976ac1c2b0227d419fc4a7b65a966358e311c7806a1a8f0457a535b4300d7"  # noqa: E501  # pragma: allowlist secret
ARTIFACT_BLOB = "ec645c7e89a126b6ec4778247460449f04da5deb"  # pragma: allowlist secret
PROJECTION_UUID = "82c75aad-b294-5b2e-a188-128cdcbada09"
PROJECTION_PAYLOAD_HASH = "76f1507bd4b5459219b7d2cfd385e52c304349dc3e2fa1b292379acf7464e080"  # noqa: E501  # pragma: allowlist secret

#: What each batch accepted, and what the file therefore holds. Kept per batch
#: rather than only as totals: a merged count that is right for the wrong reason
#: — one batch grown, another shrunk — would still add up.
CONDITIONS = {
    "spans": 185,
    "records": 16,
    "components": 54,
    "facts": 70,
    "prose_bindings": 15,
    "relationships": 0,
    "references": 15,
    "provenance": 185,
    "substantive": 87,
    "supporting": 98,
    "non_mechanical": 0,
}
HAZARDS = {
    "spans": 96,
    "records": 6,
    "components": 15,
    "facts": 21,
    "prose_bindings": 5,
    "relationships": 0,
    "references": 7,
    "provenance": 96,
    "substantive": 65,
    "supporting": 31,
    "non_mechanical": 0,
}
ACTIONS = {
    "spans": 182,
    "records": 13,
    "components": 37,
    "facts": 48,
    "prose_bindings": 27,
    "relationships": 0,
    "references": 17,
    "provenance": 199,
    "substantive": 84,
    "supporting": 98,
    "non_mechanical": 0,
}
ATTITUDES = {
    "spans": 24,
    "records": 4,
    "components": 3,
    "facts": 3,
    "prose_bindings": 2,
    "relationships": 0,
    "references": 7,
    "provenance": 24,
    "substantive": 5,
    "supporting": 19,
    "non_mechanical": 0,
}
AREAS = {
    "spans": 43,
    "records": 7,
    "components": 23,
    "facts": 23,
    "prose_bindings": 0,
    "relationships": 0,
    "references": 7,
    "provenance": 43,
    "substantive": 24,
    "supporting": 19,
    "non_mechanical": 0,
}
COVER = {
    "spans": 28,
    "records": 1,
    "components": 4,
    "facts": 8,
    "prose_bindings": 0,
    "relationships": 0,
    "references": 0,
    "provenance": 28,
    "substantive": 16,
    "supporting": 12,
    "non_mechanical": 0,
}
SPEED = {
    "spans": 36,
    "records": 1,
    "components": 9,
    "facts": 17,
    "prose_bindings": 0,
    "relationships": 0,
    "references": 9,
    "provenance": 52,
    "substantive": 16,
    "supporting": 20,
    "non_mechanical": 0,
}
PROFICIENCY_DESTINATIONS = {
    "spans": 120,
    "records": 4,
    "components": 19,
    "facts": 2,
    "prose_bindings": 70,
    "relationships": 0,
    "references": 17,
    "provenance": 138,
    "substantive": 70,
    "supporting": 50,
    "non_mechanical": 0,
}
PROFICIENCY = {
    "spans": 47,
    "records": 1,
    "components": 13,
    "facts": 18,
    "prose_bindings": 23,
    "relationships": 0,
    "references": 4,
    "provenance": 63,
    "substantive": 35,
    "supporting": 11,
    "non_mechanical": 1,
}
BATCH_COUNTS = {
    BATCH_ID: CONDITIONS,
    HAZARDS_BATCH_ID: HAZARDS,
    ACTIONS_BATCH_ID: ACTIONS,
    ATTITUDES_BATCH_ID: ATTITUDES,
    AREAS_BATCH_ID: AREAS,
    COVER_BATCH_ID: COVER,
    SPEED_BATCH_ID: SPEED,
    PROFICIENCY_DESTINATIONS_BATCH_ID: PROFICIENCY_DESTINATIONS,
    PROFICIENCY_BATCH_ID: PROFICIENCY,
}
MERGED = {k: sum(c[k] for c in BATCH_COUNTS.values()) for k in CONDITIONS}

SPANS = MERGED["spans"]
RECORDS = MERGED["records"]
COMPONENTS = MERGED["components"]
FACTS = MERGED["facts"]
PROSE_BINDINGS = MERGED["prose_bindings"]
RELATIONSHIPS = MERGED["relationships"]
REFERENCES = MERGED["references"]
PROVENANCE = MERGED["provenance"]
SUBSTANTIVE = MERGED["substantive"]
SUPPORTING = MERGED["supporting"]
NON_MECHANICAL = MERGED["non_mechanical"]

#: The cross-batch citations accepted content names and no accepted batch
#: defines. Each is a publication blocker until the batch that defines it is
#: accepted. ``glossary.concentration`` has been inherited and untouched since
#: ``conditions-1``; the other nine are the movement and special-speed entries
#: ``speed-1`` cites without ingesting — no record, component, fact or span was
#: created for any of them, and no target was invented.
UNRESOLVED_TARGETS = [
    "glossary.burrow_speed",
    "glossary.climb_speed",
    "glossary.climbing",
    "glossary.concentration",
    "glossary.crawling",
    "glossary.fly_speed",
    "glossary.flying",
    "glossary.jumping",
    "glossary.swim_speed",
    "glossary.swimming",
]

#: The other half of the residue: four citations the reviewed Proficiency
#: destinations print and that name **no target at all**, recorded as
#: ``(scope_key, source_text)``. They are honest empties rather than
#: resolutions — no destination was ingested for them and no resolution
#: decision was invoked, which is what an empty ``reference_resolutions``
#: says. They must stay unresolved until a batch that actually defines each
#: target is reviewed and accepted.
UNRESOLVED_CITATIONS = [
    ("srd-5.2.1/gameplay-toolbox", "Combat Encounters"),
    ("srd-5.2.1/playing-the-game", "Combat"),
    ("srd-5.2.1/playing-the-game", "Opportunity Attack"),
    ("srd-5.2.1/rules-glossary", "Stat Block"),
]

#: Refused by semantic review. Named here so "not selectable" is a test rather
#: than a promise in a checkpoint document.
REFUSED = (
    "756922a3892f9420dc8bfb2fe6af8a5a4db491111d1786ab0de6c2ddbf7dbfa6",  # noqa: E501  # pragma: allowlist secret
    "b9ac21bf045a3f5d1e020f91fd43fdd6e5f3fb0b3d0a715de556a574d3ab14a6",  # noqa: E501  # pragma: allowlist secret
    "2f42f2bb82bcb4ed6ac489b47f774495d2ec5d985871a0d5b69f659fc83fb24b",  # noqa: E501  # pragma: allowlist secret
    # The schema-4 hazards proposal the semantic review rejected. It stays
    # historical evidence; the batch that was accepted is a different identity
    # against a different schema, and the assertion below is what keeps the two
    # from ever being confused.
    "6277ff735e0e47b3337f2c3736ca7922864b1cde9a3c286b3aee48ee461ba259",  # noqa: E501  # pragma: allowlist secret
    # The two ``attitudes-1`` revisions the independent review declined to
    # pass for acceptance — the first still carrying an unresolved span, the
    # second still carrying the scope/type wording conflict. Both were
    # superseded rather than accepted, and the accepted batch is a third,
    # different identity.
    "da131c6f99f1108f9bea5a2a25799189df2d25562532bdfa673170647cd074a2",  # noqa: E501  # pragma: allowlist secret
    "5ea537a1b0a936c4ebc7389ffc2b3402c7d416177a04c72c6eefc9372b5bea7f",  # noqa: E501  # pragma: allowlist secret
)


# ---------------------------------------------------------------------------
# 1. Exact release lookup, and only this artifact
# ---------------------------------------------------------------------------


def test_the_release_resolves_to_this_sole_committed_artifact() -> None:
    """One artifact per release, and this release resolves to it.

    The resolver refuses two artifacts claiming one release rather than picking
    one, so a later batch must *extend* this file. Asserting the exact filename
    is what makes a second file for this release fail here before it can fail
    there.

    Recorded Owner Decision 2026-09-21 quarantines this release, so the
    resolution half of the original claim is inverted: the artifact is still the
    sole file for this release and still carries this binding and this identity
    — read through the path loader — but ``committed_inputs_for`` refuses to
    resolve it as authority.
    """
    # The others are the clean restart's replacement chains, each a different release.
    assert sorted(p.name for p in COMMITTED_ORACLE_DIR.glob("*.json")) == [
        ARTIFACT_NAME,
        "srd-5-2-1-corpus-3fe24ff6-4e3.json",
        "srd-5-2-1-corpus-574662e9-0ef.json",
        "srd-5-2-1-corpus-8781d4e0-a3b.json",
    ]
    with pytest.raises(QuarantinedAuthorityError):
        committed_inputs_for(PACKAGE_UUID, RELEASE_VERSION)
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.binding.package_uuid == PACKAGE_UUID
    assert inputs.oracle.binding.release_version == RELEASE_VERSION
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY


def test_an_unrelated_release_still_resolves_to_nothing() -> None:
    """Resolution is by binding, not by "there is a file in the directory".

    The quarantine is identity-scoped, so this has to be asserted from both
    sides: naming *either* quarantined field is refused even when the other
    field matches nothing, and an identity the quarantine says nothing about
    still gets the ordinary "no such binding" answer rather than an error.
    """
    with pytest.raises(QuarantinedAuthorityError):
        committed_oracle_for(PACKAGE_UUID, "5.2.1-corpus.not-a-release")
    with pytest.raises(QuarantinedAuthorityError):
        committed_inputs_for("no-such-package", RELEASE_VERSION)
    unrelated = "11111111-2222-5333-8444-555555555555"
    assert committed_oracle_for(unrelated, "5.2.1-corpus.not-a-release") is None
    assert committed_inputs_for(unrelated, "5.2.1-corpus.not-a-release") is None


# ---------------------------------------------------------------------------
# 2. The acceptance action, exactly as authorized
# ---------------------------------------------------------------------------


def test_the_batch_records_the_authorized_acceptance_exactly() -> None:
    """Batch id, proposal identity, reviewer, and scope size — all four.

    The proposal identity is what ties this accepted representation to a thing a
    human actually read. A batch that named a different proposal would be
    accepted authority over content nobody reviewed.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    batches = {b.batch_id: b for b in inputs.batches}
    assert len(batches) == len(inputs.batches), "a batch id is recorded twice"
    assert sorted(batches) == sorted(BATCH_COUNTS)
    for batch_id, identity in (
        (BATCH_ID, PROPOSAL_IDENTITY),
        (HAZARDS_BATCH_ID, HAZARDS_PROPOSAL_IDENTITY),
        (ACTIONS_BATCH_ID, ACTIONS_PROPOSAL_IDENTITY),
        (ATTITUDES_BATCH_ID, ATTITUDES_PROPOSAL_IDENTITY),
        (AREAS_BATCH_ID, AREAS_PROPOSAL_IDENTITY),
        (COVER_BATCH_ID, COVER_PROPOSAL_IDENTITY),
        (SPEED_BATCH_ID, SPEED_PROPOSAL_IDENTITY),
        (
            PROFICIENCY_DESTINATIONS_BATCH_ID,
            PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY,
        ),
        (PROFICIENCY_BATCH_ID, PROFICIENCY_PROPOSAL_IDENTITY),
    ):
        batch = batches[batch_id]
        counts = BATCH_COUNTS[batch_id]
        assert batch.proposal_identity == identity
        assert len(batch.resolved_scope) == counts["spans"]
        assert len(set(batch.resolved_scope)) == counts["spans"], "the scope repeats"
        assert len(batch.diff) == counts["spans"]
        assert batch.rule.strip()
    # Pairwise disjoint, which is what makes each later batch an extension
    # rather than a re-judgement of something already accepted.
    scopes = [set(b.resolved_scope) for b in inputs.batches]
    assert len(set().union(*scopes)) == sum(len(scope) for scope in scopes)


def test_every_span_has_exactly_one_acceptance_record() -> None:
    """No missing, duplicate, or out-of-scope acceptance.

    All three failures are silent in different ways — a missing record leaves a
    span unaccepted while the file looks complete, a duplicate inflates the
    evidence, and an out-of-scope record accepts something the reviewer never
    saw — so each is asserted separately.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    accepted_ids = [a.span_id for a in inputs.acceptances]
    span_ids = {s.span_id for s in inputs.oracle.spans}

    assert len(accepted_ids) == SPANS
    assert len(set(accepted_ids)) == SPANS, "an acceptance record is duplicated"
    assert set(accepted_ids) == span_ids, "acceptance and span sets differ"
    assert set(accepted_ids) == {
        span_id for batch in inputs.batches for span_id in batch.resolved_scope
    }
    assert {a.batch_id for a in inputs.acceptances} == set(BATCH_COUNTS)
    assert {a.reviewer for a in inputs.acceptances} == {REVIEWER}
    # One acceptance action per batch, so one timestamp within each and nine
    # across the file — a later acceptance must not restamp an earlier one.
    # The two Proficiency batches were accepted three seconds apart, which is
    # what makes the distinctness assertion below worth keeping.
    for batch_id, counts in BATCH_COUNTS.items():
        stamps = {a.accepted_at for a in inputs.acceptances if a.batch_id == batch_id}
        assert len(stamps) == 1, batch_id
        assert (
            len([a for a in inputs.acceptances if a.batch_id == batch_id])
            == counts["spans"]
        )
    assert len({a.accepted_at for a in inputs.acceptances}) == len(BATCH_COUNTS)


def test_the_accepted_scope_and_counts_are_exact() -> None:
    """The scope the Owner authorized, measured rather than described."""
    oracle = load_oracle(ARTIFACT_PATH)
    rep = oracle.representation

    assert len(oracle.spans) == SPANS
    assert len(rep.records) == RECORDS
    assert len(rep.components) == COMPONENTS
    assert len(rep.prose_bindings) == PROSE_BINDINGS
    assert len(rep.relationships) == RELATIONSHIPS
    assert len(rep.references) == REFERENCES
    assert len(rep.provenance) == PROVENANCE

    facts = sum(
        len(c.facts) + sum(len(o.facts) for o in c.options) for c in rep.components
    )
    assert facts == FACTS

    by_disposition = {d: 0 for d in SemanticDisposition}
    for span in oracle.spans:
        by_disposition[span.disposition] += 1
    assert by_disposition[SemanticDisposition.SUBSTANTIVE] == SUBSTANTIVE
    assert by_disposition[SemanticDisposition.SUPPORTING_AUTHORITY] == SUPPORTING
    assert by_disposition[SemanticDisposition.UNRESOLVED] == 0
    assert by_disposition[SemanticDisposition.NON_MECHANICAL] == NON_MECHANICAL


def test_the_artifact_is_accepted_authority_not_a_proposal() -> None:
    """Structurally accepted, and carrying no proposal-only shape.

    ``artifact_kind`` is the legible check; the key set is the one that cannot
    be defeated by editing a field. Review state is absent from the payload
    entirely — it is evidence, not identity — so the in-memory spans are what
    carry ``ACCEPTED``.
    """
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert raw["artifact_kind"] == ACCEPTED_ARTIFACT_KIND
    for proposal_only in (
        "proposed_spans",
        "proposed_representation",
        "proposal_origin",
    ):
        assert proposal_only not in raw
    assert "acceptance" in raw and "obligations" in raw
    assert all("review_state" not in s for s in raw["spans"])

    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert all(s.review_state is ReviewState.ACCEPTED for s in inputs.oracle.spans)


def test_each_batch_still_states_the_schema_it_was_reviewed_under() -> None:
    """The declaration follows the newest acceptance; the anchors do not move.

    An accepted artifact records the contract a human reviewed it under, and
    that record is per batch, not per file. ``conditions-1`` was reviewed under
    schema 3, ``hazards-1`` under schema 5, ``actions-1`` under schema 7,
    ``attitudes-1`` under schema 8, ``areas-of-effect-1`` under schema 9,
    ``cover-1`` under schema 10, ``speed-1`` under schema 11 and both
    Proficiency batches under schema 15, so those are the nine anchors — and
    restamping any of them to match whatever the build currently implements is
    exactly the attack ``BatchSchemaAnchor`` exists to refuse. Accepting
    ``proficiency-1`` moved the file's *declaration* to schema 15, because that
    is the schema the newest acceptance was reviewed under; it did not touch
    any earlier anchor, which is the whole reason they sit beside the batches
    rather than in the header. Two batches share the schema-15 anchor, which is
    correct: they were reviewed under one contract and accepted in one sitting,
    destinations first.

    The anchors are also the only place the artifact records acceptance
    *order*: ``batches`` comes back in canonical id order, so ``actions-1``
    sorts first while having been accepted third, and ``cover-1`` sorts fifth
    while having been accepted sixth.

    The retained succession is the one that has actually run: schema
    3 → 4 → 5 → … → 14 → 15, one row per crossing, never collapsed into a
    transition the registry has no row for.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.schema_version == SCHEMA_15_VERSION
    assert inputs.oracle.schema_hash == SCHEMA_15_HASH

    assert [a.batch_id for a in inputs.schema_anchors] == [
        BATCH_ID,
        HAZARDS_BATCH_ID,
        ACTIONS_BATCH_ID,
        ATTITUDES_BATCH_ID,
        AREAS_BATCH_ID,
        COVER_BATCH_ID,
        SPEED_BATCH_ID,
        PROFICIENCY_DESTINATIONS_BATCH_ID,
        PROFICIENCY_BATCH_ID,
    ]
    assert sorted(b.batch_id for b in inputs.batches) != [
        a.batch_id for a in inputs.schema_anchors
    ], "canonical order and acceptance order must not be conflated"
    anchors = {a.batch_id: a for a in inputs.schema_anchors}
    for batch_id, version, schema_hash, identity in (
        (BATCH_ID, SCHEMA_3_VERSION, SCHEMA_3_HASH, PROPOSAL_IDENTITY),
        (HAZARDS_BATCH_ID, SCHEMA_5_VERSION, SCHEMA_5_HASH, HAZARDS_PROPOSAL_IDENTITY),
        (ACTIONS_BATCH_ID, SCHEMA_7_VERSION, SCHEMA_7_HASH, ACTIONS_PROPOSAL_IDENTITY),
        (
            ATTITUDES_BATCH_ID,
            SCHEMA_8_VERSION,
            SCHEMA_8_HASH,
            ATTITUDES_PROPOSAL_IDENTITY,
        ),
        (AREAS_BATCH_ID, SCHEMA_9_VERSION, SCHEMA_9_HASH, AREAS_PROPOSAL_IDENTITY),
        (
            COVER_BATCH_ID,
            SCHEMA_10_VERSION,
            SCHEMA_10_HASH,
            COVER_PROPOSAL_IDENTITY,
        ),
        (
            SPEED_BATCH_ID,
            SCHEMA_11_VERSION,
            SCHEMA_11_HASH,
            SPEED_PROPOSAL_IDENTITY,
        ),
        (
            PROFICIENCY_DESTINATIONS_BATCH_ID,
            SCHEMA_15_VERSION,
            SCHEMA_15_HASH,
            PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY,
        ),
        (
            PROFICIENCY_BATCH_ID,
            SCHEMA_15_VERSION,
            SCHEMA_15_HASH,
            PROFICIENCY_PROPOSAL_IDENTITY,
        ),
    ):
        assert anchors[batch_id].schema_version == version, batch_id
        assert anchors[batch_id].schema_hash == schema_hash, batch_id
        assert anchors[batch_id].proposal_identity == identity, batch_id

    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
        "5d-lift-schema-7-to-8",
        "5d-lift-schema-8-to-9",
        "5d-lift-schema-9-to-10",
        "5d-lift-schema-10-to-11",
        "5d-lift-schema-11-to-12",
        "5d-lift-schema-12-to-13",
        "5d-lift-schema-13-to-14",
        "5d-lift-schema-14-to-15",
    ]
    assert (inputs.lifts[0].from_version, inputs.lifts[0].from_hash) == (
        SCHEMA_3_VERSION,
        SCHEMA_3_HASH,
    )
    assert (inputs.lifts[-1].to_version, inputs.lifts[-1].to_hash) == (
        SCHEMA_15_VERSION,
        SCHEMA_15_HASH,
    )


def test_accepted_authority_is_lifted_rather_than_restamped() -> None:
    """Both halves of the fail-closed rule, one specimen each.

    The two Proficiency batches were reviewed under schema 15. Schema 16 then
    added ``catalogue_member`` (Owner Decision 2026-09-23), so the committed
    artifact is superseded by exactly one registered crossing: reading it as
    current is a finding, and the 15 -> 16 lift carries it by identity. It has
    no relationships at all, which is why that crossing is byte-identical.

    The refusal half therefore needs a superseded specimen, and there are two
    — the frozen seven-batch prior, declaring schema 11 four registered
    crossings back, and the frozen schema-3 specimen at the far end of the
    same rule. Both are asserted, because a lift that worked over one
    crossing and a lift that worked over twelve are different claims.

    Accepted authority is never restamped in place. What carries an earlier
    declaration forward is the registered lift chain, not an edit: a projection
    built under a wider union is a different projection (ADR-005d Decision 6).
    The lift returns the artifact's own representation **by identity**, so the
    committed file is what the succession carried rather than something rebuilt
    to look like it. The frozen schema-3 specimen is the far end of the same
    rule — an artifact that has always needed a lift — so the refusal half is
    asserted right beside it.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.schema_version == SCHEMA_15_VERSION
    assert inputs.oracle.schema_version != REPRESENTATION_SCHEMA_VERSION
    assert inputs.oracle.representation.relationships == ()
    assert validate_schema_binding(candidate_from_accepted_inputs(inputs)) != ()
    current, current_records = lift_accepted_inputs(
        inputs, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    assert [r.lift_id for r in current_records] == crossings_from(SCHEMA_15_VERSION)
    assert current.oracle.representation is inputs.oracle.representation
    assert validate_schema_binding(candidate_from_accepted_inputs(current)) == ()
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY

    # The seven-batch prior is the specimen of the other half: it declares
    # schema 11, reading it as current is a finding, and the four registered
    # crossings between there and here close the gap without touching it.
    prior = load_accepted_inputs(FROZEN_PRIOR)
    assert prior.oracle.schema_version == SCHEMA_11_VERSION
    assert prior.oracle.schema_version != REPRESENTATION_SCHEMA_VERSION
    findings = validate_schema_binding(candidate_from_accepted_inputs(prior))
    assert findings, "reading a superseded artifact as current must be visible"
    assert any(REPRESENTATION_SCHEMA_VERSION in f for f in findings), findings

    lifted, records = lift_accepted_inputs(
        prior, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    assert [r.lift_id for r in records] == crossings_from(SCHEMA_11_VERSION)
    assert lifted.oracle.representation is prior.oracle.representation
    assert lifted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert lifted.oracle.schema_hash == representation_schema_hash()
    assert validate_schema_binding(candidate_from_accepted_inputs(lifted)) == ()
    # The frozen specimen is untouched by asking, and is the artifact the
    # seven earlier acceptances actually produced.
    assert oracle_identity(prior.oracle) == PRIOR_ORACLE_IDENTITY

    legacy = load_accepted_inputs(LEGACY_PATH)
    assert legacy.oracle.schema_version == SCHEMA_3_VERSION
    legacy_findings = validate_schema_binding(candidate_from_accepted_inputs(legacy))
    assert legacy_findings != ()
    assert any(
        REPRESENTATION_SCHEMA_VERSION in f for f in legacy_findings
    ), legacy_findings

    legacy_lifted, _ = lift_accepted_inputs(
        legacy, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    assert validate_schema_binding(candidate_from_accepted_inputs(legacy_lifted)) == ()


# ---------------------------------------------------------------------------
# 3. Strict round-trip, and every derived identity
# ---------------------------------------------------------------------------


def test_the_committed_bytes_round_trip_strictly() -> None:
    """Re-serializing what was loaded reproduces the committed payload.

    Not "loads without error": the loader rejects a missing key, an extra key,
    and an undeclared enum value, so a strict round-trip is what proves the file
    is written in exactly the canonical form the loader expects.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert accepted_inputs_payload(inputs) == raw


def test_the_accepted_candidate_reproduces_every_derived_identity() -> None:
    """The committed artifact derives the projection the Owner authorized.

    This is the direction that matters: committed bytes a reviewer accepted
    become the candidate that gets persisted. If the artifact derived a
    different projection than the one reviewed, acceptance would name one thing
    and the build would produce another.

    Asserted **under the schema the artifact declares**, which the two
    Proficiency acceptances have brought level with the schema this build
    implements. Level is not the invariant either way: the projection a
    reviewer accepted is the one derived from the artifact as it was declared,
    and the test above asserts separately whether that declaration is current.

    Both pins moved when the Proficiency batches were accepted, and had to:
    the projection covers strictly more records under a schema whose
    declaration is itself identity-bearing (ADR-005d Decision 6). The property
    is not that they never move — it is that they move only when an Owner
    accepted something.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    assert identified.projection_uuid == PROJECTION_UUID
    assert identified.payload_hash == PROJECTION_PAYLOAD_HASH
    assert len(identified.record_ids) == RECORDS
    assert len(identified.component_ids) == COMPONENTS
    assert len(identified.fact_ids) == FACTS


def test_the_lift_carries_the_artifact_without_touching_its_content() -> None:
    """The authorized succession, and exactly what it is allowed to change.

    One thing moves: the oracle's declared ``(schema_version, schema_hash)``.
    Every element is carried **by identity rather than by transformation**, and
    ``verify_lift`` has already proved their canonical payloads byte-identical
    under both contracts before this returns.

    The projection UUID does move, and that is correct rather than a leak: the
    schema declaration is identity-bearing (ADR-005d Decision 6), so a
    projection built under a wider contract is a different projection. What may
    not move — the semantic coordinates the Owner accepted — is asserted in
    ``test_every_accepted_semantic_coordinate_survives_the_lift``.
    """
    inputs = load_accepted_inputs(LEGACY_PATH)
    lifted, records = lift_accepted_inputs(
        inputs, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    # Every registered crossing between the schema this artifact was reviewed
    # under and the one this build implements, oldest first. The chain is not
    # collapsed: a single record would name a transition the registry has no row
    # for, and would assert the artifact never crossed the schemas in between.
    assert [r.lift_id for r in records] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
        "5d-lift-schema-7-to-8",
        "5d-lift-schema-8-to-9",
        "5d-lift-schema-9-to-10",
        "5d-lift-schema-10-to-11",
        "5d-lift-schema-11-to-12",
        "5d-lift-schema-12-to-13",
        "5d-lift-schema-13-to-14",
        "5d-lift-schema-14-to-15",
        "5d-lift-schema-15-to-16",
        "5d-lift-schema-16-to-17",
    ]
    for record in records:
        assert set(record.verified_collections) == REPRESENTATION_COLLECTIONS
    # The extent the lift proved, asserted against the representation itself.
    # The record no longer repeats it back as element counts: once later batches
    # merge, nothing can re-derive the pre-lift extent to check them against
    # (#137 round 3).
    assert len(inputs.oracle.representation.components) == CONDITIONS["components"]
    assert len(inputs.oracle.representation.records) == CONDITIONS["records"]

    # Carried by identity, never transformed.
    assert lifted.oracle.representation is inputs.oracle.representation
    assert lifted.oracle.spans == inputs.oracle.spans
    assert lifted.oracle.obligations == inputs.oracle.obligations
    # Review evidence is not a review, so a succession may not edit it.
    assert lifted.batches == inputs.batches
    assert lifted.acceptances == inputs.acceptances
    assert lifted.batches[0].proposal_identity == PROPOSAL_IDENTITY

    # Only the declaration moved, and it now names current authority.
    assert lifted.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert lifted.oracle.schema_hash == representation_schema_hash()
    candidate = candidate_from_accepted_inputs(lifted)
    assert validate_schema_binding(candidate) == ()

    identified = identify_projection(candidate)
    assert len(identified.record_ids) == CONDITIONS["records"]
    assert len(identified.component_ids) == CONDITIONS["components"]
    assert len(identified.fact_ids) == CONDITIONS["facts"]
    # A wider contract is a different projection, as Decision 6 requires, and
    # so is a wider *scope*: neither the pre-lift nor the post-lift identity of
    # the specimen is the identity the committed two-batch artifact derives.
    assert identified.projection_uuid != PROJECTION_UUID


def test_every_accepted_semantic_coordinate_survives_the_lift() -> None:
    """Zero movement, stated over the coordinates the Owner accepted.

    Owner Decision 2026-08-24: a previously accepted fact key or provenance
    coordinate may not move. This is that invariant as an exact assertion over
    the committed bytes rather than a count — every stored fact, qualifier,
    prose-binding and reference coordinate must re-derive exactly from the
    lifted representation.
    """
    inputs = load_accepted_inputs(LEGACY_PATH)
    lifted, _ = lift_accepted_inputs(
        inputs, (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    )
    stored = {
        tuple(claim["target_key"])
        for claim in json.loads(LEGACY_PATH.read_text(encoding="utf-8"))[
            "representation"
        ]["provenance"]
    }

    derived: set[tuple[str, ...]] = set()
    for component in lifted.oracle.representation.components:
        key = (component.record_key, component.semantic_key)
        derived.add(key)
        for fact in component.facts:
            derived.add(fact_target_key(*key, fact))
        for option in component.options:
            for fact in option.facts:
                derived.add(fact_target_key(*key, fact, option.semantic_key))
        for qualifier in component.fact_qualifiers:
            derived.add(
                fact_qualifier_target_key(
                    *key, qualifier.fact_key, qualifier.option_key
                )
            )
    for binding in lifted.oracle.representation.prose_bindings:
        derived.add(prose_binding_target_key(binding))
    for reference in lifted.oracle.representation.references:
        derived.add(reference_target_key(reference))
    for record in lifted.oracle.representation.records:
        derived.add((record.semantic_key,))

    assert not stored - derived, sorted(stored - derived)


def test_review_evidence_is_not_identity_bearing() -> None:
    """Reviewer and timestamp must not reach the oracle identity.

    Re-reviewing an unchanged classification must not remint a projection
    (#137 acceptance criterion 11), which is why the oracle half excludes
    evidence. Asserted by rebuilding the oracle identity from the file and
    comparing it to the pinned value while the evidence is right there beside
    it.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY
    assert load_oracle(ARTIFACT_PATH) == inputs.oracle
    assert inputs.acceptances, "the evidence half must still be present"
    assert inputs.batches


# ---------------------------------------------------------------------------
# 4. The refused candidates
# ---------------------------------------------------------------------------


def test_no_refused_candidate_is_selectable() -> None:
    """Six identities were refused by review; none may reach the build.

    Selection is by what a committed artifact *names*, so the check is that no
    committed batch names any of them — there is no other route by which a
    refused proposal could become authority.
    """
    named = {
        b.proposal_identity
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        for b in load_accepted_inputs(p).batches
    }
    assert named == {
        PROPOSAL_IDENTITY,
        HAZARDS_PROPOSAL_IDENTITY,
        ACTIONS_PROPOSAL_IDENTITY,
        ATTITUDES_PROPOSAL_IDENTITY,
        AREAS_PROPOSAL_IDENTITY,
        COVER_PROPOSAL_IDENTITY,
        SPEED_PROPOSAL_IDENTITY,
        PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY,
        PROFICIENCY_PROPOSAL_IDENTITY,
        # The clean restart's Owner-accepted batches (other release).
        proposal_identity(load_proposal(CONDITIONS_PILOT_PROPOSAL)),
        proposal_identity(load_proposal(ACTIONS_PILOT_PROPOSAL)),
        proposal_identity(load_proposal(REFERENCE_CLOSURE_PROPOSAL)),
        proposal_identity(load_proposal(MOVEMENT_CLOSURE_PROPOSAL)),
        proposal_identity(load_proposal(COMBAT_TURN_1_PROPOSAL)),
        proposal_identity(load_proposal(DAMAGE_AND_HIT_POINTS_PROPOSAL)),
        # (Combat, damage and breaking: replaced by the finite-reference
        # routes proposal, below.)
        # (Checks, actions and rests; core play completion and dependencies;
        # character creation foundations; spellcasting: replaced by the
        # remaining-references proposals, below.)
        # (Character origins and feats: replaced by the finite-reference
        # atoms proposal, below.)
        # (Equipment: replaced by the cited-targets proposal, below.)
        proposal_identity(load_proposal(RULES_GLOSSARY_COMPLETION_PROPOSAL)),
        # (Classes: replaced by the finite-reference atoms proposal, below.)
        proposal_identity(load_proposal(CLASS_OPTION_CATALOGUES_PROPOSAL)),
        proposal_identity(load_proposal(SPELL_DESCRIPTIONS_PROPOSAL)),
        proposal_identity(load_proposal(GAMEPLAY_TOOLBOX_PROPOSAL)),
        proposal_identity(load_proposal(MAGIC_ITEMS_PROPOSAL)),
        # The superseded ``574662e9-0ef`` file's first seventeen, regenerated
        # for that release.
        *(
            proposal_identity(
                load_proposal(NOTES / f"issue-5d-{batch}-REGEN-574662e9-PROPOSAL.json")
            )
            for batch in list(BATCHES)[:17]
        ),
        # The Monsters-corrected release: the twenty regenerated proposals
        # the Owner approved, then Monsters, then Animals, with the Equipment
        # proposal since replaced by the Owner-accepted cited-targets one and
        # eight more, Monsters among them, by the Owner-accepted
        # remaining-references ones, and the Animals proposal by the
        # Owner-accepted part-catalogue one; then the Owner-accepted
        # framing-coverage batch appended, then the Owner-accepted Character
        # Creation catalogue batch; then five proposals replaced by the
        # Owner-accepted finite-reference atoms ones, and two (Core play
        # dependencies, Monsters) by the Owner-accepted Playing the Game atoms
        # ones, and Equipment by the Owner-accepted class-eligibility one,
        # and Combat, damage and breaking by the Owner-accepted
        # finite-reference routes one, at its position.
        *(
            regenerated
            for batch, (regenerated, _) in BATCHES.items()
            if batch not in ("equipment", FINITE_REFERENCE_ROUTES.COMBAT_BATCH)
            and batch not in REMAINING.PROPOSALS
            and batch not in FINITE_REFERENCE.PROPOSALS
            and batch not in PLAYING_THE_GAME.PROPOSALS
        ),
        *(
            recorded
            for batch, (recorded, _) in REMAINING.PROPOSALS.items()
            if batch not in FINITE_REFERENCE.PROPOSALS
            and batch not in PLAYING_THE_GAME.PROPOSALS
        ),
        ANIMALS_CATALOGUE.IDENTITY,
        *(accepted for accepted, _ in EQUIPMENT_CLASS_ELIGIBILITY.PROPOSALS.values()),
        FRAMING.IDENTITY,
        CHARACTER_CREATION.IDENTITY,
        *(
            accepted
            for batch, (accepted, _) in FINITE_REFERENCE.PROPOSALS.items()
            if batch not in PLAYING_THE_GAME.PROPOSALS
        ),
        *(accepted for accepted, _ in PLAYING_THE_GAME.PROPOSALS.values()),
        FINITE_REFERENCE_ROUTES.COMBAT_IDENTITY,
        # The official-order release: the same twenty-four batches natively
        # rebound, as named by the Owner-accepted candidate (SHA-256
        # ``8a6a9a9c…``), in its batch order.
        "51d72a0e059958dd33b2912e14c628aad6c2a9c02f1af8f070b7d3dcd33cf014",
        "9241c2b876b8cee294948463d6fde415b0741e32b91fbb4301dc50e8d75f8e69",
        "d4c62a9c6a84ec60f5a483080c5c984f4175a9ec3cc1a4eb920acbe138fec323",
        "0d7648019d7d51d72fc50ea7a98709bd81561e8d68a4297dfeadf44358e5c2c9",
        "6120f64771725581d478b9bdcd29a13588ee3dd9f9776c42d2628c2ad6bf3702",
        "d96c50a32e269ae17bac1b312b643ba468ed2065e89fcfef7030ce59a55a113a",
        "6d11f46a95c5a03d519be29ccaea43895ede4930d678116c7b0615e9a24236c2",
        "ab357393ce9c3d3bcbc06e7f18ff9c6cadb13c852fdb8dce09fb0ec43737df54",
        "b11159c1f9663a28b64e1351f7c1a954cb42de2fd1e79e8818bff965f942df51",
        "252dd80fe05787a50381f8c0740e0bfbadcbf8e3799acffc722b1200190336c8",
        "cb758b9991e8a7ad859091d8d418f2204dd3a8f0eb9bc7c15fb28cf09c2b37fb",
        "96afa186fb7be74d70bd6864327efc7ad7f91ecd97dc02a7b376382233615bd2",
        "bff0773c8f2bd790265a229eafc31f03f2b920cbef7e792291f3c9750b57b037",
        "41d03ab49b5c0707c97625b94f0115a274f71cc869c5bb8b26832cd723a0e5f1",
        "390f63672ea035abb0c8f0ae2efd4cffda81753df8089daee372931b5618d728",
        "ea611567cce289a74b71a83ba26890ac09e3ba31f3ad8ed2b35a84d816d5cb78",
        "8a5add7321cd98d1d83f1761aaa91acc6504a7a2e7f1a9bbd0022f10bf81e49a",
        "54a402acd35a15887b94f286a30804a87dd32e92e91d2b075bbb2367324eed5a",
        "bc559c6ec6bd1e84a000c5656682067b24a9cd868d98440ac19ec1e61ed2c48a",
        "ba2bae69724d8948e2195ed5a0fca90132c984bcce47445d5276fb25002f238a",
        "c4a017a7909ae1198844b1117fe45c06b08b5d2ac04ee72f5f1db69be647d000",
        "38dc2df713e64a8da6a7713f19b4ecb4ce58fbd47303de2c68d2b9195b2db34f",
        "93c816fba0698f551123cac5124f161e7b1ef2c7780b8d5bd35ab42dd4205d83",
        "4783913aeda24baed59b4d5c61487f6cfb64a25563d6203ab8d6ff8c3873fb8e",
    }
    for refused in REFUSED:
        assert refused not in named
    assert PROPOSAL_IDENTITY not in REFUSED
    # The rejected schema-4 hazards proposal is in REFUSED, and the accepted
    # hazards batch is a different identity against a different schema.
    assert HAZARDS_PROPOSAL_IDENTITY not in REFUSED
    assert ACTIONS_PROPOSAL_IDENTITY not in REFUSED
    # Likewise the two superseded ``attitudes-1`` revisions: what was accepted
    # is a third identity, reviewed after both corrections landed.
    assert ATTITUDES_PROPOSAL_IDENTITY not in REFUSED
    assert AREAS_PROPOSAL_IDENTITY not in REFUSED
    assert COVER_PROPOSAL_IDENTITY not in REFUSED
    assert SPEED_PROPOSAL_IDENTITY not in REFUSED
    assert PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY not in REFUSED
    assert PROFICIENCY_PROPOSAL_IDENTITY not in REFUSED


# ---------------------------------------------------------------------------
# 5. The corpus is incomplete, so nothing publishes
# ---------------------------------------------------------------------------


def test_the_accepted_authority_covers_the_nine_accepted_batches_only() -> None:
    """Why the release still cannot publish, stated at the artifact level.

    Every accepted record belongs to one of the nine accepted batches. The
    publication gate compares accepted authority against the *whole* persisted
    projection, so a projection over the full SRD still carries records this
    artifact does not accept — the end-to-end refusal is asserted in
    ``test_production_release`` and ``test_runtime_production_release``.
    """
    oracle = load_oracle(ARTIFACT_PATH)
    keys = sorted(r.semantic_key for r in oracle.representation.records)
    assert len(keys) == RECORDS

    # Fifteen conditions, five hazards, twelve actions, three attitudes, six
    # areas of effect, the glossary entry that defines each of the five lists,
    # the ``Cover`` and ``Speed`` glossary rules — neither of which names a
    # list of its own, though only ``Cover`` added a record without adding a
    # typed family — and the five records the two Proficiency batches brought
    # in: the four reviewed destinations and the ``Proficiency`` rule the
    # Expertise destination cites. None of the five opens a typed family, so
    # they fall through to the leftover list below rather than into a prefix
    # group. Nothing from any other CRD Issue 5d batch is in here.
    conditions = [k for k in keys if k.startswith("condition.")]
    hazards = [k for k in keys if k.startswith("hazard.")]
    actions = [k for k in keys if k.startswith("action.")]
    attitudes = [k for k in keys if k.startswith("attitude.")]
    areas = [k for k in keys if k.startswith("area_of_effect.")]
    assert len(conditions) == 15, conditions
    assert hazards == [
        "hazard.burning",
        "hazard.dehydration",
        "hazard.falling",
        "hazard.malnutrition",
        "hazard.suffocation",
    ], hazards
    assert actions == [
        "action.attack",
        "action.dash",
        "action.disengage",
        "action.dodge",
        "action.help",
        "action.hide",
        "action.influence",
        "action.magic",
        "action.ready",
        "action.search",
        "action.study",
        "action.utilize",
    ], actions
    assert attitudes == [
        "attitude.friendly",
        "attitude.hostile",
        "attitude.indifferent",
    ], attitudes
    assert areas == [
        "area_of_effect.cone",
        "area_of_effect.cube",
        "area_of_effect.cylinder",
        "area_of_effect.emanation",
        "area_of_effect.line",
        "area_of_effect.sphere",
    ], areas
    assert sorted(
        set(keys)
        - set(conditions)
        - set(hazards)
        - set(actions)
        - set(attitudes)
        - set(areas)
    ) == [
        "glossary.action",
        "glossary.area_of_effect",
        "glossary.attitude",
        "glossary.challenge_rating",
        "glossary.condition",
        "glossary.cover",
        "glossary.expertise",
        "glossary.hazard",
        "glossary.speed",
        "play.actions",
        "play.proficiency",
        "play.skills",
    ], keys

    # One obligation per accepted record, and no obligation over a record this
    # artifact does not accept.
    assert {o.record_key for o in oracle.obligations} == set(keys)


def test_the_unresolved_citations_are_exactly_these_ten_and_these_four() -> None:
    """The publication residue, measured on the live artifact rather than argued.

    Until ``speed-1`` was accepted this count was arithmetic over two sets — a
    committed prior and an unaccepted draft, which nothing in :mod:`oracle`
    merges — so it could only be stated in a checkpoint. It is now a property of
    committed authority, and is asserted as one.

    The residue moves in both directions and ``speed-1`` moved it both ways at
    once: it defines ``glossary.speed``, so the ``Speed`` citation ``actions-1``
    printed in Dash finally resolves, and it emits nine citations of its own, so
    the total went from two to ten. Both halves are asserted, because "ten" is
    also reachable by never having resolved anything.

    The Proficiency batches left that ten **unchanged** and added a residue of
    a second kind: four citations naming no target at all. They are counted
    separately because they fail differently — a named-but-undefined target is
    a target somebody could satisfy by accepting the batch that defines it,
    while an empty target is a citation whose destination has not been
    identified. Neither was closed by inventing anything, which is what the
    empty ``reference_resolutions`` asserts: no resolution decision was
    invoked for any of the fourteen.
    """
    oracle = load_oracle(ARTIFACT_PATH)
    defined = {r.semantic_key for r in oracle.representation.records}
    dangling = sorted(
        {
            reference.target_record_key
            for reference in oracle.representation.references
            if reference.target_record_key
            and reference.target_record_key not in defined
        }
    )
    assert dangling == UNRESOLVED_TARGETS

    # The empty-target half, which the comprehension above deliberately skips:
    # an empty string is not an unknown key, and folding the two together
    # would report a citation with no destination as a target named
    # ``''``.
    assert (
        sorted(
            (reference.scope_key, reference.source_text)
            for reference in oracle.representation.references
            if not reference.target_record_key
        )
        == UNRESOLVED_CITATIONS
    )
    assert oracle.reference_resolutions == ()

    # The citation this batch closed: printed by an ``actions-1`` record, and
    # answered by a record ``speed-1`` brought in.
    assert "glossary.speed" in defined
    assert [
        reference.from_record_key
        for reference in oracle.representation.references
        if reference.target_record_key == "glossary.speed"
    ] == ["action.dash"]


def test_a_later_batch_extended_this_artifact_rather_than_adding_one() -> None:
    """The extension contract, now demonstrated eight times over.

    ``accept_proposal`` takes prior accepted inputs and merges, and the resolver
    refuses two artifacts for one release. Together those made "extend the file"
    the only representable way to add a batch. ``hazards-1`` did exactly that,
    ``actions-1`` did it again, ``attitudes-1`` did it a third time,
    ``areas-of-effect-1`` a fourth, ``cover-1`` a fifth, ``speed-1`` a sixth,
    and the two Proficiency batches a seventh and an eighth: nine batches, one
    file, one release.

    Acceptance order is asserted through ``schema_anchors`` rather than through
    ``batches``, which is canonically keyed — ``actions-1`` sorts first and was
    accepted third, ``cover-1`` sorts fifth and was accepted sixth, so reading
    order out of ``batches`` would assert the opposite of the truth.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert sorted(b.batch_id for b in inputs.batches) == sorted(BATCH_COUNTS)
    assert [a.batch_id for a in inputs.schema_anchors] == [
        BATCH_ID,
        HAZARDS_BATCH_ID,
        ACTIONS_BATCH_ID,
        ATTITUDES_BATCH_ID,
        AREAS_BATCH_ID,
        COVER_BATCH_ID,
        SPEED_BATCH_ID,
        PROFICIENCY_DESTINATIONS_BATCH_ID,
        PROFICIENCY_BATCH_ID,
    ]
    same_release = [
        p
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        if load_accepted_inputs(p).oracle.binding.release_version == RELEASE_VERSION
    ]
    assert same_release == [ARTIFACT_PATH]
    # The frozen specimen is a test fixture, not committed authority: it must
    # never appear in the oracle directory, because two artifacts claiming one
    # release is precisely what the resolver refuses.
    assert LEGACY_PATH.parent.name == "data"
    assert LEGACY_PATH not in set(COMMITTED_ORACLE_DIR.glob("*.json"))
    assert FROZEN_PRIOR.parent.name == "data"
    assert FROZEN_PRIOR not in set(COMMITTED_ORACLE_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# 6. The complete acceptance record, not merely the accepted content
# ---------------------------------------------------------------------------


def _content_identities(path: pathlib.Path) -> tuple[str, str]:
    """SHA-256 of the canonical LF content, and Git's blob id for it.

    Both are properties of the *content*. The raw on-disk digest is not: a
    working copy predating ``.gitattributes``' ``eol=lf`` can hold CRLF and
    hash differently while holding the same committed file.
    """
    canonical = path.read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(  # noqa: S324 - Git's object id, not a security digest
        b"blob " + str(len(canonical)).encode() + b"\x00" + canonical
    ).hexdigest()
    return hashlib.sha256(canonical).hexdigest(), blob


def test_the_whole_acceptance_record_is_pinned_not_only_the_oracle() -> None:
    """An unreviewed edit anywhere in this file fails here.

    The oracle identity is deliberately blind to acceptance evidence, so pinning
    it alone would let someone rewrite a reviewer, a timestamp, a batch rule, a
    resolved scope, an anchor or a lift and still pass every other test in this
    module. The file's own content digest and Git blob close that, and they are
    asserted beside the evidence they protect so a reader can see what would
    have slipped through.
    """
    content_sha, blob = _content_identities(ARTIFACT_PATH)
    assert content_sha == ARTIFACT_CONTENT_SHA256
    assert blob == ARTIFACT_BLOB

    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert oracle_identity(inputs.oracle) == ORACLE_IDENTITY

    # The evidence the two file-level pins are what actually protect.
    assert {b.batch_id: b.proposal_identity for b in inputs.batches} == {
        BATCH_ID: PROPOSAL_IDENTITY,
        HAZARDS_BATCH_ID: HAZARDS_PROPOSAL_IDENTITY,
        ACTIONS_BATCH_ID: ACTIONS_PROPOSAL_IDENTITY,
        ATTITUDES_BATCH_ID: ATTITUDES_PROPOSAL_IDENTITY,
        AREAS_BATCH_ID: AREAS_PROPOSAL_IDENTITY,
        COVER_BATCH_ID: COVER_PROPOSAL_IDENTITY,
        SPEED_BATCH_ID: SPEED_PROPOSAL_IDENTITY,
        PROFICIENCY_DESTINATIONS_BATCH_ID: (PROFICIENCY_DESTINATIONS_PROPOSAL_IDENTITY),
        PROFICIENCY_BATCH_ID: PROFICIENCY_PROPOSAL_IDENTITY,
    }
    assert {a.reviewer for a in inputs.acceptances} == {REVIEWER}
    assert {a.accepted_at for a in inputs.acceptances} == {
        "2026-08-23T09:53:55Z",
        "2026-09-03T10:58:59Z",
        "2026-09-09T20:45:32Z",
        "2026-09-10T18:53:49Z",
        "2026-09-11T05:30:17Z",
        "2026-09-11T17:14:44Z",
        "2026-09-12T18:26:58Z",
        "2026-09-20T02:50:55Z",
        "2026-09-20T02:50:58Z",
    }
    assert [a.schema_version for a in inputs.schema_anchors] == [
        SCHEMA_3_VERSION,
        SCHEMA_5_VERSION,
        SCHEMA_7_VERSION,
        SCHEMA_8_VERSION,
        SCHEMA_9_VERSION,
        SCHEMA_10_VERSION,
        SCHEMA_11_VERSION,
        SCHEMA_15_VERSION,
        SCHEMA_15_VERSION,
    ]
    assert [lift.lift_id for lift in inputs.lifts] == [
        "5d-lift-schema-3-to-4",
        "5d-lift-schema-4-to-5",
        "5d-lift-schema-5-to-6",
        "5d-lift-schema-6-to-7",
        "5d-lift-schema-7-to-8",
        "5d-lift-schema-8-to-9",
        "5d-lift-schema-9-to-10",
        "5d-lift-schema-10-to-11",
        "5d-lift-schema-11-to-12",
        "5d-lift-schema-12-to-13",
        "5d-lift-schema-13-to-14",
        "5d-lift-schema-14-to-15",
    ]
    assert all(b.rule.strip() for b in inputs.batches)

    # Two kinds of evidence the oracle identity is equally blind to, both
    # first written by the Proficiency acceptances: the one registered
    # semantic-policy crossing, and which review unit each batch discharged.
    assert [t.transition_id for t in inputs.policy_transitions] == ["5d-policy-1-to-2"]
    assert [(r.unit_id, r.batch_id) for r in inputs.review_unit_acceptances] == [
        (
            "proficiency-destinations-1-actions-section",
            PROFICIENCY_DESTINATIONS_BATCH_ID,
        ),
        (
            "proficiency-destinations-1-challenge-rating",
            PROFICIENCY_DESTINATIONS_BATCH_ID,
        ),
        (
            "proficiency-destinations-1-expertise",
            PROFICIENCY_DESTINATIONS_BATCH_ID,
        ),
        (
            "proficiency-destinations-1-skills-table",
            PROFICIENCY_DESTINATIONS_BATCH_ID,
        ),
        ("proficiency-1-section", PROFICIENCY_BATCH_ID),
    ]


def test_the_oracle_identity_alone_would_not_have_caught_an_evidence_edit() -> None:
    """Why the file-level pins above exist, demonstrated rather than asserted.

    Done entirely in memory: the committed artifact is never mutated. Rewriting
    a reviewer produces different accepted *inputs* — a different file, which
    the pins above would refuse — while leaving the accepted *oracle* and its
    identity untouched, which is exactly the gap the pins close.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    forged = replace(
        inputs,
        acceptances=tuple(
            replace(a, reviewer="Somebody Else") for a in inputs.acceptances
        ),
    )

    assert oracle_identity(forged.oracle) == oracle_identity(inputs.oracle)
    assert accepted_inputs_payload(forged) != accepted_inputs_payload(inputs)
    # And the file on disk is untouched by any of this.
    assert _content_identities(ARTIFACT_PATH) == (
        ARTIFACT_CONTENT_SHA256,
        ARTIFACT_BLOB,
    )


def test_the_pinned_identities_survive_a_crlf_checkout_and_the_raw_digest_does_not(
    tmp_path: pathlib.Path,
) -> None:
    """The two pins are content identities; the raw on-disk digest is not.

    ``.gitattributes`` declares ``eol=lf``, but a working copy predating that
    attribute — or a checkout made with ``core.autocrlf=true`` — holds the same
    committed JSON with CRLF line endings. Verification must fail on an edited
    *artifact*, never on a checkout's line endings, so every pinned comparison
    canonicalizes first. This is the regression for that: it asserts the raw
    digest genuinely moves, so the test would still fail if canonicalization
    were dropped and the two digests happened to coincide.

    The committed file is never touched. The CRLF form is built in ``tmp_path``
    and is not committed anywhere — a CRLF copy in the tree would be a second
    artifact claiming one release, which the resolver refuses outright.
    """
    committed = ARTIFACT_PATH.read_bytes()
    assert b"\r\n" not in committed, "the committed artifact must be LF"

    crlf_copy = tmp_path / ARTIFACT_NAME
    crlf_copy.write_bytes(committed.replace(b"\n", b"\r\n"))

    # The raw digests differ, which is exactly why a raw digest cannot decide.
    assert (
        hashlib.sha256(crlf_copy.read_bytes()).hexdigest()
        != hashlib.sha256(committed).hexdigest()
    )

    # The identities that are pinned do not move.
    assert _content_identities(crlf_copy) == (ARTIFACT_CONTENT_SHA256, ARTIFACT_BLOB)

    # And the JSON content is the same content, not merely the same hash.
    reloaded = load_accepted_inputs(crlf_copy)
    committed_inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert accepted_inputs_payload(reloaded) == accepted_inputs_payload(
        committed_inputs
    )
    assert oracle_identity(reloaded.oracle) == ORACLE_IDENTITY
