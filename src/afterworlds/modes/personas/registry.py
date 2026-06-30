"""Persona Registry — static, typed, versioned provider for Writing-mode personas.

The registry is the source of truth for active persona IDs, display names,
Mentor/Peer orientation, supported modes, UI descriptions, source anchors,
signature moves, demeanor tags, prompt fragments, negative constraints,
availability state, and profile version.

Prompt prose is NOT the source of truth for persona availability or orientation.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

_PROFILES_DIR = Path(__file__).parent / "profiles"
_WRITING_V1_PATH = _PROFILES_DIR / "writing_personas.v1.json"

REGISTRY_VERSION: int = 1


class PersonaOrientation(StrEnum):
    """Mentor personas teach through making; Peer personas collaborate alongside."""

    MENTOR = "mentor"
    PEER = "peer"


class PersonaAvailability(StrEnum):
    """Availability state of a persona in the registry.

    ACTIVE — shown for new session setup and fully supported.
    HIDDEN — valid for existing persisted stories but not offered for new selection.
    DEPRECATED — resolvable for old stories but must not be selected for new setup.
    """

    ACTIVE = "active"
    HIDDEN = "hidden"
    DEPRECATED = "deprecated"


class SupportedMode(StrEnum):
    """Story mode that a persona supports.

    Shape allows future RPG/Branching persona availability without redesign.
    """

    WRITING = "writing"
    RPG = "rpg"
    BRANCHING = "branching"


class PersonaProfile(BaseModel):
    """One registry entry — identity, UI metadata, source anchors, and behavior."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    persona_id: str
    display_name: str
    orientation: PersonaOrientation
    availability: PersonaAvailability
    supported_modes: list[SupportedMode]

    source_tradition: str
    source_anchors: list[str]
    source_note: str | None = None

    ui_short_description: str
    ui_long_description: str

    demeanor_tags: list[str]
    signature_move: str
    opening_question_style: str

    prompt_fragment: str
    negative_constraints: list[str]

    profile_version: int
    prompt_fingerprint: str | None = None


class PersonaRegistryProvider(Protocol):
    """Interface for resolving persona profiles from the registry."""

    def get_profile(self, persona_id: str, mode: SupportedMode) -> PersonaProfile:
        """Return the profile for persona_id in mode, or raise KeyError."""
        ...

    def list_active(self, mode: SupportedMode) -> list[PersonaProfile]:
        """Return all ACTIVE profiles for the given mode."""
        ...


class JsonPersonaRegistry:
    """Static registry backed by a JSON profile file.

    Loaded and validated at construction time. Thread-safe for reads.
    """

    def __init__(self, path: Path = _WRITING_V1_PATH) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._registry_version: int = raw.get("registry_version", REGISTRY_VERSION)
        self._profiles: dict[str, PersonaProfile] = {
            p["persona_id"]: PersonaProfile.model_validate(p) for p in raw["profiles"]
        }

    def get_profile(self, persona_id: str, mode: SupportedMode) -> PersonaProfile:
        """Return the profile for persona_id, or raise KeyError if not found."""
        profile = self._profiles.get(persona_id)
        if profile is None:
            raise KeyError(f"Unknown persona_id: {persona_id!r}")
        if mode not in profile.supported_modes:
            raise KeyError(f"Persona {persona_id!r} does not support mode {mode!r}")
        return profile

    def list_active(self, mode: SupportedMode) -> list[PersonaProfile]:
        """Return all ACTIVE profiles for mode, sorted by persona_id."""
        return sorted(
            (
                p
                for p in self._profiles.values()
                if p.availability is PersonaAvailability.ACTIVE
                and mode in p.supported_modes
            ),
            key=lambda p: p.persona_id,
        )

    @property
    def registry_version(self) -> int:
        return self._registry_version


_default_registry: JsonPersonaRegistry | None = None


def get_default_registry() -> JsonPersonaRegistry:
    """Return the module-level singleton writing persona registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = JsonPersonaRegistry()
    return _default_registry
