"""Tests for _build_refusal_log_fn and ScopedProviderAdapter — CRD Issue 14a.

Covers all four RefusalFallbackRouter outcome codes, two no-row cases
(ProviderCallError from primary, Safety pass refusal), and scope population
via ScopedProviderAdapter (sojourner_id and turn_id in log rows).
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
from afterworlds.pipeline.provider._resolver import (
    RefusalLogProxy,
    _build_refusal_log_fn,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.provider.adapters._scoped import ScopedProviderAdapter

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
    with pytest.raises(ProviderRefusalError):
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


# ---------------------------------------------------------------------------
# ScopedProviderAdapter: refusal log rows carry correct scope (Fix 3)
# ---------------------------------------------------------------------------


def test_scoped_planner_refusal_has_sojourner_id_no_turn_id(sf) -> None:  # type: ignore[no-untyped-def]
    """Planner refusal via ScopedProviderAdapter: sojourner_id set, turn_id=None."""
    from uuid import uuid4

    sojourner_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=None)

    request = ProviderCallRequest(
        pass_id=PipelinePassId.PLANNER,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.sojourner_id == str(sojourner_id)
        assert row.turn_id is None


def test_scoped_extractor_refusal_has_sojourner_id_and_turn_id(sf) -> None:  # type: ignore[no-untyped-def]
    """Extractor refusal via ScopedProviderAdapter: sojourner_id and turn_id set."""
    from uuid import uuid4

    sojourner_id = uuid4()
    turn_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=turn_id)

    request = ProviderCallRequest(
        pass_id=PipelinePassId.EXTRACTOR,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.sojourner_id == str(sojourner_id)
        assert row.turn_id == str(turn_id)


def test_scoped_refusal_log_row_contains_no_key_material(sf) -> None:  # type: ignore[no-untyped-def]
    """Scoped adapter refusal log row contains no key material or prompt text."""
    from uuid import uuid4

    from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock

    sojourner_id = uuid4()
    turn_id = uuid4()
    fake_key = "sk-ant-SECRETKEY99999"
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=turn_id)

    request = ProviderCallRequest(
        pass_id=PipelinePassId.EXTRACTOR,
        system_blocks=[RenderedBlock(text=f"key: {fake_key}")],
        rendered_blocks=[RenderedBlock(text=f"user: {fake_key}")],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

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
                row.sojourner_id or "",
                row.turn_id or "",
                row.coarse_metadata_json or "",
            ]
        )
        assert fake_key not in stored


# ---------------------------------------------------------------------------
# RefusalLogProxy — buffering, flush, and file-backed regression (Finding 1)
# ---------------------------------------------------------------------------


def test_proxy_direct_mode_writes_immediately(sf) -> None:  # type: ignore[no-untyped-def]
    """In direct mode (default), __call__ writes the row immediately."""
    proxy = RefusalLogProxy(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=proxy
    )
    with pytest.raises(ProviderRefusalError):
        router.call(_make_request())

    assert _count_rows(sf) == 1


def test_proxy_buffered_mode_defers_write_until_flush(sf) -> None:  # type: ignore[no-untyped-def]
    """Buffered mode: row NOT written during buffer phase; written on flush()."""
    proxy = RefusalLogProxy(sf)
    proxy.start_buffering()

    proxy(
        outcome="NO_FALLBACK_CONFIGURED",
        request=_make_request(),
        primary_refusal=_primary_refusal_err(),
        fallback_provider=None,
        fallback_model=None,
    )

    assert _count_rows(sf) == 0, "row must not be written while proxy is buffering"

    proxy.flush()

    assert _count_rows(sf) == 1


def test_proxy_flush_empty_buffer_is_noop(sf) -> None:  # type: ignore[no-untyped-def]
    """flush() with no buffered events is a no-op; direct mode still works after."""
    proxy = RefusalLogProxy(sf)
    proxy.start_buffering()
    proxy.flush()  # nothing buffered

    assert _count_rows(sf) == 0

    # Direct mode restored: next write goes immediately
    proxy(
        outcome="NO_FALLBACK_CONFIGURED",
        request=_make_request(),
        primary_refusal=_primary_refusal_err(),
        fallback_provider=None,
        fallback_model=None,
    )
    assert _count_rows(sf) == 1


def test_proxy_file_backed_no_lock_contention(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Regression (file-backed): flush after close() avoids SQLite lock contention.

    Pre-fix: _write_refusal_event opened a fresh session inside the narrative
    transaction, hitting "database is locked" on SQLite.
    Post-fix: proxy buffers in memory; flushes after session.close() releases the lock.
    """
    from sqlalchemy import text

    import afterworlds.pipeline.provider._refusal_log  # noqa: F401
    from afterworlds.persistence.database import create_engine, create_session_factory
    from afterworlds.persistence.orm.base import Base

    db_path = tmp_path / "refusal_lock_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"timeout": 0},  # fail immediately on lock, not after 5s
    )
    Base.metadata.create_all(engine)
    sf = create_session_factory(engine)

    proxy = RefusalLogProxy(sf)
    proxy.start_buffering()

    # Simulate a Writer-pass refusal event during the outer narrative transaction
    proxy(
        outcome="NO_FALLBACK_CONFIGURED",
        request=_make_request(),
        primary_refusal=_primary_refusal_err(),
        fallback_provider=None,
        fallback_model=None,
    )

    # Row must NOT be written yet (the narrative transaction has not committed)
    assert _count_rows(sf) == 0

    # Hold an exclusive write lock (simulates the outer session holding the lock)
    with engine.connect() as locked_conn:
        locked_conn.execute(text("BEGIN EXCLUSIVE"))
        # Under the old design, flush() here would open a competing session and
        # raise "database is locked".  The proxy must NOT flush here.
        assert _count_rows(sf) == 0
        locked_conn.execute(text("ROLLBACK"))

    # Lock released: flush now writes without contention (timeout=0 surfaces any lock)
    proxy.flush()

    assert _count_rows(sf) == 1


