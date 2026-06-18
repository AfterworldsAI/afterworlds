"""Credential validator and key redaction — CRD Issue 14a.

``CredentialValidator`` performs a minimal live health-check (~1 token) to
verify a BYOK key is valid and updates ``ProviderCredentialMetadata``.
``redact_key`` produces a display-safe representation (first 6 + last 4 chars;
fully obscured under 12 chars) for logs and UI display only — never stored.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from afterworlds.pipeline.provider.credentials._metadata import (
    ProviderCredentialMetadata,
    ValidationStatus,
)

# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def redact_key(key: str) -> str:
    """Return a display-safe redacted form of a key.

    - Under 12 chars: fully obscured (``"[REDACTED]"``)
    - 12+ chars: first 6 + ``"..."`` + last 4

    For display and logging only.  The result MUST NOT be stored anywhere.
    """
    if len(key) < 12:
        return "[REDACTED]"
    return f"{key[:6]}...{key[-4:]}"


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of a live credential validation call."""

    sojourner_id: UUID
    provider_name: str
    status: ValidationStatus
    checked_at: datetime
    error_detail: str | None = None  # sanitized; no key material


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class CredentialValidator:
    """Performs live health-check validation of BYOK credentials.

    Makes a minimal (~1 token) provider call to confirm the key is accepted.
    Updates ``ProviderCredentialMetadata`` in the supplied session.

    The raw key is NEVER logged.  Error messages are sanitized before storage.
    """

    def validate(
        self,
        sojourner_id: UUID,
        provider_name: str,
        raw_key: str,
        session: object,
    ) -> ValidationResult:
        """Validate ``raw_key`` with a minimal provider call.

        Args:
            sojourner_id: The Sojourner who owns the key.
            provider_name: ``"anthropic"`` or ``"openrouter"``.
            raw_key: Raw API key.  Never logged or stored.
            session: SQLAlchemy session for updating metadata.

        Returns:
            ``ValidationResult`` with status and sanitized error detail.
        """
        from sqlalchemy.orm import Session

        assert isinstance(session, Session), "session must be a SQLAlchemy Session"

        status, error = self._check(provider_name, raw_key)
        now = datetime.now(UTC)

        result = ValidationResult(
            sojourner_id=sojourner_id,
            provider_name=provider_name,
            status=status,
            checked_at=now,
            error_detail=error,
        )

        self._update_metadata(sojourner_id, provider_name, result, session)
        return result

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def _check(provider_name: str, raw_key: str) -> tuple[ValidationStatus, str | None]:
        if provider_name == "anthropic":
            return CredentialValidator._check_anthropic(raw_key)
        if provider_name == "openrouter":
            return CredentialValidator._check_openrouter(raw_key)
        return ValidationStatus.ERROR, f"Unknown provider: {provider_name!r}"

    @staticmethod
    def _check_anthropic(raw_key: str) -> tuple[ValidationStatus, str | None]:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=raw_key, max_retries=0)
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return ValidationStatus.VALID, None
        except Exception as exc:  # noqa: BLE001
            sanitized = _sanitize_error(str(exc), raw_key)
            return ValidationStatus.INVALID, sanitized

    @staticmethod
    def _check_openrouter(raw_key: str) -> tuple[ValidationStatus, str | None]:
        try:
            import openai

            client = openai.OpenAI(
                api_key=raw_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=0,
            )
            client.chat.completions.create(
                model="openai/gpt-4o-mini",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return ValidationStatus.VALID, None
        except Exception as exc:  # noqa: BLE001
            sanitized = _sanitize_error(str(exc), raw_key)
            return ValidationStatus.INVALID, sanitized

    @staticmethod
    def _update_metadata(
        sojourner_id: UUID,
        provider_name: str,
        result: ValidationResult,
        session: object,
    ) -> None:
        from sqlalchemy import select
        from sqlalchemy.orm import Session

        assert isinstance(session, Session)

        sid = str(sojourner_id)
        stmt = select(ProviderCredentialMetadata).where(
            ProviderCredentialMetadata.sojourner_id == sid,
            ProviderCredentialMetadata.provider_name == provider_name,
        )
        row = session.execute(stmt).scalar_one_or_none()
        now = datetime.now(UTC)

        if row is None:
            row = ProviderCredentialMetadata(
                sojourner_id=sid,
                provider_name=provider_name,
                is_active=True,
                validation_status=result.status.value,
                last_validated_at=result.checked_at,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.validation_status = result.status.value
            row.last_validated_at = result.checked_at
            row.updated_at = now

        session.flush()


def _sanitize_error(message: str, raw_key: str) -> str:
    if raw_key and raw_key in message:
        return message.replace(raw_key, "[REDACTED]")
    if len(raw_key) > 6 and raw_key[:6] in message:
        return message.replace(raw_key[:6], "[REDACTED]")
    return message


__all__ = [
    "CredentialValidator",
    "ValidationResult",
    "redact_key",
]
