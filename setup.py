"""Build hook (#205): ship a copy of the prompt contracts with the package.

``docs/prompts`` stays the single source of truth; the runtime reads it from a
checkout (``afterworlds.prompt_contracts``) and from this byte-identical copy
when installed. All other configuration lives in ``pyproject.toml``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

_PROMPTS = Path(__file__).resolve().parent / "docs" / "prompts"


class BuildWithPromptContracts(build_py):
    def run(self) -> None:
        super().run()
        if not _PROMPTS.is_dir():  # a staged tree without docs: nothing to ship
            return
        target = Path(self.build_lib) / "afterworlds" / "_prompts"
        target.mkdir(parents=True, exist_ok=True)
        for prompt in sorted(_PROMPTS.glob("*.md")):
            shutil.copyfile(prompt, target / prompt.name)


setup(cmdclass={"build_py": BuildWithPromptContracts})
