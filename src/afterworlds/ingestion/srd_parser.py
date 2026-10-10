"""SRD structured JSON parser — ingestion pipeline component.

Parses a structured SRD data dict (loaded from JSON) into ``ParsedChunk``
dataclasses for the ingestion service to persist.

The ``entities`` array of the obsolete prose-only ``MechanicalEntity`` family is
no longer accepted: that authority path was retired at the final CRD Issue 5d
cutover (#137 contract 6, AC22). An input that still carries the key — even an
empty array — is refused rather than silently ignored, so pre-cutover data
cannot appear to ingest.

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
  ]
}

Raises
------
ParseError
    Raised for unrecognised subsystem values, a missing section path, or a
    retired ``entities`` array.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afterworlds.models.enums import RuleSubsystemEnum

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


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------


class ParseError(Exception):
    """Raised when the SRD input data cannot be parsed."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SUBSYSTEM_MAP: dict[str, RuleSubsystemEnum] = {s.value: s for s in RuleSubsystemEnum}


def _parse_subsystem(raw: str) -> RuleSubsystemEnum:
    try:
        return _SUBSYSTEM_MAP[raw]
    except KeyError:
        valid = sorted(_SUBSYSTEM_MAP.keys())
        raise ParseError(
            f"Unrecognised subsystem {raw!r}. Valid values: {valid}"
        ) from None


# ---------------------------------------------------------------------------
# Public parser
# ---------------------------------------------------------------------------


class SRDParser:
    """Parses structured SRD JSON into ParsedChunk records.

    Usage::

        parser = SRDParser()
        chunks = list(parser.parse_chunks(srd_data))
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
            For unrecognised subsystem values, missing/blank section_path, or
            a retired ``entities`` array.
        """
        if "entities" in srd_data:
            raise ParseError(
                "the 'entities' array is the retired MechanicalEntity authority "
                "path (CRD Issue 5d final cutover); typed mechanical authority "
                "comes only from the accepted 5d projection"
            )
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
