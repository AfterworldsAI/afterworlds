"""Unit tests for SafetyConfig — CRD Issue 12b."""

from __future__ import annotations

import pytest

from afterworlds.pipeline.safety.config import _DEFAULT_SAFETY_MODEL, SafetyConfig


class TestSafetyConfigDefaults:
    def test_default_model(self) -> None:
        config = SafetyConfig()
        assert config.model == _DEFAULT_SAFETY_MODEL

    def test_default_api_key_env(self) -> None:
        config = SafetyConfig()
        assert config.api_key_env == "ANTHROPIC_API_KEY"

    def test_extended_ttl_true_by_default(self) -> None:
        config = SafetyConfig()
        assert config.extended_ttl is True


class TestSafetyConfigFromEnv:
    def test_from_env_uses_defaults_when_vars_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SAFETY_MODEL", raising=False)
        monkeypatch.delenv("SAFETY_API_KEY_ENV", raising=False)
        monkeypatch.delenv("SAFETY_EXTENDED_TTL", raising=False)
        config = SafetyConfig.from_env()
        assert config.model == _DEFAULT_SAFETY_MODEL
        assert config.api_key_env == "ANTHROPIC_API_KEY"
        assert config.extended_ttl is True

    def test_from_env_reads_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAFETY_MODEL", "claude-opus-test")
        config = SafetyConfig.from_env()
        assert config.model == "claude-opus-test"

    def test_from_env_reads_api_key_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAFETY_API_KEY_ENV", "MY_SAFETY_KEY")
        config = SafetyConfig.from_env()
        assert config.api_key_env == "MY_SAFETY_KEY"

    def test_from_env_extended_ttl_false_when_set_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAFETY_EXTENDED_TTL", "false")
        config = SafetyConfig.from_env()
        assert config.extended_ttl is False

    def test_from_env_extended_ttl_false_when_set_0(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAFETY_EXTENDED_TTL", "0")
        config = SafetyConfig.from_env()
        assert config.extended_ttl is False


class TestSafetyConfigGetApiKey:
    def test_get_api_key_returns_env_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key-123")
        config = SafetyConfig()
        assert config.get_api_key() == "sk-test-key-123"

    def test_get_api_key_raises_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        config = SafetyConfig()
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            config.get_api_key()

    def test_get_api_key_raises_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        config = SafetyConfig()
        with pytest.raises(RuntimeError):
            config.get_api_key()