# ---------------------------------------------------------------------------
# Finding 1: Writer fallback log row carries preallocated turn_id (P2 fix)
# ---------------------------------------------------------------------------


def test_writer_fallback_succeeded_log_row_has_preallocated_turn_id(sf) -> None:  # type: ignore[no-untyped-def]
    """FALLBACK_SUCCEEDED for Writer: log row turn_id equals preallocated id."""
    from uuid import uuid4

    sojourner_id = uuid4()
    writer_turn_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(),
        fallback=_SucceedingFallback(),
        refusal_log_fn=log_fn,
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=writer_turn_id)
    request = ProviderCallRequest(
        pass_id=PipelinePassId.WRITER,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    result = scoped.call(request)

    assert result.provider_name == "openrouter"
    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "FALLBACK_SUCCEEDED"
        assert row.turn_id == str(writer_turn_id)
        assert row.sojourner_id == str(sojourner_id)


def test_writer_no_fallback_log_row_has_preallocated_turn_id(sf) -> None:  # type: ignore[no-untyped-def]
    """NO_FALLBACK_CONFIGURED for Writer: log row turn_id equals preallocated id."""
    from uuid import uuid4

    sojourner_id = uuid4()
    writer_turn_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=writer_turn_id)
    request = ProviderCallRequest(
        pass_id=PipelinePassId.WRITER,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "NO_FALLBACK_CONFIGURED"
        assert row.turn_id == str(writer_turn_id)


# ---------------------------------------------------------------------------
# Finding 2: Safety provider refusals are logged before re-raising (P2 fix)
# ---------------------------------------------------------------------------


def test_input_safety_refusal_writes_one_row_no_fallback_called(sf) -> None:  # type: ignore[no-untyped-def]
    """INPUT_SAFETY refusal: one log row, NO_FALLBACK_CONFIGURED, no fallback called."""
    from unittest.mock import MagicMock
    from uuid import uuid4

    sojourner_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    fallback_spy = MagicMock()
    fallback_spy.provider_name = "openrouter"
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(),
        fallback=fallback_spy,
        refusal_log_fn=log_fn,
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=None)
    request = ProviderCallRequest(
        pass_id=PipelinePassId.INPUT_SAFETY,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

    fallback_spy.call.assert_not_called()
    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "NO_FALLBACK_CONFIGURED"
        assert row.pass_id == "input_safety"
        assert row.turn_id is None
        assert row.fallback_provider_name is None


def test_output_safety_refusal_log_row_has_writer_turn_id(sf) -> None:  # type: ignore[no-untyped-def]
    """OUTPUT_SAFETY refusal: log row turn_id equals the preallocated writer turn_id."""
    from uuid import uuid4

    sojourner_id = uuid4()
    writer_turn_id = uuid4()
    log_fn = _build_refusal_log_fn(sf)
    router = RefusalFallbackRouter(
        primary=_RefusingPrimary(), fallback=None, refusal_log_fn=log_fn
    )
    scoped = ScopedProviderAdapter(router, sojourner_id, turn_id=writer_turn_id)
    request = ProviderCallRequest(
        pass_id=PipelinePassId.OUTPUT_SAFETY,
        system_blocks=[],
        rendered_blocks=[],
        max_output_tokens=1000,
    )
    with pytest.raises(ProviderRefusalError):
        scoped.call(request)

    assert _count_rows(sf) == 1
    assert callable(sf)
    with sf() as session:
        row = session.execute(select(ProviderRefusalEvent)).scalar_one()
        assert row.fallback_outcome == "NO_FALLBACK_CONFIGURED"
        assert row.pass_id == "output_safety"
        assert row.turn_id == str(writer_turn_id)
