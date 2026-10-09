"""Committed accepted authority: resolution and selection — CRD Issue 5d.

What remains after the original 5d artifact
``srd-5-2-1-corpus-36b786d8-fa2.json`` (nine batches on the retired
PDF-geometric release) was removed under Step 5 of the Recorded Owner Decision
of 21 September 2026. Its content assertions went with it; Git history retains
them. Two properties are still current:

* the retired release's identity is refused at resolution whichever half of it
  is named, while an identity the quarantine says nothing about still gets the
  ordinary "no such binding" answer; and
* every proposal identity any committed artifact names is exactly the set the
  Owner approved, so no other proposal can be selected as authority.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    committed_inputs_for,
    committed_oracle_for,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import (
    load_proposal,
    proposal_identity,
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

#: The retired original release, refused rather than resolved.
PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"

CONDITIONS_PILOT_PROPOSAL = proposal_path("conditions-pilot")
ACTIONS_PILOT_PROPOSAL = proposal_path("actions-pilot")
REFERENCE_CLOSURE_PROPOSAL = proposal_path("reference-closure")
MOVEMENT_CLOSURE_PROPOSAL = proposal_path("movement-closure")
COMBAT_TURN_1_PROPOSAL = proposal_path("combat-turn-1")
DAMAGE_AND_HIT_POINTS_PROPOSAL = proposal_path("damage-and-hit-points")
RULES_GLOSSARY_COMPLETION_PROPOSAL = proposal_path("rules-glossary-completion")
CLASS_OPTION_CATALOGUES_PROPOSAL = proposal_path("class-option-catalogues")
#: Accepted over the replacement chain, not part of it.
SPELL_DESCRIPTIONS_PROPOSAL = NOTES / "issue-5d-spell-descriptions-PROPOSAL.json"
GAMEPLAY_TOOLBOX_PROPOSAL = NOTES / "issue-5d-gameplay-toolbox-PROPOSAL.json"
MAGIC_ITEMS_PROPOSAL = NOTES / "issue-5d-magic-items-PROPOSAL.json"


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


def test_no_refused_candidate_is_selectable() -> None:
    """Exactly the approved proposals are named; nothing else may reach the build.

    Selection is by what a committed artifact *names*, so the check is the
    complete set of named proposal identities across every committed file —
    there is no other route by which an unapproved proposal could become
    authority.
    """
    named = {
        b.proposal_identity
        for p in COMMITTED_ORACLE_DIR.glob("*.json")
        for b in load_accepted_inputs(p).batches
    }
    assert named == {
        # The clean restart's Owner-accepted batches.
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
