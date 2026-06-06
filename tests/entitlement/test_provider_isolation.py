"""Provider routing isolation test — AC 62 (provider-isolation).

Scans the Issue 13 source module directory for provider name strings.
Scoped to src/afterworlds/entitlement/ Python source files only.
Does NOT scan tests or imports from other modules.
"""

from __future__ import annotations

from pathlib import Path

_ENTITLEMENT_SRC_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "afterworlds"
    / "entitlement"
)

_FORBIDDEN_PROVIDER_NAMES = [
    "anthropic",
    "openrouter",
    "openai",
]


def test_entitlement_module_contains_no_provider_names() -> None:
    """AC 62: Issue 13 source contains no provider name literals.

    Scans only .py files in src/afterworlds/entitlement/. This confirms that
    provider routing concerns are not embedded in the entitlement module, which
    is Issue 14's domain.
    """
    violations: list[str] = []

    for py_file in _ENTITLEMENT_SRC_DIR.glob("*.py"):
        content = py_file.read_text(encoding="utf-8").lower()
        for name in _FORBIDDEN_PROVIDER_NAMES:
            if name in content:
                violations.append(f"{py_file.name}: contains '{name}'")

    assert not violations, (
        "Entitlement source files must not reference provider names "
        f"(provider routing is Issue 14): {violations}"
    )
