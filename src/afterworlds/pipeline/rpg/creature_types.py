"""A target's creature type and Elf status, from accepted authority only —
CRD Issue 15c (C8, accepted 2026-10-13).

The Ghast's and Ghoul's Claw riders spare an Undead target, and the Ghoul's
an Elf. This module decides those predicates or refuses before any die;
nothing here guesses.

**Where the type comes from.**

* A character: its exact validated species' ``creature_type`` fact
  (``character-origins.md`` "Creature Type"), which its recorded
  ``creature_type`` must agree with.
* A creature: its own certified template's ``creature_type`` fact (the stat
  block header, ``monsters.md``:7). A stored ``creature_type`` that departs
  from it is trusted only where a represented source qualifies it: Find
  Familiar's ``summoned_creature_type`` (the named forms, a type within the
  choice) and a template whose own fact is a choice (Find Steed's steed).

**The ordinary domain.** Type is read from the base authority only when
nothing recorded can change it: the subject's active effects are recorded
(``None`` is unrecorded, never empty), every one is a reviewed mastery effect
(none of which changes type), and none names an assumed form. Anything else —
a transformation, an unexecuted effect, a missing family — refuses; the visual
form's header is never read.

**Elf.** A character is an Elf exactly when its species is
``character_origins.elf``. A creature whose type is not Humanoid is not an
Elf: the Elf species is Humanoid (C8, ``character-origins.md``), so a
non-Humanoid type establishes the negative. A Humanoid creature's species is
open in its source (``monsters.md``:55); it is decided only by an exact
recorded selection (Owner decision of 2026-10-13, bounded species input),
under the creature's current binding, and is otherwise unknown. A missing tag
or a name never decides it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from afterworlds.ingestion.mechanical.representation import (
    CreatureTypeFact,
    SummonedCreatureTypeFact,
    TargetTag,
)
from afterworlds.models.dnd5e_state import CreatureSpeciesSelection
from afterworlds.models.dnd5e_vocabulary import CreatureType
from afterworlds.models.rpg import RollProposal, SheetEffect
from afterworlds.pipeline.rpg.capability import (
    AdjudicationRefusal,
    Certificate,
    Operation,
    RefusalKind,
    certify,
)
from afterworlds.pipeline.rpg.defense import facts_of, template
from afterworlds.pipeline.rpg.mastery import MASTERY_EFFECTS
from afterworlds.services.dnd5e_state.authority import AuthorityIndex
from afterworlds.services.dnd5e_state.turn import TurnCreature, TurnSubject
from afterworlds.services.dnd5e_state.validation import species_open, species_options

__all__ = [
    "ELF",
    "FIND_FAMILIAR",
    "SpeciesRecord",
    "TargetType",
    "excluded_by",
    "prepare_species",
    "record_species",
    "species_open",
    "species_options",
    "target_type",
]

ELF = "character_origins.elf"
FIND_FAMILIAR = "spells.find_familiar"
#: Familiar sources the state model admits (``validation.FAMILIAR_SOURCES``)
#: whose type authority is not Find Familiar's own fact: Wild Companion's
#: familiar is Fey and Pact of the Chain adds forms, neither represented.
_UNREPRESENTED_FAMILIAR_SOURCES = frozenset(
    {
        "classes.druid.wild_companion",
        "classes.warlock.eldritch_invocation_options.pact_of_the_chain",
    }
)
#: The tags a rider exclusion names that are creature types.
_TYPE_TAGS = {
    t: CreatureType(t.value) for t in TargetTag if t.value in set(CreatureType)
}


def _refuse(kind: RefusalKind, detail: str) -> AdjudicationRefusal:
    return AdjudicationRefusal(kind, detail)


@dataclass(frozen=True)
class TargetType:
    """A subject's established creature type and Elf status.

    ``elf`` is ``None`` when it is not established (a Humanoid creature with
    no current species selection); a caller that needs it refuses.
    """

    type: CreatureType
    elf: bool | None
    basis: str


def _type_fact(index: AuthorityIndex, record: str) -> CreatureTypeFact:
    facts = [f for f in facts_of(index, record) if isinstance(f, CreatureTypeFact)]
    if len(facts) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{record} states {len(facts)} creature types, not exactly one",
        )
    return facts[0]


def _ordinary(subject: TurnSubject, who: str) -> None:
    """Refuse unless nothing recorded can change *subject*'s type."""
    effects = subject.stored.state.active_effects
    if effects is None:
        raise _refuse(
            RefusalKind.MISSING_STATE,
            f"{who}'s active effects are not recorded, so its creature type "
            "is not established",
        )
    for effect in effects:
        if effect.form_record_key is not None:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{who} is in an assumed form ({effect.form_record_key}); its "
                "creature type and species under it are not executed here",
            )
        if effect.source.record_key not in MASTERY_EFFECTS:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"active effect {effect.source.record_key} on {who} can change "
                "its creature type and is not executable here",
            )


