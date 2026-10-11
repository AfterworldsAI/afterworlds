"""The Owner-approved replacement chain, as the per-batch tests read it (#132, #137).

``.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py`` recorded
``oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json``: the twenty regenerated
proposals of ``issue-5d-monsters-corrections-REPLACEMENT.py`` accepted in order
over no prior, with their 1,099 resolutions, under one Owner approval, then
Monsters and its 83 resolutions over them;
``issue-5d-animals-ACCEPT.py`` then appended Animals and its 65 resolutions,
``issue-5d-equipment-cited-targets-ACCEPT.py`` recorded the chain again with
only the Equipment proposal replaced and its 161 cited resolutions, keeping the
Animals recording (:func:`animals_recorded`) outside Equipment; and
``issue-5d-remaining-references-ACCEPT.py`` recorded it again with eight
proposals replaced, three resolutions re-keyed and 29 resolved: the file keeps
the Equipment recording (:func:`equipment_recorded`) outside those batches; and
``issue-5d-animals-part-catalogue-ACCEPT.py`` recorded it again with only the
Animals proposal replaced and its four resolutions, keeping the
remaining-references recording (:func:`remaining_recorded`) outside Animals;
and ``issue-5d-framing-coverage-ACCEPT.py`` appended the framing-coverage
batch over the Animals catalogue recording (:func:`animals_catalogue_recorded`),
with no resolution, keeping it whole; and
``issue-5d-character-creation-catalogue-ACCEPT.py`` appended the Character
Creation catalogue batch and its two resolutions over the framing-coverage
recording (:func:`framing_recorded`), keeping it whole; and
``issue-5d-finite-reference-atoms-ACCEPT.py`` recorded it again with five
proposals replaced (classes, character-origins-feats, spell-descriptions,
magic-items, monsters) and no resolution added, keeping the Character Creation
catalogue recording (:func:`character_creation_recorded`) outside them; and
``issue-5d-playing-the-game-atoms-ACCEPT.py`` recorded it again with two
proposals replaced (core-play-dependencies, monsters) and no resolution added,
keeping the finite-reference atoms recording
(:func:`finite_reference_recorded`) outside them; and
``issue-5d-equipment-class-eligibility-ACCEPT.py`` recorded it again with the
Equipment proposal replaced and no resolution added, keeping the Playing the
Game atoms recording (:func:`playing_the_game_recorded`) outside Equipment; and
``issue-5d-reference-alternatives-ACCEPT.py`` lifted it from schema 16 to 17
and appended thirteen reference resolutions, no batch changed, keeping the
Equipment class-eligibility recording (:func:`equipment_class_eligibility_recorded`)
whole; and ``issue-5d-finite-reference-routes-ACCEPT.py`` recorded it again
with the combat-damage-breaking proposal replaced in place and ten reference
resolutions appended, keeping the reference-alternatives recording
(:func:`reference_alternatives_recorded`) outside combat; and
``issue-5d-equipment-spell-references-ACCEPT.py`` appended thirteen
Equipment, cursed-item and spell reference resolutions, no batch changed,
keeping the finite-reference-routes recording
(:func:`finite_reference_routes_recorded`) whole; and
``issue-5d-final-ten-references-ACCEPT.py`` appended the final ten reference
resolutions, no batch changed, keeping the equipment-spell-references
recording (:func:`equipment_spell_references_recorded`) whole. :func:`through`
rebuilds the state after one batch through the same native seams, so each
batch's tests see what that batch was composed over, not the whole chain.
The last recorded bytes are :data:`COMMITTED_SHA256`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from collections.abc import Callable
from dataclasses import replace
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import ProjectionCandidate
from afterworlds.ingestion.mechanical.proposal import load_proposal
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_17_HASH,
    SCHEMA_17_VERSION,
    lift_path,
    verify_lift_path,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
SCRIPT = NOTES / "issue-5d-monsters-corrections-ACCEPT.py"


def _load(name: str = "monsters_corrections_accept", path: Path = SCRIPT) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


#: The recording, the Animals recording appended over it, the Equipment
#: replacement recorded over both, and the remaining-references replacement
#: recorded over that, and the Animals catalogue replacement recorded over that,
#: and the framing-coverage batch appended over that.
REPLACEMENT = _load()
ANIMALS = _load("animals_accept", NOTES / "issue-5d-animals-ACCEPT.py")
EQUIPMENT_CITED = _load(
    "equipment_cited_accept", NOTES / "issue-5d-equipment-cited-targets-ACCEPT.py"
)
REMAINING = _load(
    "remaining_references_accept", NOTES / "issue-5d-remaining-references-ACCEPT.py"
)
ANIMALS_CATALOGUE = _load(
    "animals_part_catalogue_accept",
    NOTES / "issue-5d-animals-part-catalogue-ACCEPT.py",
)
FRAMING = _load(
    "framing_coverage_accept", NOTES / "issue-5d-framing-coverage-ACCEPT.py"
)
CHARACTER_CREATION = _load(
    "character_creation_catalogue_accept",
    NOTES / "issue-5d-character-creation-catalogue-ACCEPT.py",
)
FINITE_REFERENCE = _load(
    "finite_reference_atoms_accept",
    NOTES / "issue-5d-finite-reference-atoms-ACCEPT.py",
)
PLAYING_THE_GAME = _load(
    "playing_the_game_atoms_accept",
    NOTES / "issue-5d-playing-the-game-atoms-ACCEPT.py",
)
EQUIPMENT_CLASS_ELIGIBILITY = _load(
    "equipment_class_eligibility_accept",
    NOTES / "issue-5d-equipment-class-eligibility-ACCEPT.py",
)
REFERENCE_ALTERNATIVES = _load(
    "reference_alternatives_accept",
    NOTES / "issue-5d-reference-alternatives-ACCEPT.py",
)
FINITE_REFERENCE_ROUTES = _load(
    "finite_reference_routes_accept",
    NOTES / "issue-5d-finite-reference-routes-ACCEPT.py",
)
EQUIPMENT_SPELL_REFERENCES = _load(
    "equipment_spell_references_accept",
    NOTES / "issue-5d-equipment-spell-references-ACCEPT.py",
)
FINAL_TEN_REFERENCES = _load(
    "final_ten_references_accept",
    NOTES / "issue-5d-final-ten-references-ACCEPT.py",
)
#: The bytes recorded last: the final ten reference resolutions appended.
COMMITTED_SHA256: str = FINAL_TEN_REFERENCES.RECORDED_SHA256["recorded"]
#: The current release's committed authority: this chain re-executed with every
#: input rebound to the official-order release ``5.2.1-corpus.8781d4e0-a3b`` and
#: recorded on 2026-10-07 by
#: ``.claude/review-notes/issue-5c-release-order-recording/RECORD.py``. The
#: session's published release is that release, so whatever is read against it
#: reads this file; the superseded ``ACCEPTED_PATH`` bytes are the chain's
#: historical evidence only.
CURRENT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b.json"
CURRENT_SHA256 = "def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c"
#: The Magic Items acceptance, for its one reviewed obligation enlargement,
#: which the chain now carries at the magic-items batch.
MAGIC_ITEMS = _load("magic_items_accept", NOTES / "issue-5d-magic-items-ACCEPT.py")

#: The representation schema each historical script was recorded under, for the
#: scripts that name "the build's current schema" as a target rather than a
#: pinned contract. Written out, not derived (CRD Issue 2b): the
#: reference-alternatives recording lifted to the build's schema, which was 17
#: when it was recorded on 2026-10-01; under a later build (schema 18, the G1
#: successor) an unpinned replay would lift on to 18 and no longer reproduce
#: the recorded bytes. The script itself is byte-pinned historical evidence
#: (5c delivery manifest), so its replay target is fixed here, at the replay
#: boundary, per script. Its own ``reviewed()`` re-asserts that the pinned
#: reviewed proposal states this schema, and every recorded SHA-256 downstream
#: is still asserted unchanged. Nothing outside these named modules changes.
RECORDED_SCHEMAS: dict[str, tuple[str, str]] = {
    "reference_alternatives_accept": (SCHEMA_17_VERSION, SCHEMA_17_HASH),
}


def pin_recorded_schemas() -> None:
    """Replay each loaded historical script at the schema it was recorded under."""
    for name, (version, schema_hash) in RECORDED_SCHEMAS.items():
        module = sys.modules.get(name)
        if module is None:
            continue
        module.REPRESENTATION_SCHEMA_VERSION = version  # type: ignore[attr-defined]
        module.representation_schema_hash = lambda h=schema_hash: h  # type: ignore[attr-defined]
        if hasattr(module, "CURRENT"):
            module.CURRENT = (version, schema_hash)  # type: ignore[attr-defined]


pin_recorded_schemas()
REFERENCE_ALTERNATIVES.reviewed()  # the pinned proposal states the pinned schema


def _judged_at_build_schema(validate: Callable[..., Any]) -> Any:
    def judged(candidate: ProjectionCandidate, *args: Any, **kwargs: Any) -> Any:
        source = (candidate.schema_version, candidate.schema_hash)
        build = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
        if source != build:
            # Each registered crossing proved over this very representation,
            # then only the candidate's declaration moves (what a lift
            # certifies); the artifact and its evidence are not touched.
            verify_lift_path(lift_path(source, build), candidate.representation)
            candidate = replace(
                candidate, schema_version=build[0], schema_hash=build[1]
            )
        return validate(candidate, *args, **kwargs)

    judged.at_build_schema = True  # type: ignore[attr-defined]
    return judged


def judge_findings_at_build_schema() -> None:
    """Judge the schema-17 recordings' release findings at the build's schema.

    Their ``_check`` counts the build's release findings (``APC.findings`` ->
    ``validate_candidate``), which admit only the live contract: a candidate at
    schema 17 now draws two schema-binding findings that no reviewer saw. The
    rule the earlier-schema recordings already follow (``_schema_pins.lifted``, "the
    version-pinned verifier judges at this build's schema") is applied at the
    judge instead of at the call, because these scripts also assert their own
    recorded schema, lift and delta on the unlifted inputs. The registered
    crossings are proved over the candidate's representation before its
    declaration moves; a candidate already at the build's schema is judged as
    it is.
    """
    for module in (
        REFERENCE_ALTERNATIVES,
        FINITE_REFERENCE_ROUTES,
        EQUIPMENT_SPELL_REFERENCES,
        FINAL_TEN_REFERENCES,
    ):
        apc = module.APC
        if not getattr(apc.validate_candidate, "at_build_schema", False):
            apc.validate_candidate = _judged_at_build_schema(apc.validate_candidate)


judge_findings_at_build_schema()

#: batch -> (proposal_identity, file SHA-256), as the approval names them.
BATCHES = {batch: (identity, sha) for batch, identity, sha in REPLACEMENT.BATCHES}


def proposal_path(batch: str) -> Path:
    """The approved regenerated proposal for ``batch``."""
    assert batch in BATCHES, batch
    return NOTES / f"issue-5d-{batch}-{REPLACEMENT.TAG}-PROPOSAL.json"


def identity(batch: str) -> str:
    return str(BATCHES[batch][0])


def kept_whole(prior: AcceptedInputs, committed: AcceptedInputs) -> list[str]:
    """Where ``committed`` fails to keep ``prior`` whole, as a multiset.

    The one change a later batch may make to it is the Magic Items batch's
    reviewed enlargement of the two shared Equipment records' derived
    obligations, which is held exactly.
    """
    old, new = accepted_inputs_payload(prior), accepted_inputs_payload(committed)
    return [
        *REPLACEMENT._preserved({**old, "obligations": []}, {**new, "obligations": []}),
        *MAGIC_ITEMS.obligation_delta(prior, committed),
    ]


@cache
def through(batch: str | None = None) -> AcceptedInputs:
    """The recorded chain after ``batch`` and its resolutions.

    Whole if None: the twenty batches, before Monsters.
    """
    if batch is None:
        return REPLACEMENT.recorded()  # type: ignore[no-any-return]
    return REPLACEMENT.owner_chain(  # type: ignore[no-any-return]
        REPLACEMENT.ACCEPTED_AT, through=batch
    )


@cache
def monsters_recorded() -> AcceptedInputs:
    """The twenty-one batches the Monsters recording wrote, rebuilt from its
    recorded times: the prior Animals was accepted over."""
    return ANIMALS.prior()  # type: ignore[no-any-return]


@cache
def animals_recorded() -> AcceptedInputs:
    """The twenty-two batches the Animals recording wrote, rebuilt from its
    recorded times: the prior the Equipment replacement was recorded over.

    Every earlier state that holds the replaced Equipment batch is kept whole
    here, not in the committed file, which keeps this outside Equipment.
    """
    return EQUIPMENT_CITED.prior()  # type: ignore[no-any-return]


@cache
def accepted_only(batch: str) -> AcceptedInputs:
    """``batch`` accepted over the previous state, before its own resolutions.

    The chain resolves right after accepting; this is the state between the two
    seams, where the accepted citations still carry their empty targets.
    """
    order = list(BATCHES)
    previous = order[order.index(batch) - 1]
    proposal = load_proposal(proposal_path(batch), expected_identity=identity(batch))
    return accept_proposal(
        proposal,
        batch_id=batch,
        rule=REPLACEMENT.APPROVAL,
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer=REPLACEMENT.OWNER,
        accepted_at=REPLACEMENT.ACCEPTED_AT,
        prior=through(previous),
    )


@cache
def equipment_recorded() -> AcceptedInputs:
    """The twenty-two batches the Equipment recording wrote, rebuilt from its
    recorded times: the prior the remaining-references replacement was recorded
    over. The committed file keeps it outside the eight replaced batches."""
    return REMAINING.prior()  # type: ignore[no-any-return]


@cache
def remaining_recorded() -> AcceptedInputs:
    """The twenty-two batches the remaining-references recording wrote, rebuilt
    from its recorded times: the prior the Animals catalogue replacement was
    recorded over. The committed file keeps it outside Animals."""
    return ANIMALS_CATALOGUE.prior()  # type: ignore[no-any-return]


@cache
def animals_catalogue_recorded() -> AcceptedInputs:
    """The twenty-two batches the Animals catalogue recording wrote, rebuilt
    from its recorded times: the prior the framing-coverage batch was appended
    to. The committed file keeps it whole."""
    return FRAMING.prior()  # type: ignore[no-any-return]


def framing_recorded() -> AcceptedInputs:
    """The twenty-three batches the framing-coverage recording wrote, rebuilt
    from its recorded time: the prior the Character Creation catalogue was
    appended to. The committed file keeps it whole."""
    return CHARACTER_CREATION.prior()  # type: ignore[no-any-return]


def character_creation_recorded() -> AcceptedInputs:
    """The twenty-four batches the Character Creation catalogue recording
    wrote, rebuilt from its recorded times: the prior the finite-reference
    atoms replacement was recorded over. The committed file keeps it outside
    the five replaced batches."""
    return FINITE_REFERENCE.prior()  # type: ignore[no-any-return]


def finite_reference_recorded() -> AcceptedInputs:
    """The twenty-four batches the finite-reference atoms recording wrote,
    rebuilt from its recorded time: the prior the Playing the Game atoms
    replacement was recorded over. The committed file keeps it outside the two
    replaced batches."""
    return PLAYING_THE_GAME.prior()  # type: ignore[no-any-return]


def playing_the_game_recorded() -> AcceptedInputs:
    """The twenty-four batches the Playing the Game atoms recording wrote,
    rebuilt from its recorded time: the prior the Equipment class-eligibility
    replacement was recorded over. The committed file keeps it outside
    Equipment."""
    return EQUIPMENT_CLASS_ELIGIBILITY.prior()  # type: ignore[no-any-return]


def equipment_class_eligibility_recorded() -> AcceptedInputs:
    """The twenty-four batches the Equipment class-eligibility recording wrote,
    rebuilt from its recorded time: the prior the reference-routes resolutions
    were lifted and appended over. The committed file keeps it whole."""
    return REFERENCE_ALTERNATIVES.prior()  # type: ignore[no-any-return]


def reference_alternatives_recorded() -> AcceptedInputs:
    """The twenty-four batches the reference-alternatives recording wrote,
    rebuilt from its recorded time: the prior the finite-reference-routes
    replacement was recorded over. The committed file keeps it outside
    combat-damage-breaking."""
    return FINITE_REFERENCE_ROUTES.prior()  # type: ignore[no-any-return]


def finite_reference_routes_recorded() -> AcceptedInputs:
    """The twenty-four batches the finite-reference-routes recording wrote,
    rebuilt from its recorded time: the prior the Equipment, cursed-item and
    spell resolutions were appended over. The committed file keeps it whole."""
    return EQUIPMENT_SPELL_REFERENCES.prior()  # type: ignore[no-any-return]


def equipment_spell_references_recorded() -> AcceptedInputs:
    """The twenty-four batches the equipment-spell-references recording wrote,
    rebuilt from its recorded time: the prior the final ten reference
    resolutions were appended over. The committed file keeps it whole."""
    return FINAL_TEN_REFERENCES.prior()  # type: ignore[no-any-return]


@cache
def current() -> AcceptedInputs:
    """The current release's committed authority, at its recorded bytes."""
    assert hashlib.sha256(CURRENT_PATH.read_bytes()).hexdigest() == CURRENT_SHA256
    return load_accepted_inputs(CURRENT_PATH)
