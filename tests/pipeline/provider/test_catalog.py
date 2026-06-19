"""Tests for OpenRouter catalog providers — CRD Issue 14b.

Coverage targets:
  - FixtureOpenRouterCatalogProvider: empty default, custom entries, protocol.
  - OpenRouterCatalogModel: tri-state fields, extra='forbid', fetched_at default.
  - LiveOpenRouterCatalogProvider: mocked urllib response; skipped in CI.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from afterworlds.pipeline.provider._catalog import (
    FixtureOpenRouterCatalogProvider,
    LiveOpenRouterCatalogProvider,
    OpenRouterCatalogModel,
    OpenRouterModelCatalogProvider,
)

# ---------------------------------------------------------------------------
# OpenRouterCatalogModel
# ---------------------------------------------------------------------------


class TestOpenRouterCatalogModel:
    def test_required_id_only(self) -> None:
        m = OpenRouterCatalogModel(id="vendor/model")
        assert m.id == "vendor/model"
        assert m.name == ""
        assert m.context_length is None
        assert m.supports_text_output is None
        assert m.supports_tool_use is None
        assert m.supports_tool_choice is None
        assert m.supports_structured_output is None
        assert m.is_dynamic_router is False

    def test_fetched_at_defaults_to_utc_now(self) -> None:
        before = datetime.now(UTC)
        m = OpenRouterCatalogModel(id="x")
        after = datetime.now(UTC)
        assert before <= m.fetched_at <= after

    def test_all_capability_fields_explicitly_set(self) -> None:
        m = OpenRouterCatalogModel(
            id="vendor/model",
            supports_text_output=True,
            supports_tool_use=False,
            supports_tool_choice=True,
            supports_structured_output=None,
            context_length=128_000,
            is_dynamic_router=False,
        )
        assert m.supports_text_output is True
        assert m.supports_tool_use is False
        assert m.supports_tool_choice is True
        assert m.supports_structured_output is None
        assert m.context_length == 128_000

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            OpenRouterCatalogModel(id="x", unknown_field="bad")  # type: ignore[call-arg]

    def test_is_dynamic_router_flag(self) -> None:
        m = OpenRouterCatalogModel(id="openrouter/auto", is_dynamic_router=True)
        assert m.is_dynamic_router is True


# ---------------------------------------------------------------------------
# FixtureOpenRouterCatalogProvider
# ---------------------------------------------------------------------------


class TestFixtureOpenRouterCatalogProvider:
    def test_default_empty_catalog(self) -> None:
        provider = FixtureOpenRouterCatalogProvider()
        assert list(provider.fetch_catalog()) == []

    def test_none_entries_treated_as_empty(self) -> None:
        provider = FixtureOpenRouterCatalogProvider(entries=None)
        assert list(provider.fetch_catalog()) == []

    def test_custom_entries_returned(self) -> None:
        entry = OpenRouterCatalogModel(id="vendor/model")
        provider = FixtureOpenRouterCatalogProvider(entries=[entry])
        result = list(provider.fetch_catalog())
        assert len(result) == 1
        assert result[0].id == "vendor/model"

    def test_multiple_entries_preserved_in_order(self) -> None:
        entries = [
            OpenRouterCatalogModel(id="a/m1"),
            OpenRouterCatalogModel(id="b/m2"),
            OpenRouterCatalogModel(id="c/m3"),
        ]
        provider = FixtureOpenRouterCatalogProvider(entries=entries)
        ids = [m.id for m in provider.fetch_catalog()]
        assert ids == ["a/m1", "b/m2", "c/m3"]

    def test_fetch_catalog_called_repeatedly_returns_same_list(self) -> None:
        entry = OpenRouterCatalogModel(id="x/y")
        provider = FixtureOpenRouterCatalogProvider(entries=[entry])
        first = list(provider.fetch_catalog())
        second = list(provider.fetch_catalog())
        assert first == second

    def test_satisfies_protocol(self) -> None:
        provider = FixtureOpenRouterCatalogProvider()
        assert isinstance(provider, OpenRouterModelCatalogProvider)


# ---------------------------------------------------------------------------
# LiveOpenRouterCatalogProvider — mocked network
# ---------------------------------------------------------------------------


def _make_api_response(data: list[dict[str, Any]]) -> MagicMock:
    """Build a mock urlopen context manager returning a JSON payload."""
    body = json.dumps({"data": data}).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestLiveOpenRouterCatalogProvider:
    """Network calls are mocked; no real HTTP is made."""

    def test_parses_text_output_from_output_modalities(self) -> None:
        payload = [
            {
                "id": "vendor/model",
                "name": "Model Name",
                "context_length": 32_768,
                "architecture": {"output_modalities": ["text"]},
                "supported_parameters": ["tools"],
            }
        ]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="test-key")
            results = list(provider.fetch_catalog())

        assert len(results) == 1
        m = results[0]
        assert m.id == "vendor/model"
        assert m.name == "Model Name"
        assert m.context_length == 32_768
        assert m.supports_text_output is True
        assert m.supports_tool_use is True
        assert m.supports_tool_choice is False
        assert m.supports_structured_output is False

    def test_no_text_in_output_modalities_gives_false(self) -> None:
        """output_modalities list present but 'text' absent → False (not None)."""
        payload = [
            {
                "id": "vendor/vision-only",
                "architecture": {"output_modalities": ["image"]},
            }
        ]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())

        assert len(results) == 1
        assert results[0].supports_text_output is False

    def test_supported_parameters_tools_only(self) -> None:
        """['tools'] → tool_use=True, tool_choice=False, structured=False."""
        payload = [{"id": "v/m", "supported_parameters": ["tools"]}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is True
        assert results[0].supports_tool_choice is False
        assert results[0].supports_structured_output is False

    def test_supported_parameters_structured_outputs_only(self) -> None:
        """['structured_outputs'] → tool_use/choice=False, structured=True."""
        payload = [{"id": "v/m", "supported_parameters": ["structured_outputs"]}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is False
        assert results[0].supports_tool_choice is False
        assert results[0].supports_structured_output is True

    def test_supported_parameters_both(self) -> None:
        """tools+structured: tool_use=True, tool_choice=False, structured=True."""
        payload = [
            {"id": "v/m", "supported_parameters": ["tools", "structured_outputs"]}
        ]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is True
        assert results[0].supports_tool_choice is False
        assert results[0].supports_structured_output is True

    def test_supported_parameters_tools_and_tool_choice(self) -> None:
        """tools+tool_choice → tool_use=True, tool_choice=True, structured=False."""
        payload = [{"id": "v/m", "supported_parameters": ["tools", "tool_choice"]}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is True
        assert results[0].supports_tool_choice is True
        assert results[0].supports_structured_output is False

    def test_supported_parameters_tool_choice_only(self) -> None:
        """['tool_choice'] → tool_use=False, tool_choice=True, structured=False."""
        payload = [{"id": "v/m", "supported_parameters": ["tool_choice"]}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is False
        assert results[0].supports_tool_choice is True
        assert results[0].supports_structured_output is False

    def test_supported_parameters_empty_list(self) -> None:
        """supported_parameters=[] (list present, no matching values) → all False."""
        payload = [{"id": "v/m", "supported_parameters": []}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is False
        assert results[0].supports_tool_choice is False
        assert results[0].supports_structured_output is False

    def test_supported_parameters_absent(self) -> None:
        """supported_parameters absent → all None (fail-safe)."""
        payload = [{"id": "v/m"}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is None
        assert results[0].supports_tool_choice is None
        assert results[0].supports_structured_output is None

    def test_supported_parameters_malformed_non_list(self) -> None:
        """supported_parameters is not a list → all None (fail-safe)."""
        payload = [{"id": "v/m", "supported_parameters": "tools"}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            results = list(LiveOpenRouterCatalogProvider(api_key="k").fetch_catalog())
        assert results[0].supports_tool_use is None
        assert results[0].supports_tool_choice is None
        assert results[0].supports_structured_output is None

    def test_missing_architecture_gives_none_text_support(self) -> None:
        payload = [{"id": "vendor/model"}]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())

        assert results[0].supports_text_output is None

    def test_entry_with_empty_id_skipped(self) -> None:
        payload = [
            {"id": ""},
            {"id": "vendor/valid"},
        ]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())

        assert len(results) == 1
        assert results[0].id == "vendor/valid"

    def test_empty_data_list_returns_empty(self) -> None:
        mock_resp = _make_api_response([])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())
        assert results == []

    def test_missing_data_key_returns_empty(self) -> None:
        body = json.dumps({}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())
        assert results == []

    def test_is_dynamic_router_flag_parsed(self) -> None:
        payload = [
            {"id": "openrouter/auto", "is_dynamic_router": True},
        ]
        mock_resp = _make_api_response(payload)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = LiveOpenRouterCatalogProvider(api_key="key")
            results = list(provider.fetch_catalog())

        assert results[0].is_dynamic_router is True

    def test_auth_header_sent(self) -> None:
        mock_resp = _make_api_response([])
        mock_request_cls = MagicMock(return_value=MagicMock())
        with (
            patch(
                "afterworlds.pipeline.provider._catalog.urllib.request.Request",
                mock_request_cls,
            ),
            patch(
                "afterworlds.pipeline.provider._catalog.urllib.request.urlopen",
                return_value=mock_resp,
            ),
        ):
            provider = LiveOpenRouterCatalogProvider(api_key="sk-test")
            provider.fetch_catalog()

        _, kwargs = mock_request_cls.call_args
        headers: dict[str, str] = kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer sk-test"

    def test_satisfies_protocol(self) -> None:
        provider = LiveOpenRouterCatalogProvider(api_key="key")
        assert isinstance(provider, OpenRouterModelCatalogProvider)
