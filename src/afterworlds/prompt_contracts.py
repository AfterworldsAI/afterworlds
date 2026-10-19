"""Where the versioned prompt contracts are read from (#205).

The authority is the repository's ``docs/prompts`` (one source of truth). An
installed distribution carries a byte-identical copy made at build time
(``setup.py``) in ``afterworlds/_prompts``; a source checkout reads
``docs/prompts`` directly.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGED = Path(__file__).resolve().parent / "_prompts"
_CHECKOUT = Path(__file__).resolve().parents[2]


def prompt_dir() -> Path:
    """The packaged copy when installed; ``docs/prompts`` in a checkout."""
    if _PACKAGED.is_dir():
        return _PACKAGED
    if (_CHECKOUT / "pyproject.toml").is_file():
        return _CHECKOUT / "docs" / "prompts"
    return _PACKAGED  # an installation without its prompts: loaders refuse


PROMPT_DIR: Path = prompt_dir()
