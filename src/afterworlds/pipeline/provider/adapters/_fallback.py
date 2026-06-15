"""Refusal fallback router — CRD Issue 14a.

Implements ``ProviderAdapter`` by wrapping a primary adapter and an optional
fallback adapter.  Fallback is triggered only on ``ProviderRefusalError`` from
the primary.  Operational failures (``ProviderCallError``) bypass fallback.

Invariants (CRD v9 Issue 14 acceptance):
  - At most one fallback attempt per ``call()`` invocation.
  - Constructor rejects a nested ``RefusalFallbackRouter`` as the fallback.
  - No hosted/BYOK boundary crossing — enforced by ``ProviderResolver``.
  - No fallback after a Safety BLOCK — enforced structurally: a BLOCK halts
    before the narrative passes, so no pass ``call()`` occurs after it.
  - BYOK pool bounded by configured credentials.

Fallback outcome codes logged to ``provider_refusal_log``:
  NO_FALLBACK_CONFIGURED  — primary refused, no fallback adapter configured
  FALLBACK_SUCCEEDED      — fallback call succeeded
  FALLBACK_ALSO_REFUSED   — fallback call also produced a ProviderRefusalError
  FALLBACK_ERROR          — fallback call produced a ProviderCallError
"""

from __future__ import annotations

import logging

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline.provider._errors import ProviderCallError, ProviderConfigError
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter

logger = logging.getLogger(__name__)

# Fallback outcome codes (coarse; stored in provider_refusal_log)
_NO_FALLBACK_CONFIGURED = "NO_FALLBACK_CONFIGURED"
_FALLBACK_SUCCEEDED = "FALLBACK_SUCCEEDED"
_FALLBACK_ALSO_REFUSED = "FALLBACK_ALSO_REFUSED"
_FALLBACK_ERROR = "FALLBACK_ERROR"


class RefusalFallbackRouter:
    """Wraps a primary adapter with an optional fallback adapter.

    Args:
        primary: Primary ``ProviderAdapter``.
        fallback: Optional fallback ``ProviderAdapter``.  Must not itself be a
            ``RefusalFallbackRouter`` — nested routers are rejected at construction
            with ``ProviderConfigError``.
        refusal_log_fn: Optional callback ``(outcome_code, primary_refusal, ...)``
            for logging to ``provider_refusal_log``.  Called before re-raise.
    """

    def __init__(
        self,
        primary: ProviderAdapter,
        fallback: ProviderAdapter | None = None,
        refusal_log_fn: object = None,
    ) -> None:
        if isinstance(fallback, RefusalFallbackRouter):
            raise ProviderConfigError(
                "RefusalFallbackRouter: nested RefusalFallbackRouter as"
                " fallback is not allowed"
            )
        self._primary = primary
        self._fallback = fallback
        self._refusal_log_fn = refusal_log_fn

    @property
    def provider_name(self) -> str:
        return self._primary.provider_name

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        """Execute the primary adapter; fall back on content-policy refusals only.

        Safety passes (INPUT_SAFETY, OUTPUT_SAFETY) are excluded from fallback:
        a Safety provider refusal propagates immediately so SafetyService.check()
        can wrap it as SafetyPassError (fail-closed contract).  No log row is
        written for Safety-pass refusals.
        """
        try:
            return self._primary.call(request)
        except ProviderRefusalError as primary_refusal:
            if request.pass_id in (
                PipelinePassId.INPUT_SAFETY,
                PipelinePassId.OUTPUT_SAFETY,
            ):
                raise
            return self._handle_refusal(request, primary_refusal)
        # ProviderCallError from primary: re-raise, no fallback, no log entry.

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def _handle_refusal(
        self,
        request: ProviderCallRequest,
        primary_refusal: ProviderRefusalError,
    ) -> ProviderCallResult:
        if self._fallback is None:
            self._log(
                _NO_FALLBACK_CONFIGURED,
                request,
                primary_refusal,
                fallback_provider=None,
                fallback_model=None,
            )
            raise primary_refusal

        try:
            result = self._fallback.call(request)
            self._log(
                _FALLBACK_SUCCEEDED,
                request,
                primary_refusal,
                fallback_provider=self._fallback.provider_name,
                fallback_model=result.model_identifier,
            )
            return result
        except ProviderRefusalError as fallback_refusal:
            self._log(
                _FALLBACK_ALSO_REFUSED,
                request,
                primary_refusal,
                fallback_provider=self._fallback.provider_name,
                fallback_model=fallback_refusal.refusal.model,
            )
            raise fallback_refusal
        except ProviderCallError as fallback_err:
            self._log(
                _FALLBACK_ERROR,
                request,
                primary_refusal,
                fallback_provider=self._fallback.provider_name,
                fallback_model=None,
            )
            raise fallback_err

    def _log(
        self,
        outcome: str,
        request: ProviderCallRequest,
        primary_refusal: ProviderRefusalError,
        fallback_provider: str | None,
        fallback_model: str | None,
    ) -> None:
        if callable(self._refusal_log_fn):
            import contextlib

            with contextlib.suppress(Exception):
                self._refusal_log_fn(
                    outcome=outcome,
                    request=request,
                    primary_refusal=primary_refusal,
                    fallback_provider=fallback_provider,
                    fallback_model=fallback_model,
                )


__all__ = ["RefusalFallbackRouter"]
