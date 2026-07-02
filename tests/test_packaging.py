"""Packaging tests for non-Python package resources.

JsonPersonaRegistry loads writing_personas.v1.json via a __file__-relative
path, which works from a checkout but requires explicit package-data
configuration for the file to survive an sdist/wheel build.  These tests
guard that configuration rather than the loading approach itself.
"""

from __future__ import annotations

import tomllib
from fnmatch import fnmatch
from pathlib import Path

from afterworlds.modes.personas.registry import _PROFILES_DIR, _WRITING_V1_PATH

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _REPO_ROOT / "src" / "afterworlds"


def _load_pyproject() -> dict[str, object]:
    with (_REPO_ROOT / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


class TestPersonaRegistryPackageData:
    def test_package_data_glob_covers_persona_registry_json(self) -> None:
        """pyproject.toml's package-data glob must match the registry's actual path.

        Derives the glob's match target from the registry module's own
        _WRITING_V1_PATH constant (relative to the package root) rather than a
        hardcoded string, so this test breaks if the registry's file layout
        moves without a corresponding packaging update.
        """
        pyproject = _load_pyproject()
        package_data = pyproject["tool"]["setuptools"]["package-data"]  # type: ignore[index]
        patterns: list[str] = package_data["afterworlds"]  # type: ignore[index]

        relative_json_path = _WRITING_V1_PATH.relative_to(_SRC_ROOT).as_posix()
        assert any(fnmatch(relative_json_path, pattern) for pattern in patterns), (
            f"No package-data glob in pyproject.toml matches {relative_json_path!r};"
            f" patterns were {patterns!r}"
        )

    def test_persona_registry_json_exists_at_declared_path(self) -> None:
        assert _WRITING_V1_PATH.is_file()
        assert _WRITING_V1_PATH.parent == _PROFILES_DIR

    def test_manifest_in_includes_persona_profiles_directory(self) -> None:
        """MANIFEST.in must include the profiles dir so sdist builds carry the JSON."""
        manifest = (_REPO_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
        relative_dir = _PROFILES_DIR.relative_to(_REPO_ROOT).as_posix()
        assert relative_dir in manifest
        assert "*.json" in manifest