def _character(subject: TurnSubject, who: str) -> TargetType:
    assert subject.index is not None
    state = subject.stored.state
    species = getattr(state, "species", None)
    if species is None:
        raise _refuse(RefusalKind.MISSING_STATE, f"{who}'s species is not recorded")
    fact = _type_fact(subject.index, species.record_key)
    if fact.type is None:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{species.record_key} states a choice of creature types",
        )
    kind = CreatureType(fact.type.value)
    recorded = state.creature_type
    if recorded is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"{who}'s creature type is not recorded"
        )
    if recorded is not kind:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{who} records creature type {recorded.value}, but its species "
            f"{species.record_key} is {kind.value}",
        )
    _ordinary(subject, who)
    return TargetType(kind, species.record_key == ELF, f"species {species.record_key}")


def _familiar(
    creature: TurnCreature, key: str, fact: CreatureTypeFact, who: str
) -> CreatureType:
    """A Find Familiar familiar's type: the stored choice, for a named form."""
    assert creature.index is not None
    sources = [
        f
        for f in facts_of(creature.index, FIND_FAMILIAR, "effect")
        if isinstance(f, SummonedCreatureTypeFact)
    ]
    if len(sources) != 1:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY, "Find Familiar's type choice is not typed"
        )
    (source,) = sources
    forms = {(r.record_key, r.component_key) for r in source.forms}
    if not any(record == key for record, _ in forms):
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{who}'s form {key} is not one of Find Familiar's named forms; "
            "another Challenge Rating 0 Beast form is not represented",
        )
    if fact.type is None or fact.type.value != source.instead_of.value:
        raise _refuse(
            RefusalKind.MISSING_AUTHORITY,
            f"{key} is not the {source.instead_of.value} Find Familiar replaces",
        )
    stored = creature.stored.state.creature_type
    choice = {t.value for t in source.type_choice}
    if stored is None or stored.value not in choice:
        raise _refuse(
            (
                RefusalKind.MISSING_STATE
                if stored is None
                else RefusalKind.INVALID_SELECTION
            ),
            f"{who}, a familiar, records "
            f"{stored.value if stored else 'no'} creature type, not one of "
            f"{sorted(choice)}",
        )
    return stored


def _creature(creature: TurnCreature, who: str) -> TargetType:
    assert creature.index is not None
    key = template(creature)
    fact = _type_fact(creature.index, key)
    state = creature.stored.state
    summon = state.summon.source.record_key if state.summon is not None else None
    stored = state.creature_type
    if summon in _UNREPRESENTED_FAMILIAR_SOURCES:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"{who} is a familiar from {summon}, whose creature type is not "
            "represented",
        )
    if summon == FIND_FAMILIAR:
        kind = _familiar(creature, key, fact, who)
        basis = f"Find Familiar choice on {key}"
    elif fact.type is None:
        # A type the creator chooses (Find Steed's steed): its own source,
        # and a recorded choice within the printed ones.
        choice = {t.value for t in fact.type_choice}
        if summon is None or not key.startswith(f"{summon}."):
            raise _refuse(
                RefusalKind.MISSING_STATE,
                f"{who}'s template {key} has a chosen type, and it records no "
                "summoning by that source",
            )
        if stored is None or stored.value not in choice:
            raise _refuse(
                (
                    RefusalKind.MISSING_STATE
                    if stored is None
                    else RefusalKind.INVALID_SELECTION
                ),
                f"{who} records {stored.value if stored else 'no'} creature "
                f"type, not one of {sorted(choice)}",
            )
        kind, basis = stored, f"{key} choice"
    else:
        kind = CreatureType(fact.type.value)
        if stored is not None and stored is not kind:
            raise _refuse(
                RefusalKind.UNSUPPORTED_CAPABILITY,
                f"{who} records creature type {stored.value}, departing from its "
                f"template's {kind.value} without a represented source",
            )
        basis = f"template {key}"
    _ordinary(creature, who)
    selected = state.species
    if kind is not CreatureType.HUMANOID:
        if selected is not None:
            raise _refuse(
                RefusalKind.INVALID_SELECTION,
                f"{who} is {kind.value}, and records a species selection only a "
                "source-open Humanoid may record",
            )
        return TargetType(kind, False, basis)
    if selected is None:
        return TargetType(kind, None, basis)
    binding = creature.index.binding
    if (
        selected.template_record_key != key
        or selected.mechanical_projection_uuid != binding.mechanical_projection_uuid
        or selected.override_set_uuid != binding.override_set_uuid
    ):
        raise _refuse(
            RefusalKind.STALE_BINDING,
            f"{who}'s species selection was recorded under another template or "
            "binding; it must be recorded again",
        )
    if not species_open(creature.index, key) or (
        selected.species_record_key not in species_options(creature.index)
    ):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            # Not named: refusal text can reach the player, and the selection
            # may have been recorded hidden.
            f"{who}'s recorded species is not a Humanoid species its template "
            f"{key} admits",
        )
    return TargetType(
        kind,
        selected.species_record_key == ELF,
        f"{basis}; recorded species {selected.species_record_key}",
    )


