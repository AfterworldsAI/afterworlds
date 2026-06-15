"""Tests for _build_refusal_log_fn — refusal-event DB writer — CRD Issue 14a.

Covers all four RefusalFallbackRouter outcome codes and two no-row cases:
ProviderCallError from primary (no log row), and sensitive-data exclusion.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.persistence.database import create_session_factory
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
    RefusalCategory,
)
from afterworlds.pipeline.provider._errors import ProviderCallError
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
)
from afterworlds.pipeline.provider._refusal_log import ProviderRefusalEvent
from afterworlds.pipeline.provider._resolver import _build_refusal_log_fn
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sf(engine):  # type: ignore[no-untyped-def]
    """Session factory backed by the conftest in-memory engine."""
    return create_session_factory(engine)


# ---------------------------------------------------------------------------
# Fake adapters
# ---------------------------------------------------------------------------


def _make_request() -> ProviderCallRequest:
    from uuid import uuid4

    return ProviderCallRequest(
        pass_id=PipelinePassId.WRITER,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
        sojourner_id=uuid4(),
        turn_id=uuid4(),
    )


def _primary_refusal_err() -> ProviderRefusalError:
    return ProviderRefusalError(
        ProviderRefusal(
            provider="anthropic",
            model="claude-sonnet-4-5",
            pass_identifier=PassIdentifier.WRITER,
            refusal_category=RefusalCategory.CONTENT_POLICY,
        )
    )


class _RefusingPrimary:
    provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise _primary_refusal_err()


class _SucceedingFallback:
    provider_name = "openrouter"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name="openrouter",
            model_identifier="anthropic/claude-haiku-4-5",
            model_tier=ModelTier.HAIKU,
            content_parts=[ProviderTextPart(text="fallback response")],
            input_token_count=10,
            output_token_count=5,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=50,
            sojourner_id=request.sojourner_id,
            turn_id=request.turn_id,
        )


class _RefusingFallback:
    provider_name = "openrouter"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise ProviderRefusalError(
            ProviderRefusal(
                provider="openrouter",
                model="anthropic/claude-haiku-4-5",
                pass_identifier=PassIdentifier.WRITER,
                refusal_category=RefusalCategory.CONTENT_POLICY,
            )
        )


class _ErrorFallback:
    provider_name = "openrouter"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise ProviderCallError("openrouter connection failed")


class _CallErrorPrimary:
    provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise ProviderCallError("anthropic connection timeout")


# ---------------------------------------------------------------------------
# Helper: count rows via fresh session
# ---------------------------------------------------------------------------


def _count_rows(sf: object) -> int:
    assert callable(sf)
    with sf() as session:
        return len(session.execute(select(ProviderRefusalEvent)).scalars().all())


# ---------------------------------------------------------------------------
# Tests: all four outcome codes each produce exactly one row
# ---------------------------------------------------------------------------


def test_no_fallback_configured_writes_one_row(sf) -> None:  # type: ignore[no-untyped-def]
    """NO_FALLBACK_CONFIGURED: primary refusal with no fallback → one log row."""
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(_make_request())

    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "NO_FALLBACK_CONFIGURED"
        assert row.primary_provider_name == "anthropic"
        assert row.pass_id == "writer"
        assert row.refusal_category == "content_policy"
        assert row.fallback_provider_name is None


def test_fallback_succeeded_writes_one_row(sf) -> None:  # type: ignore[no-untyped-def]
    """FALLBACK_SUCCEEDED: primary refuses, fallback delivers → one log row."""
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(),
        fallback=_SucceedingFallback(),
        refusal_log_fn=log_fn,
    )
    result = router.call(_make_request())

    assert result.provider_name == "openrouter"
    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "FALLBACK_SUCCEEDED"
        assert row.fallback_provider_name == "openrouter"
        assert row.fallback_model_identifier == "anthropic/claude-haiku-4-5"


def test_fallback_also_refused_writes_one_row(sf) -> None:  # type: ignore[no-untyped-def]
    """FALLBACK_ALSO_REFUSED: both providers refuse → one log row."""
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(),
        fallback=_RefusingFallback(),
        refusal_log_fn=log_fn,
    )
    with pytest.raises(ProviderRefusalError):
        router.call(_make_request())

    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "FALLBACK_ALSO_REFUSED"
        assert row.fallback_provider_name == "openrouter"


def test_fallback_error_writes_one_row(sf) -> None:  # type: ignore[no-untyped-def]
    """FALLBACK_ERROR: primary refuses, fallback raises ProviderCallError → one row."""
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(),
        fallback=_ErrorFallback(),
        refusal_log_fn=log_fn,
    )
    with pytest.raises(ProviderCallError):
        router.call(_make_request())

    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "FALLBACK_ERROR"
        assert row.fallback_provider_name == "openrouter"
        assert row.fallback_model_identifier is None


# ---------------------------------------------------------------------------
# Tests: cases that produce no log row
# ---------------------------------------------------------------------------


def test_primary_call_error_writes_no_row(sf) -> None:  # type: ignore[no-untyped-def]
    """Primary ProviderCallError is not a refusal: no log row written."""
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_CallErrorPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderCallError):
        router.call(_make_request())

    assert _count_rows(sf) == 0


def test_log_row_excludes_prompt_text_and_raw_excerpt(sf) -> None:  # type: ignore[no-untyped-def]
    """Log row omits prompt text, system block content, and raw_response_excerpt."""
    from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock

    sentinel = "SENTINEL_PROMPT_CONTENT_XYZ98765"
    request = ProviderCallRequest(
        pass_id=PipelinePassId.WRITER,
        system_blocks=[RenderedBlock(text=f"system: {sentinel}")],
        rendered_blocks=[RenderedBlock(text=f"user: {sentinel}")],
        max_output_tokens=1000,
    )
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    with pytest.raises(ProviderRefusalError):
        router.call(request)

    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        stored = " ".join(
            str(v)
            for v in [
                row.pass_id,
                row.primary_provider_name,
                row.primary_model_identifier,
                row.refusal_category,
                row.fallback_outcome,
                row.coarse_metadata_json or "",
            ]
        )
        assert sentinel not in stored
        assert not hasattr(ProviderRefusalEvent, "raw_response_excerpt")
