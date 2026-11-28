"""Cover and range claims that contradict geometry are refused (issue #211,
acceptance 11). The check decides no rules outcome; it only refuses
contradictions."""

from __future__ import annotations

import pytest

from afterworlds.mapper import fixture
from afterworlds.mapper.geometry import sight_line
from afterworlds.mapper.models import Snapshot, Token
from afterworlds.pipeline.rpg.spatial_claims import (
    ClaimContradictsGeometry,
    SpatialClaim,
    check_claim,
)


def _scene() -> Snapshot:
    truth = fixture.build()
    extra = (
        Token(
            token_id="near", glyph="N", ref="creature:n", side="hostile", square=(3, 4)
        ),
        Token(
            token_id="inside",
            glyph="I",
            ref="creature:i",
            side="hostile",
            square=(1, 9),
        ),
        Token(
            token_id="outside",
            glyph="O",
            ref="creature:o",
            side="hostile",
            square=(2, 9),
        ),
        Token(
            token_id="archer", glyph="A", ref="character:a", side="party", square=(3, 6)
        ),
        Token(
            token_id="far", glyph="F", ref="creature:f", side="hostile", square=(7, 6)
        ),
    )
    return truth.model_copy(update={"tokens": (*truth.tokens, *extra)})


def test_the_scene_geometry_this_test_relies_on() -> None:
    truth = _scene()
    behind = sight_line(truth, (3, 6), (7, 6), ignore=("archer", "far"))
    assert behind.clear and behind.obstruction == "half"
    assert "feature:barrels" in behind.passes_through
    assert not sight_line(truth, (1, 9), (2, 9), ignore=("inside", "outside")).clear


@pytest.mark.parametrize(
    ("claim", "reason"),
    [
        (
            SpatialClaim("archer", "far", distance_ft=15),
            "they are 20 ft apart, not 15 ft",
        ),
        (
            SpatialClaim("archer", "far", cover="none"),
            "an object in the line screens half",
        ),
        (
            SpatialClaim("archer", "far", cover="total"),
            "the line between them is clear",
        ),
        (
            SpatialClaim(fixture.HERO, "near", cover="half"),
            "nothing stands between them",
        ),
        (
            SpatialClaim("inside", "outside", cover="three_quarters"),
            "the line between them is fully blocked",
        ),
        (
            SpatialClaim(fixture.HERO, "hidden-pit", cover="none"),
            "both creatures need squares on the map",
        ),
    ],
    ids=[
        "range",
        "less-than-the-barrels",
        "total-on-a-clear-line",
        "cover-from-nothing",
        "blocked",
        "not-a-creature",
    ],
)
def test_contradicting_claims_are_refused(claim: SpatialClaim, reason: str) -> None:
    with pytest.raises(ClaimContradictsGeometry) as exc:
        check_claim(_scene(), claim)
    assert exc.value.reason == reason


@pytest.mark.parametrize(
    "claim",
    [
        SpatialClaim("archer", "far", cover="half", distance_ft=20),
        SpatialClaim("archer", "far", cover="three_quarters"),
        SpatialClaim(fixture.HERO, "near", cover="none", distance_ft=10),
        SpatialClaim("inside", "outside", cover="total", distance_ft=5),
        SpatialClaim(fixture.HERO, fixture.GOBLIN),
    ],
    ids=[
        "half",
        "sojourn-may-give-more",
        "open-ground",
        "total-behind-a-wall",
        "no-claim",
    ],
)
def test_claims_that_fit_the_geometry_stand(claim: SpatialClaim) -> None:
    check_claim(_scene(), claim)