def target_type(subject: TurnSubject, who: str = "the target") -> TargetType:
    """*subject*'s creature type and Elf status, or a refusal."""
    if subject.index is None:
        raise _refuse(RefusalKind.MISSING_AUTHORITY, f"{who}'s authority")
    if isinstance(subject, TurnCreature):
        return _creature(subject, who)
    return _character(subject, who)


def excluded_by(
    tags: tuple[TargetTag, ...], subject: TurnSubject, who: str = "the target"
) -> tuple[str | None, TargetType]:
    """Which of *tags* (a rider's exclusion) *subject* is, or ``None``, with
    the type it was decided from; a refusal when the answer is not
    established. A type exclusion that holds settles it without the Elf
    question."""
    unsupported = [t for t in tags if t not in _TYPE_TAGS and t is not TargetTag.ELF]
    if unsupported:
        raise _refuse(
            RefusalKind.UNSUPPORTED_CAPABILITY,
            f"an exclusion of {unsupported[0].value} is not executable here",
        )
    typed = target_type(subject, who)
    for tag in tags:
        if tag in _TYPE_TAGS and _TYPE_TAGS[tag] is typed.type:
            return tag.value, typed
    if TargetTag.ELF in tags:
        if typed.elf is None:
            raise _refuse(
                RefusalKind.MISSING_STATE,
                f"{who} is a Humanoid whose species is not recorded, so whether "
                "it is an Elf is not established",
            )
        if typed.elf:
            return TargetTag.ELF.value, typed
    return None, typed


# --- the creature_species operation (bounded species input) -------------------


@dataclass(frozen=True)
class SpeciesRecord:
    """A validated ``creature_species`` proposal, ready to record."""

    creature: TurnCreature
    selection: CreatureSpeciesSelection
    certificate: Certificate


def prepare_species(
    proposal: RollProposal,
    subjects: dict[tuple[str, str], TurnSubject],
) -> SpeciesRecord:
    """Validate a ``creature_species`` proposal, or refuse: a creature of
    the story read for this turn, whose template is a source-open Humanoid,
    one code-generated Humanoid species option, and no selection still
    current under its template and binding."""
    ref, species = proposal.subject, proposal.species
    if ref is None or ref.kind != "creature" or species is None:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            "creature_species names a creature and one species",
        )
    creature = subjects.get(("creature", str(ref.subject_id)))
    if not isinstance(creature, TurnCreature) or creature.index is None:
        raise _refuse(
            RefusalKind.MISSING_STATE, f"creature {ref.subject_id} was not read"
        )
    index = creature.index
    certificate = certify(Operation.CREATURE_SPECIES, index)
    key = template(creature)
    if not species_open(index, key):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{key} is not a Humanoid whose source leaves its species open",
        )
    options = species_options(index)
    if species not in options:
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            f"{species!r} is not one of the species options {list(options)}",
        )
    binding = index.binding
    selection = CreatureSpeciesSelection(
        species_record_key=species,
        template_record_key=key,
        mechanical_projection_uuid=binding.mechanical_projection_uuid,
        override_set_uuid=binding.override_set_uuid,
    )
    held = creature.stored.state.species
    if held is not None and (
        held.template_record_key,
        held.mechanical_projection_uuid,
        held.override_set_uuid,
    ) == (key, binding.mechanical_projection_uuid, binding.override_set_uuid):
        raise _refuse(
            RefusalKind.INVALID_SELECTION,
            # The held identity is not named: a refusal's text can reach the
            # player, and the selection may have been recorded hidden.
            f"creature {ref.subject_id} already records a species; an "
            "individual's species does not change",
        )
    return SpeciesRecord(creature, selection, certificate)


def record_species(prepared: SpeciesRecord) -> tuple[SheetEffect, str]:
    """The effect recording the selection, and its provenance JSON."""
    creature = prepared.creature
    effect = SheetEffect(
        target="creature_species",
        operation="set",
        value_json=prepared.selection.model_dump_json(),
        subject_kind="creature",
        subject_id=creature.subject_id,
    )
    provenance = {
        "operation": Operation.CREATURE_SPECIES.value,
        "creature": str(creature.subject_id),
        "template": prepared.selection.template_record_key,
        "species": prepared.selection.species_record_key,
        "replaces": (
            creature.stored.state.species.species_record_key
            if creature.stored.state.species is not None
            else None
        ),
        "certificate": prepared.certificate.as_json(),
    }
    return effect, json.dumps(provenance)
