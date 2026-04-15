"""SRD structured JSON parser — ingestion pipeline component.

Parses a structured SRD data dict (loaded from JSON) into ``ParsedChunk``
and ``ParsedEntity`` dataclasses for the ingestion service to persist.

Input format
------------
{
  "sections": [
    {
      "heading": "str",
      "content": "str",
      "subsystem": "<RuleSubsystemEnum value>",
      "section_path": "str",
      "page_ref": "str"
    },
    ...
  ],
  "entities": [
    {
      "entity_type": "<MechanicalEntityTypeEnum value>",
      "name": "str",
      "subsystem": "<RuleSubsystemEnum value>",
      "section_path": "str",
      "page_ref": "str",
      "data": { ... }
    },
    ...
  ]
}

Entity data shapes
------------------
- spell      → SpellEntity fields
- condition  → ConditionEntity fields
- stat_block → StatBlockEntity fields
- action     → ActionEntity fields
- item       → ItemEntity fields

Raises
------
ParseError
    Raised for unrecognised subsystem or entity_type values, and for entity
    data that fails validation against the expected typed model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from afterworlds.models.enums import MechanicalEntityTypeEnum, RuleSubsystemEnum
from afterworlds.models.rules_package import (
    ActionEntity,
    ConditionEntity,
    EntityData,
    ItemEntity,
    SpellEntity,
    StatBlockEntity,
)

# ---------------------------------------------------------------------------
# Parsed output dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ParsedChunk:
    """Parsed rule chunk ready for persistence."""

    heading: str
    content: str
    subsystem: RuleSubsystemEnum
    section_path: str
    page_ref: str


@dataclass
class ParsedEntity:
    """Parsed mechanical entity ready for persistence."""

    entity_type: MechanicalEntityTypeEnum
    name: str
    subsystem: RuleSubsystemEnum
    section_path: str
    page_ref: str
    data: EntityData


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when the SRD input data cannot be parsed."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ENTITY_TYPE_MAP: dict[str, MechanicalEntityTypeEnum] = {
    e.value: e for e in MechanicalEntityTypeEnum
}

_SUBSYSTEM_MAP: dict[str, RuleSubsystemEnum] = {s.value: s for s in RuleSubsystemEnum}

_ENTITY_DATA_MODELS: dict[MechanicalEntityTypeEnum, type[EntityData]] = {
    MechanicalEntityTypeEnum.SPELL: SpellEntity,
    MechanicalEntityTypeEnum.CONDITION: ConditionEntity,
    MechanicalEntityTypeEnum.STAT_BLOCK: StatBlockEntity,
    MechanicalEntityTypeEnum.ACTION: ActionEntity,
    MechanicalEntityTypeEnum.ITEM: ItemEntity,
}


def _parse_subsystem(raw: str) -> RuleSubsystemEnum:
    try:
        return _SUBSYSTEM_MAP[raw]
    except KeyError:
        valid = sorted(_SUBSYSTEM_MAP.keys())
        raise ParseError(
            f"Unrecognised subsystem {raw!r}. Valid values: {valid}"
        ) from None


def _parse_entity_type(raw: str) -> MechanicalEntityTypeEnum:
    try:
        return _ENTITY_TYPE_MAP[raw]
    except KeyError:
        valid = sorted(_ENTITY_TYPE_MAP.keys())
        raise ParseError(
            f"Unrecognised entity_type {raw!r}. Valid values: {valid}"
        ) from None


def _validate_entity_data(
    entity_type: MechanicalEntityTypeEnum, raw_data: dict[str, Any]
) -> EntityData:
    model_cls = _ENTITY_DATA_MODELS[entity_type]
    try:
        return model_cls.model_validate(raw_data)
    except ValidationError as exc:
        raise ParseError(
            f"Entity data validation failed for entity_type={entity_type!r}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public parser
# ---------------------------------------------------------------------------


class SRDParser:
    """Parses structured SRD JSON into ParsedChunk and ParsedEntity records.

    Usage::

        parser = SRDParser()
        chunks = list(parser.parse_chunks(srd_data))
        entities = list(parser.parse_entities(srd_data))
    """

    def parse_chunks(self, srd_data: dict[str, Any]) -> list[ParsedChunk]:
        """Parse the ``sections`` array into ParsedChunk records.

        Parameters
        ----------
        srd_data:
            The top-level SRD data dict loaded from JSON.

        Returns
        -------
        list[ParsedChunk]
            One ParsedChunk per valid section entry.

        Raises
        ------
        ParseError
            For unrecognised subsystem values or missing/blank section_path.
        """
        sections = srd_data.get("sections", [])
        chunks: list[ParsedChunk] = []
        for i, section in enumerate(sections):
            heading = str(section.get("heading", ""))
            content = str(section.get("content", ""))
            raw_subsystem = str(section.get("subsystem", ""))
            raw_section_path = section.get("section_path", "")
            page_ref = str(section.get("page_ref", ""))
            section_path = str(raw_section_path).strip() if raw_section_path else ""
            if not section_path:
                raise ParseError(
                    f"Section[{i}] ({heading!r}): section_path is missing or blank"
                )
            try:
                subsystem = _parse_subsystem(raw_subsystem)
            except ParseError as exc:
                raise ParseError(f"Section[{i}] ({heading!r}): {exc}") from exc
            chunks.append(
                ParsedChunk(
                    heading=heading,
                    content=content,
                    subsystem=subsystem,
                    section_path=section_path,
                    page_ref=page_ref,
                )
            )
        return chunks

    def parse_entities(self, srd_data: dict[str, Any]) -> list[ParsedEntity]:
        """Parse the ``entities`` array into ParsedEntity records.

        Parameters
        ----------
        srd_data:
            The top-level SRD data dict loaded from JSON.

        Returns
        -------
        list[ParsedEntity]
            One ParsedEntity per valid entity entry.

        Raises
        ------
        ParseError
            For unrecognised entity_type/subsystem, data validation failure,
            or missing/blank section_path.
        """
        entities_raw = srd_data.get("entities", [])
        entities: list[ParsedEntity] = []
        for i, ent in enumerate(entities_raw):
            name = str(ent.get("name", ""))
            raw_entity_type = str(ent.get("entity_type", ""))
            raw_subsystem = str(ent.get("subsystem", ""))
            raw_section_path = ent.get("section_path", "")
            page_ref = str(ent.get("page_ref", ""))
            section_path = str(raw_section_path).strip() if raw_section_path else ""
            if not section_path:
                raise ParseError(
                    f"Entity[{i}] ({name!r}): section_path is missing or blank"
                )
            raw_data: dict[str, Any] = ent.get("data", {})
            try:
                entity_type = _parse_entity_type(raw_entity_type)
            except ParseError as exc:
                raise ParseError(f"Entity[{i}] ({name!r}): {exc}") from exc
            try:
                subsystem = _parse_subsystem(raw_subsystem)
            except ParseError as exc:
                raise ParseError(f"Entity[{i}] ({name!r}): {exc}") from exc
            data = _validate_entity_data(entity_type, raw_data)
            entities.append(
                ParsedEntity(
                    entity_type=entity_type,
                    name=name,
                    subsystem=subsystem,
                    section_path=section_path,
                    page_ref=page_ref,
                    data=data,
                )
            )
        return entities
