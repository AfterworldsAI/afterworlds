"""Round 10 remediation (PR #126 P2, sibling-audit gate): every public API
DTO in ``dto.py`` must carry ``schema_version`` (Binding Decision 9).

Prior rounds added the field piecemeal -- to named request DTOs, then to
setup-state union members -- and each round missed at least one sibling
class. This test enumerates every ``BaseModel`` subclass actually defined in
``dto.py`` (not imported from elsewhere) and fails if any lacks a
``schema_version`` field, so a future addition to the module can't silently
skip it again.
"""

from __future__ import annotations

import inspect
from typing import get_args

from pydantic import BaseModel

from afterworlds.api import dto as dto_module

# Local exemption list (must be explicitly justified here, not silently
# absent from the enumeration): none currently -- every BaseModel subclass
# defined in dto.py is a public API contract object (request, response, or
# an embedded/union member of one) and must be versioned.
_EXEMPT: frozenset[str] = frozenset()


def _dto_classes() -> list[type[BaseModel]]:
    classes = []
    for obj in vars(dto_module).values():
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj.__module__ == dto_module.__name__
        ):
            classes.append(obj)
    assert classes, "no BaseModel subclasses found in dto.py -- enumeration is broken"
    return classes


def test_every_dto_class_carries_schema_version() -> None:
    missing = [
        cls.__name__
        for cls in _dto_classes()
        if cls.__name__ not in _EXEMPT and "schema_version" not in cls.model_fields
    ]
    assert not missing, (
        f"DTOs missing schema_version: {missing}. Add "
        "`schema_version: Literal[1] = 1` to each, or add a justified "
        "entry to _EXEMPT in this test."
    )


def test_schema_version_field_is_literal_one_with_default() -> None:
    for cls in _dto_classes():
        if cls.__name__ in _EXEMPT:
            continue
        field = cls.model_fields["schema_version"]
        assert get_args(field.annotation) == (
            1,
        ), f"{cls.__name__}.schema_version must be typed Literal[1]"
        assert field.default == 1, f"{cls.__name__}.schema_version must default to 1"


def test_setup_request_union_members_preserve_mode_discriminator() -> None:
    # Confirms adding schema_version to the SetupRequest union members never
    # touched the `mode` discriminator Pydantic keys the union on.
    for cls in (
        dto_module.RpgSetupRequest,
        dto_module.BranchingSetupRequest,
        dto_module.WritingSetupRequest,
    ):
        assert "mode" in cls.model_fields
